"""Python script A2-2: apply fitted job rules, check terms and calculate scores."""
from runtime_setup import a2_setup
from stage_support import stage_main

def score_interpretation(case, interpretation, exercise='job'):
    """Apply the evaluated custom rules and return the checked scored offer as JSON."""
    if exercise != 'job': raise ValueError('The numbered A2 job stages do not replace the separate tutorial path.')
    a2_setup('job')
    import a2_finalize
    return a2_finalize.finalize(case, interpretation)

if __name__ == '__main__': stage_main(score_interpretation, scoring=True, job_only=True)
