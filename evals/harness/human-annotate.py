"""Show redacted evidence only; model annotation is never displayed before the human saves."""
import argparse
import json
from pathlib import Path
from common import read,private_write,restricted,ROOT
from annotation import check_packet,validate,finish


def needs_human(packet,model,audit):
    if packet['session_id'] in audit or model.get('status')!='ANNOTATED':return True
    a=model['annotation']
    return bool(a['flags'] or not finish(packet,a)['completion'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('packets');p.add_argument('model_annotations');p.add_argument('output');p.add_argument('--expanded-review',help='adjudication plan listing criteria needing all-session human review');a=p.parse_args()
    m=read(a.manifest);audit=set(m['audit']['session_ids']);output=restricted(a.output)
    expanded=read(a.expanded_review)['expanded_criteria'] if a.expanded_review else []
    for path in sorted(Path(a.packets).glob('*.json')):
        packet=check_packet(read(path));sid=packet['session_id'];target=output/(sid+'.json')
        if target.exists():continue
        model=read(Path(a.model_annotations)/(sid+'.json'))
        if not expanded and not needs_human(packet,model,audit):continue
        print((ROOT/'evals/harness/annotator-prompt.md').read_text());print((ROOT/'evals/harness/rubric.md').read_text());print(json.dumps(packet,indent=2))
        if expanded:print('Review criteria across every session:',', '.join(expanded))
        while True:
            source=input('Path to your independently completed annotation JSON (blank exits): ').strip()
            if not source:return
            try:value=validate(read(source),packet['case'])
            except (OSError,ValueError) as error:print(error);continue
            private_write(target,{'session_id':sid,'annotator':'Tom Ballard','annotation':value});break

if __name__=='__main__':main()
