"""Phase 2 only: scratch host checks. No evaluation-case fixture is opened or copied."""
import argparse
import copy
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from common import read,write,private_write,restricted,inventory,sha,SKILL_PATH
from runner import build_command,template_hash,export_skills,classify,prepare_mounts


def invoke(host,fixture,skills,name,payload,seconds,command=None):
    prepare_mounts(fixture,skills)
    probe_host={**host,'command':command or host['command']}
    cmd=build_command(probe_host,fixture,skills,name,(fixture/'home').exists())
    before=inventory(fixture)
    try:
        result=subprocess.run(cmd,input=json.dumps(payload).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=seconds,check=False)
    except subprocess.TimeoutExpired:
        subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        raise RuntimeError('Pre-flight timed out; no retry')
    return {'command':cmd,'before':before,'after':inventory(fixture),'stdout':result.stdout.decode(errors='replace'),'stderr':result.stderr.decode(errors='replace'),'exit_status':result.returncode}


def _run(manifest,storage,evidence):
    m=copy.deepcopy(manifest);host=m['host'];storage=restricted(storage)
    if not shutil.which('docker'):raise ValueError('Docker unavailable; no pre-flight run')
    internal=json.loads(subprocess.check_output(['docker','network','inspect',host['api_only_network']]))[0]
    if internal.get('Internal') is not True:raise ValueError('Host network must be internal')
    with tempfile.TemporaryDirectory(prefix='claude-scratch-preflight-') as td:
        tmp=Path(td);skills=tmp/'skills';skills.mkdir();fixture=tmp/'fixture';fixture.mkdir()
        export_skills(m['arms']['candidate']['commit'],['omarchy-theme-scaffold'],skills,m['arms']['candidate']['skill_hashes'])
        # Scratch files never come from evals/fixtures.
        (fixture/'note.txt').write_text('A small scratch document.\n')
        for path in [tmp,fixture,skills,*skills.rglob('*')]:
            if path.is_dir():path.chmod(0o755)
        os.chmod(fixture,0o777) # isolated disposable tree writable by container UID 1000
        version=invoke(host,fixture,skills,'claude-preflight-version',{},60,['claude','--version']);evidence.append(version)
        if version['exit_status']!=0:raise ValueError('Host version unavailable')
        host['version']=version['stdout'].strip()
        def session(key,request,home=False):
            if home:(fixture/'home').mkdir(exist_ok=True,mode=0o777)
            elif (fixture/'home').exists():shutil.rmtree(fixture/'home')
            setting=m['settings'][key]
            payload={'request':request,'model':setting['configured_model_id'],'effort':setting['effort'],'tools':host['tools'],'max_turns':m['limits']['max_turns'],'max_budget_usd':m['limits']['max_budget_usd']}
            record=invoke(host,fixture,skills,'claude-preflight-'+str(len(evidence)),payload,m['limits']['seconds']);evidence.append(record)
            outcome=classify(record['exit_status'],False,record['stdout'].splitlines(),{**setting,'loaded_skills':['omarchy-theme-scaffold']},host)
            if outcome['halt'] or outcome['failure']:raise ValueError('Pre-flight session contract failed: '+str(outcome['failure']))
            if record['before']!=record['after']:raise ValueError('Host or model wrote into scratch fixture')
            return outcome,record
        for home in (False,True):session('sonnet-low','Read note.txt and reply only OK. Do not create, edit or delete any files.',home)
        for key in m['settings']:
            outcome,record=session(key,'Reply only OK. Do not create, edit or delete any files.')
            m['settings'][key].update(verified=True,returned_model_id=next(r['model'] for r in outcome['summary']['requests'] if r['query_source']=='main'),host_reported_effort=m['settings'][key]['effort'],evidence_sha256=sha(json.dumps(record,sort_keys=True).encode()))
        # Exercise skill invocation and raw reads without creating a theme.
        outcome,record=session('sonnet-low','Read the first 15 lines of '+SKILL_PATH+'/omarchy-theme-scaffold/SKILL.md using Bash head and read the complete file with the Read tool, then invoke the omarchy-theme-scaffold skill for a read-only explanation. Do not create or change files. Reply only OK.')
        from host.claude_code_adapter import skill_index
        index=skill_index(skills,exclude_root=fixture)
        from host.claude_code_adapter import skill_line
        from redact import redact
        read_calls={e['id'] for e in outcome['events'] if e['type']=='tool_call' and e.get('name')=='Read' and e.get('arguments',{}).get('file_path')==SKILL_PATH+'/omarchy-theme-scaffold/SKILL.md'}
        if not read_calls:raise ValueError('Read-tool skill probe was not exercised')
        seen_reads=set();marked=False
        annotation,_=redact({'session_id':'preflight','case':'accent-only','events':outcome['events']},[])
        redacted_results={e['call_id']:e for e in annotation['events'] if e['type']=='tool_result'}
        for event in outcome['events']:
            if event.get('type')=='tool_result':
                skill_segments=[s for s in event['segments'] if s['kind']=='skill_file']
                for segment in event['segments']:
                    if segment['kind']=='task_output' and any(skill_line(line).strip() and skill_line(line) in index.all_lines for line in segment.get('text','').splitlines()):raise ValueError('Unsegmented skill content')
                if skill_segments:
                    marked=True
                    placeholders=[s for s in redacted_results[event['call_id']]['segments'] if s.get('text')=='[skill content]']
                    if len(placeholders)!=1:raise ValueError('Skill result must have exactly one placeholder')
                if event['call_id'] in read_calls:
                    if not skill_segments:raise ValueError('Read-tool result not segmented')
                    seen_reads.add(event['call_id'])
            elif event.get('type') in ('assistant','final'):
                if any(skill_line(line).strip() and skill_line(line) in index.all_lines for line in event.get('text','').splitlines()):raise ValueError('Skill text in non-segment channel')
        if not marked or seen_reads!=read_calls:raise ValueError('Skill segmentation was not exercised')
        cargo=['cargo','run','--offline','--manifest-path',SKILL_PATH+'/omarchy-theme-scaffold/scripts/theme-tool/Cargo.toml','--']
        for args in (['scaffold','/tmp/omarchy-scratch-theme'],):
            # Scaffold and check share one container so the scratch tree survives.
            command=['sh','-c','cargo run --offline --manifest-path '+cargo[4]+' -- scaffold /tmp/omarchy-scratch-theme && cargo run --offline --manifest-path '+cargo[4]+' -- check /tmp/omarchy-scratch-theme']
            record=invoke(host,fixture,skills,'claude-preflight-helper',{},180,command);evidence.append(record)
            if record['exit_status']!=0:raise ValueError('Offline helper check failed')
        # The successful tiny sessions prove authenticated Anthropic calls through the proxy.
        for name,command in [('deny-proxy',['curl','--fail','--max-time','10','https://example.com']),('deny-direct',['curl','--noproxy','*','--fail','--max-time','10','https://api.anthropic.com'])]:
            record=invoke(host,fixture,skills,'claude-preflight-'+name,{},30,command);evidence.append(record)
            if record['exit_status']==0:raise ValueError('API-only network probe unexpectedly succeeded')
        evidence_file=storage/'preflight.json';private_write(evidence_file,{'records':evidence,'network':internal})
        digest=sha(evidence_file.read_bytes())
        host.update(verified=True,skill_content_all_channels=True,network_isolation_verified=True,permission_mode='bypassPermissions',preflight={'no_write_home':True,'no_write_no_home':True,'helper_build':True,'network_allow':True,'network_deny':True,'skill_segmentation':True,'evidence_sha256':digest,'command_template_sha256':template_hash(host)})
    return m

def run(manifest,storage):
    storage=restricted(storage);evidence=[]
    try:return _run(manifest,storage,evidence)
    except Exception:
        private_write(storage/'preflight-failed.json',{'records':evidence,'status':'FAILED_NO_RETRY'})
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('restricted_storage');p.add_argument('output_manifest');a=p.parse_args()
    write(a.output_manifest,run(read(a.manifest),a.restricted_storage),exclusive=True)
