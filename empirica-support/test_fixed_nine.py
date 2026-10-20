"""Check the nine-issue agenda separately from the retained 215-issue catalogue."""
from copy import deepcopy
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT if (ROOT / 'app/backend').is_dir() else ROOT / 'empirica'
SCENARIOS = ROOT / 'empirica/scenarios' if (ROOT / 'empirica/scenarios').is_dir() else ROOT / 'empirica-support/scenarios'
sys.path.insert(0, str(PACKAGE / 'app/backend'))
from scenario_rules import active_scoring_scenario, is_fixed, private_payoff_rows
from offer_engine import score_pair, evaluate_offer
from structured_offer import structured_interpretation, evaluate_structured_offer
NAMES = ['Salary', 'Personal Budget', 'Starting Date', 'Probation Length', 'Contract Length',
         'Vacation Days', 'Remote Working Days', 'Professional Training Program', 'Role in Recruitment Fair']


def load(name):
    return json.loads((SCENARIOS / f'{name}.json').read_text(encoding='utf-8'))


def choices(s):
    return {name: rows[2 if len(rows) == 5 else 0]['option']
            for name, rows in s['roles']['Candidate']['determinatescoretable'].items()}


class FixedNineChecks(unittest.TestCase):
    def test_counts_and_separate_conditions(self):
        fixed, flex, old = load('fixed-9'), load('flexible-215'), load('fixed-15')
        self.assertEqual(fixed['issues'], flex['issues'])
        self.assertEqual(len(fixed['issues']), 215)
        self.assertEqual(len(active_scoring_scenario(fixed)['issues']), 9)
        self.assertEqual(len(active_scoring_scenario(flex)['issues']), 215)
        self.assertEqual(fixed['required_issues'], NAMES)
        self.assertEqual(len(flex['required_issues']), 3)
        self.assertTrue(is_fixed(fixed)); self.assertFalse(is_fixed(flex))
        self.assertEqual(len(old['required_issues']), 15)

    def test_both_nine_row_views_have_at_most_five_choices_and_clean_scores(self):
        for filename in ('fixed-9', 'flexible-215'):
            s = load(filename)
            for role, info in s['roles'].items():
                self.assertEqual(set(info['determinatescoretable']), set(NAMES))
                for name, rows in info['determinatescoretable'].items():
                    self.assertLessEqual(len(rows), 5)
                    for row in rows:
                        self.assertEqual(row['score'], round(row['score'], 2))
                        self.assertAlmostEqual(row['score'], score_pair(name, row['option'], role, {}, s)[1])
        for role in s['roles']:
            self.assertEqual(load('fixed-9')['roles'][role]['determinatescoretable'], s['roles'][role]['determinatescoretable'])

    def test_fixed_narratives_match_flexible_with_only_a_table_transition(self):
        s, flexible = load('fixed-9'), load('flexible-215')
        for role, info in s['roles'].items():
            self.assertEqual(info['narrative'], flexible['roles'][role]['narrative'] + '\n\n'
                             + 'The table below shows the nine issues you can negotiate and what each choice is worth to you:')
            self.assertIn('US$15', info['narrative'])
            self.assertEqual(len(private_payoff_rows(s, role)), 9)
        self.assertIn('all 9', s['tips'])
        self.assertNotIn('15 issues', s['tips'])

    def test_all_four_training_fair_combinations_for_both_roles(self):
        s = load('fixed-9')
        for a, b in itertools.product(range(2), repeat=2):
            selected = choices(s)
            for name, index in [('Professional Training Program', a), ('Role in Recruitment Fair', b)]:
                selected[name] = s['roles']['Candidate']['determinatescoretable'][name][index]['option']
            _, extracted = structured_interpretation(selected, s)
            for role in s['roles']:
                out = evaluate_structured_offer(extracted, role, s)
                self.assertEqual(out['decision'], 'scorable')
                self.assertEqual(len(out['valid_pairs']), 9)
                self.assertAlmostEqual(out['total'], sum(score_pair(n, str(v), role, {}, s)[1] for n, v in selected.items()))

    def test_every_required_issue_is_enforced(self):
        s = load('fixed-9')
        for name in NAMES:
            selected = choices(s); selected.pop(name)
            _, extracted = structured_interpretation(selected, s)
            for role in s['roles']:
                out = evaluate_structured_offer(extracted, role, s)
                self.assertEqual(out['decision'], 'rejected')
                self.assertIn(name, out['missing_required'])

    def test_all_206_inactive_issues_are_blocked_in_fixed_but_work_in_flexible(self):
        fixed, flex = load('fixed-9'), load('flexible-215')
        for issue in fixed['issues']:
            if issue['name'] in NAMES: continue
            value = issue['options'][0]['label'] if issue['kind'] == 'discrete' else str(issue['samples'][0])
            for role in fixed['roles']:
                with self.assertRaises(ValueError): score_pair(issue['name'], value, role, {}, fixed)
                self.assertIsInstance(score_pair(issue['name'], value, role, {}, flex)[1], float)
            with self.assertRaises(ValueError): structured_interpretation({issue['name']: value}, fixed)

    def test_structured_inactive_entry_never_adds_points(self):
        s = load('fixed-9'); selected = choices(s)
        _, extracted = structured_interpretation(selected, s)
        extracted['pairs'].append({'issue': 'Mentorship Program', 'option': 'Participation'})
        result = evaluate_structured_offer(extracted, 'Candidate', s)
        self.assertNotEqual(result['decision'], 'scorable')
        self.assertNotIn('Mentorship Program', result['valid_pairs'])

    def test_free_text_cannot_reactivate_an_omitted_issue(self):
        s = load('fixed-9')
        text, extracted = structured_interpretation(choices(s), s)
        extracted['pairs'].append({'issue': 'Mentorship Program', 'option': 'Participation', 'confidence': 1})
        out = evaluate_offer(text + '; mentorship included', 'Candidate', extracted, {}, s['required_issues'], s)
        self.assertNotIn('Mentorship Program', out['valid_pairs'])
        self.assertNotEqual(out['decision'], 'scorable')

    def test_cli_from_an_unrelated_directory_uses_fixed_nine(self):
        s = load('fixed-9')
        with tempfile.TemporaryDirectory(prefix='Fixed nine check ') as folder:
            run = subprocess.run([sys.executable, str(ROOT / 'empirica/score_offer.py'),
                                  '--scenario-file', str(SCENARIOS / 'fixed-9.json'),
                                  '--choices-json', json.dumps(choices(s)), '--json'],
                                 cwd=folder, capture_output=True, encoding='utf-8', timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        out = json.loads(run.stdout)
        self.assertEqual(out['decision'], 'scorable')
        self.assertEqual(len(out['valid_pairs']), 9)
        self.assertEqual(out['scorer_routing']['calls'], 0)


if __name__ == '__main__': unittest.main(verbosity=2)
