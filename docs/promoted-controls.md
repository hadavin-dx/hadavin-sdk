# Promoted controls: defaults table

These modules were promoted from a demo's reviews (core PR #50). All are vendor-neutral and use the standard library, plus `hadavin_sdk.models` (`audit/capped.py` and `runtime/stop_gate.py` use the shared models). `guard/textnorm.py` imports the generated `guard/_confusables.py`: copy both files together.

## `LeakPolicy` (`guard/egress_text.py`): one validated place for every threshold

There is no default policy: `check_text(..., policy=)` is required, and a config section needs `profile: payments` or `profile: general` (`LeakPolicy.from_mapping`). `LeakPolicy()` (the table below) equals `LeakPolicy.payments()`, the strict profile. `LeakPolicy.general()` is for replies that carry order ids and phone numbers: `max_digits` 12, `max_total_digits` 12, `max_exempt_digits` 8, `max_dates` 2, `account_min_len` 14. **Guarantee, both presets:** fewer than 12 digits in total leave in one reply (plain digit-like characters + digits of set-aside amounts and references + 5 per date), so a card number (13 or more digits) cannot leave split across text, amounts and dates; `max_total_digits` can never exceed 12 (validated); a Luhn scan over the digit stream is kept as an independent card test (it cannot fire through `check_text` while the budgets hold). The price: `general()` refuses any phone number with 12 or more digits (E.164 for India or the UK) unless the caller passes `allowed_patterns`; `payments()` refuses an order id of 8 digits or more. **Letters standing for digits (what the check does and does NOT stop).** Digits in any script, digit-like letters next to digits (`8 O 1 l 5 S`), letter-only runs of 6 or more (`OlISBZGq`), digit-like tokens split by filler letters in a text that holds a real digit (`4 x lllll x lllll`), and padding with weak/strong pairs (`4 Ib Ib Ib ...`) are counted; the count is monotonic (appending a token never lowers it). Ordinary words are free up to the caps (`id is 12345678901`, `Total 12345678901`, `call 5551234567` pass `general()`); a letter glued to a digit (`12345678901s`, `1st`) counts and `general()` refuses an 11-digit id with such a suffix. NOT stopped: a writer who knows the rules can hide digits as single letters inside ordinary-looking words (`xl xl xl`), spell digits as words, use numerals of an unmapped script, or split a digit-free letter number with filler letters. This is a heuristic against copied, formatted or leaked numbers, not a proof against an adversary: anything that must not leave belongs in a structured field. The defaults for `date_years` (2000-2099) and `currencies` (30 ISO codes) are payments-flavoured and `general()` inherits them: set them from config for another domain.

| Field | Default (`payments()`) | Meaning |
|---|---|---|
| `max_digits` | 8 | plain digit-like characters allowed once set-aside tokens are removed (fewer than this) |
| `max_total_digits` | 12 | the SUM of the plain digit-like characters, the digits of set-aside amounts and references, and 5 per date must stay below this; at most 12 (below the shortest card number) and at most 2 x `max_digits` - 2 |
| `date_years` | (2000, 2099) | years a date may have to be set aside |
| `max_len` | 4096 | text longer than this is refused unscanned (`TEXT_TOO_LONG`); ceiling 100000 |
| `max_exempt_tokens` | 6 | dates, amounts and allowed references that may be set aside |
| `max_exempt_digits` | 6 | digits inside amounts and allowed references; must be below `max_digits` |
| `max_dates` | 2 | valid dates that may be set aside (ISO, day-first and month-first); a date counts 5 digits in the total (it carries about 15 bits) |
| `amounts_need_currency` | True | an amount is set aside only with a currency symbol or code next to it |
| `currencies` | 30 ISO codes | the codes that anchor an amount (configurable) |
| `min_protected_len` | 4 | Latin letters or digits a protected value needs to be matched as a key |
| `min_protected_digits` | 4 | digits from which a protected value is also found "in order, with anything between" |
| `letter_run_min` | 6 | a run of digit-like letters with no real digit counts as digits from this length (a letter-encoded account) |
| `max_free_words_run` | 2 | in a run that holds a real digit, the strong letters of this many ordinary words (a token with no digit and 1 to 3 strong letters plus another letter: `call`, `Hello`, `Total`, `is`) are not counted; 0 turns the rule off |
| `max_free_words` | 2 (`general()`: 4) | the same, over the whole text; the leak is bounded because every word past the cap counts |
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
| `mutation_runner.run_mutants(timeout=, baseline_timeout=)` | 900 seconds per pytest run; the baseline run gets `baseline_timeout` (default: `timeout`) |
| `mutation_runner.TREE_KILL_TIMEOUT` | 60 seconds for `taskkill /T` before the child is killed anyway |
| `RowStore(max_rows=)` | 100000 rows per store (`None` opts out; 0, negative, bool, float and text are a ValueError) |
| `approvals/gate.py` fold bound | 1 000 000 characters |

