#!/usr/bin/env python3
"""Run-state manager for passthebaton. State lives on disk, so a run survives usage limits,
closed sessions and crashes. Every step is addressable and idempotent: `next` always says
what is left, and re-running a step overwrites its own artifacts.

Usage:
  pb_state.py init  --root PROJECT_ROOT [--force]
  pb_state.py next  --root PROJECT_ROOT          # prints JSON: the next step to do
  pb_state.py step  --root R NAME STATUS [--note TEXT]   # STATUS: running|done|skipped|interrupted|failed
  pb_state.py result --root R NAME --passed 0|1 --correct N --total N [--note TEXT]
  pb_state.py show  --root R
  pb_state.py event --root R TEXT                 # append a line to the event log
"""
import argparse, json, os, sys, time
from pathlib import Path

RUN_SUBDIR = Path("handover") / ".passthebaton"
MAX_STD_ROUNDS = 3

DESCRIPTIONS = {
    "preflight": "references/safety.md: confirm scope, consent, make the scratch copies, record them",
    "harvest": "references/harvest.md: inventory the folder and extract the conversation into harvest/",
    "handover": "references/handover-spec.md: write the handover docs into handover/",
    "scan_handover": "references/safety.md: scan and redact secrets in handover/ and harvest/",
    "author_std": "references/exam.md#question-author: independent agent writes 10 questions + hidden key from the PROJECT ONLY",
    "author_hard": "references/exam.md#hard-exam: Opus writes 10 harder questions + key from project + conversation",
    "hard.run": "references/exam.md#hard-exam: Sonnet successor takes the hard exam in a fresh scratch copy",
    "hard.grade": "references/exam.md#hard-exam: Opus critic grades the hard exam",
    "hard.fix": "references/fixing.md: update handover docs from the hard-exam failures",
    "final.run": "references/exam.md#final-round: author a FRESH 10 questions (project only), then one more Haiku round after the hard-exam changes",
    "final.grade": "references/exam.md#grading: Sonnet examiner grades the final Haiku round",
    "final.fix": "references/fixing.md: last doc fix (no further rounds); then report",
    "report": "references/logging.md: build REPORT.md and tell the user the outcome",
}


def run_dir(root):
    return Path(root).resolve() / RUN_SUBDIR


def state_path(root):
    return run_dir(root) / "state.json"


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def load(root):
    p = state_path(root)
    if not p.exists():
        sys.exit(f"no run state at {p}; run `init` first")
    return json.loads(p.read_text())


def save(root, st):
    st["updated"] = now()
    p = state_path(root)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=2))
    os.replace(tmp, p)


def event(root, text):
    d = run_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "events.log", "a") as f:
        f.write(f"{now()}  {text}\n")


def done(st, name):
    return st["steps"].get(name, {}).get("status") in ("done", "skipped")


def plan(st):
    """Ordered list of step names given the results so far (deterministic)."""
    seq = ["preflight", "harvest", "handover", "scan_handover", "author_std"]
    std_passed = False
    for r in range(1, MAX_STD_ROUNDS + 1):
        seq += [f"haiku{r}.run", f"haiku{r}.grade"]
        res = st["results"].get(f"haiku{r}.grade")
        if res is None:  # grade not recorded yet: the rest depends on it
            return seq, None
        if res["passed"]:
            std_passed = True
            break
        seq.append(f"haiku{r}.fix")
        if not done(st, f"haiku{r}.fix"):
            return seq, std_passed
    seq += ["author_hard", "hard.run", "hard.grade", "hard.fix",
            "final.run", "final.grade"]
    res = st["results"].get("final.grade")
    if res is None:
        return seq, std_passed
    if not res["passed"]:
        seq.append("final.fix")
    seq.append("report")
    return seq, std_passed


def cmd_init(a):
    d = run_dir(a.root)
    if state_path(a.root).exists() and not a.force:
        sys.exit(f"run state already exists at {state_path(a.root)} (use `next` to resume, or --force to restart)")
    for sub in ("harvest", "exam", "rounds", "diffs", "answer_key"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    st = {"version": 1, "status": "running", "project_root": str(Path(a.root).resolve()),
          "started": now(), "updated": now(), "steps": {}, "results": {}, "scratch": {}}
    save(a.root, st)
    event(a.root, "run initialised")
    print(json.dumps({"run_dir": str(d)}))


def cmd_next(a):
    st = load(a.root)
    seq, _ = plan(st)
    for name in seq:
        if not done(st, name):
            st["status"] = "running"
            save(a.root, st)
            print(json.dumps({"step": name, "do": DESCRIPTIONS.get(name) or _round_desc(name),
                              "status_was": st["steps"].get(name, {}).get("status", "pending")}))
            return
    st["status"] = "done"
    save(a.root, st)
    print(json.dumps({"step": "complete"}))


def _round_desc(name):
    kind = name.split(".")[-1]
    return {"run": "references/exam.md#haiku-round: fresh Haiku successor takes the 10 questions in a new scratch copy",
            "grade": "references/exam.md#grading: Sonnet examiner grades against the hidden key",
            "fix": "references/fixing.md: update handover docs from this round's failures"}.get(kind, "")


def cmd_step(a):
    st = load(a.root)
    st["steps"][a.name] = {"status": a.status, "at": now(), "note": a.note or ""}
    if a.status == "interrupted":
        st["status"] = "interrupted"
    save(a.root, st)
    event(a.root, f"step {a.name} -> {a.status} {a.note or ''}")


def cmd_result(a):
    st = load(a.root)
    st["results"][a.name] = {"passed": bool(int(a.passed)), "correct": a.correct, "total": a.total,
                             "at": now(), "note": a.note or ""}
    save(a.root, st)
    event(a.root, f"result {a.name}: {a.correct}/{a.total} passed={bool(int(a.passed))}")


def cmd_show(a):
    st = load(a.root)
    seq, std = plan(st)
    print(json.dumps({"status": st["status"], "started": st["started"], "updated": st["updated"],
                      "plan": [{"step": n, "status": st["steps"].get(n, {}).get("status", "pending")} for n in seq],
                      "results": st["results"], "standard_exam_passed": std}, indent=2))


def cmd_event(a):
    event(a.root, a.text)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    for n in ("init", "next", "show"):
        s = sp.add_parser(n); s.add_argument("--root", required=True)
        if n == "init":
            s.add_argument("--force", action="store_true")
    s = sp.add_parser("step"); s.add_argument("--root", required=True); s.add_argument("name"); s.add_argument("status", choices=["running", "done", "skipped", "interrupted", "failed"]); s.add_argument("--note")
    s = sp.add_parser("result"); s.add_argument("--root", required=True); s.add_argument("name"); s.add_argument("--passed", required=True); s.add_argument("--correct", type=int, required=True); s.add_argument("--total", type=int, required=True); s.add_argument("--note")
    s = sp.add_parser("event"); s.add_argument("--root", required=True); s.add_argument("text")
    a = p.parse_args()
    {"init": cmd_init, "next": cmd_next, "step": cmd_step, "result": cmd_result, "show": cmd_show, "event": cmd_event}[a.cmd](a)


if __name__ == "__main__":
    main()
