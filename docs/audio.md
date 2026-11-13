# Audio

Audio on the Surface Laptop 7 needs four things the kernel package does not bring: Microsoft's
DSP firmware (in the initramfs), a topology file, UCM configuration, and on some installs a
WirePlumber rule. With them, the speakers, headphones, headset mic and internal mics work.

Status: set up 2026-09-11 on the 7.0 kernel (Debian 13 userspace, alsa-ucm-conf 1.2.14,
WirePlumber 0.5.8). On 7.3.0-sl7 (checked 2026-10-27), both DSPs start from the initramfs,
the card `X1E80100Romulus` registers, WirePlumber uses the HiFi profile with Headphones and
Speaker sinks, and the codec is in `CLS_AB_LOHIFI` mode. The author confirmed on 2026-11-13
that the speakers play on 7.3 (see [Speakers](#speakers)).

| Piece | Installed at | Needed because |
|---|---|---|
| ADSP and CDSP firmware | `/lib/firmware/qcom/x1e80100/microsoft/Romulus/` | the sound card lives on the ADSP. Microsoft-signed, from Windows; not in linux-firmware |
| [initramfs hook](../config/audio/initramfs-hook-qcom-romulus-firmware) | `/etc/initramfs-tools/hooks/qcom-romulus-firmware` | without the firmware in the initramfs, the ADSP never starts |
| Topology | `/lib/firmware/qcom/x1e80100/X1E80100-Romulus-tplg.bin` | the audio graph for this card; in linux-firmware, but newer than Debian 13's package |
| [UCM files](../config/audio/ucm2/) | `/usr/share/alsa/ucm2/` | alsa-ucm-conf before 1.2.15 has no profile for this machine; before 1.2.16 the headphones clip |
| [WirePlumber rule](../config/audio/wireplumber/51-force-hifi-profile.conf) | `~/.config/wireplumber/wireplumber.conf.d/` | stops WirePlumber from restoring the "pro-audio" profile, which bypasses UCM |

## 1. DSP firmware

The device tree asks for these files (the remoteproc nodes' `firmware-name`):

    qcom/x1e80100/microsoft/Romulus/qcadsp8380.mbn   ADSP (audio, battery manager)
    qcom/x1e80100/microsoft/Romulus/adsp_dtbs.elf
    qcom/x1e80100/microsoft/Romulus/qccdsp8380.mbn   CDSP (compute)
    qcom/x1e80100/microsoft/Romulus/cdsp_dtbs.elf

They are signed for Microsoft's hardware. The DSPs start only images signed for the device's
vendor, which is why linux-firmware keeps per-vendor directories, so its generic
`qcom/x1e80100/adsp.mbn` (for Qualcomm's reference boards) is not expected to work here (not
tried). linux-firmware has no Microsoft directory for X1E80100 (checked October 2026). This
repo does not ship the files. Get them from your own Windows install:

- [qcom-firmware-extract](https://tracker.debian.org/pkg/qcom-firmware-extract) (Debian and
  Ubuntu; script by Tobias Heider and contributors). Its device list includes "Microsoft
  Surface Laptop 7 (13.8 inch | 15 inch)" and maps it to `x1e80100/microsoft/Romulus`. It
  mounts the Windows partition read-only (BitLocker volumes through dislocker), takes the
  files from the Windows driver store, and installs them under
  `/lib/firmware/updates/qcom/x1e80100/microsoft/Romulus/`. See its
  [man page](https://dyn.manpages.debian.org/testing/qcom-firmware-extract/qcom-firmware-extract.8).
- By hand: mount the Windows partition read-only and search
  `Windows/System32/DriverStore/FileRepository/` for `qcadsp8380.mbn` and the other three
  names. Copy them to `/lib/firmware/qcom/x1e80100/microsoft/Romulus/`.

### Why the firmware must be in the initramfs

With `MODULES=most` (the Debian default), `qcom_q6v5_pas` probes from the initramfs, before
the root file system is mounted. If the firmware isn't there, the ADSP and CDSP boots fail
once with -2 (`ENOENT`) and are never retried. The ADSP stays offline, and the sound card
never registers. The ADSP also hosts the battery manager service that `qcom_battmgr` uses.

The hook [`initramfs-hook-qcom-romulus-firmware`](../config/audio/initramfs-hook-qcom-romulus-firmware)
copies the four files into every initramfs:

    sudo install -m 0755 config/audio/initramfs-hook-qcom-romulus-firmware \
        /etc/initramfs-tools/hooks/qcom-romulus-firmware
    sudo update-initramfs -u -k all
    lsinitramfs /boot/initrd.img-$(uname -r) | grep Romulus    # expect the four files

It reads the file names from the running device tree, falling back to the names above. It
finds the files under `/lib/firmware/updates/` (where qcom-firmware-extract puts them) as well
as `/lib/firmware/`, compressed or not. A missing file gives a warning, not a failed build.

To start the ADSP by hand without rebooting (a quick test after copying the firmware; check
that `remoteproc0/name` says `adsp`):

    echo start | sudo tee /sys/class/remoteproc/remoteproc0/state

Check with `cat /sys/class/remoteproc/remoteproc*/name /sys/class/remoteproc/remoteproc*/state`:
expect `adsp` and `cdsp`, both `running`.

The hook needs re-running only when you change the firmware. Kernel updates rebuild the
initramfs and run it automatically. It is in use on both the 7.0 and the 7.3 kernel here.

## 2. Topology

The ADSP's AudioReach driver (`q6apm`) loads `qcom/<driver name>/<card name>-tplg.bin`, which is
`qcom/x1e80100/X1E80100-Romulus-tplg.bin` here. It is not Microsoft firmware. It comes from
[linux-firmware](https://gitlab.com/kernel-firmware/linux-firmware/-/blob/main/qcom/x1e80100/X1E80100-Romulus-tplg.bin),
but Debian 13's `firmware-qcom-soc` (20250410) is too old to have it. Install a newer
linux-firmware package, or copy that one file to `/lib/firmware/qcom/x1e80100/`. This machine
uses a copy taken from linux-firmware by hand.

## 3. UCM

The UCM profile tells PipeWire which mixer controls make up "Speaker", "Headphones" and the
mics. The Surface Laptop 7 has the same codecs as the ThinkPad T14s Gen 6: two WSA8845
speaker amplifiers and a WCD9385 headset codec.

| alsa-ucm-conf | Surface Laptop 7 |
|---|---|
| 1.2.14 (April 2025; Debian 13) | No profile. Install the four files below |
| 1.2.15 (December 2025) | Matched by DMI to the T14s profile (commit c93b7c8). Headphones still use class-H mode, which clips bass at low volume. Install the four files below to fix that |
| 1.2.16 (June 2026) and later | Matched, with the class-AB headphone sequence (commit 3cf9df3). Nothing to install. Its boot sequence stops early, which is harmless so far (see [Boot sequence](#boot-sequence)) |

The files in [`config/audio/ucm2/`](../config/audio/ucm2/) are from alsa-ucm-conf, so they
keep its BSD-3-Clause license:

| File | What it is |
|---|---|
| `conf.d/x1e80100/SurfaceLaptop7.conf` | The card entry: LENOVO-T14s.conf pointing at Romulus-HiFi.conf, plus `RX HPH Mode = CLS_AB_LOHIFI` in the boot sequence, which also sets the WSA digital volumes under their real names (see [Boot sequence](#boot-sequence)) |
| `Qualcomm/x1e80100/Romulus-HiFi.conf` | T14s-HiFi.conf with the Headphones device using the two files below |
| `codecs/wcd938x/HeadphoneABEnableSeq.conf` | Unchanged copy of the 1.2.16 file: sets `RX HPH Mode` to `CLS_AB_LOHIFI` |
| `codecs/qcom-lpass/rx-macro/HeadphoneABEnableSeq.conf` | 1.2.16's rx-macro HeadphoneEnableSeq.conf under a new name. 1.2.14's version forces `CLS_H_ULP` after the codec sequence and turns the compander on, so it must not be included |

UCM first looks for `conf.d/<driver>/<card long name>.conf`, so the card entry must be
installed under the long name of your card. That name ends in a configuration code that
differs between models, so it is not hard-coded here. Install:

    cd config/audio/ucm2
    longname=$(awk '/X1E80100-Romulus$/ { getline; sub(/^ +/, ""); print; exit }' /proc/asound/cards)
    echo "$longname"     # MicrosoftCorporation-MicrosoftSurfaceLaptop7thEdition-...
    sudo install -m 0644 conf.d/x1e80100/SurfaceLaptop7.conf \
        "/usr/share/alsa/ucm2/conf.d/x1e80100/$longname.conf"
    sudo install -m 0644 Qualcomm/x1e80100/Romulus-HiFi.conf /usr/share/alsa/ucm2/Qualcomm/x1e80100/
    sudo install -m 0644 codecs/wcd938x/HeadphoneABEnableSeq.conf /usr/share/alsa/ucm2/codecs/wcd938x/
    sudo install -m 0644 codecs/qcom-lpass/rx-macro/HeadphoneABEnableSeq.conf \
        /usr/share/alsa/ucm2/codecs/qcom-lpass/rx-macro/
    systemctl --user restart wireplumber

Check: `alsaucm -c hw:0 list _devices/HiFi` lists Speaker, Headphones, Headset and Mic. With
headphones playing, `amixer -c0 cget name='RX HPH Mode'` shows `values=8` (`CLS_AB_LOHIFI`).
`tools/audio/ucm-boot-test check` (read-only) should end with "All 8 controls exist".

If you installed the card entry before 2026-11-12, install it again (the first
`sudo install` line above): the old one stops the boot sequence partway, as described below.

These files are not owned by any package, so an alsa-ucm-conf upgrade leaves them in place.
After upgrading to 1.2.16 or later, delete the card entry, `Romulus-HiFi.conf` and the
rx-macro file. The wcd938x file then belongs to the package.

The files were checked by loading them into a copy of the 1.2.14 tree with
`ALSA_CONFIG_UCM2` and comparing `alsaucm dump text` with the installed setup: identical.

### Boot sequence

A UCM card entry's `BootSequence` holds the mixer settings for a card that has no saved
state yet. `alsa-restore.service` runs it only when `/var/lib/alsa/asound.state` doesn't
exist, as on a fresh install, or no longer matches the card's controls, as after a kernel
that changes them. It then restores the saved state on top. Normal boots don't run it.

**The bug (found 2026-11-12).** The X1E80100 device tree gives the two WSA macros the control
name prefixes `WSA` and `WSA2` (`sound-name-prefix`; mainline's `hamoa.dtsi` has them too), so
this card's control is `WSA WSA_RX0 Digital Volume`. alsa-ucm-conf's
`codecs/qcom-lpass/wsa-macro/init.conf`, which the card entry used to include, writes
`WSA_RX0 Digital Volume`. That `cset` fails, and alsa-lib stops the whole boot sequence at
the first line that fails. The journal shows:

    alsa-lib main.c:828:(execute_sequence) unable to execute cset 'name='WSA_RX0 Digital Volume' 84'
    alsa-lib main.c:2476:(set_boot_user) Unable to execute boot sequence

alsa-lib runs the card entry's own lines first and the included files' lines after them, in
include order. So the headphone and mic gains and `RX HPH Mode` were set, and
`WSA_RX1 Digital Volume` and the rx-macro lines (`RX_RX0` and `RX_RX1 Digital Volume`) were
skipped. alsactl then fell back to its generic init ("Hardware is initialized using a
generic method"), which matches no control on this card.

It happened on four boots here: three on 7.0 before any state was saved, and the first boot of
`7.3.0-sl7`, whose controls no longer matched the saved state. Every other boot restored the
saved state, which holds the values the boot sequence would have set. That is why the bug
stayed hidden. Nothing was audibly wrong: the skipped lines set what the kernel already has
after probe (0 dB on both RX paths; 0 dB on the WSA paths, or -3 dB (81) under the speaker
cap described in [Speakers](#speakers)). But any line after the failing one is skipped.

**The fix.** The card entry now sets `WSA WSA_RX0 Digital Volume` and
`WSA WSA_RX1 Digital Volume` to 81 in its own boot sequence, and no longer includes
`wsa-macro/init.conf`. 81 is -3 dB, the most the kernel's speaker cap allows (range 0-81). On
a kernel without the cap it is 3 dB below the default, so it never raises a limit. Why the
fix lives there and why 81:
[ucm-wsa-boot-in-card-entry](decisions/2026-11-12-ucm-wsa-boot-in-card-entry.md),
[ucm-wsa-digital-volume-81](decisions/2026-11-12-ucm-wsa-digital-volume-81.md).

**Upstream.** alsa-ucm-conf has the same bug (1.2.14, 1.2.15, 1.2.16 and master, checked
2026-11-12). `Qualcomm/x1e80100/LENOVO-T14s.conf` includes the unprefixed
`wsa-macro/init.conf`. It is the profile for the T14s, for this laptop since 1.2.15, and for
several other two-speaker X1E laptops. `MICROSOFT-Surface-Pro-11.conf`,
`MICROSOFT-Surface-Pro-12in.conf` and `TUXEDO-Elite-14.conf` include it too. In master that
file also turns the WSA compander off, and the rx-macro file turns the RX compander off, so
those lines are skipped as well. Both companders are off after probe, so this is harmless so
far too. A prefixed `wsa-macro/two-speakers/init.conf` already exists upstream, but only a
Glymur laptop uses it. Including it instead is a one-line fix per file. Nobody has reported
it upstream yet.

**Test.** [`tools/audio/ucm-boot-test`](../tools/audio/ucm-boot-test):

- `tools/audio/ucm-boot-test check [FILE]` is read-only. It lists the boot sequence of the
  installed card entry (or FILE) and the files it includes, in run order, and checks each
  control against the live card. A control that doesn't exist shows as `MISSING`, and the
  lines after it as `not run`. With the fixed entry it ends with "All 8 controls exist". Pass
  `/usr/share/alsa/ucm2/Qualcomm/x1e80100/LENOVO-T14s.conf` to see the upstream profile's
  stop.
- `tools/audio/ucm-boot-test run` runs the boot sequence for real. Run it as your user from
  the desktop session; it uses sudo where needed. It first saves the mixer
  (`alsactl store`) and a copy of `/var/lib/alsa`, and stops PipeWire and WirePlumber, so
  nothing plays and no volume gets saved. Then it sets each control of the boot sequence to a
  low value (integers to their minimum; enums and switches to another value) and runs
  `alsactl -f <missing file> restore`, the no-state path a fresh install takes. It passes
  when alsa-lib logs nothing and every control has the value the sequence sets. Afterwards
  it restores the mixer and `/var/lib/alsa`, checks both against the backup, and starts
  PipeWire and WirePlumber again. It also does this on Ctrl-C or an error. Audio apps lose
  their sound until then. The report and backups are in
  `~/.local/state/sl7/ucm-boot-<time>/`.

  A pass shows `RESULT: PASS, the boot sequence ran to the end and set all 8 controls`,
  then `mixer: restored, identical to the backup` and `/var/lib/alsa: restored, identical to
  the backup`. The test doesn't move the saved state: it points alsactl at a file that
  doesn't exist.

Status: the fix passes `check` and parses in a copy of the 1.2.14 tree (`alsaucm dump text`
is unchanged); `run` hasn't been run on the hardware yet.

## 4. WirePlumber: keep the HiFi profile

If the card first appeared before the UCM files were installed, WirePlumber saved the
"pro-audio" profile and restores it at every login. Pro-audio bypasses UCM, so the codec never
gets its enable sequence, and the headphones play loud noise. `wpctl status` then shows sinks
named "Pro" or "Pro 1".

[`51-force-hifi-profile.conf`](../config/audio/wireplumber/51-force-hifi-profile.conf) pins
the card (`alsa_card.platform-sound`) to HiFi and turns off automatic profile selection
(WirePlumber 0.5 or later):

    install -D -m 0644 config/audio/wireplumber/51-force-hifi-profile.conf \
        ~/.config/wireplumber/wireplumber.conf.d/51-force-hifi-profile.conf
    systemctl --user restart wireplumber

Also check `~/.local/state/wireplumber/default-profile`. Its `alsa_card.platform-sound=` line
should say `HiFi`, or be deleted.

## Speakers

The speaker volume slider (UCM mixer element `Speakers`) drives both WSA8845 `PA Volume`
controls directly. There is no speaker protection on Linux for these amplifiers.

- On the 7.0 kernel the controls ran 0 to 31 with nothing limiting them, so 100% meant full
  amplifier gain. Keep the volume moderate on kernels like that.
- The Ubuntu 7.3.0-9.9 source this repo's kernel is built from caps them in
  `sound/soc/qcom/x1e80100.c` "until we have active speaker protection": `PA Volume` at 6
  (0 dB) and the WSA digital volume at -3 dB. Mainline 7.0-rc4 has no such cap; mainline
  added the same cap later (`0a5ee0e520ef`, April 2026).
- alsa-ucm-conf's speaker sequence (1.2.14 and current upstream) writes `PA Volume` 12, above
  that cap. This doesn't stop the sequence, so the right amplifier's settings that follow it
  are applied (checked 2026-11-12): alsa-lib parses a `cset` integer against the control's
  reported range, which the cap lowers to 0-6, so UCM writes 6 and the kernel never sees 12.
  On the tested machine every `SpkrRight` switch the sequence sets is on, including
  `PBR Switch`, which no other UCM sequence sets, and no journal has a `PA Volume` or
  `cset` error from it.
- Listening on 7.3: the author confirmed on 2026-11-13 that the speakers play. To check each
  channel on its own, at low volume: `speaker-test -c 2 -t wav -D default`.

To keep the speakers off entirely, a WirePlumber rule that matches
`node.name = "alsa_output.platform-sound.HiFi__Speaker__sink"` and sets `node.disabled = true`
works. It was used here from September to October 2026.

## Credits

- alsa-ucm-conf ([alsa-project/alsa-ucm-conf](https://github.com/alsa-project/alsa-ucm-conf)):
  the X1E80100 and T14s profiles by Srinivas Kandagatla, the Surface Laptop 7 DMI match
  (c93b7c8, by quic-kdybcio), and the class-AB headphone sequence and compander fix by Val
  Packett (3cf9df3, 8e6acab; upstream issue #670).
- linux-firmware: the `X1E80100-Romulus` AudioReach topology.
- qcom-firmware-extract: Tobias Heider and contributors.
