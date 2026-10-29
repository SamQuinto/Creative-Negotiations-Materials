"""Select issue definitions and prepare A2's interpretation request.

Exercise facts are supplied separately from the prompt. The scorer receives
the offer and its context, not benchmark labels or expected answers.
"""
import json,re,copy,difflib
import common1225 as c
STREAM=None;ROLE='Candidate';RECEIPTS=[];TRACE=[]
RUN_ID=None
GUIDANCE=c.load(c.W/'frozen/A2_Reading_Rules.json')
PROMPT=(c.W/'prompts/A2_Interpretation.txt').read_text(encoding='utf-8')

def retrieval_text(text,scenario):
    vocabulary={w.lower() for item in scenario['issues'] for w in re.findall(r'[A-Za-z]{5,}',item['name'])}
    extra=[]
    for word in set(re.findall(r'[A-Za-z]{5,}',text.lower()))-vocabulary:
        matches=difflib.get_close_matches(word,sorted(vocabulary),n=2,cutoff=.86)
        if len(matches)==1:extra.append(matches[0])
    return text+'\n'+' '.join(extra)

def build_request(text,previous_offer='',model=None):
    """Prepare the evaluated request without making an API call."""
    model=model or 'gpt-5.6-luna';stream=STREAM
    catalog=stream._catalog(retrieval_text(text+'\n'+previous_offer,stream.SCENARIO))
    schema=stream._schema();schema['properties']['pairs']['items']['properties']['issue']['enum']=list(catalog)
    fields=schema['properties']['pairs']['items']['properties']
    schema['properties']['pairs']['items']['properties']={'source_text':fields['source_text'],**{k:v for k,v in fields.items() if k!='source_text'}}
    payload=dict(proposer_role=ROLE,current_offer=text,previous_offer=previous_offer,scoring_table=catalog,
                 exercise_reading_rules=GUIDANCE,role_materials=c.load(c.W/'frozen/Role_Materials.json'))
    if RUN_ID:payload['evaluation_run']=RUN_ID
    req=dict(model=model,store=False,reasoning_effort='low',max_completion_tokens=12000,response_format=dict(type='json_schema',json_schema=dict(name='offer_extraction',strict=True,schema=schema)),messages=[dict(role='system',content=PROMPT),dict(role='user',content=json.dumps(payload,ensure_ascii=False,separators=(',',':')))])
    return req

def finish_extraction(parsed,receipt,model):
    """Retain the evaluated response bookkeeping and ambiguity representation."""
    RECEIPTS.append(receipt);TRACE.append(dict(stage='raw_model',model=model,extraction=copy.deepcopy(parsed)))
    parsed['_usage']=dict(input_tokens=receipt['input_tokens'],output_tokens=receipt['output_tokens']);parsed['_model']=model
    parsed['_discarded_ambiguities']=[];parsed['ambiguity_details']=parsed['ambiguities'];parsed['ambiguities']=[x['question'] for x in parsed['ambiguity_details']]
    return parsed

def extract(text,previous_offer='',dense_audit=False,model=None):
    model=model or 'gpt-5.6-luna'
    parsed,receipt=c.api(build_request(text,previous_offer,model),'A2_themed_'+model)
    return finish_extraction(parsed,receipt,model)
