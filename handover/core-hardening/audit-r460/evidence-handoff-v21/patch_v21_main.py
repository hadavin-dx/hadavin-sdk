#!/usr/bin/env python3
"""Builds ../CORE-PR-HANDOFF-v21.md from ../CORE-PR-HANDOFF-v20.md (never edited) plus chunk_*.md.
Line numbers are those of the v20 file; every anchor is asserted so a changed v20 file stops the script.
usage: python3 -I patch_v21_main.py   (run inside evidence-handoff-v21/)"""
import re, sys, pathlib

here = pathlib.Path(__file__).resolve().parent
src = (here.parent / "CORE-PR-HANDOFF-v20.md").read_text(encoding="utf-8").split("\n")
L = lambda n: src[n - 1]


def chunk(name):
    return (here / name).read_text(encoding="utf-8").rstrip("\n")


def chk(n, start):
    assert L(n).startswith(start), (n, start, L(n)[:80])


FILL = dict(
    DB3_SHA="e2f8017c1975f88c251e6ec2426e3c54f89cf6a3dc61c7f0417d2e8473a075fb",
    DB3_SHORT="e2f8017c1975f88c...",
    PG_RUNS="five",
    REG_RUNS="two",
    GATE4_STATE=open(here / "gate4_state.txt", encoding="utf-8").read().strip(),
    PARTLY=open(here / "fill_partly.txt", encoding="utf-8").read().strip(),
    MEASURED=open(here / "fill_measured.txt", encoding="utf-8").read().strip(),
    RUNLIST=open(here / "fill_runlist.txt", encoding="utf-8").read().strip(),
    GUARD_OPEN=open(here / "fill_guard_open.txt", encoding="utf-8").read().strip(),
)


def fill(t):
    for k, v in FILL.items():
        t = t.replace("@@%s@@" % k, v)
    assert "@@" not in t, re.findall(r"@@\w+@@", t)
    return t


# anchors
chk(1, "# Core hardening hand-off v20")
chk(3, "Replaces v19")
chk(5, "**Core is paused")
chk(7, "## 0. What failed")
chk(29, "## 0-v20.")
chk(33, "## 1. Words used")
chk(306, "### 5.6 The database side")
chk(325, "   **(o) DB-3")
chk(326, "   **(o2)")
chk(327, "   **(p) What was run in v19")
chk(329, "### 5.6c What v20 changed")
chk(356, "### 5.7 The guardrail call")
chk(381, "### 5.10 Later PRs")
chk(394, "### 5.10b")
chk(396, "What DB-1 and DB-2 do not do")
chk(398, "## 6. Every paid path")
chk(507, "## 8. Evidence saved this pass")
chk(529, "### 8.1 Planned imports")
chk(562, "## 10. What I did NOT check")
chk(564, "**Not checked (nothing here")
chk(567, "**v20 additions to what was not checked.**")

out = []
out += [
    "# Core hardening hand-off v21: spend track only (R460), 2026-11-16 UTC (same date in IST)",
    "",
    "Replaces v20 for everything about spend (v21 is the round-8 batch: `v21-CHANGES.md` lists every change and where it is; `v21-OPEN-FOR-LEAD.md` lists what is the lead's or the owner's to answer). Everything that is not spend is in `CORE-PR-HANDOFF-v21-other-tracks.md`. Raw output of every check I ran: `evidence-handoff-v21/raw/` (older folders such as `evidence-handoff-v16/` stay and are named where a file is carried). **This text is one layer:** the v19 and v20 additions were folded into the sections where they belong and the sentences they replaced were deleted (what moved where: `v21-CHANGES.md`). **A sentence that contradicts another one is a defect: report it.**",
    "",
]
# line 5 paragraph, round number corrected
p5 = L(5).replace("Round: 5 of the current review loop of the spend track (money, secret and audit path, no round cap).",
                  "Round: 8 of the current review loop of the spend track (money, secret and audit path, no round cap).")
