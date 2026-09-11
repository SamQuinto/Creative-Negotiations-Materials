# Small Empirica updates

## Use the role-specific files

After assigning Candidate or Recruiter, load that role's JSON and survey YAML. Each role JSON keeps the existing `roles`/`tips` structure, but `roles` contains **one role only**. Render `roles[0].narrative` using the existing paragraph and bold support. Do not download the other role's material into the participant interface.

**Reviewed presentation — approved for publication on 10 September 2026:** single-asterisk Markdown was displayed literally in Empirica. The new presentation keeps the same JSON schema and uses ordinary paragraph breaks, literal `•` bullets, `1.`–`5.` numbered notes, existing double-asterisk bold, and small inline HTML tags for italics, payoff colors and underlined +2 values. `developer/role_presentation.py` applies the reviewed wording/layout to a copy of the original text. The HTML mockup uses that same presentation. The agreement sentence names the other role in italics and requires a positive total score for both parties. Original scenario files, payoff values and frozen simulations remain unchanged.

The researcher's Empirica screenshots confirmed inline italics, payoff colors, the indented example and list indentation render correctly. Bullet and numbered paragraphs use an explicit block `span` with `margin-left:1.5em; padding-left:1.25em; text-indent:-1.25em` to indent the marker and align wrapped lines under the text. This does not depend on the host's list styles.

11 September refinements: each main payoff bullet has a `br` line break before its neutral choice, without creating another item. Zero payoffs are blue and bold; both +2 and −2 are underlined. Notes 2, 4 and 5 use the latest reviewed wording. These refinements still need a final visual check in Empirica after reloading.

If tags appear literally or colors are removed, check the reader's formatting support; **do not disable sanitization or enable arbitrary HTML**. Only the generated `em`, `strong`, `u`, `br` and indented `span` formatting and three fixed colors (`#166534`, `#b91c1c`, `#1d4ed8`) are needed. No script, external asset or event handler is included in the narrative. The previous `role_markdown` function remains available for a bold-only fallback; apply the review wording edits too if using it. After an update, reload the role JSON; already-open sessions or pinned older commit URLs may still show the old text.

The previous combined `role_materials_200.json` remains only for compatibility with an earlier link. Use the new role-specific links for this survey.

## Replace the hardcoded introduction

Use `About_This_Activity.md` for **About This Activity**. It distinguishes the feedback activity's random bonus draw from the main study's agreement-based bonus. Changing a role JSON cannot replace text that is hardcoded in Empirica; paste this content into that component.

## Q11: three rows, with optional additions

The YAML keeps the existing `q11` / `open_text` question so it remains compatible with the current schema. A YAML file cannot add a dynamic control unsupported by the survey renderer.

For `question.id === "q11"`, use a small repeatable-input component instead of the usual single text box:

1. Initially show **three rows**, each with an **Issue name** field and a **Why it makes sense** field. Both fields in each of these rows are required.
2. Below them, show **+ Add another issue (optional)**. Each click adds one row, up to five in total. Focus the new issue-name field.
3. Rows four and five are optional. If either field in an optional row is filled, require its partner field too. A completely blank optional row is valid.
4. Disable the add button when five rows are visible. Preserve values when participants review role materials or navigate back.
5. Save an array of `{issue, justification}` records. If the existing response API only accepts strings, serialize the nonblank rows as numbered `Issue name — justification` lines under the existing `q11` answer key. Keep all other question IDs unchanged.

The private HTML mockup already implements this behavior. Until the renderer change is installed, the public YAML remains a standard text question requesting three to five issue/reason pairs; it must not be described as already providing dynamic boxes in Empirica.
