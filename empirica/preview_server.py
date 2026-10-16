"""Local integration preview: generated scenario JSON, continuous forms, and agreement."""
import argparse
from copy import deepcopy
from datetime import date, timedelta
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app/backend'))
sys.path.insert(0,str(ROOT/'developer'))
from structured_offer import structured_interpretation
from scenario_rules import is_fixed, own_acceptance_allowed
from role_presentation import narrative_to_html

SCENARIOS={}
ENGINES={}
GAMES={}
LOCK=threading.RLock()
DEFAULTS={'Salary':50000,'Personal Budget':10000,'Starting Date':'2026-05-01',
          'Probation Length':3,'Contract Length':3,'Vacation Days':30,'Remote Working Days':3,
          'Venue fee':300,'Event date':'2027-09-15','Closing time':21}


def load():
    saved=os.environ.get('NEGOTIATOR_SCENARIO_FILE')
    try:
        for name in ('fixed-15','flexible-15','flexible-215','tutorial'):
            path=ROOT/'empirica/scenarios'/f'{name}.json'
            SCENARIOS[name]=json.loads(path.read_text(encoding='utf-8'))
            os.environ['NEGOTIATOR_SCENARIO_FILE']=str(path)
            spec=importlib.util.spec_from_file_location('preview_'+name,ROOT/'app/backend/stream.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            ENGINES[name]=module
            GAMES[name]={'offers':[],'accepted':set()}
    finally:
        if saved is None:os.environ.pop('NEGOTIATOR_SCENARIO_FILE',None)
        else:os.environ['NEGOTIATOR_SCENARIO_FILE']=saved


def score(name,role,choices):
    text,extraction=structured_interpretation(choices,SCENARIOS[name])
    return ENGINES[name].score(text,role,extraction)


def field(issue):
    result={k:deepcopy(v) for k,v in issue.items() if k in ('id','name','kind','value_type','unit')}
    if issue['kind']=='continuous':
        result['domain']=issue.get('proposal_domain',{'min':issue['min'],'max':issue['max']})
        result['default']=DEFAULTS.get(issue['name'],issue['min'])
    else:
        result['options']=[opt['label'] for opt in issue['options']]
        result['default']=result['options'][-1]
    return result


def view_result(result):
    # The reviewer sees only their own score. Full definitions stay in Python.
    return {k:result.get(k) for k in ('decision','messages','valid_pairs','total_for_proposer','proposal_allowed','model','scorer_routing','scenario_id')}


def state(name,role):
    game=GAMES[name]
    last=game['offers'][-1] if game['offers'] else None
    own=score(name,role,last['choices']) if last else None
    return {'offer_count':len(game['offers']),'accepted':sorted(game['accepted']),
            'agreement':len(game['accepted'])==2,'author':last['author'] if last else None,
            'current_offer':view_result(own) if own else None,
            'can_accept':bool(own and own['decision']=='scorable' and own_acceptance_allowed(SCENARIOS[name],own['total_for_proposer']))}


class Handler(BaseHTTPRequestHandler):
    def respond(self,data,status=200,kind='application/json'):
        body=data.encode('utf-8') if isinstance(data,str) else json.dumps(data,ensure_ascii=True).encode()
        self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)

    def do_GET(self):
        try:
            route=urlparse(self.path);query=parse_qs(route.query)
            if route.path=='/':
                return self.respond((ROOT/'empirica/preview.html').read_text(encoding='utf-8'),kind='text/html')
            if route.path=='/deterministic_score.mjs':
                return self.respond((ROOT/'empirica/deterministic_score.mjs').read_text(encoding='utf-8'),kind='text/javascript')
            name=query.get('scenario',['fixed-15'])[0];role=query.get('role',['Candidate'])[0]
            s=SCENARIOS[name]
            if role not in s['roles']:raise ValueError('Unknown role')
            if route.path=='/api/scenario':
                info=s['roles'][role]
                visible=s['issues'] if is_fixed(s) else [i for i in s['issues'] if i['name'] in s['required_issues']]
                return self.respond({'title':s['title'],'role_html':narrative_to_html(info['narrative']),
                    'instructions':s['readrole_instructions'],'required':s['required_issues'],'fixed':is_fixed(s),
                    'table':info['determinatescoretable'],'continuous':info['continuous_scoring'],
                    'fields':[field(i) for i in visible]})
            if route.path=='/api/issue':
                issue=next((i for i in s['issues'] if i['name']==query.get('issue',[''])[0]),None)
                if not issue:raise ValueError('Issue name not found in this scenario')
                return self.respond(field(issue))
            if route.path=='/api/state':
                with LOCK:return self.respond(state(name,role))
            return self.respond({'error':'Not found'},404)
        except (ValueError,KeyError) as exc:self.respond({'error':str(exc)},400)

    def do_POST(self):
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>64000:raise ValueError('Request too large')
            data=json.loads(self.rfile.read(length))
            name=data['scenario'];role=data['role'];s=SCENARIOS[name]
            if role not in s['roles']:raise ValueError('Unknown role')
            route=urlparse(self.path).path
            with LOCK:
                if route=='/api/reset':
                    GAMES[name]={'offers':[],'accepted':set()};return self.respond(state(name,role))
                if route in ('/api/score','/api/send'):
                    result=score(name,role,data['choices'])
                    if route=='/api/score':return self.respond(view_result(result))
                    if not result['proposal_allowed']:raise ValueError('Review and correct the offer before sending')
                    GAMES[name]['offers'].append({'author':role,'choices':data['choices']})
                    GAMES[name]['accepted']=set()
                    return self.respond(state(name,role))
                if route=='/api/accept':
                    current=state(name,role)
                    if not current['can_accept']:raise ValueError('This offer must be worth more than zero to you before you can accept it.')
                    GAMES[name]['accepted'].add(role)
                    return self.respond(state(name,role))
                return self.respond({'error':'Not found'},404)
        except (ValueError,KeyError,TypeError) as exc:self.respond({'error':str(exc)},400)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=3136)
    args=parser.parse_args();load()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Local Empirica integration preview: http://127.0.0.1:{args.port}/',flush=True)
    server.serve_forever()


if __name__=='__main__':main()
