from patch_lib import Doc
d = Doc("CORE-PR-HANDOFF-v14.md")
d.rep("so the UPDATE shape of 5.4 item 4 is in place (security blocker B1);", "so the UPDATE shape of 5.4 item 4 is in place (v13 review finding B1 of v12), **shown by the Postgres test `store emits UPDATE for negative deltas` green in the move PR (5.11 item 4)**;")
d.rep("(iii) the owner has answered D5 or accepted option A in writing (section 1);", "(iii) **NOT a gate by default**: v13 made the owner's answer on D5 a condition, but your answer Q28 says D5 is non-blocking; the held tables keep dollars as today and D5 gates only a NEW spend table; **you decide in L11, and until you answer, (iii) is not applied**;")
d.rep("for DB-2 also (iv) the lead's yes, L9.", "for DB-2 also (iv) the lead's yes, L9, and (v) the operator step `REVOKE TEMPORARY ON DATABASE ... FROM PUBLIC` done and the start-up check green (5.6 item 1c, 5.11 item 1).")
d.rep("(Q34's rule plus the `Infinity` clause)", "(Q34's rule; the `Infinity` clause only if the lead says yes in L7; **DB-1 also carries the seam, the runner gate, CODEOWNERS and the Sonar exclusion, which is more than Q34's one file: L10**)")
d.save()
