P="/home/user/hadavin-sdk/handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v11.md"
t=open(P,encoding="utf-8").read()
def sub(old,new,count=1):
    global t
    n=t.count(old); assert n==count,(n,old[:80]); t=t.replace(old,new)
def line(prefix,new):
    global t
    ls=t.split("\n"); idx=[i for i,l in enumerate(ls) if l.startswith(prefix)]
    assert len(idx)==1,(len(idx),prefix[:60]); ls[idx[0]]=new; t="\n".join(ls)

# facts: F12 add glob, F16 add fifth site, F7 add call site
sub("Migrations `0001` to `0005` exist.","Migrations `0001` to `0005` exist. `migrate()` applies **every** file that `_migration_files` returns (`migrate.py:93-94`: `folder.glob(\"*.sql\")` on `store/migrations/`, not recursive) and `check_ledger` requires the numbers to run without a gap (`migrate.py:97`); a file in a sibling folder is never read.")
sub("assigns `.detector =` or `.llm =` after build (`tests/test_p5p6_followups.py:101`, `tests/test_p6_detectors.py:264,364`, `tests/test_k5_tools.py:608`)","assigns `.detector =` or `.llm =` after build (`tests/test_p5p6_followups.py:101`, `tests/test_p6_detectors.py:186,264,364`, `tests/test_k5_tools.py:608`: five sites)")
sub("`_limits_stop` (`:239-250`) ends a blocked run with `_to(...)` and **no card**;","`_limits_stop` (`:239-250`; called at `:359`, `:421` and `:460`) ends a blocked run with `_to(...)` and **no card**;")
sub("(`:239-250`), which runs at the start of the run and before every step (`:421`), is edited:","(`agent_loop.py:239-250`), which runs at the start of the run (`:359`), before every step (`:421`) and after each reply and before a tool result is used (`:460`), is edited:") if "(`:239-250`), which runs at the start of the run and before every step (`:421`), is edited:" in t else None
sub("all built by `app.py:160`","all built by `app.py:161`")
sub("In `cli.py`: `gate` (`:150`) and replay (`:221-222`)","In `cli.py`: `gate` (`cli.py:150`) and replay (`cli.py:221-222`)")
sub("`llm/retry.py` 20-110","`llm/retry.py` 31-108") if "`llm/retry.py` 20-110" in t else None
sub("`llm/__init__.py`. **Carried","`llm/__init__.py`. **Carried") if False else None

# 5.1 settings
sub("- `guardrail_usd_per_call: Money | None` (required and greater than 0","- Every number in `Config.spend` is checked **finite** at load (security minor N4: `reserve_margin`, `max_call_usd`, `guardrail_usd_per_call`, `unattributed_*`, `cli_*`, `max_plausible_tokens`); `reserve_margin` must be at least 1 and at most 100; a `NaN`, `Infinity`, negative or zero value is a `ConfigError` (test E0-S1-2). New: `max_plausible_tokens: int = Field(4_000_000, gt=0)` (my choice, unmeasured; the bound `clean_tokens` uses when a route has no `max_input_tokens`, 5.3 item 3), `unattributed_max_call_usd: Money | None` (required with a paid detector kind, greater than 0: the one-call cap of the approval summary screen), `cli_daily_usd` and `cli_monthly_usd: Money | None` (required with a paid llm kind, 5.8).\n- `guardrail_usd_per_call: Money | None` (required and greater than 0")
sub("5. **Config sites that need the new fields**","5. **Reserved agent ids (security minor N5).** The pseudo agents `-unattributed` and `-cli` (constants `UNATTRIBUTED_ID` and `CLI_ID` in `limits.py`) must never equal a real agent. `AgentRecord.id` (`registry.py:41`, a plain `str` today) gets a validator that refuses an id starting with `-`; test with an agent file named `-cli`. The grep I ran over `tests/` and `src/` for ids starting with `-` (`raw-greps-v11.txt`) found none; the S-1 builder re-runs it.\n6. **Config sites that need the new fields**")
open(P,"w",encoding="utf-8").write(t); print("part2 ok")
