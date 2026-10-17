# Empirica scoring package

**Download everything in this folder, including `app/`.** You only need this
`empirica/` folder to run the main and tutorial scorers. Nothing from the
repository's other folders is required for scoring.

Keep this layout:

```text
empirica/
  score_offer.py
  score_tutorial_offer.py
  flexible-215.json
  app/
    backend/
    config/
    check_installation.py
```

Use Python 3.11 or later. No extra Python packages are needed. From inside
this folder, check the installation without an API key or paid calls:

```text
python app/check_installation.py
```

For natural-language scoring, set your own `OPENAI_API_KEY` environment
variable on the server. Then run:

```text
python score_offer.py --role Candidate --issue-space 215 --text "salary 55k budget 9k start January 1" --json
python score_tutorial_offer.py --text "venue fee 300 September 15 close at 9pm" --json
```

To load the supplied full 215-issue scenario explicitly, use
`--scenario-file /path/to/empirica/flexible-215.json`. Relative scenario paths
are resolved from the directory where you run the command. The main command
still defaults to Flexible 15: specify `--issue-space 215` or `--scenario-file`
for the expanded task. The tutorial command selects its own venue scenario.

Both commands can be called from another working directory using their full
paths. Do not edit `ROOT`. Update the whole folder together, not just the two
Python files. Natural-language scoring uses Nano for routine interpretation,
with Luna review for flagged cases; the payoff calculation is deterministic.
The installation check uses explicit choices, not live language-model calls.

Keep API keys and both roles' full payoff definitions server-side. Show each
participant only the information they are allowed to see. Replace the visible
`readrole_instructions` test placeholder before participant collection.

[Further integration instructions, tests, and optional preview](../empirica-support/)
are available separately; they are not needed to run these two commands.
