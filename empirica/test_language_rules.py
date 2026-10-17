"""Run constructed language-rule regressions locally, without an API key.

These examples contain no participant responses. They test the shared rules,
not the accuracy of a fresh language-model interpretation.
"""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if not (ROOT / 'app/backend/offer_engine.py').is_file():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / 'app/backend'))
import offer_engine as engine


class LanguageRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study = json.loads((ROOT / 'app/config/large-215.json').read_text(encoding='utf-8'))
        cls.tutorial = json.loads((ROOT / 'app/config/tutorial.json').read_text(encoding='utf-8'))

    def evaluate(self, text, *, tutorial=False, pairs=None, previous=None):
        config = self.tutorial if tutorial else self.study
        return engine.evaluate_offer(text, 'Candidate', {'pairs': pairs or []}, {}, config['required_issues'], config, previous_offer=previous)

    def test_money_shorthand_and_decimal_amounts(self):
        for value, expected in [('52.5k', 52500), ('$65.000', 65000), ('$45600.25', 45600.25)]:
            shown, _ = engine.score_pair('Salary', value, 'Candidate', {}, self.study)
            self.assertAlmostEqual(engine._number_from_text(shown), expected)

    def test_dates_never_become_money(self):
        for value in ['2026-05-01', 'May 1, 2026', '1 May']:
            with self.assertRaises(ValueError):
                engine.score_pair('Salary', value, 'Candidate', {}, self.study)

    def test_foreign_money_needs_currency_clarification(self):
        with self.assertRaises(ValueError):
            engine.score_pair('Personal Budget', '£12000', 'Candidate', {}, self.study)

    def test_a_range_is_not_one_choice(self):
        with self.assertRaises(ValueError):
            engine.score_pair('Personal Budget', '12000-14000', 'Candidate', {}, self.study)

    def test_separators_and_order_keep_required_amounts(self):
        for separator in [' ', '\n', '\t', ', ', '; ', ' and ']:
            result = self.evaluate(separator.join(['starting date May', 'salary 31213', 'budget 7000']))
            self.assertEqual(result['valid_pairs'].get('Salary'), '$31,213')
            self.assertEqual(result['valid_pairs'].get('Personal Budget'), '$7,000')
            self.assertEqual(result['valid_pairs'].get('Starting Date'), 'May 1')

    def test_previous_offer_needs_an_explicit_reference(self):
        self.assertEqual(engine.previous_offer_reference('salary 60k', self.study)['mode'], 'none')
        self.assertEqual(engine.previous_offer_reference('same other details but salary 60k', self.study)['mode'], 'full')

    def test_venue_polite_question_and_projector(self):
        result = self.evaluate('300 venue August 8 close at 7 may we use your projector?', tutorial=True)
        self.assertEqual(result['decision'], 'scorable')
        self.assertEqual(result['valid_pairs']['Projector'], 'Venue projector included')

    def test_projector_price_does_not_replace_venue_fee(self):
        result = self.evaluate('venue fee 300 August 8 close 7 I bring my own projector which cost 200 dollars', tutorial=True)
        self.assertEqual(result['valid_pairs'].get('Venue fee'), '$300')

    def test_venue_ordinal_date(self):
        result = self.evaluate('venue fee 300 August eighth close 7pm', tutorial=True)
        self.assertEqual(result['valid_pairs'].get('Event date'), 'August 8')

    def test_tutorial_unsupported_time_is_not_silently_rounded(self):
        result = self.evaluate('venue fee 300 August 8 close 7:30pm', tutorial=True)
        self.assertNotEqual(result['decision'], 'scorable')

    def test_corrected_amount_is_the_one_shown(self):
        result = self.evaluate('Salary 20k—actually make that 30k. Budget 1k, correction: 5k. Start June.')
        self.assertEqual(result['valid_pairs'].get('Salary'), '$30,000')
        self.assertEqual(result['valid_pairs'].get('Personal Budget'), '$5,000')

    def test_minimum_is_not_an_exact_salary(self):
        result = self.evaluate("I can't accept less than $55,000 for this role. Budget 8k start June 1.")
        self.assertEqual(result['decision'], 'clarification_needed')
        self.assertNotIn('Salary', result['valid_pairs'])

    def test_snacks_and_cleanup_can_have_different_owners(self):
        result = self.evaluate('300 venue August 8 close 7pm our volunteers supply snacks but your staff clean up', tutorial=True)
        self.assertEqual(result['valid_pairs'].get('Food and refreshments'), 'Organizer provides refreshments')
        self.assertEqual(result['valid_pairs'].get('Cleanup'), 'Venue handles cleanup')

    def test_full_year_end_and_mid_months(self):
        for raw, expected in [('end May','May 31'),('mid Jan','January 15'),('end February','February 28'),('December 31','December 31')]:
            result=self.evaluate('salary 50k budget 10k start '+raw)
            self.assertEqual(result['decision'],'scorable',result)
            self.assertEqual(result['valid_pairs']['Starting Date'],expected)

    def test_weekly_vacation_and_physical_limits(self):
        result=self.evaluate('salary 50k budget 10k start Jan 1 1 vacay day a week')
        self.assertEqual(result['valid_pairs']['Vacation Days'],'52 days per year')
        self.assertIn('52 weeks',result['display_text'])
        for phrase in ['366 vacation days','-1 vacation day','7 remote days per week','-1 remote days per week']:
            self.assertEqual(self.evaluate('salary 50k budget 10k start Jan 1 '+phrase)['decision'],'clarification_needed',phrase)

    def test_date_day_does_not_supply_vacation(self):
        result=self.evaluate('salary 50k budget 10k start Jan 1 vacation days')
        self.assertNotIn('Vacation Days',result['valid_pairs'])

    def test_bare_company_car_has_the_approved_default(self):
        for phrase,expected in [('a company car','Dedicated company car'),('no company car','No company car'),('a shared company car','Access to a shared pool car')]:
            result=self.evaluate('salary 50k budget 10k start Jan 1 '+phrase)
            self.assertEqual(result['valid_pairs']['Company Car'],expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
