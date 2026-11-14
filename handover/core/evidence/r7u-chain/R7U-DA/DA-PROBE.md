# DA-PROBE: does exit code fail on every "Design A" run? (evidence runner, facts only)

## FAILED / NOT RUN (first)
- NOT RUN: the `--dry-fakes` end-to-end main() path on tree-R7T and tree-R7S. The only way to run it without a
  y/N question is `--assume-yes` (tests/test_real_check_dry.py:33 calls `rrc.main(["--dry-fakes","--assume-yes"])`).
  My brief forbids an --assume-yes run and answering yes, so I stopped there.
- NOT RUN: any Design A run. No setting for it exists in the code (see 1c), so nothing to run.
- Not checked: the actual Design A desk (it is a design, not code in tree-R7T). Everything below is about tree-R7T code.
- Run done instead: two in-process unit experiments, no network, no prompts (probe.py, probe2.py; outputs
  probe-tree.out, probe-trees.out, probe2-tree.out in this folder). Copies of both trees were deleted afterwards.

## 1. What the code does (tree-R7T, file:line)
a. Counter file written when: HubspotCrm.__init__ (crm_hubspot.py:243-261) only builds the dict `_n`, which already holds
   "created": 0 (line 250); it writes nothing. The file is written by `_count` (280-284), `_settle_create` (286-295) and
   inside `_call` (402 for non-create calls, 392 strict write for a create). `_call` is used by put (creates, line 424),
   set_fields (patch, 461), rows_with_prefix/wait_visible/archive (run-script only: "never by the desk", comment at 508;
   run_real_check.py:1260 builds its own HubspotCrm with stats_file=None). So the desk writes the file only on its first
   HubSpot call of any kind (create or patch), NOT at start-up, and every write contains `created` (value 0 until a 201).
   Experiment probe2: after construct file exists = False; after one `_count` the file holds "created": 0.
b. Who calls the CRM: desk.py:1780 `self.crm.put(...)` for every lead that reaches the CRM step; desk.py:875
   `self.crm.set_fields` only with a leadflow file. desk.py:591/610 look for `refresh`/`forget_capability`, which
   HubspotCrm does not have. So with DESK_CRM=hubspot a counter file appears as soon as one lead reaches the CRM step.
c. Choices: DESK_ADAPTERS only "demo" (constants.py:142). DESK_CRM is "fake" (HttpCrm to the fakes server, loader.py:77)
   or "hubspot" (HubspotCrm, loader.py:75) (constants.py:152-155, config.py:512). There is NO "no CRM adapter" kind.
   run_real_check.py:1122 forces `DESK_CRM=hubspot` for every run (real and dry); Desk.start (873-877) always sets
   DESK_HUBSPOT_STATS_FILE to desk-<tag>-<label>.hubspot.json. No switch for "CRM is written by n8n, not the desk"
   (grep "Design A" and DESK_CRM across src, scripts, tests: none beyond the above).
d. counter_is_known (run_real_check.py:931-936) = files > 0 and unreadable == 0 and "created" in totals.
   Used at 1377; false -> prints the "cannot be trusted" message (1378-1383) and exit_code_of (625-628) returns EXIT_FAILED (=1, line 116).
   Hub read at 1306 reads files named desk-<tag>-*.hubspot.json.

## 2. Experiment (unit, tree-R7T) probe-tree.out
    case1 (no counter file): CounterRead(totals={}, files=0, unreadable=0) known: False
          exit_code_of(ok=True,written=True,[],0,known) = 1 (EXIT_FAILED = 1)
    case2 (file with created:0, calls:1, patch:1): known: True, exit 0
    case3 (file without "created"): known: False

## 3. Same on tree-R7S, probe-trees.out
    r7s has no counter_is_known; exit_code_of takes 4 args; contacts_not_accounted_for(None,0) = 0
    case1 (no file): totals {}, unseen 0, exit_code_of(True,True,[],0) = 0
Diff r7s vs r7t confirmed by `diff` of scripts/run_real_check.py: r7t adds CounterRead, counter_is_known, the 5th argument.

## Additional fact (found while reading, not asked)
floor_checks F4 (run_real_check.py:~418-427) needs `smtp_stats.get("sent")` from desk-<tag>-*.smtp.json
(DESK_SMTPP_STATS_FILE, written by smtp_provider.py:60,104). If n8n sends the mail and the desk's SMTP adapter never
runs, that counter is absent too: sent_total None -> F4 not ok -> result["ok"] false. floors F1-F4 text is identical in r7s and
r7t (diff of lines 330-440 empty), so that failure would exist in r7s as well. Not run; read from code only.

## Answer
Is the exit code failing on every Design A run? Cannot tell for sure; yes if the desk makes no HubSpot call at all.
- Rule from code: in r7t exit is 1 whenever no desk-<tag>-*.hubspot.json exists or it lacks "created" (proved by unit case 1);
  in r7s the same state gave 0 (proved by unit case 1 on r7s).
- The file exists as soon as the desk makes ANY HubSpot call (create or patch), with created:0 (proved, probe2).
  Under Design A, if the desk never calls HubspotCrm (no put, no set_fields), no file -> r7t fails every time.
  If the desk still calls put (the code in r7t always does for each lead), the file exists and this check passes.
- The code in r7t has no Design A mode, so whether Design A hits this depends on how it is built. Not run end to end.
