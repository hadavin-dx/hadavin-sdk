# P8b round 2 resolve report (egm:egm-resolve, Opus 5.5)

Status: resolved (categorised; the ticket is NOT edited here; the author writes revision 3 from this file)
Target: `handover/tickets/P8b.md` revision 2 (338 lines; path class other). Inputs: `P8b-round2-adversarial.md` (R2-ADV-1..19: 1 Blocker, 8 Major, 7 Minor, 3 Nit) and `P8b-round2-correctness.md` (R2-COR-1..13: 1 Major, 8 Minor, 4 Nit).
Gate: the skill's "wait for the user" step is skipped (auto mode, per the brief). The skill's default file name `goldfish_review_report.md` is replaced by this file (brief). Nothing is escalated to the owner. New PENDING LEAD items continue the ticket's numbering (8 onward).
Round rule: order 20 item 6 (`LEAD-ORDERS.md:80`) caps P8b at 3 rounds counting from round 1, and P8b is not a money or redaction package, so **round 3 is the last**. After round 3, remaining Minors are fixed in the build notes, then freeze, then the build-start review (order 20 item 3, order 21 item 17).

## Honest note (what I did NOT check, first)
- I ran nothing through `uv`. The Python one-liners ran with plain `python3 -I` on the worktree `src/`. I checked with `git diff --quiet origin/main -- <file>` that `backends/table.py`, `config.py` and `README.md` are identical to `origin/main` at `4ec3616` (origin/main moved again since the ticket's `397ec97`; worktree HEAD is `ef6eee6`).
- The awk ran on mawk 1.3.4 only. The two `sh` scripts ran on dash (`/bin/sh` here) with `sh -n` and on scratch pages that I generated from `roles.txt`. These are not real pages, and gawk and busybox were not tried.
- I did not run `egm:egm-drift-report`. I read its SKILL.md to learn its rules (it reports logic "not referenced in a design or README" as drift, and it has no INFO class).
- `ledger_check.py`, `ledger_lint.py` and the P0d waiver format are in the studio repo, which I cannot see. Nothing about T3 changes here.
- The ledger kept growing while I worked (its last commit moved from `0ab42a8` to `5ce76c1`). The counts below are "read at that moment".
- None of my runs is evidence. The runner re-runs everything.

## Facts I checked myself
- **Git:** `handover/` is not on `origin/main`. It is on branch `core/cloud-handover` (`git ls-tree origin/main handover` prints nothing). `docs/` on main holds only the two Slack files. So R2-ADV-1 and R2-COR-1 are TRUE: an `origin/main` sha identifies neither the pages nor the ledger.
- **`tools/` exists on main** (`scan_repo.py`, `scan_allowlist.txt`, `scan_banned_extra.txt`). `tools/proof_pack.py` does not. CI runs `python tools/scan_repo.py` (`.github/workflows/ci.yml:83`), and it scans git-tracked files.
- **`src/hadavin_sdk/defaults.py` exists on main.** There is no `guard/textnorm.py`, and no `usage`, `meter`, `stop_state` or `diagnostic` module.
- **Environment refusal on main:** `config.py:366-369` refuses every `DEV_ONLY` pair when `environment != "dev"`. `config.py:391-392` refuses `NOT_PROD` pairs only when `environment == "prod"`. `DEV_ONLY` closes at `table.py:602`.
- **plan-v3 section 9:** the test-path rows are lines 174-184. Line 173 is "Every v1 code row merged", 185 is the ledger row, 186 is "Demos re-pinned", 187 is the proof pack (`tools/proof_pack.py`) and 188 is Drift ("studio repo: `egm:egm-drift-report`"). Line 190 limits the P8b duty to "All test files named above".
- **Root README on main, line 31:** none of the three phrases matches (`grep -ciE` gives 0). The revised T6 run on the real main README prints three `MISSING-PHRASE` lines, rc 1.
- **Orders 14, 15 and 19:** the retracted wordings are "plain and re-cased" (order 15, `LEAD-ORDERS.md:44`) and "caught by nothing in v1" (order 19 C, `:67`, which retracts order 14, `:38`). No order forbids "covered" or "all copies". Order 19 B (`:66`) already makes the lead show the owner the short-password limit.
- **Ledger:** line 1 `# Cloud ledger` and line 358 `## P4d round 3 (reviewed commit b215b50)` are prose lines without a pipe. No line in the ledger has a pipe without starting with one. The revised awk (below), run on the live ledger, gave rc 1 with `rows=1694 bad=251 unresolved_blocker_major=727` (OPEN 585, FIXED-UNVERIFIED 142), 0 `BAD-NO-ARTIFACT` and 0 `BAD-STRAY`. Rows with 5 cells rose to 262 by the end of my work. The last row, `R3-P4c-COR-2`, is in 5 cells, so new rows still use the old layout.
- **Revised awk, fault results (mawk):** P1 `BAD-LAYOUT line 4 id BS-PX-1`, P7 rc 0, P8 rc 0 + `WAIVED`, P15 `BAD-HEADER count=0`+`NO-ROWS`, P16 `BAD-HEADER count=0`, P21 `BAD-NO-ARTIFACT WAIVED`, P22 `BAD-DUP ... lines 3 4`. New faults: P23 (empty artifact, and also `-`) `BAD-NO-ARTIFACT FIXED-VERIFIED BL-PX-2`; P24 (row indented with spaces, `> `-quoted or tab-indented) `BAD-STRAY line 4`; P25 (`| | | | | | | |`) `BAD-LAYOUT line 4 id `. All rc 1. Control (header, separator, one good row) rc 0. Prose headings and blank lines between tables are still accepted.
- **Revised T1 and T6 on scratch pages:** the control gives rc 0 for both scripts. Every fault listed in the table under "R2-ADV-5" gives rc 1 with exactly the named line.

## Decisions

| id(s) | category | decision for revision 3 |
|---|---|---|
| R2-ADV-1 = R2-COR-1 (Blocker; Major) | PROPOSE FIX | TRUE (Facts, Git). Each evidence file records the commit of the tree it read: the core files record `base` (origin/main) and `head` (the docs PR branch). The ledger files record the `core/cloud-handover` commit, after a clean-file check. A rebase makes the core files stale, and they are re-run. The lead re-runs at the merge commit (order 20 item 4). Text: R1 below. |
| R2-ADV-2 (Major) | PROPOSE FIX | TRUE. New run order: inputs first, then the ledger faults, then the pages, then the control run and the page faults in a named scratch copy (`cd`), then the real checks. Text: R2 below. |
| R2-ADV-3 = R2-COR-13 (Major; Nit), with R2-COR-12 (Nit) | PROPOSE FIX | TRUE. The artifact test now covers all four closed statuses (FIXED-VERIFIED included). New fault P23. The "Unresolved" definition gains "or any of these four with an empty or `-` artifact cell". Run-checked: 0 live rows fail it. Code: R3 below. |
| R2-ADV-4 (Major) | PROPOSE FIX (narrowed) | TRUE that hidden rows pass. The suggested rule "any non-blank non-pipe line is bad" is CONTESTED: ledger lines 1 and 358 are prose headings, so that rule would fail the real ledger for a reason that is not a fault. The narrower rule: a line that holds a `\|` but does not start with one prints `BAD-STRAY`. The separator must contain a `-`, so an all-blank row becomes `BAD-LAYOUT`. New faults P24 and P25. Code: R3. |
| R2-ADV-5 = R2-COR-7 (Major; Minor) | PROPOSE FIX (no new T7; folded into T6, order 8) | TRUE. T6 adds: the positive "production choice" rule; the 8 headings as exact lines; at most 60 lines; the not-a-kind line above heading 1 on the 7 non-table pages; the two "not the same as" links; the two A6 outlines inside heading 4. The T4 pass rule is defined (see R2-ADV-8). New faults P26 to P31. Code: R4 below. |
| R2-ADV-6 (Major) | PROPOSE FIX (partly CONTESTED) | TRUE for the two retracted wordings. `forbidden.txt` = "re-cased" and "caught by nothing", checked on every page and on the README paragraph (fault P27). "covered" and "all copies" are CONTESTED: no order forbids them (Facts, Orders), and "covered" is an ordinary word. A wrapped phrase already fails closed (`MISSING-PHRASE`), so the ticket only adds "each required phrase is written on one line". Owner-visible limit: one line citing order 19 B, `LEAD-ORDERS.md:66`. |
| R2-ADV-7 (Major), with R2-COR-4 (Minor) | PROPOSE FIX (cut) | TRUE that `tools/proof_pack.py` cannot exist before P8c. The detail "`tools/` does not exist yet" is wrong: it exists on main (Facts). Remove `tools/proof_pack.py` from `section9-list.txt`: plan line 190 limits the duty to test files, and P8c owns its own section 9 row (line 187). "Either order with P8c" stays. The COR-4 rewording goes into the same text. Text: R5. |
| R2-ADV-8 (Major) | PROPOSE FIX + PENDING LEAD 9 | TRUE: plan row 188 says "studio repo", and SKILL.md reports unreferenced logic as drift and has no INFO class. The INFO route is dropped (cut). "Open drift" gets a mechanical definition: a bullet in `drift.md` with no row in the lead-checked `drift-dispositions.md`. The narrower scope becomes PENDING LEAD 9. Text: R6. |
| R2-ADV-9 = R2-COR-6 (Major; Minor) | PROPOSE FIX | TRUE. Fixed content of headings 3 and 6 for the non-table pages. The outline sits under heading 4 only, and heading 8 repeats only the v1.1 row. T6 checks the heading-4 placement (P31). Text: R7. |
| R2-ADV-10 (Minor) | PROPOSE FIX | `sort -u`, an `IN-BOTH` check (`comm -12`), and an output-based rc (`t1.sh`, R4). Rule: if a name is in both lists, the table wins. The name is deleted from `extra-kinds.txt` and the page loses its not-a-kind line. Fault P32. |
| R2-ADV-11 = R2-COR-5 (Minor; Minor) | PROPOSE FIX | Data files carry no header. Each one generated from code gets a `<name>.log` holding the header and rc. The literal blocks are copied from the ticket. The full file list is in R2. `readme-redaction.txt` moves to a temporary folder inside `t6.sh`, and nothing is copied into the checkout root. The evidence folder sits on `core/cloud-handover`, never in the docs PR. |
| R2-ADV-12 (Minor) | PROPOSE FIX | Reword: "Every check except T4 and the T3 count check has a planted fault. P20's result is recorded by the lead on its first run; `ledger_lint.py` has none (tool not visible)." |
| R2-ADV-13 (Minor) | PROPOSE FIX + PENDING LEAD 8 | Line 293 becomes: "order 20 item 6: at most 3 rounds counting from round 1. This revision answers round 2, and round 3 is the last." Depends on gains item 5: "P8b's freeze and its build-start review (order 20 item 3; S0 EXIT per order 21 item 17, `LEAD-ORDERS.md:88`)". Who writes the pages and who runs the checks becomes PENDING LEAD 8 (order 6(c) and order 21 item 17 disagree). |
| R2-ADV-14 (Minor) | PROPOSE FIX (the suggested cut DECLINED) | Every count becomes "read at `<sha>`". Done item 2 says "the T1 set, derived at run time" instead of "15". If `_UNVERIFIED` is renamed, the `roles.txt` import fails with a non-zero rc in `roles.log`, which stops the run (fail closed); one sentence says so. The "not yet run live" label stays: it tells readers which backends were never run against the real service, which is the honesty rule, and it costs one label. |
| R2-ADV-15 (Minor) | PROPOSE FIX | One order: checks, then the draft PR review, then the fix batch, then a re-run of steps 5 and 6, then closing the rows, then the final ledger step (R2, steps 7-9). |
| R2-ADV-16 = R2-COR-3 (Minor; Minor) | PROPOSE FIX | TRUE (Facts, README). Files, Change: "Root `README.md`: the redaction paragraph is rewritten (it fails T6 on main today, fault P33)." |
| R2-ADV-17 + R2-COR-11 + R2-COR-2 (Nit; Nit; Minor) | PROPOSE FIX (one part DECLINED) | Cite `table.py:593-602`. Replace "the refusal in the client profile is named only if P6a is merged" with: "the page cites the refusal that exists now: `config.py:366-369` (dev-only pairs refused outside `dev`) and `config.py:391-392` (not-for-production pairs refused in `prod` only, so `pilot` allows them). A refusal that P6a adds later is caught by T4." The P6a condition is deleted, and with it the moot part of ADV-17. DECLINED: the `BAD-PROD-CHOICE` noise on "not a production choice". It is fail-closed on purpose, and pages use the label words only in the labels column. |
| R2-ADV-18 (Nit) | PROPOSE FIX | Add to "Existing core code reused": "`tests/contracts/` exists (store contract suite); it is cited by `store.md` heading 7 and not changed." |
| R2-ADV-19 (Nit) | PROPOSE FIX | Add to PENDING LEAD 6: "The lead spot-checks every rewritten severity against its review file before the T2 run." |
| R2-COR-8 (Minor) | PROPOSE FIX (partly CONTESTED) | TRUE for the modules: no textnorm, usage, meter, stop_state or diagnostic module exists on main. Reword: "textnorm, usage and meter are planned as single modules inside shared folders (their packages create them before P8a)". CONTESTED for `defaults.py`: `src/hadavin_sdk/defaults.py` is on `origin/main` (`git cat-file -e`), so "P8b does not touch it" is a true statement today. |
| R2-COR-9 (Minor) | PROPOSE FIX (reuse) | Reuse the existing scanner, with no new grep: step 6 runs `python tools/scan_repo.py` in the PR checkout after the pages are committed, saved as `E/scan.txt`; pass `rc=0`. |
| R2-COR-10 (Nit) | PROPOSE FIX | Both reviewers were off by one end. The test-path rows are `plan-v3.md:174-184` (Facts), and the ticket cites that. |

## Replacement texts (the Blocker and every Major)

**R1, Blocker R2-ADV-1 = R2-COR-1.** Replace the first paragraph of field "Evidence commands" (ticket line 190) and step 1 (line 191) with:

> All evidence files go under `handover/evidence/P8b/` on branch `core/cloud-handover` (written `E/`), never in the docs pull request. Two trees are read, and each evidence file names the one it read on its first line:
> - **Core files** (T1, T4, T5, T6, the scanner and the page faults) are run with the current folder at the core checkout on branch `core/P8b`. Their first line comes from `hdr_core`:
>   `hdr_core() { git fetch -q origin && git merge-base --is-ancestor origin/main HEAD && [ -z "$(git status --porcelain -- docs README.md CHANGELOG.md)" ] && printf 'base=%s head=%s\n' "$(git rev-parse origin/main)" "$(git rev-parse HEAD)" || { echo "HDR-FAIL core (not rebased on origin/main, or uncommitted page edits)"; return 1; }; }`
> - **Ledger files** (T2 and the ledger faults' control row) are run in the `core/cloud-handover` checkout. Their first line comes from `hdr_ledger`:
>   `hdr_ledger() { git diff --quiet HEAD -- handover/ledger.md && printf 'ledger_branch=%s ledger_commit=%s\n' "$(git rev-parse --abbrev-ref HEAD)" "$(git rev-parse HEAD)" || { echo "HDR-FAIL ledger (uncommitted ledger edits)"; return 1; }; }`
> - Every command is written as `{ hdr_core && <command>; echo "rc=$?"; } > E/<file> 2>&1` (or `hdr_ledger`). A header failure gives a non-zero `rc`.
> - Pass needs every core file of one run to carry the same `base` and `head`. After any rebase or new commit on `core/P8b`, the core files are stale: steps 5 and 6 (and step 7 if pages changed) are re-run.
> - Before merging, the lead re-runs steps 6 and 9 at the merge commit (order 20 item 4). Those files are the ones Done counts.
>
> 1. **Branch:** `git fetch origin && git switch -c core/P8b origin/main`, in the core checkout. Write `E/base.txt` with `hdr_core`.

In Done item 2, replace "at one step 1 commit, written as the first line of every evidence file" with: "with one `base`/`head` pair on every core file and one `ledger_commit` on every ledger file, from the final run (the lead's run at the merge commit)."

**R2, Major R2-ADV-2 (with R2-ADV-11, R2-ADV-15).** Replace steps 2 to 7 (lines 192-292) with this order. The code blocks are R3 and R4.

> 2. **Inputs, at the step 1 head, before any page exists.**
>    - Generated from code, data only: `E/table-keys.txt` (the T1 one-liner) and `E/roles.txt` (the T6 body). Each is written as `{ hdr_core && uv run python -c '<body>' > E/<name>.txt; echo "rc=$?"; } > E/<name>.log 2>&1`. A failed import (for example a renamed `_UNVERIFIED`) gives a non-zero `rc` and stops the run.
>    - Literal, copied from this ticket (no header): `extra-kinds.txt`, `phrases.txt`, `forbidden.txt` (`re-cased`, `caught by nothing`), `section9-list.txt`, `p8b_ledger_check.awk` (R3), `t1.sh` and `t6.sh` (R4).
>    - All evidence files: `base.txt`, the inputs above with `table-keys.log` and `roles.log`, `planted-faults.txt`, `t1.txt`, `t5.txt`, `t6.txt`, `scan.txt`, `drift.md`, `drift-dispositions.md`, `ledger-check-cloud.txt`, `ledger-check.txt`.
> 3. **Ledger faults** P1 to P8, P12 to P16 and P21 to P25. Each fault is a scratch file `"$S/<fault>.md"` with `S=$(mktemp -d)`, run as `awk -f E/p8b_ledger_check.awk "$S/<fault>.md"`. One line per fault (fault id, rc, first printed line) goes to `E/planted-faults.txt`.
> 4. **Write the 15 pages, the index, the README paragraph and the CHANGELOG line**, and commit them on `core/P8b`.
> 5. **Control run, then the page faults, in a scratch copy.** `S=$(mktemp -d); cp -R docs README.md "$S/"`.
>    - Control first: `(cd "$S" && E="$E" sh "$E/t1.sh" && E="$E" sh "$E/t6.sh")` must give rc 0. If it does not, the pages are fixed before any fault run.
>    - Then each fault of the T1 and T6 rows (P9, P10, P17 to P19, P26 to P33), each on a fresh copy, with the same command. P17 and P32 edit a scratch copy of `table-keys.txt` and point `E` at a scratch input folder.
>    - P11: the T5 loop of step 6 on a scratch copy of `section9-list.txt`.
>    - Results go to `E/planted-faults.txt`.
> 6. **Real checks in the core checkout:** `t1.txt` (`E="$E" sh "$E/t1.sh"`), `t5.txt` (the T5 loop), `t6.txt` (`E="$E" sh "$E/t6.sh"`) and `scan.txt` (`python tools/scan_repo.py`). Each uses the `hdr_core` form.
> 7. **T4 drift** (R6). After any page fix: commit, then re-run steps 5 (control only) and 6.
> 8. **Draft pull request and its review.** The reviewer reads the diff, this ticket and the evidence of steps 1-7. One fix batch, then a re-run of steps 5 (control) and 6 (and 7 if a page changed). The lead then closes P8b's own ledger rows, citing the fixing commit.
> 9. **Ledger checks last:** P20, then T2 (`{ hdr_ledger && awk -f E/p8b_ledger_check.awk handover/ledger.md; echo "rc=$?"; } > E/ledger-check-cloud.txt 2>&1`), then T3 as revision 2 wrote it (lead, laptop).

**R3, Majors R2-ADV-3 and R2-ADV-4: the awk.** It replaces lines 194-221. It was run-checked on mawk 1.3.4 (Facts):

```
BEGIN { FS="|" }
/^\| *id *\| *package *\| *severity *\|/ { hdr++; next }
/^\|[-:| ]+$/ && /-/ { next }
!/^\|/ && /\|/ { bad++; printf "BAD-STRAY line %d\n", NR; next }
/^\|/ {
  rows++
  id=$2; gsub(/ /,"",id)
  if (NF != 9 || id !~ /^[A-Za-z0-9]+(-[A-Za-z0-9]+)+$/) { bad++; printf "BAD-LAYOUT line %d id %s\n", NR, id; next }
  if (id in seen) { bad++; printf "BAD-DUP %s lines %d %d\n", id, seen[id], NR; next }
  seen[id]=NR
  sev=toupper($4); gsub(/ /,"",sev)
  st=$6; sub(/^ +/,"",st); split(st,w," "); s=toupper(w[1])
  if (sev!="BLOCKER" && sev!="MAJOR" && sev!="MINOR" && sev!="NIT") { bad++; printf "BAD-SEVERITY %s line %d\n", id, NR; next }
  if (sev!="BLOCKER" && sev!="MAJOR") next
  if (s=="FIXED-VERIFIED" || s=="WAIVED" || s=="OWNER-ONLY" || s=="IMPOSSIBLE-NOW") {
    art=$7; gsub(/ /,"",art)
    if (art=="" || art=="-") { bad++; printf "BAD-NO-ARTIFACT %s %s\n", s, id; next }
    if (s!="FIXED-VERIFIED") printf "%s %s\n", s, id
    next
  }
  open++; os[s]++; printf "UNRESOLVED %s %s\n", s, id
}
END {
  if (hdr != 1) { bad++; printf "BAD-HEADER count=%d\n", hdr }
  if (rows == 0) { bad++; print "NO-ROWS" }
  printf "rows=%d bad=%d unresolved_blocker_major=%d\n", rows, bad+0, open+0
  for (k in os) printf "  status %s: %d\n", k, os[k]
  exit (bad+open > 0) ? 1 : 0
}
```

Rules text under it: "A line that holds a pipe but does not start with one (indented, quoted or tab-indented) is `BAD-STRAY`. Prose headings and blank lines are allowed. A separator must contain `-`, so an all-blank row is read as a row and fails as `BAD-LAYOUT`. All four closed statuses need a non-empty artifact cell other than `-`." Because the escaped `\|` is gone from the bracket expression, the "`\|\|` written as `||`" sentence is deleted. New rows for the faults table:

| Fault | Planted row or change | Killed by | Expected |
|---|---|---|---|
| P23 | MAJOR, status FIXED-VERIFIED, artifact cell empty (and a second copy with `-`) | T2 artifact rule | rc 1, `BAD-NO-ARTIFACT FIXED-VERIFIED <id>` |
| P24 | a BLOCKER OPEN 7-cell row indented by two spaces (also run with `> ` and with a tab in front) | T2 stray rule | rc 1, `BAD-STRAY line 4` |
| P25 | `\| \| \| \| \| \| \| \|` | T2 (separator needs `-`) | rc 1, `BAD-LAYOUT line 4 id ` |

**R4, Major R2-ADV-5 (with R2-COR-7, R2-ADV-6, R2-ADV-10): `t1.sh` and `t6.sh`.** They replace the T1 "Pass" bullet (line 231) and the T6 `sh` block (lines 251-278). Both are POSIX `sh`, read their inputs from `$E`, use relative page paths, and are run with the current folder at the tree under test (the real checkout or the scratch copy). Run-checked on dash (Facts).

`t1.sh`:
```
E="${E:?set E to the evidence folder}"
t="$(mktemp -d)"
sort -u "$E/table-keys.txt" > "$t/k"
sort -u "$E/extra-kinds.txt" > "$t/x"
sort -u "$t/k" "$t/x" > "$t/want"
ls docs/kinds | grep -v '^README\.md$' | sed 's/\.md$//' | sort -u > "$t/have"
{ comm -12 "$t/k" "$t/x" | sed 's/^/IN-BOTH /'
  comm -3 "$t/want" "$t/have" | sed 's/^/SET-DIFF /'
  [ -f docs/kinds/README.md ] || echo "NO-INDEX"; } > "$t/out"
cat "$t/out"
if [ -s "$t/out" ]; then rm -rf "$t"; echo "t1_fail=1"; exit 1; fi
rm -rf "$t"; echo "t1_fail=0"; exit 0
```

`t6.sh`:
```
E="${E:?set E to the evidence folder}"
fail=0
tab="$(printf '\t')"
t="$(mktemp -d)"
# (a) labels of every Backends row, and the positive and negative "production choice" rule
while IFS="$tab" read -r kind be labels; do
  page="docs/kinds/$kind.md"
  row=$(grep -E "^\| *\`$be\` *\|" "$page")
  if [ -z "$row" ]; then echo "NO-ROW $kind $be"; fail=1; continue; fi
  for want in "config default" "dev only" "not for production" "open standard" "not yet run live"; do
    case ";$labels;" in *";$want;"*) code=1 ;; *) code=0 ;; esac
    case "$row" in *"$want"*) page_has=1 ;; *) page_has=0 ;; esac
    if [ "$code" != "$page_has" ]; then echo "WRONG-LABEL $kind $be '$want' code=$code page=$page_has"; fail=1; fi
  done
  case ";$labels;" in
    *";dev only;"*|*";not for production;"*)
      case "$row" in *"production choice"*) echo "BAD-PROD-CHOICE $kind $be"; fail=1 ;; esac ;;
    *)
      case "$row" in *"production choice"*) ;; *) echo "MISSING-PROD-CHOICE $kind $be"; fail=1 ;; esac ;;
  esac
done < "$E/roles.txt"
# (b) every page: the 8 headings as exact lines, at most 60 lines
cat "$E/table-keys.txt" "$E/extra-kinds.txt" | sort -u > "$t/pages"
while read -r k; do
  page="docs/kinds/$k.md"
  [ -f "$page" ] || { echo "NO-PAGE $k"; fail=1; continue; }
  for h in "## What it does" "## Interface" "## Backends" "## Single dependency" "## Identity and rights" "## Configuration keys" "## Tests that cover it" "## What it does not do"; do
    grep -qxF "$h" "$page" || { echo "MISSING-HEADING $k: $h"; fail=1; }
  done
  n=$(wc -l < "$page"); [ "$n" -le 60 ] || { echo "TOO-LONG $k $n"; fail=1; }
done < "$t/pages"
# (c) the seven non-table pages: the not-a-kind line above heading 1
while read -r k; do
  awk '/^## /{exit} /is not a kind in the backend table/{f=1} END{exit !f}' "docs/kinds/$k.md" || { echo "MISSING-NOT-A-KIND $k"; fail=1; }
done < "$E/extra-kinds.txt"
# (d) fixed sentences: no default, the two cross links, the two A6 outlines under heading 4
for k in audit llm; do
  grep -qF "no default; config must name one" "docs/kinds/$k.md" || { echo "MISSING-NO-DEFAULT $k"; fail=1; }
done
grep -qF "not the same as [detector](detector.md)" docs/kinds/redactor.md || { echo "MISSING-LINK redactor"; fail=1; }
grep -qF "not the same as [redactor](redactor.md)" docs/kinds/detector.md || { echo "MISSING-LINK detector"; fail=1; }
sec4() { awk '/^## Single dependency$/{p=1; next} /^## /{p=0} p' "$1"; }
sec4 docs/kinds/channel.md | grep -qF "second channel = email; trigger: a client needs email approvals" || { echo "MISSING-OUTLINE channel"; fail=1; }
sec4 docs/kinds/executor.md | grep -qF "per-contract none/manual/http; http refused in pilot and prod; manual not built" || { echo "MISSING-OUTLINE executor"; fail=1; }
# (e) redactor wording: required phrases (each on one line) and retracted wordings
awk '/Redaction is pattern-based and bounded/ {p=1} p && /^$/ {exit} p' README.md > "$t/readme-redaction.txt"
[ -s "$t/readme-redaction.txt" ] || { echo "NO-README-PARAGRAPH"; fail=1; }
for f in docs/kinds/redactor.md "$t/readme-redaction.txt"; do
  while IFS= read -r phrase; do
    grep -qiF -- "$phrase" "$f" || { echo "MISSING-PHRASE $f: $phrase"; fail=1; }
  done < "$E/phrases.txt"
done
for f in docs/kinds/*.md "$t/readme-redaction.txt"; do
  while IFS= read -r bad; do
    grep -qiF -- "$bad" "$f" && { echo "FORBIDDEN-PHRASE $f: $bad"; fail=1; }
  done < "$E/forbidden.txt"
done
rm -rf "$t"
echo "t6_fail=$fail"
exit "$fail"
```

The T6 bullet list in "Tests" (lines 153-157) becomes:
- (a) every Backends row has exactly the code's labels; a row with neither dev only nor not for production says "production choice", and any other row does not;
- (b) every page has the 8 headings as exact lines and at most 60 lines;
- (c) the 7 non-table pages have the not-a-kind line above heading 1;
- (d) the no-default sentence on `audit.md` and `llm.md`, the two cross links, and the two A6 outlines inside heading 4;
- (e) `redactor.md` and the README paragraph contain every phrase of `phrases.txt`, each written on one line, and no page contains a phrase of `forbidden.txt`.

The new T2 fault rows are in R3. The new T1 and T6 fault rows (all run-checked on scratch pages):

| Fault | Planted change (scratch copy) | Killed by | Expected |
|---|---|---|---|
| P26 | `detector.md`: the `regex` row loses "production choice" | T6 (a) | `MISSING-PROD-CHOICE detector regex`, rc 1 |
| P27 | append "Plain and re-cased copies." to `redactor.md` | T6 (e) | `FORBIDDEN-PHRASE docs/kinds/redactor.md: re-cased`, rc 1 |
| P28 | delete the line `## Tests that cover it` from `usage.md` | T6 (b) | `MISSING-HEADING usage: ## Tests that cover it`, rc 1 |
| P29 | pad `meter.md` to 61 or more lines | T6 (b) | `TOO-LONG meter <n>`, rc 1 |
| P30 | delete the not-a-kind line from `textnorm.md` | T6 (c) | `MISSING-NOT-A-KIND textnorm`, rc 1 |
| P31 | move the executor outline from heading 4 to the end of the page | T6 (d) | `MISSING-OUTLINE executor`, rc 1 |
| P32 | append `redactor` to a scratch `table-keys.txt` | T1 | `IN-BOTH redactor`, rc 1 |
| P33 | the root `README.md` of `origin/main` as it is (fail-before) | T6 (e) | three `MISSING-PHRASE ...readme-redaction.txt: ...` lines, rc 1 |

The fault count becomes 33: T2 18 (P1-P8, P12-P16, P21-P25; P7 and P8 are controls), T1 3 (P9, P17, P32), T6 10 (P10, P18, P19, P26-P31, P33), T5 1 (P11), T3 1 (P20). The step 5 control run is a named control, not a fault. P10's expected line set also includes `WRONG-LABEL secrets env 'not yet run live'` when the planted row drops every label; revision 3 says "at least the lines".

**R5, Major R2-ADV-7 (with R2-COR-4).** In Interface item 4, delete the line `tools/proof_pack.py` from the block. Change the cite to `plan-v3.md:174-184`. Replace "Two items are flagged in advance: …" with:

> Today only `tests/contracts/` and `tests/warden_port/` exist. Every other path is created by the package in column 2 before P8a, and T5 runs after all of them are merged, so only a path still missing then counts. `tests/test_redact*.py` is the one known mismatch: the replacement name comes from the P2d ticket. `tools/proof_pack.py` is not in the list: it is a tool, not a test file (line 190), and P8c owns its section 9 row (line 187).

**R6, Major R2-ADV-8.** Replace step 6 (T4, lines 281-285) with:

> **T4, the drift report.** Run in the core checkout at the step 1 head. The lead or the cloud (PENDING LEAD 8) invokes `egm:egm-drift-report` through the Skill tool on `docs/kinds/`, and saves the output as `E/drift.md`.
> - Each bullet in it gets one row in `E/drift-dispositions.md`: `| page | bullet (quoted) | FIXED <commit> | LEDGER <row id> | NOT-DRIFT <reason> |`. NOT-DRIFT is allowed only for "logic not described by the page" outside the 8 headings, and the lead checks each one.
> - **Open drift** = a bullet without a row. Pass: every `## ` section says "No drift detected", or every bullet has a row.
> - Frozen tickets and plan-v3 are not in scope, so the INFO route is deleted.
> - The plan row 188 run on the studio repo stays the lead's (PENDING LEAD 9).

Also delete "A ticket claim the code proves false is one INFO line" from the Source field and the CHANGELOG.

**R7, Major R2-ADV-9 (with R2-COR-6).** In Interface item 2, add under the heading list:

> For the 7 pages that are not table kinds, heading 3 holds one line, "Not in the backend table: `<module or rule>` (`file:line` once its package has merged)". Heading 6 lists the config keys that the part's own package added to `config.py`, or says "No configuration keys". The channel and executor outlines are written under heading 4 only; heading 8 repeats only the v1.1 row and its trigger. T6 (d) checks the heading-4 placement.

In item 4, replace "It is written in `channel.md` heading 8" and "It is written in `executor.md` heading 8" with "heading 4".

## Positions on the ticket's own PENDING LEAD items
- **1 (`docs/kinds/`):** keep the recommendation. It is now also needed by R1: `docs/` is on main, and the pages are in one PR branch.
- **2 (15 pages):** keep it, but Done counts "the T1 set derived at run time" (R2-ADV-14), so a table key added by P5c or P6b2 changes the count without editing the ticket.
- **5 (who closes the ledger):** keep (a). Nothing in round 2 changes it.
- **6 (cloud normalises 5-cell rows):** still needed and more urgent. 5-cell rows went from 178 (revision 2) to 262 by the end of my work, and the newest row is still in 5 cells. Add the R2-ADV-19 sentence.
- **7 (awk after each ledger write):** keep yes. It is the only thing that stops item 6 from slipping back, and the evidence above shows that it is slipping.

## Couplings
- **P8c:** with `tools/proof_pack.py` out of T5, P8b and P8c stay independent ("either order"), and P8c owns plan row 187.
- **P8a:** the corrected "Demos re-pinned" row (`P8a.md:78`) is unchanged.
- **P1, P2d, P5c wording:** `phrases.txt` and `forbidden.txt` follow the merged P1 wording. If that wording changes, both blocks change in the same revision.
- **P6a:** the pages cite today's refusal (`config.py:366-369`, `:391-392`). If P6a-1 or P6a-2 moves or adds a refusal, T4 reports it, and the page is fixed there.
- **Ledger:** R3 makes T2 stricter. That costs nothing today (0 artifact-less or stray rows), but any session that later writes FIXED-VERIFIED without an artifact now fails T2. PENDING LEAD 7 should name that rule too.
- **Order 20 item 4 / order 21 item 17:** R1's lead re-run at the merge commit is the existing lead step, not a new duty.

## PENDING LEAD (continuing the ticket's numbering)
8. **Who writes the pages and who runs the checks.** Order 6(c) (`LEAD-ORDERS.md:19`) says the lead runs P8 packages. Order 21 item 17 (`:88`) gives P8 packages the standing S0 EXIT, which under order 20 item 4 means the cloud builds on `core/<package>` and opens a draft PR.
   - Option (a): the cloud writes the pages and runs steps 1-8 and T2. The lead runs P20 and T3 on the laptop and re-runs steps 6 and 9 at the merge commit.
   - Option (b): the lead does everything.
   - Recommend (a): the later order wins, and the laptop steps stay with the lead. Reversible.
9. **The drift gate is narrower than plan row 188.** The row says "studio repo: `egm:egm-drift-report`, no open drift". P8b runs it on core `docs/kinds/` with the dispositions table (R6).
   - Option (a): accept the narrow P8b run, and keep the studio-repo run as the lead's final section 9 check (plan-v3 section 3: "the final checks of section 9" are the lead's).
   - Option (b): P8b must make the whole studio repo drift-free.
   - Recommend (a): the cloud cannot see the studio repo, and SKILL.md counts any logic not described in a doc as drift, so (b) has no reachable end for a docs package. The lead edits row 188's command column to name both runs. Reversible.

## Counts
- Findings: 32 ids (ADV 19, COR 13), in 22 decision rows after merging duplicates.
- PROPOSE FIX: 22 rows (every id is answered by one of them). Four of them are partly CONTESTED with cited evidence: R2-ADV-4 (rule narrowed: ledger lines 1 and 358), R2-ADV-6 ("covered" and "all copies": no order forbids them), R2-ADV-7 (the detail "`tools/` does not exist": it does), and R2-COR-8 (`defaults.py` exists on main). Two of them partly DECLINE a suggestion: R2-ADV-14 (the cut of "not yet run live") and R2-ADV-17 (the "not a production choice" noise; fail-closed is kept).
- Fully CONTEST: 0. ESCALATE to the owner: 0. New PENDING LEAD: 2 (8, 9).
- Planted faults: 22 become 33 (11 new: P23-P33).
- **Revision 3 needs:** R1-R7 applied word for word, the Minor and Nit rows above, the CHANGELOG entry for revision 3, the code-read header updated to `origin/main` `4ec3616`, and every count marked "read at `<sha>`".
- **Round 3 is the last round** (order 20 item 6). If it finds a Blocker, the lead decides (no round 4 for a path of class other). Minors left after it go to the build notes.
