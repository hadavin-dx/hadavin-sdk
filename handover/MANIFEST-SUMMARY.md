# Handover manifest summary (collected 2026-11-05, NOT reviewed, NOT for merge as is)

Verbatim copies from named commits (git show of the blob, not the working tree), no rewriting. Full list: handover/MANIFEST.csv (sha256 per file).
EGM skipped: mechanical verbatim copy; the lead runs EGM on the plan and a cloud session does the real promotion with EGM.

Total: 3036 files, 13.7 MB, plus 5 skipped rows. Core base: origin/main ce70eb5.

## Counts per source (files, MB, skipped rows, commit)
- intake-wp3: 408 files, 0.48 MB, 1 skipped, commit 179681efa
- intake-6b: 420 files, 0.72 MB, 0 skipped, commit 870f61c37
- intake-6d: 435 files, 1.14 MB, 0 skipped, commit 8bcadfc4b
- intake-a12: 494 files, 1.54 MB, 0 skipped, commit b6592b9ac
- intake-p2: 426 files, 0.72 MB, 1 skipped, commit 57e7a50e4
- intake-main: 15 files, 0.14 MB, 0 skipped, commit aada5aa20
- apexc: 38 files, 0.65 MB, 0 skipped, commit 3d78bc7be
- dealdesk: 53 files, 0.42 MB, 1 skipped, commit 141046f6f
- refunds: 47 files, 0.54 MB, 1 skipped, commit 1e6e6b9aa
- portal-kit: 65 files, 0.64 MB, 0 skipped, commit 87b4cd18f
- jagrat: 30 files, 0.21 MB, 0 skipped, commit 862e4245b
- warden: 525 files, 5.94 MB, 1 skipped, commit c78d77091
- killswitch: 66 files, 0.28 MB, 0 skipped, commit 40420cb5a
- studio-notes: 14 files, 0.25 MB, 0 skipped, commit (working 

Intake lanes: wp3 = invoice/payment checks; 6b = inbox scan, reader, lockfile, safe_text, mutate_src; 6d = service, access, routes, ui, sink_guard, csvsink; a12 = cost controls (budget, model*, settings), workqueue, secret_store, core_copy/* pins, older mask; p2 = newest mask.py, phrases, trace_vocab, tracelog; main = old stage 1 (rules, executor, egress, isolation) and pin files.
Most Intake test files repeat per lane (each lane has its own tests/ and the same synthetic d10 text fixtures). They are kept verbatim so each lane's tests can be diffed against its own source.

## Variants side by side (sha256 prefix, bytes) so the cloud can diff them
- textnorm.py: intake-a12 31220ff0f6 (9214); apexc 1a0574b4c1 (9903); dealdesk core_copy 1f1c482fed (9916) and wrapper 2c1527bff7 (2340); refunds core_copy 88f432215c (9915) and wrapper f60119e2c3 (7704); portal-kit 751a2dc793 (1494, deliberately different fold). The PR49 and PR50 variants live in core branches, not here.
- _confusables.py: intake-a12, apexc, dealdesk, refunds identical (41740c1173).
- redact.py: only intake-a12 core_copy (63d8a9f789, 58938 bytes). mask.py: intake-a12 317388f248 (35790) vs intake-p2 f7733a97fb (66459, newest).
- workqueue.py: intake-a12 9f07509109 vs intake-p2 d0a417747c (small difference).
- inbox.py: intake-6b 4fafa460b0 (48270, real scan) vs intake-6d 706de8ad69 (15608, interface) vs dealdesk c75058c71e (13960); apexc intake.py is the third ledger.
- lockfile.py: intake-6b 62134eadc2 vs intake-6d 4942ee75a8. strict_json.py: intake-a12 and portal-kit identical (983c26f73c).
- egress_text.py: apexc 29aeb5f08f vs dealdesk ae594a9aa4. Intake egress.py (third variant) in intake-a12 and intake-main.
- mutation runners: intake mutate_src.py 6b fc00a48827 (88080) vs 6d 67a98769bb (132547); apexc mutation_check 83859a7afb, dealdesk 30ce4a6284, refunds 2b8096eb89; portal-kit tools/mutation.py.
- freeze: dealdesk freeze.py (config freeze, other job) 9d23dd83ff; jagrat freeze.py (change windows) 0cb4193a62; warden freeze.py 753cb78386; portal-kit tools/freeze.py is something else.
- Jagrat vs Warden pairs: grounding (38a3413325 vs 6ea04aa91a), environments, landed, quarantine, confidence, trust, paths, expected, symptom, freeze, labels vs handback. Warden is the fuller original; Jagrat the trimmed copy.
- Money, signers, canonical JSON: refunds hashing.py, signers.py, money.py; dealdesk canon.py, signing.py; apexc normalise.py (negative amounts differ).

## Licences and provenance
- Warden: LICENSE and NOTICE copied (Apache-2.0, owner-authored); file headers kept as in source. agent-killswitch: LICENSE copied (Apache-2.0; its copyright line carries the old studio name, left as is).
- Jagrat: there is no LICENSE file in that repo (owner decision: all rights reserved, reuse for clients ok), so none was copied. The core licence was not checked by me (D-licence still open).
- Demo repos apexc, dealdesk, refunds: LICENSE copied. portal-kit: LICENSE copied.

## Studio notes (handover/studio-notes/, 14 files)
- inventory*.md, s0-merge-probe, plan-v1, review-plan-1, review-brainstorm-1, c18a design-v3 and amendments, WORK-PACKAGES, C1-ticket-v3 and amendments. One scrub: inventory-C.md had 3 banned vendor strings, replaced in the COPY by [vendor-inspired name removed] (original untouched). No old studio name and no personal e-mail in the notes.

## Not copied or not verified (read this)
- Core open-PR branches (#41-#50, C1a, C18a) are in the core repo / GitHub, not collected here. The demos' core_copy files are included only as the demos hold them.
- Skipped rows: warden tests/fixtures/bench (33 files, over the 2 MB fixture budget); tests/fixtures/payment_scan_exclude.txt in two lanes (not referenced by copied tests); tools/check_core_copies.py does not exist in dealdesk and refunds. No file was over 1 MB.
- Test selection is automatic: a test is copied if it names a copied module, plus shared helpers (conftest and similar). It may include unrelated tests and may miss a test that reaches a module only indirectly. No test was run and nothing was imported.
- Intake 6d service.py, ui.py, access.py mix Intake wiring with generic primitives; the inventory says promote only the primitives. review_page.py, pipeline.py, exporter.py, adapters and the rule data were NOT copied.
- Jagrat/Warden: incident-specific code (workflows, activities, aws_*, records) not copied; only the capability modules named in inventory-C and their tests.
- Fake-looking data kept verbatim because tests depend on it: 12-digit placeholders (123456789012, 111122223333 and similar) in tests, and the synthetic address a.b@gmail.com in refunds test_logic.py. The secret scan found no real credential.
- warden redaction.py and its tests contain secret-pattern text (xoxb-, password=) as detector rules and test inputs built from parts; not real secrets.
- Portal kit console UI assets were copied (whole kit 0.64 MB, far below 5 MB).
- Slip: my first worktree add used a relative path and landed inside projects/hadavin-sdk/_local; I moved it with git worktree move to _local/scratch/wt/handover (git worktree list confirms).
