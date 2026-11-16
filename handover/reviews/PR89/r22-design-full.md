<!-- full hand-back report of sub-agent a4857c31, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PR89 round 22, head c2f98f49: NOT READY. One Blocker, two Majors, five minors. I read the full runner, the full `mutation.py`, the CHANGELOG lines 88-92, the builder report and the tests that check modes. I ran nothing (read-only role). `evidence/PR89/c2f98f49/EVIDENCE-REPORT.md` does not exist yet, so none of this rests on a fresh run. The builder report also says the leak, address and lock probes were not re-run on this head.

**BLOCKER B1. The "private temp folder" promise is false after the first rebuild (`tools/mutation_runner.py:215-217`, CHANGELOG:88).**
- The docstring and CHANGELOG say the JUnit files, which hold the child's real text, lie in a folder made by `mkdtemp` with mode 0700.
- Line 1767 creates `tmp` with `mkdtemp`, which is 0700. Then `fresh()` runs, and `build()` at line 1727 does `shutil.rmtree(tmp)`. That deletes `tmp` itself. Line 1728, `(tmp / "tests").mkdir(parents=True)`, recreates `tmp` with the default mode, 0777 minus the umask.
- Python documents that `parents=True` ignores `mode` for the parents, so `tmp` is typically 0755. With umask 002 or 000 it is group-writable or world-writable.
- Every later write goes into that recreated folder: `base.xml`, `r.xml`, `again.xml`, the mutated source copy, and the copied tests. pytest creates the XML files 0644.
- Failure scenario 1 (secret read): the baseline or a mutant fails. pytest's failure text can include the address with the password, for example in an assertion rewrite or a repr of locals. Any other local user can read `/tmp/mutants_xxxx/base.xml` and get the password. The allowlist at the choke point is moot, because the raw file sits on disk world-readable.
- Failure scenario 2 (code injection): under umask 002 or 000, another user can overwrite `tmp/src` or `r.xml`. The runner then executes their code as the runner's user, with the address and password in the child's environment.
- The mode is checked nowhere. I found no test that checks the mode of `tmp`. The only tests that check mode touch the lock folder and lock file. The docstring even says the runner "does not check that mode itself", which is true but hides that it no longer holds.
- Fix: do not delete the top folder. Empty it and keep it, or `chmod(0o700)` after every rebuild, or `os.makedirs(tmp, 0o700)` and verify with `lstat` each time. Add a test that runs under umask 0 and asserts `tmp` is 0700 during a run.

**MAJOR M1. The snapshot folder is made with the umask default (line 1770, `snap.mkdir()`).**
- `snap` is `<mkdtemp name>_snap`, a sibling in the shared temp folder. It is created with the default mode, so 0755, or world-writable under umask 000.
- Every mutant copy is built from `snap/src` and `snap/tests`, so another user who can write there controls code that runs with the database address in its environment.
- The name can be seen as soon as `mkdtemp` returns. A pre-created `_snap` only gives a `FileExistsError`, which is a denial of service, but a writable `_snap` is code execution.
- Fix: put `snap` inside a 0700 parent or `mkdir(mode=0o700)`, and have the docstring say it.

**MAJOR M2. Masking applies only when a passed variable has a value, so "no password or token shape reaches logs" is not general (lines 1018-1019, 1036-1037; docstring 222-223).**
- With `pass_env=()`, or with the variable absent, `_shown_line` and `_shown_id` return the child's real `E` line and test id.
- The child still inherits `HOME` and the other `CHILD_ENV` variables. It can read `~/.pgpass`, SSH keys and cloud credential files. A failing assertion whose text holds a token comes back in `first_lines`, and the caller prints it.
- The docstring discloses "nothing is replaced", so this is not a broken promise. But the runner states a threat model (HOME readable by tests) and then ships the child's text unfiltered when there is no passed variable.
- At minimum, run the redaction path on `first_lines` and ids by default. Do not tie the allowlist to the presence of the one DSN variable.

