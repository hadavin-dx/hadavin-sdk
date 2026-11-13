# F3 RESULTS

FAILED / UNCERTAIN FIRST: (1) I did NOT run the full suite (evidence runner does). I ran 942 tests of the touched areas
(key readers, env numbers, bind, hubspot, live, path confinement, crash points, mode safety, take script) = pass, 9 skip
(no playwright, py3.13-only). Plus 137 guard tests pass, 28 skip (no gitleaks). (2) Windows: O_NONBLOCK/O_BINARY paths not run
(no FIFOs there; getattr fallbacks). (3) The generic DESK_PORT `12\n` is NOT changed: decided INTENDED (below).
(4) Two of my own first test drafts were wrong: one subprocess version tripped ruff S603 (no suppressions allowed), one test
called a reader in the pytest process and hung on old code; both rewritten (child process via multiprocessing, 5 s limit).

## Bug class
File readers/parsers that accept any file type / any character class instead of an allowlist grammar: a regular file
(POSIX open(2)/stat S_ISREG; reading a FIFO blocks until a writer appears) and plain one-line text (urlsplit drops
tab/CR/LF anywhere by design, RFC 3986 allows none of them in a host).

## Fix (choke points)
- NEW src/lead_desk/regfile.py: `open_regular(path)` = os.open O_RDONLY|O_NONBLOCK, fstat on the open handle, refuse non-regular
  (NotRegularFile, an OSError; NUL path also). All callers already map OSError to their fixed "cannot be read" text.
- Callers switched: config.py:272 read_approvers, config.py:395 _read_leadflow, smtp_provider.py:156 read_secret_file,
  crm_hubspot.py:260 HubspotCrm._key, live_claude.py:425 LiveQualifier._read_key, live_claude.py:240 SpendLedger._totals,
  trace.py:131 CrashWindows.hit, hooks.py:41 FlagFileHooks.crash_point (last two are sibling finds).
- envnum.py:68 split_url: refuses any Cc/Zs/Zl/Zp character (SettingRefused "<NAME> is not a valid address"). Covers
  DESK_FAKES_URL, DESK_HUBSPOT_BASE_URL, DESK_LIVE_BASE_URL, scripts/n8n_api.
- config.py:65 `_plain_host_text` + config.py:530 Config.__post_init__: DESK_BIND / DESK_FAKES_HOST must be printable ASCII, no
  space (new fixed text "DESK_BIND and DESK_FAKES_HOST must be plain ASCII text on one line, with no spaces"). Still accepts "0", "[::1", "::" etc
  (existing tests pin those spellings; judged by public_bind_problem, unchanged).

## C7 decisions
- DESK_BIND newline/ESC/full-width digits: REAL defect, fixed (above).
- DESK_PORT `12\n` = 12: INTENDED. env_number docstring says spaces/tabs/line ends are stripped from both ends; test_env_numbers.py
  pins `"8765\r\n"`, `" 8765 "`, `"\t7\t"`. Value in the middle (`1\n2`) and full-width digits stay refused (tested).
- HubspotSettings base URL ending in newline: REAL defect (also with allow-any `no`: `https://api.example.test\n` passed). Fixed in split_url.

## Sibling sweep (grep open( / read_text / read_bytes / .open( in src)
Fixed: the 8 above. Left on purpose: portal_api.py:85 (is_file() checked, symlink refused, packaged assets); db.py:122 packaged
schema.sql; lockfile.py:51 and live_claude.py:162/291 and trace.py:57 open in append mode ("a+b"/"a") on paths the operator names for
output (a FIFO there would block too: NOT fixed, not in this class (readers); next step: same helper with a write mode if the reviewer wants it).
scripts/ are guarded by precheck.is_special_file / tools/pathconfine.py (unchanged; src cannot import tools/, so regfile is the library-side twin).

## Tests: tests/test_special_files_and_plain_text.py (42 cases)
FIFO in a spawned child, 5 s limit, per reader (7) + symlink to FIFO + open_regular unit + control-char loops (13 bind texts x2, 4 URL
texts, 6 tails x2 allow-any, every char 0x00-0x20/0x7f/0x85/0xa0/2028/2029/3000 x3 positions in split_url).
failing-before.log: old src (git checkout ee3d6ce -- src in a copy): 39 failed, 3 passed (the 3 are the accept-still-works pins).
passing-after.log: 42 passed. Raw outputs are in those files.
Ruff (ruff.txt): `ruff check` All checks passed!; `ruff format --check` 9 files already formatted.

## NOT run
full suite, mutation, Windows, browser tests, gitleaks, bandit.
