# sonarpath-ddf1d584-design-r1: ORDER 260 path containment, head ddf1d584, round 1, persona design

Source: hand-back of the design reviewer (agent a1cd7094509a16284), saved by the lead (condensed). SECURITY path (no round cap). Static read only; nothing was run; no independent evidence existed when read. 0 Blocker, 4 Major, 5 Minor, 3 Nit. Snapshot `/home/user/build/snap/sonarpath-ddf1d584`. Verdict: not READY. pathguard.py refuses every case R1-R11 as designed; the Majors are sites still unguarded and mutants that cannot show call-site conversions can fail.

## Major
- **M1** src/hadavin_sdk/config.py:534-536: `raw[key] = root / raw[key]` for `golden_dir` and `inputs_dir` is a file-derived path with no check (absolute or `..` possible). Design section 4 last row puts it in scope; `root` is in hand, so `confined(root, raw[key])` works. No "unchanged, reason" row seen. Fix: route through `confined`, or document the exception with its origin.
- **M2** audit/signer.py:106-109, 206, 218 (`private_key_path` from config read unguarded by `load_private_key`/`load_public_key`); cli.py:132-133 (`--config` goes straight into `HADAVIN_CONFIG_DIR`, design section 4 row 4 lists it for `operator_dir`, not converted); config._read_yaml:490 reads from that unvalidated root. Fix: apply `operator_dir`/`operator_file` or record the explicit exception in the PR table.
- **M3** tests/pathguard_mutants.py: no mutant proves a call-site conversion can fail (X3 reverts the `_check_name` loop inside `join`, not a site). Nothing reverts score._read_json, _recorded_digest, replay._write_json, outputs_files, bundle._load_json, the causelist._load join, cli.score_cmd, config.confined delegation, or the key_path R8-to-outside mapping. The AST tripwire is blind across function boundaries and covers only k1b/*.py and cli.py. Fix: one mutant per converted site pinned to its caller test.
- **M4** Mutants disable whole rules, not parts: R5b one mutant for the `_check_length` body (partial revert in `inside` alone untested); R10 mutates only ValueError, not the RuntimeError loop branch; R7 nothing for "stem before the first dot" or `rstrip(" ")`; R6 no mutant separates dot from space; R11 nothing for `_operator`'s `if must_exist or real.exists()`; atomic_write no mutant for O_NOFOLLOW, BaseException vs Exception, `_TEMP_EXTRA` R5 temp check, `os.fsync`; R9 mutant overlaps R2.

## Minor
- **m1** pathguard.py:93-97, 123-129: NUL in `inside`/`join` rests on `Path.resolve` raising ValueError (true on 3.12; 3.13/3.14 not verified). Add an explicit NUL/control check in `inside` and `join`.
- **m2** score.py:225-252, cli.py:258-264: `score_cmd` validates `operator_dir(args.outputs)` then calls `score(args.outputs, ...)`; the raw value is re-resolved in outputs_files, hash_files, _recorded_digest (time-of-check gap inside a second-writer threat model). Validate once, pass the resolved path. `hash_files(out: str)` with a str not verified (hashing.py not in snapshot).
- **m3** atomic.py:27-33: `join` resolves an in-base symlink, so atomic_write now writes the link's TARGET inside the base instead of replacing the link (old os.replace replaced the link). No test for an in-base symlink or hard link as the final name. Refuse an existing symlink as the final name, or pin the behaviour with a test.
- **m4** pathguard.py:48 R4 set matches the design but omits LRM/RLM U+200E/F, ALM U+061C, U+2028/2029, U+200B-200D, U+FEFF; Windows-invalid `< > " | ? *` not refused in `component` (OSError instead of PathRefused).
- **m5** signer.py:137-149: `key_path` raises a bare ValueError for NUL (`parent.resolve(strict=True)` before `inside`); R6/R7 not applied to the key file name (by design 3.4).

## Nits
Design 3.2 says R6 and R7 apply to every component; code applies them to data-derived names only (say so in the docstring). `PathRefused.__init__(rule, message)` cannot be pickled or copied (args holds only the message). `load_bundle(s)` can now raise PathRefused instead of BundleError (still a ConfigError).

## Checked and found fine
R1-R11 lines (67, 71, 73, 69/48/156, 75/107, 77, 79, 126/148, 90, `_check_kind`); routed sites atomic, score (`_read_json`, `_record`, `_recorded_digest`, `load_answers`, `_check_layout`), replay, bundle (also fixes the discarded `confined()` result), causelist `_load`, cli `score_cmd`, config.confined, signer.key_path; no false "inside" for `..`, absolute name, folder/file link, new file under a folder link.

## Not checked
No pytest, ruff, bandit, mutant run or Sonar; unchanged sinks (hashing.hash_files, registry.py, evals.py, app.py, secrets_file.py, agent_loop.py) and the twelve `confined` callers not read; PR body and path-origin table absent from the snapshot; Windows junctions, `\\?\`, 8.3 names; Python 3.13/3.14 NUL behaviour.
