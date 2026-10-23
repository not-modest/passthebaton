#!/usr/bin/env python3
"""Make a disposable scratch copy of a project for a successor/author agent.

  make_scratch.py --src PROJECT --dst DIR [--exclude-handover] [--no-git] [--max-mb 5]

Always excluded: handover/.passthebaton (the hidden answer key, logs and state), secrets
(.env*, keys, credentials, service-account files, .npmrc/.netrc...), dependency and build
directories, files over --max-mb. With --exclude-handover the whole handover/ folder is also
left out (used for the question author, who must see the PROJECT only).
Writes DIR/../<name>.manifest.json listing what was skipped. Never modifies SRC.
"""
import argparse, fnmatch, json, os, shutil, sys
from pathlib import Path

SKIP_DIRS = {"node_modules", ".venv", "venv", "__pycache__", ".next", "dist", "build", ".cache",
             ".turbo", ".pytest_cache", ".mypy_cache", "target", ".gradle", ".idea", "coverage",
             ".aws", ".ssh", ".gnupg", "secrets", "credentials", ".passthebaton"}
SECRET_GLOBS = [".env", ".env.*", "*.env", "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "id_rsa*", "id_ed25519*",
                "*credentials*", "*service-account*.json", "*serviceaccount*.json", ".npmrc", ".netrc", ".pypirc",
                "*.keystore", "token.json", "*.token", ".htpasswd", "secrets.*", "*secret*.json", "*secret*.yaml", "*secret*.yml"]
ENV_EXAMPLE = {".env.example", ".env.sample", ".env.template"}


def is_secret(name):
    if name in ENV_EXAMPLE:
        return False
    return any(fnmatch.fnmatch(name.lower(), g.lower()) for g in SECRET_GLOBS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--exclude-handover", action="store_true")
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--max-mb", type=float, default=5.0)
    a = ap.parse_args()
    src, dst = Path(a.src).resolve(), Path(a.dst).resolve()
    if dst == src or src in dst.parents:
        sys.exit("scratch destination must be outside the source project")
    if dst.exists():
        sys.exit(f"{dst} already exists; choose a new path (scratch copies are never reused)")
    skipped = {"secret": [], "dir": [], "large": [], "unreadable": []}
    copied = 0
    for dirpath, dirnames, filenames in os.walk(src):
        rel = Path(dirpath).relative_to(src)
        keep = []
        for d in dirnames:
            r = rel / d
            if d in SKIP_DIRS or (d == ".git" and a.no_git) or (a.exclude_handover and str(r) == "handover"):
                skipped["dir"].append(str(r))
            elif os.path.islink(Path(dirpath) / d):
                skipped["dir"].append(str(r) + " (symlink)")
            else:
                keep.append(d)
        dirnames[:] = keep
        for fn in filenames:
            sp = Path(dirpath) / fn
            r = rel / fn
            if os.path.islink(sp):
                continue
            if is_secret(fn):
                skipped["secret"].append(str(r))
                continue
            try:
                if sp.stat().st_size > a.max_mb * 1024 * 1024:
                    skipped["large"].append(str(r))
                    continue
                (dst / rel).mkdir(parents=True, exist_ok=True)
                shutil.copy2(sp, dst / r)
                copied += 1
            except OSError as e:
                skipped["unreadable"].append(f"{r}: {e}")
    dst.mkdir(parents=True, exist_ok=True)
    manifest = dst.parent / f"{dst.name}.manifest.json"
    manifest.write_text(json.dumps({"src": str(src), "dst": str(dst), "files_copied": copied,
                                    "exclude_handover": a.exclude_handover, "skipped": skipped}, indent=2))
    print(json.dumps({"dst": str(dst), "files_copied": copied, "skipped_secret_files": len(skipped["secret"]),
                      "skipped_dirs": len(skipped["dir"]), "skipped_large": len(skipped["large"]),
                      "manifest": str(manifest)}))


if __name__ == "__main__":
    main()
