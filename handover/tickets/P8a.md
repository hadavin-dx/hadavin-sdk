# Package ticket P8a: re-pin the four demo repositories once to the final core commit. DRAFT revision 2

Revision 2 written 2026-11-06 03:20 UTC (08:50 IST; IST = UTC+5:30) by a ticket revision author (order 20 item 6). It applies `reviews/P8a-round1-resolve.md` (round 1: `reviews/P8a-round1-adversarial.md`, `reviews/P8a-round1-correctness.md`). Revision 1 was drafted 2026-11-06 02:45 UTC (08:15 IST). Text only: no code, no pull request, no suite run, no push.

Read on this repository at `origin/main` `4ec3616` (revision 1 read `124258b`; the resolve re-checked the main-dependent claims at `4ec3616`, fact F1, and I re-checked the two hashes T7 and T8 depend on). Demo facts come from the partial demo snapshots in `handover/promotion-inputs/` (MANIFEST.csv rows 2213-2215 apexc, 2261-2262 dealdesk, 2190-2192 intake, 2310-2311 refunds). Every demo cite names its snapshot folder. There are six intake snapshots (`intake-main`, `-6b`, `-6d`, `-a12`, `-p2`, `-wp3`), and their copy sets differ. Which snapshot matches each demo's live head is UNVERIFIED.

"UNVERIFIED" = I could not read or run it. "PENDING LEAD" = a proposal; the lead decides. "NEEDS LEAD" = an item in `questions-for-lead.md`.

**Every action on a demo repository is lead-only.** The demos are outside this repository, and "anything outside the repository" is on the LEAD-ORDERS Never list. Order 6(c) says "you write only the ticket text ... the lead executes". The cloud session does no demo work and pushes to no repository. This ticket is the plan for the lead's sitting.

Review gates (R1-COR-8):
- The ticket review follows order 20 item 6: round 1 is done, and this revision is the input to round 2. Round 3 is the last, because the cap is 3 rounds counting from round 1. P8a is not a money or redaction package, so it gets no round 4. After round 3: freeze, then one build-start review (order 21 item 17; PENDING LEAD 11).
- The review of the demo diffs follows order 6(b) Tier B: one fresh reviewer, plus the adversarial reader for the look-alike diffs. That reader is now mandatory (R1-ADV-6).

## Words used (one meaning each)
- **demo**: one of the four demo repositories named in amendment A7: apexc, dealdesk, intake, refunds. Each is a separate git repository, not part of `hadavin-sdk`.
- **pin**: the one core commit a demo says it is built against. It appears in three places: the `hadavin-sdk @ git+...@<sha>` line in the demo's `pyproject.toml`, the same line in `uv.lock`, and `core_commit` in the demo's `core_copies.json`. **re-pin**: move the pin to a newer core commit.
- **copy**: a core file held inside a demo as a temporary byte copy (some import lines rewritten), listed under `files` in `core_copies.json`. **snapshot** (`pr_snapshot`): the unmerged core commit a copy was taken from.
- **seam**: the one demo module through which the rest of the demo reaches the text fold (refunds `textnorm.py`, intake `textfold.py`, dealdesk `textnorm.py`). apexc has no seam: its modules import the fold copy directly.
- **look-alike check**: a demo decision that treats two strings as the same person or address when one is written with look-alike letters (for example a Cyrillic "а" in place of a Latin "a").
- **FINAL**: the core `main` commit at the moment P8a starts, after every v1 row except P8a, P8b and P8c is merged. It is written as `<FINAL>` below: a placeholder, never a real value in this file.
- **sync check**: the studio tool `tools/core_sync_check.py`. It lives in the studio repository on the lead's laptop, not in this repository, and nobody here has read it. **copy test**: the test inside each demo that hashes the demo's own copies (named below).
- **blocked demo**: a demo whose re-pin stops at a stop rule below. It is recorded as "P8a-<demo> blocked", with the rule and the output, and the other demos go on (R1-ADV-11).

## Template fields

- **Package id and name:** P8a, "Tag each demo `pre-repin`, re-pin each demo once to the final core commit, make each demo's own tests pass" (plan-v3 row P8a, step S5). **0 core pull requests.** 4 demo change sets (P8a-apexc, P8a-dealdesk, P8a-intake, P8a-refunds), plus an optional fifth (the portal kit, PENDING LEAD 7). Each change set is one branch and one pull request in its own demo repository. The lead makes, runs and merges all of them.
- **Path class:** other. Extended review (no round cap): **no**. Not a money, redaction or security package. One honest caveat: the fold swap (rows T1 and T2) changes the input of four look-alike checks in the demos (listed under "Security"). For those, revision 2 adds a mechanical before/after check (R13) and a mandatory adversarial reader. It does not add an extra review round.
- **Depends on (merged first):** every v1 row in plan-v3 line 48 except P8a, P8b and P8c: P0a-P0e, P1m, P1a, P1b, P2a-1, P2d-1, P2d-2, P2d-2b, P3a, P4a, P4b1, P4b2, P4c, P4d, P5a, P5b1-P5b5, P5c, P6a, P6b1, P6b2 (split ids per A12). P8b and P8c come after P8a (plan rows), and they also wait for any blocked demo.
  - P8a changes no core file, so it adds no `defaults.py` block (order 20 item 5 does not apply).
  - Gate (orders 21 item 17 and 6(c) together): the standing S0 EXIT applies only after this ticket's freeze and its build-start review (PENDING LEAD 11). "Building" P8a means the lead's sitting, because the cloud executes nothing on the demos.
  - Start rule (R1-ADV-5): before any edit, the lead runs `git -C <core> cat-file -e <FINAL>:<path>` for each of the T1-T3 core paths. If any one of them is missing, P8a's dependencies are not met and P8a does not start. There is no partial re-pin.
