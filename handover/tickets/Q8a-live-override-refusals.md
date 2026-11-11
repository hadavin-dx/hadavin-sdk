# Ticket Q8a: refuse test-only override objects in pilot and prod, and close two lock-in guard gaps (source: reviews/Q8/deps-audit.md F1, F5, F6, F8, F11)
Branch: NEW `core/q8a-live-override-refusals` from origin/main. Draft PR against main. Security path (least privilege): review rounds uncapped.

## Rung table (CODE-LAST, R447/R448/R450)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| refusal of override objects when live | a pilot/prod process must not run with a fake secrets provider, fake channel, recorded model or swapped detector | rung 1 reuse: the existing live refusals for sources=/tools= in app.build (app.py 90-98, read 2026-11-11) | same choke point exists | least-privilege guarantee inside our own build() | KEEP-CODE (about 10 lines + tests) |
| Vault static token refused when live | no long-lived credential in a live process | rung 1 reuse: config cross-checks already refuse `env` secrets when live (config.py 394-397) | same validator | same guarantee | KEEP-CODE (validator rule + tests) |
| neutral approval callback path | a second channel kind must not inherit a Slack-named route | rung 1: rename in our own receiver; no tool does this | approvals/receiver.py:18,22 (read 2026-11-11) | n/a | KEEP-CODE (rename + compatibility alias) |
| guard coverage | lock-in guard must see vendor names as path segments and the second registry | rung 1: extend tests/test_lockin_guard.py | file read by reviewer | n/a | KEEP-CODE (test only) |

## Behaviour
1. `app.build()`: when the stage is pilot or prod, passing `secrets=`, `channel=`, `detector=` or `llm=` as an object raises `ConfigError` with the same message shape as the existing `sources=`/`tools=` refusals ("<name>= is for tests; configure backends.<capability> in pilot and prod"). Demo stage unchanged. Existing tests that pass such objects to a live build (for example tests/test_stage_names.py around 313-317) are updated to reach their intended error another way, never deleted or weakened; list each changed test with the reason.
2. Config validator: `auth: token` for the Vault secrets kind and the `vault_transit` signer is refused in pilot and prod, naming the allowed kinds (`kubernetes`, `approle`); demo unchanged. If a live deployment path in docs/tests relies on token auth, say so in the report before changing it.
3. `approvals/receiver.py`: neutral names (`PATH = "/channel/actions"`, `handle_action`), with the path taken from the channel object where one is defined; keep `/slack/actions` and `handle_slack_action` working as documented aliases owned by the Slack channel module so no caller breaks; move `post_json` use to a neutral HTTP helper only if it is a pure move (else leave and record).
4. tests/test_lockin_guard.py: the vendor-name pattern also catches a vendor name as a path segment or identifier part in neutral modules; `sources.kinds.KINDS` joins the coverage check with an EXCEPTIONS entry (trigger K5-ITO, review_by date); an EXCEPTIONS trigger equal to "none" is refused, and the audit entry gets a real named trigger.
## Out of scope (separate tickets, logged in ledger): F2 role split, F3 policy texts per cloud kind, F4 approver step-up (owner decision), F7, F9 (owner decision), F10.
## Tests (each must fail on origin/main; paste the proof)
- one negative test per override (4) x pilot and prod; demo still accepts; message names the capability.
- Vault token refused when live (both kinds), accepted in demo.
- receiver: neutral path works; alias works; guard test fails if a vendor path segment is added to a neutral module (meta test with a planted string in a temp copy).
- guard: "none" trigger refused; sources registry covered.
## Gates: full pytest, ruff check, ruff format --check, bandit -ll, guard tests. Evidence by a separate EVIDENCE RUNNER; result review by egm:* agents.
