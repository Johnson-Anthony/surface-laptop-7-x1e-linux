# Kernel 7.3.0-sl7

A 7.3 kernel for the Surface Laptop 7, built from Ubuntu's 7.3.0-9.9 source, the
[ItsLucas Surface Laptop 7 kit](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel)
and eight patches of our own. It has been the default kernel on the tested machine since
2026-10-26, built with seven of them: the eighth, an `arm_scmi` cpufreq fix, is untested. The tested machine is a 13.8" Surface Laptop 7 (SKU 2036) with a Snapdragon X Plus
X1P-64-100, which is the X1E80100 ("Hamoa") die with 10 of its 12 cores enabled. It boots the
`romulus15` (15") device tree; [hardware.md](hardware.md) explains why.

- Patches and their test status: [patches/kernel-7.3/README.md](../patches/kernel-7.3/README.md)
- Exact base and step-by-step build: [patches/kernel-7.3/BASE.md](../patches/kernel-7.3/BASE.md)
- Tools: [`tools/kernel/`](../tools/kernel/) (`apply-series`, `make-config`, `first-boot-check`)
- Config: [`config/kernel/`](../config/kernel/); GRUB entries: [`config/grub/custom.cfg.example`](../config/grub/custom.cfg.example)
- Firmware: [firmware.md](firmware.md)

## Why 7.3

The machine first ran a 7.0.0-rc4 build of
[ELLX-Kernel](https://github.com/ProgrammerIn-wonderland/ELLX-Kernel) (commit `0e9944fa4cf2`).
Its deep sleep stopped at CPU subsystem (APSS) collapse: in `deep`, 7.0's `pcie-qcom` keeps its
CPU-PCIe interconnect and OPP votes and never takes the NVMe and Wi-Fi links to L2, so the SoC
cannot collapse CX or put DDR in self-refresh. 7.2 reworked that suspend path. 7.3 adds the rest of what deep sleep
needs on this machine:

- PDC GPIO wake, so the lid wakes the laptop from CX collapse;
- the X1E system idle state `domain_ss3`
  ([95f827ceb21e](https://git.kernel.org/torvalds/c/95f827ceb21e));
- the a6xx GPU stale RPMh vote fix
  ([d9108bfdb746](https://git.kernel.org/torvalds/c/d9108bfdb746));
- `pm_clk` in the LPASS audio macros, and runtime PM for the crypto engine (QCE).

With `mem_sleep_default=deep` the laptop now reaches CX collapse, AOSS sleep and DDR
self-refresh, at 263-276 mW (0.50-0.52 % battery per hour) in 2-5 hour tests. s2idle still
stays shallow, as on 7.0. See [deep-sleep.md](deep-sleep.md).

## What is in it

1. Ubuntu `linux-source-7.3.0` 7.3.0-9.9: upstream 7.3-rc6 plus Ubuntu's tree, which has the
   X1E camera (CAMSS, CCI) nodes that mainline 7.3 lacks.
2. The ItsLucas kit at `2ce3083`, all 26 patches, applied with the kit CI's rules by
   [`tools/kernel/apply-series`](../tools/kernel/apply-series). It adds the QSPI touchpad and
   SPI touchscreen (spi-hid), panel power and pin bias, DisplayPort audio, the Iris video codec
   and the front camera in the device tree, Surface Aggregator posture (POS) events, the PS883x
   dock fixes, and a QCE driver that binds without registering algorithms. Provenance of each
   patch: the kit's [PROVENANCE.md](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel/blob/2ce3083fa76855225465f809760dc7185c74a80c/PROVENANCE.md).
3. Our patches: three spi-hid recovery fixes, `domain_ss3` at 10 s, spi-hid power-up beside
   resume, cpufreq for CPU clusters 1 and 2 (`arm_scmi`, untested and not in the installed
   build yet), the release name and module signing
   ([details](../patches/kernel-7.3/README.md)).

### Kit patches on this machine

The kit was written and tested on a 15" Surface Laptop 7. Several of its patches are marked
"not yet hardware-validated" or "compile-tested only" in its provenance notes. This is what
the 13.8" here actually exercised on 7.3 (2026-10-26 and 27):

| Kit patch | What | Here |
|---|---|---|
| 0001 | ath12k: skip the firmware rfkill setup on romulus15 | Wi-Fi comes up and connects, with the 7.3 firmware from [firmware.md](firmware.md) |
| 0002, 0004, 0005 | QSPI touchpad, spi-hid power sequencing, touch power GPIOs | Touchpad works on every boot and after deep suspend |
| 0003 | SPI touchscreen (GTCH, `045E:0C6E` on `spi1.0`) | Works. The kit says the 13.8" has a different, I2C touchscreen; this 13.8" has the SPI one |
| 0007-0015, 0021 | spi-hid transport fixes (kit: not hardware-validated) | Normal paths run daily. Their recovery paths have not shown up in the logs. A review found three bugs in them, fixed by our 0001-0003 |
| 0016 | log `GENI_IF_DISABLE_RO` on QSPI | Logged for both QSPI controllers (`FIFO_IF_DISABLE=0`) |
| 0017 | QSPI pin pull-downs, touchscreen drive strength | In the running DT; no A/B comparison |
| 0018 | DisplayPort audio | The sound card registers its DP0 and DP1 jacks. Audio over DisplayPort not tested |
| 0019 | Iris video codec | Binds, loads its firmware, creates the decoder and encoder video nodes. No decode test |
| 0020 | Surface Aggregator POS events | The POS tablet-mode switch input appears and tablet mode stays off. The touchpad fault it targets was not reproduced for a test |
| 0022 | front camera (OV02C10) | Probes, and libcamera lists it as "Internal front camera". Camera checks are in [ir-camera.md](ir-camera.md) |
| 0023-0025 | PS883x retimer dock fixes | Not tested: no dock |
| 0026, 0027 | QCE binds without registering algorithms | `qcrypto` binds, and every interconnect provider reaches `sync_state` |

Outside the kit, on the same kernel:

- IR camera (out-of-tree driver): captures 30 frames at 29.6 fps, though stream starts
  sometimes stall ([ir-camera.md](ir-camera.md)). Howdy approves face logins in daily use
  ([face-unlock.md](face-unlock.md)).
- Audio: the sound card shows speaker and headphone sinks ([audio.md](audio.md)).
- Bluetooth loads its firmware and powers on; the keyboard works through the Surface
  Aggregator.
- Every `state_synced` reads 1. For the GCC and GPUCC clock controllers that only happens
  through `fw_devlink.sync_state=timeout`, about 23 s after boot, because the GPU's GMU has
  no driver yet.

The open problems are listed in [known-issues.md](known-issues.md).

## Config

[`config/kernel/config-7.3.0-sl7`](../config/kernel/config-7.3.0-sl7) is the config of the
tested kernel, unchanged. `tools/kernel/make-config TREE` copies it into a patched tree and runs
`make olddefconfig`. That changes only lines that kconfig fills in from the toolchain. On the
build machine it changed nothing on 2026-10-27, when it had rustc 1.85.1. With rustc 1.99.1
(2026-11-12) it rewrites the three `CONFIG_RUSTC_*VERSION` lines and adds five
`CONFIG_RUSTC_HAS_*` lines. Rust stays off, so nothing builds differently: the `+sl7.4` rebuild
with those lines recompiled only `perf.c`, the file patch 0006 changes, and `init/version.c`,
which every build does.

How it was made: the 7.0 kernel's config, plus the 33 Qualcomm, Surface, audio and camera
options that Ubuntu's 7.3 config enables and the 7.0 config lacked, plus the options in
[`config/kernel/sl7.fragment`](../config/kernel/sl7.fragment). Two parts of the fragment are
workarounds, not hardware needs:

- `SYSTEM_TRUSTED_KEYS` and `SYSTEM_REVOCATION_KEYS` are empty, because Ubuntu's config points
  them at `debian/canonical-*.pem` files that `linux-source` does not ship.
- Rust, BTF and debug info are off. When the config was made, the build host (Debian 13) had
  rustc 1.85, too old for this kernel's Rust support, and no `pahole`, so BTF cannot be generated. No debug info also keeps
  the build smaller and faster. If your toolchain has a newer rustc and `pahole`, you can drop
  that block of the fragment.

To start from Ubuntu's own config instead (`/usr/lib/linux/7.3.0-9-generic/config` in the
`linux-buildinfo-7.3.0-9-generic` package), run
`tools/kernel/make-config --base config-7.3.0-9-generic TREE`. It merges the fragment with the
kernel's `scripts/kconfig/merge_config.sh` and reports any fragment value that did not survive
(none did, in a test on 2026-10-27). That config was not built or booted. It differs from the
shipped one in about 1100 options. Among them, 118 that the shipped config builds in are
modules in Ubuntu's, for example the X1E GCC clock controller, the X1E interconnect driver and
the QMP PCIe PHY, so they would have to load from the initramfs. Use the shipped config unless
you have a reason not to.

## Building

The full steps, with checksums and tree hashes to check against, are in
[BASE.md](../patches/kernel-7.3/BASE.md). The build itself:

```sh
nice make -j"$(nproc)" LOCALVERSION= KDEB_PKGVERSION=7.3.0-9.9+sl7.3 bindeb-pkg
```

`LOCALVERSION=` (empty) keeps kbuild from appending `+`; the release is `7.3.0-sl7`. A native
build on the laptop takes about 1-2 hours. Keep the build tree: its `certs/signing_key.pem` signs
the out-of-tree modules below. Never publish that key.

## Outside the kernel package

| What | Installed at | Notes |
|---|---|---|
| IR camera driver `vd55g0.ko` | `/lib/modules/<kver>/updates/vd55g0.ko` | ST's driver with our Surface power-order patch; see [ir-camera.md](ir-camera.md) |
| ADSP standby message `qcom_adsp_pwr_lmts.ko` | `/lib/modules/<kver>/updates/sl7-deep-sleep/` | From [justririll/x1e-sleep](https://github.com/justririll/x1e-sleep) (`modules/adsp-pwr-lmts` at `4e84b60`, unmodified). Sends the ADSP the Modern Standby message Windows sends, so it wakes about twice a second in sleep instead of about 100 times; see [deep-sleep.md](deep-sleep.md) |
| Wi-Fi firmware for 7.3 | `/lib/firmware/updates/<kver>/ath12k/WCN7850/hw2.0/` | linux-firmware `WLAN.HMT.1.1.c7-00108`; the older firmware times out on 7.3. See [firmware.md](firmware.md) |
| Iris firmware `qcvss8380.mbn` | `/lib/firmware/updates/qcom/x1e80100/microsoft/Romulus/` | From Windows; see [firmware.md](firmware.md) |
| DTBs | `/boot/dtbs/<kver>/qcom/`, `/boot/dtb-<kver>` | `sudo tools/dtb/build-dtbs --install <kver>`: the packaged `romulus15.dtb` plus the IR camera overlays, and the packaged DTB itself for the rescue entry |
| qcrypto rule | `/etc/modprobe.d/sl7-deep-sleep.conf` | [`config/modprobe/sl7-deep-sleep.conf`](../config/modprobe/sl7-deep-sleep.conf): skips qcrypto on the old 7.0 kernel only. 7.3 needs it bound |
| GRUB entries | the booting GRUB's `custom.cfg` | [`config/grub/custom.cfg.example`](../config/grub/custom.cfg.example), with a comment for every kernel parameter |

Not needed on 7.3: the LPASS macro vote patch used on 7.0 (7.3's macros use `pm_clk`), resume
hooks that rebind spi-hid or restart iptsd (7.3's spi-hid resumes the pads itself), and
`sl7-pos-events.service` (kit patch 0020 does the same in the kernel; the service is harmless,
see [touchpad.md](touchpad.md)).

### Building the out-of-tree modules

Build against the kernel's build tree and sign with its key. The kernel does not enforce
signatures, so an unsigned module still loads, but it taints the kernel (`E`).

```sh
K=/path/to/linux-7.3.0-sl7            # the tree the kernel was built in
KVER=7.3.0-sl7
make -C "$K" M="$PWD" LOCALVERSION= modules
"$K/scripts/sign-file" sha512 "$K/certs/signing_key.pem" "$K/certs/signing_key.x509" vd55g0.ko
sudo install -D -m 644 vd55g0.ko "/lib/modules/$KVER/updates/vd55g0.ko"
sudo depmod -a "$KVER"
modinfo -F signer "/lib/modules/$KVER/updates/vd55g0.ko"   # Build time autogenerated kernel key
```

The same for `qcom_adsp_pwr_lmts.ko`, into `updates/sl7-deep-sleep/`.

## Installing and booting

```sh
sudo apt install ./linux-image-7.3.0-sl7_7.3.0-9.9+sl7.3_arm64.deb \
                 ./linux-headers-7.3.0-sl7_7.3.0-9.9+sl7.3_arm64.deb
```

The package's hooks build the initramfs and run `update-grub` on the installed system. Then
install the pieces from the table above: the out-of-tree modules, the 7.3 Wi-Fi firmware, the
Iris firmware, the DTBs (`sudo tools/dtb/build-dtbs --install 7.3.0-sl7`), and the modprobe
rule. Run `sudo update-initramfs -u -k 7.3.0-sl7` again afterwards, so the initramfs has the
new modules and the DSP firmware (see [audio.md](audio.md) for the firmware hook).

GRUB: the kernel needs a `devicetree` line in its boot entry. The tested setup uses the two
explicit entries in [`custom.cfg.example`](../config/grub/custom.cfg.example), added to the
`custom.cfg` of the GRUB the firmware actually starts. On the tested machine that GRUB belongs
to another installation on the same disk, so the installed system's own `update-grub` output
is never used, and `custom.cfg` and `grubenv` were edited from a mount of that partition. If
you rely on generated entries instead, check that they load `/boot/dtb-<kver>`.

Boot the new kernel once first. `next_entry` is a one-shot choice (what `grub-reboot` sets):

```sh
sudo grub-editenv /path/to/boot/grub/grubenv set next_entry=sl7-7.3.0-sl7-ROOT_UUID
```

After that boot, run the checklist. Once it passes, make the entry the default (this needs
`GRUB_DEFAULT=saved` in that GRUB's configuration; it is what `grub-set-default` sets):

```sh
sudo tools/kernel/first-boot-check            # add --share for a summary you can post
sudo grub-editenv /path/to/boot/grub/grubenv set saved_entry=sl7-7.3.0-sl7-ROOT_UUID
```

`first-boot-check` is read-only. It saves its full output under
`~/.local/state/sl7/first-boot/` (or `--out DIR`). That output contains MAC addresses, serial
numbers and partition UUIDs; `--share` writes `share.txt` with those replaced, for an issue
report.

## After any kernel update

Each new kernel release needs all of these. A rebuild with the same release name in the same
build tree needs steps 1 and 4, and step 2 if the device tree changed.

1. Rebuild and sign the out-of-tree modules against the new build tree, install them under
   `/lib/modules/<kver>/updates/`, and run `depmod -a <kver>`.
2. `sudo tools/dtb/build-dtbs --install <kver>`, which writes `/boot/dtbs/<kver>/qcom/` and
   points `/boot/dtb-<kver>` at the IR DTB. Never reuse another kernel's DTB: it has to match
   that kernel's bindings.
3. The 7.3 Wi-Fi firmware lives in a per-release directory: copy
   `/lib/firmware/updates/<old kver>/ath12k` to `/lib/firmware/updates/<kver>/`.
4. `sudo update-initramfs -u -k <kver>`.
5. Add or update the GRUB entries (kernel, initrd and `devicetree` paths).
6. Boot it once and run `sudo tools/kernel/first-boot-check`.

## Undo

```sh
sudo apt purge linux-image-7.3.0-sl7 linux-headers-7.3.0-sl7
sudo rm -r /boot/dtbs/7.3.0-sl7 /boot/dtb-7.3.0-sl7 /lib/modules/7.3.0-sl7 \
           /lib/firmware/updates/7.3.0-sl7
```

Then delete the two entries from GRUB's `custom.cfg` and set `saved_entry` back to the previous
kernel's entry. `/lib/firmware/updates/qcom/.../qcvss8380.mbn` and the modprobe rule are
harmless to leave; remove them if no kernel uses them.

## Known issues on 7.3

- **panel-edp warning at about 2 s.** `WARNING: drivers/gpu/drm/panel/panel-edp.c:829`, then
  `Unknown panel SHP 0x1572, using conservative timings`. The 13.8" Sharp panel is not in
  panel-edp's table, and the driver warns with a full backtrace on purpose. It taints the
  kernel (`W`). The display works. The fix is a table entry for the panel.
- **Two CPUs fail to start.** `psci: failed to boot CPU7 (-22)` and the same for CPU11. The
  device tree describes the 12 cores of the X1E80100 die and this X1P-64-100 has 10 enabled.
  10 CPUs come up; harmless.
- **Only CPU cluster 0 has cpufreq.** `/sys/devices/system/cpu/cpufreq/` has only `policy0`
  (CPUs 0-3); clusters 1 and 2 run at a fixed level with no energy model, and nothing is
  logged. Patch 0006 should fix it but is untested; until then
  [`sl7-power-mode`](power.md) parks those cores on battery.
- **GPU firmware errors before the root file system is mounted.** Three
  `Direct firmware load for qcom/gen70500_sqe.fw failed with error -2` lines, because the GPU
  firmware is not in the initramfs. The GPU starts once the root file system is up
  (`Loaded GMU firmware` at about 7 s).
- **Touchscreen hiccups.** `spi1.0` sometimes logs `Body read failed: -110` and a 2 s
  `Response timeout` for a GET_FEATURE at boot or around suspend. It recovers by itself.
- **PCIe L2 timeout on suspend.** `qcom-pcie 1c08000.pcie: Timeout waiting for L2 entry!` on
  every suspend (the Wi-Fi link). ItsLucas sees it too. Deep sleep still reaches CX collapse
  and Wi-Fi reconnects after resume.
- **GCC and GPUCC reach `sync_state` only by timeout**, so `fw_devlink.sync_state=timeout` must
  stay on the command line until the GMU gets a driver (Akhil P Oommen's "drm/msm: Attach a
  driver to GMU" series, per the kit's notes).

## Credits

- [ItsLucas/surface-laptop-7-ubuntu-kernel](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel):
  the patch kit and its CI rules, which this kernel is built on. Its provenance file credits the
  patches it carries: the ath12k rfkill workaround from
  [bryce-hoehn/linux-surface-laptop-7](https://github.com/bryce-hoehn/linux-surface-laptop-7),
  the QSPI and spi-hid transport from
  [ELLX-Kernel](https://github.com/ProgrammerIn-wonderland/ELLX-Kernel), the DisplayPort audio
  and Iris device-tree shape from [dwhinham/linux-sp11](https://github.com/dwhinham/linux-sp11),
  Oliver White's Romulus camera series, Jens Glathe's
  [PS883x series](https://patchwork.kernel.org/series/1171308/) and Bartosz Golaszewski's
  [QCE series](https://patchwork.kernel.org/series/1191131/).
- [justririll/x1e-sleep](https://github.com/justririll/x1e-sleep): the ADSP standby module.
- Ubuntu's kernel team for the 7.3.0-9.9 source with the X1E camera nodes.
