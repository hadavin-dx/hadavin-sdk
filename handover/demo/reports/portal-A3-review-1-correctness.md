# A3 review round 1, correctness and tests lens (fresh read-only reviewer; saved by the main session)
Verdict: no Blocker; 3 Major, 5 Nit.
M1 door `form|webhook` (code) vs `web_form|email_message` (spec): defensible (matches stored values, /summary, contract); lead must acknowledge and update spec. Fixtures are builder-authored (self-consistency only).
M2 door, received_at and follow-up state never asserted exactly; mutants (always "form", decided_at as time, state remapped) survive.
M3 `_STORED` hand-written with no drift test.
N4 review/open rows documented as null lead fields but not enforced by code (seed has them null). N5 paging cost of deep pages unproven. N6 test_log_cannot_write weak (redundant). N7 contract: 18-digit cap not stated, wording tight, stored purposes differ slightly from spec example. N8 re-run full suite where gitleaks and the word list exist.
## Resolution (main session, fix pass 1, see portal-A3.md)
M1: NEEDS LEAD (kept form|webhook). M2: FIXED test_log_values_match_the_book; fail-before shown with door mutant. M3: FIXED test_stored_list_names_every_field. N4: contract softened to "filled when the request names a lead". N5: FIXED with index receipts_time_ix (schema.sql, db._VIEW_AND_INDEXES) and test_log_query_uses_the_time_index (fails when the index line is removed). N7: 18 digits stated. N6, N8: N8 stays with the lead (needs gitleaks and the private word list).
Security round: M1 (full sort) FIXED by the same index; M2 (leading zeros, 500) FIXED in _digits (len(raw)), two new cases in test_log_bad_query_is_400 fail on the old check (2 failed, 24 passed shown). N3 contract note added; N4-N7 are page-wording notes for the frontend (hand-off).
