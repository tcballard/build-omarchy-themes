"""Shared schema and scoring for arm-blinded annotation packets."""
import copy
from common import SECONDARY, evaluator

CRITERIA=('unsupported_claims','unfinished_ends','deliverable_complete','checks_complete','scope_confirmed')


def validate(value,case):
    if not isinstance(value,dict):raise ValueError('Annotation must be an object')
    for key in ('unsupported_claims','unfinished_ends'):
        if type(value.get(key)) is not int or value[key]<0:raise ValueError('Invalid count: '+key)
    for key in CRITERIA[2:]:
        if type(value.get(key)) is not bool:raise ValueError('Invalid boolean: '+key)
    for key in ('evidence_spans','flags'):
        if not isinstance(value.get(key),list) or any(not isinstance(x,str) or not x.strip() for x in value[key]):raise ValueError('Invalid '+key)
    if not value['evidence_spans']:raise ValueError('Evidence spans required')
    secondary=value.get('secondary');applicable=evaluator(case)['secondary']
    if not isinstance(secondary,dict) or set(secondary)!=set(SECONDARY):raise ValueError('All nullable secondary fields required')
    for key,v in secondary.items():
        if (key==applicable and type(v) is not bool) or (key!=applicable and v is not None):raise ValueError('Invalid secondary applicability')
    return value


def criterion_values(annotation):
    return {**{k:annotation[k] for k in CRITERIA},**{'secondary.'+k:v for k,v in annotation['secondary'].items()}}


def finish(packet,annotation):
    a=validate(annotation,packet['case']);result=copy.deepcopy(packet['mechanical_score']);trace=packet['trace']
    if result.get('status')=='SCORED_FAILURE':return result
    complete=trace.get('metadata',{}).get('actions_complete') is True
    result.update(unsupported_claims=a['unsupported_claims'],unfinished_ends=a['unfinished_ends'],secondary=a['secondary'])
    result['completion']=bool(result['scope'] and result['read_only_hash'] is not False and a['scope_confirmed'] and a['deliverable_complete'] and a['checks_complete'] and a['unsupported_claims']==0 and a['unfinished_ends']==0 and complete and trace.get('exit_status')==0)
    result['status']='SCORED' if complete else 'BLOCKED_INCOMPLETE_TRACE'
    return result


def check_packet(packet):
    required={'session_id','case','raw_request','evaluator_manifest','fixture_facts','trace','mechanical_score'}
    if set(packet)!=required:raise ValueError('Unexpected packet fields')
    def scan(obj):
        if isinstance(obj,dict):
            if set(obj)&{'arm','mapping','skill_commit','skill_version','skill_hashes'}:raise ValueError('Arm or skill identity leak in packet')
            for v in obj.values():scan(v)
        elif isinstance(obj,list):
            for v in obj:scan(v)
    scan(packet)
    if packet['raw_request']!=evaluator(packet['case'])['raw_request']:raise ValueError('Raw request mismatch')
    if packet['evaluator_manifest']!=evaluator(packet['case']):raise ValueError('Evaluator manifest mismatch')
    if packet['mechanical_score']['session_id']!=packet['session_id']:raise ValueError('Session mismatch')
    return packet
