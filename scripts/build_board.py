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


def _num(v, digits=1):
    """Thousands-separated number with fixed decimals; '' for None."""
    if v is None:
        return ""
    return f"{float(v):,.{digits}f}"


def _int(v):
    if v is None:
        return ""
    return f"{round(float(v)):,d}"


def _pct(v):
    if v is None:
        return ""
    return f"{float(v) * 100:.0f}%"


def _abbrev(v):
    """Compact large counts: 2478283124 -> 2.48B."""
    if v is None:
        return ""
    v = float(v)
    for unit, size in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(v) >= size:
            return f"{v / size:.2f}{unit}"
    return f"{v:,.0f}"


# (key, header, formatter, css-class). Order drives the rendered table.
_COLS = [
    ("rank", "#", None, "rank"),
    ("github_username", "user", None, "user"),
    ("project", "project", None, "project"),
    ("value_overall", "overall score", lambda v: _num(v, 1), "score"),
    ("achievement_total", "achievement", lambda v: _num(v, 1), "num"),
    ("volume_loc_total", "volume (LOC)", _int, "num"),
    ("difficulty_rung_median", "difficulty", lambda v: _num(v, 1), "num"),
    ("cleanliness_pct_median", "cleanliness", _pct, "num"),
    ("normalized_tokens_total", "norm. tokens", _abbrev, "num"),
]


