# README refresh (backlog task 3)

Bring the README up to date with the battery-life work, check its existing claims against this
machine, add a CI badge, and prepare GitHub topics. Report to the lead; it updates PROGRESS.md
and the backlog.

## Steps

1. **Battery-life work in the README.**
   - Findings: the reproducible-kernel bullet says eight patches, one (`arm_scmi`) untested.
   - New Findings bullet: only 4 of 10 cores scale; cause in the `arm_scmi` perf turbo
     flagging; fix untested. Link `docs/power.md`.
   - Status: a CPU frequency scaling / battery row (cluster 0 only on `+sl7.3`; patch 0006
     and `sl7-power-mode` untested).
   - Getting started step 5 links `docs/power.md`; Layout rows for `patches/kernel-7.3/` and
     `tools/` mention the `arm_scmi` fix and power.
   - `docs/known-issues.md`: replace "as of October 2026" with the date of this check.
2. **Check existing claims, read-only.** Touchpad cold boots on 7.3 (`sl7-touchpad-diag`
   journal, `journalctl -b -N`), the right-speaker question from `docs/audio.md` (wireplumber
   `PA Volume` errors, mixer state), face unlock on 7.3 (Howdy/PAM approvals in the journal).
   Change a claim only where the evidence is clear; record what was found either way.
3. **CI badge** for `.github/workflows/ci.yml` under the title.
4. **Topics and description:** read `gh repo view --json description`, propose 6-10 topics.
   Change nothing on GitHub.

Not touched (another task owns them): `patches/kernel-7.3/README.md`,
`patches/kernel-7.3/0006-*`, `docs/power.md`. Not touched (the lead owns them): `PROGRESS.md`,
`docs/plans/active/resume-ready.md`.

## Done when

The CLAUDE.md checks pass, every relative link in the Markdown files resolves, the work is
committed on the branch, and the lead has the report and the proposed topics.
