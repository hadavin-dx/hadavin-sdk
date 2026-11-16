Package PR89, head 4cc427b5bfbf1ff07beb8db03da80c9e59b44fc6, round 23, persona design critic. Snapshot /home/user/build/snap/pr89r23-4cc427b5.

Verdict: no Blocker and no Major found. B1, M1 and M2 are fixed as claimed. One Nit is still open, and it is the built-in class name leak. I read the lines named below in tools/mutation_runner.py. I only grepped the other 11 spec items and the CHANGELOG, and did not check them.

### [N1] Nit - a password equal to a built-in class name still shows in first_lines
Where: tools/mutation_runner.py:1044-1045 (`_shown_class`), and :1054-1062 (`_shown_line`). Docstring lines 186 and 907 claim the opposite.
What: `_shown_class` returns `head` unchanged whenever it is in `_BUILT_IN_CLASSES` (:1044-1045). The built-in branch never reaches `_own_text`, the second layer. The `_own_text` call at :1046 only covers caller-owned names such as `crash_type` and `shown_classes`. `_secret_values` and `_checked_env_names` do not refuse a secret that is a Python class name; grep found no such check. This head therefore still allows the 2 of 498 round-22 cases.
Why it matters (concrete input -> wrong output): with `pass_env` holding a password `TimeoutError` and a child failing with `E   TimeoutError: ...`, `first_lines[name]` is `"TimeoutError"`. The text equals the secret and reaches the log. The wording "pass_env values must never reach first_lines" (:907) and "every text the runner returns" (:186) is therefore not strictly true.
Why it is a Nit and not a Major:
- The password must equal one of about 70 fixed Python names, roughly 6 bits, so it is already trivially guessable.
- The leak needs the child to raise that exact class first. The child can already read the variable anyway.
- The caller supplied the value, so the exposure is the log or CI output only.
- If the owner wants the "never" claim kept literally, fix it with one line and do not treat it as a reason for another round.
Suggested fix: in `_shown_class`, apply `_own_text(head, CLASS_HIDDEN, shown.secrets)` to built-in names as well (remove the early return at :1044-1045). Add a test with the password `TimeoutError`. Or soften the docstring claim at :186 and :907 to except built-in names equal to a secret.

### Checked and found fine
- B1: `build()` at :1858-1875 no longer calls rmtree on `tmp`. It checks `tmp` with `_refuse_unless_private` (lstat, own uid, no group or other bits) at :1861, empties the inside with `_empty_dir` (:1184-1196, keeps the top folder), makes `tests` with `os.mkdir(..., 0o700)` (:1864), and checks `tmp` again at :1875 after every rebuild. A leftover `tests` folder fails the attempt and is retried by `fresh()`.
- B1: `tmp` is also checked right after `mkdtemp` (:1913). `_dir_problem` (:1134-1144) is the single check, and the docstring at :223 now says "checked again after every rebuild".
- M1: `snap` is made by `_make_private_dir` (:1915). That function does `os.mkdir` with 0700, then `chmod` to undo the umask, then `_refuse_unless_private` (:1162-1168). `snap` is checked again after the copy (:1930). The folders made in between use `_make_dirs` with 0700 (:1171-1181). The `snap` check also covers extra_dirs copied with `copystat`.
- M2 (D-023): `_shown_line` and `_shown_id` still return the raw text with no passed value (:1054-1055, :1072-1073). CHANGELOG:63 and :89 state the limit and cite D-023. A test at test_mutation_runner_keywords.py:5724-5756 pins the sentence. This is the documented limit, not a regression.
- The lock folder check `_refuse_lock_folder_in_tree` (:1226-1235) is called before the lock is taken (:1900). It uses `lock.is_relative_to(root)`.
- The bare-string guards for `tests`, `extra_dirs` and `only` are called at :1820-1822 before any folder is made.
- The junction checks run before `mkdtemp` (:1906-1909). `_refuse_links_out` still needs the copy and runs after it (:1931), and the comment at :1904-1905 says so.
- Second-layer slots for test ids, `expect` text and caller class names work without the built-in gap: they return a fixed text and never a cut-out piece (:951-956, :1089-1090).

### Not checked
- Findings 4-14 of the r22 report were not read at their lines: port bounds, order-test additions, the MAX_SECRETS boundary tests (only the constant at :431 and the guard near :845 were seen), the new mutants, the manifest sha256, and the CHANGELOG list.
- No run of the test suite or of the new mutants. I did not confirm that the new tests fail on c2f98f49.
- Windows behaviour (the mode checks are skipped there by design).
- `_refuse_unless_private` is a check and not a lock. I did not weigh a same-user race between lstat and use, because the docstring already says a test can act as the same user.