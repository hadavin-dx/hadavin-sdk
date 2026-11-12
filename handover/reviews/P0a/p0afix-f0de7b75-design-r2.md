# p0afix-f0de7b75-design-r2: PR 71 pglast guard, fix head f0de7b75, round 2 (the one confirming round), persona design

Source: hand-back of the design reviewer (agent a4c33cbed1fbaf50f), saved by the lead session (condensed). Read-only, snapshot `/home/user/build/snap/p0afix-f0de7b75`, nothing run. Verdict: 0 Blocker, 0 Major, 4 Minor, 4 Nit. Both round-1 Majors and all round-1 nits fixed (traced by hand: pglast.libs, PGLast.Libs, pglast-8.7.dist-info, _pglast flagged; .so.1, .SO.1.2, libfoo.1.dylib flagged; .so.old not; BOM, PEP 735 names, symlink skip).

## Minor
- m1 docstring (lines 1-25) "Not caught" list lacks requirements*.txt, setup.py, Dockerfiles, CI pip installs, build-system requires; they exist only in PR-NOTE.md. Copy into the docstring.
- m2 `_vendored` uses startswith("pglast"): over-matches `pglastic`, `pglast_utils`. Use `re.match(r"pglast(-|$)", _norm(n))`.
- m3 archives by name not flagged (pglast-8.7-*.whl, .egg, .zip, .tar.gz, .a); not in the docstring limits. Flag or list.
- m4 only .py/.pyi parsed: extensionless python script with shebang, .pyw not scanned. Scan shebang files or document.

## Nit
- n5 `from . import pglast` alias not checked (folder check catches the real case). n6 group dict comprehension hides two keys that normalise to the same name: assert key counts equal. n7 bare OSError skip can silently pass on Linux: skip only on os.name == "nt". n8 `_is` does not split on tab.

## Not checked
No tests run; old guard functions and tmp test file behind failbefore.txt not in snapshot ("was 35" unverifiable); real pyproject.toml, uv.lock and tree not seen; tomllib version, os.scandir monkeypatch, CI wiring not checked. Builder's "90 passed" is two files, not 50.
