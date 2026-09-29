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
        outcome,record=session('sonnet-low','Read the first 15 lines of '+SKILL_PATH+'/omarchy-theme-scaffold/SKILL.md using Bash head, then invoke the omarchy-theme-scaffold skill for a read-only explanation. Do not create or change files. Reply only OK.')
        from host.claude_code_adapter import skill_index
        index=skill_index(skills);known=set(index)
        marked=False
        for event in outcome['events']:
            if event.get('type')=='tool_result':
                for segment in event['segments']:
                    if segment['kind']=='skill_file':marked=True
                    elif any(line in known for line in segment.get('text','').splitlines() if line):raise ValueError('Unsegmented skill content')
            elif event.get('type') in ('assistant','final'):
                if any(line in known for line in event.get('text','').splitlines() if line):raise ValueError('Skill text in non-segment channel')
        if not marked:raise ValueError('Skill segmentation was not exercised')
        cargo=['cargo','run','--offline','--manifest-path',SKILL_PATH+'/omarchy-theme-scaffold/scripts/theme-tool/Cargo.toml','--']
        for args in (['scaffold','/tmp/scratch-theme'],):
            # Scaffold and check share one container so the scratch tree survives.
            command=['sh','-c','cargo run --offline --manifest-path '+cargo[4]+' -- scaffold /tmp/scratch-theme && cargo run --offline --manifest-path '+cargo[4]+' -- check /tmp/scratch-theme']
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
