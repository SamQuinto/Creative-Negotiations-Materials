"""Apply A2's exercise rules, check the interpretation and calculate scores.

The shared checks validate the model's selections without requiring every
correctly interpreted phrase to match another spelling pattern.
"""
import copy,importlib.util,re,sys
import common1225 as c
sys.path.insert(0,str(c.W.parent/'a1/backend'))
from scorer import Scorer
import interpretation
from runtime_setup import a1_setup
SCORER=a1_setup('job')

def finalize(case,extraction):
    value=copy.deepcopy(extraction);text=case['offer'];prior=case['previous_offer']
    value['ambiguities']=value.get('ambiguity_details',[]) or [x for x in value.get('ambiguities',[]) if isinstance(x,dict)]
    from a2_custom_rules import customize
    import offer_engine
    value,changes=customize(case,value,SCORER.table,offer_engine)
    value.setdefault('explicit_reference','')
    reference=re.search(r'\b(?:same (?:as|offer)|keep (?:the |all )?(?:rest|other|previous)|everything else|as (?:previously )?agreed|accept (?:your|the) (?:offer|proposal))\b',text,re.I)
    if reference:value['explicit_reference']=reference.group()
    for pair in value.get('pairs',[]):
        pair['from_previous_offer']=bool(pair.get('from_previous_offer') or (value.get('explicit_reference') and pair.get('source_text') and not interpretation._quoted(pair['source_text'],text) and interpretation._quoted(pair['source_text'],prior)))
    result=SCORER.for_empirica(SCORER.finalize(text,value,case['role'],prior))
    for finding in result['findings']:
        q=next((q for q in value['ambiguities'] if q.get('question')==finding.get('message')),None)
        if q and q.get('_clarified_issue'):finding.update(source_only_clarification=True,clarified_issue=q['_clarified_issue'])
    result.update(architecture='A2',scorer_routing=extraction.get('_routing',{}),model=extraction.get('_model'),custom_rule_trace=changes)
    return result
