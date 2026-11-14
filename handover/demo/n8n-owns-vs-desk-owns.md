# What n8n does and what the desk does (one page, plain words)
Written 08:03Z by the demo cloud session for the lead. Basis: the NEEDED-CHECK verdict named in the lead's order (n8n is the one base and front door; the desk keeps the guarantee steps), plus my own measured numbers. Every number below is from n8n 2.46.6 self-hosted, one machine, made-up data. Make was never tested. "Measured" means I ran it and the raw rows are in `n8n-rerun/`; "stated" means it comes from the lead's order or the repo text and I did not test it here.

## Words
- **n8n**: the workflow tool where each step is a box. **Desk**: our small program (`src/lead_desk`) that sits behind it. **Fresh stack**: a newly built n8n plus database used for one test. **Reused stack**: one n8n that ran many tests in a row. **Keyed**: a mail system or CRM that recognises the same send key twice and acts once. **Blind**: one that does not. **UNKNOWN**: the desk cannot tell whether an email left; it does not guess, does not resend, and marks the follow-up for a person. **Ten at once**: ten identical lead submissions sent together.

## What n8n owns in the demo (stated)
Intake (form, e-mail, webhook), field mapping, the ten-at-once trigger, alerts, and plain sends in client builds. These are the flow stages and credentials; they stay in the no-code tool so a client can change them.

## What the desk owns, and why (stated, with what I measured)
The desk keeps the steps where a wrong answer costs money or trust: a receipt written before anything else happens, a keyed claim so one lead is sent once even when the machine stops mid-send, ambiguous sends marked for a person, approval of changed repeats, a spend limit for the model, hiding of personal data in logs, and a count that does not depend on n8n. I did not test the spend limit or the hiding of data. I found no "redact" word in the code under `src/` by a text search; the lead should check that label before it is used. Plain claim, not stronger: the desk makes sends keyed and retry-safe and marks ambiguous sends for a person; it does not promise "exactly once" for every case.

## Evidence (measured; each line says its condition)
| question | n8n alone | result |
|---|---|---|
| Ten identical leads at once through n8n's default duplicate-removal node (variant a) | reused stack | clean (one CRM row, one e-mail) in 12 of 20 bursts in R2 and 2 of 5 in R2b; published 18 of 20 |
| the same, first burst on a fresh stack | fresh stack | clean in 12 of 12 first bursts; bursts 2 and 3 on the same stack clean 8 of 10 |
| the same, in every burst | both | the number of duplicate rows equals the number of replies "200" (all 45 of my bursts) |
| Database insert that ignores repeats (b), data-table upsert (c), concurrency 1 (d) | reused stack | 20 of 20 clean each; replay added nothing |
| Stop n8n mid-flow (kill runs), a/b/c/d | reused stack | no kill without effect (0 of 15); the b, c, d kill rows ended with one CRM row and one e-mail; variant a in the CRM-request-in-flight case 1 of 5 clean (published 5 of 5, NOT reproduced) |
| Variant e (b plus a status column and a re-send job), ten at once | fresh stacks | 25 of 25 bursts clean, status sent |
| Variant e, kill at the two e-mail points: a second CRM row | reused 1 of 10; fresh 1 of 50 | published 4 of 10 NOT reproduced |
| Desk crash scene D2 (e-mail sent, result not yet noted), keyed demo mail server | desk, Linux, one run | one e-mail, follow-up `sent`, desk ended with exit code 137 |
| the same, blind demo mail server | desk, Linux, one run | one e-mail, follow-up `unknown` (counts page: unknown follow-ups 1), desk exit code 137 |

## What follows, facts only
- n8n's default duplicate node is not safe at ten-at-once on a reused stack in my runs; on a fresh stack's first burst it was. The cause is NOT established. So a claim "n8n alone is enough" cannot be made from these numbers, and neither can "n8n is broken": three alternatives (b, c, d) that put the one-time check in a database gave 20 of 20.
- The desk's two D2 rows are one measurement each; the doc table in `docs/tests.md` says the same for the two columns.
- Not tested: Make; any n8n version other than 2.46.6; n8n cloud; n8n in queue mode.
