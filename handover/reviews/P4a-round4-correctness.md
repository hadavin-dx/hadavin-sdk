# P4a round 4 correctness review (egm:egm-codebase-details), ticket rev 4. Condensed by the lead; read-only, ran nothing.
| id | sev | where | problem | fix |
|---|---|---|---|---|
| C4-1 | BLOCKER | L49, L220, L305, L216 | False claim "no k1b test stub reaches the charge with prices": `k1b/replay.py:162-166` always passes prices; `tests/test_k1b_replay.py:502` (Hung(ScriptedLLM), no REQUESTS_PER_CHAT) hits CallTimeout; `request_bound(llm)` raises TypeError inside the except; run_case breaks its "never raises" contract | Name the test; add `REQUESTS_PER_CHAT = 1` to `tests/k1b_support.py::ScriptedLLM` (line 17); define what run_case does when request_bound refuses (catch + conservative charge, still aborted); C13 row; fix L49 |
| C4-2 | Major | L216, C13 | `getattr(llm,"max_attempts",1)` fails open; wrappers (P4b1-b) lack attributes | Rule: wrappers forward both attributes; P4b1-b relay and checklist; C13 row |
| C4-3 | Major | C13 preamble L237 | `messages=[]` with 298-char system unreachable via run_case (first message built at loop.py:144-149); literals hold only for direct worst_case_usd | Compute expected tokens from the real first message, or assert via worst_case_usd |
| C4-4 | Minor | U1/U3 Bedrock, U14b/c, fail-before wording | Direct reply()/build_usage rows raise TypeError/ImportError on ce70eb5 | Drive through chat() with stub client, or label "new feature, no fail-before" |
| C4-5 | Minor | L27, L104, L304 | P4d cites wrong (249 and 269, not 244/264) | Cite by item |
| C4-6 | Minor | L53, U9 | estimate_tokens tests are two, not three (test_providers.py:30,37) | "two" |
| C4-7 | Minor | L116 | Cites PENDING LEAD 3 for zero handling; it is PL5 | PL5 |
| C4-8 | Minor | round3-disposition COR-R3-1,3,5,12 | Ids do not match the resolve report; questions-for-lead note missing | Re-map ids; add note |
| C4-9 | Nit | L48/L216/L304, L54, L38, C15 | Cite slips (loop.py 166-171 vs 172; table.py 593/595; test_llm.py 94-95); C15 "UNVERIFIED" is checkable at tests/contracts/test_llm.py:81-83 | Fix cites |
| C4-10 | Nit | C7(b) | Domain must exclude input_tokens==0 and bound output by max_tokens | State domain |
Verified: code cites on ce70eb5 (long list), Reply( count 26, fixtures 24, arithmetic, template 17 fields, mutant killers. Could not check: git state (not a git repo for the reviewer), nothing run.
