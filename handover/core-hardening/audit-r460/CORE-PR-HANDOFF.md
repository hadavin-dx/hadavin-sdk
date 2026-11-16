# R460 core pull request hand-off (for the lead)

Written 2026-11-16 by a builder agent. Inputs: the five audit files in this folder and `patches-ready/v6-extra/FIX-id-vs-command-withheld.patch`. Nothing was run: I re-opened the cited `src/` lines (read only) and ran only `patch --dry-run` on the pending patch. No `src/` or `tests/` file was changed.

## 0. Read this first: what is wrong or uncertain

1. **Every finding below comes from reading code, not from running it.** No audit ran a test, a regex or a mutation. A "test that must fail on old code" below is a design for a test; nobody has yet seen it fail. The evidence runner has to do that.
2. **Two audits disagree and I could not settle it by reading.**
   - Spend finding SG-B1 (no window end date): the first audit calls it a Blocker; the verifier says "arguable, Major". It depends on whether the owner's end-date rule is a hard gate. That is the lead's call (section 5).
   - Spend finding SG-B3: the verifier says the gate already denies an action whose own call crossed the budget (`tests/test_s5_runtime.py:107-111`, which I confirmed), so the race causes extra model-call spend, not an extra action. I rate it Major.
3. **One audit claim is probably wrong and is marked so:** "NaN passes money validation" (SG-M5). Pydantic's Decimal field likely rejects NaN by default, but nobody proved it. I confirmed that negatives are accepted (only the float check exists, `config.py:38-44`).
4. **Citation checks.** I opened every `file:line` that I list. Almost all matched. Differences are noted in the tables as "line moved" or UNVERIFIED. Items I did not open (for example regex behaviour, `guard/redact.py` pattern gaps, vendor adapters) are marked UNVERIFIED in the tables.
5. **The pending patch applies cleanly now** (`patch --dry-run -p1`: both files "checking", no reject). It fixes only one class: long hex ids read as cloud commands.
6. **Mismatch with the stage rule:** `config.py:317` still accepts the stage name `"dev"`; the preamble (rule 21) says the only stages are DEMO, PILOT, PROD and "dev" must be refused. Not in any audit's scope; I list it as a lead decision (section 5) because the spend and audit-trail fixes touch the same config file.

Severity words: Blocker = must be fixed before the PR can merge; Major = fix in the same PR series; Nit = fix in passing.
"Path" column: M = money, R = redaction (personal data masking), S = secret handling, A = audit trail integrity, G = approval-text command filter (G4), other = none of these. The repo rules treat M, R and S paths as security paths, so reviews have no round cap.

---

## 1. Spend guard (files: `spend-guard-audit.md` + `spend-guard-verification.md`)

Class of bug for the group: **the cap is checked before and charged after, and not every billed call reaches the ledger.** Choke point: `limits.py` (`charge`, `blocked`) plus the one place each model call is made.

What was confirmed by me (lines read): `limits.py:17-18` (charge), `limits.py:20-30` (blocked returns only kill switch, daily, monthly), `runtime/agent_loop.py:239-249` (per-run cap compares already-booked cost), `agent_loop.py:440-441` (reply charged after the call), `agent_loop.py:310-316` (judge cost charged after it ran, line moved to 313-315), `store/postgres.py:416-431` and `store/memory.py:196-204` (add_spend atomic, tuple returned and discarded), `config.py:38-44` (only float refused), `deferred.py:62-63` (cap required only when live), `k1b/replay.py:85-90` (zero-price refusal), `k1b/loop.py:115-122, 166-172` (worst-case charge on timeout), `llm/retry.py:92-107` (retries inside one call), `evals.py:73-80, 104-110`, `store/postgres.py:446-450` (kill switch fails closed).

