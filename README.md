# Surface Laptop 7 (Snapdragon X) on Linux

Fixes, patches, tools and findings from bringing up Linux on a Microsoft Surface Laptop 7: face
unlock with the Windows Hello IR camera, full SoC deep sleep, a fix for a touchpad that's dead
after cold boots, and a reproducible custom 7.3 kernel.

**Tested machine:** Surface Laptop 7, 13.8" (model 2036), Snapdragon X Plus X1P-64-100,
16 GB, Parrot OS (Debian-based, arm64), kernel `7.3.0-sl7`. This model boots the X1E80100
`romulus15` device tree; [hardware.md](docs/hardware.md) explains why. Other variants are
untested, and reports are welcome.

## Status

| | State on 7.3.0-sl7 | Details |
|---|---|---|
| Display, keyboard, Bluetooth, GPU | Works | [kernel-7.3.md](docs/kernel-7.3.md) |
| Wi-Fi | Works, with WCN7850 firmware `c7-00108` from linux-firmware 20261019 | [firmware.md](docs/firmware.md) |
| Touchpad | Works. The cold-boot fix isn't proven on 7.3 yet | [touchpad.md](docs/touchpad.md) |
| Touchscreen | Works, with brief error-and-recover episodes around suspend | [known-issues.md](docs/known-issues.md) |
| Speakers, headphones | Work. Right-speaker settings on 7.3 still to be checked | [audio.md](docs/audio.md) |
| Front camera | Works (libcamera) | [kernel-7.3.md](docs/kernel-7.3.md) |
| IR camera | Works with ST's driver, one patch and a device-tree overlay. Stream start sometimes stalls | [ir-camera.md](docs/ir-camera.md) |
| Face unlock | Lock screen and polkit prompts (so Bitwarden), about 1 s | [face-unlock.md](docs/face-unlock.md) |
| Deep sleep | Full SoC deep sleep (CX collapse, DDR self-refresh) at about 270 mW; the lid wakes it | [deep-sleep.md](docs/deep-sleep.md) |
| Factory MAC addresses | Work, with [valeronm/sl7-mac](https://github.com/valeronm/sl7-mac) | [mac-address.md](docs/mac-address.md) |

## Findings

- **Deep sleep at about 270 mW.** Suspend used to draw 1.1-1.2 W with the SoC never leaving its
  shallow states. On 7.3, the `deep` sleep mode reaches CX collapse, AOSS sleep and DDR
  self-refresh: 263 mW (0.50 %/h) over 5.2 hours, 271 mW on average over 20 hours of sleep.
  `s2idle` stays shallow at EL1 under the Gunyah hypervisor, so EL2 tricks aren't needed.
  ([deep-sleep.md](docs/deep-sleep.md), [raw data](data/))
- **Windows Hello IR camera identified and running.** No Linux driver or public description
  existed. The sensor (an ST VD55G0), its power rails, reset line and clock were recovered from
  the Windows driver store, ACPI tables and Qualcomm camera files
  ([windows-re.md](docs/windows-re.md)). The IR LED turned out to be fired by the sensor's own
  strobe, not the PMIC flash driver. ([ir-camera.md](docs/ir-camera.md))
- **The dead touchpad has four causes.** Across 45 boots on 7.0, 13 came up with a silently dead
  touchpad. The main cause is the embedded controller holding the touchpad off until Linux
  enables "posture events", which it never did (diagnosed by ItsLucas). This repo adds a
  boot-time workaround and three SPI HID driver fixes for the other causes, plus a change that
  stops the touch devices holding up every resume (about 3 s). ([touchpad.md](docs/touchpad.md))
- **The 13.8" runs the 15" device tree.** The two upstream board files differ only in their
  model strings, and the community kit adds its features to `romulus15` only. The touchpad,
  touchscreen and cameras it adds all work on the 13.8". ([hardware.md](docs/hardware.md))
- **A reproducible 7.3 kernel.** Ubuntu's 7.3.0-9.9 source, the
  [ItsLucas kit](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel), and seven patches
  from this repo, with git tree hashes to check each step against.
  ([BASE.md](patches/kernel-7.3/BASE.md))

## Getting started

Read [hardware.md](docs/hardware.md) and [known-issues.md](docs/known-issues.md) first. These
steps change how the laptop boots; keep a working boot entry and a way to boot rescue media.

1. **Build the kernel:** [patches/kernel-7.3/BASE.md](patches/kernel-7.3/BASE.md), then install
   and boot it once with [kernel-7.3.md](docs/kernel-7.3.md#installing-and-booting) and the
   GRUB example in [config/grub/](config/grub/).
2. **Install the firmware** it needs: [firmware.md](docs/firmware.md). None of it is
   redistributed here.
3. **Build and install the device trees:** `sudo tools/dtb/build-dtbs --install 7.3.0-sl7`.
4. **Check it:** `sudo tools/kernel/first-boot-check`, then `sudo tools/status/sl7-status`.
5. **Add features:** [face unlock](docs/face-unlock.md), [deep sleep](docs/deep-sleep.md),
   [touchpad tools](docs/touchpad.md), [audio](docs/audio.md).

## Layout

| Path | Contents |
|---|---|
| [`docs/`](docs/) | One page per area, plus [hardware](docs/hardware.md), [firmware](docs/firmware.md) and [known issues](docs/known-issues.md) |
| [`patches/kernel-7.3/`](patches/kernel-7.3/) | Kernel patches: three SPI HID fixes, the resume change, a device-tree tweak, and two packaging fixes |
| [`patches/vd55g0/`](patches/vd55g0/), [`patches/howdy/`](patches/howdy/) | IR sensor driver patch, Howdy camera reader |
| [`dts/`](dts/) | Device-tree overlays: IR camera, its power rails, deep-sleep residency |
| [`tools/`](tools/) | Status and test scripts, the DTB builder, kernel build helpers, Windows decoders |
| [`config/`](config/), [`systemd/`](systemd/) | GRUB example, kernel config, PAM, audio, modprobe, units and the sleep hook |
| [`data/`](data/) | Measurements behind the numbers above |

## How this was built

I led this work with Claude Code agents: I set the goals and the direction, ran every hardware
test, and made the calls; the agents researched, wrote most of the code and drafted the docs.
[docs/agentic-workflow.md](docs/agentic-workflow.md) shows how that split worked, with the
moments where the human side changed the outcome.

## Reports and contributions

Issues and pull requests are welcome, especially results from other Surface Laptop 7 variants.
`sudo tools/kernel/first-boot-check --share` writes a summary with MAC addresses, serial numbers
and partition IDs removed. None of the patches here has been submitted upstream yet.

## Credits and license

This builds on work by ItsLucas, the ELLX-Kernel and linux-surface projects,
STMicroelectronics, Howdy, justririll and others: see [CREDITS.md](CREDITS.md).

Licensing follows [REUSE](https://reuse.software/); each file says which license applies.
Scripts are MIT, kernel patches carry the license of the code they change (GPL-2.0-only or
BSD-3-Clause), device-tree overlays are BSD-3-Clause, and the docs are CC BY 4.0. Texts are in
[LICENSES/](LICENSES/). No firmware, Windows files or other third-party binaries are included.
