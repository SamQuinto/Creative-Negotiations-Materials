# Creative Negotiations — experiment materials

Participant-facing materials for the Candidate–Recruiter negotiation scenario, its feedback pre-test, and the class and Prolific post-negotiation surveys. The hidden payoff catalog, research data, and API keys are not included.

## Raw links for Empirica

| Material | Raw link |
|---|---|
| Candidate role materials | [candidate_role_materials_200.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/candidate_role_materials_200.json) |
| Recruiter role materials | [recruiter_role_materials_200.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/recruiter_role_materials_200.json) |
| Survey for participants assigned Candidate | [candidate_feedback_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/candidate_feedback_survey.yaml) |
| Survey for participants assigned Recruiter | [recruiter_feedback_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/recruiter_feedback_survey.yaml) |
| Earlier full post-negotiation survey | [experiment_post_negotiation_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/experiment_post_negotiation_survey.yaml) |
| Earlier full survey HTML preview | [experiment_post_negotiation_survey_preview.html](https://github.com/SamQuinto/Creative-Negotiations-Materials/blob/main/experiment_post_negotiation_survey_preview.html) |
| Class post-negotiation survey | [class_post_negotiation_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/class_post_negotiation_survey.yaml) |
| Class survey HTML preview | [class_post_negotiation_survey_preview.html](https://github.com/SamQuinto/Creative-Negotiations-Materials/blob/main/class_post_negotiation_survey_preview.html) |
| Prolific post-negotiation survey | [prolific_post_negotiation_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/prolific_post_negotiation_survey.yaml) |
| Prolific survey HTML preview | [prolific_post_negotiation_survey_preview.html](https://github.com/SamQuinto/Creative-Negotiations-Materials/blob/main/prolific_post_negotiation_survey_preview.html) |
| Survey measure and design notes | [SURVEY_MEASURE_NOTES.md](SURVEY_MEASURE_NOTES.md) |

The earlier full survey is retained for version history. Use one of the two purpose-specific surveys below for new studies.

## Which post-negotiation survey to use

- **Class:** `class_post_negotiation_survey.yaml` is the short teaching version for the Control versus Perspective Taking comparison. It asks students to compare this open negotiation with earlier fixed-issue negotiations, distinguish perspective understanding from perspective use, connect their strategy to course principles and identify a lesson for a future negotiation. It does not include the full Subjective Value Inventory, creative-engagement or creative-self-efficacy measures.
- **Prolific:** `prolific_post_negotiation_survey.yaml` is the research version for Fixed 15 versus Latent 215. It retains the full Subjective Value Inventory, creative-engagement and creative-self-efficacy measures and a literature-based temporary-impasse module. It does not include perspective-taking or issue-space manipulation checks. Q29–Q31 appear only when Q28 is **Yes**; Q32 appears only when Q31 is **Yes**.
- The HTML files are interactive visual previews only. They do not save or transmit responses.

Issue generation, issue redefinition and issue diversity are calculated from behavioral offer data by the experiment application. They are not self-report survey questions.

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
