# P4a build-start resolve (order 20, one round)

Status: resolved (AUTO mode; interactive gate skipped as ordered). Model output, not user authority.
Target: `handover/tickets/P4a.md` revision 12 (FROZEN), full file. Fixes go only into the new section "Build notes (build-start review, order 20)" at its end; the frozen body is not edited.
Gate: order 20 item 3 (two fresh reviewers, one resolve, no second round). Findings: `reviews/P4a-buildstart-adv.md` (combined file, 10 ids) and `reviews/P4a-buildstart-cor.md` (8 ids). The two files reuse BS-P4a-COR-n for DIFFERENT findings, so this file writes them as A:COR-n (adversarial file) and C:COR-n (correctness file).

Honest note (what I did NOT check). Nothing was run: no test, no probe, no repository script. I did not read P4b1, P4b2, P4c, P4d or P2a. I did not re-read the whole ticket (only the lines the findings cite, plus greps). I did not check whether a detector kind can be mislabelled the way an llm kind can (note 2 leaves detectors as a label promise). I did not confirm `k1b/tools.py:238` records come only from loaded bundles (note 12 hands that to the builder). Mutant and ConfigError counts after the notes are my arithmetic on the ticket's own numbers, not a recount on built code.

Facts I checked myself (grep and read on this tree; `python3 -I` for arithmetic only):
- `round_cost_up` and `MAX_USD`: 0 hits in `src/`. `src/` on this tree equals ce70eb5. origin/main differs from ce70eb5 in `src/` in three files only (`guard/http.py`, `guard/runmap.py`, top-level `tools.py`); the ticket names none of them.
- `AnthropicLLM`, `BedrockLLM`, `GeminiLLM` and `OpenAICompatLLM` all subclass `NetworkLLM` (`llm/common.py:193`). `FakeLLM` and the test stubs (`ScriptedLLM`, `RecordingLLM`) do not. `llm/common.py` does not import `k1b`, so importing `NetworkLLM` in `k1b/replay.py` causes no import cycle.
- `config.py` has no `Price` class (the price type is `Money`, `:47`). Mutant a2-16 (line 381) names a `Price` validator that P4a-2 does not write.
- The `Hung` stub (`tests/test_k1b_replay.py:506-509`) waits before `super().chat`, so it has recorded no messages when the timeout fires.
- OpenAI-compatible `_parse` (`:138`) and Gemini `_parse` (`:97`) do `resp.get(...) or {}` and then `.get`. A usage value that is present but not a dict raises `AttributeError` inside `self._retry`, and `with_retry` (`retry.py:97-99`) turns that into a plain `ProviderError`.
- All 24 recorded reply files carry `"input_tokens": 500` (and `"output_tokens": 50`, per the ticket).
- `ConfigError(` occurrences: 6 in `k1b/replay.py` and 169 in `src/` (matches the ticket).
- `encode(` sites in `k1b/`: `bundle.py:123`, `causelist.py:53`, `replay.py:64`, `tools.py:221`, `tools.py:238`. The ticket's sibling list omits `causelist.py:53` and `tools.py:238`.
- C13p clause 2: ceil(0.016300160557 x 10^8) = 1630017 and ceil(0.048900481671 x 10^8) = 4890049, so the ticket's literals are right. 6W = 513/3125 = 0.164160.
- The PL header (line 514) says 51 numbers, 1 to 63, 43 live. Revision 12's own count is 53 numbers, 1 to 65, 45 live.
- `backends/table.py:386` is `TABLE`, `:512` is the `llm` entry, and `k1b/loop.py:115-123` is `worst_case_usd`.

