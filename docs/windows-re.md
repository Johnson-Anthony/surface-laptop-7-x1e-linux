# Reading the camera wiring from a Windows install

A Windows-on-Snapdragon laptop doesn't describe its cameras in ACPI the way Linux would
need. The DSDT entries for the Surface Laptop 7 cameras have no `_CRS`. The wiring lives in
the camera driver packages instead: which GPIOs, which regulators at which voltage, in which
order, which I2C address, how many CSI lanes. This page describes how the
[IR camera](ir-camera.md) wiring was recovered from the laptop's own Windows partition, and
the four small decoders in [tools/windows-re/](../tools/windows-re/).

This repo ships none of the Windows files and none of their decoded dumps. They are Microsoft
and Qualcomm material. Run the tools on your own install. The docs only state short facts
taken from them, such as a GPIO number or a voltage.

## 1. Mount Windows read-only

```sh
sudo mkdir -p /mnt/win
sudo mount -t ntfs3 -o ro /dev/nvme0n1pN /mnt/win     # or: -t ntfs-3g -o ro
FR=/mnt/win/Windows/System32/DriverStore/FileRepository
```

Use the Windows partition (`lsblk -f` shows it as ntfs). If BitLocker is on, unlock it first
(`cryptsetup open --type bitlk` can, with the recovery key). Don't mount it read-write.

## 2. Find the device

Windows records every device it enumerated in the `SYSTEM` registry hive. Copy
`/mnt/win/Windows/System32/config/SYSTEM` somewhere and list the ACPI devices:

```sh
python3 -I tools/windows-re/enum_acpi.py SYSTEM CAM MSHW SMO
```

