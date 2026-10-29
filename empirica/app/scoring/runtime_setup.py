"""Find the included scorers even if their outer folder has been moved or renamed."""
from pathlib import Path
import io, json, os, sys, types, urllib.request, urllib.error
import common1225 as c
ROOT = Path(__file__).resolve().parent

def data_dir(exercise):
    return ROOT / 'frozen/tutorial' if exercise == 'tutorial' else ROOT / 'frozen'

def a1_setup(exercise):
    sys.path.insert(0, str(ROOT.parent / 'a1/backend'))
    from scorer import Scorer
    return Scorer(data_dir(exercise) / 'Scoring_Table.json', helper=False, model='gpt-6.1-sol')

class PreviewReady(Exception):
    def __init__(self, request): self.request = request

def a2_setup(exercise, preview=False):
    os.environ.update(NEGOTIATOR_SCENARIO_FILE=str(data_dir(exercise) / 'Scoring_Table.json'), NEGOTIATOR_PROVIDER='openai', NEGOTIATOR_MODEL='gpt-5.6-luna', NEGOTIATOR_SCORER_ROUTING='single')
    os.environ.pop('NEGOTIATOR_API_LEDGER', None)
    if exercise == 'job': a1_setup(exercise)
    else:
        for name in ['scenario', 'scenario_rules', 'offer_engine', 'api_budget']: sys.modules.pop(name, None)
    sys.path.insert(0, str(ROOT.parent / 'backend'))
    import stream
    if exercise == 'tutorial':
        if preview: stream._api_key = lambda: 'REQUEST_PREVIEW_ONLY'
        def post(request, timeout=45):
            req = json.loads(request.data.decode()); req['store'] = False
            if preview: raise PreviewReady(req)
            c.api(req, 'A2_tutorial')
            return io.BytesIO(json.dumps(c.LAST_BODY).encode())
        stream.urllib = types.SimpleNamespace(request=types.SimpleNamespace(Request=urllib.request.Request, urlopen=post), error=urllib.error)
    return stream
