# M14 licence test: proposed edit (UNVERIFIED, not run)

File to change: `tests/test_repo_rules.py`. Two names used below: **core-hardening** is the working session that owns this test file and the take code (the checking program); **this folder** is the system-map work folder (`handover/system-map/work/`), which holds only text proposals and did not edit the test file.
Diffs made against the file content as read on 16 Nov 2026; hunk counts re-verified against it by two readers. (No commit id is claimed here: an earlier version named one that is no longer the current head.) Each diff was applied with `patch` to a scratch copy and compared with the intended result (second pass, 16 Nov 2026). The part of `tests/test_repo_rules.py` that these diffs touch matches what the earlier page showed (same constants, same `licence_problems()` loop, same `test_plant_apache_licence_is_caught`); the hunk headers below were produced by `diff -u` against that file content, so the line counts in the `@@` lines are exact for it. Lead answer: YES, change only the test. Re-grepped 16 Nov 2026 in `ORDERS.md`: line 146, in the lead's answer headed "ANSWER (lead, 13:03Z) to your NEEDS_YOU 1 to 5" (item 2: "Licence test: YES, change only the test so it accepts the three Apache-2.0 copies; the licence files stay unchanged"), and line 177, under the later heading "LEAD ORDER (owner asked directly: which agents run right now?)" (item 3: "item 2 YES (change only the test so it accepts Apache-2.0 in handover/promotion-inputs; licence files stay unchanged)"). Decision 11 is at `inputs/DECISIONS-2026-11-16.md` line 12: the Apache copies "never overwritten or re-licensed; BRANCH ARTEFACT"; it does not name the branch, so which branch holds the copies is UNVERIFIED (next step: core-hardening names it).

## Assumption about the folder (both options)
Both options relax only the LICENSE check. The same function also fails any tracked `pyproject.toml` whose licence is not `LicenseRef-Proprietary` or whose authors are not Hadavin (`tests/test_repo_rules.py`, the `pyproject.toml` branch of `licence_problems`). ASSUMPTION (UNVERIFIED, the folder is absent here): the folder holds only LICENSE files and no `pyproject.toml`. Before merge, core-hardening confirms the full file list of `handover/promotion-inputs/` on a trusted checkout; if any `pyproject.toml` is in it, this page's edit is not enough and the lead decides (a second exception would need its own diff and tests).

## Status: UNVERIFIED
Not run: no ruff, no pytest, no bandit. Only a Python syntax parse of both patched files and a count of line lengths (every added line is 100 characters or fewer; the project limit is 100, pyproject.toml line 68) were done. The folder `handover/promotion-inputs/` is NOT in this checkout (it does not exist; nothing tracked under it), so I could not see the real licence files, their names, their exact text or their hashes. Guesses to confirm before merge:
1. The copies are named exactly `LICENSE`.
2. Their text starts with the standard Apache 2.0 heading ("Apache License", then "Version 2.0, January 2004"). Before merge, compare `APACHE_2_HEADER` with the second line of the real file: the standard file has 27 spaces before `Version`. The first line has more leading spaces, which the check removes with `lstrip()`.
3. `ruff format` may still reflow something I could not see; run `uv run --all-extras --group test ruff format --check` on the patched file.

## The two options (the lead picks; I recommend Option 2)
**Which file each diff applies to (read this first).** Option 1 and Option 2 are two separate diffs, each made against the ORIGINAL `tests/test_repo_rules.py` (before any change). Apply ONE of them to the original. If Option 1 is already applied and the lead later wants Option 2, do NOT apply the Option 2 diff on top (it would fail or leave half of Option 1 behind): apply the third diff, "Option 1 to Option 2", given below, or first revert Option 1 (`git checkout -- tests/test_repo_rules.py`) and then apply Option 2.

**Decision for the lead.** Today (the folder is absent): apply Option 2 with the empty list. If the folder arrives before the fingerprints exist: apply Option 1, then apply the third diff when the fingerprints exist.

**Which one is safe now.** The folder `handover/promotion-inputs/` is absent from this checkout, so no LICENSE under it exists today. Option 2 with the empty list `{}` is therefore safe now: it accepts no foreign LICENSE, and none exists. Option 1 is needed only if licence files arrive in that folder BEFORE the fingerprints are computed.

