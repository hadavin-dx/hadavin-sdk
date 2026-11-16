# AUDIT: does the code enforce a window end date for live model calls? (R460 idle-fallback item)

Static read only. Date of audit 2026-11-16. No code run, no tests run, nothing edited in src/ or tests/.

## Verdict (failures first)
1. **No window end date is enforced anywhere in `src/hadavin_sdk` today.** `grep -rniE "spend_window|window_end|window_ended|window.?end" src tests` returns zero hits. The names exist only in `handover/` papers.
2. **No test pins one.** Same grep over `tests/`: zero hits.
3. **CORE-PR-HANDOFF-v3 decision D1 describes code that does not exist yet.** v3 is a plan (line 101 says "`Limits.blocked` returns `window_ended` after the date"), not a description of current code. It does not claim the code exists, but any reader who treats D1 as a present control is wrong.
4. **The config has no stage or profile field either** (grep `stage|profile` in `config.py`, `defaults.py`, `registry.py` returned nothing). D1's rule "demo and pilot with a real model kind need a date, prod needs a date or `none`" depends on a stage value that I did not find in the code. v3 section 3 row D6 mentions renaming a stage `dev` to `demo`; I did not locate where that stage lives (see "Not checked").

## Every time-related hit I examined, and why it is not a window
| file:line | What it checks | Refuses a live model call after a date? | Test pins it? |
|---|---|---|---|
| `src/hadavin_sdk/limits.py:17-18` `charge` | records spend under `now().date()` | No, it only records | n/a |
| `src/hadavin_sdk/limits.py:20-30` `blocked` | returns `kill_switch`, `daily_budget`, `monthly_budget` | No date test. Day and month totals roll over by calendar, so a new day or month gives a fresh budget and calls resume. Closest thing to a date, but it is a reset, not an end. | Budget and kill switch pinned (e.g. `tests/test_s5_runtime.py:111-128`, `tests/test_review_fixes.py:151`), nothing about an end date |
| `src/hadavin_sdk/registry.py:33-36` `Budget` | `daily`, `monthly` money fields only | No date field | n/a |
| `src/hadavin_sdk/approvals/requests.py:103,154,207` | approval step expiry | Expires a pending human approval, not a model call | not examined |
| `src/hadavin_sdk/k1b/loop.py:78-95, 152-154` | per-case wall-clock timeout and a USD cap (`budget.exhausted`) | No, it is a per-case time limit and a money cap, not a calendar date | not examined |
| `src/hadavin_sdk/tools.py:495,519` | tool-call deadline | Tool bodies, not model calls | not examined |
| `src/hadavin_sdk/actions/secrets_vault.py:7,97`, `audit/anchor_azure.py:54` | token expiry, retention expiry | Unrelated to model calls | not examined |
| `src/hadavin_sdk/config.py`, `defaults.py`, `llm/*.py` | no date, clock, expiry or window setting found (grep for `datetime|clock|now(|time.time` in `llm/`, `limits.py`, `registry.py` found only `limits.py:18,24`) | No | n/a |

## Where live model calls leave the code (all callers of `.chat(`)
Found with `grep -rnE "\.chat\(" src`:
- `src/hadavin_sdk/runtime/agent_loop.py:425` main agent step. Guarded by `_limits_stop` at line 421 (defined 239-244), which calls `Limits.blocked`. Also re-checked before an approved action runs at lines 744 and 669-672 (a failure to read limits stops the run).
- `src/hadavin_sdk/guard/judge.py:72` model-based injection check. The `Limits` object is not referenced in this file. The only protection is the ordering in `agent_loop.py` (line 358-359 comment and call: limits are checked before the judge runs).
- `src/hadavin_sdk/extract.py:47` document extraction. No `limits`, `blocked` or budget reference in the file. **Unguarded by Limits.**
- `src/hadavin_sdk/evals.py:73` eval gate (loops `k` times per case). No limits reference. **Unguarded by Limits.**
- `src/hadavin_sdk/k1b/loop.py:94` replay loop. Its own header (line 3-4) says it does not run the production limits path. It has its own USD cap only.

Consequence for the task: even the existing daily and monthly budget does not cover `extract.py`, `evals.py` or `k1b/loop.py`. A date check placed only in `Limits.blocked` would inherit that same gap. This is my reading of the files; I did not run a call to confirm the unguarded paths.

