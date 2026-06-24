"""Validate one submission entry — a thin wrapper over the package's own gate.

All the real logic (identity, integrity, leak guard, current ladder+combiner version,
plausibility) lives in `haid.report.benchmark.validate_entry`, so this data repo can stay
free of application code and the gate can never drift from what `haid submit` produced.
CI installs a PINNED `haid` (see the workflows) and runs:

  python scripts/validate_submission.py --author <github-login> entries/<user>.json

Exit 0 = accept; exit 1 = reject with a one-line, public-safe reason on stdout. It parses
the entry as DATA only (json.loads) — no submitted code is ever executed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from haid.report import benchmark


def _emit(verdict_path: str | None, ok: bool, reason: str) -> int:
    print(("OK: " if ok else "REJECT: ") + reason)
    if verdict_path:
        Path(verdict_path).parent.mkdir(parents=True, exist_ok=True)
        Path(verdict_path).write_text(json.dumps({"ok": ok, "reason": reason}),
                                      encoding="utf-8")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="validate one HAID benchmark entry")
    ap.add_argument("--author", required=True, help="GitHub login of the PR author")
    ap.add_argument("--verdict", help="also write {ok,reason} JSON to this path (for CI)")
    ap.add_argument("entry", help="path to entries/<username>.json")
    args = ap.parse_args(argv)

    if not args.entry.replace("\\", "/").startswith("entries/"):
        return _emit(args.verdict, False, "entry must live under entries/<username>.json")
    try:
        payload = json.loads(Path(args.entry).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return _emit(args.verdict, False, f"cannot read/parse entry: {e}")
    try:
        benchmark.validate_entry(payload, expected_user=args.author, entry_name=args.entry)
    except benchmark.SubmissionRejected as e:
        return _emit(args.verdict, False, str(e))
    return _emit(args.verdict, True, f"{payload['github_username']} / {payload['project']} "
                 f"(value_overall={payload['value_overall']})")


if __name__ == "__main__":
    raise SystemExit(main())
