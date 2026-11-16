P="/home/user/hadavin-sdk/handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v11.md"
t=open(P,encoding="utf-8").read()
def sub(old,new,count=1):
    global t
    n=t.count(old); assert n==count,(n,old[:80]); t=t.replace(old,new)
def line(prefix,new):
    global t
    ls=t.split("\n"); idx=[i for i,l in enumerate(ls) if l.startswith(prefix)]
    assert len(idx)==1,(len(idx),prefix[:60]); ls[idx[0]]=new; t="\n".join(ls)
line("- `SpendRefused(ProviderError)` has `code`; codes:","")
t=t.replace("\n\n- `CallCtx`","\n- `CallCtx`",1)
sub("`reserve(scope, day, worst) -> Ticket` (raises `SpendRefused`), `settle(ticket, actual) -> None`.","`reserve(scope, day, worst) -> Ticket` (raises `SpendRefused`), `settle(ticket, actual) -> None`, `release(ticket) -> None`.")
sub("`SpendScope(agent_id, daily: Decimal, monthly: Decimal, max_call: Decimal, kept: Decimal, booked: Decimal)`","`SpendScope(agent_id, daily: Decimal, monthly: Decimal, max_call: Decimal, kept: Decimal = Decimal(0))`") if "`SpendScope(agent_id, daily: Decimal, monthly: Decimal, max_call: Decimal, kept: Decimal, booked: Decimal)`" in t else None

# 5.4 item 1
sub("1. Prices and budgets: `ge=0` and finite (5.1).","1. Prices, budgets and every `Config.spend` number: finite, `ge=0` (5.1; security minor N4: v10 applied the finite rule to `Route` and `Budget` only).")

# 5.5 scope / unattributed / injection_check / end states
sub("With the scope the gate no longer reads the registry.","With the scope the gate no longer reads the registry. **The approval summary screen has no agent** (`app.py:166-169`): `Limits.unattributed_scope()` returns `SpendScope(UNATTRIBUTED_ID, daily=spend.unattributed_daily_usd, monthly=spend.unattributed_monthly_usd, max_call=spend.unattributed_max_call_usd)` (all three required, 5.1; readiness major 2: v10 had no `max_call` for it and routed scopeless calls to it through a default). `app.build` wraps the summary detector in `ScopedDetector(inner, limits.unattributed_scope)` (in `llm/callgate.py`, duck-typed, passes `backend` through): it opens that scope around each `check`. Only that wrapper can book against `-unattributed`; any other paid call without a scope is refused `scope_missing`.")
sub("`injection_check` re-raises `SpendRefused` before its catch-all (`injection.py:89`).","`injection_check(detector, text, source, *, spend=\"flag\")` (`guard/injection.py:85`) catches `SpendRefused` before its catch-all: with the default `flag` it returns a flagged verdict with `reason_code=\"spend_refused\"`; the approval summary (`approvals/requests.py:37`) and the shadow card (`approvals/cards.py:79`) use the default, where a flag only adds the warning line, so a spend refusal can never raise out of the approval path or lock an approver out (security major M3); `Runtime._screen` (`agent_loop.py:312`) passes `spend=\"raise\"`, so a run stops through `_wall_stop`. Test: window ended and `-unattributed` at its cap, then an approval summary is built: no exception, the warning line is present, the approval can still be decided (E0-S2-4).")
# end-state table
a=t.index("- **End states** (the string is the run's `reason_code`")
b=t.index("- **Reason texts**")
new='''- **End states** (the string is the run's `reason_code`, written by `_to`, `:318-322`; readiness minor 8). Three different paths end a run on a spend limit and they must not be confused:
  (P1) **Our gate refuses before an attempt** (new): the table below. (P2) **`_limits_stop`** at the start of the run, before every step and after each reply (`agent_loop.py:359`, `:421`, `:460`): edited, same states, now with a card. (P3) **The existing check after a call** at the policy gate: a call whose real cost crossed the limit is `DENIED` with `limits.daily_budget`; it is unchanged and runs on the fake kind in `tests/test_s5_runtime.py:107-111`. With a network kind and a reservation, a call that would cross the limit is refused by P1 before it is sent (`NEEDS_PERSON`); P3 then only fires when the real cost exceeded the reservation.

| Code (path P1 and P2) | Run ends as | Reason string | Card |
|---|---|---|---|
| `kill_switch` | `STOPPED` | `kill_switch` | none (operator action) |
| `daily_budget`, `monthly_budget`, `window_ended` | `NEEDS_PERSON` | `limits.daily_budget`, `limits.monthly_budget`, `limits.window_ended` | once per agent, UTC day and code |
| `call_too_large`, `prompt_too_large`, `scope_missing`, `call_context_missing`, `abandoned`, `bad_amount` | `NEEDS_PERSON` | same words | yes, same rule |
| `limits_unavailable` | `NEEDS_PERSON` | `limits_unavailable` | once per agent, day, code (best effort) |
| `run_budget` (after the fact, existing) | `NEEDS_PERSON` through `_abstain` | `run_budget` | yes, as today |

- **`POLICY_STOP_REASONS` is added in S-2a** (readiness major 1: v10 put it in S-2b, but the S-2a test E0-S2-7 needs it): a constant beside `GUARD_STOP_REASONS` (`agent_loop.py:83`) listing the reason strings of the table above; K6 counts every non-null `caught_by`, so these stops stay `caught_by=None` (`.claude/rules/false-abstain-reporting.md`).

'''
t=t[:a]+new+t[b:]
sub("keys added are exactly the reason strings above;","keys added are exactly the reason strings above (plus `bad_amount`: \"A spend number was not valid, so no model call was made.\");")
# 5.5b
sub("a constant `POLICY_STOP_REASONS` beside `GUARD_STOP_REASONS` (`:83`) lists these codes for the false-abstain report.","`POLICY_STOP_REASONS` (added in S-2a, 5.5) is what the false-abstain report uses.")
open(P,"w",encoding="utf-8").write(t); print("part4 ok")
