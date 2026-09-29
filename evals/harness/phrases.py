"""Generate case-specific six-word arm differences, excluding raw-request/fixture evidence."""
import argparse
import subprocess
from common import ROOT, CASES, evaluator, read, write, sha


def windows(text):
    words=text.casefold().split()
    return {' '.join(words[i:i+6]) for i in range(len(words)-5)}


def generate(baseline,candidate):
    result={}
    for case in CASES:
        spec=evaluator(case);arm_text=[]
        for commit in (baseline,candidate):
            text=[]
            for skill in spec['skills']:
                paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'--','skills/'+skill+'/'],cwd=ROOT,text=True).splitlines()
                for path in paths:
                    data=subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
                    try: text.append(data.decode('utf-8'))
                    except UnicodeDecodeError: pass
            arm_text.append(set().union(*(windows(t) for t in text)))
        excluded=windows(spec['raw_request'])
        for p in (ROOT/'evals/fixtures/claude-v0.2.1'/case).rglob('*'):
            if p.is_file(): excluded.update(windows(p.read_text(errors='replace')))
        result[case]=sorted((arm_text[0]^arm_text[1])-excluded)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline');p.add_argument('candidate');p.add_argument('output');a=p.parse_args()
    write(a.output,{'cases':generate(a.baseline,a.candidate)},exclusive=True)
