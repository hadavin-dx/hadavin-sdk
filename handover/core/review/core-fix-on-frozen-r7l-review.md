# Review of the r7l test-only delta (codebase-details goldfish, fallback mode)

Date 2026-11-14 (UTC). Reviewer: fresh context, own tree copy `/home/user/build/rr6/tree-REV7L` (and `tree-REV7Lf` for flake runs and a second runner), scratch `/home/user/build/rr6/out/REV7L`. Not committed.

## Verdict: NOT CLEAN
Blocker 0, Major 2, minor 3, nit 1.

The new file is real work: every mutant the builder named is killed by `tests/test_r7l_findings.py` alone, restore by sha was clean, and the file was stable in 5 runs and under load. But two mutants the builder did not try, on the mail send path, survive the new file AND the 18-file mail set, and the builder's "equivalent, not killable" argument for the server mutant S13 is wrong in its real form (a one-line mutant that is killable).

## What I did NOT run or conclude (first)
- No full suite. Wide set (22 files plus r7d..r7x plus r7i/r7j) was NOT run for all survivors: it took about 6 min per mutant. I killed my own wide runner after 1 mutant (A3). For the mail survivors I used the 18-file "mail" set (includes smtp_outbox, smtp_provider, r7d..r7i); for the server survivors the 10-file "srv" set. Neither equals the brief's "wide set" exactly. A survivor on both sets is reported as a survivor; none of my kills are claimed on the wide set.
- Baseline fact: on this machine the OLD test `tests/test_r7f_findings.py::test_f1_a_connect_that_never_completes_ends_at_the_total_not_at_the_step` FAILS on the clean tree (full mail set: 1 failed, 1215 passed; `base-mail.log`). It is not part of the delta. My first mail-set mutant run reported every mutant "KILLED" by that test: those results are INVALID and are kept only as `res-D-invalid-baseline-red.tsv`. I re-ran with that one test deselected (`res-F.tsv`). This was my own slip. I do not know whether the test fails in the builder's environment; it is an environment fact to check (listen backlog 0 does not hang a connect here).
- The srv set baseline (unmutated) was not run separately; the srv kills I report name a relevant test (not a crash), and the server survivors ran 220 s each so the set did execute.
- Frozen tree and all other trees untouched; `diff -rq --exclude=__pycache__ tree-R7J/src tree-REV7L/src` is empty after every mutant (also tree-R7L/src equals tree-R7J/src). Stale `.pyc` files differ between copies; irrelevant.
- Gitleaks/secret scan not run. Mypy, ruff not run by me.
- I killed my own runner pid 9422 and its pytest child once (too slow) and restored `smtp_outbox.py` by copying from tree-R7J, verified by diff. No other pids touched. Processes still alive on the machine at the end belong to others.

## Per brief item

### (1) Each claimed test is non-vacuous: CONFIRMED
Ran the builder's `mine2.json` (42 mutants) with the new file ALONE: 41 KILLED, 1 SURVIVED (V03). Examples (line, mutant, killing test): X05 outbox 292 and PX05 provider 351 (final 3xx as SENT) by `test_l1_*`; X17 provider 268 (stats write) by `test_l2`; Y1/Y2/X14/X13/X01/X02 by `test_l3_*`; V01 server 499, V02 667, V05 732, V06 511 by `test_l4_*`; S2/S3/S4/S11/S12 by `test_l4_*`; X03/X03P/Z5/Z12 by `test_l5_*`; X20 by `test_l7`; X21/Z10 by `test_l8`; X27/X29/X30/Z11 by `test_l9_*`; X28 by `test_g1`; PEK by `test_l13`; Z6 by `test_l10`. Baseline of the new file: 91 passed. Delta applies cleanly; r7i+r7l = 128 passed (as claimed).
G4: planted a fake fifth adapter (`src/lead_desk/fifth_x.py` calling `read_secret_file`): test FAILS (good); `regfile.read_secret_file(...)` form also fails (good). See minor m2 for what it misses.

