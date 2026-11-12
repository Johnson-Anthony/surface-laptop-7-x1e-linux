# Progress

## Done

- 2026-10-27: repo created (private) with the 7.3 patch series and build tooling, device-tree
  overlays, IR camera and face unlock, deep sleep, touchpad tools, audio, MAC notes,
  `sl7-status`, README, credits and CI (green).
- 2026-11-12: set up as a long-running project; backlog in
  `docs/plans/active/resume-ready.md`.
- 2026-11-12: battery-life work merged (task 1): `tools/power/sl7-power-mode` (parks CPUs with
  no cpufreq policy on battery) with an optional niri refresh-rate hook, its service and udev
  rule, `docs/power.md`, and patch 0006 (`arm_scmi` perf: no turbo OPPs without a sustained
  frequency) in the 7.3 series. `BASE.md`'s final tree is now `5f201035`; `a7533b07` stays as
  the source of the tested `+sl7.3`. Both are untested on the hardware.
- 2026-11-12: README refresh merged (task 3): CI badge, a CPU frequency scaling row and finding,
  eight patches, and every status row rechecked against the 7.3 journals (touchpad 9 boots,
  face unlock 46 approvals at a 1.0 s median, speaker amp settings applied). Rule for status
  rows: `docs/decisions/2026-11-12-readme-status-evidence.md`.

## In progress

- Task 2: `+sl7.4` kernel build on `claude/serene-carson-8b0e7d`.

## Next

1. Build a `+sl7.4` kernel with patch 0006 and the published config unchanged, for the author
   to install and test (checks in `patches/kernel-7.3/README.md` and `docs/power.md`).
2. With the author's OK: set the GitHub topics and description (proposed in task 3's report;
   see the backlog).
3. Fix or document the UCM boot-sequence stop at `WSA_RX0 Digital Volume` (backlog task 6).
4. With the author's OK: make the repo public.
5. With the author's OK: send patches upstream (`arm_scmi`, spi-hid), then the pending forks,
   issues and PRs (ItsLucas, Howdy, panel-edp).

## Broken / known issues

- `sl7-power-mode` was never installed on this machine, although `~/sl7/power/README.md` says
  so: niri's `spawn-at-startup` line for it fails at every login (`NotFound`).
- Patch 0006 needs a `Fixes:` tag for the commit that added turbo marking before it goes upstream.
- The `arm_scmi` fix isn't in the installed kernel (`+sl7.3`): only `policy0` exists, so
  clusters 1 and 2 have no cpufreq.
- Touchpad cold-boot fix not proven on 7.3: no dead pad in 9 boots (6 cold), but the test plan
  asks for 8 good cold boots.
- Speakers not yet listened to on 7.3 (`speaker-test -c 2 -t wav -D default`, low volume).
- UCM boot sequence stops at `WSA_RX0 Digital Volume` when there's no saved ALSA state.
- IR camera stream start sometimes stalls.
