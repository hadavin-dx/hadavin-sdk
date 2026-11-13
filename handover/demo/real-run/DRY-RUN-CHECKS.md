# Dry-run checks of the take scripts (queue item Q4)

Repo: hadavin-dx/duplicate-proof-lead-desk-n8n, branch `pr-3-tests`, head `2db3926` (clone `/tmp/work/q4-base`, not modified, nothing committed).
Run: 2026-11-13, one full run of `run-dry-checks.sh` with 2 passes (224 case results), venv `/tmp/work/int2-venv`.
Who judged: nobody. This file records what the scripts did next to what the docs say; the lead's EGM reviewers judge it (EVIDENCE RUNNER role, R-numbers not looked up: no bible folder was reachable from this sandbox, so no R-number is cited).
Not committed, no PR, no sub-agent. Every process this work started was stopped; `ps` after the run shows none of ours; the temp dir is deleted by the script; the ports used are closed (a case checks it).

## What was and was not allowed to run

Made-up data only. Every command ran under `env -i` (no proxy variable, no real key, nothing inherited), in a temp folder. Keys are `made-up-key-0001` and similar, built at run time by `make_synthetic_config.py` from `scripts/real-run.env.example`; every output of every case is searched for them (never found). Addresses used: `127.0.0.1`, `localhost`, and `192.0.2.1` (documentation range, only given to settings that are refused before any call).

NOT run, on purpose (these are the real paths):

| Script | Real path (needs a real service) |
|---|---|
| `run_real_check.py` | `--config` with real hosts, answered `y`; `--live-model` with a real model address; `--cleanup` after such a run |
| `hubspot_probe.py` | `--yes-spend-calls 7` without `--dry-run` (calls the real HubSpot host) |
| `run_live_check.py` | answering `y` against the provider's address |
| `reset.ps1`, `start_all.ps1` | `pwsh` is not installed here: not run at all (only the bash twins ran) |

The only `y` answers given went to configs where every address is `127.0.0.1:1` or `localhost:1` (nothing listens there): the four `rrc-y-*` cases and nothing else.

## 1. Documentation says X but the script does Y (failures first)

| # | Doc claim (file:line) | What the script does (evidence) | Severity |
|---|---|---|---|
| D1 | `docs/settings.md:3` "A bad value stops the start with an error." and `:82` (HubSpot key file: one line, at least 8 characters, no spaces) and `:116` (the real-run script "refuses to start (exit code 2)" on a bad setting). | A key file that is missing, has two lines or is shorter than 8 characters is NOT checked at start, neither by the desk nor by `run_real_check.py`. The file is opened at the first CRM call (`src/lead_desk/crm_hubspot.py:254`). With answer `y` the script ran the whole sequence (about 75 s, two desk processes, 13 leads taken into the book, every follow-up failing with `CrmConfigError`) and ended with exit 3 and the note "The desk created an unknown number of contacts ... Archive them by hand", although the key was never usable and the first CRM call had failed. Evidence: `evidence-q4-rrc.txt`, cases `rrc-y-keyfile-missing`, `rrc-y-keyfile-2line`, `rrc-y-keyfile-short`; desk alone: started and listened with a missing key file (run by hand, exit 124 from `timeout`, no refusal). The key text never appears in any output (checked). Effect on a real run: a typo in the key file path is found only after the person answered `y` and the mailboxes were polled; the closing note sends the person looking for contacts that were never created. | Medium: the refusal comes late and the final message misleads; no secret leaks. |
| D2 | `docs/settings.md:7` ":memory: is refused at start, exit code 4, before any file is made" and `:116` (`DESK_DB_PATH` "must name a file that does NOT exist yet"). | The desk itself obeys (exit 4, no file: cases `dsk-memory-refused*`). `run_real_check.py` does not check this: `DESK_DB_PATH=:memory:` passes every check and the `y/N` question (`rrc-y-memory`), the desk then ends while starting, the script prints "the desk ended while starting" and exits 3 (docs table `settings.md:120` has no line for this case), and the run folder is the current folder, so `desk-1.log` is written into the working directory. | Low |
| D3 | `docs/real-services.md:20` "Failure tables print no address and no setting value" and the script docstring "It never prints a key, an address or a message text" (`scripts/run_real_check.py:33`). | A config file that is not UTF-8 gives `refused: UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0 ...`: one byte value and its position from the file are printed (the `ValueError` text is passed on, `run_real_check.py` `_run` except block). No key text leaks in any other case (including a key written as a config line, as a number, and inside a host name). | Low (one byte of a file that is not a config) |
| D4 | `docs/real-services.md:9`/`:20` and `docs/settings.md:120` document exit codes and "no terminal" behaviour for `run_real_check.py` (exit 1 with a clear line when no terminal answers). | `scripts/run_live_check.py` does not do the same: with no terminal (`</dev/null`) it ends with a Python traceback (`EOFError` at line 153, `input("Start? [y/N] ")`), exit 1. The docs list no exit codes for this script at all (`settings.md:121` ends with its flags only), so this contradicts no sentence, but it is the one take script that prints a traceback on a missing terminal. | Low |
| D5 | Script docstring `run_live_check.py` and `settings.md:96` (key file required, "keep it outside the repository"), `settings.md:111` (a key shorter than 8 characters is refused). | A missing, two-line or empty key file is not refused before the question, and after `y` against a dead loopback address the script ends with exit 0 and "valid labels 0 (0%) ... errors by class: {'LiveTransport': 2}": a run where every call failed is reported as exit 0. The per-line message names only the error class (no key text: checked). Not a contradiction of a sentence in the docs (no exit code is documented), but the exit code 0 cannot be read as "the check worked". | Low to medium |
| D6 | `docs/real-services.md:11` and `scripts/real-run.env.example:7` say the run folder holds the logs and `result.json` and should be deleted afterwards. | For `--dry-fakes` the folder `real-dry-XXXX/` (desk.db, desk.db.lock, desk.db-wal/-shm, two desk logs, `*.hubspot.json`, `*.smtp.json`, result.json) is created in the temp directory and never removed by the script (the script prints only the path of `result.json`). Each run leaves one more folder (14 entries each); repeat runs do not clash (new random name). `reset_check`/`reset.sh` do not know about it. No lock is held (no process). | Low |

