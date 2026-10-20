# Empirica scoring package

**Download everything in this folder, including `app/`.** You only need this
`empirica/` folder to run the main and tutorial scorers. Nothing from the
repository's other folders is required for scoring.

Keep this layout:

```text
empirica/
  score_offer.py
  score_tutorial_offer.py
  fixed-9.json
  flexible-215.json
  app/
    backend/
    config/
    check_installation.py
    openai_key_example.txt
```

Use Python 3.11 or later. No extra Python packages are needed. From inside
this folder, check the installation without an API key or paid calls:

```text
python app/check_installation.py
```

For natural-language scoring, set your own `OPENAI_API_KEY` environment
variable on the server. Alternatively, copy
[`app/openai_key_example.txt`](app/openai_key_example.txt) to
`app/openai_key.txt` and replace its placeholder with your own key on one line.
The scorer reads `OPENAI_API_KEY` first, then the local key file. The example
contains no key and is not loaded automatically. Keep the real key server-side;
`openai_key.txt` is excluded from Git. Then run:

```text
python score_offer.py --role Candidate --issue-space 215 --text "salary 55k budget 9k start January 1" --json
python score_tutorial_offer.py --text "venue fee 300 September 15 close at 9pm" --json
```

To load the supplied full 215-issue scenario explicitly, use
`--scenario-file /path/to/empirica/flexible-215.json`. Relative scenario paths
are resolved from the directory where you run the command. The main command
still defaults to Flexible 15: specify `--issue-space 215` or `--scenario-file`
for the expanded task. The tutorial command selects its own venue scenario.

### Which scenario to use

Use [`fixed-9.json`](fixed-9.json) for the fixed/control condition and
[`flexible-215.json`](flexible-215.json) for NOVA. Set the treatment's
`roleDataURL` to the matching raw JSON link. Fixed 9 keeps the same role narrative
as Flexible 215, adds a transition to the table, and requires all nine issues
in that table. Its full 215-entry catalogue stays
stored in the file, but `active_issues` restricts scoring to the nine listed
issues. Update this whole folder together so that restriction is applied.

Flexible 215 keeps all 215 issues active and only the three core issues required
in free-text offers. It also carries the same nine-row `determinatescoretable`,
as a separate table view; that view does not restrict its natural-language
scoring. Both nine-row tables have at most five representative choices per
issue and scores rounded to two decimal places. Underlying continuous scoring
keeps full precision and the existing open-amount rules.

Fixed 15 remains a separate, unchanged configuration for earlier designs.

Both commands can be called from another working directory using their full
paths. Do not edit `ROOT`. Update the whole folder together, not just the two
Python files. Natural-language scoring uses Nano for routine interpretation,
with Luna review for flagged cases; the payoff calculation is deterministic.
The installation check uses explicit choices, not live language-model calls.

If you cloned the whole repository, `empirica/` is the deployment folder: the
two scorer commands already sit at its top level, beside `app/`. The sibling
`empirica-support/` and `developer/` folders are optional tests and preview
helpers, not scoring dependencies. Existing Empirica command paths do not need
to change. For future updates, pull the repository and keep this whole folder
on the same revision.

The latest language update keeps unpriced personal requests separate from known
allowances. A relative's holiday does not request the Candidate's vacation days;
an unpriced object for commuting does not automatically request cash support.
Separate real vacation or cash-support requests still count.

Keep API keys and both roles' full payoff definitions server-side. Show each
participant only the information they are allowed to see.

For the Prolific study, the current Fixed-9 and Flexible-215 JSONs both specify
a US$15 negotiation-bonus cap. Flexible 15 carries the same payment setting.
This caps the money paid for an agreement, not the payoff returned by the scorer.
Base payment and survey-effort bonuses are separate. The payment backend must
use the JSON's `payment` settings; see the
[payment integration note](../EMPIRICA_INTEGRATION.md#prolific-payments-20-october-2026).

### Participant instructions

The scenario now separates the short preparation message (`readrole_instructions`)
from the role narrative and offer instructions (`tips`). Keep the interface headings
**Your role** and **Tips on Negotiation**. Both JSON fields contain trusted HTML
for paragraphs and bold emphasis; do not display them as literal HTML source.

The suggested offer-box placeholder is saved in
`empirica_export.display_settings.main_offer_placeholder`. This is a reference
for the experiment's placeholder factor, not an automatic change to a hard-coded
Empirica interface. The user will set that factor. Use actual line breaks in the
textarea placeholder, not HTML `<br>` tags. In JSON, those line breaks are written
as `\n`. If the admin editor keeps them as literal backslash-n, the interface
must translate them into newlines. Fixed 9 has its own all-nine-issues prompt;
the separate Fixed 15 configuration keeps its all-15-issues prompt.
The offer box should let Enter add a line break, rather than submit or calculate
an offer. Check the live interface's keyboard handler before using that wording.

[Further integration instructions, tests, and optional preview](../empirica-support/)
