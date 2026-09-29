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


def run(manifest_path, mapping_path, storage):
    m=read(manifest_path);problems=errors(m)
    if problems: raise ValueError('Readiness not frozen: '+'; '.join(problems))
    mapping_path=Path(mapping_path).resolve()
    if ROOT in mapping_path.parents or sha(mapping_path.read_bytes())!=m['mapping']['sha256']: raise ValueError('Invalid sealed mapping')
    storage=restricted(storage)
    host=m['host']
    if not shutil.which('docker'): raise ValueError('Docker host unavailable; no substitution')
    subprocess.run(['docker','image','inspect',host['image']],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    marker=storage/'EXECUTION_STARTED.json'
    private_write(marker,{'manifest_sha256':sha(Path(manifest_path).read_bytes()),'start_unix':time.time(),'protocol_status':'EXECUTION BEGUN'})
    # Do not stream stdout, errors or per-session progress to a human annotator.
    for session in read(mapping_path)['sessions']:
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
            for name in host['credential_environment_names']:
                if name not in os.environ: raise ValueError('Provider credential unavailable')
                cmd+=['--env',name]
            cmd += [host['image']]+host['command']
            before=inventory(fixture)
            shutil.copytree(fixture,target/'before')
            started=time.time();failure=None
            try:
                with (target/'raw.jsonl').open('xb') as out,(target/'stderr').open('xb') as err:
                    os.chmod(target/'raw.jsonl',0o600);os.chmod(target/'stderr',0o600)
                    result=subprocess.run(cmd,input=json.dumps(payload).encode(),stdout=out,stderr=err,timeout=m['limits']['seconds'],check=False)
                    code=result.returncode
            except subprocess.TimeoutExpired:
                subprocess.run(['docker','rm','-f',container_name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
                code=124;failure='host_timeout_no_retry'
            except OSError:
                code=127;failure='host_start_failed_no_retry'
            shutil.copytree(fixture,target/'after')
            metadata={'session_id':session['id'],'host_version':host['version'],'effort_requested':setting['effort'],'model_requested':setting['returned_model_id'],'tools':host['tools'],'token_limit':m['limits']['tokens'],'time_limit_seconds':m['limits']['seconds'],'exit_status':code,'failure':failure,'elapsed_seconds':time.time()-started,'install_paths_match':True,'installed_paths':expected_paths,'before':before,'after':inventory(fixture)}
            # Metadata must be provider/host returned, never inferred from requested flags.
            try:
                events=[json.loads(line) for line in (target/'raw.jsonl').read_text().splitlines()]
                reported=next(e for e in events if e.get('type')=='host_metadata')
                for key in ('model_id','host_version','effort','tools'):
                    metadata['returned_'+key]=reported[key]
                if reported['model_id']!=setting['returned_model_id'] or reported['effort']!=setting['effort'] or reported['host_version']!=host['version'] or reported['tools']!=host['tools']:
                    metadata['failure']='host_settings_mismatch_no_retry'
            except (OSError,ValueError,KeyError,StopIteration):
                metadata['failure']='host_metadata_missing_no_retry'
            private_write(target/'record.json',metadata)
            if not metadata['failure']:
                private_write(target/'trace.json',{'session_id':session['id'],'exit_status':code,'metadata':{'actions_complete':reported.get('actions_complete') is True},'events':[e for e in events if e.get('type')!='host_metadata']})
            # A setting mismatch halts the batch for protocol revision, never substitutes.
            if metadata['failure'] in ('host_settings_mismatch_no_retry','host_metadata_missing_no_retry'):
                raise ValueError('Host contract failed; see restricted record; batch stopped')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('mapping');p.add_argument('restricted_storage');a=p.parse_args()
    run(a.manifest,a.mapping,a.restricted_storage)