assert p5 != L(5)
out += [p5, ""]
out += [fill(chunk("chunk_sec0.md")), ""]
out += src[32:324]  # lines 33..324 (section 1 to item (n) of 5.6)
o = fill(chunk("chunk_o.md")).split("\n")
out += o
out += [""]
out += [fill(chunk("chunk_56c.md")), ""]
out += src[355:393]  # lines 356..393 (5.7 to the end of 5.10)
# 5.10b folded into 5.10: heading and the v17 history removed
l2 = (
    "**L-2 as designed (dated; security major 5).** What DB-1 and DB-2 do not do: the runtime role still holds `UPDATE` on `spend` and `kill_switch`, so a bug or a hijacked process can still lower a total or switch the kill switch off; the records say it happened, they do not stop it. DB-3 (5.6 item 1(o)) is that control: four `SECURITY DEFINER` functions (`spend_reserve`, `spend_settle`, `kill_switch_engage`, `kill_switch_release`; not one `spend_add` with a delta, because a delta cannot tell a settle from a theft), `GRANTS` changed to `SELECT` on the three tables, `EXECUTE` on the functions to the roles of the one grant table (5.6c item 5), the guard of 5.6 (j) and the start-up check of 5.6c item 4 over them. Written: the design text, the held file and the reference code. **Not written:** the store code that calls the functions, the `GRANTS` change, the `function_grants` step, the review. **Steps with dates (UTC; IST is +5:30):** design text and prototype 2026-11-16; independent review due 2026-12-04 (security minor m8: if S-1 has not merged by 2026-11-27 the date moves by the same number of days and the lead is told in the same message; it never slips silently); the store code that calls the functions is part of the DB-3 move PR (row 5b of 7.1; it is not a separate PR), written after the owner's yes L22. **Owner of each step: the lead.** Needs: Q28 (core resumed), L22, L23."
)
out += [l2, ""]
out += src[397:455]  # lines 398..455 (section 6 to the 7.1 table end / 7.2 heading)
out += src[455:506]  # lines 456..506 (7.2 body, 7.3)
# section 8: new
sec8 = open(here / "chunk_sec8.md", encoding="utf-8").read().rstrip("\n")
out += [fill(sec8), ""]
out += src[528:563]  # lines 529..563 (8.1, 9, 10 head)
# section 10: replace the Postgres sentence and drop the v20 additions paragraph
p564 = L(564)
a = p564.index("**Postgres:** what I ran is listed in 8")
b = p564.index("**Not run:** Postgres 17.10")
newpg = ("**Postgres:** what I ran is listed in section 8 (local version 16.15, scratch clusters, stopped and deleted afterwards): `raw/raw-pg-v21-run1.txt` to `-run5.txt` (run 1 and run 2 show failures that were my own wrong expectations; runs 4 and 5 are the final text: 210 safety checks, 31 controls, 3 stated exploits) and `raw/raw-pg-v16-regress-on-v21-run1.txt` and `-run2.txt` (175 of 175 checks each), including the migration step as a non-superuser role. ")
p564 = p564[:a] + newpg + p564[b:]
out += [p564]
out += src[564:566]  # 565, 566 (also-not-checked paragraph and blank)
# line 567 (v20 additions) dropped on purpose; continue from 568
out += src[567:]
text = "\n".join(out)

# ---- text edits on the carried sections (names and counts), asserted ----
def sub(old, new, count=None):
    global text
    n = text.count(old)
    assert n > 0, old
    if count is not None:
        assert n == count, (old, n)
    text = text.replace(old, new)


# ---- item (j): the v19 history folded into one live paragraph ----
def cut(old_start, old_end, new, include_end=True):
    global text
    a = text.index(old_start)
    b = text.index(old_end, a)
    if include_end:
        b += len(old_end)
    text = text[:a] + new + text[b:]


cut("   **(j) A guard test over every SQL file (security major 6 of v15;", "*Class:* a check that lists the bad shapes",
    "   **(j) A guard test over every SQL file (the rules and their tests are in 5.6c item 1, one place; this item keeps the allow-list shapes).** ", include_end=False)
