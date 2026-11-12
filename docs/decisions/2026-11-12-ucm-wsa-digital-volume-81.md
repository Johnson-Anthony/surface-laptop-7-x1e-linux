# UCM: boot value 81 for the WSA digital volumes

2026-11-12

**Context.** alsa-ucm-conf sets `WSA_RX0`/`WSA_RX1 Digital Volume` to 84 at boot, which is
0 dB (the control runs from -84 dB in 1 dB steps). The 7.3 kernel this repo builds caps both
controls at 81 (-3 dB) "until we have active speaker protection" (`snd_soc_limit_volume` in
`sound/soc/qcom/x1e80100.c`), and mainline later added the same cap (`0a5ee0e520ef`, April
2026). Kernels without the cap, such as 7.0-rc4, allow up to 124 (+40 dB) and start at 84.

**Decision.** The card entry writes 81.

**Why.**

- On a capped kernel, 81 is exactly the cap. 84 would work only because alsa-lib clamps a
  `cset` integer to the range the control reports; the kernel itself rejects values above the
  cap with -EINVAL.
- On a kernel without the cap, 81 keeps the same -3 dB headroom the cap was added for, rather
  than 0 dB. These speakers have no speaker protection on Linux, so the lower value is the safe
  one. It is 3 dB below the kernel's default, so it never raises a limit.
- The speaker volume slider drives the `PA Volume` controls, and no UCM device uses these as
  its volume, so the choice costs at most 3 dB of headroom, and only on uncapped kernels.
