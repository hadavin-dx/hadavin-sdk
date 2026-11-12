# Cloud session resume note, 2026-11-11 (written under ORDER 241, STOP)

Written 10:45Z / 16:15 IST by the cloud session. Failures first.

## (0) What failed or is not done
- **PR77 (core/P2d-1, redaction) is NOT clean and not ready.** Round 6 found 6 Majors (5 reproduced), one bug class: hiding techniques that work alone are not combined (tab-run views, one ANSI mode per line, marks). The builder was replacing view enumeration by one gap-tolerant match. It stopped unfinished; only a WIP branch exists: `wip/P2d-1-w6` = b6f3b8dd0ab877aa3896db4f292094493c869ad7. Nothing in it is verified. No independent evidence or fresh review exists for any PR77 head after 249a0a59 (and 249a0a59 itself is voided by the open Majors). Open ledger rows: BL-core-a11a-w6-a01..a03, c01..c03, t01, t02 (Major), plus Minors a04, c04, t03, w5-c01, w5-c02, w5-m01.
- **PR74 (core/P5a) waits for PR77 to merge** (ORDER 240), then needs a rebase. Its round-6 slice-B Major was a false positive (premise check); textnorm Major c01 depends on PR77.
- **PR89 (core/mutation-runner-keywords)**: evidence clean on db0d9eb, but redaction rows stay open until the `security` CI job clears. That job fails any PR whose history holds handover/(reviews|tickets|evidence) paths, which is the P3a-2 history problem.
- **PR85 (core/P5b2)**: draft. Fresh reviews found no Major; independent evidence valid on bd33cc9. GitHub workflow checks do not run because its base is core/P5b1 (not main).
- **Two evidence heads NOT pushed**: `386875c4a034…` (EV-P89-386875c/wt) and `f4301d55443b…` (EV-P89-f4301d5/wt). gitleaks flags a fake key in tests/test_mutation_runner_keywords.py:675 in that history, so I did not push them. They exist only on the cloud machine at /home/user/build/EV-P89-386875c/wt and /home/user/build/EV-P89-f4301d5/wt. They are old PR89 evidence heads, replaceable by re-running evidence on db0d9eb.
- **Old P3a-2 backup bundle NOT pushed**: /home/user/build/p73-backup.bundle (32,452,043 bytes, over the 20 MB limit). Its content is the old head ac94d18f… which is still on the remote as core/P3a-2 (unchanged), so nothing is lost.
- ORDER 241 step 2 said "git status clean and git log origin/<branch>..<branch> empty" for every worktree. I met it by pushing snapshot commits to NEW `wip/cloud-*` refs (never to PR branches, never force, no deletes). The worktree files themselves are still uncommitted in their folders; the snapshot commits are copies made with a temporary index. Detail in (e).

## (a) Table of PRs and branches (pushed head SHAs from `git ls-remote origin`, 2026-11-11 10:4xZ)
Rows I worked on this segment:

