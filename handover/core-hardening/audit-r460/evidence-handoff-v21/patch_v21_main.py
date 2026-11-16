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
    "**L-2 as designed (dated; security major 5).** What DB-1 and DB-2 do not do: the runtime role still holds `UPDATE` on `spend` and `kill_switch`, so a bug or a hijacked process can still lower a total or switch the kill switch off; the records say it happened, they do not stop it. DB-3 (5.6 item 1(o)) is that control: four `SECURITY DEFINER` functions (`spend_reserve`, `spend_settle`, `kill_switch_engage`, `kill_switch_release`; not one `spend_add` with a delta, because a delta cannot tell a settle from a theft), `GRANTS` changed to `SELECT` on the three tables, `EXECUTE` on the functions to the roles of the one grant table (5.6c item 5), the guard of 5.6 (j) and the start-up check of 5.6c item 4 over them. Written: the design text, the held file and the reference code. **Not written:** the store code that calls the functions, the `GRANTS` change, the `function_grants` step, the review. **Steps with dates (UTC; IST is +5:30):** design text and prototype 2026-11-16; independent review due 2026-12-04 (security minor m8: if S-1 has not merged by 2026-11-27 the date moves by the same number of days and the lead is told in the same message; it never slips silently); store code PR (L-2) after the owner's yes L22. **Owner of each step: the lead.** Needs: Q28 (core resumed), L22, L23."
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
