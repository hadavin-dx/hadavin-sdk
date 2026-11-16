Status: resolved (applied as P1d rev 10, P1d-learn rev 3, P1d-gate rev 3; not committed)

# P1d family, plan review round 9: resolve (Elephant, headless)

**Inputs:** `round9-design.md` (1 Blocker, 6 Major, 6 Nit), `round9-readiness.md` (1 Blocker, 9 Major, minors). **Targets:** `handover/tickets/P1d.md` rev 9, `P1d-learn.md` rev 2, `P1d-gate.md` rev 2. **Path class:** redaction; no round cap. **Skill:** `egm:egm-resolve` invoked through the Skill tool; run headless on the brief's order, so the interactive gate (step 4) was replaced by the brief's "apply" instruction. **Binding:** ORDER 165-168 (no P1e; document cap config with source "unmeasured placeholder"; BS-2 fail = HELD; markers P1D_APPLIED / P2D2_APPLIED / P1DB_APPLIED; rows 005/006/009/010 under their own topics), ORDER 177, 180.

## Code read for this resolve (`core/cloud-handover` at `fccb5bb`, 2026-11-09)
- D10-1 `redact._place` (`redact.py:958-971`) adds a placeholder for each secret-shaped piece of a secret-kind value: confirmed (design M6).
- D10-2 `URLCRED` (`redact.py:226-229`) captures only the password (group 1); the host is a lookahead `@(?=[a-z0-9.\-]+...)`, not part of the value. `HOSTNAME` (`redact.py:386-393`) matches only private suffixes (`internal`, `local`, `corp`, `lan`, `intranet`, `intra`, `localdomain`, `home.arpa`), never `example.org`. `EMAIL` (`redact.py:234-239`) includes the domain in the value.
- D10-3 `ToolSpec.side_effect: Literal["none"]` (`tools.py:76`): every model tool is declared side-effect free; writes go only through the approval and the executor.
- D10-4 `tests/test_s6_approvals.py::_request` (lines 60-65) calls `appr.request` without `store.save_plan`; production saves the plan first (`agent_loop.py:667`). `tests/test_k5_fixes2.py:96-116`: a 261,000-byte document asserted under `max_document_bytes`, and `max_document_bytes = MAX_REDACT_CHARS` asserted valid. `tests/test_review_pr3_round2.py:71-78` (`test_tampered_stored_plan_refused`) overwrites the stored plan and expects `plan_changed` after approve: a sibling the reviewers did not name.
- D10-5 `hypothesis` is not in `pyproject.toml` or any test. Pytest markers are registered in `pyproject.toml:87-90`; there is no `--strict-markers` and no warning-as-error filter.
- D10-6 `cards.py:14` imports `requests.WARNING`, so a module-level `requests -> cards` import is a cycle. `SlackChannel.notify` (`slack_channel.py:194-198`) calls `clean(text)`. `FakeChannel.update` records `(approval_id, req.status)` (`channel.py:107-108`); `FakeChannel.send` records `clean(req.summary)` (`channel.py:103-104`).
- D10-7 `Approvals.sweep` (`requests.py:190-215`) sets `sent_at=None` and calls `_send` on each escalation; `decide` order is not_pending, old_step, step_expired, approver, requester, plan_hash (`requests.py:146-163`).
- D10-8 `_Redactor.__init__` copies the map at `redact.py:897` (ticket said 896); the document-complexity check is `agent_loop.py:382` (ticket said 383); cache reuse `redact.py:916-918` (correct). `_PLACEHOLDER` (`redact.py:817`) and its split use (`redact.py:1029`) exist.
- D10-9 `register_value` and a strict mode do not exist on this branch (they are P1b's, UNVERIFIED until BS-0 (a)).
- D10-10 P1d's mutant table has 49 rows = 52 mutants (M20a-d is four); the status line's "55" was wrong.

## Findings, merged groups, severity order

### G1. Blocker (design B1): the containment filter lets a planted known value switch learning off. PROPOSE FIX (with one sub-point CONTESTED)
- Valid. A candidate that contains a known value is dropped whatever else it contains; the attacker plants the known value in the same text (`password=` + PV, then the unknown key glued to a copy of PV).
- **Contested sub-points (evidence D10-2):** (a) "URLCRED with a known host": URLCRED's value is the password only; the host is a lookahead, so the filter never saw the host and this case already worked. (b) "WEBHOOK with a known host": WEBHOOK hosts are fixed vendor domains, which HOSTNAME never matches. (c) "H28a is not learned today if `example.org` is masked as a known host": HOSTNAME matches only private suffixes, so `example.org` is never masked and H28a's expectation stands. The same attack is real for an e-mail address under a private host (`anna.m**@build-01.corp**`), which gets a row.
- **One fix, at the choke point (P1d-learn rev 3):** delete the containment filter. Run the learning patterns on **blanked learning views**: in each learning view v, every occurrence of the view's own form of a known-before value (`form_v(k)` = the same steps that made v, applied to k) whose kind is an every-copy kind or `EMAIL` is replaced by one space before the patterns run (one trie regex per view, built with P1d's finder code). A candidate then never contains a known value, so the glued tails of GLUE-UP and GLUE-EMAIL are gone, and an unknown key next to a planted value is found on its own. Known HOSTNAME and other standalone values are NOT blanked: URLCRED's lookahead and EMAIL's domain need the host characters, and no learning kind glues onto a host alone. This is the reviewer's option 2 ("`r` with known spans blanked"), applied per view; option 1 (views of the dropped form) was rejected because `neutralise` has already turned escapes into spaces there (RS-1), which loses H11, H12, H14.
- **Stated limit (new P1d-learn N9):** an unknown value with a known value INSIDE it is cut in two by the blank; each part is checked alone. Planting a value inside a secret needs knowledge of that part of the secret.
- **Rows (P1d-learn):** B1-AKIA = `"password=" + PV + " key AKIA**IOSFODNN7EXAMPLE**" + PV` (PV = `"Zz9Yy8" + "Xx7W"`), learned `AKIAIOSFODNN7EXAMPLE`; B1-SECRET = `"password=" + PV + " then secret=Qm8v**Rt2xLp5n**" + PV`, learned `Qm8vRt2xLp5n`; B1-EMAIL = `"mail anna.m**@build-01.corp**"` (pass one masks the host, 13 characters), learned; B1-URLCRED = `"https://svc:Pa**ss1234**@build-01.corp/x"`, learned (pins that the host stays readable to the pattern). GLUE-UP, GLUE-EMAIL, MD-EMAIL stay guard rows. ACC-EMAIL: hand trace not reproducible from the EMAIL pattern (`é` directly before `@` leaves no local part); BS-0 runs it; if learned it is an ow row (part of the address is shown), not a false learn.
- **Mutants:** M68 = blanking removed (killers GLUE-UP, GLUE-EMAIL); M68b = the rev-2 containment filter restored (killers B1-AKIA, B1-SECRET, B1-EMAIL); M68c = HOSTNAME added to the blanked kinds (killer B1-URLCRED, B1-EMAIL).

