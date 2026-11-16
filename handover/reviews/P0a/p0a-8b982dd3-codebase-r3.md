# p0a-8b982dd3-codebase-r3: PR #71 (core/P0a), head 8b982dd3, persona codebase details

Source: hand-back of the codebase reviewer (agent ac7736d699f370f09), saved by the lead (condensed). SECURITY path. Read-only, nothing run. 0 Blocker, 1 Major, 5 Minor, 4 Nit. Snapshot /home/user/build/snap/p0a-8b982dd3. Earlier round-1 and round-2 items stay fixed.

## Major
- **M1** test lines 113-124 (`if not py: bad.append("... no python file scanned")`) applies to all of TREES (src, demos, tools): an absent or empty tools/ or demos/ makes test_repository_ships_no_pglast fail on a clean tree. No case pins an absent tools or demos; the docstring does not say all three must exist. LEAD CHECK: on the PR head origin/core/P0a tools/ holds 4 .py and demos/ 28 .py, so the test passes there (62 passed, independent evidence); the reviewer's "no tools/" was the on-disk cloud-handover checkout. It is a real fragility (a false alarm if tools/ is emptied or renamed), not a hole in the guard. Open ledger BL-core-a22-w2-02 is the same item. Fix: require a non-empty scan only for src; treat demos and tools as optional; test and mutant.

## Minor
- m1 evidence stale for this head (newest was 977c214, 39 tests); the 10233-passed and "22 of 62 fail on old guard" claims were the builder's (independent run in handover/evidence/P0a/8b982dd3).
- m2 ARCHIVES and _vendored miss .tar.xz, .tar.bz2, .tar, .tbz2, .7z, .gz; compiled .lib .o .bundle not flagged.
- m3 reuse: tests/test_repo_rules.py has tracked_files() (git ls-files), tomllib loading and AST walkers; walking git ls-files would remove the .venv, node_modules, symlink, unreadable-folder class (cost: untracked pre-commit copies not seen; CI is a fresh checkout). No existing pglast guard (not a duplicate).
- m4 a symlink with another name to a pglast tree is not entered (documented, pinned by test_symlinked_dir_is_not_entered); flag any symlinked directory under the three trees (none exist).
- m5 docstring vs code: names compared "after one normaliser (_norm)" but folders and archives use the VENDORED regex; the unparsable-file list omits .pyw and shebang scripts; unreadable file, broken symlink or vanished file raises (fails loud, undocumented); string rule flags a bare "pglast" constant and f"pglast{x}" pieces (over-flags only).

## Nits
n1 not covered or listed: exec("import pglast"), python -c in a subprocess string, importlib.util.find_spec, sys.modules tricks; n2 _script opens every suffix-less file (FIFO or broken link would hang or raise; none in the real tree); n3 os.walk onerror raises if a dir vanishes mid-scan (no xdist in CI); n4 from .pglast import x reported (conservative; relative imports are banned anyway).

## Checked against the real repo
pglast declared once, pyproject.toml:52 in [dependency-groups] test (pglast==8.7); not in project.dependencies or any extra; dev and scan clean; [tool.uv] has no sources, constraints, overrides, dev-dependencies. uv.lock: hadavin-sdk dev-dependencies test and requires-dev test exempted exactly; no other package lists pglast. pglast used only in tests/demo_askdata (oracle, validate tests) and two README lines; no import pglast in src or demos .py. tomllib stdlib; test_unreadable_directory_raises monkeypatches os.scandir (root-safe, 3.12 and 3.13). Sub-second test.

## Not checked
No run (ruff, bandit, tests); commit messages; PR base tools/ (lead check above); ci.yml in full, requirements*.txt, Dockerfiles, setup.py, build-system; Windows junctions, case-insensitive filesystems, 3.14; docstring's owner decision of 2026-11-01; pglast licence text.
