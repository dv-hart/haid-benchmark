# Maintaining the HAID community benchmark

This is a **data-only repository** ([ADR-0005](https://github.com/dv-hart/haid/blob/main/docs/decisions/0005-community-benchmark.md)).
It holds only data plus the workflows that gate and publish it — no application code and no
release secrets — so a bad merge here can never reach the `haid` package or PyPI.

```
entries/<github-username>.json   one row per user (updates overwrite that file) — source of truth
scripts/                         thin wrappers over haid.report.benchmark (installed, pinned)
.github/workflows/               validate (read-only) → act (privileged) → build (Pages)
```

`board.json` (the full verified rows, which `haid rank --refresh` reads) and `index.html`
are **generated, Pages-only artifacts**. They are deployed to GitHub Pages by `build` and
are *never* committed to `main`. The append-only `entries/` files are the audit trail; the
board is derived from them.

## How a row lands

1. A user runs `haid submit`, which opens a PR adding `entries/<their-username>.json`.
2. **`validate`** (on `pull_request`, *read-only* token) checks the row via the pinned
   `haid` package: integrity hash, leak guard, current ladder + combiner version,
   plausibility, and that **filename == `github_username` == PR author**. It writes a
   verdict artifact; it cannot comment or merge.
3. **`act`** (on `workflow_run`, *privileged*, never touches PR code) reads the verdict and
   auto-merges on pass or comments the reason on fail. It identifies the PR from the run's
   head SHA, not the artifact.
4. **`build`** (on push to main / manual dispatch) regenerates `board.json` + `index.html`
   and deploys Pages.

This two-workflow split keeps the write token away from anything an untrusted PR can
influence. A PR that touches anything other than one `entries/*.json` is rejected before
any validation runs.

## Security posture (please read before changing settings)

- **Branch protection on `main` must require the `validate` check** and disallow merge
  without it. That is what makes "a code change can't masquerade as a data submission"
  mechanical rather than a matter of reviewer vigilance.
- Actions are **pinned to commit SHAs**. Keep them pinned.
- Entries are **self-reported**: the gate proves integrity + plausibility, not honest
  computation. Scores are comparable only within the same ladder + combiner version; the
  board is bucketed by both.
</content>