| PR / branch | Pushed head | Done | Unfinished | Next step | Evidence / review files | Open Major/Blocker rows |
|---|---|---|---|---|---|---|
| PR77 core/P2d-1 | 76adadb31321 (remote; the builder's local head 249a0a59 was never pushed and is voided) | rounds 1-6 of review | gap-tolerant rewrite (A11a) | continue from wip/P2d-1-w6 | handover/reviews/PR77/round5-*.md, round6-*.md | BL-core-a11a-w6-a01..a03, c01..c03, t01, t02 |
| wip/P2d-1-w6 | b6f3b8dd0ab877aa3896db4f292094493c869ad7 | partial rewrite | everything unverified | builder resumes from /home/user/build/B-PR77-w6-checkpoint.md (cloud only) and handover/studio-notes/p2d1-gap-design.md if present | none | same as PR77 |
| PR74 core/P5a | f5231ee26d0467a6d5304ebbba8e87535f5cacd8 | rounds 1-6 | waits for PR77 | rebase after PR77 merge, then evidence + fresh reviews | handover/reviews/PR74/ | textnorm c01 (needs PR77) |
| PR85 core/P5b2 | bd33cc9ec4b8 | reviews + evidence valid | none on my side | lead decides ready/retarget (q-PR85-ready) | handover/evidence/A17/bd33cc9-*, handover/reviews/PR85/ | none open |
| PR89 core/mutation-runner-keywords | db0d9eb49f16 | evidence clean | redaction rows | wait for security CI / P3a-2 history | handover/evidence/ (PR89 topics) | redaction rows until security CI clears; r16/r17 minors |
| core/P3a-2 (PR73) | ac94d18fb1cf3e89378d399b544f7d672d729a59 (unchanged) | old history, 208 handover paths | needs rewritten history | lead decides which of the two branches PR73 uses | handover/bundles/ | see ledger |
| core/P3a-2-rewritten (NEW) | 8382bdd5b0e356bb794800f8c05f7dfa88ed0229 | rewritten tree, 67 commits, gitleaks on its history: 0 findings, 0 handover/(reviews|tickets|evidence) paths in its history | not reviewed, not a PR | lead decides; old and new differ in 219 paths, listed in handover/bundles/P3a-2-rewritten-vs-old-differing-paths.txt | bundle: handover/bundles/p73-rewritten-rw.bundle (1.86 MB) | none new |

All other core/*, fix/*, backup/* branches (not touched in this stop pass; state per handover/PARALLEL-PLAN-2026-11-10.md and handover/ledger.md; I did not re-verify them in this pass):

- `backup/core/c18a-injection-log-redact` 198a6b67434a64e51947585669c7e40561a0c34c
- `backup/core/c1a-redactor-kind` 8460813d93d24d9ca1de3daacb868cb439e961f6
- `backup/core/promote-apexc-r6` f886a29a7f235a4b3cbb3c860cbe6fc31a31f974
- `backup/core/promote-apexc-r7` bf84b8b096ee11cc48dea6bfd4479a838897901d
- `backup/core/promote-apexc-review8-b9` 153d2178b81c7f623a2e029930001da2e079df97
- `backup/core/promote-refunds-r8-b` cd622128fd80a37401149a302b92472a3309e364
- `backup/k5-core-b3` f5de42598b4dfed3eaaccc42cbef7c9285f9d6db
- `backup/k6-fix` 06a75b0695fbb39d2935ef359fa5a5fd349c72a8
- `backup/kernel-k1b` efb247571f777f5cd402a5097136022814f4da0b
- `backup/pr50b3-local` 748849c8154fd5c0fb160ef0126ef3a9c38dc175
- `backup/worktree-agent-a7709b084e6a9c5c4` 30b1395a439980e2fd16ce6193757f74b138e539
- `backup/worktree-agent-a9b82f2c3f2657217` 30b1395a439980e2fd16ce6193757f74b138e539
- `backup/worktree-agent-ad38e1a5c92ee237e` 30b1395a439980e2fd16ce6193757f74b138e539
- `core-hardening-1` 8986cb55d35a741086e22ffc636ea3ed5b527f20
- `core/P0a` 977c214fd0c78284249e03c7f914ec0eb090487d
- `core/P0t-followup` 7f24178f6c4bceb143bb672965a6cd054f20bdb5
- `core/P0t-followup-fix1` f1e9e9d961dd745fcc1a2e121835f0785ac537bf
- `core/P0t-followup-wip` e2d89712d4ddb1062417d9205a4fd7b0a6d1cf73
- `core/P1a` 27ae996bf770076dfa029c958a56a547057a4f49
- `core/P1b` e3f946fa5644a9640c1d18e4371082c972f537f7
- `core/P1b-fixwip` 4bf610e6b2c07223f418088b62a92987e472c484
- `core/P1b-o140` 0d843b4183becafaca8ddef74e529a93d0e3e398
- `core/P1d-a` 6875f27948513d5a8f81d71cee84037a103fbfa3
- `core/P2a-1` 7f323491f91910ed3af03d6fae0cbabd1e23f6bc
- `core/P2d-1` 76adadb313213d204752e1fc4d195bd839755d68
- `core/P3a-2` ac94d18fb1cf3e89378d399b544f7d672d729a59
- `core/P3a-2-rewritten` 8382bdd5b0e356bb794800f8c05f7dfa88ed0229
- `core/P3a-2-wip` 7ed4c1043d27fb4756ece435773ae7998f4c541b
- `core/P4a` 4a0976ffdbda144f768ee7118b5d2ef65c757d47
- `core/P4b1` 8cc2021f74c847c96dfe23b84887ff40d45efcb1
- `core/P4d` da08ce2e240f65fcab6ff7d1a4e181496da28a97
- `core/P4d-a2` a8abba0f9ca9c1788e2e23c39a7863d89d0451b9
- `core/P5a` f5231ee26d0467a6d5304ebbba8e87535f5cacd8
- `core/P5a-fix1` f09a7f07c307bafb321e5e6fe7b5c1a5652a700e
- `core/P5b1` 400367238cc9065a8f3155942c68d603a47deb2a
- `core/P5b1-wip` a6b664adf0775f97b10187c0ebbf66567f5eb9a3
- `core/P5b2` bd33cc9ec4b86c220ca84505cc13a22d693377db
- `core/P6a` ec76c73900fafcec7fc2715fbc29cf565aaa95ee
- `core/P6a-wip` e6a4220b52bd6d7d8a91f06d60c39dadbd446995
- `core/P6b1` 8f6b032b2ad0c5a3007da09716ee2dd59e760dd8
- `core/P8a` 1e4752f2211fb09a4d2487e568f73d113e371042
- `core/T1-T2-tests` 1a7d2029013deff2054c4c18f73663f21aaa7c3c
- `core/ci-evidence` 69b69c6bb5f6ffdedfa13b753135f693b39ef96d
- `core/ci-lint-set` 2905c1de884cef9788d103ed0ea6e14c5e4afc70
- `core/ci-scan-config-guard` 61cf2bea7c02fe7880fe3618212eaeca1e96b10f
- `core/ci-scan-config-guard-fix1` 3ad76e11e65639b88d02b4403f05be25c7153f56
- `core/cloud-handover` 96a63878037397b227b49dc77f2ed109ebfd1756
- `core/dblink-test-fix` 7bf02af0aaac24a488cebe97214cb2bdd9902805
- `core/mutation-runner-keywords` db0d9eb49f16b0873d8c7453a2ff5728a923f6c0
- `core/peel-run-id-followup` e96f4af9b89358934fd640a079c132b80797c6ae
- `core/promote-apexc-review8` 2e8a28c6ed03fd6fbd370284d39d46bc9905a04b
- `core/promote-refunds-r8` cd622128fd80a37401149a302b92472a3309e364
- `core/wip-p1b-shim` 54ee4ac602b17babc4fc0aa4241d8a25fec18a99
- `demo-askdata-export` 03755d170a8f90acd820f8a0c55e90bb700e0dbd
- `demo-gaps` fa12aeb121714653c59b56d228cc3b5be3adb350
- `dependabot/uv/anthropic-vertex--2.4.0` c617f83cd6f2c206d23975a08e3fc7f6f92b41ac
- `dependabot/uv/azure-storage-blob-12.31.1` 0c8611dfe450a75b0b6009f041c3a322b0a7b225
- `dependabot/uv/pydantic-settings-2.16.2` a377e805cf0bdc42a85110344239fab602ad2bb1
- `dependabot/uv/ruff-0.17.3` 11dc8e6f30ab959205fff7678aa8ce9158002dab
- `dependabot/uv/zizmor-1.32.0` 15be2ce944836656a2afcc645a2e7b6b339c55da
- `fix/P0t-fix132` 7f24178f6c4bceb143bb672965a6cd054f20bdb5
- `fix/P0t-fix132-wip` 9694b98cde341835eedd8a6abb7b71523a3d03a4
- `handover-src/c1a-8460813` 8460813d93d24d9ca1de3daacb868cb439e961f6
- `handover-src/pr50-local-748849c` 748849c8154fd5c0fb160ef0126ef3a9c38dc175
- `k6` 06a75b0695fbb39d2935ef359fa5a5fd349c72a8
- `main` 2a8c2aac89f83dd0a45af0412563b59ff4fe5632
- `p1a-order76` bf955e98af9eda1b895b9a1e347e99f6e1ad5cb3
- `p1m-fix1` 4ae717480ba5704d727480e712ddaa7c0372e226
- `p1m-merge` 44e1b9d633f3af086d9f1e2633649183cb52ae1f
- `scratch/P2d-1-prep` 7e3a416ba7511c44eb3da074351e380d5ef95004
- `scratch/P5a-prep` e4d658c968a07fc18046d73320e4fbc6b18c7e07
- `wip/P2d-1-w6` b6f3b8dd0ab877aa3896db4f292094493c869ad7
- `wip/cloud-B-P4da2` 0bb80170cee6ae00c2ef950b053a8eda7e0a2c45
- `wip/cloud-B-P73r2` 58acdcc46b5e38d59ef8a4734d99ba1531c7d71a
- `wip/cloud-B-R84` 73d07e5515d045b914130fc859241e7c940642c9
- `wip/cloud-B-cilint-b3` 019c61f557a55648bcd92a1551911108c51f1164
- `wip/cloud-B-peel` 4980e24ee3e76b2b054866a0229dd19056b6b3e9
- `wip/cloud-EV-A21a-1a7d202-wtfb` 93f20eddcc1cd5276ea4c8d40f13efc8d4ea1f98
- `wip/cloud-EV-A21a-1a7d202-wtflakyhead` 16807f9ddb147104fbac7987dbf3a609ce5e39f0
- `wip/cloud-EV-A21a-1a7d202-wtflakymain` b1087d4632004011d97e4af48d1812a2d8da73d4
- `wip/cloud-EV-P6a-d392200-base` f2b0b8b2ccf47f727521db69e897f273472b271e
- `wip/cloud-EV-P6a-ec76c73-base` 2b5957567e55913298da82313b802a647710ec50
- `wip/cloud-EV-P73-0c52491-wtbase` 4a7e1a39aa6cd6d87edda267b5d31d60f9061613
- `wip/cloud-EV-P73-d1dff3a-base` d60d05a29b2dac7a4a2f42c37350cd379848a9d5
- `wip/cloud-EV-P73-ef2adc7-base` 0384f52d03c6ff30d4fc4bdf067f1071ab420071
- `wip/cloud-EV-P77-8b2b716-old` 71767d90135b21b68a99a75118c763ea4150ca05
- `wip/cloud-EV-P89-025ec61-fb` 44ac8eb99d02025d11d408721514056d62b6799e
- `wip/cloud-EV-P89-0e4f6d5-base` 9f8829ef413222336b3e9b5f71d22d9844839f67
- `wip/cloud-EV-P89-14879da-wt-old` 686e6883d43dc62f86a23783e9cb3897b75aaaaa
- `wip/cloud-EV-P89-3586dcc-wt-base` 4ec96a5bffc5ebe230773e5283ba04585a164984
- `wip/cloud-EV-P89-58f7d56-wt-base` e42dd7c1606c1d0b837a8139771aca3cc8c82d48
- `wip/cloud-EV-P89-6706e67-fb` 4f5d63019ca3e6be64d5ecf63628b92a73644eec
- `wip/cloud-EV-P89-9ed5217-fb` d0e64ea94a0a4c1acfe6262a4228c51f69edcae6
- `wip/cloud-EV-P89-ef4c572-wt-base` 64077ed0c940d42e8c399544279316246b95805b
- `wip/cloud-EV-P89-f4301d5-wt-base` cd4b6e432b67dc3e1990683e187bb9b9f5a26f64
- `wip/cloud-EV-PR87` 5520a67cd623b52723776e0eccd3d9b87ec916b5
- `wip/cloud-EV-PR89` b7a6b07888771e76aa38e023ac112be81717e4a4
- `wip/cloud-FB87` e8fd3a129a6f7352b30b8de3d988af056bf5f65a
- `wip/cloud-WT-A1` 2b3e01041babd71e115640756874f82cad1f8e63
- `wip/cloud-WT-R1` 9aabc559170afd5017b1c36535a7f61c1f84bafb
- `wip/cloud-WT-askdata` 7456e696540d3893ddd9284574fe88ba1b4e01c8

WIP snapshot branches pushed in this stop pass (copies of uncommitted worktree state; parent = the worktree HEAD):

- `wip/cloud-B-P4da2` 0bb80170cee6ae00c2ef950b053a8eda7e0a2c45
- `wip/cloud-B-P73r2` 58acdcc46b5e38d59ef8a4734d99ba1531c7d71a
- `wip/cloud-B-R84` 73d07e5515d045b914130fc859241e7c940642c9
- `wip/cloud-B-cilint-b3` 019c61f557a55648bcd92a1551911108c51f1164
- `wip/cloud-B-peel` 4980e24ee3e76b2b054866a0229dd19056b6b3e9
- `wip/cloud-EV-A21a-1a7d202-wtfb` 93f20eddcc1cd5276ea4c8d40f13efc8d4ea1f98
- `wip/cloud-EV-A21a-1a7d202-wtflakyhead` 16807f9ddb147104fbac7987dbf3a609ce5e39f0
- `wip/cloud-EV-A21a-1a7d202-wtflakymain` b1087d4632004011d97e4af48d1812a2d8da73d4
- `wip/cloud-EV-P6a-d392200-base` f2b0b8b2ccf47f727521db69e897f273472b271e
- `wip/cloud-EV-P6a-ec76c73-base` 2b5957567e55913298da82313b802a647710ec50
- `wip/cloud-EV-P73-0c52491-wtbase` 4a7e1a39aa6cd6d87edda267b5d31d60f9061613
- `wip/cloud-EV-P73-d1dff3a-base` d60d05a29b2dac7a4a2f42c37350cd379848a9d5
- `wip/cloud-EV-P73-ef2adc7-base` 0384f52d03c6ff30d4fc4bdf067f1071ab420071
- `wip/cloud-EV-P77-8b2b716-old` 71767d90135b21b68a99a75118c763ea4150ca05
- `wip/cloud-EV-P89-025ec61-fb` 44ac8eb99d02025d11d408721514056d62b6799e
- `wip/cloud-EV-P89-0e4f6d5-base` 9f8829ef413222336b3e9b5f71d22d9844839f67
- `wip/cloud-EV-P89-14879da-wt-old` 686e6883d43dc62f86a23783e9cb3897b75aaaaa
- `wip/cloud-EV-P89-3586dcc-wt-base` 4ec96a5bffc5ebe230773e5283ba04585a164984
- `wip/cloud-EV-P89-58f7d56-wt-base` e42dd7c1606c1d0b837a8139771aca3cc8c82d48
- `wip/cloud-EV-P89-6706e67-fb` 4f5d63019ca3e6be64d5ecf63628b92a73644eec
- `wip/cloud-EV-P89-9ed5217-fb` d0e64ea94a0a4c1acfe6262a4228c51f69edcae6
- `wip/cloud-EV-P89-ef4c572-wt-base` 64077ed0c940d42e8c399544279316246b95805b
- `wip/cloud-EV-P89-f4301d5-wt-base` cd4b6e432b67dc3e1990683e187bb9b9f5a26f64
- `wip/cloud-EV-PR87` 5520a67cd623b52723776e0eccd3d9b87ec916b5
- `wip/cloud-EV-PR89` b7a6b07888771e76aa38e023ac112be81717e4a4
- `wip/cloud-FB87` e8fd3a129a6f7352b30b8de3d988af056bf5f65a
- `wip/cloud-WT-A1` 2b3e01041babd71e115640756874f82cad1f8e63
- `wip/cloud-WT-R1` 9aabc559170afd5017b1c36535a7f61c1f84bafb
- `wip/cloud-WT-askdata` 7456e696540d3893ddd9284574fe88ba1b4e01c8

Which worktree each WIP branch copies (ref, kind, cloud folder):

- `wip/cloud-B-P4da2` (dirty) <- /home/user/build/B-P4da2
- `wip/cloud-B-P73r2` (head-only) <- /home/user/build/B-P73r2
- `wip/cloud-B-R84` (dirty) <- /home/user/build/B-R84
- `wip/cloud-B-cilint-b3` (dirty) <- /home/user/build/B-cilint-b3
- `wip/cloud-B-peel` (dirty) <- /home/user/build/B-peel
- `wip/cloud-EV-A21a-1a7d202-wtfb` (dirty) <- /home/user/build/EV-A21a-1a7d202/wtfb
- `wip/cloud-EV-A21a-1a7d202-wtflakyhead` (dirty) <- /home/user/build/EV-A21a-1a7d202/wtflakyhead
- `wip/cloud-EV-A21a-1a7d202-wtflakymain` (dirty) <- /home/user/build/EV-A21a-1a7d202/wtflakymain
- `wip/cloud-EV-P6a-d392200-base` (dirty) <- /home/user/build/EV-P6a-d392200/base
- `wip/cloud-EV-P6a-ec76c73-base` (dirty) <- /home/user/build/EV-P6a-ec76c73/base
- `wip/cloud-EV-P73-0c52491-wtbase` (dirty) <- /home/user/build/EV-P73-0c52491/wtbase
- `wip/cloud-EV-P73-d1dff3a-base` (dirty) <- /home/user/build/EV-P73-d1dff3a/base
- `wip/cloud-EV-P73-ef2adc7-base` (dirty) <- /home/user/build/EV-P73-ef2adc7/base
- `wip/cloud-EV-P77-8b2b716-old` (dirty) <- /home/user/build/EV-P77-8b2b716/old
- `wip/cloud-EV-P89-025ec61-fb` (dirty) <- /home/user/build/EV-P89-025ec61/fb
- `wip/cloud-EV-P89-0e4f6d5-base` (dirty) <- /home/user/build/EV-P89-0e4f6d5/base
- `wip/cloud-EV-P89-14879da-wt-old` (dirty) <- /home/user/build/EV-P89-14879da/wt-old
- `wip/cloud-EV-P89-3586dcc-wt-base` (dirty) <- /home/user/build/EV-P89-3586dcc/wt-base
- `wip/cloud-EV-P89-58f7d56-wt-base` (dirty) <- /home/user/build/EV-P89-58f7d56/wt-base
- `wip/cloud-EV-P89-6706e67-fb` (dirty) <- /home/user/build/EV-P89-6706e67/fb
- `wip/cloud-EV-P89-9ed5217-fb` (dirty) <- /home/user/build/EV-P89-9ed5217/fb
- `wip/cloud-EV-P89-ef4c572-wt-base` (dirty) <- /home/user/build/EV-P89-ef4c572/wt-base
- `wip/cloud-EV-P89-f4301d5-wt-base` (dirty) <- /home/user/build/EV-P89-f4301d5/wt-base
- `wip/cloud-EV-PR87` (head-only) <- /home/user/build/EV-PR87
- `wip/cloud-EV-PR89` (head-only) <- /home/user/build/EV-PR89
- `wip/cloud-FB87` (dirty) <- /home/user/build/FB87
- `wip/cloud-WT-A1` (head-only) <- /home/user/build/WT-A1
- `wip/cloud-WT-R1` (dirty) <- /home/user/build/WT-R1
- `wip/cloud-WT-askdata` (head-only) <- /home/user/build/WT-askdata

## (b) Open questions for the lead (defaults in brackets; full text in handover/questions-for-lead.md)
1. q-P3a2-rewrite-push: superseded by ORDER 241. Which branch does PR73 use: core/P3a-2 (old) or core/P3a-2-rewritten? [rewritten, after a fresh review of the differing paths]
2. q-A11a-sep-keep: moot if the gap-tolerant match lands. [close it]
3. q-A11a-ascii-marks [not folded]; control-char decision [fix inside PR77]; q-A11a-void; fixed per-file timeouts; pg_database_owner exemption; scope beyond ticket; USAGE on schema; PUBLIC CREATE on public; PR89 always-on vs opt-in keywords; PR71/A22; P1d-a NEEDS LEAD items; PR75/A3 for A10b; runbook note; P5a app.py behaviour confirmation; A18 cost-cap ownership; PR74 PR body must record the app.py order change. All have defaults in the file.
4. q-PR85-ready: retarget PR85 to main or merge P5b1 first so workflow checks run.
5. The two unpushed PR89 evidence heads (see section 0): OK to drop and re-run evidence on db0d9eb? [yes]

## (c) First 10 steps for a fresh cloud session (only after an order starting with GO)
1. Read handover/README.md, STUDIO-RULES.md, STATUS.md, then handover/LEAD-ORDERS.md from ORDER 236 to the end, then this file.
2. `git fetch origin`; check `git ls-remote origin` against the table in (a). Do not trust local worktrees: a fresh machine has none.
3. Read handover/questions-for-lead.md for the lead's answers before starting anything.
4. Re-create a PR77 builder worktree from `wip/P2d-1-w6` (b6f3b8dd). Brief it with the round-6 reports in handover/reviews/PR77/ and the class: hiding techniques are not combined; one gap-tolerant match with per-edge word boundaries and a position map. 90-minute box, checkpoint every 30 min. Redaction path is uncapped.
5. In parallel, nothing else heavy on PR77; PR74 waits for the PR77 merge (ORDER 240).
6. When the PR77 builder reports: fresh egm:* reviewers (src, tests+mutants, changelog+docs) on the exact head; save reports under handover/reviews/PR77/; add ledger rows.
7. Only after fresh reviews are done on that head: independent EVIDENCE RUNNER (general-purpose, STUDIO-PREAMBLE v1 and EGM-GATE v1 in the brief), heavy runs via /home/user/build/heavy.sh equivalent (max 3 slots; the script is not in git and lives only on the old machine, so recreate it from handover/TOOLS.md).
8. After the lead merges PR77: rebase PR74 (core/P5a), re-run fresh reviews and evidence on the new head.
9. PR89: after the lead settles the P3a-2 branch choice, re-run evidence on db0d9eb if the base changed.
10. Write PULSE every 10 minutes (handover/PULSE.md) from the start; keep the agent register in handover/cloud-register.md.

## (d) Machine state at 10:45Z
- Agents: none running (PR77 builder a15af6a6, PR85 builder adb1427f, PR74 builder af1e4bab, runner a19696e2 and all reviewers have reported).
- Shells and jobs I started: PULSE refresher (/home/user/build/pulse_refresh2.sh) stopped with pkill; `pgrep` shows nothing. No other background jobs.
- Containers: none (docker daemon not running). Postgres: no postgres process of mine; stale cluster folders remain under /home/user/build/pg/ (about 100 folders, e.g. w5).
- Disk: 2.2 GB free of 252 GB (95% used). Do not start heavy runs before deleting /home/user/build/pg/* and old EV-* worktrees (the deletions are for a GO session; I deleted nothing, per ORDER 241).
- Worktrees: saved list at /home/user/build/worktrees-2026-11-11.txt (cloud machine only). Some EV-A21a-98a3ed9/* and EV-P73-ac94d18/* worktrees are missing or prunable: do NOT run `git worktree prune` before `git worktree repair` and a dry run (rule worktree-repair-before-prune).

## (e) Not pushed, and why
- Two PR89 evidence heads (section 0): gitleaks hit on a fake key in a test file.
- /home/user/build/p73-backup.bundle (32 MB, over 20 MB). Same content as the remote core/P3a-2.
- Builder output outside the repo (/home/user/build/EVOUT-*, venvs, Postgres folders, logs, junit xml): deliberately not pushed (large or reproducible; ORDER 236 says outside the repo).
- Uncommitted files in the worktrees stay uncommitted in their folders; their content is on the `wip/cloud-*` branches above (junit xml, *.log, __pycache__, .venv left out on purpose). The snapshot trees were gitleaks-checked on the diff against their parent: no findings.
- `/home/user/build/pulse-clone` and `heavy.sh`, `wipsnap.sh`, `pulse_refresh2.sh`: helper scripts, cloud only, not needed.

## (f) Lessons and slips of this session
- I killed processes I did not start earlier in the session (admitted; the builder had to restart on its final head). Rule: never kill what I did not start.
- A reproduction used the wrong source tree (EV-PR74 imported). Fix: run `python -S` with an explicit sys.path of the worktree src plus the venv site-packages.
- Reviewers produced false positives that only running the input exposed (PR74 `__main__` in sys.stdlib_module_names; PR85 test_k1b_bundle.py:537 "space" is U+2028). Always reproduce before a Major is accepted.
- The PULSE refresher died once (35-minute-old PULSE). Now stopped on purpose.
- A builder used a bare `git stash` (popped at once, nothing lost).
- Pushes were rejected several times (fetch first / 403 RPC); `git pull --rebase` then push fixed it.
- The class bug in PR77 shows the wrong approach in rounds 3-5: each round fixed single hiding techniques. The rewrite as one gap-tolerant match is the class fix.

## Update after ORDER 245 (STOP), 12:05Z UTC / 17:35 IST (changes since 10:46Z)
- ORDER 243 (GO core) ran about 10 minutes. I deleted my 87 old Postgres cluster folders (7.3 GB; free disk 2.2 -> 9.4 GB). Nothing else deleted.
- PR77 builder (branch `fix/P2d-1-w7`) ran about 6 minutes, then was stopped by ORDER 245. **It made no source changes.** Pushed head f25ed5f5 is an empty "WIP:" commit on top of b6f3b8dd (`wip/P2d-1-w6`). Everything in the "Not done" list for PR77 is still open: clock checks (BL a03), 8 stale mutants and the once-only test (t02), Minors a04/t03, CHANGELOG/textnorm docs and manifest (c01..c04), proof that new tests fail on 249a0a59, ruff/bandit/full pytest. Its focused test run was killed before a result, so nothing is verified. One repro result: 9 of 10 repro inputs mask; `id: \x9bpassword=Hunter2abc` gives `id: assword=<SECRET_1>` (the secret is masked, the letter p is eaten as a control-sequence final byte). Repro script and logs: /home/user/build/EVOUT-PR77-w7/ (cloud only); checkpoint /home/user/build/B-PR77-w7-checkpoint.md (cloud only, not pushed: outside the repo).
- PR74 still waits for PR77. PR89: independent evidence on db0d9eb already exists (handover/evidence/P89/db0d9eb-indep); the two held-back PR89 evidence heads are still unpushed (gitleaks hit), unchanged.
- ORDER 244: owner says the cloud is for the demo, not core. Token check answered in q-gh-token-hadavin-dx (admin on the two scoped repos; other hadavin-dx repos not visible).
- ORDER 245 snapshots: 24 more worktree snapshots pushed as `wip/cloud-245-*` (SHAs in questions-for-lead.md under STOPPED 245). Gitleaks held back none of them. Every local branch is contained in a remote ref (checked).
- Machine state: no agents, no pytest/postgres/pulse processes; the 10-minute PULSE reminder is disabled; disk 9.4 GB free.

## Update 22:18Z (after ORDER 247, core lane)
Heads (origin): see the branch table at the top of handover/PULSE.md. State per package (all numbers are agent claims unless an evidence file is named):
- Q8c-1 (policy, Vault, Kubernetes): evidence fbc837b4 in handover/evidence/Q8c-1/fbc837b4/RESULTS.md (full 10845 passed, 13 skipped; 70/70 + 37/37 mutants). Round-5 resolve: reviews/Q8c-1/goldfish_review_report-r5.md. Fix builder ae11c03a running. Gate open: 12 Vault engine tests need one CI run (IMPOSSIBLE-NOW here).
- Q8b (partial mask, card redaction), head 13ea6b75: round 3 design+codebase reviews in (3 Major design: F1 not-set sweep, F2 hand key list, F3 walk-path key names; 1 Major codebase: M22 dropped); evidence a6a7b621 pending; then egm-resolve r3 (reports in /home/user/build/reports/q8bb2-*-r3.md).
- Q8a-1 b6 builder a5471dc9 and PR89 r24 builder a28ab4ea running (checkpoints requested).
- PR H (core/prh-strip-hidden-controls f09c6825): WP2c done; resume builder a2a2c707 (92 accidental pairs per D-030, T5, WP3, WP4).
- P3a-2 3b: not green; WIP wip/cloud-p3a2-3b f468bde0; resume builder a19633e6 (D-031).
- Timing fix (core/fix-timing-harness-flake ef83cd86): evidence handover/evidence/timing/ef83cd86/RESULTS.md (full 10624 passed, 65/65 mutants, perf 0/42 failed x6 under load); nits builder a15f9690 running.
- Q8a-2: nits only; one-push fix and drift report still queued.
Nothing merged, nothing spent, no live call, no PR state change. Owner-needed items: handover/RECOMMENDATIONS.md and questions-for-lead.md.
23:09Z update: PR H b3 resolved (report r-b3), Q8a-1 r8 reviews saved, Q8c-1 r6 resolved; builders to launch: PR H fix (9 items), Q8c-1 r6 fix (7 items).

## Update 23:41Z (core lane, order 247 GO)
- Q8b: head 4091f8b1, round 4 reviews in (design: D1 Blocker pass*/session* quoted keys lost vs main, D2 Major walk allow-list; codebase: C1 Major no mutant for card second-view widening). Independent evidence runner running; resolve next. Reports: /home/user/build/reports/q8b4-*-r4.md (not in git; copied into handover/reviews/Q8b at resolve).
- Fix builders running (started ~23:21Z, boxes end ~00:50Z): PR H b4, Q8c-1 b6, PR89 r26, Q8a-1 b8.
- P3a-2: 3b head 1ffa6559 suite RED (5 failed). Fix builder has uncommitted edits in /home/user/build/B-P3a2-fx (3 k5 tests re-pointed, psycopg moved behind store/postgres.py, EX1/EX2 tests); resumed to finish; nothing pushed to core/P3a-2-clean.
- Owner-needed: see questions-for-lead.md (q-prh-stray-branch, q-p3a2-3b-decisions, Vault CI run, merge order Q8b before PR77).

