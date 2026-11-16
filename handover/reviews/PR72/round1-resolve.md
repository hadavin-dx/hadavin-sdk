# PR 72 (P6a-1, head d15e53a) round 1: resolve (egm:egm-resolve, headless)

Status: resolved (categorised; no fix applied: this resolver edits no ticket and no source).
Target: `handover/tickets/P6a.md` (full file, 477 lines; build notes BN-1 to BN-15 and "Build note S6-pilot-prod" win over revision 3 text).
Findings in: `reviews/PR72/round1-design.md` (design: M1, M2, N3-N6), `reviews/PR72/round1-codebase.md` (codebase-details: M1-M3, 3 nits). 14 findings, merged into 10 groups.
Path class: the S6 check stops case text going to an outside service from a demo config (data-leak path) and S2 guards pilot/prod builds (security path): NO round cap. Round number of this resolve: 1.

## What I checked and what I did not
- Read: both review files; the ticket's mutant plan, BN-1 to BN-15 and S6-pilot-prod note; snapshot `/home/user/build/snap/P6a-d15e53a` (`config.py:325-440`, `app.py:100-125`, `backends/table.py:540-606`, `tests/test_client_profile.py:185-240`, `:443-479`, CHANGELOG lines 7-8); evidence `handover/evidence/P6a/d15e53a-cloud2/TABLE.md`, `handover/evidence/P6a/recon-2026-11-09/run1.txt` and `CHECKPOINT.md`, `handover/evidence/dblink-rerun-2026-11-09/PR72-312.txt`, `PR72-313.txt`; `LEAD-ORDERS.md` orders 150, 166, 172.
- Not run: no test, no mutant, no build. Not read: the five switch tests, P6a-2 code (not in this PR), the whole CHANGELOG.
- Fact the reviewers did not have: AFTER the reviews, a reconstruction run (`recon-2026-11-09/run1.txt`, started 03:55Z) ran 62 P6a-1 mutants at d15e53a: baseline 92 passed; 62 planted, 62 KILLED (45 with the killer the ticket or builder named, 17 "[invented]" by the reconstruction because the builder's own 17 were lost; ORDER 166 confirms "45 original + 17 new"); final `git status` clean, rc=0. The runner itself is only at `/home/user/build/recon/p6a1/p6a1_mutants_by_hand.py` (not in the repo, not in handover).
- dblink: `dblink-rerun-2026-11-09/PR72-312.txt` and `PR72-313.txt` show `1 passed` at d15e53a on a cluster with the default socket. The full-suite failure in TABLE.md was the environment.

## Groups, by severity

### G72-1 [Major] Mutant evidence at this head (design M1, codebase M1, mutant part of codebase M2) - PROPOSE FIX
- Verified: TABLE.md:6 and :27 say "NOT RUN: P6a-1 mutants (62)". The reviewers were right when they wrote. Now partly closed by `recon-2026-11-09/run1.txt` (62/62 killed at d15e53a). This covers the new refusal branches the design review named: mutants 47-50, 54, 55, 70, 72 hit `is_live`, `allow_test_doubles is not True`, the pilot/prod `made_up_data_only` refusal and StrictBool (`config.py:404-411`, `app.py:113-115`).
- Still open: (a) the runner is not in the repo, so nobody can re-run it and the reviewer cannot read the mutant text; (b) 17 of the 62 are new mutants, not the builder's originals, which are lost (never quote "62/62 original", ORDER 166); (c) the builder numbered its mutants 47-55, but ticket BN-5 already uses **mutant 47** for P6a-2 (the `operator` resolver). Two mutants have one id.
- Fix:
  1. **Builder (PR branch core/P6a):** commit the runner as `tests/p6a1_mutants.py`, following the committed pattern of `tests/stage_mutants.py`. Each mutant's hunk text goes in the file. Number the build-time mutants so they do not collide with BN-5: keep 1-35 and 46 as in the ticket, and renumber builder 47-55 plus the 17 new ones as `P6a1-B1` ... `P6a1-B26`, with an old-to-new id map in the file header. Add killers and mutants for G72-2 and G72-6 (below).
  2. **Evidence runner (a different agent):** on the final head, run `tests/p6a1_mutants.py` once, alone. Save the raw output to `handover/evidence/P6a/<head>/p6a1-mutants.txt` with `git status` before and after. A survivor is a Blocker.
- Class: "a mutant runner that lives outside the repo". PR 73 has the same class (G73-8). Fix both the same way.

### G72-2 [Major] S6 detector rule is a deny-list on one kind name (design M2; codebase nit "detector allow-list") - PROPOSE FIX
- Verified: `config.py:436` `out += ["detector: bedrock_guardrail" for d in b.detector if d.kind == "bedrock_guardrail"]`. A vendor kind name is hard-coded in core config, and a new vendor detector added to `TABLE["detector"]` loads in a demo config without `made_up_data_only`. T2b (`completeness_problems`) only forces a reason string in `CLIENT_REVIEWED`; it does not refuse. Llm and channel already use the allow-list form (`not in DEMO_ONLY`). Only the detector is a deny-list.
- Fix (**builder**): in `backends/table.py`, beside `DEMO_ONLY`, add `LOCAL_DETECTORS: frozenset = {("detector","regex"), ("detector","llm_judge")}` with a one-line reason each: regex sends nothing; llm_judge goes through the llm kind, which S6 already checks. `_sends_text_out` then refuses every detector whose pair is not in `LOCAL_DETECTORS`, and no kind literal stays in `config.py`. New rows: (a) a planted TABLE copy with a made-up detector kind `x_vendor` (with hosts) is refused in demo without the field and loads with it; (b) every `TABLE["detector"]` pair is either in `LOCAL_DETECTORS` or refused by S6 (a completeness check of the same shape as T2c). New mutant: "allow-list replaced by `kind == "bedrock_guardrail"`", killed by row (a).
- The codebase nit's words "REPO/tools" are unclear in the condensed report. Tool manifests with `hosts` are handled in G72-5.

### G72-3 [Major] Missing evidence: fail-before, recount, collect and wheel (codebase M2, non-mutant parts) - PROPOSE FIX
- Verified: the only fail-before is `evidence/P6a/4f01c6d/failbefore-3adacac.txt` (older head). Rows added since then have no fail-before on the base: t5q, t5r, t7e, t7f, t7h, t7i, and the S6-pilot-prod note. The P6a-1 file runs 65 tests (`p6a1-client-profile-313.txt`) and has 36 `def test_`, against the ticket's 43 rows. No recount exists, and no collect or wheel check.
- Fix (**evidence runner**, on the final head after the G72-1/2/6 fix batch): (1) fail-before: copy the new test file onto the true base (the parent of 3adacac, ORDER per q-entry F1) and record each row FAIL/PASS/ERROR; (2) a recount script: rows per letter, parametrised ids, against the ticket's numbers; (3) `pytest --collect-only -q` count; (4) `uv build` and list the wheel, showing no `tests/` or `demo_only/` content and the package files present. Raw output only, to `handover/evidence/P6a/<head>/`.

### G72-4 [Major] Ticket counts differ from the code (codebase M3) - PROPOSE FIX (ticket edit)
- Verified: the ticket says 43 rows and 35+1 mutants (`P6a.md:87`, `:361`, BN-1, BN-3). The code has 65 collected tests, 62 P6a-1 mutants and the mutant-47 collision (G72-1). The S6-pilot-prod note added rows that the counts do not include.
- Fix (**ticket edit** by the session that owns the handover branch, as ORDER 150 allows; not the builder): add build note `BN-16 (as built, PR 72)` with the real numbers from G72-3's recount script. It lists rows by letter, P6a-1 mutants 1-35 and 46 plus `P6a1-B1..B26` with their killers, says plainly that 17 of them are reconstructions, and confirms that BN-5 keeps id 47 for P6a-2. Frozen text stays. The build note wins.

### G72-5 [Nit] S6 covers only llm, detector and channel; `systems`, tool `hosts` and `sources` can still send text out (design N3) - NEEDS LEAD
- Verified: `_sends_text_out` reads only `b.llm`, `b.detector` and `b.channel`. The executor posts to `systems.<name>.base_url` over https (`config.py:398-401`).
- Why the lead decides: BN-1 and the ticket fix S6's scope at three capabilities. Widening it changes the product rule and the owner-visible limit (BN-13).
- Recommendation: widen S6 in this PR, with the same field and the same check. In demo without `made_up_data_only`, refuse a `systems` entry whose `base_url` is not loopback and a tool manifest with a non-empty `hosts`. `sources` is already refused in live (`app.py`), and in demo it reads, it does not send. Add one row and one mutant each. If the lead says no, the sentence goes into `owner-visible-limits.md` with a ledger row (owner, date), never only into the CHANGELOG.

### G72-6 [Nit] `given = dict(locals())` must stay the first statement; only a comment guards it (design N4) - PROPOSE FIX
- Verified: `app.py:108-109`. If a later edit puts a statement before it that rebinds a keyword, the check sees the rebound value. The mutants guard the check's position (16, 17) but not this line.
- Fix (**builder**): add one AST row: parse `app.build`, skip the docstring, and require that the first statement is exactly `given = dict(locals())`. Add a mutant that moves it one statement down, killed by the row. Building `given` from explicit names was rejected: it would lose T5 (l), which refuses a keyword added later by default.

### G72-7 [Nit] Stage literal repeated beside STAGES (design N5) - DECLINE
- `config.py:334` carries the comment "the same three as STAGES (a test pins it)". Pydantic needs a static `Literal`, and the pin test catches any drift. Fixing it adds nothing.

### G72-8 [Nit] Open evidence gaps listed in TABLE.md (design N6) - PROPOSE FIX (evidence runner)
- dblink: CLOSED, `dblink-rerun-2026-11-09/PR72-31{2,3}.txt` `1 passed` at d15e53a.
- Perf flake: the 3.13 rerun alone gave 28 passed (`perf-313-rerun.txt`). Re-run once on the final head, alone.
- **Evidence runner**, on the final head: ruff and bandit on 3.12 too. Vault rows: start a throwaway local Vault dev server (open source, made-up data, our own container, stopped afterwards) and set `HADAVIN_TEST_VAULT_ADDR`. If no container runtime exists in the session, say so with the exact command for the laptop runner. CI, CodeQL, SonarCloud and CodeRabbit run on push of the fix batch: record the run ids and conclusions.

### G72-9 [Nit] CHANGELOG wording on a self-hosted model (codebase nit) - PROPOSE FIX
- Code fact (`config.py:428-431`): the check is by kind, so a self-hosted `openai_compat` counts as sending text out.
- Fix (**builder**): the S6 CHANGELOG sentence states the same in plain words: "any model kind except the made-up one, including a model you host yourself (`openai_compat`)". UNVERIFIED by me: the exact current CHANGELOG sentence (I read lines 7-8 only).

### G72-10 [Nit] `model_copy` rows are defence in depth (codebase nit) - DECLINE
- The reviewer's own advice is "keep". No change.

## Counts
14 findings, 10 groups. PROPOSE FIX 7 (G72-1, -2, -3, -4, -6, -8, -9), NEEDS LEAD 1 (G72-5), DECLINE 2 (G72-7, -10), CONTEST 0.
Who: builder G72-1(1), -2, -6, -9; evidence runner G72-1(2), -3, -8; ticket edit G72-4.
Ledger: rows for G72-1 to G72-4 (Major) go into `handover/ledger.md` as OPEN, area P6a. The lead adds them; this resolver did not write the ledger.
Next round: the fix batch is one push, then a different evidence runner, then fresh round-2 egm-design and egm-codebase-details on a snapshot of the new head (no round cap: security and data-leak path).
