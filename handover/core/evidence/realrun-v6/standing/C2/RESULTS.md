# C2 hostile inputs: RESULTS (tree-C2 = 61ded9e + patch1 + patch2 + survivor-tests-v1; seed 1; container clock 12:30-12:52Z)

**What failed / unclear first:**
1. Case 120: `precheck.is_special_file(None)` ends in an uncaught TypeError traceback (wrong type; every real caller passes a path, so only a library-misuse path). Only traceback in 130 cases. Next step: decide whether to catch TypeError there (the docstring promises a bool for a path that cannot be looked at).
2. Cases 55-58, 60, 61: the plain `--dry-fakes --assume-yes` self-test did not finish inside `timeout 30` (rc 124). Not a hang: re-run with timeout 240 (ext-*.log) finished in 65 s (plain), 68 s (--keep), 36 s (--cleanup), 68 s (unknown smtp script), 68 s (port base 1); loadavg during those runs was 1.5 to 6.5 on 4 cores (other agents). Case 59 (TMPDIR on a read-only mount) finished in 6.1 s rc 0: Python fell back to another temp folder. Next step: if a 30 s bound is wanted for the self-test, say so; it needs about 65 s.
3. Killed runs (SIGTERM by timeout) leave their self-test folder behind: 9 `real-dry-*` folders in tmp-C2 (the folder is deleted only on a normal exit). Next step: decide if a SIGTERM handler is wanted; the folders hold made-up data only.
4. `--dry-smtp-script` accepts any text (unicode, newline, 120000 chars) with rc 0 and no refusal (ext-dry-badsmtp-unicode.log: rc 0, all checks pass, so an unknown name behaves as `ok`). Possible wrong-message/validation gap; F2 builder already has this item per the lead's note.
5. `--dry-port-base 99999999` refuses with `the settings: a file or folder cannot be used (OverflowError)`: the text names a file or folder but the cause is a port number out of range (ext-dry-port-huge.log, rc 2). `--dry-port-base 1` (as root) runs rc 0. F2 builder item.
6. Case 89 (ledger in a read-only mount): exit 2 with `stopped: LiveCapReached: the spend ledger could not be read or written` (the class name LiveCapReached is not what happened; the text after it is right). Next step: lead to judge the wording.
7. STATIC READ, NOT RUN (I may not answer the start question): `run_real_check.py` line ~1275 `run_dir.mkdir(parents=True, exist_ok=True)` sits after the start question and outside the try block that turns errors into refusals. Cases 25 (NUL byte in DESK_DB_PATH, reaches the question; `os.makedirs('a\x00b')` -> ValueError, shown directly) and 30 (DB folder on a read-only mount, reaches the question) pass every pre-question check, so after a yes they would likely end in a traceback. Unverified. Next step: a test that drives the post-question code with the question stubbed in a unit test (not by typing yes here).
8. Case 79: a 1,000,000-byte one-line key file is accepted by run_live_check (rc 3 only because loopback port 9 is closed); run_real_check refuses the same size (case 38 'too large'). Inconsistent limit between the two scripts. Next step: lead to judge.
9. Root ignores mode 000 (cases 39, 85: key file chmod 000 read fine, so permission-denied was NOT tested on files). Read-only folder WAS tested with a real read-only tmpfs mount (cases 30, 59, 89); it is unmounted again.
10. Linux refuses a single argument over 131072 bytes, so 1 MB cannot be passed as an argument: argv cases were capped to 120000 chars (marked in the label); the 1 MB variants are done through file contents (cases 15, 26, 27, 38, 79, 91). Run 1 (raw-C2-run1.log) had a weak config that never passed the vendor-address check, so run 2 is the record; run 1 kept for the trail.
11. Label correction: case 40 'remote host without allow flag': my base config already holds DESK_HUBSPOT_ALLOW_ANY_BASE_URL=yes, so a remote https host reached the question (by design). The refusal without the flag was seen in run 1 (raw-C2-run1.log case 40: `must be an https address at one of the vendor's own domains`).
12. precheck.py is a helper module with no main: run as a script it prints nothing, rc 0 (case 130); I tested its three functions directly (cases 115-129).

Secret printed: 0 of 130 (no made-up key string appears in any program output; case 114 passes the fake key as a wrong flag value and it is not echoed). 'Address printed yes' = loopback host / placeholder example.com the scripts print by design in the 'where the keys go' list or the file name `real-run.env.example`; no real address, no key.

