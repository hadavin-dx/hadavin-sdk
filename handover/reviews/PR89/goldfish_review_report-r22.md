Status: resolved (no person available; recommended option taken for every item)

# Goldfish Annotated Review Report

**Target:** `tools/mutation_runner.py`, `CHANGELOG.md`, `tests/` at head c2f98f49 (snapshot `/home/user/build/snap/pr89-c2f98f49/`), full files. Security path: no round cap, nothing declined.
**Inputs:** `r22-design-full.md`, `r22-codebase-full.md`. Evidence for this head: not yet run (runner a8c5dcf3 running). Each claim below was checked by reading the snapshot.

Counts: PROPOSE FIX 14, CONTEST 0, ESCALATE 0, DECLINE 0. One decision (M2) is recorded as D-023.

## Findings

### 1 [design] Blocker B1: the private temp folder is lost after the first rebuild
* Checked: `mutation_runner.py:1726-1728`: `build()` calls `shutil.rmtree(tmp)` then `(tmp / "tests").mkdir(parents=True)`. `mkdtemp` (line 1767) made `tmp` 0700; the rebuild recreates it with the default mode. True.
* ***PROPOSE FIX***: keep the top folder: empty its contents (or `os.chmod(tmp, 0o700)` after every rebuild) and re-check with `lstat` (own uid, no group/other bits); raise if wrong. Fix the docstring at line 215 and CHANGELOG:88 to say it is checked on every rebuild. Add a test under umask 0 that asserts `tmp` is 0700 during a run (after a rebuild too), and a mutant that skips the chmod/check. Fail-before proof on c2f98f49 required.

### 2 [design] Major M1: the snapshot folder uses the default mode
* Checked: line 1770 `snap.mkdir()`; `snap` is a sibling of `tmp`. True.
* ***PROPOSE FIX***: `snap.mkdir(mode=0o700)` then the same `lstat` check (uid, mode) before copying and after; or place `snap` inside the 0700 parent. Test under umask 0 for `snap`; mutant. State it in the docstring.

### 3 [design] Major M2: masking is off when no value is passed
* Checked: `_shown_line` returns `raw` when `not any(shown.secrets)` (lines 1018-1019), likewise `_shown_id`. Documented, not a broken promise; the threat model there is the passed address.
* ***PROPOSE FIX*** (decision D-023, no behaviour change): changing the default would hide all child failure text for every caller with nothing to protect. Instead state the limit plainly in the docstring and CHANGELOG ("with no passed variable nothing is replaced and nothing is claimed; the child can read the caller's home folder files, so do not pass this runner a test suite that must not see them") and pin it with a test. If the owner wants allowlisting always on, that is a later owner decision.

### 4 [codebase] Major M1: "a bare string is a TypeError" is false for `tests`, `extra_dirs`, `only`
* Checked: `isinstance(..., str)` guards exist only at lines 494, 728, 958. The sentence is at docstring 105-106, 1466 and CHANGELOG:34. True.
* ***PROPOSE FIX***: add the guard for `tests`, `extra_dirs`, `only` (TypeError, no letter-by-letter reading), with tests and mutants; keep the sentence. Re-pin the sha256 in `tests/fixtures/mutation_manifest.json` and the CHANGELOG list.

### 5 [design] minor 1: forged result file power understated
* ***PROPOSE FIX***: docstring/CHANGELOG say what a test can really do as the same user (alter `snap`, `base.xml`; forge `test_id`, first line, skipped list); the allowlist bounds what is shown.

### 6 [design] minor 2: lock folder falls back to `tempfile.gettempdir()` (may be the working folder); `XDG_RUNTIME_DIR` read late
* ***PROPOSE FIX***: refuse a lock folder inside `root` (or say so), and reword "read once" at 155-156 to except the lock folder lookup.

### 7 [design] minor 3 + [codebase] m7: huge port accepted
* ***PROPOSE FIX***: bound the port to 1-5 digits and 1-65535 in both the URL and key=value grammar; boundary tests and mutant.

### 8 [design] minor 4: lock reach
* ***PROPOSE FIX***: docstring only (it is a mistake catcher, spelling variants give two locks); already partly said, add the login and absent-variable cases.

### 9 [design] minor 5: "before any folder is made" is not universal
* Checked: `_refuse_links_out` and `_refuse_junctions` raise after `mkdtemp` and the snapshot copy (lines 1767-1787). True.
* ***PROPOSE FIX***: move those two checks before `mkdtemp`, or reword to name them as the exception; test.

### 10 [codebase] m1: order test does not pin step 8 against 9-11 and 7 against 8
* ***PROPOSE FIX***: add a value with 901 layers plus an unlisted host (and one with an odd character plus 901 layers); mutant that swaps the loops at 1705/1706; correct the test docstring.

### 11 [codebase] m2: `MAX_SECRETS = 300` unpinned
* ***PROPOSE FIX***: boundary tests at 300 and 301 texts, mutants for `>` versus `>=` and the constant.

### 12 [codebase] m3: property test partly wrong-reason
* ***PROPOSE FIX***: `_must_refuse` takes the expected step; draws that the shape grammar refuses are filtered or checked for the shape message.

### 13 [codebase] m4: no mutants for the guards at 728 and 958
* ***PROPOSE FIX***: add one mutant each (the `old` text includes the guard's own message); update the header.

### 14 [codebase] m5 / m6 / m8: wording and pins
* m5 CHANGELOG:57 "environment read once" limit to the passed variables; m6 `noqa` comment at 1363-1364 say "program path from SystemRoot"; m8 mypy count: add a test or a recorded-count check so a new POSIX-only call is noticed.
* ***PROPOSE FIX*** for all three.

## Handoff
Accepted fixes 14 (one wording-only decision, M2). Contested 0. Escalated 0. Declined 0. Unaddressed 0.
Next: one fix builder (all items, class-level: every folder this runner makes is created 0700 and checked), then delta evidence and a fresh round 23 (security path, uncapped) on the new head.
