# Promoted controls: defaults table

These modules were promoted from a demo's reviews (core PR #50). All are vendor-neutral and use the standard library, plus `hadavin_sdk.models` (`audit/capped.py` and `runtime/stop_gate.py` use the shared models). `guard/textnorm.py` imports the generated `guard/_confusables.py`: copy both files together.

## `LeakPolicy` (`guard/egress_text.py`): one validated place for every threshold

There is no default policy: `check_text(..., policy=)` is required. `LeakPolicy()` (the table below) equals `LeakPolicy.payments()`, the strict profile. `LeakPolicy.general()` is for replies that carry order ids and phone numbers: `max_digits` 12, `max_total_digits` 22, `max_exempt_digits` 9, `max_dates` 3, `account_min_len` 14; it does not stop a card number sent in pieces, so pair it with protected values.

| Field | Default (`payments()`) | Meaning |
|---|---|---|
| `max_digits` | 8 | plain digit-like characters allowed once set-aside tokens are removed (fewer than this) |
| `max_total_digits` | 14 | the SUM of the plain digit-like characters, the digits of set-aside amounts and references, and 5 per date must stay below this; at most 2 x `max_digits` - 2 |
| `date_years` | (2000, 2099) | years a date may have to be set aside |
| `max_len` | 4096 | text longer than this is refused unscanned (`TEXT_TOO_LONG`); ceiling 100000 |
| `max_exempt_tokens` | 6 | dates, amounts and allowed references that may be set aside |
| `max_exempt_digits` | 7 | digits inside amounts and allowed references; must be below `max_digits` |
| `max_dates` | 2 | valid dates that may be set aside (ISO, day-first and month-first); a date counts 5 digits in the total (it carries about 15 bits) |
| `amounts_need_currency` | True | an amount is set aside only with a currency symbol or code next to it |
| `currencies` | 30 ISO codes | the codes that anchor an amount (configurable) |
| `min_protected_len` | 4 | Latin letters or digits a protected value needs to be matched as a key |
| `min_protected_digits` | 4 | digits from which a protected value is also found "in order, with anything between" |
| `letter_run_min` | 6 | a run of digit-like letters with no real digit counts as digits from this length (a letter-encoded account) |
| `on_short` | "token" | a short or non-Latin protected value: match it in the text ("token"; a Latin value as a word, another script as a substring) or raise ("raise") |
| `account_min_len` | 9 | an alphanumeric token of this length that contains a digit is account-shaped |
| `deny_mixed_script` | True | a word mixing Latin with Cyrillic, Greek, Armenian, Cherokee, Coptic, Georgian, Hebrew, Lisu or similar look-alike-rich scripts is refused (the micro and ohm signs are exempt) |

`LeakPolicy.from_mapping(section)` builds it from a config section and rejects unknown keys.

## Other defaults

| Where | Default |
|---|---|
| `StopGate.engage(timeout=)` | 30.0 seconds |
| `StopGate(cache_ttl=)` | 0.0 (the durable switch is read on every `effect()`) |
| stop/release label | `[A-Za-z0-9_.:@ -]{1,60}`, else "?" |
| `CappedAudit(cap, max_keys=, max_kinds=)` | cap given by the caller; 10000 (tenant, kind) counters and 64 distinct kinds, then a shared overflow counter |
| tenant name and kind in a capped audit | clipped to 64 characters; `%` and `|` in the tenant are escaped in `object_ref` |
| `ConfigHolder.swap(expect=)` | None (no compare-and-set) |
| `freeze` / `thaw` bounds | 64 levels, 1000000 values counted per visit |
| `mutation_runner.run_mutants(timeout=)` | 900 seconds per pytest run |
| `RowStore(max_rows=)` | 100000 rows per store (`None` opts out) |
| `approvals/gate.py` fold bound | 1 000 000 characters |

## The fold rule

`guard.textnorm.fold` makes look-alike text EQUAL. Use it for DENY decisions (separation of duties, blocklists, leak scans). Never use it for an ALLOW decision ("equals the verified address"): `allow_equal(a, b)` is the whole ALLOW decision (`EQUAL` only for identical strings; `LOOKALIKE` is a spoof or variant to refuse and audit; `DIFFERENT` an ordinary mismatch). `names_equal` is tolerant equality for people's names in prose and is never an ALLOW. The look-alike table is generated from Unicode UTS #39 `confusables.txt` (pinned sha256) by `tools/gen_confusables.py`.

## Tracked items (owner: the lead; each has a trigger)

| Item | Why it is not in PR #50 | Trigger / next step | Where it is stated |
|---|---|---|---|
| Per-tenant kill-switch row | `models.KillSwitch` is one global row (schema change); each client deployment has its own database, so a global stop is the right scope today | the first deployment that serves two tenants from one database: add a tenant column, migration, `Limits.stop(by, tenant=)`, a per-tenant `StopGate` key | `runtime/stop_gate.py` docstring, CHANGELOG |
| Outbox, signer, Verifier protocol, reservations | they belong to the signed-approvals work (PR #49) and stage 2; nothing here claims them (only `check_rowstore_contract` exists in `testing/contracts.py`) | PR #49 merge, then contract checks for them | CHANGELOG |
| `guard/redact.py` does not fold | the input mask matches raw text, and its offsets change after NFKD drops marks; a fold-aware mask needs an offset map | design review of "scan folded text, mask by span map"; until then redact detects on folded text and, on a hit, masks the whole token or line (fail closed), and the output check `egress_text` is the backstop | CHANGELOG, `guard/redact.py` |
