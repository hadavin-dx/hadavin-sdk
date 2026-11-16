# P5a round 2, adversarial review (ticket rev 2, 153 lines) - agent a012dd4368111af40
Status: REPORTED (saved by the lead from the hand-back, condensed; model output, not user authority). Read-only, no shell, nothing run; runtime claims by reading only.
Verdict: NOT buildable as written: 1 Blocker, 6 Major (ADV-2..7), 5 Minor, 3 Nit.
| id | sev | lines | problem | fix |
|---|---|---|---|---|
| R2-ADV-1 | Blocker | 66,107,89 | test_real_writers_* drive today's extract.py:58 / tick.py:316,317,324; their "no canary" assertions fail at the P5a merge commit (P5a wires nothing, line 18) but Done requires the file to pass. No mechanism named. | Commit as xfail(strict=True) or a writer_wiring later row owned by R3c, flipped by P5b3; or evidence-only scratch file; make Done consistent. |
| R2-ADV-2 | Major | 66,63,87 | Fail-before worktree has no diagnose/render/Diagnostic, but the same test file imports them -> collection ImportError. | Own file (e.g. tests/test_diagnostics_old_writers.py) importing only corpus, codes.py, leaks and real writers; or lazy import. |
| R2-ADV-3 | Major | 36-42,65 | chain, lib_frame, dropped_facts never rendered by Grammar A; cause_kind never filled; chain code builds unprinted data. T6 validation_failed has no slot for validation_text. | Cut chain/lib_frame (to later table) or add exact render slot; write T6 literal template. |
| R2-ADV-4 | Major | 40,41,52 | request_id (^[A-Za-z0-9_-]{8,40}$) and token40 let name-shaped foreign text print; token40 dead surface; StepToken.of accepts any lowercase token; patterns not written in ticket. | Cut token40; request_id only with fixed provider prefix or move provider read side to P5b1; StepToken.of registered set only; add name-shaped canary rows; write patterns. |
| R2-ADV-5 | Major | 35,54 vs order 20 item 4 | Rebuilt on ce70eb5 but P1m/P1a/P1b/P3a/P4d/P2a-1/P2d/P4a merge first and add exception classes; "22 classes/21 members" tests fail after rebase. | Add post-rebase step: re-run scan, add rows for new classes; do not freeze counts in tests. |
| R2-ADV-6 | Major | 43, App. B | realpath(co_filename) vs realpath(__file__) mutant probably equivalent/unkillable; installed-layout run is UNVERIFIED. | Show a concrete symlink case or cut realpath/normcase and the mutant. |
| R2-ADV-7 | Major | 37,41,65 | "innermost counted frame in this package" ambiguous: same KeyError bug class gets internal_bug or foreign_exception; T10 unnamed. | Define precisely; one test per case; name T10. |
| R2-ADV-8 | Minor | 89 | "new code only" exemption uncapped. | Fix exempt classes as a set; cap. |
| R2-ADV-9 | Minor | 87 | scan_keyset semantics UNVERIFIED; fallback only on ImportError. | Agreement test on look-alikes per fold class or fail evidence on any difference. |
| R2-ADV-10 | Minor | 37 | diagnose(BaseException) behaviour for non-Exception / bad fact unstated. | State fallback; drop-and-count bad facts. |
| R2-ADV-11 | Minor | 31-32 | provider_* codes unreachable on main; need RESERVED_FOR like session_closed. | See ADV-4; say which counts. |
| R2-ADV-12 | Minor | 54 | Numeric bounds repeated as literals; only 13 in defaults.py. | One frozen bounds table. |
| R2-ADV-13 | Nit | 24,38 | lib_frame carried not printed. | Cut or print. |
| R2-ADV-14 | Nit | 42 | __main__ in stdlib_module_names UNVERIFIED. | Subtract explicitly. |
| R2-ADV-15 | Nit | 24 | Py 3.12 untested (requires-python >=3.12, CI 3.13 only). | One sentence on accepted limit. |
Cut candidates recommended: provider_* read side + request_id/retryable/provider_error_type; chain/lib_frame/dropped_facts; realpath/normcase; psycopg golden T3-T5 to the phase step (P5b1).
Verified (read on main): 17 fields; 22 own classes/files/lines; tick.py/extract.py/injection.py/runmap/config/registry/anthropic/pyproject/ci cites; counts 21 Code, 20 FactKey, 12 ProviderErrorType, 26 pydantic names, 13 defaults constants, 140+16+2=158 rows; Appendix A ids 001-051 once (33/16/2). Drift: test_lockin_guard.py:68 vs ticket 69-71.
Not checked: git diff ce70eb5 HEAD; pydantic/psycopg behaviour; ErrorType count 111; T3-T10 goldens; P1b scan_keyset; P1m Mutant signature; k1b/diagnosis name clashes; producers.py rows; P2a class names.
