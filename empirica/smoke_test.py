"""Check the downloaded runtime from another directory, without a key or AI calls."""
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app/backend'))
from offer_engine import score_pair


def main():
    defaults = {'Salary': 31213, 'Personal Budget': 7000, 'Starting Date': '2026-05-01',
        'Probation Length': 3, 'Contract Length': 3, 'Vacation Days': 30, 'Remote Working Days': 3,
        'Venue fee': 300, 'Event date': '2027-09-15'}
    env = {k: v for k, v in os.environ.items() if 'KEY' not in k.upper()}
    env.update(PYTHONIOENCODING='utf-8', PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    count = 0
    with tempfile.TemporaryDirectory(prefix='Empirica download check ') as folder:
        for name in ('fixed-15', 'flexible-15', 'flexible-215', 'tutorial'):
            path = ROOT / 'empirica/scenarios' / (name + '.json')
            scenario = json.loads(path.read_text(encoding='utf-8'))
            choices = {i['name']: defaults.get(i['name'], i.get('min')) if i['kind'] == 'continuous'
                       else i['options'][-1]['label'] for i in scenario['issues'] if i['name'] in scenario['required_issues']}
            for role in ('Candidate', 'Recruiter'):
                completed = subprocess.run([sys.executable, str(ROOT / 'empirica/score_offer.py'),
                    '--scenario-file', str(path), '--role', role, '--choices-json', json.dumps(choices), '--json'],
                    cwd=folder, env=env, capture_output=True, text=True, encoding='utf-8', timeout=20)
                assert completed.returncode == 0, completed.stderr or completed.stdout
                response = json.loads(completed.stdout)
                assert response['decision'] == 'scorable', response
                assert response['model'] == 'deterministic', response
                assert response['scorer_routing']['calls'] == 0, response
                expected = sum(score_pair(k, str(v), role, {}, scenario)[1] for k, v in choices.items())
                assert math.isclose(response['total_for_proposer'], expected, abs_tol=1e-9), response
                assert set(response['valid_pairs']) == set(choices), response
                count += 1
        completed = subprocess.run([sys.executable, str(ROOT / 'empirica/score_tutorial_offer.py'),
            '--choices-json', json.dumps({'Venue fee': 300, 'Event date': '2027-09-15', 'Closing time': '9:00 p.m.'}), '--json'],
            cwd=folder, env=env, capture_output=True, text=True, encoding='utf-8', timeout=20)
        assert completed.returncode == 0, completed.stderr or completed.stdout
        assert json.loads(completed.stdout)['scenario_id'].startswith('community-'), completed.stdout
        count += 1
        for literal in ('2026-01-01','2026-02-30','2027-05-01'):
            completed=subprocess.run([sys.executable,str(ROOT/'empirica/score_offer.py'),'--issue-space','215',
                '--choices-json',json.dumps({'Salary':25000,'Personal Budget':19000,'Starting Date':literal}),'--json'],
                cwd=folder,env=env,capture_output=True,text=True,encoding='utf-8',timeout=20)
            assert completed.returncode==0,completed.stderr or completed.stdout
            response=json.loads(completed.stdout)
            assert response['decision']!='scorable' and response['total_for_proposer'] is None,response
            assert not response.get('error'),response
            assert 'could not convert string to float' not in completed.stdout,completed.stdout
            count+=1
        flat=Path(folder)/'flat';flat.mkdir()
        for relative in ('app/backend','app/config'):
            shutil.copytree(ROOT/relative,flat/relative,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for script in ('score_offer.py','score_tutorial_offer.py'):
            shutil.copy2(ROOT/'empirica'/script,flat/script)
        for script,wanted in (('score_offer.py',15),('score_tutorial_offer.py',9)):
            completed=subprocess.run([sys.executable,str(flat/script),'--version'],cwd=folder,env=env,
                capture_output=True,text=True,encoding='utf-8',timeout=20)
            assert completed.returncode==0,completed.stderr or completed.stdout
            assert json.loads(completed.stdout)['issue_count']==wanted,completed.stdout
            count+=1
    spec = importlib.util.spec_from_file_location('download_preview', ROOT / 'empirica/preview_server.py')
    preview = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preview)
    preview.load()
    assert set(preview.SCENARIOS) == {'fixed-15', 'flexible-15', 'flexible-215', 'tutorial'}
    print(f'PASS: {count} real CLI checks, all four scenarios, both roles, invalid dates, both folder layouts, and preview imports. No AI calls.')


if __name__ == '__main__':
    main()
