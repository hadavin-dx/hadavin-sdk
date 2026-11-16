# P4a round 1: disposition of the resolve report (author, revision 2)

Date 2026-11-05. Ticket: `handover/tickets/P4a.md` revision 2 (replaces rev 1 bd061b3). Core ce70eb5, handover HEAD 7e63580. Inputs: `P4a-round1-resolve.md`, `P4a-round1-adversarial.md` (ADV-F1..F20), `P4a-round1-correctness.md` (COR-F1..F16). Nothing was run in this revision; code cites were re-read with Grep/Read only. Statuses: applied / contested (applied in part, my disagreement stated) / declined / pending (needs the lead).

## Disagreements and gaps I found (read first)

1. **Merge rule is applied but has a gap (ADV-F1, PENDING LEAD 1).** P4b1-a is the meter core; the wrapper that settles at the reserved amount on `UsageMissing` is P4b1-b (`P4b1.md` line 150), and `agent_loop` uses it only after P4c-2. So "P4a-1 merges only consecutively with P4b1-a" does not by itself close the window for `agent_loop`, `judge`, `extract`, `evals`, `k1b/loop`. I recommend adding "no live provider call from any call site until P4c-2 has merged". Not decided by me.
2. **ADV-F5 request multiple `2 x max_attempts`: applied, partly disagree (PENDING LEAD 7).** A retry follows an error, so a billed answer is not repeated; the multiple over-reserves up to 3 times and is inconsistent with the other kinds. Safe direction; one constant to relax.
3. **P4a becomes two pull requests** (P4a-3 had only cut items; `max_prompt_tokens` folded into P4a-2). Other tickets still say three (PENDING LEAD 9).
4. Resolve report said it did not re-read code; I re-read the cites I changed. No reviewer cite I re-read was wrong. Cites I did not re-read are marked UNVERIFIED in the ticket.
5. COR-F7 and COR-F10 are named inside resolve rows (boundary row; raise before the second request) but have no row of their own; I applied them as stated there.

## One line per finding

| id | status | where in `P4a.md` rev 2 |
|---|---|---|
| ADV-F1 (blocker, money) | applied + pending | Answer first 2; P4a-1 Depends-on; U10 re-pointed (no cost assertion, mutant a1-3b); X1; PENDING LEAD 1 (gap above) |
| ADV-F2 | applied | Rules stated once ("No raw ValueError"); `build_usage`, `add_usage`; U3b, U13; P4a-2 C3c, C4b; zero-input rule in `cost_usd` (U2b, a1-8, a1-8b) |
| ADV-F3 | applied | U3 per-kind reachable forms; Anthropic SDK path as unit rows; E0 probe line |
| ADV-F4 | applied (cut) | v1.1 V1; U3 Gemini rows pin that no total refusal happens; `llm_wire.py` fixture total left at 307 |
| ADV-F5 | contested | P4a-2 `request_bound()`, `estimated_worst_case_usd(requests=)`, C7(d), a2-9b, a2-23; P4a-1 U4 (raise before second request, request count); PENDING LEAD 7 |
| ADV-F6 | applied | rename to `estimated_worst_case_usd`; "not a bound" in the plain-words list and C7(c); safety net named (P4d `settle_spend`, P4c T6) |
| ADV-F7 | applied (cut) | v1.1 V4; PENDING LEAD 3 (recommend no) |
| ADV-F8 | applied (cut) | v1.1 V2, V3, V5; `Route` keeps its shape; only `Price` validator and optional fields kept |
| ADV-F9 | applied | P4a-2 `max_prompt_tokens` basis = uncached + cache write + cache read; direction of error stated; M1, a2-24, a2-25 |
| ADV-F10 | applied | P4a-2 Anthropic nested cache rule (Intake's, full); Bedrock unknown-cache-key refusal; C3b, a2-21, a2-22 |
| ADV-F11 | applied | mutation tables: a1-3 split to a1-3a and a1-3b, equivalent half dropped; a1-14 labelled AST/signature; U10 re-pointed |
| ADV-F12 | applied | U6 asserts equality with the exhausted-case charge plus the floor; pipeline edit marked temporary and dropped if P4b1-c is in the same batch |
| ADV-F13 | applied | "Verified facts" Reply storage grep with commands; loud-load rows U5 and C9 (cap and cap + 1) |
| ADV-F14 | applied (partly pending) | header and E0: probe numbers marked UNVERIFIED; the evidence runner writes `handover/evidence/p4a-probe-1.md` (I cannot: no code in this job) |
| ADV-F15 | applied | fail-before wording (shims; ImportError/AttributeError fails the run); `grep or token` command replaced by AST row U8 |
| ADV-F16 | applied | exactness proof in "Rules stated once"; Inexact trap kept only as defensive, mutant a2-18 removed |
| ADV-F17 | applied | pricing words `[a-z_]{1,30}` and equal `standard`; C3d ("Priority", "priority-plus"), a2-20 |
| ADV-F18 | declined | reviewer confirms worked values and header arithmetic; nothing to change |
| ADV-F19 | declined | same |
| ADV-F20 | applied | plain-words list: "reserved amount" (meter) vs "highest possible price" (price table) used throughout |
| COR-F1 | applied (merged into ADV-F4) | as ADV-F4 |
| COR-F2 | applied (merged into ADV-F2) | as ADV-F2 |
| COR-F3 | applied | C2 and C7 shim form (`route, err = build_route(...)`, `assert err is None`); money-defect fail-before C2-fb on a flat route |
| COR-F4 | applied | count corrected to 24 reply files plus README (Verified facts, twice removed from other places); builder probes all `*.json` for both keys |
| COR-F5 | applied (merged into ADV-F15) | as ADV-F15 |
| COR-F6 | applied (merged into ADV-F11) | as ADV-F11 |
| COR-F7 | applied | cap boundary rows (10**9 accepted, 10**9 + 1 refused), mutant a1-5b |
| COR-F8 | applied (merged into ADV-F11) | a2-18 removed |
| COR-F9 | applied (merged into ADV-F4) | as ADV-F4 |
| COR-F10 | applied | U4: second request never sent when the first lacks usage; request count asserted; a1-6b |
| COR-F11 | applied + pending (merged into ADV-F1) | as ADV-F1 |
| COR-F12 | applied | "Rules stated once", Hot-file order, reconciled with `P4d.md` 12, `P4b1.md` 21, `P4b2.md` 66 and 299, `P5b1.md` 35; revision 1 claim "no file of P4a is touched by P4d" withdrawn |
| COR-F13 | applied | the "escalates to the lead after round 5" sentence is removed; Done says no round cap for money |
| COR-F14 | applied | C8 lists the expected result per row, including bool, empty string, float |
| COR-F15 | applied (moot) | no pilot/prod price config remains after the cuts; stated in P4a-2 "Files" (`test_k3_pilot_env.py` unaffected) |
| COR-F16 | applied | Rollback of both sub-tickets names the departure from the template loud-failure test and the "old code, new data" evidence step |

## Other items from the resolve report's lead-facing list

- P4d coupling (`round_cost_up` at producers; `settle_spend` above reserved): "Notes for P4d", PENDING LEAD 2.
- Other tickets I could not edit and that need text edits after the fold: `P4b1.md` (Needs from P4a item 3; "all three"), `P4c.md` P4c-2 ("all three"; "tiers"), `P4d.md` line 12, `P5b1.md` hot-file note. Listed in the ticket under "What the lead needs to check".
