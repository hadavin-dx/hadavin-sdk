# Core copies and local re-implementations (promotion table)

Rule (one source of truth): a generic module lives in the core SDK. Until a core PR merges and this demo is re-pinned, a TEMPORARY byte copy may sit here, listed below and pinned by hash in `core_copies.json`; it never diverges silently (`tests/test_review1_newapi.py::test_core_copies_json_pins_match_the_copied_files_after_reversing_the_import_rewrite` and the studio tool `tools\core_sync_check.py`, default EOL normalisation, run with `--core <scratch core holding the PR files> --demo demos/dealdesk`). The demo's own pin is core `6608146` (`pyproject.toml`, test group, contract tests only).

The copies come from the CURRENT heads of the two open core PRs: #50 at `153d217` (textnorm, _confusables and egress_text re-synced from `e81c44b`; the byte source is the core repository at that PR head) and #49 at `cd62212` (`approvals/signed.py` is NOT in #50; it comes only from #49). If either PR moves, the re-sync is a later step: copy the new head, update `core_sha256` and `pr_snapshot`, run the tool and the tests.

## 1. Temporary copies (TEMPORARY: delete after the core PR merges and the demo is re-pinned)
| Demo file | Core file | Core PR | Import rewrite | Switch-over |
|---|---|---|---|---|
| `src/dealdesk/core_copy/textnorm.py` | `hadavin_sdk/guard/textnorm.py` | #50 | `hadavin_sdk.guard._confusables` -> `dealdesk.core_copy._confusables` | import `hadavin_sdk.guard.textnorm` after #50 merges and the pin moves; `src/dealdesk/textnorm.py` keeps the demo-specific views |
| `src/dealdesk/core_copy/_confusables.py` | `hadavin_sdk/guard/_confusables.py` | #50 | none (byte copy) | with `textnorm.py` |
| `src/dealdesk/core_copy/egress_text.py` | `hadavin_sdk/guard/egress_text.py` | #50 | `hadavin_sdk.guard.textnorm` -> `dealdesk.core_copy.textnorm` | with `textnorm.py`; used for the rep-reply leak check (`LeakPolicy.payments()`) |
| `src/dealdesk/core_copy/approvals_signed.py` | `hadavin_sdk/approvals/signed.py` | #49 | `hadavin_sdk.audit.signer` -> `dealdesk.signing`, `hadavin_sdk.errors` -> `dealdesk.errors` | import core after #49 merges; `signing.py` then becomes core `audit/signer.py` (#48) |

Core API used from the copies: `fold_key` / `same_person` family (`fold_key` for the mailbox key; `AllowVerdict` has EQUAL, VARIANT, LOOKALIKE, DIFFERENT and is a plain Enum with no truth value), `fold`, `allow_equal` (recipient ALLOW decision), `names_equal` (same-name account collision), `has_mixed_script` (account-name spoof), `LeakPolicy.payments()` and `check_text` (rep replies), `ApprovalVerifier` and `Schema` (signed approvals).

## 2. Local implementations of concerns the core also owns (not copies; each is a promotion candidate)
| Local concern | Local module | Core owner | Trigger to switch | Status |
|---|---|---|---|---|
| Ed25519 signer / verify kind | `signing.py` (the only `cryptography` import) | core `audit/signer.py` (#48) | #48 merged and pin moved | local interface-compatible stand-in |
| Egress policy for links, domains, addresses, bank patterns, recipient | `guards.py` `egress_check` | core `guard/egress.py` and `guard/reply_check.py` | core versions merged; this check is link/recipient policy, the core digit-budget check is used beside it | local, wired in `draft_quote` and `send_reply` |
| Rate cap, read log | `guards.py` `RateCap`, `ReadLog` | core `runtime/control.py` (#50) | #50 merged | local, wired in `Inbox.receive` and `ReadOnlyPorts` |
| Stop gate / kill switch | `desk.py` `set_kill_switch`, `_kill_on`, the executor | core `runtime/stop_gate.py` (#50) and `limits.py` | #50 merged; the core gate adds an in-flight count and a generation counter, this one is a per-tenant store record read under the act's lock, unreadable means ON | local |
| Audit hash chain | `store.py` `AuditChain` | core `audit/capped.py` (#50) | #50 merged | local |
| Tenant-scoped row store | `store.py` `TenantStore` | core `runtime/rowstore.py` (#50) | #50 merged | local |
| Person identity for separation of duties | `desk.py` `_mail_key`, employee and person ids | core `guard/textnorm.py` `same_person` / `fold_key` (#50 at 153d217) | `_mail_key` uses `fold_key` (same key as `same_person`) and additionally removes the plus tag; switch to `same_person` once the plus-tag rule is a core option | local, over the core `fold_key` |
| Idempotency keys | `canon.py` `idem_key` | frozen contract key `hash(action, business id, amount, currency, reason id)` | our key is `[action, deal, quote or terms hash, lane, epoch]`: the hash already covers amount and currency; deviation recorded here and in README | deviation |
| Caps, budgets | `desk.py`, `executor.py` | core `limits.py`, `actions/executor.py` | executor kind promoted to core with the same re-check hook | local |
| Identity table | `identities.py` | core identity / actions authorizer | convention in one process; a client build maps it to the IdP and cloud IAM | local |
| Inbound ledger | `inbox.py` | core `store/` + `actions/outbox.py` | when a core inbox kind exists | local |
