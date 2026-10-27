# Deep sleep (CX collapse) on the Surface Laptop 7

The goal was to make suspend reach the SoC states that Windows Modern Standby reaches
(DRIPS): CX collapse (`cxsd` in `/sys/kernel/debug/qcom_stats`), AOSS sleep with XO shutdown
(`aosd`) and DDR self-refresh (`ddr`). Before this work all three counters stayed at 0 in
suspend, and the laptop drew 1.1 to 1.2 W asleep (2.1 to 2.3 %/h). Other X1E laptops that
reach these states draw 0.2 to 0.3 W.

Everything here was tested on one machine: a Surface Laptop 7 13.8" (model 2036), booting
the `romulus15` device tree (see [hardware.md](hardware.md) for why), UEFI 175.235.235. Linux
boots at EL1, under Qualcomm's Gunyah hypervisor.

## Result

On the 7.3.0-sl7 kernel, `mem_sleep=deep` (PSCI `SYSTEM_SUSPEND`) holds CX collapse, AOSS
sleep and DDR self-refresh for the whole suspend. s2idle still does nothing.

| Run | Mode | Length | Drain (battmgr) | aosd / cxsd / ddr |
|---|---|---|---|---|
| 5 | s2idle | 4 min | n/a | 0 / 0 / 0 |
| 6 | deep | 312 min | **263 mW, 0.50 %/h** | 63 entries each, 100 % of the time |
| 7 | deep | 114 min | **276 mW, 0.52 %/h** | 23 entries each, 100 % |
| 8 | deep | 310 min | 350 mW, 0.66 %/h | 62 entries each, 100 % |
| 9 | deep | 310 min | 241 mW, 0.47 %/h | 62 entries each, 100 % |
| 10 | deep | 162 min | 191 mW, 0.37 %/h | 33 entries each, 100 % |

