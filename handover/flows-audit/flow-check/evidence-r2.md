# evidence-r2 (EVIDENCE RUNNER, raw output, no judgement), 2026-11-16 UTC

## FAILURES / NOT-AS-CLAIMED FIRST
- ruff check on flow-check: exit 1, 213 errors (UP031 152, SIM115 15, RUF015 11, BLE001 7, B007 6, FLY002 4, B023 3, I001 2, EXE001 2, S603 1); 143 check_flows.py + 70 selftest.py counted by location lines; 4 auto-fixable.
- ruff format --check: exit 1, 2 files would be reformatted (check_flows.py, selftest.py), 14 already formatted.
- bandit -ll -r: exit 0; 0 Medium, 0 High, 3 Low (below -ll threshold).
- Mutation (20 random single-check removals, scratch copy): 17 caught, 3 SURVIVED (mut12 line389 'cannot tell which output is error output' WARN; mut13 line398 'switch cannot tell output count' WARN; mut14 line462 'F-002 node missing' FAIL in patch_checks). These 3 are NOT among the fixer's 3 claimed survivors (cross_try, arg_missing_value, expect_json_object); different mechanism (fixer removed whole checks, here single fail/warn call lines).
- Fixer claims otherwise matched: run_all 0; self-test 469/0/32; real flows 8 patched / 6 pristine known open problems; strict 4 FAIL.

## (1) run_all.sh: exit 0 (22 s). Tail:
```
Known open problems: 2
exit=1
######## pristine-strict film
RESULT: 4 FAIL, 10 WARN
Known open problems: 2
exit=1
[patched-strict]
######## patched-strict real
RESULT: 4 FAIL, 12 WARN
Known open problems: 4
exit=1
######## patched-strict film
RESULT: 4 FAIL, 12 WARN
Known open problems: 4
exit=1
[selftest exit=0] SELFTEST: 469 as expected, 0 not as expected, 32 skipped (not applicable)
run_all exit status: 0

real	0m22.003s
user	0m17.906s
sys	0m3.799s
rc=0
```

