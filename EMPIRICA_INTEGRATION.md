# Small Empirica updates

## Use the role-specific files

After assigning Candidate or Recruiter, load that role's JSON and survey YAML. Each role JSON keeps the existing `roles`/`tips` structure, but `roles` contains **one role only**. Render `roles[0].narrative` as Markdown, preserving bold and italics. Do not download the other role's material into the participant interface.

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
