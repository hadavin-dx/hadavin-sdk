# patch-copies README.md round 21 stranger read (agent a6934148, egm-comprehension), security path, uncapped
Saved by flows-audit, condensed. Reviewer words unverified; static (Read/Grep/Glob). Read all 656 lines. NOT read: patch files, REVIEW.md, DMC, source at b4cce5b (no cite, shell syntax or patch-id behaviour checked). 0 Blockers, 1 Major, 9 minors. Fail-closed paths traced OK (missing logs/rc/gates, UNEXPECTED, wrong count, stamp mismatch, early verdict/proof). Arithmetic held (24+6, 26+6, 12+18, 13+19, 9364+30/32, 7/8 files, 10=7+2+1, 18:53Z=00:23 IST next day).
M1 macOS default shell is zsh; recipe is bash-only (${!pv:-}, PIPESTATUS, args+=(), unquoted globs). Fix: "start bash, check echo $BASH_VERSION prints a version, paste in that window"; mark macOS UNVERIFIED in (0b).
m1 Patch files not pinned after sha256sum -c (swap between check and apply/patch-id). Fix: cp the patches into $W after the check and use the copies.
m2 proof: rm -f of proof.txt/proof.log/final.txt comes after the guards; a refused second proof leaves an old PROOF OK that final trusts. Fix: move rm -f right after need_w.
m3 verdict.stamp hashes only the patched clone, not logs/rc/gates.txt. Fix: hash those too and compare in proof and final.
m4 Overclaims: line 3 "to prove what the patch does"; line 348 "(f) new tests really fail on old code": only 12 of 30 fail (18 controls). Fix wording "12 of the 30 new tests fail on old code (counts only)".
m5 cleanup may run without keep_logs when final.txt says PASSED/ADDS NO NEW FAILURE but deletes final.txt. Fix: always require keep_logs or print final.txt first.
m6 keep_logs: scrub failure leaves a partial copy; keep.mark failure leaves K set. Fix: rm partial, unset K before return 1.
m7 Terms before definition: "baseline", "clause (d2)", "fixer session/pass" (lines 13,17,21). Fix: words-box rows.
m8 Function lists lines 4 and 120 omit verdict_run.
m9 Count table sits under "### Cleanup" but lines 462/494 say it is under "Proof..."; verdict row of "What a good run prints" omits the "baseline: [..] patched: [..]" line; ALL_PROXY/all_proxy scrubbed but not passed by extra.env (add a sentence).
