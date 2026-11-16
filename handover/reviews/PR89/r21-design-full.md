<!-- full hand-back report of sub-agent a91411ca, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT review, round 21, pull request 89, head 7a2eb4cc. Mode: REVIEW. Read-only, snapshot only, nothing executed.

# Verdict: NOT CLEAN

Counts: 1 Blocker (a gate, not a code defect), 1 Major, 12 Minor.

What failed or is unproven, first:
- **No evidence exists for this head.** `/home/user/hadavin-sdk/handover/evidence/PR89/` holds folders `b7a6b078...`, `db0d9eb` and `b95b0ca` only. There is no `7a2eb4c/RESULTS.md`. Every "passes", "248 mutants good" and "fails on the previous runner" is unproven.
- **The second layer (`_masked`) now runs over the caller's own text and discloses a weak password by cutting it out of a name the reader knows** (M1).
- The allow-list itself holds by reading: I found no field or exception path that carries free child text while a passed variable has a value.

Paths below: MR = `/home/user/build/snap/p89-7a2eb4c/tools/mutation_runner.py`, KW = `/home/user/build/snap/p89-7a2eb4c/tests/test_mutation_runner_keywords.py`, MUT = `/home/user/build/snap/p89-7a2eb4c/tests/mutation_runner_mutants.py`, CL = `/home/user/build/snap/p89-7a2eb4c/CHANGELOG.md`, R20 = `/home/user/build/snap/p89-7a2eb4c/DIFF-r20.patch`.

## Blocker

**B1 (gate). No evidence run at 7a2eb4c.**
- Scope: whole pull request.
- Unproven: the full suite, ruff, bandit, the 248 mutants (28 new), the sha256 pins, and the CL claim that `test_a_form_of_the_password_as_a_class_name_never_reaches_first_lines_in_a_real_run` fails on the previous runner "by showing the name".
- Rule: CLAUDE.md "Never write done, passed or verified without the command and its output"; EGM order step 4 before step 5.
- Fix: an evidence run on 7a2eb4c before the next result review.

## Major

