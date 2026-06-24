"""Rebuild the public board from the merged entries (the append-only log -> artifacts).

Run by .github/workflows/build.yml on each push to main that lands an entry. Produces:
  board.json   — full verified rows; consumed by `haid rank --refresh` and the package's
                 sanitizing cross-repo sync (which re-verifies + projects to a whitelist).
  index.html   — the GitHub Pages landing page (self-reported table).

Entries are re-verified here (content_hash + leak guard, via the installed `haid` package)
even though the validate workflow already gated them — the board never emits a bad row.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from haid.report import benchmark

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "entries"
BOARD_JSON = ROOT / "board.json"
INDEX_HTML = ROOT / "index.html"
SCHEMA_VERSION = "1.1"


def load_rows() -> list[dict]:
    rows = []
    for f in sorted(ENTRIES.glob("*.json")):
        payload = json.loads(f.read_text(encoding="utf-8"))
        benchmark.assert_no_leaks(payload)
        if not benchmark.verify(payload):
            raise SystemExit(f"refusing to build: {f.name} content_hash does not verify")
        if f.stem != payload.get("github_username"):
            raise SystemExit(f"refusing to build: {f.name} != github_username "
                             f"{payload.get('github_username')!r}")
        rows.append(payload)
    rows.sort(key=lambda r: (r.get("value_overall") or -1), reverse=True)
    return rows


_COLS = [
    ("rank", "#"), ("github_username", "user"), ("project", "project"),
    ("value_overall", "overall score"), ("achievement_total", "achievement"),
    ("volume_loc_total", "volume (LOC)"), ("difficulty_rung_median", "difficulty"),
    ("cleanliness_pct_median", "cleanliness"), ("normalized_tokens_total", "norm. tokens"),
]


def render_index(rows: list[dict], generated_at: str) -> str:
    def td(v):
        return f"<td>{html.escape('' if v is None else str(v))}</td>"
    body = []
    for i, r in enumerate(rows, 1):
        cells = [f"<td>{i}</td>"] + [td(r.get(k)) for k, _ in _COLS[1:]]
        ver = f"{'·'.join(r.get('ladder_versions', {}).values())} / {r.get('combiner_config_hash', '')}"
        cells.append(f"<td class='ver'>{html.escape(ver)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    head = "".join(f"<th>{html.escape(l)}</th>" for _, l in _COLS) + "<th>ladders/combiner</th>"
    n = len(rows)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HAID community benchmark</title>
<style>
 body {{ font: 15px/1.5 system-ui, sans-serif; margin: 2rem auto; max-width: 64rem; padding: 0 1rem; }}
 table {{ border-collapse: collapse; width: 100%; }}
 th, td {{ padding: .4rem .6rem; border-bottom: 1px solid #ddd; text-align: right; }}
 th:nth-child(-n+3), td:nth-child(-n+3) {{ text-align: left; }}
 .ver {{ color: #888; font-size: 12px; font-family: ui-monospace, monospace; }}
 .note {{ color: #666; }}
</style></head><body>
<h1>HAID — community benchmark</h1>
<p class="note">Self-reported achievement scores from Claude Code sessions, opt-in. Rows are
<strong>self-reported</strong> (the only gate is a plausibility + integrity check) and are only
comparable within the same anchor-ladder &amp; combiner version. {n} entr{'y' if n == 1 else 'ies'}.
Generated {html.escape(generated_at)}.</p>
<table><thead><tr>{head}</tr></thead><tbody>
{chr(10).join(body)}
</tbody></table>
<p class="note">Add your own: <code>pip install haid</code>, then <code>haid submit</code>
(it shows exactly what becomes public first). Viewing uploads nothing.</p>
</body></html>
"""


def main() -> int:
    rows = load_rows()
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    board = {"schema_version": SCHEMA_VERSION, "kind": "haid_benchmark_board",
             "generated_at": generated_at, "n_entries": len(rows), "rows": rows}
    BOARD_JSON.write_text(json.dumps(board, indent=1) + "\n", encoding="utf-8")
    INDEX_HTML.write_text(render_index(rows, generated_at), encoding="utf-8")
    print(f"built board: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
