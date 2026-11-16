# F8 flow-check report (ORDER 016), 2026-11-16 UTC (IST = UTC + 5:30)
Folder: handover/flows-audit/flow-check/. Not committed. Nothing was run in n8n. Standard library only. Made-up data only.

## 1. What failed or is unverified (read first)
1. **F-002 is NOT proven.** All four checker runs exit 0, but the patched form and hook flows still print `WARN ... F-002 Claim alwaysOutputData/onError UNPROVEN until T19`. What n8n does when the claim insert stores nothing (a repeat lead key) needs a real n8n run (T19, T20). Next step: the laptop lead runs T19 and T20.
2. **Severity differs from system-map M1 on one point.** M1 treats "webhook without authentication" as a FAIL (exit 1 on every entry flow). This checker prints a WARN by default (the owner's audit already lists it as L7-FD-005, none of the five patches adds a key) and FAILs only with `--require-webhook-auth`. With that option both of our runs also exit 1 (2 FAIL per run, the form flow and the e-mail-style flow). Exit 0 here does not mean "the form address is protected"; it is not.
3. **A reply gap remains in the patched flows (read from the file, not run).** In patched mf-form and mf-hook the steps `RunSub` and `Stored` still stop the run on error and the caller gets no answer. F-002 closes this for `Claim` only. Same finding as M1.
4. **Checks that only guard later changes (no file has the feature today):** switch nodes, sticky notes, secret values, missing credential blocks, `$node.X` dot form, duplicate webhook paths. They are proven only by the self-test cases, not by a real hit in the 16 flow files.
5. **Not checked:** whether n8n accepts the JSON (import), SQL inside the postgres nodes, expression syntax beyond node references, `$prevNode`, computed `$items(x)` names, httpRequest credentials sent through plain header values (only `authentication` set to something other than none requires a credential block), sub-workflow call results across files. The secret scan is pattern based: a secret in a shape not listed would pass; a harmless string in a listed shape would fail. The "reads a node that is not upstream" WARN never fired in the 16 files, so its false-positive rate is unknown.
6. **M3 is not a flow check.** In system-map QUEUE.md, M3 is the drift check of the take documents (`drift/REPORT.md`), not a flow-graph check. There is nothing to compare line by line with a flow checker; the comparison below is with M1 (`flowcheck/`), which is the flow-graph check (QUEUE.md line: "M1 ... flow-graph check of the patched flows").

## 2. What was built (extended from patch-apply/check_flows.py, nothing removed)
`check_flows.py` (old checks: parse, duplicate names, dangling links, orphans, unreachable, counts, IF/Switch outputs, error output wired, `$('X')` and `$items("X")` references, F-002/F-008 patch checks, diff against pristine). **New in F8:**
- `$node.X` dot references resolved (the old checker knew `$('X')`, `$node["X"]`, `$items("X")`); WARN when a referenced node is not upstream of the reading node, WARN on self reference.
- Sticky notes are left out of orphan/unreachable checks; FAIL for a file with only sticky notes (or only trigger plus notes); notes with links FAIL.
- FAIL: incoming link into a trigger; invalid connection shape or index; duplicate node ids; names that differ only by case/spaces; missing position or typeVersion; `onError` outside the three n8n values; `retryOnFail`/`alwaysOutputData` not boolean; `maxTries` outside 2 to 5; `waitBetweenTries` outside 0 to 5000.
- WARN: `alwaysOutputData` with `continueErrorOutput`; external-call nodes without retry (one line per file); external calls that continue on error; write node (mail, CRM) whose own error or an upstream call's error is swallowed; disabled nodes.
- Credentials: FAIL when postgres, emailSend, hubspot (or httpRequest with authentication) has no credentials block, or a credential has no name or no id; credential names, ids and every placeholder are listed per file.
- Secret scan: FAIL on AWS key id (except the one allowed example key), sk- keys, GitHub/Slack tokens, private key block, JWT, password in a URL, literal `Bearer` value, and literal values under keys like password/secret/token/apiKey. Fake values in the self-test are built from parts.
- Webhook answers: for each webhook with responseMode `responseNode`, every path must end in `respondToWebhook` (FAIL names the end node; FAIL if none is reachable); WARN lists steps whose failure stops the run with no reply. Other response modes are printed.
- Cross-file FAIL: two webhooks with the same method+path or the same webhookId.
- `--table` prints the error-settings table (onError, retry, alwaysOutputData) per file; `--files all`; `--require-webhook-auth`.
`selftest.py` runs 34 negative cases (each must exit 1 AND show its named text), 4 controls (exit 0) on the pristine flows and 4 negatives + 1 control on the patched flows. `run_all.sh` rebuilds the patched flows (F-002 then F-008 applied to a scratch copy, generator run for real and film) and runs the pristine and patched checks as two background processes, each under `timeout 300`.

## 3. Commands, exit codes, counts
| command | result |
|---|---|
| `bash run_all.sh /tmp/fc8` (applies both patches rc 0, generator real and film rc 0; two parallel background processes; wall time about 0.2 s) | raw: `raw/pristine.txt`, `raw/patched.txt`, `raw/diff-real.txt`, `raw/diff-film.txt` |
| pristine real-v5 (committed folder, `--baseline` itself, counts 12:11 12:11 10:9 20:26) | exit 0, 0 FAIL, 12 WARN |
| pristine film-v5 | exit 0, 0 FAIL, 12 WARN |
| patched real (F-002+F-008, counts 15:14 15:14 10:9 20:26, `--patch-checks F002,F008 --diff-base pristine --allow F002,F008`) | exit 0, 0 FAIL, 14 WARN |
| patched film | exit 0, 0 FAIL, 14 WARN |
| same four with `--require-webhook-auth` | exit 1 each, 2 FAIL each (the two entry flows) |
| `python3 -I selftest.py ../../demo/n8n-flows-real-v5 /tmp/fc8/g/real` (`selftest-new.txt`, raw cases in `selftest-output/`) | exit 0: 43 as expected, 0 not |
| same cases against the OLD patch-apply/check_flows.py (`FC_CK=...`, `selftest-oldchecker.txt`, `selftest-output-oldchecker/`) | exit 1: 21 as expected, 22 NOT (21 new negative cases not caught, plus the sticky-note control that the old checker wrongly fails). This is the proof the new cases fail on the old code. |
The diff files show the same node and connection changes as patch-apply round 3 (ADDED KeyOk, ReplyBadKey, ReplyStoreFail; Claim and Valid changed; settings changed by F-008); no unexplained change.

## 4. Differences from system-map M1 (`handover/system-map/flowcheck/`, branch origin/cloud/system-map after `git fetch origin cloud/system-map`, tool `tools/flowcheck.py`; a copy is in `m1/flowcheck_M1_copy.py`, its self-test printed `selftest ok`, `raw/m1-selftest.txt`). Same 16 files per state, raw `raw/m1-*.md`, comparison `raw/compare-m1-vs-f8.txt`.
1. Node and connection counts: 16 of 16 files identical (12/11, 12/11, 10/9, 20/26 pristine; 15/14, 15/14, 10/9, 20/26 patched, real and film).
2. Webhook without authentication: M1 FAIL (exit 1 on all 4 sets). F8 WARN, exit 0 (FAIL with option). Reason in section 1 item 2.
3. "Step stops the run on a path from a responseNode webhook": M1 WARN per step; F8 one WARN per webhook naming the same steps. Pristine: Claim, RunSub, Stored; patched: RunSub, Stored. Identical sets in all 8 form/hook files.
4. Mail step with an upstream call that continues on error: both warn the same pair in recovery (`AlertSend` after `AlertClaim`), 4 of 4 sets.
5. alwaysOutputData with continueErrorOutput: M1 FAIL rule, F8 WARN rule; neither fires in any of the 16 files (clean, as M1 states).
6. Only F8 reports: IF nodes without a second output (`StuckRow`, `AlertRow` in recovery; WARN because the baseline lacks them too), missing retry (one line per file), steps that continue on error, F-002 UNPROVEN line, patch content checks, node-level diff against pristine, expected counts, `$node`/`$items` references, sticky notes, secrets, credential blocks, webhook path ends, duplicate webhook paths, setting validity.
7. Only M1 reports: the per-file Markdown with webhook table, `$env` reads, save settings and write-path table (F8 prints the equivalents as the info lines and `--table`, in a different layout, not byte comparable), M1's rule that an httpRequest counts as a write only when its URL contains "crm" (F8 counts any non-GET httpRequest as a write; no flow file has such a node, so no output differs today).
8. Agreement on pass items: no parse failure, duplicate name, dangling link, orphan or unreachable node and no unresolved `$('Name')` in any of the 32 built files M1 checked; F8 agrees for the 16 it ran (pristine and patched: 8 + 8).
Paths tried for M1/M3: `git ls-tree -r --name-only origin/cloud/system-map | grep -i -E 'M1|M3|check'` found no M1/M3 output file by that name; M1's output is `handover/system-map/flowcheck/{REPORT.md,tools/flowcheck.py,evidence/md/*.md,evidence/summary-table.md}`; M3 is `handover/system-map/drift/REPORT.md` (not read for flows). Read with `git show origin/cloud/system-map:<path>`; the branch was present after the fetch.

## 5. Files
check_flows.py, selftest.py, run_all.sh, REPORT.md, m1/flowcheck_M1_copy.py (copy of the system-map tool, unchanged), raw/, selftest-output/, selftest-output-oldchecker/, selftest-new.txt, selftest-oldchecker.txt. Run order: `bash run_all.sh` first (it makes /tmp/fc8), then selftest.py.
