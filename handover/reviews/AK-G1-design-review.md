# AK-G1 turn-flow design: EGM review (step 3), two fresh reviewers

Target: `designs/ak-g1/AK-G1-turn-flow-design.md` (476 lines) with `tickets/AK-G1.md` BN-1..28 and the lead answers PL11-16.
Reviewers: adversarial (egm-design, ids DES-ADV) and correctness (egm-codebase-details, ids DES-COR). Both read-only, nothing was run. Saved by the lead's cloud worker from the hand-back text, condensed to one line per finding (problem, then fix). Verdicts: ADV 0 Blocker, 5 Major, 9 Minor, 2 Nit; COR 0 Blocker, 4 Major, 8 Minor, 3 Nit.

## Adversarial (DES-ADV)
| id | sev | where | problem | fix |
|---|---|---|---|---|
| DES-ADV-1 | Major | OP-1, finish_turn rule 1, takeover, I-4 | OP-1's fix is incomplete: `finish_turn` checks only busy_run_id; a slow run can commit `open` between the item and the takeover, so the takeover (which skips the liveness check) misses it and I-4 breaks; the other way, a really alive run is taken over after it already delivered its answer | fence first: sweep/F7 move the lost run to a final state by CAS (RECEIVED/WORKING -> NEEDS_PERSON "interrupted"); `finish_turn` reads the busy run row and raises LeaseLost if final; takeover needs no liveness skip; test finish_turn landing between item and takeover |
| DES-ADV-2 | Major | E4 + crash rule, OP-3 | unknown commit outcome: if `finish_turn` raises on a lost COMMIT ack, the row may have committed; crash rule then says with_person but the chat stays open | after an E4 exception allow ONE read (answer slot at turn_no); filled = committed, use OP-3 mapping; else crash rule |
| DES-ADV-3 | Major | claim step 6, forget_user 3, purge | erasure finds run maps only via run ids named in deleted turns; the user turn need not carry run_id (Interface 3 allows None); a crashed untaken-over exchange leaves a redaction_maps row orphaned until the 400-day ceiling (breaks PL15/R98) | claim sets run_id on the user turn; A22 case crash then forget_user; delete helper also takes run ids from runs.trigger_ref for the tenant |
| DES-ADV-4 | Major | F4/F5, record_user_turn 3 | F5 saves `mapping=_keep(rmap)` for every message in a handed-off chat; map grows up to 2000 entries per message, original values (PII) at rest, forever | do not persist new map entries after hand-off; write old mapping unchanged (or refuse message_too_complex when full) |
| DES-ADV-5 | Major | money card OP-4, E2b | card hook recommended between E2 and E4, inside the crash window; unenforced 30 s hook widens it; no rate bound on repeated overshoot | post the card after E4/E6; dedupe key run id; note the pause bounds the flood |
| DES-ADV-6 | Minor | words, record_user_turn 3, claim 5 | "user turns odd, answers even" false after hand-off | role from the column, never parity; test list_turns |
| DES-ADV-7 | Minor | F7, sweep | queue down: person told "a person will take over" with no item; only an ERROR line; sweep serial, no per-tick cap | alert/metric; per-tick cap; state host retry contract |
| DES-ADV-8 | Minor | purge by updated_at | a handed-off chat waiting for a person is purged while its item is open | exempt open hand-off items or retention above queue SLA; owner-visible limit |
| DES-ADV-9 | Minor | I-1, F4, crash rule | other exceptions before the claim escape | pre-claim catch-all returns retry (same as DES-COR-3) |
| DES-ADV-10 | Minor | crash rule 1 vs `_to` | "no further store call" contradicts the `_to` write; audit blip mass-hands-off chats | reword; state blast radius in owner-visible limits |
| DES-ADV-11 | Minor | F5/F7 with_person | nothing delivered, nobody says who shows the hand-off text | state host contract for with_person + delivered=False |
| DES-ADV-12 | Minor | lease rule, timing | liveness uses app-node wall clocks; quiet_s computed in two places | state skew margin; one function, one config snapshot |
| DES-ADV-13 | Minor | claim vs forget_user/purge | missing row result unspecified; late put_redaction_map after erasure | missing row: ConversationNotOpen (claim) / LeaseLost (finish); re-check existence on map writes or second delete pass |
| DES-ADV-14 | Minor | text_digest BN-9 | digest depends on map/kinds; false message_id_reused after config change | say intended, or digest pre-label text; test |
| DES-ADV-15 | Nit | E-step order, OP-5 | ids out of order; OP-5 path mismatch | add order-of-execution line |
| DES-ADV-16 | Nit | audit digests | dev without key: plain hash of masked text, guessable | refuse chat agents in dev without a key, or per-tenant pepper |
OP verdicts: OP-1 right problem, insufficient fix; OP-2 sound; OP-3 sound but incomplete; OP-4 wrong position; OP-5 fine; OP-6 sound.