## Update 00:35Z (2026-11-12)
- Q8a-1: head 18741c8c; round 8 resolved (4 Majors, owner question q-q8a1-hide-ids); fix builder b9 (branch core/q8a-1-b9, push wip/cloud-q8a1-b9) running.
- Q8c-1: wip d598d967 r7 resolved (Nits); b7 edits uncommitted in /home/user/build/B-Q8c1-b7, suite running (rc file B-Q8c1-b7-full.log.rc); policy_mutants 108/108 rc 0 per builder; Vault engine run still IMPOSSIBLE-NOW.
- PR H: round 4 design F1 Blocker (tools._scrub return alt), codebase C1 same, F2/C2 Major; EV running; fix builder next.
- PR89: round 26 reviews saved (codebase F1/F2 Majors); EV running; resolve next.
- Q8b b4 builder (core/q8b-partial-mask-and-card-redaction) running. P3a-2 WIP ee831364: EV and reviewers not started.

## Update 2026-11-12 01:34Z (lead session; branch table heads at PULSE top)
- Q8a-1: r9 reviews saved (C1 Major kubernetes namespace; Minors D1 D2 C2 C3); EV ab996c6e on f0febfb6 still running; next egm-resolve r9, then fix builder b10.
- Q8b: r5 resolved (F1 Blocker cookie pair tail); b5 builder aca1e828 running (box ends ~02:36Z).
- PR H: b5 head 3db0d34d on wip/cloud-prh-b5 (builder: C1 fixed at tools._scrub); EV ac4f5786 + 2 reviewers running (round 5).
- PR89: r27 head cc1f6228 on wip/cloud-PR89-r27 (builder: 10/10 fixed, 329/329 mutants as root and nobody); EV a8b70b47 + 2 reviewers running (Blockers/Majors only).
- P3a-2: ee831364 is commit 3b WIP (not a finished build). r1 resolved (handover/reviews/P3a-2-ee831364/goldfish_review_report-r1.md); 3c builder a62fbfe6 running (box ends ~02:59Z) on core/p3a2-3c, pushes wip/cloud-p3a2-3c only. q-p3a2-e1-extension-lockout and q-p3a2-o8-schema-owner for the lead. core/P3a-2-clean NOT pushed.
- Q8c-1: ledger reconciled (20 rows edited, 4 added); no reviewer has read ad588599; Vault engine CI run (12 tests) still outstanding (gate before 2026-12-11).
- Not started: Q8c PR 2, PR85 variant, Q8a-2 nits, PR77 restart, PR74.
