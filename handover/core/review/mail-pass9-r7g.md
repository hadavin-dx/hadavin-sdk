# Mail-path mutant pass 9 on patch r7g (EGM goldfish, fallback mode)

Verdict: **NOT CLEAN** (REAL GAPS listed below). Tree under test: copy of tree-R7G (tree-M9, and tree-M9b for the second lane), made-up data, loopback only, no spend. Raw files: /home/user/build/rr6/out/M9/ (checkpoint.md, results-*.tsv, raw-M9-*.txt, clean-*.log, specs in work/specs9.json, runner mut9.py).

## What was NOT run or not done (first)
- 82 mutants were written (specs9.json, all counts verified once in the copy); only 43 were run. NOT run: M9-05, 09, 10, 11, 13, 15, 16, 17, 24, 25, 26 (smtp_provider/smtp_outbox), 36, 42, 43, 44, 45, 46, 47 (live_claude), 54, 55, 56, 57, 58 (crm_hubspot), 63 (regfile), 68 to 82 (scripts/run_real_check.py: NONE of its mutants ran), jsonread.py (no mutant written). The run_real_check scrub/secret-order/Start-question guarantees were therefore not re-probed in this pass.
- Selector-set survivors that did NOT get the big-set re-run (time box): see the table column "not re-run on the big set" (M9-23, 33, 34, 64, 65, 67). Treat each as UNJUDGED (suspect), not as clean.
- Clean selector sets before mutants (alone, rc recorded, in checkpoint.md and clean-*.log): mail 411 passed rc0 85 s; tls 551 passed rc0 81 s; live 327 passed rc0 56 s (second clean, without test_real_check_dry; the first clean with it was 406 passed rc0 227 s); crm 283 passed rc0 74 s; reg 378 passed 3 deselected rc0 58 s (the 3 deselected are the known socket-kind tests); rrc 889 passed rc0 273 s (no rrc mutant was run). Selector = group files + tests/test_r7f_findings.py + tests/test_r7g_findings.py.
- Big-set re-run = the 22 files of out/MAIL7/setC.txt + r7d/r7e/r7f/r7g finding files, 900 s limit, two lanes at once (second tree copy) as ordered by the lead at 06:04Z.
- I stopped my own selector driver (pid 15206) to run the big-set re-runs first (lead order). No process of anyone else was touched. Restores checked by sha after every mutant (all "restored-ok"). Slip: the stop was a SIGINT that the background job ignored, so the in-flight mutant M9-30 finished normally (tree checked clean afterwards).
- The brief says "one test process at a time"; the lead then allowed two at once for the big-set re-runs; two separate tree copies were used so mutants never shared a file.

## Counts
Run 43; KILLED by the selector set 26; survived the selector set 17. Of those 17, 10 got the big-set re-run: 11 survived (9 REAL GAP incl. M9-32 and M9-40, 1 EQUIVALENT-in-practice M9-30, 1 listed above as 7 low) and 0 were killed by the big set; the others are UNJUDGED (above).

## REAL GAPS (survived the 22-file big set; killing test in words)
1. M9-22 smtp_outbox.py (mail path): an empty send key is no longer refused. Test: `SmtpOutbox.send("", ...)` raises SendRefused("empty send key") and the fake server sees no connection.
2. M9-12 smtp_provider.py (mail path, login): AUTH answered by any 2xx is accepted. Test: fake provider answers 250 to AUTH PLAIN; expect SendRefused("login refused") and MAIL FROM never received.
3. M9-02 smtp_provider.py: a bad password file is read after the send counter is taken, so a refused secret burns a cap slot and writes the stats file. Test: max_sends=1, bad password file (missing, two lines, UTF-16): SendRefused, `attempts == 0`, no stats write, no connection; then a good file still sends.
4. M9-03 smtp_provider.py: the provider's own timeout setting is ignored when the caller passes a longer timeout. Test: timeout_seconds=1, silent server, send(timeout=30) fails in about 1.5 s.
5. M9-18 smtp_outbox.py: timeout 0 no longer means "use DESK_SMTP_TIMEOUT_SECONDS" (documented). Test: send(timeout=0) and timeout=-1 return SENT.
6. M9-19 smtp_outbox.py: no socket timeout before connect. Test: loopback listener with a full backlog, send(timeout=1) raises SendUnreachable in about 1.5 s.
8. M9-32 live_claude.py (secret): the transport error text could carry the key; survived the big set (377 s). Test: force each LiveTransport path with a known key string and assert the key is in no exception text, repr or log line.
9. M9-40 live_claude.py (money path): lock not obtained, spend goes on without the ledger lock; survived the big set (372 s). Test: hold the ledger file lock longer than the tries x wait, then qualify() must raise LiveCapReached, add no reserve row and make no network call.
7. M9-08 smtp_provider.py (low): the TLS handshake runs on a stale socket timeout instead of the time left. Test: server stalls the handshake after 0.6 s of a 1 s budget; fail by about 1.3 s. Sibling observation (not a mutant, not tested by me): imap_count has a handshake timer, smtp_provider's handshake has only a per-operation timeout, so a server sending the handshake slowly byte by byte may stretch the send past its total budget. Needs a check by the builder.