Runs 1 to 4 were on the 7.0 kernel (see [History](#history-70-kernel)). Over the five long
`deep` runs (20.2 h in total) the average is 271 mW. Single runs spread from 191 to 350 mW.
Part of that is the battery gauge: battmgr's `energy_now` moves in steps, and short suspends
(under 10 min) show no change at all. Trust only runs of 30 min or more.

The raw log is [data/sleep-7.3.0-sl7.log](../data/sleep-7.3.0-sl7.log) and the per-suspend
report is [data/sleep-report-7.3.0-sl7.txt](../data/sleep-report-7.3.0-sl7.txt). To
reproduce the report:

```sh
tools/sleep/sleep-report --log data/sleep-7.3.0-sl7.log
```

Also checked on this machine after these suspends:

- Opening the lid woke it from CX collapse in run 6. The wake IRQ was 132, `msmgpio 2`
  (`gpio_keys`, the lid switch), read from `/sys/power/pm_wakeup_irq`. A TLMM GPIO can only
  wake the SoC from this state through the PDC, which needs the PDC GPIO wake series that 7.3
  carries.
- Wi-Fi resumes: the firmware restarts and reconnects.
- Both SPI HID devices (touchpad and touchscreen) come back.
- The ADSP slept and woke about once a minute during suspend (364 times in run 6), with
  `qcom_adsp_pwr_lmts` loaded (see below).

Not tested:

- `deep` without `qcom_adsp_pwr_lmts`, without `fw_devlink.sync_state=timeout`, or with the
  upstream 9000 us `domain_ss3` min-residency. Every 7.3 run had all three as described below.
- Waking from CX collapse with the keyboard or the power key. Only the lid wake was recorded.
- EL2 (see [History](#el2-research-not-needed)), hibernation, and long-term stability beyond
  these two days.

## Why `deep` and not s2idle

In s2idle, Linux does select the system idle state: the genpd usage count of `domain_ss3`
read 234 after run 5. The firmware does nothing with it, and aosd/cxsd/ddr stay at 0. This
was the same on 7.0, with every fix tried there. With `deep`, Linux calls PSCI
`SYSTEM_SUSPEND`, and the firmware collapses the SoC. So on this laptop at EL1, deep sleep
means `mem_sleep=deep`.

`deep` still goes through genpd on 7.3. cpuidle-psci's syscore hook
(`psci_idle_syscore_suspend()`) calls `dev_pm_genpd_suspend()` for the CPUs, so genpd powers
off `power-domain-system`. That runs the RPMh RSC's genpd notifier (`rpmh_rsc_pd_callback()`),
which flushes the RPMh sleep votes. In `deep`, the system domain's `idle_states` usage (and
its `S2idle` column, despite the name) goes up by one per suspend: in a boot with a single
`deep` suspend, both read 1.

## Setup on 7.3

1. **Kernel.** 7.3 or later. 7.3 has `domain_ss3` in `hamoa.dtsi` (upstream commit
   [95f827ceb21e](https://github.com/torvalds/linux/commit/95f827ceb21e2885f40eec5d93a340abbcc22d13)),
   the PDC GPIO wake series, and the PCIe suspend rework from 7.2. This machine runs
   7.3.0-sl7: Ubuntu 7.3.0-9.9, the
   [ItsLucas SL7 kernel kit](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel) and
   [this repo's patches](../patches/kernel-7.3/). See [kernel-7.3.md](kernel-7.3.md).
   ItsLucas also publishes prebuilt images, but per its README the image package refuses to
   install on the 13.8" SKU (`..._2036`), so on a 13.8" you build from the kit.

2. **Boot flags:** `mem_sleep_default=deep fw_devlink.sync_state=timeout`. To try `deep`
   without editing GRUB, `echo deep | sudo tee /sys/power/mem_sleep` switches it until the
   next boot. Runs 6 to 10 were done that way, from a boot with `mem_sleep_default=s2idle`.

   `fw_devlink.sync_state=timeout` is still needed on 7.3. The GCC clock controller
   (`100000.clock-controller`) waits for its consumer `3d6a000.gmu`, and no driver ever binds
   to that node: the Adreno driver uses it through `of_find_device_by_node()`. So gcc and
   gpucc only reach `sync_state` when the flag forces it, about 23 s after boot
   (`Timed out. Forcing sync_state()`). Until then every GDSC that the firmware left on stays
   on, which on 7.0 kept CX up (see [History](#why-it-was-shallow)). Booting 7.3 without the
   flag was not tested.

3. **Device tree.** [`tools/dtb/build-dtbs`](../tools/dtb/build-dtbs) builds the boot DTB:
   the packaged `romulus15` DTB plus the IR camera overlays, plus
   [`dts/romulus15-deep-sleep.dtso`](../dts/romulus15-deep-sleep.dtso) when the base's
   `domain_ss3` is not at 10 s (see the next section). For 7.3.0-sl7 its output is
   byte-identical to the DTB this machine boots.

4. **ADSP standby message:** `qcom_adsp_pwr_lmts`, from
   [justririll/x1e-sleep](https://github.com/justririll/x1e-sleep) (`modules/adsp-pwr-lmts`,
   commit 4e84b60, used unmodified; not included here). Build it against your kernel tree
   (`make -C <tree> M=$PWD modules`), sign it if your kernel enforces module signatures, and
   install it under `/lib/modules/<kver>/updates/`, then run `depmod`. It loads by itself: it
   binds to the ADSP's `APPS_ADSP_PWR_LMTS_GLINK_PORT` rpmsg channel.

   What it does: Windows' power engine plug-in sends the ADSP a `MODERN_STANDBY_STATE`
   message on that channel when it enters Modern Standby, and the ADSP then stops its
   power-limits timer. The module sends the same message from its suspend and resume
   callbacks. On 7.0 in `deep`, the ADSP went to sleep 10557 times in 104 s without it
   (about 100 wakeups a second, run 3), and 126 times in 55 min with it (run 4). It was loaded
   in every 7.3 run, so whether CX collapse depends on it was not tested.

5. **qcrypto.** Leave it bound on 7.3. With ItsLucas's patches 0026/0027, QCE binds without
   registering algorithms and drops its interconnect vote in runtime PM, and the interconnect
   providers reach `sync_state` only once it has probed. (On 7.0 it held a constant
   393600 kB/s vote and had to be blacklisted.)

6. **Measuring.** Install the sleep hook, suspend, then read the counters:

   ```sh
   sudo install -m 755 systemd/sl7-sleep-stats /usr/lib/systemd/system-sleep/
   # suspend for 30 min or more, wake it, then:
   sudo tools/sleep/check-sleep          # setup, genpd, qcom_stats, last 5 suspends
   tools/sleep/sleep-report 0            # every suspend in /var/log/sl7-sleep.log
   ```

   [`check-sleep`](../tools/sleep/check-sleep) shows the sleep mode, the sync state of the
   clock controllers, the ADSP module, the DT's domain idle states (PSCI parameter and
   min-residency) with their genpd usage, any GDSC left on with no device, the qcom_stats
   counters and the last wake IRQ. [`sleep-report`](../tools/sleep/sleep-report) turns the
   [hook](../systemd/sl7-sleep-stats)'s log into drain and residency per suspend.
   [`sl7-status`](../tools/status/sl7-status) gives a one-page summary of everything in this
   repo.

To boot a different kernel or GRUB entry once, use `grub-reboot '<entry title>'`. If the GRUB
menu that the firmware loads lives on another partition (on this machine it is the Ubuntu
install's), mount that partition and pass `--boot-directory=<mount>/boot`.
`sudo tools/status/sl7-status --grub` finds that partition and shows the default and
one-shot entries.

## The `domain_ss3` overlay and the 10 s min-residency

[`dts/romulus15-deep-sleep.dtso`](../dts/romulus15-deep-sleep.dtso) sets the system idle
state to upstream's values (PSCI parameter 0x0200c354, 2500 us entry and exit latency), except
that min-residency is 10 s instead of 9000 us. The 7.3.0-sl7 kernel carries the same change as
a DT patch ([0004](../patches/kernel-7.3/0004-arm64-dts-qcom-x1e80100-romulus-keep-runtime-cpuidle.patch)).

Why 10 s: genpd's CPU governor picks the system state for suspend by latency only
(`cpu_system_power_down_ok()`), so suspend still uses it. Runtime cpuidle also needs the
predicted idle time to cover the residency (`cpu_power_down_ok()`), so with 10 s it never
enters the state while the laptop is in use. Other X1E laptops hung when the system state was
entered at runtime. Checked here: after about an hour of use with one `deep` suspend, the
system domain's usage count was 1, so runtime cpuidle had not entered it.

What was checked with `fdtget` and `fdtoverlay` (dtc 1.7.2):

- The installed 7.3.0-sl7 DTB already has `domain-sleep-0` at 10 s. Applying the overlay
  changes nothing (identical decompiled source).
- On a base with the upstream 9000 us (a copy of the packaged DTB with the value set back by
  `fdtput`, standing in for ItsLucas's prebuilt kernel), the overlay changes only
  `min-residency-us`. The node keeps its phandle, and the result matches this machine's DTB.
- It also applies to the `romulus13` DTB, and to a 7.0 base without `domain-sleep-0`, where it
  adds the node and links it from `power-domain-system`.

So for someone on ItsLucas's prebuilt kernel, the overlay keeps runtime cpuidle out of the
system state. By the code above, it does not change what suspend does. This laptop has never
run with 9000 us, so whether the runtime hang affects it is unknown.

## Known noise on 7.3

- `qcom-pcie 1c08000.pcie: Timeout waiting for L2 entry! LTSSM: 0x11` on every suspend. This is
  the Wi-Fi link. ItsLucas sees it too. It does not stop CX collapse or the Wi-Fi resume here.
- The touchscreen (`spi1.0`) logs header and sync errors around suspend, and sometimes one
  2 s response timeout, then recovers.
- Resume used to wait about 3 s for the touchpad firmware. Patch
  [0005](../patches/kernel-7.3/0005-HID-spi-hid-power-up-beside-resume-not-inside-it.patch)
  moves that power-up beside resume.
- 7.3.0-sl7 registers no Surface Aggregator battery (`BAT1`), only `qcom-battmgr-bat`, so the
  hook and `sleep-report` use battmgr. On 7.0, where both exist, they disagreed (0.72 W by BAT1
  and 1.14 W by battmgr over the same 55 min).

## History (7.0 kernel)

The first two rounds ran on 7.0.0-rc4 from
[murkurie/ELLX-Kernel](https://github.com/murkurie/ELLX-Kernel) (branch `7.0.0-rc4-10-sl7`,
package `7.0.0~rc4-g0e9944fa4cf2-44`). None of the fixes tried there got past APSS collapse,
which is what led to the 7.3 kernel.

### Why it was shallow

1. **No system-level idle state in the DT.** `power-domain-system` had only a default state
   with no PSCI parameter, so the firmware was never asked for system-level sleep. The domain
   was entered 1092 times in the first 72 min of uptime, but `apss` stayed at 0. Upstream added
   `domain_ss3` in v7.3 (95f827ceb21e).
2. **GDSCs stuck on, so CX stays up.** `3d6a000.gmu` has no driver, so gcc never reaches
   `sync_state`. Every GDSC the firmware left on keeps genpd's `stay_on`. Three of them have no
   device at all (`gcc_usb_2_phy`, `gcc_usb30_tert`, `gcc_ufs_phy`), so suspend never powers
   them off. They keep CX on, and rpmhpd then votes at least its enable level in the RPMh sleep
   set. Writing 1 to gcc's `state_synced` in sysfs turned them off at runtime with no effect on
   USB or the network; `fw_devlink.sync_state=timeout` does the same at boot.
3. **`deep` was no shortcut on 7.0.** The analysis then found that RPMh sleep votes were only
   flushed from the system power-domain notifier, which s2idle triggered and `SYSTEM_SUSPEND`
   did not. (On 7.3, `deep` does reach that notifier; see above.)

### Round 1: overlay and sync_state

The overlay in this repo was written then, for the 7.0 IR camera DTB, together with a one-shot
GRUB entry that booted it with `fw_devlink.sync_state=timeout`. Without the PDC series, only
interrupts the PDC routes directly (the power key, through SPMI) could have woken the SoC from
CX collapse; the lid and keyboard are TLMM GPIOs.

### Round 2: tests on 7.0

All with the overlay and `fw_devlink.sync_state=timeout`:

| Run | Setup | apss | aosd / cxsd / ddr | Notes |
|---|---|---|---|---|
| 1 | s2idle | 0 | 0 | Linux used `domain_ss3` (genpd usage 1); the firmware did nothing |
| 2 | s2idle, qcrypto unloaded, Bluetooth blocked | 0 | 0 | same |
| 3 | `deep` | 1 entry, 98 % | 0 | first APSS collapse; plugging in the charger woke it |
| 4 | `deep`, qcrypto blacklisted, `qcom_adsp_pwr_lmts`, patched LPASS macros, 55 min | 1 entry, 100 % | 0 | ADSP sleeps fell from about 100/s to 126 in 55 min; 0.72 W by BAT1, 1.14 W by battmgr; the lid woke it |

The LPASS macro patch released the macro and dcodec q6prm votes in runtime suspend. 7.3's
macros use `pm_clk`, so it was not carried forward. qcrypto (QCE) held a constant 393600 kB/s
interconnect vote tagged ALWAYS. Do not unload `soundwire_qcom` at runtime to reload audio
modules: on 7.0 that oopsed the kernel (stale IRQ domain) and hung shutdown.

Why it still stopped at APSS: in `deep`, 7.0's `qcom_pcie_suspend_noirq()` kept the CPU-PCIe
interconnect vote and the OPP vote and never took the link down, so the NVMe (pcie6a) and
Wi-Fi (pcie4) controllers held bus votes in the RPMh sleep set. 7.2 reworked this
(`dw_pcie_suspend_noirq()` takes the link to L2, then drops every vote). pcie-qcom is built in,
so this needed a newer kernel, as did the PDC wake series and the a6xx stale-vote fix
(d9108bfdb746). The geni UART vote fix (d0cd9c8d0fd5) was the other suspect at the time.

### Round 3: 7.3.0-sl7

Runs 5 to 10 above. The DT state and the sync_state flag were the same as in round 2, the
ADSP module was loaded as in run 4, and qcrypto was bound (see [Setup](#setup-on-73)). s2idle
stayed shallow, and `deep` now reached CX collapse.

### EL2 research (not needed)

A Surface Pro 11 reached CX collapse only at EL2
([ramonjesusmiranda-debug/sp11-el2](https://github.com/ramonjesusmiranda-debug/sp11-el2)), so
booting Linux at EL2 was researched before 7.3 made it unnecessary. It looks doable: one
Surface Laptop 7 report exists
([Ubuntu bug 2084951](https://bugs.launchpad.net/ubuntu/+bug/2084951), comments 107 and 108).
It needs a patched [slbounce](https://github.com/TravMurav/slbounce) (skip the
`clear_dcache_range` sweep), an EFI shell script or systemd-boot to load it (GRUB can't load
EFI drivers), an `-el2` DTB, `id_aa64mmfr0.ecv=1`, and extra patches for the DSPs (the attach
series, qebspil or x1e-dsp) and for efivars and the RTC (SHM bridge). At EL2 `deep` returns at
once, so sleep would use s2idle there. None of this was tried.

## Undo

```sh
sudo rm /usr/lib/systemd/system-sleep/sl7-sleep-stats      # stop logging
sudo find /lib/modules/$(uname -r)/updates -name 'qcom_adsp_pwr_lmts.ko*' -delete
sudo depmod -a
# Boot flags: remove mem_sleep_default=deep (and fw_devlink.sync_state=timeout) from the entry.
# DTB, only on a 9000 us base: sudo tools/dtb/build-dtbs --install --no-deep-sleep
# (on 7.3.0-sl7 the 10 s value is in the kernel's own DTB, patch 0004).
```

## Sources and credits

- `domain_ss3`: upstream commit
  [95f827ceb21e](https://github.com/torvalds/linux/commit/95f827ceb21e2885f40eec5d93a340abbcc22d13),
  posted as [patch 1 of the Hamoa PDC series v5](https://lore.kernel.org/all/20260715-hamoa_pdc_v3-v5-1-00440cfaf711%40oss.qualcomm.com/).
- PDC GPIO wake: Mukesh Ojha's and Maulik Shah's qcom-pdc series
  ([v4](https://lore.kernel.org/all/20260707-hamoa_pdc_v3-v4-0-dfd1f4a3ae89%40oss.qualcomm.com/)),
  with pinctrl f790ea0b699d and 77fbc756d9cb.
- [justririll/x1e-sleep](https://github.com/justririll/x1e-sleep): `qcom_adsp_pwr_lmts`, and
  working deep-sleep reports from another X1E laptop.
- [ItsLucas/surface-laptop-7-ubuntu-kernel](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel):
  the SL7 kernel kit this machine's 7.3 kernel is built from.
- [murkurie/ELLX-Kernel](https://github.com/murkurie/ELLX-Kernel): the 7.0 kernel of rounds 1
  and 2.
- [ramonjesusmiranda-debug/sp11-el2](https://github.com/ramonjesusmiranda-debug/sp11-el2) and
  [slbounce](https://github.com/TravMurav/slbounce): the EL2 route.
