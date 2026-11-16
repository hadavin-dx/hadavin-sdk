# R7I results (builder r7i). Base: r7h. Delta = ONE new file, tests/test_r7i_findings.py (37 tests). No source file changed.

## What was not done / what to know first
- NO CODE DEFECT was found: every one of the 9 survivors was a missing test (code already right). All 9 tests are PINS; they pass on tree-R7H by design (onr7h.log: 34 passed then; 37 now). Fail-before for pins = they FAIL on the mutants (below).
- Not run: the full suite (EV7H does). Run here: the new file (37 pass), 9 guard/hygiene/gitleaks files on a staged git copy (168 passed, guards.log), ruff 0.17.1 check and format --check on the whole tree (clean).
- Slip: twice I typed a null-device redirect inline in a command; the permission classifier blocked both before they ran (no effect). Not repeated.
- Mutants M9-12 and M9-03 were handed to me by message at 06:23Z; both are killed (below). No later survivor messages had arrived at the end of the run: any survivor classified after ~06:27Z is NOT covered.
- The "single choke point" for secret order was NOT built (NEEDED-CHECK below).
- No existing test was changed or deleted.

## Per item (NEEDED-CHECK, class, fix/pin, mutants killed)
| id | mutant | needed-check | class | result |
|---|---|---|---|---|
| i1 | M9-22 smtp_outbox empty send key | NEEDED (test only); code already raises SendRefused("empty send key") before any network | a refusal check with no test | pin: i1 (outbox, listener sees no connection) + sibling pin for the provider (empty key, no command, attempts 0). Killed. |
| i2 | M9-02 password read after counter | NEEDED pin; code already right. Re-verified on tree-R7I: r7h `test_order_smtp*` kill it (4 failed). live_claude (key read at 424-429 before ledger.reserve 509), crm_hubspot._call (key at 337 before counter 348), imap_count (password 256 before connect 278), smtp_outbox (no secret) all in the right order and pinned by r7h test_order_*. | order: read+validate secret, then counter, then connect | One choke point: NOT-NEEDED. The secret read is already ONE shared reader (regfile.read_secret_line); the order is per adapter (each has a different counter/ledger/connect), a wrapper would add code for no new check and each order has its own pin. Extra pin i2 (cap 1: bad file refused, then good file still sends). Killed. |
| i3 | M9-12 login on any 2xx | NEEDED | exact reply code | pin i3 for 200,234,236,250,299: AUTH reply changed to that code -> SendRefused("login refused"), MAIL never seen. Control: the existing happy-path tests give the real 235. Killed. |
| i4 | M9-03 provider cap ignored | NEEDED | time limit | pin i4: recorded budget = min(caller, provider) for 30/1/2/0/-5. Also killed by the end-to-end i6 test. |
| i5 | M9-18 timeout 0 = zero budget | NEEDED | time limit | pins i5 (recorded budget) and an end-to-end send with timeout 0 to a scripted server. Killed. Provider side of 0/-5 pinned in i4. |
| i6 | M9-08 handshake no budget | NEEDED | step gets time LEFT | pin i6: socket carries an old 10 s limit, wrap_socket must see <= 2 s. Plus an end-to-end silent-listener test (passes on this mutant by design). Killed. |
| i7 | M9-19 connect no timeout | NEEDED | same | pin i7 with a recording socket. Killed. |
| i8 | M9-23 command write no timeout | NEEDED | same | pin i8. Killed. |
| i9 | M9-30 TLS version None/unknown | NEEDED | allow-list, not deny-list | pin i9: None, "", TLSv1.4, TLSv9, TLSv1.1, TLSv1, SSLv3, DTLSv1.2, tlsv1.3 refused; 1.2/1.3 pass; and through _wrap the connection is closed and SendRefused raised. Killed. |

Mutant runner: out/R7I/m.py (plants spec, runs, restores, checks sha: every run printed restored True). Specs: out/M9/work/specs9.json. Results: mutants-i.txt (9/9 killed on tree-R7I; each shows 1 to 5 failing tests, the rest of the file passes).

## Sibling sweep (same class: a step must be given the time LEFT)
Planted 4 extra mutants (sibling-specs.json) on the 5-file mail set (302 tests): 
- S-IMAP-HS (imap_count handshake settimeout removed), S-SMTP-DATA (smtp_outbox settimeout before sendall(wire)), S-PROV-DATA (same in smtp_provider): SURVIVED = real gaps (sibling-results.txt). New tests i10 (outbox, provider: the reply to DATA takes 0.6 s of 2 s, the text must be written with < 1.5 s) and i11 (imap: connect takes 0.6 s of a 2 s total, handshake limit < 1.5 s). All 3 now killed (sibling-kill.txt).
- S-PROV-CONN (provider connect gets 600 s): killed by existing test_f6 (no new test).
Not swept for a mutant: server.py recv/sendall (HTTP server, other module; no survivor reported).

## Checks
- New file clean on tree-R7I: 37 passed. On a copy of tree-R7H (new file added): all pass (pins).
- ruff 0.17.1: check and format --check clean over the whole tree. New file has no noqa / type-ignore; no literal fake secret (uses FAKE_PASSWORD from demo_only); hosts built from parts (LOOP).
- Guard files on staged copy: 168 passed.

## Deliverables (out/R7I)
core-fix-on-frozen-r7i.patch (CRLF), core-fix-on-frozen-r7i-lf.patch, core-fix-r7h-to-r7i-delta.patch (1 file), sha256-r7i.txt, apply-matrix-r7i.txt (a-crlf, b-crlf, c-lf: git apply --check rc=0 each), build.log (BYTE-FOR-BYTE-SAME, DELTA-ON-R7H-GIVES-R7I).
