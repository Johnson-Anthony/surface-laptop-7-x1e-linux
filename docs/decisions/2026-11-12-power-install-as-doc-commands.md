# sl7-power-mode installs from commands in the docs, not install scripts

2026-11-12

**Context.** The working copy had `install` and `uninstall` scripts. Besides installing the
tool, its unit and its udev rule, they changed this machine's services: Docker and containerd
to socket activation, and ModemManager off.

**Decision.** The repo ships no install or uninstall scripts for it. `docs/power.md` lists the
`install`, `systemctl` and `udevadm` commands, and the removal commands, starting with
`sl7-power-mode full` so that no core stays offline.

**Why.**

- It is how the repo's other tools install (the touchpad services in `docs/touchpad.md`, the
  sleep hook in `docs/deep-sleep.md`): each step visible, nothing hidden in a script that runs
  as root.
- Without the service changes, which don't belong in the repo (see
  [the decision on what was left out](2026-11-12-power-left-out.md)), the scripts would be
  seven commands each, and a script would also have to decide whether to install the optional
  niri hook.