| ID | Sev | File:line | Class | Minimal fix at the choke point | Test that must fail on old code | Path |
|---|---|---|---|---|---|---|
| SG-B1 | Blocker or Major (open decision) | `limits.py:20-30` (no end-date check; grep for end/expiry names found nothing) | Missing time limit on spend window | Add a validated `window_end` (UTC) to config; `blocked()` returns `window_ended` after it; fail closed if the clock is unreadable | Frozen clock after window end: `blocked()` must contain `window_ended`; run must end NEEDS_PERSON | M |
| SG-B2 | Blocker | `runtime/agent_loop.py:239-249`, `:440-441` | Check-then-spend (no reserve/reconcile) | Reserve the worst case (input estimate + `max_tokens` x output price) before `llm.chat`, refuse if reserve would pass the cap, reconcile with the real cost after (`k1b/loop.py:115` already has `worst_case_usd` to reuse) | Cap 0.50, replies cost 0.30: old code makes 2 calls and books 0.60; new code must refuse the second call before it is sent | M |
| SG-B3 | Major (audit said Blocker; verifier says gate still denies the action) | `agent_loop.py:440` (tuple discarded), `limits.py:17,24` | Check and charge are two calls; two runs can both pass | Make reserve+charge one atomic store call that returns the new totals and refuses when over budget (the Postgres upsert already runs in one transaction) | Two threads, budget 1.00, each reserve 0.60: exactly one may succeed (old code: both) | M |
| SG-M4 | Major | per-run cap writes audit row + card only (`agent_loop.py:245-248`); daily/monthly write state reason only | Silent stop at the wall (bible R215 wants a log line AND an alert) | One helper `limits.wall_hit(...)` that logs and notifies through the alert kind; UNVERIFIED: whether an alert kind exists (the audit only grepped) | Cap hit must emit one log record and one alert call (fake alert kind) | M |
| SG-M5 | Major (negatives confirmed; NaN UNPROVEN) | `config.py:38-44` | Money validator too weak | Reject non-finite and negative values for prices, budgets, `max_run_usd` in `_money`; also `daily <= monthly` | Config with `"-1"`, `"NaN"`, `"Infinity"`, daily > monthly must raise ConfigError | M |
| SG-M6 | Major (verifier: understated) | `k1b/loop.py:166-172`; `llm/retry.py:92-107`; live loop `agent_loop.py:424-439` charges nothing on provider error | Billed-but-unrecorded calls (retries, timeouts, failures) | Charge the worst case per attempt (`max_attempts` x) on timeout; in the live loop charge worst case on `ProviderError`/`ProviderExhausted`; parse failure after a billed reply charges the real reply | Fake provider that fails twice then succeeds: ledger must show 3 attempts' worth; fake exhausted: ledger > 0 | M |
| SG-M7 | Major (verifier: partly) | `deferred.py:62-63` (cap required in pilot/prod, `registry.py:230` runs it); no sign check; `limits.py:18,24` and `models.py:19-20` use the UTC date | Config gaps and fixed UTC day | Validate signs (see SG-M5); add `billing_timezone` to config; day and month keys from it | Clock 2026-11-30 19:00 UTC with zone +05:30: spend must count to 12-01 | M |
| SG-M8 | Major | `agent_loop.py:310-316`; zero-price refusal only in `k1b/replay.py:85-90` | Judge cost charged after it ran, no re-check; zero price unguarded live | Move `_refuse_zero_price` to registry load for every route that is not the fake kind; reserve judge cost before the call and re-check the cap after | Config with a zero-price route (kind not fake) must be refused at load; judge on the last cent must not run | M |
| SV-D | Major (new, verifier) | `evals.py:73-80, 104-110` | Eval and golden-set runs spend with no cap, kill switch or ledger | Route eval calls through the same limits object, with a separate eval budget | Eval run with budget 0 must stop before the first call | M |
| SV-E | Major (new, verifier) | `extract.py:47-64` | Reply costs lost on the dead-letter path (only tests call it today) | Return the summed reply cost inside `DeadLetter` and have callers charge it | Two invalid replies with cost 0.1 each: result must report 0.2 | M |
| SV-G | Major (new, verifier) | `agent_loop.py:440-441`, `:313-315` | Partial failure between `limits.charge` and `store.add_cost` under-counts the run | One store call that books spend and run cost in one transaction | Fault injected between the two calls: run cost and agent spend must still match | M |
| SV-A/B/C/F | Major (new, verifier) | A: retry attempts never billed; B: parse failure after billed response; C: judge cost lost on failure; F: zero price in live loop | Same class as SG-M6 and SG-M8 | Covered by the SG-M6 and SG-M8 fixes; keep one test each | One test per letter | M |
| SG-nit | Nit | audit says kill-switch ordering is deliberate (`limits.py:43-51`: confirmed by `stop` docstring at 30) | none | none | none | M |

