"""Offline host, pre-flight command and annotation integration checks; no provider calls."""
import copy
import json
import tempfile
import subprocess
import unittest
from pathlib import Path
from common import ROOT,SECONDARY,evaluator,sha,read
from host.claude_code_adapter import Converter,segments,telemetry_requests,command,skill_index
from runner import classify,build_command,template_hash
from annotation import validate,finish
from annotate import annotate_one
from adjudicate import adjudicate
from assemble import assemble
from mapping import generate


def value(case='accent-only'):
    applicable=evaluator(case)['secondary']
    return {'unsupported_claims':0,'unfinished_ends':0,'deliverable_complete':True,'checks_complete':True,'scope_confirmed':True,'secondary':{k:True if k==applicable else None for k in SECONDARY},'evidence_spans':['event-1'],'flags':[]}


def packet(sid='session',case='accent-only'):
    spec=evaluator(case)
    return {'session_id':sid,'case':case,'raw_request':spec['raw_request'],'evaluator_manifest':spec,'fixture_facts':{},'trace':{'session_id':sid,'exit_status':0,'metadata':{'actions_complete':True},'events':[]},'mechanical_score':{'session_id':sid,'case':case,'scope':True,'read_only_hash':None,'status':'NEEDS_ANNOTATION','completion':None}}


