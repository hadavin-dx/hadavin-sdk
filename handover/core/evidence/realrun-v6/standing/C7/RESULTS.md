# C7 hostile inputs, seed 2 - RESULTS (EVIDENCE RUNNER: no judging, nothing fixed)

Tree: /home/user/build/rr6/tree-C7 (head 61ded9e + 2 patches + survivor-tests-v1, not edited). Python: venv312. Every case: `timeout 30 unshare -n` (plain, as root, lo brought up by drivers/lo_up-q4g.py), env cleared to PATH/HOME/TMPDIR/PYTHONPATH/LANG. Harness: /home/user/build/rr6/tmp-C7/h.py (+ mk.py). Raw output per case: /home/user/build/rr6/out/C7/raw/NNN.txt; machine rows: /home/user/build/rr6/out/C7/results.jsonl. C2 folder was empty (nothing to avoid copying).
Cases run: 158 (the brief asked for 100; 100 first-pass cases + 58 added: pty variants, follow-ups for masked cases). Groups: A run_real_check arguments (no terminal) 26; B run_real_check --config under a pty 41; C run_live_check 33; D scripts/precheck.py functions 9; E src/lead_desk config readers 32; X follow-ups 17.

## Safety facts (what I did NOT do)
- No prompt was ever answered. In pty cases (B, A#21-26) the harness only reads, and when the start question text appeared it closed the terminal (exit -1 = SIGHUP). The question asks to type the HubSpot host; none typed. No `y`.
- run_live_check cases with `--assume-yes` (the script's own flag, loopback `--base-url` only, 127.0.0.1:1 or [::1]:1, nothing listens, fake key from parts): calls end in connection refused, exit 3. No network, no spend.
- Fake key: `sk-ant-` + `api03-` + `FAKE` + `PARTS` + `0001` (built from parts); fake addresses `probe.person@example.test` style, built from parts. Leak column = fake key, `sk-ant`, or any `x@y` pattern appearing in the output.
- Kernel limit: one argv or env string is at most 128 KB, so 1 MB values were placed in files (config line, key file) and 100-120 KB values in argv/env. 1 MB env vars were not possible.
- Not run: --dry-fakes with --assume-yes to the end (about 35 s, over the 30 s limit); no Windows; no full suite (brief: C7 only).

## Totals
- Exit codes: 2 (refused) 90; 3 (library RAISED, or call failed on loopback) 30; 0 (library accepted, or precheck printed) 24; -1 (start question reached, terminal closed by harness) 13; 124 (timeout 30) 1.
- Python tracebacks anywhere: 0 of 158 (group E and D run inside a try/except wrapper that prints `RAISED <Class>: first line`; the classes seen are SettingRefused/SendRefused only, no TypeError, UnicodeError, RecursionError or MemoryError).
- Hang: 1, case 137: `read_approvers(Path(FIFO))` called directly as a library function (no precheck in the library) blocked until `timeout 30` killed it (exit 124). The scripts' own precheck refuses a FIFO for config, key and ledger files (cases 32, 56, 89, 95: exit 2, 0.2 s).
- Secret or address printed: 2 cases, both are argparse echoes in run_real_check.py (stock argparse): #155 (fake key typed as the value of `--dry-port-base` is printed back in `invalid int value: '<key>'`) and #156 (fake address typed as a stray argument is printed back in `unrecognized arguments: <address>`). run_live_check.py (RefusingParser) prints neither (#157, #158). These only happen when the person types the secret on the command line. Config-file, key-file and environment paths: no leak in any case (including fake key as URL login in config #55 and in env #123/#134).

## Observations (reported, not judged; each with its case number)
1. run_real_check argparse echoes typed values (#155, #156, also #14-17 echo the odd flag text such as the Cyrillic lookalike). See above.
2. #21 `--dry-fakes --dry-port-base 99999` ends `refused: the settings: a file or folder cannot be used (OverflowError)`: the wording blames a file or folder; exit 2, no traceback.
3. #23, #24 `--dry-smtp-script` with percent/quote/newline text and with a Cyrillic lookalike of `final_452` are accepted (start question reached); I did not run further to see which behaviour the fake mail server then uses.
4. run_live_check accepts without a size or shape check: a 1 MB key file (#91 then exit 3, the call was tried), a key with NUL and CR (#92), a 100 KB model id (#84), a model id with percent/quote (#83), the same `--model` id twice with different prices (#82, "models: 2"), fullwidth digit price (#85), Arabic-Indic digit cap (#144). run_real_check refuses a too-large key file (#59, "too large"). Whether the live script's accepting is intended was not checked.
5. run_live_check accepts `--base-url` `http://[::1]:1` as loopback (#76).
6. Config.from_env (library) accepts: DESK_BIND with newline and ESC, or fullwidth digits (#121, #122), DESK_DB_PATH with NUL (#124, via dict only; a real environment cannot hold NUL), DESK_PORT `12\n` as 12 (#111). HubspotSettings.from_env accepts a base URL ending in a newline when DESK_HUBSPOT_ALLOW_ANY_BASE_URL=yes (#151, last line of raw/151.txt: `ACCEPTED` for `http://127.0.0.1:1\n` and for `HTTP://127.0.0.1:1`).
7. Library readers read_approvers/read_leadflow/read_secret_file have no special-file check themselves (case 137 hang, FIFO). The only guard found is in the scripts (precheck.py). `grep` of src/ for is_special_file/special_file printed no match.
8. tools/pathconfine documents NFC matching: an NFD-typed name found the NFC-stored file (#43: start question reached). A Cyrillic lookalike name was not matched (no such file).
9. Config parse of a single 1 MB value ends `refused: the settings: a file or folder cannot be used (OSError)` (generic text).
10. A pty `--dry-fakes` run killed at the start question leaves its `real-dry-*` temp folder in TMPDIR (5 folders under /home/user/build/rr6/tmp-C7/tmp; I removed them, my own folders only).

## Cleanup and process counts
- Scratch: only /home/user/build/rr6/tmp-C7 (cases/, tmp/, h.py, mk.py, show.py, table.md) and /home/user/build/rr6/out/C7. tree-C7 untouched (not edited). The superseded first run is in out/C7/run1-superseded/ (the first E-group run had no try/except wrapper: uncaught library ValueErrors showed as tracebacks; replaced by the wrapped run).
- Processes of mine left: 0 (checked with pgrep at the end; other agents' processes C2/BR were running and were not touched).

## Table (# | group | input | exit code | message first line | traceback | secret or address printed)
| # | grp | input | exit code | message first line | traceback | secret or address printed |
|---|---|---|---|---|---|---|
| 1 | A | flag value is a flag name: --config --dry-fakes | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 2 | A | --config=--dry-fakes (value glued) | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 3 | A | --config twice (two different missing paths) | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 4 | A | --dry-fakes twice + --keep twice | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 5 | A | --dry-port-base 99999999999999999999 | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 6 | A | --dry-port-base -1 | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 7 | A | --dry-port-base empty string | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 8 | A | --dry-port-base fullwidth digits | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 9 | A | --dry-smtp-script with 100 KB value (argv limit 128 KB) | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 10 | A | --dry-smtp-script percent/quote string %s%(x)s'"{} | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 11 | A | --assume-yes alone | 2 | refused: --assume-yes: only for the self-test (--dry-fakes); a real run always asks | no | no |
| 12 | A | --keep alone | 2 | refused: --keep: only for the self-test (--dry-fakes); a real run keeps its folder anyway | no | no |
| 13 | A | --assume-yes --keep (no --dry-fakes) | 2 | refused: --assume-yes: only for the self-test (--dry-fakes); a real run always asks | no | no |
| 14 | A | Cyrillic-o lookalike flag --cоnfig | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 15 | A | em dash lookalike —config | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 16 | A | fullwidth --ｄry-fakes | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 17 | A | argparse prefix abbreviation --dry (ambiguous: dry-fakes/dry-port-base/dry-smtp-script) | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 18 | A | abbreviation --conf with path | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 19 | A | single dash '-' and '--' only | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | no |
| 20 | A | --config '' (empty) and --config ' ' (space) | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 21 | A | PTY --dry-fakes --dry-port-base 99999 (port out of range) | 2 | refused: the settings: a file or folder cannot be used (OverflowError) | no | no |
| 22 | A | PTY --dry-fakes --dry-port-base 0 | -1 (start question reached, nothing answered, terminal closed) | people: 8 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 23 | A | PTY --dry-fakes --dry-smtp-script with percent/quote/newline | -1 (start question reached, nothing answered, terminal closed) | people: 8 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 24 | A | PTY --dry-fakes --dry-smtp-script lookalike 'fіnal_452' | -1 (start question reached, nothing answered, terminal closed) | people: 8 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 25 | A | PTY --dry-fakes --config /dev/zero (config ignored note) | -1 (start question reached, nothing answered, terminal closed) | note: --config is ignored with --dry-fakes (the self-test uses its own local fakes) | no | no |
| 26 | A | PTY --dry-fakes --config=--keep --keep | -1 (start question reached, nothing answered, terminal closed) | note: --config is ignored with --dry-fakes (the self-test uses its own local fakes) | no | no |
| 27 | B | control: good loopback config (expect: reaches the start question, nothing answered) | -1 (start question reached, nothing answered, terminal closed) | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 28 | B | config is a directory | 2 | refused: --config: --config: names a folder, not a file | no | no |
| 29 | B | config is /dev/null | 2 | refused: --config: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 30 | B | config is /dev/zero (endless) | 2 | refused: --config: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 31 | B | config is /dev/full | 2 | refused: --config: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 32 | B | config is a FIFO with no writer | 2 | refused: --config: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 33 | B | config is a symlink loop a->b->a | 2 | refused: --config: --config: a link on the path does not resolve (a loop) | no | no |
| 34 | B | config is a symlink to a directory | 2 | refused: --config: --config: names a folder, not a file | no | no |
| 35 | B | config is a symlink to a good config | -1 (start question reached, nothing answered, terminal closed) | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 36 | B | config file literally named --dry-fakes in cwd, passed as ./--dry-fakes | -1 (start question reached, nothing answered, terminal closed) | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 37 | B | config file named --dry-fakes passed with = form | -1 (start question reached, nothing answered, terminal closed) | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 38 | B | relative path with .. that escapes upward (../../../../etc/passwd) | 2 | refused: --config: --config: no such file | no | no |
| 39 | B | relative path with .. that returns to the good file | -1 (start question reached, nothing answered, terminal closed) | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 40 | B | path with percent signs and quotes: real%s'"%(x)s.env | -1 (start question reached, nothing answered, terminal closed) | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 41 | B | path 5000 characters long (ENAMETOOLONG) | 2 | refused: --config: --config: path too long | no | no |
| 42 | B | path holding a newline and an ESC character | 2 | refused: --config: --config: contains a control character | no | no |
| 43 | B | NFC name exists, NFD lookalike referenced (e-acute) | -1 (start question reached, nothing answered, terminal closed) | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 44 | B | Cyrillic lookalike filename vs latin name (real.env vs rеal.env) | 2 | refused: --config: --config: no such file | no | no |
| 45 | B | config 1 MB single line with no '=' | 2 | refused: --config: config line 1 is not NAME=VALUE with an upper-case name | no | no |
| 46 | B | config with one value of 1 MB (DESK_DB_PATH) | 2 | refused: the settings: a file or folder cannot be used (OSError) | no | no |
| 47 | B | config with NUL bytes inside a value | 2 | refused: DESK_PORT: is not a number | no | no |
| 48 | B | config with invalid UTF-8 bytes | 2 | refused: --config: the config file is not UTF-8 text: save it as plain UTF-8 text | no | no |
| 49 | B | config with UTF-8 BOM first | 2 | refused: --config: config line 1 is not NAME=VALUE with an upper-case name | no | no |
| 50 | B | config with CRLF line ends and lone CR | 2 | refused: DESK_BIND: is not a loopback address while a real service is set (crm, mail): anyone who can reach th | no | no |
| 51 | B | config line with ESC sequence and fake key in the bad line (must not be echoed) | 2 | refused: --config: config line 19 is not NAME=VALUE with an upper-case name | no | no |
| 52 | B | config with duplicated names (second wins?) DESK_HUBSPOT_MAX_CALLS twice | 2 | refused: DESK_HUBSPOT_MAX_CALLS: must be between 1 and 10000 | no | no |
| 53 | B | config value with unmatched / lone quote and doubled quote chars | 2 | refused: DESK_SMTPP_FROM: and DESK_SMTPP_RECIPIENTS must be plain ASCII addresses | no | no |
| 54 | B | config values with Unicode lookalike loopback host (127.0.0.1 fullwidth / localhost with Cyrillic o) | 2 | refused: DESK_HUBSPOT_BASE_URL: plain http is allowed for a loopback address only | no | no |
| 55 | B | config HUBSPOT base url holds fake key as login: http://user:KEY@127.0.0.1:1 | 2 | refused: DESK_HUBSPOT_BASE_URL: must hold no query, fragment or login | no | no |
| 56 | B | config key file is a FIFO with no writer | 2 | refused: DESK_HUBSPOT_KEY_FILE: is not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 57 | B | config key file is a symlink loop | 2 | refused: DESK_HUBSPOT_KEY_FILE: the hubspot key file cannot be read | no | no |
| 58 | B | config key file is /dev/null and password file is a directory | 2 | refused: DESK_HUBSPOT_KEY_FILE: is not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 59 | B | config key file holds 1 MB of fake key text | 2 | refused: DESK_HUBSPOT_KEY_FILE: the hubspot key file is too large: it must hold only the key | no | no |
| 60 | B | config DESK_DB_PATH is /dev/null / :memory: / existing dir | 2 | refused: DESK_DB_PATH: names a file that already exists: give a new database file for each run | no | no |
| 61 | B | config DESK_DB_PATH relative with .. and a percent sign | -1 (start question reached, nothing answered, terminal closed) | people: 12 + a twin (same person, second address); desk processes: 2 (one crash) | no | no |
| 62 | B | config numbers: REAL_DRAIN_SECONDS=nan, REAL_PERSONS=1e3, DESK_PORT=８０ | 2 | refused: REAL_PERSONS: is not a number | no | no |
| 63 | B | config lower-case name and name with Cyrillic letter (DESK_DБ) | 2 | refused: --config: config line 19 is not NAME=VALUE with an upper-case name | no | no |
| 64 | B | config + --live-model flag, qualifier forced, no live settings | 2 | refused: DESK_LIVE_BASE_URL: not named in the settings; the default address is the vendor's and is never used  | no | no |
| 65 | B | config + --cleanup --cleanup --live-model --live-model (duplicates) | 2 | refused: DESK_LIVE_BASE_URL: not named in the settings; the default address is the vendor's and is never used  | no | no |
| 66 | B | config /proc/self/environ (regular file with NULs) | 2 | refused: DESK_DB_PATH, DESK_HUBSPOT_KEY_FILE, DESK_HUBSPOT_MAX_CALLS, REAL_HUBSPOT_READBACK_MAX_CALLS, DESK_SM | no | no |
| 67 | B | config is a unix socket | 2 | refused: --config: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 68 | C | control: refuses without a terminal (no --assume-yes) | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 69 | C | --base-url twice (second is real-looking host, first loopback) with --assume-yes | 2 | refused: --assume-yes: only for a test against this computer (a loopback --base-url) | no | no |
| 70 | C | --base-url with fake key as login + --assume-yes | 2 | refused: --base-url: must be an http(s) address with a host and no path | no | no |
| 71 | C | --base-url 127.0.0.1%2f..@evil.example.invalid (percent + userinfo trick) + --assume-yes | 2 | refused: --assume-yes: only for a test against this computer (a loopback --base-url) | no | no |
| 72 | C | --base-url http://127.0.0.1:1@evil.example.invalid + --assume-yes | 2 | refused: --assume-yes: only for a test against this computer (a loopback --base-url) | no | no |
| 73 | C | --base-url Unicode lookalike localhost (lоcalhost) + --assume-yes | 2 | refused: --assume-yes: only for a test against this computer (a loopback --base-url) | no | no |
| 74 | C | --base-url 100 KB long loopback URL + --assume-yes | 2 | refused: --base-url: must be an http(s) address with a host and no path | no | no |
| 75 | C | --base-url with newline and ESC chars | 2 | refused: --assume-yes: only for a test against this computer (a loopback --base-url) | no | no |
| 76 | C | --base-url IPv6 loopback http://[::1]:1 + --assume-yes | 3 | models: 1, calls per model: 1, prices dated 2026-11-13 | no | no |
| 77 | C | --cap-run nan / --cap-total inf | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 78 | C | --cap-run 1e999 and --cap-total -0 | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 79 | C | --cap-run Arabic-Indic digits ٠.٠٥ | 2 | refused: standard input: it is not a terminal (a pipe, a file, the NUL device or a scheduled job), but this sc | no | no |
| 80 | C | --cap-total with percent and quote 5%' | 2 | refused: --cap-total: is not a number | no | no |
| 81 | C | --leads 0 and --runs 99999999999999999999 | 2 | refused: --leads: must be between 1 and 1000 | no | no |
| 82 | C | --model twice with the same id and different prices | 3 | models: 2, calls per model: 1, prices dated 2026-11-13 | no | no |
| 83 | C | --model with percent/quote id: 'a%s"b=1,5' | 3 | models: 1, calls per model: 1, prices dated 2026-11-13 | no | no |
| 84 | C | --model id of 100 KB | 3 | models: 1, calls per model: 1, prices dated 2026-11-13 | no | no |
| 85 | C | --model price with Unicode digits and NFKC lookalike '1,５' | 3 | models: 1, calls per model: 1, prices dated 2026-11-13 | no | no |
| 86 | C | --key-file named like a flag: --key-file=--ledger and a file of that name | 3 | models: 1, calls per model: 1, prices dated 2026-11-13 | no | no |
| 87 | C | --key-file is a directory | 2 | refused: --key-file: the key file cannot be read | no | no |
| 88 | C | --key-file /dev/null | 2 | refused: --key-file: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 89 | C | --key-file FIFO with no writer | 2 | refused: --key-file: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 90 | C | --key-file symlink loop | 2 | refused: --key-file: the key file cannot be read | no | no |
| 91 | C | --key-file 1 MB of key text | 3 | models: 1, calls per model: 1, prices dated 2026-11-13 | no | no |
| 92 | C | --key-file key with NUL and trailing CR | 3 | models: 1, calls per model: 1, prices dated 2026-11-13 | no | no |
| 93 | C | --key-file relative path with .. back to the file | 3 | models: 1, calls per model: 1, prices dated 2026-11-13 | no | no |
| 94 | C | --ledger is a directory | 2 | refused: --ledger: the spend ledger file cannot be read (damaged, too big, or not a file) | no | no |
| 95 | C | --ledger FIFO with no writer | 2 | refused: --ledger: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 96 | C | --ledger /dev/null | 2 | refused: --ledger: not a regular file (a pipe, a device or a socket would block): give a file | no | no |
| 97 | C | --ledger symlink loop | 2 | refused: --ledger: the spend ledger file cannot be read (damaged, too big, or not a file) | no | no |
| 98 | C | --ledger same path as --key-file (key file overwritten?) | 2 | refused: --ledger: the spend ledger file cannot be read (damaged, too big, or not a file) | no | no |
| 99 | C | --price-date and --effort whitespace/control chars | 2 | refused: --price-date: must not be empty | no | no |
| 100 | C | --timeout nan, --max-tokens -5 | 2 | refused: --timeout: must be above 0 and at most the desk's AI call budget | no | no |
| 101 | D | is_special_file on NUL-containing path | 0 | False | no | no |
| 102 | D | is_special_file on 1 MB path | 0 | False | no | no |
| 103 | D | is_special_file on /dev/null, /dev/zero, /dev/tty, /proc/self/mem | 0 | [True, True, True, False] | no | no |
| 104 | D | is_special_file on symlink loop | 0 | False | no | no |
| 105 | D | folder_part_is_a_file with a part that is a file and NUL path | 0 | True False | no | no |
| 106 | D | folder_part_is_a_file on 1 MB path and relative .. chain | 0 | False False | no | no |
| 107 | D | same_file with loop, NUL, bytes-vs-str | 0 | True False False | no | no |
| 108 | D | same_file NFC vs NFD names and Cyrillic lookalike | 0 | False False | no | no |
| 109 | D | is_special_file with surrogate-escape lone surrogate path and int | 0 | False False | no | no |
| 110 | E | DESK_PORT fullwidth digits (os env) | 3 | RAISED SettingRefused: DESK_PORT is not a number | no | no |
| 111 | E | DESK_PORT '12\n' newline suffix | 0 | Config(db_path=PosixPath('data/desk.sqlite3'), bind='127.0.0.1', port=12, adapters='demo', fakes_host='127.0.0 | no | no |
| 112 | E | DESK_PORT '1_000' and hex '0x10' | 3 | RAISED SettingRefused: DESK_PORT is not a number | no | no |
| 113 | E | DESK_SEND_TIMEOUT_SECONDS nan / inf / 1e999 | 3 | RAISED SettingRefused: DESK_SEND_TIMEOUT_SECONDS is not a number | no | no |
| 114 | E | DESK_SEND_TIMEOUT_SECONDS '١٢' Arabic-Indic | 3 | RAISED SettingRefused: DESK_SEND_TIMEOUT_SECONDS is not a number | no | no |
| 115 | E | DESK_SIZE_CAP_BYTES 120 KB digit string | 3 | RAISED SettingRefused: DESK_SIZE_CAP_BYTES is not a number | no | no |
| 116 | E | DESK_FAKES_URL with fake key as login and percent signs | 3 | RAISED SettingRefused: DESK_FAKES_URL has a bad port | no | no |
| 117 | E | DESK_FAKES_URL with NUL, newline (dict) | 3 | RAISED SettingRefused: DESK_FAKES_URL has a bad port | no | no |
| 118 | E | DESK_FAKES_URL https lookalike scheme 'httр://' and path | 3 | RAISED SettingRefused: DESK_FAKES_URL must use http | no | no |
| 119 | E | DESK_FAKES_URL 120 KB host | 3 | RAISED SettingRefused: DESK_FAKES_HOST (or DESK_FAKES_URL) must be this computer: localhost or a loopback addr | no | no |
| 120 | E | DESK_FAKES_URL IPv6 zone id and brackets http://[fe80::1%25eth0]:1 | 3 | RAISED SettingRefused: DESK_FAKES_HOST (or DESK_FAKES_URL) must be this computer: localhost or a loopback addr | no | no |
| 121 | E | DESK_BIND with ESC/newline and 0.0.0.0 lookalike | 0 | Config(db_path=PosixPath('data/desk.sqlite3'), bind='0.0.0.0\n\x1b[31m', port=8765, adapters='demo', fakes_hos | no | no |
| 122 | E | DESK_BIND fullwidth '０.０.０.０' | 0 | Config(db_path=PosixPath('data/desk.sqlite3'), bind='０.０.０.０', port=8765, adapters='demo', fakes_host='127.0.0 | no | no |
| 123 | E | DESK_ALLOWED_HOSTS lookalike + empty entries + 120 KB | 3 | RAISED SettingRefused: DESK_ALLOWED_HOSTS holds a name that is not a lower-case host name | no | no |
| 124 | E | DESK_DB_PATH with NUL (dict) | 0 | Config(db_path=PosixPath('a\x00b.db'), bind='127.0.0.1', port=8765, adapters='demo', fakes_host='127.0.0.1', f | no | no |
| 125 | E | DESK_DB_PATH 120 KB, percent and quote | 0 | Config(db_path=PosixPath('%s\'"ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd | no | no |
| 126 | E | DESK_QUALIFIER / DESK_ADAPTERS with control chars and 'live_claude\n' | 3 | RAISED SettingRefused: DESK_ADAPTERS must be one of demo | no | no |
| 127 | E | DESK_QUALIFIER live_claude with all DESK_LIVE_* hostile (key file loop, base url with fake key login, nan caps) | 3 | RAISED SettingRefused: DESK_LIVE_PRICE_DATE is required for the live model | no | no |
| 128 | E | DESK_APPROVERS_FILE / DESK_LEADFLOW_FILE point at /dev/zero and a FIFO-ish path | 3 | RAISED SettingRefused: DESK_APPROVERS_FILE is set but DESK_LATER_MODE is not approval | no | no |
| 129 | E | DESK_CRM=hubspot with fake key in base url and 1 MB-class max calls | 0 | Config(db_path=PosixPath('data/desk.sqlite3'), bind='127.0.0.1', port=8765, adapters='demo', fakes_host='127.0 | no | no |
| 130 | E | read_approvers: 1 MB of JSON text | 3 | RAISED SettingRefused: the approvers file is too big | no | no |
| 131 | E | read_approvers: deep nesting [[[[ x 200000 | 3 | RAISED SettingRefused: the approvers file is too big | no | no |
| 132 | E | read_approvers: NUL, lone surrogate escapes, fake address | 0 | OK tuple | no | no |
| 133 | E | read_approvers: invalid UTF-8 bytes | 3 | RAISED SettingRefused: the approvers file is not valid JSON text | no | no |
| 134 | E | read_leadflow: JSON big number 1e999 and NaN literals | 3 | RAISED SettingRefused: DESK_LEADFLOW_FILE: rota and steps must be lists | no | no |
| 135 | E | read_leadflow: deep nesting {"a": x 100000 | 3 | RAISED SettingRefused: DESK_LEADFLOW_FILE is too big | no | no |
| 136 | E | read_leadflow: duplicated keys and lookalike key 'rоta' | 3 | RAISED SettingRefused: DESK_LEADFLOW_FILE needs exactly the keys rota, steps, closed, first, after_followup, r | no | no |
| 137 | E | read_approvers on a FIFO with no writer (library, no precheck) | 124 (timeout 30 killed it) | (no output) | no | no |
| 138 | E | read_leadflow on a symlink loop and on a directory | 0 | SettingRefused DESK_LEADFLOW_FILE cannot be read | no | no |
| 139 | E | read_secret_file on FIFO / 1 MB / NUL / loop (library, no precheck) | 0 | SendRefused the smtp password file is too large: it must hold only the password | no | no |
| 140 | E | HubspotSettings.from_env with lookalike/percent URLs and float nan timeout | 0 | SettingRefused DESK_HUBSPOT_TIMEOUT_SECONDS is not a number | no | no |
| 141 | E | ProviderSettings.from_env: recipients with fake address, 120 KB list, quotes and CR | 0 | SettingRefused DESK_SMTPP_FROM and DESK_SMTPP_RECIPIENTS must be plain ASCII addresses | no | no |
| 142 | X | LIVE --assume-yes --cap-run nan --cap-total inf | 2 | refused: --cap-run: must be a positive number | no | no |
| 143 | X | LIVE --assume-yes --cap-run 1e999 --cap-total -0 | 2 | refused: --cap-run: is outside the allowed range | no | no |
| 144 | X | LIVE --assume-yes --cap-run Arabic-Indic digits | 3 | models: 1, calls per model: 1, prices dated 2026-11-13 | no | no |
| 145 | X | LIVE --assume-yes --cap-run sNaN / --cap-total Infinity | 2 | refused: --cap-run: must be a positive number | no | no |
| 146 | X | LIVE --assume-yes --model price nan,inf | 2 | refused: --model: the input price must be a positive number | no | no |
| 147 | X | LIVE --assume-yes --model price negative -1,-5 | 2 | refused: --model: the input price must be a positive number | no | no |
| 148 | X | LIVE --assume-yes --cap-run 0.05 --cap-total 0.01 (run cap above total) | 2 | refused: --cap-run: is above --cap-total | no | no |
| 149 | X | LIVE --assume-yes --max-tokens 9999999999999999999999 | 2 | refused: --max-tokens: must be between 1 and the allowed maximum | no | no |
| 150 | X | LIVE --assume-yes ledger path under a regular file (a/b where a is a file) | 2 | refused: --ledger: the spend ledger file cannot be read (damaged, too big, or not a file) | no | no |
| 151 | X | HubspotSettings.from_env URL list (no nan timeout) | 0 | SettingRefused DESK_HUBSPOT_BASE_URL must hold no percent sign in the host | no | no |
| 152 | X | read_approvers: nesting 8000 deep (under size cap) | 0 | SettingRefused the approvers file needs a list named approvers (and a text label, if any) | no | no |
| 153 | X | read_leadflow: nesting 8000 deep inside a key | 0 | SettingRefused DESK_LEADFLOW_FILE needs exactly the keys rota, steps, closed, first, after_followup, reminder_ | no | no |
| 154 | X | read_approvers: 5000 digit integer and 1e999 as ids | 0 | SettingRefused the approvers file is not valid JSON text | no | no |
| 155 | X | run_real_check: fake key typed as the value of --dry-port-base (argparse echo test) | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | key |
| 156 | X | run_real_check: fake address typed as an unknown argument | 2 | usage: run_real_check.py [-h] [--config CONFIG] [--dry-fakes] [--live-model] | no | address:probe.person@example.test |
| 157 | X | run_live_check: fake key typed as value of --leads and as unknown argument | 2 | refused: --leads: must be a whole number | no | no |
| 158 | X | run_live_check: fake address typed as unknown argument | 2 | refused: the arguments: an option is unknown, ambiguous or has a stray value (see --help) | no | no |
