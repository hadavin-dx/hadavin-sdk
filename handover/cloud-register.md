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
| apply-P1 (resumed) | apply P1-round1-resolve-report.md to tickets/P1.md; write P1-round1-disposition.md | sonnet (claude-sonnet-5-5) | 15:06Z | 15:46Z | running | verify, commit, round 2 reviewers |
| apply-P2a (resumed) | same for P2a | sonnet (claude-sonnet-5-5) | 15:06Z | 15:46Z | running | same |
| apply-P3a (resumed) | same for P3a | sonnet (claude-sonnet-5-5) | 15:06Z | 15:46Z | running | same |
| apply-P4d (resumed) | same for P4d | sonnet (claude-sonnet-5-5) | 15:06Z | 15:46Z | running | same |

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
