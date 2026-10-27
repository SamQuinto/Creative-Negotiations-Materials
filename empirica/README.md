# Empirica scoring package

**This is the canonical folder for Joshua. Download or update everything here,
including `app/`. Both command paths stay the same.**

- `score_offer.py`: A1 main scorer, using `gpt-6.1-sol`, low reasoning and the
  evaluated job-exercise guidance. It defaults to the full 215-issue task.
- `score_tutorial_offer.py`: the existing tutorial scorer, with its existing
  scenario and interpretation behavior. It has not been switched to A1.
- `flexible-215.json` and `fixed-9.json`: the existing participant/scenario JSONs.
- `app/`: all required prompts, score calculation, scenarios and supporting files.

The old A2 main scorer is retained inside `app/backend/score_offer_a2.py`.
The tutorial and explicitly selected historical issue spaces use that retained
implementation. Do not move individual files out of this folder.

## Run

Use Python 3.11 or later. No extra Python packages or ROOT edits are needed.
Check the complete package without a key or paid model calls:

```text
python app/check_installation.py
```

Set `OPENAI_API_KEY` on the server, or copy `app/openai_key_example.txt` to
`app/openai_key.txt` and replace the placeholder with your own key. The existing
key location is unchanged. Keep the key private and server-side.

```text
python score_offer.py --role Candidate --issue-space 215 --text "salary 65k budget 13.25 grand start ASAP 4 remote days 60 vacation days waive non-compete" --json
python score_tutorial_offer.py --text "venue fee 300 September 15 close at 9pm" --json
```

Those two commands make paid model calls. Both can be run by full path from
another working directory. Existing `--role`, `--text`, `--previous-offer`,
`--scenario-file`, `--issue-space`, and `--json` arguments remain available.
No frontend patch is required by this package.

## A1 settings and checks

A1 sends every active issue description and choice to the advanced model in
one request. The Python script calculates the researcher-defined scores;
numerical scoring weights are not sent to the model. Empirica's existing
response fields and string-list score breakdowns are retained.

The A1 files are under `app/a1/`: the general prompt, optional job guidance,
response format, model settings, frozen scoring table and Python implementation.
The default table matches the evaluated A1 configuration. Its 215 issue
definitions and numerical scores match the public Flexible 215 scenario, but
role summaries and interpretation notes can differ. An explicit
`--scenario-file` is supported; changing it can change the model request.
Treatment role-data URLs and fixed-condition table scoring are unchanged.

```text
python score_offer.py --version
python score_offer.py --text "salary 50k budget 10k start March 1" --preview
```

These checks make no API calls. `--helper off` disables A1's optional job
guidance; `--reading-notes` supplies a replacement file for another exercise.
Prompt, model or scenario changes require their own validation.

A1's API spending guard defaults to US$25 per persistent ledger. Set
`NOVA_A1_API_LEDGER` to a writable server path and `NOVA_A1_BUDGET_USD` to the
agreed limit, or use `--api-ledger` and `--api-budget`. The current guard accepts
limits up to US$45. Verify price estimates in `app/a1/model_settings.json` before
live use. Requests are not retried automatically; uncertain billing stops
further dispatch until the ledger is reconciled. Do not delete a live ledger
to bypass its limit.

The evaluated low-reasoning A1 with guidance passed 973/1,000 development
inputs. Packaging checks preserve its requests and scoring results on all
1,000 saved cases; they are not a new live accuracy or holdout test. This is
not A2's separately fitted 1,000/1,000 result. The current release fingerprint
and checks are in `runtime_manifest.json`.

The backend response contains both roles' private scores. Keep it server-side
and continue showing each negotiator only their own score. The US$15 bonus
cap in the participant JSONs limits money paid, not the raw research score.

[OpenAI structured-output request format](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
