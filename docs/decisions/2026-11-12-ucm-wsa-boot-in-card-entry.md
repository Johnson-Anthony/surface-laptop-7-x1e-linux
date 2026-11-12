# UCM: set the WSA boot volumes in the card entry

2026-11-12

**Context.** alsa-ucm-conf's `codecs/qcom-lpass/wsa-macro/init.conf` writes
`WSA_RX0 Digital Volume`, but on X1E80100 the device tree prefixes the WSA macro's controls
with `WSA`. The `cset` fails and alsa-lib skips the rest of the boot sequence
(see [audio.md](../audio.md#boot-sequence)). The options were:

1. Set the prefixed controls in our card entry, `SurfaceLaptop7.conf`, and drop the include.
2. Ship a copy of upstream's prefixed `wsa-macro/two-speakers/init.conf` and include it.
3. Override the distribution's `wsa-macro/init.conf` with prefixed names.
4. Choose the file with an `If` on `ControlExists`.

**Decision.** Option 1: two `cset` lines in the card entry's own `BootSequence`, and no
`wsa-macro/init.conf` include. Only the names change: the compander lines that upstream's
newer init files carry are left out.

**Why.**

- The card entry is already our file, installed under the card's long name and owned by no
  package, so the fix needs no new install step. Users only reinstall that one file.
- Option 2 puts a file in `/usr/share/alsa/ucm2` at a path a later alsa-ucm-conf package will
  ship (the two-speakers file is in master, not in 1.2.16), so dpkg would overwrite it
  without notice.
- Option 3 breaks every other card that includes that file (the X13s, the SM8550 HDK, the
  QCM6490 IDP and others): their SoCs don't prefix the WSA controls (sc8280xp, sm8550,
  sm8650 and kodiak have no `sound-name-prefix` there). A package upgrade would also undo
  it.
- Option 4 handles a device tree without the prefix. None exists for X1E80100: the prefix is
  in the SoC `.dtsi`, in mainline and in every kernel this repo uses.
- The compander lines: with the 1.2.14 files this setup uses, `Wsa1SpeakerEnableSeq.conf`
  turns the WSA compander on each time the speakers start, so a boot-time "off" would change
  nothing. The kernel starts with both companders off anyway.

The upstream fix is different on purpose: there the right change is for `LENOVO-T14s.conf`
and the other two-speaker X1E profiles to include the existing prefixed file.
