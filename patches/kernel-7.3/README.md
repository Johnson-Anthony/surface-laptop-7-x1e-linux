# Kernel 7.3 patches

Seven patches on top of Ubuntu's 7.3.0-9.9 kernel source and the
[ItsLucas Surface Laptop 7 kit](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel).
[BASE.md](BASE.md) gives the exact base and the full build steps;
[docs/kernel-7.3.md](../../docs/kernel-7.3.md) covers the kernel as a whole.

| Directory | Patches | What for |
|---|---|---|
| `.` | 0001-0005 ([series](series)) | Four changes to the kit's spi-hid driver, one to the device tree |
| `build/` | 0001-0002 ([series](build/series)) | Packaging: the release name and module signing. Only needed when you build from Ubuntu's `linux-source` |

Apply both sets on the base tree with `git am`:

```sh
git am /path/to/repo/patches/kernel-7.3/*.patch
git am /path/to/repo/patches/kernel-7.3/build/*.patch
```

The two sets touch different files, so either order works. Both orders were checked: each
produces exactly the source tree of the kernel tested here.

## The patches

| Patch | Files | What it does |
|---|---|---|
| 0001 `HID: spi-hid: recover when a reset cuts off GET_FEATURE` | `drivers/hid/spi-hid/spi-hid-core.c` | A device-initiated reset that arrived while a GET_FEATURE was pending was taken as that request's (zero-filled) answer, so the kit's reset recovery (kit patch 0008) never ran and iptsd never re-applied its mode. Now GET_FEATURE runs the same recovery. |
| 0002 `HID: spi-hid: mask the IRQ across in-driver reset pulses and power cycles` | same | On this device tree the `reset` pinctrl state also cuts the touch rail, and the retry pulses ran with the IRQ armed, so the IRQ thread read headers from an unpowered device. The IRQ thread's storm mask was dropped only by `spi_hid_stop()` (kit patch 0021), so the power cycle (kit patch 0011) and the requests after it ran with the line masked and timed out. One helper now pulses reset with the IRQ masked, and every path drops a storm mask once. |
| 0003 `HID: spi-hid: end the IRQ loop after the error handler gives up` | same | When the error handler gives up it powers the device off but leaves the IRQ armed. An unpowered device holding the level-triggered line could keep the threaded IRQ firing until the next suspend. These are now counted as errors, so the existing storm mask stops the loop. |
| 0004 `arm64: dts: qcom: x1e80100-romulus: keep runtime cpuidle out of SS3` | `arch/arm64/boot/dts/qcom/x1e80100-microsoft-romulus.dtsi` | Raises `domain_ss3` min-residency to 10 s. Suspend still uses the system idle state; runtime cpuidle never picks it. Other X1E laptops hung when it was entered at runtime. |
| 0005 `HID: spi-hid: power up beside resume, not inside it` | `drivers/hid/spi-hid/spi-hid-core.{c,h}` | The touchpad powered up inside its PM resume callback, which sleeps about 2.3 s (supply delay, reset pulse, 2 s firmware start), so every system resume waited for it. Both pads now power up on `system_unbound_wq`. Enumeration still waits for thaw. Sets `MODULE_VERSION` to `sl7.20261026.1`. |
| build/0001 `Makefile: drop -rc6 so the release is 7.3.0-sl7` | `Makefile` | Ubuntu 7.3.0-9.9 is 7.3-rc6 but versioned 7.3.0. The kit's CI also builds with an empty `EXTRAVERSION`. |
| build/0002 `kbuild: sign modules without Ubuntu's debian/scripts/sign-module gate` | `scripts/Makefile.modinst` | Ubuntu signs a module only when `debian/scripts/sign-module` exists. `linux-source` does not ship `debian/`, so `bindeb-pkg` printed `SIGN` for every module and signed none, and the first module load tainted the kernel (`E`). This restores the upstream rule. |

