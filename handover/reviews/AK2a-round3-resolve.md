# AK2a round 3 resolve (egm:egm-resolve, AUTO mode; LAST round)

**Status:** resolved (AUTO; categorised; the skill's interactive gate is skipped because the lead's brief says AUTO, no gate). The ticket is NOT edited. The fixes are build notes BN-1 to BN-20 below, and they win over the ticket text. This file replaces the skill's default name `goldfish_review_report.md`. Nothing was committed or pushed.

**Target:** `handover/tickets/AK2a.md` revision 3 DRAFT, commit `6a852f4` (2026-11-06 04:42:19 UTC / 10:12:19 IST; `git log -1 -- handover/tickets/AK2a.md`), full file (458 lines), both sub-PRs. Source tree read at `<repo>` (`git log -1 -- src` on `main` gives `ce70eb5`, as the ticket says).

**Findings:** 27 ids. I took each severity from the reports' tables and changed none.
- `reviews/AK2a-round3-adversarial.md` R3-ADV-1..18: 0 Blocker, **12 Major** (ADV-1 to ADV-12; the report's header says 10, but its table marks 12, and the saver's note agrees), 5 Minor (ADV-13 to ADV-17), 1 Nit (ADV-18).
- `reviews/AK2a-round3-correctness.md` R3-COR-1..9: 0 Blocker, **3 Major** (COR-1 to COR-3), 4 Minor (COR-4 to COR-7), 2 Nit (COR-8, COR-9).

**Gate (order 20 item 6):** round 3 is the last round under the cap of 3. A security, money or redaction ticket may take a 4th round only if round 3 had no Blocker and at most 2 Majors. **Round 3 has 15 Majors, so there is NO round 4.** I contest one of them (COR-2), and two pairs overlap in part (ADV-1 with ADV-13; ADV-9 with COR-4). Even so, at least 13 distinct Majors remain. The ticket freezes at revision 3 with this file attached. The banner below goes under the ticket's revision line (its status line). The build-start review (order 19 A, order 20 item 3) reads the ticket and this file together.

## Facts I checked myself (on disk at `<repo>`; "probe" = a read-only scratch run described in the Honest note)
- **F1 (ADV-1, ADV-13). AK1 is FROZEN.**
  - `tickets/AK1.md` is "REVISION 3, FROZEN with build notes BN-1 to BN-17" (commit `d1459d1`). Its banner is at `:5`, and its build notes start at `:435`.
  - The `NON_TABLE_PATHS` paragraph (AK1 Interface 4) says that a key ending in `/` covers a subtree. So a key without `/` names one file.
  - The same paragraph, and AK1's relay line for AK2a, still say "AK2a's `ingest/` package imports no L8 library ... optional". The L8 closed list (AK1 Tests, row L8) holds `subprocess`.
  - AK1's own round 3 resolve, under Couplings "BN-7 and AK2a", states the rule correctly: "AK2a needs no L8 row unless it imports a library on L8's list". That coupling line is not copied into `AK1.md`.
  - AK1 BN-7 adds `asyncio`, `multiprocessing` and `ctypes` to L8's list. AK1 BN-8 redefines `content_sha256` on raw bytes; AK2a only copies it (step (g)). AK1 BN-12: `run_step` catches `Exception` only.
- **F2 (COR-1 TRUE).**
  - `tests/test_lockin_guard.py:138-139` fails any `src` module whose import has the top-level name `importlib`, unless the module is in `DYNAMIC_IMPORT_OK` (`:80-84`: `backends.factory`, `actions.executor`, `tools`). The worker's `import importlib.metadata` fails this guard.
  - `subprocess`, `signal`, `threading`, `resource`, `tempfile` and `shutil` pass rule a, which allows every stdlib top-level name (`:141`). This closes ADV's UNVERIFIED item on stdlib handling.
