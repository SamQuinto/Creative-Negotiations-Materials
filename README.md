# Creative Negotiations — experiment materials

Current materials for the Candidate–Recruiter negotiation project. This public repository contains participant role materials and surveys, plus the Empirica scorer runtime and scoring scenarios linked below. Participant data, API keys, analysis files, and internal planning documents are not included.

## Current materials

### Feedback pre-test (historical)

| Material | Raw file |
|---|---|
| Candidate role materials | [candidate_role_materials_200.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/candidate_role_materials_200.json) |
| Recruiter role materials | [recruiter_role_materials_200.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/recruiter_role_materials_200.json) |
| Candidate feedback survey | [candidate_feedback_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/candidate_feedback_survey.yaml) |
| Recruiter feedback survey | [recruiter_feedback_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/recruiter_feedback_survey.yaml) |
| Hardcoded activity introduction | [About_This_Activity.md](About_This_Activity.md) |

Load only the role JSON and survey YAML matching the participant's assigned role.

The `_200` role filenames preserve the earlier feedback pre-test wording and payoffs. They are historical materials, not the current classroom or Prolific experiment. Use the current Fixed-9 or Flexible-216 scenario links below for those setups. Historical participant materials are not rewritten when the experiment changes.

For the current fixed/control condition, use the separate Fixed-9 scenario below. It keeps the same role story as Flexible 216, with numerical explanations and tips matched to the choices in its nine-row own-payoff table. Fixed 15 remains available separately for earlier designs. The main prototype is in the [prototype repository](https://github.com/SamQuinto/Creative-Negotiations).

### Post-negotiation surveys

| Use | Empirica YAML | Interactive preview |
|---|---|---|
| Classroom exercise | [class_post_negotiation_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/class_post_negotiation_survey.yaml) | [Open preview](https://raw.githack.com/SamQuinto/Creative-Negotiations-Materials/main/class_post_negotiation_survey_preview.html) |
| Prolific Fixed-9 versus Latent-215 study | [prolific_post_negotiation_survey.yaml](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/refs/heads/main/prolific_post_negotiation_survey.yaml) | [Open preview](https://raw.githack.com/SamQuinto/Creative-Negotiations-Materials/main/prolific_post_negotiation_survey_preview.html) |

The HTML files are visual, interactive previews only. They do not save or transmit responses.

### Current Prolific payment information

[Review both roles for Fixed 9, Fixed 15 and Latent 215](https://raw.githack.com/SamQuinto/Creative-Negotiations-Materials/main/prolific_role_materials_preview.html). The payment paragraph near the end of each role explains **US$1 per point, capped at US$15 for the negotiation bonus**. The base payment and survey-effort bonus are separate. [Copy the Prolific study description](PROLIFIC_STUDY_DESCRIPTION.md).

The [Prolific survey preview](https://raw.githack.com/SamQuinto/Creative-Negotiations-Materials/main/prolific_post_negotiation_survey_preview.html) starts with a bonus notice above Q1. Among participants passing the survey-effort checks, the top 10% receive 50% of base payment, the next 20% receive 25%, the next 20% receive 15%, and the remaining 50% receive 10%. Existing Q1–Q33 and their IDs are unchanged; the separate acknowledgment is informational, not an effort check. The classroom survey and completed feedback pre-test are unchanged.

### Empirica scorer and scenarios

**Canonical scorer package:** [empirica/](empirica/) contains the current A1 main
and tutorial scorers, the fitted A2 option, both scenario JSONs and the complete `app/` folder.
Keep the same paths: `empirica/score_offer.py` and
`empirica/score_tutorial_offer.py`. Download or update the whole folder together.
[Setup](empirica/README.md). No separate A1 folder is needed.

[Open the public Empirica folder](empirica/). **Download everything inside that folder, including `app/`.** It now contains both Python commands, the current 215-issue scenario, and the complete shared scoring engine. No other repository folder is needed to run the scorers. [The short setup guide](empirica/README.md) includes a no-key installation check.

[Detailed instructions, extra tests, the preview, and other scenario exports](empirica-support/) are kept separately. The optional preview also uses the single helper in `developer/`; neither sibling folder is required to run the scorers. If you clone the whole repository, keep your Empirica commands pointed at `empirica/score_offer.py` and `empirica/score_tutorial_offer.py`. The [key template](empirica/app/openai_key_example.txt) contains a placeholder only; copy it to `empirica/app/openai_key.txt` and add your own key locally, or set `OPENAI_API_KEY` on the server. Never commit a real key. The current engine revision and file hashes are in the [runtime manifest](empirica/runtime_manifest.json).

| Backend scenario | Public raw JSON |
|---|---|
| Fixed 9 — current control | [fixed-9.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/main/empirica/fixed-9.json) |
| Fixed 15 | [fixed-15.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/main/empirica-support/scenarios/fixed-15.json) |
| Flexible 15 | [flexible-15.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/main/empirica-support/scenarios/flexible-15.json) |
| Flexible 216 — current NOVA | [flexible-216.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/main/empirica/flexible-216.json) |
| Flexible 216 — classroom, no monetary-payment notice | [flexible-216-classroom.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/main/empirica/flexible-216-classroom.json) |
| Tutorial | [tutorial.json](https://raw.githubusercontent.com/SamQuinto/Creative-Negotiations-Materials/main/empirica-support/scenarios/tutorial.json) |

Use **Fixed 9 for the fixed-issue condition** and **Flexible 216 for NOVA** in the treatment's `roleDataURL`. Each file has its own role narratives. Both have a nine-row `determinatescoretable`, at most five choices per issue, and table scores rounded to two decimals. Flexible 216 scores its full table and requires only salary, budget and starting date in natural-language offers. Fixed 9 activates only its nine listed issues. Fixed 15 is separate and unchanged.

Flexible 216 adds **Workplace Coffee** after the October 27, 2026 pilot. Free coffee is worth **+1 to the Candidate and 0 to the Recruiter**; no free coffee is worth 0 to both. The previous 215 issue definitions are unchanged, and the original 215-issue files remain available for historical replication. The classroom version has the same scores but omits the Prolific payment notice and disables monetary-payment metadata.

The current nine-issue agenda includes the **non-compete clause instead of recruitment-fair participation**. Waiving the clause gives Candidate +1 and Recruiter −1; keeping it gives both 0. Training remains in Fixed 9. Recruitment-fair participation remains available in Flexible 216, alongside the non-compete clause.

Both current conditions use mirrored priorities: remote work matters more to the Candidate (−2 to +2), while probation matters more to the Recruiter (−2 to +2). Counterpart weights stay at ±1. This allows a longer probation period to be traded for more remote work so both parties gain. The role explanations, table values and continuous scoring rules reflect these weights. Earlier 15-issue configurations and the tutorial are unchanged.

The 21 October update renames Team Sales Bonus to **Performance-Based Bonus**
in Flexible 215, covering individual or team targets on the unchanged payoff
curve. Social-media commitments can now receive proportional points. Both
issues remain zero-sum; the other 213 definitions and the fixed/frozen scenario
payoffs are unchanged. The shared scorer also includes the reviewed human-pilot
wording repairs and later-total scoring convention. [What changed and how to
update the package](empirica/README.md).

These complete scoring files include both roles' payoffs and the issue catalogue. They are publicly inspectable, not participant-facing role files; load them server-side and show only the assigned role's material. The main prototype repository remains private.

## Which survey to use

- **Classroom:** a short teaching and reflection survey for the Control versus Perspective Taking exercise. It compares an open-ended negotiation with a predefined-issue exercise such as New Recruit and supports discussion of strategy, learning, and how negotiations became stuck or resumed progress.
- **Prolific:** the research survey for Fixed-9 versus Latent-215. It includes the full Subjective Value Inventory, perceived realism and role engagement, Creative Process Engagement, Creative Self-Efficacy, offer-strategy reflection, and the plain-language “felt stuck” module.

Issue generation, issue redefinition, issue diversity, agreement, time, offers, payoffs, joint gains, and Pareto efficiency come from behavioral experiment logs rather than survey self-reports.

## Implementation notes

- [EMPIRICA_INTEGRATION.md](EMPIRICA_INTEGRATION.md) explains role rendering, conditional survey branching, and feedback-survey display requirements.
- [SURVEY_MEASURE_NOTES.md](SURVEY_MEASURE_NOTES.md) records measure sources and which items were developed for this project.
- For a live study, replace `refs/heads/main` in raw links with the approved commit ID so later edits cannot change materials during data collection.
