# Handover docs (step `handover`)

Write into `<root>/handover/`. Plain Markdown, no front matter. The reader is a capable agent with **no memory of this work** and only the files. Write for that reader: concrete, ordered, linked to evidence. Prefer short sections and tables over prose. Match the project's own language and terms.

If the project already has good docs (README, ledger, plan), do not duplicate them: point to them from `README.md` and `05_FILE_MAP.md`, and write only what they lack, especially what lives only in the conversation. If an existing doc contradicts the conversation or the code, say so in `04_GOTCHAS` and `10_UNKNOWNS`.

## File set

| File | Contents |
|---|---|
| `README.md` | **Start here.** One-paragraph summary, the reading order, a 10-minute orientation checklist, the three things most likely to go wrong, the index of the other files. Short. |
| `01_PROJECT_CONTEXT.md` | What the project is, why it exists, who it is for, the owner and their stance, success criteria, constraints (time, tools, accounts), stakeholders. |
| `02_STATE_AND_NEXT_STEPS.md` | Done / in progress / blocked / waiting on the user, each with evidence; the priority order and how it was decided; the first concrete action for the successor; open questions for the user. |
| `03_DECISIONS.md` | One entry per decision: what, why, alternatives rejected, who decided (user / assistant / default), when, reversible?, evidence. Flag any decision the assistant took without asking. |
| `04_GOTCHAS_AND_TRAPS.md` | Things that looked right and were wrong, fragile spots, files not to touch, commands that must not be run, ordering dependencies, environment quirks, with the symptom and the fix. |
| `05_FILE_MAP.md` | Where everything is: source vs generated vs vendored, entry points, config, data, docs, tests; where state lives **outside** the folder (accounts, services, caches, memory); which parts are authoritative when two disagree. |
| `06_HOW_TO_RUN.md` | Setup, run, test, build, deploy: exact commands, expected output, and for each whether it was **verified** (you ran it or saw it run) or **unverified**. Prerequisites and versions. |
| `07_GLOSSARY.md` | Project vocabulary: ids, abbreviations, nicknames, domain terms, what each means in this project. |
| `08_WORKING_AGREEMENTS.md` | The user's preferences and standing rules for how to work (style, review gates, what to ask first, what never to do), each with the reason and, if available, what prompted it. |
| `09_HISTORY_DIGEST.md` | Chronological digest of the conversation(s): what was attempted, what changed course and why, the user's corrections. Dated where possible. A map, not a transcript. |
| `10_UNKNOWNS_AND_UNVERIFIED.md` | What you could not confirm, what is stale, what was inferred, what the conversation did not cover, and what you would check first. |

Drop a file only if it would be empty for this project, and say so in `README.md`. Add files if the project needs them (for example `11_DATA_AND_SOURCES.md`).

## Keep the hand-over about the project, not about this run

The docs describe the **project**. Do not record decisions about how the hand-over itself was produced or tested (exam sizes, which agents ran, what was reduced or skipped, scratch copies). That belongs in `handover/.passthebaton/` (events.log, rounds/, REPORT.md). The only allowed mention is one line in `02_STATE_AND_NEXT_STEPS.md`: "A handover test run is logged in `handover/.passthebaton/REPORT.md`". If a fix step feels the need to add a "decision" about the test run to `03_DECISIONS.md` or `08_WORKING_AGREEMENTS.md`, that is a sign the exam question was about the process, not the project: fix or drop the question instead.

## Evidence discipline

Tag every non-obvious claim:
- `[verified: <path>:<line> | <command> → <what it showed>]` you saw it in a file or ran it
- `[conversation: <heading/timestamp in conversation.md>]` the user or assistant said it
- `[inferred]` your reading, not confirmed

Rules: never state a command works unless you ran it or saw it run; never invent a date, version, name or decision; say "not recorded" rather than guess; keep numbers exact (counts, versions, thresholds) and say where they came from; distinguish **planned** from **executed**. Paths are relative to the project root, never absolute to your machine.

## Quality bar (check before marking the step done)

- Could a stranger answer: what is this, what state is it in, what do I do first, what must I not do, how do I run and check it, where is X, why was Y chosen, what did the user ask me never to do?
- Every table row and entry has a pointer to where to check it.
- No secret values, no personal credentials. Refer to where they live.
- Contradictions between sources are written down, not silently resolved.
- Nothing is padded. A short accurate doc beats a long one.

## Pointer block for `CLAUDE.md` (only with the user's consent)

```markdown
<!-- passthebaton -->
## Handover
This project has a handover set in `handover/`. At the start of every session read `handover/README.md`, then
`handover/02_STATE_AND_NEXT_STEPS.md` and `handover/08_WORKING_AGREEMENTS.md`. Trust the files over your assumptions;
where they say "unverified", verify before relying on it. Update them when the state changes.
<!-- /passthebaton -->
```

## Finish the step

1. Write all files. 2. `scan_secrets.py --redact handover/`. 3. Write `handover/.passthebaton/rounds/handover_v0/summary.md` (one paragraph: what was written, what sources it rests on, what you were unsure about). 4. Snapshot the docs for later diffs: `cp -R handover/<docs> handover/.passthebaton/diffs/v0/` (everything in `handover/` except `.passthebaton`).
