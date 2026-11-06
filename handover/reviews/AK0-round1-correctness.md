# AK0 round 1, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

TICKET REVIEW ROUND 1, CORRECTNESS: handover/tickets/AK0.md (revision 1 DRAFT). Read-only. I did not read handover/reviews/ or handover/evidence/.

Verdict: no Blockers. Every cite into src/ and tests/ is true, and the 11,500,000 arithmetic is correct. The ticket agrees with kit-plan-v2 and GAPS except for the items below. I found 3 Majors (two planted-fault checks cannot catch their own fault, and one default contradicts the ticket's own judging rule), 8 Minors and 3 Nits.

I had no shell and no git here, so I ran no commands. I checked every cite and count by reading files. The environment says it is not a git repository.

## Findings

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R1-COR-1 | Major | 107 (E4), 95 (A6) | E4 is `(claude\|gpt\|gemini\|titan\|embed\|rerank)-[a-z0-9.]+-[0-9]`. It needs a digit right after the second dash. It matches `claude-3-5-sonnet` and `<model-id>`. It does NOT match `text-embedding-3-small` ("embed" is not followed by a dash), `titan-embed-text-v2`, `cohere-embed-english-v3`, `rerank-english-v3.0`, `gemini-2.5-flash` or `gpt-4o-mini`. Planted fault A6, "an embedding model id pasted in a price row", would pass E4 silently. This was read by hand, not run, because I had no shell. | Replace E4 with a looser pattern, for example `(claude\|gpt\|gemini\|titan\|embed\|rerank\|voyage\|cohere)[a-z0-9.-]*[-.:][a-z]*[0-9]`, and run it on a 4-row sample holding those ids. Record the sample output the way E1 does. Or add a rule that the note names product families only, and have the runner read the Option and Unit-cost columns. |
| R1-COR-2 | Major | 108 (E5), 97 (A8), 105 | E5 passes when `sed -n '<line>p'` prints a non-empty line. Planted fault A8 is "a cite to `extract.py:58` after P5b3 moved that line". A moved line is still non-empty, so E5 cannot catch it. E5 also maps cites to `src/hadavin_sdk/<path>`, but the ticket cites `tests/test_lockin_guard.py:189` (line 23) in the same way. That cite would fail E5, or be skipped by A8's "every `src/` cite". | Have each cite carry a quoted token, for example `extract.py:47 "llm.chat("`. E5 then runs `git show <sha>:<path> \| sed -n '<line>p' \| grep -F '<token>'`. Say that `tests/` cites are included, and map their path correctly. |
| R1-COR-3 | Major | 21, 30-33 (D4), 85, 127 | The judging rule J2 says an option with a new outside party can only be an alternative. The recommended D4 default is "(b) the client cloud's managed embedder" (R363). Line 85 lists "D4(b)" among the "new data paths ... a sub-processor if chosen". D2(c) is the same: line 31 says "no NEW sub-processor", and line 85 says a sub-processor if chosen. The ticket's own rule rejects its own default, and it contradicts itself on D2(c). | Say that a managed embedder inside the client's own cloud account is not a new outside party. Then take D4(b) off the line-85 list, or keep it there and mark the rule J2 exception "client's own account". Make D2(c) say the same on both lines (31 and 85). |
| R1-COR-4 | Minor | 26, 127, 128, 130 | The reference workload defines only embedding tokens (5M, 5M, 1.5M) and 10,000 pages. It does not say whether the re-index re-reads the pages. That makes the reader cost 10,000 pages or 20,000 pages. It gives no page-image tokens or answer-model tokens for D2(c). D9 asks for "cost of one extra deployment at the reference workload", and the workload cannot produce that number. A9 needs "numbers" for PL1 to PL5. | Add: reader cost on 10,000 pages (the re-index re-embeds only), D2(c) tokens per page image, and answer calls per question. Or say that D9's deployment cost is a fixed monthly figure outside the workload. |
| R1-COR-5 | Minor | 37 (D8), 33, kit-plan-v2 AK2b done condition | D8(c) "embed raw with a self-hosted embedder" is allowed in the recommended column. Kit-plan-v2 section 6 (AK2b) requires "embedding payload never contains the seeded personal data string". With D8(c) the payload does contain it. | Add one sentence to D8: under (c) the AK2b condition is replaced by the test "the payload goes only to the self-hosted host on the egress allowlist". Flag it for the AK2b ticket. |
| R1-COR-6 | Minor | 37 (D8), 131 (PL5) | The "per-tenant lasting placeholder map" must hold originals. `runmap.py:3-6` says only identifier kinds are stored; secret and regulated kinds' originals stay in memory for the run. `defaults.py:108-122` has 13 stored kinds. D8(a) stores chunks raw. The ticket does not say what a secret or card number in a document gets at question time. The text at `runmap.py:3-6` implies a run-scoped placeholder that differs between ingest and query. | Add to D8 and PL5: the lasting map covers stored kinds only, and the note must say what happens to non-stored kinds. Candidates are fail closed, a per-run placeholder, or refuse the chunk. |
| R1-COR-7 | Minor | 41 (D12), 81 | `evals.py:1-4` is cited for "exact field match". The matcher at `evals.py:26-32` is a subset match: "extra optional inputs the model added are allowed". The "no retrieval metric" claim is true. | Write "subset match on action and inputs (`evals.py:26-32`)". |
| R1-COR-8 | Minor | 52 (Problem) | The template asks for 3-5 sentences. The field has 8. | Cut to 5, or move the part list to the D-table. |
| R1-COR-9 | Minor | 72-84 (Existing core code reused) | The template list is hashing, k1b/atomic, k1b/redaction, stats, evals, store/memory, tests/contracts. The ticket reports only evals. The others are not marked "checked, not relevant". `guard/redact.py` is also absent, although D7 depends on redaction. | Add one line: "checked, not relevant to a text-only ticket", naming the six. Add `guard/redact.py` to the inventory (D11). |
| R1-COR-10 | Minor | 3, 5, 90, 126 vs LEAD-ORDERS 23-24 | Line 2 says written "from 03:30 UTC (09:00 IST)", and line 3 says it read orders 6 to 24. LEAD-ORDERS stamps order 23 at about 03:45Z / 09:15 IST and order 24 at about 03:35Z / 09:05 IST. Both are after the ticket's stamp. The lead says the hours of orders 16-19 are wrong, so one side is wrong. Line 5 ("03:20 to 03:30 UTC") and line 90 ("03:28 UTC") give no IST, which breaks the ticket's own check A11. | Re-stamp from the git push times (I could not check them), and add IST to every time in the ticket. |
| R1-COR-11 | Minor | 51 vs 132 (PL6) | "Depends on: none" ignores that every dated licence and price read needs PL6 (may AK0 read public pages?), which the lead has not answered. PL6 is on the Never list ("anything outside the repository"). The fallback (the lead pastes the lines) is written, but the start gate is not. | Under Depends on, add: "start gate: PL6 answered. If no, the lead supplies `sources.md`." |
| R1-COR-12 | Minor | 31 (D2), GAPS G6, R363 | GAPS G6 covers images, scans and speech, and its Where-planned column says "AK0 decides". The ticket covers scans only. R363 names "self-hosted open-source parsers and OCR" as the neutral document-parser default, and D2 recommends "none" without noting the departure. | Add a D2 line: images and speech are out of AK0 scope with a trigger (GAPS G6). State the R363 departure and the kit-plan reason. |
| R1-COR-13 | Nit | 30, 32, 34 | The rung labels are loose. A PDF library or OCR labelled "rung 5" is not retrieval. Own code (D3(c), D12(c)) is rung 7 and is unlabelled. | Label by the ladder text, or define the labels. |
| R1-COR-14 | Nit | 105 (E2) | The pattern ends in `\|$`. A trailing space after the last pipe makes it miss the row, and the count then disagrees. | Use `\| *$`. |
| R1-COR-15 | Nit | 3, 51 | Line 3 lists R130, R134, R196 and `tools.py` as read or affected, but none is used in the body. | Drop them, or say where they are used. Also note that order 22 item 27 removes PHONE from the stored kinds, so `defaults.py:108-122` will change. |

## Verified (read in this tree)

- **src cites, all correct:**
  - `extract.py:34-53` and `:47-53`, `:34-64`
  - `llm/common.py:86-100`, with the "PDF and image blocks are a trigger row" text at `:89-90`
  - `guard/runmap.py:1-8`, `:3-6` and `:178` (TENANT)
  - `defaults.py:108-122`, with TENANT at `:121`
  - `k1b/bundle.py:181-183`
  - `guard/injection.py:1`, `:19-20`, `:38`, `:85`
  - `guard/judge.py:62-79`, `:71` (`redact_text`), `:72` (`chat`)
  - `guard/egress.py:25-30`
  - `k1b/replay.py:1-7`
  - `llm/fake.py:17`, `:21-54`, `:46-47`; keyed by sha256 and attempt
  - `sources/__init__.py:1-11`
  - `evals.py:35`
  - `guard/bedrock_guardrail.py:1-5`
- **Other file and line cites:**
  - `tests/test_lockin_guard.py:189` is `test_vendor_sdks_stay_inside_their_kind_modules`.
  - `tickets/P1.md:27` is the Interim rule, and its quote matches.
  - `grep -i tenant` over `src/hadavin_sdk/store` finds nothing. `TENANT` appears only in `guard/redact.py`, `guard/runmap.py:178` and `defaults.py:121`.
  - No `templates/project/` folder exists (glob found none).
- **Arithmetic:** 10,000 × 500 = 5,000,000. The re-index is another 5,000,000. 1,000 × 30 × 50 = 1,500,000. The total is 11,500,000, so line 127 (PL1) is correct. PL3: 200 pages × 500 = 100,000 tokens.
- **Bible (RULES.md):** R98 and R221 (transcripts out of logs), R132 (pgvector + full-text, three managed families, and the 3-of-1000 filter test), R139, R144, R145 (neutral default is a self-hosted cross-encoder), R153, R183, R363 (embedder default is a client-cloud managed embedder). The ticket's reading of the R145-versus-"no reranker by default" conflict is sound.
- **Agreement with kit-plan-v2:**
  - The Tier B statement matches section 3.
  - The AK0 row, including the inventory list of 9 items, matches.
  - Owner decisions (a) to (e) map to PL1, PL2 and PL3. (c) and (d) are correctly "not asked".
  - The section 8 risks match.
  - "Depends on" is correctly flagged as a departure from "Core v1 (P8c)".
  - P7a, P7b, P7f and P7h are absorbed per section 4.
  - The deferred scan trigger is correct.
- **Agreement with GAPS:** G6 (sub-processor), G17 (the owner decides the tenant model; "one deployment per client" is allowed), C2 (sub-processor list).
- **Agreement with LEAD-ORDERS:**
  - Order 23 item 1 (AK0 first, Tier B) and item 4 (NEEDS LEAD) match.
  - Order 23 item 6 (freeze-list kit section) matches.
  - Order 20 item 1 (PostgreSQL 16 and 17) and item 4 (key through the lead) match.
  - Order 8(5) (placeholders only) matches.
  - Order 6(b) (one reviewer, one round, at most 2 fix batches) matches.
  - The Never-list items match.
- **Other claims confirmed:**
  - `freeze-list.md` has a "Hot files" line (19), and plan-v3 rule 10 is the hot-file rule.
  - `tickets/P4c.md` and `tickets/P5a.md` exist.
  - `P5b3.md:192` rewrites `extract.py:57-64`, which supports the ticket's U7 note.
- **Template fields:** all 17 are present, in the template's order. The Path class is "other", and the "no round cap" answer is given. Where the ticket departs from the template, it explains why:
  - A single reviewer is used instead of correctness plus adversarial (Tier B).
  - There is no `pre-` tag, because there is no code.
  - There are no code tests, because there is no code.
- **E1 columns:** counting the leading pipe, the options-table columns put Checked in field 6, Licence in field 5 and Cost in field 8. The awk field numbers are therefore right.

## Not checked

- UNVERIFIED: the stated heads `ce70eb5` (src) and `dc0c112` (handover). There is no git here.
- UNVERIFIED: the claims that E1 was run on a 3-row sample and that the A1/A2 probes at 03:28 UTC were caught. No shell.
- UNVERIFIED: all library, licence, price and pgvector filter-behaviour claims. The ticket itself marks them UNVERIFIED.
- UNVERIFIED: the "rung" labels against the tool-ladder text, beyond the nit above.
- UNVERIFIED: `MODEL-ROUTING.md`, plan-v3 rule 3 and amendments. I did not read them.
- UNVERIFIED: that P2d and P5c will move `runmap.py` and `extract.py` lines. I only saw P5b3's range.
- Not checked: R130, R134, R196, R447 content (they exist at RULES.md lines 295, 303, 445, 931).
- UNVERIFIED: the timing question R1-COR-10 (git push times not available).
- Not checked: whether PL numbers in `questions-for-lead.md` already exist, because that file is outside the supplied list.
