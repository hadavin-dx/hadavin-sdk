# EGM dry run (ORDER 001), 2026-11-16 ~06:55 UTC / 12:25 IST
Route: Skill egm:egm-review-loop (direct dispatch, one round, no fixes applied, no resolve step: dry run only).
Reviewers: egm:egm-design (design_critic) and egm:egm-implementation-readiness, both on model sonnet (Sonnet 5.5).
Test paragraph (3 lines):
1. The flow reads a new lead row from the sheet.
2. It checks the row is not a duplicate and then sends one notice.
3. If anything fails it stops and tells a person.

## design_critic: FAIL (3 Blockers, 4 Majors, 1 Nit)
- B: no alternatives considered (trigger, dedupe approach, source of truth).
- B: no risks section; failure after send but before marking processed gives a double notice; one bad row can block the queue; silent if the alert channel is down.
- B: no problem statement, goals/non-goals, or architecture.
- M: "new row" trigger/watermark, volume, concurrency unstated. M: "duplicate" key and state store undefined, check-then-send race. M: "one notice" needs idempotency, channel unnamed. M: no volume, cost, monitoring, success metric.
- Nit: vague unanchored terms, no title.

## implementation_readiness: FAIL (6 Blockers, 3 Majors, 1 Nit)
- B: no file boundary; no actionable steps; no test plan; "reads new row" leaves sheet/auth/schema open; "duplicate" undefined; "one notice" channel/recipient/idempotency open.
- M: error handling undefined; no phasing; no data structures/config.
- Nit: undefined terms.

## Read of the result
Both fresh reviewers returned real, specific reports on a deliberately thin text, so the reviewer agents run and judge. FAIL is the expected outcome for a 3-line paragraph. Not checked: the resolve step and a second round (not ordered).
