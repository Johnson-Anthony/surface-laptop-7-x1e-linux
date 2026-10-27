# IR camera (ST VD55G0) on the Surface Laptop 7

The Windows Hello camera of the Surface Laptop 7 is an STMicroelectronics **VD55G0**: a
644x604 monochrome global-shutter sensor with one MIPI CSI-2 lane, behind the Qualcomm camera
subsystem (CAMSS). Its IR flood LED is fired by the sensor's own strobe output. With ST's
out-of-tree driver, one driver patch and two device-tree overlays, it streams 644x604 GREY
frames at about 29.6 fps, with or without the IR LED, and [face unlock](face-unlock.md)
uses it.

Everything here was tested on one machine: a Surface Laptop 7 13.8" (model 2036), booting
the `romulus15` device tree (see [hardware.md](hardware.md) for why). The 15" model is
untested and may be wired differently. Check your own Windows install first
([windows-re.md](windows-re.md)).

Status on the 7.3.0-sl7 kernel (checked 2026-10-27):
- the sensor probes as `vd55g0 8-0010`, silicon revision 0x1111 (cut 1);
- `tools/ir-camera/check-ir` captures 30 frames at 29.57 fps;
- Howdy approves face logins in 1 to 2 s in daily use;
- the front RGB camera (OV02C10) still works next to it;
- streams sometimes stall at start (see [Known issues](#known-issues)).

Measured numbers and the media graph are in
[data/ir-camera-results.md](../data/ir-camera-results.md).

## Hardware

Most of the wiring comes from the Windows driver store of this laptop. The method and tools
are in [windows-re.md](windows-re.md). Windows calls the device
`ACPI\VEN_SMO&DEV_55F0&SUBSYS_MSHW0472` ("Surface IR Camera Front"). The camera platform is
`MSHW0475`.

| Item | Value | Source |
|---|---|---|
| Sensor | ST VD55G0, model ID 0x4730 (register 0x0000) | sensor module name, SCFG file |
| I2C | 7-bit address **0x10** on **CCI0, bus 0** (GPIO101/102, `cci_i2c`) | SCFG (8-bit 0x20), platform resource file |
| Reset | **GPIO109**, active low | CAMI resource file |
| Rails, in power-up order | **L4M 1.8 V** (VDDIO), **L2M 1.2 V** (VCORE), 1 ms, **L6M 1.8 V** (VANA), 1 ms, release reset | CAMI resource file |
| MCLK | **24 MHz** | sensor module power settings |
| CSI-2 | **1 data lane**, 755 Mbps, RAW10 (DT 0x2b), 644x604 | sensor module stream configuration |
| Strobe | sensor GPIO1 set to STROBE (`GPIO_0..3_CTRL` = 01 02 01 01) | sensor module init table |
| CSI receiver | **CSIPHY0** (CAMSS `port@0`) | inferred, confirmed by streaming |
| MCLK pin | **MCLK0** (`gpio96`, `cam_mclk`) | inferred, confirmed by streaming |
| CSIPHY rails | L1C 1.2 V, L2C 0.88 V (same as CSIPHY4 for the front camera) | MIPI CSI extension resource file |

The two "inferred" rows come from the Qualcomm reference IR camera slot, which other X1E
laptops use too (the Asus Zenbook A14 IR camera patches have the same GPIO109 reset, L4M rail
and 24 MHz clock). CSIPHY0/1/2 were free; the front camera sits on CSIPHY4.

The community DSDT dumps
([aarch64-laptops/build](https://github.com/aarch64-laptops/build), `misc/microsoft-surface-romulus13_and_15`;
[linux-surface/acpidumps](https://github.com/linux-surface/acpidumps), `surface_laptop_7_qcom`)
give the camera devices (`CAMI`, `CAMF`, `FLSH`) no `_CRS`, so ACPI adds nothing to the table.

### VANA: 1.8 V, not 2.8 V

ST's binding says VANA "must be 2.8 volts". Windows votes L6M at **1.8 V** on this board,
and the sensor works at 1.8 V. (The Surface Pro 11's VD55G0 does get 2.8 V, from L7M.) The
overlay pins L6M to exactly 1.8 V. Don't put 2.8 V on this rail without a schematic.

### Silicon revision and firmware patch

The driver reads REVISION (0x0004) after power-up: 0x1111 is cut 1, 0x1120 is cut 2. This
sensor is cut 1, and ST's built-in cut-1 patch (`vd55g0_patches.h` in ST's driver; also
packaged in [petm5/vd55g-firmware](https://github.com/petm5/vd55g-firmware)) works. Windows
loads a different, 552-byte patch from its init table. It isn't needed here, and it isn't
distributed with this repo. See [Optional: the Windows patch](#optional-the-windows-patch).

## What runs on Linux

| Piece | What | Status |
|---|---|---|
| Sensor driver | ST's GPL driver, [STMicroelectronics/vd55g0-linux-driver](https://github.com/STMicroelectronics/vd55g0-linux-driver) at `a05627b`, plus [patches/vd55g0/0001](../patches/vd55g0/0001-sl7-power-order-and-fw-patch.patch) | out of tree |
| CSI receiver | `qcom-camss` and `i2c-qcom-cci` | in the kernel; the Ubuntu 7.3 tree has the X1E CAMSS and CCI nodes |
| Board wiring | [dts/romulus15-ir-camera-rails.dtso](../dts/romulus15-ir-camera-rails.dtso) (L2M/L4M) and [dts/romulus15-ir-camera.dtso](../dts/romulus15-ir-camera.dtso) | overlays |
| IR flood LED | sensor strobe, V4L2 control `led_mode` | no extra driver |

Mainline 7.3 has an ST VD55G1 driver (`drivers/media/i2c/vd55g1.c`) but no VD55G0 support.
Peter Marshall posted a series to [linux-media](https://lore.kernel.org/linux-media/) in
September 2026 (v1) that generalises the VD55G1 driver and adds the VD55G0, tested on Intel
Surface Pro models. It wasn't tried here. Once it is merged, the out-of-tree driver can go,
and the overlay's `compatible` and supply names may need to follow the new binding.

### The driver patch

[patches/vd55g0/0001-sl7-power-order-and-fw-patch.patch](../patches/vd55g0/0001-sl7-power-order-and-fw-patch.patch)
changes four things in ST's driver:
- **Rail order.** It powers VDDIO, VCORE, waits 1 ms, powers VANA, waits 1 ms, then starts the
  clock and pulses reset, as Windows does. `regulator_bulk_enable()` enables the supplies
  asynchronously, so it has no order. Power-off runs in reverse, with 50 ms after VANA drops.
- **Reset on power-off.** It asserts reset before the clock and the rails go away. Before,
  the active-low reset line stayed released after the first power-up, so the pin was driven
  high into an unpowered sensor.
- **Revision logged.** The silicon revision is logged at info level (one line per power-up,
  so about one per stream), and an unknown revision no longer fails the probe.
- **Optional `fw_patch`.** With `vd55g0.fw_patch=1`, or for an unknown revision, the driver
  loads `vd55g0-surface.bin` through `request_firmware()` instead of the built-in patch.

The rail-order and reset changes follow Windows. The unpatched driver wasn't tried on this
board, so it isn't known whether they are required.

## Install (7.3 kernel)

### 1. Build the driver

```sh
git clone https://github.com/STMicroelectronics/vd55g0-linux-driver.git
cd vd55g0-linux-driver
git checkout -b sl7 a05627b0f6d8775aa54b6fa306e91f425f2cbf9e
git am /path/to/surface-laptop-7-x1e-linux/patches/vd55g0/0001-sl7-power-order-and-fw-patch.patch

KVER=7.3.0-sl7                     # the kernel you will boot
KSRC=/lib/modules/$KVER/build      # its headers, or a built kernel tree
make -C "$KSRC" M="$PWD" modules
```

If the kernel enforces module signatures (`CONFIG_MODULE_SIG_FORCE`, or lockdown under
Secure Boot), sign the module with a key the kernel trusts. For a self-built kernel that is
the tree's own build key:

```sh
"$KSRC"/scripts/sign-file sha512 "$KSRC"/certs/signing_key.pem "$KSRC"/certs/signing_key.x509 vd55g0.ko
```

The 7.3.0-sl7 kernel signs its own modules but doesn't enforce signatures. An unsigned module
still loads there, and taints the kernel (`E`). Install under `updates/` and rebuild the index:

```sh
sudo install -D -m 644 vd55g0.ko /lib/modules/$KVER/updates/vd55g0.ko
sudo depmod -a $KVER
```

Repeat this for every new kernel. [`tools/status/sl7-status`](../tools/status/sl7-status)
reports kernels that lack the module.

### 2. Build the device tree

[`tools/dtb/build-dtbs`](../tools/dtb/build-dtbs) applies the overlays to the packaged
`x1e80100-microsoft-romulus15.dtb` and installs the result as
`/boot/dtbs/<kver>/qcom/x1e80100-microsoft-romulus15-ir.dtb`. By hand:

```sh
inc=/lib/modules/$KVER/build/include     # needs include/dt-bindings
dtbo() { cpp -nostdinc -undef -D__DTS__ -x assembler-with-cpp -I "$inc" "$1" |
         dtc -@ -q -I dts -O dtb -o "$2" -; }
dtbo dts/romulus15-ir-camera-rails.dtso rails.dtbo
dtbo dts/romulus15-ir-camera.dtso ir.dtbo
fdtoverlay -i /usr/lib/linux-image-$KVER/qcom/x1e80100-microsoft-romulus15.dtb \
    -o x1e80100-microsoft-romulus15-ir.dtb rails.dtbo ir.dtbo
```

The rails overlay is only for bases without PM8010 `ldo2`/`ldo4` (the 7.3 base has L1M, L3M
and L5M for the RGB camera only). Check with
`fdtget BASE.dtb /soc@0/rsc@17500000/regulators-8/ldo2 regulator-name`. On 2026-10-27 this
reproduced the installed 7.3.0-sl7 boot DTB byte for byte.

What the main overlay does: adds L6M at 1.8 V, the MCLK0 and reset pin states, the sensor
node on CCI0 bus 0 with `st,leds = <1>` (strobe on sensor GPIO1), and enables CSIPHY0 with
the L1C/L2C rails. CSIPHY0 is disabled and unpowered in the base DT. The endpoint advertises
402 MHz (804 Mbps), the only link frequency ST's driver supports, and CAMSS uses it for its
lane timing. Windows programs the sensor's MIPI rate to 755 Mbps. ST's driver doesn't program
it at all, so the lane runs at the sensor firmware's default. That works.

### 3. Boot it

Point your boot entry's devicetree at the new DTB, and keep an entry with the packaged DTB
as a fallback. CAMSS links the sensors and creates the `/dev/v4l-subdev*` nodes only once
every sensor in the device tree has bound (`camss_subdev_notifier_complete`). So a DTB with the
IR node but no working vd55g0 module can take the front camera down too. That follows from the
CAMSS code; it wasn't observed here.

### 4. Check it

```sh
tools/ir-camera/check-ir --no-frames
```

[`check-ir`](../tools/ir-camera/check-ir) checks the DT node, the driver, the rails and the
media graph, then captures 30 frames with the IR LED off. It reports the frame rate and the
brightness of the last frame. Results go to `${XDG_STATE_HOME:-~/.local/state}/sl7/ir-test/<time>/`.
Without `--no-frames` it also keeps the raw frames and the last frame as a PGM. **The camera
faces you, so those images show your face and your room.** The directory also holds the full
kernel log. Look through it before sharing anything from it.

## Capturing by hand

The IR camera has no ISP path. Use a raw CAMSS pipeline:
`vd55g0 8-0010 -> msm_csiphy0 -> msm_csid1 -> msm_vfe1_rdi0 -> msm_vfe1_video0`.

```sh
M=/dev/media0     # the media device whose driver is qcom-camss
F=Y8_1X8/644x604
media-ctl -d $M -l '"msm_csiphy0":1->"msm_csid0":0[0]'
media-ctl -d $M -l '"msm_csiphy0":1->"msm_csid1":0[1]'
media-ctl -d $M -l '"msm_csid1":1->"msm_vfe1_rdi0":0[1]'
for p in '"vd55g0 8-0010":0' '"msm_csiphy0":0' '"msm_csid1":0' '"msm_vfe1_rdi0":0'; do
    media-ctl -d $M -V "${p}[fmt:$F field:none]"
done
VID=$(media-ctl -d $M -e msm_vfe1_video0)
v4l2-ctl -d "$VID" --set-fmt-video=width=644,height=604,pixelformat=GREY
timeout 10 v4l2-ctl -d "$VID" --stream-mmap --stream-count=30 --stream-to=ir.raw
```

- **Drop `csiphy0 -> csid0` first.** CAMSS enables that link at boot, and a CSIPHY output can
  drive only one CSID. Linking csid1 while it is enabled gives EBUSY, and STREAMON then fails
  with EPIPE.
- Lines are padded to **656 bytes** (`Bytes per Line`), so a frame is 396224 bytes.
- `Y10_1X10` (10-bit) is also offered. The frame sizes are 644x604, 640x600, 640x480 and
  320x240.
- libcamera 0.4.0 lists the sensor as a second camera, but its software ISP doesn't take 8-bit
  or 10-bit mono input. Capturing through libcamera wasn't tried.

## IR flood LED

The emitter is wired to the sensor's **GPIO1 strobe** output. With `st,leds = <1>` in the DT,
the driver exposes the V4L2 control `led_mode` on the sensor subdev. Set to 1, it fires the
LED in hardware, in sync with each exposure, and only while streaming:

```sh
SD=$(media-ctl -d /dev/media0 -e "vd55g0 8-0010")
v4l2-ctl -d "$SD" -c auto_exposure=1 -c exposure=600 -c analogue_gain=8 -c led_mode=1
# ... stream as above ...
v4l2-ctl -d "$SD" -c led_mode=0 -c auto_exposure=0
```

With manual exposure 600 and gain 8, the frame centre went from a mean of 17 (strobe off) to
114 (strobe on): a lit face on a black background, which is what face recognition wants. With
auto exposure, the sensor just lowers its exposure and the strobe mostly brightens the room.
So use manual exposure.

Windows' flash driver package configures an IR LED on the PM8550 flash block at 700 mA,
triggered by software or by the sensor ("IRLED_CCI_Trigger"). The Qualcomm reference slot
uses flash channel 4. On this board that channel did nothing in torch mode, so the overlay
leaves the PMIC flash alone, as the firmware set it up. Whether the strobe drives the LED
directly or through a PMIC channel that the firmware configured for hardware triggering is
unknown. Either way, Linux only needs `led_mode`.

**Eye safety:** Windows pulses the IR LED only during exposures. The strobe keeps it that
way. Don't drive a flash channel continuously at flash current while experimenting.

## Optional: the Windows patch

Not needed for cut-1 or cut-2 sensors, and untested: nobody has loaded it on Linux. If you
want to try it, extract it from your own Windows install. It is the run of byte writes at
0x2000 in the init table of
`DriverStore/FileRepository/surfacecamauxsensor_extension8380.inf_arm64_*/com.surface.sensormodule.aux_vd55g0_MSHW0472.bin`:

```sh
python3 -I tools/windows-re/chromatix_regs.py --patch vd55g0-surface.bin \
    /mnt/win/Windows/System32/DriverStore/FileRepository/surfacecamauxsensor_extension8380.inf_arm64_*/com.surface.sensormodule.aux_vd55g0_MSHW0472.bin
sudo install -m 644 vd55g0-surface.bin /lib/firmware/
# then load the module with fw_patch=1, e.g. options vd55g0 fw_patch=1 in /etc/modprobe.d/
```

From driver version 1.0.4546.5501 it is 552 bytes (0x2000-0x2227), sha256
`5c07088c8871792e48a3d75d5b9af1cb3725739b8d6aaed229be6f7c0126b321`. The patched driver logs
the patch version it reads back, but what version Windows expects is unknown.

## Known issues

- **Streams sometimes stall at start.** A stream stops after 0 to about 14 frames, and nothing
  is logged. Starting it again recovers it, sooner or later. On 7.0 this was occasional,
  mostly for a stream started right after another one. On 7.3, in one session of back-to-back
  test starts (2026-10-27), only 11 of 43 starts ran to completion, and it got worse as the
  session went on (6 of the first 10, then 5 of 33). Face unlock still worked in daily use
  around that time. Readers should use a frame timeout and restart: Howdy's reader restarts
  once, and `check-ir` tries twice. The cause is unknown.
- **Frame rate.** The driver's default mode is nominally 60 fps (frame length 1860 lines), but
  frames arrive at 29.6 fps. Windows writes `EXT_CLOCK` = 12 MHz although MCLK is 24 MHz,
  and sets the MIPI rate to 755 Mbps. ST's driver writes the real 24 MHz and leaves the MIPI
  rate at the firmware default. Whether that explains the factor of two wasn't checked.
  30 fps is plenty for face unlock.
- **Temperature control.** Reading `temperature` while the sensor is idle (runtime suspended)
  fails with error 110 and logs `i2c-qcom-cci ac15000.cci: master 0 queue 0 timeout`.
  `v4l2-ctl -l` on the subdev does this. It is harmless.
- **Raw I2C.** `i2ctransfer` reads to 0x10 on the CCI bus time out (seen on 7.0). Talk to the
  sensor through the driver.
- **libcamera** warns that the driver lacks the camera orientation control and has no camera
  location. It doesn't matter for the raw pipeline.
- 7.3's CAMSS logs `Entity type for entity msm_tpg0 was not initialized!` (and for tpg1/2) at
  boot. It is unrelated to the IR camera.

## History (7.0 kernel)

The camera was brought up on 2026-10-25 on a 7.0.0-rc4 kernel (murkurie's ELLX kernel,
branch `7.0.0-rc4-10-sl7`) with a hand-made `romulus15-touchscreen` base DTB. That base already had L2M and L4M, so only the
main overlay was needed, applied with `fdtoverlay`. Findings from that setup, all still valid
on 7.3:
- The first test boot probed the sensor, cut 1, with ST's built-in patch. L6M came up at
  1.8 V, and 30 of 30 frames arrived at 29.6 fps (mean 79/255 under room light). That
  confirmed CSIPHY0, MCLK0 and the single lane.
- The first capture hit the csid0 EBUSY gotcha. That failed start left `vfe1_rdi0` marked as
  streaming, and the next STREAMON triggered a one-off WARN in `call_s_stream`, a harmless
  CAMSS error path.
- The overlay then also enabled `pm8550_flash` with channel 4 (`ir:flash-0`). Torch mode on
  that channel lit nothing, the strobe did, so the flash node was dropped.
- The front camera kept working with the IR DTB (libcamera, 5 frames at about 18.8 fps).

On 7.3 the packaged romulus15 DTB lacks L2M/L4M, which is why the rails overlay exists, and
the module is built against the 7.3 tree. Nothing else changed: the sensor is still
`vd55g0 8-0010`, so Howdy's reader works unchanged.

## Credits

- STMicroelectronics for the GPL [VD55G0 driver](https://github.com/STMicroelectronics/vd55g0-linux-driver)
  and its built-in firmware patches.
- [petm5/vd55g-firmware](https://github.com/petm5/vd55g-firmware) for packaging the VD55G
  firmware patches.
- Peter Marshall's VD55G0 series on linux-media, the reference for upstream support.
- The Qualcomm CAMSS and CCI maintainers, and the Ubuntu and
  [ItsLucas](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel) SL7 kernel trees.
- [aarch64-laptops/build](https://github.com/aarch64-laptops/build) and
  [linux-surface/acpidumps](https://github.com/linux-surface/acpidumps) for the DSDT dumps.
