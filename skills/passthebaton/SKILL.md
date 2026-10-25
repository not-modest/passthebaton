---
name: passthebaton
description: Hand a long-running project over to a fresh Claude Code session or account. Reads the folder and the conversation, writes handover docs into handover/, then proves they work by examining fresh Haiku successors (must answer 10 questions correctly), a Sonnet successor on a hard exam graded by an Opus critic, and a final Haiku round, fixing the docs after each failure. Use when the user says "/passthebaton", "pass the baton", "hand this project over", "write a handover", or "make this portable to another account/session". Survives usage limits: say "resume".
argument-hint: "[resume | status | --run-commands]"
---

# passthebaton

You are the **orchestrator**. The user wants a project's context made portable: a successor with no memory of this work (a new session, another account, a colleague's Claude Code) must be able to pick up exactly where this one stops. You write the handover, then you **prove** it by testing fresh agents on it and fixing it until they pass. Everything is logged so the user can see what happened.

Run this in the **main session** (subagents cannot spawn subagents). Use only the standard `Agent` tool; do not depend on the Workflow tool.

`${CLAUDE_PLUGIN_ROOT}` below is this plugin's folder. Scripts are stdlib-only Python 3.

## First, tell the user what is about to happen

Before anything else (unless the argument is `status` or `resume`), print 4-6 plain lines: what this does (writes `handover/` from the folder and conversation, then tests it with fresh agents), that the project is never edited outside `handover/` and a backup is offered, that you will ask a few questions once and then run unattended, roughly how long and how costly it is (tens of minutes; a few million subagent tokens for a long project, much less for a small one), and that it can be resumed after a usage limit. If the argument is `help` or `--help`, print this plus the argument list below and stop.

## Arguments

- none: start a new run for the current working folder (or resume if one is unfinished: ask).
- `resume`: continue an unfinished run (see "Never lose progress").
- `status`: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pb_state.py show --root <root>` and summarise. Stop.
- `help`: print the short guide above and the argument list, then stop.
- `--run-commands`: the user allows successors to run read-only commands (tests, linters). Default is off.

`<root>` = the project folder (the current working directory unless the user says otherwise).

## The pipeline (fixed order; `pb_state.py next` always tells you where you are)

| Step | What | Who |
|---|---|---|
| preflight | consent, safety, scratch copies | you |
| harvest | inventory of the folder + extract of the conversation | script + you |
| handover | write the handover docs into `handover/` | you (you have the conversation) |
| scan_handover | secret scan + redaction of `handover/` and `harvest/` | script |
| author_std | 10 questions + hidden answer key, from the **project only** | Sonnet author |
| haiku1..3 .run/.grade/.fix | fresh Haiku successor takes the 10 questions; Sonnet examiner grades; you fix the docs | Haiku, Sonnet |
| author_hard, hard.run/.grade/.fix | 10 harder questions; Sonnet successor; Opus critic; you fix the docs | Opus, Sonnet, Opus |
| final.run/.grade/.fix | one more Haiku round on a **fresh** question set | Haiku, Sonnet |
| report | `REPORT.md` and a plain summary to the user | script + you |

Rules of the loop:
- **Standard exam passes only at 10/10 fully correct.** Rounds 1-3 reuse the same questions, so improvement is measurable. A round that passes ends the standard exam early. If round 3 still fails, **report it plainly and continue** to the hard exam; do not keep retrying.
- The hard exam and the final round are run regardless of how the standard exam went.
- After each failed round, fix the docs (`references/fixing.md`), then rerun.

## How to run it

1. If `<root>/handover/.passthebaton/state.json` does not exist: do **preflight** (below) then `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pb_state.py init --root <root>`.
2. Loop: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pb_state.py next --root <root>` → JSON with `step` and `do` (a pointer into `references/`). Read that reference section, then:
   1. `pb_state.py step --root <root> <step> running`
   2. do the work; write the artifacts the reference names (they are what makes a step resumable)
   3. record results where the step has them (`pb_state.py result ...`)
   4. `pb_state.py step --root <root> <step> done`