Seed 1. Counts run 2: 130 cases, exit codes: -1:10, 0:16, 1:1, 124:6, 2:86, 3:10, 4:1 (-1 = I hung up the terminal at the start question without typing; 124 = timeout 30; 2 = refused; 3 = check failed/calls failed; 4 = book refused).

| # | input | exit code | message (first line) | traceback | secret or address printed |
|---|---|---|---|---|---|
| 1 | [rr] no args, no tty | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this script asks a question and needs | no | no |
| 2 | [rr] no args, tty | 2 | refused: --config: give PATH (see scripts/real-run.env.example) or use --dry-fakes | no | secret no; address yes: env.example (by design) |
| 3 | [rr] empty string arg | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 4 | [rr] --config empty string, tty | 2 | refused: --config: --config: names a folder, not a file | no | no |
| 5 | [rr] --config 1MB path string [argv capped at 120000 chars: Linux refuses a single argument over 131072 bytes] | 2 | refused: --config: --config: path too long | no | no |
| 6 | [rr] --config unicode+RTL path | 2 | refused: --config: --config: no such file | no | no |
| 7 | [rr] --config newline in path | 2 | refused: --config: --config: contains a control character | no | no |
| 8 | [rr] --config ../ traversal to /etc/passwd | 2 | refused: --config: config line 1 is not NAME=VALUE with an upper-case name | no | no |
| 9 | [rr] --config ../ traversal to missing | 2 | refused: --config: --config: no such file | no | no |
| 10 | [rr] --config is a directory | 2 | refused: --config: --config: names a folder, not a file | no | no |
| 11 | [rr] --config is a FIFO | 2 | refused: --config: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 12 | [rr] --config symlink loop | 2 | refused: --config: --config: a link on the path does not resolve (a loop) | no | no |
| 13 | [rr] --config dangling symlink | 2 | refused: --config: --config: no such file | no | no |
| 14 | [rr] --config empty file | 2 | refused: DESK_DB_PATH, DESK_HUBSPOT_KEY_FILE, DESK_HUBSPOT_MAX_CALLS, REAL_HUBSPOT_READBACK_MAX_CALLS, DESK_SMTPP_HOST, DESK_SMTPP_USER, DES | no | no |
| 15 | [rr] --config 1MB of A (no =) | 2 | refused: --config: config line 1 is not NAME=VALUE with an upper-case name | no | no |
| 16 | [rr] --config binary bytes | 2 | refused: --config: the config file is not UTF-8 text: save it as plain UTF-8 text | no | no |
| 17 | [rr] --config invalid UTF-8 | 2 | refused: --config: the config file is not UTF-8 text: save it as plain UTF-8 text | no | no |
| 18 | [rr] --config /dev/null | 2 | refused: --config: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 19 | [rr] --config /proc/self/environ | 2 | refused: DESK_DB_PATH, DESK_HUBSPOT_KEY_FILE, DESK_HUBSPOT_MAX_CALLS, REAL_HUBSPOT_READBACK_MAX_CALLS, DESK_SMTPP_HOST, DESK_SMTPP_USER, DES | no | no |
| 20 | [rr] --config given twice (same file) | -1 | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 21 | [rr] --config twice different files | -1 | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 22 | [rr] --config valid synthetic, tty (hang up at question) | -1 | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 23 | [rr] --config valid synthetic, no tty | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this script asks a question and needs | no | no |
| 24 | [rr] --config lower-case name | 2 | refused: --config: config line 1 is not NAME=VALUE with an upper-case name | no | no |
| 25 | [rr] --config NUL in value | -1 | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 26 | [rr] --config 1MB value DESK_DB_PATH | 2 | refused: the settings: a file or folder cannot be used (OSError) | no | no |
| 27 | [rr] --config 1MB value key file path | 2 | refused: DESK_HUBSPOT_KEY_FILE: the hubspot key file cannot be read | no | no |
| 28 | [rr] --config DB path ../ traversal | -1 | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 29 | [rr] --config DB path = existing dir | 2 | refused: DESK_DB_PATH: names a file that already exists: give a new database file for each run | no | no |
| 30 | [rr] --config DB path in read-only mount | -1 | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 31 | [rr] --config DB path :memory: | 4 | refused: DESK_DB_PATH: the lead book must be a file: ':memory:' is empty for every thread but the first | no | no |
| 32 | [rr] --config DB path under a file | 2 | refused: DESK_DB_PATH: a part of the folder path is a file, not a folder: the run folder cannot be made | no | no |
| 33 | [rr] --config key file = directory | 2 | refused: DESK_HUBSPOT_KEY_FILE: the hubspot key file cannot be read | no | no |
| 34 | [rr] --config key file = multiline | 2 | refused: DESK_HUBSPOT_KEY_FILE: the hubspot key file has more than one line: it must hold only the key | no | no |
| 35 | [rr] --config key file with NUL bytes | 2 | refused: DESK_HUBSPOT_KEY_FILE: the hubspot key file holds a key that is too short (at least 8 characters) | no | no |
| 36 | [rr] --config key file = FIFO | 2 | refused: DESK_HUBSPOT_KEY_FILE: is not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 37 | [rr] --config key file unicode path | -1 | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 38 | [rr] --config key file 1MB key | 2 | refused: DESK_HUBSPOT_KEY_FILE: the hubspot key file is too large: it must hold only the key | no | no |
| 39 | [rr] --config key file mode 000 (root ignores) | -1 | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 40 | [rr] --config remote host without allow flag (ALLOW_ANY=yes was in base: see note 11) | -1 | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: api.example,example.com,localhost (by design) |
| 41 | [rr] --config missing REQUIRED | 2 | refused: DESK_HUBSPOT_KEY_FILE, DESK_HUBSPOT_MAX_CALLS, REAL_HUBSPOT_READBACK_MAX_CALLS, DESK_SMTPP_HOST, DESK_SMTPP_USER, DESK_SMTPP_PASSWO | no | no |
| 42 | [rr] --config recipients unicode newline | 2 | refused: DESK_SMTPP_FROM: and DESK_SMTPP_RECIPIENTS must be plain ASCII addresses | no | no |
| 43 | [rr] --config REAL_PERSONS huge/neg/unicode | 2 | refused: REAL_PERSONS: is not a number | no | no |
| 44 | [rr] --config REAL_PERSONS -1 | 2 | refused: REAL_PERSONS: must be at least 8 | no | no |
| 45 | [rr] --config REAL_DRAIN_SECONDS nan | 2 | refused: REAL_DRAIN_SECONDS: is not a number | no | no |
| 46 | [rr] --config REAL_DRAIN_SECONDS 1e999 | 2 | refused: REAL_DRAIN_SECONDS: is not a number | no | no |
| 47 | [rr] --live-model without live settings | 2 | refused: DESK_LIVE_BASE_URL: not named in the settings; the default address is the vendor's and is never used on its own: name the address y | no | no |
| 48 | [rr] wrong order: --config before flag value missing | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 49 | [rr] unknown flag | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 50 | [rr] --assume-yes alone | 2 | refused: --assume-yes: only for the self-test (--dry-fakes); a real run always asks | no | no |
| 51 | [rr] --keep alone | 2 | refused: --keep: only for the self-test (--dry-fakes); a real run keeps its folder anyway | no | no |
| 52 | [rr] --assume-yes with --config | 2 | refused: --assume-yes: only for the self-test (--dry-fakes); a real run always asks | no | no |
| 53 | [rr] --dry-port-base huge, no tty | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this script asks a question and needs | no | no |
| 54 | [rr] --dry-port-base text, tty | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 55 | [rr] --dry-smtp-script 1MB, assume-yes [argv capped at 120000 chars: Linux refuses a single argument over 131072 bytes] | 124 | people: 8 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 56 | [rr] --dry-smtp-script unicode newline, assume-yes | 124 | people: 8 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 57 | [rr] --dry-fakes --assume-yes --keep (ref. run, folder in tmp) | 124 | people: 8 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 58 | [rr] --dry-fakes --assume-yes --cleanup | 124 | people: 8 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 59 | [rr] --dry-fakes with TMPDIR read-only mount | 0 | people: 8 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 60 | [rr] --dry-fakes with TMPDIR missing | 124 | people: 8 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 61 | [rr] env: hostile DESK_* env vars + --dry-fakes | 124 | people: 8 + a twin (same person, second address); desk processes: 2 (one crash) | no | secret no; address yes: 127.0.0.1,example.com,localhost (by design) |
| 62 | [live] no args | 2 | refused: --key-file, --ledger, --cap-run, --cap-total, --price-date, --model: not given | no | no |
| 63 | [live] empty string args | 2 | refused: --key-file, --ledger, --cap-run, --cap-total, --price-date, --model: not given | no | no |
| 64 | [live] good combo, no tty | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this script asks a question and needs | no | no |
| 65 | [live] good combo, tty (hang up at question) | -1 | models: 1, calls per model: 36, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 66 | [live] good combo + --assume-yes loopback | 3 | models: 1, calls per model: 1, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 67 | [live] --assume-yes with remote url | 2 | refused: --assume-yes: only for a test against this computer (a loopback --base-url) | no | no |
| 68 | [live] --base-url missing | 2 | refused: --base-url: not given; name the provider's address (a loopback address for a test) | no | no |
| 69 | [live] --base-url 1MB [argv capped at 120000 chars: Linux refuses a single argument over 131072 bytes] | 2 | refused: --base-url: must be an http(s) address with a host and no path | no | no |
| 70 | [live] --base-url unicode host | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this script asks a question and needs | no | no |
| 71 | [live] --base-url newline | 2 | refused: --assume-yes: only for a test against this computer (a loopback --base-url) | no | no |
| 72 | [live] --base-url bad port | 3 | models: 1, calls per model: 36, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 73 | [live] --base-url ipv6 bracket broken | 2 | refused: --assume-yes: only for a test against this computer (a loopback --base-url) | no | no |
| 74 | [live] --key-file empty file | 2 | refused: --key-file: the key file holds no key | no | no |
| 75 | [live] --key-file directory | 2 | refused: --key-file: the key file cannot be read | no | no |
| 76 | [live] --key-file FIFO | 2 | refused: --key-file: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 77 | [live] --key-file ../ traversal | 2 | refused: --key-file: the key file has more than one line: it must hold only the key | no | no |
| 78 | [live] --key-file 1MB path [argv capped at 120000 chars: Linux refuses a single argument over 131072 bytes] | 2 | refused: --key-file: the key file cannot be read | no | no |
| 79 | [live] --key-file 1MB content | 3 | models: 1, calls per model: 36, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 80 | [live] --key-file multiline | 2 | refused: --key-file: the key file has more than one line: it must hold only the key | no | no |
| 81 | [live] --key-file NUL bytes | 2 | refused: --key-file: the key file holds a key that is too short (at least 8 characters) | no | no |
| 82 | [live] --key-file binary | 2 | refused: --key-file: the key file cannot be read | no | no |
| 83 | [live] --key-file unicode path | 3 | models: 1, calls per model: 1, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 84 | [live] --key-file symlink loop | 2 | refused: --key-file: the key file cannot be read | no | no |
| 85 | [live] --key-file mode 000 (root ignores) | 3 | models: 1, calls per model: 1, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 86 | [live] --key-file same as --ledger | 2 | refused: --ledger: the spend ledger file cannot be read (damaged, too big, or not a file) | no | no |
| 87 | [live] --ledger directory | 2 | refused: --ledger: the spend ledger file cannot be read (damaged, too big, or not a file) | no | no |
| 88 | [live] --ledger FIFO | 2 | refused: --ledger: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 89 | [live] --ledger in read-only mount | 2 | models: 1, calls per model: 1, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 90 | [live] --ledger under a file | 2 | refused: --ledger: the spend ledger file cannot be read (damaged, too big, or not a file) | no | no |
| 91 | [live] --ledger 1MB of A content | 2 | refused: --ledger: the spend ledger file cannot be read (damaged, too big, or not a file) | no | no |
| 92 | [live] --ledger ../ traversal | 3 | models: 1, calls per model: 1, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 93 | [live] --ledger empty string | 2 | refused: --ledger: the spend ledger file cannot be read (damaged, too big, or not a file) | no | no |
| 94 | [live] --cap-run text / unicode | 2 | refused: --cap-run: is not a number | no | no |
| 95 | [live] --cap-run negative | 2 | refused: --cap-run: must be a positive number | no | no |
| 96 | [live] --cap-run 1e999999 | 2 | refused: --cap-run: is outside the allowed range | no | no |
| 97 | [live] --cap-run NaN | 2 | refused: --cap-run: must be a positive number | no | no |
| 98 | [live] --cap-total 1MB digits [argv capped at 120000 chars: Linux refuses a single argument over 131072 bytes] | 2 | refused: --cap-total: is outside the allowed range | no | no |
| 99 | [live] --cap-run > --cap-total | 2 | refused: --cap-run: is above --cap-total | no | no |
| 100 | [live] --model empty id | 2 | refused: --model: the model id must not be empty | no | no |
| 101 | [live] --model bad prices | 2 | refused: --model: needs ID=IN_PRICE,OUT_PRICE | no | no |
| 102 | [live] --model 1MB id [argv capped at 120000 chars: Linux refuses a single argument over 131072 bytes] | 2 | refused: --model: needs ID=IN_PRICE,OUT_PRICE | no | no |
| 103 | [live] --model unicode newline id | 3 | models: 1, calls per model: 36, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 104 | [live] --price-date whitespace | 2 | refused: --price-date: must not be empty | no | no |
| 105 | [live] --leads 0 / huge | 2 | refused: --leads: must be between 1 and 1000 | no | no |
| 106 | [live] --runs -1 | 2 | refused: --runs: must be between 1 and 100 | no | no |
| 107 | [live] --timeout nan | 2 | refused: --timeout: must be above 0 and at most the desk's AI call budget | no | no |
| 108 | [live] --max-tokens 0 | 2 | refused: --max-tokens: must be between 1 and the allowed maximum | no | no |
| 109 | [live] --effort 1MB [argv capped at 120000 chars: Linux refuses a single argument over 131072 bytes] | 3 | models: 1, calls per model: 36, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 110 | [live] wrong order: value flag last without value | 2 | refused: --model: needs a value | no | no |
| 111 | [live] --key-file given twice (same file) | 3 | models: 1, calls per model: 1, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 112 | [live] --model same model twice | 3 | models: 2, calls per model: 1, prices dated 2026-11-04 | no | secret no; address yes: 127.0.0.1 (by design) |
| 113 | [live] stray positional word | 2 | refused: the arguments: an option is unknown, ambiguous or has a stray value (see --help) | no | no |
| 114 | [live] key text as flag value of wrong flag | 2 | refused: --cap-run: is not a number | no | no |
| 115 | [pre] is_special_file(1MB path) | 0 | False | no | no |
| 116 | [pre] is_special_file(NUL path) | 0 | False | no | no |
| 117 | [pre] is_special_file(FIFO) | 0 | True | no | no |
| 118 | [pre] is_special_file(/dev/null) | 0 | True | no | no |
| 119 | [pre] is_special_file(empty string) | 0 | False | no | no |
| 120 | [pre] is_special_file(None) wrong type | 1 | TB: TypeError: stat: path should be string, bytes, os.PathLike or integer, not NoneType | yes | no |
| 121 | [pre] folder_part_is_a_file(under file) | 0 | True | no | no |
| 122 | [pre] folder_part_is_a_file(1MB) | 0 | False | no | no |
| 123 | [pre] folder_part_is_a_file(NUL) | 0 | False | no | no |
| 124 | [pre] folder_part_is_a_file(../ traversal) | 0 | False | no | no |
| 125 | [pre] same_file(same twice) | 0 | True | no | no |
| 126 | [pre] same_file(dir, dir) | 0 | True | no | no |
| 127 | [pre] same_file(symlink loop twice) | 0 | True | no | no |
| 128 | [pre] same_file(NUL, 1MB) | 0 | False | no | no |
| 129 | [pre] same_file(unicode, ../) | 0 | False | no | no |
| 130 | [pre] run as script: precheck.py (no main) | 0 | (no output) | no | no |

