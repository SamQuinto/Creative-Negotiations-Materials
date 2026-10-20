# Using the current scenarios in Empirica

The generated JSONs follow the supplied sample's structure. Each has `roles.Candidate` and `roles.Recruiter`, with `narrative`, `full_text`, `BATNA`, `RP`, and `determinatescoretable`. Older scenarios also retain their source `full_blocks`. The narratives carry the approved headings, bullets, indentation, emphasis, and payoff colors. Dates in scored offers show the day as well as the month.

`readrole_instructions` contains the short preparation message. The role narrative explains the participant's interests; `tips` holds the offer and scoring instructions under **Tips on Negotiation**. Keep **Your role** as the interface's role heading, without repeating a Candidate/Recruiter role-information heading inside the narrative. These fields use trusted, researcher-authored HTML. The old office-sharing introduction, pounds, and three-party agreement wording are not copied into these files. The general `tips` do not promise an outdated feedback-survey bonus.

`empirica_export.display_settings.main_offer_placeholder` provides the suggested multiline offer-box prompt. Set it through the live experiment's placeholder factor; this metadata does not change hard-coded interface elements. A textarea needs actual newlines, written as `\n` in JSON, not HTML `<br>` tags. If Enter currently submits an offer, change that handler before displaying instructions to use Enter for a new line. Fixed 15 has its own all-15-issues placeholder.

| File under `empirica-support/scenarios/` | Required issues | Own-payoff display |
|---|---|---|
| `fixed-9.json` | All nine listed issues | Nine rows, at most five choices each |
| `fixed-15.json` | All 15 original issues | All 15 rows |
| `flexible-15.json` | Salary, budget, starting date | Three required rows |
| `flexible-215.json` | Salary, budget, starting date | Nine-row table-mode view; all 215 issues remain available in natural-language mode |
| `tutorial.json` | Venue fee, event date, closing time | Three practice rows |

A byte-identical copy of `flexible-215.json` is also available directly in `empirica/` for easy sharing. The public engine and default definitions are now inside `empirica/app/`; downloading that entire `empirica/` folder is sufficient for scoring. The 200-issue scenario in `empirica/app/config/large-200.json` is archived, not the current expanded task. Historical experiments in `replication/` retain their original files and values.

## What is in the fixed table?

The current Fixed 9 and Flexible 215 files both carry these nine table rows:

1. Salary
2. Personal Budget
3. Starting Date
4. Probation Length
5. Contract Length
6. Vacation Days
7. Remote Working Days
8. Professional Training Program
9. Role in Recruitment Fair

The first seven use numerical or date-based payoff rules. Each table row keeps the sample's `[{"option": ..., "score": ...}]` format. In Fixed 9, participants choose from the listed options; `table_negotiation.choices_are_exhaustive` records this. In Flexible 215, these entries are examples rather than limits on natural-language offers. The two choice-based issues have their complete two-option sets. Table scores are rounded to two decimals; underlying arithmetic keeps full precision.

Fixed 9 stores all 215 payoff definitions but lists only nine `active_issues` and nine `required_issues`. The scorer filters to that agenda before interpreting or scoring an offer. Flexible 215 has no active-issue restriction and still requires only the three core features in natural-language mode. Its table view does not limit the flexible issue space. Both conditions keep the same role story. Fixed 9 explains the listed table choices rather than open amounts or proportional intermediate values, then adds the closing table transition. Flexible 215 keeps its open-value wording and has four negotiation tips, with the old fifth item removed. The separate Fixed 15 file is unchanged.

For each continuous issue, `roles[role].continuous_scoring[issue]` supplies:

- `value_type` and `unit`: how to read the entry.
- `domain`: the actual permitted minimum and maximum. A null maximum means no upper limit.
- `reference_min` and `reference_max`: the displayed scoring anchors, which need not be proposal limits.
- `knots`: values and their scores, used for proportional interpolation.
- `extrapolation`: whether scoring continues outside the anchors or the value must stay within the physical/calendar range.

In Flexible 215, salary and budget accept any non-negative amount. Their scores continue at the same rate beyond the displayed anchors. Other numerical/date issues keep their configured limits. Intermediate values such as 2.25 probation months, 3.4 contract years, or 3.5 remote days are valid there. Display `step` values are not restrictions to whole numbers. Fixed 9 presents only its listed choices; the underlying curves remain available to check their arithmetic.

## How the scoring connections work

