# A3 review round 1, security lens (fresh read-only reviewer, snapshot portal-A3-r1)
Verdict: no Blocker; 2 Major, 5 Nit. (saved by the main session from the reviewer's inline report)
M1 `_LOG_ROWS` (portal_api.py ~643): ORDER BY received_at DESC, receipt_id DESC with an OR keyset predicate; no index on (received_at, receipt_id) in schema.sql (only a partial index on open receipts), so each page may sort the whole book; `count(*)` is O(n). Asked: EXPLAIN QUERY PLAN or row-value comparison. Unverified by the reviewer (schema not in snapshot).
M2 `_digits` (portal_api.py ~118): len(raw.lstrip("0")) > MAX_DIGITS lets 5000+ leading zeros through; int() then hits CPython's 4300-digit limit, ValueError, 500 internal instead of 400 (also affects /leads limit/offset). Fix: check len(raw).
N3 request_id and lead_name are caller text (could hold an email); say so in contract; canary test does not cover source_ref with PII.
N4 data-map `receives` covers the signature only, not what desk.py passes or what a live qualifier looks up with lead_id; wording must say "is given", never "cannot read".
N5 `request_payload` in `stored` is honest; page should show it prominently.
N6 `access.bind` has no loopback flag; page text "this computer only" must depend on bind.
N7 data-map refusal is a 500; frontend needs a refusal state. `mode` is a self-declaration of the qualifier class.
Checked clean: bound parameters only; cursor/limit grammar; limit 1..200; one read transaction (6 statements); no email/phone/company/message/payload selected; unmapped values masked; flags tested against real behaviour; hygiene.
