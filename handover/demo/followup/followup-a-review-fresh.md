# Fresh review of followup-a.patch (sha256 4b432e6d... verified)  -- NOT CLEAN
Scratch: /tmp/work/rv-fa/r (fresh clone, 61ded9e). `git apply --check` + apply OK (8 files, +168/-14).
## Major
M1 UNC refusal is bypassed by mixed separators. `_refuse_network_path` tests `splitroot(text)[0][:2] in ("\\\\","//")` on the RAW
   text; ntpath.splitroot treats `\/` and `/\` as UNC but returns the drive unnormalised. Measured (ntpath, py3.13):
   `\/server\share/x.db` -> ok (not refused), `/\server/share` -> ok; PureWindowsPath(...).as_uri() of the first = file://server/share/x.db,
   i.e. exactly the unopenable form the patch claims to refuse. Fix: normalise (`drive.replace("/", "\\").startswith("\\\\")`) and add
   these two cases to the test (the test only has `\\` and `//`).
M2 README (load_tools/README.md) is markdown: `\\\\server\\share\\desk.sqlite3` inside a code span renders with FOUR leading
   backslashes (the doubling is right in the non-raw pathconfine docstring, wrong in markdown). Shown path is false. Write `\\server\share\desk.sqlite3`.
## Minor / uncertain
m1 Docs advice "copy to a local folder or a mapped drive": on Windows os.path.realpath (used by confine*) resolves a mapped NETWORK drive to its UNC
   target, so such a path would then be refused too. Cannot measure on Linux; the sentence is unverified -> say "a local drive" or mark unmeasured.
m2 Check runs on the text given, not on `Path(path).absolute()`: a relative name with a UNC current directory yields a UNC URI and passes. Real flow
   (confine output is absolute) is unaffected; direct callers are.
m3 Also refuses `\\?\C:\x.db` and `\\localhost\c$\x.db` (SQLite accepts `localhost`): over-refusal, harmless, undocumented.
m4 src/lead_desk/urls.py docstring typo: "a literal\nliteral loopback address" (word repeated).
m5 Test gap (mutants that SURVIVE): (a) `except ImportError` -> `except ModuleNotFoundError` in load_driver.py: all tests pass (test uses an empty foreign
   package = ModuleNotFoundError; a foreign `tools.pathconfine` missing a name = ImportError is untested; I ran it by hand: works, foreign module executes
   then is dropped). (b) drop-everything instead of "only foreign" (`if True:`) in check_invariants.py: survives, the "only foreign modules" condition is untested.
## (a) foreign-tools fallback
- Not a new hole: a foreign `tools.pathconfine` that has all names is imported by the FIRST attempt exactly as before (code on PYTHONPATH is trusted by definition).
  A foreign one with a missing name now executes once, then is dropped and the repo's is loaded (manual run: "FOREIGN pathconfine ran" then normal usage).
- A real ImportError inside the repo's pathconfine is NOT hidden: retry re-raises it (manual run: traceback ModuleNotFoundError for the injected import).
- Dropping: removes cached `tools`/`tools.*` modules not under the repo (and namespace/None __file__). Only matters if the file is imported inside a larger
  process that already uses another project's `tools`; as a script start it is fine. No Blocker.
## (b) UNC
Refused (ntpath): `\\server\share`, `//server/share`, `\\?\UNC\...`, `\\?\unc\...`, `//?/UNC/..`, `\\.\C:\..`, `\\\server`, `\\server`. Not a path (file:// text) passes
through untouched (it is not a path). Drive-relative `C:x.db`, `C:\x.db`, `\x.db` OK. BYPASS: mixed separators (M1). Linux/macOS: posixpath.splitroot drive is always
"" so nothing refused: unchanged; all existing confinement tests pass. readonly_sqlite_uri gained an optional 2nd arg (only caller check_invariants.py:134 passes one arg).
## (c) docs sentence check
pathconfine.py/README hard-link text: true (test with os.link passes; read and write go through). "SQLite accepts only empty or localhost after file://": true per SQLite URI doc.
"refused by --book's read-only open": true (check_invariants.py:134 -> readonly_sqlite_uri) except M1/M2/m1 above. urls.py docstring: true after edit (demo_only/scripts do
contain a literal loopback http address, test confirms). The old "nothing is sent over a network" claim removed.
## (d) SO_EXCLUSIVEADDRUSE test
Mutants: `if True` with getattr default option, and `if sys.platform != "darwin"` in src/lead_desk/server.py -> test_the_exclusive_bind_is_not_set_off_windows FAILS both (good).
Patching `server.sys` with a stand-in no longer touches global sys.platform (test added). Real.
## (e) mutants (test file result)
killed: exclusive-always, exclusive-linux, UNC `//` alt removed, UNC check disabled, UNC call removed, drop-loop removed (load_driver), portal_demo re-export dropped,
README hard-link sentence changed, pathconfine hard-link sentence changed, urls "still write a literal" changed. Survived: ImportError->ModuleNotFoundError, drop-all (m5).
## (f) runs (unshare -n + loopback only, DPLD_REQUIRE_SCAN=1, gitleaks /tmp/work/gl, gpgsign off via env, after git add -A)
tests/test_path_confinement.py test_sonar_p2_choke_points.py test_hygiene*.py test_codeant_hygiene.py test_workflow*.py: 297 passed.
(With `unshare -rn` one existing test, setuid 65534, fails on the id mapping: environment, unrelated; passes with `unshare -n` as root.)
ruff check: pass; ruff format --check: 156 already formatted; mypy --platform linux: pass; --platform win32: pass (py3.13 venv /tmp/work/civenv; CI uses 3.12).
Not run: full suite, real Windows/SQLite, bandit.
