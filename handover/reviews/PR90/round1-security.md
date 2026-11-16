# PR90 (core/ci-gitleaks-scope, head fc48b9e) security review round 1 (egm-codebase-details, snapshot 90-fc48b9e)
Verdict: no Blocker; 2 Major, 3 Nit. Reviewer ran nothing.
- M1 (ci.yml:231): after the change no job scans branches other than main/PR heads (draft PRs, branches without PR, force-pushed or deleted commits). Acceptable only if gitleaks guards what reaches main; needs owner confirmation that GitHub native secret scanning + push protection are on, and an owner for handover/backup branches. Ask: PR note that other branches are out of scope, or a non-blocking scheduled --all job.
- M2 (tests/test_ci_gitleaks_scope.py): bare-substring pin passes for HEAD~1000, HEAD^!, HEAD..HEAD, "HEAD --branches", quoted/echo text, flag on a third line. Tighter: exact single --log-opts=HEAD on the joined command, reject --all/--branches/--remotes/--tags.
- Nit: comment "gitleaks scans the whole history" (line 163) and step name now imprecise.
- Nit: a tracked file named HEAD makes `git log HEAD` ambiguous (message confusing, step still fails); `--log-opts="HEAD --"` avoids it (unverified in gitleaks).
- Nit: comment claim about old --all default not confirmed against gitleaks source.
Checked fine: pull_request merge ref covers PR commits + base history; push to main covers full history; stale-ignore step still consistent; --log-opts=HEAD passes to git log (from memory, not run).
Unverified: no gitleaks run; native secret scanning status; ignore entries depending on out-of-scope commits.
## Resolve (me)
- M2 FIXED in head after fc48b9e (tight joined-command pin; fails on old ci.yml and on HEAD~1000, shown in run output). Nit 1 FIXED (labels). Nit 2/3 NOT done (unverified flag syntax; no binary).
- M1: NEEDS LEAD (q400).
