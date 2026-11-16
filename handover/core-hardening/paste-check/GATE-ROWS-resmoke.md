# GATE-ROWS-resmoke (C13, lead answer Q18 item 2). Plan text for the studio lead. Builder: sub-agent (Sonnet 5.5). NOT a verdict: the lead runs the EGM reviews (EGM-GATE v1).

## 0. Read first: what failed, what is uncertain, what I did not check
1. **Nothing was run on the real stack.** The two commands were tested only in bash and dash here, against a stand-in `env.sh` whose `pgq` prints a number I choose, and against made-up JSON files. No Postgres, n8n, Docker or WSL. Raw output: `gate-rows/gate-rows-test-output.txt`, `gate-rows/syntax-check-output.txt`.
2. **`drive.py` is not on disk** (QUESTIONS.md item 4 says the same). So these are UNVERIFIED and are not read from any file:
   - the shape of the case A and B output. I only know, from plan 11.1b, that the last JSON line has a key `replies` and that a reply is a list (index 4 = `n8n_error`). Where the "repeat" flag sits in a reply is not known. G1 therefore has an empty `RI=` that the lead fills from `drive.py`; empty = a STOP line (it never passes by default). If the real shape differs (no `replies` list, flag not true/false), G1 prints `FAIL ... shape` and stops.
   - that `$T/keys.txt` holds a line `A <lead id>` and `B <lead id>` (plan 11.3, 11.5 read `$1==CASE`, `$2`=id; A and B lines are inferred from "F ... keys A, B, B2", not read).
   - that the lead id is the `lead_key` column of `mf_leads` (plan 11.5 uses it that way for C).
   - the length of the lease. It is NOT in the plan (grep finds no "lease" except the plan's own "not proven" list). So "inside the lease" is not checked by either row; cases A and B are sent back to back and that is all I can say.
3. **I did not choose the whole-table count.** The lead's text allowed a count on `mf_leads` with "the exact number". The whole-table total after S10 depends on how many rows case P and B2 and any earlier keys leave, which I cannot read. A total I invented would be a guess. G2 counts only the two ids A and B, so the exact number is 2 whatever the other cases did. If the lead wants a whole-table number, it must come from `drive.py` (UNVERIFIED).
4. **The patch is only valid in this order:** `plan-v5-fixes.patch`, then `plan-v5-repin-v5.patch`, then `plan-v5-gate-rows.patch` (wrong order fails: hunks FAILED, saved). I did not apply the later `plan-v6-real-v5-edits.md` (a text file, not a patch) and did not check the gate rows against it; its S10 text (line "B: 10 replies ... at most 1 with repeat false") reads the same, so the rule matches, but the patch lines were not tried on it.
5. **PASS here does not mean PASS on the laptop** (Git Bash path forms, WSL, CRLF). The commands use only `awk`, `case`, `python3 -I`, `tee`, `head`, plus the plan's own `pgq` and `$T`.

## 1. What the two rows decide (plain words)
The video caption allowed ONLY when both rows PASS:
> a lead sent twice with the same id inside the lease is processed once

Row G1 checks what the system **said back** to the two sends. Row G2 checks what the database **kept**. Neither row alone is enough: replies can say "repeat" while nothing was stored, and one stored row cannot show whether the second send was recognised.

## 2. The gate rows
Where: both run straight after the S10 paste (plan step S10, patched line about 360). The S10 paste is changed in one place: its calls for cases A and B now end in `| tee $T/gate1-A.out` and `| tee $T/gate1-B.out`, so the output is saved (13.8's copy list gets `gate1-*.out gate2.out`). Case P is unchanged.

### Gate row 1 (G1): cases A and B, the same lead id sent twice, and a burst of 10
| field | content |
|---|---|
| id | G1 (paste `pastes/G1.sh`) |
| command (verbatim, `bash -n` and `dash -n` pass) | file `gate-rows/G1.sh`; it is the first fenced block of the patch |
| saved outputs | `$T/gate1-A.out`, `$T/gate1-B.out` (from the changed S10 paste); the check prints to the run log of the step |
| expected output | `GATE1-A replies=2 repeat_false=1 repeat_true=1 first_repeat=False`, `GATE1-A PASS`; `GATE1-B replies=10 repeat_false=1 repeat_true=9 first_repeat=False`, `GATE1-B PASS`; last line `GATE1 ROW: PASS` |
| exact counts | A: exactly 2 replies; the first says "not seen before" (repeat false), the second says "seen before" (repeat true). B: exactly 10 replies; at most 1 says "not seen before" (the plan's own S10 rule; 0 is allowed by that rule and is REC, my note: the stored-row count in G2 then still has to be 1 for B) |
| pass rule | the last line is `GATE1 ROW: PASS`. Anything else (`FAIL`, `STOP`, the "repeat-flag index not filled" line, a shape line) = fail |
| proves | the same id sent twice in one driver call (A) and ten times (B) was answered as "first time" at most once; the answer comes from the flow's own claim step |
| does NOT prove | that the repeat reply meant "no second mail, no second CRM call" (that is F in 11.1 and 11.8: `mails == 1`, `model_calls == 1`); the lease length or lease expiry; the recovery after a crash (S11, E); the real HubSpot node (the loopback stand-in is used, edit list 2.1b); a real model; reply status 200 and the verdict word (read by eye from the saved files, REC, because I do not know their positions) |
| who decides | the studio lead |
| on fail | STOP (R1). The caption is not allowed. The lead reads `gate1-*.out`, writes the finding, decides: fix and re-run on a new take, or drop the claim. No re-run of S10 on this take without the lead's written go (whether a re-run makes new ids is UNVERIFIED) |

### Gate row 2 (G2): ONE count on mf_leads by the read-only role
| field | content |
|---|---|
| id | G2 (paste `pastes/G2.sh`; the same role and database as step P-C2 in 1b.3 of the plan, `smk_count`, which printed `0` before any lead; P-C2 is at plan line 289 of v5, line 309 after the two earlier patches) |
| command (verbatim, `bash -n` and `dash -n` pass) | file `gate-rows/G2.sh`; second fenced block of the patch. It reads the A and B ids from `$T/keys.txt` and runs ONE `SELECT count(*) FROM mf_leads WHERE lead_key IN (<A id>, <B id>)` |
| saved output | `$T/gate2.out` (the number) and the printed line |
| expected output | exactly `GATE2 count: 2` |
| pass rule | the printed line is exactly `GATE2 count: 2` |
| what another result means | `0`: nothing stored for either id (the flow did not write, wrong database or role, or the ids were wrong). `1`: one of the two ids has no row (a lead was lost or never reached the store): a claim-path finding. A line with `STOP`: keys missing, same id for A and B, or a character in an id the guard rejects. Empty: the count could not run. All of these = G2 FAIL = STOP. More than 2 cannot appear (two ids, one row each, primary key). |
| who decides | the studio lead; no agent decides |
| on fail | STOP (R1); caption not allowed; the lead decides (stop the take, or look at `gate2.out` and the stored row with a second, separate command he writes himself); do not "fix" by editing rows |
| proves | each of the two ids has exactly one stored row, so neither id was lost and neither created a second row |
| does NOT prove | that the second send did nothing else (mails, CRM calls: F lines); lease expiry; recovery; the real CRM node; a real model; that rows from other cases (P, B2, earlier) are right (G2 ignores them on purpose); the primary key on `lead_key` makes "two rows for one id" impossible, so count 1 per id alone is weak evidence and G1 and F carry the "processed once" meaning |

## 3. Claim wording (only on PASS)
- Allowed only when G1 PASS and G2 PASS, and 11.8 / row DM do not report a double mail: "a lead sent twice with the same id inside the lease is processed once".
- Not allowed in the same caption: anything about expiry of the lease, crash recovery, real HubSpot, a real model, or "never".
- The word "lease" is used because the lead asked for it; its length is not in the plan (UNVERIFIED), so the lead should state the number only after reading the flow.

## 4. Files (all under `paste-check/`)
- `gate-rows/G1.sh`, `gate-rows/G2.sh`: the two commands, as tested.
- `plan-v5-gate-rows.patch` (47 lines, 2 hunks: the new block after the S10 expected line, the two `tee` edits in S10, the 13.8 copy list). Dry run and apply on a scratch copy after fixes and repin-v5: rc 0, result identical to my prepared copy; wrong order fails. Raw: `gate-rows/patch-chain-output.txt`. Real `inputs/` untouched (sha256 starts `67a0a195537de875`, same before and after).
- Test raw: `gate-rows/gate-rows-test-output.txt` (G2: counts 2/1/0, same key, bad character, missing key, in bash and dash; G1: pass and 5 failing made-up cases), `gate-rows/syntax-check-output.txt` (`bash -n` and `dash -n` rc 0 on both blocks as they stand inside the patched plan, and on the changed S10 paste line).
- The first run in `gate-rows-test-output.txt` shows the first G1 version (no `GATE1 ROW` line; exit code of the last loop only); I changed it and the second block of that file is the tested final version.

## 5. Open items for the lead (each needs a person, nothing deferred silently)
1. Fill `RI` (repeat-flag position) from `drive.py`: needs the lead (the file is not readable here). Until then G1 stops by design.
2. Confirm the `keys.txt` line shape and that the id equals `lead_key` (G2 stops safely if not).
3. State the lease length from the flow before it goes into any caption.
4. Run the EGM reviewers on this file and the patch.
