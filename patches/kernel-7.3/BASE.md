# Base tree and how to reproduce 7.3.0-sl7

The kernel is three layers, one git commit per change:

1. Ubuntu's kernel source package `linux-source-7.3.0`, version `7.3.0-9.9` (Ubuntu 26.10
   "stonking", changelog dated 2026-10-05). It is upstream 7.3-rc6 plus Ubuntu's tree,
   which carries the X1E CAMSS and CCI device-tree nodes that mainline 7.3 lacks.
2. The [ItsLucas Surface Laptop 7 kit](https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel)
   at commit `2ce3083fa76855225465f809760dc7185c74a80c` (2026-10-23, merge of PR #17,
   "Bind QCE so the interconnects reach sync_state"), applied by
   [`tools/kernel/apply-series`](../../tools/kernel/apply-series): 26 patches,
   `patches/series` (0001-0005, 0007-0022, 0026, 0027) and then `patches/series-if-needed`
   (0023-0025), each as one commit, with the kit CI's rules (`patch --fuzz=0`; an optional
   patch is skipped only if it is already fully in the tree). All 26 applied; none was
   skipped. The kit has no 0006: it retired it (a QRTR revert that Ubuntu 7.3.0-6.6 made
   unnecessary).
3. This directory: `*.patch` (0001-0006), then `build/*.patch` (0001-0002).

Tested build: `7.3.0-9.9+sl7.3`, which has every patch here except 0006 (the `arm_scmi`
perf fix from 2026-11-03, not built or run yet). It was compiled natively on the laptop
(arm64) with `gcc (Debian 14.2.0-19) 14.2.0` and `GNU ld (GNU Binutils for Debian) 2.44`,
from `/proc/version` and `include/generated/compile.h`. Ubuntu builds its own 7.3.0-9
kernels with GCC 15.3.0 (`Ubuntu 15.3.0-4ubuntu1`, from `linux-buildinfo`); that compiler
was not used here.

## Checkpoints

Git tree hashes (`git rev-parse HEAD^{tree}`) after each step. They depend only on file
contents and modes, not on who made the commits, so yours should match exactly.

| After | Tree hash |
|---|---|
| importing `linux-source-7.3.0` 7.3.0-9.9 | `fc1233c83759335a592a7e152cb89686d64f58f9` |
| `tools/kernel/apply-series` with the kit at `2ce3083` | `c581ba6c4a255278afdf5e06e6702c5608c9cfdc` |
| `git am` of `*.patch` and `build/*.patch` | `5f201035b57e83361672efb77f5c8fd4711fbf1d` |

All three steps were reproduced from scratch with the steps below on 2026-10-27, when the
series ended at 0005 and the last hash was `a7533b071c4d3a3758011b524939561bd6ffa35e`, the
source of the tested `+sl7.3` kernel. When 0006 was added on 2026-11-12, the last hash was
recomputed from the `c581ba6c` tree in a scratch clone with `git apply --cached`, which
changes the files the way `git am` does but makes no commits. Applying 0001-0005 and
`build/` that way gave `a7533b07` again. The full series gives `5f201035` in either order,
and the two trees differ only in `drivers/firmware/arm_scmi/perf.c`.

The tested kernel was built from a tree with five more files: `.orig` backups that GNU
patch left when two kit patches applied at an offset (`drivers/hid/Kconfig.orig`,
`drivers/hid/Makefile.orig`, `drivers/hid/hid-core.c.orig`, `include/linux/hid.h.orig`,
`drivers/net/wireless/ath/ath12k/core.c.orig`). Nothing builds them, so the kernel is the
same. The published `apply-series` passes `--no-backup-if-mismatch`, so they are gone, and
the hashes above are for the tree without them. On 2026-11-12, the build tree's last kit
commit with those five files removed gave `c581ba6c` again.

## Steps

Build dependencies (Debian or Ubuntu names): `build-essential bison flex bc libssl-dev
libelf-dev libdw-dev debhelper dpkg-dev fakeroot rsync cpio kmod lz4 zstd python3 openssl
git patch`. A native build on the laptop takes about 1-2 hours with `-j10`.

