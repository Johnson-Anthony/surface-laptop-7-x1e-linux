# What the battery-life work left out of the repo

2026-11-12

**Context.** The 2026-11-03 battery survey (`~/sl7/power/README.md` in the working folders)
mixed findings about the laptop and its kernel with changes and observations about one
installed system.

**Decision.** `docs/power.md` keeps what holds for any Surface Laptop 7 on this kernel, and
leaves out the rest:

- **Left out, specific to the author's installed system:** the Docker, containerd and
  ModemManager service changes, the other background services and scripts the survey found
  running there, and the backup name of the edited niri config.
- **Left out, personal settings or one unit's numbers:** backlight level, `noatime`, the
  EasyEffects detail, and this battery's health (its full charge against the design
  capacity).
- **Left out, already covered:** the `romulus15` versus `romulus13` device-tree question, which
  [hardware.md](../hardware.md) explains.
- **Kept:** that only cluster 0 has a cpufreq policy, the burst timings, the list of things
  already fine, and two open items that apply to anyone using this repo's GRUB example and
  kernel config (`clk_ignore_unused pd_ignore_unused`, the tick settings).

**Why.** The repo is for other owners of this laptop (SPEC: no settings or services specific to
the author's machine). Which services to run is each user's choice, and what else runs on the
author's system is private.
