# U4B notes (contract.md lines 161-317). Base /tmp/cf4-base. Patch: /tmp/work/claims-fix4-U4B.patch (sha256 61069331cf0da9445cf454112fad5fc48a2f178fe4e27554651bc1410166a94a)
Only checked: git apply --check on a fresh copy (OK), poison grep of added lines (only the two pre-existing `http://[/` and example address texts on edited lines). No tests run; all evidence read from files.
Format: contract line (by words) | audit verdict | my verdict | change | evidence

1. "refused connect ... about 2 seconds" (173) | UNBACKED | F | added "(from the author's own run on a Windows computer; no log is shipped)" | docs/limits.md says author logs not shipped; no repo measurement
2. "All desk replies ... JSON" (178) | UNBACKED (absolute All) | W | none: text already says "JSON, except the GET /ui 308 and /ui/<file>" | contract.md:178
3. 408 counts in rejected_envelopes (159, 261) | UNBACKED | S + F | pointer to tests/test_server_hardening.py (asserts count 1 after a stalled body); noted a stalled header 408 is not counted | server.py:962-965 (body: counted), :584 (header: not counted)
4. "403 from the gate does not count" (261) | UNBACKED | F | "by the code in server.py the gate never calls the counter; no test asserts it" | only server.py:944,963 call note_rejected_envelope
5. step route 503/500 (208) | UNBACKED | S (503) + F (500) | pointer to tests/test_lead_step_route.py:479-486 for 503; 500 labelled generic error path, no test | desk.py set_step except -> _error_reply
6. "offset 0..100000" (215) | UNBACKED | W (audit wrong; added pointer only) | number is OFFSET_MAX in src/lead_desk/constants.py:266; tests/test_portal_api.py:359, :707 (100000 ok, 100001 bad)
7. needs_action "same number as tabs.action" (214) | UNBACKED | F | "meant to equal ...; no test compares the two" | tests/test_portal_api.py:232 (5) and :449 (action 5) are separate asserts
8. log "never email, phone, company or message" (220) | UNBACKED-unverified | S | pointer to the log-shows-no-personal-data test | tests/test_portal_log.py:170-190
9. "value tables should never hold shown as review/unknown" (220) | UNBACKED | S | pointer | tests/test_portal_log.py:203-208
10. AI step input 500 (222) | UNBACKED | S | pointer | portal_api.py:986-994; tests/test_portal_log.py:296-321 (refusals) and the 500 assert at ~:298
11. fakes-server block (227-236) | unverified | S/F | verified line by line against demo_only/fakes_server.py. Fixed two gaps: GET /fake/outbox also returns `reminders` (fakes_server.py:81-86); the 422 of POST /fake/crm/fields also carries `mode` (:171). Rest matches (statuses, bodies, controls, no_contact, info, reset). "asking again is harmless" softened to "meant to be harmless: fake overwrites; real CRM not checked". test_reply_does_not_wait_for_send exists (tests/test_http.py:254)
12. email subject/body/CRM record (237) | unverified | S | pointer to constants.py:101-102; texts equal tests/test_infra.py:20; record fields equal desk.py:1692-1699 (lead_id,name,email,company,source,ai_label)
13. burst output formats (238) | unverified | W | no change: matches demo_only/burst.py:155-161 (SENT/STATUS/RETRIES/RESULT/MISMATCH) and constants.py:93-95 (0.1, 1.0, 30.0)
14. "never merge two" mailboxes (252) | UNBACKED | F | "the source has no normalising step, so it should not merge two; no test asserts that" | grep for normalize in src finds none
15. retry never 200 sending (259) | BACKED (absolute unverified) | S | pointer for the 409 | tests/test_http.py:219-227
16. Desk.process never raises (265) | UNBACKED (absolute) | F | "catches direct input JSON cannot write ... instead of raising; tests check deep nesting only" | desk.py:1349-1356 guard; tests/test_desk_http_edge_cases.py:1074-1078
17. crash in migration changes nothing (273) | UNBACKED | S + F (audit partly wrong) | now "a failure in the middle": test_failed_migration_rolls_back injects an error at start and end and compares the book; killed process not tested | tests/test_desk_http_edge_cases.py:656-668; db.py:133-156
18. non-WAL file refusal (277) | UNBACKED | W | none: tests/test_desk_edge_cases.py:432-448 (test_wal_refused_raises) asserts RuntimeError when the switch is refused
19. chdir (279) | UNBACKED | S | pointer | tests/test_desk_http_edge_cases.py:1517-1531 (test_path_is_fixed_at_construction)
20. "no window / no second put ever" (289) | UNBACKED absolute | F | now scoped to the crash points the named tests cover, "no test covers every path" | tests/test_crash_points.py, tests/test_desk_http_edge_cases.py:1220-1243
21. replays cannot use up the 5 tries (303) | UNBACKED | F | "not meant to ...; tests/test_flow.py shows one drive; no test replays many times against the limit" | tests/test_flow.py:114-132; tests/test_followup_edge_cases.py:155 is a busy-answer case, not replay
Skipped (stage 1): 269, 275, 294, 309.

Counts: S 7 (rows 8,9,10,12,15,19 plus S part of 5), F 8 (1,4,7,14,16,20,21 plus F part of 3/5/17 mixed), W 5 (2,6,13,18 plus 11 partly S/F). Mixed rows counted once under main verdict: S 6, F 9, W 4 (rows 2,6,13,18), 11 S/F.
Owner questions (O): none.
Not verified: the Windows 2-second figure (no way here); real-CRM idempotence of set_fields; whether needs_action and tabs.action are always equal (only the code could show it; I did not read both code paths); the 500 assert line number in test_portal_log.py is approximate (~298).
