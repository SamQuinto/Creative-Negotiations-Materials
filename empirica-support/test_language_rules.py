"""Run constructed language-rule regressions locally, without an API key.

These examples contain no participant responses. They test the shared rules,
not the accuracy of a fresh language-model interpretation.
"""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'empirica'
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

    def test_default_units_usual_allowances_and_asap(self):
        result = self.evaluate('salary 55k budget 9k start ASAP 40 vacay days work remotely 4 times')
        self.assertEqual(result['decision'], 'scorable', result)
        self.assertEqual(result['valid_pairs']['Starting Date'], 'January 1')
        self.assertEqual(result['valid_pairs']['Vacation Days'], '40 days per year')
        self.assertEqual(result['valid_pairs']['Remote Working Days'], '4 days per week')
        result = self.evaluate('salary 55k budget 9k start ASAP 10 more vacation days than usual; 1 more than usual remote working day')
        self.assertEqual(result['valid_pairs']['Vacation Days'], '40 days per year')
        self.assertEqual(result['valid_pairs']['Remote Working Days'], '4 days per week')

    def test_conjunction_does_not_create_cash_range(self):
        result = self.evaluate('salary 55k and budget 9k and 40 vacay days and start ASAP')
        self.assertEqual(result['decision'], 'scorable', result)
        self.assertEqual(result['valid_pairs']['Personal Budget'], '$9,000')

    def test_monthly_remote_times_require_weekly_amount(self):
        result = self.evaluate('salary 55k budget 9k start ASAP work remotely 4 times per month')
        self.assertEqual(result['decision'], 'clarification_needed', result)
        self.assertNotIn('Remote Working Days', result['valid_pairs'])

    def test_calendar_payoff_anchors(self):
        for value, expected in [('January 1',1), ('March 1',0), ('May 1',-1), ('July 1',-2),
                                ('September 1',-3), ('September 30',-3), ('October 1',-1000), ('December 31',-1000)]:
            result = self.evaluate('salary 50k budget 10k start ' + value)
            self.assertEqual(result['decision'], 'scorable', result)
            self.assertAlmostEqual(result['total'], expected)

    def test_tutorial_impossible_day_is_not_called_missing(self):
        for value in ['August 32', '32 August', 'September 31']:
            for text in ['venue fee 300 close 7pm ' + value, 'venue fee 300 ' + value + ' close 7pm']:
                result = self.evaluate(text, tutorial=True)
                self.assertEqual(result['decision'], 'clarification_needed', result)
                self.assertIn('one calendar day in August or September', result['message'])
                self.assertNotIn('Please add Event date', result['message'])

    def test_unpriced_commuting_idea_does_not_request_cash(self):
        text='salary 50k budget 10k start January 1. Buy me a unicorn for my commute.'
        question='What commuting amount do you propose?'
        parsed={'pairs':[], 'novel_terms':['Buy me a unicorn for my commute.'],
                'ambiguities':[question], 'ambiguity_details':[{'issue':'Commuting Support',
                'source_text':'Buy me a unicorn for my commute.','question':question}]}
        result=engine.evaluate_offer(text,'Candidate',parsed,{},self.study['required_issues'],self.study)
        self.assertEqual(result['decision'],'scorable',result)
        self.assertEqual(result['total'],1)
        self.assertNotIn('Commuting Support',result['valid_pairs'])

    def test_relative_holiday_is_not_candidate_vacation(self):
        text='salary 50k budget 10k start January 1. Fly my uncle to his personal holiday.'
        question='How many vacation days?'
        parsed={'pairs':[], 'unsupported_terms':['Fly my uncle to his personal holiday.'],
                'ambiguities':[question], 'ambiguity_details':[{'issue':'Vacation Days',
                'source_text':'holiday','question':question}]}
        result=engine.evaluate_offer(text,'Candidate',parsed,{},self.study['required_issues'],self.study)
        self.assertEqual(result['decision'],'scorable',result)
        self.assertEqual(result['total'],1)
        self.assertNotIn('Vacation Days',result['valid_pairs'])

    def test_relative_request_survives_beside_real_own_leave(self):
        result=self.evaluate('salary 50k budget 10k start January 1. Fly my uncle on his personal holiday and I want 40 vacation days per year.')
        self.assertEqual(result['valid_pairs']['Vacation Days'],'40 days per year')
        self.assertTrue(any('uncle' in term for term in result['novel_terms']),result)

    def test_real_cash_and_vacation_requests_still_need_quantities(self):
        for phrase,issue in [('I want vacation days.','Vacation Days'),('I want a commuting allowance.','Commuting Support')]:
            question='What amount for '+issue+'?'
            parsed={'pairs':[], 'ambiguities':[question], 'ambiguity_details':[{'issue':issue,'source_text':phrase,'question':question}]}
            result=engine.evaluate_offer('salary 50k budget 10k start January 1. '+phrase,'Candidate',parsed,{},self.study['required_issues'],self.study)
            self.assertEqual(result['decision'],'clarification_needed',result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
