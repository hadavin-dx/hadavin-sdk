# P3a round 5, correctness (egm:egm-codebase-details), head 60fedf6. Condensed. Verdict: 0 BLOCKER, 0 MAJOR, 5 MINOR, 3 NIT. Reviewer ran nothing (no psql, pytest, git); all "run on 16.15" claims UNVERIFIED by it.
| id | sev | problem | fix |
|---|---|---|---|
| R5-C1 | MINOR | Line 21 says every new refusal is `MigrationNumberError`; line 28 says grant-scan problems stay `ConfigError`. | Reword: every refusal is a `ConfigError`; number/order/gone are the subclass; say which tests check exact type. |
| R5-C2 | MINOR | "psql stops, exit 3" is script-mode (`-f`) behaviour; interactive use unverified. | Label verified for `-f` only; tell the administrator to save a file and run `psql -f`. (Overlaps adversarial R5-1.) |
| R5-C3 | MINOR | "each gave cannot run inside a transaction block" includes DROP SUBSCRIPTION (only refused with a slot). | State the variant run, or relabel. |
| R5-C4 | MINOR | All 16.15 claims unchecked on CI's 17.10. | Add one sentence to header and UNVERIFIED. |
| R5-C5 | MINOR | Stale cites: P2a.md line 9 -> 10; line 40 -> 41; "P2a does not rely on P3a" is stale (P2a lines 41, 75, 118 do). | Fix. |
| R5-C6 | NIT | Runbook (e): `0006_evidence` could be renamed twice. | Say only E1 touches it. |
| R5-C7 | NIT | "17 tables" is 15 tables plus 2 sequences. | Fix wording. |
| R5-C8 | NIT | Killer test names in mutation plan not named in Tests. | Add names. |
Verified OK by the reviewer (code reading): migrate.py cites, SQL file counts (34 statements), existing-test cites, ConfigError exit codes. Stop rule: not met (needs two clean rounds at the final commit); escalation after round 5 is due.