**M1. The second layer cuts the password out of caller-known text, so the output discloses it.**
- Where: MR:897 (`_shown_line`), MR:924 (`_shown_id`), `_masked` MR:769-805. Certified by KW:3464-3475 and the two mutants at MUT:512-513.
- Input: `HADAVIN_TEST_PG_DSN=postgresql://postgres:postgres@localhost:5432/postgres` (the common container default; the grammar accepts it), `tests=("tests/test_postgres_store.py",)`.
- Trace: `_url_passwords` gives the password `postgres`, so the secrets are the whole address and `postgres`. `_shown_id("tests/test_postgres_store::test_x", ...)` builds the caller's own text, then `_masked` returns `tests/test_[REDACTED]_store::test_x`.
- Wrong outcome 1 (disclosure): a reader of the log who knows the file name (it is in the repository) reads the password off the gap. The plain caller text would have told them nothing.
- Wrong outcome 2 (usability): the id column can no longer be copied into `Mutant.pinned`. With the password `test`, every id becomes `[REDACTED]s/[REDACTED]_core::[REDACTED]_a`. This is the round-19 "ordinary rows are shredded" class (design M2, codebase M3), moved from the address to the password.
- Precondition: the password is a substring of a caller file, function or class name, an allow-listed class, or the caller's `expect`. A strong random password is not affected.
- Rule: the security requirement (the output must not give the secret away); PLAN D-014 (output is built from the caller's text, "never by trying to remove the secret"); class-level-fixes.
- Smallest fix at the choke point: in `_shown_line` and `_shown_id`, when `_masked(text) != text`, return the whole fixed replacement (`CLASS_HIDDEN` / `ID_HIDDEN`) instead of the cut text. One bit ("this slot held a known text") is left, not position and length. Change the two killer assertions to expect the fixed text.
- Siblings: the `expect` part of `_shown_line` (caller text, same cut); the documented "a secret of one or two characters hides every such text" (same disclosure, shorter).

## Minor

**m1. Fail-open defaults on the projection.** MR:1410 and MR:1425: `shown: _Shown | None = None` becomes `_Shown()`, which shows the child's line and ids raw. `_run_mutants` always passes `shown`, so nothing leaks today. A future call site that forgets the argument leaks silently; the mutant at MUT "the canary skip message shows the passed value" works exactly by dropping it. Fix: make `shown` a required argument.

**m2. A bare `assert` shows `[class not shown]`.** MR:878-881 with `_leading_class` MR:357-362. Input: first line `E   assert 1 == 2` (the most common pytest failure). `_leading_class` gives `assert 1 == 2`, which is on no list, so a KILLED row reads `[class not shown] [expect found] ...` (KW:3549 pins this text). Fix: map a line that starts with `assert` to a fixed word such as `assert`.

**m3. Ids are never shown for a `tests` entry the id form does not match.** MR:848-850, 910-913. Input: `tests=("./tests/test_x.py",)` (the spelling MR:23-24 recommends for odd names) or a folder with a dot in its name. The JUnit id is `tests/test_x::...`, the file part is `./tests/test_x`, so every row is `[test id not shown]`. Fix: normalise a leading `./` in `_id_form`, or say so in the table.

**m4. No stated way to see the real line.** A `WRONG_REASON` row gives the class and `[expect not found]` only. Neither MR:142-148 nor CL:20 says what to do (run that one test by hand against the test database). Round-19 design M2 named this loss; it is still there by design.

**m5. The pick among allow-listed names is a signal channel that the docs do not name.** A hostile test chooses one of about 70 built-in class names plus the caller's function names per row (about 6 bits per row). MR:142-145 "Not covered" lists files and the network only. Same class as counts, which you ruled out of scope; one sentence in the docstring would make the claim exact.

**m6. The address check sits in `_run_mutants` only; `_pytest` enforces the name but not the address.** MR:1138 checks names at the argv choke point (a mutant pins it); `_refuse_unsafe_address` is called only at MR:1554. A direct `mr._pytest(..., env_names=("HADAVIN_TEST_PG_DSN",))` with `environ=None` hands the live variable to a child unchecked. No test does this today (KW:404 uses a refused name; the other direct calls pass no name). Fix: check in `_pytest` too, or state that `_pytest` is not an entry point.

**m7. Key letter case and scheme letter case are folded, the database library does not fold them.** MR:603 lowers the key, MR:544 has `(?i:postgres...)`. `HOST=localhost dbname=app` and `POSTGRESQL://localhost/app` pass the check; libpq refuses both, so this fails closed there. A driver that ignores an unknown key would see no host. Fix: accept lower-case keys and scheme only. Also `sslmode` and `connect_timeout` take any token (MR:609-610); an allow-list of values (`disable`, `require`, ...; digits) would match the stated principle.

**m8. The refusal message for a password is not as helpful as the docs.** MR:656-660. It is free of the password (KW:4142 checks it). But "no password word" reads as "no password at all", it says "a host, a port" (the port is optional), and it does not give the way out that MR:98-100 and CL:41 give. Fix: add "a password goes in the login part of the URL; write `@ / ? #` in it as `%40 %2F %3F %23`". Open point for the owner: the URL shape takes no options, so a password together with `sslmode=disable` or `connect_timeout` cannot be written at all.

**m9. Removed password-word check: redundant today, with no guard for tomorrow.** R20:2652 and R20:2723 removed `_PASSWORD_KEY`; R20:269-271 and 304 removed its 4 mutants. See answer (2). Nothing asserts that `ADDRESS_KEYS_ALLOWED` never gains a key holding `password`, `passwd` or `pwd`. Fix: one assertion in `test_every_allowed_key_has_a_reason_and_a_refused_sibling` (KW:4012).

**m10. `XDG_RUNTIME_DIR` splits the lock of one user on one machine.** MR:975-977. A run from a login shell (variable set) and a run from cron, `su` or a CI step without it use two folders and do not see each other. Before this round one user with one temp folder had one lock. MR:161 and CL:62 name "another temp folder" but not this case. Fix: one sentence. Also: the variable is read live from `os.environ`, not from the snapshot of the call.

**m11. Windows and macOS wording.** CL:21 and CL:63-66.
- "Nobody has run the mutant list ... on Windows" is honest but narrower than the fact a reader needs: nothing in the snapshot shows the runner itself at this head was run on Windows or macOS. "What to do on Windows: use the runner as it is" is advice without a run.
- The 12 type-checker errors for the Windows platform appear in no text I read (no `mypy`, `pyright` or "type check" in MR, CL or the tests). By reading, each POSIX-only call sits behind an early `_IS_WINDOWS` return (MR:973, 987, 1048, 1196, 1220, 1246), so I expect none is reached there; that is unproven.
- "The lock and the checks of the lock folder ... are not checked there" can be read as "there is no lock". There is one (`msvcrt.locking`, MR:1017-1020), untested on a real system.
- "on Linux and macOS the lock folder is ..." states macOS behaviour; only Linux runs in CI.
- Fix: "The runner has not been run on Windows or macOS at this version. A type check for Windows reports 12 errors in POSIX-only branches that a run-time switch skips."

**m12. Single-dependency audit.**
- pytest is hard-wired (`-m pytest`, JUnit file). The alternative is noted (MR:11-14). Acceptable for developer tooling under the lighter check.
- PostgreSQL is hard-wired at the one choke point: `_refuse_unsafe_address` applies the libpq grammar to every passed variable (MR:1552-1554). The stated way to widen (MR:66-69, MR:314-316: "add the name to the list") does not work: a second name with any other address shape is refused "not in a shape". KW:4420 adds `OTHER_NAME` only with the variable absent. Fix: say that a new name also needs its own grammar and host check, with the trigger.
- `postgresql+driver://` URLs (the SQLAlchemy spelling) are refused; not stated.

## Answers to the brief

**(1) Allow-list projection.**
- True allow-list by reading. Class: `head in shown.classes` (MR:881), built from `builtins`, `Failed`, this call's `crash_type` values and `shown_classes` (MR:815-819, 872). Id: the caller's own `tests` text is printed (MR:923), each class and function name must be in the `def`/`class` names of the snapshot copy or in `only_test`/`pinned` (MR:919-920), parameters always replaced (MR:922). The allow-list is built before any child runs (MR:1634), so a child that writes into the snapshot cannot add names.
- Every output path I traced: rows (MR:1469-1515), `first_lines` (MR:1484, 1487, 1496, 1504), baseline failure (MR:1434), baseline skip (MR:1417-1422), canary (MR:1441-1451), `CanaryFailed.rows` (already-projected rows, MR:1704), `SETUP FAILED: <class>` and the canary rebuild message (our own exception class name). Chained causes: `from None` at MR:996, 1103, 1115, 1118, 1418, 1691; the other raises are outside an `except` block.
- Steering: a child can only choose among allow-listed tokens (m5). A listed class or function equal to the password is replaced by layer two. A child-chosen parametrize id is never shown. `EXIT CODE <n>` and the skip count are child-chosen numbers: out of scope as you ruled.
- What a developer sees for an ordinary failure: mutant name, verdict, good flag, `tests/test_core::test_a[parameters hidden]`, and `AssertionError [expect found] <their expect>`. Usable, with the gaps m2, m3, m4.
- `_masked` after the projection: a real second layer for "an allow-listed token equals the secret", not a crutch over a hole. Its side effect is M1.

**(2) Password-word check.** Truly redundant for every input at this head.
- URL form: the check never applied there. A query is impossible (nothing may follow the database name, MR:544), so no `?password=`.
- Words form: the key is lowered and must be an exact member of seven keys (MR:603-605), none of which holds a password word; a value cannot hold `=` (MR:547), so no second pair hides in a value; a key cannot hold `%`.
- Repeats and case: covered by `seen` on the lowered key (MR:606-608, KW:3986-4009).
- No control disappeared; only the defence against a future edit of the key list (m9).

**(3) Address check.**
- One grammar for check and lock name: yes (MR:583-626). Socket folder only as exact member: yes (MR:611, 669; KW:3959). No host refused: yes (MR:661). Every key checked for a repeat: yes. `host=::1` accepted, `host=[::1]` refused: yes (MR:554; KW:3778, 3807). `sslrootcert` and `application_name` removed, a reason per key: yes (MR:562-570). `throwaway_hosts` checked for every call: yes (MR:1542).
- `%40` in a URL password: sound for the check. The login may not hold `@ / ? #` (MR:544), so the host the grammar reads is the host libpq and `urlsplit` read. For hiding, the written and decoded forms and one re-encoding of each are searched (MR:507-536).
- Forms layer two does not know: mixed hex case inside one text, over-encoding of plain letters (`%5A` for `Z`), a quoting with another safe set, three or more layers of encoding, entity or backslash escapes. This no longer matters for child text, which the allow-list never shows; it matters only for the caller's own `expect` and names.
- Bypasses, all refused by reading: decimal, hex and short IPv4, IPv4 inside IPv6, trailing dot (exact membership; KW:3832-3856, 4044-4078), several hosts (no comma in a host), `hostaddr` (checked like `host`), `service`, `passfile`, `options`, `target_session_attrs` (not on the key list), `dbname=` holding a URL (MR:557), `PG*` variables (not in `CHILD_ENV`, MR:310-313; KW:4271). `HOME` is inherited, so `~/.pgpass` and client certificates are used; stated at MR:119-120.
- Refusals before side effects: yes (MR:1537-1566 against the lock at MR:1608-1611). Earlier effects are only `first_lines.clear()` and the signal handlers, which are restored.

**(4) Test-only switch.** Removed (R20:371-395; KW:84-87, 134-139). No test replaces `_refuse_unsafe_address`, `_address_fields`, `_checked_throwaway_hosts`, `THROWAWAY_HOSTS` or `ADDRESS_KEYS_ALLOWED`. KW:4304 wraps the real check and calls it. KW:4420 widens `PASS_ENV_ALLOWED` for the order test. `_protection_off` (KW:445-447) switches the output layers off as a control, not the address check. The runner has no keyword, variable or flag for it. Remaining route: a direct `_pytest` call (m6).

**(5) Lock folder.** `O_DIRECTORY|O_NOFOLLOW`, `fstat` of the opened folder, `dir_fd` for the file: present (MR:992-1011, 1094). A swapped folder or link between `mkdir` and `open` is caught by the owner check or by `ELOOP`. As root: a folder planted by another user is refused (owner), a planted link is refused. The denial of service by a planted folder remains and is now stated as "refused, not prevented". A link in place of the folder gives the message "(OSError)" without saying it is a link (nit). `getuid` is compared, not `geteuid`: a set-uid run is always refused (nit). Windows honesty: m11.

**(6) Open owner decision.** Still refused, stated in CL:41 and MR:94-100. Message: m8.

**(8) Claims beyond tests.** B1 for everything that needs a run. The order test (KW:4400-4410) pins 9 of the 13 documented steps; steps 1, 5, 8 and 12 are by reading only. The pins in CL:465-468 equal `tests/fixtures/mutation_manifest.json`; not checked against the file bytes.

## (7) Round-19 checklist (verified by reading; every "resolved" still needs B1)

Design report:
| Id | Status | Where verified |
|---|---|---|
| B1 no evidence | not resolved for this head | evidence folder |
| M1 free child text in class and id slots | resolved | MR:878-881, 900-925; fuzz KW:3652-3737; real run KW:3528 |
| M2 shredding for the CI address | resolved for that address; residual is M1 above | KW:3394-3411 |
| M3 sockets and no host by pattern | resolved | MR:571-580, 661-669; KW:3945-3983 |
| M4 test-only switch | resolved | answer (4); empty value now refused, KW:4345-4375 |
| m1 lock folder claim | resolved | MR:165-170, 981-1011; CL:63-64; real-folder run KW:4296 |
| m2 lock name for sockets | resolved | MR:618-626 |
| m3 `forbid_skips` two meanings | resolved | MR:171-175, 1555-1558; table |
| m4 two `type: ignore` | resolved | none left; MR:1163-1166, 1290 |
| m5 mutant gaps | mostly | MUT list at R20:309-345; no mutant for `.strip("[]")` |
| m6 repeated key | resolved | MR:598-608 |
| m7 reason per key | resolved | MR:562-570; KW:4012 |
| m8 no `PG*` guard test | resolved | KW:4271 |
| m9 order of refusals | resolved, partly proven | MR:82-107; KW:4413 |
| m10 stale wording | resolved | "marked throwaway" gone; MR:1322-1346 |
| m11 host list checked late | resolved | MR:1542 |
| m12 unreachable code, owner decision | open (owner) | dead paths kept with a reason, MR:480-481 |
| m13 commits split | cannot verify | |

Codebase report:
| Id | Status | Where verified |
|---|---|---|
| M1 test certifies refused behaviour | resolved | as design M4 |
| M2 denylist projection | resolved | as design M1 |
| M3 pieces from the whole value | resolved; residual is M1 above | no pieces code left |
| m1 baseline skips layer two | resolved | MR:1434 |
| m2 `forbid_skips` keyed on listing | resolved | test and mutant "listed, variable absent" |
| m3 repeated key | resolved | MR:606 |
| m4 IPv6 in words | resolved | MR:554 |
| m5 socket lock name | resolved | MR:618-626 |
| m6 late host-list check | resolved | MR:1542 |
| m7 lock folder (a)-(e) | resolved | MR:989-996; MR:162-163 |
| m8 doc drift | resolved | CL:6; MR:82-107 |
| m9 mutant gaps | resolved | R20:339-341 and the allow-list mutants |
| m10 fuzz | resolved | real `_row` paths, membership check, control |
| m11 weak tests | resolved | KW:4167-4196 watches `_open_lock_dir`; fixture no longer calls `undo` (KW:3164-3171) |
| m12 secrets kept in a cache | resolved | no `lru_cache` |

Comprehension report:
| Id | Status | Where verified |
|---|---|---|
| M1 files to copy | resolved | MR:16-20; CL:7 |
| M2 `first_lines` and `crash_type` | resolved | MR:146-148, 1335-1337; CL:59 |
| M3 "token never reaches the child" | resolved | MR:66-68; CL:22 |
| M4 "set" | resolved | the three-row table |
| M5 "discarded" | resolved | MR:116; CL:44 |
| M6 safety paragraph | resolved | MR:109-112; CL:42 |
| M7 lock over-stated | resolved | MR:158-164; CL:62 |
| M8 red-list changes | resolved | CL:9-20 |
| M9 Windows | partly | m11 above |
| m1 words with two meanings | partly | "baseline" and "pin" still have two |
| m2 unexplained terms | partly | "guard", "the wheel", "demos" remain |
| m3 internal codes | resolved | ladder and constant names gone |
| m4 non-steps under upgrade steps | resolved | "background" entry |
| m5 long sentences | partly | MR:21-26 is still one sentence of about 170 words |
| m6 headline | resolved | CL:6 |
| m7 "no piece of 4 characters" | resolved | gone |
| m8 address rules without action | partly | m8 above |
| m9 table duplicates | resolved | new table |

## What I did not check
- Any run: tests, lint, bandit, type check, mutants. No hashing of the pinned files.
- `DIFF-vs-main.patch`: not read. `DIFF-r20.patch`: read the mutant hunk, the grammar hunk and searches only; I read the head files instead.
- `tests/test_mutation_runner.py`, `tests/conftest.py`, `tests/test_mutation_runner_meta.py`: searches only. KW: lines 40-170, 3140-4010 (most), 4012-4091, 4142-4468; the rest by search.
- CL outside lines 1-120 and 452-469.
- `.github/workflows/ci.yml` (not in the snapshot).
- libpq, asyncpg and pytest behaviour: stated from knowledge, not from a run. Windows and macOS behaviour: by reading only.
- Whether the commits were split.
- `.claude/rules/egm-review-routing.md` and other rule files not named in the brief.
