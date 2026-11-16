# PR 86 (P6b1) round 1, egm-codebase-details, head 8f6b032 (condensed). Ran nothing.
No Blocker. 1 Major, 4 Nits. Code matches ticket and BN-1..18.
M1 README.md not changed (no README hunk in DIFF.patch); CHANGELOG entry omits stated limits: detector bedrock_guardrail not covered (PENDING LEAD 4), Gemini key-tier limit, ASCII host <=253 chars (BN-4), loopback self_hosted needs tagged model id (BN-13), reference is guidance only (BN-9).
N1 diff carries P4a/P4d/stop-state/labelkey/store changes and pilot_cfg adds stop_credential_ref and limits: confirm PR base (stacked). N2 NO_TRAINING_MAX_AGE_CEILING duplicates default 90: derive one from the other. N3 trailing-dot host never matches (fails closed; document). N4 test reaches private _iso_date_or_none (loud failure on rename).
Evidence is for 9b153d4 not 8f6b032 (same blocker as design review).
Held: refusal order, validators, fail-closed Entry, reuse, fail-before rows real.
