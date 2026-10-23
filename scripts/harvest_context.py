#!/usr/bin/env python3
"""Harvest what a handover needs, into <root>/handover/.passthebaton/harvest/.

  harvest_context.py --root PROJECT [--session ID | --all-sessions] [--max-chars 1500] [--transcripts-root OLD_PATH] [--until ISO_UTC]

Produces:
  inventory.md      tree (secrets/deps/build skipped), sizes, git log + status, top-level docs list
  conversation.md   user and assistant TEXT from this project's Claude Code transcripts
                    (tool calls/results and thinking are dropped; each message capped at --max-chars)
  memory/           copies of the project's Claude Code memory notes, if any
  harvest.json      what was found (session ids, message counts, truncation)

Claude Code keys its state by folder path: ~/.claude/projects/<path with every non-alphanumeric
character replaced by '-'>/ . Default is the most recently modified session; the conversation
that is running right now is that one.
"""
import argparse, json, os, re, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from make_scratch import SKIP_DIRS, is_secret  # noqa: E402


def enc(path):
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def text_of(msg):
    c = msg.get("content")
    if isinstance(c, str):
        return c
    out = []
    for b in c or []:
        if isinstance(b, dict) and b.get("type") == "text":
            out.append(b.get("text", ""))
    return "\n".join(out)


def conversation(jsonl, cap, until=None):
    lines, n_trunc, n = [], 0, 0
    for raw in open(jsonl, encoding="utf-8", errors="replace"):
        try:
            o = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if until and o.get("timestamp", "") > until:
            continue
        if o.get("isSidechain") or o.get("type") not in ("user", "assistant"):
            continue
        t = text_of(o.get("message", {})).strip()
        if not t or t.startswith("<system-reminder>") or "<command-name>" in t[:200]:
            continue
        who = "USER" if o["type"] == "user" else "ASSISTANT"
        if len(t) > cap:
            t = t[:cap] + f"\n[... truncated {len(t) - cap} chars]"
            n_trunc += 1
        n += 1
        lines.append(f"### {who} · {o.get('timestamp', '')}\n{t}\n")
    return "\n".join(lines), n, n_trunc


def tree(root, limit=1500):
    out, count = [], 0
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and d != ".git" and not (rel == Path("handover") and d == ".passthebaton"))
        for fn in sorted(filenames):
            if is_secret(fn):
                continue
            p = Path(dirpath) / fn
            try:
                sz = p.stat().st_size
            except OSError:
                continue
            count += 1
            if count <= limit:
                out.append(f"{rel / fn}  ({sz} B)")
    if count > limit:
        out.append(f"... {count - limit} more files not listed")
    return "\n".join(out), count


def sh(cmd, cwd):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"(unavailable: {e})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--session")
    ap.add_argument("--all-sessions", action="store_true")
    ap.add_argument("--max-chars", type=int, default=1500)
    ap.add_argument("--until", help="ISO UTC timestamp; ignore messages after it (to match a folder snapshot taken earlier)")
    ap.add_argument("--transcripts-root", help="folder whose Claude Code transcripts to use, when the project was moved/cloned to a new path")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    out = root / "handover" / ".passthebaton" / "harvest"
    out.mkdir(parents=True, exist_ok=True)

    # inventory
    t, n_files = tree(root)
    inv = [f"# Inventory of {root}\n", f"{n_files} files (secrets, dependency and build dirs excluded)\n", "```", t, "```\n"]
    if (root / ".git").exists():
        inv += ["## git log (last 40)", "```", sh(["git", "log", "--oneline", "-40"], root), "```",
                "## git status", "```", sh(["git", "status", "--short"], root)[:3000], "```",
                "## branches", "```", sh(["git", "branch", "-a", "--format=%(refname:short)"], root)[:2000], "```"]
    (out / "inventory.md").write_text("\n".join(inv))

    # conversation + memory
    proj = Path.home() / ".claude" / "projects" / enc(Path(a.transcripts_root).resolve() if a.transcripts_root else root)
    info = {"claude_project_dir": str(proj), "found": proj.exists(), "sessions_used": [], "messages": 0, "truncated": 0}
    if proj.exists():
        sessions = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if a.session:
            sessions = [s for s in sessions if s.stem == a.session]
        elif not a.all_sessions:
            sessions = sessions[:1]
        body = []
        for s in reversed(sessions):  # oldest first
            txt, n, nt = conversation(s, a.max_chars, a.until)
            body.append(f"\n# SESSION {s.stem} ({s.stat().st_size} bytes)\n\n{txt}")
            info["sessions_used"].append(s.stem)
            info["messages"] += n
            info["truncated"] += nt
        (out / "conversation.md").write_text("".join(body))
        mem = proj / "memory"
        if mem.exists():
            shutil.copytree(mem, out / "memory", dirs_exist_ok=True)
            info["memory_files"] = len(list((out / "memory").glob("*.md")))
    else:
        (out / "conversation.md").write_text("(no Claude Code transcript found for this folder path)\n")
    (out / "harvest.json").write_text(json.dumps(info, indent=2))
    print(json.dumps(info))


if __name__ == "__main__":
    main()
