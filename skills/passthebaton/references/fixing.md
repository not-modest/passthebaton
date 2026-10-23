# Fixing the handover (steps `*.fix`)

You, the orchestrator, make the fixes: you hold the conversation context the successor lacked. Inputs: `grade.json` (verdict, why, doc_fix, soft_gaps), the successor's `doc_gap` and `orientation_notes`, and the key's evidence pointers.

## Procedure

1. **Snapshot** the docs before editing: `cp -R` everything in `handover/` except `.passthebaton` into `RUN/diffs/<name>.before/`.
2. For each failed or partial question, and each soft gap: find the cause.
   - **Missing**: the fact is nowhere in the docs. Add it where a reader would look.
   - **Buried or unfindable**: it is there but the successor did not find it. Move it up, add it to the README index, or add a pointer.
   - **Misleading or ambiguous**: reword; add the reason or the counter-example.
   - **Wrong or stale**: correct it against the evidence and say what it replaced.
   - **Not knowable from anything written**: write it into `10_UNKNOWNS_AND_UNVERIFIED.md` and, if the conversation has it, into the right doc.
3. **Fix generally, never to the test.** Do not paste a question, a key answer or an exam phrasing into the docs; do not add a doc entry whose only purpose is to match one question. Ask "what would a reader of any similar question need?" and write that. The fresh-question final round exists to catch teaching to the test.
4. Keep docs tight. Replace rather than append; do not let a fix make the docs longer than the information deserves.
5. Re-run `scan_secrets.py --redact handover/`.
6. **Diff** and log: `diff -ru RUN/diffs/<name>.before handover` excluding `.passthebaton` > `RUN/diffs/<name>.diff`; one-paragraph note of what changed and why appended to `RUN/rounds/<name-of-round>/summary.md`.
7. If the key problems list says the question or key was wrong, fix the key (log it) instead of the docs.
8. `pb_state.py step <name>.fix done`.

## After a failed round 3

Fix as usual, then go on to `author_hard`. The report will say the standard exam did not reach 10/10 and list the remaining gaps.