[`enum_acpi.py`](../tools/windows-re/enum_acpi.py) needs [regipy](https://github.com/mkorman90/regipy)
(`pip install regipy` in a venv). It prints each instance's description, hardware IDs,
service and location. On the 13.8" Surface Laptop 7 the IR camera is
`ACPI\VEN_SMO&DEV_55F0&SUBSYS_MSHW0472`, "Surface IR Camera Front". `SMO` plus `55F0`
already hints at an ST sensor, and `MSHW0472` is the board-specific subsystem ID. The other
IDs that matter are the camera platform (`MSHW0475`) and the flash (`QCOM0C27`). A different
model or size may use different subsystem IDs. The driver package for this camera also
carries files for `MSHW0492` (another VD55G0 configuration) and `MSHW0562`, next to a VD55G1
sensor module. Which devices those are wasn't checked.

## 3. Find the driver packages

Each driver package is a directory `FileRepository/<name>.inf_arm64_<hash>/`. Find the INFs
that name your subsystem ID:

```sh
grep -ril MSHW0472 $FR/*/*.inf
```

The camera INFs here were plain ASCII. Some INFs are UTF-16, and grep misses those; convert
them with `iconv -f UTF-16 -t UTF-8` first.

For the IR camera, the useful packages were:

| Package | What it holds |
|---|---|
| `surfacecamauxsensor_extension8380.inf_arm64_*` | per-board files for the IR sensor: `com.surface.sensormodule.aux_vd55g0_MSHW0472.bin` (sensor module), `SCFG_AUX_MSHW0472.bin` (sensor configuration), `CAMI_RES_MSHW0472.bin` (resources) |
| the camera platform package (`grep -ril MSHW0475`) | `CAMP_RES_MSHW0475.bin`: TLMM pins and clocks for the CCI buses |
| `qccammipicsi_ext8380.inf_arm64_*` | CSIPHY rails |
| `qccamflash_ext8380.inf_arm64_*` | flash LED settings, in the INF itself (`IrLedCurrentMilliampere`) |

The INF's `[SourceDisksFiles]` section lists what each file is for. The file names already
give away the sensor: `aux_vd55g0`.

## 4. Decode the resource files (AeoB)

The `CAMI_RES_*`, `CAMP_RES_*` and `SCFG_*` files are Qualcomm "AeoB" objects: a small
header, then nested tag-length-value packages of integers and strings, much like ACPI
packages. [`aeob.py`](../tools/windows-re/aeob.py) prints them as a tree:

```sh
python3 -I tools/windows-re/aeob.py $FR/surfacecamauxsensor_extension8380*/CAMI_RES_MSHW0472.bin
```

What to look for:
- **Power resources** with regulator names such as `PPP_RESOURCE_ID_LDO4_M`, their voltage in
  microvolts and the order they are turned on in. Delays sit between them. For the IR camera
  that gave L4M 1.8 V, L2M 1.2 V, 1 ms, L6M 1.8 V, 1 ms, then reset released.
- **`TLMMGPIO`** entries with pin numbers: the reset line (GPIO109) in the sensor file, and
  the CCI SDA/SCL pairs (101/102 and 235/236) in the platform file, next to the
  `cam_cc_cci_0_clk` / `cam_cc_cci_1_clk` clocks. That tells you which CCI and bus the sensor
  is on.
- The **SCFG** file names the sensor module and tuning files, and carries the sensor's 8-bit
  I2C address (0x20 in the low byte of a packed value, so 7-bit 0x10).

The PMIC regulator letters map to the Linux RPMh regulator nodes: `L4M` is `ldo4` of PMIC
`m` (PM8010 here, `regulators-8` under `rsc@17500000` in the X1E device tree).

## 5. Decode the sensor module (Chromatix)

The `com.<vendor>.sensormodule.*.bin` files use Qualcomm's CamX parameter layout: a schema
table of named fields, then a data section. [`schema.py`](../tools/windows-re/schema.py)
lists the fields. [`chromatix_regs.py`](../tools/windows-re/chromatix_regs.py) decodes every
`regSetting` block into register accesses:

```sh
M=$(echo $FR/surfacecamauxsensor_extension8380*/com.surface.sensormodule.aux_vd55g0_MSHW0472.bin)
python3 -I tools/windows-re/schema.py "$M" | less
python3 -I tools/windows-re/chromatix_regs.py "$M" | less
```

What to look for:
- the **power settings** (clock rate: 24 MHz MCLK) and the **init sequence**: polls, the
  firmware patch download, the boot commands and the static configuration writes;
- **stream configuration** and resolution data: lane count, data rate, CSI data type, frame
  size, line and frame length;
- **GPIO and strobe registers.** For the VD55G0, the writes to `GPIO_0..3_CTRL` set GPIO1 to
  STROBE. That led to the IR LED: it is fired by the sensor, not by Linux.

Read the register addresses against the Linux driver's register map (ST's
[vd55g0.c](https://github.com/STMicroelectronics/vd55g0-linux-driver)) to name them. With
`--patch OUT`, `chromatix_regs.py` writes the firmware patch out of the init sequence, for
the optional `vd55g0-surface.bin` ([ir-camera.md](ir-camera.md#optional-the-windows-patch)).

## 6. Fill the gaps

Two things weren't found in the files decoded here: which CSIPHY the sensor uses, and
which MCLK block. They came from the Qualcomm reference IR slot (as used for the Asus Zenbook
A14), and streaming confirmed them. Which CSIPHYs are still free narrows it down.

The DSDT was checked too. The camera devices (`CAMI`, `CAMF`, `FLSH`) have no `_CRS`, so it
adds nothing. On this laptop the DSDT is handed over by the boot firmware (XBL) at run time,
so it isn't in the UEFI capsule, and `/dev/mem` reads are blocked by `STRICT_DEVMEM`. The
community dumps ([aarch64-laptops/build](https://github.com/aarch64-laptops/build),
[linux-surface/acpidumps](https://github.com/linux-surface/acpidumps)) were enough.

Turn the findings into a DT overlay and test it with a one-shot boot entry, keeping the
stock DTB as the default until the sensor probes. Check the probe (`dmesg`, the chip ID
read), the rails (`/sys/class/regulator`), then capture frames before trusting any inferred
value. [dts/romulus15-ir-camera.dtso](../dts/romulus15-ir-camera.dtso) is the result for the
IR camera.

## The tools

| Tool | Input | Output |
|---|---|---|
| [`enum_acpi.py SYSTEM [PATTERN...]`](../tools/windows-re/enum_acpi.py) | offline SYSTEM hive | ACPI devices with IDs, service, location (needs regipy) |
| [`aeob.py FILE`](../tools/windows-re/aeob.py) | AeoB resource file (`CAMI_RES_*`, `CAMP_RES_*`, `SCFG_*`) | nested package tree |
| [`schema.py FILE`](../tools/windows-re/schema.py) | Chromatix sensor module | schema rows: id, name, offset, size |
| [`chromatix_regs.py [--patch OUT] FILE`](../tools/windows-re/chromatix_regs.py) | Chromatix sensor module | register settings, one access per line; or the firmware patch bytes |

All of them only read their input. The formats were worked out from these files alone, so
fields the tools don't name are unknown, not missing. Run them with `python3 -I` (isolated
mode) so nothing in the current directory gets imported.
