# Flow check (F8), round 1 fixes, 2026-11-16 (times in UTC; IST = UTC + 5:30)

**Bottom line: the checker finds no structural error in the 8 flow folders it was run on, but the flows are NOT shown to be ready to film. Exit code 0 only means "no structural FAIL". Known problems are open (section 1), and the checker never started n8n.**

What this is: a small program (`check_flows.py`) that reads the exported n8n flow files (JSON text files) and checks their wiring and settings without running n8n. A flow is one n8n workflow (here: `mf-form`, `mf-hook`, `mf-recovery`, `mf-sub-crm-mail`). Written for ORDER 016/017 (work orders for the flow audit). The files in this folder are not committed to git (the lead decides that). Python 3 only, no extra packages.

Words used in this report
- **FAIL** = the checker found a definite fault in the file; exit code 1. **WARN** = something a person must read; exit code stays 0. A WARN can be serious (see section 1).
- **real / film**: two versions of the same four flows. "real" is for the real filmed take; "film" is the made-up-data version for the video. Both are checked because they are separate files. The scan for secret-looking values ran on both and found none (it is pattern based: a secret in an unlisted shape would pass).
- **v5**: the 5th generated version of the flows (committed folders `handover/demo/n8n-flows-real-v5` and `n8n-flows-film-v5`).
- **pristine** = those committed folders as they are. **patched** = the same flows after patches F-002 and F-008 are applied to a scratch copy (generated again by `build_mainframe.py`).
- **F-002** = patch for audit finding F-002: the step `Claim` (writes the lead key, a made-up id, into the database so a repeated lead is only processed once) must still answer the caller when the key is repeated or the write fails. It adds `KeyOk` (is the key well formed), `ReplyBadKey` (answers 422) and `ReplyStoreFail` (answers 503). **F-008** = patch that makes n8n save the run records for the take.
- **T19, T20** = two tests of F-002 that must be run on a real n8n on the laptop (not here). **Caller** = whoever sent the web request (the form page or the hook).
- **Reply gap** = a step whose failure stops the run so the caller gets no answer at all. In the files: `RunSub` (calls the sub-flow) and `Stored` (final database write) in `mf-form` and `mf-hook`; `Claim` as well in the pristine version.
- **M1** = the earlier flow check by another agent on branch `cloud/system-map` (the comparison base). **M3** = a different check on that branch: it compares four take documents with each other (owner steps, agent scope, one-store decision, plan v5); it does not read flow files. I was asked to compare with M1 and M3; I compared with M1 only, because M3 is not a flow check. Please confirm that is what you wanted.
- **--baseline DIR** tells the checker which folder holds the unpatched flows: an IF step (a yes/no split) that already lacked its second branch there becomes a WARN instead of a FAIL. **Pristine without `--baseline` exits 1 with 2 FAIL** (`StuckRow`, `AlertRow` in `mf-recovery`; raw `raw/pristine-no-baseline.txt`). So "0 FAIL" below depends on `--baseline` excusing those two.
- Step names: `Claim` = write the lead key; `Stored` = write the result; `RunSub` = call the sub-flow; `Valid` = check the input; `AlertSend` = send the desk e-mail. Settings: `onError` = what a step does when it fails; `continueErrorOutput` = send the failure down a second output; `alwaysOutputData` = pass an empty result on instead of stopping; `responseNode` = the web answer is sent by a separate reply step.

## 1. What failed, is open or was not checked (read first)
Every number comes from a file in `raw/` (table in section 3).
1. **F-002 is not proven.** Both patched runs exit 0, but each prints "F-002 ... UNPROVEN until T19". What n8n does when a repeat key stores nothing needs a real n8n run (T19, T20). Who: the laptop lead. How long, and whether filming waits: no file I read says; the lead decides.
2. **The web addresses of `mf-form` and `mf-hook` have no password.** Anyone who knows the address can post. Default mode prints a WARN; M1 calls it a FAIL. **The owner decides** whether it is a FAIL. Both modes were run: default exit 0; `--require-webhook-auth` exit 1 (`raw/pristine-strict.txt`, `raw/patched-strict.txt`). This checker is therefore more lenient than M1 on this point.
3. **Reply gap remains** in the patched flows (`RunSub`, `Stored`): on a failure there the caller gets no answer. Read from the file; n8n was not run. Same finding as M1 (same step names in 8 of 8 form/hook runs, `raw/compare-reply-gap.txt`).
4. **New finding: 4 nodes read environment variables (`$env.NAME`).** real: `AlertSend` in `mf-recovery` (`DESK_ALERT_TO`) and `Qualify` in `mf-sub-crm-mail` (`DESK_URL`, `DESK_TIMEOUT_MS`); film: `Qualify` (`MF_STAGE_URL`, `MF_STAGE_TIMEOUT_MS`) and `CrmUpsert` (`MF_CRM_URL`). If the take blocks env access inside nodes, these nodes stop working. Default mode WARNs; `--block-env-access` makes each a FAIL (the strict runs show 4 FAIL per run: 2 webhooks plus 2 env nodes). I could not verify the name of the n8n switch that blocks env access: marked "n8n rule UNVERIFIED". The lead must decide: change the 4 nodes, or allow env access.
5. **Not checked at all:** that n8n accepts the files on import; the SQL inside database steps; expression syntax beyond node names; secrets in a shape the scan does not list. Rules about n8n itself with no source in this repo are now only WARN, marked "n8n rule UNVERIFIED": retry limits (2 to 5 tries, 0 to 5000 ms), the list of allowed `onError` values, and "the failure output is the last output of a step".
6. **A passing self-test proves the checker catches planted faults. It does not prove the real flows are right.**
7. The "reads a step that is not upstream" WARN never fired on the 16 real files, so its false-alarm rate is unknown. Several checks guard only future changes (no real file has switch steps, sticky notes, secrets, form triggers): proven by planted faults only.
8. Not redone: the M1 comparison was not re-run with the new checker. Counts and reply-gap step names were compared again from existing raw files (`raw/compare-m1-vs-f8.txt`, 16 of 16 same). Old `patch-apply` numbers were not reproduced.