### (2) My own mutants (24 on nearby lines, `own.json`, plus 6 more `ownR.json`)
Killed by the new file alone: A1, A2, A4, A5, A6, A12, A18, A21, A23, A24 (10). Survived the new file alone: A3, A7, A8, A9, A10, A11, A13, A14, A15, A16, A17, A19, A20, A22 (14). Re-run on the mail or srv set:
- Killed by an older test: A3 (test_smtp_outbox greeting_554), A7, A8, A10, A11 (r7i i3), A13 (r7c mail6 d11), A15, A16, A20.
- STILL SURVIVE the whole mail or srv set: **A9, A14, A17, A19, A22**, plus **S13R** (see below). I then wrote six small tests (`/home/user/build/rr6/out/REV7L/rev7l_killers.py`); all pass on the clean tree and each kills its mutant (`res-G.tsv`).

### (3) Timing flakiness: no problem found
New file: 5 runs alone: 91 passed each (3.6 to 4.8 s). Under 3 busy loops (4 cores), new file plus r7i: 128 passed twice (11 s). Hardcoded sleeps are small (0.02 to 0.4 s drip/header delays); margins are loose: finish drain `< 1.5 s` against 0.2 s, busy write `< 2.0` against 0.3 s, `0 < body_limit < 0.7` after a 0.4 s sleep of a 1.0 s limit (real sleep is never shorter than 0.4, so the bound cannot be crossed downward). No flake seen. Not tried: a slower machine than this one.

### (4) V03 and S13 "equivalent" argument
- V03 (`settimeout(budget)` removed in `_drain`): I agree it is equivalent. `_DeadlineReader.readinto` (server.py 139 to 150) sets `min(idle, deadline-now)` before every `recv_into`, the deadline is armed at the top of `_drain` and is earlier than the loop's own, and `read1` always goes through `readinto`. V03 survived and I could not make it matter with a drip client.
- S13 as the builder planted it (`settimeout(max(budget, 0.001))`) is a softened mutant. The REAL removal of the check (`if budget <= 0: break` deleted, `settimeout(budget)` kept) is NOT equivalent: a read that returns a byte after the loop's own deadline passed makes `settimeout(negative)` raise `ValueError`, which `except OSError` does not catch, so the handler thread dies with an exception. My test `test_drain_a_byte_after_the_total_limit_ends_the_drain_quietly` (fake reader whose `read1` sleeps past a 0.2 s limit then returns a byte, real socket) passes on r7j and kills this mutant (`S13R`); it survives the new file and the srv set. The builder's claim is wrong for the form that matters.

