"""Live API requests and opt-in test-budget accounting. Standard-library only.

Live requests do not read or change a shared budget ledger. An API failure affects
that request, not later offers. Explicitly budgeted tests retain the conservative
SQLite reservations and uncertain-billing lock. Neither mode retries automatically.
Keys and HTTP authorization headers are never saved in the ledger.
"""
from __future__ import annotations
import hashlib
import json
import math
import sqlite3
import time
import urllib.error
import urllib.request
import uuid
from contextlib import contextmanager
from pathlib import Path

PRICES={'gpt-5.6-luna':(.20,.02,1.20),'gpt-5-nano':(.05,.005,.40)}

class BudgetStop(RuntimeError):pass
class BillingUncertain(BudgetStop):pass


def live_post(url, payload, key, timeout=90):
    """Send one study request, with no persistent budget lock and no retries."""
    if url not in ('https://api.openai.com/v1/responses', 'https://api.openai.com/v1/chat/completions'):
        raise ValueError('Only the explicit OpenAI endpoints are allowed.')
    request = urllib.request.Request(url,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
        method='POST')
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        # Do not expose provider error bodies, which can include private key text.
        code = ''
        try:
            error = json.loads(exc.read().decode('utf-8')).get('error', {})
            if isinstance(error, dict):
                code = error.get('code', '')
        except (ValueError, UnicodeError, AttributeError):
            pass
        if exc.code in (401, 403):
            message = 'API authentication or access failed. Please check the server API key and permissions.'
        elif exc.code == 429 and code in (
                'insufficient_quota', 'credit_balance_exhausted',
                'organization_spend_limit_exceeded', 'project_spend_limit_exceeded',
                'organization_usage_limit_exceeded', 'billing_hard_limit_reached'):
            message = 'The API account has reached a credit, spending or usage limit. Please check the account.'
        elif exc.code == 429:
            message = 'The scoring service is temporarily rate-limited. Please wait before calculating again.'
        elif exc.code >= 500 or exc.code in (408, 409):
            message = 'The scoring service is temporarily unavailable. Please wait briefly and calculate again.'
        else:
            message = 'The API rejected this scoring request. Please check the server configuration.'
        raise BudgetStop(f'{message} (HTTP {exc.code}.) No automatic retry was made.') from None
    except (TimeoutError, urllib.error.URLError, OSError):
        raise BudgetStop('The scoring request could not be completed because of a connection problem or timeout. '
                         'Please wait briefly before calculating again. No automatic retry was made.') from None
    except (ValueError, UnicodeError):
        raise BudgetStop('The scoring service returned an unreadable response. '
                         'Please calculate again. No automatic retry was made.') from None
    if not isinstance(body, dict):
        raise BudgetStop('The scoring service returned an unreadable response. Please calculate again.')
    return body, _live_receipt(payload, body)


def _live_receipt(payload, body):
    """Estimate cost from reported usage; accounting must not discard a valid offer."""
    usage = body.get('usage') or {}
    usage = usage if isinstance(usage, dict) else {}
    detail = usage.get('input_tokens_details', usage.get('prompt_tokens_details')) or {}
    detail = detail if isinstance(detail, dict) else {}
    inp = usage.get('input_tokens', usage.get('prompt_tokens'))
    out = usage.get('output_tokens', usage.get('completion_tokens'))
    cached = detail.get('cached_tokens', 0) or 0
    requested, returned = payload['model'], body.get('model', '')
    valid_usage = all(isinstance(v, int) and not isinstance(v, bool) and v >= 0
                      for v in (inp, out, cached)) and cached <= inp
    receipt = dict(response_id=body.get('id'), model=returned,
        input_tokens=inp if valid_usage else None,
        cached_input_tokens=cached if valid_usage else None,
        output_tokens=out if valid_usage else None,
        estimated_cost_usd=None, standard_token_estimate_usd=None,
        accounting_mode='usage_estimate_no_budget_ledger')
    if valid_usage and requested in PRICES and isinstance(returned, str) and (
            returned == requested or returned.startswith(requested + '-')):
        a, b, c = PRICES[requested]
        receipt['standard_token_estimate_usd'] = ((inp-cached)*a + cached*b + out*c) / 1e6
        receipt['estimated_cost_usd'] = ((inp-cached)*a*(1.25 if requested == 'gpt-5.6-luna' else 1)
                                         + cached*b + out*c) / 1e6
    else:
        receipt['accounting_warning'] = 'Usage or model could not be priced safely; no cost estimate is reported.'
    return receipt


