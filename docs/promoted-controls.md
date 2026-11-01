# Promoted controls: defaults table

These modules were promoted from a demo's reviews (core PR #50). All are vendor-neutral and use the standard library, plus `hadavin_sdk.models` (`audit/capped.py` and `runtime/stop_gate.py` use the shared models).

## `LeakPolicy` (`guard/egress_text.py`): one validated place for every threshold

| Field | Default | Meaning |
|---|---|---|
| `max_digits` | 8 | digit-like characters allowed in the text once set-aside tokens are removed (fewer than this) |
| `date_years` | (2000, 2099) | years a date may have to be set aside |
| `max_len` | 4096 | text longer than this is refused unscanned (`TEXT_TOO_LONG`); ceiling 100000 |
| `max_exempt_tokens` | 6 | dates, amounts and allowed references that may be set aside |
| `max_exempt_digits` | 10 | digits inside amounts and allowed references; at most 3 x `max_digits` |
| `max_dates` | 3 | valid dates that may be set aside (ISO, day-first and month-first) |
| `amounts_need_currency` | True | an amount is set aside only with a currency symbol or code next to it |
| `currencies` | 30 ISO codes | the codes that anchor an amount (configurable) |
| `min_protected_len` | 4 | Latin letters or digits a protected value needs to be matched as a key |
| `min_protected_digits` | 4 | digits from which a protected value is also found "in order, with anything between" |
| `letter_run_min` | 6 | a run of digit-like letters with no real digit counts as digits from this length (a letter-encoded account) |
| `on_short` | "token" | a short or non-Latin protected value: match it as a whole word ("token") or raise ("raise") |
| `account_min_len` | 9 | an alphanumeric token of this length that contains a digit is account-shaped |
| `deny_mixed_script` | True | a word mixing Latin with Cyrillic, Greek, Armenian, Cherokee or Coptic letters is refused |

`LeakPolicy.from_mapping(section)` builds it from a config section and rejects unknown keys.

## Other defaults

| Where | Default |
|---|---|
| `StopGate.engage(timeout=)` | 30.0 seconds |
| `StopGate(cache_ttl=)` | 0.0 (the durable switch is read on every `effect()`) |
| stop/release label | `[A-Za-z0-9_.:@ -]{1,60}`, else "?" |
| `CappedAudit(cap, max_keys=)` | cap given by the caller; 10000 (tenant, kind) counters, then a shared overflow counter |
| tenant name in a capped audit | clipped to 64 characters |
| `ConfigHolder.swap(expect=)` | None (no compare-and-set) |
| `freeze` depth | 64 levels |
| `RowStore(max_rows=)` | None (unbounded) |
| `approvals/gate.py` fold bound | 1 000 000 characters |

## The fold rule

`guard.textnorm.fold` makes look-alike text EQUAL. Use it for DENY decisions (separation of duties, blocklists, leak scans). Never use it for an ALLOW decision ("equals the verified address"): use `safe_equal` and refuse when `confusable_not_equal` is True.
