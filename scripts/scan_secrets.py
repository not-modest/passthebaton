#!/usr/bin/env python3
"""Scan files/dirs for secrets. Never prints a secret in full.

  scan_secrets.py PATH [PATH...]            report findings, exit 1 if any
  scan_secrets.py --redact PATH [PATH...]   replace findings in place with [REDACTED:<type>], exit 0

Text files only; binary and files over 5 MB are skipped (and counted).
"""
import re, sys
from pathlib import Path

PATTERNS = [
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("anthropic-openai-key", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("bearer-token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{24,}")),
    ("url-credentials", re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]{3,}@[^\s]+")),
    ("assigned-secret", re.compile(
        r"""(?ix)\b(?:api[_-]?key|secret[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|password|passwd|pwd)
            \s*[:=]\s*["']?([^\s"'<>{}$`]{8,})""")),
]
MAX_BYTES = 5 * 1024 * 1024
PLACEHOLDER = re.compile(r"(?i)^(?:x{4,}|\*{4,}|<.*>|your[_-]|example|changeme|placeholder|\$\{|none|null|true|false|redacted)")


def iter_files(paths):
    for p in map(Path, paths):
        if p.is_file():
            yield p
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and ".git" not in f.parts:
                    yield f


def mask(s):
    return s[:3] + "…" + f"({len(s)} chars)"


def scan_text(text):
    hits = []
    for kind, rx in PATTERNS:
        for m in rx.finditer(text):
            val = m.group(1) if kind == "assigned-secret" else m.group(0)
            if kind == "assigned-secret" and PLACEHOLDER.match(val):
                continue
            hits.append((kind, m.start(), m.end(), val))
    return hits


def main():
    args = sys.argv[1:]
    redact = "--redact" in args
    paths = [a for a in args if a != "--redact"]
    if not paths:
        sys.exit(__doc__)
    total, skipped = 0, 0
    for f in iter_files(paths):
        try:
            if f.stat().st_size > MAX_BYTES:
                skipped += 1
                continue
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            skipped += 1
            continue
        hits = scan_text(text)
        if not hits:
            continue
        total += len(hits)
        for kind, s, e, val in hits:
            line = text.count("\n", 0, s) + 1
            print(f"{'REDACTED' if redact else 'FOUND'} {kind} {f}:{line} {mask(val)}")
        if redact:
            # replace the secret value only (for assigned-secret keep the key name); longest-first, end-to-start
            for kind, s, e, val in sorted(hits, key=lambda h: -h[1]):
                if kind == "assigned-secret":
                    i = text.index(val, s)
                    text = text[:i] + f"[REDACTED:{kind}]" + text[i + len(val):]
                else:
                    text = text[:s] + f"[REDACTED:{kind}]" + text[e:]
            f.write_text(text, encoding="utf-8")
    print(f"summary: {total} finding(s), {skipped} file(s) skipped (binary/large)")
    sys.exit(0 if redact or total == 0 else 1)


if __name__ == "__main__":
    main()
