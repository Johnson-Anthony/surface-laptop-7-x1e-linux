# Kernel +sl7.4: the arm_scmi fix in a built kernel

Status: in progress.

Task 2 of [resume-ready.md](resume-ready.md): build `7.3.0-sl7` as `7.3.0-9.9+sl7.4`, which is
the installed `+sl7.3` plus patch 0006, for the author to install and test. Then record the
results.

## Findings before starting

- The build tree (`~/sl7-kernel/linux-7.3.0-sl7`, branch `sl7`) is at `+sl7.3`: its tree is
  `a1405a3b`, which is `a7533b07` plus the five `.orig` files that `BASE.md` describes.
  Its `.config` is byte-identical to `config/kernel/config-7.3.0-sl7`, and
  `certs/signing_key.pem` is the key that signed `+sl7.3` and the out-of-tree modules.
- 0006 changes only `drivers/firmware/arm_scmi/perf.c`, which is built in
  (`CONFIG_ARM_SCMI_PROTOCOL=y`). So the whole fix is in the kernel image.
- `+sl7.4` keeps the release name `7.3.0-sl7`, so installing its packages **replaces**
  `+sl7.3` (same package names, same `/boot/vmlinuz-7.3.0-sl7`, same `/lib/modules`). The
  existing GRUB entries can't tell them apart.
- `Fixes:` target: `a897575e79d7` ("firmware: arm_scmi: Add support for marking certain
  frequencies as turbo", v6.9) added `data.turbo = freq > dom->sustained_freq_khz * 1000`.
  The only later change to that line, `ad28fc31dd70` ("Fix up turbo frequencies selection"),
  fixed its 32-bit truncation and itself carries `Fixes: a897575e79d7`.

## Steps

1. **Fixes tag.** Add `Fixes: a897575e79d7 (...)` to 0006, above `Assisted-by:`. It changes
   only the commit message, so the tree and `BASE.md`'s hash stay. checkpatch must stay clean.
   Update the "not looked up yet" note in `patches/kernel-7.3/README.md`.
2. **Tree.** In the existing build tree: commit the removal of the five `.orig` files, then
   `git am` 0006 from this branch. Check `git rev-parse HEAD^{tree}` is `5f201035` and that
   `.config` still equals the published config, before compiling.
3. **Build** in the same tree, incrementally
   ([why](../../decisions/2026-11-12-sl74-incremental-build.md)). Gate: no other
   `cargo`/`rustc`/`tauri` build and at least 8 GB available, polled in the background. Then
   `nice make -j6 LOCALVERSION= KDEB_PKGVERSION=7.3.0-9.9+sl7.4 bindeb-pkg` in a
   memory-capped scope, in the background, logged to `~/sl7-kernel/logs/build4.log`.
4. **Check the packages.** Names and sizes; the image's version string; `perf.o` rebuilt;
   `Module.symvers` equal to `+sl7.3`'s; modules signed by the same key with the same
   vermagic. Those last two show that `+sl7.3`'s modules, initramfs and out-of-tree modules
   work with the new image.
5. **Test instructions**, in a file next to the packages (outside the repo, since it needs
   the machine's real UUIDs): boot the new image once beside the installed `+sl7.3`, with no
   package installed ([why](../../decisions/2026-11-12-sl74-test-boot-image-only.md)); the
   checks from `patches/kernel-7.3/README.md` and `docs/power.md`; installing the packages
   once it passes; rolling back to `+sl7.3`. Report to the lead.
6. **Results.** When the lead sends them: record them in `patches/kernel-7.3/README.md` and
   `docs/power.md` (and the matching lines of `docs/kernel-7.3.md`), commit, report again.

Out of scope: README.md, PROGRESS.md, resume-ready.md; installing, GRUB, reboots; deleting the
`+sl7.1`-`+sl7.3` packages (`+sl7.3` is the rollback).
