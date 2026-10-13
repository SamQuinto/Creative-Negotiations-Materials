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

## Freeze live-study links

During development, the README links follow `main`. Before data collection, replace `refs/heads/main` with the approved commit ID so later repository edits cannot change materials in an active study.
