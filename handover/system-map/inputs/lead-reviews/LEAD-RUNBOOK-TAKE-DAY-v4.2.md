# LEAD RUNBOOK, TAKE DAY, v4.2 (v4.1 patched for review round 31 and the owner decisions of 2026-11-16; duplicate-proof lead desk, n8n take)

## CHANGES v4.2 (patched from v4.1 by a document agent, writing only; nothing run; v4.1 file untouched; structure unchanged)

Sources: R31-D = `wp6\fix-p13\review-fix-13m\LANE-D-REPORT-SUMMARY.md` (section "Runbook v4.1 edits needed for r31", R1 to R6, and its X and Y findings); RESMOKE = `memory\owner-resmoke-ask-first-longer-ok-2026-11-16.md`; NOCAP = `memory\owner-no-review-cap-full-quality-2026-11-16.md`. "v4.1 line" is the line number in v4.1. **ROUND 33 PENDING** = the code is not final; the wording applies after r33 lands (pending items of review-fix-13m: Lane A X1 stderr for the exit-3 reason, X2 second Ctrl-C, X3 n8n.out refusal text and exit, X4 probe-folder trap, X5, X6 refusals about the n8n subfolder and parent folders; Lane D X6 final list of filesystems, X7 the exit-3 "do not signal anything by name" sentence). The Lane A report text for X5 is not in the inputs of this patch: where X5 matters the lead verifies at re-pin. Round labels: r26 (v4.1) is relabelled r31 wherever it describes current behaviour; history rows keep r23, r24, r26 and r28.

