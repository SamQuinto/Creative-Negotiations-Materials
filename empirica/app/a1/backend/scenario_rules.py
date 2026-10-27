"""Shared participant disclosure and agreement rules (no model calls).

The configured scenario, not issue count or a UI default, determines which
terms are mandatory and whether an own-payoff table is disclosed.
"""
import math
from datetime import date


def is_fixed(scenario):
    design = (scenario or {}).get('review_design', {})
    return bool(design.get('all_terms_explicit') or design.get('all_15_terms_explicit'))


def active_scoring_scenario(scenario):
    """Keep stored catalogue entries out of scoring when a task restricts its agenda."""
    if not isinstance(scenario, dict) or 'active_issues' not in scenario:
        return scenario
    names = scenario['active_issues']
    if not isinstance(names, list) or not names or len(names) != len(set(names)):
        raise ValueError('active_issues must list distinct issue names.')
    known = {issue['name']: issue for issue in scenario.get('issues', [])}
    if any(name not in known for name in names):
        raise ValueError('An active issue is missing from the stored catalogue.')
    if not set(scenario.get('required_issues', [])).issubset(names):
        raise ValueError('Required issues must be active.')
    if set(known) == set(names):
        return scenario
    return {**scenario, 'issues': [known[name] for name in names]}


def required_instruction(scenario):
    names = scenario.get('required_issues', [])
    instruction = 'Every offer must explicitly state: ' + ', '.join(names) + '.'
    if is_fixed(scenario):
        instruction += (f' Include all {len(names)} issues, including unchanged choices. A listed No commitment or No participation is a choice, not an omission. Do not add issues outside this table.')
    else:
        instruction += ' You may include any number of additional terms supported by your role materials.'
    return instruction


def participant_text(scenario, role):
    text = str(scenario['roles'][role]['full_text']).strip()
    rows = private_payoff_rows(scenario, role) if is_fixed(scenario) else []
    if rows:
        text += '\n\nYOUR PRIVATE PAYOFF TABLE — only your own points\n'
        text += '\n'.join(' | '.join(str(cell) for cell in row) for row in rows)
    return text


def private_payoff_rows(scenario, role):
    """Derive the private table from current issue definitions, never a stale copy."""
    from offer_engine import score_pair
    scenario = active_scoring_scenario(scenario)
    rows = []
    for issue in scenario['issues']:
        name = issue['name']
        unit = scenario.get('display_units', {}).get(name, issue.get('unit', ''))
        if issue['kind'] == 'continuous':
            samples = scenario.get('table_negotiation', {}).get('samples', {}).get(name) or issue.get('samples') or [issue['min'], issue['max']]
            values = []
            for value in samples:
                if issue.get('value_type') == 'date':
                    label = date.fromisoformat(value).strftime('%B %d').replace(' 0', ' ')
                elif issue.get('value_type') == 'currency':
                    label = f'${value:,.0f}'
                else:
                    label = f'{value:g}' if isinstance(value, (int, float)) else str(value)
                _, points = score_pair(name, str(value), role, {}, scenario)
                shown = f'{points:+.2f}'.rstrip('0').rstrip('.')
                values.append(f'{label}: {shown}')
            proposal_domain = issue.get('proposal_domain')
            if scenario.get('table_negotiation', {}).get('choices_are_exhaustive'):
                kind_label = f'Listed choices · {unit}'
                value_label = '; '.join(values)
            elif isinstance(proposal_domain, dict) and proposal_domain.get('max') is None:
                kind_label = f'Open amount · {unit}'
                value_label = 'Scoring anchors — ' + '; '.join(values) + '. Amounts outside these anchors continue at the same rate.'
            else:
                kind_label = f'Continuous · {unit}'
                value_label = '; '.join(values)
                if isinstance(proposal_domain, dict):
                    value_label += f". Scoring anchors, not proposal limits. You may propose {proposal_domain.get('min')}–{proposal_domain.get('max')} {unit}; points continue at the same rate."
            rows.append([name, kind_label, value_label])
        else:
            rows.append([name, 'Choice-based', '; '.join(f"{opt['label']}: {opt[role]:+g}" for opt in issue['options'])])
    return rows


def positive_agreement_required(scenario):
    rules = scenario.get('agreement_rules', {})
    return bool(rules.get('require_positive_each_party') or rules.get('comparison') == '>')


def own_acceptance_allowed(scenario, total):
    if isinstance(total, bool) or total is None:
        return False
    try:
        value = float(total)
    except (ValueError, TypeError):
        return False
    if not math.isfinite(value):
        return False
    threshold = float(scenario.get('agreement_rules', {}).get('threshold', 0))
    return value > threshold if positive_agreement_required(scenario) else value >= threshold
