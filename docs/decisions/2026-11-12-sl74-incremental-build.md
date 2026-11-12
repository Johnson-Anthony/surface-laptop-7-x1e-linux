# +sl7.4 is built in the +sl7.3 build tree, not from scratch

2026-11-12

**Context.** `+sl7.4` is the tested `+sl7.3` plus patch 0006, which changes one built-in file
(`drivers/firmware/arm_scmi/perf.c`). [BASE.md](../../patches/kernel-7.3/BASE.md) describes a
from-scratch build: import the Ubuntu source, apply the kit and our patches, write the config,
build.

**Decision.** Build in the tree that built `+sl7.3`: commit the removal of the five `.orig`
files, `git am` 0006, check that the tree hash is `5f201035` and that `.config` is still the
published config byte for byte, then run `bindeb-pkg` there. kbuild rebuilds what changed.

**Why.**

- The tree hash proves the sources are the published ones, which is what a from-scratch build
  would prove too. Removing the `.orig` files alone gives `a7533b07` again, the `+sl7.3` source.
- The tree keeps `certs/signing_key.pem`, the key that signed `+sl7.3`'s modules and the
  out-of-tree modules already installed. A fresh tree makes a new key, and every out-of-tree
  module would have to be rebuilt and re-signed.
- The same compiler, config and objects as `+sl7.3`, so the drain results differ by the patch
  only, not by a toolchain or config change.
- A rebuild of a few files instead of a full build of about half an hour at `-j10`, on a
  machine with 15 GB of RAM shared with other builds. `+sl7.3` was built the same way, from
  the `+sl7.2` tree.

The from-scratch steps in BASE.md stay the documented route for anyone else; they give the
same tree.