| # | Location (v4.1 line) | Old text (short) | New text (short) | Source |
|---|---|---|---|---|
| V1 | title (1) | v4.1 | v4.2 | this patch |
| V2 | CHANGES source note (39) | plan-review cap of 3 reached, no further review round | v4.1 said so; SUPERSEDED by owner 2026-11-16: no review cap for any finding that can change behaviour, quality, performance, money, redaction, process-kill or the take; findings that affect nothing are listed to the owner with fix time | NOCAP |
| V3 | Summary phase 3 (51) | Short loopback re-smoke, about 1 h, done about 09:30Z | loopback re-smoke only after the owner's yes; no 1-hour limit; the ask gives estimated clock times (UTC, IST) and cost | RESMOKE |
| V4 | Summary GO rules (70) | short re-smoke green | loopback re-smoke green (T-12, started only after the owner's yes) | RESMOKE |
| V5 | section 0 facts (89) | r26 design; `echo $$ > n8n.pid && exec n8n start >> n8n.out`; final probe with one 3 s retry | r31 design; inner sh `set -C; rm -f -- n8n.pid; echo $$ > n8n.pid`, n8n.out re-check (ROUND 33 PENDING), start line, `exec n8n start >> n8n.out 2>&1`; probe retried every 0.1 s up to 3 s before every exit 0 | R31-D R2 |
| V6 | section 0 facts (90) | (5) stop timing (r26) probe before SIGKILL; (6) other-user holder; (7) deleted and recreated | (5) SIGTERM, up to 45 s, SIGKILL, up to 5 s, then 3 s probe; (6) adds shared holder and two unreadable WSL helpers; (7) adds moved-and-recreated, a rename is safe | R31-D R2 |
| V7 | STOP-N8N (119) | r26 expect, exit codes 0/2/3/130, "counts and pids only" | r31: usage, time 45 + 5 + 3 s, every per-pid line, exit 0/2/3/130 texts and the exit-3 and 130 operator actions; exit-3 reason stream, second Ctrl-C and "do not signal anything by name" marked ROUND 33 PENDING | R31-D R3, X7 |
| V8 | variable `<FINAL_HEAD>` (127) | after r23, r24 and r26 (and r28 if it lands) | after r23, r24 and r31 (and r28 and r33 if they land) | R31-D R6 |
| V9 | schedule row (168) | Short loopback re-smoke, about 1 h, done about 09:30 | no 1-hour limit; after the owner's yes; times stated in the ask | RESMOKE |
| V10 | G1 (217) | short re-smoke green (T-12) | loopback re-smoke green (T-12, asked first) | RESMOKE |
| V11 | HS-12 proof (268) | on r26 | on r31 | R31-D R6 |
| V12 | section 8 heading (270) | then short re-smoke | then loopback re-smoke (asked first) | RESMOKE |
| V13 | T-02 expect (281) | r26 lock-on-take-folder commit(s) | r31 (and r33 if it lands) | R31-D R6 |
| V14 | T-04 plan texts (292) | r26 plan texts; on r26 | r31 plan texts; on r31 | R31-D R6 |
| V15 | T-08 step 0d (323) | ROUND 28 PENDING sentence; `-F` needs util-linux 2.31 | removed; "2.31" dropped (unverified); the script itself probes flock (fresh `.flock-probe.XXXXXX` folder), two refusal strings; 0d stays an early check; probe-folder cleanup wording ROUND 33 PENDING (Lane A X4) | R31-D R1, Y5 |
| V16 | CHANGES v4.1 row 11 (19) | adds ROUND 28 PENDING: `n8n_start.sh` checks `-F` itself after F4 | the script itself probes -F | R31-D R6 |
| V17 | T-08 step 7 (331) | r26: the outer shell waits | r31 | R31-D R6 |
| V18 | T-08 step 7 refusals (333) | allow-list of filesystems; "symlink or a folder"; script refusals exit 2 | the r31 refusal strings, "symlink, folder, pipe or device", exit 2 is not proof of a refusal; filesystem list, n8n.out and n8n subfolder refusals ROUND 33 PENDING | R31-D R4 |
| V19 | T-08 step 7 refusal paragraph (337) | after r26; STOP-N8N (it kills the holders) | after r31; STOP-N8N (it signals every same-user process that holds an EXCLUSIVE flock on the folder); shared lock or unseen holder: do not kill, record and ask the owner | R31-D R5 |
| V20 | T-08 step 10 (340) | it kills every holder of this folder's lock | it signals every same-user process that holds an EXCLUSIVE flock on the folder; exit 2 alone is not proof | R31-D R5, R4 |
| V21 | T-12 heading and intro (366, 367) | about 1 h | no 1-hour limit; new step 0 "ASK THE OWNER FIRST" | RESMOKE |
| V22 | T-12 step 1 (368) | same r26 lock design | r31 | R31-D R6 |
| V23 | W-03 step 4 (429) | after r26: 45 s grace plus the 3 s probe | after r31: 45 s wait, 5 s after SIGKILL and the 3 s probe | R31-D R6 |
| V24 | section 12 (497) | NOTE (14:35Z) makes it about 1 hour | superseded: no 1-hour limit, the lead asks first | RESMOKE |
| V25 | section 12 (499, 501), U-21 (527) | neither exists on r26; still works on r26; kept in r26 | r31 | R31-D R6 |
| V26 | U-04 (510) | patterns `flock\|refused\|holds\|exit\|111`, `stopped\|holding\|refused\|exit\|130`; after r26 | new patterns of R31-D R6; after r31 | R31-D R6 |
| V27 | U-10 (516) | Short re-smoke command | Re-smoke command | RESMOKE |
| V28 | W-05 take program items 5 to 7 (452 to 455) | ROUND 28 PENDING | unchanged on purpose (the take program is not in the snapshot) | R31-D R6 |

Not placed: R31-D X1, X2, X4, X5, X8, X9, X10 and Y1 to Y4, Y6, Y7 are code, comment or NEVER-DO-owner findings with no operator step in this runbook (X10: the existing "two stops at once: one may end 143 or 137: run once alone" sentence is in V7). Line 5 of v4.1 (source note) is history and stays. Every v4.1 CHANGES row below stays as written except row 11 (V16). Where a string below is not in the R31-D report, the lead verifies at re-pin.

## CHANGES v4.1 (patched from the frozen v4 by a document agent, writing only; nothing run; v4 file untouched; structure unchanged)

Sources: R26-D = `wp6\fix-p13\review-fix-13j\LANE-D-REPORT-SUMMARY.md` ("Runbook v4 edits needed"); R24-D = `wp6\fix-p13\review-fix-13i\LANE-D-REPORT-SUMMARY.md` ("RUNBOOK must state"); R24-A = `wp6\fix-p13\review-fix-13i\LANE-A-REPORT-SUMMARY.md`; OWNER-KEY = `memory\owner-api-key-already-placed-work-tuesday-2026-11-16.md`. "v4 line" is the line number in v4. ROUND 28 PENDING = code not final; the wording applies after r28 lands.

| # | Location (v4 line) | Old text (short) | New text (short) | Source |
|---|---|---|---|---|
| 1 | section 0 facts, r23 design (53) | `flock -n -E 10 -F <take>/n8n.lock` | r26 design: `flock -n -E 111 -F <take folder>`; `n8n.lock` file no longer exists | R26-D L53 |
| 2 | same bullet (53) | stop = holders of `n8n.lock` | stop = holders of the take folder FLOCK (device and inode), final probe with one 3 s retry | R26-D L53 |
| 3 | behaviour change (5) (54) | up to 20 s grace (real n8n needs about 8 to 10 s) | 45 s grace, 3 s probe, SIGKILL, 5 s wait; 20 s and 8 to 10 s not relied on | R26-D L54(5) |
| 4 | behaviour change (6) (54) | ends at (6) | adds (7): a take folder deleted and recreated while n8n runs is a new lock; never do it | R26-D F5 |
| 5 | STOP-N8N (83) | `... holding n8n.lock, all gone`, exit 0 (about 8 to 10 s), exits 2 and 3 | new texts (`holding the take folder lock`; `no process holds the lock of this take folder (an n8n started by hand is not seen): nothing killed`), exit codes 0/2/3/130 | R26-D L83 |
| 6 | PORT-FREE (84) | a "nothing held" stop (exit 0) | exit 0 = final probe found the lock free | R26-D L84 |
| 7 | variable `<FINAL_HEAD>` (91) | after r23 and r24 are merged | after r23, r24 and r26 (and r28 if it lands) | relabel r26 |
| 8 | HS-12 proof (232) | on r23 `n8n.pid` is n8n's own pid | on r26 | relabel r26 |
| 9 | T-02 expect (245) | r23 flock commit(s) and r24 merges | adds the r26 lock-on-take-folder commit(s) | relabel r26 |
| 10 | T-04 r23 plan texts (256) | `r23 plan texts`, `holds n8n.lock` | `r26 plan texts`, `holds the take folder lock` | R26-D L256 |
| 11 | T-08 step 0d (287) | flock check only | adds (v4.2): the script itself probes -F (see T-08 step 0d) | R26-D L287 / F4 |
| 12 | T-08 step 7 (295) | `r23: the outer shell waits` | `r26` | relabel r26 |
| 13 | T-08 step 7 refusals (297) | refusals incl. `n8n.lock` symlink, exit "2 or flock's own 10" | n8n.pid/n8n.out symlink or folder, filesystem allow-list, script refusals exit 2, held lock = internal 111 -> refusal text, exit 2 | R26-D L297 |
| 14 | T-08 step 7 refusal paragraph (301) | `holds n8n.lock` and the whole "Exit 10 (m5)" paragraph | new refusal text; Exit 10 paragraph deleted | R26-D L301 |
| 15 | T-08 step 10 (304) | `holds n8n.lock ...` | `holds the take folder lock ...` | R26-D L304 |
| 16 | T-12 step 1 (332) | same r23 lock design | r26 | relabel r26 |
| 17 | W-03 step 4 (393) | `after r23 ... the stop takes about 8 to 10 s` | `after r26 ... up to the 45 s grace plus the 3 s probe` | R26-D (grep 8 to 10) |
| 18 | section 12 (455) | neither exists on r23 | r26 | R26-D L455/457 |
| 19 | section 12 (457) | still works on r23 | r26 | R26-D L455/457 |
| 20 | U-04 (466) | patterns `flock\|refused\|holds\|exit`, `stopped\|holding\|refused\|exit`, "after r23" | `flock\|refused\|holds\|exit\|111`, `stopped\|holding\|refused\|exit\|130`, "after r26" | R26-D L466 |
| 21 | U-21 (483) | CLOSED by r23 | CLOSED by r23 and kept in r26 | relabel r26 |
| 22 | section 15 map row m5 (534) | `exit 10` row | notes that v4.1 removed the exit 10 paragraph | R26-D grep exit 10 |
| 23 | Summary, owner decision 4 (29) | API key file is placed by the owner | key already in local env and n8n credentials; re-placed only if T-08 step 0 finds it missing | OWNER-KEY |
| 24 | DECIDE-AT-REPIN-7 (72) | OWNER places the API key file | already placed; again ONLY if the check finds it missing, by name and count only | OWNER-KEY |
| 25 | W-05 after the Failure line (411) | (nothing) | new block "Take program behaviour the lead knows": 4 statements (Ctrl-C inert up to 120 s; further signal after 120 s may leave `result.json` absent, exit 3 plus console are the record; search HubSpot for `take-<tag>-a/-b/-c`; `the take could not run: ...` exit 2 or 3, `<withheld` = fix permissions) plus 3 ROUND 28 PENDING items (M1 window re-check after the prompts, M4 `result.json` write-once via `.tmp` and link, M5 `person C's post may still be in flight`) | R24-D, R24-A M1, M4, M5 |
| 26 | owner step O0 (501) | placed if folder, key file ... missing | only if the T-08 step 0 check finds something missing; name and count only | OWNER-KEY |
| 27 | owner step O0c (502) | only if no route gives ids | also only if the check finds a credential missing; name and count only | OWNER-KEY |

Other hits of the whole-file grep (`n8n.lock`, `exit 10`, `20 s`, `8 to 10`, `r23`) were checked: line 52 (r23 branch head and review status), line 48 (source list), line 255 ("20 strings") and line 495 ("r23 branch's review") are history or unrelated and stay as in v4. Not placed: R26-D "L256 / L287 / L297 / L304" are all placed (items 10, 11, 13, 15); F6 to F9 of R26-D are code-comment findings and have no runbook text. R24-A M2, M3, m1 to m6 and R24-D Minor 2, 3, Nits change no operator step and are not written here.

Written 2026-11-16 by a document agent from files only (round 4 = FINAL; v4.1 said: plan-review cap of 3 reached, no further review round. SUPERSEDED by owner 2026-11-16 (no review cap, full quality): further rounds run for every finding that can change behaviour, quality, performance, money, redaction, process-kill or the take; findings that affect nothing are listed to the owner with their fix and re-review time, never decided silently). NOTHING here was run: no command tried, no network, n8n never started, no process touched. Made-up data only. No secret, real address or id appears; placeholders stand for values the lead holds. Times: UTC first, then IST (IST = UTC + 5 h 30 min). Every minute figure is the lead's own estimate from the Q26/Q27/Q30 answers or this file's step estimates, never a measurement. Where a number is not in a source it says "lead sets at re-pin". No dollar figure is written anywhere in this file.

Step type (R455): MANUAL one-off procedure plus config. No shipping code. The lead writes small glue scripts (section 8A); each is a HARD STOP item (section 7) until its path and sha sit in the take notes. Who runs it: the LEAD (the Claude session). Rows marked **OWNER** are the only things the owner does.

## SUMMARY (one page)

**Phases in order (start times from the dated schedule, section 3):**

| # | Phase | Starts UTC | IST | Ends / note |
|---|---|---|---|---|
| 1 | Re-pin event T-01 to T-11 | Tue 17 Nov, no later than 04:17 | 09:47 | done by 08:00Z (13:30 IST); 223 min sequential estimate |
| 2 | Tue script block (8A, "needed Tue" list) | lead sets at re-pin | | written, reviewed, sha recorded before the 14:00Z GO |
| 3 | Loopback re-smoke on the harness (T-12), started ONLY after the owner's yes to the lead's ask | after 08:00 and after his yes | 13:30 at the earliest | no 1-hour limit (owner 2026-11-16); the ask states estimated clock times in UTC and IST and the cost; v4.1 estimate was about 1 h, done about 09:30Z (15:00 IST), no longer a limit |
| 4 | GO / NO-GO | Tue 17 Nov 14:00 (earlier if green) | 19:30 | rules G1 to G13 |
| 5 | Wed positive control, then practice (T19 to T21) | Wed 18 Nov about 06:00 | 11:30 | 60 min, to about 07:00Z |
| 6 | Row 4 (one made-up lead through real HubSpot trial account) | about 07:00 | 12:30 | 30 min |
| 7 | Rehearsal 1 and 2 | about 07:30 | 13:00 | about 2 h, to 09:30Z |
| 8 | Start-state gate, sign-off, GO check | 09:30 | 15:00 | about 25 min gate, decision by 10:00Z |
| 9 | THE TAKE | about 10:00 | 15:30 | about 1 h |
| 10 | Lead's watch of the recording, hand-over, owner clean-up, revoke, tear-down | about 11:00 | 16:30 | watch about 20 min; hand-over about 11:20Z |
| 11 | Owner edits (about 120 min) and posts | | | post Wed 18 Nov 15:00Z (20:30 IST); latest Wed 25 Nov 15:00Z |

**Five lead decisions 2026-11-16 (owner may veto; a veto replaces the default and nothing else):**
1. Reuse the owner's existing take n8n user folder and its credentials (DECIDE-AT-REPIN-1).
2. ONE filled flow set with the real HubSpot trial-account credential in every phase; no stand-in credential, no swap. Every new lead key in practice, rehearsal, Row 4 and take creates one made-up contact in the owner's throwaway trial account; the lead counts the maximum per phase (section 4); the lead never deletes; the owner bulk-deletes once after the take (section 10 step 5). No flow ever points at a real client or customer address (DECIDE-REAL-ONLY).
3. The take database runs in its own container, separate from n8n's store (DECIDE-AT-REPIN-2).
4. The API key is already in the local env and in the n8n credentials (owner 2026-11-16, `memory\owner-api-key-already-placed-work-tuesday-2026-11-16.md`); the owner places it again only if the T-08 step 0 check finds it missing; credential ids come from the first source that works (DECIDE-AT-REPIN-7).
5. The lead's script block is split "needed Tue" and "needed Wed" with an early NO-GO tripwire (8A).

**Owner steps (OWNER; full table in section 14):** O0 only if something is missing (Tue, before T-08 step 1); O0c only if no route yields the credential ids; O1 one answer on HubSpot token scopes (Tue); O3 type `y`, the challenge and `end` on camera (take, about 10:00Z); O4 one clean-up after the take: bulk-delete the filtered HubSpot contacts and confirm the number (after the lead says "clean-up starts"); O5 decide crop, blur or cover for each private address the lead lists (about 11:20Z); O6 compare figures in the settings file; O7 revoke the model key, app passwords and HubSpot private apps (only after the lead confirms the contact count is 0); O8 edit and post.

**GO / NO-GO rules (section 5):** Tue 14:00Z GO needs merge, review, final evidence, re-pin, loopback re-smoke green (T-12, started only after the owner's yes), Tue script block reviewed, no open Blocker or Major on the take path, F-011 and F-041 fixed or downgraded with written evidence (G1, G2). Early tripwire on the script block (8A). Wed 07:30Z F-002 open = that day NO-GO (G4). T19 or T20 failing = NO-GO (G5). Counts proof not green = slip one day, until Mon 23 Nov 12:00Z; scene 4 cut if no takeover inside the limit (G6). Positive control not 2 = take blocked (G12). Any extra mail = retake (G11). Money stop Mon 23 Nov 18:29Z.

**NOT DONE AT FREEZE (lead-provided artifacts; each is a HARD STOP for its step):** `<FINAL_HEAD>`; `<TAKE_FOLDER>` name and `<N8N_TAKE_ROOT>`; `<NODE_BIN>`, `<N8N_BIN>`, `<NODE_DIR>`; `<PG_IMAGE>`, `<PG_PORT>`, `<PG_CONTAINER>`, schema decision for `<MF_TABLE>`; the SELECT-only SQL and the `q-*.sh` wrappers; the Tue scripts (`<EXPORT_SCRIPT>`, `<POST_TWICE>`, harness re-smoke command and test list, activation route if `n8n_api.py` lacks it); the Wed scripts (`<SINGLE_POST>`, `<T19_21_RUNNER>`, `<MAILCOUNT>`, `<HS_SEARCH>`); the harness copy and `<HARNESS_FILLED_DIR>`; the API key file (owner); `<KEY_PREFIX>` and the keys files; the take command choice (U-02); mailbox words, `<WAIT_S>`, `<TRIES>`, `<LIMIT_S>`; the sign-off file; the per-phase dollar figures, the backstop setting name and ledger file name (U-26); the time box and tripwire threshold of 8A; every U-item of section 13.

## 0. Sources, verified facts, and what changed from v3

| Source | Used for |
|---|---|
| `_local\scratch\wt\cloud-flows-audit\handover\flows-audit\ORDERS.md` lines 143 to 174 (Q25 to Q30, NOTE 14:35Z) | schedule, go/no-go, owner list, ceiling sentence |
| same folder: `RUNBOOK.md`, `OWNER-STEPS-q16-rows.md` | step order, take_check pass counts, Row 4, Step D |
| `egm\duplicate-proof-lead-desk\DECISIONS-2026-11-16.md` | decisions 1 to 12 (items 1, 7, 12 corrected at re-pin) |
| `memory\spend-cap-backstop-no-hardcode-demo-label-2026-11-15.md`, `memory\owner-answers-2026-11-15-n8n-push-live-credits-license.md` | what approves spend (section 4) |
| `egm\duplicate-proof-lead-desk\wp6\LEAD-RUNBOOK-U-ITEMS-RESOLVED.md` | settled facts |
| `wp6\runbook-review\READINESS-1.md`, `READINESS-2.md`, `READINESS-3.md` | every finding fixed here (map in section 15) |
| `wp6\fix-p13\review-fix-13h\LANE-D-REPORT-SUMMARY.md` (F1 to F3), `wp6\fix-p13\BUILDER-REPORT-23.md` | r23 flock design, strings, exit codes |
| `wp6\agent-briefs\RESMOKE-RUNNER-BRIEF.md`, `wp6\agent-briefs\repin-prep\README.md` and `repin.py` | harness rules, repin.py usage |

Facts (nothing run here):
- `take/nlite-merge-m1` and `take/nlite-int-r24` were both 706b34d when U-ITEMS-RESOLVED was written. The r23 branch `take/nlite-int-r23` has head 39fcf36 (worktree `_local\scratch\wt\nlite-fix23`; not pushed; reviewed by Lane D only). `<FINAL_HEAD>` is not written yet.
- r31 design (first built in r26, reviewed again in r31; one n8n per take by flock on the TAKE FOLDER itself; r23 locked a file `n8n.lock`, that file no longer exists): `n8n_start.sh` takes `flock -n -E 111 -F <take folder>` and runs an inner sh that does `set -C; rm -f -- n8n.pid; echo $$ > n8n.pid`, re-checks n8n.out (ROUND 33 PENDING: wording applies after r33 lands, Lane D X3: the re-check may be removed), prints `n8n_start: starting n8n as process N, output in <TAKE_FOLDER>/n8n.out`, then `exec n8n start >> n8n.out 2>&1`; n8n holds the lock for its whole life; `n8n.pid` is n8n's own pid. `n8n_kill.py` stops the holders of the take folder FLOCK (found by `/proc/<pid>/fd`, matched to the folder by device and inode), then runs a final probe, retried every 0.1 s for up to 3 s, before every exit 0; it does not read `n8n.pid`. No process scanner, no `--start-check`, no `--is-start`. The old strings (`refused: n8n is already running`, `refused: could not tell if n8n runs`, `confirmed gone`) are gone.
- r23 behaviour changes this runbook relies on: (1) an n8n started by hand outside `n8n_start.sh` has no lock and is invisible to the start guard and to `n8n_kill.py`; (2) `n8n_start.sh` no longer execs n8n: the outer shell WAITS and exits with n8n's exit code, so the start is always a hidden background process (Start-Process form); (3) a lingering child holding the lock open blocks the next start (correct refusal) and is killed by stop; (4) a task runner that closed the lock fd is not seen; (5) stop timing (r31): SIGTERM, then up to 45 s waiting for the lock to drop, then SIGKILL to those still holding, then up to 5 s, then the 3 s final probe (v4.1 put the probe before SIGKILL: wrong); the r23 figure (20 s grace) and the estimate "real n8n needs about 8 to 10 s" are not relied on, the lead re-measures at W-03 step 4; (6) a SHARED flock holder, two same-user WSL helpers whose /proc/pid/fd cannot be read, and an exclusive holder in another user's process are not seen (exit 3); (7) (r26 Lane D F5) a take folder deleted and recreated while n8n runs is a NEW lock: the old n8n holds the old, unreachable one and a second n8n could start in the new folder; never delete or recreate the take folder while n8n runs; the same holds for a folder moved away and recreated, but a plain rename is safe (stop by the new path) (the "never" and "fail closed" claims cover the listed cases, not a hand-removed folder).
- `n8n_api.py` subcommands: v1 read `import`, `activate`, `deactivate`, `list`; U-ITEMS-RESOLVED read only `list` and `import` (U-03 settles). No export command and no post-twice script on any branch. It defaults `N8N_URL` to `http://127.0.0.1:5679` (the owner's own n8n): every call sets `N8N_URL` (`<N8NAPI>`).
- `run_real_check_n8n.py --take` is a different program from the video's "same lead sent twice" scenes: it sends 3 made-up people (A twice, B ten times at once, C once; source line 574), needs a person typing `y` and a confirmation line. Which one the video uses is the lead's choice (U-02).
- The audit tree holds `fill_flows\fill_flows.py`, `flow-check\take_check.sh`, `flow-check\take-warns.pin`, `tools\check_patches.sh`, patches F-002, F-008, F-003, F-004, `handover\demo\n8n-mainframe\build_mainframe.py`, `handover\demo\n8n-flows-v4\mf_leads.sql`. `mf.py` holds T17 and T18 only (no T19 to T21 runner exists).
- Lead's laptop (WSL): default node v20.19.6, python3 at /usr/bin/python3, flock from util-linux 2.39.3, no `n8n` command; n8n 2.46.6 needs Node 24 or newer.

**What changed from v3 (all marked in section 15):** the stand-in HubSpot credential, second fill, swap step, `<FILLED_STANDIN>`, G13 swap row, PSG step 5 set check, U-25, HS-15 and O0b/O2 are DROPPED (lead decision 2); section 4 counts contacts; Step D is one owner clean-up; T-12 written in full; `$HOME` resolved once; credential-id source named; psql only through wrapper `.sh` files; pre-start stored-active check; bounded guard proof; 8A split Tue/Wed with a tripwire; step numbers and the PATH form made one.

## 1. Decisions the lead records (marked, with defaults)

| ID | Decision | Default | Where recorded |
|---|---|---|---|
| DECIDE-AT-REPIN-1 **LEAD DECISION 2026-11-16, owner may veto** | n8n user folder and credentials across Tue, practice, rehearsal, take | **Reuse the existing n8n user folder of the owner's take n8n setup** (holding the owner's account and the credentials the owner placed per FACTS-ALREADY-DONE). The lead names the real folder at re-pin. A fresh folder is NOT the default (no owner account, no API key, none of the credentials). OWNER step O0 happens ONLY if T-08 step 0 shows the folder or the credentials missing. TAKE_TAG changes per take-program run. If the take program refuses because `result.json` is already in the folder, copy `result.json` to `<EVID>` first, then `mv` it aside into `<EVID>` (nothing deleted), then run (U-22). | `<TAKE_NOTES>` before T-08 |
| DECIDE-REAL-ONLY **LEAD DECISION 2026-11-16, owner may veto** | Which credentials the flows carry | **ONE filled set with the real HubSpot trial-account credential in every phase** (practice, rehearsal, Row 4, take). Every post with a new lead key that reaches the CRM step creates one made-up contact in the throwaway trial account. The lead counts the maximum contacts per phase (section 4: posts x new keys). The lead's own HubSpot identity stays read-only and the lead never deletes. Step D is ONE owner clean-up after the take (section 10 step 5). Every address in every phase is made-up or the throwaway mailbox; no flow ever points at a real client or customer address. Real-credential risk rules stay: pre-send gate before every send phase, flows deactivated between phases, activation last. | `<TAKE_NOTES>` before T-09 |
| DECIDE-AT-REPIN-2 | Postgres for T21 | T21 stops the take database's server. n8n's own database must not sit on that server. **Default: the take's database runs in its own container `<PG_CONTAINER>`; n8n uses a different server or its own default store.** DEVIATION recorded: DECISIONS item 10 says "one Postgres server, two databases". | `<TAKE_NOTES>` before T-08 step 2 |
| DECIDE-AT-REPIN-4 | Python form for scripts that import siblings | `python3 -I` (isolated; the import check in T-05 decides). Fallback if it fails: `python3 -E -s` run only from inside `<TAKE_TREE>`. | `<TAKE_NOTES>` after T-05 |
| DECIDE-AT-REPIN-5 | Re-smoke form | A separate harness copy with its own n8n folder, own ports and stand-in SERVICES (mail, model, HubSpot stand-ins; the RESMOKE-RUNNER-BRIEF form); never the take's n8n and never the take's credentials | `<TAKE_NOTES>` before T-12 |
| DECIDE-AT-REPIN-6 | Where Node 24 or newer and the n8n 2.46.6 install live (`<NODE_BIN>`, `<N8N_BIN>`, `<NODE_DIR>`) | No default: a path inside the take folder or a named Node 24 path; the lead writes the real path at re-pin (HS-12) | `<TAKE_NOTES>` before T-08 step 4 |
| DECIDE-AT-REPIN-7 | How the API key and the credential ids reach the lead | The API key is already in the local env and in the n8n credentials (owner 2026-11-16); the OWNER places the API key file (mode 600, in the Linux home) again ONLY if the T-08 step 0 check finds it missing, reported by name and count only; the lead never opens secrets folders. **Credential ids (names and ids only, never data; ids are not secrets) come from the first source that works, tried in this order, verified at re-pin:** (1) a credentials list route of the n8n public API, if it exists (the lead expects it may NOT exist); (2) the ids referenced inside the exported workflow JSON of the flows already stored in the folder or of an earlier export (`<EXPORT_SCRIPT>`); (3) OWNER step O0c: the owner reads the names and ids from the credentials screen. The owner's login password is never needed. | `<TAKE_NOTES>` before T-08 step 8 |
| DECIDE-8A | Script block split | "needed Tue" and "needed Wed" lists, dated review slots, early NO-GO tripwire (8A) | `<TAKE_NOTES>` at re-pin |

## 2. Conventions and every variable (defined once, here)

- All n8n scripts run in WSL (Ubuntu), Linux home folder, never under `/mnt`. From the lead's session use the PowerShell tool: `wsl.exe -d Ubuntu --cd <LINUX_DIR> -e sh <script> ...`. Never `wsl.exe` from the Git Bash tool. `n8n_start.sh` refuses bash (exit 127 or 2): always `sh`.
- **`<HOME_ABS>` (resolved once, M1).** At the start of T-01 run `wsl.exe -d Ubuntu -e sh -c 'echo $HOME'` (single quotes: WSL expands it), write the result, an absolute `/home/<user>`, in `<TAKE_NOTES>`. Every path in this file that begins `<HOME_ABS>` is that absolute path typed out. `$HOME` is used ONLY inside `.sh` files, never in a PowerShell string.
- **QUOTING RULE.** PowerShell expands `$` and strips double quotes before WSL sees them. So every `wsl.exe ... -e sh -c '...'` snippet is written with SINGLE quotes and contains NO double quote and no single quote inside. Any snippet that needs a quote, a loop or a filter is a `.sh` file (the SH-FILE rule): the lead writes it with the Write tool into `<LOGDIR_WIN>\sh\<name>.sh`, copies it into `<SHDIR>` (`wsl.exe -d Ubuntu -e sh -c 'mkdir -p <HOME_ABS>/keep/sh && cp <that file as /mnt path> <HOME_ABS>/keep/sh/ && chmod 600 <HOME_ABS>/keep/sh/<name>.sh'`) and runs `wsl.exe -d Ubuntu --cd <DIR> -e sh <SHDIR>/<name>.sh`. Placeholders `<...>` are replaced by the lead before the command is typed.
- PowerShell exit codes: read `$LASTEXITCODE` (never `$?`); every PowerShell command ends `; "exit=$LASTEXITCODE"`. Inside WSL `sh` use `echo exit=$?`.
- Never touch ports 5678 and 5679 (owner's own n8n). Never kill a process you did not start (stop acts only on the take's own folder lock; the lead never kills anything else). Never print a key, token, password or `/proc/*/environ` value. Never open `_local\secrets` or `_local\real-run`. No model call, HubSpot write or real send before a PSG (section 6) passed for that phase.
- Register row in `_local\agents-register.md` BEFORE starting each long-lived item (n8n, container, sampler, recorder). Record the container id at creation: later docker commands act on the recorded id.
- **STOP-N8N (defined once; cited everywhere).** `wsl.exe -d Ubuntu -e python3 -I <KILL_PY> <N8N_FOLDER>; "exit=$LASTEXITCODE"` where for the take `<KILL_PY>` = `<TAKE_TREE>/scripts/n8n_kill.py` and `<N8N_FOLDER>` = `<TAKE_FOLDER>`, and for the harness `<KILL_PY>` is the harness copy's own `n8n_kill.py` and `<N8N_FOLDER>` its own folder. (r31) Usage is exactly `n8n_kill.py <take folder>` (no `--grace`; anything else gives `refused: usage: n8n_kill.py <take folder>`, exit 2). Time: up to 45 s + 5 s + 3 s (53 s worst case), usually seconds, re-measured at W-03 step 4. Per-pid lines: `process N holds the take folder lock: SIGTERM`, `process N still holds the take folder lock after 45 s: SIGKILL`, `process N: SIGTERM sent` / `SIGKILL sent`, `process N: no longer holds the lock, not signalled`, `process N: already gone`, `process N: SIGTERM failed (<ErrorName>, errno N)`.
  - Exit 0 (the final probe found the lock free): `n8n of this take is stopped: N process(es) were holding the take folder lock, all gone`, or, if nothing holds the lock, `no process holds the lock of this take folder (an n8n started by hand is not seen): nothing killed`.
  - Exit 2 (refused): `refused: this runs in WSL (Linux) only`, `refused: the take folder must be an existing absolute path`, `refused: the take folder is not yours`, `refused: cannot read the take folder (<ErrorName>)`, `refused: usage: ...`.
  - Exit 3 (still held or unreadable), lines: `still holding the take folder lock after SIGKILL: processes <pids>`, `process N: SIGTERM failed (...)` / `SIGKILL failed (...)`, `cannot finish: <ErrorName>: check by hand`, `the lock is still held by a process this script cannot see (or one not listed above): check by hand`. ROUND 33 PENDING: wording applies after r33 lands (Lane A X1: which stream, stdout or stderr, carries the exit-3 reason; the lead reads both at re-pin). On the `cannot see` line: no pid list is shown, a SHARED holder gives this line, do not signal anything by name or pattern (NEVER-DO line 13), record counts only and ask the owner, never retry with another kill. ROUND 33 PENDING: wording applies after r33 lands (Lane D X7: this sentence is added to the script's own exit-3 text; until then it is this runbook's rule).
  - Exit 130 `interrupted: check by hand whether n8n of this take still runs`: run PORT-FREE for the take's port, then STOP-N8N once more (idempotent); do not edit `n8n.pid`; exit 0 is the only proof of a stop. ROUND 33 PENDING: wording applies after r33 lands (Lane A X2, second Ctrl-C): as of r31 a second Ctrl-C is ignored once the 130 line starts, and in rare instants gives a traceback with exit 1: treat that as 130.
  - A SIGTERM kill gives no message (143 under a shell, -15 directly; the value through wsl.exe is unmeasured): treat 143, -15 or any code other than 0, 2 or 3 as 130. Two stops at once: one may end 143 or 137: run once alone.
  - On 2 or 3: record the warning with counts only (no pid list); never retry with another kill. Exact wording re-read at U-04. Then PORT-FREE.
- **PORT-FREE `<PORT>` (defined once; cited everywhere; m1).** WSL: `wsl.exe -d Ubuntu -e sh -c 'ss -H -ltn sport = :<PORT> | wc -l'` expect `0` (an exact port match, so :56790 does not count); Windows: `Get-NetTCPConnection -LocalPort <PORT> -State Listen -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count` expect `0`. The port is never 5678 or 5679. In use: find the process with `ss -ltnp` (read only), tell the owner whose it is, never kill it. Exit 0 means only that the final probe found the take folder lock free; it does not prove nothing runs (an n8n started by hand has no lock and is invisible): PORT-FREE after every stop.
- **SQL WRAPPERS (defined once; M5).** The lead never types `psql` with a connection string. Every query is a `.sh` file in `<SHDIR>` that sets `PGPASSFILE` to its own mode-600 password file (`pgpass-admin` or `pgpass-select`, in `<HOME_ABS>/keep`), holds host `127.0.0.1`, port `<PG_PORT>`, database and user as plain lines at its top (not secrets), runs `psql -X -A -t -v ON_ERROR_STOP=1` with ONE fixed query, and prints counts or yes/no flags only (never a row of values, never the password). They run in WSL: `wsl.exe -d Ubuntu --cd <HOME_ABS> -e sh <SHDIR>/<name>.sh [arg]; "exit=$LASTEXITCODE"`; the `psql` client in WSL is checked at T-08 step 0d (U-30). Names: `q-ping.sh`, `q-admin-setup.sh` (admin file; creates schema, table, roles from the lead's statement), `q-columns.sh`, `q-select-negative.sh` (SELECT works, insert refused), `q-count-keys.sh <keys-file>`, `q-nonfinal.sh`, `q-row.sh <key>` (prints `state=<state> crm_id_digits=<yes|no>`), `q-count-key.sh <key>`, `q-state-group.sh`, `q-count-prefix.sh <prefix>`. They are written in the Tue script block (8A).

| Variable | Meaning |
|---|---|
| `<STUDIO>` | `C:\Users\rakes\Downloads\Hadavin` |
| `<REPO>` | `C:\Users\rakes\Downloads\Hadavin\projects\duplicate-proof-lead-desk` |
| `<FINAL_HEAD>` | sha of `take/nlite-merge-m1` after r23, r24 and r31 are merged (and r28 and r33 if they land) |
| `<AUDIT_REPO>`, `<AUDIT_SHA>` | checkout and sha holding `handover\flows-audit` (today `<STUDIO>\_local\scratch\wt\cloud-flows-audit`, branch `cloud/flows-audit`, 8f48bf8; re-confirm, U-09) |
| `<AUDIT_REPO_WSL>` | the same checkout as a WSL path (`/mnt/c/Users/rakes/Downloads/Hadavin/_local/scratch/wt/cloud-flows-audit` today) |
| `<FLOWS_AUDIT>` | `<AUDIT_REPO>\handover\flows-audit` (WSL: `<AUDIT_REPO_WSL>/handover/flows-audit`) |
| `<NEW>` | new folder name under `handover/demo` (never `n8n-flows-real-v5`) |
| `<TAKE_NOTES>` | `<STUDIO>\egm\duplicate-proof-lead-desk\take-notes-<TAKE_TAG>.md`, one per take attempt; holds shas, PSG lines, decisions, numbers, `<HOME_ABS>` |
| `<EVID>` | `<STUDIO>\egm\duplicate-proof-lead-desk\take-evidence\<TAKE_TAG>\`: copies of `result.json`, logs, recording hash; masked outputs only |
| `<TAKE_TREE>` | `<HOME_ABS>/take-tree-<FINAL_HEAD short>` |
| `<SHDIR>` | `<HOME_ABS>/keep/sh` |
| `<N8N_TAKE_ROOT>` | the Linux folder the take program requires every take folder to sit under (from its settings file) |
| `<TAKE_TAG>` | one tag per take-program run |
| `<TAKE_FOLDER>` | the existing n8n user folder (DECIDE-AT-REPIN-1) under `<N8N_TAKE_ROOT>`; mode 700 |
| `<TAKE_SETTINGS>` | the take program's settings file (copy of `scripts/real-run-n8n.env.example`) on the Linux filesystem |
| `<TAG_MARKER_DIR>` | folder where the take program writes `<TAG>.used` (never delete a `.used` file) |
| `<PORT_TAKE>` | the `N8N_PORT` value in `<TAKE_FOLDER>/n8n.env`, read with `wsl.exe -d Ubuntu -e sh -c 'grep ^N8N_PORT= <TAKE_FOLDER>/n8n.env'`; never typed from memory; rehearsal uses the same folder and port |
| `<KEY_FILE>` | the n8n API key file in the Linux home (mode 600), placed by the OWNER; path in `<TAKE_NOTES>`; never on a command line |
| `<N8NAPI>` | `wsl.exe -d Ubuntu --cd <TAKE_TREE> -e env N8N_URL=http://127.0.0.1:<PORT_TAKE> N8N_API_KEY_FILE=<KEY_FILE> python3 -I scripts/n8n_api.py`; always includes `N8N_URL` |
| `<NODE_BIN>`, `<N8N_BIN>`, `<NODE_DIR>` | node binary, n8n binary, folder holding the Node 24 binary (HS-12) |
| `<PG_CONTAINER>`, `<PG_CID>`, `<PG_IMAGE>`, `<PG_PORT>` | name, recorded container id, image, host port of the take database's own container (named at re-pin) |
| `<MF_TABLE>` | schema-qualified take table. `scripts/n8n_drive.py` reads FROM `app.mf_leads` (round 25) and resmoke plan v5 D1 says `app.mf_leads` in database `postgres` with three roles; the flows' `mf_leads.sql` creates an unqualified `mf_leads`, so the schema is made to match (T-08 step 2). Written in `<TAKE_NOTES>` (HS-16); every wrapper query uses it |
| `<KEY_PREFIX>` | one prefix every lead key of every phase starts with (practice, rehearsal, Row 4, take), written in `<TAKE_NOTES>` before W-00. Every made-up address is `<KEY>@<allow-listed domain>`, so the HubSpot filter in section 10 step 5 is "email contains `<KEY_PREFIX>`" and catches every contact of this take |
| `<KEYS>` | the made-up lead keys of one phase, in a keys file `<HOME_ABS>/keep/keys-<TAKE_TAG>.txt` and in `<TAKE_NOTES>`, never used before |
| `<INTAKE_ADDRESS>`, `<SENDER_ADDRESS>` | made-up or throwaway-mailbox addresses (domain allow-list in `<TAKE_NOTES>`) |
| `<WAIT_S>`, `<TRIES>`, `<LIMIT_S>` | mail-count wait, tries (both set at rehearsal) and scene 4 limit (default 180 s) |
| `<LOG>`, `<LOG2>`, `<LOGDIR_WIN>` | take_check logs; Windows folder for background-start logs and `.sh` files (`<STUDIO>\_local\logs\take-<TAKE_TAG>\`) |
| `<EXPORT>` | new empty folder outside the repo for the n8n export |
| `<SHA_FOLDER>`, `<SHA_PIN>` | commit shas of the regenerated folder and of the installed WARN pin |
| `<TOOL>` | `<FLOWS_AUDIT>/fill_flows/fill_flows.py` as the WSL path |
| `<VALUES>`, `<FILLED>` | `<HOME_ABS>/keep/flow-values.env` (one values file, real credential ids) and `<HOME_ABS>/keep/filled` (the ONE filled set; its sha in `<TAKE_NOTES>`) |
| `<HARNESS_DIR>`, `<HARNESS_N8N_FOLDER>`, `<HARNESS_PORT>`, `<HARNESS_VALUES>`, `<HARNESS_FILLED_DIR>` | the re-smoke harness copy, its own n8n folder, its own port, its own values file (`resmoke-values.env`) and its filled-flows folder (HS-6); the lead writes them |
| `<SINGLE_POST>`, `<POST_TWICE>`, `<MAILCOUNT>`, `<HS_SEARCH>`, `<T19_21_RUNNER>`, `<EXPORT_SCRIPT>` | the lead-written scripts of section 8A (path + sha each) |

## 3. Schedule: ONE reading (from Q26-1, Q27, Q30, NOTE 14:35Z)

The 13:00Z stamp in Q26 is wrong (Q30 correction); the dated schedule stands.

| Event | UTC | IST | Source / arithmetic |
|---|---|---|---|
| r20 to r24 merged, fresh three-lane review, final evidence, one mutation batch | Mon 16 Nov to about 04:00 Tue 17 Nov | 09:30 Tue | Q26-1 |
| Re-pin event, T-01 to T-11, **done by 08:00 Tue 17 Nov** | start no later than 04:17; done by 08:00 | 09:47; 13:30 | Sum of step estimates T-01 to T-11 = 223 min, one after another; 08:00 minus 223 min = 04:17. The figures were estimated for two fills; with one fill and no swap they are an upper bound (lead re-adds at re-pin). The F-011/F-041 fixes (G2) and the Tue script block are NOT inside the 223 minutes. |
| **Tue script block** (8A, "needed Tue" list) | starts when the lead sets at re-pin (may run beside T-08 to T-10); written, reviewed, sha-recorded **before the 14:00Z GO** | before 19:30 | time box: lead sets at re-pin (no figure in any source) |
| Loopback re-smoke (T-12), **no 1-hour limit** (owner 2026-11-16), after the re-pin and ONLY after the owner's yes to the lead's ask | starts after 08:00 and after his yes; end: the lead states it in the ask | the lead states it in the ask | v4.1 had "about 1 h, done about 09:30Z (15:00 IST)" from NOTE 14:35Z; that is no longer a limit. The ask names estimated clock times in UTC and IST and the cost (T-12 step 0) |
| **GO / NO-GO Tue 17 Nov 14:00** (earlier if green) | 14:00 | 19:30 | Q26-1, Q27-9 |
| Wed 18 Nov: positive control, PSG, practice run (1 h) with F-002 test T19 to T21 at its end | about 06:00 to 07:00 | 11:30 to 12:30 | Q30-1, Q29-1 |
| Row 4 (30 min) | about 07:00 to 07:30 | 12:30 to 13:00 | Q30-1 |
| F-002 deadline | Wed 07:30 | 13:00 | Q27-9 |
| Rehearsal (about 2 h) | about 07:30 to 09:30 | 13:00 to 15:00 | Q30-1 |
| Start-state gate, sign-off and GO check (about 25 min, then the decision) | 09:30 to 10:00 | 15:00 to 15:30 | Q27-7 |
| Take (about 1 h) | about 10:00 to 11:00 | 15:30 to 16:30 | Q26-1 |
| Lead's watch of the whole recording (about 20 min), then hand-over | watch about 11:00 to 11:20; hand-over about 11:20 | 16:30 to 16:50 | section 10 |
| Owner edits (about 120 min) and posts | post 15:00 | 20:30 | Q27-3 |
| NO-GO path: re-pin **done by** Mon 23 Nov 07:00 | 07:00 | 12:30 | Q27-6 |
| NO-GO path: a slipped take is allowed until | Mon 23 Nov 12:00 | 17:30 | Q27-7 |
| Credits / money stop | Mon 23 Nov 18:29 | 23:59 | Q26-1 |
| Post at the latest | Wed 25 Nov 15:00 | 20:30 | Q26-1 |

Retake arithmetic: start-state gate 25 + take 60 + edit 120 + lead's watch 20 = 225 min. For a 15:00Z post the gate must start by 11:15Z. The take ends about 11:00Z and the watch takes about 20 min, so a same-day retake for the 15:00Z post is NOT possible unless the watch finishes by 11:15Z; otherwise the post slips (latest Wed 25 Nov 15:00Z) and the retake needs the model key still valid, which is why revocation waits (section 10).

## 4. Spend and contacts: one table of maximum posts, model calls and HubSpot contacts per phase

What approves the ceiling (quoted, nothing invented):
- Q25-1: "The owner's standing yes for the credits already exists (FACTS-ALREADY-DONE.md, owner answers 2026-11-15: use the credits, no more limit questions); the owner is NOT asked for a new number." and "the lead states the ceiling for up to 3 sends from the ledger at take prep; the owner is not asked".
- Owner answers 2026-11-15: "treat 5 as a standing yes for live demo calls up to the in-code cap; report the number with each run; never raise the cap or spend outside the window without his word."
- Spend-cap memory: the cap and window end are validated settings documented as a backstop checked by a human; no cap or date literal in code; no ceiling in the take config.
- So the in-code backstop plus the standing credits yes approves spend. No file gives a per-phase dollar figure; none is written here.

Method for the dollar figure (names only): the lead reads (1) the price per model unit from the one spend-ledger file kept in `_local` (named in `<TAKE_NOTES>`), (2) the backstop setting from its validated setting (name and location written at re-pin, U-26); calls = (leads that pass the key check) x (model calls per lead); dollar figure = calls x ledger price; the total never exceeds the backstop. Window end for any spend: Mon 23 Nov 18:29Z (23:59 IST). Model calls per lead = **lead computes at re-pin from the node list of the filled flows**. Posts with an invalid key are refused (422) before any model call; **T20 rule: stop at the FIRST response that is not 422, or the first row or model call that appears.**

Contacts (DECIDE-REAL-ONLY): every post whose lead key is new and that reaches the CRM step creates one made-up contact in the owner's throwaway trial account. "Max new contacts" below = max leads (new keys). A resent key creates no second contact. The mail credential, the model key and the HubSpot credential are real in every phase except the Tuesday re-smoke (harness stand-in services only).

| Phase | Max posts | Max leads (new keys) | Model calls | Max new HubSpot contacts | Real mails | USD |
|---|---|---|---|---|---|---|
| Tue re-smoke (harness, stand-in services; T-12 step 3 proves it) | 2 (one made-up lead sent twice; NOTE 14:35Z) | 1 | 0 real | 0 (stand-in HubSpot service only) | 0 real | US$0 per the resmoke brief |
| Wed positive control | 0 to the flow; 2 made-up mails to the intake mailbox | 0 | 0 (Q29-1) | 0 | 2 to the intake mailbox | lead computes (method above) |
| Wed practice T19 | 2 (same key) | 1 | 1 x calls per lead | 1 | 1 | lead computes |
| Wed practice T20 | 200 invalid keys (each must get 422, no row) | 0 | 0 expected (any call = stop at the first non-422) | 0 | 0 | lead computes |
| Wed practice T21 | 2 (one while the database is down, same key resent) | 1 | 1 x calls per lead | 1 | 1 | lead computes |
| Wed Row 4 | 1 post per try (HS-13); up to 3 sends in total (Q25-1), each retry a new key | up to 3 | up to 3 x calls per lead | up to 3 (default expectation: 1) | up to 3 | lead computes; states it before the send |
| Wed rehearsal 1 + 2 | 6 (post-twice 2 posts + scene 4 one post, twice; derived from W-03 steps, confirmed against the post-twice script at re-pin) | 4 | 4 x calls per lead | up to 4 | 4 | lead computes |
| Wed take, form (a) post-twice script | 3 (2 + 1 for scene 4; confirmed against the script) | 2 | 2 x calls per lead | up to 2 | 2 | lead computes |
| Wed take, form (b) `run_real_check_n8n.py --take` | 13 (A twice, B ten times at once, C once; line 574) | 3 | 3 x calls per lead | up to 3 (the program only reads HubSpot; the flows write) | 3 | lead computes |
| Each retake | repeat of the take row, new keys, new tag | as the take row | as the take row | as the take row | as the take row | lead checks the backstop and the ledger before each retake |
| Total | sum of the rows | | | **First attempt maximum from the rows: 1 + 1 + 3 + 4 + 2 = 11 with form (a), 12 with form (b); each retake adds the take row.** The lead writes the confirmed figure in `<TAKE_NOTES>` | | the lead writes the total in `<TAKE_NOTES>` before W-01 (the first model call), after reading the backstop value and the ledger line once; never exceeds the backstop |

The rows marked "derived" and "form (a)/(b)" stay UNVERIFIED until the post-twice script exists; the lead corrects them then. The expected contact count for the clean-up (section 10 step 5) comes from the counts (wrapper `q-count-prefix.sh` and the read-only search), not from this maximum.

## 5. GO / NO-GO table (from the lead answers, not invented)

| # | Rule | Source | Result if not met |
|---|---|---|---|
| G1 | Tue 17 Nov 14:00Z (19:30 IST): GO needs ALL of: merge, review, final evidence, re-pin, loopback re-smoke green (T-12, asked first), the Tue script block done and reviewed (8A), no open Blocker or Major in the take-path code (scripts, tests). | Q27-9 | NO-GO |
| G2 | F-011 and F-041 (Major) are take path: each fixed with a test, or downgraded with written evidence, before Tue 14:00Z. **Owner of the work: the lead, or a builder the lead names in `<TAKE_NOTES>` at re-pin; deadline Tue 14:00Z; outside the 223-minute clock; the lead writes the start time in `<TAKE_NOTES>`.** | Q27-9 | automatic NO-GO |
| G3 | T19 to T21 are NOT part of Tuesday's check. F-002 is not counted on Tuesday. | Q27-9 | n/a |
| G4 | Wed 07:30Z (13:00 IST): F-002 still open (T19 to T21 not passed) = that day NO-GO. | Q27-9, Q30-1 | NO-GO for that day |
| G5 | If T19 or T20 fail on the patched copy the take does not run; no fallback to unpatched real-v5. | Q29-3 | NO-GO |
| G6 | Wed GO check, two rules. (1) Counts proof: GO needs exactly 1 mail plus the row, mailbox counted again after the stated wait; if not green the take slips one day at the same times, allowed until Mon 23 Nov 12:00Z. (2) Scene 4: shown only if the takeover showed inside 3 minutes in the rehearsal; if not, scene 4 is CUT and the take goes ahead with scenes 1 to 3 (Q27-7). A missed takeover alone is not a NO-GO. | Q27-7, Q29-2 | as stated |
| G7 | NO-GO path: re-pin done by Mon 23 Nov 07:00Z (12:30 IST); the chain after it (re-smoke 1 h, practice 1 h, Row 4 0.5 h, rehearsal 2 h, take 1 h) must end before 18:29Z with margin. | Q27-6 | no take before the money stop |
| G8 | P4a (what the real CRM returns for a contact's number): fails = take postponed; any other failed check: that row is not filmed. | OWNER-STEPS T4 | postpone |
| G9 | Row 4 four checks all as written, else do not start the rehearsal; one sentence to the owner. | OWNER-STEPS Row 4 | stop |
| G10 | F-031 and F-007 (text fixes): applied and re-read by Wed 06:00Z; Blocker until applied. | Q30-2 | Blocker stays |
| G11 | Any extra mail: stop, retake with new keys and a new address; never explained away. | T10, T11 | retake |
| G12 | Positive control: two made-up mails with different ids must show exactly 2 in the intake mailbox; not 2 = the counting method is wrong, every mailbox count after it is void, the take does not run. | Q29-1 | take blocked |
| G13 | One rule for every phase: every address any flow can send to or write is made-up or the throwaway mailbox (PSG step 2); no flow ever points at a real client or customer address; the lead's own HubSpot calls are read-only searches and never delete. A failed domain check is a stop. | DECIDE-REAL-ONLY | stop |

Doubt kept visible: Q21 says F-011 and F-041 are "never downgraded by counting"; Q27-9 allows "downgraded with evidence". FINDINGS.md rates both Major, take path (lines 115, 117); the ledger has no rows for F-011 or F-041 and F-002 is `BL-flowslocal-4`, BLOCKER, OPEN (ledger line 3187). The lead decides the wording (U-14).

## 6. PRE-SEND GATE (PSG) and DEACTIVATE (DEACT), used before every send phase

Applies before: Tue re-smoke (on the harness), Wed positive control, W-01 practice, W-02 Row 4, W-03 rehearsals, W-04/W-05 take, and every retake. No send, post or model call before the PSG line is in `<TAKE_NOTES>`. Activation is the LAST action of the gate. Steps in order; names and counts only, never values:
1. **Key names.** Every key in `<KEYS>` starts with `<KEY_PREFIX>`, is written in `<TAKE_NOTES>`, matches the made-up pattern stated there, and has count 0: `wsl.exe -d Ubuntu --cd <HOME_ABS> -e sh <SHDIR>/q-count-keys.sh <HOME_ABS>/keep/keys-<TAKE_TAG>.txt; "exit=$LASTEXITCODE"` (HS-2). No key reused from an earlier phase or tag.
2. **Recipient domains are made-up** (`.sh` file `psg-domains.sh`; prints key names and the domain part only, and `NO-AT` for a line without an at-sign): `awk -F= '/^(DESK_ALERT_TO|FROM_ADDRESS_PLACEHOLDER|INTAKE_ADDRESS_PLACEHOLDER)=/ { n = split($2, a, "@"); if (n > 1) print $1 " domain=" a[n]; else print $1 " NO-AT" }' <VALUES>` (on the harness: `<HARNESS_VALUES>`). Expect only domains on the allow-list in `<TAKE_NOTES>` (example.com or the throwaway mailbox's own domain) and no `NO-AT`. Anything else: STOP, nothing is sent.
3. **Port proof** (phases that start n8n): PORT-FREE `<PORT_TAKE>` (section 2) before the start. Not free: STOP.
4. **Ceiling row.** The phase's row of section 4 is filled: model-call figures and the maximum new contacts for this phase; the lead states the number with the run and does not wait for a reply.
5. **Re-smoke only: stand-in assertion** (T-12 step 3).
6. **Made-up-data line.** Write in `<TAKE_NOTES>`: `PSG <phase> <UTC stamp from date -u +%FT%TZ>: all made-up: yes; domains: pass; keys: unused; port free: yes; ceiling row: <phase>; max new contacts: <n>` (the "flows active" field is added in step 7).
7. **Activate last, then record.** Activate by NAME (`<N8NAPI> activate <NAME>`, route per U-03/HS-4) only after steps 1 to 6 passed; then `<N8NAPI> list` (names and active flags only) and append `flows active: <names from that list>`. Expect exactly the flows the phase needs are active, nothing else.

DEACT (flows deactivated between phases): after every phase and before any waiting period (after T-09 on Tuesday, between practice and Row 4, between Row 4 and rehearsal, between rehearsal and take, after the take), run `<N8NAPI> deactivate <NAME>` for each active flow (route per U-03), then `<N8NAPI> list` and expect 0 active. Imported flows are NOT activated on Tuesday at all; activation happens only inside a PSG. The take's n8n folder holds real credentials, so an active flow there can send real mail or write HubSpot; inactive flows cannot be triggered by a stray post.

## 7. HARD STOPS (items the lead provides; the dependent step cannot start without them)

| ID | Step X cannot start until | Artifact and sha written in `<TAKE_NOTES>` |
|---|---|---|
| HS-1 | T-04 cannot start until `<FINAL_HEAD>` is written (U-01) | the sha |
| HS-2 | T-08 step 9 (SELECT-only login) cannot be accepted, and every wrapper query (PSG step 1, W-01 to W-05, section 10 steps 2 and 5) cannot start, until the SELECT-only role statement and the `q-*.sh` wrappers exist | statement file path + sha, wrapper shas, negative-test result |
| HS-3 | T-08 step 1 (names of every line in `n8n.env`) and step 8 (names of every line in `<VALUES>`) cannot finish until the name lists are written (names only) | the name lists |
| HS-4 | PSG step 7, DEACT and the T-12 activation proof cannot run until the activation route is confirmed (U-03). T-09 step 6 is an IMPORT and needs the `import` route only. | route: `n8n_api.py` subcommand or the lead's curl script + sha |
| HS-5 | T-10 cannot start until the n8n export script exists (8A) | export script path + sha |
| HS-6 | T-12 cannot start until the harness copy path, `<HARNESS_FILLED_DIR>`, the re-smoke command, the test list and the re-pinned HEAD_PIN (via `repin.py`) are written | those five |
| HS-7 | Positive control, T19, and every mailbox count (Row 4 check c, W-03, W-05) cannot start until the mailbox counting command, filter, address setting names, mailbox words and `<WAIT_S>` first value are written (U-16) | script/command path + sha |
| HS-8 | W-01 (T19 to T21) cannot start until the T19 to T21 runner exists (U-11; spec `<FLOWS_AUDIT>\lanes7\N7-verdicts.md` section C) | runner path + sha |
| HS-9 | T-12 step 7, W-01 (T19 posts), W-02 Row 4, W-03 and W-05 cannot start until the take command is chosen (U-02), and for the post-twice script it exists and was read by a second reader for byte-identical bodies (Q29-4) | script path + sha + reader's line |
| HS-10 | W-05 cannot start until sign-off (screens list, run list, numbers, abort rule; U-17) is written | the sign-off file |
| HS-11 | Every phase cannot start until its PSG line (section 6) is written | the PSG line |
| HS-12 | **T-08 step 7 (start n8n) cannot start until the node binary and the n8n binary are written** (path and version of each); the take folder must carry its own n8n install or a named Node 24 path; the start must NOT fall back to node 20. | `<NODE_BIN>` path + `node -v`, `<N8N_BIN>` path + `--version` |
| HS-13 | W-02 Row 4 cannot start until the single-post script exists: it posts ONE stored body once and refuses a key already used | script path + sha + second reader's line |
| HS-14 | W-02 check (d), W-03 step 2 (v), section 10 steps 2 and 5 cannot start until the read-only HubSpot search tool exists (search by address or by prefix, no write, no delete, shows a read-only identity) | tool path + sha |
| HS-16 | T-08 step 2 onward, the SELECT-only statement (HS-2), PSG step 1, W-00 to W-05 and section 10 cannot start until the schema of `mf_leads` is written in `<TAKE_NOTES>` and every wrapper uses the same qualified name (`<MF_TABLE>`) | schema name, statement file path + sha, read-back of T-08 step 3 |

(HS-15 was the stand-in credential and is dropped in v4.)

**HS-12 check and the ONE start form (one PATH form everywhere).** Check, run with the exact binaries the start will use: `wsl.exe -d Ubuntu -e sh -c '<NODE_BIN> -v; <NODE_BIN> <N8N_BIN> --version'` expect a Node major of 24 or higher and `2.46.6`; any `v20` = STOP. Start form (T-08 step 7 and the harness at T-12 step 5): `env PATH=<NODE_DIR>:/usr/bin:/bin sh scripts/n8n_start.sh <TAKE_FOLDER>` (the PATH keeps `/usr/bin` and `/bin` for `flock` and `sh`; read how `n8n_start.sh` treats PATH, because its clean-env phase may reset it: `git -C <REPO> show <FINAL_HEAD>:scripts/n8n_start.sh | Select-String -Pattern 'PATH|node|env -i'`, U-24). Proof after the start: `wsl.exe -d Ubuntu -e sh -c 'readlink /proc/<pid from n8n.pid>/exe'` must name the Node 24 binary (on r31 `n8n.pid` is n8n's own pid); a `node20` path = STOP-N8N.

## 8. TUESDAY 17 Nov: re-pin event (check inside), then loopback re-smoke (asked first)

Commands run in PowerShell from `<REPO>` unless a step says WSL. Commands marked (mine) are written here and found in no file.

### T-01 Precondition (about 3 min)
- First resolve `<HOME_ABS>` (section 2) and write it in `<TAKE_NOTES>`.
- `git -C <REPO> rev-parse --show-toplevel; git -C <REPO> branch --show-current; git -C <REPO> status --short -- scripts src`
- Expect: the repo path; the branch the lead names; status empty on `scripts` and `src`. Failure: stop, find out why. Never check out another branch inside a studio worktree; read other branches with `git show`.

### T-02 Final head and that r23 and r24 are in (about 5 min)
- `git -C <REPO> log -1 --format=%H take/nlite-merge-m1; git -C <REPO> log --oneline -8 take/nlite-merge-m1`
- Expect: `<FINAL_HEAD>` is not 706b34d and the log shows the r23 flock commit(s), the r31 lock-on-take-folder commit(s) (and the r33 commit(s) if they land) and the r24 merges. Write `<FINAL_HEAD>` once in `<TAKE_NOTES>` (HS-1).
- Failure: still 706b34d: re-pin does not start. Latest start for the sequential event is 04:17Z; a later start means the 08:00Z target is missed: tell the owner in one line.

### T-03 Ledger state before work (about 2 min)
- `python <STUDIO>\egm\tools\ledger_check.py --topic duplicate-proof-lead-desk; "exit=$LASTEXITCODE"`. Exit 0 is not expected before fixes. Failure: topic missing or tool error: U-13.

### T-04 Re-pin the plan and take scripts (about 15 min)
- Make the worktree first. Save the list before and after: `git -C <REPO> worktree list --porcelain > <LOGDIR_WIN>\worktrees-before.txt; "exit=$LASTEXITCODE"`, then `git -C <REPO> worktree add --detach <REPO>\_local\scratch\wt\repin-<FINAL_HEAD short> <FINAL_HEAD>; "exit=$LASTEXITCODE"`, then `git -C <REPO> worktree list --porcelain > <LOGDIR_WIN>\worktrees-after.txt` and compare (one new entry, nothing else changed). `<worktree>` below is this path.
- Usage (from `wp6\agent-briefs\repin-prep\README.md`): `python repin.py <worktree> <head-sha> [--branch B] [--plan P] [--strings S] [--apply]`; `--plan` default `wp6\plan-wp6-resmoke-v5.md`; `--strings` default `wp6\agent-briefs\repin-dryrun\strings.txt`.
- Dry run, writes nothing: `python <STUDIO>\egm\duplicate-proof-lead-desk\wp6\agent-briefs\repin-prep\repin.py <worktree> <FINAL_HEAD> > <STUDIO>\_local\logs\repin-dryrun.txt; "exit=$LASTEXITCODE"`. Read the FAILURES block first; add `--apply` only when FAILURES is empty.
- Expect: FAILURES empty; all 20 strings match; plan lines change. The script aborts on a non-ancestor sha. Failure: a string with no match = STOP (plan rule 0.1). Notes N1 to N5 and the 0.1 expected counts are NOT applied by the script: the lead pastes them. This step gives the re-smoke plan its HEAD_PIN (HS-6).
- r31 plan texts: the resmoke plans require `n8n.pid == pgid`; on r31 `n8n.pid` is n8n's own pid written after flock, so that is probably false. The lead finds the lines (`Select-String -Path <STUDIO>\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md -Pattern 'pgid'`) and replaces the assertion with the lock-holder check (the pid in `n8n.pid` holds the take folder lock) or drops it; note N6 (U-29).

### T-05 Copy the take scripts into the take tree by sha, no checkout, then import check (about 10 min)
- Tar on Windows without a pipe: `git -C <REPO> archive --format=tar -o <LOGDIR_WIN>\take-tree.tar <FINAL_HEAD> scripts src; "exit=$LASTEXITCODE"`.
- Extract in WSL: `wsl.exe -d Ubuntu -e sh -c 'mkdir -p <TAKE_TREE> && tar -x -f <LOGDIR_WIN as /mnt path>/take-tree.tar -C <TAKE_TREE>'; "exit=$LASTEXITCODE"`.
- File check: `wsl.exe -d Ubuntu --cd <TAKE_TREE> -e sh -c 'test -f scripts/n8n_start.sh && test -f scripts/n8n_kill.py && test -f scripts/n8n_api.py && test -f scripts/n8n_drive.py && test -f scripts/run_real_check_n8n.py && echo all-found'`. Expect `all-found`.
- **Import check, no send**: SH-FILE `import-check.sh` holding `python3 -I -c 'import sys; sys.path[:0]=["scripts","src"]; import env_guard, http_guard, n8n_drive, run_real_check_n8n, lead_desk.envnum; print("imports-ok")'`, run with `--cd <TAKE_TREE> -e sh <SHDIR>/import-check.sh`. Expect `imports-ok`. It only imports modules. If a module name is wrong at `<FINAL_HEAD>`, the lead corrects the list from `ls scripts src`.
- Real invocation form without a network target: `wsl.exe -d Ubuntu --cd <TAKE_TREE> -e env N8N_URL=http://127.0.0.1:1 python3 -I scripts/n8n_api.py; "exit=$LASTEXITCODE"` (no sub-command: expect a usage line or a clean refusal; port 1 means a stray call cannot reach the owner's n8n; if it reaches a network or unexpected port, stop). If it fails with `ModuleNotFoundError`, record DECIDE-AT-REPIN-4 and use the fallback form everywhere `<N8NAPI>` and the take program run.
- Failure: a file missing: every step that needs it is BLOCKED; NO-GO until it exists. The post-twice, single-post and export scripts do not exist yet (HS-5, HS-9, HS-13).

### T-06 Apply the flow patches and regenerate into a NEW folder (about 15 min)
All commands run inside `<AUDIT_REPO>` (absolute paths, no relative cd chains):
- `wsl.exe -d Ubuntu --cd <AUDIT_REPO_WSL> -e sh handover/flows-audit/tools/check_patches.sh; "exit=$LASTEXITCODE"`. Expect `PASS 4 patches` (the script leaves untracked `tools/scratch`: never commit it).
- **Which patches touch the flows.** `git -C <AUDIT_REPO> apply --stat handover/flows-audit/patches/F-003*.patch handover/flows-audit/patches/F-004*.patch`: if either lists `handover/demo/n8n-mainframe/build_mainframe.py` or any flow file, apply it in THIS step (before regenerating and committing) so the folder sha already contains it; otherwise it waits for T-11. Do not apply flow-touching text patches after the commit below: that is a new sha and a repeat through T-10 (about 168 min).
- Two checks and two applies, in this order, each exit code read: `git -C <AUDIT_REPO> apply --check handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch`, `git -C <AUDIT_REPO> apply handover/flows-audit/patches/F-002-take-key-check-and-claim-error-path.patch`, `git -C <AUDIT_REPO> apply --check handover/flows-audit/patches/F-008-save-runs-for-the-take.patch`, `git -C <AUDIT_REPO> apply handover/flows-audit/patches/F-008-save-runs-for-the-take.patch`. Expect all four commands exit 0 (2 checks and 2 applies); `git -C <AUDIT_REPO> diff --stat` lists only `handover/demo/n8n-mainframe/build_mainframe.py`.
- Regenerate (V5-README commands; NEVER write into `n8n-flows-real-v5`), `--cd <AUDIT_REPO_WSL>/handover/demo/n8n-mainframe`: `wsl.exe -d Ubuntu --cd <that folder> -e sh -c 'test ! -e ../<NEW> && MF_REAL=1 MF_V4=1 MF_TRIES=2 MF_TMO_MS=10000 python3 build_mainframe.py ../<NEW> PG_CREDENTIAL_ID SMTP_CREDENTIAL_ID SUB_WORKFLOW_ID 45 HS_CRED_PLACEHOLDER'` (plain `python3`, not `-I`: the generator needs its own folder on the path).
- Expect: four `wrote mf-...json` lines; `diff -r -x V5-README.md -x V5-NODE-DIFF.txt handover/demo/n8n-flows-real-v5 handover/demo/<NEW>` (from `<AUDIT_REPO_WSL>`) differs in mf-form.json and mf-hook.json (3 new nodes each) and mf-sub-crm-mail.json (run-saving only), NOT in mf-recovery.json.
- Failure: any apply error: no `--reject`, no `--3way`; if F-002 applied and F-008 did not, `git -C <AUDIT_REPO> apply -R` the F-002 patch and send the error to the audit. A difference in mf-recovery.json or outside the three: stop.
- Commit once, **LOCAL ONLY, never push**: `git -C <AUDIT_REPO> add handover/demo/n8n-mainframe/build_mainframe.py handover/demo/<NEW>` then `git -C <AUDIT_REPO> commit` (message ends with the attribution lines), then `git -C <AUDIT_REPO> rev-parse HEAD` = `<SHA_FOLDER>`. If a local branch is safer, `git -C <AUDIT_REPO> switch -c take-<TAKE_TAG>` first (U-09). Any later edit is a new sha and a repeat from here.

### T-07 take_check on the UNFILLED copy (about 3 min; runs in parallel with T-08)
- `wsl.exe -d Ubuntu --cd <AUDIT_REPO_WSL> -e sh -c 'bash handover/flows-audit/flow-check/take_check.sh --flows handover/demo/<NEW> > <LOG> 2>&1; echo exit=$?'` (NEVER the `TAKE_CHECK_FLOWS=` form: it exits 4; take_check.sh is a bash script, only `n8n_start.sh` refuses bash).
- Expect exit 0 and, in `<LOG>`, counted in the SH-FILE `take-check-counts.sh` (the patterns contain single quotes): `grep -c 'key check present (F-002 applied)' <LOG>` = 2; `grep -c 'key check ABSENT' <LOG>` = 0; `grep -cE '^INFO: .* run saving is ON' <LOG>` = 3; `grep -c '^!!!' <LOG>` = 0; `grep -c '^WARN set equals the pinned set' <LOG>` = 1; `grep -cE '^FINAL: take_check exit status 0\. RESULT: 0 FAIL' <LOG>` = 1; `grep -c '^ACCEPTED: recovery flow not part of the take' <LOG>` = 1 or 2 (the script prints "decision 4"; Q27-8 wants "decision 1": wording is the lead's choice, U-12).
- Failure: exit 4 "environment override": unset `TAKE_CHECK_*`. `key check ABSENT` or a run-saving WARN: back to T-06. `!!! THE WARN SET CHANGED`: a person reads each changed line.

### T-08 Own n8n, database and values file (about 40 min)
Steps 0 to 3 can run in parallel with T-07.
0. **Folder, credentials and prerequisites** (read-only, names and yes/no only):
   - a. `wsl.exe -d Ubuntu -e sh -c 'test -d <TAKE_FOLDER> && echo folder-found'` expect `folder-found`; mode `wsl.exe -d Ubuntu -e sh -c 'stat -c %a <TAKE_FOLDER>'` expect `700`; `wsl.exe -d Ubuntu -e sh -c 'grep ^N8N_PORT= <TAKE_FOLDER>/n8n.env'` shows a value that is not 5678 or 5679.
   - b. `wsl.exe -d Ubuntu -e sh -c 'grep -c ^N8N_ENCRYPTION_KEY= <TAKE_FOLDER>/n8n.env'` expect `1` (value never printed); mode `wsl.exe -d Ubuntu -e sh -c 'stat -c %a <TAKE_FOLDER>/n8n.env'` expect `600`.
   - c. **The owner account and the three credentials exist and their ids are known** (DECIDE-AT-REPIN-7: sources in order; verify at re-pin which one works; the credentials list route probably does not exist in the n8n public API). Expect the names `n8n-publish-pg`, `mf-mail-smtp`, `hubspot-app-token`. Names and ids only; ids go into `<VALUES>` in step 8, never into the chat. If source 3 is needed this is OWNER step O0c.
   - d. **flock and client prerequisites (r23, Lane D F2)**: `wsl.exe -d Ubuntu -e sh -c 'command -v flock'` expect a path; `wsl.exe -d Ubuntu -e sh -c 'flock --help 2>&1 | grep -c -- -F'` expect `1` or more (`-F` is required; the laptop's flock is util-linux 2.39.3: `wsl.exe -d Ubuntu -e sh -c 'flock --version'`); `wsl.exe -d Ubuntu -e sh -c 'command -v psql'` expect a path (U-30). If `flock` is missing or has no `-F`: STOP, `n8n_start.sh` refuses by design and starts nothing. `n8n_start.sh` itself probes flock (a real `flock -n -E -F` on a fresh `.flock-probe.XXXXXX` folder inside the take folder, removed afterwards). Its refusals: `refused: flock is not installed (util-linux): cannot make sure only one n8n runs for this take. Nothing started` and `refused: flock with the option -F (and -E) that can lock a folder here is required (probe exit N). Nothing started`. This step 0d stays an early check. A kill during the probe can leave one `.flock-probe.XXXXXX` folder: remove only that one. ROUND 33 PENDING: wording applies after r33 lands (Lane A X4, probe folder trap: the leftover-folder sentence may change once the script cleans it up itself; lead verifies at re-pin).
   - e. **If a, b or c fails (folder, key name, owner account or a credential missing): OWNER step O0, and only then.** The lead writes the exact one-message ask first: what is missing by name (never a value), the key file path to place, the host, port and database name the new container will use (matched to what the credential screen shows, step 2), and the question "is the Postgres password in the container env file the same one as in the n8n credential" (m3). Nothing is created by the lead in place of the owner's account or credentials.
1. **n8n settings file** (read, do not rewrite unless e) says it is missing): `<TAKE_FOLDER>/n8n.env` mode exactly 600, owned by the user, LF line ends. Names allowed: `N8N_*`, `DB_*`, `EXECUTIONS_*`, `WEBHOOK_URL`, `GENERIC_TIMEZONE`, `TZ`; `N8N_ENCRYPTION_KEY` required; `N8N_BLOCK_ENV_ACCESS_IN_NODE` may only be `true`; `N8N_USER_FOLDER` is set by the script. The port is the `N8N_PORT` line (whether n8n 2.46.6 honours it: U-05, checked by the port proof after start). Name list to `<TAKE_NOTES>` (HS-3).
2. **Take database** (DECIDE-AT-REPIN-2). The lead writes the container recipe in `<TAKE_NOTES>` before running it: image `<PG_IMAGE>` (a Postgres major the `mf_leads.sql` file and the credential accept), host port `<PG_PORT>` bound to `127.0.0.1` only, container name `<PG_CONTAINER>`, database user and name equal to what the n8n Postgres credential screen shows (host, port, database, user read where shown; never the password), password supplied by `--env-file` from a mode-600 file the OWNER placed (the lead never opens it; if absent: O0). **Before the run (m2):** `docker ps -a -q --filter "name=^<PG_CONTAINER>$"` must return nothing (no container of that name exists) and PORT-FREE `<PG_PORT>`; either fails: STOP. Shape: `docker run -d --name <PG_CONTAINER> --env-file <PG_ENV_FILE> -p 127.0.0.1:<PG_PORT>:5432 <PG_IMAGE>; "exit=$LASTEXITCODE"`. Record the id at once: `docker ps -q --filter "name=^<PG_CONTAINER>$"` must return exactly one id = `<PG_CID>` in `<TAKE_NOTES>` and the register. All later docker commands act on `<PG_CID>`. **Password match (m3):** after the container is up run `q-ping.sh` (it connects with the owner-placed password file; a success proves the file password works; the owner confirmed in the O0 message that the same password is in the n8n credential; a mismatch would show first as a Postgres-node error at T19, so the lead also states this at W-01). **Schema:** the take database gets schema `app` with `mf_leads` inside it, OR the flow SQL and the drive script are set to one and the same schema; the exact statements and the three roles are **lead writes at re-pin, reviewed with the Tue script block** (no SQL is invented here). The flows' Postgres nodes must hit the same qualified table the drive script and the SELECT-only login read; the lead greps the filled flows for the table name before T-09 step 4. Then `q-admin-setup.sh` creates the database objects and runs `handover/demo/n8n-flows-v4/mf_leads.sql` (its first line wrongly says "v3 table"; run once on a fresh database; path relative to `<AUDIT_REPO_WSL>`). If the image, port or credential match cannot be stated: hard stop for step 2, one message to the owner (O0).
3. **Column gate:** `wsl.exe -d Ubuntu --cd <HOME_ABS> -e sh <SHDIR>/q-columns.sh; "exit=$LASTEXITCODE"` prints `schema=<name> columns=4` for the four columns `alert_sent`, `alert_token`, `alert_until`, `alert_attempts`; expect exactly 4, the schema written in `<TAKE_NOTES>` (HS-16), `copies=1` (no second copy of the table in another schema) and `db=<the take's database>`, not n8n's.
4. **HS-12 binary check** (before the port proof): the command of section 7; Node 24 or newer and 2.46.6, both written in `<TAKE_NOTES>`. The default `node` (v20.19.6) must not be what the start uses.
5. **Port proof before start:** PORT-FREE `<PORT_TAKE>`. Register row written.
6. **Stored-active-flows check before the first start (M6).** The reused folder may hold flows stored ACTIVE that n8n re-activates at start. Method (U-30; the lead confirms the store type at re-pin): SH-FILE `stored-active.sh` runs `sqlite3 -readonly <TAKE_FOLDER>/.n8n/database.sqlite 'select name, active from workflow_entity'` (path of the folder's own store written at re-pin; if the folder uses a Postgres store, the same query through a wrapper) and prints names and the active flag only. Expect no flow active. Any active flow: tell no one yet, and after the start (step 7) run `<N8NAPI> list` at once and deactivate every active flow before anything else; no post is sent until DEACT shows 0 active. An empty folder (no store yet): note "none stored" and go on.
7. **Start n8n in the background** (the lead does not sit at a terminal; r31: the outer shell waits for n8n, so always hidden background). From PowerShell (single quotes, no double quotes), the ONE start form of section 7:
   `Start-Process -FilePath wsl.exe -ArgumentList '-d','Ubuntu','--cd','<TAKE_TREE>','-e','env','PATH=<NODE_DIR>:/usr/bin:/bin','sh','scripts/n8n_start.sh','<TAKE_FOLDER>' -RedirectStandardOutput <LOGDIR_WIN>\n8n-start.out -RedirectStandardError <LOGDIR_WIN>\n8n-start.err -WindowStyle Hidden`
   Bounded read, once: `Get-Content <LOGDIR_WIN>\n8n-start.out -Tail 20; Get-Content <LOGDIR_WIN>\n8n-start.err -Tail 20`. **Re-read the exit code at U-04 (m4):** `n8n_start.sh` refuses with a text and a non-zero exit. Refusal strings after r31: `refused: run this with sh (dash), not bash` (127 under bash, 2 under dash); `refused: the take folder name must not contain a newline`; `refused: the take folder must not be writable by group or others (chmod go-w). Nothing started`; `refused: the take folder is not on a local Linux filesystem (<final X6 list>): the lock cannot be trusted there. Nothing started` (ROUND 33 PENDING: wording applies after r33 lands, Lane D X6: the final list of filesystems is not written here; read it from the script at U-04); `refused: n8n.pid is not a plain file (a symlink, folder, pipe or device). Nothing started`, and the same for n8n.out (ROUND 33 PENDING: wording applies after r33 lands, Lane A X3: the n8n.out refusal text and exit, only if r33 keeps it); `refused: n8n is a symlink. Nothing started` and `refused: cannot create the n8n folder inside the take folder. Nothing started` (ROUND 33 PENDING: wording applies after r33 lands, Lane A X6: refusals about the n8n subfolder and parent folders; Lane A X5 also pending, lead verifies at re-pin); `refused: cannot create a temporary folder inside the take folder. Nothing started`; and the two flock refusals of step 0d. v4.1 said "symlink or a folder"; it is now "symlink, folder, pipe or device". Script refusals exit 2; a held lock is flock's internal exit 111 turned into the refusal `another n8n of this take holds the take folder lock (stop it with n8n_kill.py first). Nothing started` with exit 2. A flock that cannot open the folder, or a failed redirect of `n8n.pid` or `n8n.out` inside the inner sh, can give 1 or 2 with no refusal text (and n8n's own 130 and 143 are possible), so **exit 2 is not proof of a refusal**: read `n8n-start.out` and `n8n.out` and expect the line `n8n_start: starting n8n as process N, output in <TAKE_FOLDER>/n8n.out`. Any other exit is n8n's own code. The lead re-reads each exit number at U-04. Expect `<TAKE_FOLDER>/n8n.pid` written and output going to `<TAKE_FOLDER>/n8n.out`.
   Readiness, bounded (SH-FILE `ready.sh`): `i=0; while [ $i -lt 12 ]; do c=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:<PORT_TAKE>/healthz/readiness); if [ "$c" = 200 ]; then echo ready; exit 0; fi; i=$((i+1)); sleep 10; done; echo not-ready; exit 1`. Expect `ready` within 12 tries; on `not-ready` STOP and read the tail of `<TAKE_FOLDER>/n8n.out` (`/healthz` answers 3.5 to 6.5 s before the webhook is registered: never use it).
   Port and node proof: `wsl.exe -d Ubuntu -e sh -c 'ss -ltnp | grep :<PORT_TAKE>'` shows one listener whose process is the pid in `n8n.pid`; `readlink /proc/<that pid>/exe` names the Node 24 binary (HS-12). Anything else: STOP (U-05).
   **Right after the start: `<N8NAPI> list`** (names and active flags): expect every flow `inactive` (an active one: deactivate it now, step 6).
   - **Refusal text after r31:** `another n8n of this take holds the take folder lock (stop it with n8n_kill.py first). Nothing started` (exit 2) means the lock guard works (an n8n of this take already runs, possibly a lingering child that holds the lock open): read the tail of `<TAKE_FOLDER>/n8n.out`, STOP-N8N (it signals every same-user process that holds an EXCLUSIVE flock on the folder), PORT-FREE, then retry once; a second refusal is a STOP for the review lane. A refusal with no n8n running (PORT-FREE ok) plus a STOP-N8N exit 3 with the `cannot see` line means a shared lock or an unseen holder: do not kill it, record and ask the owner. The strings `n8n is already running`, `could not tell if n8n runs` and `confirmed gone` belong to r22 and must NOT be expected. Exact wording re-read at `<FINAL_HEAD>` (U-04).
8. **Values file** (DECIDE-AT-REPIN-7): `wsl.exe -d Ubuntu -e sh -c 'mkdir -p -m 700 <HOME_ABS>/keep; (umask 077; : > <VALUES>)'`. The lead writes the KEY=VALUE lines into `<VALUES>` (DESK_URL, DESK_TIMEOUT_MS, DESK_ALERT_TO, FROM_ADDRESS_PLACEHOLDER, INTAKE_ADDRESS_PLACEHOLDER, PG_CREDENTIAL_ID, SMTP_CREDENTIAL_ID, HS_CRED_PLACEHOLDER = the real `hubspot-app-token` id; made-up or from the take's settings; never printed). Credential ids come from the source chosen in step 0c; the three credentials already exist (FACTS-ALREADY-DONE); do not ask the owner again except O0c. HubSpot token scopes: the owner holds them; the lead asks ONCE in the take-prep message (O1). Name list to `<TAKE_NOTES>` (HS-3).
9. **SELECT-only login** (HS-2): the statement text is the lead's, in a file whose path and sha go in `<TAKE_NOTES>`; shape: `CREATE ROLE ... LOGIN; GRANT CONNECT ...; GRANT SELECT ON <MF_TABLE> ... (and USAGE on its schema)`. Negative test: `q-select-negative.sh` prints `select=ok insert=refused`; both results written down.
10. **Guard proof, bounded (M7)** (owner decision 2026-11-16): a second start MUST be refused. Run it once with a time limit: `wsl.exe -d Ubuntu --cd <TAKE_TREE> -e timeout 15 sh scripts/n8n_start.sh <TAKE_FOLDER>; "exit=$LASTEXITCODE"`. Expect the text `another n8n of this take holds the take folder lock ...` and exit 2 (or the exit U-04 read); exit 2 alone is not proof of a refusal (step 7): read the text. **Exit 124 (timeout) or any exit other than the refusal: the second start was NOT refused (it started or hung): STOP; run STOP-N8N (it signals every same-user process that holds an EXCLUSIVE flock on the folder, including a second one); PORT-FREE (a second n8n may now hold the port or have failed on it); read both `n8n.out` tails; the take does not run on this head; this is a Blocker for the review lane; no fallback start is tried.** After a refusal, `<N8NAPI> list` still shows all flows inactive.

### T-09 Fill, check, import (no activation) (about 65 min, the v3 two-fill estimate; one fill is less)
`<TOOL>` needs python 3.11 or newer, Linux home folder, plain `python3 -I <TOOL>` (a single file, no siblings). ONE fill from `<VALUES>`; its sha is recorded in `<TAKE_NOTES>`.
1. `python3 -I <TOOL> fill --in handover/demo/<NEW> --values <VALUES> --out <HOME_ABS>/keep/filled-1 --allow-placeholders` (run in `<AUDIT_REPO_WSL>`). Expect exit 3, only SUB_WORKFLOW_ID left; the folder holds `NOT-READY-DO-NOT-IMPORT.txt` on purpose.
2. Import ONLY `filled-1/mf-sub-crm-mail.json` (the one exception): `<N8NAPI> import <that file>`; read its id with the route chosen in DECIDE-AT-REPIN-7 or from `<N8NAPI> list`; add `SUB_WORKFLOW_ID=<id>` to `<VALUES>`. `N8N_URL` is in `<N8NAPI>` (the default would be the owner's 5679).
3. `python3 -I <TOOL> delete --out <HOME_ABS>/keep/filled-1`.
4. `python3 -I <TOOL> fill --in handover/demo/<NEW> --values <VALUES> --out <FILLED>`. Expect exit 0 and `no placeholders left`.
5. `python3 -I <TOOL> check <FILLED>`. Expect `0 problem(s)`. Greps (SH-FILE `grep-controls.sh`): controls on the UNFILLED folder must list files (a control that lists nothing means the grep is broken): `grep -rlF '$env' handover/demo/<NEW>` lists exactly mf-recovery.json and mf-sub-crm-mail.json; `grep -rlE 'PG_CREDENTIAL_ID|SMTP_CREDENTIAL_ID|SUB_WORKFLOW_ID|HS_CRED_PLACEHOLDER|FROM_ADDRESS_PLACEHOLDER|INTAKE_ADDRESS_PLACEHOLDER' handover/demo/<NEW>` lists the four flow files. The same two commands on `<FILLED>` print nothing. F-018 values loop (read the F-018 row of FINDINGS.md first), SH-FILE `f018-loop.sh` (an EMPTY value is a failure): `while IFS== read -r k v; do case "$k" in ""|\#*) continue;; esac; if [ -z "$v" ]; then echo "$k EMPTY"; elif grep -rqF -- "$v" <FILLED>; then echo "$k found"; else echo "$k NOT FOUND"; fi; done < <VALUES>`. Expect every key `found`, no `EMPTY` (a legitimately empty value is a named exception in the F-018 row).
6. Import the other three (inactive on import): `<N8NAPI> import <FILLED>/mf-form.json` (and mf-hook.json, mf-recovery.json). **Do NOT activate.** `<N8NAPI> list` expect 4 flows, all inactive. If two workflows share a name (an earlier copy stored in the reused folder), the extra copy is deleted in the n8n screen first (activation by NAME fails otherwise).
7. DEACT (section 6) and PORT-FREE not needed (n8n stays up until T-10 end). The activation route proof is done on the harness in T-12 (step 6) and for real inside the PSG of W-01 (PSG step 7).

### T-10 Export back and take_check on the export (about 45 min)
- HS-5: the export script (8A; a short curl script against the n8n REST API, token from `<KEY_FILE>`). Output: a NEW empty folder `<EXPORT>` outside the repo holding EXACTLY mf-form.json, mf-hook.json, mf-recovery.json, mf-sub-crm-mail.json; each parses (SH-FILE `parse-json.sh`: `python3 -I -c 'import json,sys; json.load(open(sys.argv[1]))' <file>`).
- `wsl.exe -d Ubuntu -e sh -c 'bash <FLOWS_AUDIT as WSL path>/flow-check/take_check.sh --flows <EXPORT> > <LOG2> 2>&1; echo exit=$?'`. First run expects exit 4 with `!!! THE WARN SET CHANGED` (placeholder WARNs vanish). A named person (U-08) reads every `+` and `-` line; only placeholder WARNs may vanish. Then a new pin: `test ! -e <TAKE_FOLDER>/export-warns-1.pin && bash .../take_check.sh --flows <EXPORT> --write-warn-pin <TAKE_FOLDER>/export-warns-1.pin > /dev/null 2>&1`; the lead copies it over `flow-check/take-warns.pin` and commits (`<SHA_PIN>`, the second sha; local only). Re-run: expect exit 0 with the same six counts as T-07 and node:link counts mf-form 15:14, mf-hook 15:14, mf-recovery 10:9, mf-sub-crm-mail 20:26.
- After the pin is installed a re-run on the UNFILLED copy exits 4; restore the first pin first: `git -C <AUDIT_REPO> checkout <SHA_FOLDER> -- handover/flows-audit/flow-check/take-warns.pin`.
- Greps on `<EXPORT>`: both greps of T-09 step 5 print nothing; F-018 loop (folder `<EXPORT>`, `<VALUES>`) all found. Does take_check read the active flag: U-23.
- **End of T-10: STOP-N8N for the take's n8n** (not needed until Wednesday; must not run through the re-smoke), then PORT-FREE `<PORT_TAKE>`. Flows stay imported and inactive in the folder; Wednesday restarts n8n with the same folder.

### T-11 Text fixes and decisions of the re-pin (about 20 min, may run parallel to T-09 and T-10)
- Apply F-003 and F-004 ONLY if T-06 showed they do not touch the flows (`git -C <AUDIT_REPO> apply --check` first), sentences F-007 and F-028; F-031 one sentence; the alert text becomes "a person has to look at this lead in the table and decide outside this flow"; never say "approval", "audit trail" or "everything is logged" (F-042, F-043). Caption in RUNSHEET-WORDING.md A-016f becomes exactly `In this recording, the same lead ID sent twice gave one e-mail message in the intake mailbox.` (Q28-1). Closing card one line, no numbers. Greps: `grep -c -F "<caption>" <run sheet path>` at least 1; `grep -n -E "60\.8|60\.1|61\.9" <run sheet path>` prints nothing.
- Correct DECISIONS items 1, 7 and 12 and VIDEO-RUNSHEET N-9, N-10, N-11 (Q28-5, Q30-1; item 12's "right after the loopback re-smoke" is superseded); correct the stale texts of section 12.
- F-011 and F-041 are NOT in this step's 20 minutes (G2). Here the lead only writes their status.
- Record the F-018 and the by-reading boxes R1 to R11 of OWNER-STEPS with date and time (UTC and IST) from `date -u +%FT%TZ`; tell the owner "re-check done".
- Event estimate check: T-01 3 + T-02 5 + T-03 2 + T-04 15 + T-05 10 + T-06 15 + T-07 3 + T-08 40 + T-09 65 + T-10 45 + T-11 20 = 223 min. Estimates are the lead's own; the lead re-adds T-08 step 0, the stored-active check and the guard proof at re-pin ("lead sets at re-pin").

### T-12 Loopback re-smoke on the harness (no 1-hour limit; starts after 08:00Z and ONLY after the owner's yes; HS-6)
Stand-in SERVICES only (mail, model and HubSpot stand-ins of the loopback re-smoke per RESMOKE-RUNNER-BRIEF). No real credential, no real send, US$0. The take's n8n is STOPPED (T-10 end) while the harness runs.
0. **ASK THE OWNER FIRST (owner 2026-11-16, `memory\owner-resmoke-ask-first-longer-ok-2026-11-16.md`); nothing below starts before his yes.** The earlier yes in `memory\owner-yes-wp6-smoke-2026-11-15.md` does not replace this ask. The ask states: what runs (the harness loopback re-smoke, stand-in services only), the estimated time as clock times in UTC and IST (start and end; the lead computes them from the re-pin progress, no figure is fixed in this file), the cost (US$0 loopback, no live model call unless the ask says so) and what it covers. The 1-hour figure of v4.1 is no longer a limit: the re-smoke runs as long as the rehearsal needs, and the lead reports the estimate honestly and corrects it with the real clock.
1. **Harness copy, own folder and ports.** The lead makes the harness copy at `<HARNESS_DIR>` with its OWN n8n folder `<HARNESS_N8N_FOLDER>` (mode 700), its OWN port `<HARNESS_PORT>` (not 5678, 5679 or `<PORT_TAKE>`) and its own values file `<HARNESS_VALUES>` (`resmoke-values.env`, made-up strings). Register row first. The harness uses its own copy of `n8n_start.sh` and `n8n_kill.py` from `<FINAL_HEAD>` (the same r31 lock design). It never reads or writes `<TAKE_FOLDER>` or the take's credentials.
2. **PSG for the harness** (section 6 steps 1 to 6 and 7 at activation; domains on `<HARNESS_VALUES>`; port proof PORT-FREE `<HARNESS_PORT>`).
3. **Stand-in assertion (M-M).** SH-FILE `standin-assert.sh` (shape; the lead adjusts the patterns to the names read at re-pin, U-28): `while IFS== read -r k v; do case "$k" in *_HOST|DESK_URL) h=$(printf '%s' "$v" | sed -E 's#^[a-z]+://##; s#[:/].*$##'); n=$((n+1)); case "$h" in 127.0.0.1|localhost) echo "$k PASS";; *) echo "$k FAIL"; bad=$((bad+1));; esac;; *_KEY) n=$((n+1)); echo "$k NAMED";; esac; done < <HARNESS_VALUES>; echo checked=${n:-0} bad=${bad:-0}`. Expect every `*_HOST` and `DESK_URL` PASS (loopback, i.e. a local stand-in SERVICE), every `*_KEY` NAMED with its paired service host among the PASS lines, `bad=0`, and `checked` equal to the number of names the U-28 list holds (a `checked=0` or short count means the pattern is wrong: STOP). A key is only as safe as the host it is sent to, so the host check carries the assertion. Written in `<TAKE_NOTES>` (names and PASS/FAIL only).
4. **Node 24 gate for the harness n8n:** the HS-12 check (section 7) with the harness's own binaries.
5. **Start the harness n8n** with the ONE start form (section 7, harness folder and `<HARNESS_PORT>`), bounded readiness as T-08 step 7 (`ready.sh` with `<HARNESS_PORT>`), port and node proof (`ss -ltnp`, `readlink`). Stored-active check as T-08 step 6 on the harness folder (fresh folder: "none stored"). `<N8NAPI>`-style `list` with the harness port: all inactive.
6. **Import and activation proof.** Import the harness's filled flows from `<HARNESS_FILLED_DIR>` (sub-flow first, then the three; inactive); `list` = 4 inactive. Activation route (HS-4): activate the entry flows by NAME; `list` shows exactly those active and the sub-flow inactive; then deactivate; `list` = 0 active.
7. **Post-twice test.** PSG step 7 (activate), then `<POST_TWICE>` against the harness webhook with one new made-up key: two byte-identical posts. Pass: the script log shows exactly 2 posts; exactly 1 mail at the stand-in mail service; exactly 1 row (harness database); exactly 1 record at the stand-in HubSpot service; no second mail after the wait. DEACT.
8. **Run the re-smoke command and test list** (HS-6) through the runner of the resmoke brief; pass lines per the plan with HEAD_PIN from T-04 and note N6.
9. **Stop and verify:** STOP-N8N for the harness (its own folder), then PORT-FREE `<HARNESS_PORT>`; stop its stand-in services by the register rows (only items the lead started). Result and the number of assertions written in `<TAKE_NOTES>`. Green = G1 satisfied for the re-smoke.

### 8A. Tue / Wed script block (LEAD DECISION 2026-11-16, owner may veto)
Time box: lead sets at re-pin (not in any source). Review: every script below has a path and sha in `<TAKE_NOTES>`; the byte-identical-body check (Q29-4) is done by `flows-audit` (the cloud audit) plus ONE `egm:*` reviewer agent (never a general-purpose agent, never handed the author's verdict); the reviewer reads the script and a recorded run log.

| List | Script (name) | Needed by | Contract (names, no code) | Review slot |
|---|---|---|---|---|
| **needed Tue** | `<EXPORT_SCRIPT>` (HS-5) | T-10, section 10 | REST export of the four flows into `<EXPORT>`; key from `<KEY_FILE>`; never prints the key | before Tue 14:00Z GO; clock time: lead sets at re-pin |
| needed Tue | harness re-smoke command + test list (HS-6) | T-12 | runs the plan through the runner of the resmoke brief | before Tue 14:00Z GO; lead sets at re-pin |
| needed Tue | `<POST_TWICE>` (HS-9) | T-12 step 7, W-01, W-03, W-05 form (a) | posts the SAME stored body twice, byte-identical, logs both posts with time and status; Q29-4 reader | before Tue 14:00Z GO; lead sets at re-pin |
| needed Tue | SELECT-only SQL + `q-*.sh` wrappers (HS-2) | T-08 steps 2, 3, 9 and every count after | role statement, negative test, wrappers of section 2 | before Tue 14:00Z GO; lead sets at re-pin |
| needed Tue | activate/deactivate route (HS-4) | T-12 step 6, PSG, DEACT | only if `n8n_api.py` lacks it | before Tue 14:00Z GO; lead sets at re-pin |
| **needed Wed** | `<MAILCOUNT>` (HS-7) | positive control, Row 4, W-03, W-05 | counts mails to the intake address after `<WAIT_S>`; wraps `imap_count.py`; positive-control form sends 2 made-up mails with different ids | reviewed before Wed about 06:00Z (positive control start); clock time: lead sets at re-pin |
| needed Wed | `<T19_21_RUNNER>` (HS-8) | W-01 | T19, T20 (200 invalid keys; stops at the first non-422), T21 (database down) per the spec | reviewed before Wed about 06:00Z; lead sets at re-pin |
| needed Wed | `<SINGLE_POST>` (HS-13) | Row 4 | posts ONE stored body once to the entry hook; refuses a key already used; prints the status line and the key only | reviewed before Wed about 07:00Z (Row 4 start); lead sets at re-pin |
| needed Wed | `<HS_SEARCH>` (HS-14) | Row 4 check d, W-03 (v), section 10 steps 2 and 5 | read-only search by address or by prefix; no write call; shows a read-only identity | reviewed before Wed about 07:00Z; lead sets at re-pin |

**Early NO-GO tripwire.** The Tue list is the part that gates 14:00Z. If fewer than the threshold (**lead sets at re-pin**) of the five "needed Tue" scripts are written and reviewed by the check time (**lead sets at re-pin**), the lead declares NO-GO at that moment (does not wait for 14:00Z), tells the owner in one line and starts the NO-GO path (section 11). Likewise, a "needed Wed" script not reviewed by its Wed time above is a HARD STOP for the phase it feeds (that day's phase slips, or the take is NO-GO that day).

## 9. WEDNESDAY 18 Nov (path GO)

There is ONE filled set (`<FILLED>`) with real credentials in every phase; nothing is swapped. Every phase starts with PSG (activate last) and ends with DEACT.

### W-00 Restart, positive control FIRST (before T19, before Row 4) (about 06:00Z, inside the practice hour)
1. Restart the take's n8n: T-08 steps 4 (HS-12 check), 5 (port proof), 6 (stored-active check), 7 (start, readiness, proofs, `list`) with the SAME `<TAKE_FOLDER>` and a NEW `<TAKE_TAG>` for each take-program run. `<N8NAPI> list` shows 0 active.
2. PSG for "positive control": keys and mailbox words written; domains pass; `<KEY_PREFIX>` and the keys file written.
3. **Positive control** (T15, no model call, HS-7): two made-up mails with two DIFFERENT ids to the intake mailbox using `<MAILCOUNT>`'s positive-control form; the intake mailbox must show exactly 2 after `<WAIT_S>`. Not 2: the counting method is wrong, every mailbox count after it is void, nothing else in W-01 to W-05 starts (G12). Write the result in `<TAKE_NOTES>`.

### W-01 Practice run with T19, T20, T21 (06:00 to 07:00Z, 11:30 to 12:30 IST, 60 min)
- PSG "practice" passes; activate the entry flows and the recovery flow by NAME in PSG step 7; `<N8NAPI> list` expect three `active`, the sub-flow `inactive`; expect `<NAME> 200` each. The flows carry the real credentials: T19 and T21 each create one made-up contact (section 4).
- Take program, for later phases (its two forms): `python scripts/run_real_check_n8n.py --take <TAKE_SETTINGS>` (a person at the keyboard; typed `y`, then a confirmation line: the random 6-digit number shown, a space and the take id; an answer faster than a person can read is refused) and `python scripts/run_real_check_n8n.py --retire-check <TAKE_SETTINGS>` (after the take). Exit codes: pass 0; answer not `y` or line mismatch 1; refusal (config, probe, no keyboard, end of input, signal before first send, answer too fast, keys or TAKE_TAG already used, second take of the same tag, window too close, second mailbox) 2; a count or verdict failure 3. Settings file: copy `scripts/real-run-n8n.env.example` to the Linux filesystem; `REAL_IMAP_1_FOLDERS=demo` is required; `N8N_HEALTH_URL` must be the readiness address.
- T19 to T21 runner (HS-8). Pass lines (written once, in the F-002 row of FINDINGS.md): T19 reply to POST 2 arrives inside the test's own fixed 10 s bound AND exactly one mail exists (that 10 s belongs to this test only; the take has no "under 10 s" line, Q25-3); T20 200 invalid keys each get 422 and no row is written (stop at the first non-422); T21 database down gives 503 `retry` (not 200, not a bare 500), then the same key resent works and sends one mail. A Postgres-node error at T19 can mean the container password and the credential password differ (T-08 step 2): check that first.
- T21 database stop and start (scope: the take database's own container only). In PowerShell: first confirm the id is still the recorded one: `docker ps -q --filter "name=^<PG_CONTAINER>$"` returns exactly `<PG_CID>` (zero or two ids: STOP); `docker stop <PG_CID>; "exit=$LASTEXITCODE"`. Run the T21 request, expect 503 `retry`. Then `docker start <PG_CID>; "exit=$LASTEXITCODE"`, wait for ready with a bounded PowerShell `for` loop (at most 12 tries, 5 s apart) over `docker exec <PG_CID> pg_isready`, then resend the same key, expect one mail. Never `docker stop` any other id.
- Read before the run, once: the take program has no HubSpot write, delete or archive call and shows a read-only identity at start-up (exact start-up line: lead writes at re-pin; NOT CHECKED until then, U-15).
- Expect: T19 to T21 pass; F-002 lifted in the ledger (BL-flowslocal-4). Failure: T19 fails: the F-002 fallback changes the generator: new sha, T-06 to T-10 again (about 168 min): NO-GO that day (G5). T20 or T21 fails: F-002 stays Blocker. F-002 open at 07:30Z: NO-GO that day (G4).
- DEACT at the end of the practice run.

### W-02 Row 4: ONE made-up lead through the real HubSpot trial account (07:00 to 07:30Z, 12:30 to 13:00 IST, 30 min)
- Before: PSG "Row 4" passes (made-up address `<KEY>@<allow-listed domain>`, key unused); the lead states the ceiling and the maximum new contacts from section 4 (up to 3 sends; the owner is NOT asked, Q25-1). Mailbox words confirmed; `<WAIT_S>` and `<TRIES>` have first values; the lead writes the HubSpot before-value with `<HS_SEARCH>` ("search by address finds nothing"). The positive control passed.
- Part 1: send ONE made-up person (new key, made-up address) with `<SINGLE_POST>` (HS-13).
- Part 2 (four read-only checks):
  - (a) `q-row.sh <KEY>`: expect `state=done crm_id_digits=yes`.
  - (b) `q-count-key.sh <KEY>`: expect exactly 1.
  - (c) the mailbox count after `<WAIT_S>`: exactly 1 mail for that address (`<MAILCOUNT>`).
  - (d) HubSpot search by the made-up address (`<HS_SEARCH>`): exactly 1 contact; write the contact id.
- Failure: any check off: do not start the rehearsal; one sentence to the owner; the next try uses a new key and address (sends counted against the up-to-3 ceiling; each extra contact is a new made-up contact that the section 10 step 5 clean-up will include). A contact count alone is NOT proof of "once". Non-digit crm_id: check P4a (G8).
- **No delete now (m6).** The Row 4 contact STAYS in the trial account until the one owner clean-up after the take (section 10 step 5); the lead sends no Step D message here and the owner does nothing at Row 4.
- DEACT.

### W-03 Rehearsal (07:30 to 09:30Z, 13:00 to 15:00 IST, about 2 h)
1. PSG "rehearsal" passes; activate by name. (The rehearsal goes into the real trial account: up to 4 new made-up contacts, section 4.)
2. Start-state gate (T1), five checks: (i) `q-count-keys.sh <keys-file>` expect 0; (ii) `q-nonfinal.sh` (counts rows whose state is not in `done`, `review`, `unknown`, `failed`; whole table) expect 0; (iii) the intake mailbox shows 0 mails for the take's addresses; (iv) the n8n run list filtered to runs after this attempt is empty; (v) HubSpot search (`<HS_SEARCH>`) finds nothing for the take's addresses.
3. Rehearsal 1 (measures N, the wait and the scene 4 takeover time): the lead writes the expected run list and WHEN POST 2 is sent (after the first run finished, or while it holds the claim; FIX-PLAN rule d); times Qualify and the CRM write against the 45 s lease (rule e); the real HubSpot latency is now included in these numbers. `<POST_TWICE>` sends the SAME stored body twice with identical bytes and logs both posts with times.
4. Scene 4 rehearsal: with the post in flight, STOP-N8N for the take's n8n (then PORT-FREE `<PORT_TAKE>`), then start it again with the T-08 step 7 start form (same folder). Time on the lead's own clock, off screen, from the n8n start until the stopped row goes `processing` to `done` by itself. **The old "about 75 s" is not valid after r31: the stop waits up to 45 s, then up to 5 s after SIGKILL, then the 3 s probe (53 s worst case; the earlier "8 to 10 s" is not relied on) and the outer start shell waits, so the elapsed time is re-measured here and written in `<TAKE_NOTES>`; the 45 s lease plus a 30 s check describes the flow, not a promise of the total.** `<LIMIT_S>` = 180 s unless the rehearsal shows otherwise. A lingering child keeping the lock open would refuse the restart (correct); the stop kills it too. After the restart, `<N8NAPI> list` and DEACT/PSG activation as for any start.
5. The lead sets the numbers (step 22 of the cloud RUNBOOK): N seconds, `<WAIT_S>`, `<TRIES>`, `<LIMIT_S>`; each written with the rehearsal it came from. No numbers: the take does not start (HS-10).
6. Rehearsal 2 repeats the exact choices with the numbers, **with NEW keys, a new PSG line and a new start-state gate (the five checks of step 2) before it starts**. Pass: the run list equals the written one; exactly 1 mail after `<WAIT_S>` AND the row `done`; mailbox recounted after the stated wait (Q29-2); no extra mail; takeover inside `<LIMIT_S>` (else scene 4 is cut, G6 rule 2).
- Failure: a third mail, a stray alert or an unexplained row state: find the cause before the take (G11). DEACT after the rehearsal.

### W-04 Start-state gate, sign-off and GO check (09:30 to 10:00Z, 15:00 to 15:30 IST; gate about 25 min)
- Fresh keys (starting with `<KEY_PREFIX>`) and fresh made-up addresses used nowhere before, new `<TAKE_TAG>`. Repeat the FIVE checks of W-03 step 2 for the NEW keys (expect 0, 0, 0 mails, empty run list, nothing in HubSpot). If anything in n8n was edited since T-10, export again into a new folder and run take_check (exit 0, T-07 counts).
- PSG "take" passes, including the ceiling row for the take (maximum new contacts written) and the take's own port proof.
- Sign-off on the sha(s), screens list, run list, numbers and abort rule (U-17, HS-10). Screens shown but never clicked: credentials, Settings, node output holding environment values.
- GO check (G6 rules 1 and 2): the lead writes the time and the decision. Counts proof not green: the take slips (until Mon 23 Nov 12:00Z).

### W-05 THE TAKE (about 10:00 to 11:00Z, 15:30 to 16:30 IST, about 1 h)
- Recording: the lead records via Playwright; the owner never operates the screens. Do not call the desk doors (F-019). Watch the screens list.
- Tell the owner in the chat what the three typed items are, before the take (decision 7). **OWNER** types, on camera: `y`, the challenge (the confirmation number shown plus a space and the take id) and `end`.
- Take command: HS-9 (form (a) post-twice script or form (b) `run_real_check_n8n.py --take`; its notice states 3 people, maximum model calls, contacts and mails; it prints counts and lead keys only).
- Scenes 1 to 3: the same lead ID POSTed twice, identical bytes (the script log shows exactly 2 posts). Scene 4: stop and start n8n as in W-03 step 4; CUT scene 4 if no takeover shows within `<LIMIT_S>`; the takeover line is spoken only after a rehearsal showed it.
- Counts proof AFTER the take, shown in frame so the caption claims only what is on screen. **ONE form is written in `<TAKE_NOTES>` before W-04 (U-27):** DECISIONS item 9 and Q28-2 name the on-screen proof form (a screenshot or an n8n Postgres node preview); the wrapper `q-row.sh <KEY>` is the lead's own read-only cross-check, run off screen, unless the lead decides at re-pin that a live read is the frame form. Cross-check: `q-count-key.sh <KEY>` and the state and attempts of the row; the intake mailbox count after `<WAIT_S>` and once more after the stated wait: exactly 1 mail. Screen label: "from the take, read after it, SELECT-only login". `result.json` in `<TAKE_FOLDER>` shows `archive_contacts` = `no`.
- Pass: exactly 2 identical posts; exactly 1 mail; one row `done`; no extra mail.
- Failure: a third post, a changed body, 0 or 2+ mails, another state: stop, retake with new keys and a new address (back to W-04). An extra mail is never explained away.
- **Take program behaviour the lead knows (r24 Lane D and Lane A findings; form (b) `run_real_check_n8n.py --take`).**
  1. Ctrl-C in the closing phase looks inert for up to 120 s: press it ONCE and wait.
  2. A further signal after 120 s ends a hung clean-up; `result.json` may then be absent, and exit 3 plus the console lines are the record.
  3. If `result.json` is absent, find the take's contacts by searching HubSpot for `take-<tag>-a`, `take-<tag>-b` and `take-<tag>-c` (read-only `<HS_SEARCH>`).
  4. An uncaught failure prints `the take could not run: ...` with no traceback and exits 2 (exit 3 once a send began). A line starting `<withheld` means a secret file was unreadable: stop and fix its permissions. ROUND 28 PENDING: wording applies after r28 lands (Lane D Major 1: the secret files are then read once before any send, so a `<withheld` line can appear only before a send).
  5. ROUND 28 PENDING: wording applies after r28 lands (Lane A M1): the time window is re-checked after the `y` prompt and the confirmation line, before the marker file and the first send; a refusal then spends no tag. Until then the window is checked only before the prompts, so a slow answer can run past it.
  6. ROUND 28 PENDING: wording applies after r28 lands (Lane A M4): `result.json` is written to a `.tmp` file and linked into place, so it is write-once and never half-written; the lead copies it to `<EVID>` as before and a leftover `result.json.tmp` is read as a failed write. Until then a write failure at close can leave a half-written `result.json`.
  7. ROUND 28 PENDING: wording applies after r28 lands (Lane A M5): if the take is interrupted while person C's post is running, the result carries the reason `person C's post may still be in flight`; the lead then counts the rows, the mails and the HubSpot contacts for person C after the wait and does not call it clean. Until then the post thread may still be posting after the interrupt.
- DEACT immediately after the counts proof. Caption on screen and card (exact): `In this recording, the same lead ID sent twice gave one e-mail message in the intake mailbox.` Closing card one line, no numbers. No Step D message now: the contacts of the take stay until the one owner clean-up (section 10 step 5).

## 10. AFTER THE TAKE (same day): watch and copy FIRST, then hand over, then clean up, revoke and tear down

Order matters: nothing is handed over, revoked or deleted before step 3 passes. A retake after revocation is impossible: the owner would have to create a new model key and new app passwords, and the n8n credentials, `<TAKE_FOLDER>` and database would have to be rebuilt.

1. **Copy out first.** Copy `<TAKE_FOLDER>/result.json`, the take program's log, the script log (both posts with times), `<LOG>` and `<LOG2>` and the recording's sha-256 into `<EVID>` (masked outputs only; the lead never opens secret files). Also copy the masked state counts BEFORE any teardown: the output of `q-state-group.sh`. Verify each copy exists and has non-zero size: `Get-Item <EVID>\* | Select-Object Name,Length`.
2. **Read-only listing of what the take left behind** (the program prints a CLEAN-UP list at its end and only reads HubSpot, never deletes): made-up contacts by prefix and contact id via `<HS_SEARCH>` (read-only, HS-14); if the listing failed, search `<KEY_PREFIX>`-based addresses by hand. Plus `q-state-group.sh`, `q-count-prefix.sh <KEY_PREFIX>` and `<N8NAPI> list` (names and active flags, no ids; expect 0 active).
3. **Watch the whole recording once, start to end** (about 20 min), before any hand-over, clean-up, revocation or teardown (T9, W-5.29): only made-up addresses, nothing secret, the screens list holds, the counts proof is in frame. Cut or retake if not. Write the verdict in `<TAKE_NOTES>`. If a retake is needed: the same day for a 15:00Z post only if this watch finished by 11:15Z (section 3); otherwise the post slips; a retake needs a new `<TAKE_TAG>`, new keys, a new made-up address, the model key and passwords still valid and the ceiling re-checked.
4. **Hand over the recording** to the owner after the watch, about 11:20Z (method: U-18). The lead never edits it (owner rule 2026-11-16, Q28-2). The lead lists every private address visible on screen; the **OWNER** decides crop, blur, cover or not needed (O5).
5. **ONE owner clean-up, only after the lead writes "no retake, clean-up starts" in `<TAKE_NOTES>`** (times set by the lead, U-19). This is Step D, now one step:
   - The lead counts first: `q-count-prefix.sh <KEY_PREFIX>` (rows with a contact id) and the read-only search count by prefix (`<HS_SEARCH>`); the HubSpot search count is the EXPECTED NUMBER; if the two counts differ the lead writes why in `<TAKE_NOTES>` before sending.
   - The lead sends the owner ONE message: the HubSpot trial account name, the filter text "email contains `<KEY_PREFIX>`" (every made-up address is `<KEY>@<allow-listed domain>`), the expected number, the login route, the menu names to Contacts and to bulk delete, and what HubSpot shows after a delete (never a password).
   - **OWNER** (O4) bulk-deletes every contact in that filtered list by hand (manual, minutes) and replies with the number deleted. The owner confirms the number equals the expected number; a different number: stop, nothing more is deleted, tell the lead.
   - The lead re-runs the read-only search: expect 0 for the prefix; the take identity stays read-only and the lead never deletes. Only then: (S9-2, O6) the owner compares, by himself, the figures in the take's settings file; (S9-3, O7) the owner revokes the model key and, per the program's list, the SENDER and RECEIVER app passwords and the two HubSpot private apps. Step A stays removed (Q28-3). Q27-10 says the owner does S9-2 and S9-3 "the same day"; the lead holds the "clean-up starts" message until step 3 passes, and after it the owner cannot retake without new keys.
6. **Lead clean-up (from the program's own list), after step 5:** in the n8n screen delete the credentials the take used (the 3 real ones) and turn "save successful production executions" back off in each workflow; STOP-N8N for the take's n8n, then PORT-FREE `<PORT_TAKE>`. **Delete only after a path guard**: the SH-FILE `rm-guard.sh` runs `p=$(realpath <TAKE_FOLDER>); case "$p" in <N8N_TAKE_ROOT>/*) echo guard-ok "$p";; *) echo GUARD-FAIL "$p"; exit 1;; esac` and prints `ls -la` of that one folder; only on `guard-ok` and with the step 1 copies present the lead runs `rm -rf` on that one path. NOTE: if DECIDE-AT-REPIN-1 reused the OWNER's existing take n8n folder, this step does not delete it: the lead deletes only what this take created inside it (result.json already copied, take-specific files) and asks the owner whether to keep the folder; the default is keep. Database container: `docker ps -q --filter "name=^<PG_CONTAINER>$"` must return exactly `<PG_CID>`; then `docker rm -f -v <PG_CID>`; do NOT delete `<TAG_MARKER_DIR>/<TAG>.used`.
7. **Retire check** (after the owner revokes): `python scripts/run_real_check_n8n.py --retire-check <TAKE_SETTINGS>; "exit=$LASTEXITCODE"`. Expect 0 (both logins refused). Exit 3 = a login still works: tell the owner at once. Exit 2 = anything else.
8. **OWNER** (O8) edits the video (about 120 min) and posts on LinkedIn Wed 18 Nov 15:00Z (20:30 IST), or at the latest Wed 25 Nov 15:00Z (20:30 IST) on a slipped take.
9. End-of-block routine (CLAUDE.md): ledger rows, SESSION-HANDOFF tables, one memory file plus index line, `_local\agents-register.md`, studio commit.

## 11. If something is NO-GO, quick routing

| Event | Do |
|---|---|
| Tue 14:00Z NO-GO, or the 8A tripwire fires | take later, before Mon 23 Nov 18:29Z; re-pin done by Mon 23 Nov 07:00Z (G7). One repeat of T-06 to T-10 takes about 168 min (15 + 3 + 40 + 65 + 45); the re-pin event of 223 min must start by Mon 23 Nov 03:17Z to be done by 07:00Z. |
| Wed 07:30Z F-002 open | Wed NO-GO; try again the next day at the same times |
| Take counts not green | slip one day at the same times, until Mon 23 Nov 12:00Z |
| Scene 4 takeover not inside 3 min | scene 4 cut; take goes ahead (G6 rule 2) |
| Retake needed | gate 25 + take 60 + edit 120 + watch 20 = 225 min; a 15:00Z post needs the gate to start by 11:15Z |
| Second start not refused (T-08 step 10) or a node 20 path in `readlink` | STOP-N8N, PORT-FREE, review lane; no take on this head |
| Stored-active flow found at start (T-08 step 6) | deactivate at once, DEACT shows 0 active before any post; tell the owner in one line |

## 12. Stale texts the lead corrects at re-pin (listed, not edited here)

- `take_check.sh` INFO sentence "must be deleted at clean-up"; `fill_flows/README.md` clean-up item 3 (about line 240).
- `TAKE_CHECK_FLOWS` and `TAKE_CHECK_WARN_PIN` forms in FIX-PLAN item 3, TAKE-CHECKLIST check 1, `flow-check/README.md` item 4 (use `--flows DIR`).
- OWNER-STEPS "import before fill" (fill comes first).
- TAKE-CHECKLIST Step D and FIX-PLAN step 14: "HubSpot probe needs the owner's written yes with numbers" (superseded by Q25-1); Step D as several messages (superseded by the one clean-up of section 10 step 5).
- FIX-PLAN steps 11 to 13 and rule b3: "about 10 s" second-reply criteria (superseded by Q25-3).
- `QUEUE.md` line 8, `ORDERS.md` line 20, `PLAN-4-NLITE-FROM-LEAD.md` line 106 (contradict decision 2, no deletion).
- DECISIONS items 1, 7 and 12; VIDEO-RUNSHEET N-9, N-10, N-11 (Q28-5, Q30-1). DECISIONS item 10 deviates by DECIDE-AT-REPIN-2.
- The cloud `RUNBOOK.md` uses a 3.5 to 4.5 h re-smoke and a separate practice run; the lead's NOTE (14:35Z) made it about 1 hour; SUPERSEDED by owner 2026-11-16: no 1-hour limit, and the lead asks the owner first (T-12 step 0). ORDERS Q25-10 and DECIDE-3 text about a stand-in or "rehearsal not in real HubSpot" is superseded by DECIDE-REAL-ONLY.
- Several time stamps in ORDERS blocks (13:00Z to 15:00Z) are wrong (Q30 correction); use the dated schedule and `date -u +%FT%TZ`.
- v1's `--is-start` and v2's `--start-check` (U-04): neither exists on r31 (flock only).
- The resmoke plans' `n8n.pid == pgid` assertion and any "scene-4 about 75 s" statement (U-29).
- The take program's own text "run n8n_kill.py <take folder>" still works on r31.

## 13. UNVERIFIED items, each with ONE command or a recorded decision

Count: 30 open items (U-01 to U-31; U-25 removed in v4). Commands run from `<STUDIO>` in PowerShell unless noted.

- **U-01** `<FINAL_HEAD>`: `git -C <REPO> log -1 --format=%H take/nlite-merge-m1`
- **U-02** The take command for the video: `git -C <REPO> ls-tree -r --name-only <FINAL_HEAD> | Select-String -Pattern 'post|twice'` (none today). Decision in `<TAKE_NOTES>` before HS-9: form (a) post-twice script or form (b) `--take`.
- **U-03** Post-twice script and the n8n export, activate and deactivate routes: `git -C <REPO> show <FINAL_HEAD>:scripts/n8n_api.py | Select-String -Pattern 'cmd == |activate|deactivate'` (if `activate` and `deactivate` are absent the lead writes that route like the export route, HS-4, HS-5).
- **U-04** Guard text, exit numbers and stop form after r31: `git -C <REPO> show <FINAL_HEAD>:scripts/n8n_start.sh | Select-String -Pattern 'flock|refused|holds|exit|111|symlink|newline|writable|plain file|probe'` and `git -C <REPO> show <FINAL_HEAD>:scripts/n8n_kill.py | Select-String -Pattern 'stopped|holding|refused|exit|130|interrupted|cannot see|cannot finish|usage'` (the exact strings and which exit each refusal gives are re-read here).
- **U-05** `N8N_PORT` honoured: after start, `ss -ltnp | grep :<PORT_TAKE>`. TAKE_TAG scheme recorded before W-00.
- **U-06** API key file: `wsl.exe -d Ubuntu -e sh -c 'test -s <KEY_FILE> && stat -c %a <KEY_FILE>'` expect `600`.
- **U-07** F-018 values loop: definition in the F-018 row of FINDINGS.md; decision recorded before T-09 step 5.
- **U-08** Named WARN reader for T-10 (a person other than the author of the pin): recorded before T-10.
- **U-09** Checkout and sha holding flow files and patches: `git -C <AUDIT_REPO> rev-parse HEAD; git -C <AUDIT_REPO> ls-tree -r --name-only HEAD | Select-String -Pattern 'take_check.sh|fill_flows.py|F-002'`; also the local branch for the T-06 commit and whether `/mnt` paths work for the generator.
- **U-10** Re-smoke command and test list: `Test-Path <STUDIO>\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md`; decision recorded before T-12 (HS-6).
- **U-11** T19 to T21 runner: `Select-String -Path <AUDIT_REPO>\handover\demo\n8n-mainframe\mf.py -Pattern 'T19|T20|T21'` (no hit; written at re-pin, HS-8).
- **U-12** "decision 4" versus "decision 1": `Select-String -Path <FLOWS_AUDIT>\flow-check\take_check.sh -Pattern 'decision 4'`; wording recorded before T-07.
- **U-13** Ledger tool: `python <STUDIO>\egm\tools\ledger_check.py --topic duplicate-proof-lead-desk; "exit=$LASTEXITCODE"`
- **U-14** F-011 and F-041 wording: `Select-String -Path <STUDIO>\egm\BLOCKER-LEDGER.md -Pattern 'F-011|F-041|BL-flowslocal-4'`; decision recorded before the G2 work starts (T-11).
- **U-15** Take program read-only HubSpot start-up line: `git -C <REPO> show <FINAL_HEAD>:scripts/run_real_check_n8n.py | Select-String -Pattern 'probe_hubspot|read-only'`.
- **U-16** Mailbox tool, filter, `<WAIT_S>`, `<TRIES>`, setting names: `git -C <REPO> show <FINAL_HEAD>:src/lead_desk/imap_count.py | Select-Object -First 40` (tool is `imap_count.py`; take program defaults `MAIL_WAIT_SECONDS=150.0`, `MAIL_SETTLE_SECONDS=20.0`, `WAIT_STEP_SECONDS=60.0`; `<TRIES>` and the positive-control command are not in a file, HS-7).
- **U-17** Sign-off format and screens list: recorded before W-04 (path in HS-10).
- **U-18** How the recording reaches the owner; his editing tool: recorded before W-05.
- **U-19** Clock times of the owner clean-up, S9-2 and S9-3: recorded before section 10 step 5.
- **U-20** CLOSED: Mon 23 Nov 07:00Z reading is "re-pin done by 07:00Z" (section 3).
- **U-21** CLOSED by r23 and kept in r31: the outer shell waits; Start-Process background form required. Re-confirm: `git -C <REPO> show <FINAL_HEAD>:scripts/n8n_start.sh | Select-String -Pattern 'exec|flock'`.
- **U-22** Does the take program refuse a folder that already holds `result.json`: `git -C <REPO> show <FINAL_HEAD>:scripts/run_real_check_n8n.py | Select-String -Pattern 'result.json'`
- **U-23** Does `take_check.sh` read an `active` flag: `Select-String -Path <FLOWS_AUDIT>\flow-check\take_check.sh -Pattern 'active'`
- **U-24** How `n8n_start.sh` treats PATH and which node it finds: `git -C <REPO> show <FINAL_HEAD>:scripts/n8n_start.sh | Select-String -Pattern 'PATH|node|env -i'`; recorded before T-08 step 7; proof by `readlink /proc/<pid>/exe`.
- **U-25** REMOVED in v4 (the stand-in HubSpot credential is dropped).
- **U-26** The backstop setting name and location and the spend-ledger file name: recorded in `<TAKE_NOTES>`.
- **U-27** Which counts-proof form is in frame: recorded before W-04.
- **U-28** Setting names for the re-smoke stand-in assertion (model key, model host, mail host, IMAP host, desk URL in `<HARNESS_VALUES>`) and the count of names: read at re-pin (names only), recorded before T-12.
- **U-29** The resmoke plans' `n8n.pid == pgid` assertion and any timing that assumed the old stop: `Select-String -Path <STUDIO>\egm\duplicate-proof-lead-desk\wp6\plan-wp6-resmoke-v5.md -Pattern 'pgid|75'`; replaced by the lock-holder check or dropped (note N6).
- **U-30** (new) The WSL `psql` client is present (T-08 step 0d) and the store type and path of the take folder's n8n store (for the stored-active check, T-08 step 6): recorded in `<TAKE_NOTES>`.
- **U-31** (new) Which credential-id source of DECIDE-AT-REPIN-7 works (list route, ids inside exported workflow JSON, or O0c): verified at re-pin, recorded before T-08 step 8.

Also not checked by this document: whether the four patches still apply to the committed audit tree today; whether `build_mainframe.py` still reproduces real-v5; whether fill_flows and take_check run on the lead's laptop; every n8n screen and setting name; the real HubSpot reply; `check_patches.sh` result; disk and slots (`tools\heavy_slot.py` exists; the resmoke brief says a manual run does not use it); whether `docker` is installed and which image is usable; the r23 branch's review beyond Lane D, tests and mutants; whether n8n's public API has a credentials list route.

## 14. Owner steps (everything the owner does, nothing else)

| # | OWNER step | When (UTC / IST) |
|---|---|---|
| O0 | ONLY IF the T-08 step 0 check finds something missing (the API key is already in the local env and in the n8n credentials per the owner 2026-11-16; the lead reports what is missing by name and count only, never a value): the n8n folder, owner account, API key file, container password file or a credential: place what the lead's one-message ask names (API key file at the path the lead names, mode 600; the Postgres container password file; the three credentials by hand if absent, with host, port and database written first by the lead); confirm one password for container and credential. Never needed if all exist. | Tue, in the re-pin chat, before T-08 step 1 |
| O0c | ONLY IF the T-08 step 0 check finds a credential missing or neither the list route nor the exported workflow JSON gives the credential ids (reported by name and count only): read the names and ids of the three credentials from the credentials screen and tell the lead (ids are not secrets; never the data) | Tue, before T-08 step 8 |
| O1 | Answer the one question about the HubSpot token scopes (the lead asks once at take prep) | Tue, in the re-pin chat |
| O3 | On camera type `y`, the challenge and `end` (the lead explains each first) | the take, about Wed 10:00Z / 15:30 IST |
| O4 | ONE clean-up: bulk-delete every contact in the filtered HubSpot list (email contains `<KEY_PREFIX>`) and reply with the number deleted, which must equal the expected number the lead gave | after the lead's watch and "clean-up starts", about Wed 11:20Z / 16:50 IST or later (time U-19) |
| O5 | Decide crop, blur, cover or not needed for each private address the lead lists | after the watch, about Wed 11:20Z |
| O6 | S9-2: compare the figures in the settings file by himself | same day, after the lead's "clean-up starts" |
| O7 | S9-3: revoke the model key (and, per the program's list, the sender and receiver app passwords and the two HubSpot private apps) only after the lead confirms the HubSpot contact count for the prefix is 0 | same day, time set by the lead (U-19) |
| O8 | Edit the video and post on LinkedIn | Wed 18 Nov 15:00Z / 20:30 IST (latest Wed 25 Nov 15:00Z / 20:30 IST) |

(v3's O0b and O2 are dropped.) The owner creates no credentials unless O0 or O0c triggers (they already exist per FACTS-ALREADY-DONE), is asked for no money yes (Q25-1) and does not type any path. LEAD DECISIONS 2026-11-16 are marked in the sections above; the owner may veto any of them, and a veto replaces the default and nothing else.

## 15. Map: every finding to where v4 fixes it

| Finding | Fixed in v4 | Fully fixed? |
|---|---|---|
| READINESS-3 B1 T-12 missing; dangling T-12/T-13 references | T-12 steps 1 to 9; STOP-N8N and PORT-FREE defined once (section 2); U-14 now cites T-11; HS-6, HS-4, HS-9, G1, section 4 point to T-12 | Yes; names read at re-pin (U-28) |
| B2 stand-in contradiction (U-25) | stand-in dropped entirely; DECIDE-REAL-ONLY; section 4 contact column; one filled set; G13 rewritten | Yes |
| M1 `$HOME` | `<HOME_ABS>` resolved once (T-01, section 2); `$HOME` only in `.sh` files | Yes |
| M2 T-09 real set on Tuesday (SUB_WORKFLOW_ID per set) | one set only; T-09 steps 1 to 7 | Yes |
| M3 swap re-verify and time | swap step removed | Yes |
| M4 credential-id source | DECIDE-AT-REPIN-7 (three sources in order), T-08 step 0c, O0c, U-31 | Procedure yes; verified at re-pin |
| M5 psql quoting and connection source | SQL WRAPPERS rule (section 2), `q-*.sh` in 8A, every count command | Yes; wrappers written Tue |
| M6 stored active flows | T-08 steps 6 and 7 (`list` right after start), section 11 row, U-30 | Yes |
| M7 guard proof can hang | T-08 step 10 (`timeout 15`, exit 124 handling, STOP-N8N, PORT-FREE) | Yes |
| M8 8A realism | 8A split Tue/Wed, dated slots from the schedule, tripwire (threshold "lead sets at re-pin"), G1 | Procedure yes; numbers lead sets |
| M9 step numbers, PATH form, W-00 abbreviation | section 7 HS-12 (ONE start form), T-08 renumbered, W-00 cites steps 4 to 7 | Yes |
| M10 PSG domains of the imported set | one values file `<VALUES>` | Yes |
| M11 M-K / M-M | M-K: U-27; M-M: T-12 step 3 | Yes |
| m1 port grep | PORT-FREE (`ss -H -ltn sport = :<PORT>`) | Yes |
| m2 container exists, port free | T-08 step 2 | Yes |
| m3 password match | T-08 steps 0e and 2, W-01 note | Yes |
| m4 start exit code | T-08 step 7, U-04 | Yes |
| m5 exit 10 | T-08 step 7 (v4.1: the exit 10 paragraph is removed; a held lock is internal exit 111 and the refusal exits 2) | Yes |
| m6 W-02 Step D wording | W-02 "No delete now"; section 10 step 5 | Yes |
| m7 spend row timing | section 4 Total row (before W-01, backstop and ledger read once) | Yes |
| m8 G13 search note | G13 one-line rule | Yes |
| m9 T-06 "all four exit 0" | T-06 "2 checks and 2 applies" | Yes |
| Lane D F1 to F3 | section 0 facts, STOP-N8N, PORT-FREE, T-08 steps 0d, 7, 10, W-03 step 4, U-04, U-29 | Yes (exact lines re-read at `<FINAL_HEAD>`) |
| Round 25 schema `app.mf_leads` | `<MF_TABLE>`, HS-16, T-08 steps 2, 3 and 9, every wrapper | Procedure yes; SQL the lead writes at re-pin |
