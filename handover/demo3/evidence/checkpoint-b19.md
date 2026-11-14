# checkpoint B19 (lane3 fix-2 round 8)
Written 2026-11-14T06:23:31Z (started 06:06:52Z).

Done: tests first (75 failed / 21 passed on the unchanged tree, all behavioural, none function-absent: raw/b19-fails-before.log); read_secret_file (mode, lstat, inode, link text); Retry-After clamp in the three copies + constant; umask fixture; guards rebuilt (src covered, keyed allowances, reader/probe/Retry-After/shell additions); docs in one section of docs/settings.md; pins updated; E501 zero over changed .py files; mutation check (raw/b19-mutation.log) all killed.
Next: subset run of key-file tests (running), then the ONE full run on a clean clone, the two guard tests alone, patches, notes.
Blockers: none.