In plain words: a licence file under `handover/promotion-inputs/` belongs to another holder and must stay unchanged. The test needs a rule that accepts it there and nowhere else.

- **Option 1, heading check (usable now).** The test accepts a file called `LICENSE` under `handover/promotion-inputs/` if its text starts with the Apache 2.0 heading. Weakness: a file that starts with the heading but was changed further down is accepted. This is the interim rule.
- **Option 2, exact fingerprint list (recommended).** The test keeps a list: exact file path, and the SHA-256 fingerprint (a long hex number computed from the whole text) of the unchanged licence. A file passes only if its path is listed and its text gives the same fingerprint. Any change anywhere in the file fails. The fingerprints must come from core-hardening, computed on a trusted checkout that has the folder, and each file must first be compared with the upstream Apache 2.0 licence file. The folder is absent here, so the list is written empty (`{}`) with a comment. UNTIL the fingerprints exist, Option 2 would reject every file in that folder, so Option 1 stays as the interim rule and is replaced by Option 2 when core-hardening supplies the list.

The fingerprint is computed on the text that Python reads (`read_text`, then UTF-8), not on the raw bytes, because Python turns Windows line endings (CRLF) into plain line feeds while reading; the fingerprints must be computed the same way (`hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()`).

## Option 1: proposed diff (heading check)
```diff
--- a/tests/test_repo_rules.py
+++ b/tests/test_repo_rules.py
@@ -3,7 +3,7 @@
 import ast
 import subprocess
 import tomllib
-from pathlib import Path
+from pathlib import Path, PurePosixPath
 
 import pytest
 import yaml
@@ -17,6 +17,11 @@
     "agreement with Hadavin. Viewing this repository on GitHub does not grant any such licence.\n"
 )
 
+# Other holders' licence copies kept unchanged here (decision 11). Only this folder may hold them,
+# and only the Apache-2.0 text is accepted there. Remove these constants when handover/ goes.
+THIRD_PARTY_LICENCE_DIR = ("handover", "promotion-inputs")
+APACHE_2_HEADER = "Apache License\n                           Version 2.0, January 2004"
+
 
 def tracked_files(root: Path) -> list[str]:
     out = subprocess.run(
@@ -30,12 +35,21 @@
 
 
 def licence_problems(root: Path, files: list[str]) -> list[str]:
-    """Every tracked LICENSE and pyproject.toml must be proprietary."""
+    """Every tracked LICENSE and pyproject.toml must be proprietary.
+
+    One exception, LICENSE files only: an unchanged Apache-2.0 copy of another holder under
+    handover/promotion-inputs/ (decision 11). The pyproject.toml checks have no exception.
+    """
     problems = []
     for name in files:
         path = root / name
-        if path.name == "LICENSE" and path.read_text(encoding="utf-8") != LICENCE_TEXT:
-            problems.append(f"{name}: not the proprietary licence text")
+        if path.name == "LICENSE":
+            text = path.read_text(encoding="utf-8")
+            parts = PurePosixPath(name).parts
+            third_party = parts[:2] == THIRD_PARTY_LICENCE_DIR and ".." not in parts
+            is_apache = third_party and text.lstrip().startswith(APACHE_2_HEADER)
+            if text != LICENCE_TEXT and not is_apache:
+                problems.append(f"{name}: not the proprietary licence text")
         if path.name == "pyproject.toml":
             project = tomllib.loads(path.read_text(encoding="utf-8")).get("project", {})
             if project.get("license") != "LicenseRef-Proprietary":
@@ -200,6 +214,44 @@
     assert licence_problems(tmp_path, ["LICENSE"]) == ["LICENSE: not the proprietary licence text"]
 
 
+APACHE_TEXT = APACHE_2_HEADER + "\n"
+PROBLEM = "not the proprietary licence text"
+LOOKALIKES = (
+    "handover/promotion-inputs-evil/x/LICENSE",
+    "handover/promotion-inputs/../x/LICENSE",
+)
+
+
+def write_licence(root: Path, name: str, text: str) -> None:
+    path = root / name
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(text, encoding="utf-8")
+
+
+def test_plant_apache_outside_promotion_inputs_is_caught(tmp_path):
+    write_licence(tmp_path, "LICENSE", APACHE_TEXT)
+    assert licence_problems(tmp_path, ["LICENSE"]) == [f"LICENSE: {PROBLEM}"]
+
+
+def test_plant_mit_inside_promotion_inputs_is_caught(tmp_path):
+    name = "handover/promotion-inputs/x/LICENSE"
+    write_licence(tmp_path, name, "MIT License\n")
+    assert licence_problems(tmp_path, [name]) == [f"{name}: {PROBLEM}"]
+
+
+def test_apache_inside_promotion_inputs_is_accepted(tmp_path):
+    name = "handover/promotion-inputs/x/LICENSE"
+    write_licence(tmp_path, name, APACHE_TEXT)
+    assert licence_problems(tmp_path, [name]) == []
+
+
+def test_plant_apache_in_lookalike_folder_is_caught(tmp_path):
+    (tmp_path / "handover" / "promotion-inputs").mkdir(parents=True)
+    for name in LOOKALIKES:
+        write_licence(tmp_path, name, APACHE_TEXT)
+        assert licence_problems(tmp_path, [name]) == [f"{name}: {PROBLEM}"]
+
+
 def test_plant_open_pyproject_is_caught(tmp_path):
     (tmp_path / "pyproject.toml").write_text(
         '[project]\nname = "x"\nlicense = "Apache-2.0"\nauthors = [{ name = "Someone" }]\n',
```

