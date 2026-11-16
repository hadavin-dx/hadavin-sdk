import re,sys
P="/home/user/hadavin-sdk/handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v11.md"
t=open(P,encoding="utf-8").read()
def sub(old,new,count=1):
    global t
    n=t.count(old)
    assert n==count,(n,old[:70])
    t=t.replace(old,new)
def line(prefix,new):
    global t
    ls=t.split("\n"); idx=[i for i,l in enumerate(ls) if l.startswith(prefix)]
    assert len(idx)==1,(len(idx),prefix[:60]); ls[idx[0]]=new; t="\n".join(ls)

# ---- header
line("# Core hardening hand-off v10","# Core hardening hand-off v11: spend track only (R460), 2026-11-16 UTC (same date in IST)")
sub("Replaces v9 for everything about spend. v9 and v4 to v8 stay as they are.","Replaces v10 for everything about spend. v10 and v4 to v9 stay as they are.")
sub("`CORE-PR-HANDOFF-v10-other-tracks.md`","`CORE-PR-HANDOFF-v11-other-tracks.md`",t.count("`CORE-PR-HANDOFF-v10-other-tracks.md`"))
sub("What changed from v9, finding by finding, with the test that fails on the old design: `v10-CHANGES.md`. Raw output of every check I ran: `evidence-handoff-v10/`.","What changed from v10, finding by finding, with the test that fails on the old design: `v11-CHANGES.md`. Raw output of every check I ran: `evidence-handoff-v11/`.")
sub("Round: 2 of the spend track after v9 (money path, no round cap).","Round: 3 of the spend track after v10 (money path, no round cap).")
sub("`evidence-handoff-v10/","`evidence-handoff-v11/",t.count("`evidence-handoff-v10/"))
sub("evidence-handoff-v10/","evidence-handoff-v11/",t.count("evidence-handoff-v10/"))
sub("CORE-PR-HANDOFF-v10.md","CORE-PR-HANDOFF-v11.md",t.count("CORE-PR-HANDOFF-v10.md"))
sub("import_graph_v10.py","import_graph_v11.py",t.count("import_graph_v10.py"))
sub("cite_check_v10.py","cite_check_v11.py",t.count("cite_check_v10.py"))
sub("snippet_check_v10.py","snippet_check_v11.py",t.count("snippet_check_v10.py"))
sub("banned_count_v10.py","banned_count_v11.py",t.count("banned_count_v10.py"))
sub("raw-import-graph-v10","raw-import-graph-v11",t.count("raw-import-graph-v10"))
sub("raw-cite-check-v10","raw-cite-check-v11",t.count("raw-cite-check-v10"))
sub("raw-greps-v10.txt","raw-greps-v11.txt",t.count("raw-greps-v10.txt"))