3. Repeat until `next` prints `{"step": "complete"}`. Then run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/build_report.py --root <root>` and give the user the outcome (see `references/logging.md` for what to say).

Reference files (read the one for the current step, not all of them up front):
`references/safety.md` · `references/harvest.md` · `references/handover-spec.md` · `references/exam.md` · `references/fixing.md` · `references/logging.md`

## Preflight (ask once, up front, with AskUserQuestion; then do not ask again)

Read `references/safety.md`. Ask in one call (AskUserQuestion takes up to 4 questions per call: use two calls, items 1-3 and then 4-6, or merge 'git history' and 'redaction'; the session picker is a further call only when asked for):
1. **Which conversation** to harvest. Before asking, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/list_sessions.py --root <root>` to see how many sessions exist for the folder. Options: "This folder + this session only" (recommended when there is little history), "This folder + all its sessions" (recommended for a long-running project; `harvest_context.py --all-sessions`), "This folder + sessions I pick", "Folder only, no conversation". If the user picks "sessions I pick", **do not ask them to type ids**: show the lister's output (id, date, size, messages, first user message) and ask a follow-up AskUserQuestion with the most recent ~8 sessions as multi-select options (label = date + first words, description = id and size), plus "Other" for a session of a different folder (then ask for that folder's path and use `--transcripts-root`). If the project was moved or cloned to a new path and the lister finds nothing, ask for the old folder path and use `--transcripts-root` with it.
2. **Let the test agents run commands?** Label the options exactly: "No, they only read files (Recommended)" and "Yes, they may run tests and other commands (this executes the project's code on your machine)". Explain in the option text: the scratch copy protects your original files, but it is not a sandbox, so tests and linters can still write files, use the network or start processes. Choose yes only for a project the user trusts, where "does this command really work" should be proved.
3. **Safety copy of the project**: first run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/backup_project.py --root <root> --estimate` and tell the user the size. Options: "Yes, make a backup copy now (Recommended)" (runs `backup_project.py --root <root>`, which copies the folder to `~/.passthebaton/backups/<name>-<time>/`, git history and .env included, dependency/build folders left out) and "No, I already have my own backup (git, Time Machine, ...)". Say plainly that the plugin never edits the project outside `handover/`, and that the copy is for reassurance. Do not make the copy without a yes.
4. **CLAUDE.md pointer**: may the finished run append a short pointer block to `CLAUDE.md` so future sessions find the handover? Default no; the docs are still written to `handover/`.
5. **Git history in scratch copies**: successors can read it (useful) but it may hold old secrets the scanner cannot see. Default: leave `.git` out of scratch copies (`--no-git`; the git log is still summarised in `inventory.md`). Yes: copy it.
6. **Conversation redaction**: the conversation extract is scanned for secrets and redacted; ask whether anything else must be excluded.

Right after the answers (and after the backup, if chosen) record the tamper-evidence baseline: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/fingerprint.py snapshot --root <root>`. At the end (step `report`) run `fingerprint.py verify --root <root>` (add `--allow CLAUDE.md` if the user agreed to the pointer) and report its verdict word for word. If it prints WARNING, stop, tell the user which files changed, and point them to the backup.

Then create two scratch copies **outside** the project with `scripts/make_scratch.py` (see safety.md for the exact commands), record them in the event log, and tell the user which files were skipped as secrets.

## Model pinning

| Role | Model |
|---|---|
| Question author (standard + final) | `sonnet` |
| Standard successor (rounds 1-3 + final) | `haiku` |
| Examiner for standard exam | `sonnet` |
| Hard-question author | `opus` |
| Hard successor | `sonnet` |
| Hard critic | `opus` |

Pass `model` on every `Agent` call; use `subagent_type: general-purpose`. Never let a successor inherit your context: each is a fresh agent with only the prompt in `references/exam.md`.

## Never lose progress (usage limits, closed windows, crashes)

State is on disk, never in `/tmp` and never only in your head. `handover/.passthebaton/state.json` plus the per-step artifacts are the truth; `pb_state.py next` recomputes the plan from them.

- Mark a step `running` before work and `done` after. A step interrupted halfway is simply redone; steps are idempotent (outputs overwritten).
- If an `Agent` call fails with a usage-limit, rate-limit or overload error: do **not** retry in a loop. Run `pb_state.py step --root <root> <step> interrupted --note "<error text>"`, tell the user in one or two sentences that the run is paused and saved, and stop. Do not fake a result.
- When the user (or the app, which sends a "limit reset, continue" message) resumes: run `pb_state.py show` and `pb_state.py next`, tell the user in one line where you are, and carry on from that step. The `/passthebaton:passthebaton resume` argument does the same.
- A SessionStart hook in this plugin reminds a fresh session when an unfinished run exists in the folder.
- Commit-friendly: all of it is plain files under `handover/`.
- You cannot reliably schedule your own wake-up across sessions; do not claim you will. The resume mechanism is "run it again, it picks up".

## Honesty rules

- A passing exam shows that a fresh agent **on the same account and tooling** could answer from the docs. It does not prove a different account or machine behaves identically, and it cannot recover knowledge that was never written down anywhere. Say so in the final summary.
- Never report a pass you did not see. Quote the real scores. If a step was skipped or failed, say that.
- Handover docs separate what is **verified** (with the command or file that shows it), what is **from the conversation**, and what is **inferred**. Do not invent history.
