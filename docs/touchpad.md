# Touchpad: dead after a cold boot

The Surface Laptop 7 touchpad sometimes stays dead after power-on. It enumerates normally,
but no input ever arrives. On the 7.0 kernel this machine first ran, 13 of 45 boots had a
dead touchpad.

The main cause is in the embedded controller (EC). The EC keeps the touchpad off until the
host enables Surface Aggregator posture (POS) events, and mainline Linux never does that on
this model. Three bugs in the SPI HID driver made the failure silent and recovery harder.

Status, 2026-11-12:

- Kernels with ItsLucas patch 0020, including the 7.3.0-sl7 kernel this repo builds,
  enable POS events themselves.
- On kernels without it, [`sl7-pos-events`](../tools/touchpad/sl7-pos-events) sends the same
  request from userspace at every boot.
- **Not proven yet.** On 7.3 (2026-10-25 to 2026-11-12) the machine booted 9 times: 3 after a
  reboot, 5 after a clean power-off, and 1 after a session that ended without a clean
  shutdown. The touchpad worked every time: in 8 boots `sl7-touchpad-diag` logged its IRQ
  count rising in the first 90 s, and in the ninth the compositor logged touchpad tap and hold
  events later on. No device reset was logged, and `sl7-touchpad-kick` never ran. Twice, the
  re-enumeration after a resume hit one SPI timeout and a 2 s GET_FEATURE timeout, like the
  touchscreen's ([known issues](known-issues.md)); the pad worked afterwards. At the old rate
  of about 1 failure in 3 boots, 6 good cold boots in a row would happen by chance about 9% of
  the time ((2/3)^6). The [test plan](#testing-cold-boots) below asks for 8, or far fewer with
  the lid-closed repro.
- On this machine every one of those boots enabled POS events twice, from 0020 and from an
  older copy of `sl7-pos-events` that doesn't skip 7.3 (see
  [When the touchpad is dead](#when-the-touchpad-is-dead)), so they test the boot-time enable,
  not 0020 on its own.

## The hardware

| | |
|---|---|
| Machine | Surface Laptop 7, 13.8" (model 2036, X1E80100), booting the `romulus15` device tree (see [hardware.md](hardware.md)) |
| Touchpad | HID over SPI (HIDSPI v3), 045E:0C77, on the GENI QSPI controller as `spi0.0` |
| IRQ | `msmgpio` 3, level-triggered |
| Power | `vreg_ts_5p0`, a fixed regulator enabled by gpio65; reset on gpio120 |
| Touchscreen | 045E:0C6E on `spi1.0` (same driver, separate device) |
| Userspace | [iptsd](https://github.com/linux-surface/iptsd) turns the raw HID reports into a virtual touchpad |

## The four causes

### 1. EC posture gate (main cause)

The Surface Aggregator Module (SAM) in the EC tracks the lid posture. After a lid change the
host has not seen (lid closed, then laptop), the EC keeps the touchpad off: no input and no
haptics, even in GRUB. It releases the pad once a host enables POS events and takes the
pending posture change. Windows' SurfaceHotPlug does this at every boot.

On Linux, the posture devices come from `surface_aggregator_registry`. Its Surface Laptop 7
node group (`ssam_node_group_sl7`) has no POS node, so nothing ever sends the enable. Mainline
7.0-rc4 still lacks it.

ItsLucas found this and published it in
[surface-laptop-7-ubuntu-kernel commit 004e91d](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel/commit/004e91d)
(patch 0020, 2026-10-23). The request is a SAM registry call (TC 0x01, CID 0x0b, "enable
event") with the payload `26 01 26 00 00`: target category 0x26 (POS), flags 0x01
(sequenced), request ID 0x0026, instance 0. ItsLucas reproduced the fault on a 15" model by
closing the lid right after starting a Windows shutdown: the touchpad was dead on the next
boot about 90% of the time. With the touchpad stuck, enabling POS events made it stream
again within 10 ms.

Checked on this machine (13.8", 7.0 kernel): the EC has the same single posture source
(ID 1, posture 3 = laptop), accepted the enable, and at once delivered a queued POS event
that had been waiting for a host. That confirms the EC side of
the mechanism here. A dead touchpad has not yet been revived this way on this machine,
because none has happened since.

### 2. Swallowed device-initiated resets

The touchpad sometimes resets itself and sends a RESET_RESP. If the driver does not
re-enumerate after that, iptsd never re-applies its mode, and the pad sits in its default mode
with no usable input. The ELLX driver (7.0) swallowed these resets, and
`device_initiated_reset_count` stayed 0. ItsLucas patch 0008 adds the recovery (module
parameter `reset_recovery`). A code review found that a reset arriving during a GET_FEATURE
still skipped it. That is fixed by
[0001](../patches/kernel-7.3/0001-HID-spi-hid-recover-when-a-reset-cuts-off-GET_FEATUR.patch)
in this repo.

### 3. Power sequencing

In the 7.0 device tree, the pinctrl "reset" state drove both gpio65 (the rail enable) and
gpio120 (reset). The driver held it for 300 ms, then released power and reset in the same
instant. ItsLucas 0004, 0005 and 0011 move gpio65 to the regulator only, keep reset asserted
through power-up, use longer off and startup times, and power-cycle once more if the pad stays
silent. Details are under [Rail and reset timing](#rail-and-reset-timing).

### 4. Unbalanced IRQ after an error storm

After 100 consecutive bus errors the driver masks its IRQ. In the older code the mask was
never undone, so the pad stayed silent until reboot. That shows up as `bus_error_count` > 0
with a flat IRQ count. ItsLucas 0021 balances the mask in stop/start. Two more cases are fixed
by this repo's
[0002](../patches/kernel-7.3/0002-HID-spi-hid-mask-the-IRQ-across-in-driver-reset-puls.patch)
and
[0003](../patches/kernel-7.3/0003-HID-spi-hid-end-the-IRQ-loop-after-the-error-handler.patch)
(see [Driver fixes](#driver-fixes)).

## The fix and the workaround

### Proper fix: ItsLucas 0020

[`0020-surface-aggregator-sl7-pos-events.patch`](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel/blob/2ce3083/patches/0020-surface-aggregator-sl7-pos-events.patch)
does two things:

1. It adds the existing `ssam_node_pos_tablet_switch` (`ssam:01:26:01:00:01`) to
   `ssam_node_group_sl7`. `surface_aggregator_tabletsw` then binds to it and enables POS
   events at probe, with the same bytes as above.
2. It teaches `surface_aggregator_tabletsw` that posture source 0x01 is a clamshell lid
   (2 = closed, 3 = laptop) and never tablet mode. Without this part the driver would report
   tablet mode, and libinput would turn off the keyboard and touchpad.

The registry uses the same node group for `microsoft,romulus13` and `microsoft,romulus15`, so
the patch covers a 13.8" machine booting either device tree.

With it, the device shows up as:

    $ readlink /sys/bus/surface_aggregator/devices/01:26:01:00:01/driver
    ../../../../bus/surface_aggregator/drivers/surface_aggregator_tablet_mode_switch
    $ cat /sys/bus/surface_aggregator/devices/01:26:01:00:01/state
    laptop

and the input device "Microsoft Surface POS Tablet Mode Switch" appears. `SW_TABLET_MODE`
stays 0.

### Workaround: `sl7-pos-events` (kernels without 0020)

[`tools/touchpad/sl7-pos-events`](../tools/touchpad/sl7-pos-events) sends the enable through
the stock `surface_aggregator_cdev` module (`/dev/surface/aggregator`), so no kernel rebuild
is needed. [`sl7-pos-events.service`](../systemd/sl7-pos-events.service) runs it once per
boot.

| Command | What it does |
|---|---|
| `status` | Read-only. Shows whether the kernel's POS node is bound, then the posture sources and their posture |
| `enable [--wait S]` | Registers for POS events, enables them, and prints events for S seconds (default 2). Does nothing if the kernel's POS driver is bound |
| `disable` | Sends the matching disable (CID 0x0c). Refused if the kernel's POS driver is bound, since it would take that driver's events away |
| `watch` | Prints POS events until Ctrl-C (events must already be enabled) |

`--force` sends `enable` or `disable` through the cdev even when the kernel driver is bound.
It is for testing only.

Things to know:

- The SAM controller reference-counts event enables. Only the first enable and the last
  disable reach the EC, and the cdev does not undo an enable when the program exits. So the
  events stay enabled after `enable` returns.
- At boot, `/dev/surface/aggregator` appears only after the SAM controller has probed. The
  script loads `surface_aggregator_cdev` and waits up to 30 s (`--timeout`) for the node. If
  that fails, the unit retries every 5 s, up to 4 more times. The first version gave up after
  5 s, a review finding.
- Before it decides the kernel has no POS node, it waits for the registry hub
  (`surface_aggregator_platform_hub`) to bind, because the hub adds all SAM client devices in
  its probe. So the boot service does not race the kernel driver.
- On kernels without 0020, every lid open or close logs one harmless line,
  `surface_serial_hub serial1-0: event: unhandled event (... tc: 0x26 ...)`. Nobody consumes
  the events once the script exits. The SAM serial hub has wakeup disabled, so these events
  can't wake the machine or abort suspend.

## Driver fixes

The 7.3.0-sl7 kernel's spi-hid driver is ItsLucas's (the kit's 0002, 0004, 0007 to 0015, and
0021) plus four patches from this work, in [`../patches/kernel-7.3/`](../patches/kernel-7.3/):

| Patch | What it fixes |
|---|---|
| [0001 recover when a reset cuts off GET_FEATURE](../patches/kernel-7.3/0001-HID-spi-hid-recover-when-a-reset-cuts-off-GET_FEATUR.patch) | A reset response was taken as the answer to a pending GET_FEATURE and returned as zero-filled success. The reset was not counted, the descriptors were not re-read, and iptsd never re-applied its mode. GET_FEATURE now runs the 0008 recovery. SET_FEATURE still accepts a reset as its answer, since a mode change may reset the device |
| [0002 mask the IRQ across in-driver reset pulses and power cycles](../patches/kernel-7.3/0002-HID-spi-hid-mask-the-IRQ-across-in-driver-reset-puls.patch) | The retry and error-handler reset pulses ran with the IRQ armed. On the 7.0 device tree they also cut the rail, so the IRQ thread read headers from an unpowered pad. And a storm mask was only dropped by `spi_hid_stop()`, so recovery after a storm ran with the line masked and timed out. Both helpers now mask the IRQ for the pulse and settle, and drop a storm mask once |
| [0003 end the IRQ loop after the error handler gives up](../patches/kernel-7.3/0003-HID-spi-hid-end-the-IRQ-loop-after-the-error-handler.patch) | When the error handler gave up, it powered the pad down but left the IRQ armed. An unpowered pad holding the level-triggered line kept the IRQ firing until the next suspend. These IRQs now count as errors, so the storm mask ends the loop |
| [0005 power up beside resume, not inside it](../patches/kernel-7.3/0005-HID-spi-hid-power-up-beside-resume-not-inside-it.patch) | The 2 s firmware settle ran inside the PM resume callback and held every system resume for about 3 s. Both pads now power up on `system_unbound_wq`, while enumeration still waits for thaw (`MODULE_VERSION sl7.20261026.1`) |

0001 to 0003 were written and build-tested against the ELLX 7.0 driver plus the ItsLucas
patches, then carried into 7.3, where they have run on every boot. The touchpad has logged no
device reset or bus error on 7.3 yet, so their recovery paths are untested on it. The
touchscreen has had bus errors around suspend, and on one boot device-initiated resets, and
recovered each time.

## Rail and reset timing

| | 7.0 (ELLX driver and DT) | 7.3.0-sl7 (ItsLucas driver and DT) |
|---|---|---|
| gpio65 (rail enable) | in the pinctrl "reset" and "active" states, so every reset pulse also cuts the rail | owned by the regulator only |
| gpio120 (reset) | same pinctrl states | pinctrl states |
| Regulator | `startup-delay-us = 100000` | `startup-delay-us = 500000`, `regulator-boot-on` |
| Probe | "reset" state 300 ms, then power and reset released together | rail off: reset asserted, 10 ms, regulator off, 500 ms |
| Power-up | (as above) | reset asserted, regulator on (500 ms startup delay), reset held 300 ms more, released, 2 s firmware settle, then the IRQ is armed |
| No reset response | nothing | after 5 s: "No reset response after power on; requesting descriptors" |
| Still silent | nothing | one more power cycle: "Unresponsive device; power cycling once" |

So on 7.3 the pad gets at least 510 ms with the rail off at probe, and reset is held through
the whole rail ramp. Power-up to armed IRQ takes about 2.8 s. The 7.0 device tree is left
alone: there the pinctrl reset state is the only thing that cuts power.

## Code review findings

A review of the ported driver and the tools (2026-10-25) found 10 issues: 6 confirmed (C)
and 4 plausible (P). The out-of-tree port and its helper scripts are not published here.
Apart from the three fixes that became patches 0001 to 0003, the port is ItsLucas's patches
applied to the 7.0 driver.

| | Finding | Status |
|---|---|---|
| C | RESET_RESP claimed as a pending request's reply, so the 0008 recovery never runs | Fixed by patch 0001 |
| C | `irq_storm` cleared only in `spi_hid_stop()`, so power cycle, error handler and reset work all run masked | Fixed by patch 0002 |
| P | Retry reset pulses cut the rail (7.0 DT) with the IRQ live, reading from an unpowered pad | Fixed by patch 0002. On the 7.3 DT the pulse no longer touches the rail |
| P | The give-up path powers off but leaves the level IRQ enabled: possible IRQ loop until suspend | Fixed by patch 0003 |
| C | Resume sleeps about 2.3 s per touch device inside the resume callback | Fixed by patch 0005 |
| C | The live-swap helper left both touch devices unbound if `insmod` failed | Fixed in the out-of-tree tools (falls back to `modprobe`). Moot on 7.3: the driver is in-tree |
| C | `sl7-touchpad-kick`'s rebind runs the stock driver's `remove()`, which can use freed memory | Applies to the ELLX 7.0 driver only. ItsLucas 0002 cancels the work first. The kick script still warns and asks before rebinding a driver without a module version |
| P | `sl7-pos-events.service` has no retry and gives up if the SAM cdev appears more than 5 s late | Fixed here: 30 s wait plus `Restart=on-failure`. Moot on 7.3 (0020) |
| C | The out-of-tree `make info` labels the on-disk module as "running" | Fixed in the out-of-tree Makefile. Moot on 7.3 |
| C | `sl7-touchpad-diag`'s IRQ count includes the hwirq column, so it reads 3 too high (deltas were right) | Fixed here: only the per-CPU columns are summed |

## Install

The tools and units are only needed on a kernel without ItsLucas 0020. The diagnostic logger
is useful on any kernel until cold boots are known to be good. From a checkout of this repo:

    sudo install -m 0755 tools/touchpad/sl7-pos-events tools/touchpad/sl7-touchpad-diag \
        tools/touchpad/sl7-touchpad-kick /usr/local/sbin/
    sudo install -m 0644 systemd/sl7-pos-events.service systemd/sl7-touchpad-diag.service \
        /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now sl7-pos-events.service   # kernels without 0020
    sudo systemctl enable sl7-touchpad-diag.service      # logs the next boots

Leaving `sl7-pos-events.service` enabled on a kernel with 0020 is harmless. It logs that the
kernel driver is bound and exits.

Remove:

    sudo systemctl disable --now sl7-pos-events.service sl7-touchpad-diag.service
    sudo rm /etc/systemd/system/sl7-pos-events.service /etc/systemd/system/sl7-touchpad-diag.service
    sudo rm /usr/local/sbin/sl7-pos-events /usr/local/sbin/sl7-touchpad-diag /usr/local/sbin/sl7-touchpad-kick
    sudo systemctl daemon-reload

POS events enabled through the cdev stay enabled until the next boot, or until
`sl7-pos-events disable`.

## Diagnostic tools

- [`sl7-touchpad-diag`](../tools/touchpad/sl7-touchpad-diag), run by
  [`sl7-touchpad-diag.service`](../systemd/sl7-touchpad-diag.service), logs the touchpad's IRQ
  count, `ready`, `bus_error_count`, `device_initiated_reset_count` and the iptsd state every
  5 s for the first 90 s of boot. It logs only changed lines, and it syncs the journal after
  each one, so a forced power-off keeps them. It finds the touchpad by its HID ID (045E:0C77)
  and its hidraw node through sysfs; `SL7_TOUCHPAD_SPI=spiX.Y` overrides the device.
- [`sl7-touchpad-kick`](../tools/touchpad/sl7-touchpad-kick) tries to revive a dead touchpad
  without a reboot. See below.
- [`touch-lid-test`](../tools/debug/touch-lid-test) checks whether closing the lid upsets the
  touchscreen. It is for an open 7.3 issue: the touchscreen (spi1.0) logs header errors and
  one 2 s timeout around suspend, then recovers. It keeps the machine awake for 90 s, records
  lid events and spi_hid kernel messages with wall-clock times, and writes them to
  `${XDG_STATE_HOME:-$HOME/.local/state}/sl7/` of the user who ran sudo. **It has not been run
  yet.**

## Testing cold boots

The failure happens at power-on, so reboots prove little. Change one thing at a time.

1. Enable `sl7-touchpad-diag.service`.
2. Shut down fully (`systemctl poweroff`), then power on. Vary how the previous session
   ended: a clean poweroff, a forced power-off (hold the power key), a battery run down.
3. The strongest test is ItsLucas's repro: close the lid right after starting a shutdown.
   ItsLucas saw a dead touchpad on about 90% of the next boots after doing this with a
   **Windows** shutdown. Whether a Linux shutdown triggers it the same way has not been
   tested. If you dual-boot, use Windows. If the fix did nothing, 3 good boots in a row after
   this repro would happen by chance only 0.1% of the time (0.1^3).
4. Without the repro, count ordinary cold boots. At the old rate of 1 in 3, 8 good boots in
   a row would happen by chance about 4% of the time ((2/3)^8).
5. After each boot, check:

        journalctl -b -t sl7-touchpad -o short-monotonic
        journalctl -b -u sl7-pos-events
        journalctl -b -k | grep -iE 'spi_hid|spi0\.0|tablet mode|unhandled event'

   A good boot shows the IRQ count rising once you touch the pad.

## When the touchpad is dead

1. Before power-cycling, run `sudo sl7-touchpad-kick` from a terminal (the keyboard still
   works). It tries three steps in order and stops when you say the cursor works:
   - `pos`: makes the EC see a fresh POS enable. On a kernel with 0020 it rebinds the
     tablet-mode-switch driver (its `remove()` disables the events, its probe enables them).
     Otherwise it sends a disable and an enable through the cdev. If this step helps, it is
     cause 1. If the boot service had already run, that means its timing matters.
   - `iptsd`: restarts the touchpad's iptsd. If this helps, it is cause 2.
   - `rebind`: unbinds and rebinds `spi_hid`, which power-cycles the pad and re-enumerates.
     This points at cause 2 or 3. On the ELLX 7.0 driver it asks first, because that driver's
     `remove()` can use freed memory if a reset is queued.

   Each step counts IRQs over 5 s of touching, then asks whether the cursor moves. The results
   go to the journal (`journalctl -t sl7-touchpad`).
2. Read the evidence with the commands from the last section:
   - IRQ count flat while touching: the pad isn't streaming (EC gate or power).
   - IRQ count rising but no cursor: mode or reset problem (cause 2).
   - `bus_error_count` above 0 and a flat IRQ count: the storm mask (cause 4).
   - On kernels without 0020, `sl7-pos-events` logging posture values `2/3` at boot: the EC
     was holding a lid-closed change, which is cause 1 caught in the act.

The kick's `pos` step on a 0020 kernel reaches the EC only if nothing else holds a reference
to the event. Copies of `sl7-pos-events` older than this repo also sent the enable on 7.3.
That is harmless, but it holds a second reference until the next boot.

## History (7.0 kernel)

Until 2026-10-26 this machine ran `7.0.0-rc4+` (package `7.0.0~rc4-g0e9944fa4cf2-44`, from
[murkurie/ELLX-Kernel](https://github.com/murkurie/ELLX-Kernel/tree/7.0.0-rc4-10-sl7), branch
`7.0.0-rc4-10-sl7`), with its out-of-tree `spi_hid` on `spi0.0` and iptsd 3.1.0.

What the journal showed (2026-10-25):

- 45 boots, 13 of them cut off within about 60 s because the touchpad was dead and the
  machine was power-cycled.
- The dead boots followed clean poweroffs as well as battery deaths, so the failure was
  intermittent at cold boot, not tied to one kind of shutdown.
- 12 of the 13 ended in a forced power-off (power key, then suspend, then hold the power key).
  Only one of the 45 boots ended in a real `reboot`.
- On a dead boot, kernel and iptsd logs matched a good boot line for line. The touchpad
  enumerated (GET_DD and GET_RD answered, input devices created, iptsd connected), then
  nothing came. The failure was silent.

Earlier evidence: an August 2026 sleep hook that stopped iptsd before suspend blamed a "deep
wedge" with dead haptics that only an EC reset cleared. That is the same symptom.

What was done on 7.0:

- `sl7-pos-events.service` (the first version of the workaround) and the diagnostic logger,
  installed 2026-10-25. The two 7.0 boots after that both had a working touchpad.
- ItsLucas's spi-hid patches ported to the ELLX driver as an out-of-tree module, plus the three
  fixes that became patches 0001 to 0003 here. The port built cleanly but was never loaded:
  the move to 7.3 came first.
- An older sleep hook unbound and rebound `spi_hid` after every resume, because the ELLX driver
  has no PM callbacks. That runs the same `remove()` path the review flagged. It never caused
  a known crash. On 7.3 the hook exits early, since the driver resumes the pads itself.

## Credits and references

- [ItsLucas/surface-laptop-7-ubuntu-kernel](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel)
  (at [2ce3083](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel/tree/2ce3083)):
  the EC gate diagnosis and patch 0020
  ([004e91d](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel/commit/004e91d)), the
  QSPI touchpad and touchscreen enablement, the spi-hid driver patches (0002, 0004, 0007 to
  0015, 0021) that the 7.3 driver is built from, and the rail change in 0005.
- [linux-surface issue #1590](https://github.com/linux-surface/linux-surface/issues/1590),
  "Surface Laptop 7th Edition Support": where the SL7 community work is tracked, including
  ItsLucas's lid-close repro.
- [murkurie/ELLX-Kernel](https://github.com/murkurie/ELLX-Kernel/tree/7.0.0-rc4-10-sl7): the
  7.0 kernel and `spi_hid` driver this machine ran first.
- The Surface Aggregator drivers (`surface_aggregator`, `surface_aggregator_cdev`,
  `surface_aggregator_registry`, `surface_aggregator_tabletsw`) are Maximilian Luz's upstream
  work; the workaround only uses the cdev's documented ioctls.
- [linux-surface/iptsd](https://github.com/linux-surface/iptsd): the touch daemon.
- Upstreaming of QSPI mode for the GENI SPI driver, which the touchpad needs, is discussed in
  ["spi: geni-qcom: any planned QSPI support?"](https://ratatoskr.run/linux-spi/2026/06/17091838/t)
  on linux-spi (June 2026).
