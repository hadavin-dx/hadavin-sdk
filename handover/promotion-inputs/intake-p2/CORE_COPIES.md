# Core copies and local re-implementations (promotion table)

Rule (one source of truth): a generic module lives in the core SDK. Until a core PR merges and this demo is re-pinned, a TEMPORARY byte copy may sit here, listed below and pinned by hash in `core_copies.json`; it never diverges silently (`tests/test_review6.py::test_core_copies_json_pins_every_copied_file_and_lists_every_local_generic` and the studio tool `tools\core_sync_check.py`, run with `--core <core checkout or snapshot holding the PR files> --demo demos/intake`). The demo has no `hadavin_sdk` dependency at stage 1 (stdlib only); the core pin for stage 2 is `6608146` (`pyproject.toml` comment).

The text-fold copies come from the CURRENT head of open core PR #50 at `855b4e0` and are **awaiting core PR #50**. If the PR moves, the re-sync is a later step: copy the new head, update `core_sha256` and `pr_snapshot`, run the tool and the tests.

## 1. Temporary copies (TEMPORARY: delete after the core PR merges and the demo is re-pinned)
| Demo file | Core file | Core PR | Import rewrite | Switch-over |
|---|---|---|---|---|
| `src/intake/core_copy/textnorm.py` | `hadavin_sdk/guard/textnorm.py` | #50 (awaiting core PR #50) | `hadavin_sdk.guard._confusables` -> `intake.core_copy._confusables` | import `hadavin_sdk.guard.textnorm` in `src/intake/textfold.py` after #50 merges and the pin moves; delete `core_copy/` |
| `src/intake/core_copy/_confusables.py` | `hadavin_sdk/guard/_confusables.py` | #50 (awaiting core PR #50) | none (byte copy; UTS #39 generated table, Unicode License v3 notice inside) | with `textnorm.py` |
| `src/intake/safe_text.py` | `demos/ask-your-data/askdata/safe_text.py` (core main `6608146`) | none (already in core main as a demo module) | none (byte copy; the two "vendored" comment lines were removed so the file is byte-identical, provenance lives here) | promote `clean` / `is_forbidden` to a core kind module (`guard/safe_text.py`), then import it; until then never edit this file, change the core file and re-copy |
| `src/intake/core_copy/redact.py` | `hadavin_sdk/guard/redact.py` (core main `ce70eb5`) | #42 (merged) | none (byte copy, LF) | import `hadavin_sdk.guard.redact` in `src/intake/coreredact.py` after the demo pin passes `ce70eb5`; delete the copy |

API used from the copies: `fold` (via `src/intake/textfold.py:fold_text`, same signature as core: `fold(raw, *, casefold=False, collapse_ws=False)`), used by `egress.check_egress` as a DENY scan (look-alike letters in a host or link become Latin before the host and link patterns run). It is never used to decide that an address IS the verified one: that comparison stays exact (`recipient.lower() == verified_sender.lower()` and ASCII-only).

## 2. Local implementations of concerns the core also owns (not copies; each is a promotion candidate; `allowed_local` in `core_copies.json` carries the reason and an expiry)
| Local concern | Local module | Core owner | Trigger to switch | Status |
|---|---|---|---|---|
| Text-fold seam | `src/intake/textfold.py` | core `guard/textnorm.py` (#50) | #50 merged and pin moved | local seam, no logic |
| Strict JSON (the copy refuses NaN, Infinity and duplicate keys; it has no depth cap or surrogate check: the seam adds both) | `src/intake/core_copy/strict_json.py` | the studio portal kit, `hadavin_kit/strict_json.py` at kit commit `87b4cd18f4df914e6d338d39a201a5da06f804f0`, sha256 `983c26f73cdc9f4bc3e1c8a92a152ddae99c3d4cd20663ff90918f57feef8fd6` (byte copy; not a core SDK file, so not pinned in `files`) | the kit or core becomes a declared dependency | local copy until then; expires 2027-01-31 |
| Core redactor seam | `src/intake/coreredact.py` | core `guard/redact.py` (#42, merged at `ce70eb5`; our copy `src/intake/core_copy/redact.py`) | the demo pin passes `ce70eb5` | local seam, no logic |
| Invoice masking (hide sensitive values before the AI service, put them back after) | `src/intake/mask.py` | core run-map module (`guard/runmap.py`) | a promoted invoice-neutral masking kind | local; promotion candidate; expires 2027-01-31 |
| Strict JSON seam | `src/intake/strictjson.py` | same | same | the one place `src/intake` parses JSON (a test fails on any other `json.loads`); adds a depth cap |
| Egress policy for links, hosts, addresses, recipient | `src/intake/egress.py` | core `guard/reply_check.py` (#49) and `guard/egress_text.py` (#50) | #49 merged, then a differential test of the three variants | local (tokens now match EXACT hosts, addresses and address parts, not substrings) |
| Live-run gate | `src/intake/rules.py` `live_run_allowed` | none yet; two sibling demos have the same semantics | a core `runtime/livegate.py` | local; checks `allowed` is true, `training_use` is false, the setting, region and quoted yes are text, the check date is a real ISO date, not in the future and not older than `setting_max_age_days` |
| Inbound ledger | `src/intake/adapters/fake_ledger.py` | none yet (core has only a `DeadLetter` model) | a core `runtime/inbox.py` | local (see section 3) |
| Kill switch, write caps | `src/intake/executor.py` | core `runtime/stop_gate.py` (#50) | core per-tenant stop | local |
| Namespace and few-shot ownership | `src/intake/isolation.py` | none | tenant-scoped store kind | local |
| Order and invoice checks | `src/intake/checks.py` | none (domain rules) | none | local, listed so the sync tool does not read the name as a core module |
| Mutation runner | `tools/mutate_src.py` | core `testing/mutation.py` (#50, judge only) | a promoted runner | local; KILLED means an assertion failed, CRASH (import error, other exception, timeout, no tests) is reported apart and never counted as a kill |
| Look-alike letters for the bank-detail scan | `src/intake/confusables_data.py` | core `guard/_confusables.py` (#50; our copy `src/intake/core_copy/_confusables.py`) | core offers the single-character ASCII filter | generated by `tools/gen_confusables_wp3.py` from the same UTS #39 file (sha256 pinned, Unicode License v3 notice in the module); `test_core_copy_agrees_on_overlapping_confusables` lists the differences |
| Invoice and bank-detail checks | `src/intake/invoicecheck.py` | none (domain rules) | none | local |

## 3. Behaviour differences from the other demos (recorded, with the reason)
- **Message-id reuse (same id, different body).** Intake ends the new receipt as `dead_lettered` with an alert (`message_id_conflict`, link to the first receipt via `conflict_of`); a sibling demo records it as `rejected` (`id_reuse`); another sibling uses `rejected:<reason>`. Intake keeps `dead_lettered` because in this pipeline `rejected` is a clean refusal by a rule (the sender is told why) while a reused id with different content is a possible spoof or an upstream bug that a person must look at: dead letters go to the clerk queue and raise an alert, a rejection does not. The invariant all three share (nothing lost, nothing applied twice, the first receipt untouched) is tested here by `tests/test_inbound_isolation.py` (lines about `message_id_conflict`). When core gets an inbox kind (`runtime/inbox.py`) the three outcomes are folded into one rule and this note is deleted.
- **PO key.** `normalise_po("PO-48211") == "P48211"` is the specified fold (R-INTAKE-017: O reads as 0, a leading 0 of a digit run is stripped), pinned by `tests/test_review6.py`.