sub("**Rules inside a function, kept from v18:**", "**Rules inside a function:**", 1)
sub("**New in v19 (MA1 and MA2 of the v18 review):** **N1**", "**N1**", 1)
cut("**Run on 16.15 (`evidence-handoff-v19/raw/raw-secdef-mutants-v19.txt`)", "(`raw/raw-spell30-guard-v19.txt`).",
    "**Rules added after S1 to S7 and N1 to N3 (bodies, calls, triggers, ASCII case folding, carriage-return comments, alias lists and the rest) are in 5.6c item 1.** **Run on 16.15 (section 0 item 5; raw files in section 8):** `secdef_mutants_v21.py` 226 checks, 0 failed (mutants of every earlier round, controls that must not be flagged, the independent runner's spellings, unit checks P3 to P11, the five held files and five product migrations clean); the v20 guard misses 12 of the 16 new v21 mutants; `spell30_guard_v21.py` flags 30 of 30 of the independent runner's spellings (`raw/raw-spell30-v21.txt`); `chk.py` finds no problem in the five held files and the five product migrations (`raw/raw-chk-v21.txt`). ")
cut("**there is still no independent run of v19:", "until a runner finds none.**",
    "**no independent run of v21 exists: earlier rounds each had spellings and bypasses the author did not think of, so expect more until a runner finds none.**")
sub("**v19 adds** the function", "It also holds the function", 1)
sub("v19 adds `SET LOCAL statement_timeout", "the file also sets `SET LOCAL statement_timeout", 1)
sub(" (v19 count; v18 said two functions and four triggers, which was stale since v16)", "", 1)
sub("**or the audit-reader role exists (v20, L19)**", "**or the audit-reader role exists (L19)**", 1)
sub("**v19 (security minor m1): a second trigger function", "**Second trigger function (security minor m1):** a second trigger function", 1)
sub("(all five of v17)", "(all five)", 1)
sub("`raw/raw-secrets-v19.txt` M3a to M3l (12 of 12; v19 adds a pre-check line", "`raw/raw-secrets-v21-run1.txt` M3a to M3l (12 of 12; the script has a pre-check line", 1)
sub("; v18 added the folder-mode test M3h", "; it also holds the folder-mode test M3h", 1)
# commands and names in the Postgres question (L18) and the gate paragraph
for old, new in [
    ("run_pg_v20.sh", "run_pg_v21.sh"),
    ("raw-pg-v20-run1.txt", "raw-pg-v21-run1.txt"),
    ("raw-pg-v16-regress-on-v20-run1.txt", "raw-pg-v16-regress-on-v21-run1.txt"),
    ("(the 177 checks;", "(the 210 checks;"),
    ("(the 175 v16 checks on the v20 files)", "(the 175 v16 checks on the v21 files)"),
    ("run_secrets_v20.sh", "run_secrets_v21.sh"),
    ("agent_probe_v20.py", "agent_probe_v21.py"),
    ("agent_probe_v19.py", "agent_probe_v21.py"),
    ("/opt/hv20", "/opt/hv21"),
    ("raw/raw-gate4-compare-v19.txt", "raw/raw-gate4-compare-v21.txt"),
    ("raw/raw-chk-v19.txt", "raw/raw-chk-v21.txt"),
]:
    text = text.replace(old, new)
sub("`gate4_v19.sh` itself has NOT been run; its first run is its first test;", "`gate4_v21.sh` was run once as one script in v21 on the unchanged tree (section 0 item 1);")
sub("a copy; v19 has `gate4_v19.sh`, not run)", "a copy; v21 has `gate4_v21.sh`)")
sub("it was syntax-checked with `sh -n` (v19) and its five commands", "its five commands")
sub("not re-compared in v19)", "not re-compared since)")
sub("written in v19, tested on four cases in", "tested on four cases in")


