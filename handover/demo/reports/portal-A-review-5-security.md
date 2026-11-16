# WP-A pass-4 delta, security and correctness review, round 5 (egm-design, read-only, snapshot portal-A-r5, patch sha 7a59d904c1df)
Saved by the cloud session from the reviewer's inline report. Reviewer ran nothing; read desk.py in full, test_portal_api.py lines 1-1066 plus the two new tests; did not read the schema/review_items view, tests/support.py, test lines 1067-1617 otherwise, JS rendering, Windows/other Python.

Verdict: no Blocker, 1 Major in this delta (+1 pre-existing Major), several Nits.

(1) Drain deadline: holds. read1 + settimeout(deadline-now) makes the wall-clock limit real; reply delay bounded about 1 s; timeout restored in finally does not break the write; no rfile read follows _drain.
- Nit: test_trickle_is_cut_at_drain_deadline drips every 0.2 s, finish() quiet window is 0.05 s, so it does not exercise finish()'s deadline (docstring "and after the reply" wrong); bound < 4.0 is loose (passes with 3 s). Drip faster than 0.05 s, bound about 2.5 s. Low residual RST flake risk.
- Nit: undocumented invariant that no rfile read may follow _drain (poisoned reader after timeout); add a comment.
- Nit: honest slow client sending more than 1 s / 1 MiB to a refused request can lose the reply to an RST; accepted trade-off, not in contract.
- Pre-existing Major (not this delta): header phase and body-read phase have only a per-recv 30 s timeout; 1 byte per 29 s holds a thread; no thread cap (server.py:139, 358, 424; contract.md:75).

(2) Person-card truth (Desk.resolve): 
- MAJOR portal_api.py:474-477: "person: not sent" is written for both the email question (crm_done=1) and the CRM question (crm_unconfirmed, crm_done 2->0); the card cannot tell them apart. Generic "not done" claims a superset; for the CRM question the sentence "check the mail system first" points at the wrong system (desk hint says no email was tried) and omits "an extra CRM row may need deleting by hand". Fix: pick the text from the followups row (crm_done), separate texts.
- Nit: contract says person cards "never say the email may have left"; the not_sent text hedges the same thing.
- Nit: _PERSON_TEXT wins over maybe_sent; crm_present with ambiguous_prior=1 shows no warning (latent; crm_done=2 with ambiguous_prior=1 judged unreachable).

(3) Tests: test_person_cards_after_the_real_resolve can fail but pre-state is hand-written (includes unreachable combo crm_unconfirmed/2/prior 1); does not assert post-resolve crm_done/ambiguous_prior, does not run Retry, does not assert the CRM-question not_sent body.

(4) contract.md: DRAIN_TOTAL_SECONDS not documented (lines 62, 75); person-card text sentence missing (62); line 3 count stale. Pre-existing drift: resolve section (23-28) and HTTP table (99-102) omit crm_present, 409 wrong_decision, 400 bad_decision; line 21 says stuck `sending` needs a restart but a reaper exists.
