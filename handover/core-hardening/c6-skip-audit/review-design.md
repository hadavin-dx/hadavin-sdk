# C6 review, design critic (egm-design), condensed copy of the inline report, 2026-11-16
Not run: n8n, lane3 reports (absent). Tree: scratchpad c6/tree (full copy of origin/cloud/flows-audit).
Verdict: audit mostly sound; cites check out; downgrades of F-006, F-007, F-023 defensible. Two gaps matter for filming (M1, M2); one understated item (M3).

## Major
- M1 Run sheet scene 4 caption contradicts the sheet's own rules; the audit missed it. VIDEO-RUNSHEET.md:90 sets a FINAL caption with a number ("about a minute after the crash, measured at lease 45 s: 18 kill runs, 60.1 to 61.9 s"), while :22 says the 45 s lease is UNMEASURED, :85 says NO number until lane3 numbers land, :90 itself says "Raw not seen by me", and PAGE-STATEMENTS-V4.md:149 says "I read nothing". Decide before the take: read and cite the lane3 raw, or drop the number.
- M2 Saved runs ON invalidates privacy test T7b and the old "saving off" text. mf.py:276-278 sets EXECUTIONS_DATA_SAVE_ON_SUCCESS/ERROR="none" and T7b passes only with name and e-mail 0 hits when saving is off; plan v5:125 sets saving "all". Re-scope T7b: name and e-mail may appear in the n8n database; key and SMTP password must stay 0 hits. Add to F-011 fix and test.
- M3 F-007 reach understated. Line :90 of the run sheet lets "Kill cases K3B/K3 ... killed after the mail left" be spoken in scene 4, which is false for K3B (mf.py:158: mail NOT delivered). Three-way disagreement confirmed (page :150, run sheet :24, mf.py). Must fix before the take. Fold N4 into it. The proposed wording ("the mail may or may not have gone") is right for the harness case only; do not attribute it to the 18 lane3 runs.

## Ratings per finding
F-006 Major accepted; add the open decision (cut scene 5 or keep the stand-in, run sheet :56, :78) to the fix. F-011 rating right; the fix is already in plan v5:550 and EXCEPTIONS.md:5, so attribute it. F-020 Nit accepted. F-022 Nit accepted; state that mf-form real-v5 (:238-295) only sets n8n_error:false so the bug class does not recur in the take flows. F-023 Nit accepted (ask the laptop agent first). F-025 Nit accepted.

## New items
N1 Major accepted; name which two flow folders are importable (many stale folders also carry mf-form.json); add a check that exactly one set is active per scene. N2 upgrade to Major for filming (empty execution list in scene 1 until the saving patch is applied); make it a gate item. N3 accept (client-build blocker, Nit for the take; ledger it). N4 duplicate of M3. N5 accept as Nit; recommend cutting "80 kills, 0 doubled, 0 lost" from the closing card or labelling it v3, lease 20 s. N6 Nit.

## Minor
m1 flow-set diff claim has no command or output in the report. m2 bible not on disk, so R460 unverifiable. m3 page statement 20 run counts (K1 5, K2 5, K3B 5, K3 3): "18 kill runs" hides n=3 for K3. m4 add "lane3 HB194 raw not read" to the not-checked list.

## Suggested order
M1, M3+N4, M2, F-006+N1, N2, F-011, nits.
