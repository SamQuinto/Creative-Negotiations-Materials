"""A1 deployment tests with simulated HTTP responses; no paid calls or real keys."""
from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1] / 'empirica-a1'
sys.path.insert(0, str(ROOT / 'app/backend'))
from scorer import Scorer
from api_budget import Ledger, BillingUncertain

TEXT = "I'd like 4 remote work days and 60 vacation days, on top of a salary of 65k\nclient budget of 13.25 grand!\nand perhaps start date as early as possible pls.\nOh and waive my non copete"
CHOICES = {'Remote Working Days': '4', 'Vacation Days': '60', 'Salary': '65000',
           'Personal Budget': '13250', 'Starting Date': 'January 1', 'Non-compete Clause': 'Waive'}


def interpretation():
    quotes = ['4 remote work days', '60 vacation days', 'salary of 65k',
              'client budget of 13.25 grand', 'start date as early as possible', 'waive my non copete']
    return {'pairs': [{'issue': issue, 'option': option, 'source_text': quote,
                       'from_previous_offer': False} for (issue, option), quote in zip(CHOICES.items(), quotes)],
            'ambiguities': [], 'novel_terms': [], 'unsupported_terms': [],
            'offer_intent': 'offer', 'explicit_reference': '', 'interpretation_notes': []}


class FakeResponse(io.BytesIO):
    def __init__(self, body):
        super().__init__(json.dumps(body).encode())


