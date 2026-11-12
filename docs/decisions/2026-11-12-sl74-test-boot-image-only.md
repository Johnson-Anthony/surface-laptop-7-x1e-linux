# +sl7.4 is test-booted as a bare kernel image beside +sl7.3

2026-11-12

**Context.** `+sl7.4` keeps the release name `7.3.0-sl7`. Installing its packages replaces
`+sl7.3`: the same package names, the same `/boot/vmlinuz-7.3.0-sl7` and the same
`/lib/modules/7.3.0-sl7`. The GRUB entries can't tell the two apart, so a one-time boot with
`next_entry` would boot `+sl7.4` from the default entry, with no `+sl7.3` left to fall back to
except by reinstalling it. The rule for a new kernel is to boot it once before it becomes the
default.

**Decision.** The first boot of `+sl7.4` uses only its kernel image, copied out of the package
to a separate path, with the installed `+sl7.3` initramfs, modules and device tree, from a
one-time GRUB entry. Nothing is installed. If the checks pass, the packages are installed the
usual way, which makes `+sl7.4` the default.

**Why.**

- Patch 0006 changes only built-in code, so the whole fix is in the image.
- `+sl7.3`'s modules load into the new image. Checked after the build: `Module.symvers` (the
  exported symbols and their CRCs) is identical, the signing key and the module vermagic are
  the same, and of the 9954 files in the image package only `vmlinuz`, `System.map`, `config`
  and the changelog differ. Every module and DTB is byte-identical to `+sl7.3`'s.
- A failed test costs a reboot: the next boot is the unchanged `+sl7.3`.
- Renaming the release instead (for example `7.3.0-sl7.4`) would have given it its own entries
  and modules, but it would change the release name every doc and GRUB entry uses, and
  every out-of-tree module, the Wi-Fi firmware directory and the DTBs would need a second copy.