## Option 2: proposed diff (exact fingerprint list)
This is an alternative to the Option 1 diff, made against the same original file; do not apply both to the same file (use the third diff below to go from Option 1 to Option 2). With the list empty, only the tests that register a fingerprint themselves (through `monkeypatch`) show acceptance; the real folder will be rejected until core-hardening fills the list.
```diff
--- a/tests/test_repo_rules.py
+++ b/tests/test_repo_rules.py
@@ -1,6 +1,7 @@
 """Repository rules: proprietary licence everywhere, and the core never depends on a demo."""
 
 import ast
+import hashlib
 import subprocess
 import tomllib
 from pathlib import Path
@@ -17,6 +18,14 @@
     "agreement with Hadavin. Viewing this repository on GitHub does not grant any such licence.\n"
 )
 
+# Other holders' licence copies kept unchanged here (decision 11). A LICENSE file other than the
+# proprietary text is accepted only if its exact path is listed here with the SHA-256 of its text.
+# Remove this list when handover/ goes.
+# core-hardening fills this on a trusted checkout: for each file, take the hash of the text as
+# read_text() returns it, and check the file against the upstream Apache-2.0 licence file first.
+# Form: {"handover/promotion-inputs/<path>/LICENSE": "<64 hex characters>"}
+APACHE_LICENCE_SHA256: dict[str, str] = {}
+
 
 def tracked_files(root: Path) -> list[str]:
     out = subprocess.run(
@@ -30,12 +39,20 @@
 
 
 def licence_problems(root: Path, files: list[str]) -> list[str]:
-    """Every tracked LICENSE and pyproject.toml must be proprietary."""
+    """Every tracked LICENSE and pyproject.toml must be proprietary.
+
+    One exception, LICENSE files only: an unchanged Apache-2.0 copy of another holder under
+    handover/promotion-inputs/ (decision 11). The pyproject.toml checks have no exception.
+    """
     problems = []
     for name in files:
         path = root / name
-        if path.name == "LICENSE" and path.read_text(encoding="utf-8") != LICENCE_TEXT:
-            problems.append(f"{name}: not the proprietary licence text")
+        if path.name == "LICENSE":
+            text = path.read_text(encoding="utf-8")
+            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
+            is_apache = APACHE_LICENCE_SHA256.get(name) == digest
+            if text != LICENCE_TEXT and not is_apache:
+                problems.append(f"{name}: not the proprietary licence text")
         if path.name == "pyproject.toml":
             project = tomllib.loads(path.read_text(encoding="utf-8")).get("project", {})
             if project.get("license") != "LicenseRef-Proprietary":
@@ -200,6 +217,58 @@
     assert licence_problems(tmp_path, ["LICENSE"]) == ["LICENSE: not the proprietary licence text"]
 
 
+APACHE_TEXT = "Apache License\n                           Version 2.0, January 2004\n"
+LISTED = "handover/promotion-inputs/x/LICENSE"
+PROBLEM = "not the proprietary licence text"
+LOOKALIKES = (
+    "handover/promotion-inputs-evil/x/LICENSE",
+    "handover/promotion-inputs/../x/LICENSE",
+)
+
+
+def write_licence(root: Path, name: str, text: str) -> None:
+    path = root / name
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(text, encoding="utf-8")
+
+
+def list_hash(monkeypatch, name: str, text: str) -> None:
+    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
+    monkeypatch.setitem(APACHE_LICENCE_SHA256, name, digest)
+
+
+def test_plant_apache_outside_promotion_inputs_is_caught(tmp_path, monkeypatch):
+    list_hash(monkeypatch, LISTED, APACHE_TEXT)
+    write_licence(tmp_path, "LICENSE", APACHE_TEXT)
+    assert licence_problems(tmp_path, ["LICENSE"]) == [f"LICENSE: {PROBLEM}"]
+
+
+def test_plant_mit_inside_promotion_inputs_is_caught(tmp_path, monkeypatch):
+    list_hash(monkeypatch, LISTED, APACHE_TEXT)
+    write_licence(tmp_path, LISTED, "MIT License\n")
+    assert licence_problems(tmp_path, [LISTED]) == [f"{LISTED}: {PROBLEM}"]
+
+
+def test_apache_inside_promotion_inputs_is_accepted(tmp_path, monkeypatch):
+    list_hash(monkeypatch, LISTED, APACHE_TEXT)
+    write_licence(tmp_path, LISTED, APACHE_TEXT)
+    assert licence_problems(tmp_path, [LISTED]) == []
+
+
+def test_plant_apache_with_added_line_is_caught(tmp_path, monkeypatch):
+    list_hash(monkeypatch, LISTED, APACHE_TEXT)
+    write_licence(tmp_path, LISTED, APACHE_TEXT + "Extra line added further down.\n")
+    assert licence_problems(tmp_path, [LISTED]) == [f"{LISTED}: {PROBLEM}"]
+
+
+def test_plant_apache_in_lookalike_folder_is_caught(tmp_path, monkeypatch):
+    list_hash(monkeypatch, LISTED, APACHE_TEXT)
+    (tmp_path / "handover" / "promotion-inputs").mkdir(parents=True)
+    for name in LOOKALIKES:
+        write_licence(tmp_path, name, APACHE_TEXT)
+        assert licence_problems(tmp_path, [name]) == [f"{name}: {PROBLEM}"]
+
+
 def test_plant_open_pyproject_is_caught(tmp_path):
     (tmp_path / "pyproject.toml").write_text(
         '[project]\nname = "x"\nlicense = "Apache-2.0"\nauthors = [{ name = "Someone" }]\n',
```

