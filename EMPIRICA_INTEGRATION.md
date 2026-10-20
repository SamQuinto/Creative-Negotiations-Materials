# Empirica integration

## Load the assigned role only

After assigning Candidate or Recruiter, load the matching role JSON. Each file keeps the existing `roles` and `tips` structure but contains only one role. Render `roles[0].narrative`; do not load the other party's private material into the participant interface.

The `_200` filenames remain unchanged so existing raw links continue to work. Their contents are the current reviewed role materials.

## Render role formatting safely

The narratives use paragraph breaks, double-asterisk bold, and a small fixed set of inline tags: `em`, `strong`, `u`, `br`, and `span`. The spans provide payoff colors and hanging indentation for bullets and numbered notes.

Keep HTML sanitization enabled. Allow only those tags, their required style properties, and these fixed colors: `#166534`, `#b91c1c`, `#1d4ed8`, and `#1e3a8a`. No script, external asset, or event handler is needed. Empirica has already rendered the reviewed italics, colors, examples, bullets, and numbering correctly.

## Feedback pre-test

- Paste [About_This_Activity.md](About_This_Activity.md) into the hardcoded activity-introduction component.
- Keep Q11 as one `open_text` field. Participants enter three job-feature names and may add up to two more; do not request explanations.
- Display `question.hint` above Q11 and bind the textarea placeholder to `question.placeholder`. Preserve line breaks with `white-space: pre-line`.
- Q2, Q9, and Q12 use role-specific counterpart wording. Preserve Q9's paragraph breaks so the counteroffer is easy to read.

## Class and Prolific survey branching

Both current surveys use `show_if.equals` and `show_if.not_equals`.

- **Class:** show Q13–Q15 when Q12 is either **Yes, once** or **Yes, multiple times**. Show optional Q16 only when Q12 is **No**.
- **Prolific:** show Q30–Q31 when Q29 has either Yes response. Show optional Q32 only when Q29 is **No**.

The HTML previews implement both rules. The Empirica reader must do the same before deployment and must not require hidden questions.

## Prolific payments (20 October 2026)

The current Fixed-15, Flexible-15 and Flexible-215 scoring files store
`payment.agreement_bonus_cap_usd = 15`. For the Prolific comparison, use Fixed 15
and Flexible/Latent 215. Keep the raw payoff score unchanged in the scorer and
research logs. For an accepted agreement, the negotiation payment is
`min(15, own_points * 1 USD)`, with no negotiation bonus for an impasse.
Base payment and survey-effort bonuses are separate and do not use this cap.
The payment backend must apply this rule; changing a JSON file does not itself
send a bonus payment or update an unrelated hard-coded payment function.

Load the updated scenario JSON and the updated Prolific survey YAML together.
The survey begins with `survey_bonus_information`, a single-select informational
item with one optional acknowledgment. Preserve Q1–Q33 and their branching IDs.
The label is a short heading; the `hint` contains the normal-weight body. The
notice omits `n` rather than using 0, so it is not numbered. Display the hint's
line breaks (for example, `white-space: pre-line`). Do not
count this acknowledgment as an attention/effort check or as part of any scale.

Rank response effort and quality only among participants passing the effort
checks. The four group shares are 10%, 20%, 20% and 50%; their bonus rates are
50%, 25%, 15% and 10% of base payment. Do not rank participants by whether their
ratings are positive or match the study predictions. Complete the assessment
after collection; these percentages are not a live score for each survey item.

## Empirica client display fixes (20 October 2026)

The [small client patch](https://github.com/SamQuinto/Creative-Negotiations-Materials/blob/main/empirica-support/empirica-ui-fixes.patch) targets Joshua's
published client revision `1825e959c6b2177df20498987c3762b2ecd53aa0`. It changes:

- `Survey.jsx`: no literal zero for unnumbered notices; normal-weight hint text,
  preserved line breaks and a compact bonus-information card.
- `tableScoring.jsx`: at most two decimal places in displayed scores, no floating
  tails or negative zero, and enough column width for the score. Stored values,
  table totals and server scoring keep their existing full precision.
- `.empirica/treatments.yaml`: the `test-table` treatment uses the Fixed-15 file,
  not Flexible 215. The free-text treatment keeps Flexible 215.

Apply the patch in **Joshua's creative-negotiation checkout**, not this materials
repository. Check first and do not force it if his local files have since changed:

```text
git apply --check /path/to/Creative-Negotiations-Materials/empirica-support/empirica-ui-fixes.patch
git apply /path/to/Creative-Negotiations-Materials/empirica-support/empirica-ui-fixes.patch
```

For admin-created treatments, set these factors explicitly:

```yaml
scoringMode: table
roleDataURL: https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/main/empirica-support/scenarios/fixed-15.json
```

Both roles in that file have all **15 main issues** in `determinatescoretable`.
Flexible 215 intentionally exposes only three required-issue rows; switching the
interface to table mode does not turn that file into Fixed 15. Do not add all 15
rows to the flexible file, because that would disclose issues in the open task.

Rebuild/redeploy the client as usual and start a **fresh test game** after changing
settings. Existing games keep their already loaded survey and role scoresheets.
The Python scoring package alone cannot update these frontend components or
the factors stored on an already running Empirica game. No changes have been
made directly to Joshua's GitHub repository or deployed server.

## Freeze live-study links

During development, the README links follow `main`. Before data collection, replace `refs/heads/main` with the approved commit ID so later repository edits cannot change materials in an active study.
