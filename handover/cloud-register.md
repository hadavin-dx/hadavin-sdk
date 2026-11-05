# Cloud agent register (live). One row per agent, written BEFORE it starts.
Times UTC. Model column = the model set explicitly on the Agent call (MODEL-ROUTING.md rule 2/6).

| agent | purpose | model | started | expected end | last checked | state | next action |
|---|---|---|---|---|---|---|---|
| drafter-P1 | draft P1 ticket | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | 2026-11-05 14:36Z | revision reported, closed | verify; egm-review-loop needs the user |
| drafter-P3a | draft P3a ticket | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | 2026-11-05 14:36Z | revision reported, closed | verify claims, then egm-review-loop |
| drafter-P2a | draft P2a ticket | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | 2026-11-05 15:05Z | revision reported, closed | verify; egm-review-loop needs the user |
| drafter-P4d | draft P4d ticket | sonnet (claude-sonnet-5-5) | 2026-11-05 14:27Z | 15:12Z | 2026-11-05 15:05Z | revision reported, closed | verify claims, then egm-review-loop |

Note (honesty): "last checked" times written before 14:43Z today were estimated by the lead, not read from a clock, and can be off by tens of minutes. From here the clock is read with `date -u`.

## Round 1 ticket reviews (fresh reviewers, Sonnet 5.5, read-only; started 14:43Z UTC, expected end 15:13Z UTC)
| agent | purpose | model | started | expected end | state | next action |
|---|---|---|---|---|---|---|
| rev-P1-correctness | egm:egm-codebase-details on tickets/P1.md (ticket commit e35eb4d) | sonnet (claude-sonnet-5-5) | 14:43Z | 15:13Z | reported, report saved, closed | n/a: save report to handover/reviews/P1-round1-correctness.md |
| rev-P1-adversarial | egm:egm-design on tickets/P1.md | sonnet (claude-sonnet-5-5) | 14:43Z | 15:13Z | reported, report saved, closed | n/a: save to handover/reviews/P1-round1-adversarial.md |
| rev-P3a-correctness | egm:egm-codebase-details on tickets/P3a.md (1ed7499) | sonnet (claude-sonnet-5-5) | 14:43Z | 15:13Z | reported, report saved, closed | n/a: save report |
| rev-P3a-adversarial | egm:egm-design on tickets/P3a.md | sonnet (claude-sonnet-5-5) | 14:43Z | 15:13Z | reported, report saved, closed | n/a: save report |
| rev-P2a-correctness | egm:egm-codebase-details on tickets/P2a.md (b300b6b) | sonnet (claude-sonnet-5-5) | 14:43Z | 15:13Z | reported, report saved, closed | n/a: save report |
| rev-P2a-adversarial | egm:egm-design on tickets/P2a.md | sonnet (claude-sonnet-5-5) | 14:43Z | 15:13Z | reported, report saved, closed | n/a: save report |
| rev-P4d-correctness | egm:egm-codebase-details on tickets/P4d.md (d2d658b) | sonnet (claude-sonnet-5-5) | 14:43Z | 15:13Z | reported, report saved, closed | n/a: save report |
| rev-P4d-adversarial | egm:egm-design on tickets/P4d.md | sonnet (claude-sonnet-5-5) | 14:43Z | 15:13Z | reported, report saved, closed | n/a: save report |

## Round 1 fix batch (ticket authors resumed; Sonnet 5.5; started 15:00Z, expected end 15:40Z)
The egm-resolve skill cannot be started by the cloud session (tool refusal), so each ticket author works through every ledger row of its ticket and writes a disposition file. Fresh reviewers do round 2.
| agent | purpose | model | started | expected end | state | next action |
|---|---|---|---|---|---|---|
| fix-P1 (resumed drafter-P1) | rewrite tickets/P1.md for 43 findings; write reviews/P1-round1-disposition.md | sonnet (claude-sonnet-5-5) | 15:00Z | 15:40Z | STOPPED by lead at 15:05Z (superseded by the resolve step below) | none |
| fix-P2a (resumed drafter-P2a) | rewrite tickets/P2a.md for 34 findings; disposition file | sonnet (claude-sonnet-5-5) | 15:00Z | 15:40Z | STOPPED by lead at 15:05Z (superseded) | none |
| fix-P3a (resumed drafter-P3a) | rewrite tickets/P3a.md for 24 findings; disposition file | sonnet (claude-sonnet-5-5) | 15:00Z | 15:40Z | STOPPED by lead at 15:05Z (superseded) | none |
| fix-P4d (resumed drafter-P4d) | rewrite tickets/P4d.md for 37 findings (A11: money SQL in P4d); disposition file | sonnet (claude-sonnet-5-5) | 15:00Z | 15:40Z | STOPPED by lead at 15:05Z (superseded) | none |