## Smallest place a refusal must sit (no code written)
Every caller above reaches a model through the `LLM` protocol (`src/hadavin_sdk/llm/protocol.py:19`, implemented by `llm/common.py:208` `NetworkLLM.chat`, `llm/fake.py:29`, and the kind modules). The LLM object is built in one place: `src/hadavin_sdk/app.py:162` (`llm = llm or make("llm", b.llm, secrets, routes=cfg.routes)`). Note line 162 also accepts an `llm` argument passed in by the caller (`app.py:69`), so a refusal inside the kind objects alone could be bypassed by a caller-supplied LLM.

Choke point recommendation: a thin wrapper around the LLM that checks the window with the clock before delegating to `chat`, applied at `app.py:162` to whatever LLM results (made or supplied), and skipped only for kind `fake`. Every caller listed above that receives the app's `llm` (agent loop, judge via `make("detector", ..., llm=llm)` at `app.py:165`) then passes it. `Limits.blocked` is a worse home: it is not reached by `extract.py`, `evals.py` or the replay loop. A reason string in `Limits.blocked` can still be added so the agent loop reports `limits.window_ended`, but the wrapper is what actually guarantees refusal. Callers that build their own LLM (`extract.py` and `evals.py` take an `llm` parameter; `k1b` takes one) would need to be given the wrapped one, or the same check put in `NetworkLLM.chat` (`llm/common.py:208`), which all real kinds share; I did not confirm that all four real kinds (`anthropic.py`, `bedrock.py`, `gemini.py`, `openai_compat.py`) go through `NetworkLLM.chat` rather than overriding it. That confirmation is needed before choosing between the wrapper and `common.py`.

## Cross-check against CORE-PR-HANDOFF-v3 D1
- v3 line 46 (D1) and 99-101 (4.5): new `Config.spend_window_end`, required for real model kinds in demo/pilot, explicit `none` allowed in prod, `Limits.blocked` returns `window_ended`. Tests listed: missing date refused, `none` audited, past date blocks.
- Match with code: none of this exists. Mismatch in design: v3 puts the refusal in `Limits.blocked`, which by the table above does not cover `extract.py`, `evals.py` or `k1b/loop.py`. Suggest v3 name the LLM-level choke point, or state which callers stay uncovered and why.
- v3 line 4.5 says the date is checked "after the date" but does not say which clock; the code's existing clock is `models.now()` (`limits.py:8,18`). I did not read `models.now`, so I do not know if it is injectable in tests.
- CLAUDE.md says "the code must enforce the end date of the window" (rule `model-choice-and-cost-follow-bible.md`, last bullet), so today's code is out of line with that rule.

## Not checked
- Whether `models.now()` is monkeypatchable or clock-injected.
- `llm/anthropic.py`, `bedrock.py`, `gemini.py`, `openai_compat.py` bodies: not read, so I cannot say if they all route through `NetworkLLM.chat`.
- `cli.py`, `deferred.py`, `replay_records.py`, `scrub_settings.py`, `backends/`, `sources/`, `store/` for any date setting beyond the grep patterns (grep covered `window|end_date|expir|not_after|valid_until|deadline|ends_at|cutoff|sunset`, with context-window wording filtered out; a differently named setting would be missed).
- Where a stage (`dev`/`demo`/`pilot`/`prod`) is defined, if anywhere, in config.
- Test files other than by grep; no test was run.
- Config YAML/JSON samples under `config/` or elsewhere in the repo.
- `__pycache__` binary hits ignored.

## CORRECTIONS after independent review (review-window-end.md, 2026-11-16)
The recommended choke point "wrap at app.py:162" is NOT enough: cli.py:150 (gate) and cli.py:221-222 (replay) build their own llm and bypass it; the true choke point is NetworkLLM.chat (llm/common.py:208), which all four real kinds inherit, checked per retry attempt (_retry, common.py:233). Also: a stage field exists (config.py:317 environment dev/pilot/prod; no "demo" yet), Limits has no clock (models.py:19; app.py:73 clock goes only to Approvals), guard/bedrock_guardrail.py:101 and demos/ask-your-data/askdata/pipeline.py:155 are further paid-call sites, and app.py:90-98 does not refuse llm= in pilot/prod. Details and file:line in review-window-end.md.
