# A1 main scorer for Empirica

Download **everything in this folder**, including `app/` and `flexible-215.json`.
Python 3.11 or later is sufficient. No extra packages or ROOT edits are needed.

This is **A1: the full-table scorer**, using `gpt-6.1-sol`, low reasoning,
and the evaluated job-exercise guidance. It sends all 215 issue descriptions
and choices to the model in one request. The Python script, not the model,
calculates the scores. Numerical scoring weights are not sent to the model.

## Joshua's setup

1. Run `python app/check_installation.py` without a key or paid calls.
2. Set `OPENAI_API_KEY` on the server. Alternatively, copy
   `app/openai_key_example.txt` to `app/openai_key.txt` and replace the placeholder.
3. Point the **main** Empirica scoring command at this folder's `score_offer.py`.
   The existing `--role`, `--text`, `--previous-offer`, `--scenario-file`,
   `--issue-space 215`, and `--json` arguments are supported.

```text
python score_offer.py --role Candidate --text "salary 65k budget 13.25 grand start ASAP 4 remote days 60 vacation days waive non-compete" --json
```

That command makes a paid model call. The output keeps the existing Empirica
fields, including `decision`, `valid_pairs`, `lines`, `display_text`,
`total_for_proposer`, `total_for_receiver`, and `proposal_allowed`.
Keep this backend JSON server-side: it contains both roles' private scores.
The participant interface must continue showing only the appropriate own score.

**Leave the tutorial command at `empirica/score_tutorial_offer.py`.** This release
adds A1 for the main negotiation only; it does not replace or modify the existing
A2 main scorer or tutorial. A1's tutorial comparison was weaker, so it is not
silently substituted here. Fixed-condition table scoring and role-data URLs
are also unchanged. No frontend patch is required by this package.

## Quick checks and settings

```text
python score_offer.py --version
python score_offer.py --text "salary 50k budget 10k start March 1" --preview
python score_offer.py --choices-json "{\"Salary\":\"50000\",\"Personal Budget\":\"10000\",\"Starting Date\":\"March 1\"}" --json
```

These checks make no API calls. Commands also work from another directory when
called by full path. The default scenario is the scoring table used in the A1
comparison. Its 215 issue definitions and numerical scores match the current
public Flexible 215 scenario; additional interpretation notes and role summaries
can differ. Supplying another `--scenario-file` is supported, but a changed
request is not the exact frozen benchmark configuration.

The general prompt, optional job guidance, response format, and model settings
are separate editable files under `app/`. `--helper off` disables the job
guidance. Custom exercise guidance can be passed with `--reading-notes`.
Different prompts, models, scenarios, or guidance need their own validation.

The API spending guard defaults to US$25 per local ledger, saved at
`app/.runtime/scoring.sqlite`. Set `NOVA_A1_API_LEDGER` to a writable persistent
server path and `NOVA_A1_BUDGET_USD` to the agreed limit, or use `--api-ledger`
and `--api-budget`. The current guard accepts limits up to US$45. Verify the
price estimates in `app/model_settings.json`; they are not an invoice. Requests
are not retried automatically. Uncertain billing pauses further dispatch until
the local ledger is reconciled. Never delete a live ledger to bypass its limit.

The evaluated low-reasoning A1 with guidance passed **973/1,000 development
inputs** using the saved comparison and answer key. This is not the customized
A2's 1,000/1,000 result, and it is not an independent holdout estimate.
Release checks verify request/scoring equivalence with saved A1 replies; they
do not claim a new live accuracy measurement.

[OpenAI structured-output request format](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
