"""Python script A2-1: retrieve issue definitions and prepare the job request."""
from runtime_setup import a2_setup
from stage_support import stage_main

def prepare_request(case, exercise='job', reasoning='low'):
    """Select relevant definitions and prepare one JSON request without an API call."""
    if exercise != 'job': raise ValueError('The numbered A2 job stages do not replace the separate tutorial path.')
    if reasoning != 'low': raise ValueError('The evaluated A2 configuration uses low reasoning.')
    import a2_extract
    a2_extract.STREAM = a2_setup('job'); a2_extract.ROLE = case['role']; a2_extract.RUN_ID = None
    a2_extract.RECEIPTS.clear(); a2_extract.TRACE.clear()
    return a2_extract.build_request(case['offer'], case.get('previous_offer', ''), model='gpt-5.6-luna')

if __name__ == '__main__': stage_main(prepare_request, job_only=True)
