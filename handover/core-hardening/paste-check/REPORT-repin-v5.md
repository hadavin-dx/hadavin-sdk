# REPORT repin v5 (SUPERSEDED by REPORT-repin-v6.md; C3b, round 2 of the re-pin fix pass, 2026-11-16)
Builder: sub-agent (Sonnet 5.5). No sub-agents, no spend, made-up data only. This report is NOT a verdict: the lead runs the EGM reviews (EGM-GATE v1). Evidence: `evidence-c7f.md` (raw).

## 1. FAILURES, UNVERIFIED and NOT RUN (read first)
1. **Nothing was run on the real target.** No PowerShell, no WSL, no Git for Windows, no n8n, no Docker were available. Every test ran in plain bash and dash on this Linux container against stub repos, stub folders and stand-in processes. A pass here does not show a pass on the laptop (differences: Git Bash path forms, WSL `/proc`, `ss`, `setpriv`, CRLF checkouts).
2. **`ss` is not installed here**, so the port-wait loop of `gone()` saw no listener in every test (section 8 of the evidence). The loop with a real listener is untested.
3. **P-4b is only a proposal** (in `LEAD-FILL-list-v5.md`). The "n8n-shaped" and "unreadable" definitions are my guess; the real definitions must come from the final-head `n8n_kill.py`, which I did not read. The tests used uid 65534 via `setpriv` and a non-dumpable stand-in; not tested: a real unreadable n8n, `hidepid` mounts, WSL. P-3b proves only that the control file belongs to the P-4b.sh that exists now and has the right line shape; that the hit lines came from a real run stays the lead's attestation (stated in the plan, UNVERIFIED 15).
4. **The v5 acceptance rule accepted `exit 3x`** (a number followed by any non-digit). This is FIXED in v6 (see `REPORT-repin-v6.md`): after the number only the end of the line, a space, `)`, `;`, `#`, a comma or a quote may follow, so `exit 3x` and `exit 30` both stop. (An earlier line of this report said "accepted as written; not tightened", which contradicted the plan text, which says `exit 30` does not pass; that line is removed.) The v5 rule still proved only that the text `exit 3` exists; v6 says so in the plan.
5. The inline-span extractor of c3 reports 4 spans failing syntax after placeholders (same 4 in v4 and v5). I looked at them: two are a lone `&` (plan text about running in the background, not a command), two are log-line examples `== P-3b <UTC time>` and `== P-4b <UTC time>` (text, not commands). They are not commands, so no fix is needed; this is my reading of their text, not a reviewer's check.
6. The plan's Git Bash commands are shipped as text for the lead or the owner to paste; the lead steps (a) (c) (d) depend on a person on the laptop. This cannot be removed by a patch (exception: needs the owner/lead).
7. The patch is only valid applied after `plan-v5-fixes.patch` and never together with v1 to v4 (both wrong orders fail: evidence section 1).

## 2. Files
- `plan-v5-repin-v5.patch` (268 lines, 15 hunks; `patch -p1` from `core-hardening/`, after `plan-v5-fixes.patch`; replaces v4, which stays as superseded).
- `LEAD-FILL-list-v5.md` (safe defaults only; P-4b proposal with positive and negative control tests).
- `evidence-c7f.md` (raw), this report, `checkpoint-v5.md`.
- `inputs/` and v1 to v4 files are untouched (real inputs plan sha256 starts `67a0a195537de875`, same before and after).

## 3. Finding table (patch line = line in `plan-v5-repin-v5.patch`; many RE-PIN edits sit on patch line 8, which is the one very long plan line 3)
| id | finding | status | where |
|---|---|---|---|
| B1 | positive control for the leftover count | fixed: pattern `^[*][*]HEAD_PIN = \|^[$]HEAD_PIN = ` must match exactly 2 lines; the last check prints a third count `2`; no match = `STOP count control`. Tested: patched plan 24/10/2, simulated flip 0/0/2, wrong path and no-control copy print `0 0 0`/error | patch 5, 7, 8, 109, 110, 125 |
| B2 | P-4b / exit-3 resume rules; plain statement of what is unverified; default STOP | fixed: P-4b step, Resume rules step, UNVERIFIED 15 and 16, LEAD-FILL 1, 1b, 2 | patch 120, 123, 258 to 268 |
| M1 | release line | fixed: `LEAD-GO RE-PIN <UTC time>` written by the lead, must start the line | patch 8, 9, 104 |
| M2 | second fill uses the pin, mismatch prints a STOP | fixed: `PIN=` read via `git show <sha>:`, never HEAD; MISMATCH line; 7 or garbage characters = STOP; tested with 8 cases; LEAD-FILL 5 default none | patch 8 |
| M3 | who runs lead steps a/c, where | fixed: stated as the lead, in Git Bash on the laptop, or the owner pastes and sends output back | patch 8, 9; LEAD-FILL list |
| M4/M5 | R2 paste name, log name, prefix; KILL only if pid alive; `LEAD-YES` by the lead (also facts Major 1) | fixed: R2.sh block with arguments `<pid>` `<which>`, exact `environ` check, TERM, wait 30 s, KILL only if still alive; tested 7 cases | patch 47 to 66, 9 |
| M6 | CR trigger | fixed: the `CR-FIX strings.txt` message and the CR scan before the loop; CR in a P-4b file = STOP | patch 8, 9, 28, 68 |
| M7 | resume path per STOP; P-1 not before the gate | fixed: Preconditions order (P-3a, P-3b, P-4b, P-5 before P-1) and Resume rules | patch 102 to 125 |
| M8 | decisions 6, 7, 8, 12 | handled as out of scope of the re-pin and written down (section 9 bullet; section 10 line for decision 12) | patch 196 to 203 |
| N1 | wording of the gone change | fixed in the changed-output wording text | patch 8 |
| N2 | ignore control-gone after GONE-FAIL | fixed | patch 141 to 143 |
| N3 | S13 after exit 3 | fixed in 13.1 and 13.3 (no R2, alive = STOP, none alive = go on to 13.4 to 13.9) | patch 142, 143 |
| N4 | anchor exit numbers | fixed: by-file rule, anchored; tested 9 made-up outputs (30, main(), 4, constant, 20: STOP) | patch 8 |
| N5 | temp files instead of process substitution | fixed: one diff command with `mktemp` and temp files; tested | patch 8 |
| N6 | names-check list omits UNVERIFIED 16 | fixed: list now includes sections 580 to 584 lines; names check prints them | patch 8, 258 to 268 |
| N7 | not in the task list | n/a | |
| N8 | `grep -nE 'kill\|env.sh' pastes/P-4b.sh` must print nothing | fixed: P-3b word scan (p4b words exit=1 means nothing printed); tested with `kill` in a comment and `env.sh` | patch 117 |
| extra | fill loop dropped a last row without newline | fixed (`\|\| [ -n "$id" ]`); tested | patch 8 |

Patch line numbers in the table are approximate (taken by grep on keywords).

## 4. What I changed after first writing (honest log)
Reworded the P-4b proposal (comments contained the two words the new scan rejects); added a 5 s wait after KILL in R2 (race found by test); changed the MISMATCH wording and re-extracted all spans from the final patched plan before the evidence run.
