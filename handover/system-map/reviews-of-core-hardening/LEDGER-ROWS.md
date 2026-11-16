# LEDGER-ROWS (ORDER 005, review of core-hardening). 9 columns; status values OPEN / FIXED-UNVERIFIED / FIXED-VERIFIED / OWNER-ONLY / IMPOSSIBLE-NOW; date UTC.

| id | source | severity | area | summary | status | fixing artifact | verified-by | date |
|---|---|---|---|---|---|---|---|---|
| CHR-SEV-01 | REVIEW.md Blockers; verify-V1.md A-02 | Major | security | A-02 rated Blocker, is a false comment (gate.py:5-7 Not ported; README.md:31) | OPEN | patches/A-02.patch | V1, V6, lead | 2026-11-16 |
| CHR-SEV-02 | REVIEW.md Blockers; verify-V6.md B-01 | Major | state | B-01 Blocker rests on unverified deployment; exit-code statement wrong (app.py:125-128) | OPEN | patches/B-01.patch | V6, lead | 2026-11-16 |
| CHR-SEV-03 | REVIEW.md Blockers; verify-V4.md D2-01 | Major | demos | D2-01 Blocker too high: demo command, scripted model, read-only login; README does not claim the controls | OPEN | patches/D2-01.patch | V4, V6, lead | 2026-11-16 |
| CHR-SEV-04 | REVIEW.md severity list; verify-V1.md | Nit | audit | V1 lane A and X: A-10, X-05, X-06, X-09, X-10 (part), X-11, X-13 rated too high | OPEN | CORRECTIONS.md item 4 | V1 | 2026-11-16 |
| CHR-SEV-05 | verify-V2.md | Nit | state | V2: B-03, B-07, B-08, B-09, D1-03 rated too high | OPEN | CORRECTIONS.md item 4 | V2 | 2026-11-16 |
| CHR-SEV-06 | verify-V3.md | Nit | docs | V3: C-10, C-11, C-17, C-19, D3-06, D3-09, D3-10, D3-20 rated too high | OPEN | CORRECTIONS.md item 4 | V3 | 2026-11-16 |
| CHR-SEV-07 | verify-V4.md | Nit | demos | V4: D2-06, D2-07, D2-08, D2-18 rated too high | OPEN | CORRECTIONS.md item 4 | V4 | 2026-11-16 |
| CHR-DUP-01 | verify-V1/V2/V3 | Major | audit | Double counts: X-05=A-02, D3-08=C-09, D3-09=C-10, B-11=D1-01 | OPEN | CORRECTIONS.md item 5 | V1, V2, V3 | 2026-11-16 |
| CHR-CITE-01 | evidence-ch-2-loose-cites.txt; verify-V3.md | Major | audit | limits.py cites 197-231 do not exist (51-line file); factory.py:109, prompt.py:400/408, test_k5_round6_contracts.py:45 past end of file | OPEN | patches/C-01.patch; patches/D2-11-12.patch (partial) | lead, V3, V4 | 2026-11-16 |
| CHR-PATCH-01 | verify-V3.md; V5a; V6 on target patch A-02 | Major | redaction | Target patch fixes redact.py comment only; gate.py:42-44, 59, 63 still claim G5 BLOCK and enforce | OPEN | CORRECTIONS.md item 1 | V3, V5a, V6 | 2026-11-16 |
| CHR-PATCH-02 | verify-V3.md; V6; lead one-liner | Major | money | Target patch C-01: NaN raises InvalidOperation, Infinity passes, max_tokens unbounded, no test, zero-price local models refused | OPEN | CORRECTIONS.md item 2 | V3, V6, lead | 2026-11-16 |
| CHR-MISS-01 | lead check limits.py:43-46; verify-V1.md | Major | audit | Limits.stop writes the emergency-stop audit event with write_outcome, which falls into the A-01 hole (parked, never drained) | OPEN | CORRECTIONS.md item 3 | lead, V1 | 2026-11-16 |
| CHR-MISS-02 | verify-V2.md | Major | state | on_decided (agent_loop.py:753) calls execute without a state check for any caller (widens B-03) | OPEN | none (needs fix by owner of runtime) | V2 | 2026-11-16 |
| CHR-MISS-03 | hunt-H1.md H1-10, H1-11 | Major | least-privilege | One secrets provider serves executor, model key, signer, anchor, store, channel, HMAC key; no IAM policy text or negative tests for cloud kinds | OPEN | none (design decision, owner) | H1 (unverified by me beyond app.py:82-173) | 2026-11-16 |
| CHR-MISS-04 | hunt-H1.md H1-01 | Major | single-dependency | Demo import guard names only psycopg and sqlglot; boto3 or anthropic in demos/ passes both guards | OPEN | none | H1 | 2026-11-16 |
| CHR-MISS-05 | hunt-H1.md H1-17 | Nit | single-dependency | audit kind exception names trigger none | OPEN | none | H1 | 2026-11-16 |
| CHR-MISS-06 | hunt-H1.md H1-16 | Nit | security | exec(compile(...)) of pinned bytes at tools.py:389; 211 suppression comment lines in the repo (upper bound, not split) | OPEN | none | H1, lead (code line read) | 2026-11-16 |
| CHR-MISS-07 | hunt-H2.md | Major | one-source | Demo-local generic code without promotion entry: safe_text.py (weaker ANSI pattern than guard/redact.py:820), meter.py, ledger torn-tail append; six places hash text with SHA-256 | OPEN | none | H2 (regex compared by reading, not run) | 2026-11-16 |
| CHR-CUT-01 | verify-V5a.md | Major | cut list | Archive would break callers: CLOUD-RESUME-2026-11-07, -09, CLOUD-PROMPT.md, bible-extract files | OPEN | CORRECTIONS.md item 7 | V5a | 2026-11-16 |
| CHR-CUT-02 | verify-V5a.md | Major | cut list | replay_records (live gate deferred.py:95), trigger_ref (12 tests), dead_letters, marker live (ci.yml:88) are not unused; extract.py contradiction between cut list and X-02 | OPEN | CORRECTIONS.md item 7 | V5a | 2026-11-16 |
| CHR-RUNG-01 | verify-V5a.md | Major | tool ladder | No rung table in fix plan; X-06, B-10, A-05 sit one rung too high | OPEN | CORRECTIONS.md item 8 | V5a | 2026-11-16 |
| CHR-VER-01 | evidence-ch-1.md; lead-notes.md | Major | method | Not checked: 65 Nits; MASTER-MAP rows one by one (183 of 473 without path:line); no sample re-read of verifier Major lines | OPEN | none | lead | 2026-11-16 |