Checked and in agreement with the docs (no deviation): every missing required name gives exit 2 and names the setting (14 cases); `REAL_PERSONS` below 8 or above 1000, non-number, `REAL_HUBSPOT_READBACK_MAX_CALLS` below 5, caps 0 or above 10000, timeout above 9, port above 65535, `starttls`/`ssl` value, mailbox user not equal to the n-th recipient, a seconds value 0 or `nan`, a folder name with a backslash, an existing database file, a lower-case name, a line with no `=` (`settings.md:116-119`, `real-run.env.example`); a public or a non-loopback `http` HubSpot address and `https://127.0.0.1` are refused (`real-run.env.example:17-19`); `--assume-yes` without `--dry-fakes` is refused (exit 2); a valid-looking config stops at `y/N` with exit 1 and says nothing was called, with no terminal or with `n` (`settings.md:120`); the config's `DESK_QUALIFIER=live_claude` is overridden to the recorded replies without `--live-model` (`settings.md:118`); `--live-model` with no live settings, with a public provider address, with `http` to a non-loopback address: exit 2 (`settings.md:100`); `hubspot_probe.py`: `--plan` exit 0 with 7, a wrong count, a token name that looks like a token, a token with a space, a non-loopback or `https` `--dry-run` (also `http://127.0.0.1@192.0.2.1`), an abbreviated flag and a token given as an argument are all refused with exit 2 and no echo of the value; against the loopback stub the happy path makes exactly 7 calls in the documented order and prints PASS for all six questions; a stub that refuses the owner list gives FAIL and uses 6 calls (`docs/hubspot-probe.md:4`); a stub that echoes the token in an error text gets `***`; a lost create answer falls back to delete-by-email; desk settings refusals exit 4 (`settings.md:7,8,18`) and make no file; `reset.sh` exit codes 2, 3, 4, 6 and `reset done` with all files, pid files and processes gone, twice in a row (`README.md:88`); an empty `RESET_STOP_WAIT_SECONDS` means 10 (`README.md:88`); `start_all.sh` refuses a second start (`pid files exist`) and a wrong mode (exit 1).

Not reached: README exit 5 (a process that does not stop in time), the `ps`-missing refusal (exit 3), the unreadable-folder refusal (exit 3), `--dry-port-base`, and the real-account assumptions (`UNVERIFIED` in `docs/hubspot-probe.md`).

## 2. Table: script | path | command | exit | matches docs? | notes

