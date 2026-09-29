"""Synthetic records only. Imports only pure runner helpers; never contacts any model/provider."""
import copy
import csv
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from common import ROOT, SKILL_PATH, SETTINGS, CASES, inventory, read, sha
from redact import redact
from score import score
from mapping import generate
from audit import select


def transcript():
    return {'case':'accent-only','session_id':'synthetic-001','metadata':{'arm':'candidate','skill_commit':'secret-sha','actions_complete':True},'exit_status':0,'events':[{'type':'tool_call','id':'1','name':'read','arguments':{'path':SKILL_PATH+'/example/SKILL.md'}},{'type':'tool_result','call_id':'1','segments':[{'kind':'skill_file','path':SKILL_PATH+'/example/SKILL.md','text':'sets scope and deliverable'},{'kind':'task_output','text':'accent measured; command output preserved'}]},{'type':'assistant','text':'BEFORE the first\nchange, say in one line: editing accent.'},{'type':'patch','text':'-accent old\n+accent new'},{'type':'final','text':'Changed accent.'}]}


def annotation(secondary=None):
    return {'unsupported_claims':0,'unfinished_ends':0,'deliverable_complete':True,'checks_complete':True,'scope_confirmed':True,'secondary':secondary or {},'evidence_spans':['synthetic-final','synthetic-tool-result']}