Tests the fix will break on purpose: `tests/test_k5_tools.py:723-731` (pins the overshoot: asserts exactly 2 calls) and likely `tests/test_s5_runtime.py:107-111` (DENIED vs NEEDS_PERSON may change). Other tests that call `charge` or `blocked` were not read by anyone.

**Not checked by these audits:** `tests/demo_askdata/*`, provider adapters in full (retry and attempt accounting), `store/postgres.py` beyond `add_spend` and `add_cost`, `app.py`, `guard/judge.py`, `cli.py` beyond `--max-usd`, SQL migrations beyond column types, any alert kind (grep only), approvals and executor code, `tick.py`, `runs.py`, Pydantic NaN behaviour (from memory).

---

## 2. Redaction (file: `redaction-audit.md`)

Class: **personal data and secrets reach a model, log or audit row because masking is done per caller, not at one exit.** Choke point: one wrapper around `llm.chat`, plus `runmap.redact_text` (`guard/runmap.py:417`, exists).

| ID | Sev | File:line | Class | Minimal fix at the choke point | Test that must fail on old code | Path |
|---|---|---|---|---|---|---|
| RD-1.1 | Blocker | `extract.py:47-53` (confirmed: `documents=[document]` raw), `:59-63` (assistant turn text re-sent); `guard/producers.py:55-65` lists `extract.py` in the model-caller set (confirmed) | Unmasked model input | Mask the document and the replayed assistant text with `runmap.redact_untrusted` (`guard/runmap.py:298`) before the call; refuse (fail closed) if masking raises. Ledger row R1-AK1-ADV-1 at `handover/ledger.md:1807` is already OPEN (UNVERIFIED: I did not open the ledger line) | Fake LLM that records `documents`; feed a document with an email, a card number, a fake key built from parts; assert none appear in `documents`. The existing driver `tests/test_k5_round9.py:91-109` records only the messages and never looks at `documents` (confirmed), so it passes on the leaking code | R |
| RD-1.2 | Major | callers of `llm.chat`: `extract.py:47`, `evals.py:73`, `guard/judge.py:72`, `runtime/agent_loop.py:425`, `k1b/loop.py:94` (lines checked: extract, evals, agent_loop (now 424); others UNVERIFIED) | No single exit; masking depends on each caller | A `MaskedLLM` wrapper returned by the llm factory; repo test that fails when any module calls an unwrapped client | Repo guard test: a new module that calls the raw client fails the test | R |
| RD-1.3 | Major | `cli.py:75`, `:300-305` (confirmed: exception text printed raw); `registry.py:224` (`ConfigError(str(exc))`); `config.py:120`; `models.py` Shape (no `hide_input_in_errors`; the flag exists on other classes: `config.py:52`, `backends/table.py:24`, `scrub_settings.py:12`) | Error text carries input values | `safe_head` once in `main()` and `_tick()`; add `hide_input_in_errors=True` to the Shape base; strip the YAML snippet | Config with a fake password in a bad field: stderr must not contain it | R, S |
| RD-1.5 | Major (defence in depth) | `models.py:188-215` AuditEvent fields free text; `k1b/audit_sink.py:31-49`; `audit/chain.py:180-205` | No allowlist on audit fields | Pattern validation per field (codes, hashes, ids only) | Event with an email in `result` must be rejected | R, A |
| RD-2.1 to 2.7 | Major each (UNVERIFIED: regex behaviour only by reading) | `guard/redact.py` (`redact` at 862, `redact_many` at 1244) | Pattern gaps: phone separators; IBAN spaced or lower case; card numbers not 4-4-4-4; non-ASCII or quoted emails; credentials in signed URLs and unlisted webhook URLs; JSON name/value pair split (runtime path misses what the other path handles); base64 personal data | Extend the grammar in `redact.py`; one canary test per gap; fix the JSON pair inconsistency by sharing one function between both paths | One canary string per gap, each asserted masked; confirmed to fail on old code by the evidence runner | R |
| RD-1.4 / 1.6 / 1.7 / 2.8 / 2.9 | Nit | `cli.py:81`, `:287`; `receiver.py:63` (UNVERIFIED); `k1b/audit_sink.py:29, 52-56` (OS user name: confirmed); `defaults.py:108-120` (UNVERIFIED) | Debug text, user name in rows, raw originals kept by design | Fix in passing; document retention; check role access | One test each | R |
| RD-test | Nit | `tests/test_k5_tools.py:371` and `:378` use the literal card number 4111 1111 1111 1111 (confirmed). The CLAUDE.md rule allows only one fake literal (the AWS example key) | Fake-data rule | Build the card number from parts | The repo guard for fake literals must flag it | R |

