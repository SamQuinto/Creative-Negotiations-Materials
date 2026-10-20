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

The current Fixed-9, Fixed-15, Flexible-15 and Flexible-215 scoring files store
`payment.agreement_bonus_cap_usd = 15`. For the Prolific comparison, use Fixed 9
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

## Choose the condition's scenario (20 October 2026)

Use the existing treatment factors to select the file. Fixed/control:

```yaml
scoringMode: table
roleDataURL: https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/main/empirica/fixed-9.json
```

For NOVA, use the natural-language scoring mode and this `roleDataURL`:

```text
https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/main/empirica/flexible-215.json
```

Fixed 9 keeps the same role story as Flexible 215. Its numerical explanations
and tips describe the available table choices rather than open amounts or
intermediate values. A short closing transition leads to its nine mandatory
issues and nine payoff-table rows for each role.
Other issue definitions stay stored in `issues`, but
`active_issues` prevents them from entering a scored fixed offer. The updated
scorer applies that restriction; keep the whole `empirica/` folder together.

Flexible 215 keeps the full catalogue and flexible narratives. Only salary,
personal budget and starting date are required for natural-language offers.
Its separate `determinatescoretable` also contains nine rows, as requested for
table-mode compatibility. This display table does not restrict flexible
scoring and is not a list of the only issues that can be negotiated.

Both nine-row tables use at most five representative choices per issue, with
table scores rounded to two decimal places. The continuous rules remain full
precision; salary and budget in Flexible 215 still have no upper proposal bound.
The fifth Flexible-215 tip is removed; agreement still requires both parties
to accept an offer worth more than zero to each. Fixed 15 is
retained separately and unchanged. No external interface changes are included
in this update. Start a fresh test game to load the selected scenario.

## Freeze live-study links

During development, the README links follow `main`. Before data collection, replace `refs/heads/main` with the approved commit ID so later repository edits cannot change materials in an active study.