0001-0003 came out of a code review of the kit's spi-hid driver during the touchpad work
(see [docs/touchpad.md](../../docs/touchpad.md)). They fix code that exists only in the kit,
so they carry no `Fixes:` tags: there is no upstream commit to point at.

## What was tested

All seven are in the kernel this machine runs daily (`7.3.0-9.9+sl7.3`, a Surface Laptop 7
13.8", X1E80100, booting the romulus15 device tree). Built natively with GCC 14.2.

| Patch | Tested | Not tested |
|---|---|---|
| 0001-0003 | The touchpad and touchscreen enumerate and work on every boot since 2026-10-26, and across deep suspend and resume. | The recovery paths themselves. No device-initiated reset, power cycle or storm mask shows up in the logs yet (`device_initiated_reset_count` 0). |
| 0004 | Deep suspend reaches CX collapse, AOSS sleep and DDR self-refresh (263-276 mW over 2-5 h tests). At runtime the system idle state is never entered: in debugfs, `power-domain-system` usage stays 0 until the first suspend and then equals its suspend count. | Whether the hang seen on other X1E laptops would happen on this one without it. |
| 0005 | One deep suspend and resume on this build: `PM: suspend exit` came 2.0 s before the touchpad's power-on message. On the previous build it came 0.7 s after it. Both pads came back. | Many cycles; lid close with the touchscreen glitching (see the known issues in [docs/kernel-7.3.md](../../docs/kernel-7.3.md)). |
| build/0001 | `uname -r` is `7.3.0-sl7`. | |
| build/0002 | Every module in the package is signed with the build's key (`modinfo -F signer`: "Build time autogenerated kernel key"); the kernel no longer taints `E`. | Secure Boot or `module.sig_enforce=1`. |

## Signed-off-by and Assisted-by

The patches have no `Signed-off-by:` line, on purpose. They were written with help from an AI
coding assistant (Claude Opus 5.5, model `claude-opus-5-5`, in Claude Code). The kernel's
[`Documentation/process/coding-assistants.rst`](https://docs.kernel.org/process/coding-assistants.html)
says an AI must not add `Signed-off-by`, because only a human can certify the Developer
Certificate of Origin. The human who submits a patch adds it, after reviewing the code and
taking responsibility for it. For mailing-list submission that also means a real address in
`From:` and `Signed-off-by:`: the GitHub noreply address in these files cannot receive review
mail. For example, with `user.name` and `user.email` set to the submitter:

```sh
git rebase --exec 'git commit --amend --no-edit --reset-author --signoff' <base>
```

The same document asks for an `Assisted-by:` tag. In the 7.3 tree these patches apply to, its
format is `Assisted-by: LLM [TOOL1] [TOOL2]`, where the tools are optional analysis tools such
as coccinelle or sparse (none were used). So each patch ends in `Assisted-by: LLM`. The format
has changed between kernel releases; check the version of the document in the tree you submit
to and adjust the tag.

None of these patches has been submitted anywhere yet. 0001-0003 and 0005 change the kit's
spi-hid driver, which is not upstream, so they would go to the kit first. 0004 changes an
upstream file and would go to linux-arm-msm after a rebase on mainline. The build/ patches are
for this packaging route only.

## checkpatch

`scripts/checkpatch.pl --strict --no-tree` from the 7.3 tree reports, for every patch, only
`Missing Signed-off-by: line(s)`, which is expected (see above): 0 warnings, 0 checks.
checkpatch learned the `Assisted-by:` tag in 7.1; 7.0 and older call it a non-standard
signature.

## Licenses

Each patch is under the license of the file it changes:

| Patch | License |
|---|---|
| 0001, 0002, 0003, 0005 (`drivers/hid/spi-hid/`) | GPL-2.0-only |
| 0004 (`x1e80100-microsoft-romulus.dtsi`) | BSD-3-Clause |
| build/0001 (`Makefile`), build/0002 (`scripts/Makefile.modinst`) | GPL-2.0-only |