Full per-case rows (224 results, command, expected and actual exit, note): `results.tsv`. Last 30 lines of output of every case: `evidence-q4-<rrc|rlc|hsp|dsk|rst>.txt`. Counts: rrc 124 (112 match, 12 known mismatches), rlc 22 (18, 4), hsp 38 (38), dsk 8 (8), rst 34 (32 match, 2 skipped). A case shows `FAIL(known)` when it is one of D1 to D6.

| Script | Path (dry) | Command (short) | Exit | Matches docs? | Notes |
|---|---|---|---|---|---|
| run_real_check.py | `--help` | `--help` | 0 | yes | prints the docstring |
| run_real_check.py | no arguments | (none) | 2 | yes | "give --config or --dry-fakes" |
| run_real_check.py | `--assume-yes` without dry | `--assume-yes [--config C]` | 2 | yes | refused |
| run_real_check.py | config unreadable | missing file, a directory, `/dev/null`, non-UTF-8 | 2 | yes except D3 | error class name only (D3: one byte value for non-UTF-8) |
| run_real_check.py | config content | lower-case name, line without `=`, line that is a key | 2 | yes | the line number only, no text |
| run_real_check.py | each missing required name | 14 configs | 2 | yes | names the missing setting |
| run_real_check.py | bad numbers and settings | 22 configs (list in section 1) | 2 | yes | names the setting, never the value |
| run_real_check.py | hosts | public `https`, public `http`, `https` to loopback, key text in host | 2 | yes | vendor domains only |
| run_real_check.py | prompt | valid-looking config, stdin empty / `n` / `n` with `--cleanup` | 1 | yes | "nothing was called"; the worst-case numbers are printed first (no call) |
| run_real_check.py | `--live-model` | no live settings; public provider address; loopback + `n` | 2, 2, 1 | yes | worst-case dollars printed before `y/N` |
| run_real_check.py | `--dry-fakes --assume-yes` | self-test | 0 | yes | "ALL CHECKS HOLD", 35 s, 8 people + twin, crash at point D2 (exit 137 as designed) |
| run_real_check.py | `--dry-fakes` (no assume) | stdin empty | 1 | yes | still asks |
| run_real_check.py | `--dry-fakes --config C` | | 0 | yes | prints that the config is ignored |
| run_real_check.py | `--dry-fakes --dry-smtp-script final_452` | mail server that always ends in doubt | 3 | yes | "AT LEAST ONE CHECK FAILED" (checks 2 and F1), no address or key in the output |
| run_real_check.py | `y` with a dead loopback address | missing / 2-line / short key file | 3 (docs expect a refusal, 2) | NO (D1) | 75 s each |
| run_real_check.py | `y`, `DESK_DB_PATH=:memory:` | | 3 | NO (D2) | 0.5 s |
| run_live_check.py | `--help`, no args, bad flags | | 0, 2 | yes | argparse |
| run_live_check.py | provider address checks | public `https`, public `http`, cap run above total, bad `--model`, `--leads 0` | 2 | yes | same words as `settings.md:100` |
| run_live_check.py | prompt | `n` | 1 | yes | prints worst-case dollars first |
| run_live_check.py | prompt, no terminal | stdin empty | 1 with traceback | NO (D4) | |
| run_live_check.py | key file problems | missing, two lines (with `n`) | 1 (prompt reached) | not documented (D5) | key checked only after `y` |
| hubspot_probe.py | `--help`, `--plan` | | 0 | yes | "planned calls: 7" |
| hubspot_probe.py | refusals | wrong or missing count, token name that is a token, token with space, bad flags, token as argument, abbreviation, non-loopback/https/userinfo `--dry-run` | 2 | yes | nothing echoed |
| hubspot_probe.py | loopback stub, 4 modes (`probe_stub.py`) | happy, owners 403, token echoed in error, create answer lost | 0, 1, 1, 1 | yes | 7 / 6 / 3 / 4 calls; `***` for the echoed token |
| hubspot_probe.py | dead loopback port | `--dry-run http://127.0.0.1:9` | 1 | yes | no traceback |
| reset_check.py | free ports, no lock / port answering / lock held / `:memory:` | with `PYTHONPATH=src:.` | 0 / 4 / 3 / 0 | yes (`README.md:88`) | without `PYTHONPATH` it stops with `ModuleNotFoundError` (it is meant to be started by reset.sh) |
| reset.sh | stop and delete, twice; empty wait value | in a copy of the repo | 0 | yes | data folder empty, processes and ports gone |
| reset.sh | refusals | database outside data/, wait `08`, wait `1000`, pid file naming another program | 2, 2, 2, 6 | yes | nothing stopped or deleted; the other program was started and stopped by the check |
| start_all.sh | start, second start, bad mode | in a copy of the repo | 0, 1, 1 | yes | desk answers `/counts` with zeros |
| reset.ps1, start_all.ps1 | | | not run | n/a | no `pwsh` here |
| lead_desk.server (desk) | `:memory:`, port 99999, non-loopback bind with a real service, non-loopback fakes host | `python -m lead_desk.server` | 4 | yes (`settings.md:7,8,18`) | no file made |