## Ticket rewrite after resolve (authors resumed; Sonnet 5.5; started 15:06Z, expected end 15:46Z)
The Sonnet fix-batch rows above were stopped at 15:05Z before writing anything. The egm-resolve skill then ran (skill loaded after the patch script removed disable-model-invocation); reports: reviews/<P>-round1-resolve-report.md. The authors now APPLY those reports.
| agent | purpose | model | started | expected end | state | next action |
|---|---|---|---|---|---|---|
| apply-P1 (resumed) | apply P1-round1-resolve-report.md to tickets/P1.md; write P1-round1-disposition.md | sonnet (claude-sonnet-5-5) | 15:06Z | 15:46Z | reported, closed | verify, commit, round 2 reviewers |
| apply-P2a (resumed) | same for P2a | sonnet (claude-sonnet-5-5) | 15:06Z | 15:46Z | reported, closed | same |
| apply-P3a (resumed) | same for P3a | sonnet (claude-sonnet-5-5) | 15:06Z | 15:46Z | reported, closed | same |
| apply-P4d (resumed) | same for P4d | sonnet (claude-sonnet-5-5) | 15:06Z | 15:46Z | reported, closed | same |

## Round 2 reviews (fresh agents, Sonnet 5.5, read-only; they get the ticket and authorities only, NOT round 1 findings or dispositions)
| agent | purpose | model | started | expected end | state | next action |
|---|---|---|---|---|---|---|
| rev2-P2a-correctness | egm:egm-codebase-details on tickets/P2a.md rev 3 | sonnet (claude-sonnet-5-5) | 15:10Z | 15:40Z | reported, report saved, closed | saved reviews/P2a-round2-correctness.md |
| rev2-P2a-adversarial | egm:egm-design on tickets/P2a.md rev 3 | sonnet (claude-sonnet-5-5) | 15:10Z | 15:40Z | reported, report saved, closed | saved reviews/P2a-round2-adversarial.md |
| rev2-P3a-correctness | egm:egm-codebase-details on tickets/P3a.md rev 3 | sonnet (claude-sonnet-5-5) | 15:10Z | 15:40Z | reported, report saved, closed | saved reviews/P3a-round2-correctness.md |
| rev2-P3a-adversarial | egm:egm-design on tickets/P3a.md rev 3 | sonnet (claude-sonnet-5-5) | 15:10Z | 15:40Z | reported, report saved, closed | saved reviews/P3a-round2-adversarial.md |
| rev2-P4d-correctness | egm:egm-codebase-details on tickets/P4d.md rev 3 | sonnet (claude-sonnet-5-5) | 15:10Z | 15:40Z | reported, report saved, closed | saved reviews/P4d-round2-correctness.md |
| rev2-P4d-adversarial | egm:egm-design on tickets/P4d.md rev 3 | sonnet (claude-sonnet-5-5) | 15:10Z | 15:40Z | reported, report saved, closed | saved reviews/P4d-round2-adversarial.md |
| rev2-P1-correctness | egm:egm-codebase-details on tickets/P1.md rev 3 | sonnet (claude-sonnet-5-5) | 15:12Z | 15:42Z | reported, report saved, closed | saved reviews/P1-round2-correctness.md |
| rev2-P1-adversarial | egm:egm-design on tickets/P1.md rev 3 | sonnet (claude-sonnet-5-5) | 15:12Z | 15:42Z | reported, report saved, closed | saved reviews/P1-round2-adversarial.md |

