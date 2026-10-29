"""Shared file loading and API calls for the included scoring scripts.

The older filename is kept so existing imports continue to work. The number
in its name does not limit how many offers the scorer can process.
"""
from pathlib import Path
import json,os,time,urllib.request,urllib.error
W=Path(__file__).resolve().parent
LAST_BODY=None
RECEIPTS=[]
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def key():
    value=os.environ.get('OPENAI_API_KEY','').strip()
    if not value:raise RuntimeError('Set OPENAI_API_KEY in your environment. No key is bundled.')
    return value
def api(request,stage):
    global LAST_BODY
    url='https://api.openai.com/v1/chat/completions' if 'messages' in request else 'https://api.openai.com/v1/responses'
    start=time.perf_counter()
    req=urllib.request.Request(url,data=json.dumps(request,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+key(),'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=180) as response:body=json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        try:detail=json.loads(e.read().decode()).get('error',{}).get('message','API request rejected')
        except Exception:detail='API request rejected'
        raise RuntimeError(f'API HTTP {e.code}: {detail}') from None
    # A failed or incomplete request may still be billed, so leave retries to
    # the user rather than quietly making another paid call.
    if 'choices' in body:
        if body['choices'][0].get('finish_reason')!='stop':raise RuntimeError('Incomplete response; no automatic retry.')
        text=body['choices'][0]['message'].get('content') or ''
    else:
        if body.get('status')!='completed':raise RuntimeError('Incomplete response; no automatic retry.')
        text=''.join(p.get('text','') for item in body.get('output',[]) for p in item.get('content',[]) if p.get('type')=='output_text')
    value=json.loads(text);u=body.get('usage') or {}
    inp=u.get('input_tokens',u.get('prompt_tokens',0));out=u.get('output_tokens',u.get('completion_tokens',0));cached=(u.get('input_tokens_details',u.get('prompt_tokens_details')) or {}).get('cached_tokens',0)
    rates={'gpt-6.1-sol':(2,.1,10),'gpt-5.6-luna':(.2,.02,1.2)};a,b,d=rates[request['model']]
    receipt=dict(model=body.get('model'),response_id=body.get('id'),stage=stage,input_tokens=inp,cached_input_tokens=cached,output_tokens=out,api_seconds=time.perf_counter()-start,estimated_cost_usd=((inp-cached)*a+cached*b+out*d)/1e6)
    RECEIPTS.append(receipt);LAST_BODY=body
    return value,receipt
