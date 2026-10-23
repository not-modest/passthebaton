#!/usr/bin/env python3
"""Split harvest/conversation.md into slices of about --kb KB, cutting only at message headings.

  split_conversation.py --root PROJECT [--kb 140]

Writes harvest/slices/slice_NN.md and prints the list. Used when the conversation is too large
for the orchestrator to read directly: each slice goes to a digest agent (see references/harvest.md).
"""
import argparse
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--kb", type=int, default=140)
a = ap.parse_args()
h = Path(a.root).resolve() / "handover" / ".passthebaton" / "harvest"
text = (h / "conversation.md").read_text()
parts = text.split("\n### ")
head, msgs = parts[0], ["### " + p if i else p for i, p in enumerate(parts[1:])]
out = h / "slices"
out.mkdir(exist_ok=True)
for f in out.glob("slice_*.md"):
    f.unlink()
cur, size, n = [], 0, 0
def flush():
    global cur, size, n
    if cur:
        n += 1
        (out / f"slice_{n:02d}.md").write_text("\n".join(cur))
        cur, size = [], 0
for m in msgs:
    if size + len(m) > a.kb * 1024:
        flush()
    cur.append(m)
    size += len(m)
flush()
print("\n".join(str(p) for p in sorted(out.glob("slice_*.md"))))
