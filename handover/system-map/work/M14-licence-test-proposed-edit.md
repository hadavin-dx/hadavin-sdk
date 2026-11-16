# M14 licence test: proposed edit (UNVERIFIED, not run)

File to change: `tests/test_repo_rules.py` (owned by core-hardening; this folder did not edit it).
Diff made against the current contents of this checkout, head `d9d82669f` (git rev-parse --short HEAD).
Lead answer: YES, change only the test (ORDERS.md line 177; decision 11 of inputs/DECISIONS-2026-11-16.md).

## Status: UNVERIFIED
Not run: no ruff, no pytest. The folder `handover/promotion-inputs/` is NOT in this checkout (git ls-files lists nothing under it), so I could not see the real licence files, their names, or the exact failing line. The edit is my reading of `licence_problems()` in that test file, which fails any tracked file named `LICENSE` whose text is not the proprietary text. Two guesses to confirm: (1) the copies are named exactly `LICENSE`; (2) their text starts with the standard Apache 2.0 heading ("Apache License", then "Version 2.0, January 2004"). The new `if not (...)` line may be too long for ruff format; run `ruff format` on it.

## Proposed diff
```diff
--- a/tests/test_repo_rules.py	2026-11-16 18:31:13.240454456 +0000
+++ b/tests/test_repo_rules.py	2026-11-16 18:31:13.255123764 +0000
@@ -17,6 +17,11 @@
     "agreement with Hadavin. Viewing this repository on GitHub does not grant any such licence.\n"
 )
 
+# Other holders' licence copies kept unchanged here (decision 11). Only this folder may hold them,
+# and only the Apache-2.0 text is accepted there.
+THIRD_PARTY_LICENCE_DIR = "handover/promotion-inputs/"
+APACHE_2_HEADER = "Apache License\n                           Version 2.0, January 2004"
+
 
 def tracked_files(root: Path) -> list[str]:
     out = subprocess.run(
@@ -34,8 +39,11 @@
     problems = []
     for name in files:
         path = root / name
-        if path.name == "LICENSE" and path.read_text(encoding="utf-8") != LICENCE_TEXT:
-            problems.append(f"{name}: not the proprietary licence text")
+        if path.name == "LICENSE":
+            text = path.read_text(encoding="utf-8")
+            third_party = name.startswith(THIRD_PARTY_LICENCE_DIR)
+            if not (text == LICENCE_TEXT or (third_party and text.lstrip().startswith(APACHE_2_HEADER))):
+                problems.append(f"{name}: not the proprietary licence text")
         if path.name == "pyproject.toml":
             project = tomllib.loads(path.read_text(encoding="utf-8")).get("project", {})
             if project.get("license") != "LicenseRef-Proprietary":
@@ -200,6 +208,18 @@
     assert licence_problems(tmp_path, ["LICENSE"]) == ["LICENSE: not the proprietary licence text"]
 
 
+def test_apache_licence_is_accepted_only_under_promotion_inputs(tmp_path):
+    apache = "Apache License\n                           Version 2.0, January 2004\n"
+    inside = tmp_path / "handover" / "promotion-inputs" / "x"
+    inside.mkdir(parents=True)
+    (inside / "LICENSE").write_text(apache, encoding="utf-8")
+    assert licence_problems(tmp_path, ["handover/promotion-inputs/x/LICENSE"]) == []
+    (inside / "LICENSE").write_text("MIT License\n", encoding="utf-8")
+    assert licence_problems(tmp_path, ["handover/promotion-inputs/x/LICENSE"]) != []
+    (tmp_path / "LICENSE").write_text(apache, encoding="utf-8")
+    assert licence_problems(tmp_path, ["LICENSE"]) != []
+
+
 def test_plant_open_pyproject_is_caught(tmp_path):
     (tmp_path / "pyproject.toml").write_text(
         '[project]\nname = "x"\nlicense = "Apache-2.0"\nauthors = [{ name = "Someone" }]\n',
```

## Why it is safe, in plain words
- The licence files are not touched. Only the test changes.
- The test accepts the Apache-2.0 heading only when the file path starts with `handover/promotion-inputs/`. Everywhere else a LICENSE file must still be the exact proprietary text.
- Nothing else is widened: the `pyproject.toml` checks are unchanged; the proprietary text is still accepted as before.

## Cases that must still fail (the new test in the diff checks them)
- A different licence (for example MIT) in a LICENSE file under `handover/promotion-inputs/`: still reported.
- An Apache-2.0 LICENSE at any other place (for example the repo root): still reported. The existing `test_plant_apache_licence_is_caught` also still passes.
- Untested gap: a file under that folder that begins with the Apache heading but is changed further down is accepted (only the heading is checked). Tightening it needs the real file hash; the owner of the files can supply it.
