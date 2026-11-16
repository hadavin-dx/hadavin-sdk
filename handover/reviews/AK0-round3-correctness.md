# AK0 round 3, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

AK0 rev 3, round 3 correctness review. Read-only. I did not read handover/reviews/ or handover/evidence/. I had no shell (no git, awk or date). I could not confirm that the checkout equals ce70eb5, and I ran none of the E commands. I read the full ticket and orders 23, 27 and 28. All cites below are against the on-disk tree.

Verdict: no Blocker. 3 Majors and 5 Minors in the table below. The ticket is mostly executable, but three points still leave a guess.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-COR-1 | Major | 26 (J2), 36 (D1) | J2 lists `bypasses mask` for D1(c), D2(c) and D2(d) only. D1(d) (per-cloud document services) takes the same raw PDF bytes as D2(d), and it is D1's recommended alternative. Whether D1(d) carries `bypasses mask` in the note is left to guess. | Add D1(d) to the J2 list and to line 36. Add it to A5 or A8 as a manual check: the D1(d) Risk cell contains `bypasses mask`. |
| R3-COR-2 | Major | 113, 168 (PL3), 112 | The run file's command "passes the three caps (pages 200, model calls 50, USD 2.00) the meter enforces". P4b1 revision 3 describes only USD caps (day, month and run, via `Limits.caps`, in micro-dollars). I found no call-count or page cap in P4b1, in `src/hadavin_sdk/limits.py` (no match for "calls") or in P4c. Order 28 says "enforced by the meter", but the ticket cannot name who enforces pages and calls. U11 covers only command names and config keys. | Add an UNVERIFIED line (U13): no P4b1 or P4c row enforces a page or call cap. Add a status-rule item: the run is `NOT READY` until a merged package enforces all three caps. Put it to the lead as one more line in PL11. |
| R3-COR-3 | Major | 114 (item 4), 191 (PL11) | The expected-cost formula reads "pages x 500 tokens x unit price". The unit price is per million tokens (line 36 and the D4 evidence), so the formula needs "/ 1,000,000". It also does not say whether embedding calls count toward the 50-call cap. If the job sends one embedding request per chunk, 200 pages already exceeds 50. The `NOT RUNNABLE` test depends on this. | Write the formula as tokens/1,000,000 x USD per million tokens. State that embedding batches count (or do not count) toward the 50 calls, and give the number of embedding requests as an input to the expected cost. |
| R3-COR-4 | Minor | 65, 196 | Path class names redaction (D8) and money (PL3, PL11), yet "Extended review: no". Orders 6(b) and 8(1) say money and redaction have no round cap. Order 23 ("capped at 3") is newer and the ticket argues from it, but the departure is in no INFORM line and no PL item. | Add INFORM I10: "Extended review no, per order 23 (newer than 6(b) and 8(1)); D8 goes to AK2b's uncapped review". |
| R3-COR-5 | Minor | 32, 73, 77 (PL1 table) | For free-software defaults (D1, D5 pgvector) the Options cell reads `licence cost 0; hosting not costed`. The PL1 column wants "USD per month (formula)", and the `not costed` rule "never applies" to PL1 defaults. What the PL1 cell holds for D1 and D5 is not stated. | State it, for example `0 (licence cost 0 x ...); hosting not costed` or `USD 0.00`. |
| R3-COR-6 | Minor | 75, 146 | Questions 1 to 8 and the E8 `[1-8]` pattern are tied to option (a) only. Line 55 says option (b) carries (a)'s three extra questions, so under (b) 8 answers are needed too. | Write "(a) or (b)" on lines 75 and 146 and in A7a. |
| R3-COR-7 | Minor | 3 | Only order 27's written time is called wrong. Order 28's header says ~04:50Z / 10:20 IST, but the ticket's own commit time is 04:02:07 UTC. Order 26 and order 29 headers also differ from their commits. | Say once that git commit times win for all orders (order 20), or list order 28 beside 27. |
| R3-COR-8 | Minor | 143, 77 | E6 checks D1, D2, D4 and D5 only. Interface 3 also requires a `default` row for D6 (`none`), and PL1 requires "one D4 default per cloud". Neither is checked by any command or A-row. | Add D6 to E6's list. Add a manual A9 line for "one D4 per cloud". |
| R3-COR-9 | Nit | 141, 88 | E4 will flag benign words such as "adapter-based" (the `ada` prefix plus `[a-z0-9]*` plus a hyphen). The "list in acceptance.txt" route covers this. | Optional: put a `\b` after the family word. |
| R3-COR-10 | Nit | 88 | "Append two numbered entries" to `owner-visible-limits.md`, which holds entry 1 now. | Say "the next two free numbers". |

