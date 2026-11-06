# P6b1 round 3, correctness review (ticket revision 3)
Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority).

TICKET REVIEW round 3, CORRECTNESS, tickets/P6b1.md revision 3. Read-only. I did not read anything under handover/reviews/ or handover/evidence/.

Result: no Blocker. 1 Major, 4 Minor, 3 Nit.

SOURCE STATE. Every code, file and line cite I checked matches the CURRENT tree at src and /tests. The ticket says it was drafted on ce70eb5 and the checkout is not pinned. I cannot run git here, so I cannot say whether the tree equals ce70eb5 (UNVERIFIED). Where the ticket says "main may differ", I found no difference in any cited line.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-COR-1 | Major | 166, 180-183, 275 (interface and security notes); T7 line 318; T8 | The ticket says every validator message is a fixed text with no part of the input. The `checked_on` rule parses with `date.fromisoformat` after the regex. A string that matches `[0-9]{4}-[0-9]{2}-[0-9]{2}` but is not a real date (2026-13-45, 2026-02-30, 0000-00-00) makes `fromisoformat` raise a ValueError whose text can hold the input, and `hide_input_in_errors` does not hide message text. The ticket does not say the error is caught and re-raised with a fixed text. T7 has no impossible-calendar-date row, and the T8 canary rule does not cover `checked_on`, so M26 and M24 would not notice. | Say the interface catches ValueError from `fromisoformat` and raises the fixed text `checked_on must be a date written YYYY-MM-DD`. Add T7 refused rows `2026-13-45`, `2026-02-30`, `0000-00-00`. Add a row asserting the invalid text is absent from `str(ConfigError)`. |
| R3-COR-2 | Minor | 173, 247, 273 | The ticket says `reference` "never holds ... a person's or party's name". The pattern `^[A-Za-z0-9][A-Za-z0-9 ._:/#-]{6,198}[A-Za-z0-9]$` allows letters and spaces, so "Jane Doe Acme" passes. This is a documentation rule, not a code rule. The "Known gaps" list at 273 names only short secrets and split ids. | Reword to "must not hold" and add the name case to the stated tripwire gaps and to the README text. Do not imply that code enforces it. |
| R3-COR-3 | Minor | 178 (and 177) | The ticket says the `hosts` pattern "accepts every value the host functions can return". That is false for a non-ASCII host. `openai_compat` only requires https (`table.py:77-85`), and `urlsplit(...).hostname` returns an IDN host as unicode. The expected side then holds characters the pattern refuses, so no statement can ever match and pilot or prod cannot start. A `_NAME` value is `[A-Za-z0-9-]+` with no length cap (`table.py:33`), so a very long Foundry resource can exceed 253 characters with the same effect. It fails closed, but the claim is wrong. | State the limit (host names must be ASCII or punycode and at most 253 characters), or IDNA-encode the expected side. Add one T14 row for a non-ASCII `base_url` host. |
| R3-COR-4 | Minor | 342-346 (T11); 213-216 | The log line is built in `make("llm", ...)`. `FakeLLMSettings` does not inherit `_LLMSettings` (`table.py:28-29`, ticket line 62), so `settings.no_training` does not exist for `fake`. The ticket does not say the log code must use `getattr(..., None)`. T11 runs only `openai_compat`. A plain attribute read would crash every dev and fake test. | Say `getattr(settings, "no_training", None)`, and add a T11 row that calls `make("llm", FakeLLMSettings(...))` without error. |
| R3-COR-5 | Minor | 357, 355 (T14 loopback row); 221; UNVERIFIED list | The row `http://[::1]:8000/v1` with `self_hosted` loads at config time, which is correct (`table.py:77-85`). But `guard/http.py:112-115` (a docstring, enforcement not traced) says LLM clients in pilot or prod "must not point" at a loopback name. `llm/openai_compat.py:49` also treats a loopback host with a tagless model id as "floating". The ticket offers loopback as a `self_hosted` sample without saying these runtime facts. | Add one plain sentence that a loopback `self_hosted` sample loads but may be refused or pinned at runtime. Settle in the build notes whether `guard/http.py` enforces it. Keep it in the UNVERIFIED list until traced. |
| R3-COR-6 | Nit | 101 | "`pilot_cfg(` appears 11 times" in `test_k3_pilot_env.py`. My count is 11, but that includes the `def` at :35, so there are 10 calls. The other files match: `test_k5_round5.py` 2; `test_k5_round9b.py`, `test_k5_round10.py`, `test_k5_round8_postgres.py` and `test_k5_tools.py` 1 each. | Write "11 matches, 10 calls and the definition". |
| R3-COR-7 | Nit | 311 vs 310 vs fail-before row "T4 bounds (0, 180, 181)" | Bounds are described inconsistently. Line 311 lists 0 and 181 as refused. 180 is "accepted" at line 310. The table groups all three as "bounds". | Say "bounds: 0 and 181 refused (field errors), 180 accepted (load)". |
| R3-COR-8 | Nit | 128 vs LEAD-ORDERS 6(b), 8(1), 20(6) | "Extended review (no round cap): yes" for RESULT review. The ticket correctly uses order 20(6) for TICKET review (3 rounds; the extra round only for money or redaction). Orders 6(b) and 8(1) said security tickets have no cap, and order 16 and later orders override them. The line is correct but could be read the other way. | Add "order 20(6) and order 16 supersede 6(b) and 8(1) for ticket rounds". |

