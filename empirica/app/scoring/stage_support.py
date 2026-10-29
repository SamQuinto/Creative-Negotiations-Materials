"""Read input files and run the four numbered scoring scripts."""
from pathlib import Path
import argparse, importlib.util, json, sys
ROOT = Path(__file__).resolve().parent

def load_stage(label):
    name = 'nova_stage_' + label.replace('-', '_')
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / (label + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]

def input_path(path):
    path = Path(path)
    return path if path.is_absolute() or path.exists() else ROOT / path

def read_json(path):
    return json.loads(input_path(path).read_text(encoding='utf-8-sig'))

def stage_main(function, *, scoring=False, job_only=False):
    parser = argparse.ArgumentParser(description=function.__doc__)
    parser.add_argument('--case-json', type=Path, required=True)
    parser.add_argument('--exercise', choices=['job'] if job_only else ['job', 'tutorial'], default='job')
    parser.add_argument('--reasoning', choices=['low', 'high'], default='low')
    parser.add_argument('--output', type=Path)
    if scoring: parser.add_argument('--interpretation-json', type=Path, required=True)
    args = parser.parse_args(); case = read_json(args.case_json); case.setdefault('previous_offer', '')
    result = function(case, read_json(args.interpretation_json), args.exercise) if scoring else function(case, args.exercise, args.reasoning)
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding='utf-8')
    else:
        if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
        print(serialized)
