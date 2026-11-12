# Battery-life work into the repo

Status: done, merged 2026-11-12 (`f756b21`).

Task 1 of [resume-ready.md](../active/resume-ready.md): `sl7-power-mode` from `~/sl7/power/` and the
`arm_scmi` perf patch from `~/sl7-kernel/patches/local/0002-…`.

## Findings before starting

- `sl7-power-mode` is **not installed** on the machine: none of its files exist under
  `/usr/local/sbin`, `/etc/systemd/system` or `/etc/udev/rules.d`, the journal has no
  `sl7-power-mode` entries since 2026-11-02, and niri logs "error spawning
  /usr/local/sbin/sl7-power-mode: NotFound" at login. So the tool has never run as a service on
  the hardware. Mark it untested, like the patch.
- On the running kernel only `policy0` (CPUs 0-3) exists and `/sys/kernel/debug/opp/` has
  tables only for cpu0-3: a failed policy removes its OPPs, so the patch's premise (every NCC1
  and NCC2 OPP flagged turbo) can't be read back on this kernel.
- `qcom-battmgr-bat` has no `capacity` file; percentage comes from `energy_now/energy_full`.

## Steps

1. **Tool.** `tools/power/sl7-power-mode`: CPU parking only, generalized (any `Battery`
   supply, no fixed output or modes), then runs hooks from `/etc/sl7-power-mode.d/` with
   `battery` or `ac`. As a user (compositor autostart) it runs only the hooks.
2. **niri hook.** `tools/power/hooks/niri-refresh-rate`: finds the internal panel (`eDP-*`),
   keeps its resolution, picks the highest rate on AC and the one nearest 60 Hz on battery.
   As root it sets every running niri session as its owner.
3. **Units.** `systemd/sl7-power-mode.service`, `config/udev/90-sl7-power-mode.rules`, with SPDX
   headers and repo URLs.
4. **Docs.** `docs/power.md`: what it does and why, the measured findings, install and removal
   commands (the repo's style, no install scripts), what's already fine, open items. Parking is
   a workaround until the kernel fix lands. A row in `docs/known-issues.md`.
5. **Patch.** Rebuild it as a commit in a scratch clone (repo identity, date kept,
   `Assisted-by: LLM`), `format-patch --zero-commit` as `0006`, add to `series`, REUSE entry
   (GPL-2.0-only), the patches README and `docs/kernel-7.3.md`. Untested everywhere.
6. **Hashes.** In a `--shared` scratch clone of `~/sl7-kernel/linux-7.3.0`: check that the kit
   commits of the built tree minus the five `.orig` files give `c581ba6c`, that applying the old
   series to it gives `a7533b07`, then apply the new series in both orders for the new hash.
   Update `BASE.md`.
7. **Decisions.** One file each in `docs/decisions/`: the refresh rate as a hook, install as doc
   commands, what was left out.
8. **Checks.** scrub-check (and `--history`), `reuse lint`, shellcheck, py_compile, checkpatch.
   Test the tool against a fake sysfs in the scratchpad (`unshare -r`), never the live one.
9. Commit, report to the lead (including what the README needs).

Out of scope: README.md, PROGRESS.md, resume-ready.md, installing anything, kernel builds.