## Third diff: Option 1 to Option 2 (for a checkout where Option 1 is already applied)
Made with `diff -u` between the file with Option 1 applied and the file with Option 2 applied; applied with `patch` to a scratch copy that had Option 1 and compared with the Option 2 file: identical (second pass, 16 Nov 2026; the ruff and pytest runs are still not done). It carries the same docstring change as the other two diffs.
```diff
--- a/tests/test_repo_rules.py
+++ b/tests/test_repo_rules.py
@@ -1,9 +1,10 @@
 """Repository rules: proprietary licence everywhere, and the core never depends on a demo."""
 
 import ast
+import hashlib
 import subprocess
 import tomllib
-from pathlib import Path, PurePosixPath
+from pathlib import Path
 
 import pytest
 import yaml
@@ -17,10 +18,13 @@
     "agreement with Hadavin. Viewing this repository on GitHub does not grant any such licence.\n"
 )
 
-# Other holders' licence copies kept unchanged here (decision 11). Only this folder may hold them,
-# and only the Apache-2.0 text is accepted there. Remove these constants when handover/ goes.
-THIRD_PARTY_LICENCE_DIR = ("handover", "promotion-inputs")
-APACHE_2_HEADER = "Apache License\n                           Version 2.0, January 2004"
+# Other holders' licence copies kept unchanged here (decision 11). A LICENSE file other than the
+# proprietary text is accepted only if its exact path is listed here with the SHA-256 of its text.
+# Remove this list when handover/ goes.
+# core-hardening fills this on a trusted checkout: for each file, take the hash of the text as
+# read_text() returns it, and check the file against the upstream Apache-2.0 licence file first.
+# Form: {"handover/promotion-inputs/<path>/LICENSE": "<64 hex characters>"}
+APACHE_LICENCE_SHA256: dict[str, str] = {}
 
 
 def tracked_files(root: Path) -> list[str]:
@@ -45,9 +49,8 @@
         path = root / name
         if path.name == "LICENSE":
             text = path.read_text(encoding="utf-8")
-            parts = PurePosixPath(name).parts
-            third_party = parts[:2] == THIRD_PARTY_LICENCE_DIR and ".." not in parts
-            is_apache = third_party and text.lstrip().startswith(APACHE_2_HEADER)
+            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
+            is_apache = APACHE_LICENCE_SHA256.get(name) == digest
             if text != LICENCE_TEXT and not is_apache:
                 problems.append(f"{name}: not the proprietary licence text")
         if path.name == "pyproject.toml":
@@ -214,7 +217,8 @@
     assert licence_problems(tmp_path, ["LICENSE"]) == ["LICENSE: not the proprietary licence text"]
 
 
-APACHE_TEXT = APACHE_2_HEADER + "\n"
+APACHE_TEXT = "Apache License\n                           Version 2.0, January 2004\n"
+LISTED = "handover/promotion-inputs/x/LICENSE"
 PROBLEM = "not the proprietary licence text"
 LOOKALIKES = (
     "handover/promotion-inputs-evil/x/LICENSE",
@@ -228,24 +232,37 @@
     path.write_text(text, encoding="utf-8")
 
 
-def test_plant_apache_outside_promotion_inputs_is_caught(tmp_path):
+def list_hash(monkeypatch, name: str, text: str) -> None:
+    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
+    monkeypatch.setitem(APACHE_LICENCE_SHA256, name, digest)
+
+
+def test_plant_apache_outside_promotion_inputs_is_caught(tmp_path, monkeypatch):
+    list_hash(monkeypatch, LISTED, APACHE_TEXT)
     write_licence(tmp_path, "LICENSE", APACHE_TEXT)
     assert licence_problems(tmp_path, ["LICENSE"]) == [f"LICENSE: {PROBLEM}"]
 
 
-def test_plant_mit_inside_promotion_inputs_is_caught(tmp_path):
-    name = "handover/promotion-inputs/x/LICENSE"
-    write_licence(tmp_path, name, "MIT License\n")
-    assert licence_problems(tmp_path, [name]) == [f"{name}: {PROBLEM}"]
+def test_plant_mit_inside_promotion_inputs_is_caught(tmp_path, monkeypatch):
+    list_hash(monkeypatch, LISTED, APACHE_TEXT)
+    write_licence(tmp_path, LISTED, "MIT License\n")
+    assert licence_problems(tmp_path, [LISTED]) == [f"{LISTED}: {PROBLEM}"]
+
+
+def test_apache_inside_promotion_inputs_is_accepted(tmp_path, monkeypatch):
+    list_hash(monkeypatch, LISTED, APACHE_TEXT)
+    write_licence(tmp_path, LISTED, APACHE_TEXT)
+    assert licence_problems(tmp_path, [LISTED]) == []
 
 
-def test_apache_inside_promotion_inputs_is_accepted(tmp_path):
-    name = "handover/promotion-inputs/x/LICENSE"
-    write_licence(tmp_path, name, APACHE_TEXT)
-    assert licence_problems(tmp_path, [name]) == []
+def test_plant_apache_with_added_line_is_caught(tmp_path, monkeypatch):
+    list_hash(monkeypatch, LISTED, APACHE_TEXT)
+    write_licence(tmp_path, LISTED, APACHE_TEXT + "Extra line added further down.\n")
+    assert licence_problems(tmp_path, [LISTED]) == [f"{LISTED}: {PROBLEM}"]
 
 
-def test_plant_apache_in_lookalike_folder_is_caught(tmp_path):
+def test_plant_apache_in_lookalike_folder_is_caught(tmp_path, monkeypatch):
+    list_hash(monkeypatch, LISTED, APACHE_TEXT)
     (tmp_path / "handover" / "promotion-inputs").mkdir(parents=True)
     for name in LOOKALIKES:
         write_licence(tmp_path, name, APACHE_TEXT)
```

