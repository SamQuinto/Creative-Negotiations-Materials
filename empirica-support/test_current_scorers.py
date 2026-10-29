"""Check current defaults, exact requests, portability and absence of billing locks."""
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch
import hashlib,io,json,os,shutil,subprocess,sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]/'empirica'
EXAMPLES=ROOT/'app/scoring/examples'

def command(package,exercise,*args,env=None,cwd=None):
    script='score_tutorial_offer.py' if exercise=='tutorial' else 'score_offer.py'
    clean={k:v for k,v in os.environ.items() if 'KEY' not in k.upper() and k not in ['PYTHONPATH','PYTHONHOME','SCORER_DEFAULT_SPACE']}
    clean.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1');clean.update(env or {})
    result=subprocess.run([sys.executable,str(package/script),*args],cwd=cwd or package,env=clean,capture_output=True,text=True,encoding='utf-8',timeout=45)
    if result.returncode:raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)

class CurrentScorerTests(unittest.TestCase):
    def test_both_default_to_general_a1(self):
        for exercise,count in [('job',215),('tutorial',9)]:
            with self.subTest(exercise=exercise):
                result=command(ROOT,exercise,'--version')
                self.assertEqual(result['architecture'],'A1');self.assertEqual(result['model'],'gpt-6.1-sol')
                self.assertEqual(result['reasoning'],'low');self.assertEqual(result['issue_count'],count)
                self.assertFalse(result['guidance_enabled'])

    def test_requests_match_replication_fingerprints(self):
        reference=json.loads((EXAMPLES/'request_fingerprints.json').read_text())
        for config in reference['configurations']:
            exercise=config['exercise'];prefix='job' if exercise=='job' else 'tutorial'
            case=json.loads((EXAMPLES/f'{prefix}_offer.json').read_text())
            with self.subTest(config=config):
                result=command(ROOT,exercise,'--architecture',config['architecture'],'--reasoning',config['reasoning'],
                    '--role',case['role'],'--text',case['offer'],'--previous-offer',case.get('previous_offer',''),'--preview')
                digest=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
                self.assertEqual(digest,config['request_sha256'])

    def test_six_term_example_both_roles_and_architectures(self):
        case=json.loads((EXAMPLES/'appendix_a_offer.json').read_text())
        for architecture in ['A1','A2']:
            for role,total,other in [('Candidate',7.8,-5.3),('Recruiter',-5.3,7.8)]:
                with self.subTest(architecture=architecture,role=role):
                    result=command(ROOT,'job','--architecture',architecture,'--role',role,'--text',case['offer'],
                                   '--replay',str(EXAMPLES/'appendix_a_interpretation.json'),'--json')
                    self.assertEqual(result['decision'],'scorable');self.assertEqual(len(result['valid_pairs']),6)
                    self.assertAlmostEqual(result['total_for_proposer'],total);self.assertAlmostEqual(result['total_for_receiver'],other)
                    self.assertEqual(result['scorer_routing']['calls'],0)
                    self.assertTrue(all(isinstance(line,str) for line in result['lines']))

    def test_tutorial_saved_interpretation_both_roles(self):
        case=json.loads((EXAMPLES/'tutorial_offer.json').read_text())
        for role in ['Candidate','Recruiter']:
            result=command(ROOT,'tutorial','--role',role,'--text',case['offer'],
                '--replay',str(EXAMPLES/'tutorial_interpretation.json'),'--json')
            self.assertEqual(result['decision'],'scorable');self.assertEqual(len(result['valid_pairs']),4)
            self.assertEqual(result['scorer_routing']['calls'],0)

    def test_zero_agreement_metadata_and_external_scenario(self):
        choices=json.dumps({'Salary':50000,'Personal Budget':10000,'Starting Date':'2026-03-01'})
        for role in ['Candidate','Recruiter']:
            result=command(ROOT,'job','--role',role,'--choices-json',choices,'--scenario-file',str(ROOT/'flexible-215.json'),'--json')
            self.assertAlmostEqual(result['total_for_proposer'],0)
            self.assertTrue(result['agreement_rules']['allow_zero']);self.assertEqual(result['agreement_rules']['comparison'],'>=')

    def test_standalone_folder_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix='NOVA standalone ') as work:
            relocated=Path(work)/'Renamed package'
            shutil.copytree(ROOT,relocated,ignore=shutil.ignore_patterns('__pycache__','openai_key.txt','.runtime'))
            for exercise in ['job','tutorial']:
                result=command(relocated,exercise,'--version',cwd=work)
                self.assertEqual(result['architecture'],'A1')
            case=json.loads((EXAMPLES/'appendix_a_offer.json').read_text())
            result=command(relocated,'job','--text',case['offer'],'--replay',str(relocated/'app/scoring/examples/appendix_a_interpretation.json'),'--json',cwd=work)
            self.assertAlmostEqual(result['total_for_proposer'],7.8)

    def test_failed_call_does_not_lock_next_offer(self):
        sys.path.insert(0,str(ROOT/'app'))
        import empirica_bridge as entry
        case=json.loads((EXAMPLES/'appendix_a_offer.json').read_text())
        interpretation=json.loads((EXAMPLES/'appendix_a_interpretation.json').read_text())
        fake_receipt={'input_tokens':1,'cached_input_tokens':0,'output_tokens':1,'model':'gpt-6.1-sol','estimated_cost_usd':0,'api_seconds':0}
        def succeed(*args):
            entry.calls.RECEIPTS.append(dict(fake_receipt));return interpretation,dict(fake_receipt)
        argv=['score_offer.py','--text',case['offer'],'--json']
        with patch.dict(os.environ,{'OPENAI_API_KEY':'LOCAL_TEST_PLACEHOLDER','NOVA_A1_BUDGET_USD':'not-a-number','NOVA_A1_API_LEDGER':'DO_NOT_OPEN.sqlite'}):
            for fake,expected in [(RuntimeError('simulated API failure'),1),(succeed,0)]:
                output=io.StringIO()
                with patch.object(sys,'argv',argv),patch.object(entry.calls,'api',side_effect=fake),redirect_stdout(output):
                    code=entry.main()
                result=json.loads(output.getvalue());self.assertEqual(code,expected)
                if code==0:self.assertAlmostEqual(result['total_for_proposer'],7.8)
                self.assertNotIn('LOCAL_TEST_PLACEHOLDER',output.getvalue())

if __name__=='__main__':unittest.main()
