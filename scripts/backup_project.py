#!/usr/bin/env python3
"""Make a safety copy of a project before a passthebaton run.

  backup_project.py --root PROJECT [--dest-base ~/.passthebaton/backups] [--estimate] [--max-gb 3]

The backup is a faithful copy: it INCLUDES .git and .env files (it is a copy of the user's own
folder, kept on the same machine) and leaves out only regenerable directories (node_modules,
.venv, build output, caches). Prints the destination and how to restore. Never touches the
original. Refuses to copy more than --max-gb unless the user raises it.
"""
import argparse, os, shutil, sys, time
from pathlib import Path

SKIP = {"node_modules", ".venv", "venv", "__pycache__", ".next", "dist", "build", ".cache", ".turbo",
        ".pytest_cache", ".mypy_cache", "target", ".gradle", "coverage"}


def size_of(root):
    total = 0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP and d != "handover"]
        for f in fn:
            try:
                total += (Path(dp) / f).stat().st_size
            except OSError:
                pass
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--dest-base", default=str(Path.home() / ".passthebaton" / "backups"))
    ap.add_argument("--estimate", action="store_true")
    ap.add_argument("--max-gb", type=float, default=3.0)
    a = ap.parse_args()
    root = Path(a.root).resolve()
    sz = size_of(root)
    print(f"{root}: about {sz / 1e6:.1f} MB to copy (dependency and build directories skipped)")
    if a.estimate:
        return
    if sz > a.max_gb * 1e9:
        sys.exit(f"over {a.max_gb} GB: raise --max-gb or use your own backup (git, Time Machine)")
    dest = Path(a.dest_base) / f"{root.name}-{time.strftime('%Y%m%d-%H%M%S')}"
    if dest.exists():
        sys.exit(f"{dest} exists")
    shutil.copytree(root, dest, ignore=lambda d, names: [n for n in names if n in SKIP or (Path(d) == root and n == "handover")],
                    symlinks=True)
    print(f"backup written: {dest}")
    print(f"restore a single file: cp '{dest}/<path>' '{root}/<path>'   (the original is never modified by the run)")


if __name__ == "__main__":
    main()
