# PR89 result review, round 4 (head 58f7d56), reviewer egm:egm-codebase-details

Verdict from the reviewer: 0 Blockers, 0 Majors, 7 Minors/Nits. All 10 minors and the Major of round 3 verified FIXED by reading code and the builder's logs (reviewer could not run anything; it did not recompute sha256 pins nor exercise the Windows lock branch).

Open minors (to fix in one batch, no new review round needed unless the fix touches masking):
- M1 Evidence for "unchanged main runner" has no command and no sha256 of that runner: add both.
- M2 "-q -vv nets to verbosity 1": evidence shows only the outcome; say "observed: still shortened".
- M3 CHANGELOG, runner and mutation.py cite handover/evidence/P89 paths that do not exist in demo repos that byte-copy these files: cite command and output inline or commit the small files at a stable path.
- M4 lock file never deleted (one 0-byte file per DSN); open("a+b") follows a planted symlink in a shared temp folder (DoS only): O_NOFOLLOW and a private per-user folder; document.
- M5 _fragment_spans is O(hits x len(secret)^2) on a line up to 8 MB: cap line length or hit count.
- M6 Unmasked printed forms not listed in the CHANGELOG "not masked" list: JSON form (é), bytes repr, passwords containing quote/;/&, glued prefix (dbpassword=): add JSON form to _written_forms or list them.
- Nit: CHANGELOG:12 repeats the CanaryFailed sentence; canary exit codes -1000/-1001 read better as "timed out"/"reaped".