- **Problem in plain words:** Each demo holds byte copies of core files taken from unmerged core pull requests, and pins an old core commit (`6608146`). When v1 is merged, some of those files will exist on core `main` in a newer form and others still will not. If the demos are not moved, they keep testing old copies, and the next client build that starts from a demo starts from old code. P8a moves every demo, once, to the same core commit. It deletes the copies that core now provides, keeps the copies core still lacks (with their snapshot written down), and proves with each demo's own tests, plain git checks and the sync check that nothing drifted.
- **Source of the code / what is NOT taken:** no code is taken. What exists today (cites re-read for revision 2):
  - **Pins.** apexc, intake and refunds have `core_commit` = `660814674ece...` (`apexc/core_copies.json:5`, `intake-main/core_copies.json:4`, `refunds/core_copies.json:5`). dealdesk has the short form `"6608146"` (`dealdesk/core_copies.json:4`). apexc pins `hadavin-sdk` in `pyproject.toml` and `uv.lock` (`apexc/CORE_COPIES.md:17`), in the test group only (recipe step 3, `apexc/CORE_COPIES.md:37`). Neither `pyproject.toml` nor `uv.lock` of any demo is in `handover/`: UNVERIFIED.
  - **Copies (counted by script from each `core_copies.json`).**
    - apexc has 7: `textnorm.py`, `_confusables.py`, `egress_text.py`, `stop_gate.py`, `rowstore.py`, `config_view.py`, `mutation_judge.py`, all from snapshot `153d217`.
    - dealdesk has 4: `core_copy/textnorm.py`, `core_copy/_confusables.py` and `core_copy/egress_text.py` from `153d217`, and `core_copy/approvals_signed.py` from `cd62212`.
    - refunds has 2: `core_copy/textnorm.py` and `core_copy/_confusables.py`, from `153d217`.
    - intake has 3 in `intake-main`, `-6b`, `-6d` and `-wp3`: `core_copy/textnorm.py` and `core_copy/_confusables.py` from `855b4e0`, and `safe_text.py` with no snapshot. It has 4 in `-a12` and `-p2`, where the fourth is `core_copy/redact.py` from `ce70eb5` (PENDING LEAD 10).
    - Total 16 on `intake-main` (17 on `intake-a12`). The 13 copies of apexc, dealdesk and refunds have their bytes in `promotion-inputs/<demo>/`. intake's copies are listed in `intake-main/core_copies.json`, but their bytes are in `intake-a12` and `-6b` (`intake-main` has no `src/intake/core_copy/`).
  - **Where the snapshots live.** `153d217` and `855b4e0` are reachable only on `origin/core/promote-apexc-review8` and `origin/handover-src/pr50-local-748849c`. `cd62212` is reachable only on `origin/core/promote-refunds-r8` (resolve F1, `git branch -a --contains`). `ce70eb5` is an ancestor of `origin/main` (I re-ran `git merge-base --is-ancestor`).
  - **NOT taken: copying `check_core_copies`.** The plan row's "copy `check_core_copies` into a demo that lacks it" is withdrawn by amendment A9 F9, which wins over plan-v3 (order 2). The reason, re-read: the script never opens the demo's own copy. Its loop reads only the core side (`apexc/tools/check_core_copies.py:24-34`). intake's version claims in its docstring that it undoes the rewrite (`intake-main/tools/check_core_copies.py:5-6`), but its code reads only the core side too. So a hand-edited copy passes it.
  - **The copy test that does work** already exists in all four demos: apexc `tests/test_v9.py:335`, dealdesk `tests/test_review1_newapi.py:259`, intake-main `tests/test_review6.py:242` (and `:260` for `safe_text`), refunds `tests/test_review11.py:280`.
- **Target module and path in `src/hadavin_sdk/`:** none. The targets are in the demo repositories: `pyproject.toml`, `uv.lock`, `core_copies.json`, `CORE_COPIES.md`, the copy files, the files that import a deleted copy (table "Import sites" below), the copy tests, the mutant lists, and apexc's `mutant_kills.json`, `acceptance.md` and `README.md`.
- **Interface:** none in core. After the swap, the demos call these public names of `hadavin_sdk.guard.textnorm`, all in P1's `__all__` (`tickets/P1.md:42`): `fold`, `squeeze`, `fold_key` (an alias of `identity_key`, `P1.md:44`), `has_mixed_script`, `AllowVerdict`, `allow_equal`, `names_equal`. They also call:
  - one private module, `hadavin_sdk.guard._confusables` (its `TABLE`; `P1.md:42` keeps `_confusables.TABLE` and makes the fold read a frozen copy of it), read only by an intake test (row T1, intake);
  - `hadavin_sdk.testing.mutation` `judge` and `Verdict` (apexc, row T3; `P1.md:236` keeps the module in the wheel, and `P1.md:72` says it is not verbatim).
  - Coupling to P1: if P1's build drops or renames any of these, that demo is blocked (R0b, R0c).