## The docstring change (all three diffs)
`licence_problems()` says "Every tracked LICENSE and pyproject.toml must be proprietary." Both options make that untrue for one case, so the diffs add two lines naming the exception: LICENSE files only, an unchanged Apache-2.0 copy of another holder under `handover/promotion-inputs/` (decision 11); the `pyproject.toml` checks have no exception.

## Why it is safe, in plain words
- The licence files are not touched. Only the test changes.
- Everywhere else a LICENSE file must still be the exact proprietary text.
- Nothing else is widened: the `pyproject.toml` checks are unchanged; the proprietary text is still accepted as before.
- Option 1 checks the folder by path parts, not by text prefix: `handover/promotion-inputs-evil/...` does not match, and any path containing a `..` segment is refused.
- Option 2 needs an exact path and an exact fingerprint, so a lookalike folder, a `..` path, or a file changed anywhere fails.

## Cases that must still fail (tests in the diffs)
- `test_plant_apache_outside_promotion_inputs_is_caught`: an Apache 2.0 LICENSE at the repo root is still reported. This test guards against a rule that is too loose; it passes on the old code too. The existing `test_plant_apache_licence_is_caught` also still applies.
- `test_plant_mit_inside_promotion_inputs_is_caught`: a different licence (MIT) in a LICENSE file under `handover/promotion-inputs/` is still reported. Guards against a too loose rule; passes on the old code too.
- `test_apache_inside_promotion_inputs_is_accepted`: the accepted case. This is the ONLY new test expected to fail on the old code (the old code rejects every non-proprietary LICENSE).
- `test_plant_apache_in_lookalike_folder_is_caught` (loops over two names): `handover/promotion-inputs-evil/x/LICENSE` and `handover/promotion-inputs/../x/LICENSE` are reported. Guards against a too loose rule; passes on the old code too.
- Option 2 only: `test_plant_apache_with_added_line_is_caught`: a listed file with one line appended is reported. Option 1 cannot catch this (the gap that Option 2 closes). Also a too-loose guard: it passes on the old code.

