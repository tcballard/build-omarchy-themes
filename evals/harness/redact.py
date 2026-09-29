"""Redact a structured host export; unsegmented results fail closed for manual resolution."""
import argparse
import copy
import json
import re
from pathlib import Path
from common import read, write, sha, SKILL_PATH, ROOT

def pattern(case):
    phrases=read(ROOT/'evals/harness/phrases-claude-v0.2.1.json')['cases'][case]
    return re.compile('|'.join(r'(?<!\S)'+r'\s+'.join(re.escape(w) for w in p.split())+r'(?!\S)' for p in phrases),re.I)

SECRET_KEYS = {'arm', 'skill_commit', 'skill_version', 'skill_hashes'}

def protected_events(trace):
    # All actions, commands, non-skill output and patches are evidence that must survive.
    result = []
    for e in trace['events']:
        if e['type'] == 'tool_call':
            result.append(e)
        elif e['type'] == 'tool_result':
            result.append({'type': 'tool_result', 'call_id': e['call_id'], 'segments': [s for s in e['segments'] if s['kind'] != 'skill_file']})
        elif e['type'] in ('patch', 'action', 'check', 'read'):
            result.append(e)
    return result

def redact(original, forbidden_ids, case=None):
    matcher=pattern(case or original['case'])
    trace = copy.deepcopy(original)
    trace['events']=[e for e in trace['events'] if e['type']!='host_summary']
    spans = []
    def log(kind):
        spans.append({'span_id': f'span-{len(spans)+1:04d}', 'kind': kind})
    # A tool result consists of typed segments, never inferred by regex from raw terminal output.
    for e in trace['events']:
        if e['type'] == 'tool_result':
            if 'segments' not in e:
                raise ValueError('Unsegmented tool result: annotation blocked')
            for s in e['segments']:
                if s['kind'] == 'skill_file':
                    path = Path(s['path'])
                    if not path.is_relative_to(SKILL_PATH):
                        raise ValueError('Non-skill content marked as skill file')
                    s.clear()
                    s.update(kind='skill_file',text='[skill content]')
                    log('skill_file')
                elif s['kind'] != 'task_output':
                    raise ValueError('Unknown result segment')
        elif e['type'] in ('assistant', 'final'):
            e['text'], count = matcher.subn('[skill quote]', e['text'])
            for _ in range(count): log('skill_quote')
    def strip(obj):
        if isinstance(obj, dict):
            for k in list(obj):
                if k in SECRET_KEYS:
                    del obj[k]; log('metadata')
                else: strip(obj[k])
        elif isinstance(obj, list):
            for x in obj: strip(x)
    # Strip metadata only: never silently change commands or task evidence.
    strip(trace.setdefault('metadata', {}))
    before = protected_events(original)
    after = protected_events(trace)
    if before != after:
        raise ValueError('Protected task evidence changed: annotation blocked')
    encoded = json.dumps(trace, sort_keys=True)
    # Unknown leaks are flagged; task content is not scrubbed to make a check pass.
    if any(x and x in encoded for x in forbidden_ids):
        raise ValueError('Skill-version identifier remains: annotation blocked')
    def strings(obj):
        if isinstance(obj,str): yield obj
        elif isinstance(obj,dict):
            for k,v in obj.items(): yield k; yield from strings(v)
        elif isinstance(obj,list):
            for v in obj: yield from strings(v)
    if any(matcher.search(value) for value in strings(trace)):
        raise ValueError('Skill quote remains outside redactable assistant text')
    log_value = {'session_id': trace['session_id'], 'spans': spans, 'counts': {k: sum(s['kind'] == k for s in spans) for k in ('skill_file', 'skill_quote', 'metadata')}, 'input_sha256': sha(json.dumps(original, sort_keys=True).encode()), 'output_sha256': sha(encoded.encode()), 'protected_evidence_sha256': sha(json.dumps(after, sort_keys=True).encode()), 'protected_evidence_unchanged': True, 'blinding': 'partial'}
    return trace, log_value

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input'); p.add_argument('output'); p.add_argument('log')
    p.add_argument('--case', required=True)
    p.add_argument('--forbidden-ids', required=True, help='Restricted JSON array of skill versions/hashes')
    a = p.parse_args()
    try:
        result, log = redact(read(a.input), read(a.forbidden_ids), a.case)
        write(a.output, result, exclusive=True); write(a.log, log, exclusive=True)
    except ValueError as e:
        write(a.log, {'status':'FLAGGED', 'reason':str(e), 'input_sha256':sha(Path(a.input).read_bytes())}, exclusive=True)
        raise SystemExit('Redaction flagged; no annotation may proceed')