**Not checked:** `guard/bedrock_guardrail.py`, `guard/egress.py`, `guard/http.py`, `runtime/evidence.py`, `runtime/plan.py`, `approvals/*`, `audit/local_dir.py`, every `store/*`, most of `k1b/*`, `sources/kubernetes.py`, `actions/*`, LLM adapter bodies, `demos/`, most tests. The demo pipeline in `demos/ask-your-data` was exempted as "only the typed question" and nobody verified that.

---

## 3. Approval-text command filter, called G4 (files: `gate-g4-audit.md` + the pending patch)

G4 is a display filter: it replaces a command found in model-written text with a "withheld" marker before a person reads it. It does not decide whether a tool call runs. Because it is not the last line of defence, the first lead decision is wording versus behaviour (section 5, D2).

Class: **closed list of program names and upper-case-only SQL; anything off the list is shown to the person as plain text.** Choke point: `approvals/gate.py` `withhold_commands` (line 681), used by `channel.clean` (`approvals/channel.py:18`).

Confirmed by me: the fail-closed wording is at `gate.py:373` (the audit cites 375, which is the sentence on subcommand paths: **line moved**); `_story` returns True for a punctuation-first token at `gate.py:614-615` (the audit cites 614: **confirmed**); `_WRITE_SHAPES` at `gate.py:647-678`; `_NO_VALUE_FLAGS` at `:551`; `_ENGLISH` at `:480`; `_NAMES` at `:540`.

