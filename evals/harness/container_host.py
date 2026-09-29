"""Single locked command/environment builder used by execution and scratch pre-flight."""
import hashlib
import json
from pathlib import Path

SKILL_PATH='/opt/evaluation/.claude/skills'
FIXTURE_PATH='/work/fixture'


def build_command(host,fixture,skills,name,has_home):
    if host['config_environment_name']!='CLAUDE_CONFIG_DIR':raise ValueError('Claude config directory must be relocated')
    if set(host['credential_environment_names'])-{'ANTHROPIC_API_KEY','CLAUDE_CODE_OAUTH_TOKEN'}:raise ValueError('Unexpected credential environment name')
    env={'HOME':FIXTURE_PATH+'/home' if has_home else '/tmp/home','CLAUDE_CONFIG_DIR':'/tmp/host-config','XDG_CONFIG_HOME':'/tmp/config','XDG_CACHE_HOME':'/tmp/cache','XDG_DATA_HOME':'/tmp/data','XDG_STATE_HOME':'/tmp/state','CARGO_NET_OFFLINE':'true','CARGO_HOME':'/tmp/cargo-home','CARGO_TARGET_DIR':'/tmp/cargo-target','PIP_CACHE_DIR':'/tmp/pip-cache','npm_config_cache':'/tmp/npm-cache','CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC':'1','HTTPS_PROXY':host['proxy_url'],'HTTP_PROXY':host['proxy_url'],'https_proxy':host['proxy_url'],'http_proxy':host['proxy_url'],'NO_PROXY':'127.0.0.1,localhost','no_proxy':'127.0.0.1,localhost'}
    cmd=['docker','run','--name',name,'--rm','--read-only','--user','1000:1000','--cap-drop=ALL','--security-opt=no-new-privileges','--pids-limit=256','--network',host['api_only_network'],'--tmpfs','/tmp:rw,nosuid,nodev,mode=1777','--mount',f'type=bind,src={fixture},dst={FIXTURE_PATH}','--mount',f'type=bind,src={skills},dst={SKILL_PATH},readonly','--workdir',FIXTURE_PATH,'-i']
    for key,value in env.items():cmd+=['--env',key+'='+value]
    for key in host['credential_environment_names']:cmd+=['--env',key]
    # unset rather than empty: inherited image ENV must not override --effort.
    return cmd+[host['image'],'env','-u','CLAUDE_CODE_EFFORT_LEVEL']+host['command']


def template_hash(host):
    templates=[build_command(host,'<fixture>','<skills>','<session>',v) for v in (False,True)]
    return hashlib.sha256(json.dumps(templates,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def prepare_mounts(fixture,skills):
    import os
    if os.getuid() not in (0,1000):raise ValueError('Mount preparation requires host UID 1000 or root')
    for root in (Path(fixture),Path(skills)):
        root.parent.chmod(0o755)
        for path in [root,*root.rglob('*')]:
            if path.is_symlink():raise ValueError('Symlink in mount')
            if os.getuid()==0 and root==Path(fixture):os.chown(path,1000,1000)
            if root==Path(skills):path.chmod(0o755 if path.is_dir() else (path.stat().st_mode&0o777)|0o444)
