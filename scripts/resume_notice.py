#!/usr/bin/env python3
"""SessionStart hook: if this folder has an unfinished passthebaton run, say so.
stdout from a SessionStart hook is added to Claude's context, so a fresh session (for example
after a usage limit reset or a closed window) knows to resume instead of starting over."""
import json, os
from pathlib import Path

root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
p = root / "handover" / ".passthebaton" / "state.json"
try:
    st = json.loads(p.read_text())
except (OSError, ValueError):
    raise SystemExit(0)
if st.get("status") != "done":
    print(f"[passthebaton] An unfinished handover run exists for this folder (status: {st.get('status')}, "
          f"last update {st.get('updated')}). Tell the user, and if they want to continue, run /passthebaton resume. "
          f"State: {p}")
