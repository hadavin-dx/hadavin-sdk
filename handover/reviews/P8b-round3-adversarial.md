# P8b round 3, adversarial review
Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

P8b revision 3, round 3 (last). Read-only review. Result: no Blocker found. 3 Majors, 5 Minors, 2 Nits. Cites and the awk logic mostly hold.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-ADV-1 | Major | 217-224, 227-231, 370 | `E/` is never given as an absolute path. It lives on `core/cloud-handover`, but the core files are written from the core checkout on `core/P8b`, so it is a different worktree. Step 5 runs `cd "$S"` and then `sh "$E/t1.sh"`, `$E/roles.txt` and so on. With a relative `E=handover/evidence/P8b` every script fails (`E/roles.txt` not found), so the control run fails for a reason that is not a page fault. The `while read ... < "$E/roles.txt"` loop would also just read an empty or missing file. | Add a step 0 line: `E` is an absolute path to the ledger worktree's `handover/evidence/P8b`, exported once. State that both worktrees exist and where. |
| R3-ADV-2 | Major | 223, 227-231, 393 | "Pass needs every core file of one run to carry the same `base` and `head`". But `base.txt`, `table-keys.log` and `roles.log` are written at step 2, before the pages are committed (step 4). Their `head` is the `origin/main` commit. `t1.txt`, `t5.txt`, `t6.txt` and `scan.txt` carry the pages commit as `head`. As written the rule can never hold (or only holds if the inputs are re-run after step 4). The rule also contradicts "inputs at the step 1 head, before any page exists". Done item 2 depends on it. | Say the inputs carry `head` = step 1 head and must match on `base` only. Or re-run step 2 after step 4. Or drop `head` from the input logs. |
| R3-ADV-3 | Major | 379 | T4 drift runs "in the core checkout at the step 1 head". At that head `docs/kinds/` does not exist. The pages are committed at step 4. Drift on an empty folder passes trivially. | Change to "at the docs PR head (the commit of step 4 or the latest fix commit)". Add the same `hdr_core` same-head rule. |
| R3-ADV-4 | Minor | 112-113, 348-349, 411 | The ticket calls these strings "A6 words", but `amendments.md:9` says "second channel = email, trigger: a client needs email approvals" (comma) and "per-contract none/manual/http; http refused in pilot/prod, manual unbuilt". The ticket's required strings use `;`, "pilot and prod" and "manual not built". Pages and the T6 (d) greps follow the ticket, not A6. They will not drift-fail, but the "A6 words" claim is false. The old PENDING LEAD 3 "closed by A6" cites A6 as if the words were identical. | Either use A6's exact strings in the T6 (d) greps, or say "A6 paraphrased" and cite `amendments.md:9`. |
| R3-ADV-5 | Minor | 375 vs 397 | T5 pass is "no `MISSING`, or each `MISSING` followed by the replacement name the lead accepted". Done item 2 says "or its correction was sent to the lead". These two tests differ. `tests/test_redact*.py` is a known mismatch, so T5 can only pass by the lead's acceptance. | Use one rule in both places. |
| R3-ADV-6 | Minor | 207-212, 370-371 | P33 plants the origin/main README in a scratch copy, but the scratch copy is `cp -R docs README.md` of the committed (fixed) README. How the old README gets in is not stated (`git show origin/main:README.md > "$S/README.md"`). A builder has to guess. Also main README may already trip `FORBIDDEN-PHRASE` (UNVERIFIED), so "three MISSING-PHRASE lines" may be incomplete. | Give the exact command and say "at least these three lines". |
| R3-ADV-7 | Minor | 313 | T6 (a) builds the grep from `$be` unescaped (`grep -E "^\| *\`$be\` *\|"`). Backend names with `.`, `+` or `-` would still match, so it is only sloppy; but `\`` inside double quotes in dash is fine. Read-only note: if a backend name is a prefix of another, the `\|` anchor protects it. Low risk. | Optional: use `grep -F` with a built prefix. |
| R3-ADV-8 | Minor | 105, 176 | The 23-of-31 and 10-open-standard counts came from an author scratch run. They are not independently re-run here (UNVERIFIED). | None needed; they are already marked "not evidence". |
| R3-ADV-9 | Minor | 405 vs 288 | The Honest note and the awk text say "7 cells" and "NF != 9". The ledger header has 7 cells, and `NF=9` is right for the leading and trailing empty fields. This is correct but unexplained to a builder. | Add one sentence: NF = cells + 2. |
| R3-ADV-10 | Nit | 3, 9-33 | The changelog is long for a ticket (about 25 lines of history). It carries no builder decision. | Cut it to the build notes after freeze. |
| R3-ADV-11 | Nit | 170 vs 358 | T6 (e) runs the forbidden check on `docs/kinds/*.md`, which includes the index `README.md`, but the ticket text says "every page and the README paragraph". Fine, but say so. | One word. |

Template fields: all 17 are present in order, with the template's labels. The Reviewers field, the Done field and the Rollback field are complete.

Verified (read at the current `main` working tree, not at `4ec3616`, so line numbers could differ; none did):
- `table.py` lines: `TABLE` 386, `_UNVERIFIED` 380, `neutral` 344, `status` 338, `DEFAULTS` 582-588 (values secrets `fake`, signer `none`, anchor `none`, store `memory`, detector `regex`, channel `fake`, matching the ticket), `NOT_PROD` 604 (signer `none`, anchor `none`), `DEV_ONLY` 593, detector `regex` at 544 and `llm_judge` at 546-548. The 8 capability keys are the ones the ticket lists.
- Ledger header is `| id | package | severity | summary | status | verifying artifact | reviewed commit |` (`ledger.md:3`), matching the awk header regex and the NF=9 rule.
- Awk logic traced by hand for P1, P3, P5, P8, P15, P16, P22, P25 (output lines match the table). The separator-with-dash rule works. I did not run the awk.
- `README.md:31` contains "Redaction is pattern-based".
- `amendments.md:9` holds the A6 channel and executor outlines (wording differs, see R3-ADV-4).
- A6 plus `tests/test_executor.py` exist; `tests/contracts` and `tests/warden_port` were not re-listed.
- The Glob listing of `tests/test_*.py` shows none of the section 9 names (`test_redact*`, `test_stop_state*`, `test_usage*`, and so on), consistent with "only contracts and warden_port exist today".

Not checked (UNVERIFIED):
- Any script run (`t1.sh`, `t6.sh`, awk, `hdr_core`, `hdr_ledger`).
- `plan-v3.md` line cites (174-184, 185, 187, 188, 190).
- `LEAD-ORDERS.md` cites for orders 14, 15, 19 B/C, 20, 21 (only grepped numbers).
- `P1.md:20`, `P8a.md:78`, `inventory-A.md:10`.
- `config.py:366-369`, `:391-392` and `:71`, `guard/*` cites, `tools.py:744`, `actions/*` cites, `.github/workflows/ci.yml:83`, `pyproject.toml:57-58`.
- `tools/scan_repo.py` behaviour; the 31/23/10/6/2 counts; the dash and mawk behaviour of the scripts.
- Whether main README line 31 already contains a forbidden phrase (the grep output was too long to see).
