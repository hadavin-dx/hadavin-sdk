# SONAR-PATH round 6 codebase review (egm-codebase-details), head 4398e3bd
Read-only reviewer, ran no code. Verdict: 0 Blocker, 2 Major, 9 groups of nits.
M1 tools._module_files (tools.py ~256-265): per-part limit 252 bytes, but part count and whole path are unbounded; 17 parts of 252 bytes exceed 4096 and on Python 3.12 Path.is_file re-raises ENAMETOOLONG as a raw OSError carrying the path. CHANGELOG "13 sites, 3 leaked, fixed" is false for total length. Fix: cap parts/total bytes or run the built path through pathguard.inside.
M2 tests/test_pathguard_batch3.py 177-183: the R5 "exactly the limit" test builds 4095 bytes, so mutating > to >= at pathguard.py:142 is not killed; no off-by-one mutant row. Fix: build exactly 4096 and add the row.
N1 4096 limit vs Linux PATH_MAX 4096 incl. NUL (largest usable 4095); must_exist=False without kind does no file call after resolve; operator_dir/operator_file measure typed text only.
N2 LocalDirSink write_outcome vs write_intent treat id "abc." differently; "event id refused" can blame the id for an unrelated refusal.
N3 two new tests depend on tmp_path length (20x201 bytes) and error on long prefixes.
N4 sweep test docstring says 13 sites, checks 9 files.
N5 stale exemption label != "inside" in batch5:98; one-element loop batch6:100; test name says characters not bytes.
N6 signer.key_path except tuple: TypeError/OSError branches untested, no mutant row.
N7 CHANGELOG lines 10/20 describe different check orders; line 17 omits per-name 255 refusal; baseline of "10 already checked" unclear.
N8 _os catches RuntimeError (wider than symlink loop); _size surrogatepass counts lone surrogate as 3; atomic.py:28 repeats _size expression; pathguard docstring cites removed causelist._inside.
N9 test_no_test_name_carries_a_key_shaped_string runs nested pytest.main collect-only on whole tests/ (magic 1000, picks up addopts, star-unpack); could not be verified.
Checked correct: _os raises with no __cause__/__context__; _check_text order; 252/255 arithmetic; confined delegation; key_path argument order; exceptions-file rows; mutant old-texts occur once; header counts; no suppressions added.
