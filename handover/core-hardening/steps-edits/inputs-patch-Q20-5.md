# Patch text for inputs (lead answer Q20.5), 2026-11-16
Patch file: `steps-edits/inputs-patch-Q20-5.patch` (`patch -p1` from `core-hardening/`). Dry run and a real apply were done only on a scratch copy; `inputs/` was never touched (checked by `cmp`). Nothing committed or pushed. S = inputs/AGENT-SCOPE-DO-AND-DONT.md, X = inputs/DECISIONS-2026-11-16.md.

## Failures and not checked (first)
1. OWNER-STEPS v11 (D) and the appendix (A) are NOT patched here and still say the code archives by DELETE (A:174, D:163/173/176, A:59, D:208 claim sentences). The lead must make those match (findings F02, F03, F10).
2. S lines 19 and 21-23 not changed. Line 21 (MUST NOT) and 22 (enforcement) were not re-read for delete or archive wording beyond a keyword search (only hits: unrelated "deleted vacuous test", lock file).
3. The claim sentence uses my own reading of `mf-recovery.json` (CLAIM-EVIDENCE-Q21.md), which differs from the lead's "no takeover after expiry": the recovery flow does take over an unfinished lead after the lease, up to 3 times. The patched sentence therefore says "may pick it up again" and claims nothing about a crash. Lead re-reads ClaimStuck before approving. 45 s and 3 tries come from files, not a run.
4. F18 fix: I took D row 8 from `OWNER-STEPS-realrun-v11.md` line 36 (secret files live in the owner's home folder, named by run card row 8). I did not read the card row itself, so "NOT the take folder" is lead verifies at re-pin.
5. Not verified by me: that the take program has no delete call (taken from Q19.1; "lead verifies at the final head, r10"); which database holds the n8n execution log and the table (Q20.2: names unverified); HubSpot app count and scopes (owner-held, Q20.3); whether the program re-reads its settings after start.

## Changes
| # | File : line | Old (key words) | New (key words) | Reason / finding |
|---|---|---|---|---|
| 1 | S:5 | "its own Postgres table" | "its own table in the take's Postgres database (one Postgres server, two databases)"; lead verifies at re-pin | F13, decision 10 |
| 2 | S:9 | "the one execution log in Postgres" | "one execution log, kept in n8n's own database on the one Postgres server (two databases)"; clean-up wording owned by OWNER-STEPS step I.5 | F14 (pointer), decision 10, Q21.3 never "Postgres is the one store" |
| 3 | S:13 | key file in take folder = PROCEDURE rule | key file is in the owner's secret folder named by run card row 8, not the take folder; lead verifies config path at re-pin | F18 |
| 4 | S:20 | "at the end ARCHIVE ... DELETE call (`:1051`, `:504-509`)" and the NOTE F-01 | "at the end LIST leftover contacts by lead key and contact id (no delete)"; NO DELETE text: owner deletes by hand; old desk harness is `run_real_check.py`; take key read-only, probe key separate, probe only with owner's written yes; closing the terminal is safe; go condition 5 only after lead's final-head check | F01, Q19.1, Q20.3, decision 2 |
| 5 | S new section 3b (before section 4) | none | Lead's own row: MAY start the model program with the owner's key file, start/stop n8n with `n8n_start.sh`/`n8n_kill.py`, read only masked outputs; MUST NOT read the key file or edit the backstop or ledger; accepted exposure (one shared Linux user), owner may veto, guards named | F17, Q19.3 |
| 6 | X:2 | claim without lease | claim kept ("processed once") plus one lease sentence; claim text owned by step J and appendix section 8 | F10, cross-read/CLAIM-EVIDENCE-Q21.md |
| 7 | X:9 | "no extra real smoke" | loopback re-smoke labelled "real-v5 minus ONE node" plus ONE made-up lead; no extra real-account smoke; owner's HubSpot probe stays, only with the owner's written yes (O:129) | F05, Q17 |
