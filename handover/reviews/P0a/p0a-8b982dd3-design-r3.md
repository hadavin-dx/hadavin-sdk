# p0a-8b982dd3-design-r3: PR #71 (core/P0a), head 8b982dd3, persona design

Source: hand-back of the design reviewer (agent a1b6c7e34e93c182b), saved by the lead (condensed). SECURITY path. Hand traces only (reviewer has no shell). 0 Blocker, 0 Major, 5 Minor, 4 Nit. Snapshot /home/user/build/snap/p0a-8b982dd3. Verdict: sound for the listed routes; every earlier finding stays fixed (pglast.libs, _pglast, dist-info folders, .so.N, .dylib, archives, shebang scripts, pglastic and pglast_utils not matched, tab split, from . import pglast, key collision, skip symlink only on nt).

## Minor
1. Lines 27-33, 89-96, 263-267: src/.venv and src/node_modules (also under demos, tools) are skipped; a pglast import or folder there passes. Stated in the docstring and in mutants. Cheap fix: apply the vendored-name and binary rules inside them or fail if they exist.
2. Lines 32, 89-96, 404-419: a directory symlink with any other name is not entered (src/x -> a pglast folder); packaging may follow it. Documented and pinned by test_symlinked_dir_is_not_entered. Fix: flag any directory symlink in the three trees, or follow with a cycle guard.
3. Lines 116, 129: not scanned: PEP 723 inline script metadata (comment), exec("import pglast"), subprocess pip install pglast, a .PY upper-case suffix (BINARY is case-insensitive, .py is not). Add to the limits or scan comment lines.
4. Lines 54-56, 46: archives and names narrower than they look: .tar.xz, .tar.bz2, .tar, .7z, .egg-link, a pglast-stubs folder, .pyc (documented), .bundle; archives judged by name only.
5. Lines 136-160, 227-238: rules with no mutant: uv.lock optional-dependencies, metadata.requires-dist, requires-dev non-test group, top-package dependencies edge; tool.uv dev-dependencies and override-dependencies; .egg-info branch; pglast8 digit branch; .tgz; a .pyi that imports pglast; symlinked file; broken symlink; unreadable .py; invalid uv.lock; missing pyproject.toml.

## Nits
6 the test group is exempt by name: say so. 7 requires-dev skip applies to every package, dev-dependencies skip only to the top package (safe, inconsistent). 8 unread: tool.uv.build-constraint-dependencies, extra-build-dependencies, dependency-metadata, lock [manifest]. 9 missing or empty tree fails with "no python file scanned": confirm src, demos and tools exist in the real repo. Also pglast8x folder is a harmless false positive.

## Not checked
No test run (builder's "90 passed" unverified); real pyproject, uv.lock, tree; packaging config shipping other folders (scripts, examples, root *.py); tomllib and os.scandir monkeypatch on 3.12 vs 3.13; Windows and macOS; real chmod unreadable folder as root; whether CI requires the job.