## Revision 4 (round 3 preparation): authors resumed; Sonnet 5.5; started 16:33Z, expected end 17:13Z
Order 5 of LEAD-ORDERS.md. The round 2 resolve reports are reviews/<P>-round2-resolve-report.md; each author applies them and writes reviews/<P>-round2-disposition.md.
| agent | purpose | model | started | expected end | state | next action |
|---|---|---|---|---|---|---|
| rev4-P1 (resumed author) | apply 32 round 2 findings to tickets/P1.md | sonnet (claude-sonnet-5-5) | 16:33Z | 17:13Z | reported, closed | round 3 |
| rev4-P2a (resumed author) | apply 30 round 2 findings to tickets/P2a.md (Route A) | sonnet (claude-sonnet-5-5) | 16:33Z | 17:13Z | reported, closed | round 3 |
| rev4-P3a (resumed author) | apply 22 round 2 findings to tickets/P3a.md | sonnet (claude-sonnet-5-5) | 16:33Z | 17:13Z | reported, closed | round 3 |
| rev4-P4d (resumed author) | apply 34 round 2 findings to tickets/P4d.md | sonnet (claude-sonnet-5-5) | 16:33Z | 17:13Z | reported, closed | round 3 |

## Round 3 reviews (fresh agents, Sonnet 5.5, read-only; ticket revision 4 only; brief requires reading amendments A1-A14 first)
| agent | purpose | model | started | expected end | state | next action |
|---|---|---|---|---|---|---|
| rev3-P3a-correctness | egm:egm-codebase-details on tickets/P3a.md rev 4 | sonnet (claude-sonnet-5-5) | 16:39Z | 17:09Z | REPORTED, saved | save reviews/P3a-round3-correctness.md |
| rev3-P3a-adversarial | egm:egm-design on tickets/P3a.md rev 4 | sonnet (claude-sonnet-5-5) | 16:39Z | 17:09Z | REPORTED, saved | save reviews/P3a-round3-adversarial.md |
| rev3-P4d-correctness (SPAWNED LATE ~16:55Z; the earlier row was written before the agent existed: my mistake) | egm:egm-codebase-details on tickets/P4d.md rev 4 (b215b50) | sonnet (claude-sonnet-5-5) | 16:40Z | 17:10Z | REPORTED, saved | save reviews/P4d-round3-correctness.md |
| rev3-P4d-adversarial | egm:egm-design on tickets/P4d.md rev 4 | sonnet (claude-sonnet-5-5) | 16:40Z | 17:10Z | REPORTED, saved | save reviews/P4d-round3-adversarial.md |
| rev3-P2a-correctness | egm:egm-codebase-details on tickets/P2a.md rev 4 (6d84ad6) | sonnet (claude-sonnet-5-5) | 16:41Z | 17:11Z | REPORTED, saved | save reviews/P2a-round3-correctness.md |
| rev3-P2a-adversarial | egm:egm-design on tickets/P2a.md rev 4 | sonnet (claude-sonnet-5-5) | 16:41Z | 17:11Z | REPORTED, saved | save reviews/P2a-round3-adversarial.md |
| rev3-P1-correctness | egm:egm-codebase-details on tickets/P1.md rev 4 (221513b) | sonnet (claude-sonnet-5-5) | 16:41Z | 17:11Z | REPORTED, saved | save reviews/P1-round3-correctness.md |
| rev3-P1-adversarial | egm:egm-design on tickets/P1.md rev 4 | sonnet (claude-sonnet-5-5) | 16:41Z | 17:11Z | REPORTED, saved | save reviews/P1-round3-adversarial.md |

## Truth table at the time of STATUS 'READY FOR COMPACT'
Running: P4d round 3 correctness a57b3c2ac560f8313, P4d round 3 adversarial acecb19dd55a5e570. Finished and saved: P3a r3 adv+cor, P2a r3 adv+cor, P1 r3 adv+cor. Authors idle (resumable): P1 aaaeea25aaef763ea, P2a a64cfd8eaa8b64a3a, P3a a7dc068fb47091bf0, P4d a8190d79eb2c7579c.

