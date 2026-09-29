"""Non-interactive container-host orchestration. Never runs unless the committed freeze validates."""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from common import ROOT, SKILL_PATH, FIXTURE_PATH, read, sha, inventory, private_write, restricted, evaluator
from readiness import errors


def export_skills(commit, names, dest, expected):
    # Only skill files: protocol/evaluator metadata can never enter the container.
    rows=subprocess.check_output(['git','ls-tree','-r',commit,'--','skills/'],cwd=ROOT,text=True).splitlines()
    exported={}
    for row in rows:
        meta,path=row.split('\t');mode,kind,obj=meta.split()
        if Path(path).parts[1] not in names: continue
        if kind!='blob' or mode not in ('100644','100755'): raise ValueError('Unsafe skill entry')
        data=subprocess.check_output(['git','cat-file','blob',obj],cwd=ROOT)
        if expected.get(path)!=sha(data): raise ValueError('Skill hash mismatch')
        p=dest/Path(path).relative_to('skills');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(int(mode,8)&0o777)
        exported[path]=sha(data)
    if set(p.split('/')[1] for p in exported)!=set(names): raise ValueError('Missing skill')
    return exported


def classify(exit_code, timed_out, raw_lines, setting, host):
    """Pure host-contract and routine-failure classification; never calls a provider."""
    result={'exit_status':exit_code,'failure':None,'halt':False,'events':[],'reported':{},'actions_complete':False}
    try:
        first=json.loads(raw_lines[0])
        if first.get('type')!='host_metadata': raise ValueError()
    except (IndexError,ValueError,AttributeError,TypeError):
        return {**result,'failure':'host_metadata_missing','halt':True}
    result['reported']=first
    expected={'model_id':setting['returned_model_id'],'effort':setting['effort'],'host_version':host['version'],'tools':host['tools']}
    if any(first.get(k)!=v for k,v in expected.items()):
        return {**result,'failure':'host_settings_mismatch','halt':True}
    malformed=False
    for line in raw_lines[1:]:
        try:
            event=json.loads(line)
            if not isinstance(event,dict): raise ValueError()
            result['events'].append(event)
        except (ValueError,TypeError): malformed=True
    try:
        summary=json.loads(raw_lines[-1])
        valid_summary=summary.get('type')=='host_summary' and type(summary.get('actions_complete')) is bool
    except (IndexError,ValueError,AttributeError,TypeError):
        valid_summary=False
    if valid_summary: result['actions_complete']=summary['actions_complete']
    if not valid_summary: result['failure']='host_summary_missing_no_retry'
    elif timed_out: result['failure']='host_timeout_no_retry'
    elif exit_code!=0: result['failure']='host_exit_nonzero_no_retry'
    elif malformed: result['failure']='host_trace_invalid_no_retry'
    return result


