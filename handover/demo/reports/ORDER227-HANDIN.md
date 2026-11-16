# ORDER 227 hand-in (cloud session, written by `date -u` 23:1xZ)
No python edits since A4r9. Nothing new started.

## The one diff
`CONSOLIDATED-A4r7-to-A4r9.diff` : A4r7 (= snapshot A4r7, tree /tmp/dpld-s9) -> A4r9 (= /tmp/dpld-s11; contains S1j and S1k and nothing later). 21 files. Checked: applied with `patch -p1` to a clean copy of A4r7 (no caches), `diff -rq` against A4r9 = identical.
(S1j.diff and S1k.diff stay as the two steps; the consolidated one is the same content.)

## Fail-before evidence
- S1j: `S1j-failbefore.txt`, report `S1j-report.md`, full suite `S1j-full.log` (761 passed).
- S1k: `S1k-failbefore.txt`, `S1k-loop30.txt` (30x repeat of the new timing tests), report `S1k-report.md`, full suite `S1k-full.log` (797 passed, 1 skipped, 2 known red: gitleaks and wordlist hygiene).

## Review findings still open on my side (round 9, nothing fixed, Blocker none)
Security lens (`A4-r9-security-lens.md`), Major:
1. a lead given back as busy never ages into the stalled list (desk.py ~1328, `_closed_kind`)
2. a person's `not_sent` while an abandoned blind send or CRM put is still running can lead to a second message/row (desk.py ~1531, 1688)
3. an abandoned refresh/put worker can overwrite the adapter's cached capability late (adapters.py ~85-145) -> a re-send with an ignored key
Code/tests lens (`A4-r9-code-tests-lens.md`), Major: stale exit-4 wording (README:246, contract.md:72); overclaim that model_busy rows age (README:57, contract.md:22); `test_answer_lost_real_lock_keeps_try` does not pin its name; worst-case pass time and chained reads vs 30 s grace (README:71, gate.py:29-32).
Plus nits in both reports (NaN `send_timeout_seconds`, `SHORT=0.2` timing flake, etc.).

## Evidence running on A4r9 (not yet finished)
- Campaign (model-slow, model-timeout, catcher-slow, drain ceiling 1500 s): started 22:43:57Z in /home/user/build/campaign9; model-slow still running at last check.
- Mutation round (81 + 23 new) starts after the campaign (4 cores); Linux full suite = S1k-full.log above.
Counts follow in a later PULSE line and `A4r9-evidence.md`.
