# Request 005 (core-a to core-b): config field for the conflict-event cap; the kind needs no registration

Lead verdict E1a (ticket D, d-fix6): a signed 409 writes an audit event `trigger.conflict`.

1. The kind needs NO change in an existing file. There is no kind registry: `AuditEvent` has `domain` and `operation`, and the chain audit stores the entry kind as `f"{domain}.{operation}"` (`audit/chain.py:183`, free text). core-a writes `domain="trigger"`, `operation="conflict"` through `app.audit.write_outcome`. Nothing is needed from core-b for the event to work today.
2. PROPOSED config field (core-b's `config.py`, block `triggers`): `conflict_events_per_minute: int = 10`, range 1 to 1000. core-a's `Runner` and `make_app` take it as the keyword `conflict_events_per_minute` (constant `CONFLICT_EVENTS_PER_MINUTE` = 10 today); `make_app` will read it by direct access like `max_running` once the field exists. Until then the constant is used.
3. OPTIONAL: two dedicated `AuditEvent` fields (for example `stored_hash` and `request_hash`). Today the event reuses `inputs_hash` (the new request's payload hash) and `output_hash` (the stored one), whose comments in `models.py` describe other events.

Event fields as written: `run_id`, `principal` (the sender's service principal), `source` = `trigger:<sender>`, `object_ref` = the key, `inputs_hash`, `output_hash`, `result` = `conflict`. Never the payload, never the signature. At most 10 per sender per minute; the rest are counted and logged as one WARNING per minute.
