# fix-review2: round-2 fixes to REVIEW.md (2026-11-16)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-rev2/REVIEW.md

## What failed or is unverified (first)
- The patch files, the patched tree and DEAD-MAN-CHECK.md are not on disk. Every patched-copy cite, the exact lines of the A-4 write path in local_dir.py (reviewer cite :130 does not match src), and the X-2 table names rest on reviewer words; REVIEW.md now says so in a new 'Inputs read' section.
- No failing test for C-3 was written or run; REVIEW.md now says so.
- Reviewer round 2 (M-1..M-5) checked against src by me, all confirmed: config.py executor_timeout_s is at 360-362; k1b/loop.py:120-121, llm/common.py:167-168, llm/fake.py:51-52 multiply by route prices; chain.py:243-244 unguarded validate and DELETE; local_dir.py:143 ValueError only, :146 os.replace, :154 unlink; other write_outcome callers at limits.py:46, approvals/requests.py:82, runtime/agent_loop.py:241, k1b/audit_sink.py:39; cli.py:262-273 uses emit/emit_outcome; chain.py:229 last resort is a bare _pending append with no log (so A-4 'the chain kind has the ERROR' was wrong without A-01; corrected).
- Not done: the first row of heavy-lane numbers (70 tests = 5+10+41+14 whole files) was reworded from SUMMARY.md only; I did not recount the test files.

## Edits (REVIEW.md only)
Inputs-read section and cite convention; COUNTS_OUTPUT_PLACEHOLDER replaced by the real script output; script path fixed (script is in the folder); config.py:344 -> 360-362; src/patched/not-read tags on cites; C-3 siblings and 'config load not K1b replay'; A-1 other write_outcome callers and CLI _pending loss; A-4 corrected; A-5 raised to Major (tied to A-2); A-6 and X-3 siblings; X-2 detail (SELECT+INSERT audit entries, SELECT+DELETE outbox, own tick identity not stated, read-only role for dead-man SQL, negative tests); effective Major count under the lead's decision (3 live: C-3, G-1, X-2; 2 if X-2 waits with A-01; C-2 moot, A-01 Majors deferred); 'two choices' now 'three choices' (ceiling, K1bAudit, A-3 contract) in all places; 70-tests sentence; 10 vs 8 C-01 tests sentence; Not checked and round-3 note updated.
Count script output after edits: rows 22, Nit 10, Major 9, Minor 3, PROPOSE FIX 20, DECLINE 2. Round 3 review will follow.
