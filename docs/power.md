# Battery life on the Surface Laptop 7

A battery survey of the tested machine (13.8", X1P-64-100, kernel `7.3.0-sl7` build `+sl7.3`)
on 2026-11-03. It found one real problem: CPU clusters 1 and 2 have no frequency scaling. This
page covers that problem, a kernel patch that should fix it, a workaround for kernels without the
patch (`sl7-power-mode`), and what was already fine.

> **Both untested.** Patch 0006 is not in any built kernel yet. `sl7-power-mode` has not been
> installed on the tested machine yet, so it has never run there as a service, and how much
> battery parking saves has not been measured. [Testing](#testing-on-the-hardware) lists what
> to check.

## Only cluster 0 has cpufreq

The X1E80100 die has three clusters of four cores. The X1P-64-100 has two of those cores
disabled (CPU7 and CPU11), so the online CPUs are 0-3 (cluster 0), 4-6 (cluster 1) and 8-10
(cluster 2); see [hardware.md](hardware.md). Measured on `+sl7.3`:

- `scmi-cpufreq` registers one policy, `policy0`, for CPUs 0-3: 13 frequencies from 710 MHz
  to 3.42 GHz, with schedutil. The device tree gives all three clusters SCMI perf domains
  (`scmi_dvfs 0`, `1` and `2`), and `scmi-perf-domain` initialises 3 domains, but `policy4`
  and `policy8` never appear. Nothing is logged: no `scmi-cpufreq` warning and no `->init()`
  failure.
- So clusters 1 and 2 have no cpufreq, no energy model and no DVFS. They stay at whatever
  performance level the boot firmware left them at, whatever the load.
- That level looks like a high one. In a timing test, a short burst of work started right
  after idle took 2.6-2.8 ms on clusters 1 and 2, every time. On cluster 0 it took
  4.6-12 ms, because schedutil first ramps cluster 0 up from about 1 GHz.

**The fix** is kernel patch 0006, `firmware: arm_scmi: perf: no turbo OPPs without a sustained
frequency` ([patches/kernel-7.3/](../patches/kernel-7.3/README.md#0006-and-the-missing-cpufreq-policies)).
The firmware reports no sustained frequency for clusters 1 and 2, so the SCMI perf driver
flags every one of their frequencies as turbo, cpufreq finds no frequency it may use, and it
drops the policy without a message. The patch stops flagging anything turbo when there is no
sustained frequency. **It is untested.**

**The workaround**, until a kernel with that fix is installed: on battery, take the cores
without a policy offline ("park" them). Offline cores are powered off, and the scheduler
runs everything on cluster 0, which does scale. This is only a workaround. On battery it
leaves 4 of the 10 cores, it does nothing for the clusters themselves, and it stops by itself
once the kernel gives them a policy. `sl7-power-mode` does this.

## sl7-power-mode

[`tools/power/sl7-power-mode`](../tools/power/sl7-power-mode) switches between two modes:

| Mode | When | CPUs | Hooks |
|---|---|---|---|
| `battery` | a system battery reports `Discharging` | Parks every online CPU without a cpufreq policy, except cpu0, and only if at least two CPUs do scale, so a broken cpufreq driver can't leave one core running | Run with `battery` |
| `ac` | otherwise, or while held by `full` | Brings back the CPUs it parked | Run with `ac` |

`Discharging` also covers a charger too weak to run the laptop. Batteries with scope `Device`
(Bluetooth mice, pens) are ignored. On a kernel where every CPU has a policy, it parks
nothing, so it can stay installed after the fix.

It runs when a power supply appears or changes (a udev rule, which also fires at boot), and
after every resume. The service waits 2 s for a plug or unplug to settle, then does nothing
unless the mode has changed. State lives in `/run/sl7-power-mode/`.

| Command | What it does |
|---|---|
| `sudo sl7-power-mode status` | Mode, battery, parked CPUs, CPUs without a policy, and each hook's status line. Changes nothing |
| `sudo sl7-power-mode full` | All cores now, held on battery until `auto` or a reboot (for a big build) |
| `sudo sl7-power-mode auto` | Drops the hold and applies the mode |
| `journalctl -t sl7-power-mode` | Every mode switch, and any hook that failed |

### Install

From a checkout of this repo:

```sh
sudo install -m 755 tools/power/sl7-power-mode /usr/local/sbin/
sudo install -m 644 systemd/sl7-power-mode.service /etc/systemd/system/
sudo install -m 644 config/udev/90-sl7-power-mode.rules /etc/udev/rules.d/
sudo systemctl daemon-reload
sudo systemctl enable sl7-power-mode.service   # the after-resume run
sudo udevadm control --reload
sudo sl7-power-mode apply
sudo sl7-power-mode status
```

### Hooks and the refresh rate

The original setup also ran the panel at 60 Hz on battery and 120 Hz on the charger, which
halves the redraw work of the compositor and of every Chromium or Electron window. That part
depends on the desktop, though, so it is a hook rather than part of the tool
([why](decisions/2026-11-12-power-refresh-rate-hook.md)).

A hook is an executable file in `/etc/sl7-power-mode.d/`. It gets one argument: `battery`,
`ac`, or `status` (print one line, change nothing). It should ignore anything else. It runs as
root from the service, and as the user when the desktop runs `sl7-power-mode` at login. A hook
that fails is logged and the rest still run.

[`tools/power/hooks/niri-refresh-rate`](../tools/power/hooks/niri-refresh-rate) is the hook for
[niri](https://github.com/YaLTeR/niri). It keeps the internal panel's resolution and picks the
rate nearest 60 Hz on battery and the highest rate on the charger: 2304x1536 at 60 or 120 Hz
on the 13.8". From the service it sets every running niri session, as that session's owner.
`SL7_PANEL` names a different output.

```sh
sudo install -D -m 755 tools/power/hooks/niri-refresh-rate /etc/sl7-power-mode.d/niri-refresh-rate
```

Then add this to `~/.config/niri/config.kdl`, so that a new session starts at the right rate
(run as a user, `sl7-power-mode` only runs the hooks):

```kdl
spawn-at-startup "/usr/local/sbin/sl7-power-mode"
```

Another compositor needs its own hook, doing the same through its own IPC.

### Remove

```sh
sudo sl7-power-mode full    # all cores and the charger refresh rate back first
sudo systemctl disable sl7-power-mode.service
sudo rm -f /usr/local/sbin/sl7-power-mode /etc/systemd/system/sl7-power-mode.service \
    /etc/udev/rules.d/90-sl7-power-mode.rules /etc/sl7-power-mode.d/niri-refresh-rate
sudo rm -rf /run/sl7-power-mode
sudo systemctl daemon-reload
sudo udevadm control --reload
```

Then delete the `spawn-at-startup` line, and `/etc/sl7-power-mode.d/` once no hooks are left.

## Testing on the hardware

On `+sl7.3`, without patch 0006, after installing the tool and the niri hook:

1. On the charger, `sudo sl7-power-mode status` shows `mode: ac`, nothing parked,
   `fixed-clock and online: [4 5 6 8 9 10]` and `niri eDP-1: 2304x1536@120.000`.
2. Unplug. Within a few seconds `journalctl -t sl7-power-mode` shows
   `battery: parked CPUs [4 5 6 8 9 10], online 0-3`, and the panel switches to 60 Hz.
   `dmesg` shows the six CPUs going offline with no errors.
3. Plug in again: `ac: parked CPUs [], online 0-6,8-10`, the CPUs come back without errors,
   and the panel is at 120 Hz.
4. Suspend and resume once on battery and once on the charger, and once unplug while it is
   asleep. Each time the mode should match the power state after resume.
5. On battery, `sudo sl7-power-mode full` brings every core and 120 Hz back, and
   `sudo sl7-power-mode auto` parks them again.
6. Log out and in again on battery: the new session starts at 60 Hz.
7. Drain: idle on battery for at least 30 minutes with parking (`auto`), then as long without
   it (`full`), at the same brightness, and compare battmgr's `energy_now` before and after
   each run. As in [deep-sleep.md](deep-sleep.md), runs shorter than 30 minutes say little,
   because the gauge moves in steps.

On a kernel with 0006, `status` should show `fixed-clock and online: []`, and unplugging
should park nothing. The patch has its own checks in
[patches/kernel-7.3/README.md](../patches/kernel-7.3/README.md#0006-and-the-missing-cpufreq-policies).

## Already fine

Checked on 2026-11-03; nothing to change:

- `deep` sleep at about 270 mW ([deep-sleep.md](deep-sleep.md)).
- Wi-Fi power save is on.
- ASPM L1 and L1.2 are on for the NVMe and Wi-Fi links.
- NVMe autonomous power state transitions (APST) are on, at 100 ms.
- The USB host controllers runtime-suspend when idle.
- Audio sinks suspend when idle.
- schedutil drives cluster 0.
- The NMI watchdog is off.

## Open

- **`clk_ignore_unused pd_ignore_unused`.** Both are in the
  [GRUB example](../config/grub/custom.cfg.example). They keep every clock and power domain
  that no driver has claimed switched on for the whole session. On 2026-11-03 every provider
  had reached `sync_state` (gcc and gpucc through `fw_devlink.sync_state=timeout`), so they
  may no longer be needed. Test a boot without them from a one-time GRUB entry before
  changing the default entry.
- **Tick settings.** [`config/kernel/config-7.3.0-sl7`](../config/kernel/config-7.3.0-sl7)
  keeps Ubuntu's `CONFIG_NO_HZ_FULL=y` and `CONFIG_HZ=1000`. Without `nohz_full=` on the
  command line, full dynticks behaves like `NO_HZ_IDLE` but adds some cost to every
  user/kernel transition. `CONFIG_NO_HZ_IDLE=y` with `CONFIG_HZ_250=y` is the usual laptop
  choice. Whether the change is measurable here is unknown; it needs a rebuild and a drain
  test.
- **How much parking saves.** See step 7 above.