## Order 6 author agents (Sonnet 5.5, general-purpose; spawned 16:53Z UTC, expected end 17:28Z UTC)
| agent | purpose | model | started | expected end | state | next action |
|---|---|---|---|---|---|---|
| author-P2d | draft tickets/P2d.md (Wave 1, Tier A (redaction)); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| author-P4a | draft tickets/P4a.md (Wave 1, Tier A money, 3 PRs); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| author-P5a | draft tickets/P5a.md (Wave 1, Tier A); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| author-P0a | draft tickets/P0a.md (Wave 1, Tier B, text only); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| author-P0c | draft tickets/P0c.md (Wave 1, Tier B, text only); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| author-P4b1 | draft tickets/P4b1.md (Wave 2, Tier A money); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| author-P4b2 | draft tickets/P4b2.md (Wave 2, Tier A money); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| author-P4c | draft tickets/P4c.md (Wave 2, Tier A money); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| author-P5b1 | draft tickets/P5b1.md (Wave 2, Tier A); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| author-P5b2 | draft tickets/P5b2.md (Wave 2, Tier B); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| author-P6b1 | draft tickets/P6b1.md (Wave 2, Tier A); brief = scratchpad author-brief.md | sonnet (claude-sonnet-5-5) | 16:53Z | 17:28Z | REPORTED, saved | verify, commit/push, 2 fresh egm reviewers (1 for Tier B) |
| rev5-P4d (resumed author a8190d79eb2c7579c) | apply 40 round 3 findings (resolve report reviews/P4d-round3-resolve.md) to tickets/P4d.md | sonnet (claude-sonnet-5-5) | 17:20Z | 18:00Z | REPORTED, saved | on report: verify, push, round 4 fresh reviewers |
| rev5-P3a (resumed author a7dc068fb47091bf0) | apply round 3 resolve (reviews/P3a-round3-resolve.md): REMOVE --accept-late per order 6(f) | sonnet (claude-sonnet-5-5) | 17:28Z | 18:00Z | REPORTED, saved | on report: verify, push, round 4 |
| rev5-P2a (resumed author a64cfd8eaa8b64a3a) | apply round 3 resolve (reviews/P2a-round3-resolve.md); merge 1a+1b | sonnet (claude-sonnet-5-5) | 17:07Z | +40min | CLOSED, reported 18:25Z, rev 5 committed | on report: verify, push, round 4 |
| r4-P4d-adv | round 4 adversarial review of tickets/P4d.md rev 5 (d12bfa7), egm:egm-design | sonnet (claude-sonnet-5-5) | 17:07Z | +30min | REPORTED, saved | save report, ledger rows |
| r4-P4d-cor | round 4 correctness review of P4d rev 5, egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:07Z | +30min | REPORTED, saved | save report, ledger rows |
| r4-P3a-adv | round 4 adversarial review of tickets/P3a.md rev 5 (60e16a5), egm:egm-design | sonnet (claude-sonnet-5-5) | 17:07Z | +25min | REPORTED, saved reviews/P3a-round4-adversarial.md | save report, ledger rows |
| r4-P3a-cor | round 4 correctness review of P3a rev 5, egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:07Z | +25min | REPORTED, saved | save report, ledger rows |
| r1-P6b1-adv | round 1 adversarial review of tickets/P6b1.md (315ab52), egm:egm-design | sonnet (claude-sonnet-5-5) | 17:07Z | +30min | REPORTED, saved reviews/P6b1-round1-adversarial.md | save report, ledger rows |
| r1-P6b1-cor | round 1 correctness review of P6b1, egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:07Z | +30min | REPORTED, saved reviews/P6b1-round1-correctness.md | save report, ledger rows |
| r1-P4c-adv | round 1 adversarial review of tickets/P4c.md (63549c7), egm:egm-design | sonnet (claude-sonnet-5-5) | 17:07Z | +30min | REPORTED, saved reviews/P4c-round1-adversarial.md | save report, ledger rows |
| r1-P4c-cor | round 1 correctness review of P4c, egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:07Z | +30min | REPORTED, saved reviews/P4c-round1-correctness.md | save report, ledger rows |
| r1-P0a-cor | round 1 single reviewer (Tier B) of tickets/P0a.md (c826f2d), egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:07Z | +30min | REPORTED, saved reviews/P0a-round1-reviewer.md | save report, ledger rows |
| r1-P0c-cor | round 1 single reviewer (Tier B) of tickets/P0c.md (e1ffdb5), egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:07Z | +30min | REPORTED, saved reviews/P0c-round1-reviewer.md | save report, ledger rows |
| r1-P5b2-cor | round 1 single reviewer (Tier B) of tickets/P5b2.md (45fe05b), egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:07Z | +30min | REPORTED, saved reviews/P5b2-round1-reviewer.md | save report, ledger rows |
| rev5-P1 (resumed author aaaeea25aaef763ea) | apply round 3 resolve (reviews/P1-round3-resolve.md) to tickets/P1.md | sonnet (claude-sonnet-5-5) | 17:08Z | +45min | REPORTED, saved | on report: verify, push, round 4 |
| r1-P4b1-adv | round 1 adversarial review of tickets/P4b1.md (15d01fa), egm:egm-design | sonnet (claude-sonnet-5-5) | 17:09Z | +35min | REPORTED, saved reviews/P4b1-round1-adversarial.md | save report, ledger rows |
| r1-P4b1-cor | round 1 correctness review of P4b1 (15d01fa), egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:09Z | +35min | REPORTED, saved | save report, ledger rows |
| r1-P5b1-adv | round 1 adversarial review of tickets/P5b1.md (30fd0e8), egm:egm-design | sonnet (claude-sonnet-5-5) | 17:09Z | +35min | REPORTED, saved | save report, ledger rows |
| r1-P5b1-cor | round 1 correctness review of P5b1 (30fd0e8), egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:09Z | +35min | NOT STARTED (20-agent limit); start when a slot frees | save report, ledger rows |
| r1-P5a-adv | round 1 adversarial review of tickets/P5a.md (def2d2a), egm:egm-design | sonnet (claude-sonnet-5-5) | 17:45Z | +35min | REPORTED, saved | save report, ledger rows |
| r1-P5a-cor | round 1 correctness review of P5a, egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:45Z | +35min | REPORTED, saved | save report, ledger rows |
| r1-P4b2-adv | round 1 adversarial review of tickets/P4b2.md (f2349e3), egm:egm-design | sonnet (claude-sonnet-5-5) | 17:45Z | +35min | REPORTED, saved | save report, ledger rows |
| r1-P4b2-cor | round 1 correctness review of P4b2, egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 17:45Z | +35min | REPORTED, saved | save report, ledger rows |
| probe-gp | model probe: general-purpose, model sonnet | sonnet | now | +2min | REPORTED, see evidence/model-probe.md | record in evidence/model-probe.md |
| probe-design | model probe: egm:egm-design | sonnet | now | +2min | REPORTED, see evidence/model-probe.md | same |
| probe-cod | model probe: egm:egm-codebase-details | sonnet | now | +2min | REPORTED, see evidence/model-probe.md | same |
| probe-haiku | model probe: general-purpose, model haiku | haiku | now | +2min | REPORTED, see evidence/model-probe.md | same |
| r1-P2d-adv | round 1 adversarial review of tickets/P2d.md rev 1, egm:egm-design | sonnet (claude-sonnet-5-5) | 18:00Z | +30min | REPORTED, saved | save report, ledger rows |
| r1-P2d-cor | round 1 correctness review of tickets/P2d.md rev 1, egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 18:00Z | +30min | REPORTED, saved | save report, ledger rows |
| r1-P4a-adv | round 1 adversarial review of tickets/P4a.md rev 1 (bd061b3), egm:egm-design | sonnet (claude-sonnet-5-5) | 18:00Z | +35min | REPORTED, saved | save report, ledger rows |
| r1-P4a-cor | round 1 correctness review of tickets/P4a.md rev 1, egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 18:00Z | +35min | REPORTED, saved | save report, ledger rows |
| r1-P5b1-cor | round 1 correctness review of P5b1 (30fd0e8), egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 18:00Z | +35min | REPORTED, saved | save report, ledger rows |
| rev6-P4d (resumed author a8190d79eb2c7579c) | apply round 4 resolve (reviews/P4d-round4-resolve.md) to tickets/P4d.md | sonnet (claude-sonnet-5-5) | 18:10Z | +40min | REPORTED | on report: verify, push, 2 fresh reviewers (round 5) |
| r4-P2a-adv | round 4 adversarial review of tickets/P2a.md rev 5, egm:egm-design | sonnet (claude-sonnet-5-5) | 18:30Z | +35min | REPORTED, saved | save report, ledger rows |
| r4-P2a-cor | round 4 correctness review of tickets/P2a.md rev 5, egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 18:30Z | +35min | REPORTED, saved | save report, ledger rows |
| rev6-P3a (resumed author a7dc068fb47091bf0) | apply reviews/P3a-round4-resolve.md to tickets/P3a.md (rev 6) | sonnet (claude-sonnet-5-5) | 18:40Z | +40min | REPORTED, saved | on report: verify, commit, push, round-5 reviewers |
| rev2-P4a (new author, sonnet) | apply reviews/P4a-round1-resolve.md to tickets/P4a.md (rev 2) | sonnet (claude-sonnet-5-5) | 18:55Z | +45min | REPORTED, saved | on report: verify, commit, push, round-2 reviewers |
| r4-P1-adv | round 4 adversarial review of tickets/P1.md rev 5 (b13ff07), egm:egm-design | sonnet (claude-sonnet-5-5) | 19:05Z | +40min | REPORTED, saved | save report, ledger rows |
| r4-P1-cor | round 4 correctness review of tickets/P1.md rev 5 (b13ff07), egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | 19:05Z | +40min | REPORTED, saved | save report, ledger rows |
| r5-P4d-adv | round 5 adversarial review of tickets/P4d.md rev 6, egm:egm-design | sonnet (claude-sonnet-5-5) | now | +35min | REPORTED, saved | save report, ledger rows |
| r5-P4d-cor | round 5 correctness review of tickets/P4d.md rev 6, egm:egm-codebase-details | sonnet (claude-sonnet-5-5) | now | +35min | REPORTED, saved | save report, ledger rows |
| rev6-P2a | author rewrite tickets/P2a.md rev 6 from reviews/P2a-round4-resolve.md (continues agent a64cfd8eaa8b64a3a) | sonnet (claude-sonnet-5-5) | now | +30min | REPORTED, saved | verify, explicit add, commit, push, round 5 reviewers |
| rev2-P2d | author rewrite tickets/P2d.md rev 2 from reviews/P2d-round1-resolve.md (new general-purpose agent) | sonnet (claude-sonnet-5-5) | now | +35min | running | verify, explicit add, commit, push, round 2 reviewers |
| r5-P3a-adv | round 5 adversarial review of tickets/egm:egm-design.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| rP3a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | running | save report, ledger rows |
| r5-P3a-cor | round 5 correctness review of tickets/egm:egm-codebase-details.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| rP3a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | running | save report, ledger rows |
| r2-P4a-adv | round 2 adversarial review of tickets/egm:egm-design.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED, saved | save report, ledger rows |
| rP4a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | running | save report, ledger rows |
| r2-P4a-cor | round 2 correctness review of tickets/egm:egm-codebase-details.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED, saved | save report, ledger rows |
| rP4a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | running | save report, ledger rows |
| r5-P2a-adv | round 5 adversarial review of tickets/egm:egm-design.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| rP2a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | running | save report, ledger rows |
| r5-P2a-cor | round 5 correctness review of tickets/egm:egm-codebase-details.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| rP2a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | running | save report, ledger rows |
| rev7-P4d | author rewrite tickets/P4d.md rev 7 from reviews/P4d-round5-resolve.md | sonnet (claude-sonnet-5-5) | now | +50min | running | verify, commit, round-6 reviewers |
| rev6-P1 | author rewrite tickets/P1.md rev 6 from reviews/P1-round4-resolve.md | sonnet (claude-sonnet-5-5) | now | +60min | running | verify, explicit add, commit, push, round 5 reviewers |
| rev3-P4a | author rewrite tickets/P4a.md rev 3 from reviews/P4a-round2-resolve.md | sonnet (claude-sonnet-5-5) | now | +50min | running | verify, explicit add, commit, push, round 3 reviewers |
| r2-P2d-adv | round 2 adversarial review of tickets/P2d.md (head d6be4de) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| r2-P2d-cor | round 2 correctness review of tickets/P2d.md (head d6be4de) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| rev7-P3a | author rewrite tickets/P3a.md rev 7 from reviews/P3a-round5-resolve.md | sonnet (claude-sonnet-5-5) | now | +50min | running | verify, explicit add, commit, push, round 6 reviewers |
| rev7-P2a | author rewrite tickets/P2a.md rev 7 from reviews/P2a-round5-resolve.md | sonnet (claude-sonnet-5-5) | now | +60min | REPORTED | verify, explicit add, commit, push, round 6 reviewers |
| r6-P4d-adv | round 6 adversarial review of tickets/P4d.md rev 7 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r6-P4d-cor | round 6 correctness review of tickets/P4d.md rev 7 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r5-P1-adv | round 5 adversarial review of tickets/P1.md rev 6 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r5-P1-cor | round 5 correctness review of tickets/P1.md rev 6 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| rev3-P2d | author rewrite tickets/P2d.md rev 3 from reviews/P2d-round2-resolve.md | sonnet (claude-sonnet-5-5) | now | +50min | running | verify, explicit add, commit, push, round 3 reviewers |
| r3-P4a-adv | round 3 adversarial review of tickets/P4a.md rev 3 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r3-P4a-cor | round 3 correctness review of tickets/P4a.md rev 3 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r6-P3a-adv | round 6 adversarial review of tickets/P3a.md rev 7 (3c9fe6a) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r6-P3a-cor | round 6 correctness review of tickets/P3a.md rev 7 (3c9fe6a) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| rev8-P4d | author P4d ticket rev 8 (round 6 resolve f360ed0) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | verify, explicit add, commit, push, launch round 7 |
| rev4-P4a | author P4a ticket rev 4 (round 3 resolve 9f1ea43) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | verify, explicit add, commit, push, launch round 4 |
| r6-P2a-adv | round 6 adversarial review of tickets/P2a.md rev 7 (bd846f2) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r6-P2a-cor | round 6 correctness review of tickets/P2a.md rev 7 (bd846f2) | sonnet (claude-sonnet-5-5) | now | +45min | running | save report, ledger rows |
| rev8-P3a | author P3a ticket rev 8 (round 6 resolve c19b7e7) | sonnet (claude-sonnet-5-5) | now | +50min | running | verify, explicit add, commit, push, launch round 7 |
| rev7-P1 | author P1 ticket rev 7 (round 5 resolve) | sonnet (claude-sonnet-5-5) | now | +50min | running | verify, explicit add, commit, push, launch round 6 |
| r7-P4d-adv | round 7 adversarial review of tickets/P4d.md rev 8 | sonnet (claude-sonnet-5-5) | now | +45min | running | save report, ledger rows |
| r7-P4d-cor | round 7 correctness review of tickets/P4d.md rev 8 | sonnet (claude-sonnet-5-5) | now | +45min | running | save report, ledger rows |
| r4-P4a-adv | round 4 adversarial review of tickets/P4a.md rev 4 | sonnet (claude-sonnet-5-5) | now | +45min | running | save report, ledger rows |
| r4-P4a-cor | round 4 correctness review of tickets/P4a.md rev 4 | sonnet (claude-sonnet-5-5) | now | +45min | running | save report, ledger rows |
