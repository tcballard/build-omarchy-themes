"""One pinned OpenAI annotation per redacted packet; no mapping input and no automatic retry."""
import argparse
import json
import os
import urllib.request
from pathlib import Path
from common import ROOT,read,sha,private_write,restricted
from annotation import validate,check_packet


def annotate_one(packet,config,prompt,rubric,call):
    check_packet(packet)
    try:
        response=call({'model':config['model_snapshot_id'],'reasoning':{'effort':config['effort']},'store':False,'instructions':prompt+'\n\n'+rubric,'input':json.dumps(packet),'text':{'format':{'type':'json_object'}},'tools':[]})
        if response.get('model')!=config['model_snapshot_id']:raise ValueError('Annotator snapshot mismatch')
        text=''.join(b['text'] for item in response.get('output',[]) if item.get('type')=='message' for b in item.get('content',[]) if b.get('type')=='output_text')
        value=validate(json.loads(text),packet['case'])
        return {'session_id':packet['session_id'],'status':'ANNOTATED','annotation':value,'response':response}
    except (ValueError,KeyError,TypeError) as error:
        return {'session_id':packet['session_id'],'status':'FLAGGED','reason':str(error),'response':locals().get('response',{})}


def call_api(payload):
    request=urllib.request.Request('https://api.openai.com/v1/responses',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY'],'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=600) as response:return json.load(response)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('packets');p.add_argument('output');a=p.parse_args()
    m=read(a.manifest);config=m['annotator']
    if config.get('verified') is not True or 'BLOCKED' in str(config):raise ValueError('Annotator not frozen')
    prompt=(ROOT/'evals/harness/annotator-prompt.md').read_text();rubric=(ROOT/'evals/harness/rubric.md').read_text()
    if sha(prompt.encode())!=config['prompt_sha256'] or sha(rubric.encode())!=config['rubric_sha256']:raise ValueError('Prompt/rubric drift')
    output=restricted(a.output)
    for path in sorted(Path(a.packets).glob('*.json')):
        packet=check_packet(read(path));target=output/(packet['session_id']+'.json')
        if target.exists():continue
        marker=output/(packet['session_id']+'.started')
        if marker.exists():raise ValueError('Interrupted annotation: human resolution required')
        private_write(marker,{'packet_sha256':sha(path.read_bytes())})
        try:result=annotate_one(packet,config,prompt,rubric,call_api)
        except Exception as error:result={'session_id':packet['session_id'],'status':'FLAGGED','reason':type(error).__name__}
        private_write(target,result)

if __name__=='__main__':main()