RECOUNTS (all match the ticket)
- Test ids: 19. They are T1, T1b, T2, T3, T4, T5, T6, T6b, T7, T7b, T8, T9b, T10, T11, T12, T13, T14, T15, T16.
- Mutants: M1 to M31, all listed. Each has a named killer (M7 -> T9b with T16 rows 1-3, M14 -> T1b, M21 -> T8, M31 -> T7). M3b and M4 are variants that count once.
- T1: 8 rows (4 kinds x 2 environments). T2: 9 pairs (2+2+2+3) x 2 = 18. T3: 3. T16: 3 + (5 rows x 4 kinds = 20) + (2 rows x 3 kinds = 6) = 29.
- Fail-before table: 23 rows (T1 pilot, T1 prod, T1b, T2, T3, T4 x3, T5, T6, T6b, T7 x2, T7b, T8, T9b, T10, T11, T12, T13, T14, T15, T16). The ticket says the only real proof is the 8 T1 rows. That holds on my read: the others fail only on missing names or keys, or are pins.
- Pins: T1b, T6, T15 (5 = 5 kinds), and the three T7 pin rows.
- Not killable swaps: the ticket's statement (b against c, f, d, e; and d against e) is correct. (a) against (b) is killable by T16 row 1, and the c/f/d/e swaps are killable by rows 5-8. M22 and M23 are killed.

VERIFIED against source (all match)
- `config.py`:
  - `_Strict` :50-52; `Backends.llm` :70, no default.
  - `_one` :89-120 (wrap at :117-120, TABLE lookup at call time at :95-101).
  - `_inventory_ref_ok` :302; `Config` :316; `_cross_checks` :349-374 (DEV_ONLY text at :366-369, loopback at :370, anchor call at :371, raise at :372-373).
  - `_anchor_refusals` :377-397 (prod refusals :391-396, which matches the "pilot_cfg is refused in prod on old code" claim).
  - `_UniqueKeyLoader` :400; `load_config` re-raise and wrap :451-454. `Config` has exactly one model_validator, so the "single error" assumption in `_cross_check_text` holds.
  - `config.py` already imports `defaults` and `table`; it needs `datetime` added.
- `backends/table.py`:
  - `KindSettings` :20-25; `FakeLLMSettings` :28-29; `_NAME` :33 (not :31); `_LLMSettings` :36-40.
  - Anthropic :43-61, Bedrock :64-65, `_LOOPBACK` :68, OpenAICompat :71-85, Gemini :88-89, Guardrail :101.
  - `key_label` rule :196-210, regex at :208. `Entry` :332-344.
  - `_aws` :347-353; `_anthropic_hosts` :365-370 (vertex has two hosts, :367).
  - llm table :512-542 (kinds :513, :515-521, :522-528, :529-535, :536-541); `lambda` hosts at :533 and :540; `neutral=True` at :534; `bedrock_guardrail` :549; `DEV_ONLY` :593-596; `NOT_PROD` :604.
- `backends/platform_secrets.py:18-20`: `secret_names` reads top-level fields only.
- `backends/factory.py`:
  - `make` :29-57, no logger; `hosts` :60-66.
  - `registry.py:136-149`: the hash allow-list matches the ticket.
  - `make("llm"` sites: `cli.py:150` (gate, branch :146), `cli.py:221` (replay only; score returns at :219-220), `app.py:162`. `cli.py:299` `build(None, agents)` is the only `build` call in cli.
  - `llm/__init__.py` imports `llm/fake.py`, which imports `hadavin_sdk.config` (import chain confirmed).
- `defaults.py:1-3` docstring says "K5 read path".
- Tests: `test_k3_pilot_env.py` :35, :60, :61, :89 (the `pilot_cfg` signature has `config=` merged at top level, and `yaml.safe_dump` round-trips a `date`).
  - `test_lockin_guard.py`: `coverage_problems` at :406, its test at :429-430, `_TABLE_VENDOR_NAME` at :516.
  - `P4d.md:273` exists and matches the ticket's description.
- Claim "only `pilot_cfg` builds pilot or prod with a real llm kind": no counterexample.
  - `test_p1b_backends.py:89-102` and `test_p3b_neutral_audit.py:248-261` use `fake` or no valid prod config.
  - `test_p1b_backends.py:89-102` asserts the substring `llm: fake`. That stays compatible with the design, because `_no_training_refusals` returns `[]` for DEV_ONLY pairs.
- `openai_compat.make` needs no SDK (stdlib HTTP) and needs `routes`, so T11 is feasible.
- Orders 20(6), 20(4) and 16 are described correctly. Times are consistent: 02:58 UTC is 08:28 IST.
- No real-looking secrets in the ticket. Canaries are built from parts.

NOT CHECKED
- Whether the tree equals ce70eb5 (git not run).
- All pydantic and Python 3.12 behaviour, including the `str()` form of the wrapped error, the Rust regex treatment of `$` and a trailing newline, and `date.fromisoformat` on non-ASCII digits. The ticket marks these UNVERIFIED too.
- The `P4a.md:205` cite (a long line I did not expand), and the hot-file lists for P2a, P4b1, P4b2, P4c, P5b3, P5b4, P5c, P6a and P6b2.
- Whether `guard/http.py` enforces its no-loopback statement in pilot and prod (R3-COR-5).
- Whether `test_no_hardcoded_values.py` accepts the new messages and docstrings. Its patterns (12-digit run, host, URL) look compatible, but I did not run them.
- Provider terms, P1m's mutation runner format, and README's claim about loopback.