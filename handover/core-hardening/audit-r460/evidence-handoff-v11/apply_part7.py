import re
P="/home/user/hadavin-sdk/handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v11.md"
t=open(P,encoding="utf-8").read()
def sub(old,new,count=1):
    global t
    n=t.count(old); assert n==count,(n,old[:80]); t=t.replace(old,new)
def line(prefix,new):
    global t
    ls=t.split("\n"); idx=[i for i,l in enumerate(ls) if l.startswith(prefix)]
    assert len(idx)==1,(len(idx),prefix[:60]); ls[idx[0]]=new; t="\n".join(ls)
def cell_row(prefix, fn):
    global t
    ls=t.split("\n"); idx=[i for i,l in enumerate(ls) if l.startswith(prefix)]
    assert len(idx)==1,(len(idx),prefix); ls[idx[0]]=fn(ls[idx[0]]); t="\n".join(ls)

# 7.1
def s1(r):
    r=r.replace("`Deps.gate`, `ALLOWED`; `NetworkLLM` constructor,","`Deps.gate`, `ALLOWED`; `NetworkLLM` constructor (`gate` required or `unmetered=True`), `ScopedDetector` type (not yet used), the reserved-id check in the registry,")
    r=r.replace("census C1, C2;","census C1, C2, C5; tests E0-S1-7;")
    i=r.rindex("| session 1 of 1")
    return r[:i]+"| **two sessions, fixed now (readiness minor 10)**: (1) `Config.spend`, `Money`/`Route`, the config checks, the five config sites, `llm/spend.py`, `SpendWindow`, tests E0-S1-2 to E0-S1-4; (2) `callgate.py`, `NetworkLLM` and the four kinds, `Deps`, `app.py`/`cli.py` order, `Limits(window)`, guardrail window check, census, import graph, E0-S1-5 to E0-S1-7. Session 2 starts from session 1's commit on the same branch; the checkpoint note says which session is running |"
cell_row("| 1 | **S-1** |",s1)
def s2(r):
    r=r.replace("`POLICY_STOP_REASONS` not yet;","`POLICY_STOP_REASONS` (moved here from S-2b), `ScopedDetector` use and `Limits.unattributed_scope`, `injection_check(spend=)`, release on 400/401/403/404/422, one-call bound, audit rows for failed settle and give-back, guardrail one request (5.7), CLI shared total (5.8);")
    return r
cell_row("| 2 | **S-2a** |",s2)
cell_row("| 3 | **S-2b** |",lambda r:r.replace("card once per day and `POLICY_STOP_REASONS`;","card once per day;").replace("store timeouts and `tcp_user_timeout`;","store timeouts, `tcp_user_timeout`, `spend_totals` in a transaction, reconnect (5.5b);"))
line("| 4 | **S-3** |","| 4 | **DB-1** | migration `0006` held in `store/migrations_held/`, the runner gate `store/owner_gates.py`, its tests, the pre-flight repair (5.6 item 1). **Merging DB-1 does not apply the migration**: applying needs the owner's yes and one lead PR that moves the file and adds the `OWNER_YES` entry | U | none (it may be built in parallel with S-1; merged after S-2b so the code-level refusal ships first; the lead may reorder) | one short session |\n| 5 | **S-3** | **not code**: the owner sets a monthly spend limit at the provider (or a prepaid balance) | n/a | **POST-DEMO, needs a new owner yes** | owner |")
line("| side | **DB-1**","")
t=t.replace("\n\n| later | L-1","\n| later | L-1",1)
line("Merge order: S-1, S-2a, S-2b.","**Start gates for S-1 (all must hold; none is mine to grant):** (1) the lead resumes core (L4, answer Q28); (2) two independent reviewers have read this document (answer Q33); (3) **the owner has answered D5** (money unit, section 1; needs-owner). Merge order: S-1, S-2a, S-2b, DB-1. Each head runs the full suite once at its final head (rule `faster-builds` rule 3). Critical path: S-1 (2 sessions), S-2a (2), S-2b (1), DB-1 (1): **6 builder sessions of up to 60 minutes plus review rounds**; to be re-baselined on the real clock; **core is paused, so nothing starts before the lead resumes it**.")

# 7.2 gate4 row
sub("(runs `ruff check`, `ruff format --check`, `pytest`, `bandit -q -r src demos -ll` with `echo rc=$?` after each, the exact commands of `.github/workflows/ci.yml`; the last of them is `ci.yml:119`)","(five commands copied from `.github/workflows/ci.yml` and compared with it by `evidence-handoff-v11/check_gate4_vs_ci.py`: `ruff check src tests demos` and `ruff format --check src tests demos` (`ci.yml:76-78`), `pytest -q -m \"not live and not perf\" -rs` (`:87`), the timing tests alone `pytest -q -m perf -rs` (`:93`), and `bandit -q -r src demos -ll` (`:119`), each with `rc=$?`; the independent re-check found v10's script ran no paths, ran plain `pytest` (which would also run live and timing tests) and no timing step: fixed) |")
sub("| `E0-S1-1-{ruff,format,pytest,bandit}.txt` | four `rc=0` at the S-1 head; the same four at each later head (`E0-S2-1`, `E0-S2b-1`) |","| `E0-S1-1-{ruff,format,pytest,perf,bandit}.txt` | five `rc=0` at the S-1 head; the same five at each later head (`E0-S2-1`, `E0-S2b-1`). **`gate4.sh` is UNTESTED**: it was only syntax-checked with `bash -n` and compared line by line with `ci.yml` (`evidence-handoff-v11/raw-gate4-vs-ci.txt`); its first run is its first test; the timing step runs alone (rule `faster-builds` 2) |")
sub("| four `rc=0` | exists |","| five `rc=0`; script UNTESTED (see E0-S1-1) | exists |",1) if t.count("| four `rc=0` | exists |")==1 else None
open(P,"w",encoding="utf-8").write(t); print("part7 ok", t.count("four `rc=0`"))
