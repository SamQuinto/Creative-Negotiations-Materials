"""A1 request preparation, deterministic scoring and Empirica response formatting."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path

import interpretation
import offer_engine
from api_budget import Ledger, PRICES, guarded_post, live_post

APP = Path(__file__).resolve().parents[1]
PACKAGE = APP.parents[1]
VERSION = 'A1-empirica-2026-10-27'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def api_key():
    value = os.environ.get('OPENAI_API_KEY', '').strip()
    path = PACKAGE / 'app/openai_key.txt'
    if not value and path.is_file():
        value = path.read_text(encoding='utf-8-sig').strip()
    if not value or value == 'YOUR_OPENAI_API_KEY_HERE':
        raise ValueError('Set OPENAI_API_KEY or put your key in app/openai_key.txt.')
    return value


class Scorer:
    def __init__(self, scenario_file=None, *, helper=True, model=None, reasoning=None,
                 reading_notes=None):
        self.scenario_file = Path(scenario_file or APP / 'scoring_table.json').resolve()
        self.table = read_json(self.scenario_file)
        self.settings = read_json(APP / 'model_settings.json')
        self.model = model or self.settings['model']
        self.reasoning = reasoning or self.settings['reasoning']
        self.helper = helper
        guide = self.settings.get('guidance', {})
        self.notes_file = Path(reading_notes).resolve() if reading_notes else (
            APP / guide['file'] if guide.get('scenario_id') == self.table.get('scenario_id')
            and guide.get('file') else None)
        interpretation.PROMPT_FILE = APP / 'prompts/general_interpretation.txt'
        interpretation.SCHEMA_FILE = APP / 'formats/interpretation.json'
        interpretation.score_pair = offer_engine.score_pair

    def request(self, text, role='Candidate', previous_offer=''):
        request = interpretation.request_payload(
            text, self.table, previous_offer, self.model, self.reasoning, role)
        if self.helper and self.notes_file:
            notes = self.notes_file.read_text(encoding='utf-8').strip()
            request['input'][1]['content'] += '\n\nScenario-specific reading notes:\n' + notes
        return request

    def finalize(self, text, response, role='Candidate', previous_offer=''):
        """Preserve the evaluated A1 checks before formatting for Empirica."""
        if not isinstance(response, dict) or not isinstance(response.get('pairs'), list):
            raise ValueError('The interpretation must contain a pairs list.')
        return interpretation.finalize(text, role, deepcopy(response), self.table, previous_offer)

    def structured(self, choices, role='Candidate'):
        """Score explicitly selected choices without asking a model to interpret text."""
        if not isinstance(choices, dict) or not choices:
            raise ValueError('choices-json must be a non-empty object.')
        pairs = []
        known = {item['name']: item for item in self.table['issues']}
        recognized = offer_engine._scenario_issue_map(self.table)
        names_by_id = {item['id']: item['name'] for item in self.table['issues'] if item.get('id')}
        for issue, value in choices.items():
            issue = names_by_id.get(issue, issue)
            if issue not in known and issue in recognized:
                issue = recognized[issue]['name']
            if value is None or isinstance(value, (bool, dict, list)):
                raise ValueError('Each explicit choice must be a string or number.')
            option = str(value)
            pairs.append({'issue': issue, 'option': option,
                          'source_text': f'{issue}: {option}', 'from_previous_offer': False})
        text = '\n'.join(pair['source_text'] for pair in pairs)
        response = {'pairs': pairs, 'ambiguities': [], 'novel_terms': [],
                    'unsupported_terms': [], 'offer_intent': 'offer',
                    'explicit_reference': '', 'interpretation_notes': []}
        return self.finalize(text, response, role)

    def live(self, text, role, previous_offer, ledger_path=None, budget=None):
        prices = self.settings.get('api_prices_per_million')
        if not isinstance(prices, list) or len(prices) != 3 or not all(
            isinstance(p, (float, int)) and math.isfinite(p) and p >= 0 for p in prices):
            raise ValueError('Configure verified input, cached-input and output prices.')
        if self.model != self.settings['model']:
            raise ValueError('For a different model, update app/model_settings.json and its prices together.')
        PRICES[self.model] = tuple(prices)
        request = self.request(text, role, previous_offer)
        if budget is None:
            # Study scoring must not inherit a shared development-budget lock.
            body, receipt = live_post('https://api.openai.com/v1/responses', request,
                api_key(), timeout=120)
        else:
            if ledger_path is None:
                raise ValueError('A ledger path is required for an explicit API budget.')
            body, receipt = guarded_post('https://api.openai.com/v1/responses', request,
                api_key(), Ledger(ledger_path, budget), 'A1_main_offer', timeout=120)
        if body.get('status') != 'completed':
            raise ValueError('The model response did not complete. Please try scoring again.')
        parts = [part for item in body.get('output', []) for part in item.get('content', [])]
        if any(part.get('type') == 'refusal' for part in parts):
            raise ValueError('The model could not interpret this offer. Please rephrase it.')
        content = ''.join(part.get('text', '') for part in parts if part.get('type') == 'output_text')
        if not content:
            raise ValueError('The model returned no interpretation. Please try scoring again.')
        try:
            response = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError('The model returned an unreadable interpretation. Please try scoring again.') from None
        result = self.finalize(text, response, role, previous_offer)
        return result, receipt

    def version(self):
        files = [PACKAGE / 'score_offer.py', self.scenario_file,
                 APP / 'model_settings.json', APP / 'prompts/general_interpretation.txt',
                 APP / 'formats/interpretation.json',
                 Path(__file__), APP / 'backend/interpretation.py',
                 APP / 'backend/offer_engine.py', APP / 'backend/scenario.py',
                 APP / 'backend/scenario_rules.py', APP / 'backend/api_budget.py']
        if self.helper and self.notes_file:
            files.append(self.notes_file)
        return {'architecture': 'A1', 'scorer_version': VERSION, 'model': self.model,
                'reasoning': self.reasoning, 'guidance_enabled': bool(self.helper and self.notes_file),
                'scenario_id': self.table.get('scenario_id'),
                'issue_count': len(interpretation.catalogue(self.table)),
                'sha256': {str(f.relative_to(PACKAGE)) if f.is_relative_to(PACKAGE) else f.name:
                           hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}

    def for_empirica(self, raw, *, mode='live', receipt=None):
        """Keep the existing CLI response fields and string-list breakdown format."""
        result = deepcopy(raw)
        rows = result['lines']
        render = lambda row, key: f"- {row['issue']}: {row['option']}  [{row[key]:+.2f}]"
        result['issue_breakdown'] = rows
        result['lines'] = [render(row, 'points') for row in rows]
        result['lines_for_receiver'] = [render(row, 'counterpart_points') for row in rows] if raw['decision'] == 'scorable' else []
        missing = [i for i in self.table.get('required_issues', []) if i not in raw['valid_pairs']]
        messages = list(dict.fromkeys(f['message'] for f in raw.get('findings', [])))
        result.update(any_valid=bool(rows), invalid_present=bool(raw.get('findings')),
                      required_ok=not missing, missing_required=missing, messages=messages,
                      required_issues=self.table.get('required_issues', []))
        rule = self.table.get('proposal_rules', {})
        result['proposal_rule'] = {
            'require_positive_proposer': rule.get('require_positive_proposer', True),
            'positive_threshold': rule.get('positive_threshold', 0),
            'counterpart_score_affects_submission': False,
            'unknown_term_policy': self.table.get('issue_space', {}).get('unknown_term_policy', 'reject')}
        display = messages + result['lines']
        if raw['total'] is not None:
            display.append(f"Total: {raw['total']:+.2f}")
        else:
            display.append('Please check the points above and calculate again.')
        for heading, key in [('Recorded without points:', 'novel_terms'),
                             ('Not scored:', 'unsupported_terms')]:
            if raw.get(key):
                display.append(heading)
                display.extend('- ' + str(value) for value in raw[key])
        result['display_text'] = '\n'.join(display)
        selected_model = self.model if mode == 'live' else mode
        result.update(architecture='A1', scorer_version=VERSION,
                      interpretation_version=raw['scorer_version'], provider='openai',
                      model=selected_model, reasoning=self.reasoning,
                      guidance_enabled=bool(self.helper and self.notes_file),
                      scenario_schema_version=self.table.get('schema_version'),
                      material_revision=self.table.get('material_revision'),
                      scenario_variant=self.table.get('scenario_variant', {}).get('id'),
                      extraction_usage={'input_tokens': 0, 'output_tokens': 0},
                      scorer_routing={'policy': 'A1_full_table', 'selected': selected_model,
                                      'calls': 1 if mode == 'live' else 0})
        if receipt:
            result['api_receipt'] = receipt
            result['extraction_usage'] = {key: receipt[key] for key in
                ('input_tokens', 'cached_input_tokens', 'output_tokens')}
        if raw.get('revision_confirmation'):
            result['relative_revision'] = True
        return result
