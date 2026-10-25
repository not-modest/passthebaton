# passthebaton

**Hand a long-running Claude Code project to a fresh session, a new account or a colleague, and check that the hand-over actually works.**

Long projects pile up context that lives nowhere a new session can see: decisions made in conversation, why a file must not be touched, what is half-done, what the owner said never to do again. `passthebaton` reads your project folder **and** the conversation, writes a hand-over set into `handover/`, and then *tests it*: fresh agents with no memory try to pick the project up and answer questions, a separate examiner grades them against a hidden answer key, and the docs are fixed until they pass. Everything is logged so you can see what happened.

- **Your project is never edited** outside the new `handover/` folder, and the plugin proves it at the end (see [Safety](#safety)).
- **One command**, a few questions up front, then it runs on its own and survives usage limits.
- Needs only Claude Code, `python3` and `git`. No other installs, no API keys.

---

## 1. Install (two minutes)

### Easiest: paste this to Claude Code

Open Claude Code anywhere and paste:

```text
Please install the passthebaton plugin for Claude Code from this GitHub repository:
https://github.com/not-modest/passthebaton

Steps: add it as a plugin marketplace (not-modest/passthebaton), install the plugin
passthebaton@passthebaton, then run /reload-plugins (or tell me to restart) and confirm
that the command /passthebaton:passthebaton is available. Do not run it yet. If anything
fails, tell me the exact error instead of guessing.
```

### Or do it yourself

In Claude Code:

```text
/plugin marketplace add not-modest/passthebaton
/plugin install passthebaton@passthebaton
/reload-plugins
```

Or from a normal terminal:

```bash
claude plugin marketplace add not-modest/passthebaton
claude plugin install passthebaton@passthebaton
```

**Requirements:** a Claude Code with plugin support (the `/plugin` command exists), `python3` and `git`. Tested on macOS; Linux should work; Windows is untested.

**Check it worked:** type `/passthebaton` in Claude Code; `passthebaton:passthebaton` should appear in the list. Claude Code namespaces plugin commands by plugin name, so the full command is **`/passthebaton:passthebaton`**.

**Update later:** `claude plugin marketplace update passthebaton`, then `claude plugin update passthebaton@passthebaton`, then restart or `/reload-plugins`.

### Alternative: the Georgia Tech copy

The same plugin is mirrored at `https://github.gatech.edu/pmehta334/passthebaton.git`. That host requires you to be signed in even to read a public repository, and Claude Code installs plugins with plain `git`, so git must already know your login. Once, in a normal terminal:

1. On `github.gatech.edu`: profile picture → Settings → Developer settings → Personal access tokens → generate a token with the `repo` scope.
2. Run `git ls-remote https://github.gatech.edu/pmehta334/passthebaton.git`, enter your GT username and paste the token as the password (the macOS Keychain remembers it; or use `gh auth login --hostname github.gatech.edu`).
3. Then use the commands above with `https://github.gatech.edu/pmehta334/passthebaton.git` in place of `not-modest/passthebaton`.

If git sign-in is a problem, clone it yourself and add the folder: `git clone <url> ~/passthebaton`, then `claude plugin marketplace add ~/passthebaton` and `claude plugin install passthebaton@passthebaton`.

---

## 2. Use it

1. Open Claude Code **in the project folder** you want to hand over.
2. Run:

   ```text
   /passthebaton:passthebaton
   ```

   Other forms: `... help` (short guide), `... status` (where is the run?), `... resume` (continue an interrupted run), `... --run-commands` (see the commands question below).

3. Answer the questions it asks once, up front. The recommended option is marked each time, and you can accept the recommendations everywhere.

   | Question | What it means |
   |---|---|
   | **Which conversation?** | Just this session, all sessions of this folder (best for a long project), sessions you pick from a list, or none. |
   | **Let the test agents run commands?** | Default **no**: they only read files. "Yes" lets them run tests and other commands, which executes your project's code on your machine. |
   | **Make a backup copy first?** | Recommended. Copies the folder to `~/.passthebaton/backups/` before anything else. |
   | **Add a pointer to `CLAUDE.md`?** | Default no. If yes, a short block telling future sessions to read `handover/README.md`. |
   | **Keep git history in test copies?** | Default no (old commits may hold secrets). |

4. Leave it running. It tells you each stage as it goes. A real run takes tens of minutes and a few million subagent tokens (see [Cost](#cost)); you can walk away.
5. At the end you get a score table and a short verdict.

### What it does, in order

1. **Preflight**: your answers, the backup, a fingerprint of every file (so it can prove nothing changed), scratch copies outside your project.
2. **Harvest**: inventory of the folder and an extract of the conversation, secrets redacted. For a long conversation it digests the transcript in parallel first.
3. **Write the hand-over** into `handover/`: a README, project context, state and next steps, decisions with reasons, gotchas, file map, how to run, glossary, the owner's working rules, a history digest, and an honest list of unknowns. Every claim is tagged *verified*, *from the conversation* or *inferred*.
4. **Standard exam, up to 3 rounds.** An independent agent that reads only your project (never the hand-over) writes 10 questions and a hidden answer key. A fresh **Haiku** agent with no memory answers from the hand-over; a **Sonnet** examiner grades. **Pass = 10/10.** After a miss the docs are fixed (in general terms, never by pasting the question) and the round reruns. If round 3 still fails it says so and carries on.
5. **Hard exam.** An **Opus** agent writes 10 questions on judgement and on decisions that only the conversation contains; a **Sonnet** successor takes it; an **Opus** critic grades it; the docs are fixed again.
6. **Final round.** One more Haiku round on 10 **new** questions, so a pass cannot come from docs tuned to earlier questions.
7. **Report** and the "your project is untouched" check.

Very small projects: if there is not enough material for 10 real questions it asks whether to run reduced exams or skip them instead of padding with trivia.

---

## 3. After the run: using the hand-over

Everything is in your project folder:

```text
handover/
  README.md                      <- start here
  01_PROJECT_CONTEXT.md  02_STATE_AND_NEXT_STEPS.md  03_DECISIONS.md  04_GOTCHAS_AND_TRAPS.md
  05_FILE_MAP.md  06_HOW_TO_RUN.md  07_GLOSSARY.md  08_WORKING_AGREEMENTS.md
  09_HISTORY_DIGEST.md  10_UNKNOWNS_AND_UNVERIFIED.md
  .passthebaton/                 <- the test: REPORT.md, per-round files, diffs, logs
```

**Please read `handover/README.md` and `10_UNKNOWNS_AND_UNVERIFIED.md` and correct anything wrong or missing.** The tests cannot know what you never wrote down anywhere.

**To hand the project to a new session or account**, copy the project folder (including `handover/`) to the other machine or account, open Claude Code in it, and paste:

```text
You are taking over this project from a previous session. Read handover/README.md first,
then handover/02_STATE_AND_NEXT_STEPS.md and handover/08_WORKING_AGREEMENTS.md, and follow
the reading order there. Do not change anything yet. Tell me what the project is, what state
it is in, what is waiting on me, and what you would do first.
```

If you agreed to the `CLAUDE.md` pointer, new sessions in that folder are told to do this automatically.

Tip: add `handover/.passthebaton/answer_key/` and `handover/.passthebaton/harvest/` to `.gitignore`. The second holds your raw conversation.

---

## Safety

- **Your project is never edited outside `handover/`** (plus `CLAUDE.md` only if you said yes). The plugin records a fingerprint of every file at the start and checks again at the end: you get either "VERIFIED: N files outside handover/ are byte-identical" or a list of exactly what differs. This is evidence after the fact, not a lock; the optional backup is your way back.
- Test agents work in **scratch copies** in `~/.passthebaton/scratch/`, never in your folder. Secret-looking files (`.env*`, keys, credentials, service-account files…) are never copied; git history is left out unless you ask.
- **Read-only by default**: no installs, no network, no file changes by the test agents, except the single answer file each is told to write. Commands only if you opt in.
- Everything written to `handover/`, logs and the report is scanned and redacted for secret-looking values. The scanner is pattern-based and will miss unusual secrets, and it does not read `.git`.
- Nothing is pushed, published or sent anywhere.
- Isolation of test agents is by instruction plus a scratch copy, not an operating-system sandbox. For an untrusted project, run it in a container or a throwaway user account.

## Usage limits and interruptions

All progress is saved to disk (`handover/.passthebaton/state.json` plus a file per step), and each step can be safely redone. If a usage limit stops the run, the plugin says so and stops. When the limit resets, say "continue" or run `/passthebaton:passthebaton resume` and it picks up at the interrupted step. A session-start hook also reminds a fresh session in the same folder that a run is unfinished. It does **not** wake itself up across sessions; you (or the desktop app's "limit has reset" message) restart it.

## Cost

A full run is many agent calls (digest agents for a long conversation, a question author, up to 3 Haiku rounds with an examiner, a hard exam with Opus twice, a final round), so it can cost **a few million subagent tokens** depending on the project and the length of its conversation. Example: one run on a project with about 12 MB of source (roughly 500 files, excluding git history, dependencies and build output) and a 1.1 MB conversation transcript took about 2 million subagent tokens and about 35 minutes. Tiny projects are far cheaper. It is meant for projects worth handing over.

## Troubleshooting

| Problem | Fix |
|---|---|
| `/passthebaton` is not listed | Run `/reload-plugins` or restart Claude Code; check `claude plugin list` shows `passthebaton` enabled. |
| Adding the marketplace asks for a password or fails | If you use the `github.gatech.edu` copy, git needs your sign-in first (see the Georgia Tech section). The github.com copy needs no sign-in. |
| "python3: command not found" | Install Python 3 (it only uses the standard library). |
| It says there is almost no history | The folder has little conversation. Pick "all sessions", choose from the session list, or give the old folder's path if the project was moved. |
| Run interrupted by a usage limit | Wait for the reset, then `/passthebaton:passthebaton resume`. |
| It warns files outside `handover/` changed | Stop, look at the listed files, restore from the backup in `~/.passthebaton/backups/`, and open an issue. |
| Project too small for 10 questions | Choose reduced exams or skip; the docs are still written. |

## Honest limits

- A pass shows that a fresh agent **on the same account, machine and tooling** could answer from the docs. It does not prove that another account behaves identically, and it cannot recover knowledge that was never written anywhere.
- A model grades a model. Answer keys are built from evidence and spot-checked, but a key can be wrong; the report flags suspect questions. A 10/10 on questions the docs do not cover means the successor dug through the project, which the report shows (`found in: project`).
- Question quality limits what the test proves. Small projects give weak tests.

## Layout

```text
.claude-plugin/   plugin.json, marketplace.json
skills/passthebaton/SKILL.md + references/   the orchestration instructions
scripts/          pb_state.py (resumable state), list_sessions.py, make_scratch.py, backup_project.py,
                  fingerprint.py, scan_secrets.py, harvest_context.py, split_conversation.py,
                  build_report.py, resume_notice.py
hooks/hooks.json  session-start reminder when a run is unfinished
```

MIT licensed. Issues and ideas welcome.
