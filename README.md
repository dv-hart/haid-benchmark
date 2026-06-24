# HAID community benchmark (data-only)

The append-only data store and public board for the HAID community benchmark
([ADR-0005](https://github.com/dv-hart/haid/blob/main/docs/decisions/0005-community-benchmark.md)).
This repo holds **only data + the workflows that gate and publish it** — no application
code and no release secrets — so a bad merge here cannot reach the `haid` package or PyPI.

```
entries/<github-username>.json   one row per user (updates overwrite that file)
board.json                       generated: full verified rows; what `haid rank --refresh` reads
index.html                       generated: the GitHub Pages board
scripts/                         thin wrappers over haid.report.benchmark (installed, pinned)
.github/workflows/               validate (read-only) → act (privileged) → build (Pages)
```

## How a row lands

1. A user runs `haid submit`. It builds a **summary-only** row (leak-guarded — no
   transcripts, diffs, prompts, or paths), shows exactly what becomes public, and opens a
   PR adding `entries/<their-username>.json`.
2. **`validate`** (on `pull_request`, *read-only* token) checks the row via the pinned
   `haid` package: integrity hash, leak guard, current ladder + combiner version,
   plausibility, and that **filename == `github_username` == PR author**. It writes a
   verdict artifact. It cannot comment or merge.
3. **`act`** (on `workflow_run`, *privileged*, never touches PR code) reads the verdict and
   auto-merges on pass or comments the reason on fail. It identifies the PR from the run's
   head SHA, not the artifact.
4. **`build`** (on push to main) regenerates `board.json` + `index.html` and deploys Pages.

This two-workflow split keeps the write token away from anything an untrusted PR can
influence. A PR that touches anything other than one `entries/*.json` is rejected before
any validation runs.

## Security posture (please read before changing settings)

- **Branch protection on `main` must require the `validate` check** and disallow merge
  without it. That is what makes "a code change can't masquerade as a data submission"
  mechanical rather than a matter of reviewer vigilance.
- Actions are **pinned to commit SHAs**. Keep them pinned.
- Entries are **self-reported**: the gate proves integrity + plausibility, not honest
  computation (a score is computed on the submitter's machine). Scores are comparable only
  within the same ladder + combiner version; the board is bucketed by both.

Viewing requires no account and uploads nothing. Submission is opt-in and needs a GitHub
account (identity comes from the authenticated PR).
