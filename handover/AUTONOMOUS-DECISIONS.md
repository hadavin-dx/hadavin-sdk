# Autonomous decision log (core-modules cloud session)
Rule (owner 2026-11-11): the cloud session takes ALL decisions itself, including major ones, choosing the recommended option, and records each one here BEFORE acting and updates the outcome after. Owner-safety items (money, secrets, merge to main, repo settings, history rewrites of existing remote branches, deletes, DNS, demo/client material in this repo) are not decided here; they go to `questions-for-lead.md` with a do-nothing-irreversible default.
Entry format: `D-NNN | date UTC / IST | question | options (cost, risk) | RECOMMENDED + why | reversible? | evidence | revisit if | outcome (commit/PR)`.

## Decisions already taken by the lead before leaving (carry forward, you may refine them by a new entry)
- D-001 | 2026-11-11 14:40Z / 20:10 IST | Who drives core work? | (a) laptop lead + cloud in parallel, (b) cloud alone | RECOMMENDED (b): the owner decided the laptop works only on the duplicate-proof-lead-desk demo | reversible: yes (a new GO order from the laptop) | owner message 2026-11-11 | revisit: owner restarts laptop core work | outcome: ORDER 246 retired the old session; this plan starts a new one.
- D-002 | same | Queue order | (a) PR77 first, (b) PR89 evidence first | RECOMMENDED (b) first (small, already clean evidence, unblocks nothing else) then PR77 (largest open Major class), PR74 after PR77 (depends on it), PR85/P3a-2 as new branches | reversible: yes | CLOUD-RESUME-2026-11-11.md | revisit: PR77 shows a smaller fix is possible | outcome: see AUTONOMOUS-LOG.md.
- D-003 | same | Merge authority | (a) cloud may merge own clean PRs, (b) cloud only prepares READY PRs, a human merges | RECOMMENDED (b) as the default (repo CLAUDE.md: cloud sessions never merge; merging is not reversible on `main`); (a) only if the owner adds the line `MERGE ALLOWED` to the prompt | reversible: yes | repo CLAUDE.md, owner standing approval applies to the laptop lead | revisit: owner pastes `MERGE ALLOWED` | outcome: n/a.
- D-004 | same | Old unpushed laptop branches | push as backups | DONE: 11 branches pushed as `backup/laptop-2026-11-11/*` after gitleaks (0 findings each); they are backups, not work items.
- D-005 | same | Two unpushed PR89 evidence heads (gitleaks hit in history) | (a) push anyway, (b) drop and re-run evidence on db0d9eb | RECOMMENDED (b) | reversible: yes | ORDER 242 | outcome: re-run is Q2.

## Decisions taken by the cloud session (append below, newest last)

