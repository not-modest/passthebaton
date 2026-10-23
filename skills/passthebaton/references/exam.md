# The exams

All agents here are fresh `Agent` calls (`subagent_type: general-purpose`) with an explicit `model`. They get only what their prompt gives them plus their scratch directory. Fill `<...>` placeholders; paste prompts verbatim otherwise. Directory shorthand: `RUN = <root>/handover/.passthebaton`.

Why the questions are written by a separate agent that never sees the handover docs: if the same mind writes the docs and the questions, the exam only checks that the docs answer what the writer remembered to cover. The author finds out what a successor will actually need by reading the project cold.

## Question author

Used for `author_std` (Sonnet) and for the fresh set in `final.run` (Sonnet). Make the author copy first (project only, `--exclude-handover`; see safety.md).

Prompt:

```
You are writing an entrance exam for an agent who will take over the project in <AUTHOR_DIR>. You have never seen this project before. Read it (README, docs, configs, entry points, tests, git log via `git log` if a .git folder is there, notes). Work ONLY inside <AUTHOR_DIR>; do not read anything outside it. Do not install anything, use the network, or modify any file. Do not run project code.

Write exactly 10 questions that a successor must be able to answer to continue this project safely, and a hidden answer key. Cover, in this spread:
 1-2 orientation: what the project is for and what state it is in
 1   how to run/verify something (exact command or procedure, and the expected result)
 1-2 where things live (a specific file/module/dataset and what is in it; what is authoritative if two disagree)
 1-2 a gotcha or trap that is discoverable from the files (something that looks right but is wrong, a file not to edit, a stale script)
 1   a design choice and the reason for it, if the files record one
 1   a "what do you do next and why" question about current work
 1   one question whose honest answer is "the files do not record this" (so we can tell guessing from reading)
Rules: every question must be answerable from the files, specific, unambiguous, with a checkable answer (no yes/no, no opinion). At least 3 must need information from two different files. Avoid trivia that does not help someone continue the work. Do not write questions about secrets or credentials.

For each question the key entry must contain: id (1-10), question, answer (the complete correct answer), must_include (the short list of facts an answer needs to be fully correct), evidence (file paths with line numbers or the exact command whose output proves it), and common_wrong_answers (what a careless reader would say). {{AVOID}}

Return ONLY a JSON object: {"questions":[{"id":1,"question":"..."},...], "key":[{"id":1,"question":"...","answer":"...","must_include":["..."],"evidence":["path:line"],"common_wrong_answers":["..."]},...]}
```

`{{AVOID}}`: empty for `author_std`; for the final round: `Do not reuse or rephrase any of these earlier questions, and cover different ground where you can: <the earlier question texts>.`

Save: questions only → `RUN/exam/standard_questions.json` (or `final_questions.json`); the full object → `RUN/answer_key/standard.json` (or `final.json`). **The key never goes into a prompt for a successor, and never into any scratch copy.** Check: 10 questions, ids 1-10, every key entry has non-empty `must_include` and `evidence`. If the JSON is malformed, re-ask once; if still bad, fix it yourself.

You (orchestrator) may spot-check 3 keys by opening the cited evidence; correct the key if wrong and log it in `events.log`. A wrong key makes the exam meaningless.

## Haiku round

Step `haikuN.run` (N = 1, 2, 3) and `final.run`. Make a **new** successor copy (with `handover/`, without `.passthebaton`). Spawn one agent, `model: haiku`.

Prompt:

```
You are taking over a project. You have no memory of earlier work. Everything you may know is in <SCRATCH_DIR>. Start with <SCRATCH_DIR>/handover/README.md and follow it; the handover set is meant to let you continue the work. Then answer the exam below.

Rules:
- Work ONLY inside <SCRATCH_DIR>. Do not read any path outside it.
- Do not install anything, use the network, or modify/create/delete any file. {{COMMANDS}}
- If something looks like a credential, do not repeat it; say "credential-like value at <path>".
- Answer from the handover docs first; open code or other files to confirm or to fill gaps. For every answer, say where you found it: "handover" (the handover docs were enough), "project" (you had to dig through the project), or "guess" (you could not find it).
- If the files do not record the answer, say exactly that ("not documented") and say what you found instead. Do not invent.
- Be specific: file paths, commands, numbers, names.

Exam:
<the 10 questions, numbered>

Return ONLY a JSON object: {"orientation_notes":"what was unclear or missing in the handover when you began, in your own words (or 'none')","answers":[{"id":1,"answer":"...","found_in":"handover|project|guess","files_consulted":["..."],"confidence":"high|medium|low","doc_gap":"what in the handover would have made this faster or surer (or 'none')"},...]}
```

`{{COMMANDS}}`: `Do not run any commands that execute project code; you may list and read files only.` or, if the user allowed it, `You may run read-only commands (tests, linters, --help, git log/status/diff) if they help; never commands that write, install or touch the network.`

Save the returned JSON to `RUN/rounds/<name>/answers.json` and the questions to `RUN/rounds/<name>/questions.json` (`<name>` = `haiku1`, `haiku2`, `haiku3`, `final`). If the JSON is unparseable, save the raw text as `answers.raw.txt` and re-ask once.

## Grading

