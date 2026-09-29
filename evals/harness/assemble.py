"""Join frozen adjudicated scores to a sealed mapping only after verifying both hashes."""
import argparse
import csv
from pathlib import Path
from common import read, sha, CASES, SETTINGS, SECONDARY


def assemble(manifest, mapping_path, annotations_path, output):
    if sha(Path(mapping_path).read_bytes())!=manifest['mapping']['sha256']:
        raise ValueError('Mapping hash mismatch')
    if sha(Path(annotations_path).read_bytes())!=manifest['annotations']['frozen_sha256']:
        raise ValueError('Frozen annotation hash mismatch')
    mapping=read(mapping_path)['sessions'];scores=read(annotations_path)['scores']
    for rows,key in ((mapping,'id'),(scores,'session_id')):
        if len({r[key] for r in rows})!=len(rows): raise ValueError('Duplicate session')
        if len(rows)!=144: raise ValueError('Exactly 144 sessions required')
    by_id={r['session_id']:r for r in scores}
    if set(by_id)!={r['id'] for r in mapping}: raise ValueError('Missing or unexpected session')
    for s in scores:
        if type(s.get('completion')) is not bool or s.get('status') not in ('SCORED','SCORED_FAILURE'):
            raise ValueError('Unscored or unresolved session')
    strata={}
    primary=[];secondary=[]
    for s in mapping:
        key=(s['setting'],s['case'],s['arm'])
        if key[0] not in SETTINGS or key[1] not in CASES or key[2] not in ('baseline','candidate'): raise ValueError('Unknown stratum')
        strata[key]=strata.get(key,0)+1
        score=by_id[s['id']]
        if score.get('case')!=s['case']: raise ValueError('Case mismatch')
        primary.append([s['id'],*key,int(score['completion'])])
        for criterion in SECONDARY:
            v=score.get('secondary',{}).get(criterion)
            if v is None: continue
            if type(v) is not bool: raise ValueError('Invalid secondary value')
            secondary.append([s['id'],*key,criterion,int(v)])
    if len(strata)!=48 or any(n!=3 for n in strata.values()): raise ValueError('Invalid stratum sizes')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    for name,header,rows in [('primary.csv',['session_id','setting','case','arm','completion'],primary),('secondary.csv',['session_id','setting','case','arm','criterion','value'],secondary)]:
        with (output/name).open('x',newline='') as f:
            w=csv.writer(f);w.writerow(header);w.writerows(rows)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('mapping');p.add_argument('annotations');p.add_argument('output');a=p.parse_args()
    assemble(read(a.manifest),a.mapping,a.annotations,a.output)
