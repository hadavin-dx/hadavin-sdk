# lane3 fix-2 round 8: builder notes (B19)

Builder B19, cloud session 3. Worktree: /home/user/work/b19-tree (base f3c39cf8 + fix-1 r6 + fix-2 r7 patch + this round). Nothing pushed, nothing committed (`git add -A` only).
Plan followed: resolve-lane3-fix-2-r7.md rows 1-26 and its 12-step work order.
Tree id of the final head (git write-tree): eb5e171ad818b5b1b16ce820232b4b27610e3c92 (same id after applying each patch on a fresh clone, see raw/b19-patch-sha256.txt).

## What did not go the way the plan wanted, or was not checked (first)

* EGM skills were not invoked by me (I cannot switch models from inside this brief); the lead runs the EGM review of this result.
* No ruff, mypy or bandit was run (ordered: CI only). Line length was checked by a scratch script over the changed `.py` files (zero lines over 120 characters, ruff's own exemptions for a trailing `# type: ignore`/`# noqa` and one-word lines applied; output: raw/b19-line-length.log) plus an AST scan for unused imports and f-strings without a placeholder (0 findings). The `.md`, `.sh` and `.ps1` files have long lines on purpose (one paragraph per line) and were not wrapped; ruff does not check them. The wrapped docstrings and lines I rewrote were not run through `ruff format`: if CI wants a different wrap, it will say so.
* Windows was not checked at all. The mode check is POSIX only (by the plan). The Windows lines in docs/settings.md say "not tried by the author". The PowerShell lines in the n8n recipe stay "not tried".
* The key-file docs rule has one conditional escalation (row 2): a demo flow that must create a world-readable key file. I found none: the only places that create key files are `scripts/run_real_check.py --dry-fakes` (now made with mode 0600), `docs/n8n-recipe.md` Step C (already had `chmod 600`) and the tests (one session umask 077). `docs/real-services.md` now tells the reader to `chmod 600`. Not escalated.
* The guards are AST tripwires, not proofs: they name this in their docstring. A reader built through a path the scan cannot see (a computed attribute name, a call through a variable) is not found; non-literal `getattr` and `builtins` subscripts are reported as findings, so those two doors are closed, the rest is not.
* The guard tests for rows 1, 6-10 live in the test file, so they cannot fail on the old tree. They are proved the other way (planted violations in the real tree, raw/b19-mutation.log) and by their planted cases.

## Evidence files (all under evidence/raw/)

* b19-fails-before.log: r8 tests on the unchanged tree, 75 failed / 21 passed; all 75 behavioural, 0 function-absent (summary at the end of the file). (b19-fails-before-r8.log is the same raw run.)
* b19-mutation.log: every rule reverted or violation planted, each killed (the 2 first-pass survivors were weak tests; fixed and killed, noted in the file).
* b19-full-final.log: the ONE full run on the final head (see the end of this file for its result line).
* b19-guards-alone.log: the wall-clock guard test and the hygiene scan test run alone on the final head, with return codes.
* b19-patch-sha256.txt: tree id and sha256 of every patch.

## Row by row

| Row | Status | Where / test |
|---|---|---|
| 1 | done | `tests/test_one_key_file_rule_r7.py`: probe guard covers `src/lead_desk` (PROBE_FOLDERS), allowances keyed (file, enclosing function, line text) -> (count, reason), a stale or unreasoned allowance fails. The two old regex guards are deleted (`test_one_key_file_rule_and_path_walk.py`, `test_settings_lane3.py`, each with a pointer comment). Scan result: 26 probe hits, 66 reader hits, all allow-listed with a reason. |
| 2 | done | `envnum.read_secret_file`: after fstat, POSIX only, refuses `st_mode & 0o077` with "the {what} file can be read by other users: run chmod 600 on it"; no opt-out; no owner check (reason written in docs/settings.md). One session-wide autouse `umask(0o077)` fixture in `tests/conftest.py`. 60 mode tests (every kind x 10 modes). Docs sweep: see Not-checked above. |
| 3 | done | After the open: `os.lstat`; S_ISLNK refused; (st_ino, st_dev) mismatch refused when the handle's inode is not 0; O_NOFOLLOW kept. Texts: "the {what} file is a symbolic link: name the real file" and "... changed while it was being opened: try again". Tests: link, broken link, link loop, no-O_NOFOLLOW system, lstat/open swap by monkeypatch, lstat says link, zero inode (handle 0, name real), a spy that the open call carries O_NOFOLLOW. Windows skipif on the POSIX ones. |
| 4 | partly: 13 lines stay over 120 by a plain `awk length>120` | zero lines over 120 by ruff's own rule (raw/b19-line-length.log). The plain awk count over the changed `.py` files is 13: all 13 are lines that were already in the base, unchanged by me, that end in a `# type: ignore`, `# noqa` or `# nosec` comment (ruff leaves such a tail out of the width; one more has curly quotes that awk counts as 3 bytes). I did not wrap them: moving a pragma comment can change which line mypy, bandit or ruff blames, and I may not run those tools. The lead decides: leave as is (they pass CI at the base), or order a wrap with CI feedback. Files: scripts/run_live_check.py:170, src/lead_desk/config.py:369 and :388, live_claude.py:461, trace.py:103, tests/support.py:339, test_portal_api.py:1329, test_portal_mode.py:371, :478 and :487, test_reset_scripts.py:140, :168 and :223. |
| 5 | done | The whole key-file rule is one section `## Key and password files` in docs/settings.md. contract.md, limits.md and the n8n recipe keep one sentence plus the link `docs/settings.md#key-and-password-files`. Drift fixed: "read once" vs "read again" (the section says which file is read when), the "; Only" grammar, the BOM sentence (a BOM IS accepted, the code uses utf-8-sig), the device sentence. Tests pin one section, fail on a repeat and fail on a second section. The older pin tests (r6, r7, path_walk, docs_claims) now point at the one section. |
| 6 | done | BANNED additions: FileIO, read_binary, open_text, open_binary, linecache, fileinput, configparser, shutil.copy*, tokenize.open, mmap; subprocess/os.system/os.popen only on an allow-list; non-literal getattr and builtins subscripts are findings; docstring says tripwire. |
| 7 | done | enclosing function in the allowance key (3-tuple keys everywhere, including ALLOWED_WRONG_WORD). |
| 8 | done | PROBES: resolve, is_mount, is_socket, is_fifo, is_block_device, is_char_device, is_junction, owner, group, statvfs, disk_usage, expanduser; planted cases include a bare name. `Path(__file__).resolve()` is exempt structurally; `owner()`/`group()` only when called with no argument. |
| 9 | done | Shell scan over .sh .ps1 .bat .cmd .yml .yaml Makefile Dockerfile docker-compose* and `python -c` strings; reader word and key word must both be on the line, either order. The "any cat" rule is declined (as the plan says). |
| 10 | done | Retry-After scanner: any Subscript or Call whose string argument matches retry-after, resolving module constants; planted `headers["Retry-After"]`, a constant, `dict(headers)`, `.items()`, `getheader`. |
| 11 | done | Three copies pinned with an alphabet extended by \r \n \x0b \x0c, NBSP and Arabic-Indic digits, exhaustive to length 4 (r8 test, 9 x N digit clamp test too). `RETRY_AFTER_MAX_SECONDS` is in constants.py once; the other two copies import-or-mirror it as before and a test pins them. |
| 12 | done | A text that parses to an infinite float is clamped (not None) in envnum, load_driver and hubspot_probe; 400-digit tests. The unused `import math` is gone from the two copies. |
| 13 | done | docs/settings.md section: 4096 bytes counting the line break; kept as text; `crm_hubspot._key()` re-reads at every call. |
| 14 | done | Decision record at the end of docs/limits.md (3600 s, a decimal part is accepted, an HTTP date is read as no value); envnum `_RETRY_AFTER` comment no longer says RFC; the constant is in the "Fixed in code" list of settings.md. |
| 15 | done | scripts/n8n_api.py docstring: one sentence plus a pointer. |
| 16 | done | `test_settings_lane3.py`: `skipif(not hasattr(os, "geteuid") or os.geteuid() == 0, ...)`. |
| 17 | done | `run_real_check.py`: `flag.unlink(missing_ok=True)`; dry-fakes key files made with `touch(mode=0o600)`; `portal_demo.py` assets read with try/except OSError (no `is_file()`); tests against a denied read. |
| 18 | done | guard names and docstrings (tripwire). |
| 19 | done (softened) | grep of `int(`/`float(`/`Decimal(` over src, scripts, load_tools, tools, demo_only: none is on environment or config-file text (they are database values, reply values, command-line options, headers). Existing `tests/test_env_numbers.py` scan agrees. The `envnum.py` module docstring now says exactly that instead of "everywhere". |
| 20 | done | Windows markers: POSIX-only tests carry the skipif. |
| 21 | done | `_fresh` uses `monkeypatch.setitem`; no module leaks into later tests. |
| 22 | done | `tests/test_env_numbers.py`: `DESK_FAKES_PORT` is now a closed port from `support.free_port()`, not `1`. |
| 23 | done | WORD is the regex `lead\s+book` (built from parts); PLAIN_WORD is the literal for the allow-list keys. |
| 24 | done | `tests/test_docs_claims_lane3.py`: the 12 formatting-only hunks reverted to the fix-1 r6 text (31 semantic diff lines remain, all about the one section; two pins were rewritten to point there). |
| 25 | done | `# fmt: skip` on the generated allow-list tables. |
| 26 | done | docs-only rule and clamp (rows 13 and 14). |

## Slips of mine found while working (fixed)

* Two guard tests were first written to read the docs page the old way; the docs change broke 8 older pins. All 8 re-pointed to the one section (no test deleted, no pin weakened: each still asserts the same fact, now where it lives).
* My line-length rewraps broke one docstring pin in `tests/test_path_confinement.py` (the phrase "another project's ``tools``" was split across lines). Fixed by wrapping elsewhere; the subset run found it before the full run.
* One planted source line in the r7 allow-list tripped `tests/test_clock_steps.py` (the wall-clock guard); marked `# wall-clock: key text only`.
* My first "allow-list entry removed" mutation left an unmatched bracket and only "killed" by a collection error; redone properly (killed by the guard).

## Files changed

62 files against base f3c39cf8 (58 against base + fix-1 r6). Added by this round: tests/test_one_key_file_rule_r8.py. Patches: lane3-fix-2-r8-on-fix-1-r6.patch, lane3-fix-2-r8-recut.patch; read-only parts in lane3-fix-2-r8-parts/ (each at most 90 KB; the r7 test in three chunks).
