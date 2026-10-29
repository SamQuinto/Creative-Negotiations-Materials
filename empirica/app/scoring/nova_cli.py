"""Run the named architecture stages, with API use only when --live is supplied."""
from pathlib import Path
import argparse, copy, json, sys
import common1225 as c
from runtime_setup import a1_setup, a2_setup, data_dir, PreviewReady
from stage_support import load_stage, input_path
ROOT = Path(__file__).resolve().parent

def a1_request(case, exercise, reasoning):
    return load_stage('A1-1').prepare_request(case, exercise, reasoning)

def run(case, architecture, exercise, reasoning, interpretation=None, live=False):
    c.RECEIPTS.clear(); case = dict(case); case.setdefault('previous_offer', '')
    if architecture == 'A1':
        request = a1_request(case, exercise, reasoning)
        if interpretation is None and not live: return dict(model_request=request, api_called=False)
        if interpretation is None: interpretation, _ = c.api(request, 'A1_' + reasoning)
        result = load_stage('A1-2').score_interpretation(case, interpretation, exercise)
    elif exercise == 'job':
        request = load_stage('A2-1').prepare_request(case, exercise, reasoning)
        if interpretation is None and not live: return dict(model_request=request, api_called=False)
        if interpretation is None:
            import a2_extract
            parsed, receipt = c.api(request, 'A2_themed_gpt-5.6-luna')
            interpretation = a2_extract.finish_extraction(parsed, receipt, 'gpt-5.6-luna')
        result = load_stage('A2-2').score_interpretation(case, interpretation, exercise)
    else:
        stream = a2_setup(exercise, preview=not live)
        if interpretation is None and not live:
            try: stream._llm_extract_once(case['offer'], case.get('previous_offer', ''))
            except PreviewReady as e:
                return dict(model_request=e.request, api_called=False,
                    note='A dense offer can receive a second existing completeness call in live mode.')
        if interpretation is None: interpretation = stream.llm_extract(case['offer'], case.get('previous_offer', ''))
        result = stream.score(case['offer'], case['role'], copy.deepcopy(interpretation), case.get('previous_offer', ''))
    return dict(response=result, interpretation=interpretation, receipts=c.RECEIPTS, api_called=bool(c.RECEIPTS))

def main(default_exercise='job'):
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--architecture', choices=['A1', 'A2'], default='A1')
    p.add_argument('--exercise', choices=['job', 'tutorial'], default=default_exercise)
    p.add_argument('--reasoning', choices=['low', 'high'], default='low')
    p.add_argument('--offer'); p.add_argument('--case-json', type=Path)
    p.add_argument('--role', choices=['Candidate', 'Recruiter'], default='Candidate')
    p.add_argument('--previous-offer', default=''); p.add_argument('--interpretation-json', type=Path)
    p.add_argument('--live', action='store_true'); p.add_argument('--output', type=Path)
    a = p.parse_args()
    if a.case_json: case = c.load(input_path(a.case_json))
    elif a.offer: case = dict(role=a.role, offer=a.offer, previous_offer=a.previous_offer)
    else: p.error('Supply --offer or --case-json.')
    case.setdefault('previous_offer', '')
    if a.architecture == 'A2' and a.reasoning != 'low': p.error('The evaluated A2 setting is low reasoning.')
    interpretation = c.load(input_path(a.interpretation_json)) if a.interpretation_json else None
    value = run(case, a.architecture, a.exercise, a.reasoning, interpretation, a.live)
    serialized = json.dumps(value, ensure_ascii=False, indent=2)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(serialized, encoding='utf-8')
    else: print(serialized)

if __name__ == '__main__': main()