### G2. Blocker (readiness B1): row H25 cannot be withheld by P1d. PROPOSE FIX
- Valid: SV_A has 5 characters, under `min_key_chars`, so nothing is known.
- **Decision: move H25 to P1d-learn as L-H25** (learning view b1 of `r` deletes the escape and reads `password=` + SV; SV is not in the work map; learned). Its fail-before oracle is `leaks(out, SV_B)`, because the base shows SV_B, not SV. P1d drops H25 (not replaced: H11-kv to H14-kv cover escapes). M4's killer becomes H29b on the model entry (no `clean` joined pass, so only b1 deletes the tag) and H15c-kv (overstrike).

### G3. Major (readiness M2): `_withhold` raises inside the `try`, so the catch-all catches it. PROPOSE FIX
- Valid. Rewritten: the `try` computes an outcome (`shown` or `_Held(reason, work, exc)`); `_withhold` is called once, after the `try`. In raise mode, `size` from `max_work` (no exception object) raises `InputTooLarge("work bound")`. New mutant M77 (`_withhold` called inside the `try`), killer `test_raise_mode_logs_once` (X02b in raise mode: one log line, `InputTooLarge`, not `RedactionError`).

### G4. Major (readiness M3, plus one sibling found here): existing tests break and were not listed. PROPOSE FIX
- `test_s6_approvals.py::_request`: add `appr.store.save_plan(plan)` before `appr.request` (production order, `agent_loop.py:667`). Not a weakening: without a stored plan `_card_check` fails closed.
- `test_k5_fixes2.py::test_a_document_whose_views_are_over_the_cap_is_document_too_large` and `::test_max_document_bytes_cannot_exceed_what_the_redactor_takes`: their configs also set `evidence.redaction.max_text_chars = MAX_REDACT_CHARS`; both keep their assertions.
- **Sibling (D10-4):** `test_review_pr3_round2.py::test_tampered_stored_plan_refused` would get `card_withheld` instead of `plan_changed`. **Decision:** `_card_check` returns True on a plan-hash mismatch (logged), because the existing `plan_changed` re-check refuses that run before any call; the check judges only the plan that can run. The test stays unchanged and becomes the killer of new mutant M78. `test_decide_refuses_when_stored_plan_differs` is deleted from the plan (it pinned the old choice).