Per-run exit codes in raw/*.txt:
```
raw/pristine.txt:132:exit=0
raw/pristine.txt:261:exit=0
raw/patched.txt:179:exit=0
raw/patched.txt:355:exit=0
raw/pristine-strict.txt:128:exit=1
raw/pristine-strict.txt:253:exit=1
raw/patched-strict.txt:175:exit=1
raw/patched-strict.txt:347:exit=1
```

## (2) self-test standalone (python3 -I selftest.py real-v5 /tmp/fc8/g/real film-v5): exit 0
```
duplicate_json_key_is_fail (exit 1)                                      as expected
SKIPPED, by case name (a case is skipped on a file that lacks the node type it needs): form_trigger_auth_without_credentials=2, form_trigger_without_auth_default=2, form_trigger_without_auth_strict=2, silent_error_external_call=1, webhook_auth_without_credentials=2, webhook_dead_branch=2, webhook_disabled_no_trigger=2, webhook_id_dict_no_crash=2, webhook_id_list_no_crash=2, webhook_id_reused_in_other_file=2, webhook_no_reply_node=2, webhook_parameters_list_no_crash=2, webhook_parameters_text_no_crash=2, webhook_path_reused_in_other_file=2, webhook_reply_node_disabled=2, write_node_continues_on
SELFTEST: 469 as expected, 0 not as expected, 32 skipped (not applicable)
```

## (3) checker on handover/demo/n8n-flows-real-v5 and -film-v5 (--baseline itself): exit 0 both
```
-- real
RESULT: 0 FAIL, 14 WARN
Known open problems: 6
-- film
RESULT: 0 FAIL, 14 WARN
Known open problems: 6
```
Full raw: /tmp/claude-0/ev/chk-real.out, chk-film.out (scratchpad, not kept in repo); run_all outputs in raw/.

## (4) lint
```
ruff check: rc=1

Found 213 errors.
[*] 4 fixable with the `--fix` option (143 hidden fixes can be enabled with the `--unsafe-fixes` option).
ruff format --check: rc=1
bandit -ll -r: rc=0
	Total issues (by severity):
		Undefined: 0
		Low: 3
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
```

## (5) mutation, seed 20261116, scratch /tmp/claude-0/ev/mut, FC_CK env pointing to mutated copy; real folder untouched
```
mut0 line100 rc=1 caught=YES | fail(tag, "parse failure: duplicate JSON key %r (n8n keeps only the last one, so the file  -> pass | SELFTEST: 468 as expected, 1 not as expected, 32 skipped (not applicable)
mut1 line102 rc=1 caught=YES | fail(tag, "parse failure %s" % type(e).__name__); return None -> pass | SELFTEST: 464 as expected, 5 not as expected, 32 skipped (not applicable)
mut2 line244 rc=1 caught=YES | if near: fail(tag, "names that differ only by case or spaces %s" % near) -> if near: pass | SELFTEST: 464 as expected, 5 not as expected, 32 skipped (not applicable)
mut3 line251 rc=1 caught=YES | if not isinstance(n.get("typeVersion"), (int, float)) or isinstance(n.get("typeVersion"),  -> if not isinstance(n.get("typeVersion"),  | SELFTEST: 464 as expected, 5 not as expected, 32 skipped (not 
mut4 line252 rc=1 caught=YES | if n.get("onError") not in ONERROR_OK: warn(tag, "node %s onError=%r is not one of stopWor -> if n.get("onError") not in ONERROR_OK: p | SELFTEST: 464 as expected, 5 not as expected, 32 skipped (not 
mut5 line258 rc=1 caught=YES | elif "maxTries" in n or "waitBetweenTries" in n: warn(tag, "node %s sets maxTries/waitBetw -> elif "maxTries" in n or "waitBetweenTrie | SELFTEST: 464 as expected, 5 not as expected, 32 skipped (not 
mut6 line278 rc=1 caught=YES | else: warn(tag, msg + " [run with --block-env-access to make it a FAIL]", known=True) -> else: pass | SELFTEST: 464 as expected, 5 not as expected, 32 skipped (not applicable)
mut7 line284 rc=1 caught=YES | if OPTS["webhook_auth"]: fail(tag, msg) -> if OPTS["webhook_auth"]: pass | SELFTEST: 464 as expected, 5 not as expected, 32 skipped (not applicable)
mut8 line290 rc=1 caught=YES | if au not in ("none", None, "") and (not isinstance(cr, dict) or not cr): fail(tag, "form  -> if au not in ("none", None, "") and (not | SELFTEST: 466 as expected, 3 not as expected, 32 skipped (not 
mut9 line293 rc=1 caught=YES | if OPTS["webhook_auth"]: fail(tag, msg) -> if OPTS["webhook_auth"]: pass | SELFTEST: 466 as expected, 3 not as expected, 32 skipped (not applicable)
mut10 line314 rc=1 caught=YES | if ref == n["name"]: warn(tag, "node %s reads its own output $('%s')" % (n["name"], ref)) -> if ref == n["name"]: pass | SELFTEST: 464 as expected, 5 not as expected, 32 skipped (not applicable)
mut11 line342 rc=1 caught=YES | if ("id", wid) in seen: fail(dr, "two webhooks share webhookId %r: %s and %s" % (wid, seen -> if ("id", wid) in seen: pass | SELFTEST: 466 as expected, 3 not as expected, 32 skipped (not applicable)
mut12 line389 rc=0 caught=NO | if normal is None: warn(tag, "node %s: cannot tell which output is its error output (%s)"  -> if normal is None: pass | SELFTEST: 469 as expected, 0 not as expected, 32 skipped (not applicable)
mut13 line398 rc=0 caught=NO | if not normal: warn(tag, "switch node %s: cannot tell its output count" % n["name"]) -> if not normal: pass | SELFTEST: 469 as expected, 0 not as expected, 32 skipped (not applicable)
mut14 line462 rc=0 caught=NO | if not get(d, nm): fail(tag, "F-002 node %s missing" % nm) -> if not get(d, nm): pass | SELFTEST: 469 as expected, 0 not as expected, 32 skipped (not applicable)
mut15 line466 rc=1 caught=YES | if tg(s, i) != want: fail(tag, "F-002 link %s out%d -> %s expected %s" % (s, i, tg(s, i),  -> if tg(s, i) != want: pass | SELFTEST: 468 as expected, 1 not as expected, 32 skipped (not applicable)
mut16 line468 rc=1 caught=YES | if d["connections"].get(nm) != want: fail(tag, "F-002 connection structure of %s is %s exp -> if d["connections"].get(nm) != want: pas | SELFTEST: 468 as expected, 1 not as expected, 32 skipped (not
mut17 line502 rc=1 caught=YES | if nm not in allow_added: fail(tag, "unexplained added node %s" % nm) -> if nm not in allow_added: pass | SELFTEST: 468 as expected, 1 not as expected, 32 skipped (not applicable)
mut18 line516 rc=1 caught=YES | if not any(src in ALLOW_CONN.get(a, ()) and fname in ("mf-form.json", "mf-hook.json") for  -> if not any(src in ALLOW_CONN.get(a, ())  | SELFTEST: 467 as expected, 2 not as expected, 32 skipped (not
mut19 line521 rc=1 caught=YES | if not any(k in ALLOW_SETTINGS.get(a, {}).get(fname, ()) for a in allow): fail(tag, "unexp -> if not any(k in ALLOW_SETTINGS.get(a, {} | SELFTEST: 468 as expected, 1 not as expected, 32 skipped (not
```
Verified for mut2, mut4, mut6: mutated file compiles, and the named self-test cases fail (not a syntax-error false catch).