- **Neutral default / working alternative:** not a kind; there is nothing to choose. The two checking tools are an honest pair. The demo copy test lives in each demo and catches an edited copy. The sync check lives in the studio and catches a stale pin, an expired local item, and a copy left behind after core has the file. **Done does not rest on the sync check** (R1-ADV-4): every check it makes has a plain git or stdlib killer below, and R4 is the second killer of each.
- **Files to change per demo (the lead does all of it; the start rule above gates the table):**

  | Row | Demo copy | Core path | On main at FINAL? | Action |
  |---|---|---|---|---|
  | T1 | `textnorm.py` (apexc `src/apexc/`; dealdesk, refunds, intake `.../core_copy/`) | `guard/textnorm.py` | yes (P1a), with different bytes | Delete the copy and its `files` entry. Every import site in the table below moves to `hadavin_sdk.guard.textnorm`. |
  | T2 | `_confusables.py` (all four) | `guard/_confusables.py` | yes (P1a) | Delete the copy and its `files` entry. |
  | T3 | apexc `mutation_judge.py` | `testing/mutation.py` | yes (P1m), edited, not verbatim (`P1.md:72`) | First run R0c. Then delete the copy and its entry. `apexc/mutation_check.py:29-30` imports `Verdict` and `judge` from `hadavin_sdk.testing.mutation`; the call at `:486` stays as it is. Reword the docstring at `:483` (it says "a copy"). Drop the 7 apexc fold mutants (PENDING LEAD 12) and update `mutant_kills.json`, `acceptance.md` and `README.md` for the new count and list hash (recipe step 6, `apexc/CORE_COPIES.md:42-43`). |
  | T4 | `egress_text.py` (apexc; dealdesk `core_copy/`) | `guard/egress_text.py` | no (P2b, v1.1) | Keep it at `153d217`. Drop its import-rewrite pair (`hadavin_sdk.guard.textnorm` ↔ the demo fold), so the copy's `:57` imports core's fold (one fold per demo). The pinned hash is unchanged, because the bytes become the core bytes. |
  | T5 | apexc `stop_gate.py`, `rowstore.py`, `config_view.py` | `runtime/...` | no (P2a moved them to v1.1: `P2a.md:42`, `:418-419`) | Keep at `153d217`, unchanged, rewrite included (`stop_gate.py` keeps `hadavin_sdk.models` ↔ `apexc.audit_event`). |
  | T6 | dealdesk `core_copy/approvals_signed.py` | `approvals/signed.py` | no (PR #49 = P3b, v1.1) | Keep at `cd62212`, unchanged. Its three importers stay: `tests/engine_kit.py:12`, `tests/test_decisions.py:9`, `tests/test_review1_newapi.py:15`. |
  | T7 | intake `safe_text.py` | `demos/ask-your-data/askdata/safe_text.py` | yes, already today | Keep it. It has no snapshot, so it is read at `core_commit`. Expected unchanged: today its core file at `4ec3616` hashes (LF) to the pin, which I re-ran (`49ef89fc...` both), and no v1 ticket edits that file (resolve F1). **Stop rule:** a mismatch at `<FINAL>` blocks intake, with no re-copy. |
  | T8 | intake `core_copy/redact.py` (only on heads like `-a12` and `-p2`) | `guard/redact.py` | yes (it is on main today, in a newer form) | Conditional on PENDING LEAD 10. Delete the copy and its entry. The seam `src/intake/coreredact.py:10-11` imports `hadavin_sdk.guard.redact` (`kind_of`, `redact`). intake's seam test (intake-main `tests/test_review6.py:271-281`) exempts `coreredact.py` the way it exempts `textfold.py`: the test is rewritten, not deleted. The copy is already behind main today: `ce70eb5` hashes `63d8a9f7...`, `4ec3616` hashes `0de1df57...` (I re-ran both). |

  **Import sites of T1-T3 copies** (resolve F3; every line re-read; these are the only sites in the snapshots):

  | Demo (snapshot) | Site | What it imports | Change |
  |---|---|---|---|
  | apexc | `src/apexc/normalise.py:9` | `fold, squeeze` (re-export; `fakes.py:15` takes `squeeze` from it, so `fakes.py:760, 770` reach the fold indirectly, through `normalise.py:9`) | import from `hadavin_sdk.guard.textnorm` |
  | apexc | `src/apexc/egress_text.py:57` (kept copy, T4) | `fold, fold_key, has_mixed_script, squeeze` | T4 |
  | apexc | `tests/test_v9.py:220` (`test_every_unicode_space_separates_words_in_the_fold`) and `:347` (`test_shared_vectors_pass_on_the_copy`) | `fold` | import from core; `:346`'s name becomes `..._on_core`; its vectors are judged by R13 |
  | apexc | `mutation_check.py:29-30` | `Verdict`, `judge` | T3 |
  | dealdesk | `src/dealdesk/textnorm.py:11` (seam); docstring `:1` names `core_copy/textnorm.py` | `fold` | import from core; reword `:1` |
  | dealdesk | `src/dealdesk/guards.py:13` | `AllowVerdict, allow_equal` | import from core |
  | dealdesk | `src/dealdesk/core_copy/egress_text.py:57` (kept copy, T4) | `fold, fold_key, has_mixed_script, squeeze` | T4 |
  | dealdesk | `tests/test_nameindex.py:55` | `names_equal` | import from core |
  | refunds | `src/refunds/textnorm.py:17-18` (seam; a two-line import, `textnorm as _core`) | the module | `from hadavin_sdk.guard import textnorm as _core` (the alias `_core` stays: refunds' mutant `mutants_review12.py:35` searches for `return _core\.fold_key\(s\)`) |
  | intake (`-a12`) | `src/intake/textfold.py:11` (seam); docstring `:3` names `intake.core_copy.textnorm` | `fold` | import from core, or PENDING LEAD 9 option (b); reword `:3` |
  | intake (`-a12`) | `tests/test_invoicecheck.py:1226` (`test_core_copy_agrees_on_overlapping_confusables`) | the module `_confusables` (reads `TABLE`) | import `hadavin_sdk.guard._confusables`. Its exact-set assertion at `:1229-1230` will change if P1's table differs: closed under R12, with the code points listed |

  **Also per demo:**
  - `pyproject.toml` and `uv.lock` move to `<FINAL>`.
  - `core_commit` becomes the full 40-character `<FINAL>`; dealdesk's short form goes.
  - `CORE_COPIES.md` is rewritten to list the kept copies. `allowed_local` entries whose file was deleted are removed.
  - **Dependency placement rule (all four demos, R1c):** if `git grep -lE "^\s*(from|import) hadavin_sdk" -- src` prints anything, `hadavin-sdk` goes in `[project].dependencies`; otherwise it goes in the test group. After T1, apexc, dealdesk and refunds import core at run time, so for them it goes in `dependencies`. intake is PENDING LEAD 9.
  - apexc's own merge recipe (`CORE_COPIES.md:31-45`) assumed that ALL of PR #50 merges. Its step 2 ("drop every `pr_snapshot`", `:34`) is WRONG for P8a, because T4 and T5 stay unmerged. Its step 5 (delete `core_copies.json`, the copy test and the file, `:40`) does not apply while copies remain.
  - **Demo tests that must change (read).** One rule (R1-ADV-1): **no test is deleted. A test whose subject is gone is rewritten to assert that the subject is gone, so it still fails if the subject comes back.**
    - refunds `tests/test_review11.py:280` (`test_the_core_copy_is_byte_for_byte_what_the_pin_says`; `:283` asserts `pin["files"]` is not empty, and `:293` pins `core_pr == 50` and `pr_snapshot == "153d217"` per file). It is rewritten to assert four things: `pin["files"] == {}`; `src/refunds/core_copy/` does not exist; `pin["core_commit"]` is 40 hex characters; and `src/refunds/textnorm.py` imports `hadavin_sdk.guard.textnorm`.
    - refunds `:296` (`test_the_promotion_table_names_every_copy_every_core_pr_and_the_pin_note`). Its `files` loop becomes empty, but its needles still bind (`"PR 49"`, `"PR 50"`, `"textnorm"`, `"153d217"`, ...: `:302-313`). So refunds `CORE_COPIES.md` keeps those words, truthfully: the `allowed_local` rows name PR 49, and a history line names PR 50 and `153d217`. refunds `core_copies.json` keeps `"files": {}` and `allowed_local`; it is not deleted. Its top-level `"core_pr": 50` is removed, because no copy from PR 50 is left. refunds `tests/test_review12.py:247` (only the seam may name `core_copy`) stays true without an edit.
    - intake-main `tests/test_review6.py:257` (asserts "core PR #50" in `CORE_COPIES.md`). It is rewritten to assert that no `core_pr` 50 row remains, and the top-level `core_pr` 50 is removed (R1-COR-4). This applies under PENDING LEAD 9 option (a) only. Under (b), intake keeps its copies and the test as they are.
    - dealdesk `tests/test_review1_newapi.py:259-268`. `:261` (`table["core_pr"] and table["files"]`) holds, because dealdesk keeps T4 and T6. `:268` also requires the word `TEMPORARY` in `CORE_COPIES.md`, which stays.
    - apexc `tests/test_v9.py:343` requires `#<core_pr>` (that is, `#50`) in `CORE_COPIES.md`, and `tests/test_v11.py:263` requires `core_pr == 50` at top level and on every file. Both hold, because the kept T4 and T5 copies are still from PR 50.
    - apexc `tests/test_v9.py:220`, `:347`, dealdesk `tests/test_nameindex.py:55` and intake-a12 `tests/test_invoicecheck.py:1226`: import changes, as in the import-site table.
  - **Possible changes of an expected value (UNVERIFIED until run; R12 lists them):** fixtures pinned to the old fold output (apexc `tests/fixtures/textnorm_vectors.json`, used by `test_v9.py:346`), anything that calls `fold_key`, and intake-a12 `test_invoicecheck.py:1229-1230`. A changed value that is NOT a look-alike decision is fixed by re-deriving it from the core fold and saying so in the demo pull request, never by deleting the test. A changed look-alike value is accepted only through R13.
- **Existing core code reused (checked):** none is changed. Read:
  - P1 (the names kept; `P1.md:42`, `:44`, `:72`, `:236`).
  - P2a (stop gate, row store and config view moved to v1.1; `P2a.md:42`, `:418-419`).
  - `limits.py` on `origin/main` `4ec3616` (`git show`, re-read). `stop(self, by)` is at line 43 and `reset(self, by)` at line 48. There is no `source=` and no `is_stopped`.
  - apexc's gate copy declares `stop(by, source)`, `reset(by, source)` and `is_stopped()` (`stop_gate.py:61-63`). Neither today's core nor P2a's `Limits` has them (`P2a.md:42`; `:84` makes `environment` a required keyword). So the gate can only run against apexc's own fake today. Whether apexc ever passes a real core `Limits` is UNVERIFIED (PENDING LEAD 4).
  - Resolve F2: in no snapshot does a runtime module import `hadavin_sdk`; the hits are docstrings and comments only. R0b re-checks this on the live heads, which is why no audit of the wider core API is planned (cut, R1-ADV-2).
- **Security and least-privilege notes:**
  - The lead works in a fresh clone of each demo, never in a worktree a builder is editing.
  - No secret, no live model call, no paid call. `uv lock` needs network access to GitHub on the lead's laptop.
  - Tags `pre-repin` are created only by the lead (plan rule 9(b); plan-v3 line 193: "Each demo repo gets a `pre-repin` tag before P8a").
  - The demo repositories are public. The re-pin pull requests carry no owner name, studio path or real-looking value.
  - **Look-alike checks that get a new fold (resolve F4, re-read):**
    - refunds `approval.py:144-147` (requester or beneficiary equal to an approver after `_skeleton`, `:53` → `textnorm.skeleton` → `_core.fold_key`, `textnorm.py:96-98`);
    - apexc `egress_text.py:352, 415` (`fold_key`);
    - dealdesk `guards.py:84-89` (`allow_equal(recipient, requester_email)`; `LOOKALIKE` and `VARIANT` refuse an outbound recipient; new in revision 2);
    - intake `tests/test_review6.py:285` (`fold_text("аpple") == "apple"`, a Cyrillic look-alike pinned through the seam; the same line is in `intake-main`, `-6b` and `-a12`).

    Each of these diffs gets R13 (a mechanical before/after check) and the mandatory adversarial reader.
  - Fold version: P1's keys carry `FOLD_VERSION` (A9 F3), which includes `unicodedata.unidata_version`. A demo that runs a different Python than core's pinned one can get different keys. Which Python each demo runs is UNVERIFIED (PENDING LEAD 5).
  - Whether any demo STORES fold output (dealdesk `SqliteLedger`, refunds `store.py`) is UNVERIFIED. If one does, its made-up local data is re-seeded after the re-pin.
- **Tests (pass criteria; each row is run per demo by the lead and the raw output is saved; sitting order: R8, R0a, R0b, R0c, fail-before, edits, the rest):**
  - R0a sync tool, read and baseline, before any edit (R1-ADV-4). The lead reads `core_sync_check.py`, runs `--help`, and runs it once on each unmodified demo, and pastes all of it into the evidence. The flags as memo-6 section C describes them (`studio-notes/memos/memo-6-kernel-and-claims.md:38`): `--core <core> --demo <dir> [--demo ...] [--json] [--strict-pin] [--core-ref REF]`, with exits 0 (no errors), 1 (errors) and 2 (incomplete). That is "as described, confirmed by R0a". For PENDING LEAD 10, R0a also records intake's live `core_copies.json` `files` keys.
  - R0b import inventory, before any edit (R1-ADV-2). Run `git grep -nE "^\s*(from|import) hadavin_sdk" -- '*.py'`, and then the R7 pattern below, and save the output. A hit that is not in the import-site table (or in T5's kept rewrite) blocks that demo. The fix is a demo adapter in the demo, never a core change, and the lead decides.
  - R0c judge signature (apexc only, before T3). Compare `inspect.signature(judge)` and the members of `Verdict` in `mutation_judge.py` and in `hadavin_sdk.testing.mutation` at `<FINAL>`, using one short `python -I` print, saved. If they are not equal, apexc is blocked (P1m's edits are suppression edits, `P1.md:72-74`, but the signature after them is UNVERIFIED).
  - R1 pin equals FINAL: `pyproject.toml`, `uv.lock` and `core_commit` all name `<FINAL>` (one grep line each).
  - R1b pin is on core main: `git -C <core> merge-base --is-ancestor <core_commit> <FINAL>` exits 0 (a plain-git killer for M2).
  - R1c dependency placement follows the rule above: a printed pair (src imports core yes/no; `hadavin-sdk` in `dependencies` yes/no) must agree.
  - R2 lock is consistent: `uv lock --check` exits 0. The flag name is UNVERIFIED for the lead's uv version; `uv sync --locked` is the fallback.
  - R3 copy test of the demo passes: apexc `test_v9.py:335`, dealdesk `test_review1_newapi.py:259`, intake `test_review6.py:242` and `:260`, refunds the rewritten `test_review11.py:280`.
  - R4 `python <studio>/tools/core_sync_check.py --core <core checkout at FINAL> --demo <apexc> --demo <dealdesk> --demo <intake> --demo <refunds> --strict-pin --json` exits 0. This is one call with four `--demo` flags (R1-COR-7; repeatable per memo-6 C; confirmed by R0a). R4 is the second killer of every tool-killed mutant, never the only one.
  - R5 apexc and intake only: `python tools/check_core_copies.py <core checkout>` exits 0. It is kept because both demos already run it. It proves only that the pinned core files exist on the core side.
  - R6 the demo's own full suite is green, run with the command the demo's own CI file uses, plus its lint step. The command is UNVERIFIED per demo: the lead reads it from the demo's workflow file and writes it in the evidence.
  - R7 no import of a deleted copy remains. Run `git grep -nE "core_copy[./]+(textnorm|_confusables)|core_copy import (\(|textnorm|_confusables)|apexc[. ]+(import )?(textnorm|_confusables)|(from|import) mutation_judge" -- '*.py'` (this covers src, tests, tools and mutation). It **must print nothing**.
    - It does NOT ban `core_copy` itself: dealdesk keeps `core_copy.approvals_signed` and `core_copy.egress_text`, and the pattern does not match those imports.
    - I ran it on the snapshots before writing this row. It finds all 16 known lines (apexc 6, dealdesk 6, refunds 1, intake-a12 3). Those are the 13 import sites above, the two stale docstrings (dealdesk `textnorm.py:1`, intake `textfold.py:3`), and the dropped dealdesk mutant (`mutation/mutation_check.py:960`). It does not match the kept copies apart from their rewritten import line, which T4 removes. So on the old code it is a working fail-before.
    - Corrected from the resolve's pattern for two reasons. The resolve's version missed refunds' two-line import `from refunds.core_copy import (` (hence `core_copy import \(`). Its bare `mutation_judge` also matched intake's own test `test_mutation_judge_separates_assertion_kills_from_crashes` (intake-main `tests/test_review6.py:225`, intake's own judge, not the copy), so I changed it to `(from|import) mutation_judge`.
  - R8 tag exists before the first edit: `git -C <demo> rev-parse -q --verify refs/tags/pre-repin` and `git -C <demo> ls-remote --tags origin pre-repin` are both non-empty, and the tag points at the demo's head before the re-pin commit. It is the first row of the sitting, before any edit and before `uv lock` (R1-ADV-10).
  - R9 kept snapshots are reachable: `git -C <core> cat-file -e <snapshot>^{commit}` for exactly these sets: apexc {`153d217`}, dealdesk {`153d217`, `cd62212`}, intake {} (T8's `ce70eb5` leaves with its copy), refunds {}. Under PENDING LEAD 9 option (b), intake's set is still {}, because its copies are re-read at `core_commit` = `<FINAL>` with no snapshot. A plain-git killer for M7.
  - R10 mutant targets hold: for each demo's mutant list, every target path exists and every search string occurs exactly once in its target (one printed count per mutant). Then one full mutation run of the demo's list, with its recorded verdicts. This closes "R6 does not run mutants".
  - R11 expiry: a short stdlib `python -I` check that every `allowed_local.expires` is later than the run date, with a non-zero exit otherwise (a plain killer for M8).
  - R12 pin-only failures are closed (R1-ADV-9). The fail-before's pin-only run lists the failing tests per demo. Every entry on that list must be closed by a named diff hunk or by a row of this ticket, and the closing is recorded entry by entry.
  - R13 look-alike before/after (R1-ADV-6). At fail-before, with the copies still present, one script per demo runs that demo's own look-alike fixtures through the OLD copy and saves the verdicts as JSON. The fixtures are: apexc `tests/fixtures/textnorm_vectors.json` and its `fold_key` pairs; refunds' approval look-alike cases; dealdesk's `allow_equal` recipient cases; intake's `fold_text` cases. After the swap, the same script runs on core at `<FINAL>`.
    - Pass rule (the same in each direction, never weaker): every pair that was equal (or `LOOKALIKE`) before is still equal (or `LOOKALIKE`) after.
    - A pair that splits means a look-alike check got weaker, and that demo is blocked.
    - A pair that newly joins is listed for the adversarial reader (it can refuse a real user) but does not block.
  - **Fail-before (run first, with the core checkout at `<FINAL>` and before any edit):**
    - R1 fails on every demo, because the pins are `6608146`.
    - R7 prints its lines (on the snapshots, the 16 above; the live count goes in the evidence).
    - The R13 "before" JSON is saved.
    - The pin-only run (only the pin moved, copies untouched) gives R12's list.
    - R4 with `--core-ref <FINAL>` is expected to flag the T1-T3 copies whose core file now exists on main (tool rule `remove_copy_after_pin`, named in `dealdesk/core_copies.json:2`). This is informational: its output is pasted, not asserted.
  - Hostile inputs, race tests, contract suite: none (no core code, no shared state). R13 is the hostile-input row for the look-alike checks.
- **Mutation plan (the lead plants each mutant in a throwaway clone of the demo, runs the killer, saves the output, and discards the clone; nothing is pushed). The first killer named is the required one; R4 is never required:**
  - M1 change one byte in a kept copy (apexc `stop_gate.py`) → apexc `test_v9.py::test_the_core_copies_match_the_pinned_core_files`; R4 second. It is an expected SURVIVOR of R5 (`check_core_copies.py` reads only the core side), and that survival is recorded as the evidence for A9 F9. M1 also takes over the job of the dropped apexc mutant "r9 parity: a core copy drifts" (`mutation_check.py:398`) on a kept copy.
  - M2 `core_commit` set to a commit that is not on core main (`748849c`) → R1b; R4 (`--strict-pin`) second.
  - M3 one demo left at `6608146` in `pyproject.toml` → R1.
  - M4 `pyproject.toml` moved, `uv.lock` not regenerated → R2.
  - M5 a deleted copy still listed under `files` → R3 (apexc, dealdesk and intake: the copy test opens the missing file; refunds: the rewritten `:280`, because `files` is not empty); R4 second.
  - M6 a copy deleted while a module still imports it → R7; R6 (import error) second.
  - M7 a kept copy's `pr_snapshot` changed to a commit that does not exist (apexc and dealdesk; intake and refunds keep no snapshot) → R9; R5 (`MISSING`, `apexc/tools/check_core_copies.py:27-30`, apexc only) and R4 second.
  - M8 one kept `allowed_local` entry given a past `expires` → R11; R4 second. intake's test only checks that the field is present (`intake-main/tests/test_review6.py:251-253`), so it is not a killer.
  - M9 the `pre-repin` tag not pushed → R8.
  - M10 the egress copy (T4) keeps its rewrite to the deleted demo fold → R7; R6 (import error) second.
  - M11 a look-alike check weakened (in the seam, `fold_key` replaced by `str.casefold`; for refunds, at `textnorm.py:98`) → R13 (a Cyrillic pair splits). New, for R1-ADV-6.
  - M12 one dropped fold mutant left in a mutant list (apexc `mutation_check.py:323`, target `src/apexc/textnorm.py`) → R10 (missing target path). New, for R1-ADV-3.
  - M13 `hadavin-sdk` left in the test group while `src` imports core (apexc) → R1c. R6 alone cannot kill this mutant, because the suite installs the test group. New, for R1-ADV-5.
  - M14 refunds seam alias renamed (`textnorm as core` instead of `as _core`) → R10 (`mutants_review12.py:35` search string count 0). New, for the seam rule.
- **Evidence commands and where saved:** the lead runs R0a-R13, the fail-before and M1-M14 per demo and saves the raw output in `handover/evidence/P8a/<demo>-<n>.md`. Each file is headed with the demo head before and after, and `<FINAL>`. The summary for plan section 9 row "Demos re-pinned" goes to `repin.md` (the plan's file name). Each demo pull request and the evidence list the 8 dropped mutants by name (PENDING LEAD 12), and for each one, the P1 mutant that covers the same behaviour, or "none". Exit codes are taken from the command itself, never from a `| tail` pipe. A blocked demo's file records the rule, the output and "P8a-<demo> blocked".
- **Reviewers:** one fresh `egm:*` reviewer (Tier B) reads the four demo diffs, this ticket and the evidence. In addition, one **mandatory** adversarial reader reads the look-alike diffs (refunds `approval.py`/`textnorm.py`, apexc `egress_text.py`, dealdesk `guards.py`, intake `textfold.py` and `test_review6.py`) together with the R13 output (R1-ADV-6; this closes revision 1's PENDING LEAD 1, which the lead may reverse).
- **Done =** done is judged per demo. A demo is done when R0a-R13 are green at its merged re-pin commit, M1-M14 are killed by their required killer (M1's survival of R5 recorded; any mutant that R0a shows R4 does not kill is recorded as "not killed by R4", with its plain killer still required), and its CI is green. P8a is done when all four demos are done. Then plan section 9 row "Demos re-pinned" is filled with the sync check (A7, A9 F9), not with the plan's `check_core_copies` command. Core gates (ruff, bandit, CodeQL, SonarCloud, CodeRabbit) do not apply, because there is no core diff.
- **Rollback:** each demo has the tag `pre-repin` (lead). To roll back, revert the demo's re-pin merge commit. That also restores the `hadavin-sdk` dependency group, which changes in the same commit. No data migration; core untouched. If a later core merge changes a copied core path, that package re-pins in the same package (plan section 10).

## PENDING LEAD (lead-only or owner-only; each with a recommendation unless it is a NEEDS LEAD item)
1. *Closed in revision 2:* the adversarial reader for the look-alike diffs is now part of the Reviewers line (R1-ADV-6). The lead may reverse this.
2. **Lead-only execution, all of P8a:** create and push `pre-repin` in four demo repositories; branch, edit, `uv lock`; run the suites and the sync check; open and merge four demo pull requests. None of this can be done by the cloud session (outside the repository; no demo clone here). Recommend: the lead does it after the last v1 merge, in one sitting, in the order refunds (smallest, 2 copies), intake, dealdesk, apexc (largest, 7 copies).
3. **Keep the snapshot branches.** The kept copies (T4-T6) point at `153d217` and `cd62212`, which live only on `core/promote-apexc-review8`, `handover-src/pr50-local-748849c` and `core/promote-refunds-r8`. Plan section 11 ends with deleting every branch except `main`. Recommend: before any of those branches is deleted, the lead creates archive tags on the two commits (`archive/pr50-153d217`, `archive/pr49-cd62212`); otherwise R9 fails and those copies become `MISSING`.
4. **apexc stop gate against core `Limits`:** the copy needs `source=` and `is_stopped()`, which v1 core does not have. Recommend: no change in P8a (the copy stays as it is and runs against apexc's fake). If apexc's suite shows that it is wired to a real core `Limits`, apexc is blocked (a demo adapter or the v1.1 stop gate row; the lead decides), and the other demos go on.
5. **Python version of each demo** vs core's single pinned Python (A9 F3). Recommend: each demo's CI runs the same Python as core; the lead checks it in R6 and writes it in the evidence.
6. **`allowed_local` expiry.** It is 2026-12-31 on every entry in the apexc, dealdesk, refunds and `intake-main` snapshots (for example `apexc/core_copies.json:76, 80`). The newer intake heads (`-6b`, `-a12`) use 2027-01-31 (counted by script; corrected from revision 1, which said 2026-12-31 for all four). If P8a runs after the date, R11 and the sync check fail. Recommend: entries that stay get a new date and a one-line reason in the re-pin pull request.
7. **Portal kit pin:** `promotion-inputs/portal-kit/pyproject.toml:11` also pins `hadavin-sdk` at `6608146`. The kit is not one of A7's four demos. Recommend: bump it in the same sitting as the optional fifth change set (pin only, no copies; it uses `stats.upper_error_bound`), or leave it to its own trigger. Coupling: intake-a12 holds a kit copy (`core_copy/strict_json.py` under `allowed_local`) and its CI checks out the kit at a pinned commit, so bumping the kit can touch intake's CI. Jagrat: no pin found in `handover/` (UNVERIFIED).
8. **Plan text:** plan row P8a (plan-v3 line 112) and section 9 row "Demos re-pinned" (line 186) still say "copy `check_core_copies`" and name `python tools/check_core_copies.py`; A7 and A9 F9 replace them. Recommend: P8b updates the plan table.
9. **NEEDS LEAD 35 (not chosen here): intake's "stdlib only" rule vs a run-time core import.** intake-a12 `tests/test_dependencies_empty.py:15-16` asserts `[project].dependencies == []`; its docstring (`:1-2`) says the package "stays stdlib only after every work package". After T1, `textfold.py` imports `hadavin_sdk`, so the placement rule puts `hadavin-sdk` in `dependencies`, which breaks that test. This holds in the `intake-a12` snapshot; it is UNVERIFIED on the live head. Both options, with what changes under each:
   - (a) **Take the dependency.** Apply T1 and T2 to intake. `test_dependencies_empty.py:15-16` is rewritten to assert that `dependencies` is exactly one entry, `hadavin-sdk` at `<FINAL>`. That is a rewrite, not a deletion, and the reason is one line in intake's pull request. The intake rows of the import-site table, intake-main `test_review6.py:257`, R1c "dependencies" and R13 apply.
   - (b) **Keep intake's fold as a byte copy.** T1 and T2 do not apply to intake. Its two fold copies are re-copied from core at `<FINAL>` (no snapshot), and `textfold.py`, `test_invoicecheck.py:1226` and `test_review6.py:257` stay as they are. R1c puts `hadavin-sdk` in the test group. The consequences: a second fold stays in intake, and R4's `remove_copy_after_pin` rule will flag the copies, so they need an `allowed_local`-style reason or a recorded R4 failure (to be confirmed by R0a). M5 and M6 do not apply to intake, and R13 for intake compares the old copy with the re-copied one.
   - Under either option, intake's R9 set is {}. The resolve's recommendation and its reason are in `reviews/P8a-round1-resolve.md` (PENDING LEAD 9). This ticket does not choose.
10. **NEEDS LEAD 35 (not chosen here): which intake head P8a re-pins, and row T8.** Six intake snapshots differ (resolve F5): `intake-main` has 3 copies; `-6b`, `-6d` and `-wp3` have the same 3 plus `core_copy/strict_json.py` under `allowed_local`; `-a12` and `-p2` have 4 copies, the fourth being `core_copy/redact.py` (PR 42, snapshot `ce70eb5`). Both options:
    - (a) **The head carries `core_copy/redact.py`.** Apply T8: the intake copy count becomes 4 before and 1 (`safe_text`) after, or 3 under item 9(b). intake-main `test_review6.py:271-281` gains the `coreredact.py` exemption. R7 gains `core_copy[./]+redact|core_copy import redact` for intake. R13 does not cover T8, because redaction is not a look-alike decision. R6 must still pass, and the redaction change it brings comes from P2d's frozen `guard/redact.py`. This also couples P8a to P2d.
    - (b) **The head does not carry it.** No T8. intake's count is 3 before and 1 (`safe_text`) after, or 3 under item 9(b).
    - Either way, R0a records the live head's `files` keys, and the evidence restates intake's counts and its R9 set. This ticket does not choose.
11. **Order 21 item 17 for P8a** (INFORM 36; following the resolve's recommendation): the freeze and one build-start review (one fresh reviewer pair on the frozen text) come before the lead's sitting, as for every package. Order 6(c) still holds: the cloud does no demo work.
12. **Dropping the demo mutants aimed at copied core code** (INFORM 36; following the resolve's recommendation, with its count corrected). The count is **8, not 9**. apexc has 7: 6 on `src/apexc/textnorm.py` and 1 on `src/apexc/_confusables.py`. The resolve's `grep -o` counted 8 for apexc because the mutant at `mutation_check.py:398` names its target path twice. dealdesk has 1. They are dropped, not retargeted: after the re-pin their target is installed core code, outside the demo tree. apexc's own recipe step 6 allows "drop". By name:
    - apexc `mutation_check.py:279` "M5: zero-width characters are not dropped from a summary";
    - `:323` "M6: look-alike letters are not folded";
    - `:324` "M6: combining marks are not dropped";
    - `:325` "M6: O/0 and I/l/1 are not folded for protected values";
    - `:346` "M3: uppercase Cyrillic S, I, J and Y are not folded" (`_confusables.py`);
    - `:374` "r9 M1: S B Z G Q are not mapped for protected values";
    - `:398` "r9 parity: a core copy drifts" (its job moves to M1);
    - dealdesk `mutation/mutation_check.py:959-960` "core copy: textnorm fold drops the digit table".

    Whether P1's own mutants cover each of these behaviours one by one is UNVERIFIED. The evidence maps each to a P1 mutant or writes "none", and every "none" goes to the v1.1 row below. refunds' mutants (`mutants_review12.py:5, 35`) target refunds' own seam, not a copy, and stay. intake's `tools/mutate_src.py` has no target in a copy.

## v1.1 rows (nothing dropped silently)
| Item | Trigger |
|---|---|
| Fix the per-demo `check_core_copies.py` to hash the demo's own copy (undo the rewrite), so it catches what the copy test catches | a demo's CI needs a standalone check without the studio tool |
| Second re-pin of apexc and dealdesk when P2b (egress text), the v1.1 stop gate / row store / config view rows, or P3b (signed approvals) merge | that package's merge (plan section 10) |
| Re-add a demo mutant of core fold code for each of the 8 dropped mutants that the evidence maps to "none" in P1's list (cut 1) | a dropped mutant maps to "none", or a P1 fold mutant is removed |
| An audit of the wider core API each demo uses (`Limits`, `Config`, `AuditEvent`, `stats`, the store), beyond the names in the import-site table (cut 2) | R0b finds a runtime `hadavin_sdk` import outside the table on any demo |

## CHANGELOG (revision 1 → revision 2; one line per resolve decision)
| Resolve id | Decision | Change in revision 2 |
|---|---|---|
| R1-ADV-1 (Major) | PROPOSE FIX | The rule "no test deleted; rewrite to assert the subject is gone". The rewrites of refunds `test_review11.py:280` and `:296` are written out (with the needles at `:302-313`). refunds keeps `"files": {}`. Required killer for M5 in refunds = the rewritten `:280`. M1 is apexc-only. |
| R1-ADV-2 (Major) | PROPOSE FIX, partly contested | New row R0b (import inventory plus a stop rule; fix = a demo adapter). dealdesk `guards.py` and `tests/test_nameindex.py` added to the import-site table. The stale "dealdesk/intake seams UNVERIFIED" sentences deleted. Broad API audit CUT (v1.1 row). |
| R1-ADV-3 (Major) | PROPOSE FIX + CUT, partly contested | T3 names `mutation_check.py:29-30, 483, 486`. New row R0c (judge signature). New row R10 (mutant targets plus one full mutation run). Fold mutants dropped by name (PENDING LEAD 12; count corrected to 8). `mutant_kills.json`, `acceptance.md`, `README.md` added. intake's `mutate_src.py` stated as not affected. |
| R1-ADV-4 (Major) | PROPOSE FIX | New row R0a (read and baseline the tool). Done no longer rests on R4. Plain killers: M2 → R1b, M5 → R3, M7 → R9, M8 → R11 (new); R4 is second for each. The fail-before R4 output is informational. |
| R1-ADV-5 (Major) | PROPOSE FIX | T7 stop rule (no re-copy). R9 exact sets per demo. Start rule: a T1-T3 path missing at `<FINAL>` means P8a does not start. Dependency placement rule plus new row R1c (and M13). intake's conflict → PENDING LEAD 9. |
| R1-ADV-6 (Major) | PROPOSE FIX | New row R13 (the same pass rule before and after) and M11. dealdesk `guards.py:84-89` and intake `test_review6.py:285` added to the look-alike list. The adversarial reader made mandatory; old PENDING LEAD 1 closed. |
| R1-COR-1 (Major) | PROPOSE FIX | Interface lists the 7 public names plus `_confusables` and `testing.mutation`. The import-site table re-read site by site (snapshot named on each). intake `test_invoicecheck.py:1226` added. Line-87-style UNVERIFIED text removed. |
| R1-COR-2 (Major) | PROPOSE FIX (reviewers' R7 fix corrected) | Tests that must change: apexc `test_v9.py:220` and `:347`, dealdesk `test_nameindex.py:55`, intake `test_invoicecheck.py:1226`. R7 rewritten as "must print nothing", without banning `core_copy` (dealdesk keeps two). **Further corrected in revision 2** after a run on the snapshots: `core_copy import \(` added (refunds' two-line import was missed), and the bare `mutation_judge` narrowed to `(from|import) mutation_judge` (it matched intake's own test name). |
| R1-ADV-7 | PROPOSE FIX | Closed by the R7 rewrite. |
| R1-ADV-8, R1-COR-6 | PROPOSE FIX | Depends-on gives the full id list from plan-v3 line 48. Orders 21 item 17 and 6(c) cited together. "No S0 EXIT build lane" sentence deleted. |
| R1-ADV-9 | PROPOSE FIX | New row R12: the pin-only failing list, closed entry by entry. |
| R1-ADV-10 | PROPOSE FIX | Sitting order puts R8 first, before any edit and `uv lock`. Rollback restores the dependency group. |
| R1-ADV-11 | PROPOSE FIX | "Blocked demo" defined; the other demos proceed; Done per demo; P8b waits. |
| R1-ADV-12, R1-COR-9 | PROPOSE FIX | The 13 named (apexc 7, dealdesk 4, refunds 2 in `promotion-inputs/<demo>/`); intake bytes in `-a12`/`-6b`; snapshot named on each intake cite. |
| R1-ADV-13 | PROPOSE FIX | One count: "4 demo change sets, plus an optional fifth". |
| R1-COR-3 | PROPOSE FIX | `fakes.py:760, 770` reach `squeeze` "indirectly, through `normalise.py:9`". |
| R1-COR-4 | PROPOSE FIX | dealdesk keeps `TEMPORARY` (`:268`). intake's top-level `core_pr` 50 goes, and the test is rewritten. The cite is `:257` (the resolve wrote `:256`; re-read: `:257`). refunds' top-level `core_pr` 50 goes too (same rule). |
| R1-COR-5 | PROPOSE FIX | Closed in R1-ADV-3. |
| R1-COR-7 | CONTEST (wording fix) | R4 shows four `--demo` flags in one call; R0a confirms. |
| R1-COR-8 | PROPOSE FIX | The review-gates paragraph separates the ticket review (order 20 item 6) from the demo-diff review (order 6(b)). |
| R1-COR-10, R1-COR-11 | DECLINE | No change. |
| Cut 1 | surface cut | The fold mutants are dropped, not retargeted (count 8; v1.1 row). |
| Cut 2 | surface cut | Broad core-API audit removed (R0b plus a stop rule instead; v1.1 row). |
| Cut 3 | surface cut | Done no longer rests on the unread sync tool. |
| PL9 (new) | NEEDS LEAD 35 | Both options written out with their row changes; not chosen. |
| PL10 (new) | NEEDS LEAD 35 | Both options written out (T8 conditional); not chosen. |
| PL11 (new) | INFORM 36, recommendation followed | Freeze plus a build-start review before the sitting. |
| PL12 (new) | INFORM 36, recommendation followed | Mutants dropped by name; count corrected 9 → 8, with the reason. |
| Author re-check (not in the resolve) | correction | `allowed_local` dates: the newer intake heads use 2027-01-31 (PENDING LEAD 6). The T7 and T8 hashes re-run at `4ec3616`. apexc `test_v9.py:343` and `test_v11.py:263` found and shown to still hold. intake-a12 `test_invoicecheck.py:1229-1230` exact-set assertion added to R12. |

## Counts (by script, `python3 -I` over this file)
Counted by regex over this file: 17 template fields (16 "**name:**" bullets plus "**Done =**"); **18 pass-criterion rows** (R0a, R0b, R0c, R1, R1b, R1c, R2-R13), up from 9 in revision 1; **14 mutants** (M1-M14, each with a named required killer), up from 10; 8 file-table rows (T1-T8, T8 conditional); 11 import-site rows; 12 PENDING LEAD items (9 and 10 are NEEDS LEAD 35); 4 v1.1 rows; 28 CHANGELOG rows.
Copies before and after (counted by script from each snapshot's `core_copies.json`; intake under PENDING LEAD 9 option (a) / (b)): apexc 7 to 4; dealdesk 4 to 2; refunds 2 to 0; intake-main 3 to 1 / 3; intake-a12 (with T8) 4 to 1 / 3. Total on `intake-main`: 16 to 7 / 9. Dropped demo mutants: 8 (apexc 7, dealdesk 1). R7 fail-before lines on the snapshots: 16.

## UNVERIFIED
- The demo repositories themselves: only partial copies are in `handover/`, and which snapshot matches each live head is unknown (intake most of all; PENDING LEAD 10). Each demo's `pyproject.toml`, `uv.lock`, full test command, Python version and CI file.
- The sync check: its exact output, flags and rules (memo-6 C describes it, and the memo's author did not run it either; R0a settles it). A9 F9's S0 run "result in s0-report.md" has no file in `handover/`.
- `uv lock --check` in the lead's uv.
- Whether P1m's edits leave `judge` and `Verdict` with the same signature (R0c settles it).
- Whether P1's mutants cover each of the 8 dropped demo mutants (the evidence maps them).
- Which demo tests change value after the fold swap (R12 and R13 settle it).
- Whether any demo stores fold output; whether apexc wires a real core `Limits`.
- The "on main at FINAL" column (the start rule settles it).
- The exact refunds, dealdesk and intake look-alike fixture names R13 runs (I named the decision sites; the fixtures are picked by the lead from each demo's tests).
- Jagrat's pin.

## Sources
- plan-v3: line 48 (v1 rows), line 112 (row P8a), line 186 (section 9 row), line 193 (rollback), sections 9-11, rule 9(b).
- Amendments A7, A9 F3, A9 F9, A12.
- LEAD-ORDERS: 2, 6(b), 6(c), 8 (cut surface), 20 items 4-6, 21 item 17.
- memo-6 section C (`studio-notes/memos/memo-6-kernel-and-claims.md:38`).
- `tickets/P1.md` lines 42, 44, 72-74, 236; `tickets/P2a.md` lines 42, 84, 418-419.
- `reviews/P8a-round1-resolve.md` (facts F1-F8, decisions, PENDING LEAD 9-12); `reviews/P8a-round1-adversarial.md`; `reviews/P8a-round1-correctness.md`.
- The files under `handover/promotion-inputs/` cited above (apexc, dealdesk, refunds, intake-main, intake-6b, intake-a12, intake-p2, portal-kit).
- Orders 14 and 15 (look-alike wording for secrets) do not apply to this package.
