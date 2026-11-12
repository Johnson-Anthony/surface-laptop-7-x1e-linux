# Progress

## Done

- 2026-10-27: repo created (private) with the 7.3 patch series and build tooling, device-tree
  overlays, IR camera and face unlock, deep sleep, touchpad tools, audio, MAC notes,
  `sl7-status`, README, credits and CI (green).
- 2026-11-12: set up as a long-running project; backlog in
  `docs/plans/active/resume-ready.md`.

## In progress

- Task 1 (battery-life work) on `claude/bold-pasteur-c5ca7c`.

## Next

1. Bring in the 2026-11-03 battery-life work: `sl7-power-mode` (`~/sl7/power`) and the
   `arm_scmi` perf patch (`~/sl7-kernel/patches/local/0002-…`), with its author line and trailer
   fixed. The patch hasn't run on the hardware yet.
2. Build a `+sl7.4` kernel with that patch for the author to install and test.
3. Refresh the README for the new work and prepare the GitHub description, topics and CI badge.
4. With the author's OK: make the repo public.
5. With the author's OK: send patches upstream (`arm_scmi`, spi-hid), then the pending forks,
   issues and PRs (ItsLucas, Howdy, panel-edp).

## Broken / known issues

- The `arm_scmi` fix isn't in the installed kernel (`+sl7.3`): only `policy0` exists, so
  clusters 1 and 2 have no cpufreq.
- Untested on 7.3: the touchpad cold-boot fix, and the right-speaker settings.
- IR camera stream start sometimes stalls.
