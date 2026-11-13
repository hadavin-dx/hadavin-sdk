# CRLF emulation (Q7 item 3). EVIDENCE only. Repo pr-3-tests 2db3926, Linux, gitleaks 8.30.1. Nothing here is a real Windows run.
Trees: /tmp/work/crlf-base (LF clone), crlf-A (autocrlf=true + repo .gitattributes), crlf-B (autocrlf=true, .gitattributes overridden by .git/info/attributes `* !text !eol`), crlf-tree (every tracked non-PNG file rewritten to CRLF, autocrlf=false: worst case), crlf-C (only sonar-project.properties hand-saved CRLF).

## 1. Checkout conversion (MEASURED)
.gitattributes: `* text=auto eol=lf`, plus *.sh/.py/.json/.md/.toml/.yml/.txt/.in text eol=lf, and `*.ps1 text eol=crlf` (intentional).
- A (autocrlf=true, attributes active): 226 files i/lf w/lf; only scripts/reset.ps1 and scripts/start_all.ps1 are w/crlf. So eol=lf wins over core.autocrlf. sonar-project.properties, .gitleaks.toml, exceptions.txt, patterns.txt, requirements-*.txt, docs, tests/*.py: 0 CR bytes. (evidence-crlf-1-eol.A.txt, -2-bytes.txt)
- B (autocrlf=true, attributes overridden = what a repo WITHOUT .gitattributes would do): 228 files w/crlf (all text files). sonar-project.properties 14 CR, .gitleaks.toml 110, exceptions.txt 31, patterns.txt 9, tests/test_hygiene.py 480. (evidence-crlf-1-eol.B.txt)
- Only non-converted: icon.png (binary), tests/.gitkeep, tools/__init__.py (empty).

## 2. Worst case, all text files CRLF (crlf-tree) (MEASURED)
(a) gitleaks dir .: exit 1, 1 finding: generic-api-key, sonar-project.properties line 4 (the projectKey line). LF base: no leaks. (evidence-crlf-3)
(b) tests/test_gitleaks_exceptions.py: 44 passed (it already pins CRLF as "reported"). (evidence-crlf-4)
    tests/test_hygiene.py: 14 passed, 1 failed: test_hygiene_scan_public, "gitleaks dir reported findings" (the same one finding). (evidence-crlf-5)
(c) git-grep hygiene (tools/hygiene.py, patterns.txt/exceptions.txt, CRLF in both): no failure; the other 14 hygiene tests pass. tests/test_codeant_hygiene.py: 7 passed. (evidence-crlf-6)
Classification of the single failure: (i) true Windows risk ONLY IF a checkout converts that file to CRLF (case B: no/overridden attribute, autocrlf=true; gitleaks on B also reports 1 leak, evidence-crlf-7). (ii) Fixed by .gitattributes in A (no leaks in A). Not an emulation artifact: B reproduces it through real git conversion. Note: the (c) git-grep scan and the 44 exception tests were unaffected by CRLF.

## 3. Hand-saved CRLF in sonar-project.properties (crlf-C) (MEASURED)
- `gitleaks dir .` reports 1 leak (CRLF working copy), as the repo's test comment pins.
- `git add` prints: "warning: in the working copy of 'sonar-project.properties', CRLF will be replaced by LF the next time Git touches it"; nothing is staged (index stays i/lf, `git diff --cached` empty). `gitleaks git .` (history/commits) = no leaks. So a developer sees a git warning and a local `gitleaks dir` / test_hygiene_scan_public failure, but nothing reaches a commit or CI (CI checks out LF).
- Failure text in the test is a bare "gitleaks dir reported findings (values are redacted)": it does not say CRLF.

## 4. Recommendations (not applied; each from the evidence)
1. Keep `.gitattributes`; it is the control that worked (A vs B). Optionally add explicit `*.properties text eol=lf` (INFERRED: the `*` rule already gave i/lf w/lf for sonar-project.properties in A, so this only guards against someone deleting the catch-all line).
2. Add `.editorconfig` (`end_of_line = lf`, `[*.ps1] end_of_line = crlf`) so editors do not save CRLF (INFERRED benefit; no editor was run).
3. Make the failure self-explaining: in test_hygiene_scan_public, if the failing file bytes contain b"\r\n", append "file has CRLF line endings; run `git add --renormalize .` or re-save with LF". Evidence: today's message names neither file nor cause (evidence-crlf-5).
4. A fast pre-check test that fails on CR in the allowlisted files (sonar-project.properties, .gitleaks.toml, exceptions.txt, patterns.txt), clear message. Evidence: crlf-tree shows these as the files whose CR matters.
5. Docs (docs/tests.md line 74) already states this; add the fix command from 3.
Not checked: real Windows git/editors, Git for Windows safecrlf defaults, PowerShell tooling, the full test suite on CRLF, the .ps1 scripts under gitleaks (covered only inside the tree scan, no findings).
