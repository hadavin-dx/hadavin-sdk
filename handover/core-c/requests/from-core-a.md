# From core-a to core-c, 13:10 UTC (lead order: core-a has a free box and builds for other lanes on separate branches)
Branch wip/core-a-for-c (pushed to hadavin-sdk; you cherry-pick; I never push to cloud/core-c):
1. tools.py error_reason un-sanitised str(exc) crash (lone surrogate + handed-out secret) + docstring order; test + mutant.
2. tests/test_k5_producers.py exemption narrowed to error_reason / redactor-assigned names; test proving a planted `str(exc)[:N]` elsewhere fails.
Files I will NOT touch: redact.py (_build/_Redactor/sweep/_trie), runmap.py, defaults.py, model_gate.py, agent_loop.py, config.py, tests/b64*, tests/test_redact_finder_cap.py.
After these two I will list free QUEUE items on my board and take ONLY those you answer here with 'yes, build X' (add a line below, or tell the lead). No doubles: I start nothing else on your lane without your line.

## 13:14 UTC: free core-c items found by core-a (read-only list; nothing started beyond X1/X2)
Buildable outside the held files, awaiting YOUR line 'yes, build <id>' (and core-b's consent where marked):
- R4 tools.error_reason redacts with a throw-away map: redact once with the run's map (tools.py; request 4 says core-b owns tools.py: confirm). Named test: a secret in an error text is masked in a later tool result of the same run. Size S-M.
- R5 SlackChannel._who (approvals/slack_channel.py ~62-65, 93, 97, 198) posts email / <!channel> principals raw: new test with an email principal and a <!channel> principal. Core-b owns the file: consent needed. Size S.
- C3 usd_cap as the sixth reason in SPEND_REASONS (model_gate.py:117-119, allowlist six, ORDER 014): collides partly with G13 _chunk and the G9 docstring hold: NOT started.
Not buildable by me: G11, G12b, G13, E14 nits, runmap/redact/textnorm items (held), items waiting on lead decisions E16, L-D13, E19 O-1, G6.
core-a owes you: the 256 KB scan-stall script (request not received here: send the request text, or the lead can).

## 13:17 UTC: branch wip/core-a-for-c READY (head see `git log wip/core-a-for-c`, two commits on top of your head 9072e701f)
Fixes both Majors: tools.py error_reason sanitises str(exc) (lone surrogate crash), docstring states the real order; test_k5_producers exemption narrowed to error_reason (+ planted-slice tests); mutant ER1 (tests/error_reason_mutants.py) killed. Fresh review: no Blocker/Major; nits fixed (non-vacuous straddle test, secrets=None test, docstring).
OPEN DECISION for you (found by the reviewer, not changed by me): an exception whose __str__ raises propagates out of error_reason (called inside except handlers at agent_loop.py:314 and tools.py:1196: the tool turn is lost). Should error_reason swallow it? Also: a handed-out secret that itself contains NUL/U+FFFD no longer matches after sanitising (unrealistic).
Checker limits left known: the narrowed slice-before-redact checker does not see walrus, AugAssign, tuple unpacking, f-string or %-format copies of str(exc).
