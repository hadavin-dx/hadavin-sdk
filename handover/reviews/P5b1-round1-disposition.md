# P5b1 round 1: disposition of every finding (ticket revision 1 -> revision 2)

Written 2026-11-06 about 03:00 UTC (08:30 IST). Author: ticket revision author (text only; no code run, no suite run). Source of decisions: `reviews/P5b1-round1-resolve.md` (applied one per finding). Findings: `P5b1-round1-adversarial.md` (A1-A18) and `P5b1-round1-correctness.md` (C1-C14), 32 in all; the resolve merges duplicates into 20 rows. Ticket locations are section names in `tickets/P5b1.md` revision 2.

Words: applied = done as the resolve says; applied-narrowed = done as the resolve's narrowed version; contested = I disagree and say why; declined = not done and why. Result: 32 applied (3 of them narrowed), 0 contested, 0 declined. Cuts the resolve ordered (order 7) are listed under the rows they touch.

## One row per finding
| Finding | Disposition | Where in revision 2 | Note |
|---|---|---|---|
| A1 (library class name printed; modelled Amazon codes are class names) | applied | Interface 3 `describe`; "Where provider text can still be"; Tests R6, R16; Files (r16:68, CHANGELOG) | `describe` uses `class_name_of`; `type(exc).__name__` fallback deleted. Modelled Amazon errors print `dynamic_class`. The `__module__` claim is READ in botocore, not run: UNVERIFIED |
| A2 (P5a/P4a "PENDING", `retry_count`, request-id shape) | applied | Interface 1, 6; "Depends on"; golden table; PENDING LEAD 1 | Real P5a names used. `REQUEST_ID_SHAPE` deleted; P5a `SafeToken.shape` is the one home. Follow-on `diagnostic.py` edit owned here |
| A3 (hot files, P4b2 missing) | applied | "Hot files"; PENDING LEAD 2, 5 | Order P4a, P5b1, P4b2; P6b1 removed. New conflict found with frozen P4a rev 12 (PENDING LEAD 5) |
| A4 (read test cannot fail) | applied | Tests R4; "What each adapter reads" | Rebuilt as read-recorder: assert on recorded names, `__str__`/`__repr__` defined, `BaseException` variant, no proxies. Recording subclass of the real error: construction UNVERIFIED |
| A5 (library loggers) | applied-narrowed | "What is NOT taken" (c); Tests R14; PENDING LEAD 14 | Strict xfail naming P5b4, exactly 2 expected. No logging filter (cut). Stubber kept out of the Amazon row |
| A6 (hostile objects escape `_chain`, `transient`, hooks, Bedrock `retryable`) | applied | Interface 3, 5; "Fail-closed" 2; "Retry interplay"; Tests R5, R10 | Whole failure path guarded, tested end to end through `with_retry`. List of behaviour changes written down |
| A7 (raising `status_code` money wording) | applied | "Retry interplay"; PENDING LEAD 4 | Stated plainly; recommended refused for v1 |
| A8 (timeout vs connection order) | applied | Interface 3 `default_facts`; fact-sources table; golden rows 9, 31; mutant M33 | Timeout wins everywhere |
| A9 (kind adapters must end in `default_facts`) | applied | Interface 5; mutant M38 | |
| A10 (tables and mutants thin) | applied | Tests R15; golden rows 29-31; Mutation plan M21-M40 | One table-driven test per table with a literal copy. 64-character bounds are behaviourally equivalent (no table key above 29 characters), so they are killed by a patched-table test; this is a judgement call, recorded here |
| A11 (grammar too loose) | applied | Tests R6 | Closed `ProviderErrorType` values enumerated |
| A12 (source guard too weak) | applied | Tests R7; PENDING LEAD 12 | Sanctioned path named (`describe`), taint sources and sinks listed, one planted violation per sanitiser. P5b3 must allow `llm.retry.describe` |
| A13 (reason for vendor-table deviation) | applied | Fact tables note; PENDING LEAD 6 | Reason now lock-in rule a, not rule c |
| A14 (traceback / `HADAVIN_DEBUG`) | applied-narrowed | "What is NOT taken" (a); Interface 3 `with_retry`; Tests R17; PENDING LEAD 11 | `from None` at the two raises; `__context__` kept for P5a's chain walk (P5a honouring it: UNVERIFIED). No `cause_kind` fact (cut). `HADAVIN_DEBUG` beyond this stays with P5b3 |
| A15 (status 777, success-body cap) | applied-narrowed | "Retry interplay"; PENDING LEAD 10 | Pointer only: owner is P4b2. I grep-checked that `P4b2.md` and `P4a.md` carry neither |
| A16 (`HTTPError` not closed on retried attempts) | applied | Interface 3 `with_retry`; Tests R8; M31, M32 | Close on every failed attempt in a `try`; `Retry-After` read after close |
| A17 (jargon) | applied | "Words used in this ticket"; Problem field | Five-sentence Problem; "tripwire", "zone T2" replaced; "R1P", "mutant", "stand-in" defined |
| A18 (P5a dependency wording) | applied | "Depends on"; Interface 2 | Import direction written; cycle means the build stops and reports |
| C1 (P5a names not real) | applied | whole ticket; Interface 1-2 | Merged with A2 |
| C2 (P4b2 missing from hot files) | applied | "Hot files" | Merged with A3 |
| C3 (Bedrock `retryable` unguarded) | applied | Interface 5; M36 | Merged with A6 |
| C4 (test wire cannot produce the rows) | applied | "Files" (`llm_wire.py`, new fixtures, `raw_http.py`); golden table Source column | `response_meta` in `BedrockWire.serve`; named stand-ins for rows 9, 10, 16, 17, 23, 24, 31 |
| C5 (hostile rows not P5a `Row`s) | applied | Hostile corpus table (HC-51 to HC-69); Files | `CORPUS_STEP` bump to "R1P". 19 rows (old 14). Teeth exemption stated |
| C6 (H11 expectation wrong) | applied | HC-hostile_class-61 to -63 | Re-aligned to `dynamic_class`. Merged with A1 |
| C7 (guard wording) | applied | Tests R7 | Merged with A12 |
| C8 (mutants unnamed killers) | applied | Mutation plan (every mutant names its killers) | Merged with A10 |
| C9 (close() robustness) | applied | Tests R8 (c); M31 | Merged with A16 |
| C10 (R4 rebuild) | applied | Tests R4 | Merged with A4 |
| C11 (`retry_count` range 1..1000) | applied | Interface 1 (0 to 1000) | Merged with A2 |
| C12 (`URLError(TimeoutError())`) | applied | Interface 3; golden row 31 | Merged with A8 |
| C13 (table tests) | applied | Tests R15 | Merged with A10 |
| C14 (small corrections) | applied | R1 wording; Evidence command 6; Verified facts (`bedrock.py:101`); Interface 2 (`kind_hint` deleted); Files (item 9 money-neutral); botocore version | botocore 1.43.122 is the lock version (rev 1 said 1.43.118) |