| id | category | decision |
|---|---|---|
| A:COR-1 | PROPOSE FIX | Build note 1: the start gate (P2a-1 and all P4d pull requests merged), branch from origin/main, re-locate the cites at E0, draft pull requests until hard gate item 0 holds, no stand-in helper. |
| A:ADV-1 | PROPOSE FIX (+PL66) | Build note 2: add `isinstance(llm, NetworkLLM)` refusal, row C18(c) and mutant a2-62. The body's reason for rejecting a type check is true only of an allowlist; corrected at build start. Changes the accepted PL55 scope, so it is PL66. |
| A:COR-2 | PROPOSE FIX | Build note 3: no bool clause, no `Price` class; mutant a2-16 is planted in P4d-a2-i's merged `Route` validator and killed by C10. |
| A:COR-3 | PROPOSE FIX | Build note 4: what "line 68" points at, and "no second rounding function". |
| A:COR-4 | PROPOSE FIX | Build note 5: a local `Hung` records `messages` before it waits. |
| A:COR-5 | PROPOSE FIX | Build note 6: PL header corrected. |
| A:ADV-2 | CONTEST | The ticket already states it. "Settle in `finally`" in Rules stated once (line 163) names "`ValueError` from `round_cost_up`" and assigns the settle to P4b1-b's `finally`. Line 157 and row U14c pin the loud `ValueError` as intended for a route that bypassed validation. |
| A:ADV-3 | PROPOSE FIX | Build note 7: the V36 trigger gains a check of one recorded reply against the byte bound. |
| A:ADV-4 | DECLINE | Nit. Line 359 already says these are "named here as checked and are NOT counted as ids". |
| A:ADV-5 | DECLINE | Nit. `cli.py:221` looks up the secret and builds the object, but makes no call. v1 replay is dev-only (PL61), and moving the check means a `cli.py` edit (cut surface). |
| C:COR-1 | PROPOSE FIX | Same as A:COR-1 (build note 1). |
| C:COR-2 | PROPOSE FIX | Build note 8: `FakeLLM` has no exemption from the input-zero rule, and U5 gains two clauses. No recording changes. |
| C:COR-3 | PROPOSE FIX | Build note 9: order 20 item 5 supersedes the hot-file edit order. The one-sitting money rule and PL63 stay, because order 20 does not touch them. |
| C:COR-4 | PROPOSE FIX | Build note 10: pin the count as a delta (+3 with note 2) and recount at the rebased head. |
| C:COR-5 | PROPOSE FIX | Build note 11: a non-dict usage is `UsageMissing("absent","usage")` for OpenAI-compatible and Gemini, with U1 clauses and mutants a1-30 and a1-31. |
| C:COR-6 | PROPOSE FIX | Build note 6: the PL header is fixed. The `table.py` and `loop.py` cites were checked and are right, so they are not changed. |
| C:COR-7 | PROPOSE FIX | Same as A:COR-2 (build note 3). |
| C:COR-8 | PROPOSE FIX | Build note 12: two sites missing from the sibling list. The builder greps at the rebased head and confirms where `render`'s records come from. |

Couplings:
- A:ADV-1 and C:COR-4. The third `ConfigError` makes the delta +3 (replay.py 6 to 9; `src/` 169 to 172 on today's tree).
- A:COR-2 and C:COR-7 are one fix.
- A:COR-1 and C:COR-1 are one fix, and they agree with order 20 item 2 ("P4a (after P2a-1 and P4d are merged)").
- A:ADV-3 and V35 share the byte-bound assumption.
- The counts in build note 13 (mutants 38 + 48 = 86) depend on notes 2 and 11.
- Surface cut considered: deleting C8's `True` regression pin would also close part of A:COR-2. I did not delete it: the pin costs nothing, and the body says it is a regression pin.

PENDING LEAD (continues the ticket's list):
66. [PL66] (A:ADV-1; changes the accepted PL55 scope) PL55 made the replay guard read labels only, as "a caller promise". Options:
    (a) Keep labels only, and the lead accepts in writing that a Python caller can pass `llm_kind="fake"` with a real kind object.
    (b) Add `isinstance(llm, NetworkLLM)` as a denylist: one check, row C18(c), mutant a2-62. It refuses no test stub. A wrapper around a real kind is still not caught.
    (c) An allowlist by type (`FakeLLM` only). Rejected, because it refuses `ScriptedLLM` and `RecordingLLM`.
    RECOMMENDED: (b). The studio rule is that a forged-input exposure gets a control, not a note, and here the cost is one line. I proceeded with (b) in build note 2. It is reversible: delete the check, the row and the mutant.

Counts: 18 findings. PROPOSE FIX 15 (12 distinct fixes, build notes 1 to 12; note 13 is the recount); CONTEST 1; DECLINE 2; ESCALATE 0. Remaining unaddressed: 0. New PENDING LEAD: 1 (PL66). Ticket counts after the notes: mutants 86 (38 + 48), test rows 34.
