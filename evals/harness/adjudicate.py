"""Expand disagreements by criterion, retain originals, and freeze only resolved scores."""
import argparse
import copy
from pathlib import Path
from common import read,write,sha
from annotation import validate,criterion_values,finish,check_packet


def adjudicate(packets,models,humans,audit,resolutions):
    if len(packets)!=144 or len({p['session_id'] for p in packets})!=144:raise ValueError('144 unique packets required')
    expanded=set();pending=[]
    for p in packets:
        check_packet(p);sid=p['session_id'];model=models[sid];human=humans.get(sid)
        if model.get('status')=='ANNOTATED':validate(model['annotation'],p['case'])
        if human:
            validate(human['annotation'],p['case'])
            if model.get('status')=='ANNOTATED':
                left=criterion_values(model['annotation']);right=criterion_values(human['annotation'])
                expanded.update(k for k in left if left[k]!=right[k])
    scores=[];decisions=[]
    for p in packets:
        sid=p['session_id'];model=models[sid];human=humans.get(sid)
        failed=model.get('status')!='ANNOTATED'
        if not failed:failed=bool(model['annotation']['flags'] or not finish(p,model['annotation'])['completion'])
        if (sid in audit or failed or expanded) and not human:pending.append(sid+': independent human review required');continue
        chosen=copy.deepcopy(human['annotation'] if human else model['annotation'])
        if human and model.get('status')=='ANNOTATED':
            mv=criterion_values(model['annotation']);hv=criterion_values(human['annotation'])
            for key in mv:
                if mv[key]==hv[key]:continue
                resolution=resolutions.get(sid,{}).get(key)
                if not resolution or not resolution.get('evidence_spans'):pending.append(sid+': resolve '+key);continue
                if key.startswith('secondary.'):chosen['secondary'][key.split('.',1)[1]]=resolution['value']
                else:chosen[key]=resolution['value']
                decisions.append({'session_id':sid,'criterion':key,**resolution})
        if chosen['flags']:
            cleared=resolutions.get(sid,{}).get('flags')
            if not cleared or cleared.get('value')!=[] or not cleared.get('evidence_spans'):pending.append(sid+': unresolved flags')
            else:chosen['flags']=[];decisions.append({'session_id':sid,'criterion':'flags',**cleared})
        validate(chosen,p['case']);scores.append(finish(p,chosen))
    if pending:return {'status':'NEEDS_REVIEW','expanded_criteria':sorted(expanded),'pending':pending}
    if any(s['status'] not in ('SCORED','SCORED_FAILURE') for s in scores):raise ValueError('Unresolved mechanical score')
    return {'status':'FROZEN','scores':scores,'expanded_criteria':sorted(expanded),'resolutions':decisions,'model_originals':models,'human_originals':humans}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('packets');p.add_argument('model_annotations');p.add_argument('human_annotations');p.add_argument('resolutions');p.add_argument('output');a=p.parse_args()
    packets=[read(p) for p in sorted(Path(a.packets).glob('*.json'))]
    models={p.stem:read(p) for p in Path(a.model_annotations).glob('*.json')};humans={p.stem:read(p) for p in Path(a.human_annotations).glob('*.json')}
    result=adjudicate(packets,models,humans,set(read(a.manifest)['audit']['session_ids']),read(a.resolutions))
    write(a.output,result,exclusive=True)
    if result['status']=='FROZEN':write(a.output+'.sha256',{'frozen_sha256':sha(Path(a.output).read_bytes())},exclusive=True)
    else:raise SystemExit('Human review remains; see the exclusive review plan')

if __name__=='__main__':main()
