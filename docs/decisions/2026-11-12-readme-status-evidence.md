# What counts as evidence for a README status row

2026-11-12

**Context.** The README refresh checked three claims against this machine's journal and sysfs
instead of new hardware tests: the touchpad cold-boot fix, the right-speaker settings and face
unlock on 7.3. Logs and mixer state show different things, and some of them stop short of the
claim.

**Decision.** A row says something works only when the logs show it doing its job, and it
says what kind of check backs it:

- **Touchpad:** "works" because every 7.3 boot logged touch input (IRQs rising, or the
  compositor's tap and hold events). The cold-boot fix stays "not proven": the count of good
  cold boots (6) is still below the test plan's 8.
- **Speakers:** the right-amplifier question is closed by the mixer state and alsa-lib's
  source, but nothing shows sound coming out on 7.3, so the row no longer says the speakers
  work. It says they haven't been listened to yet. The row in `known-issues.md` is gone,
  because the cause it guessed at turned out not to happen; the listening test is in
  `audio.md`.
- **Face unlock:** the row gives the journal's median approval time and count on 7.3. The
  timeouts are counted in `known-issues.md`, but not blamed on camera stalls, since a timeout
  with no face in view looks the same.

**Why.** The spec's "accurate" goal is that the status table matches what was tested on the
hardware, and that anything untested says so. Saying which check backs a row lets the author
see what is left to test by hand. It also keeps a log-based check from reading as a hands-on
one.