# ---- readiness M4, M5, M7 and the contradictions of 7.1 / 5.10 ----
sub("(`SECURITY DEFINER` function `spend_add`)", "(the four DB-3 functions, 5.6 item 1(o))", 1)
sub("The store code that calls the functions is the later PR L-2 (5.10) |", "The store code that calls the functions is part of THIS PR (start gate G-5(e); the empty-result handling of E0-F5 is S-2b-2's) |", 1)
sub("| 3 | **S-2b** | card once per day; `limits status`; store timeouts, `tcp_user_timeout`, `spend_totals` in a transaction, reconnect (5.5b); role setting check, `PostgresStore.startup_checks` (idle-transaction check and temporary-table check), `statement_timeout_ms`, `reconnect`, `PostgresSettings.audit_reader_dsn_secret` and the audit-reader read in `limits status` (5.5b items 1 to 6, 5.6 items 2 and 4) | U | S-2a | one session |",
    "| 3 | **S-2b** (delivered as **S-2b-1 then S-2b-2**, two builder sessions of at most 60 minutes each, one merge-order id; two PRs if the lead agrees, readiness major M7) | **S-2b-1:** card once per day; store timeouts, `tcp_user_timeout`, `statement_timeout_ms`, `spend_totals` in a transaction, `reconnect`; `PostgresSettings.audit_reader_dsn_secret` and the audit-reader read in `limits status` (5.5b items 1, 2, 5, 6). **S-2b-2:** `PostgresStore.startup_checks` (role setting check, idle-transaction check, temporary-table check), `store/secdef.py` with `secdef_problems` and `FUNCTION_POLICY` (5.6c item 4), `limits status --check` (5.6c item 5), the empty-result handling and test E0-F5 (5.6c item 3), `tests/test_secdef_startup.py` (5.5b items 3, 4 and 7, 5.6 items 2 and 4) | U | S-2a (S-2b-2 also S-2b-1) | two sessions |", 1)
# L24 and L25 rows of the conditional test table (readiness M5)
rows = ("| L24: volume of the decrease record | default of section 10 L24 (every ordinary settle below its reservation writes two rows, 5.6c item 5; no sampling) | the lead names a rule that writes fewer rows | `tests/test_decrease_log_pg.py` counts the rows of 100 ordinary settles (two per settle below its reservation) under the default; under another rule the count and the alert text change, nothing else |\n"
        "| L25: agent-id character set | the ASCII allow-list of 5.6c item 2 (`A-Z a-z 0-9 . _ : @ / + -`, first character a letter or digit, 1 to 200 characters) | the lead changes the set | `pg_v21.py` G12 (the ASCII cases), the DB-3 CHECK text, its pin in `allow_v21.py` and `tests/test_guarded_writes_pg.py` change together in one commit; the guard test names the file |\n")
anchor = "| L22: DB-3 (needs L23 as well) |"
assert anchor in text
text = text.replace(anchor, rows + anchor, 1)