Verified, by reading the files:
- **Source cites.** Every cite in lines 36 to 49 and 93 to 105 matches the file text:
  - `extract.py`: 34-53, 47-53, 34-64.
  - `llm/common.py`: 86-100, with the "PDF and image blocks are a trigger row" text on 89-90.
  - `guard/runmap.py`: 1-8, 3-6, 178.
  - `guard/redact.py`: 1 and 7.
  - `guard/injection.py`: 1, 19-20, 38, 85.
  - `guard/judge.py`: 62-79, with `redact_text(text, {})` at 71 and `chat` at 72.
  - `guard/egress.py`: 25-30.
  - `k1b/replay.py`: 1-7.
  - `llm/fake.py`: 21-54, 17, 46-47.
  - `sources/__init__.py`: 1-11.
  - `evals.py`: 1 ("exact field match") and 26-32 (subset match).
  - `k1b/bundle.py`: 181-183.
  - `guard/bedrock_guardrail.py`: 1-5.
  - `defaults.py`: 108-122 with PHONE at 120 and TENANT at 121.
  - `tests/test_lockin_guard.py:189`.
- **Absence claims.** There is no "tenant" in `src/hadavin_sdk/store` (0 matches). TENANT exists only as a redaction kind. There is no `templates/project` folder. `freeze-list.md` has 0 lines matching `AK` or `Kit`. `AK2b.md` does not exist (the AK tickets present are AK0, AK1, AK2a, AK4a, AK-G1 and AK-G2).
- **AK1 cites.** `AK1.md:288` is I2. `AK1.md:324` is row V8 and reads "AK0 PL5 (questions item 57)". `AK1.md:91` gives `PIPELINE_MAX_READERS = 1000`.
- **Counts.**
  - Acceptance rows: 13.
  - Evidence commands: 10 (E1 to E9 plus E7b), plus R1.
  - Cuts: 8. INFORM: 9. UNVERIFIED: 12.
  - PENDING LEAD: 11, of which 5 are ANSWERED (PL1, 2, 3, 4, 6) and 6 are NEEDS LEAD (PL5, 7, 8, 9, 10, 11).
  - Line 272 arithmetic: 23 + 1 + 1 = 25 decision rows.
  - The planted-fault column covers A1 to A12. A12 pairs with E9, and its manual part covers the `ak0-optin-run.md` content.
- **Template fields.** All 17 template fields appear in order. Reviewers is on line 150, Done on 151 and Rollback on 152. The departures from the template (no tag, extra reviewer inputs) are explained.
- **Arithmetic.**
  - 10,000 x 500 = 5.0M, plus a 5.0M re-index, plus 1,000 x 30 x 50 = 1.5M, gives 11.5M.
  - 200 pages x 500 = 100,000 tokens.
  - USD 2.00 = 2,000,000 micro-dollars, which matches P4b1's micro-dollar unit.
- **Dates.** All the UTC to IST conversions on lines 3 and 5 and in the E-run times are correct (+5:30): 04:08 / 09:38, 03:50:41 / 09:20:41, 03:30:44 / 09:00:44, 04:02:07 / 09:32:07, 03:47 / 09:17, 03:28 / 08:58, and 04:08 to 04:12 / 09:38 to 09:42. Order 27's header time is indeed wrong against the 03:42:46 commit.
- **Orders.**
  - Order 27 item 53: the quoted "no AGPL/SSPL-class licence in a default" is exact. Items 54 to 58 are as described.
  - Order 28: the ceiling and its "cap, not a start order" wording match, and it adds no key and no call.
  - Order 22 item 27 (PHONE) and order 24 item 39 (limits file) match.
  - Order 23: the "capped at 3" and freeze-list wording match.
  - Order 23 item 2: P7a is absorbed by AK-G2, as the ticket says.
- **E-command column positions.** With `-F'|'`, the Id, Licence, Checked, Cost and Verdict columns are fields $2, $5, $6, $8 and $10. E1, E3 and E6 use the right ones. E2's regex matches the Verdict column. E9's regex matches the layout in Interface item 1 of the run file. E8 needs at least 5 words (the 4-word-plus-space prefix).
- **Secrets.** No real-looking secret or model id in the ticket text.

Not checked, UNVERIFIED:
- Whether the tree equals `ce70eb5` and `handover/` equals `4655015`. I had no git.
- The claimed commit shas and times (`0ae4785`, `e302a62`, `083d33a`, `92dac2d`, `d32d904`).
- Whether any E command runs as written. I did not run any, including E1, E2, E4, E5, E6 and E7.
- The cite `freeze-list.md` "Hot files".
- `kit-plan-v2.md` lines 42, 46 and 60. Line 78 and line 57 are consistent; line 37 matches the Tier A text.
- The P4a "W" definition and P4b1's other facts beyond the revision number and micro-dollar unit.
- The claim that CI does not run on pushes to `core/cloud-handover`.
- Library, licence and price facts. The ticket itself marks these UNVERIFIED.
- Whether the AK2a fixture folder can supply 200 pages. The cap is a maximum, so this is harmless.
- `AK-G1`, `AK-G2` and `AK4a` beyond their existence.
