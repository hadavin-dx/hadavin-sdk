# flow-check round 2 false passes review (fresh reviewer a6ad3edf, condensed; read only, nothing run)
No Blocker; 7 Majors.
1 settings null/[] crashes check_flows.py:533 (shape_ok :84-103 does not validate settings); REPORT.md:32 "no crash" contradicted; no self-test.
2 cross_file (:299,:303-305, call :544 outside try) crashes on webhook parameters non-empty list/string or dict/list webhookId; json.load(open(p)) leaks handle (:295).
3 --files all on empty dir / no *.json: "0 FAIL" exit 0 with nothing checked (:521-523).
4 unknown --patch-checks token (F02, F-002) silently ignored (:501,:416,:443); pc not validated against {F002,F008}.
5 $env forms not matched: ENVTOK (:47) only $env.NAME; misses $env["X"], process.env.X; :127 treats blocks starting $json/$node as safe so literal secret inside passes.
6 webhook authentication headerAuth/basicAuth without credentials block passes (:245-252, :233-238); credential kind not matched to node kind; credential names n8n-publish-pg, mf-mail-smtp printed, never asserted.
7 self-test has no case failing if checks removed: F-002 patch content (:430-442: Claim onError, KEY_COND, 503 code, $('Valid') ref, no F-002 nodes in recovery/sub), F-008 settings (:443-447), node_diff (:461-484 unexplained added/removed/changed node, settings, top-level), WARN :285 and :259, secret scan list branch :138, argument errors/exit 2, skipped cases (f_bad_ref_reply, f_selfref_ok unused; 20 skips not broken down); nobody ran remove-each-check mutation (evidence-rerun-2 ran 9 mutants, all killed, but not these).
Nits: val() IndexError exit 1 not 2 (:491-492); --expect-json TypeError; sticky note text scanned for $('Name') false alarm (:364-368); orphan rule/ is_trigger misses cron; short secrets <=5 chars pass; duplicate JSON keys; baseline equals target in run_all.sh so IF-branch FAIL cannot fire on pristine (REPORT.md:16 honest, :32 reads otherwise).
REPORT.md missing from unverified list: credential kind/name/webhook auth attachment, $env forms beyond .NAME, shape claim only for fields shape_ok reads.
Not checked: ran nothing; raw/ outputs; flow JSON.
