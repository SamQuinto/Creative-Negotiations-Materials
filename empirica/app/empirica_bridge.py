"""Keep Empirica's commands and JSON fields while using the tested scorer stages."""
from pathlib import Path
from copy import deepcopy
import argparse,hashlib,importlib.util,json,os,sys

APP=Path(__file__).resolve().parent
PACKAGE=APP.parent
ENGINE=APP/'scoring'
RELEASE='NOVA-empirica-2026-10-29'
sys.path.insert(0,str(ENGINE))
import common1225 as calls
import nova_cli
from runtime_setup import a1_setup

def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def load_key():
    """Retain the existing private server-side key location."""
    value=os.environ.get('OPENAI_API_KEY','').strip()
    file=APP/'openai_key.txt'
    if not value and file.is_file():value=file.read_text(encoding='utf-8-sig').strip()
    if not value or value=='YOUR_OPENAI_API_KEY_HERE':
        raise ValueError('Set OPENAI_API_KEY or put your key in app/openai_key.txt.')
    os.environ['OPENAI_API_KEY']=value

def custom_request(case,table,exercise,reasoning):
    """Use the same general prompt with an explicitly supplied exercise file."""
    request=nova_cli.a1_request(case,exercise,reasoning)
    import interpretation
    active=interpretation.active_scoring_scenario(table)
    info={'title':table.get('title',''),'required_issues':active.get('required_issues',[]),
          'outside_table_policy':table.get('issue_space',{}).get('unknown_term_policy','reject'),
          'role_names':list(table.get('roles',{}))}
    materials={name:role.get('full_text') or role.get('summary','') for name,role in table.get('roles',{}).items()}
    data={'EXERCISE_INFORMATION':info,'SCORING_TABLE':interpretation.catalogue(table),'ROLE_MATERIALS':materials}
    for message in request['input']:
        name=message['content'].split('\n',1)[0]
        if name in data:message['content']=name+'\n'+json.dumps(data[name],ensure_ascii=False,separators=(',',':'))
    names=[i['name'] for i in active['issues']]
    schema=request['text']['format']['schema']
    schema['properties']['pairs']['items']['properties']['issue']['enum']=names
    schema['properties']['ambiguities']['items']['properties']['issue']['enum']=names+['General offer']
    return request

