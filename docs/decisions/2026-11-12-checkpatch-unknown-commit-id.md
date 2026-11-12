# checkpatch ignores UNKNOWN_COMMIT_ID; Fixes: tags are checked by hand

2026-11-12

**Context.** Patch 0006 now carries `Fixes: a897575e79d7 (...)`. CI and the check command in
`CLAUDE.md` run checkpatch with `GIT_DIR=/nonexistent`, because with a git directory it checks
tracked files as source files instead of patches. With no git history, checkpatch can't find
any commit id and reports `Unknown commit id` for every `Fixes:` tag, which fails the check.

**Decision.** Both pass `--ignore MISSING_SIGN_OFF,UNKNOWN_COMMIT_ID`. A new `Fixes:` tag is
checked by hand: checkpatch run with `GIT_DIR` set to a bare repository holding the upstream
commit, as described under "checkpatch" in
[patches/kernel-7.3/README.md](../../patches/kernel-7.3/README.md). That also checks that the
subject in the tag matches the commit.

**Why.**

- Without history the check can't pass for any correct tag, so it only blocks.
- Fetching the commits in CI needs their full ids, which the tags don't have, or a large
  fetch of mainline history on every run.
- Only the lookup is lost. The rest of checkpatch still runs on every patch, including the
  form of the `Fixes:` line (12 or more hex digits, the subject in `("...")`): a malformed tag
  still fails CI.
