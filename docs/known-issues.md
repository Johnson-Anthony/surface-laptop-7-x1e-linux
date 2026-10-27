# Known issues

State on the tested machine (13.8", X1P-64-100, kernel `7.3.0-sl7`) as of October 2026.
"Open" means the cause isn't known yet.

## Open

| Area | Issue | Impact | Notes |
|---|---|---|---|
| IR camera | Stream start often stalls on 7.3: in one session, 11 of 43 capture starts delivered every frame; the rest stopped after 0-14 frames with nothing in the kernel log | Face unlock still approves in 1-2 s most of the time, but Howdy's reader retries only once, so some attempts probably fall back to the password | [ir-camera.md](ir-camera.md) |
| Touchscreen | Header errors ("bad sync"), `Body read failed: -110` and a 2 s GET_FEATURE timeout at boot or around lid close and suspend; it recovers | Brief loss of touch | [`tools/debug/touch-lid-test`](../tools/debug/touch-lid-test) is written to catch it but hasn't been run yet |
| Touchpad | The cold-boot fix (ItsLucas patch 0020, plus SPI HID fixes) isn't proven on 7.3 yet. The bug hit about 1 boot in 3 on 7.0; the first boots on 7.3 were all fine | Dead touchpad after some cold boots, if not fixed | Cold-boot several times, including with the lid closed right after shutdown. See [touchpad.md](touchpad.md) |
| Speakers | The kernel caps `PA Volume` at 6, but the UCM speaker sequence writes 12. If UCM stops at the rejected write, the right amplifier's settings are skipped | Possibly a quiet or silent right speaker | Not yet checked by ear; see [audio.md](audio.md) |

## Known, with a workaround

| Area | Issue | Workaround |
|---|---|---|
| Sleep | `s2idle` stays shallow: Linux runs at EL1 under Qualcomm's Gunyah hypervisor, and s2idle never reaches SoC deep sleep there | Use `mem_sleep_default=deep`, which reaches full deep sleep (~270 mW). See [deep-sleep.md](deep-sleep.md) |
| Boot | The global clock controller never reaches `sync_state` on its own: it waits for the GPU's GMU (`3d6a000.gmu`), which has no driver bound, so three power domains stay on | `fw_devlink.sync_state=timeout` releases them about 23 s after boot |
| Battery | The 7.0-era battery `BAT1` (Surface Aggregator) doesn't exist on 7.3 | Read `qcom-battmgr-bat` instead, e.g. in status bars |
| Kernel | ItsLucas's prebuilt kernel image refuses to install on SKU 2036 (the 13.8") | Build from the kit instead; see [kernel-7.3.md](kernel-7.3.md) |
| Face unlock | Howdy's `abort_if_lid_closed` does nothing on a device-tree boot and logs a harmless glob error on each attempt | Ignore, or turn the option off |

## Harmless messages

- `WARNING: drivers/gpu/drm/panel/panel-edp.c:829` with `Unknown panel SHP 0x1572, using
  conservative timings` at about 2 s. The 13.8" Sharp panel isn't in panel-edp's table, so the
  driver warns with a backtrace and taints the kernel (`W`). The display works. The proper fix
  is a table entry for this panel, which would make a small upstream patch.
- `psci: failed to boot CPU7 (-22)` and `CPU11`: the X1P-64-100 has 10 cores, and the X1E80100
  device tree describes 12. See [hardware.md](hardware.md).
- `Direct firmware load for qcom/gen70500_sqe.fw failed with error -2` (three times) before the
  root file system is mounted: the GPU firmware isn't in the initramfs. The GPU starts at about
  7 s once it can load it.
- `/sys/devices/soc0` has no SoC name: the kernel's ID table doesn't list `soc_id` 615 yet.
- `Timeout waiting for L2 entry` from the Wi-Fi PCIe link on every suspend.
- The IR sensor runs at about 29.6 fps, where the driver nominally expects 60. Reading its
  temperature control while it's idle logs a CCI timeout.
