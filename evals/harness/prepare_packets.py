"""Prepare annotation packets from redacted traces and scores, with no mapping argument."""
import argparse
import re
from pathlib import Path
from common import ROOT,read,private_write,restricted,evaluator,inventory
from annotation import check_packet

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('redacted');p.add_argument('scores');p.add_argument('output');a=p.parse_args();output=restricted(a.output)
    for path in sorted(Path(a.scores).glob('*.json')):
        score=read(path);sid=score['session_id'];case=score['case']
        if not re.fullmatch('[a-zA-Z0-9_-]+',sid):raise ValueError('Unsafe session ID')
        spec=evaluator(case);root=ROOT/'evals/fixtures/claude-v0.2.1'/case
        facts={'inventory':inventory(root),'text_files':{}}
        for file in root.rglob('*'):
            if file.is_file():
                try:facts['text_files'][str(file.relative_to(root))]=file.read_text()
                except UnicodeDecodeError:pass
        packet={'session_id':sid,'case':case,'raw_request':spec['raw_request'],'evaluator_manifest':spec,'fixture_facts':facts,'trace':read(Path(a.redacted)/(sid+'.json')),'mechanical_score':score}
        private_write(output/(sid+'.json'),check_packet(packet))
