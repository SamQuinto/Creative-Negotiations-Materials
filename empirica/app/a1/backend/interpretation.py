"""A1 reusable interpretation and checking; exercise facts come from files.

Functions retain the evaluated request wording and checking behavior. The
runner supplies a prompt path, response format, scoring function and settings.
"""
from __future__ import annotations
import json
import math
import unicodedata
import re
from scenario import active_scoring_scenario
DEFAULT_MODEL = None
DEFAULT_REASONING = None
REASONING_LEVELS = ('low', 'medium', 'high', 'xhigh', 'max')
PROMPT_FILE = None
SCHEMA_FILE = None
score_pair = None
VERSION = 'full-catalogue-v2.1-2026-10-22-general-prompt'


def catalogue(scenario):
    """Every active issue, with meanings/choices but no private payoff weights."""
    scenario = active_scoring_scenario(scenario)
    result = []
    keys = ('name', 'definition', 'description', 'kind', 'value_type', 'unit', 'aliases',
            'proposal_domain', 'default_period', 'usual_value', 'assume_year',
            'natural_date_conventions', 'weekly_to_annual_factor',
            'bare_request_default', 'commitment_scale', 'interpretation_notes')
    for issue in scenario['issues']:
        item = {k: issue[k] for k in keys if k in issue}
        item['required'] = issue['name'] in scenario.get('required_issues', [])
        if issue['kind'] == 'discrete':
            item['choices'] = [o['label'] for o in issue.get('options', [])]
        else:
            item['reference_values'] = [issue.get('min'), issue.get('max')]
            item['permitted_values'] = issue.get('proposal_domain', {'min': issue.get('min'), 'max': issue.get('max')})
            item['reference_values_are_not_limits'] = 'proposal_domain' in issue
            if issue.get('value_type')=='date' and str(issue.get('min',''))[:4]==str(issue.get('max',''))[:4]:
                item['default_year']=int(str(issue['min'])[:4])
        result.append(item)
    return result

def schema(scenario):
    scenario = active_scoring_scenario(scenario)
    names = [i['name'] for i in scenario['issues']]
    result = json.loads(SCHEMA_FILE.read_text(encoding='utf-8'))
    result['properties']['pairs']['items']['properties']['issue']['enum'] = names
    result['properties']['ambiguities']['items']['properties']['issue']['enum'] = names + ['General offer']
    return result


def master_prompt():
    """One editable, scenario-independent set of instructions."""
    text = PROMPT_FILE.read_text(encoding='utf-8').strip()
    if not text:
        raise ValueError('The V2 master prompt is empty.')
    return text

def conventions(scenario):
    """Read study information from the scenario, without recognizing its topic."""
    scenario = active_scoring_scenario(scenario)
    result = {'title': scenario.get('title', ''), 'required_issues': scenario.get('required_issues', []),
              'outside_catalogue_policy': scenario.get('issue_space', {}).get('unknown_term_policy', 'reject')}
    result['role_descriptions']={role:data.get('summary','') for role,data in scenario.get('roles',{}).items()}
    if scenario.get('parties'):
        result['role_names']={role:data.get('name',role) for role,data in scenario['parties'].items()}
    guidance = scenario.get('offer_interpretation', {})
    if not isinstance(guidance, dict):
        raise ValueError('offer_interpretation must be an object in the scenario file.')
    notes = guidance.get('notes', [])
    if not isinstance(notes, list) or any(not isinstance(note, str) for note in notes):
        raise ValueError('offer_interpretation.notes must be a list of plain-language notes.')
    if notes:
        result['interpretation_notes'] = notes
    return result

def request_payload(text, scenario, previous_offer='', model=DEFAULT_MODEL, reasoning=DEFAULT_REASONING, role=None):
    # Stable catalogue and instructions precede the changing offer, permitting
    # caching without omitting any definitions. No expected answer is included.
    scenario = active_scoring_scenario(scenario)
    if reasoning not in REASONING_LEVELS:
        raise ValueError('Choose a supported reasoning setting: ' + ', '.join(REASONING_LEVELS))
    role = role or next(iter(scenario.get('roles', {})), None)
    if role not in scenario.get('roles', {}):
        raise ValueError('Please choose a role from the loaded scenario.')
    context = json.dumps({'scenario': conventions(scenario), 'issues': catalogue(scenario)}, ensure_ascii=False, separators=(',', ':'))
    return {'model': model, 'store': False, 'reasoning': {'effort': reasoning},
        'max_output_tokens': 6000,
        'input': [{'role': 'developer', 'content': master_prompt()},
                  {'role': 'developer', 'content': 'Scenario data and complete active catalogue:\n' + context},
                  {'role': 'user', 'content': json.dumps({'proposer_role': role, 'offer': text, 'previous_offer': previous_offer}, ensure_ascii=False)}],
        'text': {'format': {'type': 'json_schema', 'name': 'offer_interpretation_v2', 'strict': True, 'schema': schema(scenario)}}}

def _plain(text):
    return ' '.join(unicodedata.normalize('NFKC', str(text)).split()).casefold()