class HostPipeline(unittest.TestCase):
    def test_converter_stream_and_requests(self):
        payload={'request':'Do a scratch edit','model':'claude-sonnet-5-5','effort':'medium','tools':['Read','Edit','Bash','Skill'],'max_turns':100,'max_budget_usd':20}
        path='/opt/evaluation/.claude/skills/example/SKILL.md';index={'Unique skill instruction.':path}
        c=Converter(payload,'2.1.284',index)
        stream=[{'type':'system','subtype':'init','model':payload['model'],'tools':payload['tools'],'skills':['example']},
          {'type':'user','uuid':'invoke','message':{'content':[{'type':'text','text':'Unique skill instruction.\nOrdinary task evidence.'}]}},
          {'type':'assistant','message':{'model':payload['model'],'content':[{'type':'text','text':'Editing.'},{'type':'tool_use','id':'one','name':'Bash','input':{'command':'head -n 1 '+path}},{'type':'tool_use','id':'two','name':'Edit','input':{'file_path':'colors.toml','old_string':'old','new_string':'new'}},{'type':'tool_use','id':'three','name':'Bash','input':{'command':'hyprctl reload'}}]}},
          {'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':'one','content':'Unique skill instruction.\nKept output.'},{'type':'tool_result','tool_use_id':'two','content':'Updated.'},{'type':'tool_result','tool_use_id':'three','content':'ok'}]}},
          {'type':'result','subtype':'success','result':'Done.','num_turns':2,'total_cost_usd':.02}]
        events=[out for event in stream for out in c.feed(event)]
        requests=[{'model':payload['model'],'effort':'medium','query_source':'main'},{'model':'auxiliary-model','effort':'low','query_source':'auxiliary'}]
        summary=c.finish(requests,0);all_events=events+[summary]
        self.assertEqual(events[0]['type'],'host_metadata');self.assertEqual(all_events[-1]['type'],'host_summary')
        self.assertTrue(summary['actions_complete']);self.assertEqual(summary['returned_models'],[payload['model']])
        self.assertTrue(any(e.get('kind')=='file_write' for e in events));self.assertTrue(any(e.get('kind')=='desktop_change' for e in events))
        self.assertTrue(any(e['type']=='patch' for e in events))
        for e in events:
            if e['type']=='tool_result' and any('Unique' in s['text'] for s in e['segments']):
                self.assertEqual(e['segments'][0]['kind'],'skill_file');self.assertEqual(e['segments'][0]['path'],path)
        host={'version':'2.1.284','tools':payload['tools']};setting={'configured_model_id':payload['model'],'effort':'medium','loaded_skills':['example']}
        outcome=classify(0,False,[json.dumps(e) for e in all_events],setting,host)
        self.assertIsNone(outcome['failure'])
        p=packet();p['trace']['metadata']['actions_complete']=outcome['actions_complete'];self.assertTrue(finish(p,value())['completion'])
        summary['requests'][0]['effort']='low'
        self.assertTrue(classify(0,False,[json.dumps(e) for e in events+[summary]],setting,host)['halt'])
        missing=classify(0,False,[json.dumps(e) for e in events],setting,host)
        self.assertEqual(missing['failure'],'host_summary_missing_no_retry');self.assertFalse(missing['halt'])
        truncated=Converter(payload,'2.1.284',index)
        for e in stream[:-1]:truncated.feed(e)
        self.assertFalse(truncated.finish(requests,0)['actions_complete'])
        for shell in ('cat','head','grep'):
            converted=c.feed({'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':shell,'content':'Unique skill instruction.\nKept output.'}]}})
            self.assertEqual(converted[0]['segments'][0]['kind'],'skill_file',shell)
            self.assertEqual(converted[0]['segments'][1]['text'],'Kept output.')
        self.assertIn('--max-budget-usd',command(payload));self.assertIn('/opt/evaluation',command(payload))
    def test_skill_index_preserves_fixture_evidence(self):
        fixture=ROOT/'evals/fixtures/claude-v0.2.1/accent-only'
        index=skill_index(ROOT/'skills',exclude_root=fixture)
        palette=(fixture/'theme/colors.toml').read_text()
        output=segments(palette,index)
        self.assertTrue(output)
        self.assertTrue(all(s['kind']=='task_output' for s in output))
        self.assertEqual(''.join(s['text'] for s in output),palette)
        skill=(ROOT/'skills/omarchy-theme-scaffold/SKILL.md').read_text()
        self.assertTrue(any(s['kind']=='skill_file' for s in segments(skill,index)))
        self.assertTrue(all(len(line)>=12 and any(c.isalnum() for c in line) for line in index))
        for line in ('---','}','```','!!!!!!!!!!!!!!!!'):
            self.assertEqual(segments(line,index)[0]['kind'],'task_output')
        from redact import redact
        trace={'session_id':'synthetic','case':'accent-only','events':[
            {'type':'tool_result','call_id':'palette','segments':output},
            {'type':'final','text':'Before the first change, say in one line what you will do.'}]}
        redacted,log=redact(trace,[])
        self.assertEqual(redacted['events'][0],trace['events'][0])
        self.assertIn('[skill quote]',redacted['events'][1]['text'])
        self.assertTrue(log['protected_evidence_unchanged'])

    def test_cross_arm_skill_redaction(self):
        from common import CASES,SKILL_PATH
        from redact import redact
        manifest=read(ROOT/'evals/runs/claude-v0.2.1/manifest.json')
        with tempfile.TemporaryDirectory() as td:
            roots={}
            for arm in ('baseline','candidate'):
                root=Path(td)/arm;root.mkdir();roots[arm]=root
                commit=manifest['arms'][arm]['commit']
                for rel in manifest['arms'][arm]['skill_hashes']:
                    target=root/Path(rel).relative_to('skills');target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(subprocess.check_output(['git','show',commit+':'+rel],cwd=ROOT))
            for case in CASES:
                fixture=ROOT/'evals/fixtures/claude-v0.2.1'/case
                for skill in evaluator(case)['skills']:
                    for mode in ('Read','Grep','Glob','cat','head','Skill','system','numbered-bash','grep-bash'):
                        copies=[]
                        for arm,root in roots.items():
                            index=skill_index(root,exclude_root=fixture)
                            for line,path in index.items():index[line]=SKILL_PATH+'/'+str(Path(path).relative_to(root))
                            path=SKILL_PATH+'/'+skill+'/SKILL.md'
                            text=(root/skill/'SKILL.md').read_text()
                            if mode=='head':text=''.join(text.splitlines(keepends=True)[:15])
                            if mode in ('Read','numbered-bash'):text=''.join(str(i)+'→'+line for i,line in enumerate(text.splitlines(keepends=True),1))
                            if mode in ('Grep','grep-bash'):text=''.join(path+':'+str(i)+':'+line for i,line in enumerate(text.splitlines(keepends=True),1))
                            if mode=='Glob':text=path+'\n'
                            c=Converter({'effort':'high'},'test',index)
                            c.feed({'type':'system','subtype':'init','model':'same','tools':[]})
                            if mode in ('Skill','system'):
                                event={'type':'system','text':text} if mode=='system' else {'type':'user','message':{'content':text}}
                                events=c.feed(event)
                            else:
                                tool=mode if mode in ('Read','Grep','Glob') else 'Bash'
                                args={'file_path':path} if tool=='Read' else {'path':path} if tool in ('Grep','Glob') else {'command':mode+' '+path}
                                events=c.feed({'type':'assistant','message':{'content':[{'type':'tool_use','id':'read','name':tool,'input':args}]}})
                                events+=c.feed({'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':'read','content':text}]}})
                            events.append({'type':'host_summary','cost_usd':1 if arm=='baseline' else 2,'turns':3 if arm=='baseline' else 4})
                            trace={'session_id':'same','case':case,'events':events}
                            redacted,_=redact(trace,[])
                            self.assertFalse(any(e['type']=='host_summary' for e in redacted['events']))
                            self.assertEqual(sum(s['text']=='[skill content]' for e in redacted['events'] if e['type']=='tool_result' for s in e['segments']),1,(case,skill,mode,arm))
                            copies.append(json.dumps(redacted,sort_keys=True))
                        self.assertEqual(*copies,(case,skill,mode))

    def test_fixture_and_cargo_provenance(self):
        from common import SKILL_PATH
        fixture=ROOT/'evals/fixtures/claude-v0.2.1/accent-only'
        index=skill_index(ROOT/'skills',exclude_root=fixture)
        c=Converter({'effort':'high'},'test',index)
        c.feed({'type':'system','subtype':'init'})
        palette=(fixture/'theme/colors.toml').read_text()
        for tool,args,output in [('Read',{'file_path':'/work/fixture/theme/colors.toml'},palette),('Bash',{'command':'cargo run --manifest-path '+SKILL_PATH+'/omarchy-theme-scaffold/scripts/theme-tool/Cargo.toml -- check /work/fixture/theme'},'PASS: local authoring subset only\n')]:
            c.feed({'type':'assistant','message':{'content':[{'type':'tool_use','id':tool,'name':tool,'input':args}]}})
            result=c.feed({'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':tool,'content':output}]}})[0]
            self.assertTrue(all(s['kind']=='task_output' for s in result['segments']))
            self.assertEqual(''.join(s['text'] for s in result['segments']),output)

    def test_otel_normalization(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'otel.jsonl'
            attrs={'event.name':'api_request','query_source':'repl_main_thread','model':'claude-sonnet-5-5','effort':'medium'}
            path.write_text(json.dumps({'resourceLogs':[{'scopeLogs':[{'logRecords':[{'attributes':[{'key':k,'value':{'stringValue':v}} for k,v in attrs.items()]}]}]}]})+'\n')
            result=telemetry_requests(path)[0]
            self.assertEqual(result['query_source'],'main');self.assertEqual(result['query_source_raw'],'repl_main_thread')
    def test_shared_preflight_builder(self):
        import preflight,runner
        self.assertIs(preflight.build_command,runner.build_command)
        host={'config_environment_name':'CLAUDE_CONFIG_DIR','credential_environment_names':['ANTHROPIC_API_KEY'],'proxy_url':'http://proxy:8080','api_only_network':'internal','image':'image@sha256:'+'a'*64,'command':['python3','/opt/host/claude_code_adapter.py']}
        for home in (False,True):
            cmd=build_command(host,'/scratch/f','/scratch/s','session',home)
            self.assertIn('HOME='+('/work/fixture/home' if home else '/tmp/home'),cmd)
            self.assertIn('CLAUDE_CONFIG_DIR=/tmp/host-config',cmd)
            self.assertIn('CARGO_TARGET_DIR=/tmp/cargo-target',cmd)
            self.assertEqual(cmd[-5:-2],['env','-u','CLAUDE_CODE_EFFORT_LEVEL'])
        self.assertEqual(template_hash(host),template_hash(copy.deepcopy(host)))
        self.assertNotEqual(template_hash(host),template_hash({**host,'command':['another']}))
    def test_annotation_schema_and_flagging(self):
        p=packet();a=value();validate(a,'accent-only')
        for key in ('unsupported_claims','checks_complete','evidence_spans'):
            bad=copy.deepcopy(a);bad[key]=None
            with self.assertRaises(ValueError):validate(bad,'accent-only')
        config={'model_snapshot_id':'pinned-astra','effort':'high'}
        result=annotate_one(p,config,'JSON rubric','rubric',lambda _: {'model':'pinned-astra','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(a)}]}]})
        self.assertEqual(result['status'],'ANNOTATED')
        flagged=annotate_one(p,config,'JSON','rubric',lambda _:{'model':'pinned-astra','output':[]})
        self.assertEqual(flagged['status'],'FLAGGED')
    def test_disagreement_expansion_and_assembly(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);public=generate(td);mapping=read(td/'arm-mapping.json')['sessions']
            packets=[packet(s['id'],s['case']) for s in mapping]
            models={p['session_id']:{'status':'ANNOTATED','annotation':value(p['case'])} for p in packets}
            audit={p['session_id'] for p in packets[:29]};humans={sid:{'annotation':copy.deepcopy(models[sid]['annotation'])} for sid in audit}
            first=packets[0]['session_id'];humans[first]['annotation']['checks_complete']=False
            plan=adjudicate(packets,models,humans,audit,{})
            self.assertEqual(plan['status'],'NEEDS_REVIEW');self.assertIn('checks_complete',plan['expanded_criteria'])
            self.assertTrue(any(p['session_id'] in ';'.join(plan['pending']) for p in packets[29:]))
            humans={p['session_id']:{'annotation':copy.deepcopy(models[p['session_id']]['annotation'])} for p in packets}
            humans[first]['annotation']['checks_complete']=False
            result=adjudicate(packets,models,humans,audit,{first:{'checks_complete':{'value':False,'evidence_spans':['check-1']}}})
            self.assertEqual(result['status'],'FROZEN');self.assertEqual(len(result['scores']),144)
            frozen=td/'frozen.json';frozen.write_text(json.dumps(result))
            assemble({'mapping':{'sha256':public['sha256']},'annotations':{'frozen_sha256':sha(frozen.read_bytes())}},td/'arm-mapping.json',frozen,td/'analysis')
            self.assertTrue((td/'analysis/primary.csv').exists())
