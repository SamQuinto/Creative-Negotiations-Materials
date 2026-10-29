"""Python script A1-2: check and score an interpretation. No model is called."""
from runtime_setup import a1_setup
from stage_support import stage_main

def score_interpretation(case, interpretation, exercise='job'):
    """Check supported terms, look up assigned values and return scored JSON."""
    scorer = a1_setup(exercise)
    return scorer.for_empirica(scorer.finalize(case['offer'], interpretation, case['role'], case.get('previous_offer', '')))

if __name__ == '__main__': stage_main(score_interpretation, scoring=True)
