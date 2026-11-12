# The refresh-rate switch is a hook, not part of sl7-power-mode

2026-11-12

**Context.** The working copy of `sl7-power-mode` (2026-11-03) did two things on battery: park
the CPUs without a cpufreq policy, and set `eDP-1` to `2304x1536@60.000` through niri's IPC,
from root, by running itself as the owner of each niri socket. The output name and both mode
strings were fixed for the 13.8" panel.

**Decision.** The published tool only parks CPUs, then runs the executables in
`/etc/sl7-power-mode.d/` with `battery`, `ac` or `status`. The niri part is a separate,
optional hook, `tools/power/hooks/niri-refresh-rate`. It finds the internal panel (the first
`eDP-*` output, or `SL7_PANEL`), keeps its current resolution, and picks the highest rate on
the charger and the one nearest 60 Hz on battery, instead of using fixed mode strings.

**Why.**

- Parking works around a kernel bug that every Surface Laptop 7 on this kernel has, whatever
  the desktop. The refresh rate is a desktop setting: it depends on the compositor, on the
  panel (the 15" has a different resolution), and on taste.
- A hook keeps the root tool free of compositor code, and someone on sway, Hyprland or a
  desktop with its own power profiles can add or skip their own.
- Detecting the panel and its modes makes the niri hook work on both panel sizes and with a
  changed resolution, without editing the script.

**Cost.** One more file to install, and a small hook contract (`battery`, `ac`, `status`, run as
root from the service and as the user at login) to document in `docs/power.md`.
