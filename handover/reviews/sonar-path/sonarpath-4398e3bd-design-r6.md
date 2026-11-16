# SONAR-PATH round 6, design review (egm-design a32f547b), head 4398e3bd

Condensed by the lead from the reviewer's inline report. Snapshot: /home/user/build/snap/sonarpath-4398e3bd/. The reviewer read the batch 6 delta in full and the sites listed below, not the whole DIFF.patch; it ran nothing and read no builder report. Verdict: 0 Blocker, 1 Major, 9 Nit.

## Major
- M1 `actions/secrets_vault.py` ~188-191: `except (OSError, UnicodeDecodeError, pathguard.PathRefused)` prints `cannot read {settings.jwt_path} (PathRefused)` with the raw value, including control characters (the R4 leak). `signer.build_local` maps only R10/R11 to its echo text. CHANGELOG list of places that "still print text the caller gave" omits the Vault message. Fix: map only R10/R11 to the echo text, or add to the list and print `!r`.

## Nits
- N1 `k1b/atomic.py:33` `final.is_dir()` is the one unwrapped OS probe in `atomic_write` (EACCES re-raised on 3.12 with the path). Use `os.path.isdir` or wrap.
- N2 `__context__` still holds the OSError at `atomic._without_path` (atomic.py:43, 58) and `signer.key_path` (signer.py:164-167); the test asserts only `__cause__ is None`.
- N3 `tools._module_files` (tools.py:251-265): whole-path length unbounded (about 17 parts of 250 bytes gives ENAMETOOLONG with the path on 3.12); 252 is applied to directory parts too (over-refusal of 253-255, stated accurately in the CHANGELOG).
- N4 `score._recorded_digest` docstring (score.py:162-175): `""` unreadable vs `None` absent, but R10 maps to `None` and also covers a symlink loop, EACCES, ENAMETOOLONG.
- N5 CHANGELOG item A wording "same folder" contradicts the `..data/token` example (target must lie inside the link's own folder, subfolders included); the projected-volume shape has no test; `test_changelog_claims` pins the loose phrase.
- N6 `test_the_sweep_sites_the_entry_counts_are_the_ones_in_the_source` docstring says 13 sites; it checks 9 files, not 13 nor the "3 leaked / 10 already checked" split.
- N7 `key_path` applies shape rules but not name rules (R3/R6/R7/R12) to the key file name; CHANGELOG sentence "no read follows" is false for `key_path`.
- N8 `local_dir.py:123` + `_id_refused`: for write_intent with id `abc.` and an unrelated refusal the text says "event id refused"; check only `<id>.json`.
- N9 `replay.py:151,159,173` and `cli.py:263,270` can raise a raw PermissionError carrying the typed path; route through `operator_dir(create_mode=...)` or state it is accepted.

## Checks that passed (reviewer)
Choke point `_within` is the shared tail of join/inside/operator_*; `_check_text` on base, joined and each part; atomic_write 233-byte limit, O_EXCL/O_NOFOLLOW/0o600; items B-E land; header counts for batch6 match (3/7/30); mutant rows B-E old text match; R1-R13 tested with mutants; tripwire scope and removed rows consistent; listed CHANGELOG claims verified.

## Not ruled
Q-R5-1 (operator-link refusal) is the lead's question; M1 and N5 touch the same paragraph.