## Correctness (DES-COR)
| id | sev | where | problem | fix |
|---|---|---|---|---|
| DES-COR-1 | Major | forget_user, lease rule | `forget_user` must return busy on a live lease but has no quiet_s argument and the purge role cannot read agent config | add `quiet_s: Mapping[str,float]` argument filled from runtime `_quiet`, or define live as "busy run not final"; test row |
| DES-COR-2 | Major | F9, Money | design/BN-8 say the wrapper books the screen cost; today `_screen` (agent_loop.py:310-316) does `limits.charge` and `store.add_cost` itself, so a model-backed screen cost may be booked twice | say whether `_screen` stops charging when the metered wrapper is present (then in AK-G1-b scope); T21 case booked exactly once |
| DES-COR-3 | Major | I-1, crash rule, F2-F6 | I-1 "no Exception leaves handle_turn after F1" is false before the claim | rule: any Exception in F2-F6 before the claim gives retry after one ERROR line (ids and class), or narrow I-1 |
| DES-COR-4 | Major | I-7, OP-1 | I-7 "agent never calls the model again after hand-off" false: `touch` checks no state, a woken slow run can call the model and deliver; only E4 gives LeaseLost | weaken I-7 to "no new exchange starts" and state the window in OP-1 and limits; or make touch fail when the lease is lost and abort in F10/before E2 |
| DES-COR-5 | Minor | Verification Plan | "19 .handle( test files pass unchanged" but test_p7_tick.py changes (BN-19) | "all pass unchanged except the BN-19 assertion" |
| DES-COR-6 | Minor | goal text, diagram | E2b missing from goal/diagram; bullets numbered 1-7 vs ids; crash arrow only from WORKING | rename/keep consistently; draw crash from RECEIVED too |
| DES-COR-7 | Minor | line 40, stale table | "folds in 28 build notes" not fully true: two superseded ticket texts not in table (Interface 2 claimed creates run row -> BN-6; Interface 3 GRANT -> BN-15); BN-24 and BN-18 ADV-19 dropped silently | add rows and a line, or say "applicable build notes" |
| DES-COR-8 | Minor | line 17, 188, 431 | no dependency/build-order section (P4d-a1, AK1-a, P4b1-b, P4c-2, P5c-2/3, AK1-b); names absent in this checkout | add subsection from ticket sub-PR table |
| DES-COR-9 | Minor | purge_conversations | unclear whether age-out purge deletes tool_calls | state: maps only, tool_calls stay on tool_calls_days |
| DES-COR-10 | Minor | text_digest | HMAC under restored_key: key rotation makes a genuine resend refused; `_keyed_digest` rename on str not described | unkeyed digest for reuse compare, or state as limit; fix signature |
| DES-COR-11 | Minor | sweep, lease | "stuck runs first so quiet runs are final" false (limit 100, failed step lets others run); strict vs non-strict edge | drop the sentence; same comparison in both |
| DES-COR-12 | Minor | purge role locks | purge role has no UPDATE; `SELECT ... FOR UPDATE` probably needs it (UNVERIFIED) | choose one conditional DELETE (lease check and delete in one statement); keep rows 16, 17 |
| DES-COR-13 | Nit | F4/F8 | evidence_unavailable overrides conversation_too_long | keep conversation_too_long if set |
| DES-COR-14 | Nit | words | odd/even parity (same as ADV-6) | add "until a hand-off" |
| DES-COR-15 | Nit | F7 second F6 | `run_id` undefined for `recorded` | state run_id=None |

Not checked by either: P4c-2/P4b1-b/P5c/AK1 names (absent here), Postgres lock privileges, audit protocol semantics, retention values, mutant ids and test rows.
