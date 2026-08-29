# CLEANUP.md

Read AGENTS.md first (roles, contract, layout). Cleanup pass only — no new features, no behavior changes.

## Do
- Remove dead code: unused functions, unused imports, unreachable branches, commented-out code blocks.
- Remove unused files (check for orphaned modules nothing imports).
- Trim comments to only what explains *why*, not *what* — delete comments that just restate the code.
- Rename unclear variables/functions to match their actual purpose, if trivially safe to do.
- Ensure consistent formatting (run `black .` if available; otherwise match existing style).
- Consolidate duplicated logic into one place, only if the duplication is exact/near-exact.

## Do NOT
- Change any function signature, return type, or behavior.
- Touch anything covered by tests without re-running tests after.
- Remove TODO comments that reference an unfinished planned feature (check project-plan.md phases first).
- Refactor architecture/structure — that's a planner decision, not a cleanup task.
- Delete a file without confirming nothing imports it (grep first).

## After
- Re-run full test suite, report pass/fail/skip counts (must match pre-cleanup counts).
- Launch app, confirm it still runs.
- List every file touched and, per file, what was removed/changed (1 line each).
- List every file deleted, with the grep confirmation it was unused.