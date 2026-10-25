#!/usr/bin/env python3
"""List the Claude Code sessions recorded for a folder, newest first, so the user can pick which
conversation(s) to harvest.

  list_sessions.py --root PROJECT [--transcripts-root OLD_PATH] [--limit 12] [--json]

Claude Code keys transcripts by folder path: ~/.claude/projects/<path, every non-alphanumeric
character replaced by '-'>/<session-id>.jsonl . Use --transcripts-root when the project was moved
or cloned to a new path and its history lives under the old one.

Prints: id, last modified, size, number of user/assistant messages, and the first user message
(shortened, secrets are not scanned here: do not paste the output elsewhere).
"""
import argparse, json, re, sys, time
from pathlib import Path


def enc(p):
    return re.sub(r"[^A-Za-z0-9]", "-", str(p))


def first_text(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return c
    return "\n".join(b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text")


def summarise(path):
    n, first = 0, ""
    for raw in open(path, encoding="utf-8", errors="replace"):
        try:
            o = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if o.get("isSidechain") or o.get("type") not in ("user", "assistant"):
            continue
        t = first_text(o.get("message", {})).strip()
        if not t or t.startswith("<system-reminder>") or "<command-name>" in t[:200]:
            continue
        n += 1
        if not first and o["type"] == "user":
            first = " ".join(t.split())[:110]
    return n, first


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--transcripts-root")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    base = Path(a.transcripts_root or a.root).resolve()
    proj = Path.home() / ".claude" / "projects" / enc(base)
    if not proj.exists():
        print(f"no Claude Code transcripts found for {base} (looked in {proj})", file=sys.stderr)
        sys.exit(1)
    files = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    rows = []
    for f in files[: a.limit]:
        n, first = summarise(f)
        rows.append({"id": f.stem, "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime)),
                     "kb": round(f.stat().st_size / 1024), "messages": n, "first_user_message": first})
    if a.json:
        print(json.dumps({"total_sessions": len(files), "shown": rows}, indent=1))
        return
    print(f"{len(files)} session(s) for {base}; showing the {len(rows)} most recent\n")
    for r in rows:
        print(f"{r['id']}  {r['modified']}  {r['kb']:>6} KB  {r['messages']:>5} msgs  {r['first_user_message']}")


if __name__ == "__main__":
    main()
