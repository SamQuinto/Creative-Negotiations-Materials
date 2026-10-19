"""Tutorial-specific regressions; no keys, API calls or extra packages."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'app' if (ROOT/'app/backend').is_dir() else ROOT/'empirica/app'
sys.path.insert(0,str(APP/'backend'))
import offer_engine as engine

BASE='Venue fee $300; September 15; closing at 9pm; '


class TutorialLanguage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.scenario=json.loads((APP/'config/tutorial.json').read_text(encoding='utf-8'))

    def run_offer(self,text,role='Candidate',pairs=None):
        return engine.evaluate_offer(text,role,{'pairs':pairs or []},{},self.scenario['required_issues'],self.scenario)

    def test_exact_reported_offer_includes_cancellation(self):
        text=('I can offer the venue for $500 on August 22 next year, closing at 7:00 p.m. '
              'The projector is included if your volunteers handle cleanup, free cancelation')
        r=self.run_offer(text)
        self.assertEqual(r['decision'],'scorable')
        self.assertEqual(len(r['valid_pairs']),6)
        self.assertEqual(r['valid_pairs']['Cancellation notice'],'Free cancellation allowed with notice')
        self.assertAlmostEqual(r['total'],0.3342857142857143)

    def test_cancelation_spelling_and_typos_are_not_filtered_out(self):
        for spelling in ('cancelation','cancellation','cancellaton','cancllation','canclelation'):
            with self.subTest(spelling=spelling):
                r=self.run_offer(BASE+'free '+spelling)
                self.assertEqual(r['valid_pairs'].get('Cancellation notice'),'Free cancellation allowed with notice')

    def test_model_recognition_survives_spelling_evidence_guard(self):
        pairs=[{'issue':'Cancellation notice','option':'Free cancellation allowed with notice','confidence':1}]
        r=self.run_offer(BASE+'free cancelation',pairs=pairs)
        self.assertIn('Cancellation notice',r['valid_pairs'])

    def test_negative_cancellation_does_not_turn_positive(self):
        for wording in ('no free cancelation','no cancellation','non-refundable booking','no refunds'):
            self.assertEqual(self.run_offer(BASE+wording)['valid_pairs'].get('Cancellation notice'),'Booking is non-refundable')

    def test_no_cancellation_fee_is_not_no_refund(self):
        for wording in ('no cancellation fee','no refund charge'):
            self.assertEqual(self.run_offer(BASE+wording)['valid_pairs'].get('Cancellation notice'),'Free cancellation allowed with notice')

    def test_bare_cancellation_gets_an_issue_specific_question(self):
        r=self.run_offer(BASE+'cancellation',pairs=[{'issue':'Cancellation notice','option':'Free cancellation allowed with notice','confidence':1}])
        self.assertEqual(r['decision'],'clarification_needed')
        self.assertNotIn('Cancellation notice',r['valid_pairs'])
        self.assertTrue(any(f.get('issue')=='Cancellation notice' for f in r['findings']))

    def test_missing_cleanup_owner_is_not_guessed_from_first_person_offer(self):
        r=self.run_offer('I can offer the venue for $300 on September 15 closing at 9pm; cleanup',pairs=[{'issue':'Cleanup','option':'Organizer handles cleanup','confidence':1}])
        self.assertEqual(r['decision'],'clarification_needed')
        self.assertNotIn('Cleanup',r['valid_pairs'])

    def test_split_projector_word(self):
        r=self.run_offer(BASE+'venue pro jector included')
        self.assertEqual(r['valid_pairs'].get('Projector'),'Venue projector included')
        self.assertNotIn('pro jector',r['novel_terms'])

    def test_unknown_words_are_kept_even_with_an_empty_extraction(self):
        for phrase in ('unicorn rides','a teleportation portal','fly my rich uncle first class','qzxplorn credits'):
            r=self.run_offer(BASE+phrase)
            self.assertTrue(r['novel_terms'],r)
            self.assertEqual(len(r['valid_pairs']),3,r)
            self.assertIn('not scored',r['display_text'])

    def test_known_and_unpriced_requests_remain_separate(self):
        r=self.run_offer(BASE+'free cancelation and a teleportation portal')
        self.assertIn('Cancellation notice',r['valid_pairs'])
        self.assertTrue(any('teleportation' in term for term in r['novel_terms']))
        self.assertFalse(any('cancelation' in term for term in r['novel_terms']))

    def test_we_and_you_follow_the_speakers_role(self):
        for role,owner in (('Candidate','Organizer'),('Recruiter','Venue')):
            r=self.run_offer(BASE+'we handle cleanup',role)
            self.assertEqual(r['valid_pairs'].get('Cleanup'),owner+' handles cleanup')

    def test_coordinated_food_and_staff_share_the_explicit_provider(self):
        r=self.run_offer(BASE+'we provide refreshments and door staff')
        self.assertEqual(r['valid_pairs'].get('Food and refreshments'),'Organizer provides refreshments')
        self.assertEqual(r['valid_pairs'].get('Door staffing'),'Organizer provides door staff')

    def test_unmentioned_features_are_not_added_by_model_output(self):
        pairs=[{'issue':'Projector','option':'Venue projector included','confidence':1}]
        r=self.run_offer(BASE,pairs=pairs)
        self.assertNotIn('Projector',r['valid_pairs'])

    def test_unread_wording_still_shows_when_another_issue_needs_clarifying(self):
        r=self.run_offer(BASE+'cancellation and a teleportation portal')
        self.assertEqual(r['decision'],'clarification_needed')
        self.assertIn('teleportation',r['display_text'])

    def test_recognized_food_and_staff_wording_is_not_also_called_unread(self):
        for phrase in ('venue supplies tea and coffee','our volunteers cover the entrance'):
            r=self.run_offer(BASE+phrase)
            self.assertEqual(r['novel_terms'],[],r)


if __name__=='__main__':unittest.main(verbosity=2)
