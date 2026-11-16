# patch-copies README.md pass 27 fresh read (agent ac14474e, egm-comprehension), security path, uncapped
Saved by flows-audit, condensed. Reviewer words unverified; static. NOT read: README 1-35, 345-524 (run, verdict_run, proof, final, pass rule), DMC except 1-40 and 234-253, patch bodies, REVIEW.md, repo. Ran nothing. 0 Blockers, 2 Majors, 8 minors. Counts, UTC/IST pairs, function order, rm -rf/cd guards, cleanup-without-logs refusal, gates failures held per reviewer.
M1 README 266 (setup), 190-196: git wrapper not checked; a skipped helper block still gives `setup ok` and git then runs with the user's config (credential helper, templateDir hooks, insteadOf, GIT_* vars). Fix: at top of setup require type -t git, scrub, keep_logs to be functions else STOP.
M2 README 36 (0d) vs 278: "no keys" rule but setup refuses only ~/.netrc, ~/_netrc; ~/.ssh, ~/.aws, ~/.config/gcloud, ~/.config/gh not checked. Fix: STOP with explicit override variable, or say only .netrc is enforced.
m1 L277 SRC checked only for empty/OWNER_NAME; ssh://, git@, user:token@ pass. Fix: STOP on `*://*@*`, `git@*`, `ssh://*`.
m2 L198-212 scrub: `${v%%:*}` mangles IPv6 proxy `[::1]:3128`. Fix: WARNING skip when host starts with `[`.
m3 L235/182: empty $W (first heredoc fails) can never be cleaned. Fix: cleanup accepts a $W holding nothing.
m4 L37 "lint steps" vs words table L66 ("step" = tick job). Fix: "lint parts".
m5 L88 vs 118: BRIEF-PREAMBLE rule 9 quoted two ways; real line 11 "Never merge; the lead merges." Fix: quote fully.
m6 L60, 737, 739, 741: report numbering shared counter inconsistent (r23-r25 vs fix-patchcopies25, r26 vs r24). Fix: one name per report checked against folder.
m7 L737, 739: passes 23 and 24 date without UTC and IST clock time.
m8 DMC 27: D2 "Who" studio head but default LEAD DECIDES; README row 8 (110) says studio head names persons.
