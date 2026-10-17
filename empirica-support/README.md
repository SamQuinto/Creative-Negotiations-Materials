# Empirica setup, tests, and other scenarios

The [Empirica folder](../empirica/) contains only the two scorer commands and a copy of the current 215-issue scenario. This support folder holds the instructions, tests, local preview, and all four current scenario exports. The `empirica/flexible-215.json` copy must match `scenarios/flexible-215.json`; the smoke test checks this. [runtime_manifest.json](runtime_manifest.json) records the engine source revision, this package layout, and file hashes. The latest October 17 scoring update adds the September job-start deadline, default vacation/remote units, and changes from the usual allowances. Update the shared `app/` folder and scenario JSONs together, not just the two Python entry points. Archived experimental versions keep their earlier payoffs.

## Download and run

Use the [public repository](https://github.com/SamQuinto/Creative-Negotiations-Materials). Keep `empirica/` and `app/` together as supplied: the two scorer commands call the shared engine rather than containing separate scoring logic. Keep `empirica-support/` and `developer/` too if you want to run the tests or local preview. Moving the optional tools here does not change the scoring logic or payoffs.

Use Python 3.11 or later. No extra Python packages are required. From the extracted folder, run:

```text
python empirica-support/smoke_test.py
python empirica-support/test_language_rules.py
```

This tests the actual command-line scripts, all four current scenarios, both roles, invalid calendar dates, both supported folder layouts, and the local preview imports. It makes no AI calls and does not need a key. It is a packaging and rule check, not a live language-model test.

For natural-language scoring, set your own `OPENAI_API_KEY` environment variable, then run:

```text
python empirica/score_offer.py --role Candidate --issue-space 215 --text "budget of 7000 salary of 31213 starting date of may" --json
python empirica/score_tutorial_offer.py --text "300 venue fee September 15 close at 9pm include projector use" --json
python empirica/score_offer.py --issue-space 215 --version
python empirica/score_offer.py --scenario-file empirica/flexible-215.json --role Candidate --text "salary 55k budget 9k start January 1" --json
```

The main command defaults to Flexible 15. Use `--issue-space fixed-15`, `15`, or `215` explicitly for the intended study; `200` selects the archived scenario. Use `--scenario-file /path/to/scenario.json` to load an external complete scoring file. Explicit form values can use `--choices-json` instead of `--text`, with zero AI calls. Include all 15 rows for Fixed 15.

Natural-language offers use Nano for routine interpretation and independent Luna review when flagged. Payoffs are calculated by the shared deterministic engine. A month-only start such as May is shown as May 1 for confirmation; a supplied day is preserved. Salary and budget accept any non-negative amount, with proportional scoring beyond the displayed reference anchors.

Current job dates give both roles January 1 = +1, March 1 = 0, May 1 = −1, July 1 = −2, and September 1–30 = −3. Dates between anchors are scored proportionally. October–December give −1000 to both roles, making agreement impossible under the normal positive-payoff rule. Role materials explain that a start after September cannot go ahead. A supplied year is ignored; month/day use the 2026 calendar. A month alone means day 1, mid-month day 15, end-month its last day, and “start ASAP” means January 1. The venue tutorial keeps its separate dates and payoffs.

Vacation days default to annual days and remote days to weekly days: “work remotely 4 times” means four days per week. “10 more vacation days than usual” means 40 annually; “1 more than usual remote working day” means four weekly. The scenario explicitly stores the usual 30/3 allowances; these are not inherited earlier offers. Show the resolved totals for confirmation. Explicit monthly remote requests still ask for a weekly value. Vacation allows 0–365 days; explicit weekly allowances use 52 weeks and show the annual conversion. Remote work allows 0–5 days per week. Existing scoring anchors still apply proportionally outside the examples. Bare company-car requests mean a dedicated car; explicit shared/pool/no-car wording takes precedence.

The tutorial now retains an impossible date such as “August 32” and asks for a valid calendar day rather than saying the date is missing or quietly reading August 1. `--version` prints the selected scenario's ID, issue count, and shared-file fingerprints without an AI call.

The supplied layout keeps the commands in `empirica/`. A server may also put both commands directly beside `app/`; both layouts work without editing `ROOT`. Replace the shared `app/` files as well as the commands when updating. A new JSON URL alone cannot update Python interpretation or feedback behavior. The original root-level commands in the private prototype were not overwritten.

When a participant explicitly refers back, pass the relevant offer using `--previous-offer "..."`. “Same other details but salary 60k” may retain that package; “keep their start date” may retain only the named date. Missing information is not automatically inherited just because context is supplied. Show the resulting complete package for confirmation before sending it. A new feature without a specified numerical choice should be acknowledged with a focused question, not assigned a guessed amount. A genuinely new idea outside the catalogue is kept visible without invented points in the expanded task.

The private development audit includes verbatim survey responses, earlier simulated offers and constructed main/tutorial edge cases. Its individual records stay private. These public checks contain constructed examples only. Passing a development collection is not a guarantee that every future message will be interpreted correctly.

For natural-language feedback, `unstated_required` lists required issues the participant did not supply, while `invalid_required` lists supplied values that need correction. `missing_required` remains the compatibility list of all required rows without a valid choice. Use the first two fields to distinguish “still needed” from “please clarify.” Display a final value only for a `scorable` result, using `total_for_proposer`; a partial `total` is not a complete offer's value. Show the complete interpreted package for confirmation before sending it.

## Files and integration

- [Main scorer](../empirica/score_offer.py) and [tutorial scorer](../empirica/score_tutorial_offer.py).
- [Convenient 215-issue scenario copy](../empirica/flexible-215.json).
- [Current scenario JSONs](scenarios/): Fixed 15, Flexible 15, Flexible 215, and the venue tutorial.
- [Continuous-scoring browser helper](deterministic_score.mjs).
- [Scenario format and integration guide](SCENARIO_FORMAT.md). Its development/rebuild commands refer to the full prototype checkout; this public download includes only the runtime and the smoke check above.
- `python empirica-support/preview_server.py` starts a local researcher integration game at `http://127.0.0.1:3136/`. It uses explicit form choices, needs no key, and is not the live Empirica study.

Keep the full scoring JSON and counterpart payoffs on the server, and return only each participant's permitted information. These files are publicly inspectable, not secret. Replace the visible `readrole_instructions` test placeholder before human collection. An older dropdown-only Empirica reader must be connected to `continuous_scoring` or the explicit-choices Python route; fetching the JSON alone does not update that reader.

Keys, participant data, historical simulation results, and private planning files are not included. The original root-level scorer scripts remain in the [full prototype repository](https://github.com/SamQuinto/Creative-Negotiations), whose privacy has not changed.
