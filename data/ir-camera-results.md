# IR camera test results

Measured on a Surface Laptop 7 13.8" (model 2036) booting the `romulus15` DTB with the IR
overlays, on 7.0.0-rc4 (2026-10-25) and 7.3.0-sl7 (2026-10-27). Setup and background are
in [docs/ir-camera.md](../docs/ir-camera.md). These are summaries; the raw logs and frames
are not published.

## Probe and power

| | 7.0.0-rc4 | 7.3.0-sl7 |
|---|---|---|
| I2C client | `8-0010`, name `vd55g0`, driver `vd55g0` | same |
| Silicon revision | 0x1111 (cut 1), ST's built-in patch | same |
| `vreg_l6m_1p8` | 1800000 uV | 1800000 uV |
| `vreg_l2m_1p2`, `vreg_l4m_1p8` | from the base DTB | from the rails overlay. At boot the kernel logs "Bringing 2000000uV into 1800000-1800000uV" for L4M and 1152000 uV into 1200000 uV for L2M |
| Rails while idle | disabled (runtime PM powers the sensor per stream) | same |
| Modules | `vd55g0` (out of tree), `qcom_camss`, `i2c_qcom_cci`, `ov02c10` | same |
| libcamera 0.4.0 `cam -l` | "Internal front camera" and `'vd55g0'` | same |

## Sensor subdev (7.3)

| Control | Range | Default |
|---|---|---|
| `exposure` | 0-1796 lines | 200 |
| `analogue_gain` | 0-24 | 0 |
| `digital_gain` | 256-2048 | 256 |
| `vertical_blanking` | 77-64931 | 1256 (frame length 1860 lines) |
| `horizontal_blanking` | 556, read-only (line length 1200) | |
| `link_frequency` | 402000000, read-only | |
| `pixel_rate` | 100500000, read-only | |
| `auto_exposure` | 0 auto, 1 manual | 0 |
| `led_mode` | 0 off, 1 on (strobe on sensor GPIO1) | 0 |
| `test_pattern` | 0-7 | 0 |
| `temperature` | fails with error 110 while the sensor is idle | |

Media bus codes: `Y8_1X8` (0x2001), `Y10_1X10` (0x200a). Frame sizes: 644x604, 640x600,
640x480, 320x240.

Video node (`msm_vfe1_video0`) with GREY 644x604: multiplanar, 1 plane, 656 bytes per line,
396224 bytes per frame.

## Media graph (7.3)

CAMSS is `/dev/media0` (driver `qcom-camss`, model "Qualcomm Camera Subsystem"). Entities
other than the VFE nodes:

```
msm_csiphy0, msm_csiphy4
msm_tpg0, msm_tpg1, msm_tpg2          (new in 7.3)
msm_csid0 ... msm_csid4
ov02c10 11-0036                       front camera, on csiphy4
vd55g0 8-0010                         IR camera, on csiphy0
```

Links used for the IR camera:

```
"vd55g0 8-0010":0  -> "msm_csiphy0":0    [ENABLED,IMMUTABLE]
"msm_csiphy0":1    -> "msm_csid1":0      [ENABLED]   (csiphy0 -> csid0 disabled first)
"msm_csid1":1      -> "msm_vfe1_rdi0":0  [ENABLED]
"msm_vfe1_rdi0":1  -> "msm_vfe1_video0"  [ENABLED,IMMUTABLE]
```

All four pads at `Y8_1X8/644x604 field:none`.

## Captures

All GREY 644x604, through the pipeline above.

| Kernel | Conditions | Frames | Frame rate | Last frame (0-255) |
|---|---|---|---|---|
| 7.0 | room light, auto exposure, LED off (first test boot) | 30 of 30 | 29.6 fps | mean 79 |
| 7.0 | auto exposure, LED off | 30 of 30 | 29.56-29.57 fps | mean 72.8, min 6, max 255 |
| 7.0 | manual exposure 600, gain 8, strobe on | 60 of 60 | 29.43-29.73 fps | |
| 7.3 | dark room, auto exposure, LED off (`check-ir --no-frames`) | 30 of 30 | 29.57 fps | mean 16.5, min 0, max 31 |

Over 88 frame intervals logged on 7.0, the interval was 31.9 to 35.9 ms, mean 33.8 ms.

## IR flood LED

| Setting | Frame centre, mean (0-255) |
|---|---|
| manual exposure 600, gain 8, `led_mode=0` | 17 |
| manual exposure 600, gain 8, `led_mode=1` | 114 |

With auto exposure and the strobe on, the sensor shortens its exposure, so the face doesn't
stand out from the background. PM8550 flash channel 4 in torch mode (7.0, `ir:flash-0`,
brightness 255) had no visible effect in the frames.

## Stream stalls (7.3, 2026-10-27)

Back-to-back test starts in one session, each asking for 30 frames (5 in two short tests),
with a 10 s or 5 s timeout:

| Starts | Ran to completion | Stalled after |
|---|---|---|
| first 10 | 6 | 0-2 frames |
| next 33 | 5 | 0-14 frames |

Pauses of 0, 2, 3, 6 or 15 s between starts made no clear difference, nor did manual vs
auto exposure. Nothing was logged in the kernel log. On 7.0, stalls were occasional and
mostly hit a stream started right after another one.

## Front camera with the IR DTB (7.0)

libcamera `cam` captured 5 frames from the OV02C10 at about 18.8 fps, so adding the IR
sensor to CAMSS didn't break the front camera. On 7.3 both cameras are listed too.
