# AK0 round 2, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

AK0 revision 2: correctness review, round 2 (R2-COR). I found 0 Blockers, 3 Majors, 8 Minors and 4 Nits.

Limit of this review: I had no shell, only Read, Grep and Glob. I could not run any E-command, any arithmetic snippet or `git`. Every E-command verdict below is hand-derived and marked UNVERIFIED. I did not read `handover/reviews/` or `handover/evidence/`.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R2-COR-1 | Major | 126 (E7b), 73 (Interface 8), 114 (A10) | E7b prints hits on a correct note. The URL strip leaves path-like cites, and the `[A-Za-z0-9+/=_-]{32,}` rule matches runs that stop at `.` or `:`. Hand count, UNVERIFIED: `src/hadavin_sdk/guard/bedrock_guardrail` is 39 characters. `src/hadavin_sdk/sources/__init__` is 32. A quoted token such as `test_vendor_sdks_stay_inside_their_kind_modules` (line 25) is 47. `handover/evidence/AK0/acceptance` is 32. Interface 8 forces full `src/hadavin_sdk/<path>` cites with quoted tokens, so "prints nothing on the real files" cannot hold. A10 then fails on a good note, or the runner waives hits by hand. | Strip cite fragments before the rule, for example also `s#(src\|tests)/[A-Za-z0-9_./-]*##g` and drop `"..."` tokens. Or raise the rule to 40 and add a mixed-case-and-digit test. Run E7b on a made-up note with every Interface-8 cite before relying on it. |
| R2-COR-2 | Major | 111 (A7), 127 (E8) | A7's planted fault is an example that masks the question and the chunks in two maps and shows two placeholders. E8 only counts lines matching `^[1-5]\. ` in the section, so it cannot catch that fault. A7 claims the check catches it. A numbered line inside the example could also inflate the count. | Make the detecting step explicit. Either add a command (fixed example block: one placeholder token must appear in both the chunk lines and the question line), or relabel that half of A7 manual (reviewer read, like A9). Say that example lines must not start with `N. `. |
| R2-COR-3 | Major | 123 (E5), 112 (A8) | E5 is a template, not an exact command. (a) Nothing extracts the cites from the note. (b) The ticket's own cites are ranges (`extract.py:34-53`), but `sed -n '<line>p'` and Interface 8 take one line. (c) There is no pass rule. `grep -F` exits 1 on a miss, but the text says "the runner pastes the output". A8 therefore has no mechanical pass or fail. | Give a loop. It extracts `(src/hadavin_sdk\|tests)/\S+:[0-9]+ "[^"]+"`, runs `git show \| sed -n \| grep -F -q`, and prints each cite that fails. State that a range cite is split into one cite per token line. Expected output: nothing. |
| R2-COR-4 | Minor | 122 (E4) | The model-id regex needs a digit after the last separator, so digit-less ids are missed. By hand, UNVERIFIED: `mistral-large-latest`, `<model-id>`, `gemini-flash-latest`, `bge-small-en`, and `multilingual-e5-large` (the `e5` ends the prefix, and `-large` has no digit). Caught by hand: `gpt-4o`, `voyage-3`, `text-embedding-3-small`, `amazon.titan-embed-text-v2:0`. The "15 of 15" figure (line 173) comes from the resolve's own set, UNVERIFIED. | Allow `[-.:_][a-z0-9]+` as the tail, and remove false positives by an allowlist in `acceptance.txt`. Or add a `latest\|large\|small\|pro\|flash` tail. |
| R2-COR-5 | Minor | 109 (A5), 121 (E3) | A5 allows `LGPL-<v> owner-yes`, but E3 accepts only `LGPL-(2.1\|3.0)` and `MPL-2.0`. SPDX writes `LGPL-3.0-only` and `LGPL-3.0-or-later`, and Interface 3 says "an SPDX id where one exists". Those spellings print as violations even after the owner says yes. | Use `LGPL-(2\.1\|3\.0)(-only\|-or-later)?` and the same pattern in J1 and A5. |
| R2-COR-6 | Minor | 37 (D6), 68 (Interface 3), 28 | D6 says "no cost row (nothing is built)". Interface 3 says an Options row exists for D6 and its cost cell is never blank. The "not costed" list names the reranker but gives no cell text. | Say D6(b) reads `licence cost 0; hosting not costed` or `not costed: nothing built (D6)`. |
| R2-COR-7 | Minor | 22 (J2), 45 (D14), 32/33 | J2 says the `bypasses mask` Risk cell applies to D14. D14 has no Options row and so no Risk cell (line 4 of cut surface, Interface 3). D1(d) and D2(d) have no rung label, which the Rung column requires. Test-only rows (D4(a) fake embedder, D5(c) in-memory) have no stated verdict among the four allowed words. | D14's risk goes in its prose. Add rungs for D1(d) and D2(d). State the verdict for test-only rows (suggest `alternative`), so that E6 and A4 stay unambiguous. |
| R2-COR-8 | Minor | 39, 151 (D8/PL5), 42 of kit-plan | The kit-plan AK0 row requires the masking policy to say "same pseudonyms in both" (stored and queried). Recommended (d) has no lasting map, so the pseudonyms differ between ingest and query. The departure is only in PL5 and question (3). It is not labelled as a departure from the kit-plan row. | Add one sentence in D8 and PL5: "(d) departs from kit-plan row AK0 wording 'same pseudonyms in both' because ...". |
| R2-COR-9 | Minor | 21 (J1), 153 (PL7) | J1 attributes the never-default list "GPL of any version, AGPL, SSPL, BUSL, Elastic, Commons Clause, non-commercial" to order 27 item 53 (line 21). The order says only "no AGPL/SSPL-class licence in a default". The wider list is the author's. PL7 states it as "never under any option" and puts it nowhere in INFORM. I6 covers allowlist additions only. | Add an INFORM line (I8) or an explicit PL7 option for the wider list. Quote only the order's actual words as the order. |
| R2-COR-10 | Minor | 149 (PL3), 28 | PL3 says AK0 will replace the USD 2.00 ceiling with an estimate from the dated price. That run needs 50 model calls. The workload line says answer-model calls are "not costed". The note therefore has no model price to compute with. | Either add a model-call price row for the PL3 estimate only, or say the ceiling stays unchanged until AK2b. |
| R2-COR-11 | Minor | 4, 3, header lines of orders 23-27 | The ticket says it was written from 03:46 UTC and applies order 27, whose header reads "~04:30Z / 10:00 IST". Revision 1 (03:30:44 UTC) predates order 23 (~03:45Z). "Git commit times win" (order 20) may explain this, but I cannot check commit times here. UNVERIFIED. | State in the ticket the push time of order 27 as seen in git, or drop the claimed times. |
| R2-COR-12 | Minor | 161 (I3), 10-15 (cuts), 208 | "Cuts: 5" is true by numbering. Item 5 bundles three cuts (lasting map, fault-seeding check, extra-deployment cost), and I3 lists seven things. A reader counting cuts gets 7. | Number them 1 to 7, or say "5 numbered items, 7 cuts" in the Counts block. |
| R2-COR-13 | Nit | 36 (D5) | The lettering runs (a), (b), (c), (e) with no (d). | Rename (e) to (d). |
| R2-COR-14 | Nit | 125 (E7) | `grep -vE 'UTC\|Z'` passes any line that contains a capital Z (for example "Zero", "Zapier") together with a zoneless time. | Use `UTC\|[0-9]Z`. |
| R2-COR-15 | Nit | 65-72, 128, 147 | Interface item 5 does not give the heading level of "Masking policy for RAG". E8 needs the literal `## Masking policy for RAG`. The PL1 defaults table is described in PL1 but has no layout or section in Interface 3 or 7. It must not start with `\| D<n> \|`, or E1, E2 and E6 break. | Add the exact `##` heading text and the PL1 table columns, and say its rows do not start with `\| D`. |
| R2-COR-16 | Nit | 41 (D10) | D10 says P7a is "absorbed ... (kit-plan section 4)". Kit-plan section 4 only lists P7a as absorbed "as written above", and section 3 names P7b, P7f and P7h but not P7a. P7a is absorbed by AK-G2 per order 23 item 2. | Cite order 23 item 2 for P7a. |

