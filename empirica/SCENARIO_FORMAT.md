# Using the current scenarios in Empirica

The generated JSONs follow the supplied 200-issue sample's structure. Each has `roles.Candidate` and `roles.Recruiter`, with `narrative`, `full_text`, `full_blocks`, `BATNA`, `RP`, and `determinatescoretable`. The narratives carry the approved headings, bullets, indentation, emphasis, and payoff colors. Dates in scored offers show the day as well as the month.

`readrole_instructions` keeps the visible **test placeholder** requested by the researcher. Replace it before collecting participant data. The old office-sharing introduction, pounds, and three-party agreement wording are not copied into these files. The general `tips` do not promise an outdated feedback-survey bonus.

| File under `empirica/scenarios/` | Required issues | Own-payoff display |
|---|---|---|
| `fixed-15.json` | All 15 original issues | All 15 rows |
| `flexible-15.json` | Salary, budget, starting date | Three required rows |
| `flexible-215.json` | Salary, budget, starting date | Three required rows |
| `tutorial.json` | Venue fee, event date, closing time | Three practice rows |

The 200-issue scenario in `app/config/large-200.json` is archived, not the current expanded task. Historical experiments in `replication/` retain their original files and values.

## What is in the fixed table?

Both roles' `determinatescoretable` contain these 15 issues:

1. Salary
2. Personal Budget
3. Starting Date
4. Probation Length
5. Contract Length
6. Vacation Days
7. Remote Working Days
8. Professional Training Program
9. Mentorship Program
10. Role in Recruitment Fair
11. Mandatory Conference Presentations
12. Non-compete Clause
13. Professional Associations Membership
14. Role in Organizing Social Events
15. Regular Social Media Posts for Company

The first seven are continuous in the current study design. Each table row keeps the sample's `[{"option": ..., "score": ...}]` format. For continuous issues these entries are **examples**, not the complete set of allowed values. For the eight choice-based issues they are the complete allowed options.

For each continuous issue, `roles[role].continuous_scoring[issue]` supplies:

- `value_type` and `unit`: how to read the entry.
- `domain`: the actual permitted minimum and maximum. A null maximum means no upper limit.
- `reference_min` and `reference_max`: the displayed scoring anchors, which need not be proposal limits.
- `knots`: values and their scores, used for proportional interpolation.
- `extrapolation`: whether scoring continues outside the anchors or the value must stay within the physical/calendar range.

Salary and budget accept any non-negative amount. Their scores continue at the same rate beyond the displayed anchors. Other numerical/date issues keep their configured limits. Intermediate values such as 2.25 probation months, 3.4 contract years, or 3.5 remote days are valid under the current design. Display `step` values are not restrictions to whole numbers.

## The live Empirica reader needs this connection

An older reader that uses the table as a finite dropdown lookup will still be restricted to those examples. **Adding the JSON field alone cannot make that reader continuous.** Render number/date inputs for continuous issues and dropdowns for choice-based issues.

The included browser helper calculates a fixed-condition preview using only the assigned role's rules:

```javascript
import { scoreChoices } from './deterministic_score.mjs';
const preview = scoreChoices(ownRole, choices, requiredIssues);
```

`ownRole` must contain only that participant's disclosed table and continuous rules. The helper performs interpolation and permitted extrapolation, and rejects missing choices or values outside the actual domain. Its results have been compared with Python for both roles.

For authoritative server scoring, pass explicit choices to the Python adapter. This makes **zero LLM calls**:

```python
import json, subprocess, sys
result = subprocess.run([
    sys.executable, 'empirica/score_offer.py',
    '--scenario-file', 'empirica/scenarios/fixed-15.json',
    '--role', 'Candidate', '--choices-json', json.dumps(choices), '--json'
], capture_output=True, text=True)
```

`choices` is an object mapping the 15 issue names to their selected number, ISO date, or exact discrete option. Do not omit unchanged rows. The response keeps the existing `decision`, `valid_pairs`, `total_for_proposer`, `total_for_receiver`, and `proposal_allowed` fields. Its model is `deterministic` and its routing reports zero calls. Capture standard error when the process exits unsuccessfully.

For natural-language offers, continue using `--text`; Nano interprets routine offers and Luna independently checks flagged cases. Both routes use the same payoff definitions. The form route validates explicit choices directly rather than asking an LLM to reinterpret them.

Keep the full scoring JSON on the server. Return only the assigned narrative, that role's permitted scoring display, and the review response appropriate to that participant. Do not reveal the counterpart's private totals or the latent issue list. The local preview permits role switching for researchers; the live server must enforce the assigned role and matching itself.

## The latest required-issue payoffs are preserved

- Salary: $35,000 / $50,000 / $65,000 are the −2 / 0 / +2 Candidate anchors, with the opposite scores for Recruiter.
- Budget: $5,000 / $10,000 / $15,000 are the −2 / 0 / +2 Candidate anchors, with the opposite scores for Recruiter.
- Starting date: May 1 = +1, June 8 = 0, September 30 = −3, for both roles.

For example, a $50,000 salary, $10,000 budget and May 1 start give +1 to each party before optional issues. Salary and budget only transfer value; date changes joint value. With only these three issues, a June 8 or later start cannot give both parties strictly positive totals. The four role-private numerical issues offset across roles and do not independently create joint value.

This preserves the smaller required-only bargaining zone. If salary and budget are sampled independently and uniformly between their reference anchors, and dates uniformly across the permitted calendar days, the jointly positive share is **5.8345%**. It is identical in Flexible 15 and Flexible 215. This is a share under that stated reference distribution; there is no uniform distribution over every unbounded dollar amount. Other sampling assumptions yield other shares.

Zero or negative offers may be proposed, but acceptance requires strictly positive totals for both parties. The expanded task still caps the paid agreement bonus at $15 while retaining the uncapped research score.

## Try the local game

```text
python empirica/preview_server.py
```

Open `http://127.0.0.1:3136/`. Select a scenario and role, enter values, review and send an offer, then switch roles and accept it on both sides. The game loads the generated JSON, checks the browser's fixed-condition calculation against the shared Python scorer, and applies the agreement rules. It needs no key and makes no AI calls. It is a local integration check, not the deployed Empirica app or a participant data-collection service.

## Rebuild and check

```text
python developer/build_empirica_scenarios.py
python developer/test_empirica_scenarios.py
python developer/test_empirica_preview.py
python developer/test_empirica_adapters.py
python developer/test_scorer.py
python developer/test_experiment_materials.py
```

Edit the payoff definitions in `app/config/`, then rebuild the exports. Tables and continuous rules are derived from the same definitions; do not maintain a separate table by hand. The generator also refreshes Fixed 15's private display table.

Checks cover all 256 discrete packages for both roles, fractional values, open money, calendar limits, browser/Python agreement, external files in paths with spaces, missing fixed choices, and agreement from both sides. These are offline checks, not a claim of perfect live language interpretation. Final deployment still requires connecting the reader to these inputs and verifying the live server's version.