**minor 1. A forged result file is narrower than the real power of a test (docstring 212, CHANGELOG).**
- A test also runs as the same user in a writable `tmp` and `snap`.
- It can alter the snapshot, so later mutants or canary runs are falsely killed or survive. The runner re-copies from `snap`, and it does not protect `snap`.
- It can also rewrite `base.xml` ahead of its own check.
- The documented limit ("forge its own verdict row") understates this. What the runner trusts from a forged file is `test_id`, `first_line` and the skipped list, and all three are attacker-chosen.
- Allowlisting does bound what is shown. The forged `[expect found]` word and the 70-class choice are a bit channel only, as documented.

**minor 2. Lock folder fallback to `tempfile.gettempdir()` (lines 1098-1108).**
- A pre-created `hadavin_mutation_locks_<uid>` owned by someone else, or a symlink, is refused. That is only a denial of service, and the owner uid check works.
- `gettempdir()` falls back to the current working directory when no standard folder is writable. The lock folder could then land in the repository, and the docstring does not say so.
- `XDG_RUNTIME_DIR` is read from `os.environ` at lock time (line 1105), not from the one-time snapshot. The docstring discloses this, but it contradicts the "read once" bullet at 155-156.

**minor 3. Huge port accepted.**
- `_ADDRESS_VALUE["port"] = [0-9]+` and the URL port have no upper bound, so `99999999999` and 1,900 zeros both pass.
- The host is still checked, and libpq rejects a port above 65535, so there is no safety consequence.
- It does make `0005432` and `5432` two lock names. That is the documented "spelling" limit, but a bound of 1-5 digits and the range 1-65535 would be cheap.

**minor 4. Lock reach.** The lock hashes only host, hostaddr, port and dbname. It does not include the login, and it takes no lock when the variable is absent. Both are documented. Spelling variants (`localhost` / `127.0.0.1`, port omitted) give two locks. It is a mistake catcher only, which the docstring says.

**minor 5. Order and message claims are mostly accurate.** Refusals 1-12 in the code match the docstring order, and the address-refusal messages name the variable and the reason, never the value. One difference: `_refuse_links_out` and `_refuse_junctions` raise `ValueError` after `mkdtemp` and the snapshot copy (lines 1767-1787). So "before any folder is made" does not hold for those two refusals. They are not in the numbered list, but the sentence at 105-107 reads as universal.

**Checked and holding at the choke point:**
- Child stdout and stderr go to the null device.
- `_pytest` re-checks the address before the child gets it (line 1279).
- The environment is read once.
- The shown text is an allowlist (class names, test ids from the snapshot's `def` and `class` names, fixed words).
- Whole-slot replacement is used instead of cutting out parts of a text.
- JUnit reading is guarded: `lstat`, a size ceiling, DOCTYPE and ENTITY refused, and an error row on `OSError`, `ValueError` or `SyntaxError` that keeps only the class name.
- The address grammar refuses a `dbname` that is a URI, a comma host list, `%` in a URL host, a login with `@`, and any password key.
- Both `host` and `hostaddr` must be listed.
- The lock folder is opened with `O_NOFOLLOW` plus `fstat` checks on uid and mode, and the lock file is opened with `O_NOFOLLOW` and `O_NONBLOCK`, then checked.

**Builder-report claims.**
- "Huge port left as is": confirmed in code, see minor 3.
- "Evidence folded in" (forged result file, `gettempdir` fallback): both are present in the docstring and CHANGELOG. The 0700 claim added in the same text is the false one (B1).
- "Leak table 0 of 498, not re-probed": not re-probed on this head. The mutant list shows no mutant that targets the folder mode of `tmp` or `snap`, so the 261 of 261 figure says nothing about B1 or M1.

**Verdict: NOT READY.** Fix B1 and M1, add an umask-0 test that checks the modes of `tmp` and `snap` during a run, decide M2, and then re-run the leak, address and lock probes on the new head.