def render_index(rows: list[dict], generated_at: str) -> str:
    body = []
    for i, r in enumerate(rows, 1):
        cells = []
        for key, _, fmt, cls in _COLS:
            if key == "rank":
                medal = {1: " top1", 2: " top2", 3: " top3"}.get(i, "")
                cells.append(f"<td class='rank{medal}'>{i}</td>")
                continue
            raw = r.get(key)
            text = html.escape(fmt(raw) if fmt else ("" if raw is None else str(raw)))
            cells.append(f"<td class='{cls}'>{text}</td>")
        ladders = "·".join(r.get("ladder_versions", {}).values())
        ver = f"{ladders} / {r.get('combiner_config_hash', '')}"
        cells.append(f"<td class='ver'>{html.escape(ver)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    head = "".join(f"<th class='{cls}'>{html.escape(l)}</th>" for _, l, _, cls in _COLS)
    head += "<th class='ver'>ladders / combiner</th>"
    n = len(rows)
    plural = "entry" if n == 1 else "entries"
    short_date = html.escape(generated_at.replace("T", " ").replace("+00:00", " UTC"))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HAID — community benchmark</title>
<meta name="description" content="HAID community benchmark: self-reported achievement scores from Claude Code sessions.">
<style>
 :root {{
   --bg: #f6f7f9; --surface: #ffffff; --ink: #1c2024; --muted: #6b7280;
   --line: #e6e8eb; --line-soft: #f0f1f3; --accent: #4f46e5; --accent-soft: #eef0fe;
   --gold: #b4881b; --silver: #707684; --bronze: #9a6a3a;
   --shadow: 0 1px 2px rgba(16,24,40,.04), 0 8px 24px rgba(16,24,40,.06);
 }}
 @media (prefers-color-scheme: dark) {{
   :root {{
     --bg: #0d1117; --surface: #161b22; --ink: #e6edf3; --muted: #8b949e;
     --line: #232a33; --line-soft: #1b2129; --accent: #8b9bff; --accent-soft: #1d2440;
     --gold: #d9b24a; --silver: #aab1bd; --bronze: #c08a55;
     --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.35);
   }}
 }}
 * {{ box-sizing: border-box; }}
 body {{
   font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
   color: var(--ink); background: var(--bg); margin: 0; padding: 3rem 1.25rem 4rem;
   -webkit-font-smoothing: antialiased;
 }}
 .wrap {{ max-width: 72rem; margin: 0 auto; }}
 header {{ margin-bottom: 1.75rem; }}
 .brand {{ display: flex; align-items: center; gap: .65rem; }}
 .logo {{
   width: 2.1rem; height: 2.1rem; border-radius: .55rem; flex: none;
   background: linear-gradient(135deg, var(--accent), #8b5cf6);
   color: #fff; font-weight: 700; font-size: .95rem; letter-spacing: .02em;
   display: grid; place-items: center;
 }}
 h1 {{ font-size: 1.5rem; line-height: 1.1; margin: 0; letter-spacing: -.01em; }}
 .tag {{ color: var(--muted); font-size: .9rem; margin-top: .15rem; }}
 .lead {{ color: var(--muted); max-width: 46rem; margin: 1.1rem 0 0; }}
 .lead strong {{ color: var(--ink); font-weight: 600; }}
 .stats {{ display: flex; flex-wrap: wrap; gap: .5rem .65rem; margin: 1.25rem 0 0; }}
 .chip {{
   display: inline-flex; align-items: baseline; gap: .35rem; background: var(--surface);
   border: 1px solid var(--line); border-radius: 999px; padding: .3rem .8rem; font-size: .82rem;
 }}
 .chip b {{ color: var(--accent); font-weight: 600; }}
 .chip span {{ color: var(--muted); }}
 .card {{
   margin-top: 1.5rem; background: var(--surface); border: 1px solid var(--line);
   border-radius: .9rem; box-shadow: var(--shadow); overflow: hidden;
 }}
 .scroll {{ overflow-x: auto; }}
 table {{ border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }}
 thead th {{
   position: sticky; top: 0; background: var(--surface); z-index: 1;
   font-size: .72rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted);
   font-weight: 600; padding: .85rem .8rem; border-bottom: 1px solid var(--line); white-space: nowrap;
 }}
 td {{ padding: .7rem .8rem; border-bottom: 1px solid var(--line-soft); white-space: nowrap; }}
 tbody tr:last-child td {{ border-bottom: 0; }}
 tbody tr:hover td {{ background: var(--accent-soft); }}
 th.num, td.num, th.score, td.score, th.rank, td.rank {{ text-align: right; }}
 td.score {{ font-weight: 600; color: var(--accent); }}
 td.user {{ font-weight: 600; }}
 td.project {{ color: var(--muted); }}
 td.rank {{ color: var(--muted); font-weight: 600; width: 2.5rem; }}
 td.rank.top1 {{ color: var(--gold); }}
 td.rank.top2 {{ color: var(--silver); }}
 td.rank.top3 {{ color: var(--bronze); }}
 th.ver, td.ver {{ color: var(--muted); font-size: 11px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
 footer {{ margin-top: 1.5rem; color: var(--muted); font-size: .9rem; }}
 .submit {{
   background: var(--surface); border: 1px solid var(--line); border-radius: .9rem;
   padding: 1.1rem 1.25rem; box-shadow: var(--shadow);
 }}
 .submit b {{ color: var(--ink); }}
 code {{
   font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .85em;
   background: var(--accent-soft); color: var(--accent); padding: .1rem .4rem; border-radius: .35rem;
 }}
 .fine {{ margin-top: 1.25rem; font-size: .82rem; line-height: 1.5; }}
</style></head><body>
<div class="wrap">
 <header>
  <div class="brand">
   <div class="logo">HD</div>
   <div>
    <h1>HAID — community benchmark</h1>
    <div class="tag">Self-reported achievement from Claude Code sessions · opt-in</div>
   </div>
  </div>
  <p class="lead">A public leaderboard of agent-coding sessions. Every row is
  <strong>self-reported</strong> — the only gate is a plausibility &amp; integrity check — and
  scores are only comparable within the same anchor-ladder and combiner version.</p>
  <div class="stats">
   <span class="chip"><b>{n}</b><span>{plural}</span></span>
   <span class="chip"><span>updated</span><b>{short_date}</b></span>
   <span class="chip"><span>schema</span><b>{html.escape(SCHEMA_VERSION)}</b></span>
  </div>
 </header>

 <div class="card"><div class="scroll">
  <table>
   <thead><tr>{head}</tr></thead>
   <tbody>
{chr(10).join(body)}
   </tbody>
  </table>
 </div></div>

 <footer>
  <div class="submit">
   <b>Add your own.</b> Run <code>pip install haid</code>, then <code>haid submit</code> —
   it shows exactly what becomes public before anything leaves your machine. Viewing this page
   uploads nothing.
  </div>
  <p class="fine">Scores are self-reported and unaudited beyond an automated integrity check.
  Treat the board as a directional signal, not a ranking of skill.</p>
 </footer>
</div>
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
