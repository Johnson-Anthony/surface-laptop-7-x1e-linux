# UCM boot sequence stops at `WSA_RX0 Digital Volume`

Status: steps 1-5 done 2026-11-12; waiting for the author's `ucm-boot-test run` (task 6 of
[resume-ready.md](resume-ready.md)).

## Findings before starting

- Four boots in the journals logged `unable to execute cset 'name='WSA_RX0 Digital Volume' 84'`
  and `Unable to execute boot sequence` from `alsa-restore.service`: three on 7.0 (2026-09-14,
  2026-09-18 twice), each with "No state is present for card", and the first boot of
  `7.3.0-sl7` (2026-10-25), where a state file existed but no longer matched the card.
- The SoC device tree gives the two WSA macros the name prefixes `WSA` and `WSA2`
  (`sound-name-prefix`, also in mainline's `hamoa.dtsi`), so the card has
  `WSA WSA_RX0 Digital Volume`, range 0-81 under the -3 dB cap. `wsa-macro/init.conf` uses the
  unprefixed name.
- alsa-lib appends included `BootSequence` items after the card file's own, and stops the
  whole sequence at the first failing `cset`. So the card entry's own four lines run, and
  `WSA_RX1`, `RX_RX0` and `RX_RX1 Digital Volume` are skipped. alsactl then falls back to its
  generic init, which matches no control on this card.
- alsactl runs the boot sequence only when there is no state file, or the state no longer
  matches the card's controls, and then restores the state on top. Normal boots on this
  machine never run it, so the saved state hides the bug.
- The skipped lines set what the kernel already has after probe (0 dB on RX, the 81 clamp on
  WSA). So nothing is audible today; the error and the stop are real, and anything added after
  that line would be skipped too.
- Upstream alsa-ucm-conf has the same bug (master, checked 2026-11-12): `LENOVO-T14s.conf`
  (which matches the Surface Laptop 7 by DMI since 1.2.15), both Surface Pro files and
  `TUXEDO-Elite-14.conf` include the unprefixed `wsa-macro/init.conf`. A prefixed
  `wsa-macro/two-speakers/init.conf` exists upstream, but only a Glymur laptop uses it. No
  upstream issue or PR reports it.

## Steps

1. **Fix** `config/audio/ucm2/conf.d/x1e80100/SurfaceLaptop7.conf`: set
   `WSA WSA_RX0/RX1 Digital Volume` to 81 in its own `BootSequence` and drop the
   `wsa-macro/init.conf` include. Keep the rx-macro include (its names have no prefix).
2. **Test tool** `tools/audio/ucm-boot-test`: `check` (read-only) lists the effective boot
   sequence and checks each control and value against the live card; `run` (the author)
   backs up the mixer and `/var/lib/alsa`, stops PipeWire and WirePlumber, sets the boot
   controls to low sentinel values, runs alsactl's no-state path, checks the log and the
   values, then restores everything and compares.
3. **Docs**: `docs/audio.md` (the bug, the fix, how to test, reinstall note, upstream status),
   a row in `docs/known-issues.md`.
4. **Decisions**: where the fix lives; the value 81.
5. Verify: `check` against the live card, an `alsaucm` parse of the new file in a copy of the
   installed tree, and the checks from `CLAUDE.md`. Commit, report to the lead.

## Verification so far

- `ucm-boot-test check`: the installed (old) entry shows `MISSING` at `WSA_RX0 Digital Volume`
  and three lines `not run`, matching the journals; the repo's entry passes with 8 controls.
  Upstream master's T14s profile stops at the same line and skips 8; with its include
  switched to `wsa-macro/two-speakers/init.conf` it passes with 11.
- The new card entry parses in a copy of the installed tree (`ALSA_CONFIG_UCM2`), and
  `alsaucm dump text` is unchanged; a deliberately broken copy fails, so the copy was used.
- `ucm-boot-test run` against mock `amixer`, `alsactl`, `sudo` and `systemctl` (scratch
  `/var/lib`): PASS case, FAIL case (exit 1), and Ctrl-C during the boot sequence all restore
  the mixer and `/var/lib/alsa` and restart the audio units. The mock run caught one
  ordering bug in the restore, fixed before commit.

## Author's test

Reinstall the card entry, then `tools/audio/ucm-boot-test run`; see `docs/audio.md`.
