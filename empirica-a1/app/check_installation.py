"""Check the downloaded A1 folder without an API key or network calls."""
from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'backend'))
from scorer import Scorer


def main():
    package = Path(__file__).resolve().parents[1]
    manifest_file = package / 'runtime_manifest.json'
    if manifest_file.is_file():
        manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
        for name, expected in manifest['file_sha256_lf'].items():
            digest = hashlib.sha256((package / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
            assert digest == expected, 'Update the complete A1 folder: file mismatch in ' + name
    scorer = Scorer()
    choices = {'Salary': '65000', 'Personal Budget': '13250', 'Starting Date': 'January 1',
               'Remote Working Days': '4', 'Vacation Days': '60', 'Non-compete Clause': 'Waive'}
    result = scorer.for_empirica(scorer.structured(choices))
    assert result['decision'] == 'scorable'
    assert abs(result['total_for_proposer'] - 7.8) < 1e-9
    assert abs(result['total_for_receiver'] + 5.3) < 1e-9
    assert all(isinstance(line, str) for line in result['lines'])
    request = scorer.request('salary 50k budget 10k start March 1')
    data = json.loads(request['input'][1]['content'].split('\n\nScenario-specific reading notes:')[0].split('\n', 1)[1])
    assert len(data['issues']) == 215
    assert all('Candidate' not in issue and 'Recruiter' not in issue for issue in data['issues'])
    assert request['model'] == 'gpt-6.1-sol'
    assert request['reasoning']['effort'] == 'low'
    assert len(request['input']) == 3
    missing = scorer.for_empirica(scorer.structured({'Salary': '50000'}))
    assert missing['decision'] == 'clarification_needed' and missing['total'] is None
    print('A1 installation check passed: 215 issues, prompts, scoring and Empirica JSON fields.')
    print('Example scores: Candidate +7.80; Recruiter -5.30. No API calls were made.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
