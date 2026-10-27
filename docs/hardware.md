# Hardware

Everything in this repo was developed and tested on one machine: a Surface Laptop 7 (13.8")
with the Snapdragon X Plus X1P-64-100. Other variants are untested. Reports are welcome (see the end of
this page).

## Tested machine

| Part | Details | Linux device |
|---|---|---|
| Model | Surface Laptop, 7th Edition, 13.8" (DMI SKU `Surface_Laptop_7th_Edition_2036`) | |
| SoC | Snapdragon X Plus X1P-64-100, 10 Oryon cores, 16 GB RAM (SMBIOS: "Snapdragon(R) X 10-core X1P64100"; `soc_id` 615) | runs the `qcom,x1e80100` device tree |
| UEFI | Microsoft 175.235.235 (2026-04-02) | |
| Panel | Sharp LQ138P1JX61, 2304x1536, 291 x 194 mm (eDP) | `card1-eDP-1` |
| Keyboard | Surface Aggregator HID, 045E:006C | `0019:045E:006C` |
| Touchpad | SPI HID, 045E:0C77 | `spi0.0` |
| Touchscreen | SPI HID, 045E:0C6E | `spi1.0` |
| Wi-Fi / Bluetooth | Qualcomm WCN7850 (FastConnect 7800), PCI 17cb:1107 | `0004:01:00.0` |
| Front camera | OmniVision OV02C10 | `ov02c10 11-0036` |
| IR camera | STMicroelectronics VD55G0, 644x604 monochrome | `vd55g0 8-0010` |
| Audio | X1E80100-Romulus (WCD938x headphone codec, WSA speakers) | ALSA card `X1E80100Romulus` |
| Battery | through the ADSP battery manager | `qcom-battmgr-bat` |

## Why a 13.8" runs the 15" device tree

The kernel has two board files for this laptop, `x1e80100-microsoft-romulus13.dts` (13.8") and
`x1e80100-microsoft-romulus15.dts` (15"). In the Ubuntu 7.3.0-9.9 source they differ only in
the `model` and `compatible` strings. Both include the same `x1e80100-microsoft-romulus.dtsi`.

The [ItsLucas SL7 kernel kit](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel)
adds the touchpad, touchscreen, cameras, GPIO power rails and DisplayPort audio links to
`romulus15.dts` only. So this machine boots `romulus15` and gets all of them. The touchpad,
touchscreen, cameras and power rails work on the 13.8" model; DisplayPort audio wasn't tested
(see [the kernel page](kernel-7.3.md) for what was checked).

One side effect: the kernel reports the model as "Microsoft Surface Laptop 7 (15 inch)"
(`/proc/device-tree/model`), even though DMI and the panel say 13.8". The DMI SKU is the
reliable way to identify the machine.

## Why an X Plus runs the X1E80100 device tree

The X1P-64-100 is the same die as the X Elite X1E-80-100 (Qualcomm's "Hamoa"), with two of the
twelve cores disabled. Linux has no separate device tree for it, so it boots the X1E80100 one,
which describes twelve CPUs. Two of them fail to start, and that is expected:

```
psci: failed to boot CPU7 (-22)
psci: failed to boot CPU11 (-22)
```

`/sys/devices/system/cpu/online` shows `0-6,8-10`. The kernel's SoC ID table (7.3) doesn't know
`soc_id` 615 yet, so `/sys/devices/soc0` reports no SoC name. Neither causes any problem seen here.

## Identify your machine

```sh
cat /sys/class/dmi/id/product_sku            # ..._2036 on the 13.8" tested here
cat /sys/devices/soc0/machine                # model string from the device tree in use
cat /sys/devices/soc0/soc_id                 # 615 = X1P-64-100 here; 555 = X1E-80-100
sudo dmidecode -t processor | grep Version   # the CPU name the firmware reports
ls /sys/bus/hid/devices/                     # 045E:0C77 touchpad, 045E:0C6E touchscreen
```

To read the panel size, decode the EDID (`edid-decode /sys/class/drm/card*-eDP-*/edid`). The
13.8" panel reports 2304x1536 at 291 x 194 mm.

## Other variants

| Variant | Status |
|---|---|
| 13.8", X Plus X1P-64-100 (2036) | **Tested here** |
| 13.8", X Elite X1E-80-100 | Untested. Same die with all twelve cores, so it should behave the same |
| 15", X Elite X1E-80-100 | Untested here. The `romulus15` tree targets it, and ItsLucas's kit was written for it |
| 15", X Plus | Untested |

If you have a variant and try any of this, run
[`tools/kernel/first-boot-check --share`](../tools/kernel/) and open an issue with the
summary it writes. It removes MAC addresses, serial numbers and partition IDs.
