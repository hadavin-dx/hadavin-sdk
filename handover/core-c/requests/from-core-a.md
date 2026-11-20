# From core-a to core-c, 13:10 UTC (lead order: core-a has a free box and builds for other lanes on separate branches)
Branch wip/core-a-for-c (pushed to hadavin-sdk; you cherry-pick; I never push to cloud/core-c):
1. tools.py error_reason un-sanitised str(exc) crash (lone surrogate + handed-out secret) + docstring order; test + mutant.
2. tests/test_k5_producers.py exemption narrowed to error_reason / redactor-assigned names; test proving a planted `str(exc)[:N]` elsewhere fails.
Files I will NOT touch: redact.py (_build/_Redactor/sweep/_trie), runmap.py, defaults.py, model_gate.py, agent_loop.py, config.py, tests/b64*, tests/test_redact_finder_cap.py.
After these two I will list free QUEUE items on my board and take ONLY those you answer here with 'yes, build X' (add a line below, or tell the lead). No doubles: I start nothing else on your lane without your line.
