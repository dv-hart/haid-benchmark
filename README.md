# HAID community benchmark

**→ [View the live leaderboard](https://dv-hart.github.io/haid-benchmark/)**

A public, opt-in leaderboard for [HAID](https://github.com/dv-hart/haid) — a local tool
that audits your own Claude Code sessions and scores how effectively you collaborate with
the AI. Run HAID on your sessions, and if you like, submit your score to see how you
compare with the community.

Looking at the board needs no account and uploads nothing. Submitting is entirely up to
you.

## Get on the board

1. **Install HAID** and run it on your recent Claude Code sessions — see the
   [HAID repo](https://github.com/dv-hart/haid) for setup.
2. **Run `haid submit`.** It builds a summary-only row — just a handful of numbers, never
   your transcripts, code, prompts, or file paths — shows you exactly what will become
   public, and (with your go-ahead) opens a pull request with your entry.
3. **Wait a minute.** An automated check verifies your row and merges it, and your score
   appears on the [leaderboard](https://dv-hart.github.io/haid-benchmark/).

You'll need a GitHub account to submit — your identity on the board comes from your pull
request. Resubmit anytime; a new score replaces your old one.

## Reading the board

Each row is one person's best self-reported score. The scoring formula evolves over time,
and **scores are only comparable within the same version** (shown in the right-hand
column), so the board groups people by version — you're always ranked against others
measured the same way.

Scores are self-reported: the automated check confirms each row is well-formed and
realistic, but the number itself is computed on the submitter's own machine. Think of it
as a friendly, honest-effort leaderboard, not a refereed contest.

## Your privacy

- A submission contains **only summary metrics** — never transcripts, code, prompts, or
  paths. `haid submit` shows you the full payload before anything leaves your computer.
- **Viewing the board sends nothing** and needs no account.
- **Submitting is opt-in** and tied to your GitHub identity.

## Questions or problems?

Open an issue on the [HAID repo](https://github.com/dv-hart/haid/issues).
</content>