class Pipeline(unittest.TestCase):
    def test_redaction_preserves_evidence_and_case_whitespace(self):
        t=transcript();r,log=redact(t,['secret-sha'])
        self.assertEqual(r['events'][0],t['events'][0]);self.assertEqual(r['events'][3],t['events'][3])
        self.assertEqual(r['events'][1]['segments'][1],t['events'][1]['segments'][1])
        self.assertIn('[skill file:',r['events'][1]['segments'][0]['text'])
        self.assertIn('[skill quote]',r['events'][2]['text']);self.assertNotIn('arm',r['metadata'])
        self.assertEqual(log['counts']['skill_quote'],1);self.assertTrue(log['protected_evidence_unchanged'])
        self.assertEqual(log['blinding'],'partial')
    def test_redaction_flags_unsafe_edges(self):
        for mutation in ('unsegmented','task_marked_skill','leaked_sha','phrase_in_command'):
            t=transcript()
            if mutation=='unsegmented':del t['events'][1]['segments']
            elif mutation=='task_marked_skill':t['events'][1]['segments'][0]['path']='/work/fixture/colors.toml'
            elif mutation=='leaked_sha':t['events'][-1]['text']='secret-sha'
            else:t['events'][0]['arguments']['command']='echo Keep a narrow change narrow. Add'
            with self.assertRaises(ValueError):redact(t,['secret-sha'])
    def case(self,name,mutate,ann):
        with tempfile.TemporaryDirectory() as td:
            before=Path(td)/'before';after=Path(td)/'after'
            shutil.copytree(ROOT/'evals/fixtures/claude-v0.2.1'/name,before);shutil.copytree(before,after)
            mutate(after)
            return score(name,before,after,transcript(),ann)
    @staticmethod
    def accent(p):
        f=p/'theme/colors.toml';f.write_bytes(f.read_bytes().replace(b'accent = "#9bbf94"',b'accent = "#80bfa0"'))
    def test_pass_and_unsupported_claim(self):
        self.assertTrue(self.case('accent-only',self.accent,annotation())['completion'])
        a=annotation();a['unsupported_claims']=1
        self.assertFalse(self.case('accent-only',self.accent,a)['completion'])
    def test_readonly_and_added_test(self):
        def test_added(p):
            self.accent(p);(p/'test_new.py').write_text('def test_new(): pass\n')
        s=self.case('accent-only',test_added,annotation())
        self.assertFalse(s['scope']);self.assertEqual(s['tests_added']['new_files'],1)
        def mutate(p):(p/'extra.txt').write_text('unexpected')
        s=self.case('diagnose-staging',mutate,annotation())
        self.assertFalse(s['completion']);self.assertFalse(s['read_only_hash'])
    def test_modes_secondary_and_pending(self):
        s=self.case('ideas-only',lambda p:None,annotation({'closest_builtin_comparison':False}))
        self.assertTrue(s['completion']);self.assertIsNone(s['secondary']['override_named_before_edit'])
        self.assertIsNone(self.case('accent-only',self.accent,None)['completion'])
        def badmode(p):self.accent(p);(p/'theme/colors.toml').chmod(0o755)
        self.assertFalse(self.case('accent-only',badmode,annotation())['scope'])
    def test_override_report_only_and_ineffective_edit(self):
        a=annotation({'override_named_before_edit':False})
        self.assertTrue(self.case('override-present',lambda p:None,a)['completion'])
        self.assertFalse(self.case('override-present',self.accent,a)['completion'])
    def test_mapping_and_audit_synthetic_only(self):
        with tempfile.TemporaryDirectory() as td:
            public=generate(td);sealed=read(Path(td)/'arm-mapping.json')
            self.assertEqual(len(public['session_ids']),144)
            self.assertEqual(public['sha256'],sha((Path(td)/'arm-mapping.json').read_bytes()))
            for case in CASES:
                for setting in SETTINGS:
                    rows=[s for s in sealed['sessions'] if s['case']==case and s['setting']==setting]
                    self.assertEqual(sum(s['arm']=='baseline' for s in rows),3)
                    self.assertEqual(sum(s['arm']=='candidate' for s in rows),3)
            self.assertEqual(len(select(public['session_ids'])['session_ids']),29)
            self.assertEqual(select(public['session_ids']),select(public['session_ids']))
    def test_unconfigured_run_is_blocked(self):
        from readiness import errors
        from runner import run
        self.assertTrue(errors({}))
        with tempfile.TemporaryDirectory() as td:
            manifest=Path(td)/'manifest.json';manifest.write_text('{}')
            with self.assertRaisesRegex(ValueError,'Readiness not frozen'):
                run(manifest,Path(td)/'missing-mapping',Path(td)/'records')
            self.assertFalse((Path(td)/'records').exists())
    def test_fixture_manifests_and_mirror(self):
        for case in CASES:
            self.assertEqual(read(ROOT/f'evals/fixture-manifests/claude-v0.2.1/{case}.json')['files'],inventory(ROOT/f'evals/fixtures/claude-v0.2.1/{case}'))
        h='| Case | Raw request | Fixture and expected deliverable |\n| --- | --- | --- |\n'
        self.assertEqual((ROOT/'evals/README.md').read_text().split(h)[1].split('\n\n')[0],(ROOT/'evals/claude-v0.2.1.md').read_text().split(h)[1].split('\n\n')[0])
    def test_fixture_leak_scan_and_upstream_hashes(self):
        import re,hashlib
        for case in CASES:
            root=ROOT/'evals/fixtures/claude-v0.2.1'/case
            manifest=read(ROOT/f'evals/fixture-manifests/claude-v0.2.1/{case}.json')
            for p in root.rglob('*'):
                if not p.is_file(): continue
                self.assertNotEqual(p.name,'provenance.json')
                rel=p.relative_to(root).as_posix()
                if rel.startswith('sources/'):
                    entry=manifest['upstream_sources'][rel]
                    self.assertEqual(sha(p.read_bytes()),entry['sha256'])
                    full=root/entry['full_file'];data=full.read_bytes()
                    self.assertEqual(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),entry['upstream_blob'])
                    if rel!=entry['full_file']:
                        parts=re.split(r'^# Source: .*?, lines (\d+)-(\d+)\n',p.read_text(),flags=re.M)
                        self.assertEqual(parts[0],'')
                        for i in range(1,len(parts),3):
                            self.assertEqual(parts[i+2],''.join(data.decode().splitlines(True)[int(parts[i])-1:int(parts[i+1])]))
                else:
                    self.assertIsNone(re.search(r'\b(evaluation|evaluator|fixture|synthetic|benchmark|protocol|Claude)\b',p.read_text(errors='replace'),re.I),rel)
    def test_outcomes_failure_scores_and_resume(self):
        from runner import classify,prepare_execution
        setting={'returned_model_id':'claude-example','effort':'medium'}
        host={'version':'host-1','tools':['read']}
        first={'type':'host_metadata','model_id':'claude-example','effort':'medium','host_version':'host-1','tools':['read']}
        lines=[json.dumps(first)]
        timeout=classify(124,True,lines,setting,host)
        self.assertFalse(timeout['halt']);self.assertEqual(timeout['failure'],'host_timeout_no_retry')
        t={**transcript(),**timeout}
        self.assertEqual(score('accent-only',None,None,t)['status'],'SCORED_FAILURE')
        self.assertFalse(score('accent-only',None,None,t)['completion'])
        self.assertEqual(classify(2,False,lines,setting,host)['failure'],'host_exit_nonzero_no_retry')
        for raw in ([],[json.dumps({'type':'assistant'})]):
            out=classify(124,True,raw,setting,host)
            self.assertTrue(out['halt']);self.assertEqual(out['failure'],'host_metadata_missing')
        wrong={**first,'effort':'low'};out=classify(0,False,[json.dumps(wrong)],setting,host)
        self.assertTrue(out['halt']);self.assertEqual(out['failure'],'host_settings_mismatch')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);sessions=[{'id':'done'},{'id':'interrupted'},{'id':'new'}]
            prepare_execution(root,'a'*64,sessions)
            (root/'done').mkdir();(root/'done/record.json').write_text('{}')
            (root/'interrupted').mkdir()
            skipped=prepare_execution(root,'a'*64,sessions,True)
            self.assertEqual(skipped,{'done','interrupted'})
            trace=read(root/'interrupted/trace.json')
            self.assertEqual(trace['failure'],'interrupted_no_retry')
            self.assertFalse(score('accent-only',None,None,trace)['completion'])
            self.assertEqual(len((root/'execution-log.jsonl').read_text().splitlines()),1)
            with self.assertRaisesRegex(ValueError,'Resume manifest mismatch'):
                prepare_execution(root,'b'*64,sessions,True)
    def test_assembly(self):
        from assemble import assemble
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);public=generate(td);mapping=td/'arm-mapping.json';sessions=read(mapping)['sessions']
            scores=[{'session_id':r['id'],'case':r['case'],'completion':True,'status':'SCORED','secondary':{'closest_builtin_comparison':True if r['case']=='ideas-only' else None}} for r in sessions]
            annotations=td/'annotations.json'
            def execute(rows,wrong=False):
                annotations.write_text(json.dumps({'scores':rows}))
                manifest={'mapping':{'sha256':'0'*64 if wrong else public['sha256']},'annotations':{'frozen_sha256':sha(annotations.read_bytes())}}
                assemble(manifest,mapping,annotations,td/'out')
            with self.assertRaisesRegex(ValueError,'Mapping hash mismatch'):execute(scores,True)
            with self.assertRaisesRegex(ValueError,'Duplicate session'):execute(scores[:-1]+[scores[0]])
            with self.assertRaisesRegex(ValueError,'Exactly 144'):execute(scores[:-1])
            with self.assertRaisesRegex(ValueError,'Unscored'):execute([{**scores[0],'completion':None,'status':'NEEDS_ANNOTATION'}]+scores[1:])
            execute(scores)
            self.assertEqual(len(list(csv.DictReader((td/'out/primary.csv').read_text().splitlines()))),144)
            self.assertEqual(len(list(csv.DictReader((td/'out/secondary.csv').read_text().splitlines()))),24)
            with self.assertRaises(FileExistsError):execute(scores)
    def test_case_body_phrase_redaction(self):
        t=transcript();t['case']='ideas-only';t['events']=[{'type':'final','text':'This is closest to Tokyo Night'}]
        result,_=redact(t,[]);self.assertEqual(result['events'],t['events'])
        t['events']=[{'type':'final','text':'Name the built-in theme this palette'}]
        result,_=redact(t,[]);self.assertIn('[skill quote]',result['events'][0]['text'])
    def test_readiness_field_validation(self):
        from readiness import errors
        base=read(ROOT/'evals/runs/claude-v0.2.1/manifest.json')
        base['host'].update(verified=True,image='host@sha256:'+'a'*64,network_isolation_verified=True,command=['host'],tools=['read'],credential_environment_names=['API_KEY'],api_only_network='provider-only',version='1.0',config_environment_name='HOST_CONFIG',skill_content_all_channels=True,preflight={'no_write_home':True,'no_write_no_home':True,'helper_build':True,'evidence_sha256':'a'*64})
        base['limits']={'seconds':30,'tokens':1000}
        for v in base['settings'].values():v.update(verified=True,returned_model_id='claude-example',host_reported_effort=v['effort'],evidence_sha256='a'*64)
        mutations=[(('settings','fable-high','evidence_sha256'),'BLOCKED: missing','host effort evidence invalid: fable-high'),(('settings','fable-high','host_reported_effort'),'low','host reported effort mismatch: fable-high')]
        for field in ('command','tools','credential_environment_names'):
            for bad in ('host',[],['']):mutations.append((('host',field),bad,'host '+field+' must be a nonempty string list'))
        for field in ('api_only_network','version','config_environment_name'):
            mutations.append((('host',field),'','host '+field+' must be a nonempty observed string'))
        for field in ('seconds','tokens'):
            for bad in (0,-1,'30',True):mutations.append((('limits',field),bad,'limits '+field+' must be a positive integer'))
        for field in ('no_write_home','no_write_no_home','helper_build'):
            mutations.append((('host','preflight',field),False,'host preflight '+field+' not passed'))
        mutations.append((('host','preflight','evidence_sha256'),'BLOCKED: missing','host preflight evidence invalid'))
        for path,value,message in mutations:
            with self.subTest(path=path,value=value):
                m=copy.deepcopy(base);obj=m
                for k in path[:-1]:obj=obj[k]
                obj[path[-1]]=value
                self.assertIn(message,errors(m,through=5))
        m=copy.deepcopy(base);m['extra']={'nested':['BLOCKED: hidden'],'verified':False}
        issues=errors(m)
        self.assertIn('unresolved BLOCKED value: manifest.extra.nested[0]',issues)
        self.assertIn('verified must be true: manifest.extra.verified',issues)
    @unittest.skipUnless(shutil.which('Rscript') or __import__('os').environ.get('CI'),'Rscript unavailable; R checks are mandatory in CI')
    def test_R_synthetic_analysis(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);data=td/'scores.csv'
            with data.open('w') as f:
                w=csv.writer(f);w.writerow(['session_id','setting','case','arm','completion'])
                for si,setting in enumerate(SETTINGS):
                    for ci,case in enumerate(CASES):
                        for arm in ('baseline','candidate'):
                            for rep in range(3):
                                value=int(arm=='candidate' or ci>=2)
                                w.writerow([f'synthetic-{si}-{ci}-{arm}-{rep}',setting,case,arm,value])
            subprocess.run(['Rscript',str(ROOT/'evals/harness/analysis.R'),str(data),str(td/'analysis')],check=True)
            print((td/'analysis/versions.txt').read_text(), flush=True)
            rows=list(csv.DictReader((td/'analysis/settings.csv').open()))
            self.assertEqual(len(rows),4)
            for row in rows:
                self.assertAlmostEqual(float(row['exact_p']),.005,places=10)
                self.assertAlmostEqual(float(row['holm_p']),.02,places=10)
                self.assertEqual(row['headline_eligible'],'TRUE')
            subprocess.run(['Rscript',str(ROOT/'evals/harness/test_detectability.R')],check=True)

if __name__=='__main__':unittest.main()