## 2. What the checker does now
Closing block on every run: "Known open problems: N" (WARN lines that are real open defects: no password on a web address, reply gap, F-002, env reads), "Not proven: ...", "Passing this check does NOT mean the flows are ready to film." The exit code depends only on FAIL.
- **FAIL:** file does not parse or has the wrong shape (a FAIL line, no crash); duplicate step names or ids; link to or from a step that does not exist; step with no way in; step no trigger can reach; wrong step or link count; IF step with a branch leading nowhere (project rule); failure output missing; missing position or version; wrong value types; missing credentials; secret-looking value (keys, tokens, private key, password in a URL, `Bearer` value, literal value under keys like password/token/apiKey) in any step, sticky note or top-level key; web reply paths that end without a reply step (a disabled reply step or disabled webhook does not count); two webhooks with the same address or id.
- **WARN:** section 1 items, steps without retry, steps that swallow errors, mail or CRM steps after swallowed errors, unwired Switch outputs, disabled steps, `$prevNode`, reading a step that may not have run, `alwaysOutputData` with a failure output (F-002 pattern).
- **Options:** `--require-webhook-auth`, `--block-env-access`, `--baseline`, `--patch-checks`, `--diff-base`, `--table`, `--files all`, `--expect`.
- **Credentials per flow** are always printed. Real flows: Postgres credential `n8n-publish-pg` (id is the placeholder `PG_CREDENTIAL_ID`) and SMTP credential `mf-mail-smtp` (placeholder `SMTP_CREDENTIAL_ID`); placeholders must be replaced in n8n.
- **Which checker:** `flow-check/check_flows.py` replaces `patch-apply/check_flows.py` (pointer line added there). M1 (`flowcheck.py` on branch `cloud/system-map`, commit `a14a437cbeb8facaac3c19d54ea45a5c4a8fdb79`, confirmed with `git log -1`) is a separate tool; the byte-identical copy in `m1/` was replaced by `m1/POINTER.txt`. Raw M1 outputs stay in `raw/m1-*.md`.
- Round-1 review findings, one line each: `fix-f8-r1.md`.

## 3. How to run, and where every number comes from
`bash run_all.sh` (default work folder `/tmp/fc8`; it deletes only that exact folder and creates it itself). It applies both patches to a scratch copy, generates the patched flows, runs the checker four times (pristine and patched, default and strict), runs the self-test, and exits 0 only if the 4 default runs and the self-test exit 0. Last run: exit 0.

| what | result | raw file |
|---|---|---|
| pristine real and film, default | each exit 0, 0 FAIL, 14 WARN, 6 known open problems | `raw/pristine.txt` |
| patched real and film, default | each exit 0, 0 FAIL, 16 WARN, 8 known open problems | `raw/patched.txt` |
| pristine, strict (`--require-webhook-auth --block-env-access`) | each exit 1, 4 FAIL | `raw/pristine-strict.txt` |
| patched, strict | each exit 1, 4 FAIL | `raw/patched-strict.txt` |
| pristine real without `--baseline` | exit 1, 2 FAIL | `raw/pristine-no-baseline.txt` |
| self-test, new checker | exit 0: 368 as expected, 0 not, 20 skipped (case does not apply to that file) | `raw/selftest-new.txt`, cases in `selftest-output/` |
| same cases, OLD checker | exit 1: 68 as expected, 300 not. Caution: many fail only because the old checker does not know the new options; this shows the new cases do not pass on old code, not 300 separate bugs | `raw/selftest-oldchecker.txt` |
| patch and generator steps | logs and a list of generated flow files with short hashes | `raw/apply.log`, `raw/gen-real.log`, `raw/gen-film.log`, `raw/patched-flows-list.txt` |
| what the patches change | no unexplained change (patched runs exit 0) | `raw/diff-real.txt`, `raw/diff-film.txt` |
| M1 comparison | counts 16 of 16 same; reply-gap steps same in 8 of 8 | `raw/compare-m1-vs-f8.txt`, `raw/compare-reply-gap.txt` |
| time | four checker runs together under 1 s (whole-second clock shows 0 s); self-test 17 s | `raw/timing.txt` |

Self-test rules (`selftest.py`): each case plants ONE fault in a copy and requires the exit code, a line that STARTS with FAIL (or WARN) holding the named text, and no unrelated FAIL line. Cases run on 4 real files and 1 film file. Optional settings `FC_CK` (another checker) and `FC_OUT` (output folder) are described at the top of the file. Counts are recomputed so a count mismatch is not a hidden second cause.

M1 versus this checker: webhook without password: M1 FAIL, here WARN by default (item 2); `alwaysOutputData` with failure output: M1 FAIL, here WARN with the F-002 reason (neither fires in the 16 files); only here: IF steps with one branch, retry, env reads, credential blocks, patch content, diff against pristine, expected counts, secrets, sticky notes; only in M1: its per-file markdown tables.
