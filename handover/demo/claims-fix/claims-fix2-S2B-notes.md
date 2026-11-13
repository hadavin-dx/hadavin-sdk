# S2B notes (versions.md only). Patch: /tmp/work/claims-fix2-S2B.patch (git apply --check OK on a fresh copy of /tmp/cf2-base). No test or tool was run; only reads, grep and a pin count (grep -c of lines "name==" in the two dev lock files: 18 and 19).
Already handled by stage 1 / code-fix and left alone: line 3 (Windows + Linux wording), line 9 (three rows: counts labelled as earlier-commit run results, edits-after wording, collect-only 3726), lines 28-35 (actions table).

| row | OLD | NEW | evidence | verdict |
|---|---|---|---|---|
| :8 Python 3.13.3 | `python --version` | adds "run by the author; no log is shipped" | no log in repo | F |
| :10 SQLite 3.49.1 / 3.24 | "3.49.1 (needs 3.24 or newer ...)" | 3.49.1 labelled author's run, no log; names src/lead_desk/desk.py (line 1362 uses ON CONFLICT ... DO UPDATE), says code does not check the version | desk.py:1362 | S (3.24 use) + F (3.49.1) |
| :16 n8n 2.46.6 | "the n8n runs, once" | "the author's n8n runs, once; no log is shipped" | grep: 2.46.6 appears in no other file | F |
| :17 Node 24.22.2 | "same runs" | adds "no log is shipped" | grep: nowhere else | F |
| :37 (was 35) SHA/gitleaks check | "were checked against the upstream repositories ..." | "checked by the author ...; no log ... not repeated here. The comment in lint.yml says where the checksum was copied from" | lint.yml:20-23 comment (copied from checksums file 2026-11-09) | F |
| :40 Python 3.12.16, pip-tools 7.6.2, container | stated as facts | header really records "pip-compile with Python 3.12" and the command (allow-unsafe, generate-hashes, strip-extras); 3.12.16, 7.6.2, container named as from the author's records, in no file | requirements-dev.txt lines 2-5; grep over repo | S (3.12 + command) + F (rest) |
| :40 uv 0.12.21 | "made with uv 0.12.21" | header records the command, not the uv version; 0.12.21 from author's records | requirements-dev-win.txt lines 1-2 | S + F |
| :40 "Neither file works on the other OS" | guarantee | "Each file is made for one OS (--python-platform in the header; colorama only in the Windows file); installing either on the other OS was not tried" | headers; not tested | F |
| :48-54 licence table (MIT, Apache, BSD, PSF, MPL) | column "as pip-licenses reads it" | column says "as the author's pip-licenses scan read it; raw output not shipped" | no log, packages not installed here | F |
| :57 uv 0.11.32 | "made with uv 0.11.32" | files do not record uv version; requirements-coverage.in:4 names 0.11.32 for the coverage lock only; same version for these two not checked | grep | F |
| :59 review bot | "it still reads requirements-browser.in ... not the three packages" | "going by that settings file ... the bot itself was not run or checked"; wording of the package list fixed (two named + typing-extensions) | .codeant/configuration.json exclude_files lists the four locks and not requirements-browser.in | F + O |
| :61 planted hash, gitleaks one finding | "tried with gitleaks 8.30.1 on this tree: one finding" | "the author tried this once ...; no log; gitleaks not run here"; second check now points at the test test_exceptions_narrow in tests/test_hygiene.py (plants docs/requirements-browser.txt and expects it reported). The test for gitleaks (test_lock_file_hashes_are_allowed_only_at_the_root) covers dev/coverage locks, not the browser locks, so the gitleaks half stays a labelled author's run | tests/test_hygiene.py ~371-396, ~528-560 | S (second check) + F (gitleaks half) |
| :63-67 browser licences | "read from installed packages' metadata" | "read by the author ... (no log is shipped)"; column header same | no log | F |
| :71 licence scan, counts | "19 packages ... 18 packages" | counts now labelled "has 19 / 18 pinned lines, counted here" (measured); scan results labelled author's statements not re-checkable | grep -c = 19 and 18 | S (counts) + F (results) |
| :74 "about 2 minutes" | number | "the short wait after a connection closes; its length was not measured here" | no source; port 0 part already backed (tests/test_http.py, config.py) | F |
| :75 hash install success | "verified by a successful pip install --require-hashes ..." | "The author reports ...; own runs, no log, not repeated here" | no log | F |
| :75 "hashes for all files PyPI listed" | claim | "made with --generate-hashes (in the headers), which by the tools' documentation lists the files PyPI offered ...; not re-checked (no network)" | headers | S (flag) + F |

Counts: S-only 0; mixed S+F 6; F 12 (approx per row above); O 1 (mixed with F); W 0. Rows total 18 lines of notes for the 15 audit rows (some audit rows were merged).

ASK for the owner:
1. Is the external review bot CodeAnt (the settings file .codeant/configuration.json) actually switched on for this GitHub repository, and does its dependency check really skip the files listed there? (versions.md now says only "going by that settings file; the bot was not run or checked".)

Could not verify: any run result (n8n, Node, Python/pip-tools/uv patch versions, container name, pip-licenses output, hash-install runs, gitleaks tried-once, SQLite 3.49.1/3.46.1); the upstream SHA/checksum check (no network); the Windows TIME_WAIT length.
Added-line scans: no long strings, paths with drive letters, links, e-mail, or suppressions in the diff.
sha256 of patch: 21b144203e6ae9a5b3811198baa381eb8b38a0de18b4b95c20c0c0f038495fe4