### G5. Major (readiness M4, design M2 harness part): fail-before harness undefined. PROPOSE FIX
- `tests/p1d_api.py` (new, plain module, imported by all P1d-family test files): `api("runmap.WITHHELD_NOTICE")` returns the attribute or an `_Absent` sentinel whose use raises `AssertionError("NEW_SURFACE: <name>")`; `call(fn, *a, **kw)` turns a `TypeError` for an unknown keyword into the same prefix. `leaks(out, secret)` = `textnorm.scan_holds(text=out, value=secret)` (exact fallback for short keys); a failing leak assertion starts with `LEAK:`.
- Marker `p1d(cls)` registered in `pyproject.toml` `markers` (`pyproject.toml:87`); on the base it is unregistered, which is only a warning there (D10-5).
- `tools/p1d_fail_before.py --base <sha> --files <test files>` (not a pytest test: it needs a worktree and two Pythons): runs the files in a worktree of the base on 3.12 and 3.13 with `--junitxml`, reads each failure message's prefix, exits 0 only if errors are 0, every `fb` row failed with `LEAK:` or `NEW_SURFACE:`, every `pb` row passed; raw output to the package's `fail-before.txt`, base SHA on line 1. Used by P1d, P1d-learn and P1d-gate.

### G6. Major (readiness M5): `hypothesis` is not a dependency. PROPOSE FIX
- Decision: 0 new dependency. Every "property" test is a plain seeded loop (`random.Random(1)`, 500 cases, plus every row); the word "Hypothesis" is removed.

### G7. Major (readiness M6): wrong or undecided row classes. PROPOSE FIX
- MP-4 and F20 are `fb` (the base sweep is case-sensitive, V5). New class **`inv`** = asserted after the package (no leak, stated output), base outcome recorded in `fail-before.txt` but not gated: H17k, H29a, PB-ENC, JOINED-PH. No "pb?" remains.

