"""Python script A1-1: prepare one model request. No API call is made here."""
from pathlib import Path
import json
import common1225 as c
from runtime_setup import data_dir
from stage_support import stage_main
ROOT = Path(__file__).resolve().parent

def prepare_request(case, exercise='job', reasoning='low'):
    """Combine offer data, instructions and exercise files into one JSON request."""
    folder = data_dir(exercise)
    schema = c.load(folder / ('OUTPUT_FORMAT.json' if exercise == 'tutorial' else 'SOURCE_FIRST_FORMAT.json'))
    return dict(model='gpt-6.1-sol', store=False, reasoning=dict(effort=reasoning), max_output_tokens=32768,
        input=[dict(role='developer', content=(ROOT / 'prompts/A1_Final.txt').read_text(encoding='utf-8')),
          *[dict(role='developer', content=name+'\n'+json.dumps(c.load(folder/file), ensure_ascii=False, separators=(',', ':')))
            for name, file in [('EXERCISE_INFORMATION', 'A1_Exercise.json'), ('SCORING_TABLE', 'A1_Scoring_Definitions.json'), ('ROLE_MATERIALS', 'Role_Materials.json')]],
          dict(role='user', content=json.dumps(dict(CURRENT_OFFER=dict(proposer_role=case['role'], text=case['offer']), PREVIOUS_OFFER=dict(text=case.get('previous_offer', ''))), ensure_ascii=False, separators=(',', ':')))],
        text=dict(format=dict(type='json_schema', name='offer_interpretation', strict=True, schema=schema)))

if __name__ == '__main__': stage_main(prepare_request)