1. Get the Ubuntu source. The ports archive keeps only current versions; Launchpad keeps
   all of them ([linux 7.3.0-9.9](https://launchpad.net/ubuntu/+source/linux/7.3.0-9.9)).

   ```sh
   B=http://ports.ubuntu.com/ubuntu-ports/pool/main/l/linux
   curl -fLO $B/linux-source-7.3.0_7.3.0-9.9_all.deb
   sha256sum linux-source-7.3.0_7.3.0-9.9_all.deb
   # 9c7b7b53a54af6c461d400a81dd035bbf37a5a9fa43de167c58b9d6f3229f398
   dpkg-deb -x linux-source-7.3.0_7.3.0-9.9_all.deb x-src
   tar -xf x-src/usr/src/linux-source-7.3.0/linux-source-7.3.0.tar.bz2
   mv linux-source-7.3.0 linux-7.3.0-sl7 && cd linux-7.3.0-sl7
   git init -q -b sl7 && git add -A && git commit -qm "Ubuntu linux-source 7.3.0-9.9"
   git rev-parse HEAD^{tree}       # fc1233c8...
   ```

   The tarball has no `.gitignore` files, so after a build `git status` lists every
   build output file as untracked. That is harmless, but run steps 2 and 3 before the
   first build: `apply-series` needs a clean tree.

2. Apply the kit. `apply-series` refuses a tree with uncommitted changes. Commits for the
   kit's own patches are made under your git identity, because those patches have no
   `From:` header; don't push that branch anywhere public. Patches that have one (0023-0027)
   keep their authors.

   ```sh
   git clone https://github.com/ItsLucas/surface-laptop-7-ubuntu-kernel ../sl7-kit
   git -C ../sl7-kit checkout 2ce3083fa76855225465f809760dc7185c74a80c
   /path/to/repo/tools/kernel/apply-series . ../sl7-kit
   git rev-parse HEAD^{tree}       # c581ba6c...
   ```

3. Apply this repo's patches.

   ```sh
   git am /path/to/repo/patches/kernel-7.3/*.patch
   git am /path/to/repo/patches/kernel-7.3/build/*.patch
   git rev-parse HEAD^{tree}       # 5f201035...
   ```

4. Write the config. By default this copies
   [`config/kernel/config-7.3.0-sl7`](../../config/kernel/config-7.3.0-sl7), the config of
   the tested kernel, and runs `make olddefconfig`; it prints any value your toolchain
   changed. In the from-scratch check on the build machine (2026-10-27), nothing changed;
   with a newer rustc only the `CONFIG_RUSTC_*` lines do (see "Config" in
   [docs/kernel-7.3.md](../../docs/kernel-7.3.md)).

   ```sh
   /path/to/repo/tools/kernel/make-config .
   ```

   To start from Ubuntu's own config instead, see "Config" in
   [docs/kernel-7.3.md](../../docs/kernel-7.3.md).

5. Build Debian packages. `LOCALVERSION=` (empty) stops kbuild from appending `+` for a
   git tree without a release tag. Pick your own package revision.

   ```sh
   nice make -j"$(nproc)" LOCALVERSION= KDEB_PKGVERSION=7.3.0-9.9+sl7.3 bindeb-pkg
   ```

   This writes `linux-image-7.3.0-sl7_*.deb`, `linux-headers-7.3.0-sl7_*.deb` and
   `linux-libc-dev_*.deb` to the parent directory. The kernel records the build user and
   host in `/proc/version`, and the package's maintainer field records a name and email
   address. Set `KBUILD_BUILD_USER`, `KBUILD_BUILD_HOST`, `DEBFULLNAME` and `DEBEMAIL` if
   you plan to share the packages.

   The build signs every module with a key it generates in `certs/signing_key.pem`. Keep
   the tree, or at least `certs/`: out-of-tree modules for this kernel have to be signed
   with the same key (see "After any kernel update" in
   [docs/kernel-7.3.md](../../docs/kernel-7.3.md)). Never publish that key.

6. Install and boot: see "Installing and booting" in
   [docs/kernel-7.3.md](../../docs/kernel-7.3.md).