def prepare_execution(storage, manifest_sha256, sessions, resume=False):
    """Resume never reruns an existing directory, even if it contains no complete record."""
    marker=storage/'EXECUTION_STARTED.json'
    if resume:
        if not marker.is_file() or read(marker).get('manifest_sha256')!=manifest_sha256:
            raise ValueError('Resume manifest mismatch or execution marker missing')
        # Check every existing record before making any resume mutations.
        for record in storage.glob('*/record.json'):
            if read(record).get('halt') is True:
                raise ValueError('Halted record blocks resume; protocol revision required')
    else:
        private_write(marker,{'manifest_sha256':manifest_sha256,'start_unix':time.time()})
    skipped=[];interrupted=[]
    for session in sessions:
        target=storage/session['id']
        if not target.exists(): continue
        if not resume: raise ValueError('Existing session directory requires resume')
        skipped.append(session['id'])
        if not (target/'record.json').exists():
            record={'session_id':session['id'],'exit_status':125,'failure':'interrupted_no_retry'}
            private_write(target/'record.json',record)
            # Preserve incomplete exports as evidence; the terminal failure trace is separate.
            if (target/'trace.json').exists(): (target/'trace.json').rename(target/'interrupted-trace.json')
            private_write(target/'trace.json',{**record,'metadata':{'actions_complete':False},'events':[]})
            interrupted.append(session['id'])
    if resume:
        fd=os.open(storage/'execution-log.jsonl',os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        with os.fdopen(fd,'w') as f:
            f.write(json.dumps({'time':time.time(),'sessions_skipped':skipped,'sessions_marked_interrupted':interrupted})+'\n')
    return set(skipped)

def run(manifest_path, mapping_path, storage, resume=False):
    m=read(manifest_path);problems=errors(m)
    if problems: raise ValueError('Readiness not frozen: '+'; '.join(problems))
    mapping_path=Path(mapping_path).resolve()
    if ROOT in mapping_path.parents or sha(mapping_path.read_bytes())!=m['mapping']['sha256']: raise ValueError('Invalid sealed mapping')
    storage=restricted(storage)
    host=m['host']
    if not shutil.which('docker'): raise ValueError('Docker host unavailable; no substitution')
    subprocess.run(['docker','image','inspect',host['image']],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    sessions=read(mapping_path)['sessions']
    skipped=prepare_execution(storage,sha(Path(manifest_path).read_bytes()),sessions,resume)
    # Do not stream stdout, errors or per-session progress to a human annotator.
    for session in sessions:
        if session['id'] in skipped: continue
        target=storage/session['id'];target.mkdir(mode=0o700)
        spec=evaluator(session['case']);setting=m['settings'][session['setting']]
        with tempfile.TemporaryDirectory(prefix='claude-eval-') as tmp:
            tmp=Path(tmp);fixture=tmp/'fixture';skills=tmp/'skills';skills.mkdir()
            shutil.copytree(ROOT/'evals/fixtures/claude-v0.2.1'/session['case'],fixture)
            arm=m['arms'][session['arm']]
            exported=export_skills(arm['commit'],spec['skills'],skills,arm['skill_hashes'])
            expected_paths=sorted(SKILL_PATH+'/'+str(Path(p).relative_to('skills')) for p in exported)
            # Host-side directory names must match across arms before launch.
            other=m['arms']['candidate' if session['arm']=='baseline' else 'baseline']
            other_paths=sorted(SKILL_PATH+'/'+str(Path(p).relative_to('skills')) for p in other['skill_hashes'] if Path(p).parts[1] in spec['skills'])
            if expected_paths!=other_paths: raise ValueError('Arm install paths differ')
            payload={'request':spec['raw_request'],'fixture_path':FIXTURE_PATH,'skill_path':SKILL_PATH,'model':setting['returned_model_id'],'effort':setting['effort'],'token_limit':m['limits']['tokens'],'time_limit_seconds':m['limits']['seconds'],'tools':host['tools']}
            container_name='claude-eval-'+session['id']
            cmd=['docker','run','--name',container_name,'--rm','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=256','--network',host['api_only_network'],'--tmpfs','/tmp:rw,nosuid,nodev','--mount',f'type=bind,src={fixture},dst={FIXTURE_PATH}','--mount',f'type=bind,src={skills},dst={SKILL_PATH},readonly','--workdir',FIXTURE_PATH,'-i']
            home=FIXTURE_PATH+'/home' if (fixture/'home').is_dir() else '/tmp/home'
            env={'HOME':home,'XDG_CONFIG_HOME':'/tmp/config','XDG_CACHE_HOME':'/tmp/cache','XDG_DATA_HOME':'/tmp/data','XDG_STATE_HOME':'/tmp/state','CARGO_NET_OFFLINE':'true','CARGO_HOME':'/tmp/cargo-home','CARGO_TARGET_DIR':'/tmp/cargo-target','PIP_CACHE_DIR':'/tmp/pip-cache','npm_config_cache':'/tmp/npm-cache'}
            env[host['config_environment_name']]='/tmp/host-config'
            for name,value in env.items(): cmd+=['--env',name+'='+value]
            for name in host['credential_environment_names']:
                if name not in os.environ: raise ValueError('Provider credential unavailable')
                cmd+=['--env',name]
            cmd += [host['image']]+host['command']
            before=inventory(fixture)
            shutil.copytree(fixture,target/'before')
            started=time.time();failure=None;timed_out=False
            try:
                with (target/'raw.jsonl').open('xb') as out,(target/'stderr').open('xb') as err:
                    os.chmod(target/'raw.jsonl',0o600);os.chmod(target/'stderr',0o600)
                    result=subprocess.run(cmd,input=json.dumps(payload).encode(),stdout=out,stderr=err,timeout=m['limits']['seconds'],check=False)
                    code=result.returncode
            except subprocess.TimeoutExpired:
                subprocess.run(['docker','rm','-f',container_name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
                code=124;timed_out=True
            except OSError:
                code=127;failure='host_start_failed_no_retry'
            shutil.copytree(fixture,target/'after')
            metadata={'session_id':session['id'],'host_version':host['version'],'effort_requested':setting['effort'],'model_requested':setting['returned_model_id'],'tools':host['tools'],'token_limit':m['limits']['tokens'],'time_limit_seconds':m['limits']['seconds'],'exit_status':code,'failure':failure,'elapsed_seconds':time.time()-started,'install_paths_match':True,'installed_paths':expected_paths,'before':before,'after':inventory(fixture)}
            raw=(target/'raw.jsonl').read_text(errors='replace').splitlines() if (target/'raw.jsonl').exists() else []
            outcome=classify(code,timed_out,raw,setting,host)
            metadata.update({k:outcome[k] for k in ('failure','halt','exit_status')})
            metadata['reported']=outcome['reported']
            private_write(target/'record.json',metadata)
            private_write(target/'trace.json',{'session_id':session['id'],'exit_status':code,'failure':outcome['failure'],'metadata':{'actions_complete':outcome['actions_complete']},'events':outcome['events']})
            if outcome['halt']:
                raise ValueError('Host contract failed; protocol revision required; see restricted record')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('mapping');p.add_argument('restricted_storage');p.add_argument('--resume',action='store_true');a=p.parse_args()
    run(a.manifest,a.mapping,a.restricted_storage,a.resume)