## Extended runs (timeout 240, detached, loopback, `env -i`, stdin /dev/null, --assume-yes with --dry-fakes only; never typed an answer)
| run | rc | wall | traceback |
|---|---|---|---|
| dry-plain | 0 | 65 s | no |
| dry-keep | 0 | 68 s | no |
| dry-smtp-452 | 3 | 95 s | no |
| dry-badsmtp-unicode | 0 | 68 s | no |
| dry-cleanup | 0 | 36 s | no |
| dry-port-low | 0 | 68 s | no |
| dry-port-huge | 2 | 1 s | no |
(dry-smtp-452 rc 3 = the scenario's own checks 2 and F1 FAIL, expected for a fake mail server that answers 452; not a crash.)

## Not run / limits
- Never answered the start question (hung up at it in 10 cases); so no run went past it with --config.
- Windows, ruff/mypy/bandit, pytest suite: not run (not in task). hubspot_probe.py, feed.py, crash_desk.py, reset scripts: not in task.
- File permission denial (root).
- Files: harness.py, raw-C2-run1.log, raw-C2-run2.log, rows-run2.json, ext-*.log, harness-run2.out, checkpoint.md.
- Commands: `python3 harness.py` (runs each case as `timeout 30 unshare -n env python3 lo_up-q4g.py <cmd>`; tty cases through a pty that is closed at the start question), `bash ext.sh`, `mount -t tmpfs` + remount ro + umount of tmp-C2/rodir, one direct python call for os.makedirs on a NUL path.
