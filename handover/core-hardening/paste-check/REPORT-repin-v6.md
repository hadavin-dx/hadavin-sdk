# REPORT repin v6 (C3b, fix pass after the round-2 reviews, 2026-11-16)
Builder: sub-agent (Sonnet 5.5). No sub-agents, no spend, made-up data only, nothing committed. This report is NOT a verdict: the lead runs the EGM reviews (EGM-GATE v1). Raw evidence: `evidence-c7g.md`. Sources of the findings: `review-v5-readiness.md` (M-1 to M-3, minors) and `review-v5-facts.md` (Majors 1 to 4, minors), plus the lead's message that asked for both.

## 1. FAILURES, UNVERIFIED and NOT RUN (read first)
1. **Nothing was run on the real target.** No PowerShell, no WSL, no Git for Windows, no n8n, no Docker. Every test ran in plain bash and dash on this Linux container (kernel 6.18) against stand-in folders, stand-in git repositories and stand-in processes. Not covered: Git Bash path forms, WSL `/proc`, a CRLF checkout, whether `patch` exists in Git Bash, how the Grep tool prints a count of 0.
2. **M-1 is only partly settled.** On this kernel the folder `/proc/<pid>` of a not-dumpable process stays owned by the user and only `/proc/<pid>/environ` belongs to root, so the v5 `stat` filter would have worked here. I could not test WSL's kernel. I changed the proposal to read the user id from the `Uid:` line of `/proc/<pid>/status`, which does not depend on that detail, and gave the lead a one-line test. That the real `n8n_kill.py` finds the same processes as this scan is still UNVERIFIED (UNVERIFIED 15 in the plan). `P-4b.sh` is still only a proposal.
3. **The acceptance rule still proves only text.** `print("exit 3")` passes (tested). The plan and the checklist now say so and make the lead's own reading of the `n8n_kill.py` lines the real check. I did not make the rule stricter than text matching, because a diff cannot show what a line does.
4. **`LEAD-GO` and `LEAD-YES` stay a procedural gate.** I added no technical control: the runner can write to the same file. The wording now says so in the plan, in `LEAD-FILL-list-v5.md` and in the checklist, and the claim "no default lets the runner give itself permission" is replaced by what is true.
5. **R2 with a leftover group member:** tested with stand-ins. If the leader is gone but a child is left, R2 stops and sends nothing (it cannot check the leader's environ). If the leader is a not-yet-reaped zombie, R2 also stops, with the older message "environ ... does not name"; both are safe stops, the second has a less exact text. `pgrep` is assumed to exist in WSL Ubuntu (`gone()` already relies on it).
6. **`ss` is not installed here**, so the port wait of `gone()` still saw no listener in section 8. Untested with a real listener.
7. **Negative control 4 of the P-4b tests is weak** (run as root, every `environ` is readable, so "no hit" is expected for any reason). Controls 1 to 3 are the real negative tests.
8. **Minors I could not map with certainty:** the round-2 review lists minors without numbers inside the facts review. I took readiness minors m-1 to m-7 in the order listed (m-2 = acceptance-rule stuck cases, which the task did not name but the review lists; I fixed it too). The facts review's "R5 sentence about gone() vs v4 N1": I could not find a sentence that is still wrong (the "Why:" sentence in the acceptance rule and the `gone()` text are consistent with the code); I changed nothing for it.
9. **Four inline spans still fail syntax after placeholders** (same 4 as v4 and v5: a lone `&` twice, two log-line examples). They are text, not commands; this is my reading, not a reviewer's.
10. The checklist commands were run only in the form A2 to A6 (patching, counts); C1 to C8 are the plan's own commands, tested through the plan extraction (fill, diff, last check, names check), not through the checklist file itself.

## 2. Files
- `plan-v5-repin-v6.patch` (270 lines, 15 hunks; `patch -p1` from `core-hardening/` after `plan-v5-fixes.patch`; replaces v5, which stays as superseded). Built against the pristine `inputs/plan-wp6-resmoke-v5.md` (sha256 starts `67a0a195537de875`, unchanged before and after).
- `LEAD-FILL-list-v5.md` (edited in place, same name): procedural-gate wording, Q1/Q4/Q9 fixes, the P-4b proposal with the `status` filter, the concrete stand-in recipe and the one-line test.
- `LEAD-CHECKLIST-v5.md` (new, M-2 and M-3): numbered lead checklist; commands copied by script from the patched plan.
- `acc5.sh` (new): reference implementation of the acceptance rule, with 18 test cases in the evidence.
- `evidence-c7g.md` (raw), this report, `checkpoint-v6.md`. `REPORT-repin-v5.md` item 4 corrected (the contradiction), marked superseded.

## 3. Finding table (patch line numbers approximate)
| id | finding | status | where |
|---|---|---|---|
| M-1 | no concrete stand-in recipe; uid filter unproven | fixed as far as testable: recipe (`exec -a n8n-stand-in python3 ... prctl(4,0,0,0,0)`), one-line test, filter changed to the `status` `Uid:` line, stat behaviour on this kernel stated; WSL UNVERIFIED | LEAD-FILL list, proposal section; evidence section 9 |
| M-2 | one 7,000-word paragraph | fixed: `LEAD-CHECKLIST-v5.md` (sections A to D, `EDIT POINT` marks, commands in separate blocks) | new file |
| M-3 | no way to make the patched plan | fixed: checklist A1 to A7 (order fixes patch then v6, checksum and CR check, dry-run, counts `24 10 2 1`, marker list) and A5 `git apply` fallback; tested: both routes give the same file | checklist; evidence sections 1 and 11 |
| m-1 | PROGRESS.md append-only | fixed in R5, step (d), the checklist and the list | patch hunks 1, 2 |
| m-2 | acceptance rule stuck cases (`return 3` with `sys.exit(main())`, comment line `exit code 3`) | fixed: three allowed kinds of `+` line, `return 3` counts, comments never count; 18 cases tested | patch hunk 2; `acc5.sh` |
| m-3 | patch names superseded `LEAD-FILL-list.md` | fixed (`-v5`) | patch, P-4b step |
| m-4 | Q1 says P-1 not started | fixed (P-3b runs after P-1 and P-2) | LEAD-FILL list Q1 |
| m-5 | step (e) should count first | fixed: Grep tool in count mode, content mode only to list lines | patch hunk 2; P-2 line |
| m-6 | S13 circular (13.4 before 13.5) | fixed: 13.4 and 13.5 always run in order; 13.6 to 13.9 only if 13.5 shows no n8n of this run | 13.1; list Q4 |
| m-7 | header says HEAD_PIN, command uses PIN | fixed: the plan says `PIN` is the full 40 characters and `HEAD_PIN` its first 7 | fill command text |
| report | REPORT v5 section 1 item 4 contradicted the plan | fixed in `REPORT-repin-v5.md` | |
| F-1 | acceptance rule proves only text | stated in the plan, list, checklist and `acc5.sh`; lead's reading required | see section 1 item 3 |
| F-2 | R2 checked only the leader (`/proc/$p`) | fixed: `pgrep -g` before "not alive", while waiting, before KILL and in the end line (`alive=no group=0`); tested with a child that ignores TERM (old block printed `alive=no` with 1 member left; new block waits, sends KILL, group 0) and with a dead leader (new: STOP) | R2 block |
| F-3 | procedural gate | reworded (see section 1 item 4) | step (d), WORDS, list |
| F-4 | positive control proves only a plan-shaped file | fixed: fourth check `^[*][*]RE-PIN [(]lead only[)]. FOUR places hold` must give 1 (the unpatched plan gives 0, the old three-count check printed `0 0 2` on it); wording of the third check narrowed | last check, step (e), P-2 |
| F-min | 13.1 order | fixed (m-6) | |
| F-min | stale name | fixed (m-3) | |
| F-min | "`<n>` only value the runner fills" | fixed: lists the other values and points to the placeholder paragraph | P-5 text |
| F-min | `2>/dev/null` after `<` | fixed in R2 (`2>/dev/null < file`); the P-4b proposal uses the same order; other uses are grouped or sit after `< /dev/null` | R2 block; proposal |
| F-min | R2 not-alive output undefined | fixed: `R2: pid <pid> is not alive and its process group is empty: nothing sent`, exit 0, accepted | R2 expected line |
| F-min | `--no-color` | added to the known-branch `git diff` | diff command |
| F-min | 16 versus 17 lettered cases | the P-3b tests have 16 lettered cases (A to R without F and M); the earlier "17" was wrong (17 is the number of marker texts) | evidence section 6 |
| F-min | evidence masked P-4b-HIT | section 9 now prints the raw hit line of the positive control | evidence |

## 4. Counts after both patches (evidence section 2)
`<FINAL[-]` lines 24; `LEAD-FILL [0-9]` lines 10 (17 marker texts); control pattern 2; patch-marker pattern 1; names check lists the same 10 places. Simulated fill and flip gives `0 0 2 1`; the unpatched plan gives `0 0 2 0` (the v5 three-count check gave `0 0 2` there). Wrong order: v6 on the original plan 5 of 15 hunks fail; v6 on fixes plus v5 patch 15 of 15 fail.

## 5. What I changed after first writing (honest log)
Reworded the proposal sentence about the stand-in twice (a nonsense phrase in step 2 of the recipe, and an unclear description of the expected output). Rebuilt `LEAD-CHECKLIST-v5.md` from the extraction so that every command is the plan's own text.