Verified (read in this tree; none of it run).
- Counts are as claimed:
  - Decisions: 14 (D1 to D14). Options rows: D1 to D7 and D12.
  - Acceptance rows A1 to A11: 11. Evidence commands: E1 to E8 plus E7b is 9, plus runner step R1. Every A-row maps to a command except A9, which is manual.
  - PENDING LEAD: 10 items, 6 ANSWERED (PL1 to PL6, order 27 items 53 to 58) and 4 open (PL7 to PL10).
  - INFORM: 7. UNVERIFIED: 9. Cuts: 5 numbered (see R2-COR-12). Round-1 resolve: 26 fixes plus 1 decline is 27.
- Arithmetic:
  - Reference workload: 5,000,000 + 5,000,000 + (1,000 x 30 x 50 = 1,500,000) = 11,500,000 tokens.
  - PL3 run: 200 pages x 500 tokens = 100,000 tokens.
  - IST offsets: every UTC to IST pair in the ticket and in order headers 20 to 27 is exactly +5:30. Examples: 03:46 UTC is 09:16 IST, 03:30:44 UTC is 09:00 IST, 03:47 UTC is 09:17 IST.
- Template: all 17 fields are present and in the template's order. The Problem field has exactly 5 sentences. Departures from the template are justified in the text: one reviewer (Tier B), no code gates, no rollback tag.
- E1, E3 and E6 use the right awk columns for the 9-column Options table. The pipe splits as `$1` empty, `$2` Id, `$5` Licence, `$6` Checked, `$8` Cost, `$9` Risk, `$10` Verdict.
- The E3 allowlist equals the J1 permissive list plus `service terms`, `core` and the two weak-copyleft owner-yes forms (apart from R2-COR-5).
- E1, E2, E3 and E6 do catch their planted faults by reading the code: empty Checked cell, 100-day-old check, verdict "maybe", PyMuPDF with an AGPL default, D5 with no alternative. They pass the recommended defaults: pgvector with PostgreSQL (the licence name itself is UNVERIFIED), a permissive reader, a managed embedder with `service terms`, and the core row with `core; this repository`.
- Source cites re-read on the current tree. All match their line, token or range:
  - `extract.py` 34-53, 47-53 and 34-64.
  - `llm/common.py` 86-100 and 89-90.
  - `llm/fake.py` 21-54, 17 and 46-47.
  - `guard/runmap.py` 1-8, 3-6 and 178 (`TENANT`).
  - `guard/redact.py` line 1 and `<KIND_n>` at line 7.
  - `guard/judge.py` 62-79, 71 and 72.
  - `guard/egress.py` 25-30.
  - `guard/injection.py` 19, 38 and 85.
  - `guard/bedrock_guardrail.py` 1-5.
  - `k1b/replay.py` 1-7.
  - `k1b/bundle.py` 181-183.
  - `sources/__init__.py` 1-11.
  - `evals.py` 26-32 and 1 (the docstring says "exact field match", which is wrong).
  - `defaults.py` 108, 120 (PHONE) and 121 (TENANT).
  - `tests/test_lockin_guard.py` 189.
  - `tickets/P1.md` 27 (Interim rule).
