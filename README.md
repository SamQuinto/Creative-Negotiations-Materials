# Creative Negotiations — experiment materials

Participant materials for the 200-issue Candidate–Recruiter negotiation scenario and its feedback survey. The hidden payoff catalog, research data, and API keys are not included.

## Raw links for Empirica

| Material | Raw link |
|---|---|
| Candidate role materials | [candidate_role_materials_200.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/candidate_role_materials_200.json) |
| Recruiter role materials | [recruiter_role_materials_200.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/recruiter_role_materials_200.json) |
| Survey for participants assigned Candidate | [candidate_feedback_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/candidate_feedback_survey.yaml) |
| Survey for participants assigned Recruiter | [recruiter_feedback_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/recruiter_feedback_survey.yaml) |
| Actual experiment post-negotiation survey | [experiment_post_negotiation_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/experiment_post_negotiation_survey.yaml) |
| Post-negotiation survey HTML preview | [experiment_post_negotiation_survey_preview.html](https://github.com/SamQuinto/Creative-Negotiations-Materials/blob/main/experiment_post_negotiation_survey_preview.html) |

The experiment survey is role-independent and is used after both Fixed 15 and Latent 215 negotiations. It contains two participant pages. Q29 and Q30 use `show_if` and should appear, and become required, only when Q28 is answered **Yes**. The standalone HTML file is a visual and interaction preview; it does not collect or transmit responses.

Randomly assign Candidate or Recruiter and load that role's JSON and matching survey. Each JSON contains just one role, in the existing `roles` array. Q2, Q9 and Q12 depend on the assigned role. The reviewed role materials use shorter paragraphs, selected bullets, five numbered scoring notes, and inline HTML for italic role names/examples and colored payoff values. Single-asterisk Markdown is not used. The external Empirica reader still needs checking for this inline formatting; see the integration notes below. The earlier combined JSON remains only for old-link compatibility; use the separate files above for this survey.

## File format

- **Role JSON:** `roles` and `tips`; each role has `role_name`, `narrative`, `RP`, and `scoresheet`. The scoresheet is intentionally empty so the feedback task does not disclose the hidden issue menu. This file does not score offers.
- **Survey YAML:** `scales` and `questions`, with the existing `likert`, `single_select`, `multi_select`, and `open_text` types. Q6 requests three written terms; Q11 requests 3–5 job-feature names only, one per line in a single box. Required/optional responses must be enforced by the survey host.
- **Researcher preview:** the two-page HTML preview and answer key are kept in the separate private project, not this public repository. Participant YAML files do not contain answer keys.

For the hardcoded introduction, use [About This Activity](About_This_Activity.md), including the feedback bonus draw. **Q11 stays one text box**, with a short gray guide and three-line placeholder; no reasons are requested. If the external reader ignores those presentation fields, see [the integration notes](EMPIRICA_INTEGRATION.md). The private mockup shows the intended layout.

The formats follow the existing [narrative JSON](https://raw.githubusercontent.com/SamQuinto/Describing-Search-in-Negotiations/refs/heads/main/shared_office_3p_easy.json) and [survey YAML](https://raw.githubusercontent.com/SamQuinto/Describing-Search-in-Negotiations/refs/heads/main/narative_survey.yaml) examples. The Empirica loader is maintained separately; no running experiment or participant response collection is hosted here.

For data collection, replace `refs/heads/main` in the raw links with a commit ID so later edits cannot change the materials during an active study.

## Measure attribution

The experiment survey contains established or adapted research measures cited in the accompanying study documentation, including the Subjective Value Inventory and measures of perceived realism, creative process engagement, creative self-efficacy, temporary impasse and perspective taking. Retain those citations when reusing the survey. This repository does not grant additional rights to third-party measure wording.