## The fold rule

`guard.textnorm.fold` makes look-alike text EQUAL. Use it for DENY decisions (separation of duties, blocklists, leak scans). Never use it for an ALLOW decision ("equals the verified address"): `allow_equal(a, b)` is the whole ALLOW decision (`EQUAL` only for identical strings; `LOOKALIKE` is a spoof or variant to refuse and audit; `DIFFERENT` an ordinary mismatch). `names_equal` is tolerant equality for people's names in prose and is never an ALLOW. The look-alike table is generated from Unicode UTS #39 `confusables.txt` (pinned sha256) by `tools/gen_confusables.py`.

## Tracked items (owner: the lead; each has a trigger)

| Item | Why it is not in PR #50 | Trigger / next step | Where it is stated |
|---|---|---|---|
| Per-tenant kill-switch row | `models.KillSwitch` is one global row (schema change); each client deployment has its own database, so a global stop is the right scope today | the first deployment that serves two tenants from one database: add a tenant column, migration, `Limits.stop(by, tenant=)`, a per-tenant `StopGate` key | `runtime/stop_gate.py` docstring, CHANGELOG |
| Outbox, signer, Verifier protocol, reservations | they belong to the signed-approvals work (PR #49) and stage 2; nothing here claims them (only `check_rowstore_contract` exists in `testing/contracts.py`) | PR #49 merge, then contract checks for them | CHANGELOG |
| `guard/redact.py` does not fold | the input mask matches raw text, and its offsets change after NFKD drops marks; a fold-aware mask needs an offset map | design review of "scan folded text, mask by span map"; until then redact detects on folded text and, on a hit, masks the whole token or line (fail closed), and the output check `egress_text` is the backstop | CHANGELOG, `guard/redact.py` |

## Behaviours worth knowing

- `StopGate.release` can write the durable stop twice when an `engage` interleaves with it (the engage writes it, then the release sees the changed generation and writes it again); both writes are audited and `StopGateBusy.durable` says whether the second one succeeded.
- `EngageResult` for a call that found a sweep already running has `already_sweeping=True`, `durable=None`, `complete=False` (nothing was undone by that call).
- `has_mixed_script` flags Greek letters beside Latin ones (a delta or theta symbol glued to Latin letters is a false positive) and uses a curated script list, not the UTS #39 script-extension data; see its docstring.
- The look-alike table is generated and checked on Unicode 15.1.0 (Python 3.13, the version CI runs: `python-version: "3.13"`). On Python 3.12 (Unicode 15.0) or 3.14+ the table is the same, but the regeneration test is skipped and the fold drops code points the interpreter calls unassigned (Cn), so a letter assigned only in a later Unicode version is dropped instead of mapped.

## Copying a core file into a demo (rows for `core_copies.json`)

A demo that keeps a byte copy lists one row per file; `core_pr` is 50 until it merges, then the copy is dropped for the pin.

```json
{"core_path": "src/hadavin_sdk/guard/textnorm.py",   "core_sha256": "<tests/fixtures/textnorm_manifest.json>", "core_pr": 50,
 "import_rewrite": [["hadavin_sdk.guard._confusables", "<demo package>.guard._confusables"]]}
{"core_path": "src/hadavin_sdk/guard/_confusables.py", "core_sha256": "<manifest>", "core_pr": 50, "import_rewrite": []}
{"core_path": "src/hadavin_sdk/guard/egress_text.py", "core_sha256": "<manifest>", "core_pr": 50,
 "import_rewrite": [["hadavin_sdk.guard.textnorm", "<demo package>.guard.textnorm"]]}
{"core_path": "src/hadavin_sdk/runtime/stop_gate.py", "core_sha256": "<manifest>", "core_pr": 50,
 "import_rewrite": [["hadavin_sdk.models", "<demo package>.models"]]}
{"core_path": "tests/fixtures/textnorm_vectors.json", "core_sha256": "<manifest>", "core_pr": 50, "import_rewrite": []}
```

The generator pin test (`tools/gen_confusables.py`, `tools/data/confusables.txt`) stays in core: a demo cannot run it. `stop_gate.py` needs core's `limits.py` with `Limits.stop/reset(by, source)` and `Limits.is_stopped()` (copy it together or pin core at PR #50 or later); `StopGate` raises `TypeError` at construction otherwise. `tools/mutation_runner.py` is a developer tool outside the wheel: copy it like any other file. Hashes of the five pinned files: `tests/fixtures/textnorm_manifest.json`.
