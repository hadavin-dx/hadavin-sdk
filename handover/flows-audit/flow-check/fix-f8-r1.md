# F8 fixer round 1 change log (2026-11-16 UTC). Raw run: raw/ (run_all.sh exit 0; selftest 368/0/20 skipped).
zoom-out
- Z1 closing block (known open problems, not proven, not ready to film): fixed, check_flows.py final_block(); exit tied to FAIL only.
- Z2 run_all.sh exit status: fixed (statuses taken from the checker runs and the self-test; `set -u`).
- Z3 REPORT listed --require-webhook-auth runs run_all did not run: fixed, run_all runs them (raw/*-strict.txt).
- Z4 webhook auth WARN vs M1 FAIL: both modes run and shown; decision marked as the owner's (REPORT 1.2).
- Z5 scope creep: partly disputed. Checks without a real hit are kept because each has a planted-fault case and guards future changes; REPORT 1.7 says so. A repo-wide secret guard was not searched for (not checked).
- Z6 three checkers: fixed. REPORT says which replaces which; patch-apply/REPORT.md got a pointer line; m1/ copy replaced by m1/POINTER.txt (sha a14a437c... confirmed by git log; copy was byte-identical).
- Z7 REPORT readability: fixed, rewritten (bottom line first, every label explained).
- Nits: M3 read (git show origin/cloud/system-map:.../drift/REPORT.md) and stated; `--files all` per folder fixed; form trigger without password now WARN/FAIL (parameter name marked UNVERIFIED); selftest /tmp/fc8 dependence removed (paths are arguments), FC_CK/FC_OUT documented; "0.2 s" replaced by measured timing (raw/timing.txt).
codebase
- C-not-confirmable no raw file for strict runs and gen/apply logs: fixed (raw/).
- C1 unsourced n8n rules: fixed. onError value list, maxTries, waitBetweenTries are WARN "n8n rule UNVERIFIED"; error output is the last output (IF 2, Switch rules+fallback); Filter has one output (no false FAIL); unwired Switch output is WARN.
- C2 missing self-test cases: fixed, cases added for every listed check (shape, typeVersion, waitBetweenTries, maxTries without retry, not upstream, $prevNode, disabled, webhookId, sticky links, trigger plus notes, 8 secret shapes, credentials, silent error, write node, alwaysOutputData). Vacuous control replaced by a WARN case that must show a new WARN line. Disputed in part: "alwaysOutputData WARN can never fire" is wrong, it fires on a planted case.
- C3 traceback on malformed JSON: fixed (shape_ok plus per-file try/except; RESULT line always printed); 9 shape cases.
- C4 secret scan: fixed. Sticky notes and top-level keys scanned; ALL-CAPS bypass removed (only the repo placeholder tokens and pure $env/$credentials references pass; real flows still pass, 0 FAIL); key match no longer fires on passThrough (control case).
- C5 disabled reply or webhook counted as a reply: fixed (+3 cases).
- C6 webhook auth only for webhook nodes: fixed for formTrigger; both modes run.
- C7 self-test accepted FAIL text anywhere and unrelated FAILs: fixed (line must start with FAIL/WARN, stray FAILs rejected, counts recomputed); negatives now run on mf-hook, mf-recovery, mf-sub-crm-mail and the film form file.
- Nits: rm -rf guarded (only /tmp/fc8 default; other dirs must be empty); selftest rmtree guarded; ALLOW_CONN scoped to form/hook files; `--files all` with `--expect` fixed; "no reply" list now includes code steps. Not changed: node without id not flagged (n8n id rule unverified, no source).
comprehension (read after it appeared)
- Fixed in REPORT: purpose and "not safe to film" up front, WARN/FAIL and all labels defined, who runs T19/T20 (time not stated in any file: said so), "Not committed" explained, 0 FAIL depends on --baseline (pristine without it: exit 1, raw/pristine-no-baseline.txt), every number has a raw file, real vs film explained, M3 stated as "asked X, did Y, please confirm", M1 path narrative removed.
ORDER 017
- connection source/target missing: FAIL, self-test cases added (connection_source_not_a_node, dangling). alwaysOutputData with failure output: WARN with F-002 reason + case. $env reads: new WARN, FAIL with --block-env-access; real flows have 4 such nodes (finding, REPORT 1.4). Credential names printed per flow always. Webhook auth: both modes.
