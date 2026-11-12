# Spec

## What it is

The public home of the work to run Linux on a Microsoft Surface Laptop 7 (Snapdragon X): kernel
patches, device-tree overlays, tools, configuration, docs and the measurements behind them. It is
for other Surface Laptop 7 owners and Linux-on-Arm developers, and it is a portfolio piece for
the author's resume.

The working copies stay in the author's `~/sl7*` folders. This repo holds curated, generalized
and scrubbed copies of them, never whole folders.

## Done for a first version ("resume ready")

1. **Current:** everything finished in the working folders is in the repo, up to and including
   the 2026-11-03 battery-life work (`sl7-power-mode` and the `arm_scmi` perf patch).
2. **Accurate:** the README status table and findings match what has been tested on the hardware.
   Anything untested says so.
3. **Findable:** GitHub description, topics and a CI badge are in place.
4. **Public:** the repo is public. Only the author makes this call.
5. **Upstream:** at least one patch has been sent upstream, with a public link to it. Only the
   author sends patches.

## Constraints

- **Privacy.** No personal data: serial numbers, UUIDs, MAC addresses, the author's personal
  email, home-directory paths. `tools/dev/scrub-check` enforces this in the git hooks and CI; the
  real private values are in a denylist outside the repo.
- **Nothing that can't be redistributed.** No firmware, Windows/Qualcomm/Microsoft files, IR
  camera frames, kernel signing keys, raw dmesg or prebuilt kernel packages.
- **Licensing** follows REUSE: scripts MIT, kernel patches the license of the code they change,
  device-tree overlays BSD-3-Clause, docs CC BY 4.0.
- **Kernel patches** carry `Assisted-by: LLM` and no `Signed-off-by`; only the author adds that,
  when submitting. They must pass checkpatch from v7.3.
- **Commits** use the noreply GitHub identity set in the repo's local git config.
- **Hardware.** The author runs every hardware test: installing kernels, changing GRUB, reboots,
  suspends and cold boots. Agents prepare and explain the test, then read the results.
- **Machine limits.** 15 GB RAM and no swap: at most one kernel build at a time, and none while
  other heavy builds run.

## Not wanted

- Copies of whole working folders, or settings and services specific to the author's machine.
- Claims that something works before it has been tested on the hardware.
