P="/home/user/hadavin-sdk/handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v11.md"
t=open(P,encoding="utf-8").read()
def sub(old,new,count=1):
    global t
    n=t.count(old); assert n==count,(n,old[:80]); t=t.replace(old,new)
def line(prefix,new):
    global t
    ls=t.split("\n"); idx=[i for i,l in enumerate(ls) if l.startswith(prefix)]
    assert len(idx)==1,(len(idx),prefix[:60]); ls[idx[0]]=new; t="\n".join(ls)

line("`GuardrailDetector.__init__(client, guardrail_id, version, threshold, gate=None","`GuardrailDetector.__init__(client, guardrail_id, version, threshold, *, gate, usd_per_call=None, unmetered=False)` (same rule as the llm kinds: a gate, or `unmetered=True` said out loud, 5.3); `make(settings, deps)` (`bedrock_guardrail.py:61`) reads `deps.gate`. In `check`, **after** the empty-text return (no request, nothing reserved) and the redaction, and **before** `apply_guardrail` (`:101`): `ctx = CallCtx(route=None, worst=usd_per_call * GUARDRAIL_MAX_REQUESTS, kind=\"fixed\")`; `ticket = gate.admit(ctx)`; then `try:` the `apply_guardrail` request, `finally: gate.keep(ticket, ctx)`. The attempt is **kept** after success or failure (the price is a fixed number, so there is no settle; `keep` adds it to the run's cost through `scope.kept`). `admit` runs the window check (S-1) and, from S-2a, reserves against the run's scope, or, on the approval summary screen, against `-unattributed` through `ScopedDetector` (5.5). **One request per check (security major M1: v10 reserved one price while the vendor client could send two requests, `bedrock_guardrail.py:36` sets `total_max_attempts: 2`, and a billed timeout followed by a re-send is two bills):** `defaults.GUARDRAIL_MAX_REQUESTS = 1` is the single source; `_client` takes `total_max_attempts` from it for the **runtime** client only (the start-up client that reads the guardrail's settings keeps 2); a fail-closed check does not need the SDK's own retry, because `injection_check` turns an error into a flagged verdict, so one failed request is a stop (5.5). The reserve is `usd_per_call * GUARDRAIL_MAX_REQUESTS`, so if someone raises the constant the reserve rises with it. Test: build the runtime client with a stub that captures the `Config` passed to `boto3.client`, assert `total_max_attempts == GUARDRAIL_MAX_REQUESTS`; mutant: set 2. The detector lets `SpendRefused` rise; `injection_check` handles it per 5.5. The price comes from the operator's config (read from the vendor's page that day), so no vendor price is in our code; a wrong number is a config error the invoice comparison catches. This pulls v9's L-5 into S-2a. The window-only part is in S-1 and works with `llm.kind: fake` (5.2).")

# 5.8
sub("`ProcessCap(max_usd)` in `llm/callgate.py` is a `Reserver` that keeps one in-memory total behind a lock and refuses `>=` the cap (`daily_budget`).","`ProcessCap(max_usd)` in `llm/callgate.py` is a `Reserver` that keeps one in-memory total behind a lock and refuses `>=` the cap (`daily_budget`). **It caps one invocation only** (security minor N5): a cron job that starts the command every hour spends `--max-usd` each time. So when `cfg.backends.store` is configured and is not the memory kind, the command also reserves through `Limits` under the scope `CLI_ID` (`-cli`), whose daily and monthly limits are `spend.cli_daily_usd` and `spend.cli_monthly_usd` (5.1), so repeated invocations share one total in the store; with the memory store the command prints \"cap applies per invocation only\" on stderr and the `limits status` line says so. The pseudo ids cannot collide with a real agent (5.1 check 5).")
sub("The command opens a `SpendScope(\"-cli\", daily=max_usd, monthly=max_usd, max_call=max_usd)` around the work.","The command opens a `SpendScope(CLI_ID, daily=max_usd, monthly=max_usd, max_call=max_usd)` around the work (with the shared store, the smaller of these and the `cli_*` limits).")

