# Creative Negotiations — experiment materials

Participant materials for the 200-issue Candidate–Recruiter negotiation scenario and its feedback survey. The hidden payoff catalog, research data, and API keys are not included.

## Raw links for Empirica

| Material | Raw link |
|---|---|
| Candidate role materials | [candidate_role_materials_200.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/candidate_role_materials_200.json) |
| Recruiter role materials | [recruiter_role_materials_200.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/recruiter_role_materials_200.json) |
| Survey for participants assigned Candidate | [candidate_feedback_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/candidate_feedback_survey.yaml) |
| Survey for participants assigned Recruiter | [recruiter_feedback_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/recruiter_feedback_survey.yaml) |

Randomly assign Candidate or Recruiter and load that role's JSON and matching survey. Each JSON contains just one role, in the existing `roles` array. Q9 and Q12 depend on the assigned role. Role text uses bold-only Markdown: italic markers are omitted because the current Empirica reader displays them as stray asterisks. Wording is unchanged; original italics remain in the private source materials and HTML mockup. The earlier combined JSON remains only for old-link compatibility; use the separate files above for this survey.

## File format

- **Role JSON:** `roles` and `tips`; each role has `role_name`, `narrative`, `RP`, and `scoresheet`. The scoresheet is intentionally empty so the feedback task does not disclose the hidden issue menu. This file does not score offers.
- **Survey YAML:** `scales` and `questions`, with the existing `likert`, `single_select`, `multi_select`, and `open_text` types. Q6 requests three written terms; Q11 requests 3–5 issue/justification pairs using one line per issue. Required/optional responses must be enforced by the survey host.
- **Researcher preview:** the two-page HTML preview and answer key are kept in the separate private project, not this public repository. Participant YAML files do not contain answer keys.

For the hardcoded introduction, use [About This Activity](About_This_Activity.md), including the feedback bonus draw. For **Q11**, the recommended interface starts with three issue-and-reason rows and lets participants add up to two more. The private mockup implements it; Empirica needs the small renderer change described in [the integration notes](EMPIRICA_INTEGRATION.md). The standard YAML alone does not create the dynamic controls.

The formats follow the existing [narrative JSON](https://raw.githubusercontent.com/SamQuinto/Describing-Search-in-Negotiations/refs/heads/main/shared_office_3p_easy.json) and [survey YAML](https://raw.githubusercontent.com/SamQuinto/Describing-Search-in-Negotiations/refs/heads/main/narative_survey.yaml) examples. The Empirica loader is maintained separately; no running experiment or participant response collection is hosted here.

For data collection, replace `refs/heads/main` in the raw links with a commit ID so later edits cannot change the materials during an active study.