### (5) i10/i11 edit (2 s to 5 s, `< 1.5` to `< 4.5`)
Still kills what it was written for: R1 (outbox text write, no settimeout), R2 (provider), R3 (imap, no settimeout before wrap), R4 (imap step only): all KILLED by the edited r7i (`res-H.tsv`). But it is weaker for one class: A1/A2 (text write given the module's OWN full 2.0 s limit instead of the time left) were KILLED by the old r7i (`test_r7i_old` copy, `res-I.tsv`) and now SURVIVE the edited r7i, because 2.0 < 4.5. The new `test_l3_*` kills them, so the net coverage is not lost, but r7i alone no longer holds it (minor m3). The change is not a vacuous test: the sleep of 0.6 s makes `t <= 4.4` always.

### (6) Literals, suppressions, names
No IP literal (`LOOP = "127.0.0." + "1"`), no secret literal (`FAKE_PASSWORD` from demo_only), no `noqa`. NEW suppressions: 19 `# type: ignore[...]` in `tests/test_r7l_findings.py`; r7h/r7i/r7j have 0, and mypy is configured for `src/` and `tools/` only, so they suppress nothing the gate checks (minor m1). Names checked against bodies for l1, l2, l4 (busy reply, busy drain), l13, g4: they do what they say. One header-table row says "Kills V03 pinned" while the test is a control that passes on V03: the docstring says so honestly.

### (7) "No source file changed": CONFIRMED
`diff -rq --exclude=__pycache__ tree-R7J/src tree-R7L/src` and tree-R7J vs tree-REV7L (after applying the delta) are empty.

## Findings

### Major 1: smtp_provider.py:332 the EHLO reply after STARTTLS is not pinned (mail/secret path, no round cap)
Mutant A14: `_expect(_command(... "EHLO ..."), "ehlo after tls")` replaced by the bare command. Survives `test_r7l_findings.py` (91 tests) and the mail set (18 files, 1215 tests). Consequence: a server that refuses EHLO after TLS (for example 554) still gets `AUTH PLAIN <password>`. Killing test (in words): starttls mode, script replies 220, 250, 220, 554; `_dialogue` must raise `SendRefused` and no sent line may start with `AUTH`. Mine: `test_ehlo_after_starttls_refused_stops_before_the_password` in `out/REV7L/rev7l_killers.py` (passes on r7j, kills A14). The builder's table row F7 pins only the EHLO BEFORE STARTTLS (X20).

### Major 2: wrong "equivalent" claim and three unpinned time/size limits in server.py (SURVIVE new file and srv set)
- server.py ~705 `_drain` total-limit check (S13R): see item (4). Test above.
- server.py ~665 `_send_bytes`: `if left <= 0: raise TimeoutError("reply write deadline")` (A17, weakened to `left < -100`): headers that use more than the whole reply limit give `settimeout(negative)`, a `ValueError` that is not caught by `_GONE` or `OSError`. Killing test: reply limit 0.2 s, headers write sleeps 0.4 s, real socket; `_send_bytes` must return without raising and must not write the body (`test_reply_whose_headers_used_up_the_limit_writes_no_body`).
- server.py ~739 `finish`: `left -= len(chunk)` (A19, byte cap): without it a client that keeps sending is read until the time limit instead of at `DRAIN_MAX_BYTES`. Killing test: fake connection whose recv returns the requested size at once; calls must be bounded by the byte cap (`test_finish_stops_at_the_byte_cap`).
- server.py ~702 `_drain`: `min(max(remaining, 0), DRAIN_MAX_BYTES)` without the cap (A22). Same shape of test (`test_drain_stops_at_the_byte_cap`).
These are the "every blocking read/write has a limit" family that finding F4 was about; the builder covered the timeouts and not the byte and past-deadline guards beside them. One survivor class: fix them in the same file.

### minor m1: 19 new `# type: ignore[...]` in tests/test_r7l_findings.py
New suppressions against the repo rule (no suppressions). mypy is not run on tests, so they are unneeded; remove them (or give the fakes the real types).

### minor m2: G4 guard has two known bypasses
`SRC.glob("*.py")` plus the regex `read_secret_(line|file)\(`: a fifth adapter that imports the reader under another name (`from lead_desk.regfile import read_secret_file as rsf; rsf(p)`) passes the guard (tested: 1 passed with the planted file); so does one that reads the secret with plain `open(path)`. The `any(word in n ...)` check also only needs the word to appear in some test name, not that the test checks anything. Narrowing: also search for `as ` aliases of the reader and for `open(` on `*_file` settings, and walk subfolders.

### minor m3: edited i10 no longer kills "own full limit" mutants on its own
See item (5). Covered by `test_l3_*`; to keep r7i self-sufficient, set the settings limit above the `t <` bound (for example own limit 8 s) or add the `t < own limit` form.

### nit n1: test_r7l header says "V03, S13 are EQUIVALENT (not killable)"
Wrong for S13 (see item 4); fix the wording when the S13R test is added.

## Not a finding (checked)
A9 (`smtp_provider.py:280`, the `sent` count written after a successful send) also survived the new file and the mail set; my test `test_stats_file_holds_sent_after_a_send` kills it. I count it under minor (statistics only; the send cap uses `attempts`, which is pinned): add that test too.

## Artifacts
`/home/user/build/rr6/out/REV7L/`: `res-A.tsv` (builder mutants, new file alone), `res-C.tsv` (own, new file alone), `res-F.tsv` (own survivors, mail set, valid), `res-D-invalid-baseline-red.tsv` (invalid, see above), `res-E.tsv` (own server survivors, srv set), `res-G.tsv` (killer tests), `res-H.tsv`, `res-I.tsv` (r7i checks), `rev7l_killers.py` (6 tests, pass on clean r7j tree), `own.json`, `ownE.json`, `ownR.json`, `s13raw.json`, `base1.log`, `base-mail.log`, `checkpoint.md`, `mr.py`.