def version(exercise,architecture,reasoning,scorer):
    paths=[ENGINE/'prompts/A1_Final.txt',ENGINE/'prompts/A2_Interpretation.txt',
           ENGINE/'frozen/A2_Reading_Rules.json',scorer.scenario_file,
           ENGINE/'A1-1.py',ENGINE/'A1-2.py',ENGINE/'A2-1.py',ENGINE/'A2-2.py',
           ENGINE/'a2_custom_rules.py',APP/'a1/backend/interpretation.py',APP/'a1/backend/offer_engine.py']
    return dict(scorer_version=RELEASE,architecture=architecture,
        model='gpt-6.1-sol' if architecture=='A1' else 'gpt-5.6-luna',reasoning=reasoning,
        exercise=exercise,scenario_id=scorer.table.get('scenario_id'),
        issue_count=len(scorer.table.get('active_issues',scorer.table['issues'])),
        guidance_enabled=architecture=='A2',
        sha256={str(p.relative_to(PACKAGE)) if p.is_relative_to(PACKAGE) else p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

def historical(default_space):
    spec=importlib.util.spec_from_file_location('nova_historical_entry',APP/'backend/score_offer_a2.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.main(default_space=default_space)

def main(default_space=None):
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role',choices=['Candidate','Recruiter'],default='Candidate')
    parser.add_argument('--issue-space',choices=['215','tutorial','15','200','fixed-9','fixed-15'],
                        default=default_space or os.environ.get('SCORER_DEFAULT_SPACE','215'))
    parser.add_argument('--architecture',choices=['A1','A2'],default='A1')
    parser.add_argument('--reasoning',choices=['low','medium','high','xhigh','max'],default='low')
    inputs=parser.add_mutually_exclusive_group()
    inputs.add_argument('--text');inputs.add_argument('--choices-json')
    parser.add_argument('--previous-offer',default='');parser.add_argument('--scenario-file')
    parser.add_argument('--json',action='store_true');parser.add_argument('--version',action='store_true')
    parser.add_argument('--preview',action='store_true');parser.add_argument('--replay')
    parser.add_argument('--helper',choices=['on','off'],default='off',help=argparse.SUPPRESS)
    parser.add_argument('--reading-notes',help=argparse.SUPPRESS)
    parser.add_argument('--api-budget',type=float,help=argparse.SUPPRESS)
    parser.add_argument('--api-ledger',help=argparse.SUPPRESS)
    args=parser.parse_args()
    try:
        if args.issue_space in ['15','200','fixed-9','fixed-15']:
            return historical(default_space)
        exercise='tutorial' if args.issue_space=='tutorial' else 'job'
        if args.architecture=='A2' and args.reasoning!='low':raise ValueError('The tested A2 uses low reasoning.')
        if args.helper=='on' or args.reading_notes:
            raise ValueError('Current A1 uses the general prompt without an addendum. Remove --helper on or --reading-notes.')
        if args.api_budget is not None or args.api_ledger:
            raise ValueError('Live study scoring does not use the old budget guard. Remove --api-budget and --api-ledger.')
        if args.preview and (args.replay or args.choices_json):raise ValueError('Use preview without replay or choices-json.')
        scorer=a1_setup(exercise)
        if args.scenario_file:
            from scorer import Scorer
            scorer=Scorer(Path(args.scenario_file).resolve(),helper=False,model='gpt-6.1-sol')
        if args.version:
            print(json.dumps(version(exercise,args.architecture,args.reasoning,scorer),indent=2));return 0
        if args.choices_json is not None:
            result=scorer.for_empirica(scorer.structured(loads_choices(args.choices_json),args.role),mode='deterministic')
            receipts=[];model='deterministic'
        else:
            text=str(args.text if args.text is not None else input('Offer text: ')).encode('utf-8',errors='replace').decode().strip()
            if not text:raise ValueError('Please provide an offer.')
            case=dict(offer=text,role=args.role,previous_offer=args.previous_offer)
            if args.scenario_file:
                if args.architecture!='A1':raise ValueError('Use A1 with an external scenario; A2 is fitted to the included exercises.')
                request=custom_request(case,scorer.table,exercise,args.reasoning)
                if args.preview:print(json.dumps(request,ensure_ascii=True,indent=2));return 0
                calls.RECEIPTS.clear()
                interpretation=load(args.replay) if args.replay else None
                if interpretation is None:load_key();interpretation,_=calls.api(request,'A1_'+args.reasoning)
                result=scorer.for_empirica(scorer.finalize(text,interpretation,args.role,args.previous_offer))
                receipts=list(calls.RECEIPTS)
            else:
                interpretation=load(args.replay) if args.replay else None
                live=not args.preview and interpretation is None
                if live:load_key()
                value=nova_cli.run(case,args.architecture,exercise,args.reasoning,interpretation,live)
                if args.preview:print(json.dumps(value['model_request'],ensure_ascii=True,indent=2));return 0
                result=value['response'];receipts=value['receipts']
            model='recorded_interpretation' if args.replay else ('gpt-6.1-sol' if args.architecture=='A1' else 'gpt-5.6-luna')
        result.update(architecture=args.architecture,scorer_version=RELEASE,model=model,
            reasoning=args.reasoning,guidance_enabled=args.architecture=='A2',
            scorer_routing=dict(policy='A1_full_table' if args.architecture=='A1' else 'A2_exercise_specific',selected=model,calls=len(receipts)),
            extraction_usage={k:sum(r.get(k,0) for r in receipts) for k in ['input_tokens','cached_input_tokens','output_tokens']})
        if receipts:result['api_receipt']=receipts[-1];result['api_receipts']=receipts
        import interpretation as checks
        required=checks.active_scoring_scenario(scorer.table).get('required_issues',[])
        missing=[name for name in required if name not in result.get('valid_pairs',{})]
        result.update(required_issues=required,missing_required=missing,required_ok=not missing)
        # This is agreement metadata, not a change to researcher-defined scores.
        agreement=deepcopy(result.get('agreement_rules') or {})
        agreement.update(require_nonnegative_each_party=True,require_positive_each_party=False,allow_zero=True,comparison='>=',threshold=0)
        result['agreement_rules']=agreement
        print(json.dumps(result,ensure_ascii=True,indent=2) if args.json else result['display_text'])
        return 0
    except Exception as exc:
        message=str(exc);key=os.environ.get('OPENAI_API_KEY','')
        if key:message=message.replace(key,'[key removed]')
        print(json.dumps({'error':message,'decision':'error','architecture':args.architecture},ensure_ascii=True));return 1

def loads_choices(text):
    value=json.loads(text)
    if not isinstance(value,dict) or not value:raise ValueError('choices-json must be a non-empty object.')
    return value