def _quoted(quote, text):
    if bool(_plain(quote)) and _plain(quote) in _plain(text):return True
    # Formatting differences are not differences in meaning. Require the same
    # contiguous words and numeric tokens; never fuzzy-match a different word.
    tokens=lambda s:re.findall(r'\d+(?:[.,]\d+)*|[^\W\d_]+',_plain(s),re.UNICODE)
    q=tokens(quote);t=tokens(text)
    return bool(q) and any(t[i:i+len(q)]==q for i in range(len(t)-len(q)+1))

def finalize(text, role, interpretation, scenario, previous_offer=''):
    """Generic schema/evidence/domain checks only; no V1 language filters."""
    scenario = active_scoring_scenario(scenario)
    roles = list(scenario.get('roles', {}))
    if role not in roles or len(roles) != 2:
        raise ValueError('V2 currently expects a configured dyadic scenario and one of its roles.')
    other = next(r for r in roles if r != role)
    names = {i['name'] for i in scenario['issues']}
    findings, choices, lines, audit = [], {}, [], []
    ref = interpretation.get('explicit_reference', '')
    can_inherit = bool(previous_offer and _quoted(ref, text))
    if ref and not can_inherit:
        findings.append({'code': 'invalid_reference', 'issue': 'General offer', 'message': 'Please state which earlier offer you want to use.'})
    for item in interpretation.get('ambiguities', []):
        findings.append({'code': 'model_ambiguity', 'issue': item['issue'], 'message': item['question'], 'source_text': item['source_text']})
    seen = set()
    for pair in interpretation.get('pairs', []):
        name, value = pair.get('issue'), str(pair.get('option', ''))
        source = pair.get('source_text', '')
        inherited = bool(pair.get('from_previous_offer'))
        if name not in names:
            findings.append({'code': 'unknown_issue', 'issue': str(name), 'message': 'This feature is not in the active catalogue.'}); continue
        if name in seen:
            findings.append({'code': 'duplicate_choice', 'issue': name, 'message': f'Please give one final choice for {name}.'}); continue
        seen.add(name)
        supported = _quoted(source, previous_offer if inherited else text)
        if (inherited and not can_inherit) or not supported:
            findings.append({'code': 'unsupported_quote', 'issue': name, 'message': f'Please confirm your choice for {name}.'})
            audit.append({**pair, 'handling': 'needs_confirmation'}); continue
        try:
            label, own = score_pair(name, value, role, {}, scenario)
            _, theirs = score_pair(name, value, other, {}, scenario)
            if not all(math.isfinite(n) for n in (own, theirs)): raise ValueError('Please provide a finite value.')
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            findings.append({'code': 'invalid_value', 'issue': name, 'message': f'{name}: {exc}.', 'stated_choice': value})
            audit.append({**pair, 'handling': 'invalid_value'}); continue
        choices[name] = label
        lines.append({'issue': name, 'option': label, 'points': own, 'counterpart_points': theirs})
        audit.append({**pair, 'handling': 'scored', 'scored_choice': label})
    for name in scenario.get('required_issues', []):
        if name not in choices and not any(f.get('issue') == name for f in findings):
            findings.append({'code': 'missing_required', 'issue': name, 'message': f'Please add your choice for {name}.'})
    novel = interpretation.get('novel_terms', [])
    if novel and scenario.get('issue_space', {}).get('unknown_term_policy') != 'capture_unscored':
        findings.append({'code': 'outside_catalogue', 'issue': 'General offer', 'message': 'Please use only the available issues in this condition.'})
    intent = interpretation.get('offer_intent', 'uncertain')
    if intent != 'offer':
        findings.append({'code': 'offer_intent', 'issue': 'General offer', 'message': 'Please state one offer you want to propose.'})
    decision = 'scorable' if not findings else 'clarification_needed'
    own_total = sum(l['points'] for l in lines) if decision == 'scorable' else None
    other_total = sum(l['counterpart_points'] for l in lines) if decision == 'scorable' else None
    message = ' '.join(dict.fromkeys(f['message'] for f in findings)) or 'Please check this interpretation before sending your offer.'
    rules = scenario.get('proposal_rules', {})
    allowed = decision == 'scorable' and (not rules.get('require_positive_proposer', True) or own_total > rules.get('positive_threshold', 0))
    result = {'decision': decision, 'valid_pairs': choices, 'lines': lines, 'findings': findings,
        'total': own_total, 'total_for_proposer': own_total, 'total_for_receiver': other_total,
        'proposal_allowed': bool(allowed), 'proposer_role': role, 'receiver_role': other,
        'message': message, 'display_text': message + '\n' + '\n'.join(f"- {l['issue']}: {l['option']} ({l['points']:+.2f})" for l in lines),
        'extraction': interpretation, 'novel_terms': novel, 'unpriced_details': [{'detail': n, 'meaning': 'Recorded without an improvised payoff.'} for n in novel],
        'unsupported_terms': interpretation.get('unsupported_terms', []), 'interpretation_audit': audit,
        'scorer_version': VERSION, 'scenario_id': scenario.get('scenario_id'), 'scenario_issue_count': len(scenario['issues']),
        'architecture': 'full_catalogue_generic_checks', 'agreement_rules': scenario.get('agreement_rules', {})}
    if can_inherit:
        result['revision_confirmation'] = {'previous_offer': previous_offer, 'submitted_change': text,
            'prompt': 'Please confirm that this is the complete revised offer you meant.', 'interpreted_lines': [f'{k}: {v}' for k, v in choices.items()]}
    return result
