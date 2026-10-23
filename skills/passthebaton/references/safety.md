# Safety

## Principles

1. The original project is never modified by any agent except you, and you only write inside `handover/` (plus the optional `CLAUDE.md` pointer, with consent).
2. Question authors and successors work in **scratch copies outside the project**, never the original.
3. Read-only by default. No installs, no network, no git writes. Commands only if the user passed `--run-commands` / said yes in preflight, and then only read-only ones (tests, linters, `--help`, `git log/status/diff`).
4. Secrets: files that look like credentials are never copied to scratch and never read; text that looks like a secret is redacted before it is written into a handover doc, a log or a report.
5. Never push, publish, email or post anything. The run is local.

## Scratch copies

Pick a run id `YYMMDD-HHMM` and a base `~/.passthebaton/scratch/<project-name>-<run id>/` (never `/tmp`: macOS wipes it, and a lost scratch copy mid-run is a pain; `~/.passthebaton` survives).

Create the copies with the script (each successor round needs its own **new** destination; the script refuses to reuse one):

```bash
# For the question author: the PROJECT ONLY (no handover/ folder at all)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/make_scratch.py --src <root> --dst ~/.passthebaton/scratch/<name>-<id>/author --exclude-handover

# For a successor round: the project WITH handover/ (never handover/.passthebaton: it holds the answer key)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/make_scratch.py --src <root> --dst ~/.passthebaton/scratch/<name>-<id>/<round-name>
```

The script always skips: `.env*`, `*.pem`, `*.key`, `id_rsa*`, `*credentials*`, `*service-account*.json`, `.npmrc`, `.netrc`, `secrets/`, dependency and build dirs, files over 5 MB, symlinks, and `handover/.passthebaton/`. It writes `<dst>.manifest.json` listing every skipped path. Show the user the count of skipped secret-like files (not their contents).

Because the handover docs change after each fix, **make a new successor copy for every round** (the docs in the old copy are stale).

After the run: tell the user the scratch folder can be deleted (`rm -r ~/.passthebaton/scratch/<name>-<id>`). Do not delete it yourself without their say-so.

**Git history is copied by default** (successors may need it to understand the project). It can contain secrets that were committed once and later removed; the secret scanner does not read `.git`. In preflight, tell the user and offer `--no-git` (the scratch copies then have no history, and the docs must say so). Default to keeping it only if the user says yes.

## Secret scanning

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scan_secrets.py handover/ handover/.passthebaton/harvest   # report
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scan_secrets.py --redact handover/ handover/.passthebaton/harvest
```

Run it: (a) right after harvest on `harvest/`, (b) on `handover/` after you write it (step `scan_handover`), (c) again after **every** doc fix, (d) on `rounds/` and `exam/` before building the report. It prints masked findings only. It is pattern-based: it will miss unusual secrets. When writing docs, never copy a value that looks like a token, password, key or personal credential; refer to where it lives ("the API key is in the user's `.env`, not in the repo") instead.

## What to tell successors (verbatim in every prompt)

- Work only inside your assigned directory. Do not read any path outside it.
- You may not install anything, use the network, or modify, create (other than your own answer text) or delete files.
- (If commands are not allowed) Do not run commands that execute project code; reading and listing only.
- If you find something that looks like a credential, do not repeat it; say "credential-like value present at <path>".

## Honest limits to put in the README and the final summary

Enforcement against successors is by instruction plus a scratch copy, not an OS sandbox. A misbehaving agent with shell access could still read elsewhere on the machine. If that matters, the user should run the test in a container or a throwaway user account.

## CLAUDE.md pointer

Only if the user said yes in preflight. Append (never overwrite; create `CLAUDE.md` if absent) exactly the block in `references/handover-spec.md` §Pointer. If CLAUDE.md already contains the marker `<!-- passthebaton -->`, replace that block instead of appending a second one. Show the user the block before writing.
