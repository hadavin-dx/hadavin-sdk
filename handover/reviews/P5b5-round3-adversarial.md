# P5b5 round 3, adversarial review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

ROUND 3 ADVERSARIAL REVIEW, P5b5 revision 3 (read-only)

Verdict: no Blocker. I count 3 Majors (R3-ADV-1, -2, -3), which is above the "at most 2 Majors" limit for a round 4 in order 20 item 6. The order text itself is UNVERIFIED (I did not open LEAD-ORDERS.md; I relied on the ticket's quotation of it). The lead decides. All three Majors are one-line text fixes.

Cite check: <repo> is not a git repo here, so `git show cd2243f:` was impossible. I compared the cites with the on-disk `src/`. They match for `receiver.py:62-63`, `cli.py:32/82/287`, `extract.py:58`, `injection.py:96`, `tick.py:292`, `k1b/loop.py:187/194` and `producers.py:19`. They fail only for `guard/runmap.py:532` (on disk `safe_head` is at 485), which the ticket itself says (older on-disk `src/`). `k1b/loop.py` `run_case` starts at :125 on disk too.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-ADV-1 | Major | 59 (key definition), 62 (rule 3), 96, 110-112, 122 (N6-N8, N18) | The two sections contradict each other. Line 59 says `<key>` is `<import>` for "an import statement". Rule 3 findings, T2's fail-before and N6/N7 use `<module>` for `import traceback` and `from traceback import`. Rule 4 puts `from logging import basicConfig` under `<import>`. A builder cannot tell whether `import traceback as tb` is `::<import>::` or `::<module>::`. An `import traceback` inside a `def` is keyed by neither rule. | Say which key each rule uses. Suggested: rule 3 keys all import forms `<import>` and the `__import__` / `import_module` calls by enclosing key or `<module>`. Then change N6, N7 and the T2 fail-before literal to match. |
| R3-ADV-2 | Major | 95-96, 98, 124, plus Interface (no import rule) | Collection. T6 and T7 need `Code`, `FactKey` and the P5a modules. At `cd2243f` these do not exist. If they are imported at module level, `pytest` fails with a collection error, not an assertion. That breaks the claim "T1-T3 FAIL on cd2243f on an assertion". The step-0 and fail-before commands copy only the test file into the old worktrees, so this is the exact run. P5b3 has a "Collection rule" (`P5b3.md:340`); this ticket has none. | Add: names new at the head are imported inside T6/T7 only. The fail-before runner must show T1-T3 as FAILED, not ERROR. |
| R3-ADV-3 | Major | 98 (T4), 126 | T4 is under-specified. "POST to /slack/actions with a made-up path suffix" is a contradiction in terms: any suffix makes `self.path != PATH`, so the 404 branch runs and `handle_slack_action` is never reached. If the builder posts to the exact path instead, `approvals.receive` runs on a fake body. Whether it raises is not stated. If it raises, `handle_error` prints `127.0.0.1` and T4 fails on old code, which the ticket says it passes. It is UNVERIFIED that `receive` returns `bad_signature` on junk. | Fix one request, for example a POST to `PATH + "/<made-up>"` that gets 404, or an exact path with a stub `Approvals` whose `receive` returns. State the expected status. Assert it, so a swallowed exception cannot pass. |
| R3-ADV-4 | Minor | 61 (rule 2) | The selector is "any base name ending in `RequestHandler`". That includes `socketserver.StreamRequestHandler` and `BaseRequestHandler`, which have no `log_message`. Such a class would get a permanent false `server_log_noop_missing`. In the other direction, `class Sub(Handler)` or an indirect base escapes. No such class exists on disk today (only receiver.py:43). | Limit the rule to bases ending `BaseHTTPRequestHandler` / `SimpleHTTPRequestHandler`, or add a plant for a stream handler. State the indirect-subclass limit in V2. |
| R3-ADV-5 | Minor | 62, 65 | `TRACEBACK_IMPORTERS` may whitelist P5a's `diagnose` module. The rule pins only the import, not what the module does with `traceback`. A `traceback.print_exc()` there is invisible to T2. The taint guard covers only text from `except ... as` names. | Add a rule: no `traceback.print_*` or `format_*` call in the allowed module (a name check). Or state it as a limit. |
| R3-ADV-6 | Minor | 100-101, 138-139 | Not every check has a mutant. Row-level coverage is true (line 274), but some halves of rows are unmutated: T6's `FactKey` half (M8 only deletes a `Code` row), T7's `.log` path half, T5's "BASE row still present" half, and T4 on 3.12. Dropping those halves would go unnoticed. | Add three mutants: delete a `FactKey` row, name a bogus `.log` path, delete a BASE row. Or drop the unmutated assertions. |
| R3-ADV-7 | Minor | 155, 51 | M25 reads "inside `run_case`, add `except ValueError as exc: ...`" with no `try` or position given. The mutant edit needs a valid insertion point. Its killer is P5b3's unbuilt guard, and the "SURVIVES, builder STOPS" branch only halts the build. Also, nothing but the guard catches `redact_text(str(exc))` or any other cleaner on exception text. T1 pins only the `safe_head` name. | Give the exact insertion (an existing `try` at `loop.py:166/173/176`). Note in F2b that other cleaners are covered only by the guard's "call not on SAFE" sink rule. |
| R3-ADV-8 | Minor | 53, 226 (PL 13), 89 | The one known exception-text-to-stderr path left in the package (`handle_error` in the dev server) has no test and no failing signal. Recommendation (a) is "state it". An owner-visible limit is not a control, and `fix-dont-defer` allows deferral only for impossible, owner-only or third-party items. This is P5b4's code, so it is defensible, but only if the lead accepts it explicitly. | Prefer alternative (b), an `xfail(strict=True)` T4b. Or have the lead record in the ledger that (a) is accepted. |
| R3-ADV-9 | Minor | 63, 121, 109 | The plants depend on structure that P4a and P5c may change. N1 needs `extract.py::extract` to exist at the head. N5 needs both `safe_head` calls inside `run_case`. N19 needs `k1b/loop.py`. Nothing says what the builder does if the base moved. | Add: plants must anchor on the head, and a missing anchor is a STOP (same as C6). |
| R3-ADV-10 | Minor | 101 | T7 hard-codes `output_guard.py`, a file that does not exist yet (P5b4.md:26, 63 confirm the plan). Rename or split would make T7 error, not fail. The page claims in 6(a) (fd 2 lost) have no test of their own. | Resolve the path from step 0, and make a missing file a clear failure message. |
| R3-ADV-11 | Nit | 17, 71-83 | The surface could be cut: rule 4 `basic_config` and N9, N10, M12, M21 duplicate P5b4's ownership of `cli.py:287`. T7 and M9 guard a single hypothetical config key. They are the likeliest cut candidates, though the ticket argues for them. | Lead's call. Cutting both saves 2 test rows and 3 mutants with no leak-coverage loss. |
| R3-ADV-12 | Nit | 23, 89 | The caller calls this a "security path"; the ticket says "redaction ... Not a money or security package". The extended-review result is the same, but the labels differ. | One sentence aligning the label with the lead's classification. |
| R3-ADV-13 | Nit | 98, 138 | `server_log_noop` accepts only a bare `return` or `pass`; `return None` is a finding. Not stated. | Say so, or accept `return None`. |

Template fields: all 17 are present in the template's order (Package id ... Rollback). Rollback names the tag `pre-P5b5`, as the template asks.

Dev-config leak check: nothing sends text out. T4 binds 127.0.0.1 with port 0. The page uses placeholders. The evidence commands use only local `uv`, `pytest`, `ruff`, `bandit` and `git`. No real-looking secrets found in the ticket.

Counts: the ticket's own counts recompute correctly (7 + 19 = 26 test rows, 30 mutants M1-M30, 22 finding rows with 19 fix / 3 decline, 13 couplings with 4 closed or withdrawn, PL 1-16). Every mutant has a killer that exists in the tables, except M25, whose killer is the unbuilt P5b3 guard (see R3-ADV-7). Mutant-to-plant kills hold as tabled:
- M14 by N1
- M18 by N5
- M24 by N14 (a `<lambda>` key gives a new finding)
- M26 by N15
- M30 by N19

Verified (read):
- The ticket in full (315 lines), the template, `receiver.py` (all 66 lines).
- The on-disk `safe_head` import and call sites: 4 imports, 5 calls (`extract.py:58`, `injection.py:96`, `tick.py:292`, `loop.py:187` and `:194`).
- `cli.py:32/82/287`; `producers.py:19/47`; `injection_check` at `injection.py:85`, so the T1 key name is right.
- `output_guard.py` is P5b4's planned module (`P5b4.md:26, 63, 151`).
- `P5b3.md` lines 110, 204-228 (`own_text`, taint guard, SAFE list without `safe_head`, no waivers), 309 and 340.
- `P5a.md:127-128` (`CORPUS_STEP` and `STEPS`).

Not checked (UNVERIFIED):
- Every line cite against commit `cd2243f`, and the standard-library lines (`socketserver.py`, `http/server.py`, 3.13 and 3.12).
- The neighbour tickets beyond the lines listed above: P5b4 (U19, U6, S1, V-OG-4), P5c, P8b, P4a.
- LEAD-ORDERS.md and amendments.md (I did not open them), and so every order citation.
- Whether `approvals.receive` raises on junk (see R3-ADV-3), whether `capfd` sees the server thread's write, and whether `handle_error` prints the message.
- Whether M25 is killed by P5b3's unbuilt guard.
- P5a's `Code` and `FactKey` member counts, the P1m runner arguments, and whether P5a's `diagnose` imports `traceback`.
- Anything about the old branch `198a6b6`.