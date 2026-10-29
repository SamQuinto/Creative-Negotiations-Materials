# Empirica scoring package

This is the folder Joshua uses for the study. Please update **everything in `empirica/`, including the whole `app/` folder**. Keep the files together; the two command paths have not changed.

## Current scorers

Both `score_offer.py` and `score_tutorial_offer.py` now use the latest tested **A1 with low reasoning** by default: `gpt-6.1-sol`, the general-purpose prompt, and the full issue definitions for the selected exercise. A1 no longer adds the older job-specific helper prompt. The tutorial uses the same general prompt with its own exercise files.

The latest **A2** job scorer is included too. It uses `gpt-5.6-luna`, exercise-specific instructions and the tested Python corrections. Select it explicitly with `--architecture A2`. A2's tutorial path remains the separately developed tutorial implementation; it does not use the fitted job corrections. We recommend the default A1 for the tutorial.

`flexible-215.json` and `fixed-9.json` remain the participant-material files. Their numerical values and the nine fixed issues are unchanged. Agreement metadata now consistently allows a score of **0 or higher for each party**.

## Add or update your key

You need Python 3.11 or later, with no extra Python packages.

1. Set `OPENAI_API_KEY` in the server environment, or make a copy of `app/openai_key_example.txt` called **`app/openai_key.txt`**.
2. If using the file, replace its placeholder with your actual key, save it as plain text, and keep it in `app/`. Put only the key in that file. On Windows, show file-name extensions so it does not accidentally become `openai_key.txt.txt`.
3. To replace a key later, edit that same file or update the server environment. An environment key takes priority over the file. If the server keeps its own environment open, restart that process after changing its environment key.

Please keep the key private. It is read on the server, never included in a model request's offer text or returned to the participant. OpenAI's [authentication guidance](https://developers.openai.com/api/reference/overview#authentication) explains why keys should stay server-side. Your OpenAI account needs available credit and access to the selected model.

## Run

From this folder:

```sh
python score_offer.py --role Candidate --issue-space 215 --text "salary 65k budget 13.25 grand start ASAP 4 remote days 60 vacation days waive non-compete" --json
python score_tutorial_offer.py --role Candidate --text "Venue fee $350, event date September 12 next year, closing time 8 p.m., venue projector included" --json
```

These make paid calls. You can also run either script by its full path from another working directory; no ROOT edit or sibling folder is needed.

Use `--reasoning high` for A1-high or `--architecture A2` for A2. The existing `--role`, `--text`, `--previous-offer`, `--issue-space`, `--scenario-file` and `--json` arguments remain available. Explicit choices supplied with `--choices-json` are scored without an API call. A1 can read an external scenario; the fitted A2 is intended for the included exercises.

Historical `15`, `200`, `fixed-9` and `fixed-15` command paths remain available. The main command defaults to `215`; the tutorial command defaults to `tutorial`.

## Check the update without paid calls

```sh
python app/check_installation.py
python score_offer.py --version
python score_tutorial_offer.py --version
python score_offer.py --text "salary 50k budget 10k start March 1" --preview
```

`--preview` shows the exact model request without sending it. `--replay path/to/interpretation.json` scores a saved interpretation without a model call. The installation check covers both roles, both exercises, the retained issue spaces, and numerical and date checks. Additional packaging tests are in `empirica-support/`; that folder is not needed to run the study.

## Where the current files live

- `app/scoring/prompts/`: the exact A1 and A2 instructions.
- `app/scoring/frozen/`: the evaluated job and tutorial exercise information, role materials, issue definitions, response formats and scoring tables.
- `app/scoring/A1-1.py` and `A1-2.py`: prepare A1's request, then check and score its interpretation.
- `app/scoring/A2-1.py` and `A2-2.py`: prepare A2's selected-issue request, then apply its fitted corrections and score the result.
- `app/scoring/a2_custom_rules.py`: the tested job-specific corrections.
- `app/empirica_bridge.py`: preserves the study's command-line arguments and response fields.
- `app/a1/` and `app/backend/`: the shared checks, numerical scoring functions and retained historical implementation.

The prompts, exercise inputs and scoring code are synchronized with the [NOVA replication implementation](https://github.com/SamQuinto/NOVA-Replication-Materials/tree/main/1_Architecture_and_Demonstration). Packaging checks verify that model requests and scored terms match that implementation. They are not a new accuracy study.

Normal study scoring has **no local spending guard, billing ledger or automatic retries**. An old development ledger or budget environment variable cannot block later offers. OpenAI's own credit, rate and access limits still apply. Do not pass the older `--api-budget` or `--api-ledger` options to this study scorer. The retired `--helper on` and `--reading-notes` options are not used by the current general A1.

The response contains private values for both roles. Keep it server-side and display only the intended negotiator's value. The US$15 payment cap is separate from the raw research score.
