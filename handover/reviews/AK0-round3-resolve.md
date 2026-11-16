# AK0 round 3 resolve (egm:egm-resolve, AUTO mode; LAST round)

**Status:** resolved (categorised; AUTO, so the skill's interactive gate is skipped per the lead's order 20 item 6 brief). The ticket is NOT edited. The fixes are build notes BN-1 to BN-17 below. They win over the ticket text. This file replaces the skill's default file name `goldfish_review_report.md`.
**Target:** `handover/tickets/AK0.md` revision 3 (commit `e8c0e60`, 2026-11-06 04:12:40 UTC / 09:42:40 IST), full file read (274 lines; Tier B; D8 on the redaction path, the run file on the money path).
**Findings:** 24 ids.
- `reviews/AK0-round3-adversarial.md`, R3-ADV-1..14: 0 Blocker, **6 Major** (ADV-1 to ADV-6), 6 Minor, 2 Nit.
- `reviews/AK0-round3-correctness.md`, R3-COR-1..10: 0 Blocker, **3 Major** (COR-1 to COR-3), 5 Minor, 2 Nit.
- Severity is taken from the tables and never changed here.
**Gate:** order 23 caps kit tickets at 3 rounds, then freeze. Order 20 item 6 allows one more round only for a money or redaction package whose last round had no Blocker and at most 2 Majors. Round 3 has 9 Majors. R3-ADV-1 and R3-COR-2 are one defect, and so are R3-ADV-4 and R3-COR-3, so there are 7 distinct Major defects. So there is **NO round 4**. AK0 freezes at revision 3 with this file attached, except D8 (BN-11). The banner below goes under the ticket's revision line. Every Major is closed by a build note here. The orchestrating session adds the ledger rows (the ticket's review rule). D8's open points also go to AK2b's Tier A review, which has no round cap (ticket line 4).
- Nothing is escalated to the owner directly. Five items go to the lead as NEEDS LEAD: PL5 updated, PL11 updated, and the new PL12, PL13 and PL14. Three new items are INFORM: PL15, PL16 and PL17.

## Honest note (what I did NOT check, first)
- **Nothing was run except arithmetic and two check scripts on made-up samples.** No real model or embedding call was made, no key was held, nothing was installed, and no network was used (order 27 item 55). I ran E10 and E11 (new, BN-3) with `python3 -I` and `awk` on four made-up run files in my scratchpad. E11 caught one sum that I had worked out by hand wrong (893,606 instead of 893,605). That is evidence the check works, and also evidence that my hand arithmetic needs the check. Nothing was written to `handover/` except this file.
- **I did not run the redactor.** The ADV-5 fact rests on reading: the code comment at `guard/redact.py:424-426` and P5c's own "does NOT promise" list (`tickets/P5c.md:399`). I measured no miss rate, so the share of names missed is unknown (see the partial contest in the table).
- **AK2b has no ticket** (`tickets/` holds no `AK2b.md`). So every point that hands work to AK2b (page and call limits, embedding metering, the bare-name test) is a requirement on a ticket that does not exist yet. The orchestrating session must carry these to AK2b's ticket. Nothing enforces that except coupling C-1 below.
- **Not re-read by me:** the full text of P4b1 (I read lines 10-17, 31-32, 49, 89-103, 250-259 and grepped the rest), P4c beyond a grep, P4b2 beyond a grep, and `docs/DATA-EGRESS.md` (the redactor comment points there). Also not re-read: the vendor pages and the PostgreSQL logging values (still U1 to U3, U10).
- **Bytes as an upper bound on tokens (BN-4)** is P4a's rule for the worst case (`tickets/P4a.md:84`, "the byte bound of its prompt"). That it also holds for every embedder's billing unit is UNVERIFIED for tokens. It does hold for characters, because one UTF-8 character is at least one byte. It goes in as U14.
- **The git facts are checked.** The repository has git, although the reviewers said they had none. The order commit times below come from `git log -- handover/LEAD-ORDERS.md`.

## Facts I checked myself (read on disk, git, or `python3 -I`)
- **F1, R3-ADV-1 and R3-COR-2 are TRUE.**
  - P4b1's `Caps` has three USD fields only: `day`, `month` and `run` (`tickets/P4b1.md:96`).
  - `grep -ci embed tickets/P4b1.md` prints `0`, and so do the same greps on P4c and P4b2.
  - `grep -ci calls src/hadavin_sdk/limits.py` prints `0`. No P4b1, P4c or P4b2 line names a page cap or a call-count cap.
  - The only planned home of embedding metering is kit-plan-v2 row AK2b: "the embedding price record and batch reserve/settle against the meter" (`studio-notes/kit-plan-v2.md:46`). AK2b has no ticket.
  - The caps for jobs that are not agent runs (embedding at ingest) are still an open money item in AK1 (`tickets/AK1.md:300`, its PENDING LEAD 2).
- **F2, own finding N1.** P4b1 has its own live-call gate: "No live provider call from any call site until P4c-2 AND P4b2-a have merged" (`tickets/P4b1.md:49`). The run file's status rule (ticket line 112) names only P4b1, so a file could turn `READY` against P4b1's own gate.
- **F3, own finding N2.** `Meter.reserve` takes one `run_id`, and `caps.run` must be `None` when `run_id` is `None` (`tickets/P4b1.md:98`). A run cap therefore covers only the reservations made under ONE run id. If the embedding batches and the model calls reserve under different run ids (or the embedding under none), "USD 2.00 in total" becomes 2.00 per part, or no cap on the embedding.
- **F4, R3-ADV-5 is TRUE.** The redactor finds a NAME only after a name field's key, a title (`Mr`, `Dr`, ...) or `Dear` (`guard/redact.py:427-447`). The code says so itself at `:424-426`: "Honest limit: a name in free prose with no such marker is NOT found". P5c keeps this. Its list "What P5c does NOT promise" starts with "(a) names in free prose with no title or `Dear`" (`tickets/P5c.md:399`), and its detector-model backend (a local model that finds names) is an outline only, with a trigger (`tickets/P5c.md:309`).
- **F5, R3-COR-3 and R3-ADV-4 are TRUE.** `python3 -I` arithmetic:
  - 200 pages x 500 tokens = 100,000 tokens = 0.1 million, so the formula without "/ 1,000,000" overstates the cost a million times;
  - with one embedding request per chunk, 500-token chunks give 200 requests and 1,000-token chunks give 100, both above 50;
  - 50 questions x 50 tokens = 2,500 question tokens, which line 114 leaves out;
  - USD 2.00 = 2,000,000 micro-dollars.