- `tenant` does not appear in `src/hadavin_sdk/store` (Grep: 0 matches).
- No `templates/project` folder exists in the repository.
- Order citations hold: 6(b), 7(3), 8(5), 20 items 1 and 6, 22 item 27, 23 items 2, 3, 4 and 6, and 27 items 53 to 58. Order 27 items 53 to 58 are paraphrased correctly, except for the J1 extension (R2-COR-9).
- Bible R139 and R153 say what the ticket says. Kit-plan Tier B and the AK0 row are quoted correctly.
- No real-looking secret and no model id appears in the ticket.

Not checked (UNVERIFIED).
- No E-command, awk, grep or python snippet was run, because I had no shell. All E1 to E8, E7b and R1 verdicts above are hand-derived.
- The hand counts for E7b and E4 should be re-run by the author before the fix is accepted.
- The claimed scratch probes of E1 (revision 1) and E4 ("15 of 15", "0 of 32"), and the claim that `git log -1 -- src` prints `ce70eb5`. This tree is not a git repository for me.
- Commit times and shas: `0ae4785`, `53e8b12` and `ce70eb5`.
- The round-1 resolve file, the two round-1 reports, and the "27 rows over 34 ids" figures, because I was told not to read `reviews/`.
- Text I did not read: `GAPS.md`, `.claude/rules/tool-ladder-before-code.md` as cited, the bible R98, R221, R183, R447, R144, R132 and R145 text beyond the grep hits, the `freeze-list.md` Hot-files body, `amendments.md` beyond a grep for AK0 and P7 (hits only on two long lines), and the `P4c` and `P5a` ticket shape.
- All external facts about licences and prices (pgvector, pypdf, pdfminer.six, Tesseract, PyMuPDF and others). The ticket marks them UNVERIFIED itself.
- Whether the line number cited for `guard/injection.py` "fail closed, `:1`" matches. I only confirmed a "fail closed" comment at line 89.
