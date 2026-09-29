"""Fail-closed freeze validator; BLOCKED values are records of missing evidence, never ready."""
import argparse
import re
import subprocess
from pathlib import Path
from common import ROOT, read, sha, inventory, CASES, SETTINGS


def errors(m, through=9):
    issues=[]
    def digest(v): return isinstance(v,str) and bool(re.fullmatch('[0-9a-f]{64}',v))
    def text(v): return isinstance(v,str) and bool(v.strip()) and 'BLOCKED' not in v.upper()
    def strings(v): return isinstance(v,list) and bool(v) and all(text(x) for x in v)
    def fail(test,text):
        if not test: issues.append(text)
    fail(m.get('status')=='NOT RUN','status must be NOT RUN')
    for key,step in [('fixture_manifests',1),('evaluator_manifests',2),('scripts',3)]:
        if through < step: continue
        items=m.get(key,{})
        fail(bool(items),key+' missing')
        for path,item in items.items():
            p=ROOT/path
            fail(p.is_file() and sha(p.read_bytes())==item.get('sha256'),key+' hash mismatch: '+path)
            if key=='scripts':
                commit=item.get('commit','')
                fail(bool(re.fullmatch('[0-9a-f]{40}',commit)),'script commit unresolved: '+path)
                try:
                    committed=subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT,stderr=subprocess.DEVNULL)
                    fail(sha(committed)==item.get('sha256'),'script commit content mismatch: '+path)
                except subprocess.CalledProcessError: issues.append('script commit unavailable: '+path)
    for case in CASES:
        fm=ROOT/f'evals/fixture-manifests/claude-v0.2.1/{case}.json'
        try: fail(read(fm)['files']==inventory(ROOT/f'evals/fixtures/claude-v0.2.1/{case}'),'fixture drift: '+case)
        except (OSError,ValueError): issues.append('fixture unavailable: '+case)
    for arm in ('baseline','candidate'):
        v=m.get('arms',{}).get(arm,{})
        fail(bool(re.fullmatch('[0-9a-f]{40}',v.get('commit',''))),'arm commit missing')
        fail(bool(v.get('skill_hashes')),'skill hashes missing')
    if through>=4:
        fail(m.get('synthetic_pipeline',{}).get('status')=='PASS','synthetic pipeline not passed')
    if through>=5:
        settings=m.get('settings',{})
        fail(set(settings)==set(SETTINGS),'four settings required')
        expected=dict(zip(SETTINGS,['high','medium','medium','low']))
        for key,v in settings.items():
            fail(v.get('verified') is True and v.get('effort')==expected.get(key),'setting not verified: '+key)
            fail(v.get('returned_model_id','').startswith('claude-'),'returned model ID unavailable: '+key)
            fail(digest(v.get('evidence_sha256')),'host effort evidence invalid: '+key)
            fail(v.get('host_reported_effort')==v.get('effort'),'host reported effort mismatch: '+key)
        host=m.get('host',{})
        fail(host.get('verified') is True,'host not verified')
        for field in ('command','tools','credential_environment_names'):
            fail(strings(host.get(field)),'host '+field+' must be a nonempty string list')
        for field in ('api_only_network','version','config_environment_name'):
            fail(text(host.get(field)),'host '+field+' must be a nonempty observed string')
        fail(host.get('skill_content_all_channels') is True,'host skill content export unverified')
        for field in ('seconds','tokens'):
            v=m.get('limits',{}).get(field)
            fail(type(v) is int and v>0,'limits '+field+' must be a positive integer')
        preflight=host.get('preflight',{})
        for field in ('no_write_home','no_write_no_home','helper_build'):
            fail(preflight.get(field) is True,'host preflight '+field+' not passed')
        fail(digest(preflight.get('evidence_sha256')),'host preflight evidence invalid')
        fail(bool(re.fullmatch(r'.+@sha256:[0-9a-f]{64}',host.get('image',''))),'host image not digest-pinned')
        fail(host.get('network_isolation_verified') is True,'API-only egress not verified')
        fail(host.get('skill_install_path')=='/opt/evaluation/skills','noncanonical skill install path')
    if through>=6:
        a=m.get('annotator',{})
        fail(a.get('verified') is True,'annotator unresolved')
        for key in ('model_snapshot_id','host_version','effort','prompt_sha256','rubric_sha256','scoring_commit','software_versions'):
            fail(bool(a.get(key)) and 'BLOCKED' not in str(a[key]),'annotator '+key+' unresolved')
    if through>=7:
        mapping=m.get('mapping',{})
        fail(bool(re.fullmatch('[0-9a-f]{64}',mapping.get('sha256',''))),'mapping not committed')
        fail(len(mapping.get('session_ids',[]))==144 and len(set(mapping.get('session_ids',[])))==144,'144 unique IDs required')
    if through>=8:
        from audit import select
        try: fail(m.get('audit')==select(m['mapping']['session_ids']),'audit sample/version mismatch')
        except (KeyError,ValueError): issues.append('audit not generated')
    if through>=9:
        def scan(value,path='manifest'):
            if isinstance(value,str) and 'BLOCKED' in value.upper(): issues.append('unresolved BLOCKED value: '+path)
            elif isinstance(value,dict):
                for key,item in value.items():
                    if key=='verified' and item is not True: issues.append('verified must be true: '+path+'.'+key)
                    scan(item,path+'.'+key)
            elif isinstance(value,list):
                for i,item in enumerate(value): scan(item,path+'['+str(i)+']')
        scan(m)
        fail(m.get('freeze',{}).get('state')=='FROZEN','run manifest not frozen')
        fail(not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip(),'worktree must be clean')
    return issues

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');a=p.parse_args()
    problems=errors(read(a.manifest))
    print('BLOCKED: '+'; '.join(problems) if problems else 'PASS: readiness')
    raise SystemExit(bool(problems))
