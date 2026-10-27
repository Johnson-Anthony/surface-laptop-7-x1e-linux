<!-- SPDX-FileCopyrightText: 2026 Anthony Johnson -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Howdy patches: CAMSS IR reader

Three patches for [Howdy](https://github.com/boltgolt/howdy) that add a recording plugin,
`camss_ir`, for the Surface Laptop 7 IR camera (ST VD55G0 behind Qualcomm CAMSS). Howdy's
stock readers open a V4L2 node with OpenCV or ffmpeg. That doesn't work here: the CAMSS raw
video node streams nothing until its media links and pad formats are set, and the IR flood
LED only fires when the sensor's strobe output is enabled.

| Patch | What it does |
|---|---|
| 0001 | `recorders/camss_ir_reader.py`: sets up the media pipeline, sets manual exposure and gain, turns on the strobe (`led_mode=1`), streams GREY frames through a `v4l2-ctl` pipe, restarts once if the stream stalls, and stops the stream (and so the LED) if Howdy dies. Hooks it into `video_capture.py` and `meson.build`. |
| 0002 | Makes `release()` idempotent. It runs from `atexit` and again from `VideoCapture.__del__` at interpreter shutdown. |
| 0003 | Adds `get()` for the frame size, which `compare.py` uses to scale frames. |

Base: `boltgolt/howdy` master at
[`d3ab99382f88`](https://github.com/boltgolt/howdy/commit/d3ab99382f88f043d15f15c1450ab69433892a1c)
("Merge pull request #1023 from boltgolt/beta"). The patches keep Howdy's MIT license.

The setup around them (PAM, enrolment, results) is in
[docs/face-unlock.md](../../docs/face-unlock.md). The camera itself is in
[docs/ir-camera.md](../../docs/ir-camera.md).

## Apply

```sh
git clone https://github.com/boltgolt/howdy.git
cd howdy
git checkout -b sl7-camss-ir d3ab99382f88f043d15f15c1450ab69433892a1c
git am /path/to/surface-laptop-7-x1e-linux/patches/howdy/*.patch
```

## Build and install

Tested on a Debian-based system (Parrot OS 7, Python 3.13). Build dependencies:

```sh
sudo apt install meson ninja-build g++ libpam0g-dev libinih-dev libevdev-dev \
    python3-dev python3-venv python3-numpy v4l-utils
```

`v4l-utils` is a runtime dependency too: the reader calls `media-ctl` and `v4l2-ctl`.

Howdy's Python side runs from a virtual environment that also sees the system packages
(numpy comes from Debian), with dlib and OpenCV from pip. dlib builds from source on arm64,
which takes a while.

```sh
sudo python3 -m venv --system-site-packages /opt/howdy-venv
sudo /opt/howdy-venv/bin/pip install dlib opencv-python-headless
```

Tested with dlib 20.0.1, opencv-python-headless 5.0.0 and numpy 2.2.4. OpenCV 5's
`calcHist` returns a flat array; Howdy's `hist[0]` indexing still works with it.

Configure, build and install under `/usr/local`:

```sh
meson setup build --prefix=/usr/local -Dconfig_dir=/etc/howdy \
    -Dpam_dir=/usr/local/lib/security -Dpython_path=/opt/howdy-venv/bin/python3
ninja -C build
sudo ninja -C build install
```

That gives `/usr/local/bin/howdy`, `/usr/local/lib/security/pam_howdy.so` and
`/etc/howdy/config.ini`. Keep a copy of the installed `config.ini` before editing it.
Then download the three dlib models (face detector, landmarks, recognition) from
[davisking/dlib-models](https://github.com/davisking/dlib-models) with the script Howdy
installs next to where they belong:

```sh
cd /usr/local/share/dlib-data && sudo ./install.sh
```

To remove it again: `sudo ninja -C build uninstall`, then delete `/opt/howdy-venv` and
`/etc/howdy`.

## Configuration

In `/etc/howdy/config.ini`, section `[video]`:

| Key | Value used | Why |
|---|---|---|
| `recording_plugin` | `camss_ir` | selects this reader |
| `device_path` | `/dev/media0` | the CAMSS **media** device, not a video node. Find it with `for m in /dev/media*; do media-ctl -d $m -p \| grep -q qcom-camss && echo $m; done` |
| `camss_exposure` | `600` | manual exposure in lines (sensor control `exposure`, 0-1796 here). New key, read only by this reader |
| `camss_gain` | `8` | analogue gain index (sensor control `analogue_gain`, 0-24). New key |
| `dark_threshold` | `90` (default 60) | the strobe lights the face and leaves the background black, so about 65% of each frame is dark by design. With the default, Howdy drops these frames as "too dark" |

`certainty` stays at the default 3.5 (see the results in
[docs/face-unlock.md](../../docs/face-unlock.md)). `frame_width`, `frame_height` and
`device_format` are ignored by this reader: it always streams the sensor's full 644x604 GREY
mode.

The reader hardcodes this machine's pipeline at the top of `camss_ir_reader.py`: the sensor
entity `vd55g0 8-0010` and `msm_csiphy0 -> msm_csid1 -> msm_vfe1_rdi0 -> msm_vfe1_video0`. If
your sensor shows up under another name in `media-ctl -p`, change those constants.

## Permissions

Whoever runs Howdy needs the CAMSS media device, the video node and the sensor subdev. All
are `root:video`, mode 0660. polkit's authentication helper is setuid root, so that case
just works. swaylock authenticates as the locked user, so that user must be in the `video`
group, and `/etc/howdy/config.ini` and the models in `/etc/howdy/models/` must be readable by
them. Howdy's installed defaults were world-readable here.
