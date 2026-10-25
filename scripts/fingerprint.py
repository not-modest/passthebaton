#!/usr/bin/env python3
"""Prove the original project was not modified by a passthebaton run.

  fingerprint.py snapshot --root PROJECT      record sha256/size of every file (before the run)
  fingerprint.py verify   --root PROJECT [--allow CLAUDE.md ...]   compare now vs the snapshot

Only `handover/` is ever written by the plugin (plus `CLAUDE.md` when the user said yes to the
pointer, pass it with --allow). Everything else must be byte-identical. Excluded from the check:
.git internals, dependency/build directories, and handover/ itself.
verify prints a plain verdict, writes handover/.passthebaton/fingerprint_report.json and exits 1
if anything outside the allowed paths changed, appeared or disappeared.
"""
import argparse, hashlib, json, os, sys, time
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".next", "dist", "build", ".cache",
             ".turbo", ".pytest_cache", ".mypy_cache", "target", ".gradle", ".idea", "coverage", "handover"}


def scan(root):
    out = {}
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            p = Path(dp) / f
            if p.is_symlink():
                continue
            rel = str(p.relative_to(root))
            try:
                h = hashlib.sha256()
                with open(p, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
                out[rel] = {"sha256": h.hexdigest(), "size": p.stat().st_size}
            except OSError as e:
                out[rel] = {"error": str(e)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["snapshot", "verify"])
    ap.add_argument("--root", required=True)
    ap.add_argument("--allow", nargs="*", default=[])
    a = ap.parse_args()
    root = Path(a.root).resolve()
    run = root / "handover" / ".passthebaton"
    snap = run / "fingerprint_before.json"
    if a.cmd == "snapshot":
        run.mkdir(parents=True, exist_ok=True)
        data = scan(root)
        snap.write_text(json.dumps({"taken": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "files": data}))
        print(f"fingerprint recorded: {len(data)} files")
        return
    if not snap.exists():
        sys.exit("no fingerprint_before.json; run `snapshot` in preflight first")
    before = json.loads(snap.read_text())["files"]
    now = scan(root)
    allow = set(a.allow)
    changed = sorted(p for p in before if p in now and before[p] != now[p] and p not in allow)
    removed = sorted(p for p in before if p not in now and p not in allow)
    added = sorted(p for p in now if p not in before and p not in allow)
    allowed_touched = sorted(p for p in allow if before.get(p) != now.get(p))
    ok = not (changed or removed or added)
    rep = {"checked": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "files_checked": len(before), "ok": ok,
           "changed": changed, "removed": removed, "added": added, "allowed_paths_touched": allowed_touched}
    (run / "fingerprint_report.json").write_text(json.dumps(rep, indent=1))
    if ok:
        extra = f" (allowed and changed: {', '.join(allowed_touched)})" if allowed_touched else ""
        print(f"VERIFIED: {len(before)} files outside handover/ are byte-identical to the start of the run{extra}.")
    else:
        print("WARNING: files outside handover/ differ from the start of the run.")
        for label, lst in (("changed", changed), ("removed", removed), ("added", added)):
            for p in lst[:30]:
                print(f"  {label}: {p}")
        print("  (a backup copy, if you made one, is in ~/.passthebaton/backups/)")
        sys.exit(1)


if __name__ == "__main__":
    main()
