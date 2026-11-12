# Surface Laptop 7 Linux

Patches, device-tree overlays, tools and docs for Linux on the Surface Laptop 7 (Snapdragon X),
published as `Johnson-Anthony/surface-laptop-7-x1e-linux`.
Full spec: docs/SPEC.md

# Commands

There is no build or test suite; the author runs the hardware tests. These are the CI checks:

- Scrub: `tools/dev/scrub-check` (whole history, as the pre-push hook does: `--history`)
- Licenses: `reuse lint`
- Shell: `grep -rlE '^#!.*\b(ba|da)?sh\b' tools systemd config .githooks | xargs -r shellcheck`
- Python: `grep -rlE '^#!.*python' tools systemd config | xargs -r -n1 python3 -m py_compile`
- Kernel patch style: `GIT_DIR=/nonexistent perl ~/sl7-kernel/linux-7.3.0/scripts/checkpatch.pl --no-tree --strict --ignore MISSING_SIGN_OFF patches/kernel-7.3/*.patch patches/kernel-7.3/build/*.patch`

# Rules

- Never skip the scrub-check hooks (`--no-verify`). Private values are in `~/.config/sl7-scrub/denylist`, outside the repo; never commit it.
- Never commit firmware, Windows/Qualcomm/Microsoft files, IR camera frames, signing keys or raw dmesg.
- Copy curated, generalized pieces from the `~/sl7*` working folders, never whole folders or machine-specific services.
- Kernel patches: the repo's git identity as author, `Assisted-by: LLM`, no `Signed-off-by`.
- Every new file needs a REUSE license (an SPDX header or an entry in `REUSE.toml`).
- Don't install kernels, edit GRUB, reboot or suspend: ask the author to.

# Gotchas