Repeatability: the whole set ran twice in fresh temp folders; every case gave the same exit code and the same normalised output (numbers, paths and random hex removed); for `--dry-fakes` the pass/fail column of every check was equal. Strays: after each pass the working folder was unchanged for every case except the `y` and dry cases (listed: D2's `desk-1.log`, D6's folder, and the lock/db files of the four `y` runs, which sit in their own temp folder); `reset.sh` left no pid, lock or log file; no process of ours remained; all ports used were closed. A `desk.db.lock` file stays next to each used database by design (also in the `y` runs); `run_live_check.py` leaves `<ledger>.lock` beside its ledger. No `:memory:.lock` or `:memory:` file appeared anywhere (checked with `reset_check.py` and the desk).

## 3. What the dry paths do NOT prove

Each path ran only against stand-ins or refusals, so:

- `--dry-fakes` proves the script's own logic (crash, restart, counting) against a fake HubSpot, a fake mail server and two fake mailboxes written by the same author, all on `localhost` with a test certificate. It says nothing about what real HubSpot does (duplicate message, `.test` addresses, scopes, rate limits, recycle-bin e-mail reservation: all `UNVERIFIED` in the docs), about Gmail/Workspace behaviour (app passwords, IMAP folder names, spam folder, delays), about delivery to a stranger, or about volumes. The checks "the CRM lists a contact right after the create" (F3) and the fake mailboxes mirroring the mail server are properties of the stand-ins.
- The refusal paths prove the checks the script makes BEFORE its first call. They do not prove that a real key file is valid (D1: it is checked later), that a mail host name is the right one (any host name passes), or that the mailbox password is right.
- `hubspot_probe.py` against the stub proves the call order, the call count, the masking and the exit codes for four invented answers. Whether a free HubSpot account accepts the owner and lead-status writes is only what the author reported (`docs/hubspot-probe.md:4`); not re-run.
- `run_live_check.py` was never run against a model; the loopback runs only show that failures are counted as errors (and exit 0, D5). The worst-case dollar figure was printed for made-up prices only.
- `reset.sh`/`start_all.sh` ran against the demo stand-ins in a copy of the repo on Linux. Windows (`.ps1`), the Z-state handling after a real crash, and the "did not stop in time" exit 5 were not run.
- The `y/N` path of `run_real_check.py` toward real addresses was never exercised: the code before the question was read and nothing in it opens a network connection (settings objects are built, no calls), but that is a reading, not a run.
- Nothing here measures money, mail deliverability or a real crash on the laptop; the real run stays on the laptop.

## 4. How to re-run

```
/tmp/demo-push/handover/demo/real-run/run-dry-checks.sh [REPO_CLONE] [PASSES]
  QUICK=1       skip the --dry-fakes and "y" cases (about 1 minute instead of about 12)
  ALLOW_KNOWN=1 exit 0 when only the known mismatches D1 to D6 fail
  PY=...        python of a venv that has the repo's test dependencies
```
Defaults: `/tmp/work/q4-base`, 2 passes. Exit 0 = every case matched; 1 = a mismatch; 2 = setup problem. The last full run on `2db3926`: 224 results, 0 unexpected failures, 16 known mismatches (8 cases, D1 to D6, times two passes), so the exit code is 1 without `ALLOW_KNOWN=1`. When a mismatch is fixed, the case turns PASS and its id should be taken out of the `KNOWN` line at the top of the script.

Files in this folder: `run-dry-checks.sh` (the checklist), `make_synthetic_config.py` (builds a made-up config from `real-run.env.example`), `probe_stub.py` (loopback stand-in for the HubSpot probe), `results.tsv`, `evidence-q4-*.txt`.