| ID | Sev | File:line | Class | Minimal fix at the choke point | Test that must fail on old code | Path |
|---|---|---|---|---|---|---|
| G4-B1 | Blocker (or fix the wording, D2) | `gate.py:373`, `approvals/channel.py:20-21` claim "fail closed on any platform"; list is `_NAMES` (`:540`) | Wording claims more than the code does | Either deny by command shape, or correct both sentences to "a closed list of programs" | A set of strings (dd, mkfs, chmod -R, kill, shutdown, eksctl delete, dropdb, crontab -r, sed -i, rsync --delete, plain `rm x`, `> file`, `tee`) must be withheld; the existing prose pin `rm the file` (`tests/test_g4_parity.py:224`, confirmed) must stay prose | G |
| G4-B2 | Blocker | `gate.py:614-615` (first token punctuation counts as prose) | Line continuation and leading punctuation bypass | Join continuation lines (`\` + newline, `^`, backtick) before matching; do not treat a punctuation-first token as prose when the program is a write-capable CLI | `"kubectl \\\n delete ns prod"`, same for aws, docker, terraform; `kubectl > /dev/null delete ...` must be withheld | G |
| G4-M1 | Major | quoted-in-prose exemption (`gate.py:616-618`) | Forgeable exemption | Allow it only when no write verb follows the quote; keep the pin `a 'kubectl rollout restart' replaced the pods` (`test_g4_parity.py:96`, confirmed) | `Please run the 'terraform destroy' now` withheld; pin still prose | G |
| G4-M2 | Major | `gate.py:647-678`, upper case only for SQL | Case-sensitive match | Match SQL statements case-insensitively with a statement-shape check (verb + object + `from/set/into` in order); keep pins `drop table pressure`, `we should delete from the queue only after a fix` (`test_g4_parity.py:221-222`, confirmed) | `drop table users;`, `delete from users`, `truncate x`, `grant all on x` in lower case withheld | G |
| G4-M3 | Major | same regex | SQL shape gaps | Add UPDATE with alias/ONLY/quoted name, INSERT IGNORE/REPLACE/COPY/LOAD DATA, CREATE/DROP of other kinds, ALTER MODIFY/CHANGE, privilege changes, comment-as-space (`DROP/**/TABLE`), `nextval`, `setval`, `pg_reload_conf`, VACUUM, CALL, EXEC, DO | One string per shape | G |
| G4-M4 | Major | PowerShell list (`gate.py:671-673`) | Closed module list, aliases missing | Match by verb (`Remove-`, `Stop-`, `Set-`...) not by module; add aliases `ri`, `del`, `rd`, `kill`; `rd /s /q`; `Invoke-Expression (Invoke-WebRequest u)` without a literal pipe | `Remove-SQSQueue`, `Remove-ADUser`, `rd /s /q C:\x`, the iex form | G |
| G4-M5 | Major | unknown subcommand of a known program treated as prose | Open default | Invert: prose only when the next word is plain English and the program is in `_ENGLISH` (`:480`) | `git update-ref -d`, `git config --global core.hooksPath`, `docker trust revoke`, `systemctl rescue` | G |
| G4-M6 | Major | read verb decides the whole command | Read verb with a write flag | Reject read verbs when a write-capable flag is present: `git diff --output=`, `git -c core.fsmonitor=`, `git reflog expire`, `terraform plan -out=` (Nit) | the four strings | G |
| G4-M7 | Major | program name match is lower-case ASCII with a fixed suffix list | Name normalisation | Normalise case, `.exe/.ps1`, version suffixes, `$VAR` and `${IFS}` before matching | `KUBECTL.EXE`, `AWS ec2 ...`, `kubectl.ps1`, `kubectl-1.28`, `$K delete`, `rm${IFS}-rf` | G |
| G4-M8 | Major | `gate.py:674` rm shape | Narrow flag shape | Parse rm flags as a set; add `find -delete`, `shred`, `unlink`, `truncate` | `rm -v -rf /x`, `rm -i -r`, `rm --no-preserve-root -rf /` | G |
| G4-M9 | Major | `gate.py:675-677` download-and-run | Interpreter list narrow | Add `\| python3/perl/node`, `source <(curl ..)`, `eval "$(curl ..)"`, `curl -o x u && sh x`, `base64 -d \| sh`, `python -c shutil.rmtree` | one string each | G |
| G4-M10 | Major | capitalised first word read as prose (`gate.py:614`) | Same line as B2 | Only treat as prose when the program is in `_ENGLISH` | `mysql Shop -e "delete from x"`, `psql Prod -c "drop table x"`, `ansible Prod -m command -a reboot` | G |
| G4-M11 | Major | `gate.py:636` English-word CLIs mid-sentence | Write verb list incomplete | Add checkout, clean, commit, merge, rebase, pull and others to the write verbs | `Run: git checkout main`, `Then git clean`, `Run: psql prod < dump.sql` | G |
| G4-patch | Minor (fixes one class) | patch changes `_WRITE_SHAPES` cmdlet shape (now at `gate.py:671`; hunk context is `MERGE INTO` at 668: applies cleanly per dry run) | Random hex id matches a cloud cmdlet shape | Apply as is: `(?![0-9a-f]{32,}\b)` plus `tests/test_g4_ids_not_withheld.py` | The patch's own test walks all 65,536 first-four-digit values for 4 prefixes; must fail on old code (for example `pln-ec2a` + 28 zeros). The audit judged it correct; short hex runs (under 32) still trip the pattern (N2) | G |
| G4-N1..N4 | Nit | `_NO_VALUE_FLAGS` global (`:551`); short hex over-matching; NBSP matches `\s`; aws read prefixes include `get-secret-value` and `get-session-token` | Over-matching and a read of secrets shown as read-only | Fix in passing; decide whether secret reads count as read-only (D3) | one test each | G |

Note on the patch: the audit says it did not find a "Remove-EC2* gap" on current code. Remove-EC2Instance is covered (`tests/test_g4_parity.py:46, 159-161`, cited by the audit; I did not open those lines).

Performance: the patch's id-walk test does 4 x 65,536 calls; mark it slow so it does not stretch the normal run.

**Not checked:** `runmap.py`, `redact.py`, `gate.py:229-340` (G3 helpers), `actions/*`, `deferred.py`, `runtime/agent_loop.py` use of G4, `cards.py`, `models.py`, most tests. Every "passes" in the audit was hand-traced through the regexes, never run. Existing tests: `tests/test_g4_parity.py` has no test that fails for any bypass above.

---

## 4. Secrets kind and audit trail (file: `secrets-audittrail-audit.md`)

The audit found no secret value reaching a log, exception, audit row or model (no Blocker). Its Majors are cloud identifiers in error chains, a key file read without checks, and an audit check that says "intact" when it should not.

Class A (honesty): **a verify command that cannot detect rollback still prints "intact".** Choke point: `audit/chain.py` `Verification` (`.ok` at `:143-145`, confirmed) and `cli.py audit_verify` (`:349-363`, confirmed).

| ID | Sev | File:line | Class | Minimal fix at the choke point | Test that must fail on old code | Path |
|---|---|---|---|---|---|---|
| SA-3.1 | Major | `cli.py:356-362`, `chain.py:143-145`; the audit cites a test at "`:520`" in an audit test file: UNVERIFIED (file not named) | Over-claim: prints "intact" with no signer, or with no anchor, or with unsigned rows | Add a field "tamper-evident: yes/no, why" to the result; print "NOT tamper-evident: no signer or anchor" and the unsigned range; exit code stays 0 only when the chain is consistent, but the word "intact" appears only when signer and anchor exist and the tail is signed | Chain with no signer: output must contain "NOT tamper-evident" and not "intact" | A |
| SA-3.2 | Major | anchor kind `none` allowed outside prod: `backends/table.py:604` (`NOT_PROD`: confirmed) | Rollback to an older consistent prefix is invisible without an anchor | Verify prints the rollback limit in plain words when there is no anchor (same fix as 3.1); decide whether pilot should refuse `none` (D4) | Delete the last rows and their checkpoints; verify must say "cannot detect rollback" | A |
| SA-3.3 | Major | `audit/anchor_s3.py:70-81`, `audit/anchor_gcs.py:50-55`, `audit/anchor_azure.py:62-67` (all confirmed), `audit/anchors.py:35-37` (`parse` does not compare object name to seq: confirmed) | Name and body disagree: planted alias object wins | One shared `anchors.collect` that requires object name == `key(seq)`, rejects duplicates and rejects names it cannot parse as a verify error with a clear message; three backends call it | Plant an object with a different name and a body of seq=2 with a forged head: verify must fail; two objects for one seq must fail | A |
| SA-3.4 | Major | `chain.py:309, 325` one identity signs and anchors (docstring `chain.py:16` says another principal; confirmed); `backends/table.py:155` `retain_days` default 1, `ge=1` | Separation not enforced; no retention floor | Separate anchor-writer identity setting; retention floor in config for pilot and prod; start-up probe for S3 object lock like the GCS and Azure ones (UNVERIFIED that those probe: not opened) | Config with retain_days 1 in prod must refuse; S3 bucket without lock must fail start-up | A |
| SA-3.5 | Major | `chain.py:174-176` (`_unanchored` in memory only; comment says restart drops it: confirmed) | Unanchored checkpoint forgotten after restart | At start-up, list checkpoints without an anchor and re-anchor them; add an anchor freshness alarm | Fail the anchor put, restart the process (new object), run reconcile: anchor must exist | A |
| SA-3.6 | Major | `chain.py:215-230` (confirmed), `store/migrate.py:59` runtime role may SELECT, INSERT, DELETE on `audit_outbox` (confirmed) | Outcome events can leave the chain | Alert on outbox age; verify prints how many events are outside the chain; consider removing DELETE from the runtime role (needs a purge identity) | Force chain failure, drop an outbox row: verify output must report the count (old code: silent) | A, least privilege |
| SA-1.1 | Major | `backends/platform_secrets.py:63` (`from exc`: confirmed), `audit/signer.py:87` (`from exc`: confirmed), `actions/secrets_aws.py:34` (bare `raise`: confirmed); `cli.py:81-82` prints the traceback with `HADAVIN_DEBUG=1` (confirmed) | Chained exception carries a cloud caller identifier | `from None`, class name only; for the AWS provider convert the raw error to a `ConfigError` with the error code | Fake AccessDenied whose message contains a 12-digit number: no output stream, `str()` or `__cause__` of the raised error may contain it | S |
| SA-1.2 | Major | `audit/signer.py:104-108` and `:196-197` (confirmed: `read_bytes()` with no checks); `actions/secrets_file.py:35-58` does the checks (confirmed: `O_NOFOLLOW`, `fstat`, mode test); `key_path()` (`signer.py:130`) guards generation only; `config.py:395-396` refuses key files in prod only | Same class as the secret file reader, but unguarded | Route the signer's key read through the same checked reader as `secrets_file.py`; refuse mode 0644 and symlinks in every stage | Key file mode 0644 and a symlink: loading must raise ConfigError | S |
| SA-4 | Major | one runtime identity writes, reads, verifies, signs and anchors; `audit verify` reuses the runtime store identity | Least privilege (rule asks for separate writer, reader, CI) | Give `audit verify` a read-only role setting and a separate anchor writer; policy text + per-action reasons + negative test (writer cannot read, reader cannot write) | Negative test per identity | A, least privilege |
| SA-nits | Nit | holders have plain attributes (`CachedSecrets._cache`, `VaultProvider._token`); `SECRET_HOLDERS` (`tests/test_repo_rules.py:131-142`) omits `audit/signer.py` and `signer_vault.py` (confirmed: list read); `local_dir.verify_object` raises on a missing object (`audit/local_dir.py:158-164`, confirmed); event time writer-chosen and not checked; signed message has no chain id; torn index lines skipped; `index.jsonl` umask; `secrets_cache` never evicts and holds one lock across the network call; vault 403 re-login each fetch; `secrets_file` folder mode and owner unchecked | Hygiene | Fix in passing: `__repr__` that hides values, add the two modules to `SECRET_HOLDERS`, return False on missing object, chain id in the signed message | one test each | S, A |

Audit's list of twelve missing negative tests (all appear above): rollback with no anchor; alias-named anchor; key mode 0644 or symlink; AccessDenied with a 12-digit number; restart after anchor outage; S3 without Object Lock fails start-up; deleted outbox row or lost pending; event time going backwards or far future; two processes signing the same seq; CLI must not say intact for unsigned or unanchored chain; `verify_object` on a missing object; mounted-file folder mode and owner.

**Not checked:** `secrets_gcp`, `secrets_azure`, `signer_aws/gcp/azure`, `anchor_azure` beyond `all()`, `store/postgres.py` and `memory.py`, `config.py` beyond prod refusals, `backends/factory` and `builtin`, callers of `Executor._caller(headers=)`, how non-K1b callers build `AuditEvent`, CI, bandit and ruff. Vault and vault-transit kinds were never run against an open-source vault. The audit's claim that no secret value reaches a log is an absence of evidence from reading, not a proof.

---

## 5. Suggested PR split and order (blockers first)

Each PR goes through the full EGM sequence. All four security PRs (1, 2, 3, 5) have uncapped review rounds. Each PR proves its new tests fail on the old code with an evidence runner.

| Order | PR | Contents | Why this order |
|---|---|---|---|
| 1 | **PR-A: model input masking** | RD-1.1 (Blocker), RD-1.2 wrapper, RD-1.3 error text, RD-test | Only confirmed leak of personal data to a model. Smallest, self-contained. |
| 2 | **PR-B: spend guard core** | SG-B2 reserve/reconcile, SG-B3 atomic reserve, SG-M5/M7 validation, SG-M6/M8 + SV-A/B/C/F billed-call accounting, SG-G, SG-M4 alert | Money path. Changes `limits.py`, so SG-B1 (window end) goes here only if D1 says "Blocker". |
| 3 | **PR-C: G4 command filter** | G4-B2, G4-M2/M3 together, G4-M5, G4-M7, then the rest; the pending patch applies first and unchanged | B2 is the cheapest high-value fix (join continuations). The patch is independent and can ship first as a tiny PR. |
| 4 | **PR-D: audit-trail honesty and anchors** | SA-3.1, SA-3.3 (shared `anchors.collect`), SA-3.5, SA-3.2 text | Honest wording first; plain-word output changes tests that assert "intact". |
| 5 | **PR-E: secrets and signer** | SA-1.1, SA-1.2, SA-nits | Small and independent. |
| 6 | **PR-F: second wave** | RD-2.x pattern gaps (one canary each), RD-1.5 audit field allowlist, SV-D eval budget, SV-E extract cost, SA-3.4/3.6/4 identity split, G4 remaining Majors | Majors with larger design or config effect. |

PR-A, PR-C (patch only), PR-E can run in parallel; PR-B and PR-D touch different files from each other. Promote rule: all of this is generic core work, so builders branch as `core/promote-<topic>`, open ready (not draft) PRs, never merge.

## 6. Open lead decisions

- **D1.** Is the owner's window-end rule a hard gate? Yes: SG-B1 is a Blocker and joins PR-B. No: it is a Major in PR-F.
- **D2.** G4 wording: deny by command shape (big change, high false-positive risk, existing prose pins) or correct the sentence at `gate.py:373` and `approvals/channel.py:20-21` to "a closed list of programs"? I suggest correcting the wording now (it is an honesty fix, same PR as G4-B2) and extending the list per G4-M5.
- **D3.** Should `get-secret-value` and `get-session-token` count as read-only commands in the approval text?
- **D4.** Should pilot refuse anchor kind `none` and signer kind `none` (today only prod refuses: `backends/table.py:604`)? This needs the owner if it changes what a client build can run.
- **D5.** Spend: money type. The first audit says Decimal is not integer minor units; the verifier calls it a Nit because the whole repo uses Decimal. The CLAUDE.md says "money is integers". I recommend leaving Decimal in this PR series (a repo-wide change) and recording it as a lead decision, not hiding it.
- **D6.** Stage names: `config.py:317` still accepts `"dev"` (rule 21 says DEMO, PILOT, PROD only; frozen text may still say "dev"). Out of scope of the five audits; needs the lead's yes before it joins any PR here.
- **D7.** Reviews: the first spend audit says two independent reviewers on it have not run. They must run before PR-B starts (money path).
- **D8.** Ledger: the new findings need rows in `handover/ledger.md` the same turn (blocker ledger rule). I did not write them (outside my allowed folder).

## 7. What I did and did not do

Did: read all five audit files and the patch; re-opened the cited `src/` lines in about 40 places; ran `patch --dry-run` (read only, no change).
Did not: run any test, lint, bandit or regex; open `guard/redact.py` pattern code or the vendor adapters; open `handover/ledger.md`; open the `test_g4_parity.py` lines 46 and 159-161; check callers beyond the audit's own lists; write ledger rows; use EGM (this is a hand-off document written from existing audits; the lead runs the EGM chain on each PR; "EGM skipped: read-only synthesis, no plan or code produced").
