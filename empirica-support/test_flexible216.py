"""Check the current coffee issue, classroom materials and request schemas without API calls."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'empirica'

def call(*args):
    run=subprocess.run([sys.executable,str(PACKAGE/'score_offer.py'),*args],capture_output=True,
        text=True,encoding='utf-8',timeout=25)
    assert run.returncode==0,run.stderr or run.stdout
    return json.loads(run.stdout)

def main():
    old=json.loads((PACKAGE/'flexible-215.json').read_text(encoding='utf-8'))
    current=json.loads((PACKAGE/'flexible-216.json').read_text(encoding='utf-8'))
    classroom=json.loads((PACKAGE/'flexible-216-classroom.json').read_text(encoding='utf-8'))
    assert len(current['issues'])==216
    assert current['issues'][:215]==old['issues']
    assert classroom['issues']==current['issues']
    assert 'Each point from your final agreement' not in json.dumps(classroom)
    offer='salary 50000, budget 10000, start March 1, free coffee'
    request=call('--issue-space','216','--text',offer,'--preview')
    enum=request['text']['format']['schema']['properties']['pairs']['items']['properties']['issue']['enum']
    assert len(enum)==216 and 'Workplace Coffee' in enum
    definitions=next(x['content'] for x in request['input'] if x['content'].startswith('SCORING_TABLE\n'))
    assert any(x['name']=='Workplace Coffee' for x in json.loads(definitions.split('\n',1)[1]))
    request=call('--issue-space','216','--architecture','A2','--text',offer,'--preview')
    payload=json.loads(request['messages'][-1]['content'])
    assert 'Workplace Coffee' in payload['scoring_table']
    for filename in ['flexible-216.json','flexible-216-classroom.json']:
        for role in ['Candidate','Recruiter']:
            for option,score in [('Free coffee provided',1),('No free coffee provided',0)]:
                choices={'Salary':50000,'Personal Budget':10000,'Starting Date':'2026-03-01','Workplace Coffee':option}
                result=call('--scenario-file',str(PACKAGE/filename),'--role',role,
                    '--choices-json',json.dumps(choices),'--json')
                assert result['decision']=='scorable'
                assert result['total_for_proposer']==(score if role=='Candidate' else 0)
                assert result['total_for_receiver']==(0 if role=='Candidate' else score)
                assert result['scorer_routing']['calls']==0
    assert call('--version')['issue_count']==216
    assert call('--issue-space','215','--version')['issue_count']==215
    print('PASS: all original issue definitions preserved; A1/A2 request schemas include coffee; both roles and both coffee choices score correctly in standard and classroom JSON. No API calls.')

if __name__=='__main__':main()