- **F6, R3-COR-1 is TRUE.** J2 (ticket line 26) applies `bypasses mask` to D1(c), D2(c) and D2(d) only. D1(d) is the same per-cloud document service as D2(d), and line 36 gives it no `bypasses mask`.
- **F7, R3-COR-7 and R3-ADV-13 are TRUE** (`git log -- handover/LEAD-ORDERS.md`, times in UTC):

  | Order | Header says | Commit |
  |---|---|---|
  | 26 | ~04:25Z | 03:40:43 |
  | 27 | ~04:30Z | 03:42:46 |
  | 28 | ~04:50Z | 04:02:07 |
  | 29 | ~04:15Z | 04:04:25 |
  | 30 | ~04:25Z | 04:14:25 |

- **F8, R3-ADV-7 is TRUE.** E1 prints "no licence source" when `$5` has no `;` (ticket line 138), and an `unreadable <date>` Licence cell has none.
- **F9, R3-COR-10 is TRUE.** `owner-visible-limits.md` holds entry 1 only. Its rule is "append one entry per limit at the end, numbered ... Do not edit another author's entry".
- **F10, the E10 and E11 checks work on samples** (scratchpad only). On a clean made-up `READY` file, E10 printed `3`, `3` and `1`, and E11 printed `ok 893605`. On the planted faults:
  - a command with `--calls 60`: E10's command count gave 2;
  - a wrong total: E11 printed `total_micro 800000 != recomputed 893605`;
  - 10 embedding requests plus 45 answer calls: E11 printed `calls 55 > 50`;
  - a total of 2,453,605 micro-dollars: E11 printed `over cap: 2453605`.

## Banner for the ticket (placed under the revision line, word for word)
> **BUILD NOTES WIN.** Review round 3 (`reviews/AK0-round3-adversarial.md`, `reviews/AK0-round3-correctness.md`) had 9 Majors, so there is no round 4 (orders 23 and 20 item 6). This ticket is FROZEN at revision 3, except D8, which stays open until a numbered order records the owner's PL5 answer. AK0's executor applies build notes BN-1 to BN-17 in `reviews/AK0-round3-resolve.md`. Where a build note and the text below disagree, the build note wins. The CHANGELOG sections are history, not instructions. Totals after the notes: 14 acceptance rows (A7c new), 12 evidence commands (E10 and E11 new) plus R1, 17 PENDING LEAD items, 3 owner-visible entries to append. The run file is `NOT READY` until all three caps are enforced by merged code with a test (BN-1), and `READY` never means "run": the owner's yes with the figure is a separate numbered order (BN-2).