# 5.9
a=t.index("| 1 | reservation is a ceiling for output")
b=t.index("### 5.10")
new='''| 1 | reservation is a ceiling for output, and the usage we read is what is billed | one request's output stays within `max_tokens` (anthropic and bedrock by the code; **gemini and OpenAI-compatible hidden reasoning tokens UNVERIFIED**, F15); the reported usage includes everything billed | (a) real cost above the reservation: settle books the reported cost afterwards, only the admission check was too optimistic. (b) billed tokens that the reply does not report: **never booked, a permanent under-count** | (a) the excess of one request; (b) the unreported share of every call | stated; `high` counts are booked at no less than the worst case (5.3 item 3); the only catch for (b) is the invoice comparison (7.3) |
| 2 | input is counted completely | cached tokens inside the reported input count | cached tokens outside it are not booked: **a permanent under-count on every call, settle cannot correct it** (v10 called this safe by omission) | the cached share of the input of every call | none today (no kind sends a cache marker, guard test); UNVERIFIED for automatic vendor caching; invoice comparison only |
| 3 | input estimate is high enough | `reserve_margin 3` and the 3-characters-per-token estimator | text with few characters per token (Chinese, base64) is under-reserved | admission too optimistic by up to the estimator error for such text; settle books the true cost after | **unmeasured**; stated; needs real replies (L2) |
| 4 | a price tier is not crossed | `max_input_tokens` and the dated tier list | a tier applies to the whole call | cost per call above the flat price: **a permanent under-count if the tier is crossed** | `tiered` refused; list dated and UNVERIFIED; invoice comparison |
| 5 | an errored request is billed or not | statuses 400, 401, 403, 404, 422 are not billed (released); every other failure after the request was sent is billed (kept) | a released status was billed: under-count of that attempt; a kept failure was not billed: over-count | one attempt per such call | released set is small and dated; kept is the safe direction; L-6 may release more with invoice evidence |
| 6 | window end | host clock and request duration | request admitted at 23:59:59 billed after | one request in flight per process (5.2) | stated |

**What each row can do to a counter, stated without the v10 over-claim.** Rows 1(a) and 3 make the admission check too optimistic for one request, and settle then books the reported cost, so a counter does not stay low because of them. **Rows 1(b), 2 and 4 can leave a counter permanently low** (the vendor bills more than the usage we read), and row 5 can leave it low by one released attempt. Nothing in the code detects these; the only catch is the monthly invoice comparison with its 5 percent rule (7.3) and the provider-side limit S-3. Apart from these, the only way a counter goes down is a holder of the runtime role writing to the table directly (5.6 item 6).

'''
t=t[:a]+new+t[b:]

# 5.10
sub("**nano-dollar `BIGINT`** (D5 default)","money unit as the owner decides in D5")
sub("| any `spend_settle_failed` in a live window;","| any `spend_settle_failed` audit row in a live window;")
sub("| lead yes; D5 (POST-DEMO) |","| lead yes; **D5 answered** (no default) |")
sub("| L-6 | release a definite client error after the request | invoice over-count above the owner's tolerance two months in a row | invoice figures |","| L-6 | release 408, 429, 5xx and timeouts after the request (statuses 400, 401, 403, 404, 422 are already released in S-2a) | invoice over-count above the owner's tolerance two months in a row | invoice figures |")
sub("(v9's L-5, metering the guardrail, is now in S-2a.)","(v9's L-5, metering the guardrail, is in S-2a. The earlier L-6 for client errors is also in S-2a.)")
sub("S-1, S-2a and S-2b add **no** database role, table or grant.","S-1, S-2a, S-2b and DB-1 add **no** database role, table or grant (DB-1 adds a constraint).")
# 6
sub("census C3 `test_c3","census C3 `test_c3",0) if False else None
sub("C1 `test_c1_every_network_kind_passes_gate` (by `ast`: every `NetworkLLM` subclass `make()` passes `gate=deps.gate`;","C5 `test_c5_unmetered_only_in_tests` (no `unmetered=True` in `src/` or `demos/`), C1 `test_c1_every_network_kind_passes_gate` (by `ast`: every `NetworkLLM` subclass `make()` passes `gate=deps.gate`;")
sub("| yes, configured price (S-2a), run scope or `-unattributed` | kept, no settle |","| yes, configured price times one request (S-2a), run scope or `-unattributed` through `ScopedDetector` | kept, no settle |")
open(P,"w",encoding="utf-8").write(t); print("part6 ok")
