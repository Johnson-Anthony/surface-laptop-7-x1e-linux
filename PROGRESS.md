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
- 2026-11-12: UCM boot-sequence fix merged (task 6): the card entry sets the prefixed
  `WSA WSA_RX0/RX1 Digital Volume` to 81 itself instead of including `wsa-macro/init.conf`,
  plus `tools/audio/ucm-boot-test` (`check` read-only, `run` for the author). Nothing audible
  changed on this machine (saved state hid it); fresh installs were affected.
- 2026-11-12: pushed and made public, with the author's OK; GitHub topics set (linux,
  linux-kernel, arm64, snapdragon, snapdragon-x, x1e80100, surface-laptop-7, linux-surface,
  device-tree, face-unlock). Description unchanged.

## In progress

- Task 2: `+sl7.4` is built (only `perf.o` and `version.o` changed; modules, DTBs and CRCs are
  identical to `+sl7.3`). Waiting for the author's one-time test boot; steps in
  `~/sl7-kernel/sl7.4-test/TEST-sl7.4.md`. Results go on `claude/serene-carson-8b0e7d`.

## Next

1. Author: test-boot `+sl7.4` once, run the checks, then install it or roll back.
2. Optional, author: `tools/audio/ucm-boot-test run` after reinstalling the card entry (steps
   in `docs/audio.md`, "Boot sequence"). Only fresh installs were affected.
3. With the author's OK: send patches upstream (`arm_scmi`, spi-hid) and report the same UCM
   boot stop to alsa-ucm-conf, then the pending forks,
   issues and PRs (ItsLucas, Howdy, panel-edp).

## Broken / known issues

- `sl7-power-mode` was never installed on this machine, although `~/sl7/power/README.md` says
  so: niri's `spawn-at-startup` line for it fails at every login (`NotFound`).
- The `arm_scmi` fix isn't in the installed kernel (`+sl7.3`): only `policy0` exists, so
  clusters 1 and 2 have no cpufreq.
- Touchpad cold-boot fix not proven on 7.3: no dead pad in 9 boots (6 cold), but the test plan
  asks for 8 good cold boots.
- Speakers not yet listened to on 7.3 (`speaker-test -c 2 -t wav -D default`, low volume).
- UCM boot-sequence fix is in the repo but untested on the hardware (`ucm-boot-test run`); the
  installed card entry still has the old include. Same bug upstream, not reported yet.
- IR camera stream start sometimes stalls.