class A1Tests(unittest.TestCase):
    def setUp(self):
        self.scorer = Scorer()

    def test_all_215_definitions_and_no_numerical_weights(self):
        request = self.scorer.request(TEXT)
        context = json.loads(request['input'][1]['content'].split('\n\nScenario-specific reading notes:')[0].split('\n', 1)[1])
        self.assertEqual(len(context['issues']), 215)
        self.assertEqual([i['name'] for i in context['issues']], [i['name'] for i in self.scorer.table['issues']])
        for issue in context['issues']:
            for key in ('payoff', 'payoff_knots', 'Candidate', 'Recruiter', 'score', 'scores'):
                self.assertNotIn(key, issue)
        self.assertEqual(request['model'], 'gpt-6.1-sol')
        self.assertEqual(request['reasoning'], {'effort': 'low'})
        self.assertFalse(request['store'])
        self.assertEqual(request['text']['format']['schema']['properties']['pairs']['items']['properties']['issue']['enum'], [i['name'] for i in self.scorer.table['issues']])

    def test_guidance_changes_only_second_message(self):
        plain = Scorer(helper=False).request(TEXT)
        guided = self.scorer.request(TEXT)
        self.assertEqual(len(guided['input']), 3)
        self.assertEqual(plain['input'][0], guided['input'][0])
        self.assertEqual(plain['input'][2], guided['input'][2])
        self.assertEqual(plain['text'], guided['text'])
        self.assertNotEqual(plain['input'][1], guided['input'][1])

    def test_figure_example_and_response_compatibility(self):
        result = self.scorer.for_empirica(self.scorer.finalize(TEXT, interpretation()), mode='recorded_interpretation')
        self.assertEqual(result['decision'], 'scorable')
        self.assertAlmostEqual(result['total_for_proposer'], 7.8)
        self.assertAlmostEqual(result['total_for_receiver'], -5.3)
        self.assertEqual(len(result['valid_pairs']), 6)
        self.assertTrue(all(isinstance(line, str) for line in result['lines']))
        self.assertTrue(all(isinstance(line, str) for line in result['lines_for_receiver']))
        self.assertIn('Total: +7.80', result['display_text'])
        self.assertEqual(result['scorer_routing']['calls'], 0)
        self.assertEqual(result['architecture'], 'A1')

    def test_recruiter_totals_reversed(self):
        result = self.scorer.structured(CHOICES, 'Recruiter')
        self.assertAlmostEqual(result['total_for_proposer'], -5.3)
        self.assertAlmostEqual(result['total_for_receiver'], 7.8)

    def test_missing_required_has_no_total(self):
        result = self.scorer.for_empirica(self.scorer.structured({'Salary': '50000'}))
        self.assertEqual(result['decision'], 'clarification_needed')
        self.assertIsNone(result['total'])
        self.assertEqual(result['missing_required'], ['Personal Budget', 'Starting Date'])

    def test_explicit_zero_is_preserved(self):
        choices = {**CHOICES, 'Remote Working Days': '0'}
        result = self.scorer.structured(choices)
        self.assertEqual(result['decision'], 'scorable')
        self.assertIn('Remote Working Days', result['valid_pairs'])

    def test_impossible_vacation_is_not_silently_dropped(self):
        result = self.scorer.structured({**CHOICES, 'Vacation Days': '500'})
        self.assertEqual(result['decision'], 'clarification_needed')
        self.assertTrue(any(f['issue'] == 'Vacation Days' for f in result['findings']))
        self.assertIsNone(result['total'])

    def test_month_date_does_not_become_float(self):
        result = self.scorer.structured({**CHOICES, 'Starting Date': '2026-05-01'})
        self.assertEqual(result['decision'], 'scorable')
        self.assertEqual(result['valid_pairs']['Starting Date'], 'May 1')

    def test_unpriced_ideas_are_in_display(self):
        response = interpretation()
        response['novel_terms'] = ['a quiet room for my pet dragon']
        response['unsupported_terms'] = ['fly my rich uncle to Mars']
        result = self.scorer.for_empirica(self.scorer.finalize(TEXT, response))
        self.assertIn('a quiet room for my pet dragon', result['display_text'])
        self.assertIn('fly my rich uncle to Mars', result['display_text'])
        self.assertEqual(len(result['valid_pairs']), 6)

    def test_ungrounded_choice_is_not_priced(self):
        response = interpretation()
        response['pairs'].append({'issue': 'Professional Training Program', 'option': 'Participation',
                                  'source_text': 'training please', 'from_previous_offer': False})
        result = self.scorer.finalize(TEXT, response)
        self.assertNotIn('Professional Training Program', result['valid_pairs'])
        self.assertEqual(result['decision'], 'clarification_needed')

    def test_new_scenario_does_not_get_job_guidance(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'another.json'
            table = deepcopy(self.scorer.table)
            table['scenario_id'] = 'another_exercise'
            path.write_text(json.dumps(table), encoding='utf-8')
            request = Scorer(path).request(TEXT)
            self.assertNotIn('Scenario-specific reading notes:', request['input'][1]['content'])

    def response_body(self, status='completed', refusal=False):
        content = [{'type': 'refusal', 'refusal': 'Cannot interpret.'}] if refusal else [{'type': 'output_text', 'text': json.dumps(interpretation())}]
        return {'id': 'test-response', 'status': status, 'model': 'gpt-6.1-sol',
                'usage': {'input_tokens': 1000, 'input_tokens_details': {'cached_tokens': 800}, 'output_tokens': 100},
                'output': [{'type': 'message', 'content': content}]}

    def test_full_http_path_without_network(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}):
            with patch('urllib.request.urlopen', return_value=FakeResponse(self.response_body())) as transport:
                result, receipt = self.scorer.live(TEXT, 'Candidate', '', Path(folder)/'ledger.sqlite', 1)
            self.assertEqual(transport.call_count, 1)
            request = transport.call_args.args[0]
            self.assertEqual(request.full_url, 'https://api.openai.com/v1/responses')
            sent = json.loads(request.data)
            self.assertEqual(sent, self.scorer.request(TEXT))
            self.assertAlmostEqual(result['total'], 7.8)
            self.assertEqual(receipt['input_tokens'], 1000)
            self.assertEqual(Ledger(Path(folder)/'ledger.sqlite', 1).status()['unresolved'], 0)

    def test_incomplete_response_stops(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), patch('urllib.request.urlopen', return_value=FakeResponse(self.response_body(status='incomplete'))):
            with self.assertRaisesRegex(ValueError, 'did not complete'):
                self.scorer.live(TEXT, 'Candidate', '', Path(folder)/'ledger.sqlite', 1)

    def test_refusal_stops(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), patch('urllib.request.urlopen', return_value=FakeResponse(self.response_body(refusal=True))):
            with self.assertRaisesRegex(ValueError, 'could not interpret'):
                self.scorer.live(TEXT, 'Candidate', '', Path(folder)/'ledger.sqlite', 1)

    def test_timeout_does_not_retry(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), patch('urllib.request.urlopen', side_effect=TimeoutError()) as transport:
            with self.assertRaises(BillingUncertain):
                self.scorer.live(TEXT, 'Candidate', '', Path(folder)/'ledger.sqlite', 1)
            self.assertEqual(transport.call_count, 1)
            self.assertEqual(Ledger(Path(folder)/'ledger.sqlite', 1).status()['unknown'], 1)

    def test_standalone_copy_and_another_working_directory(self):
        with tempfile.TemporaryDirectory(prefix='NOVA A1 package ') as folder:
            package = Path(folder) / 'downloaded A1 folder'
            shutil.copytree(ROOT, package, ignore=shutil.ignore_patterns('__pycache__', '.runtime', 'openai_key.txt'))
            command = [sys.executable, str(package/'score_offer.py'), '--choices-json', json.dumps(CHOICES), '--json']
            run = subprocess.run(command, cwd=folder, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertAlmostEqual(json.loads(run.stdout)['total'], 7.8)
            check = subprocess.run([sys.executable, str(package/'app/check_installation.py')], cwd=folder, capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            preview = subprocess.run([sys.executable, str(package/'score_offer.py'), '--text', TEXT, '--preview'], cwd=folder, capture_output=True, text=True)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(json.loads(preview.stdout)['model'], 'gpt-6.1-sol')


if __name__ == '__main__':
    unittest.main()
