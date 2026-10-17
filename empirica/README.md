# Empirica scorer download

This public package contains the current main and tutorial scorer commands, scenario JSONs, and the shared files they need. [runtime_manifest.json](runtime_manifest.json) records the exact source revision and file hashes. The October 17 update improves date feedback, monetary shorthand, explicit references to earlier offers and optional-feature recognition. The venue tutorial also handles more ordinary wording and keeps projector costs separate from venue fees. Scenario payoffs have not changed.

## Download and run

[Download ZIP](https://github.com/SamQuinto/Creative-Negotiations-Materials/archive/refs/heads/main.zip), then extract it. Keep `empirica/`, `app/`, and `developer/` together as supplied: the two scorer commands call the shared engine rather than containing separate scoring logic.

Use Python 3.11 or later. No extra Python packages are required. From the extracted folder, run:

```text
python empirica/smoke_test.py
python empirica/test_language_rules.py
```

This tests the actual command-line scripts, all four current scenarios, both roles, invalid calendar dates, both supported folder layouts, and the local preview imports. It makes no AI calls and does not need a key. It is a packaging and rule check, not a live language-model test.

For natural-language scoring, set your own `OPENAI_API_KEY` environment variable, then run:

```text
python empirica/score_offer.py --role Candidate --issue-space 215 --text "budget of 7000 salary of 31213 starting date of may" --json
python empirica/score_tutorial_offer.py --text "300 venue fee September 15 close at 9pm include projector use" --json
python empirica/score_offer.py --issue-space 215 --version
```

The main command defaults to Flexible 15. Use `--issue-space fixed-15`, `15`, or `215` explicitly for the intended study; `200` selects the archived scenario. Use `--scenario-file /path/to/scenario.json` to load an external complete scoring file. Explicit form values can use `--choices-json` instead of `--text`, with zero AI calls. Include all 15 rows for Fixed 15.

Natural-language offers use Nano for routine interpretation and independent Luna review when flagged. Payoffs are calculated by the shared deterministic engine. A month-only start such as May is shown as May 1 for confirmation; a supplied day is preserved. Salary and budget accept any non-negative amount, with proportional scoring beyond the displayed reference anchors.

A stated date outside May 1–September 30 is acknowledged with a correction question, not called missing or silently replaced. The date interval remains intentional. `--version` prints the selected scenario's ID, issue count, and shared-file fingerprints without an AI call; use it to check the actual server installation.

The supplied layout keeps the commands in `empirica/`. A server may also put both commands directly beside `app/`; both layouts work without editing `ROOT`. Replace the shared `app/` files as well as the commands when updating. A new JSON URL alone cannot update Python interpretation or feedback behavior. The original root-level commands in the private prototype were not overwritten.

When a participant explicitly refers back, pass the relevant offer using `--previous-offer "..."`. “Same other details but salary 60k” may retain that package; “keep their start date” may retain only the named date. Missing information is not automatically inherited just because context is supplied. Show the resulting complete package for confirmation before sending it. A new feature without a specified numerical choice should be acknowledged with a focused question, not assigned a guessed amount. A genuinely new idea outside the catalogue is kept visible without invented points in the expanded task.

The private development audit includes verbatim survey responses, earlier simulated offers and constructed main/tutorial edge cases. Its individual records stay private. These public checks contain constructed examples only. Passing a development collection is not a guarantee that every future message will be interpreted correctly.

For natural-language feedback, `unstated_required` lists required issues the participant did not supply, while `invalid_required` lists supplied values that need correction. `missing_required` remains the compatibility list of all required rows without a valid choice. Use the first two fields to distinguish “still needed” from “please clarify.” Display a final value only for a `scorable` result, using `total_for_proposer`; a partial `total` is not a complete offer's value. Show the complete interpreted package for confirmation before sending it.

## Files and integration

- [Main scorer](score_offer.py) and [tutorial scorer](score_tutorial_offer.py).
- [Current scenario JSONs](scenarios/): Fixed 15, Flexible 15, Flexible 215, and the venue tutorial.
- [Continuous-scoring browser helper](deterministic_score.mjs).
- [Scenario format and integration guide](SCENARIO_FORMAT.md). Its development/rebuild commands refer to the full prototype checkout; this public download includes only the runtime and the smoke check above.
- `python empirica/preview_server.py` starts a local researcher integration game at `http://127.0.0.1:3136/`. It uses explicit form choices, needs no key, and is not the live Empirica study.

Keep the full scoring JSON and counterpart payoffs on the server, and return only each participant's permitted information. These files are publicly inspectable, not secret. Replace the visible `readrole_instructions` test placeholder before human collection. An older dropdown-only Empirica reader must be connected to `continuous_scoring` or the explicit-choices Python route; fetching the JSON alone does not update that reader.

Keys, participant data, historical simulation results, and private planning files are not included. The original root-level scorer scripts remain in the [full prototype repository](https://github.com/SamQuinto/Creative-Negotiations), whose privacy has not changed.