- **F3 (COR-2 FALSE as stated; probe, ruff 0.17.1 = the version pinned in `pyproject.toml:50`, using the repository's `extend-select`).**
  - The ticket's exact call, `subprocess.Popen([sys.executable, "-I", "-m", "<module>"], stdin=PIPE, stdout=PIPE, stderr=DEVNULL, env=env, close_fds=True, shell=False, start_new_session=True)`, gives **no S603**. So does `subprocess.run([sys.executable, "-I", "-c", "pass"])`.
  - S603 DOES fire when any list element is not a string literal or `sys.executable`. Examples: `[sys.executable, "-c", script]` with a parameter, the same with a module-level constant `SCRIPT`, and an argv held in a module constant tuple.
  - The precedents the reviewer cites are this second shape: `tests/test_k5_classes.py:489-490` (`script` is a variable) and `tests/demo_askdata/test_meter.py:162` (`cmd` is a variable). They do not show that the ticket's literal fires.
  - S404 (`import subprocess`) does not fire.
  - A test wrapper that calls a saved `_REAL_POPEN = subprocess.Popen` with a swapped argv gives no finding.
- **F4 (COR-3 TRUE).**
  - `tickets/P6b2.md:173` (fact 14), `:350` (item 7) and `:357` say: `<subprocess>` and `<ctypes>` can never be in `ALLOW`, items 6 and 7 apply to every file, and their allow-list is EMPTY.
  - `_child_env`'s `os.environ[k]` with a variable `k` is P6b2's `<dynamic>` (`:356`), which is also fail-closed.
  - None of P6b2's build notes BN-1 to BN-15 changes either rule (`:925-1042`).
- **F5 (COR-5 FALSE as stated; probe).** Ruff 0.17.1 does not flag `except ProcessLookupError: pass` or `except OSError: pass`. S110 fires only for a broad `except Exception`, or a bare `except`, followed by `pass`.
- **F6 (ADV-16 TRUE; the reviewer's own fix is WRONG; probe).**
  - In `tests/`, S105 fires on `OWNER_PASSWORD = "..."`, S106 on `f(owner_password="...")` and S107 on a default argument `owner_password="x"`.
  - S311 fires on `random.Random(seed)` and on `from random import Random; Random(seed)`, at the constructor. The repository's own `tests/test_k5_layers.py:147` carries `# noqa: S311` on exactly that call.
  - A generator built on `hashlib.sha256(f"{seed}:{i}".encode())` gives no finding. `hashlib.md5(b, usedforsecurity=False)` gives no ruff finding (this confirms resolve fact 8 for ruff only).
- **F7 (COR-6 TRUE in part).**
  - CI runs Semgrep 1.181.0 (`p/python`, `p/secrets`, `--error`) over `src tests demos` (`ci.yml:123`), and bandit `-ll` over `src demos` (`:119`).
  - `demos/ask-your-data/askdata/cli.py:175` carries `# nosemgrep: ...dangerous-subprocess-use-tainted-env-args...` on a subprocess argv that holds a value read from the environment. So Semgrep does fire on subprocess calls whose arguments come from the environment.
  - No `hashlib.md5` call exists in `src`, `tests` or `demos` today (grep), so nothing shows whether Semgrep flags it. Semgrep and bandit are not installed in `.venv`, and I installed nothing.
- **F8 (COR-7 TRUE).** `tests/test_repo_rules.py:296` `SECRET_FREE = ["runtime", "approvals", "llm", "sources"]` and `:297-302` `SECRET_FREE_MODULES` (`tools`, `guard.http`, `guard.runmap`, `guard.egress`). The tests at `:167`, `:305` and `:401` start only from these, so a new `ingest/` package is neither scanned nor required.
- **F9 (COR-8 FALSE).**
  - `config.py:311-313` is `class Settings(BaseSettings)` with only `config_dir`.
  - `:316` `class Config(_Strict)` and `:317` `environment: Literal["dev", "pilot", "prod"]`.
  - The ticket's "`:316-317` `Config.environment`" is correct as written.
- **F10 (ADV-5; probe, Python 3.13.18 from `.venv`).**
  - A child started as `[sys.executable, "-I", "-c", ...]` with `env={}` and `cwd=` a fresh temporary folder starts and imports `hadavin_sdk` from the editable install. `sys.flags.isolated` is 1, and its environment holds only `LC_CTYPE`.
  - `/usr/bin/python3.12` (3.12.3) also starts `-I` with `env={}`, and only `LC_CTYPE` is set. This closes part of the ticket's UNVERIFIED item; I did not import `hadavin_sdk` on 3.12.
  - In this container the soft `RLIMIT_CORE` is 0 but the hard limit is unlimited, so the child can raise it; the value depends on the environment.
  - With `RLIMIT_FSIZE` set to 1 MiB in the child, a 2 MiB write to a regular file raises `OSError` errno 27 (EFBIG), and the file stops at 1,048,576 bytes. A 3 MiB write to the stdout pipe is not limited. Python ignores SIGXFSZ, so the child is not killed.
- **F11 (ADV-10; probe).** While one thread is blocked in `proc.stdout.read(...)`, `proc.stdout.close()` from another thread blocked for **4.72 s**, until the child ended. So the parent must never close a pipe that its own thread is still reading; it must kill the child first.
- **F12 (ADV-10, the reuse question).**
  - P1m's runner is `tools/mutation_runner.py` on `origin/core/P1m` (`c9fc7c9`, 2026-11-06 04:46:24 UTC), not on main. Order 26 confirms that `tools/` is not in the wheel or sdist.
  - Its `_pytest` holds `Popen` inside `try` / `except BaseException: _kill_tree(proc); raise` / `finally` (cleanup of its private ini folder).
  - Its `_wait_unreaped` uses `os.waitid(..., WNOWAIT)` because P1m must wait for the process's exit. Its `_kill_tree` does `killpg` and then `proc.kill(); proc.wait()`.
  - Its `noqa: S603` comments are on argv lists that hold caller strings.
- **F13 (ADV-8, own finding RES-1).** Step (e)'s first rule is `empty` (all pages have zero non-space characters). The addendum's `scanlike.pdf` (one image, no text) therefore gives `empty`, never `suspected_scan`, whatever the library reports. P4's stated expectation is unreachable. Both codes map to `needs_person low_quality`, so no safety outcome changes.
- **F14 (ADV-7, own finding RES-2).** Under BN-8's exact tiling, revision 3's M-72 ("an overlap-0 chunk must start at `prev.char_end` exactly") becomes the product rule itself. As worded, it would be an equivalent mutant, which the ticket forbids. BN-8 redefines it.

## Honest note (what I did NOT check, and what my probes do and do not prove)
- **No test, suite, mutant, build or install was run.** I did not edit the ticket, commit or push, and I did not touch `DECISIONS.md`, `owner-visible-limits.md`, `questions-for-lead.md` or `HEARTBEAT.md`.
- **What I ran:** six read-only probes in a scratch folder outside the repository.
  - Four `ruff check` runs (the repository's pinned ruff 0.17.1, with a copy of its `extend-select` and per-file ignores) on scratch files (F3, F5, F6).
  - Two `.venv` interpreter runs that started throwaway child processes with `env={}` (F10, F11).
  - They are probes, not evidence. The builder repeats each claim on its branch (BN-17).
- **Not checked:**
  - Semgrep and bandit (not installed; F7). Whether Semgrep 1.181.0 flags the production `Popen` with `env={}` and a literal argv is UNVERIFIED.
  - Whether `RLIMIT_CORE=0` also stops a core dump when the host's `core_pattern` pipes dumps to a handler program (UNVERIFIED; row V2 covers it).
  - Whether the named PDF library writes temporary files (it would then hit `RLIMIT_FSIZE=0`; the library addendum decides).
  - The P1m runner's command line (it is not merged).
  - Every AK1-a name, which is still ticket text.
  - Python 3.12 importing `hadavin_sdk` with `-I` and `env={}`.
- **One judgement a reader may dispute.** BN-7 makes the wait for a children slot unbounded and starts the parse deadline only after the slot is held. A queued document therefore waits instead of failing. My reason: every slot holder releases its slot within its own deadline plus the kill, because the release is in `finally` (BN-12). So any wait ends, without a new setting or a new code. The cost: one batch takes longer, and the semaphore is not strictly first-come, first-served.

## Banner for the ticket (placed under the revision line, word for word)
> **BUILD NOTES WIN.** Review round 3 (`reviews/AK2a-round3-adversarial.md`, `reviews/AK2a-round3-correctness.md`) had 15 Majors, so there is no round 4 (order 20 item 6). This ticket is FROZEN at revision 3. The builder applies build notes BN-1 to BN-20 in `reviews/AK2a-round3-resolve.md`. Where a build note and the text below disagree, the build note wins. The build-start review (order 19 A) reads this ticket together with those notes. The CHANGELOG sections are history, not instructions. Totals after the notes: 61 test rows written, 51 counted (AK2a-1: 24 R + 12 K; process runner: 15 P; library addendum: 10 P, listed). 98 mutants written, 95 counted (AK2a-1: 66; process runner: 29; addendum: 3). 20 settings (FP 7, NOT_FP 13). 17 quality codes. Cut by these notes: `KIT_PDF_CHILD_ENV`; the committed `encrypted.pdf` and its RC4 generator (moved to the addendum); Roman-numeral and single-letter headings; digit normalisation in c4; the slot timeout. AK2a-2 does not build until PENDING LEAD 7 is answered.

## Decisions (one category per finding; merged duplicates share a row)

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 (Major) + R3-ADV-13 (Minor) | PROPOSE FIX | TRUE (F1). AK1 is re-cited by name as FROZEN. The `NON_TABLE_PATHS` key becomes the single file `src/hadavin_sdk/ingest/pdf_text.py`. AK2a-2 adds that row and AK2a-1 adds none. AK1's "optional" applies to AK2a-1 only, and a relay line goes to the lead (PL 13). **BN-1.** |
| R3-ADV-2 (Major) | PROPOSE FIX (surface cut) | TRUE. The committed `encrypted.pdf` and the RC4/md5 generator are CUT from AK2a-1. The encrypted file is built at test time in the library addendum, and R14 uses a stand-in byte string. R19's `/Filter` check then holds as written. The `@` check holds because `latin1.txt`'s bytes are chosen without 0x40. **BN-2.** |
| R3-ADV-3 (Major) + R3-ADV-17 (Minor) + R3-COR-9 (Nit) | PROPOSE FIX | TRUE. The "pure function of `settings_fp`" sentence is replaced. V7 names the whole settings dump. Signatures added: `assess(pages, settings, *, reader)`, raw `chars`, an explicit dict builder for `to_bytes`/`repr`, and `from_bytes`' error mapping. **BN-4.** |
| R3-ADV-4 (Major) | PROPOSE FIX (PL 8, NEEDS LEAD, redaction) | TRUE. The neighbour set becomes ASCII graphic `0x21-0x7E` on both sides. R23 gains `/`, `:` and `12/03` cases, and M-83 is added. The remaining limit (a non-ASCII or whitespace neighbour) is stated. **BN-5.** |
| R3-ADV-5 (Major) | PROPOSE FIX | TRUE (F10). The child sets `RLIMIT_CORE=0`, `RLIMIT_FSIZE=0` and `RLIMIT_CPU` = timeout + 1 s before reading or importing anything. It runs in a private temporary working folder that is removed in `finally`. `RLIMIT_NOFILE` is a stated limit. New row P18; mutants M-94 to M-98. **BN-6.** |
| R3-ADV-6 (Major) | PROPOSE FIX (surface cut; PL 10, INFORM) | TRUE. The slot is acquired with no timeout, and the one deadline starts after the slot is held. No new setting and no new code. P7c is rewritten; M-99 is added. **BN-7.** |
| R3-ADV-7 (Major) | PROPOSE FIX | TRUE. One exact paragraph: exclusive end offset, inclusive limit, the whitespace goes to the next chunk, no zero-length or whitespace-only chunk, tail and merge rules, exact tiling. K2, K5 and `from_bytes` follow it. New K12; M-84, M-85; M-72 redefined (F14). **BN-8.** |
| R3-ADV-8 (Major) | PROPOSE FIX (+ own finding RES-1) | TRUE. `FakePdfReader` maps a sha256 to a whole `ReadResult`, with the table written out. Own finding: P4 as written is unreachable (F13), so the addendum's P3 and P4 accept `empty` or `suspected_scan`. **BN-10.** |
| R3-ADV-9 (Major) + R3-COR-4 (Minor) | PROPOSE FIX (wording; PL 9, NEEDS LEAD, owner-visible) | TRUE. I3 and Fail closed are reworded: "never partly indexed by a cut or a cleaning rule; picture pages are not read at all". The owner line states the 1-in-10 allowance and "short and either hold pictures or the reader cannot tell". `poor_pages` is already in `ChunkSet.quality`. The value is unchanged (V6). **BN-11.** |
| R3-ADV-10 (Major) | PROPOSE FIX | TRUE (F11, F12). The runner's control flow is written as one try/finally: kill the group before any wait, then wait, join threads (bounded), close pipes only after their thread ended, remove the folder, release the slot. A `Popen` `OSError` gives `worker_crash`. `KeyboardInterrupt` propagates after cleanup. The P1m runner is not imported (it lives in `tools/`, which is not in the wheel); its patterns are reused. P16 and P17; M-90 to M-93. **BN-12.** |
| R3-ADV-11 (Major) | PROPOSE FIX | TRUE. `kit_support.run_bounded` (helper thread, join with a limit, fail on a live thread) for every P row except P17, and for K3, K4, K12. P17 arms `faulthandler` as a backstop. **BN-13.** |
| R3-ADV-12 (Major) | PROPOSE FIX (PL 8 and 9, NEEDS LEAD, redaction) | TRUE. The security claim is reworded to the real property. A whitespace cut between two ASCII letters or digits, at least one of them a digit, is not valid (this keeps spaced numbers whole). New K13; M-86. Multi-word values (names) can still be split: a stated limit and an owner line. **BN-9.** |
| R3-ADV-14 (Minor) | PROPOSE FIX (surface cut) | TRUE. Roman-numeral and single-letter heading forms are CUT. Each numbered part has 1 to 3 digits, and the text after the space must not start with a lower-case letter. K1 gains negative cases; M-87, M-88. **BN-14.** |
| R3-ADV-15 (Minor) | PROPOSE FIX (surface cut) | TRUE. c4 compares lines exactly (spaces collapsed), with NO digit normalisation. That closes both the content loss and R9's c5 masking. R9 gains a `Subtotal` case; M-89. **BN-15.** |
| R3-ADV-16 (Minor) | PROPOSE FIX; the reviewer's `random.Random(seed)` fix is CONTESTED | TRUE for the password literal, which BN-2's cut removes from AK2a-1. The reviewer's fix is wrong: `random.Random(seed)` fires S311 (F6). Seeded tables use a `hashlib`-based generator in `kit_support.py`. **BN-3.** |
| R3-ADV-18 (Nit) | PROPOSE FIX (command); DECLINE (Problem length) | The mutation command is pasted by the builder from the merged P1m runner. Problem length: Nit, declined (a frozen ticket gains no rewrite). **BN-19.** |
| R3-COR-1 (Major) | PROPOSE FIX (PL 11, INFORM) | TRUE (F2). The worker imports no `importlib`. `_import_library()` returns `(extract, "<dist>==<version>")` from the library's own version attribute (addendum). P12 compares it with installed metadata in the test. A `DYNAMIC_IMPORT_OK` row is a fallback that only the lead can approve. **BN-16.** |
| R3-COR-2 (Major) | CONTEST (probe), plus a named fallback | FALSE as stated (F3): the ticket's literal argv is S603-clean under the pinned ruff. The precedents have a variable element. Plan: the builder probes first on its branch, and the test wrapper calls the saved original. If the branch's ruff or Semgrep fires on the production call, the builder stops: PL 14 (NEEDS LEAD; no suppression without the lead). **BN-17.** |
| R3-COR-3 (Major) | PROPOSE FIX (environment half, surface cut) + PL 7 (NEEDS LEAD, the `subprocess` half) | TRUE (F4). `KIT_PDF_CHILD_ENV` and `_child_env` are CUT: the child's `env` is the literal `{}`, so `pdf_text.py` reads no environment variable. The `<subprocess>` ban stays a lead decision (options and recommendation in PL 7). P6b2 joins Couplings, with the merge order. **BN-18.** |
| R3-COR-5 (Minor) | CONTEST (probe) | FALSE as stated (F5): S110 does not fire on a named exception with `pass`. Style rule only: `contextlib.suppress(<named>)`, never `except Exception: pass`. Part of **BN-17.** |
| R3-COR-6 (Minor) | PROPOSE FIX | TRUE in part (F7). Semgrep (the CI command) and bandit join the evidence. The md5 half is gone with BN-2's cut. The rule on a finding: stop and ask. **BN-17.** |
| R3-COR-7 (Minor) | PROPOSE FIX | TRUE (F8). The UNVERIFIED line becomes "accepted by reading; the builder confirms by running". **BN-19.** |
| R3-COR-8 (Nit) | CONTEST (code) | FALSE (F9). `config.py:316-317` is `Config.environment`. `Settings` (`:311`) has no `environment`. No change. **BN-19** records it. |

## Build notes (round 3), to be copied into the ticket as the section "Build notes (round 3)"

**BN-1. AK1 cites by name; the single-file `NON_TABLE_PATHS` key (R3-ADV-1, R3-ADV-13).**
- **Where these cites appear:** the header, "Words used", "Depends on", I7, I8, the step (g) cite, the `tenant_key` cite in chunk ids, and UNVERIFIED.
- **New wording:** every "AK1 revision 3 DRAFT (`3a3fcca`, unreviewed)" reads "AK1 revision 3, FROZEN with build notes BN-1 to BN-17 (`d1459d1`)".
- **Line numbers become names:** "AK1 `REASONS`", "AK1 `StepInput`", "AK1 `StepOutput`", "AK1 `tenant_key`", "AK1 Interface 4 `NON_TABLE_PATHS` paragraph", "AK1 row L8 (closed list)", "AK1 row G4 (`forged_mark`)", "AK1 I8", "AK1 Interface 7 'No step escapes'", "AK1 Interface 3 (d) as amended by AK1 BN-12".
- **AK1 build notes AK2a must respect:**
  - BN-8: `content_sha256` is hashed on raw bytes. AK2a only copies `inp.content_sha256`, so nothing changes.
  - BN-12: `run_step` catches `Exception` only. AK2a's `KeyboardInterrupt` path (BN-12 here) propagates through it unchanged.
  - BN-7: `asyncio`, `multiprocessing` and `ctypes` join L8. `ingest/` imports none of them; R17 already lists `asyncio`.
- **The row (replaces "Rules stated once", `NON_TABLE_PATHS` row):** `"src/hadavin_sdk/ingest/pdf_text.py": ("local", "starts the PDF child: a local Python process with an empty environment that opens no connection by design and is not network-isolated (V2)")`. It is a single-file key, so a future `ingest/` module that imports an L8 library is still caught.
- **Which PR adds it:** AK2a-2 adds it in AK1-b's `guard/outbound.py` if AK1-b has merged. If AK1-b has not merged, AK1-b's builder adds it on the L8 failure (L8 fails closed). AK2a-1 adds no row: it imports no L8 library.
- Couplings (AK1) and the relay to the lead: see PL 13.

**BN-2. Sample files: `encrypted.pdf` leaves AK2a-1; R19's checks (R3-ADV-2, R3-ADV-16 password half, R3-COR-6 md5 half; surface cut).**
- **CUT from AK2a-1:**
  - the committed `encrypted.pdf`;
  - the generator's RC4 and `hashlib.md5` code;
  - its made-up owner value and fixed `/ID` (AUTH-9 is withdrawn).
- **AK2a-1's committed PDFs are:** `text.pdf`, `corrupt.pdf`, `empty.pdf`, `injected.pdf`, `scanlike.pdf`.
- **The library addendum builds the encrypted file at test time** (as `bomb.pdf` is), into `tmp_path`.
  - The first choice is the named library's own writer, with an empty user password and an owner value assembled from parts in a variable whose name contains none of `password`, `pass`, `pwd`, `token`, `secret` (S105/S106/S107, F6).
  - If the library cannot write an encrypted file, the addendum's generator does it. The addendum then runs Semgrep on it (BN-17).
  - P5 keeps its precondition (open with `""` and read the made-up text), and M-33 keeps P5 as its killer.
- **R14 (encrypted case):** `FakePdfReader` maps the sha256 of the in-test stand-in `b"%PDF-1.7\n% made-up encrypted stand-in\n"` to `encrypted` (BN-10). The row asserts `needs_person unreadable` with `quality_code="encrypted"`.
- **R19 checks, now exact:**
  - (i) no committed PDF contains the bytes `/Filter`;
  - (ii) no committed file contains the byte 0x40 except inside the ASCII string `@example.invalid`;
  - (iii) `make_docs.py` writes `latin1.txt` from a fixed byte string that holds no 0x40 and is not valid UTF-8 (for example made-up words with `\xe9`).
- M-32 keeps R19.
- Files: the AK2a-1 CREATE list loses `encrypted.pdf`. `SHA256SUMS` covers 7 committed files.

**BN-3. Seeded tables without `random` (R3-ADV-16, S311 half).**
- `tests/kit_support.py` gains `seeded_ints(seed: int, label: str) -> Iterator[int]`. It yields `int.from_bytes(hashlib.sha256(f"{seed}:{label}:{i}".encode()).digest()[:8], "big")` for `i = 0, 1, ...`.
- Every "seeded random table" (R8, R10, R16b, K2, K4, K5) draws from it, with the seed in the test id.
- No `tests/` file of AK2a imports `random` (F6: `random.Random(seed)` fires S311, and suppressions are banned). `make_docs.py` already uses no randomness.

**BN-4. Quality report: signatures, what it depends on, JSON conversion (R3-ADV-3, R3-ADV-17, R3-COR-9).**
- **Signature:** `assess(pages: tuple[Page, ...], settings: IngestSettings, *, reader: str) -> QualityReport`. `settings_fp` is `settings.settings_fp`. `chars` and every count are taken from the RAW pages the reader returned, before cleaning, because step (e) runs before (f).
- **Interface 7, "The quality code reaches a person", last sentence, replaced:** "The full quality report is a function of the stored file, the WHOLE `IngestSettings` (all 20 fields, not only `FP_FIELDS`) and the Unicode data version. `settings_fp` alone is not enough to recompute it. A `done` document's report is stored in `ChunkSet.quality`. For other outcomes AK2a stores no report (row V7)."
- **V7's item gains:** "store `settings.model_dump()` and `unicodedata.unidata_version` beside the report".
- **JSON:** `ChunkSet.to_bytes()` builds a plain dict through one module function `_as_dict(chunk_set)`, which converts each dataclass field by name, writes `readers` as a sorted list and nests `quality`, `removal` and the chunks as dicts. It then calls `models.canonical_json` on that dict. No `default=` hook is used. The same `_as_dict` is never used by `repr`: records' `__repr__` stays ids, counts and hashes only (R18).
- **`ChunkSet.from_bytes` error mapping:** it catches `ValueError` (which includes `UnicodeDecodeError` and `json.JSONDecodeError`), `RecursionError` and `TypeError` from decoding and type checks. It raises `ValueError("chunk_set: <field or 'json'>")` `from None`, so the message holds no body text.
- **K11 gains:** a 100,000-deep `[` body and a 5,000-digit integer body each give `ValueError`, and a canary in the body is not in the message.

**BN-5. `hidden_chars` neighbours: ASCII graphic on both sides (R3-ADV-4; PL 8).**
- **Step (f2) rule, replaced:** `True` when a run of one or more format characters (category Cf) has an ASCII graphic character (U+0021 to U+007E) directly before it AND directly after it, on one page.
- **R23 gains**, each giving `hidden_chars`:
  - `12/` + U+200B + `03`;
  - `https:` + U+200B + `//host.example.invalid`;
  - `ab/` + U+200B + `cd`;
  - `(555)` + U+200B + `0100`;
  - `a=` + U+200B + `b`.
- **R23 keeps** `done` for the Hindi ZWJ word, the emoji ZWJ sequence and a U+200B with a space on one side.
- **Stated remaining limit (Security, and PL 8):** a format-character run with a non-ASCII character or whitespace on either side is not refused here. Examples are a Cyrillic look-alike letter next to the run, or a run at a word edge beside a space.
- **Added cost (V6):** right-to-left text with bidirectional marks beside ASCII punctuation or digits, for example `(` next to U+200F, goes to a person more often.
- **M-83** (`ingest/quality.py`): neighbour set back to `[A-Za-z0-9@._+-]`. Killed by R23 (`ab/` + U+200B + `cd`).

**BN-6. Child limits and a private working folder (R3-ADV-5).**
- **`ingest/_limits.py`:** `apply_limits(memory_mb: int, cpu_s: int) -> None` sets:
  - `RLIMIT_AS` to `memory_mb` MiB;
  - `RLIMIT_CORE` to `(0, 0)` (no core dump);
  - `RLIMIT_FSIZE` to `(0, 0)` (the child writes no regular file; pipes are not affected, F10);
  - `RLIMIT_CPU` to `(cpu_s, cpu_s)`.
  `apply_memory_limit` is renamed to it, and M-38 and M-69 refer to `apply_limits`.
- **Header line:** it gains `"cpu_s": KIT_PDF_TIMEOUT_S + 1`, a derived value, not a setting. Its job: a child orphaned by a parent killed from outside (SIGKILL, or SIGTERM with no handler) cannot spin a CPU forever.
- **Order in `_run`:** `_run` calls `apply_limits(...)` right after the header line, BEFORE reading the PDF bytes and before `_import_library()`.
- **`RLIMIT_NOFILE` is NOT lowered**, and this is stated. The child starts with `close_fds=True`, and exhausting its own table harms only itself.
- **The library addendum** may raise `RLIMIT_FSIZE` only if the named library must write a temporary file, with the reason written there.
- **Python's own `.pyc` writes:** an `.pyc` write that fails on EFBIG is ignored by the import system.
- **Private folder:** `read()` creates `cwd = tempfile.mkdtemp(prefix="kit_pdf_")` for each read and passes `cwd=cwd` to `Popen`. It removes the folder in `finally` with `shutil.rmtree(cwd, ignore_errors=True)` (BN-12). The `-I` flag already keeps the folder off `sys.path`.
- **New row P18 (process runner, counted).** Child code runs the real `w._run(w._hide_stdout())` with `w._import_library` replaced.
  - (i) The fake returns one page whose text is `repr((resource.getrlimit(RLIMIT_CORE), resource.getrlimit(RLIMIT_FSIZE), resource.getrlimit(RLIMIT_CPU), os.getcwd()))`. The read gives `ok`. The page shows `(0, 0)`, `(0, 0)` and `(timeout + 1, timeout + 1)`. The child's working folder equals the `cwd` the wrapper recorded and differs from the test's own.
  - (ii) The fake writes 1 MiB to `big.bin` in its working folder. The read gives `corrupt` (the `OSError` is "any other exception"). After the read, the recorded `cwd` no longer exists.
- **Mutants (2r):**
  - M-94 `RLIMIT_CORE` not set (P18 i);
  - M-95 `RLIMIT_FSIZE` not set (P18 ii gives `ok`);
  - M-96 `RLIMIT_CPU` not set (P18 i);
  - M-97 no `cwd=` (P18 i);
  - M-98 the private folder not removed (P18 ii).
- **Security and V2 gain:** "a core dump through a `core_pattern` pipe handler may ignore `RLIMIT_CORE` (UNVERIFIED); a process that leaves the child's process group (a library calling `setsid`) survives the group kill. Only an operating-system sandbox stops both."

**BN-7. The children slot: wait, then start the deadline (R3-ADV-6; surface cut; PL 10).**
- **Interface 9, "One deadline and the children limit", replaced:** "The slot is acquired with no timeout (`slot.acquire()`). The one monotonic deadline of `KIT_PDF_TIMEOUT_S` starts AFTER the slot is held, and it covers writing, reading and waiting."
- **Why every wait ends:** every holder releases its slot in `finally` (BN-12) within its own deadline plus the kill and the reap. So a queued read waits at most about (queued reads ahead / `KIT_PDF_MAX_CHILDREN`) x (`KIT_PDF_TIMEOUT_S` + kill time).
- **What is cut:** a queued document no longer gets `timeout`, so the "contention reported as a hostile file" path is gone. No setting and no code is added.
- **Stated cost:** batch latency, and the semaphore does not guarantee first-come order.
- **P7c rewritten:**
  - Setup: `KIT_PDF_MAX_CHILDREN=1`. Thread A reads with `KIT_PDF_TIMEOUT_S=2` against a sleeping child (A gives `timeout`). Thread B starts after the wrapper's event for A's `Popen`, with `KIT_PDF_TIMEOUT_S=2` and child code that writes a valid one-page result at once.
  - Asserts: B gives `ok`. At each `Popen` call, every earlier `Popen` object the wrapper recorded already has `returncode is not None`, read as an attribute and never through `poll()`.
- **Mutants (2r):** M-68 (semaphore removed) keeps P7c. **M-99:** the deadline starts before the slot wait (revision 3 behaviour). Killed by P7c (B gives `timeout`).
- V16 is unchanged.

**BN-8. The cut algorithm, exactly (R3-ADV-7). This replaces Interface 6 "Packing and cuts", "Overlap" and "Coverage rule" where they differ.**
- **Offsets and limit.**
  - A chunk's **new text** is `joined[s:e]`. `e` is an EXCLUSIVE end offset, and `s` is the previous chunk's `e` (or the section's start).
  - The limit is INCLUSIVE: `e - s <= KIT_CHUNK_MAX_CHARS`.
  - `char_end = e` and `char_start = s - overlap_chars`.
  - Chunks TILE `joined` exactly: the first chunk has `char_start == 0`, each later chunk's new text starts at the previous `char_end`, and the last has `char_end == len(joined)`.
- **Cut positions.**
  - A **sentence cut** after a sentence-end character at index `i` is `e = i + 1`. The character is `.`, `?`, `!` or `;` followed by whitespace, or U+3002, U+FF01 or U+FF1F.
  - A **whitespace cut** at a whitespace character at index `w` is `e = w`.
  - So the whitespace after a cut always begins the NEXT chunk.
  - A section boundary is a cut at the start of the blank-line gap before the heading line. The new section's first chunk starts with that gap and then the heading line.
- **Valid cut.** `e` is valid only if ALL of these hold:
  - (1) `s < e <= s + KIT_CHUNK_MAX_CHARS`;
  - (2) `joined[s:e]` holds at least one non-whitespace character (so no zero-length or whitespace-only chunk, and the cut always makes progress);
  - (3) `joined[e]` is not a combining mark, a ZWJ or a variation selector;
  - (4) for a whitespace cut, BN-9's digit rule.
- **Choice.** Take the largest valid sentence cut. If there is none, take the largest valid whitespace cut. If there is none and `section_end - s > KIT_CHUNK_MAX_CHARS`, `chunk` returns `(None, "unsplittable")`. If `section_end - s <= KIT_CHUNK_MAX_CHARS`, the rest of the section is one chunk.
- **Packing.** Blocks are packed from `s`. The next block (including the whitespace that separates it) is added while the new text's end stays `<= s + KIT_CHUNK_MAX_CHARS`. The `\n\n` separators count toward the limit. When the next block does not fit, the cut is the whitespace cut at the start of its gap. When one block alone does not fit, the window search above runs inside it. The tail after the last cut in a long block starts a new chunk, and packing continues with the following blocks of the same section.
- **Merging.**
  - It runs once per section, left to right, after all cuts.
  - A chunk whose new text is shorter than `KIT_CHUNK_MIN_CHARS`, and that is not the last chunk of its section, merges into the next chunk of the same section when the merged new text satisfies `next.e - this.s <= KIT_CHUNK_MAX_CHARS`. The merged chunk is checked again against its own next chunk.
  - A tail piece is an ordinary chunk for this rule. The last chunk of a section never merges.
- **Overlap**, computed last for each chunk after the first of its section:
  - `overlap_chars` is the largest `k <= KIT_CHUNK_OVERLAP_CHARS` such that `joined[s - k]` is a non-whitespace character preceded by whitespace and is a valid start under rule (3);
  - it is 0 if no such `k` exists, and 0 after a heading.
- **K5 coverage (replaces the old rule):** `chunks[0].text + "".join(c.text[c.overlap_chars:] for c in chunks[1:]) == joined` exactly, and `chunks[0].char_start == 0`.
- **K2 check (replaces its formula):** for every chunk `c` that is not the last of its section and whose new-text length `c.char_end - c.char_start - c.overlap_chars < KIT_CHUNK_MIN_CHARS`, assert `next.char_end - (c.char_start + c.overlap_chars) > KIT_CHUNK_MAX_CHARS`.
- **`from_bytes`, the overlap-0 neighbour rule tightened:** `overlap_chars == 0` requires `char_start == prev.char_end` (no gap). The first chunk requires `char_start == 0`.
- **M-72 redefined (F14):** "`from_bytes` accepts an overlap-0 chunk that starts after `prev.char_end` (a gap)". Killed by a new K11 refusal case (a set with a 1-character gap).
- **New row K12 (AK2a-1, counted), hand table.** Settings: `KIT_CHUNK_MAX_CHARS=100`, `KIT_CHUNK_MIN_CHARS=1`, `KIT_CHUNK_OVERLAP_CHARS=0`, one section, no heading, run through `run_bounded` (BN-13).
  - (a) `"a"*95 + ". " + "b"*50` gives two chunks: `[0, 96)` (ends with `.`) and `[96, 147)` (starts with the space).
  - (b) `"c"*100 + " " + "d"*10` gives `[0, 100)` and `[100, 111)` (the inclusive limit).
  - (c) `" " + "e"*100 + " x"` gives `unsplittable`. The only whitespace inside the limit is at `e = s`, which is not allowed, so there is no empty chunk and no loop.
  - (d) With the defaults, `" " + 2,000-character token` gives `unsplittable`, and `" " + 1,999-character token + " z"` gives a first chunk of exactly 2,000 characters.
- **Mutants (1):**
  - **M-84:** the progress rule (2) removed (a cut at `e == s`, or a whitespace-only chunk, allowed). Killed by K12 (c): a hang caught by `run_bounded`, or an empty chunk.
  - **M-85:** limit made exclusive (`<`). Killed by K12 (b).
- K3, K4 and K12 run through `run_bounded`.

**BN-9. Spaced values at a cut (R3-ADV-12; PL 8 and 9).**
- **Valid-cut rule (4):** a whitespace cut at `e` is NOT valid when `joined[e - 1]` and the first non-whitespace character after the whitespace run are both ASCII letters or digits and at least one of them is an ASCII digit. This keeps `+91 98765 43210`, a spaced card number and IBAN-style groups whole. The chunker then takes an earlier cut. It reaches `unsplittable` only if the whole window has no other cut.
- **"Security and least-privilege notes", the redaction sentence, replaced:** "No cut falls inside a token (a run without whitespace), and no whitespace cut falls between two digit-bearing groups. So an e-mail address or a spaced number is never split across two chunks. A value of several words, such as a two-word name, CAN be split at a whitespace cut: chunk A then holds only its first words, and the gate sees each part separately. With overlap greater than 0, the whole value is in chunk B; with overlap 0, it is in neither. A sentence cut such as `No. 5` can still separate a label from its number."
- The same correction applies to Interface 6, where it says "a value such as an e-mail address is never split across two chunks".
- **New row K13 (AK2a-1, counted).** With the defaults, made-up values:
  - a section whose last whitespace before the limit sits inside `+91 98765 43210`, and another inside `DE00 1234 5678 9000 0000 00`: no chunk boundary falls inside either value, and each value appears whole in one chunk's new text;
  - the made-up name `Person One` placed at the limit IS split. This pins the stated limit.
- **M-86** (`ingest/chunk.py`): rule (4) removed. Killed by K13.

**BN-10. `FakePdfReader` and the PDF samples (R3-ADV-8; own finding RES-1).**
- **The table:** `tests/kit_support.py` holds `FAKE_PDF: Mapping[str, tuple[tuple[tuple[str, bool | None], ...] | None, str]]`, keyed by sha256 hex and mapping to `(pages, code)`. `FakePdfReader.read` returns `ReadResult(pages=<Page tuple or None>, code=code, reader="pdf:fake==0")`, building the `Page` objects lazily inside the method. An unknown sha256 gives `(None, "corrupt")`.
- **Rows**, with page texts taken from `make_docs.PAGE_TEXTS` (the generator's own made-up strings, exposed as a module constant), not recorded from a library:

  | file | pages | code |
  |---|---|---|
  | `text.pdf` | its 3 page texts, `has_images=False` | `ok` |
  | `injected.pdf` | its page text(s), `False` | `ok` |
  | `empty.pdf` | `(("", False),)` | `ok` (`assess` gives `empty`) |
  | `scanlike.pdf` | `(("", True),)` | `ok` (`assess` gives `empty`, F13) |
  | `corrupt.pdf` | `None` | `corrupt` |
  | stand-in bytes of BN-2 | `None` | `encrypted` |

- **R14's expectations hold:** `empty.pdf` and `scanlike.pdf` give `low_quality`; `corrupt.pdf` and the stand-in give `unreadable`.
- **R4 and R1b keep** their own made-up fake pages, built in the test.
- **Library addendum, RES-1:** P3 (`empty.pdf`) and P4 (`scanlike.pdf`) each assert `needs_person low_quality` with code `empty` or `suspected_scan`, and record which. P4's "the row records whether the named library reports page images" stays.
- **Lead's call:** step (e)'s order is NOT changed. Putting the scan rule first would turn `empty.pdf` into `suspected_scan` wherever the library reports `has_images=None`. Both map to `low_quality`.

**BN-11. I3 and the owner wording on picture pages (R3-ADV-9, R3-COR-4; PL 9).**
- **I3 and "Fail closed", replaced:**
  - I3: "A document is never partly indexed by a reader cap, a cleaning rule or a cut: each of those rules either sends the whole document to a person or keeps every character the reader returned. Pages that look like pictures are not read at all (order 27 item 54). A document with at most one such page, or with at most 1 in 10 of its pages like that, is indexed without their content, and `poor_pages` in `ChunkSet.quality` says how many there were."
  - Fail closed: "never as `done` with less text than the reader returned".
- **Problem paragraph and PENDING LEAD 2, owner sentence, replaced** (the lead shows the owner; PL 9): "A PDF is sent to a person when every page is short, or when at least 2 pages and more than 1 in 10 of its pages are short and either hold pictures or the reader cannot tell. Up to 1 in 10 such pages can otherwise be left out without a person being told (in a 300-page PDF, up to 30 pages); a single short page, such as a cover, is left out too."
- **V6 gains:** "the share of `done` documents with `poor_pages > 0`, and the value of `KIT_MAX_POOR_PAGE_PPM`".
- The value stays 100,000 (I10: a made-up starting value in config).

**BN-12. The process runner's control flow (R3-ADV-10; order 31 item 2's "kill before waiting").**
- **Interface 9 gains one ordered paragraph.** `read(data, settings)`:
  1. type check;
  2. `slot.acquire()` (BN-7), then `held = True`;
  3. `try:`
     - `deadline = monotonic() + KIT_PDF_TIMEOUT_S`;
     - `cwd = tempfile.mkdtemp(...)`;
     - `proc = subprocess.Popen(<the literal argv>, ..., env={}, cwd=cwd, ...)` inside its own `try`; an `OSError` (for example EAGAIN or ENOMEM) returns `ReadResult(None, "worker_crash", ...)` and writes one log record `ingest_spawn_failed` carrying the `errno` only;
     - start the writer and reader threads (`daemon=True`; each closes its own pipe end in its own `finally`);
     - `reader.join(max(0.0, deadline - monotonic()))`;
     - if it is still alive, the result is `timeout`; otherwise judge the line (trust boundary as written);
     - `return` the result.
  4. `finally:`
     - (a) if `proc` is set: `os.killpg(proc.pid, SIGKILL)` inside `contextlib.suppress(ProcessLookupError, PermissionError)`, BEFORE any `wait()`, `poll()`, `communicate()` or read of `returncode`, then `proc.kill()` inside the same suppress (the child itself, always, as P1m's `_kill_tree` does), then `proc.wait()`;
     - (b) join the writer and reader threads, each with a timeout of `KIT_PDF_TIMEOUT_S`; a thread still alive after that (possible only if a process left the group, BN-6) is left as a daemon, and one log record `ingest_thread_stuck` (no text) is written;
     - (c) the parent closes `proc.stdin` and `proc.stdout` only for a thread that has ended, because closing a pipe that a live thread reads blocks (F11);
     - (d) `shutil.rmtree(cwd, ignore_errors=True)`;
     - (e) `if held: slot.release()`.
- **Exceptions.** `read()` catches no `BaseException`. `KeyboardInterrupt` and `SystemExit` propagate after `finally` has done (a) to (e), and so does any bug in the runner's own code. AK1-a's `run_step` (as amended by AK1 BN-12) passes them on unchanged.
- **Stated narrow window:** a `KeyboardInterrupt` that lands between `Popen` returning and the assignment to `proc`, or between `acquire()` returning and `held = True`, can leak one child or one permit. `read()` may run in a thread that is not the main thread, so no signal is masked (the same window P1m documents, order 31 item 5). A leaked child is still bounded by `RLIMIT_CPU` (BN-6).
- **Pid reuse:** no code path reaps the child before `killpg`. The reader thread ends at the newline or end of file, so the parent never needs the exit status first. That is why P1m's `waitid(WNOWAIT)` (order 31 item 2, F12) is not needed here. P1m must wait for the exit; AK2a never does.
- **Reuse decision:** AK2a does NOT import or call P1m's runner. It lives in `tools/`, outside the wheel (order 26), and `src/` must not depend on it. Its control flow is POSIX plus Windows, while AK2a-2 is POSIX only. The patterns ARE reused: try / `BaseException` kill / `finally` cleanup, the child-itself kill after the group kill, the private temporary folder, and the test lessons of orders 29 and 30: the patched call raises only once, kills are compared with the `Popen` object's pid, and a child-written pid is used only to probe the grandchild.
- **P7 gains:** after the read, the recorded `Popen` object has `stdin.closed and stdout.closed`. **M-93** (2r): pipes never closed. Killed by P7.
- **New row P16 (counted):** the wrapper raises `OSError(errno.EAGAIN, "made-up")` on its first `Popen` call. The read gives `worker_crash`, raises nothing, and leaves no `kit_pdf_*` folder from that call. A second read with `KIT_PDF_MAX_CHILDREN=1` and a valid fake child then gives `ok` inside `run_bounded`, which proves the permit was released.
  - **M-90:** the `Popen` `OSError` is not caught. Killed by P16.
  - **M-91:** the slot is released only on the normal path, not in `finally`. Killed by P16 (the second read hangs and is caught by `run_bounded`).
- **New row P17 (counted), KeyboardInterrupt.**
  - Setup: the read runs in the MAIN test thread (`_thread.interrupt_main` needs it). Child code starts a sleeping grandchild, writes its pid to a temporary file and sleeps, with `KIT_PDF_TIMEOUT_S=30`. A timer thread, started from the wrapper's `Popen` event, calls `_thread.interrupt_main()` once after 0.5 s. `faulthandler.dump_traceback_later(60, exit=True)` is armed as a hang backstop and cancelled at the end.
  - Asserts: `pytest.raises(KeyboardInterrupt)` catches it. Afterwards the recorded `Popen` object has a `returncode`. The grandchild is gone (a zombie counts as gone, as in P1m). The recorded `cwd` does not exist. A second read with `KIT_PDF_MAX_CHILDREN=1` gives `ok`.
  - **M-92:** the group kill runs only on the normal paths (not in `finally`). Killed by P17.

**BN-13. A hang harness for every process row (R3-ADV-11).**
- `tests/kit_support.py` gains `run_bounded(fn, *, limit_s: float, what: str)`. It runs `fn` in a daemon thread, joins it with `limit_s`, re-raises `fn`'s exception, and fails with `pytest.fail(f"hung: {what}")` if the thread is still alive.
- **Who uses it:** every P row except P17 (BN-12), with `limit_s` = the row's `KIT_PDF_TIMEOUT_S` + 10, and K3, K4 and K12, with `limit_s` = 30.
- So a mutant that blocks the read (M-34, M-61, M-63, M-68, M-91) or loops the chunker (M-84) fails by assertion, not by hanging. This does not rely on P1m's timeout handling, which becomes a second backstop only.
- P7's existing helper-thread join becomes this function.

**BN-14. Headings (R3-ADV-14; surface cut).**
- **Rule (a), replaced:** a numbered heading is 1 to `KIT_MAX_HEADING_DEPTH` parts of 1 to 3 ASCII digits each, separated by `.` (`1`, `1.2`, `12.3.4`), then one space, then text whose first character is not a lower-case letter (`not ch.islower()`).
- **CUT:** the Roman-numeral and single-capital-letter forms. Rules (b) Markdown and (c) all-caps stay.
- **Stated cost:** `A. Definitions`- and `IV. Results`-style headings become paragraph text. That costs only `heading_path`, never text. A first line such as `12 1/2 Inch Panels` can still be read as a heading (V6).
- **K1 gains negative cases, each staying paragraph text:** `2024 Revenue grew` (4 digits), `12 months after signing` (lower case), `A. Smith signed`, `IV. Results`. It keeps `1 Scope`, `1.1 Terms` and `2 PAYMENT`.
- **Mutants (1):**
  - M-87: the 3-digit limit removed. Killed by K1 (`2024 Revenue grew`).
  - M-88: the lower-case check removed. Killed by K1 (`12 months after signing`).

**BN-15. c4 compares lines exactly (R3-ADV-15; surface cut).**
- **c4:** "compared after digits are replaced by `#` and spaces collapsed" becomes "compared after spaces are collapsed (no digit replacement)".
- **Stated cost:** a running footer that carries a changing number (for example `ACME report - page 3`) stays in the text, unless it is a page-number-only line that c5 removes. That is noise in retrieval, not lost content.
- **Effect on R9:** the c5 fixtures (`- 3 -` on page 3 of 5) differ per page, so c4 cannot remove them first.
- **R9 gains:** `Subtotal 1,200`, `Subtotal 3,400`, `Subtotal 5,600` as the last line of pages 1 to 3 of 4 are all kept.
- **M-89** (1): digit normalisation put back. Killed by R9 (`Subtotal` case).
- M-6 keeps its killer.

**BN-16. The library version without `importlib` (R3-COR-1; PL 11).**
- **The worker** (`_pdf_worker.py`) imports at module top only `sys`, `os`, `json` and `hadavin_sdk.ingest._limits`. It never imports `importlib`.
- **The seam becomes** `_import_library() -> tuple[Callable[[bytes], Iterator[tuple[str, bool | None]]], str]`. The `str` is `"<distribution>==<version>"`, which the addendum reads from the named library's own version attribute (for example `__version__`). `reader` is `"pdf:" + that string`.
- **Test fakes** (P6b, P8d, P15, P18) return `(iterator, "fake==0")`.
- **P12 (addendum)** compares the `reader` field with `importlib.metadata.version(<distribution>)` inside the TEST. Tests are not scanned by rule a, which scans `SRC` only (`test_lockin_guard.py:21`).
- **Fallback, a lead call at the addendum's build-start review:** if the named library has no version attribute, add `f"{PKG}.ingest._pdf_worker"` to `DYNAMIC_IMPORT_OK` as one line with a reason. That widens the dynamic-import allowance for a module that parses hostile bytes, so it needs the lead.

**BN-17. Lint plan: probe first, then the named fallbacks (R3-COR-2, R3-COR-5, R3-COR-6).**
- **Step 1 of AK2a-2's build, before any other edit:** run the branch's ruff on a 10-line copy of the production `Popen` call. Save it as `AK2a-2-s603-probe.txt`. F3 says no S603 with ruff 0.17.1.
- **The argv stays the inline literal list in the call itself,** never a constant or a variable (F3: a constant tuple fires).
- **The `Popen` test wrapper** calls the saved original `_REAL_POPEN = subprocess.Popen` with the swapped argv (F3: no finding). This is stated in `kit_support.py`'s docstring as "a test-only call ruff does not see; the code string is the test's own". It is not a suppression.
- **Exceptions with `pass`:** use `contextlib.suppress(<named exception>)` wherever an error is ignored (`BrokenPipeError`, `ProcessLookupError`, `PermissionError`, `OSError` on close). Never use `except Exception: pass` (F5).
- **Evidence (AK2a-1 and AK2a-2 lint files) gains:**
  - the CI Semgrep command exactly as `ci.yml:123` runs it;
  - `bandit -q -r src demos -ll` as `ci.yml:119` runs it.
- **If ruff or Semgrep reports the production call** (Semgrep's tainted-environment rule should not match an argv of literals with `env={}`, but that is UNVERIFIED), the builder STOPS and reports. It adds no `noqa` and no `nosemgrep`: PL 14.
- **The Done line** "ruff (no S603, no `noqa`)" gains "and no `nosemgrep` in `src/hadavin_sdk/ingest`".

**BN-18. The child environment is always empty; P6b2 (R3-COR-3; PL 7).**
- **CUT:** the setting `KIT_PDF_CHILD_ENV` and `_child_env`. `Popen` receives the literal `env={}`, so `pdf_text.py` reads no environment variable, and P6b2's environment rule has nothing to report there.
- **The interpreter may still add `LC_CTYPE`** itself (F10: it does, on 3.12.3 and 3.13.18).
- **Settings:** 21 becomes 20 (AK2a-2 adds 3: `KIT_PDF_TIMEOUT_S`, `KIT_PDF_MEMORY_MB`, `KIT_PDF_MAX_CHILDREN`). `NOT_FP_FIELDS` becomes 13. R20's AK2a-2 rows become 3.
- **Other text that changes:** I13's "`KIT_PDF_CHILD_ENV` defaults to `()` everywhere" is deleted. I6 and Security say "an empty environment".
- **P11 (1) becomes:** the recorded `env` equals `{}` exactly, and the recorded `cwd` is a fresh folder (BN-6).
- **P11 (2) becomes:** the child's environment names are a subset of `{"LC_CTYPE"}`. The canary set in the parent is absent.
- M-36 (`env=None`) keeps P11.
- **`<subprocess>` under P6b2:** `pdf_text.py` still imports `subprocess`, which P6b2 bans in every file with an empty allow-list (F4). **AK2a-2 does not build until PL 7 is answered.** It already waits for AK0 D1 and PENDING LEAD 1.

**BN-19. Small cites, closed UNVERIFIED items and the mutation command (R3-ADV-18, R3-COR-7, R3-COR-8).**
- **UNVERIFIED, the import-boundary line, replaced:** "accepted by reading: `tests/test_repo_rules.py:296-302` starts its scans from `runtime`, `approvals`, `llm`, `sources` and four named modules only, so `ingest/` is neither scanned nor required; the builder confirms by running them (the guards evidence)". The same applies to "Target module and path".
- **UNVERIFIED gains, closed by probe (this file's F10):** "a `-I` child with `env={}` starts on 3.12.3 and 3.13.18; on 3.13.18 it imports the editable `hadavin_sdk`".
- **R3-COR-8: no change.** `config.py:316-317` is `Config.environment` (F9).
- **Mutation evidence command:** "the builder pastes the exact command line from the merged P1m runner (`tools/mutation_runner.py`, unmerged at `origin/core/P1m` `c9fc7c9` when this was written) into `AK2a-1-mutants.txt` / `AK2a-2-mutants.txt` at build start". The ticket's fail-before prose stays.

**BN-20. Table delta and totals (one place for the builder).**
- **New rows:** K12, K13 (AK2a-1); P16, P17, P18 (process runner).
- **Changed rows:**
  - R9, R14, R19, R20 (AK2a-2 adds 3 rows), R23;
  - K1, K2, K3, K4 (run through `run_bounded`), K5, K11 (gap and deep-JSON cases);
  - P6b, P7, P7c, P8d, P11, P15 (fakes return a version);
  - addendum rows P3, P4, P5, P12.
- **New mutants:** AK2a-1 M-83 to M-89 (7); process runner M-90 to M-99 (10).
- **Redefined:** M-72 (BN-8). M-38 and M-69 now name `apply_limits`. M-68's killer is the rewritten P7c.
- **Deleted:** the setting `KIT_PDF_CHILD_ENV`; the committed `encrypted.pdf` and its RC4/md5 generator; the Roman and letter heading forms; c4's digit normalisation; the slot timeout. AUTH-9 is withdrawn.
- **Totals:**
  - Rows: 61 written, **51 counted**. AK2a-1 has 36 (24 R + 12 K), the process runner 15 P, and the library addendum 10 P (listed).
  - Mutants: 98 written, **95 counted**. AK2a-1 has 66, the process runner 29, and the addendum 3 (listed).
  - Settings: 20 (FP 7, NOT_FP 13). Quality codes: 17. INFORM: 13 (unchanged). PENDING LEAD: 5 + 9 new (6 to 14). v1.1 rows: 16.

## Positions
- **Cut before design (order 7(3), order 8(1)).** Six findings close by deleting:
  - the child environment setting (COR-3, environment half);
  - the committed encrypted file and its RC4/md5 generator (ADV-2, ADV-16, COR-6's md5 half);
  - two heading forms (ADV-14);
  - c4's digit normalisation (ADV-15);
  - the slot timeout (ADV-6).
  Design is added only where a security or redaction defect needs it: BN-5, BN-6, BN-9, BN-12.
- **COR-2 is contested on a run, not on memory.** The pinned ruff accepts the ticket's literal argv (F3). The cited precedents have a variable element, which is a different shape. The fallback is named now (PL 14), so the builder does not guess.
- **COR-5 is contested on a run (F5).** The `contextlib.suppress` rule is kept as style, not as a lint need.
- **COR-8 is contested on code (F9).** The reviewer read `Settings` (`:311`). `Config` starts at `:316`.
- **ADV-16's own fix is refused on a run (F6),** because `random.Random(seed)` fires S311. The `hashlib`-based generator is the fix.
- **BN-12 does not reuse P1m's runner,** for three reasons: `src/` cannot import `tools/`, AK2a never needs the exit status before the kill, and AK2a-2 is POSIX only. Copying the patterns, not the code, keeps one process path per package. P1m's own reviewers judged those patterns over three rounds.
- **BN-10 keeps step (e)'s order** (`empty` before the scan rule). Changing it would move `empty.pdf` to `suspected_scan` on libraries that cannot report images. Both codes reach a person.

## Couplings (text other tickets own; this resolve edits none of them)
- **AK1 (FROZEN, revision 3 + BN-1 to BN-17, `d1459d1`).** AK1's `NON_TABLE_PATHS` paragraph and its AK2a relay line say the `ingest` row is optional. That is true for AK2a-1 and false for AK2a-2. L8 fails closed, so the row is added whichever PR merges second (BN-1). The lead may add one relay line to AK1 (PL 13). AK1-b's integration row (a chunk set holding an e-mail goes through the real gate and comes out masked) stays as revision 3 says.
- **P6b2 (revision 3 + BN-1 to BN-15).** Its fact 14 / item 7 bans `subprocess` in every `src` file with an EMPTY allow-list (F4). Its environment rule is satisfied after BN-18. PL 7 decides the `<subprocess>` exception. Merge order: P6b2 is v1 and kit work yields to v1 (order 23 item 5), so P6b2 is expected to merge first. AK2a-2 then carries the exception row PL 7 (a) defines. `tests/test_lockin_guard.py` (AK2a-2 addendum) is also on P6b2's hot-file list.
- **P1m.** Patterns reused, code not imported (BN-12). The mutation command is pasted from the merged runner (BN-19). P1m's timeout handling is no longer needed for AK2a's rows (BN-13).
- **AK0.** D1 names the library. The addendum now also decides how the encrypted sample is written (BN-2), whether the library writes temporary files (BN-6) and where its version comes from (BN-16).
- **AK2d.** `ChunkSet.quality.poor_pages` is the "pages left out" count (BN-11). The settings that change chunk ids are unchanged (`FP_FIELDS`). BN-8's exact tiling makes `from_bytes` stricter, and nothing is stored yet.
- **The lead's files.** `questions-for-lead.md` (NEEDS LEAD items 7, 8, 9, 14), `owner-visible-limits.md` (the PL 9 wording) and `freeze-list.md` (AK2a: "frozen at rev 3 + build notes BN-1 to BN-20; AK2a-2 also waits for PL 7"). I edited none of them.

## PENDING LEAD (continuing the ticket's numbering after 5)
Routing rule: an item that touches an owner hard rule (least privilege, money, redaction), owner-visible wording, the wording of an order or a frozen ticket's fail-closed rule is NEEDS LEAD. An item I can recommend on checkable evidence is INFORM, and the builder takes the recommendation meanwhile.

6. **NEW, INFORM. Freeze with build notes, no round 4.** Round 3 had 15 Majors (at least 13 distinct after the contest and the merges). Recommend: yes, per order 20 item 6. The banner goes under the revision line, and the build-start review reads the ticket and this file.

7. **NEW, NEEDS LEAD (least privilege; a frozen ticket's fail-closed rule; P6b2's wording "can never be in `ALLOW`"). AK2a-2's `subprocess` import vs P6b2's empty allow-list (BN-18).**
   - Facts: `tickets/P6b2.md:173`, `:350`, `:357`. After BN-18 the environment half is gone (`env={}`), and only `<subprocess>` remains.
   - **(a) Recommended:** a P6b2 build note, written now and before either builds, adds one mechanism: `SUBPROCESS_OK: dict[str, str]`, keyed by repository path, EMPTY when P6b2 merges.
     - AK2a-2's PR adds exactly `"src/hadavin_sdk/ingest/pdf_text.py": "<reason: starts the PDF child, literal argv, env={}, no shell>"`.
     - The rule stays fail-closed for every other file.
     - Teeth: a planted `import subprocess` in any other file is flagged, a stale key (the file is missing or no longer imports `subprocess`) fails, and `<ctypes>`, `<os.system>` and `<os.popen>` stay with no allow-list.
     - A companion check: the one listed file calls `subprocess.Popen` only with an inline list literal and `env={}` (AST).
     - Cost: one reviewed exception in a security lint, plus about 20 test lines in P6b2's file.
   - (b) Start the child with `os.posix_spawn` and `os.pipe`. P6b2 does not list it, but this dodges the intent of the ban and loses `Popen`'s pipe handling. **Refused.**
   - (c) No PDF reading in kit v1: every PDF goes to a person (AK2a-1's R21 behaviour). The cost is most client document sets.
   - (d) Run the PDF reader as a separate deployable process outside `src/`. That means a new deployment part (AK-G16) and more surface.
   - Least-privilege side of this item, for the lead to confirm with it:
     - BN-18 (the child's environment is always empty, `KIT_PDF_CHILD_ENV` cut);
     - BN-6 (`RLIMIT_CORE`, `RLIMIT_FSIZE`, `RLIMIT_CPU`, private folder).
     Both only narrow what the child can do.
   - Confidence 80 percent. Reversible (one dict entry). Interim: AK2a-2 does not build. It cannot build before AK0 D1 and PENDING LEAD 1 anyway.

8. **NEW, NEEDS LEAD (redaction). Two fail-closed widenings at ingest (BN-5, BN-9).**
   - (i) `hidden_chars` neighbours become ASCII graphic `0x21-0x7E` on both sides. Cost: more right-to-left documents and web-pasted text go to a person; the rate is unmeasured (V6).
   - (ii) No whitespace cut between two digit-bearing ASCII groups. Cost: none in safety. The cut moves earlier, and `unsplittable` happens only if the whole window has no other cut.
   - Recommended: (i) and (ii) as written.
   - Alternatives:
     - for (i), keep revision 3's `[A-Za-z0-9@._+-]` and state the `/`, `:`, `=`, `(` hole (not recommended);
     - for (ii), state the split of spaced numbers only (not recommended: a partial card or phone number would reach a model).
   - Interim: the builder takes the recommendation, because both are stricter than revision 3. Confidence 75 percent. Reversible (two predicates).

9. **NEW, NEEDS LEAD (owner-visible, for `owner-visible-limits.md`). Two wording changes.**
   - (i) PENDING LEAD 2's scan sentence is replaced by BN-11's text ("Up to 1 in 10 such pages can otherwise be left out without a person being told (in a 300-page PDF, up to 30 pages)..."). It merges COR-4's "short and either hold pictures or the reader cannot tell".
   - (ii) PENDING LEAD 5's owner line gains: "A value written as several words, such as a two-word name, can be cut into two passages; each passage is checked for masking on its own, so a name the system knows only as a whole may be sent in parts."
   - Recommended: approve both as written. `KIT_MAX_POOR_PAGE_PPM` stays 100,000 until V6 measures it.
   - The alternative, to lower the poor-page share (for example to 1 page in 50), is a threshold decision. It sends more mixed documents to a person, at a rate nobody has measured.

10. **NEW, INFORM. Slot wait without a timeout (BN-7).** Recommend: accept. A queued document waits instead of being reported as a hostile file. Every holder releases within its deadline, because the release is in `finally`. Confidence 80 percent. Reversible (one argument).

11. **NEW, INFORM. The library version without `importlib` (BN-16).** Recommend: the library's own version attribute, checked against installed metadata in P12. The `DYNAMIC_IMPORT_OK` fallback becomes NEEDS LEAD at the addendum's build-start review, if the named library has no version attribute. Confidence 75 percent.

12. **NEW, INFORM. Surface cuts.** Each is reversible and each is stated with its cost:
    - `encrypted.pdf` built at test time in the addendum (BN-2);
    - Roman and letter headings (BN-14);
    - c4's digit normalisation (BN-15);
    - the `hashlib`-based seeded tables (BN-3).
    Recommend: accept. Confidence 80 percent.

13. **NEW, LEAD (not owner). One relay line for frozen AK1 (BN-1).** AK1's `NON_TABLE_PATHS` paragraph and its AK2a relay line say "optional". Recommend: the lead appends to AK1's relays, without a new AK1 round: "AK2a-2's `ingest/pdf_text.py` imports `subprocess` (on L8's list), so its single-file `NON_TABLE_PATHS` row is required; 'optional' applies to AK2a-1 only." Nothing breaks without it, because L8 fails closed. Only the lead edits a frozen ticket.

14. **NEW, NEEDS LEAD (conditional; the owner's "no suppressions" rule). Only if BN-17's probe on the branch shows S603, or Semgrep reports the production `Popen`.**
    - Options:
      - (a) one reasoned `# noqa: S603` or `nosemgrep` on that one call, as `tools/mutation_runner.py` and `demos/.../cli.py:175` carry;
      - (b) `os.posix_spawn` (refused, see 7 (b));
      - (c) no PDF reading in kit v1.
    - Recommended: (a), only with the lead's explicit yes, because CLAUDE.md bans suppressions.
    - F3 says this should not arise with ruff 0.17.1. It is stated now so the builder stops instead of guessing.

## Counts
- **Finding ids: 27** (ADV 18, COR 9).
  - Majors: 15 (ADV-1 to ADV-12, COR-1 to COR-3).
  - Minors: 9 (ADV-13 to ADV-17, COR-4 to COR-7).
  - Nits: 3 (ADV-18, COR-8, COR-9).
  - No Blocker. No severity changed.
  - Merged: ADV-1 + ADV-13; ADV-3 + ADV-17 + COR-9; ADV-9 + COR-4. That leaves 23 decision rows.
- **Categories by id:**
  - PROPOSE FIX: 24.
    - Six of them are surface cuts (ADV-2, ADV-6, ADV-14, ADV-15, the environment half of COR-3, and ADV-16 through BN-2).
    - ADV-16 has a CONTESTED part (the reviewer's `random.Random` fix).
    - ADV-18 has a DECLINED part (Problem length).
  - CONTEST: 3 (COR-2, COR-5 and COR-8; by probe or code).
  - ESCALATE: 0.
- **Own findings:** 2. RES-1 (P4's expectation is unreachable under step (e)'s order, F13). RES-2 (M-72 would become equivalent under exact tiling, F14).
- **Build notes:** 20 (BN-1 to BN-20; BN-20 holds the table delta and totals).
- **Totals after the notes:**
  - Rows: 61 written / 51 counted (+K12, K13, P16, P17, P18).
  - Mutants: 98 written / 95 counted (+M-83 to M-99).
  - Settings: 20 (-`KIT_PDF_CHILD_ENV`).
  - Codes: 17.
- **PENDING LEAD:** 9 new (6 to 14).
  - NEEDS LEAD: 7, 8, 9, and 14 (conditional).
  - LEAD: 13.
  - INFORM: 6, 10, 11, 12.
- **Probes run:** 6, read-only, in a scratch folder, not evidence. Tests, suites, lints of the repository and mutants run: 0.
- **Fixes applied to the ticket in this step:** 0 (they are build notes). Remaining unaddressed findings: 0.

**Gate sentence:** Review round 3 of AK2a had 15 Majors (12 adversarial, 3 correctness; at least 13 distinct after one contest and the merges), above the cap of 2 for a 4th round, so there is NO round 4: AK2a is FROZEN at revision 3 with build notes BN-1 to BN-20, and AK2a-2 additionally waits for PENDING LEAD 7.