class Ledger:
    def __init__(self,path,limit):
        self.path=Path(path).resolve();self.path.parent.mkdir(parents=True,exist_ok=True)
        if not math.isfinite(limit) or not 0 < limit <= 45:raise ValueError('Dispatch limit must be >0 and <=45 USD.')
        self.limit=float(limit)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, limit_usd REAL NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, stage TEXT, model TEXT, status TEXT, reserved REAL, cost REAL, started REAL, ended REAL, request TEXT, response TEXT, error TEXT)')
            db.execute('INSERT OR IGNORE INTO config VALUES (1,?)',(self.limit,))
            old=db.execute('SELECT limit_usd FROM config WHERE id=1').fetchone()[0]
            if abs(old-self.limit)>1e-9:raise ValueError('Saved ledger limit differs. Do not silently reset or raise a budget.')
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=30)
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:yield db
        finally:db.close()
    def status(self):
        with self.connect() as db:
            rows=db.execute('SELECT status,reserved,cost FROM calls').fetchall()
        return dict(calls=len(rows),spent=sum(r[2] or 0 for r in rows),reserved=sum(r[1] for r in rows if r[0] in ('reserved','unknown')),unresolved=sum(r[0] in ('reserved','unknown') for r in rows),unknown=sum(r[0]=='unknown' for r in rows),limit=self.limit)
    def reserve(self,stage,payload):
        model=payload['model']
        if model not in PRICES:raise ValueError('Unpriced model refused: '+model)
        raw=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        # A byte-level upper bound plus framing/schema allowance. Stay below the
        # model's long-context pricing threshold; no tools/images in this client.
        if len(raw)>200000:raise BudgetStop('Context exceeds the frozen 200,000-byte request policy. Nothing was truncated or sent.')
        ceiling=payload.get('max_output_tokens',payload.get('max_completion_tokens'))
        if not isinstance(ceiling,int) or not 0<ceiling<=8000:raise ValueError('A bounded output ceiling is required.')
        inp,_,out=PRICES[model]
        amount=((len(raw)+2048)*inp*1.25+ceiling*out)/1e6
        ident=uuid.uuid4().hex
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows=db.execute('SELECT status,reserved,cost FROM calls').fetchall()
            if any(r[0]=='unknown' for r in rows):raise BillingUncertain('An earlier request has unknown billing. Reconcile before continuing.')
            total=sum((r[2] or 0)+(r[1] if r[0] in ('reserved','unknown') else 0) for r in rows)
            if total+amount>self.limit:raise BudgetStop('Shared API budget would be exceeded; request was not sent.')
            db.execute('INSERT INTO calls VALUES (?,?,?,?,?,?,?,?,?,?,?)',(ident,stage,model,'reserved',amount,0,time.time(),None,raw.decode(),None,None))
        return ident
    def uncertain(self,ident,error):
        with self.connect() as db:db.execute("UPDATE calls SET status='unknown',ended=?,error=? WHERE id=?",(time.time(),str(error)[:1000],ident))
    def rejected(self,ident,error):
        with self.connect() as db:db.execute("UPDATE calls SET status='http_rejected',ended=?,error=? WHERE id=?",(time.time(),str(error)[:1000],ident))
    def finish(self,ident,body):
        with self.connect() as db:
            requested,reserved=db.execute('SELECT model,reserved FROM calls WHERE id=?',(ident,)).fetchone()
        returned=body.get('model','')
        usage=body.get('usage') or {}
        inp=usage.get('input_tokens',usage.get('prompt_tokens'))
        out=usage.get('output_tokens',usage.get('completion_tokens'))
        detail=usage.get('input_tokens_details',usage.get('prompt_tokens_details')) or {}
        cached=detail.get('cached_tokens',0) or 0
        if not all(isinstance(v,int) and not isinstance(v,bool) and v>=0 for v in (inp,out,cached)) or cached>inp or not (returned==requested or returned.startswith(requested+'-')):
            self.uncertain(ident,'Missing/invalid usage or unexpected returned model.')
            raise BillingUncertain('Response usage/model could not be priced safely.')
        a,b,c=PRICES[requested]
        # Conservatively allow the documented cache-write premium on all uncached
        # Luna input; the undiscounted token estimate remains separately available.
        token_cost=((inp-cached)*a+cached*b+out*c)/1e6
        cost=((inp-cached)*a*(1.25 if requested=='gpt-5.6-luna' else 1)+cached*b+out*c)/1e6
        with self.connect() as db:
            db.execute("UPDATE calls SET status=?,cost=?,ended=?,response=? WHERE id=?",('unknown' if cost>reserved else 'completed',cost,time.time(),json.dumps(body,ensure_ascii=False),ident))
        if cost>reserved:raise BillingUncertain('Usage exceeded its conservative reservation; further dispatch suspended.')
        return dict(call_id=ident,response_id=body.get('id'),model=returned,input_tokens=inp,cached_input_tokens=cached,output_tokens=out,estimated_cost_usd=cost,standard_token_estimate_usd=token_cost)
    def export(self):
        with self.connect() as db:
            db.row_factory=sqlite3.Row
            rows=[dict(row) for row in db.execute('SELECT * FROM calls ORDER BY started')]
        for row in rows:
            for field in ('request','response'):
                if row[field]:row[field]=json.loads(row[field])
        return rows

def guarded_post(url,payload,key,ledger,stage,timeout=90):
    if url not in ('https://api.openai.com/v1/responses','https://api.openai.com/v1/chat/completions'):
        raise ValueError('Only the explicit OpenAI endpoints are allowed.')
    ident=ledger.reserve(stage,payload)
    request=urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:body=json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        # Explicit ordinary 4xx rejections have no completed model response;
        # timeout/conflict/server failures remain conservatively unresolved.
        if 400<=exc.code<500 and exc.code not in (408,409):ledger.rejected(ident,'HTTP '+str(exc.code))
        else:ledger.uncertain(ident,'HTTP '+str(exc.code))
        raise BudgetStop('OpenAI request stopped: HTTP '+str(exc.code)) from None
    except Exception as exc:
        ledger.uncertain(ident,type(exc).__name__)
        raise BillingUncertain('OpenAI response uncertain; reservation retained, no automatic retry.') from exc
    metadata=ledger.finish(ident,body)
    return body,metadata