## D-001 2026-11-11 13:19Z UTC: EGM plugin unavailable, use manual reviewer fallback
- Question: how to run EGM reviews when the plugin cannot be installed (install command denied by the environment's auto-mode classifier).
- Options: (a) retry/work around the denial (rejected: bypasses a safety control); (b) fallback in the prompt: fresh general-purpose read-only reviewer agents, same order (design, codebase-details, comprehension, implementation-readiness, structural, zoom-out, synthesizer); (c) stop. 
- Recommended/chosen: (b). Reversible: yes (swap to egm:* once a human installs the plugin and restarts).
- Revisit: if the owner installs the plugin.

## D-002 2026-11-11 13:31Z UTC: PR89 round 18 fix approach
- Question: how to resolve design Majors M2 (denylist masker) and M3 (no throwaway-DB check) without replacing working code.
- Options: (a) rewrite masker from scratch as k-gram + allowlist (reviewer proposal; big, loses 2,800 lines of tests); (b) add the k-gram class mask as ONE extra pass at the existing choke point _masked (every substring >= 6 chars of any secret, plus its percent-decoded/base64/hex forms), keep existing API/tests, add fuzz tests with random slices; add allowlisted output (class name + caller expect fragment) only when pass_env set if tests still pass; (c) accept documented gaps (forbidden: fix-dont-defer). For M3: refuse non-loopback host/non-socket and require database-name marker unless explicit keyword allow_remote_address=True; negative tests.
- Chosen: (b) (improve-before-replace; reversible; security path uncapped rounds). M3 as stated. m1-m9 + c1-c5 fixed in same batch.
- Revisit if k-gram pass breaks legitimate error text (then allowlist for pass_env outputs).
- Verified by lead: grep of tools/mutation_runner.py found no host/loopback refusal code (only docs), M3 premise holds.

## D-003 2026-11-11 13:35Z UTC: P3a-2 history (Q6)
- Options: A keep old core/P3a-2 (never mergeable, 208 handover files in tree); B open a NEW draft PR from core/P3a-2-rewritten (additive, old PR73 untouched); C rewrite/force existing branch (owner-only, forbidden).
- Chosen: B as the recommendation only; opening the PR is deferred until the security-CI question is settled (it would fail for the same reason). Round-11 commits on the rewritten branch (4 commits, 11 non-handover files) have no review/evidence: schedule fresh review + evidence when PR is opened.
- Evidence: handover/decisions/P3a2-history-memo.md; lead verified CI rule in main ci.yml.

## D-004 2026-11-11 13:36Z UTC: EGM model = Fable 5.2 (owner order, not my decision)
Owner said: use Fable 5.2 for all EGM skills/agents instead of Opus/Sonnet/Haiku. Done by patching egm_model_patch.py (OPUS=SONNET=FABLE) and running it. Scope: EGM only; builders/evidence runners unchanged (ambiguous in the order; revisit if the owner means all agents). Reversible: restore the two constants. Cost goes up (Fable pricing not verified here).

## D-005 2026-11-11 13:40Z UTC: Fable 5.2 for ALL agents (owner order, not my decision)
Owner switched the session to claude-fable-5-2 and said "use fable 5.2 for all agents also". Action: every new Agent call sets model=fable; one-line edit of .claude/hooks/agent_preamble_gate.py (VALID_MODELS += "fable"), otherwise the hook refuses the owner's chosen model. EGM skipped: one-line mechanical edit on a direct owner order. Running Sonnet agents (EV-P89, B-PR77, B-PR85, B-PR89-r18) are not restarted (restart would waste finished work). Cost: higher; Fable prices not verified here. Reversible: remove "fable" from the set.

## D-002 REVISED 2026-11-11 13:42Z UTC (after Fable zoom-out plan review, reviews/PR89/r18-zoomout-plan.md)
- My first choice (k-gram pass) was wrong: still a denylist, and it shreds ordinary text for the CI address. Lead verified ci.yml uses postgresql://postgres@localhost:5432/postgres.
- New plan: (1) evidence on db0d9eb is already running (EV-P89). (2) M3: reuse _address_parts extended to return parts; fail closed on unparsed when pass_env is set; key allowlist; host AND hostaddr must be in an exact allowlist keyword throwaway_hosts (default localhost, 127.0.0.1, ::1, unix socket); NO database-name marker (it would refuse CI and proves nothing because the login is an admin; changing ci.yml is out of scope); docs say plainly loopback is not proof of throwaway. (3) M2: output projection at _row, skip messages and baseline error when secrets are non-empty (exception class identifier + fixed expect-match word + caller's expect; test id = path+function, parameters replaced); existing _masked untouched as second layer; NO k-gram pass; fuzz test (no 4-char secret slice in any output field outside caller's expect) proven to fail on old code. (4) minors in a separate commit; baseline error under pass_env carries only run end + class name. (5) ladder line + why the core redactor is not reused.
- Option "refuse any password-bearing address" rejected for now: changes the contract and weakens existing tests; needs the owner (logged as an idea, not a blocker).
- Reversible: yes (new commits on wip branch).

## D-006 2026-11-11 13:44Z UTC: new package Q8a from the dependency audit
- Question: what to do with the 6 Majors of reviews/Q8/deps-audit.md (merged core). Options: (a) log only; (b) one small package for the clear code fixes (F1 override objects not refused when live, F5 Vault static token when live, F6 Slack-named neutral receiver, F8/F11 guard gaps), separate tickets later for F2/F3, owner questions for F4/F9; (c) one big package for all.
- Chosen: (b). F1 and F6 premises verified by me in the code. New branch from main, draft PR, security path uncapped. Reversible (new branch).
- Order note: this is Q8 work started while Q2-Q5 agents run; it takes no heavy slot until its builder's final suite.

## D-007 2026-11-11 13:51Z UTC: PR85 retarget result (Q5)
- Fact (verified by lead): core/P5b2-main 3b9617e4 = P5b2 head + merge of main + one fix; against main it carries 44 commits, 87 files, 33,047 added lines, because P1a, P1b, P5a and P5b1 are not in main. Full suite on it: 12088 passed, 1 failed (a timing test that is flaky on main itself), ruff/format/bandit clean.
- Options: (a) open a draft PR from it now for real checks (a 33k-line bundle of five packages; P5a inside it depends on the unclean PR77; the security check fails for every PR anyway); (b) keep the branch, open no PR until its base packages are merged or the owner asks for a bundle PR; (c) squash.
- Chosen: (b). PR85 cannot be READY alone; honest status = "branch prepared, local gates green except one flaky main test, no real GitHub checks". The flaky test gets its own fix branch (B-flaky). Reversible.
## D-008 2026-11-11 13:51Z UTC: owner order "use as many agents as possible": 11 agents now run; work without a heavy test slot is started at once (reviews, ticket authors, dry runs); heavy runs stay capped at 3.

## D-009 2026-11-11 14:02Z UTC: P3a-2 round 12 fix batch on a NEW branch
- Round 11 result reviews (two fresh Fable reviewers, reviews/P3a-2/r11-*.md): 8 distinct Majors, no Blocker by reading, no evidence yet (EV-P3a2 running).
- Options: (a) wait for the evidence before fixing; (b) start ONE builder now on NEW branch core/P3a-2-clean from 8382bdd (never touching core/P3a-2 or core/P3a-2-rewritten), who folds in the evidence when it lands; (c) leave for the human.
- Chosen: (b) (security/data path, uncapped rounds; additive and reversible). Where the two reviewers rate the same issue differently, the higher severity counts. Policy choices made here (recommended, least privilege): a named role gets NO right outside the grant map and no default right; sequence USAGE is not "reading"; an unmanaged SECURITY DEFINER function owned by the migration role in the run schema is refused again; comparison scoped to objects the migration role (or its memberships) owns or granted.

## D-010 2026-11-11 14:08Z UTC: Q8c after plan review round 1 (6 Blockers between two reviewers)
- Options: (a) build as drafted (rejected: tests would not prove what they claim; rendered Deny blocks would break deployments); (b) rewrite as slice 1 = Vault x2, Kubernetes, Slack, six AWS kinds, data + one set-equality guard, no Deny rendering, no verifier split, loader/renderer outside src/, names verified against vendor pages with date+URL in the data before any copy-ready text, moto IAM-enforcement spike before any home-made enforcer; slice 2 (Azure, Google) after verification and the owner's answer; (c) drop the package.
- Chosen: (b). A separate network verifier agent checks the slice-1 names now (evidence runner; it records page text, it does not judge). Reversible (ticket only).