## What I did not do or check
- Did not run the tests, so I have not shown that the new tests fail on the old code (rule: class-level fixes). Expectation (UNVERIFIED): only `test_apache_inside_promotion_inputs_is_accepted` fails on the old code; the other new tests are guards against a too loose rule and pass on both. Run both: the new tests against the old `licence_problems()`, then with the change.
- Did not see the real licence files, so the fingerprints, exact file names and the exact heading text are open (UNVERIFIED; next step: core-hardening on a trusted checkout).
- Second pass (reader findings M-1 to M-5): both options now state which file they apply to, the Option 1 to Option 2 diff was added, the pyproject.toml assumption was stated, the tests-fail-on-old-code wording was corrected, and the docstring change was added to the diffs. Third pass (16 Nov 2026): the commit id claim was removed (replaced by "file content as read on 16 Nov 2026"), the decision sentence was added, the two names core-hardening and this folder were defined, and the ORDERS.md lines were re-grepped. All three diffs were applied with `patch` to scratch copies and the results compared; Python syntax parse of the results OK; no ruff, pytest or bandit.
- Fixes applied from the first reader's findings: F1 (long line split into `is_apache = ...` and a short `if`), F2 (fingerprint option added, heading check kept as the interim), F3 (`..` refused, path compared by parts), F4 (one test split into named tests plus a lookalike-folder case), F5 (comment to remove the constants when `handover/` goes), F6 (compare the heading with the real file).