## Counts, old to new
- Ticket lines: 305 to 368 (the same-length measure, `wc -l`).
- Golden table rows: 28 to 31.
- Test rows: R1-R14 to R1-R18.
- Mutants: 20 to 40 (M1-M40).
- Hostile corpus rows: 14 (H01-H14) to 19 (HC-51 to HC-69).
- PENDING LEAD items: 15 to 16 (new: 5 order disagreement, 11 `from None`, 14 library loggers; item 16 is the UNVERIFIED list; rev 1's items renumbered).
- Findings: 32; resolve rows 20 (PROPOSE FIX 20, of which 3 narrowed and 4 cuts; CONTEST 0; DECLINE 0; ESCALATE 0; PENDING LEAD 4 as the resolve counted). My dispositions: applied 29, applied-narrowed 3, contested 0, declined 0.

## Author decisions beyond the resolve (judgement calls, please check)
1. Dependency name `provider_facts` direction (`protocol` -> `provider_facts` -> `guard/diagnostic`) chosen by me; if an import cycle appears the build stops.
2. Corpus numbers 51-69 for P5b1 are my choice; P5a must be told (PENDING LEAD 1).
3. The 64-character table bound is tested only by a patched-table white-box test (see A10).
4. Row 28 expected values were written by me from P5a's rule (status 418 kept, `error_type` decides); UNVERIFIED against merged P5a.
5. New cross-ticket finding: frozen P4a rev 12 (line 167) and `P4b2.md:66,82` conflict with the decided file order (PENDING LEAD 5).

## UNVERIFIED (carried into the ticket)
Merged P5a code (`class_name_of`, `SafeToken.shape`, whether `diagnose` honours `__context__` under `from None`); P4a/P4b2/P6b1 beyond cited lines; the `__module__` of the modelled Amazon class; whether the replay server can send status 777 to the Claude library; whether a recording subclass of the library error can be built; live provider shapes (no spend); Vertex and Foundry `request-id` headers; whether demo repos copy `llm/*`; `urllib` writing no log lines; every test row (nothing run).
