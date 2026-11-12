# Face unlock with Howdy

With the [IR camera](ir-camera.md) working, [Howdy](https://github.com/boltgolt/howdy) gives
Windows Hello-style face unlock. On this machine it unlocks polkit prompts (so also the
Bitwarden desktop app's "unlock with system authentication") and the swaylock lock screen,
in about 1 s. Every prompt falls back to the password if no face matches.

Tested on a Surface Laptop 7 13.8" (model 2036) with the 7.0.0-rc4 and 7.3.0-sl7 kernels, on
a Debian-based system (Parrot OS 7). It was set up on 2026-10-25 on 7.0, where the timings
below were measured. On 7.3, in daily use from 2026-10-25 to 2026-11-12, the journal has 46
approvals (27 swaylock, 19 polkit), with a median of 1.0 s from the attempt starting and 42
within 2 s. 15 more attempts timed out and 1 couldn't open the camera; those fell back to the
password. LightDM was deliberately left alone, and sudo wasn't set up.

Howdy compares face encodings. It has no liveness check beyond what an IR image gives, and
[its own README](https://github.com/boltgolt/howdy#a-note-on-security) says it is not as
secure as a password. Treat it as a convenience.

## How it fits together

```
PAM (polkit-1, swaylock)
  -> pam_howdy.so            "sufficient": a match ends the auth stack, anything else falls through
    -> Howdy compare.py      dlib face detection and recognition
      -> camss_ir reader     media links, manual exposure, strobe on, v4l2-ctl pipe
        -> CAMSS raw node    vd55g0 -> csiphy0 -> csid1 -> vfe1_rdi0
```

Howdy's stock readers use OpenCV or ffmpeg on a V4L2 node. That doesn't work with CAMSS:
the raw node streams nothing until the media links and pad formats are set, and the IR LED
fires only when the sensor's strobe is enabled. So
[patches/howdy/](../patches/howdy/README.md) adds a `camss_ir` reader. It sets up the
pipeline, uses manual exposure (600 lines, gain 8) with the strobe on, reads GREY frames
from a `v4l2-ctl` pipe, and restarts once if the stream stalls. If Howdy dies, the kernel
sends `v4l2-ctl` SIGTERM (`PR_SET_PDEATHSIG`), which stops the stream and with it the LED.

## Setup

1. Get the camera working: [ir-camera.md](ir-camera.md). `tools/ir-camera/check-ir` should
   capture frames.
2. Build and install Howdy with the patches: [patches/howdy/README.md](../patches/howdy/README.md).
3. Configure `/etc/howdy/config.ini`, section `[video]`:

   ```ini
   device_path = /dev/media0       ; the qcom-camss media device
   recording_plugin = camss_ir
   camss_exposure = 600
   camss_gain = 8
   dark_threshold = 90             ; default 60 drops the strobe-lit frames as too dark
   ```

   The keys are explained in [patches/howdy/README.md](../patches/howdy/README.md#configuration).
4. Enrol your face. Add several models under different conditions: normal distance, close
   up, with and without glasses, different light. Each `add` takes a label.

   ```sh
   sudo howdy -U "$USER" add
   sudo howdy -U "$USER" list
   ```

   `howdy test` shows the frames in an OpenCV window, which `opencv-python-headless` can't
   open.
5. Add Howdy to the PAM services you want (below), and test each one with
   [pamtester](https://pamtester.sourceforge.net/) before relying on it:

   ```sh
   pamtester polkit-1 "$USER" authenticate
   pamtester swaylock "$USER" authenticate
   ```

## Results

| Models | Best match distance | Detection | Result |
|---|---|---|---|
| 1 | 0.41 | | rejected: Howdy's cut-off is 0.35 (`certainty = 3.5`) |
| 3 | min 0.23, median 0.31 | a face in 75 of 76 frames | accepted, `certainty` left at the default |

With three models, `pamtester polkit-1 <user> authenticate` printed "Identified face as
<user>" in 1.0 to 1.3 s. Add models instead of raising `certainty`.

## PAM

### polkit (and Bitwarden)

Debian's polkit ships its PAM file as `/usr/lib/pam.d/polkit-1`. A file with the same name
in `/etc/pam.d/` overrides it **as a whole**, so the override must repeat the vendor lines.
[config/pam/polkit-1](../config/pam/polkit-1) is the vendor file plus one line at the top:

```
auth       sufficient   /usr/local/lib/security/pam_howdy.so
```

Compare it with your `/usr/lib/pam.d/polkit-1`, then install it as `/etc/pam.d/polkit-1`.
Every polkit prompt then tries the face first. That includes the Bitwarden desktop app's
system-authentication unlock, which goes through polkit. polkit's authentication helper is
setuid root, so permissions aren't an issue. To undo, delete `/etc/pam.d/polkit-1`.

### swaylock

[config/pam/swaylock](../config/pam/swaylock) puts the same `pam_howdy` line before
`auth include login`. Install it as `/etc/pam.d/swaylock`, after saving the original. On
Debian this file is a dpkg conffile, so keep the local version when an upgrade asks.

On the lock screen, press Enter with an empty password and look at the screen. If no face
matches within Howdy's timeout (`timeout = 4` s), type the password as usual.

swaylock authenticates as the locked user, not as root. That user must be in the `video`
group, and must be able to read `/etc/howdy/config.ini` and `/etc/howdy/models/`. Howdy's
installed defaults were world-readable here. That also means every local user can read the
face encodings. Decide whether that is acceptable on your machine.

To bind locking to a key, use the same swaylock command as your idle locker. In niri, for
example: `Mod+Alt+L { spawn "swaylock" "-f"; }`.

### Login screen: left alone

LightDM was not changed on purpose. The login keyring (gnome-keyring) is unlocked with the
login password through `pam_gnome_keyring`. A face login gives PAM no password, so the
keyring would stay locked, and every app that uses it would ask for the password again.

## Known issues

- **Lid check does nothing.** `abort_if_lid_closed` reads `/proc/acpi/button/lid/*/state`,
  which doesn't exist on a device-tree boot. Each attempt logs
  `pam_howdy: Failed to read files from glob: 3`, and Howdy carries on. So with the lid
  closed it can't skip the camera, and should wait out its 4 s timeout before the password
  prompt (not tested). Set `abort_if_lid_closed = false` to silence the log line.
- **Stream stalls.** See [ir-camera.md](ir-camera.md#known-issues). The reader restarts once
  after 1.5 s without a frame. If that stalls too, the attempt fails and PAM asks for the
  password.
- Not systematically tested right after resume from deep sleep.

## Undo

```sh
sudo rm /etc/pam.d/polkit-1                      # back to /usr/lib/pam.d/polkit-1
sudo cp /etc/pam.d/swaylock.orig /etc/pam.d/swaylock   # wherever you saved the original
sudo ninja -C build uninstall                    # in the Howdy build tree
sudo rm -r /opt/howdy-venv /etc/howdy
```

## Credits

- [boltgolt/howdy](https://github.com/boltgolt/howdy) and its contributors.
- [davisking/dlib](https://github.com/davisking/dlib) and the
  [dlib models](https://github.com/davisking/dlib-models) Howdy uses.
- [sppidy/facelock](https://github.com/sppidy/facelock), a CAMSS-aware Howdy-like tool and
  an alternative to this setup (not tried here).