Step `<name>.grade`. Examiner: `model: sonnet`. The examiner may read the **original project** (read-only) to verify the evidence, and gets the key.

Prompt:

```
You are a strict examiner. Grade a successor's answers against an answer key. Do not be generous.

Key (with evidence pointers): <contents of the answer key for this question set>
Successor's answers: <contents of answers.json>
Project (read-only, to verify evidence if the key is unclear): <root>. Do not modify anything; do not use the network.

For each question give a verdict:
- "correct": every item in must_include is present or clearly implied, nothing contradicts the key, and no invented detail changes the meaning
- "partial": some but not all of must_include, or correct plus a material error
- "wrong": missing the point, contradicts the key, or invents
- "honest-gap": the key says the files do not record this and the successor said so (counts as correct)
Also say whether the successor's "found_in" claim is believable and whether its doc_gap is a real gap in the handover.

Return ONLY JSON: {"verdicts":[{"id":1,"verdict":"correct|partial|wrong|honest-gap","why":"one or two sentences, naming what was missing or wrong","doc_fix":"what the handover should say so the next reader gets this right (general, not a quote of the question)"},...],"soft_gaps":["questions answered correctly but with found_in=project|guess, and what the docs lacked"],"correct":<number correct incl. honest-gap>,"total":10}
```

Save to `RUN/rounds/<name>/grade.json`. **Pass = 10/10 correct (honest-gap counts).** Record: `pb_state.py result <name>.grade --passed 0|1 --correct N --total 10`. Compute `passed` from the counts yourself; do not trust the examiner's word for it. Write `RUN/rounds/<name>/summary.md` (3-6 lines: score, which questions failed, the pattern, which docs they point at).

## Hard exam

Steps `author_hard`, `hard.run`, `hard.grade`. Harder means nuance: the obvious answer is wrong, two sources conflict, a rule only makes sense with its reason, or the right move is to refuse or ask.

**Author** (`model: opus`). Needs the project copy (no handover) **and** the conversation extract. Copy `RUN/harvest/conversation.md` into the author directory as `CONVERSATION.md` (the author copy exists only for the author; it is a different copy from every successor's). Prompt:

```
You are writing a hard exam for a successor who will take over the project in <AUTHOR_DIR>. You have never seen this project. Read the project and read CONVERSATION.md (the transcript of the work so far: decisions, user corrections, dead ends). Work ONLY inside <AUTHOR_DIR>; no installs, no network, no modifications, do not run project code.

Write exactly 10 questions that test judgement, not recall. Every question must hinge on nuance that a surface reading gets wrong. Use these types, about two of each: 
 (a) a trap: the obvious action or answer is wrong and the reason is in the files or conversation
 (b) a decision with its rationale and the alternatives that were rejected: ask what to do when someone proposes a rejected alternative
 (c) a user preference or standing rule that constrains what the successor may do in a concrete scenario
 (d) conflicting or stale information: two sources disagree; which is right and how do you know
 (e) status: what is done vs merely planned vs blocked, and what is waiting on whom
Each question must be a concrete scenario or ask that has a checkable, defensible answer and a clear wrong answer. Questions may rest on the conversation only if the decision or rule is not fully recorded in the files (that is the point: it tests whether the handover captured the conversation).

Key per question: id, question, answer (complete), must_include (facts and reasoning needed), evidence (file:line, or CONVERSATION.md heading/timestamp), common_wrong_answers, severity_if_wrong ("low|medium|high": what a successor who gets it wrong would break), whether the evidence is in the project, the conversation, or both.

Return ONLY JSON: {"questions":[{"id":1,"question":"..."}...],"key":[...]}
```

Save: `RUN/exam/hard_questions.json`, `RUN/answer_key/hard.json`.

**Successor** (`model: sonnet`): same prompt as the Haiku round (copy `handover/` fresh, no conversation file, no `.passthebaton`), with the hard questions. Save `RUN/rounds/hard/answers.json`, `questions.json`.

**Critic** (`model: opus`): grading prompt as above, but add: `Besides the verdict, state for each wrong or partial answer what concrete harm following it would cause (severity), and what the handover should say. Also list any question where the key itself looks wrong or the question is ambiguous.` Return the same JSON plus `"key_problems":[...]` and per-verdict `"harm":"..."`. Save `RUN/rounds/hard/grade.json`. Record the result (`passed` = all correct; the hard exam is a diagnostic: its result drives doc fixes and is reported, and does not stop the run).

## Final round

Step `final.run`: author a **fresh** 10 questions (Question author prompt with `{{AVOID}}` filled in with the standard and hard question texts) from a new author copy of the project (without `handover/`), then a Haiku round exactly as above on a new successor copy that includes the docs as fixed after the hard exam. Grade with the standard examiner. Pass = 10/10. If it fails, do one `final.fix` and then report; no further rounds.

Rationale: rounds 1-3 reuse questions so improvement is measurable; the final round uses new questions so a pass cannot be explained by docs that were tuned to specific questions.

## When an exam cannot run

If an agent call is refused or limited, follow "Never lose progress" in SKILL.md. If the project is too small for 10 meaningful questions, tell the user and ask whether to continue with fewer; do not pad with trivia.
