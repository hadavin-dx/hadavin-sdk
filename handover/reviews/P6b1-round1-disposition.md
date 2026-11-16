# P6b1 round 1 disposition (ticket revision 1 -> revision 2)

Author pass, 2026-11-06. Applies every decision in `P6b1-round1-resolve.md` to `tickets/P6b1.md`. Reads of the two review reports were only to check the resolve was applied faithfully. Nothing was run; every code fact below was read in the core checkout. Ticket is now 163 lines (was 120). Counts: 26 mutants (was 17), 19 test ids (was 15: T1, T1b, T2-T6, T7, T7b, T8-T13 plus T9 as one), 9 PENDING LEAD items (was 8).

| finding | decision | where fixed in revision 2 |
|---|---|---|
| A1 + C9 | PROPOSE FIX (narrowed) | Interface: `NoTrainingStatement.hosts` (required, 1 to 8 entries, character rules, 12-digit refusal); refusal (f) with the exact message, checked after (c); expected = the entry's own host function; factory log prints the hosts; "What the statement check means" lists what is NOT checked (key or tier, truly self-run, truth of the statement); `config_hash` unchanged, reason kept (T10). Tests T14 (per kind, platform and region switch, order pinned), T2 and `pilot_cfg` updated to carry hosts. Mutants M18, M19. PENDING LEAD 9 (new). |
| A2 + C7 | PROPOSE FIX | Tests intro: hard-coded `SAMPLES`; T15 `set(SAMPLES) == set(TABLE["llm"])` with the instructive message; T9 tautology deleted (T9b says so); T1-T3, T9a, T14 parametrised over SAMPLES; "What the statement check means" item 3 corrected (fail-closed default plus refusal (a) enforce, the test only makes the author notice); Class-level notes; M20. |
| A3 | PROPOSE FIX (cut) | Problem (exclusion named), Source (NOT taken), Files (`guard/*` not changed), Class-level notes (sibling and why undoing it is cheap, with the `table.py:101` evidence), new "v1.1 list" with the trigger, PENDING LEAD 3 wording ("llm kind only") and PENDING LEAD 4 (reversed, builder default = exclude). Title says "inside the llm kind". |
| A4 + C6 + P4d Ask | PROPOSE FIX; Ask half declined | Depends-on rewritten: F6 quoted from `amendments.md` (table.py list corrected, llm/anthropic.py correction), `defaults.py` and `tests/test_k3_pilot_env.py` added, each `config.py`/`table.py` hit classed "edits" or "mentions only" from the ticket text; merge order after P4b1-b and before P4b2-b (P4a item 27, order 8(2)); stale "price tiers, C4a" and "BEFORE P4b1" deleted; the "before P4b1" half of `P4d.md:273` declined and PENDING LEAD 2 tells the P4d author. |
| A5 + C8 | PROPOSE FIX | `_utc_today()` in Interface and Files; M17 restated; T5 load-level row with the patched clock; T4 reworded ("refused under 30, accepted under 90"). No time-zone-shifted test (replaced by the seam, as decided). |
| A6 + C5 | PROPOSE FIX | `checked_on` strict validator; the false sentence "a number is refused" replaced in Verified facts by the probe values; T7 rows (0, 86400, 1767225600, digit strings, float, `"0"`, unquoted datetime); M26 (author addition). |
| A7 | PROPOSE FIX | 12-digit refusal on `reference` and `hosts` (rule copied from `key_label`, `table.py:196-212`, re-read); docs wording (title, URL path, version; no person or party); T7 ARN-shaped row built from parts; M25 (author addition). |
| A8 | PROPOSE FIX (narrowed) | Factory log shows "valid until"; README text about start-up-only age check named in Files and Interface. No warning window (PENDING LEAD 5). Deviation, stated: `make` does not see the configured age limit, so the date is computed with the default limit and the log says the config may set another; passing the configured value needs `app.py` (hot, out of scope). |
| A9 | PROPOSE FIX | Fixed sentence in README, CHANGELOG, log line (Files, Interface, "What the statement check means"); user-facing text says "no-training statement"; field name `no_training` kept. |
| A10 + C4 | PROPOSE FIX | T1 and Evidence 4: pilot rows "DID NOT RAISE", prod rows `match=` mismatch (old code refuses `anchor: none` and the signer key file, re-read in Verified facts); prod acceptance in T2. |
| A11 | PROPOSE FIX | "Three constants" in Target, Interface, Files. PENDING LEAD list now 1-9 with the note that the orchestrator copies it to `questions-for-lead.md`. I did not edit `questions-for-lead.md` (task limits me to two files). |
| A12 | PROPOSE FIX + partial CONTEST | M21, M22, M23 added with tests T8, T16, T14. cli half contested with evidence (`cli.py:299`); the injection half stated as a limit in Interface (log) and Verified facts, not fixed. |
| C1 | PROPOSE FIX | T1b: direct `DEV_ONLY` assertion, exact-token regex, absence of `declares no`; M15 reworded (check skips `neutral=True` kinds). |
| C2 | PROPOSE FIX | Files: all new-name imports function-local; T9 split into T9a (old names, fails by assertion) and T9b (new feature); Evidence 4 lists T1 pilot and prod rows and T9a pilot rows as the only assertion fail-befores. |
| C3 | PROPOSE FIX | T8 pattern-valid canary in stale, wrong-basis, future-dated, hosts-mismatch cases, checked in `str(ConfigError)` and the returned list; log assertion only on the success path; M24. |
| P2a relay | PROPOSE FIX | Mutation plan: runner is P1m's (`P1.md:24`). |

## Deviations and additions (not in the resolve; judged by the lead)
- Refusal letters keep the resolve's naming; the order is written as (a), (b), (c), (f), (d), (e).
- Host character set is stricter than "reference minus slash and hash": the space is also refused, and compare is case-insensitive (both sides lower-cased) so a capitalised resource name still matches. Reason: the table's host functions do not promise lower case (UNVERIFIED), and an unmatchable statement would be a dead config.
- The resolve names `hadavin_sdk.backends.hosts` as the egress list; there is no such module. The function is `hosts` in `backends/factory.py`; the ticket cites that. The statement check uses the entry's own `hosts` function directly because `config.py` imports `table.py` only.
- M25 and M26 are mine, so each new behaviour (12-digit rule, strict date validator) has a mutant, as the ticket's own rule requires.
- A planted kind in T9b is tested by calling `_no_training_refusals` directly, because whether a planted kind loads through YAML depends on how the settings union is built (UNVERIFIED).
- The ticket no longer names the model of the author or the reviewers; Studio-rule citations unchanged.

## Not applied
None of the resolve decisions was left out. Not done because outside this task: copying PENDING LEAD to `questions-for-lead.md`; telling the P4d author; the F6 amendment; the ledger/v1.1 row (all are lead or orchestrator actions named in the ticket).

## Unverified
The reviewers' condensed evidence lines; the P5b3/P5b4/P5c/P6a/P6b2 tickets (F6 lists quoted only); whether P5b2 edits `config.py`; per-kind required settings fields for SAMPLES; Python 3.12; provider terms.
