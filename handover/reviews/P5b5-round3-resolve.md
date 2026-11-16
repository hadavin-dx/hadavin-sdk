# P5b5 round 3 resolve (egm:egm-resolve, AUTO mode; LAST round)

**Status:** resolved (AUTO: no interactive gate, per the lead's order 20 item 6 instruction). The ticket is NOT edited. The fixes are build notes BN-1 to BN-14 below, which the builder applies. They win over the ticket text.
**Target:** `handover/tickets/P5b5.md` revision 3, full file (314 lines, commit `1638424`; the file is unchanged at the current branch head).
**Findings:** `reviews/P5b5-round3-adversarial.md` (R3-ADV-1..13: 0 Blocker, 3 Major, 7 Minor, 3 Nit) and `reviews/P5b5-round3-correctness.md` (R3-COR-1..10: 0 Blocker, 2 Major, 6 Minor, 2 Nit). 23 ids.
**Gate:** order 20 item 6 caps the review at 3 rounds, counting from round 1. A redaction ticket gets a round 4 only if its last round had no Blocker and at most 2 Majors. Round 3 has 5 Majors in total (3 ADV and 2 COR; R3-ADV-2 and R3-COR-2 are one defect, so 4 distinct Major defects). Each reviewer's own "≤2 Majors" reading is per report, and the gate counts the round. So there is **NO round 4**. The ticket freezes at revision 3 with this file's build notes attached. The banner below goes under the ticket's status line. The build-start review (order 19 A, order 20 item 3) reads the ticket plus this file.

## Honest note (read first)
- **Not checked by me:**
  - nothing was run: no test, no checker, no `ast` walk, no T4 socket run. `python3 -I` was used only for the totals;
  - whether `capfd` sees the server thread's `sys.stderr.write` (reasoned, see F-c);
  - whether P5b3's unbuilt taint guard kills M25;
  - the real failure-line text of that guard (so M25's `expect` is filled at build start);
  - where the merged P5a defines `OLD_WRITER_LEAKS` (P5a.md:121 says "a frozen tuple"; it does not name the file);
  - whether the merged P5a imports `traceback`: I read only P5a's text, which walks `exc.__traceback__` itself (BN-6 depends on this);
  - whether the merged P5b4 sends fd 2 to the null device (BN-8 depends on this);
  - the P1m runner's merged interface: I read its draft branch head `657b20b` only, and PR 61 is not merged;
  - P4a and P5c edits to `k1b/loop.py`.
- **Read in full:**
  - LEAD-ORDERS orders 1-27, `studio-notes/amendments.md` (A1-A14) and `TICKET-TEMPLATE.md`;
  - the ticket, both round 3 reports and the round 2 resolve;
  - `approvals/receiver.py` at `cd2243f`.
- **Read only the cited lines:**
  - P5a (`:7`, `:40`, `:43`, `:47`, `:72`, `:75`, `:81`, `:121-123`, `:147-148`, `:166`, `:240`);
  - P5b3 (`:225-228`, `:282`, `:340`, `:491`);
  - P5b4 (`:43`, `:89`, `:151`, `:174`, `:275`, `:440`);
  - plan-v3 (`:61`, `:86-109`);
  - `k1b/loop.py:160-196`, `tests/test_p7_tick.py:275-300`, `approvals/requests.py:71-79` and the P1m `Mutant` fields.
- I CONTEST nothing. Five fixes are smaller than the reviewer asked, or are cuts instead of new design: BN-6, BN-8, BN-11, BN-13 and the T5 BASE-row part of BN-7. One fix adds surface instead (BN-10, a trigger pin for the dev-server limit), and I say why under Positions. The lead can drop it (PL 17).
- I replaced the skill's default output (`goldfish_review_report.md`, one block per finding) with the file name and layout the caller ordered.
- I did not edit the ticket, commit, push, or write DECISIONS.md.

## Facts checked by me (code at `cd2243f` via `git show` / `git grep`, unless named)
- **F-a (R3-ADV-1, R3-COR-4).** Ticket `:59` defines `<import>` as the key for "an import statement". Rule 3 (`:62`), T2 (`:96`) and N6-N8 and N18 (`:110-112`, `:122`) key `import traceback` and `from traceback import` as `<module>`. Rule 4 and N10 key `from logging import basicConfig` as `<import>` (`:63`, `:114`). The definition contradicts rule 3. The reviewers are right.
- **F-b (R3-ADV-2, R3-COR-2).** P5a puts `Code` and `FactKey` in the new module `codes.py` (`P5a.md:40`, `:43`, `:47`), which is absent at `cd2243f`. The ticket has no collection rule. P5b3 has one (`P5b3.md:340`: "a fail-before file imports at module level only names that exist on the base; ... Collection must succeed on the base before any result is claimed"). The fail-before command copies only the new test file into the old worktrees (ticket `:176`). The reviewers are right.
- **F-c (R3-ADV-3).** `receiver.py:47-48`: `if self.path != PATH: status, out = 404, b""`, so any path suffix answers 404 and `handle_slack_action` is never called. The exact path calls `approvals.receive`, which calls `channel.parse_decision` (`approvals/requests.py:76`). Whether that raises on junk depends on the channel: UNVERIFIED, so it is avoided. The repo already uses the 404 shape: `tests/test_p7_tick.py:295-298` posts `data=b""` to `/other` and asserts `HTTPError` code 404. `send_response` calls `log_request` before the headers are flushed, so the stderr line is written before the client gets its answer (reasoned from the stdlib, as R3-COR said; not run). An empty body is chosen on purpose: a body the server never reads, followed by a socket close, can reset the connection on Linux (reasoned, not run).
- **F-d (R3-COR-1).** `P5a.md:166`: the plan row is `pytest tests/test_diagnostics_hostile.py tests/test_diagnostics_old_writers.py`, and P8b's check includes "`OLD_WRITER_LEAKS` empty". `P5b3.md:282` and `:491`: P5b3 turns every strict-xfail row into a plain assert, and `OLD_WRITER_LEAKS == ()`. The ticket's re-run (`:125`), evidence command (`:178`) and Done (`:187`) never name that file. The reviewer is right.
- **F-e (R3-ADV-5, R3-COR-5(a)).** P5a's `diagnose` walks `exc.__traceback__` link by link (`P5a.md:72`, `:75`), and `grep -c "import traceback" P5a.md` is 0. On `cd2243f` the only importer is `cli.py:32`, which P5b3 deletes (`P5b3.md:176`). So the one-entry `TRACEBACK_IMPORTERS` allowance protects nothing that is known to exist. Deleting it also deletes the dead `traceback_import_missing` branch.
- **F-f (R3-ADV-4, R3-COR-3).** The only `RequestHandler` names in `src/` are `receiver.py:12` (an import) and `:43` (`class Handler(BaseHTTPRequestHandler)`). Nothing under `socketserver` is subclassed today.
- **F-g (R3-ADV-6).** P5a's `test_every_ledger_id_is_covered` already asserts "exactly one BASE row" per ledger id (`P5a.md:148`, `:240`). It runs in the same file as T5, so T5's BASE-row clause is a duplicate.
- **F-h (R3-ADV-7, R3-COR-6).** The P1m draft head `657b20b`, `tools/mutation_runner.py:28-46`: a `Mutant` is a text swap `old` → `new` in `file`, with `expect` (at least 4 characters), `test_file` (run only that file), `only_test` and `pinned`. A missing snippet gives the verdict `ERROR "SNIPPET NOT FOUND"` (`:255-258`). So the runner can pin each mutant's killer with no new feature. `k1b/loop.py:176-177` is `except ProviderError:` followed by `out.status, out.stop_reason, out.halt = "error", "aborted", "aborted"`, a real insertion point. P5b3's SAFE list (`P5b3.md:227`) does not hold `safe_head` or `redact_text`, so `redact_text(str(exc))` is also a sink under "any call not on the SAFE list" (`:225`).
- **F-i (R3-ADV-8).** At `cd2243f`, no module under `src/hadavin_sdk` imports `approvals.receiver` (`git grep receiver` finds only docstrings and comments outside the file). The only importer of `serve` is `tests/test_p7_tick.py:18`. P5b4's trigger for V-OG-4 is "`serve()` gets a caller in `src/` or in a demo shown to a client" (ticket `:53`).
- **F-j (R3-ADV-11).** P5b4 deletes `basicConfig` (`P5b4.md:174`) but pins nothing by name. Its run-time restore (`:89`, `:275`) only re-adds its handler at audit points after a `force=True` call. So rule 4 is the only pin against a plain re-add.
- **F-k (R3-ADV-12, R3-COR-9).** In `plan-v3.md:109` the "R" column is the step lane ("Redesign step R5"), not a path class, and P5b5 is Tier A. Plan rule 3 (`plan-v3.md:61`) lists redaction under Tier A. No plan line calls P5b5 a security package. The ticket's "redaction" label is consistent with the plan. "Security path" is the reviewers' brief wording, not ticket text.

## Decisions
| id(s) | category | decision (BN-n) |
|---|---|---|
| R3-ADV-1 (Major), R3-COR-4 | PROPOSE FIX | BN-1: one key table per rule; rule 3 is file-level (`<module>`); `<import>` only for rules 1(b), 4, 5(a); plant N20, mutant M31 |
| R3-ADV-2 (Major), R3-COR-2 (Major) | PROPOSE FIX | BN-2: collection rule; module-level imports are standard library and `pytest` only; FAILED-not-ERROR check in the fail-before evidence |
| R3-ADV-3 (Major) | PROPOSE FIX | BN-3: T4 rewritten as one exact request (`POST PATH + "/p5b5-made-up"`, empty body, 404 asserted, stub `Approvals` that raises if called) |
| R3-COR-1 (Major) | PROPOSE FIX | BN-4: `tests/test_diagnostics_old_writers.py` in the re-run, evidence and Done; T5 also pins `OLD_WRITER_LEAKS == ()` and no `xfail`; STOP owner P5b3; mutants M36, M37 |
| R3-ADV-4, R3-COR-3 | PROPOSE FIX (smaller: no in-file subclass walk) | BN-5: closed set of three stdlib base names; indirect subclasses are a V2 limit; negative plant N21; mutant M32 |
| R3-ADV-5 | PROPOSE FIX (cut) | BN-6: `TRACEBACK_IMPORTERS` deleted; any `traceback` importer in `src/` is a finding and a STOP |
| R3-ADV-6 | PROPOSE FIX (partly by cut) | BN-7: mutant M38 (FactKey row); `.log` half by M39 (BN-8); T5's BASE-row clause cut (F-g); T4 on 3.12 gets no mutant (an interpreter is not a behaviour; the 3.12 run is reported) |
| R3-ADV-7, R3-COR-6 | PROPOSE FIX | BN-9: M25 as an exact `old`/`new` swap at `k1b/loop.py:176-177`, with `test_file`, `pinned` and `expect`; every mutant row gets a "Run with" column; F2b sentence on other cleaners |
| R3-ADV-8 | PROPOSE FIX (a trigger pin, not T4b) | BN-10: rule 5 `dev_server_caller`, real-tree row T8, plant N23, mutants M34, M35; PL 13 recommendation becomes (a) plus this pin (PL 17) |
| R3-ADV-9 | PROPOSE FIX (partly by moving plants) | BN-11: N1 and N14 move into the plant file; N5 and N19 keep the `k1b/loop.py` anchor, and a missing anchor is a STOP (C6) |
| R3-ADV-10, R3-COR-7 | PROPOSE FIX (cut to page text) | BN-8: T7 reads only `docs/diagnostics.md`: no backticked `logging.` key and no backticked `.log` path; step 0 STOPs if the merged P5b4 writes a file; mutant M39 |
| R3-ADV-11 (Nit) | DECLINE | rule 4 is the only pin against a plain `basicConfig` re-add (F-j); T7 is narrowed by BN-8, not kept as is |
| R3-ADV-12 (Nit), R3-COR-9 (Nit) | DECLINE | the label "redaction" matches `plan-v3.md:61`, `:109` (F-k); no ticket change |
| R3-ADV-13 (Nit) | PROPOSE FIX (one clause, inside BN-12) | `return None` is stated as a finding |
| R3-COR-5 | PROPOSE FIX | (a) closed by BN-6 (branch deleted); (b) BN-13 deletes the `receiver.py::<module>::server_log_noop_missing` branch (T4 is the control); (c) BN-12 negative plant N22, mutant M33 |
| R3-COR-8 | PROPOSE FIX | BN-14: "expected: empty file, rc=1"; `<same pattern>` replaced by the literal |
| R3-COR-10 (Nit) | DECLINE | the reviewer reproduced the six keys; step 0 re-measures and saves the output |

## Build notes (the builder applies each; where a note and the ticket disagree, the note wins)

**BN-1. One key per rule (R3-ADV-1, R3-COR-4).** Replace the `<key>` sentence in Interface (ticket `:59`) with this:
"`<key>` is decided by the rule, never by the reader:

| Rule | Key |
|---|---|
| rule 1 (a) `safe_head_caller` | the **qualified name** of the innermost enclosing `def`. A `lambda` counts for its enclosing `def`. Module level or directly in a class body: `<module>`. |
| rule 1 (b) `safe_head_caller` | `<import>`, for any `from <module> import safe_head [as X]`, wherever the statement sits (module, `def` or class body). |
| rule 2 `server_log_noop`, `server_log_noop_missing` | the class's qualified name. |
| rule 2 `server_log_noop_assign` | as rule 1 (a). |
| rule 3 `traceback_import` | always `<module>`, wherever the import or call sits (the file is the unit). |
| rule 4 `basic_config` | as rule 1 (a) for the attribute; `<import>` for `from logging import basicConfig [as X]`, wherever it sits. |
| rule 5 `dev_server_caller` (BN-10) | `<import>` for the import form; as rule 1 (a) for the attribute form. |
| `parse_error` | `<module>`. |"

N6-N8, N18 and T2's fail-before literal already use `<module>` and stay as they are. Add plant **N20**: the plant file holds `def f():` with `import traceback` in its body. Expected: `_p5b5_plant.py::<module>::traceback_import`. Add mutant **M31**: "checker: rule 3 skips an import inside a `def`, or keys it by the `def`". It is killed by N20.

**BN-2. Collection rule (R3-ADV-2, R3-COR-2).** Add to Files (`:71`) and to the fail-before paragraph (`:124`):
- "`tests/test_diagnostics_legacy_gone.py` imports at module level only the standard library and `pytest`. Every `hadavin_sdk` name is imported inside the test body that uses it: `serve` inside T4 and T8's helpers; `Code` and `FactKey` inside T6, from the module the merged P5a defines them in (`codes.py` per `P5a.md:40`; step 0 records the path in `step0-p5a-paths.txt` with `git grep -n "class Code\|class FactKey" <P5B4_HEAD> -- src`).
- The checker only parses with `ast`; it never imports the tree it checks.
- At `cd2243f` the fail-before run must collect without error. It must show T1, T2 and T3 as FAILED on an assertion, and T4 and T8 as PASSED. T6 and T7 fail there too (T6 on the `ImportError` inside its body, T7 on the missing page). They are labelled 'not a fail-before at `cd2243f`; fail-before is the P5b4 head'.
- At `<P5B4_HEAD>`, T6 and T7 must FAIL on the assertion 'docs/diagnostics.md is missing'. Both check `page.exists()` first.
- Any ERROR (at collection, in setup, or an exception outside an assertion in T1-T3) is a failed evidence run, not a fail-before. Plant rows N1-N23 pass on both bases."
Add to the Evidence notes: the runner pastes the `-rA` summary lines that show each test's outcome for both bases.

**BN-3. T4 as one exact request (R3-ADV-3).** Replace T4's Asserts cell (`:98`) with this:
"`serve(stub, port=0)`, where `stub` is a local class whose `receive` raises `AssertionError("receiver must not be called")`. `serve_forever` runs in a daemon thread. The test sends ONE `urllib.request.Request(url + PATH + "/p5b5-made-up", data=b"", method="POST")` with an empty body, which takes the `self.path != PATH` branch (`receiver.py:47-48`). Asserts, in order:
1. `urllib.error.HTTPError` is raised with `code == 404`. A dropped connection, a timeout or any other status fails the test, so an exception the handler swallowed cannot pass.
2. After `server.shutdown()` and `server.server_close()`, `capfd.readouterr().err` contains neither `127.0.0.1` nor `p5b5-made-up`.

The shape copies `tests/test_p7_tick.py:295-298`."
The Fail-before cell stays: it passes on `cd2243f` and fails under M6. Add to the Security note (1): "if a mistake routed the request into `handle_slack_action`, the stub would raise. `handle_error` would then print to stderr and the 404 check would fail. So T4 cannot pass by accident."

**BN-4. Old-writer rows close at R5 (R3-COR-1).** Apply all five edits:
1. **Hostile re-run (`:125`):** add `tests/test_diagnostics_old_writers.py` (P5a's file, flipped by P5b3, `P5b3.md:282`).
2. **Evidence command at the P5b5 head (`:178`):** add `tests/test_diagnostics_old_writers.py` after `tests/test_diagnostics_hostile.py`. Add step 0: `git grep -n -E "OLD_WRITER_LEAKS|xfail" <P5B4_HEAD> -- tests > step0-old-writers.txt`. It records the file that defines `OLD_WRITER_LEAKS` and any mark that is left.
3. **T5 (`:99`)** asserts, in addition, by `ast` (no import of another test file): the file that `step0-old-writers.txt` names holds exactly one assignment to `OLD_WRITER_LEAKS`, and `ast.literal_eval` of its value `== ()`; and `tests/test_diagnostics_old_writers.py` has no attribute load named `xfail`. Cut from T5 "every id of `LEDGER_IDS` still has its one BASE row": P5a's `test_every_ledger_id_is_covered` already asserts it (`P5a.md:148`) and runs in the same file (see BN-7).
4. **STOP rule (`:85`):** add "a non-empty `OLD_WRITER_LEAKS` or a `xfail` mark left in `tests/test_diagnostics_old_writers.py` (owner P5b3)".
5. **Done (`:187`):** "`pytest tests/test_diagnostics_hostile.py tests/test_diagnostics_old_writers.py` passes at the P5b5 head with `CORPUS_STEP == "R5"`, no `later` row, `OLD_WRITER_LEAKS == ()`, no xfail mark, and all 51 ledger ids accounted for (`P5a.md:166`, the check P8b relies on)".

New mutants: **M36** "`OLD_WRITER_LEAKS` holds one made-up row id", killed by T5. **M37** "one `pytest.mark.xfail(strict=True)` mark put back on a row of `tests/test_diagnostics_old_writers.py`", killed by T5 (P5a's `test_old_writer_marks_follow_their_later_row` may also fail; `pinned` names T5).

**BN-5. Handler selector is a closed set (R3-ADV-4, R3-COR-3).** In rule 2 (`:61`), replace "whose base is a name or attribute ending in `RequestHandler`" with this: "whose base is a name, or an attribute whose last part is, one of `BaseHTTPRequestHandler`, `SimpleHTTPRequestHandler`, `CGIHTTPRequestHandler` (the `http.server` handlers that define `log_message`)". Add to V2 (`:195`): "a class whose base is another local class, or an alias bound at run time, is not selected. T4 is the run-time control for the one real server." Add negative plant **N21**: the plant file holds `class S(socketserver.StreamRequestHandler)` with a `handle` method and no `log_message`. Expected: nothing new and nothing lost. Add mutant **M32**: "checker: selector back to 'any base ending in `RequestHandler`'". It is killed by N21.

**BN-6. Cut `TRACEBACK_IMPORTERS` (R3-ADV-5, R3-COR-5(a); PENDING LEAD 16 changes, see PL 17).**
- Delete the `TRACEBACK_IMPORTERS` bullet in Interface (`:65`). Rule 3 becomes: "any `traceback` import or constant-string dynamic import in any file under `src/hadavin_sdk/` gives `<relpath>::<module>::traceback_import`. There is no allowed importer." Delete the finding `traceback_import_missing` from rule 3 and from T2 (`:96`).
- Delete the conditional reason clause in the CHANGELOG item (`:83`).
- STOP rule (`:85`): "any `traceback` importer at the P5b4 head is a leftover: owner P5b3 for `cli.py`, P5a for its own modules, else the lead assigns." Reason: P5a's `diagnose` walks `exc.__traceback__` itself (`P5a.md:72`, `:75`), so no known module needs the import, and an allowed module could call `traceback.print_exc()` unseen (R3-ADV-5).
- M3, M11 and M19-M20 stay as they are.
- New coupling C14.

**BN-7. Mutants for the unmutated halves (R3-ADV-6).** Add mutant **M38**: "delete one `FactKey` row from the page's `| Fact | Meaning |` table", killed by T6. The `.log` half of T7 is M39 (BN-8). The BASE-row half of T5 is cut (BN-4 item 3). T4 is run on 3.12 when that Python is installed; the mutation run is 3.13 only, and the evidence says so.

**BN-8. T7 reads only the page (R3-ADV-10, R3-COR-7).**
- Replace T7 (`:101`) with `test_operator_page_names_no_log_file_or_config_key`. It reads `docs/diagnostics.md` only: no `src/` file and no import. It asserts:
  1. the page exists;
  2. no backticked token starts with `logging.`;
  3. no backticked token ends with `.log`.
- This matches the merged P5b4 when its PENDING LEAD 2 stands: fd 2 goes to the null device, with no config field and no file (`P5b4.md:440`, steps at `:151`).
- Step 0: if `step0-fd2.txt` shows the merged P5b4 writing a file or reading a config key for fd 2, the builder STOPS and reports to the lead. Page item 6(a) and T7 then need a ticket change, not a build note.
- Page item 6(a) (`:78`) keeps its first clause and drops "only if the merged code writes a file does the page name it, with the config key".
- M9 stays (`` `logging.capture_fd2` `` on the page). Add **M39**: "the page names `` `tick-stderr.log` ``", killed by T7.

**BN-9. M25 as an exact swap, and a "Run with" column (R3-ADV-7, R3-COR-6).**
- M25's edit (`:155`) becomes a P1m `Mutant`:
  - `file="src/hadavin_sdk/k1b/loop.py"`;
  - `old` = the two lines `except ProviderError:` and `out.status, out.stop_reason, out.halt = "error", "aborted", "aborted"`, as they stand at the head (`cd2243f` `:176-177`, re-read at step 0);
  - `new` = `except ProviderError as exc:`, then `out.raw = safe_head(str(exc), RAW_LIMIT)`, then the same status line;
  - `test_file="tests/test_taint_guard.py"`;
  - `pinned` = the guard's real-tree test id at the head;
  - `expect` = a fragment (at least 4 characters) of the guard's failure line that names `k1b/loop.py`. It is read from the built guard at build start and is never the test name (order 26 item 2).
- A `SNIPPET NOT FOUND` verdict means the mutant is rewritten to the current handler, never dropped.
- Every row of the mutation table gets a column "Run with" (`test_file`, `only_test`, `pinned`). `tests/diagnostic_r5_mutants.py` fills those fields for every mutant: checker mutants point at their plant row, source mutants at their T row, and M2 at T1 (`pinned`) with `tests/test_k5_producers.py` as a second listed run.
- Add to F2b (`:51`): "a different cleaner on exception text (for example `redact_text(str(exc))`) is not a `safe_head` use, so T1 does not see it. P5b3's guard does, because only the SAFE list (`P5b3.md:227`) is exempt from the sink rule 'any call not on the SAFE list' (`:225`)."

**BN-10. Trigger pin for the dev-server limit (R3-ADV-8).**
- Add rule 5 `dev_server_caller` to `LEGACY_RULES` (now five rules), in every file under `src/hadavin_sdk/` except `approvals/receiver.py`:
  - (a) any `from <m> import serve [as X]` where `<m>` resolves to `hadavin_sdk.approvals.receiver` (absolute or relative, resolved against the file's package): `<relpath>::<import>::dev_server_caller`;
  - (b) any attribute load `.serve` on a name that the same file bound by importing the module `hadavin_sdk.approvals.receiver` (`import ... [as Y]` or `from hadavin_sdk.approvals import receiver [as Y]`): `<relpath>::<key>::dev_server_caller`.
- Add real-tree row **T8** `test_dev_server_has_no_caller_in_the_package`: no `dev_server_caller` finding on the real tree. Fail-before: it passes on `cd2243f` (F-i). It is a regression pin, killed by M35.
- Add plant **N23**: the plant file holds `from hadavin_sdk.approvals.receiver import serve`, then `from hadavin_sdk.approvals import receiver`, then `def f(): receiver.serve(None)`. Expected: `_p5b5_plant.py::<import>::dev_server_caller` and `_p5b5_plant.py::f::dev_server_caller`.
- Add mutants **M34** "checker: rule `dev_server_caller` removed" (killed by N23) and **M35** "source: `cli.py` gains `from hadavin_sdk.approvals.receiver import serve`" (killed by T8).
- Page item 6(d) (`:78`) adds: "a test (T8) fails the day `serve()` gets a caller inside the package. A demo that calls it is not covered by that test."
- Coupling C9 adds: "the pull request that builds V-OG-4 changes T8 and rule 5 to match, with its reason."

**BN-11. Plants that no longer depend on moving code (R3-ADV-9).**
- **N1** becomes: the plant file holds `def g():` containing `def _p5b5_inner(): safe_head("x", 10)`. Expected: `_p5b5_plant.py::g._p5b5_inner::safe_head_caller`. M14 is still killed by N1, and M10 by N1 and N5.
- **N14** becomes: the plant file holds `def g(): return (lambda: safe_head("x", 10))()`. Expected: `_p5b5_plant.py::g::safe_head_caller`. M24 is still killed by N14, which is now a positive plant.
- Plant intro (`:102`): "N14 (negative) expects both parts empty" becomes "N21 and N22 (negative) expect both parts empty".
- N5 and N19 keep their anchor, `k1b/loop.py` with `run_case` holding both `safe_head` calls. The builder checks the anchor at the P5b4 head, and a missing anchor is a STOP under the rename rule (F2b, coupling C6).

**BN-12. Accepted no-op bodies, stated and planted (R3-COR-5(c), R3-ADV-13).**
- Rule 2 (`:61`) gets this sentence: "accepted bodies, after an optional docstring: exactly one bare `return`, or exactly one `pass`. `return None`, `...`, or any second statement is a finding."
- Add negative plant **N22**: the plant file holds two selected handler classes. One has `log_message` with a docstring then `return`; the other has `log_message` with `pass`. Expected: nothing new and nothing lost.
- Add mutant **M33**: "checker: only a bare `return` with no docstring is accepted". It is killed by N22.

**BN-13. Cut the receiver-file branch of rule 2 (R3-COR-5(b)).** Delete "and `approvals/receiver.py::<module>::server_log_noop_missing` if that file holds no such class" from rule 2 (`:61`) and from T3 (`:97`). If the handler is moved or renamed, or its base is aliased, T4 still exercises the real server, and T4 fails if `serve` leaves the module (an `ImportError` inside its body). No new row is needed.

**BN-14. Evidence command wording (R3-COR-8).** Line `:166`: replace `"<same pattern>"` with the literal `"_DRIVERS|def _message|safe_head|traceback|basicConfig|def log_message|safe_message|safe_str"`. Line `:173`: "expected: empty file and `rc=1` (grep found nothing). `rc=0` means a waiver file exists: STOP."

**Totals after BN-1 to BN-14** (by hand, checked with `python3 -I` as arithmetic only):

| Item | Revision 3 | After the build notes | What changed |
|---|---|---|---|
| Real-tree rows | 7 (T1-T7) | 8 (T1-T8) | T8 new; T4, T5 and T7 rewritten |
| Plants | 19 (N1-N19) | 23 (N1-N23) | N20-N23 new; N1 and N14 moved |
| Test rows in all | 26 | 31 | |
| Mutants | 30 (M1-M30) | 39 (M1-M39) | M31-M39 new; M25 made exact; none dropped |
| Checker rules | 4 | 5 | rule 5 `dev_server_caller` new |
| Finding names | | | `traceback_import_missing` and the receiver-file `server_log_noop_missing` case deleted |
| Constants | | | `TRACEBACK_IMPORTERS` deleted |

New killers:

| Mutant | Killed by |
|---|---|
| M31 | N20 |
| M32 | N21 |
| M33 | N22 |
| M34 | N23 |
| M35 | T8 |
| M36, M37 | T5 |
| M38 | T6 |
| M39 | T7 |

Every new row and plant kills at least one mutant.

## Banner (put directly under the ticket's status line, line 1)
> **BUILD NOTES WIN.** Review round 3 (`reviews/P5b5-round3-adversarial.md`, `reviews/P5b5-round3-correctness.md`) had 5 Majors, so there is no round 4 (order 20 item 6). This ticket is FROZEN at revision 3 (commit `1638424`). The builder applies build notes BN-1 to BN-14 in `reviews/P5b5-round3-resolve.md`. Where a build note and the text below disagree, the build note wins. The build-start review (order 19 A) reads this ticket together with those notes. Totals after the notes: 8 real-tree rows, 23 plants, 39 mutants, 5 checker rules, and no `TRACEBACK_IMPORTERS`.

## Positions (where my fix differs from the reviewer's)
- **R3-ADV-1: rule 3 stays `<module>`, and the definition changes instead.** `TRACEBACK_IMPORTERS` was a set of files, and BN-6 now bans the import in every file, so the file is the natural unit. Changing N6, N7, N18 and T2 to `<import>` (the reviewer's suggestion) would touch four rows to keep a key that carries no extra information.
- **R3-ADV-4: no in-file subclass walk.** The only real handler is local to `serve()`, so nothing outside the function can subclass it. A walk adds a rule branch, a plant and a mutant to cover a case T4 already covers at run time. The limit is written into V2.
- **R3-ADV-5: cut instead of a new `traceback_text` rule.** Deleting the one allowed entry closes the hole and the dead `_missing` branch (R3-COR-5(a)) with less surface. The cost: if the merged P5a does import `traceback`, P5b5 stops and P5a changes its import (C14). P5a's text shows it does not need to.
- **R3-ADV-8: a trigger pin (T8), not the strict-xfail T4b.** T4b would turn red only when the fix lands. T8 turns red when the risk becomes real (V-OG-4's own trigger, for its `src/` half), which is the control the "fix, do not defer" rule asks for. It is new surface (one rule, one row, one plant, two mutants). The lead can drop it and keep PL 13 (a) as an accepted, owner-visible limit (PL 17).
- **R3-ADV-10 and R3-COR-7: T7 cut to page text, not resolved by naming a config class.** No logging config model exists on `cd2243f`, and P5b4 PL 2 adds none. Naming how to find a model that should not exist is design for a case that becomes a STOP instead.
- **R3-COR-5(b): branch deleted, no plant.** A plant for "Handler moved out of `receiver.py`" cannot pass the two-difference rule on `cd2243f`. There the unplanted copy already has `serve.Handler::server_log_noop`, which the plant would remove. T4 is the stronger control.
- **R3-ADV-6, T4 on 3.12:** declined in part. A mutant edits behaviour, not the interpreter. The 3.12 run is reported, or written "not run" with the reason.

## Couplings (relay; other tickets NOT edited)
- C1-C13 stand as in revision 3, with two additions:
  - **C9** gains BN-10's sentence: the V-OG-4 pull request changes T8 and rule 5;
  - **C11** gains: M25 runs with `test_file="tests/test_taint_guard.py"`, and its `expect` comes from the built guard.
- **C14 (new, to P5a):** P5b5 now allows no `traceback` importer in `src/` (BN-6). P5a's `diagnose` should keep walking `exc.__traceback__` without `import traceback` (`P5a.md:72`, `:75`). A merged P5a that imports it makes P5b5 stop.
- **C15 (new, to P5a):** T5 reads `OLD_WRITER_LEAKS` by `ast` from the file step 0 finds. P5a should keep it as one module-level tuple literal (`P5a.md:121`), so `ast.literal_eval` can read it.
- **C16 (new, to P1m):** BN-9 relies on the `Mutant` fields `test_file`, `only_test`, `pinned` and `expect` of the draft head `657b20b` (PR 61, not merged). If the merged runner renames them, the builder maps them one to one. A missing feature is a STOP.

## PENDING LEAD (continues the ticket's numbering after PL 16)
17. **PL 13 and PL 16 change their recommendation (R3-ADV-5, R3-ADV-8).**
    - PL 16: the recommendation moves to its own alternative, "empty only": no `traceback` importer anywhere, by BN-6. Reason: no known module needs the import (F-e), and an allowed one could print unseen.
    - PL 13: the recommendation becomes (a) plus the trigger pin T8 (BN-10).
    - Alternative: drop BN-10 and keep PL 13 (a) alone, as an owner-visible limit in `handover/owner-visible-limits.md` (C12).
    - Recommend: BN-6 and BN-10 as written.
18. **Freeze with build notes, no round 4.** Recommend: yes, per order 20 item 6 (5 Majors in round 3). The banner goes under the status line, and the build-start review reads the ticket plus this file.
    - Alternative: one author revision 4 that folds the notes into the text, with no new review round. It costs about one author run and makes the ticket easier to read for the builder. It is not needed for correctness, because the notes are complete replacement text.
19. **Step-0 STOP added by BN-8 (fd 2 writes a file).** Recommend: yes. If P5b4 PL 2 is rejected, page item 6(a) and T7 need a ticket change that the lead orders. A builder rewriting a redaction claim on its own is the risk this avoids.

## Counts
- **Ids:** 23. By severity: 0 Blocker, 5 Major, 13 Minor, 5 Nit. ADV: 3 Major, 7 Minor, 3 Nit. COR: 2 Major, 6 Minor, 2 Nit.
- **Pairs:** 4 pairs count as one decision each (ADV-1 = COR-4, ADV-2 = COR-2, ADV-4 = COR-3, ADV-12 = COR-9). ADV-7 and COR-6 share BN-9, and ADV-10 and COR-7 share BN-8.
- **By decision:**

| Decision | Ids | Count |
|---|---|---|
| PROPOSE FIX | ADV-1..10, ADV-13; COR-1..8 | 19 |
| CONTEST | none | 0 |
| ESCALATE | none | 0 |
| DECLINE | ADV-11, ADV-12, COR-9, COR-10 | 4 |

- **Majors:** all 5 fixed by build notes (BN-1, BN-2, BN-3, BN-4).
- **Fixes that cut instead of adding:** BN-6 (`TRACEBACK_IMPORTERS` and `traceback_import_missing`), BN-8 (T7's `src/` reads), BN-13 (the receiver-file branch), and the BASE-row clause of T5 in BN-4 and BN-7.
- **New:** 1 row (T8), 4 plants (N20-N23), 9 mutants (M31-M39), 1 rule (`dev_server_caller`).
- **Build notes:** 14 (BN-1 to BN-14). PENDING LEAD: 3 new (17-19). Couplings: 3 new (C14-C16) and 2 amended (C9, C11).
- **Unaddressed:** 0.
