"""Synthetic records only. Does not import runner or contact any model/provider."""
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
    return {'session_id':'synthetic-001','metadata':{'arm':'candidate','skill_commit':'secret-sha','actions_complete':True},'exit_status':0,'events':[{'type':'tool_call','id':'1','name':'read','arguments':{'path':SKILL_PATH+'/example/SKILL.md'}},{'type':'tool_result','call_id':'1','segments':[{'kind':'skill_file','path':SKILL_PATH+'/example/SKILL.md','text':'sets scope and deliverable'},{'kind':'task_output','text':'accent measured; command output preserved'}]},{'type':'assistant','text':'BEFORE the first\nchange, say in one line: editing accent.'},{'type':'patch','text':'-accent old\n+accent new'},{'type':'final','text':'Changed accent.'}]}


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
            else:t['events'][0]['arguments']['command']='echo Keep a narrow change narrow'
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
    @unittest.skipUnless(shutil.which('Rscript'),'Rscript unavailable; R checks are mandatory in CI')
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
            rows=list(csv.DictReader((td/'analysis/settings.csv').open()))
            self.assertEqual(len(rows),4)
            for row in rows:
                self.assertAlmostEqual(float(row['exact_p']),.005,places=10)
                self.assertAlmostEqual(float(row['holm_p']),.02,places=10)
                self.assertEqual(row['headline_eligible'],'TRUE')
            subprocess.run(['Rscript',str(ROOT/'evals/harness/test_detectability.R')],check=True)

if __name__=='__main__':unittest.main()
