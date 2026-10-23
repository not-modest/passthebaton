#!/usr/bin/env python3
"""Assemble handover/.passthebaton/REPORT.md from state.json and the per-round artifacts.

  build_report.py --root PROJECT

Per-round artifacts it looks for (written by the orchestrator, see references/logging.md):
  rounds/<name>/questions.json      [{id, question}]
  rounds/<name>/answers.json        successor answers (+ which docs it read, doc_gaps)
  rounds/<name>/grade.json          {verdicts:[{id, verdict, why}], correct, total, passed}
  rounds/<name>/summary.md          what failed and why
  diffs/<name>.diff                 handover doc changes made after the round
The answer key is deliberately NOT quoted here: it lives in answer_key/ and stays out of the report.
"""
import argparse, json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    a = ap.parse_args()
    d = Path(a.root).resolve() / "handover" / ".passthebaton"
    st = json.loads((d / "state.json").read_text())
    L = [f"# Handover test report\n", f"Project: `{st['project_root']}`  ",
         f"Run started {st['started']}, last update {st['updated']}\n",
         "## Outcome\n", "| Exam | Successor | Examiner | Score | Passed |", "|---|---|---|---|---|"]
    who = {"hard": ("Sonnet", "Opus critic")}
    names = sorted((k[:-6] for k in st["results"] if k.endswith(".grade")),
                   key=lambda k: (k.startswith("final"), k.startswith("hard"), k))
    for n in names:
        r = st["results"][n + ".grade"]
        s, e = who.get(n, ("Haiku", "Sonnet"))
        L.append(f"| {n} | {s} | {e} | {r['correct']}/{r['total']} | {'yes' if r['passed'] else 'NO'} |")
    std = [n for n in names if n.startswith("haiku")]
    if std and not st["results"][std[-1] + ".grade"]["passed"]:
        L.append("\n**The standard exam did not reach 10/10 within the round limit.** The remaining gaps are listed below; "
                 "the run continued to the hard exam as agreed.")
    L.append("\n## Step log\n")
    for k, v in st["steps"].items():
        L.append(f"- `{k}`: {v['status']} ({v['at']}){' — ' + v['note'] if v.get('note') else ''}")
    for n in names:
        rd = d / "rounds" / n
        L.append(f"\n## Round `{n}`\n")
        sm = rd / "summary.md"
        L.append(sm.read_text() if sm.exists() else "(no summary written)")
        g = rd / "grade.json"
        if g.exists():
            try:
                for v in json.loads(g.read_text()).get("verdicts", []):
                    L.append(f"- Q{v.get('id')}: **{v.get('verdict')}** — {v.get('why', '')}")
            except ValueError:
                L.append("(grade.json unreadable)")
        df = d / "diffs" / f"{n}.diff"
        if df.exists():
            L.append(f"\nDoc changes after this round: `handover/.passthebaton/diffs/{n}.diff`")
    L.append("\n## Where everything is\n\n- `state.json`, `events.log`: run state and timeline\n- `exam/`: question sets (answer keys are in `answer_key/`, not repeated here)\n"
             "- `rounds/<name>/`: questions, successor answers, grades, summaries\n- `diffs/`: what changed in the handover docs after each round\n- `harvest/`: the inventory and conversation extract the docs were written from")
    (d / "REPORT.md").write_text("\n".join(L) + "\n")
    print(str(d / "REPORT.md"))


if __name__ == "__main__":
    main()