# ---- section 10: the open questions as they stand in v21 ----
sub("Default: keep as built, alert only on kill-switch records and on decreases not made by `spend_settle`. Alternative:", "Default: keep as built; the status check alerts on kill-switch records only (5.6c item 5: a decrease made by another route cannot be told from a settle without L-1). Alternative:", 1)
sub("(select only on the three tables and execute on three functions, `spend_reserve`, `spend_settle` and `kill_switch_engage`; the operator role gets execute on `kill_switch_release` only and no table right; nobody else gets anything) and needs new store code (L-2).", "(select only on the three tables and execute on `spend_reserve` and `spend_settle`; the operator role gets execute on `kill_switch_engage` and `kill_switch_release` and no table right; nobody else gets anything: the one grant table of 5.6c item 5) and needs new store code, written in the DB-3 move PR (row 5b of 7.1).", 1)
sub("Who holds `kill_switch_release`:", "Who holds `kill_switch_engage` and `kill_switch_release` (the operator role):", 1)
a = "- **L21** (needs-lead, new in v16)"
assert a in text
newq = (
"- **L22b** (**OWNER-OPEN** choice of the lead, new in v21) **Who may call `kill_switch_engage`.** Default (least privilege): the operator role only; the runtime role cannot stop a run by itself, so an agent that finds a stuck loop asks a person (the cost: the agent process cannot switch the kill switch ON on its own; today the only caller is the operator command `limits stop`, `cli.py:391`, which runs as the operator). Alternative: the runtime role may also call it (one more `EXECUTE` right; engaging the switch is the safe direction, but a hostile runtime login could stop all runs). I did not decide; the default is built into `FUNCTION_POLICY`. Ask: which.\n"
"- **L26** (**OWNER-OPEN** choice of the lead, new in v21; security major M3 of v20) **A dedicated no-login owner role for the DB-3 definer functions.** Today every definer runs with the rights of the role that applied the file, which is the database or migration owner, so a bypass of the guard runs with full owner rights. Default: not built (the owner stays the migration role; the start-up check reports the owner it finds and the controls of 5.6c item 8 apply). Alternative: a no-login role that owns the four functions and holds only `SELECT, INSERT, UPDATE` on the three tables. Cost: one more role, its policy and negative test, and a change of the file and of `migrate()`. Ask: which.\n"
"- **L26b** (**OWNER-OPEN** choice of the lead, new in v21; security major M1 of v20) **The pseudo agent ids `-cli` and `-unattributed:<agent>` under DB-3.** The lead's default was: the store skips the DB-3 functions for them and keeps the old path. **That default cannot work as written:** after DB-3 the runtime role has `SELECT` only, so the old path is refused, and the CHECK of the file refuses those names. Two ways (5.6c item 8): (A) widen the agent-id rule to allow exactly these two shapes, or (B) a second table for them with its own functions. Until the lead chooses, DB-3 is not applied, and the file refuses an apply when such a row exists (shown in `pg_v21.py`). Ask: A or B.\n")
text = text.replace(a, newq + a, 1)
# current-folder names in the carried text
for old, new in [
    ("evidence-handoff-v20/gate4_v20.sh", "evidence-handoff-v21/gate4_v21.sh"),
    ("evidence-handoff-v19/gate4_v19.sh", "evidence-handoff-v21/gate4_v21.sh"),
    ("gate4_v19.sh", "gate4_v21.sh"),
    ("gate4_v20.sh", "gate4_v21.sh"),
    ("gate4_v18.sh", "gate4_v21.sh"),
    ("run_pg_v19.sh", "run_pg_v21.sh"),
    ("run_secrets_v19.sh", "run_secrets_v21.sh"),
    ("pg_v20.py", "pg_v21.py"),
    ("pg_v19.py", "pg_v21.py"),
    ("tests/test_startup_secdef.py", "tests/test_secdef_startup.py"),
    ("secdef_guard_v19.py", "secdef_guard_v21.py"),
    ("secdef_guard_v20.py", "secdef_guard_v21.py"),
    ("secdef_audit_v19.py", "secdef_audit_v21.py"),
    ("secdef_audit_v20.py", "secdef_audit_v21.py"),
    ("allow_v19.py", "allow_v21.py"),
    ("allow_v20.py", "allow_v21.py"),
    ("evidence-handoff-v19/held-sql/", "evidence-handoff-v21/held-sql/"),
    ("evidence-handoff-v20/held-sql/", "evidence-handoff-v21/held-sql/"),
    ("evidence-handoff-v19/", "evidence-handoff-v21/"),
    ("evidence-handoff-v20/", "evidence-handoff-v21/"),
    ("CORE-PR-HANDOFF-v20.md", "CORE-PR-HANDOFF-v21.md"),
    ("CORE-PR-HANDOFF-v19-other-tracks.md", "CORE-PR-HANDOFF-v21-other-tracks.md"),
    ("CORE-PR-HANDOFF-v20-other-tracks.md", "CORE-PR-HANDOFF-v21-other-tracks.md"),
    ("sha256-v19.txt", "sha256-v21.txt"),
    ("sha256-v20.txt", "sha256-v21.txt"),
]:
    text = text.replace(old, new)

# 5.10b is gone: every pointer goes to 5.10
text = text.replace("5.10b", "5.10")

pathlib.Path(here.parent / "CORE-PR-HANDOFF-v21.md").write_text(text + "\n", encoding="utf-8")
print("written", len(text))
