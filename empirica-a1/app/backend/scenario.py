"""Read the active issues declared in an exercise file."""
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
