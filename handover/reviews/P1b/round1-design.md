# P1b result review, round 1, egm-design, snapshot P1b-0d843b4 (branch core/P1b-fixwip)
Reviewer: fresh egm:egm-design agent (Sonnet). Ran no code; read snapshot, ticket P1.md, evidence TABLE.md. Condensed by the cloud session (fields kept: id, severity, where, issue, fix). Not yet checked by me against code.

| id | sev | where | issue | fix |
|---|---|---|---|---|
| F1 | MAJOR | runmap.py:276-285 canonical; evidence.py:57,87,88,151 | canonical now NFKCs per character; decomposed identifier ("cafe"+U+0301) now passes grounded()/contains() if evidence holds same bytes (ALLOW-side loosening). Precomposed vs decomposed no longer matches (regression). No test. Ticket says canonical stays. | Revert canonical for ALLOW consumers; keep per-char view only in replace_canonical; add grounded() test that fails on new code. |
| F2 | MAJOR | textnorm.py:1081,1099-1101; defaults.py; CHANGELOG | Ticket SK-2 says <=8 keys; code allows 16 (13 reachable). Ticket rev 16 never mentions scan_holds, register_value, scan_cache, scan_needles, EmptyView, ViewTooShort, CoverageRefused, TEXTNORM_* constants, injection.py or runmap.py change. 33 public names vs 19-20. Tests cite order 137/140. P2d-2 cost model assumes <=8. | Lead: point to authorising orders or amend ticket. |
| F3 | MAJOR | textnorm.py:1421-1427; TEXTNORM_STRICT_COVERAGE=True | register_value("hunter2-secret-key") gets coverage exact_only and raises CoverageRefused under default strict. Every ASCII/Latin secret refused at registration; rate not measured (false-abstain rule). | Strict only for uncovered shapes, or default non-strict with loud log; measure refusal rate on made-up corpus. |
| F4 | MAJOR | injection.py:49; textnorm._checked | 262145-char text raises TextTooLong -> guard_unavailable flag; redact_bounded cuts instead. Perf allows 10 s at cap; no figure logged. | Scan head or document + measure flag rate. |
| F5 | MAJOR | TABLE.md:15 | Fail-before vs core/P1a not run. | Run new tests on P1a/shim, save raw. |
| F6 | MAJOR | perf312/313.txt; test_textnorm_perf.py | S_call and 1,000-call figures not recorded (-q without -s). | Re-run with -s, save lines; tighten bound. |
| F7 | MINOR | textnorm.py:1156-1189 | contextvars cache shared into to_thread workers; unlocked eviction can raise RuntimeError/KeyError (not TextnormError). | Per-thread dict or lock; to_thread test. |
| F8 | MINOR | TABLE.md:4 | 1 skip attributed to dblink wrongly; no -rs; no baseline run of dblink test. | Re-run with -rs; run on base. |
| F9 | MINOR | textnorm_mutants.py | No mutant for app.build require_pinned_unidata, evidence.py, cache threads. | Add mutants. |
| F10 | MINOR | CHANGELOG | Earlier P1a entries rewritten; ticket says append only. | Restore, append. |
| F11 | MINOR | textnorm.py literals | _SCAN_KEY_CAP, _SCAN_CACHE_TEXTS, _MINIMUM_FLOOR, tag ranges not in defaults.py; insertion minimums cite unattached measurement. | Move to defaults.py; attach data. |
| F12 | MINOR | textnorm.py:216,1381 | scan_holds has no production caller; redact_text and tools._secret_forms do not use it. | State in ticket/hand-off; track consumer package (P1d). |
| F13 | MINOR | textnorm.py:1317,767 | scan_holds(text, value) two plain str args, swap undetected; fold_views casefold=False default. | Keyword-only args. |
| F14 | MINOR | injection.py:13 | Import runs full-range loops on every import; unmeasured. | Measure; lazy build. |

Not covered by reviewer: no code run; F1/F4/F7 from reading only; ticket Decisions/Relays/PENDING LEAD not read; test bodies, fixtures, Unicode data hashes not read; egress/redact.py/approvals not reviewed.