Fixed 9 uses the finite table choices. Flexible 215 uses natural-language offers and the shared scorer; its table metadata does not restrict those offers. A separate numerical-input interface would need to read `continuous_scoring` to support intermediate values; adding metadata alone does not change an interface's behavior.

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
    '--scenario-file', 'empirica/fixed-9.json',
    '--role', 'Candidate', '--choices-json', json.dumps(choices), '--json'
], capture_output=True, text=True)
```

`choices` is an object mapping the nine active issue names to their selected number, ISO date, or exact discrete option. Do not omit unchanged rows. The response keeps the existing `decision`, `valid_pairs`, `total_for_proposer`, `total_for_receiver`, and `proposal_allowed` fields. Its model is `deterministic` and its routing reports zero calls. Capture standard error when the process exits unsuccessfully.

For natural-language offers, continue using `--text`; Nano interprets routine offers and Luna independently checks flagged cases. Both routes use the same payoff definitions. The form route validates explicit choices directly rather than asking an LLM to reinterpret them.

Keep the full scoring JSON on the server. Return only the assigned narrative, that role's permitted scoring display, and the review response appropriate to that participant. Do not reveal the counterpart's private totals or the latent issue list. The local preview permits role switching for researchers; the live server must enforce the assigned role and matching itself.

## The latest required-issue payoffs are preserved

- Salary: $35,000 / $50,000 / $65,000 are the −2 / 0 / +2 Candidate anchors, with the opposite scores for Recruiter.
- Budget: $5,000 / $10,000 / $15,000 are the −2 / 0 / +2 Candidate anchors, with the opposite scores for Recruiter.
- Starting date: January 1 = +1, March 1 = 0, May 1 = −1, July 1 = −2, September 1–30 = −3; October–December = −1000, for both roles. Intermediate dates are proportional. Supplied years are ignored; month/day use the 2026 calendar. `continuous_scoring.assume_year` keeps the browser's calculation consistent with Python.

For example, a $50,000 salary, $10,000 budget and January 1 start give +1 to each party before optional issues. Salary and budget only transfer value; date changes joint value. With only these three core issues, a March 1 or later start cannot give both parties strictly positive totals.

Fixed 9 and Flexible 215 now have mirrored priorities. The Candidate's remote-work points run from −2 at one day to +2 at five days; the Recruiter's points remain +1 to −1. The Recruiter's probation points run from −2 at no probation to +2 at six months; the Candidate's points remain +1 to −1. Three remote days and three probation months stay worth 0 to both. Giving five remote days in exchange for six months' probation therefore adds +1 to each party, without relying on training or recruitment-fair participation. Vacation and contract-length weights are unchanged. Fixed 15, Flexible 15 and the tutorial retain their previous payoffs.

Vacation allows 0–365 annual days and remote work allows 0–5 weekly days. `usual_value` holds the 30/3 baselines; `default_period` holds the default units. These defaults do not authorize reuse of omitted earlier offers. Use `continuous_scoring.domain` for form limits, not `reference_min` or `reference_max`. Show weekly vacation conversions, relative changes from usual, and the complete interpreted package before sending.

If salary and budget are sampled independently and uniformly between their reference anchors, and dates uniformly across the 365 calendar days, the jointly positive share using only those three core issues is **3.7642%**. Those three payoff functions are unchanged by the new priorities. This is a share under that stated reference distribution, not the Fixed-9 table share; there is no uniform distribution over every unbounded dollar amount.

Counting each complete Fixed-9 table package once gives **47,380 mutually positive packages out of 312,500 (15.1616%)**. Maximum joint payoff is **8**; a balanced best-joint deal gives **4 points each**. Among mutually positive fixed-table deals, either party can receive **0.5–7.5 points**. The complete offer range is **−12 to +12** per party, including offers the counterpart would not accept. The public `test_fixed_nine.py` checks this exact count and the new trade-off. A start after September still cannot be offset by other features; the hard deadline is unchanged.

Zero or negative offers may be proposed, but acceptance requires strictly positive totals for both parties. The expanded task still caps the paid agreement bonus at $15 while retaining the uncapped research score.

## Try the local game

```text
python empirica-support/preview_server.py
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

These rebuild commands belong to the full prototype checkout, which keeps its original development layout. Edit the prototype payoff definitions in `app/config/`, then rebuild the exports. When publishing here, mirror the engine into `empirica/app/`, place those exports in `empirica-support/scenarios/`, and refresh the matching `empirica/flexible-215.json` copy. Tables and continuous rules are derived from the same definitions; do not maintain a separate table by hand. The generator also refreshes Fixed 15's private display table.

Checks cover all 256 discrete packages for both roles, fractional values, open money, calendar limits, browser/Python agreement, external files in paths with spaces, missing fixed choices, and agreement from both sides. These are offline checks, not a claim of perfect live language interpretation. Final deployment still requires connecting the reader to these inputs and verifying the live server's version.
