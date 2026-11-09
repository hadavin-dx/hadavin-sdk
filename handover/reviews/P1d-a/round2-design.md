# P1d-a rev 2 plan review r2, egm-design (aa89841a), redaction path
Verdict 0B/4M/6N. Round-1 closed (two partial).
M1 _blocks step (1) summary.replace("[.]",".") is global; hits inline code and fences (regex classes); restrict to prose parts or (?<=\w)\[\.\](?=\w) outside code; row + mutant; decide on stored summaries.
M2 ZWSP rule under-specified: _ANY_BLOCK must match d=_defang_outside_code(c) and d != lines[i]; row `1。 x`; strengthen A13.
M3 D3 order vs wide dots: `<HOSTNAME_1>。example.com` leaves a link and breaks idempotence. Order: wide dots, then D3, then _NON_ASCII_HOST/_DOMAIN; row D3e + swapped-order mutant.
M4 BS-1 corpus cannot measure the CHANGELOG promise (F16 band by construction; `=`-less query segments unmeasured; run<=120 near tautology). Add shape, per-shape over-mask, real-text sample, secret length range/tail model; ceilings to lead per ORDER 165.
Nits: N1 stale line refs (clean ends 38/39; _blocks :74/:81); N2 card map unreadable by test (spy on channel._seeded or assert no original); N3 `&amp;` query rows; N4 `?password=ab&cd=34ef` leak by grammar needs explicit non-goal, wide-dot hosts never reach redactor; N5 other readers of stored req.summary (console, FakeChannel, cards.py) grep in BS-0; N6 AST literal collector limits, D3a-d fail as NEW_SURFACE, run link property on base once, name test_k5_round11.py:113 must-run.
