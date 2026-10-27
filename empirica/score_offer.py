#!/usr/bin/env python3
"""Run one offer through the same scorer used by the Creative Negotiations app."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'app/a1/backend'))
from scorer import Scorer


def main(default_space=None):
    # Keep tutorial and explicitly selected historical tasks on their existing scorer.
    space = default_space
    for index, value in enumerate(sys.argv[1:], 1):
        if value == '--issue-space' and index + 1 < len(sys.argv):
            space = sys.argv[index + 1]
        elif value.startswith('--issue-space='):
            space = value.split('=', 1)[1]
    if space in ('tutorial', '15', '200', 'fixed-9', 'fixed-15'):
        import importlib.util
        spec = importlib.util.spec_from_file_location('nova_legacy_entry', ROOT / 'app/backend/score_offer_a2.py')
        legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(legacy)
        return legacy.main(default_space=default_space)
    parser = argparse.ArgumentParser(description='Score one main offer with A1.')
    parser.add_argument('--role', choices=('Candidate', 'Recruiter'), default='Candidate')
    parser.add_argument('--issue-space', choices=('215',), default='215')
    parser.add_argument('--scenario-file', help='Optional replacement scoring scenario JSON.')
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('--text', help='Offer text; if omitted, reads a line from the terminal.')
    inputs.add_argument('--choices-json', help='Explicit issue choices; makes no model call.')
    parser.add_argument('--previous-offer', default='')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--version', action='store_true')
    parser.add_argument('--preview', action='store_true', help='Print the model request; no API call.')
    parser.add_argument('--replay', help='Read a saved interpretation JSON; no API call.')
    parser.add_argument('--helper', choices=('on', 'off'), default='on')
    parser.add_argument('--reading-notes', help='Optional exercise-specific guidance file.')
    parser.add_argument('--reasoning', choices=('low', 'medium', 'high', 'xhigh', 'max'))
    parser.add_argument('--api-budget', type=float, default=float(os.environ.get('NOVA_A1_BUDGET_USD', '25')))
    parser.add_argument('--api-ledger', default=os.environ.get('NOVA_A1_API_LEDGER', str(ROOT / 'app/.runtime/scoring.sqlite')))
    args = parser.parse_args()
    try:
        scorer = Scorer(args.scenario_file, helper=args.helper == 'on',
                        reasoning=args.reasoning, reading_notes=args.reading_notes)
        if args.version:
            print(json.dumps(scorer.version(), indent=2))
            return 0
        if args.choices_json is not None:
            if args.preview or args.replay:
                raise ValueError('Use choices-json without preview or replay.')
            result = scorer.for_empirica(scorer.structured(json.loads(args.choices_json), args.role), mode='deterministic')
        else:
            if args.preview and args.replay:
                raise ValueError('Use preview or replay, not both.')
            text = str(args.text if args.text is not None else input('Offer text: '))
            text = text.encode('utf-8', errors='replace').decode('utf-8').strip()
            if not text:
                raise ValueError('Please provide an offer.')
            if args.preview:
                print(json.dumps(scorer.request(text, args.role, args.previous_offer), ensure_ascii=True, indent=2))
                return 0
            if args.replay:
                response = json.loads(Path(args.replay).read_text(encoding='utf-8-sig'))
                raw = scorer.finalize(text, response, args.role, args.previous_offer)
                result = scorer.for_empirica(raw, mode='recorded_interpretation')
            else:
                raw, receipt = scorer.live(text, args.role, args.previous_offer, args.api_ledger, args.api_budget)
                result = scorer.for_empirica(raw, receipt=receipt)
        print(json.dumps(result, ensure_ascii=True, indent=2) if args.json else result['display_text'])
        return 0
    except Exception as exc:
        print(json.dumps({'error': str(exc), 'decision': 'error', 'architecture': 'A1'}, ensure_ascii=True))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