# ---- section 0
line("1. **An instruction conflict I could not settle","1. **Migration `0006` (the database rule \"a spend total may not be negative\") is settled by the lead's answer Q34 (`ORDERS.md` line 217): no veto, keep it, it ships with its own negative test and is applied only on an owner yes.** My v10 treated this as a conflict with my brief; the brief was wrong (the lead says so), so v11 removes the conflict, the \"lead's confirmation\" gate and the question L1. The migration is now the scheduled PR **DB-1** (merge order 4, section 7.1). Two things the lead should read: (a) the CHECK has one clause beyond Q34, `usd < 'Infinity'`, explained in section 5.6 item 1 with the plain alternative if the lead refuses it; (b) the owner yes is made enforceable, not only promised: the file waits in a folder the migration runner does not read, and the runner refuses it if it is moved without a written owner yes (5.6 item 1). S-1, S-2a and S-2b need nothing from DB-1; until DB-1 is applied the exposure of section 5.6 item 6 stays.")
sub("2. **Nothing was run except reads and read-only programs.** No test suite, no `ruff`, no `bandit`, no Postgres, no vendor call, no spend.","2. **Nothing was run except reads and read-only programs** (plus one `bash -n` syntax check of `gate4.sh`, which runs nothing). No test suite, no `ruff`, no `bandit`, no Postgres, no vendor call, no spend.")
line("6. **Why v9 failed","6. **Why v10 failed (details in `v11-CHANGES.md`).** Security review: 5 majors (the guardrail client can send two requests while one is reserved; a missing gate still lets a paid kind run unmetered; a spend refusal at the approval summary has no handler; one failed call can keep three worst cases, and a wrong key empties the day in four calls; the runtime role can still write any total, with a migration gate that was only process) and 8 minors. Readiness review: 6 majors (a test needs a constant from a later PR; the default scope contradicts `scope_missing`; migration 0006 not scheduled; seven versus nine PRs; the NEEDED-CHECK gate had no owner or format; S-1 passes a reserver it does not have) and 6 minors. Independent citation re-check: the script `gate4.sh` did not run the commands of CI, the import-cycle text understated the cycle that the planned edges create, and cite slips (a range past the end of a file, a line off by one, a missed test site, a missed call site).")
line("7. **Code I read this pass**","7. **Code I read this pass** (every cite below was opened by me unless it is marked \"carried\"): `store/migrate.py` 40-100 and 283-345, `guard/bedrock_guardrail.py` 25-66 and 90-110, `guard/injection.py` 60-101, `approvals/requests.py:37` and `approvals/cards.py:79` (the lines that call the check), `app.py` 150-215, `cli.py` 140-160 and 205-235, `limits.py` (whole), `llm/retry.py` 31-108, `runtime/agent_loop.py` 236-252 and 436-462, `store/postgres.py` 190-197, `tests/test_s5_runtime.py` 95-125, `.github/workflows/ci.yml` 36-125, `llm/protocol.py` 10-16. **Carried from v10** (read there, machine-checked by the citation programs, not re-read): the other cites of section 2 marked \"carried\", `llm/common.py`, `store/postgres.py` 405-440, `store/memory.py` 185-210, `k1b/loop.py`, `tools.py`, `guard/http.py`, `evals.py`, `extract.py`, `models.py`, `backends/factory.py`, `config.py`, `registry.py`, the demo meter files. **Not read:** `llm/gemini.py` and the other three kinds' request code beyond grep, `store/memory.py` outside spend, the bodies of the demo meter tests, the shape of each kind's error object (whether it carries a status the retry code can read).")

# ---- words
sub("**Release**: take a reservation back off without an answer. v10 releases only when our own gate refuses; it never releases after a request was sent (section 5.3).","**Release**: take a reservation back off without an answer. v11 releases in two cases only: our own gate refuses (no request was sent), or the provider answers with a definite client error (status 400, 401, 403, 404 or 422: the provider rejected the request itself). After any other failure once a request was sent, the reservation is kept (section 5.3).")
line("- **Money type exception.**","- **Money type (OWNER-OPEN, question D5; v11 grants itself no exception and picks no default).** CLAUDE.md says \"money is integers\". The money values that exist today are `Decimal` US dollars: `Reply.cost_usd` and `Verdict.cost_usd` (`models.py:294`, `:305`), `Route` prices (`config.py:57-58`), `Budget` (`registry.py:33-36`), the `spend` and `spend_month` tables (`store/migrations/0001_core.sql:87-92`, `0003_approvals_tick.sql:15-20`) and `runs.cost_usd` (`models.py:98`). Step 1 (S-1, S-2a, S-2b) adds **new** `Decimal` money values next to them (the `Config.spend` amounts, `Reply.booked_usd`, `SpendScope`, `Ticket`), because the store, `Limits`, `Budget` and every price are `Decimal` already and the two spend columns are `NUMERIC`. The owner's options, with the price of each in plain words: **(A)** keep `Decimal` US dollars for step 1 and for any later new table, as a written exception to the integer rule (no migration; the risk is rounding mistakes that integers avoid; the code never uses floats and always rounds a reservation up and a limit down); **(B)** whole nano-dollars (1 nano-dollar = 0.000000001 US dollar) in `BIGINT` for a **new** table only, the existing `Decimal` values stay (two money units in one code base and one conversion function); **(C)** integers everywhere (a migration of both spend tables and a rewrite of every reader and every price field; the largest change, the most consistent with the rule). **No option is the default.** S-1 does not start until the owner answers D5 (section 7.1, start gates), and the answer is written into this section. Review-by date 2026-12-31: if D5 is still open on that date, the gate stays closed and the lead tells the owner.")
open(P,"w",encoding="utf-8").write(t)
print("part1 ok")
