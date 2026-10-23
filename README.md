# passthebaton

Hand a long-running Claude Code project to a fresh session, a new account or a colleague, and **check that it worked**.

Long projects accumulate context that lives nowhere a new session can see it: decisions made in conversation, the reason a file must not be touched, what is half-done, what the owner said never to do again. `passthebaton` reads the folder **and the conversation**, writes a handover set into `handover/`, then tests it: fresh agents with no memory try to pick the project up, a separate examiner grades them against a hidden answer key, and the docs are fixed until they pass. Everything is logged.

## Install

```
/plugin marketplace add <owner>/passthebaton
/plugin install passthebaton@passthebaton
```

(or `claude plugin marketplace add <owner>/passthebaton` and `claude plugin install passthebaton@passthebaton` from a shell). Needs Claude Code, Python 3 and `git`. No other dependencies, no Workflow tool.

## Use

Open Claude Code **in the project folder** and run:

```
/passthebaton
```

Plugin skills are normally namespaced by the plugin name, so if the bare form is not offered use `/passthebaton:passthebaton`. Other forms: `/passthebaton resume` (continue an unfinished run), `/passthebaton status`, `/passthebaton --run-commands` (let test successors run read-only commands; default is read-only file access).

It asks a handful of questions up front (scope, whether successors may run commands, whether to keep git history in test copies, whether to append a pointer to `CLAUDE.md`) and then runs unattended.

## What it does

1. **Preflight**: consent; builds disposable scratch copies of the project *outside* the project folder, skipping secrets.
2. **Harvest**: inventories the folder and extracts the conversation (user and assistant text from the Claude Code transcript for that folder, plus memory notes), redacted for secrets.
3. **Handover**: writes `handover/README.md` plus context, state and next steps, decisions, gotchas, file map, how to run, glossary, working agreements, history digest, and an honest list of unknowns, every claim tagged verified / from the conversation / inferred.
4. **Standard exam (up to 3 rounds)**: an independent Sonnet agent reads the *project only* (not the handover) and writes 10 questions and a hidden answer key with evidence. A fresh **Haiku** successor reads the handover and answers; a **Sonnet** examiner grades. **Pass = 10/10 fully correct.** After a failure the docs are fixed (generally, never by pasting the question) and the round reruns. If round 3 still fails, it is reported and the run continues.
5. **Hard exam**: an **Opus** author writes 10 nuance questions from the project *and* the conversation (traps, rejected alternatives, standing rules, conflicting sources, done vs planned). A **Sonnet** successor takes it, an **Opus** critic grades it, and the docs are updated.
6. **Final round**: one more Haiku round on a **fresh** set of 10 questions, so a pass cannot be explained by docs tuned to earlier questions.
7. **Report**: `handover/.passthebaton/REPORT.md` with scores, failures, doc diffs per round, and where everything is.

## Surviving usage limits

All progress is on disk: `handover/.passthebaton/state.json` and per-step artifacts; steps are idempotent and the plan is recomputed from them. If a usage limit hits mid-run the orchestrator marks the step interrupted, says so and stops. When limits reset (the desktop app sends a "continue" message, or you run `/passthebaton resume`) it picks up at the interrupted step. A SessionStart hook reminds a fresh session in the same folder that an unfinished run exists. It does **not** wake itself up across sessions.

## Safety

- Test agents work in scratch copies in `~/.passthebaton/scratch/`, never the original. Secrets (`.env*`, keys, credentials, service-account files…) are never copied; git history is left out unless you ask for it.
- Read-only by default: no installs, no network, no writes. Commands only with `--run-commands`.
- Everything written to `handover/`, logs and reports is scanned and redacted for secret-looking values.
- Nothing is pushed or published. `CLAUDE.md` is changed only with your yes.

## Honest limits

- Passing shows a fresh agent **on the same account, machine and tooling** can answer from the docs. It does not prove another account behaves identically, and it cannot recover knowledge that was never written anywhere (the report lists what the writer could not confirm).
- A model grades a model. Keys are built from evidence and spot-checked, but a wrong key is possible; the report flags suspect questions.
- Isolation of test agents is by instruction plus a scratch copy, not an OS sandbox. For untrusted projects run in a container or throwaway user.
- The secret scanner is pattern-based and does not read `.git`.
- Cost: a full run is many agent calls (an author, up to 3 Haiku rounds with examiner, hard exam with Opus twice, a final round). It is meant for projects worth handing over.

## What you get

```
handover/
  README.md  01_PROJECT_CONTEXT.md  02_STATE_AND_NEXT_STEPS.md  03_DECISIONS.md  04_GOTCHAS_AND_TRAPS.md
  05_FILE_MAP.md  06_HOW_TO_RUN.md  07_GLOSSARY.md  08_WORKING_AGREEMENTS.md  09_HISTORY_DIGEST.md
  10_UNKNOWNS_AND_UNVERIFIED.md
  .passthebaton/   state, events.log, REPORT.md, harvest/, exam/, answer_key/, rounds/, diffs/
```

Consider adding `handover/.passthebaton/answer_key/` and `handover/.passthebaton/harvest/` to `.gitignore`: the latter is your raw conversation.

## Layout

```
.claude-plugin/   plugin.json, marketplace.json
skills/passthebaton/SKILL.md + references/   the orchestration instructions
scripts/          pb_state.py (resumable state), make_scratch.py, scan_secrets.py, harvest_context.py, build_report.py, resume_notice.py
hooks/hooks.json  SessionStart resume reminder
```

MIT licensed.
