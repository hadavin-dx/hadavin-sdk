# fix-review6 (round 6 of REVIEW.md; static, made-up data, nothing committed)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-rev6/REVIEW.md
Opened by me in src before editing (read, not run): audit/chain.py 112-125, 176-232, 295-317; store/migrate.py 42-68, 193, 286, 340; app.py 87, 161; k1b/audit_sink.py 24-50; k1b/replay.py; store/postgres.py 326-352; approvals/requests.py 146-180; runtime/tick.py 85-97, 196; runtime/agent_loop.py 806-915; guard/injection.py 77; demos meter.py 48-55, fixtures.py 24-25; tests/contracts/kinds/builtin.py 20; config.py 61.
1 (X-4 example): fixed. checkpoint() never raises (chain.py:295-317); real route = failed _append with outbox INSERT (chain.py:223-227) succeeding; frequency not measured; "in this repository" added; same fix in the live-consequence paragraph.
2 (A-2 / K1bAudit): fixed. tick app.audit = make("audit") at app.py:161, never K1bAudit; K1bAudit docstring (audit_sink.py:38) defect kept as separate; "Open for the studio head" corrected.
3 (headline): fixed. Short answer, line 16 sentence, effective count (3 sure: G-1, X-4, X-5; 4 with C-3) and counts text agree.
4 (X-5): new row (Major, owner lead decision, live). X-2 "already granted" reworded; widening by client hooks stated.
Nits: X-3(b) shown impossible (chain.py:117/120/123); X-2 receiver UPDATE (postgres.py:350, requests.py:173); C-3 cites (meter.py:53-54, injection.py:77 opened, fixtures.py:24-25, builtin.py:20); C-4 frozen vs model_copy; single-dependency section added; A-3 note.
Not checked: patched-copy cites (still unchecked); nothing run; INSERT-only with ON CONFLICT for a role lacking SELECT not run.