### G8. Major (readiness M7): rows not self-contained. PROPOSE FIX
- A twin table spells C01-kv to C10-kv and H12a-kv to H12d-kv. H21-kv follows the KV twin rule (Cyrillic U+0445 for SV_B's `x`), not U+0422. F02, F02b, F14, F19 get literals. LK-UNFOLD's reason is pinned at BS-0 (l) like other pinned outputs. S1-S5 get their call forms.

### G9. Major (readiness M8): no row kills the standalone leg. PROPOSE FIX
- Row SA-1 (model): `RunMap({"<NAME_1>": "José Müller"})`, text `Jo**sé Mü**ller agreed` → notice (view c folds, view d joins; a NAME is standalone, so only `standalone_hit` sees it). Mutant M76 (`standalone_hit` branch removed), killer SA-1.

### G10. Major (readiness M9): folded sweep split and overlap rule unspecified. PROPOSE FIX
- The pass runs after the existing exact loop, on a fresh `_PLACEHOLDER.split` of the text that loop produced (`redact.py:817`, used at `:1029`); offsets are positions in each free segment; spans never cross a segment, so they cannot overlap a written placeholder; replacements per segment right to left; segments rejoined in order.

### G11. Major (readiness M10, design Nits N1, N2): caller-table gaps. PROPOSE FIX
- `SlackChannel.notify` row: catches `LookalikeCopy`, posts `card_withheld_text()`.
- `send_card`/`update_card` import `cards.withheld_card` inside the function (cycle D10-6); `test_requests_imports_alone` in a fresh interpreter.
- `card_withheld_text(inputs=...)` deleted (no caller).
- `FakeChannel.update`: tuple `(approval_id, status)` unchanged; a withheld update also appends the approval id to a new list `withheld_updates`.
- Sweep escalation: one withheld post per approval step (each step's approvers are told why); pinned by `test_withheld_row_one_post_per_step`.
- N1: `request_approval`'s log line gains `posted=true|false`. N2: the adapter checks only for a parameter named `withheld` (a `**kwargs` forwarder no longer counts); `test_forwarding_channel_without_withheld`; mutant M79.

### G12. Major (design M1): token, card and IBAN kinds not named as not learned. PROPOSE FIX
- P1d-learn N8 + CHANGELOG sentence; known copies of those kinds stay covered by P1d. Measure rows L-HE, L-CC, L-IBAN.

### G13. Major (design M3): a withheld tool result hides a side effect's outcome. CONTEST
- Evidence the reviewer could read: `ToolSpec.side_effect: Literal["none"]` (`tools.py:76`). A model tool cannot have a side effect; payments, sends and ticket actions run only through the approval and the executor, whose result is not a model tool result. One sentence is added to RK4 for a human reader.

### G14. Major (design M4): cost grows with the run map. PROPOSE FIX
- BS-4 row "call N": a run map of 2,000 values grown one value per call, 30,000 characters, finder and folded-finder rebuild time apart, number of `scripted` values reported; gate: p95 including the rebuild under `REDACT_BUDGET_S / 4`; STOP to the lead otherwise, with the named fallback A20 (an append-only second finder for values added since the last full build). Operator signal stated: each withheld text writes one line with `reason=size known=<n>`, so a run that degrades shows a rising `known` count and repeated `reason=size` lines. The 1.5 s target at 30,000 characters is still unshown (BS-0 (p) STOP rule, unchanged).

### G15. Major (design M5): canaries pass on any withhold. PROPOSE FIX
- `runmap.last_withhold()` returns the thread-local `(reason, source)` of the last `_withhold`; each canary passes only on `reason == "residue"` (C-CARD: `LookalikeCopy`, which only `residue` raises). Test `test_canary_fails_on_error_withhold` patches `_finish` to raise. Per-view coverage stays with P1d's build tests; written in the "why not merged" column.

### G16. Major (design M6): the flood limit counts pieces. PROPOSE FIX
- `max_learned_per_call` counts candidates passed to `add_known` (values), not the pieces `_place` adds. Row FLOOD-PIECE (one SECRET value with three secret-shaped pieces, split by `**`): withheld, 1 counted. A committed piece masks later copies for the whole run; BS-2 counts every new map entry, pieces included, as a learn, so a false piece is a false learn (HELD).

### G17. Nits and minors. PROPOSE FIX unless marked
- d-N3 window between merges: stated in P1d's status. d-N4 unjoined model-path pieces: P1d Non-Goal N8. d-N5: row AGG-1. d-N6: the document-and-arguments test asserts both behaviours; the eval message quoting the cap number: DECLINE (a constant, no content).
- Readiness minors: line refs fixed (D10-8); mutant count fixed (D10-10); M26 split into M26a/M26b; M60's row sets `max_work` exactly to the product; M6 and M16 marked conditional; BS-0 letters (g), (i), (j) explained as removed; "BS-2 is P1d-learn's" stated; P1b names marked as `2034512` names; finder cache form named; `_views.py` keeps only `TAG` and `ANSI`; clean step 2 snapshot `keys_before` defined.
- P1d-learn minors: `test_marker_means_rule_runs` defined; **M54 deleted with the `_learn` flag** (new: learning also runs in `card_text`, so a summary stored between the P1d and P1d-learn merges is checked when it is shown; `test_card_text_accepts_every_clean_output` is the evidence that this never raises on `clean`'s output); FLOOD keys spelled; H37 prefix `ghp_`.
- P1d-gate minors: placement after `app.py:93-97`; spy target `app.make`; `pilot_cfg(tmp_path)` needs no extra config (defaults); C-LEARN uses K, whose last 16 characters hold one digit from 2-7, so `_learn_aws` cannot learn it and C-LEARN isolates the pattern pass (stated).

## Counts
PROPOSE FIX 16 groups (2 Blockers, 13 Majors, the Nit batch); CONTEST 1 group (G13) plus 3 sub-points of G1; ESCALATE 0; DECLINE 1 sub-point (G17 d-N6 message).

## NEEDS LEAD
1. G1: blanked learning views replace the containment filter (one fix); stated limit N9 (unknown value with a known value inside). Confirm.
2. G2: H25 moved to P1d-learn (L-H25). Confirm.
3. G4: `_card_check` returns True on a stored-plan hash mismatch so `plan_changed` stays the refusal (keeps `test_tampered_stored_plan_refused` unchanged). Confirm.
4. G17: the `_learn` flag deleted; learning runs in `card_text` too. Confirm.
5. Still open from rev 9: H28a-b in P1d-learn (ORDER 180 (1) said "stay in P1d", (2) moves every learning pass to P1d-learn); merge order P1d-learn before P1d-gate (DEFAULT 4).
