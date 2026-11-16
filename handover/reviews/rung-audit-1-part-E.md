# Rung audit 1, part E: P4b1, P4b2, P4c, P8a, P8b (lead order 54)

Written 2026-11-06 (UTC; IST = UTC+5:30) by a read-only audit agent. No ticket was edited, no code was written, and no test was run. Inputs read: `LEAD-ORDERS.md` orders 53 and 54; `bible/RULES.md` R445-R447; `tickets/P4b1.md` (revision 3 FROZEN plus BN-1 to BN-32); `tickets/P4b2.md` (revision 4 plus BN-1 to BN-26); `tickets/P4c.md` (revision 4 FROZEN); `tickets/P8a.md` (revision 3 plus BN-1 to BN-21); `tickets/P8b.md` (revision 3 plus BN-1 to BN-17); `reviews/gateway-check-lead-reading-1.md` (the lead's own gateway test, 2026-11-06). Line numbers are those files' line numbers.

The rung numbers are the ones order 54 uses: 1 studio code, 2 the client's tool, 3 no-code/low-code, 4 MCP server, 5 maintained library or standard tool, 6 new model feature, 7 our code.

Web access in this session: only github.com resolved. The doc sites docs.litellm.ai, developer.pagerduty.com and docs.renovatebot.com failed DNS (they are outside the session's allowed network). Facts from them are UNVERIFIED unless a GitHub copy of the doc was read. Every web citation below was read on 2026-11-06.

## Summary (one row per ticket)

| ticket | cut? | agent-time saved (estimate, basis) | risk of the cut (what could go wrong, which guarantee) |
|---|---|---|---|
| P4b1 (meter, money types, `MeteredLLM`) | none | 0. Every component is the exact-decimal reserve/settle guarantee or the per-run cap. The one higher rung, a client's LLM gateway, was tested by the lead on 2026-11-06 and does not give reserve-before or settle-after per run. | n/a. The not-cutting risk is that a gateway gets offered later as a replacement, not as an adapter. BN-32 already says adapter-only. |
| P4b2 (billing contract, sweep login, reservation age) | none | 0 by cut. If the client already runs pg_cron, the tick step could be swapped for it as an option: about 0.5 agent-hour less glue, at the cost of a second SQL path (basis: one appended TickStep plus a few E rows). Not recommended for core. | If the sweep moved to pg_cron: memory-store parity is lost, the probe that runs before the sweep (`maintenance_identity_problems`) is lost, and pg_cron needs a superuser install. Guarantee at stake: least privilege, one identity per function. |
| P4c (alert ledger, metered run path, wall alert) | none (an option is noted) | 0 for core. A client that already runs an alerting tool with dedupe could take the "normally once" half. P4c-1 is still needed for at-least-once delivery. Saving if P4c-1 were cut: about 3 to 5 agent-hours (basis: 1 table, 3 store methods on 2 stores, 1 migration, 1 GRANTS row, contract rows, 12 mutants). | Cutting P4c-1 loses the alert when the process dies between writing the run state and sending, and no later run hits the wall that period. That is the R368 "no lost message" guarantee. Test idea below (P4c-1 row). |
| P8a (re-pin four demos) | none | 0. It has no core code; it is one sitting by the lead of git and test commands. Renovate supports `uv` (GitHub doc read 2026-11-06), but setting it up across 4 demo repos for ONE bump costs more than the bump. | n/a |
| P8b (kind pages, drift report, ledger check) | partial | About 1.5 to 3 agent-hours (basis: `p8b_ledger_check.awk` plus T2, with about 21 planted faults P1-P24, each one written, run and recorded on mawk; P20 and T3 already run the studio's `ledger_check.py`). | Without T2 the cloud cannot check its own ledger before the copy to the laptop. A bad row would be caught later, at T3 on the laptop, which costs one more round-trip. No safety guarantee is involved: this is a docs and process ticket. |

UNVERIFIED count: 9 (list at the end).

Honest overall reading: my five tickets are mostly the "really required" money brain. They were already pushed down the ladder where it fits:
- prices and caps are config (`config.py:55-59`, `registry.py:53`);
- sending an alert uses the existing channel kind;
- the drift report is the existing `egm:egm-drift-report` skill;
- the sweep runs inside the existing tick.

The owner's complaint is fair for other tickets (order 54 item 2 names AK-G16, AK-G2, AK-G15, AK1/2a/4a and P5b). In this part I found only one real cut, the duplicate ledger checker in P8b, and it is small. I will not invent cuts to fill the table.

## Check of the named guarantee: "exact-decimal money reserve/settle" in P4b1 and P4b2

The question was whether this guarantee is true for each component, and whether price tables, reporting or caps can be config or a library.

- TRUE for `money.py` (`SpendMicro`: whole micro-dollars, the exact conversion to a `Decimal` with exponent -6, `ceil_cost` that rounds up once; P4b1:94, BN-17).
- TRUE for `Meter.reserve`/`settle`/`release`/`hold`: id-keyed, idempotent, settles in a `finally` on every exit (P4b1:98-103). P4b1:9-10 measured the defects this fixes: 0.2 booked instead of 1.1, and 3.20 spent against a cap of 1.00.
- TRUE for W and the conversion of prices into micro-dollars (P4b1:261 plus BN-3: `check_usd`, then an exact `scaleb`).
- TRUE for P4b2-a's booking table (P4b2:59-67: release only on proof; otherwise the upper bound in whole micro-dollars).
- NOT this guarantee, but other justifying reasons:
  - P4b2-b's maintenance login: least privilege, one identity per function (order 21 item 13).
  - P4b1's `orphan_age_s`, `Hold.age_s` and log lines: operating policy and signals. They are a few lines inside the same module, and no tool does them better.
  - P4b1 Step 0: a process document, not code.
- Price tables: ALREADY config (`Route.input_usd_per_mtok` and `output_usd_per_mtok`, `config.py:55-59`, cited at P4b1:16). A maintained price list (for example the price file a gateway library ships) could SEED that config, but R16 requires prices that are re-verified live and dated, so it cannot replace the check. That price-file fact is UNVERIFIED (its doc site was blocked).
- Caps: ALREADY config (`budget_usd` daily and monthly, `max_run_usd`, read by `Limits.caps`, P4b1:107). The meter only passes them to the store.
- Reporting: neither P4b1 nor P4b2 builds reporting. They write log lines and the reservation rows only (P4b2:113). Any spend dashboard is the client's tool (rung 2) reading those rows. Nothing to cut.

## P4b1: neutral meter kind (P4b1-a core, P4b1-b wrapper)

| component | what it must do (cite) | rung that could cover it | evidence | what only our code can give | verdict |
|---|---|---|---|---|---|
| Step 0 base comparison | Measure Intake's spend guard against PR #48 before any code (P4b1:56-83) | 1 (studio code: it decides WHICH studio code to reuse) | P4b1:58 | n/a: it is the improve-before-replace step, a document | KEEP (it is the ladder's rung 1 itself; no code) |
| `money.py` `SpendMicro`, `BusinessMoney` | Whole micro-dollars, an exact conversion to Decimal, rounding up once, no mixing with business money (P4b1:94-95, R171, R214) | 5 (a money library such as py-moneyed) | UNVERIFIED (not checked) | A spend type that refuses `int`, `float`, `Decimal` and business money as operands, sized to P4d's bounds. A general money library models currencies, not "micro-dollars, round up once per call". | KEEP-CODE (exact-decimal guarantee) |
| `Meter.reserve`/`settle`/`release`, error table, release table | Reserve before the call, idempotent settle keyed by id, fail closed, closed error codes (P4b1:31-47, 98-101) | 2 or 5 (a client's LLM gateway, e.g. a key budget in a LiteLLM proxy) | `reviews/gateway-check-lead-reading-1.md` (2026-11-06): no overshoot in a simple sequential run; under 20 concurrent calls 19 were refused for an unexplained reason; "does not show it gives our guarantees (reserve before, settle after, exact decimal, per-run cap, fail closed on unknown billing)" | Reserve-before and settle-after per RUN; settle replay returns the first result; release only when the outcome is unknown to the meter | KEEP-CODE (exact-decimal reserve/settle) |
| `Meter.hold` context manager, exit-settle failure, overshoot signal | Settle on every exit, including `KeyboardInterrupt`; never replace the body's exception; signal an overshoot (P4b1:102-104, BN-2, BN-4) | 7 only | P4b1:64 (gate 4) | The settle in a `finally` around the model call | KEEP-CODE |
| `Limits.caps` / `Limits.hold` | Read caps from the registry; one lazily built `Meter` (P4b1:107) | 1 (the registry config already holds the caps) | `registry.py:53` (P4b1:14) | Already config plus thin glue: about 30 lines | KEEP-CODE (it is already the glue) |
| Time and age policy (`spend_day`, `orphan_age_s`) | UTC budget day; orphan age floor (P4b1:105-106) | 7 | P4b1:29 | One day expression shared with `Limits` | KEEP-CODE (a few lines; not worth a tool) |
| `MeteredLLM` wrapper and scope | Same `chat` signature; a hold per call; a per-run scope; `scope.refusal` (P4b1:258-259) | 2 (client gateway, BN-32 option b) | BN-32 (P4b1:505-509) and the lead's gateway test (2026-11-06) | Run-scoped caps, the judge call covered by the same scope, fail closed on unknown billing | KEEP-CODE; the gateway stays an outlined adapter (BN-32) |
| `prompt_bytes` and W (the worst case of one request) | An upper bound on tokens from bytes; exact conversion of prices; floor of 1 micro-dollar (P4b1:260-262, BN-3, BN-10) | 6 (a provider token-counting endpoint) or 5 (a tokenizer library) | UNVERIFIED (no doc fetched) | A bound with NO network call that is never below the real cost. A token-count call adds a request and latency before every reserve, and its result is an estimate unless documented as an upper bound. | KEEP-CODE |
| Prices | Prices for each route (P4b1:16) | 1 (already config) | `config.py:55-59` | n/a | Already config: nothing to cut |
| Failure booking `count x attempts x W` | Upper bound when billing is unknown (BN-5) | 7 | LEAD-ORDERS 14(3), 19 D (cited in BN-5) | Fail closed on unknown billing | KEEP-CODE |

## P4b2: billing contract (P4b2-a) and sweep login (P4b2-b)

| component | what it must do (cite) | rung that could cover it | evidence | what only our code can give | verdict |
|---|---|---|---|---|---|
| `AttemptCounts` stamp, call-scoped counter, `classify_attempt` | Count attempts per chat; tell refused, unsent and unknown apart; never release on doubt (P4b2:50-58, 97-103) | 1 (the core already has `with_retry`, P4b2:31) or 5 (a retry library such as tenacity) | P4b2:31 (one caller, `NetworkLLM._retry`); tenacity facts UNVERIFIED | A retry library retries; it does not book billing. "Release only on proof" is a money rule. | KEEP-CODE (exact reserve/settle; upper bound when billing is unknown) |
| `REFUSED_STATUSES` | Allow-list of HTTP statuses taken as "not billed" (P4b2:52, 97) | config | P4b2:47 (the provider's error page says nothing about billing; read 2026-11-05) | A constant whose change is a money decision; config would let an operator widen what gets released | KEEP-CODE as a constant. Moving it to config would weaken fail closed. |
| `billing_outcome` and the wrapper's failure branches | Release, keep or book the upper bound (P4b2:103-111, BN-1) | 2 (gateway) | Lead gateway test 2026-11-06 (no unknown-billing rule) | Fail closed on unknown billing | KEEP-CODE |
| k1b answered path (E2) | Book the hidden attempts on the replay path (P4b2:112) | 1 (k1b exists) | P4b2:38 | n/a: it is an edit of studio code | KEEP-CODE (edit of rung 1) |
| Billing log line | Counts only, no text (P4b2:113) | 2 (the client's log tool reads it) | n/a | A log line is the glue; any dashboard is the client's tool | KEEP (already minimal) |
| Maintenance login, grants, actor trigger, `maintenance_identity_problems` | One identity for the sweep; the runtime cannot expire a row (P4b2:201-224) | 7 | LEAD-ORDERS 21 item 13; least-privilege rule | Least privilege, one identity per function | KEEP-CODE (justified by the tenant/least-privilege rule) |
| Tick step `expire_spend_reservations` | Bounded sweep under the maintenance login (P4b2:231-236, BN-12, BN-13) | 1 (the existing tick, `runtime/tick.py` STEPS) or 5 (pg_cron in the database) | pg_cron README (github.com/citusdata/pg_cron, read 2026-11-06): a job runs "with the same permissions as the current user"; `cron.schedule_in_database` takes a `username`; the README lists Amazon RDS, Azure and Google Cloud among supporting services | The probe before the sweep, parity with the memory store, and no superuser extension install. The tick already exists, so this step IS glue on rung 1. | KEEP-CODE (it is already thin glue). pg_cron could be offered as a client option only if the client runs it. |
| Age rules (A1, A2) | Age measured on the database clock (P4b2:238-239) | 5 (PostgreSQL `clock_timestamp()`) | P4b2:20 | Already uses the standard tool; the rule is a constraint on callers | KEEP (no extra code) |

## P4c: alert ledger (P4c-1) and metered run path plus wall alert (P4c-2)

| component | what it must do (cite) | rung that could cover it | evidence | what only our code can give | verdict |
|---|---|---|---|---|---|
| `max_run_usd` on the run path through one `MeteredLLM` and one scope per run (P4c-2) | Reserve before every model call, the judge call included; fail closed (P4c:193, rule 2 at :99) | 7 | P4c:196 | The per-run money cap | KEEP-CODE (exact-decimal reserve/settle) |
| Overshoot and settle-failure handling (P4c-2) | End the run with its own reason code and a card (P4c rule 6 table, :104-110) | 7 | P4c:104-110 | Run state written first | KEEP-CODE |
| `registry.py` and `deferred.py` checks | Validate caps and `alert_to` (P4c-2) | 1 (validated config, pydantic) | P4c-2 interface | Config validation is already the config path | KEEP (it IS config) |
| `alerts.render` and `WallAlerter.raise_wall` sending | Fixed-text alert sent through the channel kind (P4c-2) | 1 (existing channel kind, Slack backend) or 2/3 (the client's alert tool, n8n) | P4c-2 interface (`slack_channel.py:45` timeout) | Sending is already rung 1. The template text is a few strings. | KEEP (already reuses rung 1). Making the templates config is not worth it: the text is checked through `channel.clean`. |
| `wall_alerts` ledger (P4c-1: 1 table, 3 store methods, migration, grant) | "At least once, normally once, per agent per wall per period"; survive a crash between "decide" and "sent" (P4c:128-131) | 2 or 5 (Alertmanager grouping and `repeat_interval`; PagerDuty `dedup_key`) | Alertmanager configuration doc (github.com/prometheus/alertmanager docs/configuration.md, read 2026-11-06): `repeat_interval` is "How long to wait before repeating the last notification"; it does NOT say it deduplicates, and it leaves dedupe to the receiver through `groupKey`. PagerDuty `dedup_key`: UNVERIFIED (site blocked). | A durable "not yet sent" record in the CLIENT's own store, with no extra tool. An alert tool fed by a log line loses the alert if the process dies before the log is shipped, and Alertmanager needs a metrics source that the core does not have. | KEEP-CODE for core. Guarantee gap test idea: "the process is killed after the run state is written and before `channel.send`; no later run hits the wall that period; the tick retry still delivers within `WALL_ALERT_RETRY_AFTER_S`". Option for a client with PagerDuty or Opsgenie: send with a dedup key, and the "normally once" half moves to the tool. |
| Retry tick step and red rule (P4c-2) | Retry unsent alerts for the current and previous period; turn red on failure (P4c:13-14) | 1 (the existing tick) | P4c:13 | It is glue on rung 1 | KEEP |
| `MAX_DOCUMENT_BYTES` tied to the prompt bound | A config bound may only be lowered (P4c:30) | config | P4c:30 | Already config plus one constant | KEEP (already config) |

## P8a: re-pin the four demo repositories

| component | what it must do (cite) | rung that could cover it | evidence | what only our code can give | verdict |
|---|---|---|---|---|---|
| Pin bump in `pyproject.toml` and `uv.lock` | Move all 4 demos to ONE `<FINAL>` commit; stop if `origin/main` moves (P8a:33-38) | 5 (Renovate or Dependabot) | Renovate pep621 manager readme (github.com/renovatebot/renovate lib/modules/manager/pep621/readme.md, read 2026-11-06): supports "`uv` (including `uv.lock` files and `uv` workspaces)"; support for git-commit dependencies is NOT stated (UNVERIFIED) | n/a. It is a one-time bump; "same commit across 4 repos, stop if main moves" is a start rule, not code. | KEEP the lead's manual sitting (there is no code to cut; a bot costs more for one bump) |
| Delete or keep the copies; copy tests; R1c and R10 one-line scripts | Delete the copies core now provides, keep the rest with their snapshot, prove nothing drifted (P8a:39-55, BN-7, BN-8, BN-15) | 1 (each demo's existing copy test, P8a:55) plus 5 (git) | P8a:54-55 | Look-alike checks did not get weaker (R13, R14) | KEEP (already plain git plus existing tests; the "code" is one-liners) |
| R13 and R14 checks at the deny and allow sites | No look-alike check gets weaker (P8a:29, BN-3, BN-4) | 7 | P8a:29 | Redaction and egress safety | KEEP (it tests the core safety chain; not audited here) |

## P8b: one README per kind, the drift report and the ledger check

| component | what it must do (cite) | rung that could cover it | evidence | what only our code can give | verdict |
|---|---|---|---|---|---|
| 16 pages in `docs/kinds/` | Plain-word page per kind with fixed headings; the Backends rows come from `TABLE` (P8b:98-110, 150) | 5 (an API doc generator such as pdoc or mkdocstrings for the Interface part) | UNVERIFIED (no doc fetched) | The plain-word role, "what it does not do" and the dev-only labels are writing, not code. A generator gives signatures only. | KEEP (it is writing; the `roles.py` generator is already about 1 file) |
| T1 and T6 checks (`t1.sh`, `t6.sh`, grep and awk) | Page set equals `TABLE` keys plus the extra list; fixed headings; labels (P8b:161, 166) | 5 (a prose or markdown linter such as markdownlint or Vale) | UNVERIFIED | The set comparison against `TABLE` is project-specific; a linter checks style only | KEEP (small shell, no tool covers 80 percent) |
| T4 drift report | No open drift in `docs/kinds/` (P8b:164) | 1 (the existing `egm:egm-drift-report` skill) | P8b:47 | n/a | KEEP (already rung 1) |
| T2 `p8b_ledger_check.awk` plus about 21 planted faults (P1-P24) | Cloud ledger has no unresolved BLOCKER or MAJOR (P8b:162, 181-203) | 1 (the studio's `ledger_check.py`, which T3 already runs on the laptop, P8b:163, 388) | P8b:163, 388; the tool itself is not visible in the cloud (P8b:439) | Only that the cloud can check itself before the copy. No guarantee from the order 54 list. | CUT-TO-CONFIG+GLUE (partial): drop T2 and its planted faults, normalise the 5-cell rows (needed anyway, PENDING LEAD 6), and gate on T3 alone. Or copy `ledger_check.py` into the cloud branch and run it there. |
| T5 section 9 paths | Every path exists (P8b:165) | 5 (`test -e`) | P8b:165 | n/a | KEEP (already a standard tool) |

## UNVERIFIED (not read or not runnable in this session)

1. Whether a maintained money library (for example py-moneyed) could represent "micro-dollars, round up once per call" (P4b1 `money.py` row). No doc was fetched; the verdict does not depend on it.
2. Whether a provider token-counting endpoint or a tokenizer library returns a documented UPPER bound (P4b1 W row). No doc was fetched.
3. Whether a gateway price file (for example LiteLLM's) is fit to seed `Route` prices (docs.litellm.ai failed DNS in this session).
4. What tenacity (or another retry library) offers for attempt accounting (P4b2-a row). No doc was fetched.
5. PagerDuty Events API `dedup_key` behaviour (developer.pagerduty.com failed DNS).
6. Whether Renovate can bump a git-commit dependency in `pyproject.toml` (docs.renovatebot.com failed DNS; the GitHub readme does not say).
7. What pdoc or mkdocstrings generate for this repo (P8b pages row).
8. Whether a markdown or prose linter could replace any T6 check (P8b T1/T6 row).
9. What `ledger_check.py` and `ledger_lint.py` do and which arguments they take (not visible in the cloud, P8b:439). The P8b partial cut assumes T3 already catches what T2 catches; the lead should confirm this on the laptop.

The network hosts above (docs.litellm.ai, developer.pagerduty.com, docs.renovatebot.com) would need to be allowed in the session's network settings to verify items 3, 5 and 6 here.
