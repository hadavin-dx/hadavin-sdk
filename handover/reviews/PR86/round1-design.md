# PR 86 (P6b1) round 1, egm-design, head 8f6b032 (condensed). Read-only.
BLOCKER: no evidence for 8f6b032; all evidence at 9b153d4 (py3.12/3.13 10859 passed; fail-before 124 failed/10 passed; ruff/bandit rc=0; mutants 2 survived). Re-run at head or show 9b153d4..8f6b032 touches no src/tests.
M1 two mutants survived unrecorded: M31 ([0-9] back to \d) and M23b (check reorder) - need hand-written equivalence entry (BN-11) or killing row; test_t4b pins future-before-stale with limit=-5, should have killed a (d)/(e) swap.
M2 README section required by the ticket (plain definition, age checked only at start-up, "does NOT check" list incl `dev` label and host-only binding, BN-5/9/13) not in snapshot - missing deliverable or export gap.
M3 CHANGELOG long lines unchecked (two-host Vertex example, dev label sentence, training sentence, 90-day renewal, BN-5).
Nits: self_hosted on public https loads (honest, tested; README must say code does not check); ceiling==default invariant only via test M28; defaults.py docstring sentence not confirmed; config.py:360-363 ConfigError prints raw base_url (PENDING LEAD 14: check ledger row).
Correct (read): refusal order a,b,c,f,d,e; one message per kind; date validator BN-3; fullmatch patterns; no_training nested; basis sets; BN-16 StrictInt le=90.
