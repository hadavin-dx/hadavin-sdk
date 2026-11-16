# fix-patchcopies11 (eleventh fixer pass, security path) for patch-copies README.md and DEAD-MAN-CHECK.md
Edited only those two files plus this report. .patch files untouched. Shell checked with `bash -n` only; the recipe itself was not run; no Postgres. Reviewer words were checked; none wrong (patch-id and catalog claims confirmed from the src tree and by experiment).

## Results: finding -> fixed / contested / needs lead
| Finding | Result |
|---|---|
| Reader 1 HOME / "no credential, writes only in temp folder" | fixed: function `E` (one place) sets HOME, XDG_*, UV_CACHE_DIR, UV_PYTHON_INSTALL_DIR under `$W`; used by gates, run, proof; the "Who runs" row reworded; new paragraph "Not a sandbox" (the code still reads any file the user can read; use a throwaway container/user); proxy/credential removal rule on lines 3/9. Clone/fetch/apply lines still use the user's git settings: stated. |
| Reader 2 patch integrity | fixed: three sha256 in a fenced `sha256sum`-form block and in a heredoc in setup; setup prints the three values and runs `sha256sum -c`; README says "recorded by the audit on 2026-11-16, lead to confirm". Hash check tested in isolation: both OK. |
| Reader 3 mktemp / unset W | fixed: mktemp checked; setup stops on empty/missing `$W` and on a `$W` inside a git work tree; `need_w` guard in gates, run, verdict, proof (blocks wrapped in functions so a pasted block cannot write to /). |
| Reader 4 evidence claims | fixed: "NOT YET RUN END TO END" in the short answer and the recipe heading; "eleventh pass"; report-file locations given (pass 1, 2-3, 4-7/9-11; no report for pass 8); "eighth pass" cites replaced by the round-10 check; first run called a test. |
| Reader 5 clause (e) | fixed: sorted names from `git apply --numstat` AND `git patch-id --stable` equality. Tested on a scratch repo from `git archive b4cce5b`: equal for both pairs; different after a one-line hand edit. Spaces-only edits are not caught: stated. |
| Reader 6 who is the lead / merge | needs lead: written as UNANSWERED (CLAUDE.md: cloud sessions never merge; preamble rule 9: lead merges; if lead is cloud, studio head merges). No answer invented. |
| Reader 7 watcher not watched | fixed (proposal, NOT RUN): new DMC section with heartbeat sent only on healthy exit, receiver outside the machine alarming after N minutes (options a/b/c, client chooses), job script with self-check of commands, D7 added (README row 8, numbering box, T2), rule 5, three negative tests (disable job, delete job, break alert). N=5 is an AUDIT PROPOSAL. |
| Reader 8 secret handling | fixed: block gated at top "do not run before storage answer"; S2 run last; S1 sets no password; `trap` removes the secret file when the window closes; job script uses `trap 'rm -rf "$D"' EXIT` for the pgpass file. |
| Reader 9 labels | fixed: DMC statements S1-S8; review ids written RV-C3 ... RV-D3 (35 renames in README, 4 in DMC); numbering box lists five schemes. |
| Code M1 catalog query (c) | fixed: `p.prorettype <> 'trigger'::regtype` added with the reason and extension caveat; new c2 lists every SECURITY DEFINER function (trigger functions too). Confirmed from `0002_audit_chain.sql:25` (trigger function, no SECURITY DEFINER) and `migrate.py:179` (only per-role REVOKE on table/sequence) at b4cce5b. Not run on a database. |
| Cites: DMC:49 :29 -> :30; DMC:153 :192 -> :193 | fixed (b4cce5b `migrate.py:193` confirmed). |
| Citation 3 bandit "one nosec warning" | fixed in both places: 9 warning lines (2 B608, 2 B102, 5 "Test in comment"). Source is the r10 report; raw bandit output not available to this pass. |
| Citation 4 "ninth pass" | fixed (eleventh). |
| Newest commit / sha256 | newest commit text now 80e9b09a7; `git diff --stat` of src tests .github vs working head 50d3820ed: empty for 80e9b09a7 and bbfbeee19. sha256 recomputed here: same three values as the r10 report. |
| Lead message: check_secrets FAIL (6 hits) | fixed: line 10 reworded (no user:password@host example), hashes only as `<64 hex>  <name>` lines. Raw: `PASS 0 hits in 2671 files`. |

## Facts re-read from raw outputs before use (scratchpad runs/*.log, proof logs)
base.log last line `2 failed, 9364 passed, 454 skipped, 26 deselected in 253.60s`, rc 1; patched.log `2 failed, 9394 passed ... 237.98s`, rc 1; proof `12 failed, 18 passed in 6.25s`, `13 failed, 19 passed in 0.55s`; new tests `30 passed`, `32 passed`; `Left contains 10 more items`. Added to README as the round-10 run, marked "not the eleventh-pass form of E". ruff counts 294/296 and bandit lines are from the report only (stated).
Also run: function `verdict` on the real r10 logs in scratch repos (gates.txt hand-written): (a)-(e) ok, ADDS NO NEW FAILURE; after a hand edit (e) FAILED, NOT PASSED. This tests the script, not the recipe.

## Verification (from handover/flows-audit)
bash -n: README 6 fenced blocks (hash list, setup, gates, run, verdict, proof) all ok; DMC job script and password block ok (SQL/output blocks are not shell).
check_refs: `PASS 5176 references`; check_names: `PASS 655 rows`; check_secrets: `PASS 0 hits in 2671 files`; `ruff format --check .`: `819 files already formatted`.

## New lines marked NOT RUN
README: setup (fingerprint heredoc, `need_w`, checks, `E`), `gates()`, `run()`, `verdict()` (only run on scratch data), `proof()`, `cp -R <uv cache> "$W/uv-cache"` suggestion. DMC: whole job script, `trap` + `shred` lines, S2 reorder, queries (c) and (c2), the three watcher negative tests, D7 proposal.

## Still open (needs lead / studio head)
Who holds the merge credential; D7 receiver and N; storage place of the scheduler secret (already UNANSWERED); first real run of the recipe on a throwaway machine (also measures download time with the isolated uv cache, UNVERIFIED).
