"""Claude Code stream-json to the evaluation trace contract. Pure conversion is testable offline."""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SKILL_PATH='/opt/evaluation/.claude/skills'


class SkillIndex(dict):
    pass


def skill_index(root, exclude_root='/work/fixture'):
    excluded=set()
    for path in Path(exclude_root).rglob('*'):
        if not path.is_file(): continue
        try: excluded.update(path.read_text().splitlines())
        except UnicodeDecodeError: continue
    lines=SkillIndex();lines.all_lines=set();lines.excluded=excluded
    for path in sorted(Path(root).rglob('*')):
        if not path.is_file(): continue
        try: text=path.read_text()
        except UnicodeDecodeError: continue
        for line in text.splitlines():
            lines.all_lines.add(line)
            if len(line)>=12 and any(c.isalnum() for c in line) and line not in excluded:
                lines.setdefault(line,str(path))
    return lines


def skill_line(line):
    line=line.rstrip('\r\n')
    line=re.sub(r'^\s*\d+[\t→]', '', line)
    return re.sub(r'^[^:\n]+:\d+:', '', line)


def skill_segment(text,path):
    import hashlib
    return {'kind':'skill_file','path':path,'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest()}


def segments(text,index):
    result=[];run=[];path=None
    all_lines=getattr(index,'all_lines',set(index))
    excluded=getattr(index,'excluded',set())
    for line in text.splitlines(keepends=True):
        key=skill_line(line)
        if run and (not key.strip() or (key in all_lines and key not in excluded)):
            run.append(line)
        elif key in index:
            if run: result.append(skill_segment(''.join(run),path))
            run=[line];path=index[key]
            # Include an adjacent short/blank prefix only after a trusted anchor.
            while result and result[-1]['kind']=='task_output':
                previous=skill_line(result[-1]['text'])
                if previous.strip() and (previous not in all_lines or previous in excluded):break
                run.insert(0,result.pop()['text'])
        else:
            if run: result.append(skill_segment(''.join(run),path));run=[]
            result.append({'kind':'task_output','text':line})
    if run: result.append(skill_segment(''.join(run),path))
    return result


def content_text(content):
    if isinstance(content,str): return content
    if isinstance(content,list): return '\n'.join(x.get('text',json.dumps(x)) for x in content)
    return json.dumps(content)


def telemetry_requests(path):
    requests=[]
    if not Path(path).exists(): return requests
    for line in Path(path).read_text().splitlines():
        entry=json.loads(line)
        for resource in entry.get('resourceLogs',[]):
            for scope in resource.get('scopeLogs',[]):
                for record in scope.get('logRecords',[]):
                    attrs={a['key']:next(iter(a.get('value',{}).values()),None) for a in record.get('attributes',[])}
                    if attrs.get('event.name')!='api_request': continue
                    raw=attrs.get('query_source')
                    if raw in ('main','repl_main_thread'): source='main'
                    elif raw=='subagent' or attrs.get('agent.name') or str(raw).startswith(('agent.','subagent.')): source='subagent'
                    elif raw in ('auxiliary','compact','summarize','summarization','prompt_suggestion','session_title','title','background'): source='auxiliary'
                    else: source='unknown'
                    requests.append({'model':attrs.get('model'),'effort':attrs.get('effort'),'query_source':source,'query_source_raw':raw})
    return requests


class Converter:
    def __init__(self,payload,version,index):
        self.payload=payload;self.version=version;self.index=index
        self.skill_calls={};self.started=False;self.calls=set();self.results=set();self.models=set();self.result=None;self.invalid=False
    def feed(self,event):
        kind=event.get('type');out=[]
        if kind=='system' and event.get('subtype')=='init':
            if self.started: self.invalid=True;return []
            self.started=True
            return [{'type':'host_metadata','configured_model_id':event.get('model'),'requested_effort':self.payload['effort'],'host_version':self.version,'tools':event.get('tools',[]),'loaded_skills':event.get('skills',[])}]
        if not self.started: self.invalid=True;return []
        if kind=='assistant':
            message=event.get('message',{});model=message.get('model')
            if model: self.models.add(model)
            for block in message.get('content',[]):
                if block.get('type')=='text':out.append({'type':'assistant','text':block['text']})
                elif block.get('type')=='tool_use':
                    call=block['id'];name=block['name'];args=block.get('input',{})
                    if call in self.calls:self.invalid=True
                    self.calls.add(call);out.append({'type':'tool_call','id':call,'name':name,'arguments':args})
                    if name in ('Read','Grep','Glob'):
                        source=args.get('file_path') or args.get('path')
                        if isinstance(source,str):
                            source=os.path.normpath(os.path.join('/work/fixture',source))
                            if Path(source).is_relative_to(SKILL_PATH):self.skill_calls[call]=source
                    if name in ('Edit','Write','MultiEdit'):
                        out.extend([{'type':'patch','call_id':call,'path':args.get('file_path'),'input':args},{'type':'action','call_id':call,'kind':'file_write','path':args.get('file_path')}])
                    if name=='Bash':
                        command=args.get('command','');out.append({'type':'action','call_id':call,'kind':'command','command':command})
                        if re.search(r'\b(omarchy-theme-set|hyprctl|swaybg|swww|waybar|systemctl|reboot|shutdown)\b',command):out.append({'type':'action','call_id':call,'kind':'desktop_change','command':command})
        elif kind=='user':
            content=event.get('message',{}).get('content',[])
            if isinstance(content,str):content=[{'type':'text','text':content}]
            for i,block in enumerate(content):
                if block.get('type')=='tool_result':
                    call=block['tool_use_id'];self.results.add(call)
                    out.append({'type':'tool_result','call_id':call,'is_error':block.get('is_error',False),'segments':([skill_segment(content_text(block.get('content','')),self.skill_calls[call])] if call in self.skill_calls else segments(content_text(block.get('content','')),self.index))})
                elif block.get('type')=='text':
                    out.append({'type':'tool_result','call_id':'invocation-'+str(event.get('uuid',''))+'-'+str(i),'segments':segments(block['text'],self.index)})
        elif kind=='system' and any(key in event for key in ('content','text','message')):
            text=content_text(event.get('content',event.get('text',event.get('message',''))))
            out.append({'type':'tool_result','call_id':'system-'+str(event.get('uuid','')),'segments':segments(text,self.index)})
        elif kind=='result':
            self.result=event;out.append({'type':'final','text':event.get('result',''),'subtype':event.get('subtype'),'errors':event.get('errors',[])})
        elif kind not in ('system','rate_limit_event'):
            self.invalid=True
        return out
    def finish(self,requests,exit_status):
        success=self.result is not None and self.result.get('subtype')=='success' and not self.result.get('is_error')
        return {'type':'host_summary','actions_complete':bool(success and not self.invalid and self.calls==self.results and exit_status==0),'returned_models':sorted(self.models),'requests':requests,'cost_usd':(self.result or {}).get('total_cost_usd'),'turns':(self.result or {}).get('num_turns'),'result_subtype':(self.result or {}).get('subtype'),'exit_status':exit_status}


def command(payload):
    return ['claude','-p',payload['request'],'--bare','--add-dir','/opt/evaluation','--model',payload['model'],'--effort',payload['effort'],'--output-format','stream-json','--verbose','--no-session-persistence','--permission-mode','bypassPermissions','--max-turns',str(payload['max_turns']),'--max-budget-usd',str(payload['max_budget_usd']),'--tools',','.join(payload['tools'])]


def main():
    payload=json.load(sys.stdin);env=os.environ.copy();env.pop('CLAUDE_CODE_EFFORT_LEVEL',None)
    for key in ('HOME','CLAUDE_CONFIG_DIR','CARGO_HOME','CARGO_TARGET_DIR','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_DATA_HOME','XDG_STATE_HOME'):
        Path(env[key]).mkdir(parents=True,exist_ok=True)
    env.update(CLAUDE_CODE_ENABLE_TELEMETRY='1',OTEL_LOGS_EXPORTER='otlp',OTEL_METRICS_EXPORTER='none',OTEL_EXPORTER_OTLP_PROTOCOL='http/protobuf',OTEL_EXPORTER_OTLP_ENDPOINT='http://127.0.0.1:4318',OTEL_LOGS_EXPORT_INTERVAL='100',NO_PROXY='127.0.0.1,localhost',no_proxy='127.0.0.1,localhost',CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
    telemetry=Path('/tmp/otel/events.jsonl');telemetry.parent.mkdir(parents=True,exist_ok=True)
    collector=subprocess.Popen(['otelcol-contrib','--config=/opt/host/otel.yaml'],stdout=sys.stderr,stderr=sys.stderr)
    try:
        import socket
        deadline=time.monotonic()+10
        while True:
            try:
                with socket.create_connection(('127.0.0.1',4318),timeout=.2):break
            except OSError:
                if time.monotonic()>deadline:raise RuntimeError('Local collector not ready')
                time.sleep(.05)
        version=subprocess.check_output(['claude','--version'],text=True,env=env).strip()
        converter=Converter(payload,version,skill_index(SKILL_PATH,exclude_root='/work/fixture'))
        proc=subprocess.Popen(command(payload),stdout=subprocess.PIPE,stderr=sys.stderr,text=True,env=env,cwd='/work/fixture')
        for line in proc.stdout:
            sys.stderr.write('CLAUDE_STREAM '+line);sys.stderr.flush()
            try:
                for event in converter.feed(json.loads(line)):print(json.dumps(event),flush=True)
            except (ValueError,KeyError,TypeError):converter.invalid=True
        code=proc.wait()
        collector.terminate();collector.wait(timeout=10)
        print(json.dumps(converter.finish(telemetry_requests(telemetry),code)),flush=True)
        return code
    finally:
        if collector.poll() is None:collector.kill();collector.wait()

if __name__=='__main__':sys.exit(main())
