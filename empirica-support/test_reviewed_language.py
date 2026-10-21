"""Check reviewed language and both parties' points without model calls or keys."""
from copy import deepcopy
import itertools
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'empirica/app/backend'))
import offer_engine
import stream

SCENARIO = json.loads((ROOT / 'empirica/flexible-215.json').read_text(encoding='utf-8'))
CORE = {'Salary': '55000', 'Personal Budget': '10000', 'Starting Date': 'January 1'}
BASE = 'salary 55000; personal budget 10000; start January 1; '
SOCIAL = 'Regular Social Media Posts for Company'
BONUS = 'Performance-Based Bonus'


def interpretation(items=()):
    return {'offer_intent': 'offer', 'ambiguities': [], 'ambiguity_details': [],
            'novel_terms': [], 'unsupported_terms': [],
            'pairs': [dict(issue=issue, option=value, source_text=source, confidence=1)
                      for issue, value, source in items]}


def evaluate(text, items=(), role='Candidate'):
    return offer_engine.evaluate_offer(text, role, interpretation(items), {},
                                       SCENARIO['required_issues'], SCENARIO)


class ReviewedLanguage(unittest.TestCase):
    def test_social_workload_is_proportional_and_zero_sum(self):
        for step in range(101):
            share = step / 100
            with self.subTest(share=share):
                label, candidate = offer_engine.score_pair(SOCIAL, str(share), 'Candidate', {}, SCENARIO)
                _, recruiter = offer_engine.score_pair(SOCIAL, label, 'Recruiter', {}, SCENARIO)
                self.assertAlmostEqual(candidate, -share)
                self.assertAlmostEqual(recruiter, share)
                self.assertAlmostEqual(candidate + recruiter, 0)

    def test_separators_and_order_preserve_reduced_commitment(self):
        parts = ['salary 50000', 'personal budget 15000', 'start January 1',
                 'slightly reduced company social media commitment', 'remote work 4 days']
        for separator, ordered in itertools.product(['\n', ', ', '; ', ' and ', ' '], [parts, parts[::-1]]):
            with self.subTest(separator=repr(separator), first=ordered[0]):
                result = evaluate(separator.join(ordered))
                self.assertEqual(result['decision'], 'scorable', result)
                self.assertEqual(result['valid_pairs'][SOCIAL], '75% of usual posting commitment')
                self.assertAlmostEqual(result['total'], 3.25)

    def test_explicit_percentages_override_qualitative_language(self):
        for phrase, share in [('40% less company social media posting', .6),
                              ('company social media posting at 40% of usual', .4),
                              ('minimal company social media commitment', .25)]:
            with self.subTest(phrase=phrase):
                result = evaluate(BASE + phrase)
                self.assertEqual(result['decision'], 'scorable', result)
                self.assertEqual(result['valid_pairs'][SOCIAL],
                                 offer_engine.score_pair(SOCIAL, str(share), 'Candidate', {}, SCENARIO)[0])

    def test_bonus_anchors_and_legacy_name_keep_opposite_points(self):
        for amount, candidate in [(0, -1), (2000, 0), (4000, 1/3), (8000, 1)]:
            with self.subTest(amount=amount):
                for name in (BONUS, 'Team Sales Bonus'):
                    self.assertAlmostEqual(offer_engine.score_pair(name, str(amount), 'Candidate', {}, SCENARIO)[1], candidate)
                    self.assertAlmostEqual(offer_engine.score_pair(name, str(amount), 'Recruiter', {}, SCENARIO)[1], -candidate)

    def test_individual_or_team_targets_use_one_bonus(self):
        for kind in ['individual', 'team']:
            phrase = f'a $4000 {kind} performance bonus'
            with self.subTest(kind=kind):
                result = evaluate(BASE + phrase, [(BONUS, '4000', phrase), ('Team Sales Bonus', '4000', phrase)])
                self.assertEqual(result['decision'], 'scorable', result)
                self.assertEqual(set(result['valid_pairs']), set(CORE) | {BONUS})
                self.assertEqual(result['valid_pairs'][BONUS], '$4,000')

    def test_bonus_maximum_and_percent_are_not_guessed_as_cash(self):
        for phrase in ['a performance bonus up to $2000', 'a performance bonus of 10%']:
            with self.subTest(phrase=phrase):
                result = evaluate(BASE + phrase, [(BONUS, '2000', phrase)])
                self.assertEqual(result['decision'], 'clarification_needed', result)
                self.assertNotIn(BONUS, result['valid_pairs'])
                self.assertNotIn('individual or team', result['message'])

    def test_later_totals_keep_probation_without_extra_rise_points(self):
        text = ('salary 45000; personal budget 5000; start January 1; six month probation; '
                'after probation salary will be 50000 and personal budget will be 10000')
        result = evaluate(text)
        self.assertEqual(result['decision'], 'scorable', result)
        self.assertEqual(set(result['valid_pairs']), set(CORE) | {'Probation Length'})
        self.assertEqual(result['valid_pairs']['Salary'], '$50,000')
        self.assertEqual(result['valid_pairs']['Personal Budget'], '$10,000')
        self.assertEqual(result['valid_pairs']['Probation Length'], '6 months')
        self.assertIn('Points use the later', result['display_text'])

    def test_full_response_scores_counterpart_without_api(self):
        phrase = 'slightly reduced company social media commitment; a $4000 individual performance bonus'
        text = BASE + phrase
        extracted = interpretation([(BONUS, '4000', 'a $4000 individual performance bonus')])
        with patch.object(stream, 'SCENARIO', SCENARIO), patch.object(stream, 'REQUIRED_ISSUES', SCENARIO['required_issues']), patch.object(stream, 'llm_extract', side_effect=AssertionError('No API allowed')):
            catalogue = stream._catalog(text)
            self.assertIn(BONUS, catalogue)
            self.assertNotIn('Team Sales Bonus', catalogue)
            self.assertEqual(catalogue[SOCIAL]['commitment_scale']['language_levels']['Slightly reduced commitment'], .75)
            for role, other in [('Candidate', 'Recruiter'), ('Recruiter', 'Candidate')]:
                with self.subTest(role=role):
                    result = stream.score(text, role, extraction=deepcopy(extracted))
                    self.assertEqual(result['decision'], 'scorable', result)
                    self.assertAlmostEqual(result['total_for_receiver'], evaluate(text, [(BONUS, '4000', 'a $4000 individual performance bonus')], other)['total'])

    def test_form_alias_cannot_double_count_or_reactivate_fixed_issue(self):
        from structured_offer import structured_interpretation
        with self.assertRaisesRegex(ValueError, 'Duplicate issue'):
            structured_interpretation({**CORE, BONUS: 4000, 'Team Sales Bonus': 4000}, SCENARIO)
        fixed = json.loads((ROOT / 'empirica/fixed-9.json').read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ValueError, 'Unknown issue'):
            structured_interpretation({'Team Sales Bonus': 4000}, fixed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