## Selector survivors not (yet) judged on the big set (treat as suspect)
M9-23 (smtp_outbox `_command` write gets no budget timeout), M9-33 (live_claude: ProxyHandler() instead of ProxyHandler({}), key could go to an environment proxy), M9-34 (live reply read stops one byte early: cap boundary), M9-64 (regfile.iter_regular_lines: readline without +1, a line over the cap is split silently instead of refused), M9-65 (regfile: BOM no longer accepted in a secret file, documented as accepted), M9-67 (errcode: a module whose name merely starts with the package name counts as ours; low). M9-61 is EQUIVALENT: NaN/Infinity read by default are found by `_has_non_finite`, the same single refusal. M9-30 is EQUIVALENT for real handshakes (cheap test: stub connection whose version() is None must be refused).

## Table (every mutant run; killed ones name the first killing test)
| id | file:line | mutation | selector result | big-set result / class |
|---|---|---|---|---|
| M9-01 | smtp_provider.py:252 | send: pre-network re-check of the TLS context removed | KILLED tests/test_r7_mail_context.py | not re-run on the big set  |
| M9-02 | smtp_provider.py:251 | send: password file read moved AFTER the send counter is taken (bad secret then costs a send) | SURVIVED | big set: SURVIVED REAL GAP: bad password file burns a send-cap slot (attempts+1, stats written) before it is refused. Test: bad file, attempts stays 0, no connection. |
| M9-03 | smtp_provider.py:262 | send: provider timeout cap ignored (caller's timeout used) | SURVIVED | big set: SURVIVED REAL GAP: provider timeout setting ignored when the caller passes a longer one. Test: timeout_seconds=1, send(timeout=30), silent server, fails in ~1.5 s. |
| M9-04 | smtp_provider.py:322 | STARTTLS: connection not wrapped, login goes in clear | KILLED tests/test_smtp_provider.py | not re-run on the big set  |
| M9-06 | smtp_provider.py:344 | final non-2xx reply is a plain refusal (retry safe) instead of maybe sent | KILLED tests/test_smtp_provider.py | not re-run on the big set  |
| M9-07 | smtp_provider.py:342 | phase 2 exception classed unreachable (retry safe) instead of maybe sent | KILLED tests/test_smtp_provider.py | not re-run on the big set  |
| M9-08 | smtp_provider.py:297 | _wrap: handshake gets no budget timeout | SURVIVED | big set: SURVIVED REAL GAP (low): TLS handshake runs on a stale socket timeout. Test: stall after 0.6 s of a 1 s budget, fail by ~1.3 s. Sibling note: imap_count has a handshake timer, smtp_provider has none (per-operation timeout only). |
| M9-12 | smtp_provider.py:326 | login accepted on any 2xx | SURVIVED | big set: SURVIVED REAL GAP (mail path): AUTH answered 250 accepted as login. Test: server answers 250 to AUTH, expect SendRefused('login refused'), MAIL FROM never seen. |
| M9-14 | smtp_provider.py:236 | X-Send-Key carries the per-attempt token (count key changes every attempt) | KILLED tests/test_smtp_provider.py | not re-run on the big set  |
| M9-18 | smtp_outbox.py:231 | timeout 0 means a zero budget | SURVIVED | big set: SURVIVED REAL GAP: timeout 0 no longer means the default budget. Test: send(timeout=0 and -1) returns SENT. |
| M9-19 | smtp_outbox.py:254 | connect: no socket timeout before connect | SURVIVED | big set: SURVIVED REAL GAP: connect has no socket timeout. Test: full-backlog loopback listener, send(timeout=1) raises SendUnreachable in ~1.5 s. |
| M9-20 | smtp_outbox.py:163 | read_reply: recv gets no budget timeout | KILLED tests/test_smtp_outbox.py | not re-run on the big set  |
| M9-21 | smtp_outbox.py:161 | read_reply: unbounded line without CRLF allowed | KILLED tests/test_r7f_findings.py | not re-run on the big set  |
| M9-22 | smtp_outbox.py:225 | empty send key allowed | SURVIVED | big set: SURVIVED REAL GAP (mail path): empty send key sent as a mail with empty X-Send-Key. Test: send('') raises SendRefused, no connection. |
| M9-23 | smtp_outbox.py:171 | command: write gets no budget timeout | SURVIVED | not re-run on the big set  |
| M9-27 | tls_trust.py:123 | require_verifying: CERT_OPTIONAL accepted | KILLED tests/test_r7_mail_context.py | not re-run on the big set  |
| M9-28 | tls_trust.py:71 | PEM with a leading comment line is read as DER | KILLED tests/test_ca_file_reads.py | not re-run on the big set  |
| M9-29 | tls_trust.py:53 | after an END line the rest of the file still counts as inside a block | KILLED tests/test_ca_file_reads.py | not re-run on the big set  |
| M9-30 | tls_trust.py:110 | TLS result check: version None / unknown accepted | SURVIVED | big set: SURVIVED EQUIVALENT for real handshakes (version() is always a named version after a handshake, floor 1.2); differs only for a stub with version() None. Test (cheap): stub version None refused. |
| M9-31 | live_claude.py:497 | qualify: key file read AFTER the ledger reserve | KILLED tests/test_live_claude.py | not re-run on the big set  |
| M9-32 | live_claude.py:484 | transport error text carries the key | SURVIVED | not re-run on the big set  |
| M9-33 | live_claude.py:379 | environment proxies used (key goes to a proxy) | SURVIVED | not re-run on the big set  |
| M9-34 | live_claude.py:468 | reply read stops one byte early (cap boundary) | SURVIVED | not re-run on the big set  |
| M9-35 | live_claude.py:335 | total cap boundary: a call that reaches the cap exactly is refused | KILLED tests/test_live_claude.py | not re-run on the big set  |
| M9-37 | live_claude.py:278 | double settle counts the smaller | KILLED tests/test_ledger_amounts.py | not re-run on the big set  |
| M9-38 | live_claude.py:273 | duplicate reserve id accepted | KILLED tests/test_ledger_amounts.py | not re-run on the big set  |
| M9-39 | live_claude.py:147 | negative ledger amount down to -1 accepted | KILLED tests/test_ledger_amounts.py | not re-run on the big set  |
| M9-40 | live_claude.py:183 | file lock not obtained: spend goes on without the lock | SURVIVED | not re-run on the big set  |
| M9-41 | live_claude.py:242 | ledger read without the +1 (a file over the cap is read cut, not refused) | KILLED tests/test_ledger_amounts.py | not re-run on the big set  |
| M9-48 | crm_hubspot.py:344 | call cap off by one | KILLED tests/test_crm_hubspot.py | not re-run on the big set  |
| M9-49 | crm_hubspot.py:356 | 429 wait not bounded by the deadline | KILLED tests/test_crm_hubspot.py | not re-run on the big set  |
| M9-50 | crm_hubspot.py:324 | reads not armed with the time left | KILLED tests/test_r7f_findings.py | not re-run on the big set  |
| M9-51 | crm_hubspot.py:268 | one request may outlive the budget size | KILLED tests/test_crm_hubspot.py | not re-run on the big set  |
| M9-52 | crm_hubspot.py:433 | ALREADY_PRESENT without the email check | KILLED tests/test_crm_hubspot.py | not re-run on the big set  |
| M9-53 | crm_hubspot.py:364 | lead id checked by prefix match only | KILLED tests/test_crm_hubspot.py | not re-run on the big set  |
| M9-59 | regfile.py:113 | read_regular_bytes reads exactly max (a bigger file is cut, not refused) | KILLED tests/test_file_reader_refusals.py | not re-run on the big set  |
| M9-60 | regfile.py:180 | non-finite numbers inside lists not found | KILLED tests/test_file_reader_refusals.py | not re-run on the big set  |
| M9-61 | regfile.py:157 | NaN/Infinity constants accepted | SURVIVED | not re-run on the big set EQUIVALENT: NaN/Infinity parsed by default json become floats and _has_non_finite finds them (same single refusal). Selector set only. |
| M9-62 | regfile.py:247 | refuse_replacing_special never refuses | KILLED tests/test_r7_no_replace_of_special.py | not re-run on the big set  |
| M9-64 | regfile.py:130 | readline limit without +1 (line of exactly the cap refused? or cut) | SURVIVED | not re-run on the big set  |
| M9-65 | regfile.py:83 | UTF-8 BOM not removed | SURVIVED | not re-run on the big set  |
| M9-66 | errcode.py:22 | error code: subclasses of the three bad-input classes also become data | KILLED tests/test_r7_class_names.py | not re-run on the big set  |
| M9-67 | errcode.py:20 | error code: a module whose name only starts with the package name counts as ours | SURVIVED | not re-run on the big set  |

Later big-set results (if any) are in /home/user/build/rr6/out/M9/checkpoint.md.
