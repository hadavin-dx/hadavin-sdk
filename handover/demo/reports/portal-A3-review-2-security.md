# A3 security review, round 2 (egm-codebase-details, snapshot portal-A3-r2)

Saved by the cloud session from the reviewer's inline report. Reviewer had no shell: ran no tests, no EXPLAIN. Could not read desk.py, contract.py, loader.py, portal html/js, test_portal_api.py helpers.

Verdict: no Blocker. 3 Major, 5 Nit. Both round-1 Majors fixed for correctness; index fix weaker than it looks.

## Major
- M1. Log query is not a keyset seek. Predicate `(:first = 1 OR received_at < :at OR (received_at = :at AND receipt_id < :id))` is not indexable, so a deep page walks ~N index entries; `SELECT count(*) FROM receipts` walks the whole tree each page. Eight deep-cursor requests can hold all 8 in-flight slots (503 busy for the real UI). Test only checks the text `receipts_time_ix` and no TEMP B-TREE, so SCAN passes. Ask: row-value comparison or explicit seek, assert SEARCH, deep-cursor timing case, decide whether `total` must be exact per page.
- M2. `portal_read_only: true` misleads: it only means the /api/ui read connection is mode=ro; the portal also offers POST retry/resolve and /api/demo. Ask: rename/qualify the field and fix spec wording.
- M3. `never_receives` overstates: it checks parameter names only, not the call site in desk.py, and a live step can look up name/phone/company/message with lead_id. Ask: caveat/rename in payload or a call-site test; frontend says "is given", never "cannot read".

## Nit
- N1. No loopback flag in `access`; host_check/origin_check hard-coded true; gate only blocks browsers.
- N2. 500 refusal not distinguishable; server logs class name only; `mode` is a self-declaration.
- N3. `stored` list has no drift test beyond lead columns (last_error, outcome_reason, differing_fields, email_key, crm_done unlisted).
- N4. Caller text (request_id, lead_name) shown as sent; no PII canary in source_ref; frontend must use textContent; "hide personal details" must not claim to cover them.
- N5. spec.md 1.2 still says web_form|email_message; negative received_at gives cursor `-5:3` rejected next page; data-map takes an in-flight slot; thread count unbounded outside the 8-slot cap (pre-existing).

## Checked clean (reviewer)
Leading-zero fix; index added and migrated; gate order, Host/Origin/Sec-Fetch-Site rules; cursor strictness and keyset ties; bound SQL; selected columns carry no email/phone/company/message; read connection and snapshot; error bodies; limits 1..200.