## Decisions (one category per finding id)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 (Major), R3-COR-2 (Major) | PROPOSE FIX (NEEDS LEAD 12) | TRUE (F1, F2, F3). A table in the run file says which package enforces each cap, with its test id. USD 2.00 is P4b1's run cap, with the embedding and the model calls under ONE run id. Pages 200 and calls 50 are limits in AK2b's job, which fail closed, each with a test. `NOT READY` lasts until all three are enforced by merged code with a test, and until P4b2-a and P4c-2 have merged (P4b1's own gate). New U13. The alternative, "USD only, said plainly", goes to the lead. **BN-1.** |
| R3-ADV-2 (Major) | PROPOSE FIX | TRUE. Order 27 item 55 ("I will ask the owner with these numbers only when a run is actually ready") and order 28 ("a cap, not a start order") make `READY` mean "ready to ask the owner", not "run". Line 2 of the run file becomes `owner yes with figure: <order n> | none`. The lead runs nothing while it reads `none`. Added to the lead's checks and to A12. This applies the orders, so no new PL item is needed. **BN-2.** |
| R3-ADV-3 (Major), R3-ADV-12 (Minor) | PROPOSE FIX (NEEDS LEAD 11 updated) | TRUE. The orchestrating cloud session completes the run file as a step of AK2b's Done. It is checked mechanically by E10 (caps and placeholder) and E11 (a recompute with `python3 -I`). Then a fresh reviewer checks it on the money path, with no round cap (orders 6(b) and 8(1)), before the lead takes the figure to the owner. **BN-3.** |
| R3-ADV-4 (Major), R3-COR-3 (Major) | PROPOSE FIX (NEEDS LEAD 13) | TRUE (F5). New formula in integer micro-dollars: the embedding part uses the UTF-8 bytes of the pages AND the questions as the upper bound (P4a's byte rule), divided by 1,000,000, times the price per million units of the D4 row that the run's embedder config selects. The model part is answer calls x W of the configured route's model family (quoted with `<model-id>`). No safety factor is needed, because both parts are upper bounds (U14). How embedding requests count against the 50 calls is the owner's reading of his own figure: NEEDS LEAD 13, with an interim default of "they count". **BN-4.** |
| R3-ADV-5 (Major) | PROPOSE FIX (NEEDS LEAD 5 updated, NEEDS LEAD 14); PARTIAL CONTEST of "state what share of names is missed" | TRUE (F4). The PL5 owner text no longer says that names are hidden. It says names are hidden only where the masking can see one. A third owner-visible entry is drafted. New A7c and an AK2b test pin it: a bare made-up name reaches the embed payload. AK2b's done-condition string must be of a kind the redactor finds. **Contested part:** AK0 cannot state a miss SHARE. Measuring needs documents and a run, and AK0 is desk-only (cut 1). P5c:399 and `redact.py:424-426` already state the fact qualitatively, and the share is measured on AK2a's made-up documents (BN-6). Whether kit v1 needs a name finder before real client documents is NEEDS LEAD 14. **BN-6.** |
| R3-ADV-6 (Major) | PROPOSE FIX (INFORM 17) | TRUE. A dated line that the lead pastes into `sources.md`, marked `lead paste <date>`, counts as the primary source. R1 checks it against the paste. After the paste and R1 the row may be `default` again. The run file stays `NOT READY` with the reason "D4 price unreadable". **BN-7.** |
| R3-ADV-7 (Minor) | PROPOSE FIX (form, no awk change) | TRUE (F8). An unreadable Licence cell is written `unreadable <YYYY-MM-DD>; <URL>`. E1 then sees a `;`, and E3 keeps such a row out of `default`, because `unreadable` is not on the allowlist. **BN-7.** |
| R3-COR-1 (Major) | PROPOSE FIX | TRUE (F6). D1(d) joins the J2 list and line 36. A5's manual part checks that the D1(d) Risk cell holds `bypasses mask`. **BN-8.** |
| R3-ADV-8 (Minor) | PROPOSE FIX (INFORM 15) | TRUE. The freeze-list status reads "frozen at revision 3 with round 3 build notes, except D8 (open until a numbered order on PL5)". **BN-11.** |
| R3-ADV-9 (Minor) | PROPOSE FIX | TRUE. E7b gains a second pass over URLs: known key prefixes anywhere in a URL, and URLs written without a query part. New planted fault: a key in a URL path. **BN-10.** |
| R3-ADV-10 (Minor) | PROPOSE FIX | TRUE. R1 becomes a fixed-string check (`grep -cF`) of the stored quote against the saved page text, and the runner records the count only. New planted fault: a changed digit in a stored price quote. **BN-9.** |
| R3-ADV-11 (Minor) | PROPOSE FIX | TRUE. When the file is `NOT RUNNABLE`, the lead may LOWER the pages or calls (never raise them, never raise USD). The completer then recomputes, and E10/E11 and the money review run again. **BN-5.** |
| R3-COR-4 (Minor) | PROPOSE FIX (INFORM 16) | TRUE. "Extended review: no" is a departure from orders 6(b) and 8(1). It is stated with its basis: order 23 (newer, written for kit tickets) and order 20 item 6. D8 goes to AK2b's uncapped review, and the run file gets an uncapped money review at completion (BN-3). **BN-12.** |
| R3-COR-5 (Minor) | PROPOSE FIX | TRUE. A free-software default's PL1 cell reads `USD 0.00 (licence cost 0 x 10,000 pages); hosting not costed: AK-G16`. **BN-13.** |
| R3-COR-6 (Minor) | PROPOSE FIX | TRUE (ticket line 55: (b) carries (a)'s three questions). "(a) or (b)" goes on lines 75 and 146 and in A7a. **BN-14.** |
| R3-COR-7 (Minor), R3-ADV-13 (Nit) | PROPOSE FIX | TRUE (F7). One sentence: git commit times win for every order (order 20). The headers of orders 26 to 30 differ from their commits. **BN-16.** |
| R3-COR-8 (Minor) | PROPOSE FIX | TRUE. E6 adds D6. A9 gains a manual line: one D4 `default` row per cloud family named in the note. **BN-15.** |
| R3-COR-9 (Nit) | DECLINE | A `\b` right after the family word would miss ids where a digit follows the family name directly (no word boundary between a letter and a digit). The ticket's benign-hit route (listed in `acceptance.txt` with the reason, line 141) already handles "adapter-based". No change. |
| R3-COR-10 (Nit) | PROPOSE FIX | TRUE (F9). "The next free numbers", now three entries. Part of **BN-6.** |
| R3-ADV-14 (Nit) | DECLINE | The reviewer asks for nothing ("None needed"). |
| (resolve, own) N1 | PROPOSE FIX | P4b1's live-call gate (F2): `READY` also needs P4b2-a and P4c-2 merged. Part of **BN-1.** |
| (resolve, own) N2 | PROPOSE FIX | One run id for the embedding and the model calls (F3). Part of **BN-1.** |
| (resolve, own) N3 | PROPOSE FIX | AK2b's done condition ("embedding payload never contains the seeded personal data string") holds only for a seeded string of a kind the redactor finds. Part of **BN-6.** |
| (resolve) counts | fact only | **BN-17** holds the count delta. |

## Build notes (round 3), to be copied into the ticket as the section "Build notes (round 3 resolve)"

**BN-1. Who enforces each cap; `NOT READY` until all three are enforced (R3-ADV-1, R3-COR-2, own N1 and N2; NEEDS LEAD 12).**
- **Place:** section "Opt-in run file", item 2 (status rule, line 112) and item 3 (command, line 113); UNVERIFIED list (new U13).
- **Item 2 is replaced by:**
  > 2. **Status rule.** `NOT READY` until ALL of these hold:
  >    - (i) AK2b's opt-in job is merged: the D4 default embedder kind behind the AK1 gate, with D8 masking;
  >    - (ii) P4b1 (-a and -b), P4b2-a and P4c-2 are merged (P4b1's own live-call gate, `tickets/P4b1.md:49`);
  >    - (iii) the D4 row that the run's embedder config selects has a dated unit price in `sources.md`, read live or pasted by the lead (BN-7);
  >    - (iv) each of the three caps has a row in the file's **Caps** block naming the merged package and the test id that enforces it, as in the table below.
  >
  >    While `NOT READY`, the file lists each missing item by package, and the command block reads `not ready: waiting for <package>`. `NOT RUNNABLE` when the expected total is above USD 2.00 (item 4). `READY` otherwise. `READY` means "ready to ask the owner", never "run" (BN-2). Today it is `NOT READY`: AK2b has no ticket, P4b1 is revision 3, and no package enforces the page or call cap.
  >
  > | Cap | Enforced by | How | Test the file names |
  > |---|---|---|---|
  > | USD 2.00 in total (2,000,000 micro-dollars) | P4b1's meter, run cap `Caps.run` | Every model call (through `MeteredLLM`) AND every embedding batch (AK2b's reserve and settle against the meter, kit-plan row AK2b) reserves under ONE `run_id`, with `Caps.run` = 2.00. If the parts used two run ids, each would get its own 2.00. | an AK2b test: with the run cap set to the cost of one batch, a second batch in the same run is refused before the embedder is called |
  > | 200 made-up pages | AK2b's opt-in job | A config value that only lowers (`le=200`). The job counts pages BEFORE it reads any page, and refuses the whole run if the folder holds more. It fails closed. | an AK2b test: 201 made-up pages give a refusal and zero embedder calls; plus a mutant |
  > | 50 model calls | AK2b's opt-in job | A config value that only lowers (`le=50`). It counts every paid request in the run (answer-model calls AND, under NEEDS LEAD 13(a), embedding requests) and refuses request 51 before it is sent. | an AK2b test: the 51st request is refused and the fake provider sees 50; plus a mutant |
- **Item 3, the sentence "pass the three caps as config values the meter enforces"** reads: "pass the three caps as config values to the components named in the Caps block (USD: P4b1's run cap; pages and calls: AK2b's job limits)".
- **New U13:** "No v1 package enforces a page cap or a model-call cap. P4b1's `Caps` has USD fields only (`tickets/P4b1.md:96`), and P4b1, P4b2 and P4c never mention embedding. Embedding metering is planned only in kit-plan row AK2b, which has no ticket. The page and call caps exist only as BN-1's requirement on AK2b."
- **If the lead picks NEEDS LEAD 12(b)** (USD only), the Caps block keeps only the USD row. Line 3 of the run file then reads `pages and calls are NOT enforced by code; only USD 2.00 is`, and the lead tells the owner that sentence with the figure.

**BN-2. `READY` is not a start order (R3-ADV-2).**
- **Place:** run-file item 1 (layout, line 111), item 6 (lead's checks, line 116), A12 (line 134), E9 (line 147).
- **Item 1 gains** a fixed line 2: `owner yes with figure: <order n> | none`. AK0's executor and the completer always write `none`. Only the lead replaces it, with the number of the order that records the owner's yes to the exact total in the file.
- **Item 6 gains, as its first check:** "line 2 names an order, and that order quotes the same `total_micro` as the file. If line 2 reads `none`, do not run: take the figure to the owner (order 27 item 55)."
- **A12 gains a planted fault:** a `READY` file whose line 2 reads `none` is run by the lead's checklist (it must stop).
- **E9 gains:** `sed -n 2p ak0-optin-run.md | grep -cE '^owner yes with figure: (order [0-9]+|none)$'` prints `1`.

**BN-3. Who completes and checks the run file (R3-ADV-3, R3-ADV-12; NEEDS LEAD 11 updated).**
- **Place:** run-file items 2 and 4; Files list (line 86); Evidence commands (after E9); A12; Done (line 151); PL11 (line 191).
- **Who:** AK0's executor writes the `NOT READY` file. The **orchestrating cloud session completes it**, as a listed step of AK2b's Done, once BN-1's conditions hold. It fills the Caps block (with test ids from the merged code), the Expected cost inputs (BN-4) and the command. The lead does not compute the figure. The completer never holds a key and makes no call (order 27 item 55): every input is a byte count, a dated price line, or a constant from merged code.
- **Fixed blocks the completer writes** (E10 and E11 read them):

  ```
  ## Caps
  cap pages: 200
  cap model calls: 50
  cap total USD: 2.00 (2000000 micro-dollars)
  ## Expected cost inputs
  embed_bytes: <int>
  embed_price_micro_per_munit: <int>
  embed_requests: <int>
  answer_calls: <int>
  w_micro: <int>
  total_micro: <int>
  ```

  Each Caps line is followed by an `enforced by: <package> <test id>` line (BN-1).
- **E10 (A12, new), mechanical cap check:**
  - `awk '/^## Caps$/{f=1;next} /^## /{f=0} f' ak0-optin-run.md | grep -cE '^cap (pages: 200|model calls: 50|total USD: 2\.00 \(2000000 micro-dollars\))$'` prints `3`;
  - `awk '/^```/{f=!f;next} f' ak0-optin-run.md | grep -oE '(^|[^0-9.])(200|50|2000000)([^0-9.]|$)' | grep -oE '[0-9]+' | sort -u | wc -l` prints `3` (all three numbers appear in the fenced command or config blocks);
  - `grep -c '<secret-name>' ak0-optin-run.md` prints at least `1`.
- **E11 (A12, new), recompute:** the runner writes this script to the scratchpad and runs it with `python3 -I <scratch>/e11.py ak0-optin-run.md`. Expected output: `ok <total_micro>`.

  ```python
  import re, sys
  t = open(sys.argv[1], encoding="utf-8").read()
  def v(k):
      m = re.search(r"^" + k + r": (\d+)$", t, re.M)
      if not m: print("missing " + k); sys.exit(1)
      return int(m.group(1))
  b, p, er, ac, w, tot = (v(k) for k in ("embed_bytes", "embed_price_micro_per_munit", "embed_requests", "answer_calls", "w_micro", "total_micro"))
  emb = -(-b * p // 1000000)
  calc = emb + ac * w
  bad = []
  if calc != tot: bad.append("total_micro %d != recomputed %d" % (tot, calc))
  if calc > 2000000: bad.append("over cap: %d" % calc)
  if er + ac > 50: bad.append("calls %d > 50" % (er + ac))
  print("\n".join(bad) if bad else "ok %d" % calc)
  ```

  The line `er + ac > 50` applies under NEEDS LEAD 13(a). Under 13(b) it reads `ac > 50`. Run on made-up samples by me (F10): the clean file passed, and the wrong total, 55 calls and the over-cap total were each printed.
- **Planted faults for A12 (added):**
  - a command block with `--calls 60` (E10 count 2);
  - `total_micro` one less than the recompute (E11);
  - `embed_requests` 10 + `answer_calls` 45 (E11, `calls 55 > 50`);
  - a total above 2,000,000 written as `READY` (E11, `over cap`).
- **Money review at completion:** before the lead takes the figure to the owner, ONE fresh reviewer (an `egm:*` reviewer, Sonnet per `MODEL-ROUTING.md`) reads the completed file, `sources.md` and the merged code the Caps block names. It reports in `reviews/AK0-optin-run-review-<n>.md`. This is the money path, so there is no round cap (orders 6(b) and 8(1)). Rounds repeat until one finds no Blocker or Major. The AK0 freeze does not cover the completed file.
- **Done (line 151)** adds: "`ak0-optin-run.md` is written `NOT READY` with each missing item named; its completion is a step of AK2b's Done, not AK0's".

**BN-4. The expected-cost formula (R3-ADV-4, R3-COR-3; NEEDS LEAD 13).**
- **Place:** run-file item 4 (line 114); PL11's figure sentence (line 191); UNVERIFIED (new U14).
- **Item 4 is replaced by:**
  > 4. **Expected cost** (integer micro-dollars; computed only by the completer, BN-3):
  >    - **Embedding part:** `ceil(embed_bytes x embed_price_micro_per_munit / 1,000,000)`.
  >      - `embed_bytes` = the UTF-8 bytes of the made-up pages the run will read (at most 200) PLUS the bytes of every question the run will embed. It is measured with `wc -c` on the fixture files and the question file.
  >      - `embed_price_micro_per_munit` = the dated price, in USD per million billing units (tokens or characters, as the price line says), x 1,000,000. It is taken from the D4 row that the run's embedder config selects. The row is named by cloud family and product family, never by model id. If the config selects an embedder with no D4 row, the file is `NOT READY`.
  >      - Bytes are used as the upper bound on tokens, as in P4a's worst case (`tickets/P4a.md:84`). A UTF-8 character is at least one byte, so the bound also holds for billing per character (U14).
  >    - **Model part:** `answer_calls x w_micro`.
  >      - `w_micro` = P4a's W for the configured route (the byte bound of the largest prompt times the input price, plus `max_tokens` times the output price, per million tokens), rounded up to whole micro-dollars.
  >      - The prices come from that day's dated price page of the configured route's model family. The quote is written with `<model-id>` plus the family name (Interface item 9).
  >    - **Calls:** `embed_requests` = ceil(chunks / the batch size in AK2b's config). Under NEEDS LEAD 13(a), `embed_requests + answer_calls` <= 50.
  >    - **Total** = embedding part + model part. If it is above 2,000,000 micro-dollars, the status is `NOT RUNNABLE` (BN-5).
  >    - **No safety factor:** both parts are upper bounds. "500 tokens per page" is the reference-workload assumption and is not used for the run. E11 recomputes the total.
- **PL11's sentence** "100,000 tokens x the D4 default's dated unit price, plus 50 calls x the most one call can cost" reads "the item 4 formula (bytes of pages and questions / 1,000,000 x the selected D4 row's price per million units, plus answer calls x W)".
- **New U14:** "That bytes bound an embedder's billed tokens is P4a's rule for model prompts. For embedders it is UNVERIFIED for tokens, and it holds for characters. AK2b's price record (kit-plan row AK2b) states the billing unit."

**BN-5. `NOT RUNNABLE` may only shrink the run (R3-ADV-11).**
- **Place:** run-file item 4's last sentence and item 5 (line 115).
- **Item 5 gains:** "If the file is `NOT RUNNABLE`, the lead may LOWER the pages cap, the calls cap or both, never raise either, and never raise USD 2.00. The completer then recomputes with the lower figures, E10 and E11 run again, and the money review (BN-3) reads the new file. The cap values in the Caps block and in the command block change together, and E10's expected numbers change with them."

**BN-6. Names are hidden only where a pattern sees one (R3-ADV-5, R3-COR-10, own N3; NEEDS LEAD 5 updated, NEEDS LEAD 14).**
- **Place:** D7 row (line 42); D8 facts (line 51) and D8(d) (line 52); "Owner-visible limit under (d)" (line 57); PL5 owner text (lines 175-182); Files list (line 88); Acceptance (new A7c); U8.
- **D7 row, Evidence cell** reads: "Which kinds the core finds and which it misses on document text: P5c's 'does NOT promise' list (`tickets/P5c.md:399`; its first item is names in free prose with no title or `Dear`) and `guard/redact.py:424-426` (the code's own limit note); licence of (b)". The note cites both with quoted tokens. D7(b)'s trigger reads "before the first pilot with real client documents, or a client's documents carry kinds the core does not find" (NEEDS LEAD 14).
- **D8 facts (line 51) gains:** "The core redactor finds a person's name only after a name field's key, a title or `Dear` (`guard/redact.py:427-447`). A name written plainly in a sentence is not masked (`:424-426`; P5c:399). So under every option, a bare name in a chunk or a question reaches the embedder and the answer model as written."
- **D8(d)'s sentence "The managed embedder gets each chunk masked with a throw-away per-call map"** gains: "(masked where a pattern fires; a bare name is sent as written, see the limit below)".
- **Line 57 gains a second limit:** "A person's name written plainly in a document or a question, with no title, greeting or name label, is not hidden from the embedder or the answer model."
- **PL5 owner text, replacements:**
  - Bullet 2 ("names and other personal details are replaced with labels for that one call") reads: "personal details that the masking can recognise are replaced with labels for that one call: for example e-mail addresses, and names that follow 'Mr', 'Dr', 'Dear' or a 'Name:' label. **A name written plainly in a sentence is NOT recognised and is sent as written.** The labels are thrown away after the call."
  - The "Limit you should know" paragraph gains a first sentence: "**Names are hidden only where the masking can see one.** A name written plainly in a document, such as 'Asha signed the contract', is sent to the embedder and to the answer model as written. Today no part of our code finds such names; a separate name-finding tool is a later option (decision below)."
  - Bullet 5 ("Only names and ids are put back") reads "Only the names and ids that were hidden are put back, ...".
  - The sentence "Recommendation: (d)" gains: "This limit is the same under every option; it is not caused by (d)."
- **Files list, line 88:** "append two numbered entries" reads "append three entries, numbered with the next free numbers when appended (entry 1 exists; other packages may append first)". The third entry draft, for the lead to append in the file's own format:

  > ## N. A person's name written plainly in a document or a question is not hidden
  > - **What can go wrong.** When the kit answers questions from a client's documents, it hides personal details before text goes to the outside service that turns text into search numbers, and before it goes to the answer model. It finds a name only next to a title ("Mr", "Dr"), a greeting ("Dear") or a label such as "Name:". A name written plainly in a sentence, for example "Asha signed the contract", is sent to those services as written.
  > - **What the program checks.** It hides the names and the other personal details it can recognise. If the hiding step itself fails, nothing is sent.
  > - **What it does not check.** It cannot tell a plainly written name from an ordinary word.
  > - **What a person must do, and when.** Before the first pilot with real client documents, the owner decides whether a name-finding tool is added (studio item AK0-PL14). Until then, only made-up documents are used.
  > - Studio reference: package AK0, D7 and D8, AK0-PL5 and AK0-PL14; `guard/redact.py` limit note; P5c "does NOT promise" (a).

- **New A7c (manual, reviewer):** "The Masking section, the owner text in 'Asked of the owner' and the owner-visible entry say that names are hidden only where a pattern fires. None of them says names are hidden without that qualifier." Planted fault: the PL5 owner text with its bullet 2 reverted to "names ... are replaced with labels".
- **Relay to AK2b's ticket (coupling C-1):**
  - (i) the done condition's seeded personal-data string is of a kind the redactor finds (for example a made-up e-mail address or `Dr <made-up name>`);
  - (ii) a companion test `test_bare_name_reaches_embed_payload` seeds a made-up bare name with no marker and asserts that it IS in the fake embedder's payload, so the limit is pinned and the test fails the day a name finder lands. Its message names the owner-visible entry;
  - (iii) AK2a's made-up documents give the first measured share of bare names (names per document, how many have a marker), which goes into the limit entry when known.
- **U8 gains:** "and the bare-name limit (F4) is read from code and P5c, not measured".

**BN-7. An unreadable page has a way back (R3-ADV-6, R3-ADV-7; INFORM 17).**
- **Place:** "Source of the code" (line 68); Interface item 3 (line 73); R1 (line 148); run-file status (BN-1 (iii)).
- **Line 68's `unreadable` sentence gains:** "The lead may paste the dated line into `sources.md` (PL6's route). The pasted entry reads `lead paste <YYYY-MM-DD>; <URL>; "<quoted line>"` and counts as the primary source for that row. Runner step R1 checks the row against the paste (BN-9) and records `source: lead paste`. Once the paste is in and R1 records a hit, the row's cells are filled from the paste and its verdict may be `default` again. Until then the row is `outline`, E6 prints for that part, the PL1 table stops for that part (coupling C7), and the run file stays `NOT READY` with the reason `D4 price unreadable` when the row is D4."
- **Interface item 3:** an unreadable Licence cell is written `unreadable <YYYY-MM-DD>; <URL>`. So E1 finds its `;`, and E3 prints it if the row were ever marked `default` (`unreadable` is not on the allowlist). An unreadable cell in any other column stays `unreadable <YYYY-MM-DD>`.

**BN-8. D1(d) bypasses the mask (R3-COR-1).**
- **Place:** J2 (line 26), D1 row (line 36), A5 (line 126).
- **J2's list** reads "This applies to D1(c), D1(d), D2(c) and D2(d)".
- **D1 row, option (d)** reads "(d) rung 5 (managed building block): per-cloud document services (takes the raw PDF bytes; Risk `bypasses mask`; alternative only; a sub-processor if outside the client's account)".
- **A5 gains a manual part:** "the D1(d) and D2(d) Risk cells contain `bypasses mask`". Planted fault: D1(d) with an empty Risk cell, or with `bypasses mask` left out.

**BN-9. R1 becomes a fixed-string check (R3-ADV-10).**
- **Place:** runner step R1 (line 148), A-table (new planted fault under A9).
- **R1 reads:** "For every `default` row, the runner saves the page text of its `sources.md` URL in the scratchpad. For a lead paste, it uses the paste itself. It then runs `grep -cF -- '<stored quoted line>' <saved page text>` and records in `acceptance.txt` the URL, the UTC date and the count. It judges nothing. A count of 0 stops the PL1 table, and the lead decides." The quoted lines are short (Interface item 9 replaces any model id with `<model-id>`). The runner therefore matches only the part after the last `<model-id>`, and records which part it matched.
- **Planted fault (new, under A9):** a scratchpad copy of `sources.md` with one digit changed in a stored price quote gives count 0.

**BN-10. E7b also reads URLs (R3-ADV-9).**
- **Place:** E7b (line 145), A10 (line 132), Interface item 8's last line (line 80).
- **E7b gains a second pass:** `grep -noE 'https?://[^ )|]+' <file> | grep -E '(<prefix list>)[A-Za-z0-9]{8,}'` on the same three files. Expected: prints nothing. It uses the key-prefix list only (not the 32-character rule), because long hashes in public URLs would give false hits.
- **The source notes rule (line 80) gains:** "URLs are written without a query part (nothing after `?`)."
- **A10 gains a planted fault:** a key-like string, built from parts at run time, inside the path of a URL in the scratchpad copy of `sources.md`.

**BN-11. Frozen, except D8 (R3-ADV-8; INFORM 15).**
- **Place:** Files list, `freeze-list.md` line (line 89); Path class (line 65); Done (line 151).
- The freeze-list status reads: `AK0 | revision 3 + round 3 build notes | frozen, except D8 (open until a numbered order records the owner's PL5 answer)`. Done's "AK0 set frozen" reads the same.

**BN-12. Extended review: no, with its basis (R3-COR-4; INFORM 16).**
- **Place:** Path class (line 65).
- It gains: "This departs from orders 6(b) and 8(1) (money and redaction have no round cap). The basis is order 23 ('rounds capped at 3 then freeze', newer, written for kit tickets) and order 20 item 6 (a fourth round only with at most 2 Majors). The two open paths keep an uncapped review elsewhere: D8 in AK2b's Tier A review, and the completed run file in the money review of BN-3."

**BN-13. The PL1 cell for a free-software default (R3-COR-5).**
- **Place:** Reference workload (line 32), Interface item 7 (line 77).
- A free-software `default` row's PL1 cell reads `USD 0.00 (licence cost 0 x 10,000 pages); hosting not costed: AK-G16`. That is a USD figure with its formula, so the "never `not costed` on a PL1 default row" rule holds. In the Options table, the row keeps `licence cost 0; hosting not costed`.

**BN-14. Option (b) also needs 8 answers (R3-COR-6).**
- **Place:** Interface item 5 (line 75), E8 (line 146), A7a (line 128).
- "if option (a) is chosen" reads "if option (a) or (b) is chosen". E8's note reads "(with option (a) or (b): `[1-8]` and `8`)". A7a reads "(8 under option (a) or (b))".

**BN-15. E6 checks D6; one D4 default per cloud (R3-COR-8).**
- **Place:** E6 (line 143), A4 (line 125), A9 (line 131).
- E6's list reads `split("D1 D2 D4 D5 D6", k, " ")`. A4 reads "D1, D2, D4, D5 and D6". D6's `none` row is the default, and D6(b) is the outline.
- **A9 gains a manual line:** "the PL1 table has one D4 row per cloud family named in the note's D4 Decisions prose, and each has a matching `default` Options row". Planted fault: a note naming three clouds with two D4 default rows.

**BN-16. Order times (R3-COR-7, R3-ADV-13).**
- **Place:** revision line (line 3).
- The sentence "the '~04:30Z' written inside order 27 is wrong" reads: "the '~' times written in the headers of orders 26 to 30 differ from their git commit times (order 26 03:40:43, 27 03:42:46, 28 04:02:07, 29 04:04:25, 30 04:14:25 UTC), and git commit times win for every order (order 20)".

**BN-17. Count delta (one place for the executor).**
- Acceptance rows: 13 become **14** (A7c new). Evidence commands: 10 become **12** (E10, E11 new), plus R1.
- New planted faults:
  - A5: D1(d) Risk;
  - A9: R1 digit change and D4 per cloud;
  - A10: key in a URL path;
  - A12: `owner yes: none` run, `--calls 60`, total off by one, 55 calls, over cap.
- PENDING LEAD: 11 become **17** (PL12 to PL17 new; PL5 and PL11 updated). NEEDS LEAD: 6 become **9** (PL5, PL7 to PL14). INFORM (as PL items): PL15 to PL17.
- UNVERIFIED: 12 become **14** (U13, U14). Owner-visible entries to append: 2 become **3**. Money items: PL3, PL11, PL12, PL13.

## Positions
- **BN-1 makes the status rule stricter instead of adding a meter feature.** A page cap and a call cap are job limits, not money accounting. Putting them in P4b1's frozen meter would reopen a money ticket. AK2b's job, which reads the pages and sends the calls, is the narrowest place that sees both. The USD cap stays where it already is (P4b1's run cap). The cost: AK2b gains two limits, two tests and two mutants.
- **BN-2 applies orders 27 item 55 and 28, so it gets no PL item.** `READY` was the only word a reader could take as a go. Line 2 separates "ready to ask" from "owner said yes".
- **BN-3 puts the money check on code (E11), not on a reader.** E11 already caught my own hand arithmetic (Honest note). The money review is added because the frozen Tier B rounds never see the completed figure.
- **BN-4 removes a guess instead of adding a safety factor.** Bytes are a measured upper bound, so no factor has to be chosen. A factor would be a threshold the owner must set.
- **ADV-5 is fixed in the text the owner reads, and the design is not changed.** The bare-name limit is a core limit (P5c:399), not a D8 choice. Changing D8's option would not close it, and only a name finder would. That is an owner decision (PL14), because it adds a detector-model package to the redaction path.
- **R3-COR-9 is declined** (no surface added). A `\b` would miss real ids. The benign-hit route already exists.

## Couplings
- **C-1 (AK2b, no ticket yet).** BN-1 (page and call limits with tests and mutants, embedding reserve and settle under the run's one `run_id`), BN-3 (completing the run file is a step of AK2b's Done) and BN-6 (the seeded-string kind, `test_bare_name_reaches_embed_payload`) are requirements on AK2b's ticket. The orchestrating session copies them into AK2b's ticket brief. AK2b's ticket does not freeze without them.
- **C-2 (AK1 PENDING LEAD 2, `tickets/AK1.md:300`).** The caps for jobs that are not agent runs are open. The opt-in run's embedding batches are such a job. BN-1's "one run id with `Caps.run` = 2.00" is consistent with AK1's option (a), where each job is its own agent entry with its own caps. Under AK1's option (b) the run would share the answering agent's caps, and the run id still bounds the total. Whichever is answered, the run file's USD row names it.
- **C-3 (P4b1 live-call gate).** BN-1 (ii) relies on `tickets/P4b1.md:49`. If a P4b1 build note moves that gate, BN-1 (ii) follows it.
- **C-4 (P5c).** BN-6 cites P5c:399 and :309. If P5c's detector-model backend is built, `test_bare_name_reaches_embed_payload` fails, and the owner-visible entry and the PL5 text are updated (entry rule: add a new entry, do not edit).
- **C-5 (owner-visible-limits.md).** P5b4 (six drafts), P6a and P6b2 may append first. The lead numbers AK0's three entries when appending.
- **C-6 (questions-for-lead.md).** The orchestrating session writes AK0-PL12 to AK0-PL17 there, and replaces AK0-PL5's owner text with the BN-6 version. Item 57 there still holds revision 1's text.

## PENDING LEAD (continuing the ticket's numbering after 11)
Routing rule: money and redaction items, and anything that sets or reads an owner figure, are NEEDS LEAD. Everything else is INFORM, and the executor takes the recommendation meanwhile.
- **5 (updated, NEEDS LEAD, redaction).** The owner text is replaced as in BN-6: names are hidden only where the masking can see one. Recommend: the lead shows the owner the BN-6 text, not revision 3's. Reversible: the text can be reworded before the owner answers.
- **11 (updated, NEEDS LEAD, money).** Options:
  - (a) **recommended:** no estimate in the note. The orchestrating session completes the run file as a step of AK2b's Done, with BN-4's formula, E10, E11 and a money review with no round cap (BN-3). The lead takes the checked figure to the owner;
  - (b) the note also carries an embedding-only figure now.

  I recommend (a): a half figure can be read as the whole cost, and (a) is the only option with a check on the figure.
- **12. NEW, NEEDS LEAD (money). Which caps must be enforced by code before the run file may be `READY`.** Options:
  - (a) **recommended:** all three. USD 2.00 by P4b1's run cap under one run id (embedding and model calls). Pages 200 and calls 50 by AK2b's job limits, each with a test and a mutant (BN-1);
  - (b) USD 2.00 only. The file says on line 3 that pages and calls are not enforced by code, and the lead tells the owner.

  Reason for (a): order 28 says the ceiling is "enforced by the meter"; under (b), two of its three numbers would be promises. Cost of (a): two small limits in AK2b. Confidence 85 percent.
- **13. NEW, NEEDS LEAD (money; the owner's reading of his own figure). Do embedding requests count against the 50 model calls?** Options:
  - (a) **recommended, and the interim default:** yes, every paid request counts, so `embed_requests + answer_calls <= 50`. AK2b then batches the chunks (for example, 200 chunks in batches of 20 = 10 requests, leaving 40 answer calls; the numbers are made up);
  - (b) no: 50 answer-model calls, with the embedding requests bounded by the 200-page cap and the USD cap.

  (a) is the stricter reading and can never exceed what the owner approved. With one request per 500-token chunk and no batching, 200 pages alone would make 200 requests (F5).
- **14. NEW, NEEDS LEAD (redaction). A person's name written plainly is not hidden (BN-6).** Options:
  - (a) **recommended:** accept for kit v1, with made-up documents only. The limit is stated to the owner (PL5 text, owner-visible entry). P5c's detector-model backend, or D7(b), gets the trigger "before the first pilot with real client documents", so it cannot be skipped silently;
  - (b) add a name-finding package (a self-hosted named-entity model behind P5c's protocol) to kit v1 now, before AK2b.

  Reason for (a): no real client document enters the kit before a pilot, and (b) is a new redaction package with its own uncapped review. Cost of (a): the first pilot waits for that package or for the owner's written acceptance of the limit. Confidence 75 percent.
- **15. NEW, INFORM. Freeze with build notes, no round 4, except D8 (BN-11).** Round 3 had 9 Majors (7 distinct). Recommend: yes, per orders 23 and 20 item 6. The banner goes under the revision line.
- **16. NEW, INFORM. "Extended review: no" stated with its basis (BN-12).** Recommend: accept. D8 and the completed run file keep uncapped reviews elsewhere.
- **17. NEW, INFORM. A lead-pasted dated line counts as the primary source (BN-7).** Recommend: accept. The lead pastes from the vendor's or project's own page, R1 checks the paste mechanically, and the row may then be `default`. Reversible.

## Counts
- **Finding ids:** 24 (ADV 14, COR 10).
  - Majors: 9 (ADV-1 to ADV-6, COR-1 to COR-3). ADV-1 and COR-2 are one defect, and ADV-4 and COR-3 are one, so 7 distinct.
  - Minors: 11. Nits: 4. No Blocker. No severity changed.
- **PROPOSE FIX:** 22 ids.
  - ADV-1 to ADV-13;
  - COR-1 to COR-8 and COR-10.
  - ADV-5 also carries a PARTIAL CONTEST of its "state the share" part: AK0 is desk-only, and the share is measured on AK2a's made-up documents.
- **CONTEST (whole finding):** 0. **DECLINE:** 2 (COR-9, ADV-14). **ESCALATE:** 0.
- **Own findings:** 3 (N1 and N2 in BN-1, N3 in BN-6).
- **Build notes:** 17 (BN-1 to BN-17; BN-17 is the count delta).
- **PENDING LEAD:** 2 updated (5, 11: NEEDS LEAD) and 6 new (12, 13, 14 NEEDS LEAD; 15, 16, 17 INFORM).
- **Owner-visible entries drafted:** 1 new (BN-6), 3 to append in all.
- **Fixes applied to the ticket in this step:** 0 (they are build notes). Remaining unaddressed findings: 0.
