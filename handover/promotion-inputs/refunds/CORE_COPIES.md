# Core copies and the promotion table (refunds demo)

Rule (one source of truth): a generic piece lives in `hadavin-dx/hadavin-sdk`; a demo may hold a TEMPORARY copy until its core pin moves,
and the copy is listed here with the step that deletes it. Today **no promoted module is in the pinned core**: `pyproject.toml` and `gate_rules.md` pin
`hadavin-sdk` at `660814674ece8ad578293e5412633d796eddb96f`, which holds none of them. They are in core PR 49 (refunds fixes, branch `core/promote-refunds-r8`) and
core PR 50 (text fold, branch `core/promote-apexc-review8`), both open and unmerged. PR 49 has not been through an independent result review yet; read this table as
a plan, not as a claim that core already has them. `tools\core_sync_check.py` reads `core_copies.json` (copies with hashes, `allowed_local` with a reason and expiry per local item); run it with `--core <core checkout or PR snapshot> --demo demos/refunds`.

## 1 Verbatim copies (pinned; stop-gap, awaiting core PR 50)
| Core file | Demo copy | Core PR | Pin | Switch-over step |
|---|---|---|---|---|
| `src/hadavin_sdk/guard/textnorm.py` | `src/refunds/core_copy/textnorm.py` (one import line rewritten: `hadavin_sdk.guard._confusables` -> `refunds.core_copy._confusables`) | PR 50 (snapshot 153d217) | `core_copies.json` (`core_sha256`, LF, import rewrite reversed before hashing; `tests/test_review11.py` and `tools\core_sync_check.py` fail on any edit) | Import `hadavin_sdk.guard.textnorm` in `src/refunds/textnorm.py` (the only importer) and delete the copy when the pin moves past the PR 50 merge. |
| `src/hadavin_sdk/guard/_confusables.py` (UTS #39 generated table) | `src/refunds/core_copy/_confusables.py` | PR 50 (snapshot 153d217) | same | with `textnorm.py` |

Interface: only `src/refunds/textnorm.py` imports the copy and exposes `skeleton`, `mixed_script` and the look-alike-aware `contains_marker`; `approval.py` calls `skeleton` and `writegate.py` calls `mixed_script` (`contains_marker` has no runtime caller; it is tested and meant for the stage-2 scorer), so the switch is one import line. The earlier copy (PR 50 commit 3224f3d, curated table) is replaced by the generated-table version.

## 2 Demo implementations that core will replace (not verbatim; behaviour differs where stated)
| Demo file | Generic or demo-only | Core module (PR) | Difference today | Switch-over step | Test that carries over |
|---|---|---|---|---|---|
| `src/refunds/textnorm.py` (`normalise`, `text_ok`, `normalise_keep_case`, `skeleton`, `mixed_script`, `contains_marker`) | generic | `guard/textnorm.py` (PR 50) + `guard/identity_text.py` (PR 49) | demo `normalise` (the stored form) has no look-alike table by design; `skeleton`, `mixed_script` and `contains_marker` use the core copy above | `approval.norm`/`_text_ok` call `identity_text.exact_key/identity_key`; delete this file | `tests/test_review8.py` look-alike rows, `tests/test_review11.py` |
| `src/refunds/guards.py` (`egress_check`) | generic (reply text) | `guard/reply_check.py` (PR 49) | demo keeps the old names (`RECIPIENT_NOT_VERIFIED_CUSTOMER`); no `allowed_patterns`; recipient compare is the demo's | adapt callers to `reply_violations`; delete `egress_check` | `tests/test_purpose_blast_radius.py`, `tests/test_review8.py`, `tests/test_review11.py` (spaced dots) |
| `src/refunds/guards.py` (`RateCap`, `ReadLog`) | generic | (not yet promoted; PR 50 has capped audit) | none in core; `RateCap` is locked (same code as dealdesk) | promote one locked `RateCap` and a generic `ReadLog` to core | `tests/test_purpose_blast_radius.py`, `tests/test_review12.py` (thread race) |
| `src/refunds/signers.py`, `src/refunds/approval.py` (signing, verifier, one-use) | generic | `approvals/signed.py` on `audit.signer` kinds (PR 49) | demo has an HMAC dev kind and a `Verifier.kind` label; core signs `key_id` and verifies tenant/hash/age/single-use itself | use `signed.ApprovalVerifier`; keep the demo SoD checks | `tests/test_review8.py` signer rows |
| `src/refunds/store.py` (`reserve`, `open_state`, `release`, `sweep_reservations`, `void_key`) | reserve generic, rest demo | `Store.reserve/release_reservation/list_reservations/prune_reservations` + `store/reservations.py` (PR 49) | signature differs: demo `reserve(tenant, key, customer_id, order_id, amount, currency, at, *, cluster, sender)`, code `PENDING_CAP`; core `reserve(Reservation, ReservationLimits, since, request=None)`, code `OPEN_LIMIT`; core has no tombstone | call through `src/refunds/core_seam.py` today; replace the body by the core store at the pin move; `void_key` stays demo-side until a core tombstone exists | `tests/test_review8.py` flood rows; `tests/contracts` in core |
| `src/refunds/core_seam.py` | demo-only seam | none | accepts the core argument shape and returns core codes; refuses limits that differ from config | delete with the demo store's `reserve` | `tests/test_review11.py` |
| `src/refunds/writegate.py` (refusal audit rows) | generic shape | `audit/refusal.py` (PR 49) | demo allow-lists labels itself | use `refusal_fields` | `tests/test_review8.py` audit rows |
| R-REF-024 placement (writegate docstring) | generic | `actions/outbox.py` (PR 49) | the demo writes intent and applied in one transaction; a processor build must use the core outbox (attempt rows, compare-and-set settle, IN_DOUBT) so two executors cannot both call the processor for one key | adopt when a processor exists | none yet |
| `src/refunds/hashing.py`, `identity.py`, `money.py` | demo-only (refund business rules) | none | none | stay | n/a |

## 3 Order of the switch
PR 50 merges (textnorm) -> PR 49 merges (store, reply_check, signed approvals, outbox) -> the core pin is bumped in `pyproject.toml` and `gate_rules.md` -> delete section 1 and the
section 2 rows in the order above, one commit each, tests green after each -> run `tools\core_sync_check.py` and empty `allowed_local`.
