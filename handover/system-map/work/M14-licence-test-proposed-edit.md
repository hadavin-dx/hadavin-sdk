# M14 licence test: proposed edit (UNVERIFIED, not run)

File to change: `tests/test_repo_rules.py` (owned by core-hardening; this folder did not edit it).
Diffs made against the current contents of this checkout, head `dd60d96ff` (git rev-parse --short HEAD, read 16 Nov 2026). The earlier version of this page said `d9d82669f`: the head has moved since. The part of `tests/test_repo_rules.py` that these diffs touch matches what the earlier page showed (same constants, same `licence_problems()` loop, same `test_plant_apache_licence_is_caught`); the hunk headers below were produced by `diff -u` against the file as it stands now, so the line counts in the `@@` lines are exact for this head. Lead answer: YES, change only the test (ORDERS.md line 177; decision 11 of inputs/DECISIONS-2026-11-16.md).

## Status: UNVERIFIED
Not run: no ruff, no pytest, no bandit. Only a Python syntax parse of both patched files and a count of line lengths (every added line is 100 characters or fewer; the project limit is 100, pyproject.toml line 68) were done. The folder `handover/promotion-inputs/` is NOT in this checkout (it does not exist; nothing tracked under it), so I could not see the real licence files, their names, their exact text or their hashes. Guesses to confirm before merge:
1. The copies are named exactly `LICENSE`.
2. Their text starts with the standard Apache 2.0 heading ("Apache License", then "Version 2.0, January 2004"). Before merge, compare `APACHE_2_HEADER` with the second line of the real file: the standard file has 27 spaces before `Version`. The first line has more leading spaces, which the check removes with `lstrip()`.
3. `ruff format` may still reflow something I could not see; run `uv run --all-extras --group test ruff format --check` on the patched file.

## The two options (the lead picks; I recommend Option 2)
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
@@ -34,8 +39,13 @@
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
@@ -200,6 +210,44 @@
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
This replaces the Option 1 diff; do not apply both. With the list empty, only the tests that register a fingerprint themselves (through `monkeypatch`) show acceptance; the real folder will be rejected until core-hardening fills the list.
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
@@ -34,8 +43,12 @@
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
@@ -200,6 +213,58 @@
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

## Why it is safe, in plain words
- The licence files are not touched. Only the test changes.
- Everywhere else a LICENSE file must still be the exact proprietary text.
- Nothing else is widened: the `pyproject.toml` checks are unchanged; the proprietary text is still accepted as before.
- Option 1 checks the folder by path parts, not by text prefix: `handover/promotion-inputs-evil/...` does not match, and any path containing a `..` segment is refused.
- Option 2 needs an exact path and an exact fingerprint, so a lookalike folder, a `..` path, or a file changed anywhere fails.

## Cases that must still fail (tests in the diffs)
- `test_plant_apache_outside_promotion_inputs_is_caught`: an Apache 2.0 LICENSE at the repo root is still reported. The existing `test_plant_apache_licence_is_caught` also still applies.
- `test_plant_mit_inside_promotion_inputs_is_caught`: a different licence (MIT) in a LICENSE file under `handover/promotion-inputs/` is still reported.
- `test_apache_inside_promotion_inputs_is_accepted`: the accepted case.
- `test_plant_apache_in_lookalike_folder_is_caught` (loops over two names): `handover/promotion-inputs-evil/x/LICENSE` and `handover/promotion-inputs/../x/LICENSE` are reported.
- Option 2 only: `test_plant_apache_with_added_line_is_caught`: a listed file with one line appended is reported. Option 1 cannot catch this (the gap that Option 2 closes).

## What I did not do or check
- Did not run the tests, so I have not shown that the new tests fail on the old code (rule: class-level fixes). Run both: the new tests against the old `licence_problems()` must fail, then pass with the change.
- Did not see the real licence files, so the fingerprints, exact file names and the exact heading text are open (UNVERIFIED; next step: core-hardening on a trusted checkout).
- Fixes applied from the fresh reader's findings: F1 (long line split into `is_apache = ...` and a short `if`), F2 (fingerprint option added, heading check kept as the interim), F3 (`..` refused, path compared by parts), F4 (one test split into named tests plus a lookalike-folder case), F5 (comment to remove the constants when `handover/` goes), F6 (compare the heading with the real file).
