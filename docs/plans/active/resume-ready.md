# Resume ready

Goal: the first version from [SPEC.md](../../SPEC.md): current, accurate, findable, public, and
at least one patch upstream.

## Tasks

| # | Task | Depends on | Status |
|---|---|---|---|
| 1 | Battery-life work into the repo: `sl7-power-mode`, its docs, and the `arm_scmi` patch in the 7.3 series | | done, merged 2026-11-12 (`f756b21`) |
| 2 | Build `+sl7.4` with the `arm_scmi` patch; the author installs and tests it; record the results | 1 | running (`claude/serene-carson-8b0e7d`): tree ready, `Fixes:` tag added, build waiting for free RAM |
| 3 | README refresh for the new work; GitHub description, topics and CI badge prepared | 1 | done, merged 2026-11-12 (`3aa7072`); topics and description proposed, waiting for the author's OK |
| 4 | Make the repo public | 1-3, author's OK | waiting |
| 5 | Upstream: `arm_scmi`, spi-hid fixes; forks, issues and PRs | 2, author's OK | waiting |
| 6 | UCM boot sequence stops at `WSA_RX0 Digital Volume` (this card names it `WSA WSA_RX0 Digital Volume`), so RX1 and rx-macro init are skipped when there's no saved ALSA state: fix or document in `docs/audio.md` | | queued |

Tasks 2 and 3 can run in parallel once 1 is merged. Only one kernel build at a time.

## Proposed GitHub metadata (task 3, waiting for the author's OK)

- **Topics** (public repo counts, 2026-11-12): linux, linux-kernel (3.8k), arm64 (3.7k),
  snapdragon (242), snapdragon-x (13), x1e80100 (11), surface-laptop-7 (2), linux-surface (53),
  device-tree (481), face-unlock (50). Alternates: qualcomm (516), microsoft-surface (22),
  howdy (34), snapdragon-x-elite (24; not accurate for the X1P-64-100, but people search for it).
- **Description:** the current one is accurate. Optional tweak: "Linux on the Surface Laptop 7
  (Snapdragon X): IR camera face unlock, ~270 mW deep sleep, touchpad and cpufreq fixes, a
  reproducible 7.3 kernel".
- The CI badge renders for visitors only once the repo is public and `main` is pushed.
