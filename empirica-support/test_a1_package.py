"""A1 deployment tests with simulated HTTP responses; no paid calls or real keys."""
from copy import deepcopy
from contextlib import redirect_stdout
import importlib.util
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

ROOT = Path(__file__).resolve().parents[1] / 'empirica'
sys.path.insert(0, str(ROOT / 'app/a1/backend'))
from scorer import Scorer
from api_budget import Ledger, BillingUncertain, BudgetStop, PRICES

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

    def locked_ledger(self, folder):
        path = Path(folder) / 'ledger.sqlite'
        PRICES[self.scorer.model] = tuple(self.scorer.settings['api_prices_per_million'])
        ledger = Ledger(path, 1)
        call = ledger.reserve('earlier_request', self.scorer.request(TEXT))
        ledger.uncertain(call, 'HTTP 503')
        return path

    def test_study_default_never_opens_a_ledger(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), \
                patch('scorer.Ledger', side_effect=AssertionError('Must not open a ledger')), \
                patch('urllib.request.urlopen', return_value=FakeResponse(self.response_body())) as transport:
            raw, receipt = self.scorer.live(TEXT, 'Candidate', '')
        self.assertEqual(transport.call_count, 1)
        self.assertAlmostEqual(raw['total'], 7.8)
        self.assertEqual(receipt['accounting_mode'], 'usage_estimate_no_budget_ledger')
        self.assertAlmostEqual(receipt['estimated_cost_usd'], .00158)

    def test_study_ignores_old_unknown_billing_without_changing_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.locked_ledger(folder)
            before = path.read_bytes()
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), \
                    patch('urllib.request.urlopen', return_value=FakeResponse(self.response_body())):
                result, _ = self.scorer.live(TEXT, 'Candidate', '', path)
            self.assertEqual(result['decision'], 'scorable')
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(Ledger(path, 1).status()['unknown'], 1)

    def test_study_ignores_exhausted_test_budget_without_resetting_it(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.locked_ledger(folder)
            with Ledger(path, 1).connect() as db:
                db.execute("UPDATE calls SET status='completed',cost=1")
            before = path.read_bytes()
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), \
                    patch('urllib.request.urlopen', return_value=FakeResponse(self.response_body())):
                raw, _ = self.scorer.live(TEXT, 'Candidate', '', path)
            self.assertAlmostEqual(raw['total'], 7.8)
            self.assertEqual(path.read_bytes(), before)

    def test_study_http_503_does_not_retry_or_block_next_offer(self):
        with tempfile.TemporaryDirectory() as folder, \
                patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}):
            path = Path(folder) / 'not_created.sqlite'
            error = urllib.error.HTTPError('https://api.openai.com/v1/responses', 503,
                                          'Unavailable', {}, io.BytesIO(b'{}'))
            with patch('urllib.request.urlopen', side_effect=[error, FakeResponse(self.response_body())]) as transport:
                with self.assertRaisesRegex(BudgetStop, 'temporarily unavailable.*HTTP 503'):
                    self.scorer.live(TEXT, 'Candidate', '', path)
                self.assertEqual(transport.call_count, 1)
                raw, _ = Scorer().live(TEXT, 'Candidate', '', path)
            self.assertEqual(transport.call_count, 2)
            self.assertEqual(raw['decision'], 'scorable')
            self.assertFalse(path.exists())

    def test_study_timeout_does_not_retry_or_block_next_offer(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), \
                patch('urllib.request.urlopen', side_effect=[TimeoutError(), FakeResponse(self.response_body())]) as transport:
            with self.assertRaisesRegex(BudgetStop, 'timeout'):
                self.scorer.live(TEXT, 'Candidate', '')
            self.assertEqual(transport.call_count, 1)
            raw, _ = self.scorer.live(TEXT, 'Candidate', '')
        self.assertEqual(transport.call_count, 2)
        self.assertAlmostEqual(raw['total'], 7.8)

    def test_study_connection_failure_does_not_block_next_offer(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), \
                patch('urllib.request.urlopen', side_effect=[urllib.error.URLError('offline'), FakeResponse(self.response_body())]):
            with self.assertRaisesRegex(BudgetStop, 'connection problem'):
                self.scorer.live(TEXT, 'Candidate', '')
            raw, _ = self.scorer.live(TEXT, 'Candidate', '')
        self.assertEqual(raw['decision'], 'scorable')

    def test_study_http_errors_have_safe_distinct_messages(self):
        examples = [
            (400, '', 'rejected this scoring request'),
            (401, '', 'authentication or access'),
            (403, '', 'authentication or access'),
            (408, '', 'temporarily unavailable'),
            (409, '', 'temporarily unavailable'),
            (429, 'rate_limit_exceeded', 'temporarily rate-limited'),
            (429, 'insufficient_quota', 'credit, spending or usage limit'),
            (429, 'credit_balance_exhausted', 'credit, spending or usage limit'),
            (429, 'project_spend_limit_exceeded', 'credit, spending or usage limit'),
            (500, '', 'temporarily unavailable'),
            (503, 'server_is_overloaded', 'temporarily unavailable'),
        ]
        for status, code, message in examples:
            with self.subTest(status=status, code=code):
                body = json.dumps({'error': {'code': code, 'message': 'PRIVATE_KEY_SHOULD_NOT_APPEAR'}}).encode()
                error = urllib.error.HTTPError('https://api.openai.com/v1/responses', status, 'Error', {}, io.BytesIO(body))
                with patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), \
                        patch('urllib.request.urlopen', side_effect=error) as transport:
                    with self.assertRaises(BudgetStop) as caught:
                        self.scorer.live(TEXT, 'Candidate', '')
                self.assertIn(message, str(caught.exception))
                self.assertNotIn('PRIVATE_KEY_SHOULD_NOT_APPEAR', str(caught.exception))
                self.assertNotIn('LOCAL_TEST_PLACEHOLDER', str(caught.exception))
                self.assertEqual(transport.call_count, 1)

    def test_study_bad_response_does_not_block_next_offer(self):
        for response in (io.BytesIO(b'{not JSON'), FakeResponse([])):
            with self.subTest(response=type(response).__name__), \
                    patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), \
                    patch('urllib.request.urlopen', side_effect=[response, FakeResponse(self.response_body())]):
                with self.assertRaisesRegex(BudgetStop, 'unreadable response'):
                    self.scorer.live(TEXT, 'Candidate', '')
                raw, _ = self.scorer.live(TEXT, 'Candidate', '')
                self.assertEqual(raw['decision'], 'scorable')

    def test_study_missing_or_invalid_usage_does_not_discard_a_valid_offer(self):
        for usage in (None, {}, 'invalid', {'input_tokens': 1000, 'output_tokens': 100,
                                           'input_tokens_details': {'cached_tokens': 1001}}):
            with self.subTest(usage=usage):
                body = self.response_body()
                body['usage'] = usage
                with patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), \
                        patch('urllib.request.urlopen', return_value=FakeResponse(body)):
                    raw, receipt = self.scorer.live(TEXT, 'Candidate', '')
                self.assertEqual(raw['decision'], 'scorable')
                self.assertIsNone(receipt['estimated_cost_usd'])
                self.assertIn('accounting_warning', receipt)
                formatted = self.scorer.for_empirica(raw, receipt=receipt)
                self.assertAlmostEqual(formatted['total_for_proposer'], 7.8)

    def test_explicit_test_budget_still_enforces_unknown_billing_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.locked_ledger(folder)
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), \
                    patch('urllib.request.urlopen') as transport:
                with self.assertRaisesRegex(BillingUncertain, 'unknown billing'):
                    self.scorer.live(TEXT, 'Candidate', '', path, 1)
            transport.assert_not_called()

    def test_explicit_test_budget_still_stops_at_its_limit(self):
        with tempfile.TemporaryDirectory() as folder, \
                patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER'}), \
                patch('urllib.request.urlopen') as transport:
            with self.assertRaisesRegex(BudgetStop, 'budget would be exceeded'):
                self.scorer.live(TEXT, 'Candidate', '', Path(folder) / 'test.sqlite', .000001)
        transport.assert_not_called()

    def test_cli_ignores_old_budget_environment_and_locked_ledger(self):
        spec = importlib.util.spec_from_file_location('a1_entry_for_test', ROOT / 'score_offer.py')
        entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entry)
        with tempfile.TemporaryDirectory() as folder:
            path = self.locked_ledger(folder)
            output = io.StringIO()
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'LOCAL_TEST_PLACEHOLDER',
                    'NOVA_A1_BUDGET_USD': 'not-a-number', 'NOVA_A1_API_LEDGER': str(path)}), \
                    patch('sys.argv', ['score_offer.py', '--text', TEXT, '--json']), \
                    patch('urllib.request.urlopen', return_value=FakeResponse(self.response_body())), \
                    redirect_stdout(output):
                code = entry.main()
            result = json.loads(output.getvalue())
            self.assertEqual(code, 0, result)
            self.assertAlmostEqual(result['total_for_proposer'], 7.8)
            self.assertEqual(Ledger(path, 1).status()['unknown'], 1)

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
