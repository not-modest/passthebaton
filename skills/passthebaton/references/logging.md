# Logging and the final report

Everything the user might want to inspect is a file under `<root>/handover/.passthebaton/` (`RUN`). Write each artifact **when its step finishes**, not at the end, so an interruption loses at most one step.

```
RUN/
  state.json           plan, step statuses, results (pb_state.py owns it)
  events.log           timeline, one line per event (pb_state.py event ...)
  REPORT.md            built by build_report.py at the end
  harvest/             inventory.md, conversation.md, memory/, harvest.json
  exam/                standard_questions.json, hard_questions.json, final_questions.json   (questions only)
  answer_key/          standard.json, hard.json, final.json                                (hidden keys)
  rounds/<name>/       questions.json, answers.json, grade.json, summary.md   (name: handover_v0, haiku1..3, hard, final)
  diffs/               v0/ (first docs), <round>.before/, <round>.diff
```

Log to `events.log` (`pb_state.py event --root <root> "<text>"`) at least: the scratch copies made (path, files copied, secret-like files skipped), every agent spawned (role, model, round), each score, each key correction you made, each interruption.

The answer keys are the one thing not to share casually: they are in `answer_key/`; `REPORT.md` quotes verdicts and reasons but not key answers. Suggest the user keep `handover/.passthebaton/answer_key/` and `harvest/` out of git (`.gitignore` lines) because `harvest/conversation.md` is the raw conversation. Offer to add the lines; do it only on a yes.

## Prove the original is untouched

Before the summary run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/fingerprint.py verify --root <root>` (with `--allow CLAUDE.md` if the pointer was added). Quote its verdict ("VERIFIED: N files outside handover/ are byte-identical ..."). It writes `RUN/fingerprint_report.json`. If it fails, say so first, list the files, and point to the backup copy.

## The final summary to the user

Run `build_report.py`, then tell the user, plainly and briefly:
- the table of scores (standard rounds, hard exam, final round) with models;
- whether the standard exam reached 10/10 and in which round, or that it did not and what remains;
- the most important doc changes the tests forced (two or three);
- what the tests cannot show: same account and tooling, no real new-account test, and anything the user knows that was never written down; ask them to read `handover/README.md` and `10_UNKNOWNS_AND_UNVERIFIED.md` and correct them;
- where everything is (`handover/`, `handover/.passthebaton/REPORT.md`) and that scratch copies in `~/.passthebaton/scratch/` can be deleted;
- the CLAUDE.md pointer: added (show it) or not added (offer it).
Do not claim more than was observed.
