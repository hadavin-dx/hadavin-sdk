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
| rev2-P2d | author rewrite tickets/P2d.md rev 2 from reviews/P2d-round1-resolve.md (new general-purpose agent) | sonnet (claude-sonnet-5-5) | now | +35min | CLOSED-STALE (no live agent; swept 03:30Z) | verify, explicit add, commit, push, round 2 reviewers |
| r5-P3a-adv | round 5 adversarial review of tickets/egm:egm-design.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| rP3a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | CLOSED-STALE (no live agent; swept 03:30Z) | save report, ledger rows |
| r5-P3a-cor | round 5 correctness review of tickets/egm:egm-codebase-details.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| rP3a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | CLOSED-STALE (no live agent; swept 03:30Z) | save report, ledger rows |
| r2-P4a-adv | round 2 adversarial review of tickets/egm:egm-design.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED, saved | save report, ledger rows |
| rP4a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | CLOSED-STALE (no live agent; swept 03:30Z) | save report, ledger rows |
| r2-P4a-cor | round 2 correctness review of tickets/egm:egm-codebase-details.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED, saved | save report, ledger rows |
| rP4a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | CLOSED-STALE (no live agent; swept 03:30Z) | save report, ledger rows |
| r5-P2a-adv | round 5 adversarial review of tickets/egm:egm-design.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| rP2a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | CLOSED-STALE (no live agent; swept 03:30Z) | save report, ledger rows |
| r5-P2a-cor | round 5 correctness review of tickets/egm:egm-codebase-details.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| rP2a-- | round   review of tickets/.md (head 60fedf6) | sonnet (claude-sonnet-5-5) | now | +40min | CLOSED-STALE (no live agent; swept 03:30Z) | save report, ledger rows |
| rev7-P4d | author rewrite tickets/P4d.md rev 7 from reviews/P4d-round5-resolve.md | sonnet (claude-sonnet-5-5) | now | +50min | CLOSED-STALE (no live agent; swept 03:30Z) | verify, commit, round-6 reviewers |
| rev6-P1 | author rewrite tickets/P1.md rev 6 from reviews/P1-round4-resolve.md | sonnet (claude-sonnet-5-5) | now | +60min | CLOSED-STALE (no live agent; swept 03:30Z) | verify, explicit add, commit, push, round 5 reviewers |
| rev3-P4a | author rewrite tickets/P4a.md rev 3 from reviews/P4a-round2-resolve.md | sonnet (claude-sonnet-5-5) | now | +50min | CLOSED-STALE (no live agent; swept 03:30Z) | verify, explicit add, commit, push, round 3 reviewers |
| r2-P2d-adv | round 2 adversarial review of tickets/P2d.md (head d6be4de) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| r2-P2d-cor | round 2 correctness review of tickets/P2d.md (head d6be4de) | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | save report, ledger rows |
| rev7-P3a | author rewrite tickets/P3a.md rev 7 from reviews/P3a-round5-resolve.md | sonnet (claude-sonnet-5-5) | now | +50min | CLOSED-STALE (no live agent; swept 03:30Z) | verify, explicit add, commit, push, round 6 reviewers |
| rev7-P2a | author rewrite tickets/P2a.md rev 7 from reviews/P2a-round5-resolve.md | sonnet (claude-sonnet-5-5) | now | +60min | REPORTED | verify, explicit add, commit, push, round 6 reviewers |
| r6-P4d-adv | round 6 adversarial review of tickets/P4d.md rev 7 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r6-P4d-cor | round 6 correctness review of tickets/P4d.md rev 7 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r5-P1-adv | round 5 adversarial review of tickets/P1.md rev 6 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r5-P1-cor | round 5 correctness review of tickets/P1.md rev 6 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| rev3-P2d | author rewrite tickets/P2d.md rev 3 from reviews/P2d-round2-resolve.md | sonnet (claude-sonnet-5-5) | now | +50min | REPORTED | verify, explicit add, commit, push, round 3 reviewers |
| r3-P4a-adv | round 3 adversarial review of tickets/P4a.md rev 3 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r3-P4a-cor | round 3 correctness review of tickets/P4a.md rev 3 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r6-P3a-adv | round 6 adversarial review of tickets/P3a.md rev 7 (3c9fe6a) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r6-P3a-cor | round 6 correctness review of tickets/P3a.md rev 7 (3c9fe6a) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| rev8-P4d | author P4d ticket rev 8 (round 6 resolve f360ed0) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | verify, explicit add, commit, push, launch round 7 |
| rev4-P4a | author P4a ticket rev 4 (round 3 resolve 9f1ea43) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | verify, explicit add, commit, push, launch round 4 |
| r6-P2a-adv | round 6 adversarial review of tickets/P2a.md rev 7 (bd846f2) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r6-P2a-cor | round 6 correctness review of tickets/P2a.md rev 7 (bd846f2) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| rev8-P3a | author P3a ticket rev 8 (round 6 resolve c19b7e7) | sonnet (claude-sonnet-5-5) | now | +50min | REPORTED | verify, explicit add, commit, push, launch round 7 |
| rev7-P1 | author P1 ticket rev 7 (round 5 resolve) | sonnet (claude-sonnet-5-5) | now | +50min | REPORTED | verify, explicit add, commit, push, launch round 6 |
| r7-P4d-adv | round 7 adversarial review of tickets/P4d.md rev 8 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r7-P4d-cor | round 7 correctness review of tickets/P4d.md rev 8 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r4-P4a-adv | round 4 adversarial review of tickets/P4a.md rev 4 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r4-P4a-cor | round 4 correctness review of tickets/P4a.md rev 4 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| rev8-P2a | author P2a ticket rev 8 (round 6 resolve) | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r3-P2d-adv | round 3 adversarial review of tickets/P2d.md rev 3 | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r3-P2d-cor | round 3 correctness review of tickets/P2d.md rev 3 | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r7-P3a-adv | round 7 review of tickets/P3a.md rev 8 | sonnet (claude-sonnet-5-5) | now | +45min | now | REPORTED | collect, save |
| r7-P3a-cor | round 7 review of tickets/P3a.md rev 8 | sonnet (claude-sonnet-5-5) | now | +45min | now | REPORTED | collect, save |
| rev5-P4a | author P4a ticket rev 5 (round 4 resolve d82bf36) | sonnet (claude-sonnet-5-5) | now | +45min | now | REPORTED | collect, verify, commit, round 5 |
| rev4-P2d | author P2d ticket rev 4 (round 3 resolve 0cdc5ab) | sonnet (claude-sonnet-5-5) | now | +60min | now | REPORTED | collect, verify, commit, round 4 |
| r6-P1-adv | round 6 review of tickets/P1.md rev 7 (99828b6) | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r6-P1-cor | round 6 review of tickets/P1.md rev 7 (99828b6) | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r7-P2a-adv | round 7 review of tickets/P2a.md rev 8 | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r7-P2a-cor | round 7 review of tickets/P2a.md rev 8 | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r5-P4a-adv | round 5 review of tickets/P4a.md rev 5 | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r5-P4a-cor | round 5 review of tickets/P4a.md rev 5 | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r4-P2d-adv | round 4 review of tickets/P2d.md rev 4 (egm:egm-design) | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r4-P2d-cor | round 4 review of tickets/P2d.md rev 4 (egm:egm-codebase-details) | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| rev8-P1 | author P1 ticket next revision (round resolve applied) | sonnet (claude-sonnet-5-5) | now | +60min | REPORTED | verify, commit, push, launch next round |
| rev9-P2a | author P2a ticket next revision (round resolve applied) | sonnet (claude-sonnet-5-5) | now | +60min | REPORTED | verify, commit, push, launch next round |
| rev6-P4a | author P4a ticket next revision (round resolve applied) | sonnet (claude-sonnet-5-5) | now | +60min | REPORTED | verify, commit, push, launch next round |
| rev5-P2d | author P2d ticket next revision (round resolve applied) | sonnet (claude-sonnet-5-5) | now | +60min | REPORTED | verify, commit, push, launch next round |
| rev9-P3a | author P3a ticket next revision (round resolve applied) | sonnet (claude-sonnet-5-5) | now | +60min | REPORTED | verify, commit, push, launch next round |
| rev9-P4d | author P4d ticket next revision (round resolve applied) | sonnet (claude-sonnet-5-5) | now | +60min | REPORTED | verify, commit, push, launch next round |
| r6-P4a-adv | round 6 review of tickets/P4a.md rev 6 (egm:egm-design) | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r6-P4a-cor | round 6 review of tickets/P4a.md rev 6 (egm:egm-codebase-details) | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r5-P2d-adv | round 5 review of tickets/P2d.md rev 5 (egm:egm-design) | sonnet (claude-sonnet-5-5) | now | +50min | now | REPORTED | collect, save, resolve |
| r5-P2d-cor | round 5 review of tickets/P2d.md rev 5 (egm:egm-codebase-details) | sonnet (claude-sonnet-5-5) | now | +50min | now | CLOSED-STALE (no live agent; swept 03:30Z) | collect, save, resolve |
| r7-P1-adv | round 7 adversarial review of tickets/P1.md rev 8 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r7-P1-cor | round 7 correctness review of tickets/P1.md rev 8 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r1-LK-adv | round 1 adversarial review of designs/lookalike-leak.md | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r1-LK-cor | round 1 correctness review of designs/lookalike-leak.md | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r8-P3a-adv | round 8 review of tickets/P3a.md rev 9 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r8-P3a-cor | round 8 review of tickets/P3a.md rev 9 | sonnet (claude-sonnet-5-5) | now | +45min | CLOSED-STALE (no live agent; swept 03:30Z) | save report, ledger rows |
| r2-LK-adv | round 2 adversarial review of designs/lookalike-leak.md draft 2 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r2-LK-cor | round 2 correctness review of designs/lookalike-leak.md draft 2 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r2-LK-resolve | egm-resolve of lookalike round 2 reports -> designs/lookalike-leak.md draft 3 | opus (claude-opus-5-5) | now | +45min | REPORTED | verify, commit, push |
| r9-P1-author | P1 rev 9 author from reviews/P1-round7-resolve.md | sonnet (claude-sonnet-5-5) | now | +60min | REPORTED | verify, commit, push, then round 8 reviewers |
| r8-P1-adv | round 8 adversarial review of tickets/P1.md rev 9 (head 74a6e26) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r8-P1-cor | round 8 correctness review of tickets/P1.md rev 9 (head 74a6e26) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r3-LK-adv | round 3 adversarial review of designs/lookalike-leak.md draft 3 (head 74a6e26) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r3-LK-cor | round 3 correctness review of designs/lookalike-leak.md draft 3 (head 74a6e26) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r8-P1-resolve | egm-resolve P1 round 8 (ADV-R8-1..11, COR-R8-1..12) | opus (claude-opus-5-5) | now | +45min | REPORTED | verify, commit, push |
| r3-LK-resolve | egm-resolve look-alike round 3 (ADV-LK3-1..13, COR-LK3-1..10) -> draft 4 | opus (claude-opus-5-5) | now | +45min | REPORTED | verify, commit, push |
| r10-P1-author | P1 rev 10 author from reviews/P1-round8-resolve.md | sonnet (claude-sonnet-5-5) | now | +60min | REPORTED | verify, commit, push, then round 9 reviewers |
| r4-LK-adv | round 4 adversarial review of designs/lookalike-leak.md draft 4 (head bdab309) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r4-LK-cor | round 4 correctness review of designs/lookalike-leak.md draft 4 (head bdab309) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r4-LK-resolve | round 4 resolve of designs/lookalike-leak.md (draft 5), reviews/lookalike-round4-*.md | opus (claude-opus-5-5) | 22:37Z | +50min | REPORTED | verify, push, round 5 reviewers |
| r9-P1-adv | round 9 adversarial review of tickets/P1.md rev 10 (head 82b477e) | sonnet (claude-sonnet-5-5) | 22:38Z | +45min | REPORTED | save report, ledger rows |
| r9-P1-cor | round 9 correctness review of tickets/P1.md rev 10 (head 82b477e) | sonnet (claude-sonnet-5-5) | 22:38Z | +45min | REPORTED-INCOMPLETE (context compacted, no usable findings; re-run as r9b) | save report, ledger rows |
| r9b-P1-cor | round 9 correctness re-run of tickets/P1.md rev 10 (head 82b477e), narrower scope | sonnet (claude-sonnet-5-5) | 22:49Z | +40min | REPORTED | save report, ledger rows |
| r5-LK-adv | round 5 adversarial review of designs/lookalike-leak.md draft 5 | sonnet (claude-sonnet-5-5) | 22:51Z | +45min | REPORTED | save report, ledger rows |
| r5-LK-cor | round 5 correctness review of designs/lookalike-leak.md draft 5 | sonnet (claude-sonnet-5-5) | 22:51Z | +45min | REPORTED | save report, ledger rows |
| r6-P4a-resolve | round 6 resolve of tickets/P4a.md using reviews/P4a-round6-adversarial.md + -correctness.md | opus (claude-opus-5-5) | 22:52Z | +45min | REPORTED | verify, push, rev author |
| r9-P1-resolve | round 9 resolve of tickets/P1.md rev 10 (adv ADV-R9-1..19, cor COR-R9-1..10) | opus (claude-opus-5-5) | 22:56Z | +50min | REPORTED | verify, push, rev 11 author |
| rev7-P4a-author | author rewrite tickets/P4a.md rev 7 from reviews/P4a-round6-resolve.md | sonnet (claude-sonnet-5-5) | 22:58Z | +40min | REPORTED | verify, push, round 7 reviewers |
| r5-LK-resolve | round 5 resolve of designs/lookalike-leak.md (draft 6) incl. order 13 | opus (claude-opus-5-5) | 23:00Z | +50min | REPORTED | verify, push, round 6 reviewers |
| rev11-P1-author | author rewrite tickets/P1.md rev 11 from reviews/P1-round9-resolve.md | sonnet (claude-sonnet-5-5) | 23:06Z | +45min | REPORTED | verify, push, round 10 reviewers |
| r6-LK-adv | round 6 adversarial review of designs/lookalike-leak.md draft 6 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r6-LK-cor | round 6 correctness review of designs/lookalike-leak.md draft 6 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED-INCOMPLETE (reviewer lost context) | save report, ledger rows |
| r10-P1-adv | round 10 adversarial review of tickets/P1.md rev 11 (d055d28) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r10-P1-cor | round 10 correctness review of tickets/P1.md rev 11 (d055d28) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r7-P4a-adv | round 7 adversarial review of tickets/P4a.md rev 7 (b782b8d) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r7-P4a-cor | round 7 correctness review of tickets/P4a.md rev 7 (b782b8d) | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED-INCOMPLETE (reviewer lost context; 5 nits lost) | save report, ledger rows |
| r6-LK-resolve | round 6 resolve of designs/lookalike-leak.md (draft 7) using reviews/lookalike-round6-*.md | opus (claude-opus-5-5) | now | +50min | REPORTED | verify, push, round 7 reviewers |
| r10-P1-resolve | round 10 resolve of tickets/P1.md rev 11 using reviews/P1-round10-*.md | opus (claude-opus-5-5) | now | +50min | REPORTED | verify, push, rev 12 author |
| r7-P4a-resolve | round 7 resolve of tickets/P4a.md rev 7 using reviews/P4a-round7-*.md | opus (claude-opus-5-5) | now | +50min | REPORTED | verify, push, rev 8 author, round 8 reviewers |
| rev8-P4a-author | author rewrite tickets/P4a.md rev 8 from reviews/P4a-round7-resolve.md | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | verify, push, round 8 reviewers |
| r7-LK-adv | round 7 adversarial review of designs/lookalike-leak.md draft 7 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| r7-LK-cor | round 7 correctness review of designs/lookalike-leak.md draft 7 | sonnet (claude-sonnet-5-5) | now | +45min | REPORTED | save report, ledger rows |
| rev12-P1-author | author rewrite tickets/P1.md rev 12 from reviews/P1-round10-resolve.md | sonnet (claude-sonnet-5-5) | now | +40min | REPORTED | verify, push, round 11 reviewers |
| r7-LK-resolve | round 7 resolve of designs/lookalike-leak.md (draft 8) using reviews/lookalike-round7-*.md and order 14 | opus (claude-opus-5-5) | 23:56Z | +50min | REPORTED | verify, push, round 8 reviewers |
| r8-P4a-adv | round 8 adversarial review of tickets/P4a.md rev 8 (head d12b498) | sonnet (claude-sonnet-5-5) | 00:01Z | +45min | REPORTED | save report, ledger rows |
| r8-P4a-cor | round 8 correctness review of tickets/P4a.md rev 8 (head d12b498), FULL | sonnet (claude-sonnet-5-5) | 00:01Z | +45min | REPORTED | save report, ledger rows |
| r11-P1-adv | round 11 adversarial review of tickets/P1.md rev 12 (commit 0cb3f69) | sonnet (claude-sonnet-5-5) | 00:05Z | +45min | REPORTED | save report, ledger rows |
| r11-P1-cor | round 11 correctness review of tickets/P1.md rev 12 (commit 0cb3f69) | sonnet (claude-sonnet-5-5) | 00:05Z | +45min | REPORTED | save report, ledger rows |
| r8-P4a-resolve | round 8 resolve of tickets/P4a.md rev 8 (ADV-R8-1..7, COR-R8-1..6) | opus (claude-opus-5-5) | 00:09Z | +50min | REPORTED | verify, rev 9 author, round 9 reviewers |
| r11-P1-resolve | round 11 resolve of tickets/P1.md rev 12 (ADV-R11-1..4, COR-R11-1..5) | opus (claude-opus-5-5) | 00:12Z | +50min | LOST (container restart; relaunch) | verify, rev 13 author, round 12 reviewers |
| r8-LK-adv | round 8 adversarial review of designs/lookalike-leak.md draft 8 (head 2ca11dd) | sonnet (claude-sonnet-5-5) | 00:18Z | +45min | REPORTED | save report, ledger rows |
| r8-LK-cor | round 8 correctness review of designs/lookalike-leak.md draft 8 (head 2ca11dd) | sonnet (claude-sonnet-5-5) | 00:18Z | +45min | LOST (container restart 00:25Z; relaunch) | save report, ledger rows |
| rev9-P4a-author | author rewrite tickets/P4a.md rev 9 from reviews/P4a-round8-resolve.md | sonnet (claude-sonnet-5-5) | 00:20Z | +40min | LOST (container restart; relaunch) | verify, push, round 9 reviewers |
| r8b-LK-cor | round 8 correctness review of designs/lookalike-leak.md draft 8 (relaunch after restart) | sonnet | 00:30Z | +45min | REPORTED | save report, ledger rows |
| r11b-P1-resolve | round 11 resolve of tickets/P1.md (relaunch after restart) | opus | 00:30Z | +60min | REPORTED | verify, rev 13 author, round 12 reviewers |
| rev9b-P4a-author | P4a rev 9 author (relaunch after restart; partial edits reverted) | sonnet | 00:30Z | +45min | REPORTED | verify, push, round 9 reviewers |
| rev13-P1-author | author rewrite tickets/P1.md rev 13 from reviews/P1-round11-resolve.md | sonnet | 00:42Z | +45min | REPORTED | verify, push, round 12 reviewers |
| r8-LK-resolve | Opus egm-resolve of LK draft 8 over round 8 adv+cor reports -> draft 9 | opus | 00:50Z | +60min | REPORTED | verify, push, round 9 reviewers |
| r12-P1-adv | P1 round 12 adversarial review of tickets/P1.md rev 13 (3f0236f) | sonnet | 00:58Z | +45min | REPORTED | save report, ledger rows |
| r12-P1-cor | P1 round 12 correctness review of tickets/P1.md rev 13 (3f0236f) | sonnet | 00:58Z | +45min | REPORTED | save report, ledger rows |
| r9-P4a-adv | P4a round 9 adversarial review of tickets/P4a.md rev 9 (a01a8b2) | sonnet | 01:10Z | +45min | REPORTED | save report, ledger rows |
| r9-P4a-cor | P4a round 9 correctness review of tickets/P4a.md rev 9 (a01a8b2) | sonnet | 01:10Z | +45min | REPORTED | save report, ledger rows |
| r9-LK-adv | LK round 9 adversarial review of designs/lookalike-leak.md draft 9 (871dc07) | sonnet | 01:25Z | +45min | REPORTED | save report, ledger rows |
| r9-LK-cor | LK round 9 correctness review of designs/lookalike-leak.md draft 9 (871dc07) | sonnet | 01:25Z | +45min | REPORTED | save report, ledger rows |
| r12-P1-resolve | Opus egm-resolve of P1 rev 13 over round 12 adv+cor reports -> rev 14 input | opus | 01:35Z | +60min | REPORTED | verify, push, rev 14 author, round 13 reviewers |
| r9-P4a-resolve | Opus egm-resolve of P4a rev 9 over round 9 adv+cor -> rev 10 input | opus | 00:55Z | +60min | REPORTED | verify, push, rev 10 author, round 10 reviewers |
| r9-LK-resolve | Opus egm-resolve of LK draft 9 over round 9 adv+cor -> draft 10 input | opus | 01:03Z | +60min | REPORTED | verify, push, draft 10, round 10 reviewers |
| rev14-P1-author | author rewrite tickets/P1.md rev 14 from reviews/P1-round12-resolve.md | sonnet | 01:04Z | +45min | REPORTED | verify, push, round 13 reviewers |
| rev10-P4a-author | author rewrite tickets/P4a.md rev 10 from reviews/P4a-round9-resolve.md | sonnet | 01:05Z | +45min | REPORTED | verify, push, round 10 reviewers |
| draft10-LK-author | Opus draft 10 of designs/lookalike-leak.md from reviews/lookalike-round9-resolve.md | opus | 01:13Z | +50min | REPORTED | verify, push, round 10 reviewers |
| r13-P1-adv | P1 round 13 adversarial review of tickets/P1.md rev 14 (8b5d849) | sonnet | 01:15Z | +45min | REPORTED | save report, ledger rows |
| r13-P1-cor | P1 round 13 correctness review of tickets/P1.md rev 14 (8b5d849) | sonnet | 01:15Z | +45min | REPORTED | save report, ledger rows |
| r10-P4a-adv | P4a round 10 adversarial review of tickets/P4a.md rev 10 (94c4c82) | sonnet | 01:20Z | +45min | REPORTED | save report, ledger |
| r10-P4a-cor | P4a round 10 correctness review of tickets/P4a.md rev 10 (94c4c82) | sonnet | 01:20Z | +45min | REPORTED | save report, ledger |
| r10-LK-adv | LK round 10 adversarial review of designs/lookalike-leak.md draft 10 (8cc31a9) | sonnet | 01:21Z | +45min | REPORTED | save report, ledger |
| r10-LK-cor | LK round 10 correctness review of draft 10 (8cc31a9) | sonnet | 01:21Z | +45min | REPORTED | save report, ledger |
| r13-P1-resolve | Opus egm-resolve of P1 rev 14 over round 13 adv+cor reports -> rev 15 input | opus | 01:24Z | +60min | REPORTED | verify, push, rev 15 author, round 14 reviewers |
| rev15-P1-author | Sonnet author: apply P1 round 13 resolve to tickets/P1.md -> rev 15 | sonnet | 01:29Z | +50min | REPORTED | verify commit, register r14 reviewers |
| r14-P1-adv | egm-design adversarial round 14 on tickets/P1.md rev 15 (afbaac9) | sonnet | 01:36Z | +40min | REPORTED | save report, ledger |
| r14-P1-cor | egm-codebase-details correctness round 14 on tickets/P1.md rev 15 (afbaac9) | sonnet | 01:36Z | +40min | REPORTED | save report, ledger |
| r10-P4a-resolve | Opus resolve of P4a r10 adv+cor -> reviews/P4a-round10-resolve.md | opus | 01:37Z | +45min | REPORTED | verify, then rev 11 author |
| r10-LK-resolve | Opus resolve of LK r10 adv+cor -> reviews/LK-round10-resolve.md | opus | 01:37Z | +45min | REPORTED | verify, then draft 11 author |
| r14-P1-resolve | Opus resolve of P1 r14 adv+cor -> reviews/P1-round14-resolve.md | opus | 01:45Z | +45min | REPORTED | verify, then rev 16 author |
| rev11-P4a-author | Sonnet author: apply P4a r10 resolve to tickets/P4a.md -> rev 11 | sonnet | 01:47Z | +60min | REPORTED | verify commit, r11 reviewers |
| r8-P2a-adv | round 8 adversarial P2a rev 9 (order 16: older package, round count 1 of 3 from now) | sonnet | 01:51Z | +45min | REPORTED | save report, ledger |
| r8-P2a-cor | round 8 correctness P2a rev 9 (order 16: older package, round count 1 of 3 from now) | sonnet | 01:51Z | +45min | REPORTED | save report, ledger |
| r8-P4d-adv | round 8 adversarial P4d rev 9 (order 16: older package, round count 1 of 3 from now) | sonnet | 01:51Z | +45min | REPORTED | save report, ledger |
| r8-P4d-cor | round 8 correctness P4d rev 9 (order 16: older package, round count 1 of 3 from now) | sonnet | 01:51Z | +45min | REPORTED | save report, ledger |
| r8-P3a-cor2 | round 8 correctness P3a rev 9 (rerun, first run lost) (order 16: older package, round count 1 of 3 from now) | sonnet | 01:51Z | +45min | REPORTED | save report, ledger |
| r5-P2d-cor2 | round 5 correctness P2d rev 5 (rerun, first run lost) (order 16: older package, round count 1 of 3 from now) | sonnet | 01:51Z | +45min | REPORTED | save report, ledger |
| draft11-LK-author | Sonnet author: apply LK r10 resolve to designs/lookalike-leak.md -> draft 11 (FINAL, then frozen per order 16) | sonnet | 01:52Z | +60min | REPORTED | verify commit; freeze |
| rev16-P1-author | Sonnet author: apply reviews/P1-round14-resolve.md to tickets/P1.md -> revision 16 (FINAL; then FROZEN per order 16) | sonnet | 01:58Z | +60min | REPORTED | verify commit; six-copy x6; recount; freeze |
| r11-P4a-adv | round 11 adversarial P4a rev 11 (4fff3cc) (order 16: last review round before final resolve) | sonnet | 01:58Z | +45min | REPORTED | save report, ledger |
| r11-P4a-cor | round 11 correctness P4a rev 11 (4fff3cc) | sonnet | 01:58Z | +45min | REPORTED | save report, ledger |
| r8-P4d-resolve | Opus egm-resolve of round reviews for P4d rev 9 (order 16: older package, round 1 of 3) | opus | 01:59Z | +45min | REPORTED | save nothing (agent writes reviews/*-resolve.md); commit; launch author |
| r8-P3a-resolve | Opus egm-resolve of round reviews for P3a rev 9 (order 16: older package, round 1 of 3) | opus | 01:59Z | +45min | REPORTED | save nothing (agent writes reviews/*-resolve.md); commit; launch author |
| r5-P2d-resolve | Opus egm-resolve of round reviews for P2d rev 5 (order 16: older package, round 1 of 3) | opus | 01:59Z | +45min | REPORTED | save nothing (agent writes reviews/*-resolve.md); commit; launch author |
| r8-P2a-resolve | Opus egm-resolve of P2a r8 reviews (rev 9) (order 16: round 1 of 3) | opus | 01:59Z | +45min | REPORTED | commit; launch author |
| r11-P4a-resolve | Opus egm-resolve of P4a r11 reviews (rev 11) -> then final rev 12 and FROZEN | opus | 02:04Z | +45min | REPORTED | commit; launch rev 12 author |
| rev10-P4d-author | Sonnet author: apply reviews/P4d-round8-resolve.md to tickets/P4d.md -> revision 10 (order 16: round 1 of 3 done) | sonnet | 02:05Z | +60min | REPORTED | verify commit, recount |
| rev10-P3a-author | Sonnet author: apply reviews/P3a-round8-resolve.md to tickets/P3a.md -> revision 10 (order 16: round 1 of 3 done) | sonnet | 02:06Z | +60min | REPORTED | verify commit, recount |
| rev6-P2d-author | Sonnet author: apply reviews/P2d-round5-resolve.md + frozen designs/lookalike-leak.md draft 11 to tickets/P2d.md -> revision 6 | sonnet | 02:06Z | +90min | REPORTED | verify commit, recount |
| rev10-P2a-author | Sonnet author: apply reviews/P2a-round8-resolve.md to tickets/P2a.md -> revision 10 (order 16: round 1 of 3 done) | sonnet | 02:20Z | +60min | REPORTED | verify commit, recount |
| rev12-P4a-author | Sonnet author: apply reviews/P4a-round11-resolve.md to tickets/P4a.md -> revision 12 FINAL (order 16/17: then FROZEN) | sonnet | 02:32Z | +60min | REPORTED | verify commit, recount |
| bs-P1-adv | build-start review (order 20) of frozen tickets/P1.md, egm:*, read-only | sonnet | 02:31Z | +45min | REPORTED | save report as reviews/P1-buildstart-adv.md; then ONE resolve |
| bs-P1-cor | build-start review (order 20) of frozen tickets/P1.md, egm:*, read-only | sonnet | 02:31Z | +45min | REPORTED | save report as reviews/P1-buildstart-cor.md; then ONE resolve |
| bs-P3a-adv | build-start review (order 20) of frozen tickets/P3a.md, egm:*, read-only | sonnet | 02:31Z | +45min | REPORTED | save report as reviews/P3a-buildstart-adv.md; then ONE resolve |
| bs-P3a-cor | build-start review (order 20) of frozen tickets/P3a.md, egm:*, read-only | sonnet | 02:31Z | +45min | REPORTED | save report as reviews/P3a-buildstart-cor.md; then ONE resolve |
| bs-P4d-adv | build-start review (order 20) of frozen tickets/P4d.md, egm:*, read-only | sonnet | 02:31Z | +45min | REPORTED | save report as reviews/P4d-buildstart-adv.md; then ONE resolve |
| bs-P4d-cor | build-start review (order 20) of frozen tickets/P4d.md, egm:*, read-only | sonnet | 02:31Z | +45min | REPORTED | save report as reviews/P4d-buildstart-cor.md; then ONE resolve |
| bs-P2a-adv | build-start review (order 20) of frozen tickets/P2a.md, egm:*, read-only | sonnet | 02:31Z | +45min | REPORTED | save report as reviews/P2a-buildstart-adv.md; then ONE resolve |
| bs-P2a-cor | build-start review (order 20) of frozen tickets/P2a.md, egm:*, read-only | sonnet | 02:31Z | +45min | REPORTED | save report as reviews/P2a-buildstart-cor.md; then ONE resolve |
| bs-P4a-adv | build-start review (order 20) of frozen tickets/P4a.md, egm:*, read-only | sonnet | 02:31Z | +45min | REPORTED | save report as reviews/P4a-buildstart-adv.md; then ONE resolve |
| bs-P4a-cor | build-start review (order 20) of frozen tickets/P4a.md, egm:*, read-only | sonnet | 02:31Z | +45min | REPORTED | save report as reviews/P4a-buildstart-cor.md; then ONE resolve |
| res1-P4b1 | Opus egm-resolve of round-1 reviews of tickets/P4b1.md (order 20 item 6) | opus | 02:32Z | +40min | REPORTED | commit report; launch revision author |
| res1-P4b2 | Opus egm-resolve of round-1 reviews of tickets/P4b2.md (order 20 item 6) | opus | 02:32Z | +40min | REPORTED | commit report; launch revision author |
| res1-P4c | Opus egm-resolve of round-1 reviews of tickets/P4c.md (order 20 item 6) | opus | 02:32Z | +40min | REPORTED | commit report; launch revision author |
| res1-P6b1 | Opus egm-resolve of round-1 reviews of tickets/P6b1.md (order 20 item 6) | opus | 02:32Z | +40min | REPORTED | commit report; launch revision author |
| res1-P5b2 | Opus egm-resolve of round-1 reviews of tickets/P5b2.md (order 20 item 6) | opus | 02:32Z | +40min | REPORTED | commit report; launch revision author |
| draft-P5b3 | Opus first draft of tickets/P5b3.md (order 20 item 6, missing v1 ticket) | opus | 02:32Z | +60min | REPORTED | verify commit; then round 1 reviewers |
| draft-P5b4 | Opus first draft of tickets/P5b4.md (order 20 item 6, missing v1 ticket) | opus | 02:32Z | +60min | REPORTED | verify commit; then round 1 reviewers |
| draft-P5b5 | Opus first draft of tickets/P5b5.md (order 20 item 6, missing v1 ticket) | opus | 02:32Z | +60min | running | verify commit; then round 1 reviewers |
| draft-P5c | Opus first draft of tickets/P5c.md (order 20 item 6, missing v1 ticket) | opus | 02:32Z | +60min | QUEUED (agent limit 20; launch when a slot frees) | verify commit; then round 1 reviewers |
| draft-P6a | Opus first draft of tickets/P6a.md (order 20 item 6, missing v1 ticket) | opus | 02:32Z | +60min | REPORTED | verify commit; then round 1 reviewers |
| draft-P6b2 | Opus first draft of tickets/P6b2.md (order 20 item 6, missing v1 ticket) | opus | 02:32Z | +60min | REPORTED | verify commit; then round 1 reviewers |
| draft-P8a | Opus first draft of tickets/P8a.md (order 20 item 6, missing v1 ticket) | opus | 02:32Z | +60min | REPORTED | verify commit; then round 1 reviewers |
| draft-P8b | Opus first draft of tickets/P8b.md (order 20 item 6, missing v1 ticket) | opus | 02:32Z | +60min | REPORTED | verify commit; then round 1 reviewers |
| draft-P8c | Opus first draft of tickets/P8c.md (order 20 item 6, missing v1 ticket) | opus | 02:32Z | +60min | QUEUED (agent limit 20; launch when a slot frees) | verify commit; then round 1 reviewers |
| rev2-P5a | Sonnet author: apply reviews/P5a-round1-resolve.md -> next revision | sonnet | 02:32Z | +45min | running | verify; round-2 reviewers |
| rev2-P5b1 | Sonnet author: apply reviews/P5b1-round1-resolve.md -> next revision | sonnet | 02:32Z | +45min | running | verify; round-2 reviewers |
| rev2-P6b1 | Sonnet revision author for P6b1 after round-1 resolve (order 20) | sonnet | 02:37Z | +60min | running | verify commit and counts; then round 2 reviewers |
| rev2-P5b2 | Sonnet revision author for P5b2 after round-1 resolve (order 20) | sonnet | 02:37Z | +60min | running | verify commit and counts; then round 2 reviewers |
| rev2-P4c | Sonnet revision author for P4c after round-1 resolve (order 20) | sonnet | 02:38Z | +60min | running | verify commit and counts; then round 2 reviewers |
| res-bs-P4d | Opus egm-resolve build-start P4d (one round) | opus | 02:38Z | +60min | REPORTED | verify build notes in tickets/P4d.md; S0 EXIT P4d effective |
| res-bs-P4a | Opus egm-resolve build-start P4a (one round) | opus | 02:38Z | +60min | REPORTED | verify build notes in tickets/P4a.md; S0 EXIT P4a effective |
| rev2-P4b1 | Sonnet revision author for P4b1 after round-1 resolve (order 20) | sonnet | 02:39Z | +60min | running | verify commit and counts; then round 2 reviewers |
| res-bs-P1 | Opus egm-resolve build-start P1 (one round) | opus | 02:40Z | +60min | REPORTED | verify build notes in tickets/P1.md; S0 EXIT P1 effective |
| rev2-P4b2 | Sonnet revision author for P4b2 after round-1 resolve | sonnet | 02:40Z | +60min | running | verify commit and counts; then round 2 reviewers |
| r2-P5a-adv | Sonnet egm-design adversarial round 2 of tickets/P5a.md | sonnet | 02:40Z | +30min | REPORTED | save report to reviews/; then resolve |
| r2-P5a-cor | Sonnet egm-codebase-details correctness round 2 of tickets/P5a.md | sonnet | 02:40Z | +30min | REPORTED | save report to reviews/; then resolve |
| r1-P5b5-adv | Sonnet egm-design adversarial round 1 of tickets/P5b5.md | sonnet | 02:40Z | +30min | QUEUED (agent limit 20) | save report to reviews/; then resolve |
| r1-P5b5-cor | Sonnet egm-codebase-details correctness round 1 of tickets/P5b5.md | sonnet | 02:40Z | +30min | QUEUED (agent limit 20) | save report to reviews/; then resolve |
| res-bs-P3a | Opus egm-resolve build-start P3a (one round) | opus | 02:41Z | +60min | REPORTED | verify build notes in tickets/P3a.md; S0 EXIT P3a effective |
| res-bs-P2a | Opus egm-resolve build-start P2a (one round) | opus | 02:42Z | +60min | REPORTED | verify build notes in tickets/P2a.md; S0 EXIT P2a effective |
| r2-P5b2-adv | P5b2 round-2 reviewer (adv) | sonnet | 02:43Z | +30min | REPORTED | save report, ledger, then resolve/rev3 |
| r2-P5b2-cor | P5b2 round-2 reviewer (cor) | sonnet | 02:43Z | +30min | running | save report, ledger, then resolve/rev3 |
| r1-P8b-adv | P8b ticket reviewer (adv) | sonnet | 02:43Z | +30min | REPORTED | save report, ledger, resolve |
| r1-P8b-cor | P8b ticket reviewer (cor) | sonnet | 02:43Z | +30min | REPORTED | save report, ledger, resolve |
| r2-P6b1-adv | P6b1 ticket reviewer (adv) | sonnet | 02:43Z | +30min | QUEUED (agent limit) | save report, ledger, resolve |
| r2-P6b1-cor | P6b1 ticket reviewer (cor) | sonnet | 02:43Z | +30min | QUEUED (agent limit) | save report, ledger, resolve |
| r1-P5b4-adv | P5b4 ticket reviewer (adv) | sonnet | 02:43Z | +30min | REPORTED | save report, ledger, resolve |
| r1-P5b4-cor | P5b4 ticket reviewer (cor) | sonnet | 02:43Z | +30min | running | save report, ledger, resolve |
| r1-P8a-adv | P8a round-1 reviewer (adv) | sonnet | 02:45Z | +30min | QUEUED (agent limit) | launch when slots free |
| r1-P8a-cor | P8a round-1 reviewer (cor) | sonnet | 02:45Z | +30min | QUEUED (agent limit) | launch when slots free |
| r1-P5b3-adv | P5b3 round-1 reviewer (adv) | sonnet | 02:45Z | +30min | QUEUED (agent limit) | launch when slots free |
| r1-P5b3-cor | P5b3 round-1 reviewer (cor) | sonnet | 02:45Z | +30min | QUEUED (agent limit) | launch when slots free |
| res-r2-P5a | Opus egm-resolve P5a round 2 | opus | 02:46Z | +45min | running | verify disposition; then rev 3 author, round 3 reviewers (cap 3 rounds) |
| r2-P4c-adv | P4c round-2 reviewer (adv) | sonnet | 02:46Z | +30min | REPORTED | save report, ledger, resolve |
| r2-P4c-cor | P4c round-2 reviewer (cor) | sonnet | 02:46Z | +30min | REPORTED | save report, ledger, resolve |
| save-reports-0611 | Sonnet saves 6 reviewer reports from task outputs (P5b2 r2 cor, P6b1 r2 adv+cor, P5b4 r1 adv, P8b r1 cor, P4c r2 adv) + ledger rows | sonnet | 03:10Z | +20min | REPORTED | verify commit; then launch resolves |
| fix-P4b2-maint | Opus: restore P4b2 maintenance identity per order 21 (rev 2 correction) | opus | 03:10Z | +30min | running | verify commit; then round 2 reviewers |
| r2-P5b1-adv | P5b1 round-2 reviewer (adv) | sonnet | 03:10Z | +30min | running | save, ledger, resolve |
| r2-P5b1-cor | P5b1 round-2 reviewer (cor) | sonnet | 03:10Z | +30min | running | save, ledger, resolve |
| r2-P4b1-adv | P4b1 round-2 reviewer (adv) | sonnet | 03:10Z | +30min | REPORTED | save, ledger, resolve |
| r2-P4b1-cor | P4b1 round-2 reviewer (cor) | sonnet | 03:10Z | +30min | REPORTED | save, ledger, resolve |
| r1-P5c-adv | P5c round-1 reviewer (adv) | sonnet | 03:10Z | +30min | running | save, ledger, resolve |
| r1-P5c-cor | P5c round-1 reviewer (cor) | sonnet | 03:10Z | +30min | running | save, ledger, resolve |
| r1-P6a-adv | P6a round-1 reviewer (adv) | sonnet | 03:10Z | +30min | running | save, ledger, resolve |
| r1-P6a-cor | P6a round-1 reviewer (cor) | sonnet | 03:10Z | +30min | running | save, ledger, resolve |
| build-P1m | Sonnet builder P1m on core/P1m, draft PR, evidence/P1m | sonnet | 02:50Z | +90min | running | verify PR, evidence, then review of result |
| res-r2-P5b2 | Opus egm-resolve P5b2 round 2 | opus | 03:25Z | +45min | REPORTED | verify disposition; rev 3 author; round 3 |
| res-r2-P6b1 | Opus egm-resolve P6b1 round 2 | opus | 03:25Z | +45min | REPORTED | verify; rev 3 author; round 3 |
| res-r1-P8b | Opus egm-resolve P8b round 1 | opus | 03:25Z | +45min | REPORTED | verify; rev 2 author; round 2 |
| draft-P6b2 | Opus first draft tickets/P6b2.md | opus | 02:50Z | | REPORTED | committed 1901def; round 1 launched |
| r1-P6b2-adv | P6b2 round-1 reviewer (adv) | sonnet | 03:30Z | +30min | REPORTED (unsaved: save-r2c) | save, ledger, resolve |
| r1-P6b2-cor | P6b2 round-1 reviewer (cor) | sonnet | 03:30Z | +30min | REPORTED (unsaved: save-r2c) | save, ledger, resolve |
| res-r2-P4c | Opus egm-resolve P4c round 2 | opus | 02:51Z | +45min | REPORTED | verify; rev 3; round 3 |
| res-r2-P4b1 | Opus egm-resolve P4b1 round 2 | opus | 02:52Z | +45min | REPORTED | launch after report save |
| save-r2b | Sonnet saver: P5b1 r2, P6a r1, P5c r1 (adv+cor each) = 6 reports + ledger rows | sonnet | ~02:55Z | +20min | REPORTED | verify, push, launch resolves |
| save-r2c | Sonnet saver: P6b2 r1 adv (a8ac760d78cffcdde) + cor (a9f6d3e5a184b9a11) | sonnet | - | +15min | REPORTED | launch after save-r2b pushes; then P6b2 resolve |
| res-r2-P5b1 | Opus egm-resolve P5b1 round 2 | opus | ~02:56Z | +45min | REPORTED | verify; rev 3; round 3 |
| res-r1-P5c | Opus egm-resolve P5c round 1 | opus | ~02:56Z | +45min | REPORTED | verify; rev 2; round 2 |
| res-r1-P6a | Opus egm-resolve P6a round 1 | opus | ~02:56Z | +45min | REPORTED | verify; rev 2; round 2 |
| rev-P8b-2 | Opus author: P8b revision 2 from reviews/P8b-round1-resolve.md | opus | 02:55Z | +45min | REPORTED | verify; round 2 reviewers |
| rev-P6b1-3 | Opus author: P6b1 revision 3 from reviews/P6b1-round2-resolve.md | opus | 02:55Z | +45min | REPORTED | verify; round 3 reviewers; freeze |
| res-r1-P6b2 | Opus egm-resolve P6b2 round 1 | opus | 02:56Z | +45min | REPORTED | verify; rev 2; round 2 |
| fix-P4b2-maint | (closed) maintenance identity restored, rev 3 daae169 pushed | opus | 03:10Z | - | CLOSED (REPORTED, verified) | round 2 reviewers |
| r2-P4b2-adv | egm-design adversarial round 2 of tickets/P4b2.md rev 3 | sonnet | 02:57Z | +30min | running | REPORTED |
| r2-P4b2-cor | egm-codebase-details correctness round 2 of tickets/P4b2.md rev 3 | sonnet | 02:57Z | +30min | running | REPORTED |
| rev-P5b2-3 | Opus author: P5b2 revision 3 from reviews/P5b2-round2-resolve.md | opus | 02:57Z | +45min | REPORTED | verify; round 3 reviewers; one resolve; freeze |
| rev-P4c-3 | Opus author: P4c revision 3 from reviews/P4c-round2-resolve.md | opus | 02:58Z | +45min | REPORTED | verify; round 3 reviewers; resolve; freeze |
| rev-P4b1-3 | Opus author: P4b1 revision 3 from reviews/P4b1-round2-resolve.md | opus | 02:59Z | +45min | REPORTED | verify; round 3 reviewers; resolve; freeze |
| rev-P5a-3 | Opus author: P5a revision 3 from reviews/P5a-round2-resolve.md (was NOT launched earlier: lead slip, found 03:00Z) | opus | 03:00Z | +45min | REPORTED | verify; P5b1 rev 3 waits for it; round 3 reviewers |
| rev-P6a-2 | Opus author: P6a revision 2 from reviews/P6a-round1-resolve.md | opus | 03:00Z | +45min | REPORTED | verify; round 2 reviewers |
| rev-P5c-2 | Opus author: P5c revision 2 from reviews/P5c-round1-resolve.md | opus | 03:02Z | +45min | REPORTED | verify; round 2 |
| rev-P6b2-2 | Opus author: P6b2 revision 2 from reviews/P6b2-round1-resolve.md | opus | 03:02Z | +45min | REPORTED | verify; round 2 |
| r2-P8b-adv | egm-design adversarial round 2 of P8b rev 2 | sonnet | 03:02Z | +20min | REPORTED | save |
| r2-P8b-cor | egm-codebase-details correctness round 2 of P8b rev 2 | sonnet | 03:02Z | +20min | REPORTED | save |
| r3-P6b1-adv | egm-design adversarial round 3 (LAST) of P6b1 rev 3 | sonnet | 03:03Z | +20min | running | save |
| r3-P6b1-cor | egm-codebase-details correctness round 3 (LAST) of P6b1 rev 3 | sonnet | 03:03Z | +20min | REPORTED | save |
| res-r2-P4b2 | Opus egm-resolve P4b2 round 2 (5 Majors + minors) | opus | 03:03Z | +30min | REPORTED | save, rev 4 author |
| r1-P5b4-cor2 | round 1 ticket review | sonnet | 03:04Z | +20min | REPORTED | save |
| r1-P8a-adv | round 1 ticket review | sonnet | 03:04Z | +20min | REPORTED | save |
| r1-P8a-cor | round 1 ticket review | sonnet | 03:04Z | +20min | REPORTED | save |
| r1-P5b3-adv | round 1 ticket review | sonnet | 03:04Z | +20min | running | save |
| r1-P5b3-cor | round 1 ticket review | sonnet | 03:04Z | +20min | REPORTED | save |
| r1-P5b5-adv | round 1 ticket review | sonnet | 03:04Z | +20min | REPORTED | save |
| r1-P5b5-cor | round 1 ticket review | sonnet | 03:04Z | +20min | REPORTED | save |
| r3-P5b2-adv | egm-design adversarial round 3 of P5b2 rev 3 | sonnet | 03:05Z | +20min | REPORTED | save |
| r3-P5b2-cor | egm-codebase-details correctness round 3 of P5b2 rev 3 | sonnet | 03:05Z | +20min | REPORTED | save |
| sav-P5b5-r1 | Saver: P5b5 round 1 reports + ledger | sonnet | 03:06Z | +10min | REPORTED | resolve |
| r3-P4c-adv | egm-design adversarial round 3 of P4c rev 3 (money) | sonnet | 03:06Z | +20min | REPORTED | save |
| r3-P4c-cor | egm-codebase-details correctness round 3 of P4c rev 3 | sonnet | 03:06Z | +20min | REPORTED | save |
| sav-P5b4-P8a-r1 | Saver: P5b4 cor, P8a adv+cor round 1 + ledger | sonnet | 03:07Z | +10min | REPORTED | resolves |
| res-r1-P5b5 | Opus egm-resolve P5b5 round 1 (1 Blocker, 11 Majors) | opus | 03:07Z | +30min | REPORTED | rev 2 author |
| sav-P5b3-P6b1-P8b-P5b2 | Saver: P5b3 r1 adv+cor, P6b1 r3 adv+cor, P8b r2 adv (cor pending), P5b2 r3 adv | sonnet | 03:09Z | +12min | REPORTED | resolves |
| r2-P6a-adv | Round 2 adversarial P6a rev 2 | egm-design | 03:10Z | +10min | REPORTED | save |
| r2-P6a-cor | Round 2 correctness P6a rev 2 | egm-codebase-details | 03:10Z | +10min | REPORTED | save |
| r3-P4b1-adv | Round 3 adversarial P4b1 rev 3 | egm-design | 03:10Z | +12min | REPORTED | save |
| r3-P4b1-cor | Round 3 correctness P4b1 rev 3 | egm-codebase-details | 03:10Z | +12min | REPORTED | save |
| res-r1-P5b4 | Opus resolve P5b4 r1 (1 Blocker, Majors) | opus | 03:10Z | +30min | running | rev 2 author |
| res-r1-P8a | Opus resolve P8a r1 (8 Majors) | opus | 03:10Z | +30min | running | rev 2 author |
| res-r1-P5b3 | Opus resolve P5b3 r1 (11 Majors) | opus | 03:11Z | +30min | running | rev 2 author |
| res-r3-P6b1 | Opus resolve P6b1 r3 (3 Majors) | opus | 03:11Z | +25min | running | rev 4/freeze |
| sav-P8b-P5b2-P4c | Saver: P8b r2 cor, P5b2 r3 cor, P4c r3 adv+cor | sonnet | 03:11Z | +12min | REPORTED | resolves |
| rev-P4b2-4 | Opus author P4b2 rev 4 (round 2 resolve) | opus | 03:11Z | +25min | running | round 3 |
| res-r3-P4c | Opus resolve P4c r3 (1 Blocker, 6 Majors) | opus | 03:12Z | +25min | running | build notes / freeze |
| res-r3-P5b2 | Opus resolve P5b2 r3 (7 Majors) | opus | 03:12Z | +25min | running | build notes / freeze |
| res-r2-P8b | Opus resolve P8b r2 (1 Blocker, 9 Majors) | opus | 03:12Z | +30min | running | rev 3 |
| r3-P5a-adv | Round 3 adversarial P5a rev 3 | egm-design | 03:13Z | +12min | REPORTED | save |
| r3-P5a-cor | Round 3 correctness P5a rev 3 | egm-codebase-details | 03:13Z | +12min | REPORTED | save |
| rev-P5b5-2 | Opus author P5b5 rev 2 (shrinks to tests + page) | opus | 03:14Z | +25min | REPORTED | round 2 |
| sav-P6a-r2-P4b1-r3adv | Saver: P6a r2 adv+cor, P4b1 r3 adv reports to reviews/ and ledger | claude | 03:15Z | +10min | REPORTED | verify, push; launch P6a rev 3 resolve |
| res-r2-P6a | Opus resolve P6a round 2 (adv 4 Major, cor 4 Major) + order 22 | opus | 03:16Z | +25min | running | verify, then rev 3 author |
| sav-P4b1-r3cor | Saver: P4b1 r3 correctness report + ledger | claude | 03:17Z | +8min | REPORTED | verify, then P4b1 round 3 resolve |
| rev-P8a-2 | Opus author P8a rev 2 from reviews/P8a-round1-resolve.md | opus | 03:17Z | +30min | running | verify; round 2 reviewers |
| rev-P5b4-2 | Opus author P5b4 rev 2 from reviews/P5b4-round1-resolve.md | opus | 03:17Z | +30min | running | verify; round 2 reviewers |
| res-r3-P4b1 | Opus resolve P4b1 round 3 (3 Majors: ADV-1, ADV-2, COR-1) | opus | 03:18Z | +25min | running | verify; build notes |
| sav-P5a-r3 | Saver: P5a r3 adv+cor reports + ledger | claude | 03:18Z | +10min | REPORTED | verify; P5a round 3 resolve |
| res-r3-P5a | Opus resolve P5a round 3 (6 Majors) -> build notes | opus | 03:19Z | +25min | running | verify |
| rev-P5b3-2 | Opus author P5b3 rev 2 from reviews/P5b3-round1-resolve.md | opus | 03:19Z | +35min | running | verify; round 2 reviewers |
| rev-P8b-3 | Opus author P8b rev 3 from reviews/P8b-round2-resolve.md (last round) | opus | 03:20Z | +35min | running | verify; round 3 reviewers |
| r2-P5b5-adv | Round 2 adversarial P5b5 rev 2 (snapshot cd2243f) | egm-design | 03:21Z | +10min | running | save |
| r2-P5b5-cor | Round 2 correctness P5b5 rev 2 (snapshot cd2243f) | egm-codebase-details | 03:21Z | +10min | running | save |
| tk-AK0 | Opus author ticket AK0 rev 1 (research and decisions note, Tier B) | opus | 03:23Z | +35min | running | verify; round 1 reviewers |
| tk-AK1 | Opus author ticket AK1 rev 1 (step contract + outbound gate, absorbs P7b) | opus | 03:23Z | +40min | running | verify; round 1 reviewers |
| rv-P8a-r2-adv | P8a round 2 adversarial (egm-design) | 03:25Z | +30min | running | verify |
| rv-P8a-r2-cor | P8a round 2 correctness (egm-codebase-details) | 03:25Z | +30min | running | verify |
| rv-P4b2-r3-adv | P4b2 round 3 adversarial (egm-design) | 03:25Z | +30min | running | verify |
| rv-P4b2-r3-cor | P4b2 round 3 correctness (egm-codebase-details) | 03:25Z | +30min | running | verify |
| sv-P5b5-r2 | saver P5b5 r2 reports | 03:25Z | +30min | running | verify |
| au-P6a-r3 | P6a rev 3 author (Opus) | 03:26Z | +30min | running | verify |
| rv-P5c-r2-adv | P5c r2 adversarial | 03:26Z | +30min | running | verify |
| rv-P5c-r2-cor | P5c r2 correctness | 03:26Z | +30min | running | verify |
| rv-P6b2-r2-adv | P6b2 r2 adversarial | 03:26Z | +30min | running | verify |
| rv-P6b2-r2-cor | P6b2 r2 correctness | 03:26Z | +30min | running | verify |
| rs-P5b5-r2 | P5b5 round 2 resolve (Opus) | 03:26Z | +25min | running | verify |
| rs-P5b5-r2 | P5b5 round 2 resolve (Opus) | 03:26Z | +25min | running | verify |
| rv-P8b-r3-adv | P8b r3 adversarial | 03:27Z | +30min | running | verify |
| rv-P8b-r3-cor | P8b r3 correctness | 03:27Z | +30min | running | verify |
| rv-P5b3-r2-adv | P5b3 r2 adversarial | 04:05Z | +30min | running | verify |
| rv-P5b3-r2-cor | P5b3 r2 correctness | 04:05Z | +30min | running | verify |
| rv-P5b4-r2-adv | P5b4 r2 adversarial | 04:05Z | +30min | running | verify |
| rv-P5b4-r2-cor | P5b4 r2 correctness | 04:05Z | +30min | running | verify |
| sv-batch-r | save P4b2 r3, P5c r2, P8a r2, P8b r3 reports | 04:05Z | +25min | running | verify |
| rs-P6b2-r2 | P6b2 round 2 resolve (Opus) | 04:05Z | +25min | running | verify |
| au-P5b5-r3 | P5b5 rev 3 author (Opus) | 04:05Z | +30min | running | verify |
| rv-AK0-r1-adv | AK0 r1 adversarial | 04:20Z | +30min | running | verify |
| rv-AK0-r1-cor | AK0 r1 correctness | 04:20Z | +30min | running | verify |
| rv-AK1-r1-adv | AK1 r1 adversarial | 04:20Z | +30min | running | verify |
| rv-AK1-r1-cor | AK1 r1 correctness | 04:20Z | +30min | running | verify |
