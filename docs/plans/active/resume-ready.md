# Resume ready

Goal: the first version from [SPEC.md](../../SPEC.md): current, accurate, findable, public, and
at least one patch upstream.

## Tasks

| # | Task | Depends on | Status |
|---|---|---|---|
| 1 | Battery-life work into the repo: `sl7-power-mode`, its docs, and the `arm_scmi` patch in the 7.3 series | | queued |
| 2 | Build `+sl7.4` with the `arm_scmi` patch; the author installs and tests it; record the results | 1 | queued |
| 3 | README refresh for the new work; GitHub description, topics and CI badge prepared | 1 | queued |
| 4 | Make the repo public | 1-3, author's OK | waiting |
| 5 | Upstream: `arm_scmi`, spi-hid fixes; forks, issues and PRs | 2, author's OK | waiting |

Tasks 2 and 3 can run in parallel once 1 is merged. Only one kernel build at a time.
