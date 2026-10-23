# Harvest (step `harvest`)

Goal: collect everything a faithful handover needs: the folder **and** the conversation. The conversation is usually where the decisions, the user's corrections, the rejected options and the unwritten "why" live. Treat it as primary evidence, not an afterthought.

## 1. Run the harvester

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/harvest_context.py --root <root>            # latest session (the one running now)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/harvest_context.py --root <root> --all-sessions   # long projects: every session of this folder
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/harvest_context.py --root <root> --session <id>
```

Output in `<root>/handover/.passthebaton/harvest/`:
- `inventory.md` file tree (secrets/deps/build skipped), git log, status, branches
- `conversation.md` user + assistant text from the transcripts (tool output and hidden reasoning dropped; messages over 1500 chars truncated, raise with `--max-chars`)
- `memory/` Claude Code memory notes for this folder, if any
- `harvest.json` what was found

For a project with several sessions, use `--all-sessions`. If the transcript is huge, read it in slices (Read with offset/limit), newest first for current state, oldest first for origin and decisions.

If `found` is false in `harvest.json` the folder has no Claude Code transcript (new account, moved folder). Say so; the handover then rests on the folder alone and `10_UNKNOWNS` must say the conversation was unavailable. If the user has the transcript elsewhere, ask for its path.

Claude Code keys state by folder path: `~/.claude/projects/<path with each non-alphanumeric char → '-'>/`. A clone at a different path has none of it. That is why the memory notes are copied into `handover/` (via harvest, then summarised into the docs).

## 2. Read the folder yourself

Read, do not run. Order: README/docs → build/config files → entry points → tests (what they pin down) → recent git history (`git log` in the inventory; open the last ~10 commits' messages) → TODO/FIXME/notes files → anything named like ledger, plan, changelog, roadmap, handover. Note for every claim where you saw it. Look for: what is generated vs hand-written, what must not be edited, where state lives outside the folder (databases, services, deployments, accounts), and the commands that prove things work.

## 3. Read the conversation

Extract, with a pointer to where in `conversation.md` (heading timestamp) each came from:
- **Goal and audience**: what the project is for, who it serves, what "done" means.
- **Decisions** the user made, with the reason and what was rejected.
- **Corrections** the user gave you ("no, do it this way"): these are the user's working agreements.
- **Traps hit**: errors, dead ends, what fixed them.
- **State**: what is finished, in progress, blocked, waiting on the user; the order of priorities.
- **Open questions** nobody has answered yet.
- **Vocabulary** the user uses (ids, nicknames, abbreviations).
- **Anything promised** but not delivered.

Prefer the user's later statements over earlier ones when they conflict, and record the conflict.

## 4. Redact

`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scan_secrets.py --redact handover/.passthebaton/harvest` before anyone else reads it.

Mark the step done only when `inventory.md`, `conversation.md` and `harvest.json` exist.
