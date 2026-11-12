# EV-PRHb6 results: PR H (strip hidden controls) head c802cc0f4c5dc7e0ae7130f004b2460ce862c869

EVIDENCE RUNNER: results are recorded, not judged, nothing was fixed. Run 2026-11-12 04:12 to about 04:45 UTC (09:42 to 10:15 IST). Raw logs: /home/user/build/evidence-raw/PRHb6-c802cc0f/ (outside the repository); small raw excerpts in this folder.
Head confirmed in my own detached worktree: `git rev-parse HEAD` = c802cc0f4c5dc7e0ae7130f004b2460ce862c869, `git status --short` empty. `git diff --name-only 931d7396 c802cc0f` = only `handover/evidence/PRH/b6-checkpoint.md` and `handover/evidence/PRH/b6/NOTES.md` (notes only, confirmed). origin/main = 2a8c2aac. I did not read the builder notes. The main checkout is on another branch; I did not use it.

## Failed, not run, or different (first)

| # | What | Result |
|---|---|---|
| F1 | Full suite, first run, own Postgres 16.15 | exit 1: 1 failed, 12962 passed, 1 skipped, 62 deselected (12964 tests in the junit XML: failures 1, errors 0, skipped 1), 341.7 s. The one failure: `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`: the database server opens a connection on the fixed socket `/var/run/postgresql/.s.PGSQL.5432`, which my server (own socket dir) does not have. The same file on clean origin/main with the same server: 1 failed, 252 passed (same test). Re-run with my own server in a private mount namespace (own /tmp, own /var/run/postgresql, script `ns-run.sh`): head 253 passed (exit 0), origin/main 253 passed (exit 0). |
| F2 | Skip | `tests/contracts/test_llm.py:95` (`test_a_malformed_answer_is_a_provider_error[bedrock]`): "Stubber refuses a malformed Converse shape before the kind sees it" |
| F3 | Probe rows with a readable secret piece on the head | see section (6) and items 9 to 11 below |
| F4 | Items 9 and 11 raise `InputTooLarge` out of `tools.prepare_output` on small fuzz input (7 of 3000 texts, head and 3db0d34d; 0 on origin/main) | section (7), fuzz |
| F5 | Cost compare: H rows ratio to main 2.74 to 4.40 at 262,144 characters | section (7) |
| F6 | Not run | mutant runner as user `nobody` (the earlier evidence folders do not mention it, so not repeated); Python 3.12 full suite; CI steps outside the redaction package (Semgrep, zizmor, Trivy, pip-audit); the timing test `test_the_timing_harness_flags_a_quadratic_stand_in` 3x3 runs (item 9 of the common brief; this brief did not list it) |
| F7 | bandit first via `uv run --no-sync bandit` is not installed in the venv; ran `uv run --no-sync --with bandit bandit -q -r src demos tools -ll` | exit 0 |

## Results table

| Item | Command (cloud variables unset, own venvs, `uv sync --locked --all-extras --group test`, exit 0 for all 4 venvs) | Exit | Last line |
|---|---|---|---|
| (1) files vs origin/main | `git diff --name-only origin/main...c802cc0f` | 0 | 32 files (`files-vs-main.txt`) |
| (1) files vs 3db0d34d | `git diff --name-only 3db0d34d c802cc0f` | 0 | 13 files (`files-vs-3db0.txt`): CHANGELOG.md, 2 handover notes, src/hadavin_sdk/{defaults.py, guard/hidden.py, guard/redact.py, guard/runmap.py, scrub_settings.py, tools.py}, tests/{prh_mutants.py, test_prh_regressions.py, test_prh_steps.py, test_prh_tools.py} |
| (2) ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| (2) ruff format | `ruff format --check src tests demos tools` | 0 | 333 files already formatted |
| (2) bandit | `bandit -q -r src demos tools -ll` | 0 | only the warning "nosec encountered (B102), but no failed test on file src/hadavin_sdk/tools.py:389" (twice) |
| (2) scan | `python tools/scan_repo.py` | 0 | no output |
| (2) stage mutants | `python tests/stage_mutants.py` | 0 | 37 of 37 good; problems: [] |
| (3) PR H mutants | `heavy.sh python tests/prh_mutants.py` (own worktree) | 0 | **81 of 81 good; problems: []**; 81 lines "ok  KILLED", no survivor, `git status` of that worktree clean afterwards |
| (4) full suite | `heavy.sh uv run --no-sync pytest -p no:cacheprovider -q -m "not live and not perf" -rfEs --junitxml=full.xml`, HADAVIN_REQUIRE_PINNED_UNIDATA=1 | 1 | 1 failed, 12962 passed, 1 skipped, 62 deselected (F1, F2) |
| (4) failing file on origin/main | same file alone, same server | 1 | 1 failed, 252 passed (same dblink-connect test) |
| (4) failing file, private socket namespace | head / origin/main | 0 / 0 | 253 passed / 253 passed |
| (5) fail-before vs 3db0d34d src | head's changed tests (test_prh_regressions.py, test_prh_steps.py, test_prh_tools.py, tests/prh_mutants.py, which the regression test imports) copied onto a clean worktree of 3db0d34d; `pytest -rA` on those 3 files; imported tree printed: `.../wt-old/src/hadavin_sdk/...` | 1 | 27 failed, 2085 passed (list `fb3db0b-failed.txt`) |
| (5) fail-before vs origin/main src | all 20 changed test and fixture files of the diff copied onto a clean worktree of origin/main; `pytest -rA --continue-on-collection-errors -m "not live and not perf"` on the 14 test files | 1 | 286 failed, 212 passed, 34 deselected, 2 errors (tests/test_prh_hidden_unit.py and tests/test_prh_tools.py fail at collection on main) |
| (8) gitleaks git | `gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..c802cc0f"` | 0 | no leaks found |
| (8) gitleaks dir | `gitleaks dir --no-banner --redact --config .gitleaks.toml` on this folder | 0 after one edit | first run exit 1 (2 generic-api-key hits on one made-up capital-hex row in probe_hostile-wt-main.txt); I replaced the output column of the three probe_hostile files by `<omitted>`, re-run exit 0 |

### (5) fail-before detail (lists, no judgment)
- vs 3db0d34d: 27 failed. 15 new test functions added by the head over 3db0d34d (`+def test_` in the three test files): 14 of them have at least one failing row on the old src; `test_b6_scrub_without_a_find_or_a_changed_reading_is_still_the_text_as_written` passes on old src; rows `[single]` and `[two_plain]` of `test_b6_h1_every_copy_is_masked_or_nothing_is_shown` pass on old src. Two older tests also fail on old src with the new runner file: `test_every_prh_mutant_still_applies` (before my second overlay it failed with 71 >= 81 because I had not copied `tests/prh_mutants.py`; first run 27 failed too, `failbefore-3db0.log`) and `test_pass_bound_holds_for_a_seeded_search` (`AssertionError: 13`). First failing lines are in `fb3db0b-first-lines.txt` of the raw folder.
- vs origin/main: 212 passed on main src (`fbmain-passed.txt`): test_k5_fixes3 8, test_prh_clean_corpus 61, test_prh_contract 18, test_prh_grounding 13, test_prh_regressions 95, test_prh_spans 13, test_prh_steps 1, test_prh_wiring 3.

## (6) Probes of the previous evidence, re-run on the head, 3db0d34d and origin/main
Scripts `probe_b5.py`, `probe_h.py` (copied unchanged from handover/evidence/PRH/3db0d34d), raw: `probe_b5-wt*.txt`, `probe_h-wt*.txt` (wt = head, wt-old = 3db0d34d). "yes" = a named piece of the secret stands in the output. The handed-out list exists only on the tool and error paths; untrusted and head (`safe_head`) are given none, so a handed-out value reads yes there on all trees.

| Probe | 3db0d34d (untrusted/tool/error/head) | head c802cc0f |
|---|---|---|
| H1a `x HAND y ESC+HAND`, piece HAND[1:] | y/y/y/y | y/**n/n**/y |
| H1b plain + copy cut by ESC(B ESC[m, pieces HAND[9:], HAND[:9]| y/y/y/y | y/n/n/y |
| H2 `log ESC+HAND[:11]+TRUNCATED`, piece HAND[1:11] | y/y/y/y | y/n/n/y |
| H3 key cut by ESC+letter, `user BEL IP` (map holds IP) | n/n/n/n, output `id <APIKEY_1> user <IPV4_1>` | n/n/n/n |
| L1 to L5, L7 to L11, M2a/b, G1 to G3 (probe_b5) | n on all four paths | n on all four paths (no row with a key or password readable on the head) |
| L6 / L12 (handed out) | tool and error n; untrusted and head y (no list) | same |
| d3 (direct `redact()`, key cut by ESC ( B ESC [ m) | `id AKIA(B IOSFODNN7EXAMPLE` (key tail readable) | masked `id <APIKEY_1>` |
| d11 (seeded value, ESC before it, direct `redact()`) | tail readable | withheld note `(details withheld)`, 0 readable |
| d6 (key + U+0301, not a hidden item) | readable | readable `id AKIÁIOSFODNN7EXAMPLE` |
| control: key cut by a tab | readable | readable |

### My own hostile rows (script `probe_hostile.py`, raw `probe_hostile-wt*.txt`)
Cell: R = an 8-character window of the secret stands in the output; sq = readable only after removing spaces and controls; - = none. Columns: untrusted / tool / error / head / direct `redact()`. Secrets: the allowed example key, a made-up 32-character capital-hex value under `ENCRYPTION_KEY=`, a made-up handed-out value (list given on tool and error only).

| Row | origin/main | 3db0d34d | head c802cc0f |
|---|---|---|---|
| X1 capital hex under ENCRYPTION_KEY= | -/-/-/-/- | -/-/-/-/- | -/-/-/-/- |
| X2 capital hex cut by U+200B | -/-/-/-/R | -/-/-/-/R | -/-/-/-/R |
| X3 capital hex cut by U+202E and U+2066+U+2069 | -/-/-/-/R | -/-/-/-/R | -/-/-/-/R |
| X4 hex cut by ZW, bidi, ESC[0m, BEL | R/R/R/R/R | -/-/-/-/R | -/-/-/-/R |
| X5 key, 2 copies (plain + ZW cut) | -/-/-/-/R | same | same |
| X6 key, 3 copies (plain, ZW, ESC[0m) | R/R/R/R/R | -/-/-/-/R | -/-/-/-/R |
| X7 key, 3 copies each cut (ZW, RLO, BOM) | -/-/-/-/R | same | same |
| X8 key spaced out `A K I A ...` | sq/sq/sq/sq/sq | same | same (output shows the spaced characters unchanged) |
| X9 key spaced out with ZW between | sq on all | same | same (ZW left in output) |
| X10 key spaced + a copy cut by ESC[m | R/R/R/R/R | -/-/-/-/- | -/-/-/-/- |
| X11 handed-out value, 3 copies (plain, ESC-prefix, ESC(B ESC[m cut) | R/R/R/R/R | R/R/R/R/R | R/**-/-**/R/R |
| X12 handed-out value cut by ZW and by RLO | R/-/-/R/R | same | same |
| X13 handed-out value spaced out | sq on all | same | same |
| X14 mixed: 2 handed-out copies, 2 key copies, hex cut by ZW+ESC[0m | R/R/R/R/R | R/-/-/R/R | R/-/-/R/R |
| X15 handed-out value cut by ZW at the end + TRUNCATED | R/-/-/R/R | same | same |

Direct `redact()` (the last cell of each row) does not remove ZW or bidi characters on 3db0d34d or on the head: output for X2 on the head is `ENCRYPTION_KEY=9F3AC7B2E1D04<U+200B>A6B55C8F0123D7E9A4B` (two readable halves). Same on 3db0d34d. The untrusted, tool, error and head paths do not show those rows readable except X8, X9, X13 (spaced-out characters) and the untrusted/head columns for handed-out values.

## (7) Cost compare (run alone: all three slot locks held; queued 04:16:32, started 04:23:39, done 04:24:45 UTC)
`python tests/test_prh_perf.py --compare-main <clean origin/main worktree>`, exit 0, raw `cost.log`. Median CPU seconds, five alternating runs (as the tool does):

| Row (262,144 characters) | head | main | ratio |
|---|---|---|---|
| S1 plain ASCII log | 0.392 | 0.391 | 1.00 |
| S2 tab table | 0.400 | 0.403 | 0.99 |
| S3 JSON lines | 0.392 | 0.394 | 0.99 |
| S4 Hindi | 0.782 | 0.802 | 0.97 |
| S5 Persian ZWNJ emoji | 1.417 | 1.363 | 1.04 |
| H1 coloured output | 0.652 | 0.238 | 2.74 |
| H2 colour inside a word | 1.044 | 0.318 | 3.28 |
| H3 sgr0 inside a word | 1.734 | 0.394 | 4.40 |
| H4 colourised log with sgr0 | 1.005 | 0.304 | 3.30 |

The tool prints only these 262,144-character rows (no 65,536 row, no W row, no pass counts).
Withheld share of hostile fuzz output (own script `fuzz_withheld.py`, fixed seed 20261112, 3000 random texts of 2 to 8 pieces of words, handed-out value, key, cut variants, escape and zero-width and bidi items, spelled-out escapes `%1b`, `&#27;`, `\u001b`; `tools.prepare_output(t, {}, 4000, [HAND])`; "withheld" = output only the marker, the truncated note, or a "withheld" note):

| Tree | withheld | readable secret window (8 chars) in output | exceptions out of prepare_output |
|---|---|---|---|
| origin/main | 47 of 3000 (1.6 %) | 1408 | 0 |
| 3db0d34d | 124 of 3000 (4.1 %) | 704 | `InputTooLarge` 7 |
| head c802cc0f | 226 of 3000 (7.5 %) | 548 | `InputTooLarge` 7 |

First text that raises `InputTooLarge` on head and 3db0d34d (about 130 characters): `Qx7m<ESC>Lp-9vRtzKw2 AKIAIOSFODNN%1b7EXAMPLE Qx7mLp-9vRtzKw2 AKIAIOSFODNN7EXAMPLE AK\u001bIAIOSFODNN7EXAMPLE AKIAIOSFODNN7EXAMPLE Qx7mLp-9vRtzKw2 <BEL>` (raw in `fuzz-wt.txt`). Of the 548 head outputs with a readable window, the input held a spelled-out escape (`%1b`, `&#27;` or `\u001b`) in 322 and none in 226 (the 226 include a key cut by ESC ( B inside a longer text, example: out `... A(BKIAIOSFODNN7EXAMPLE`, window `KIAIOSFO` readable); examples in `fuzz-wt.txt`.

## Items 9 to 11 (lead addition: probes F1, F2, F3). Script `probe_lead.py`, raw `probe_lead-wt.txt` (head), `probe_lead-wt-old.txt` (3db0d34d), `probe_lead-wt-main.txt` (origin/main)
Paths: tool = `tools.prepare_output(t, {}, 4000, [HAND])`; error = `tools.error_reason(ValueError(t), [HAND])`; choke = `runmap.redact_untrusted(t, {})` (the choke point; it takes no handed-out list); head = `runmap.safe_head(t, 4000, {})`. Readable = HAND whole or HAND without its first letter in the output; "dec" = after one decode step of the output (percent, entity or JSON) HAND or HAND[1:] shows.

### Item 9 (F1): handed-out secret `Tr0ub4dor-3xyzQ` (made-up, built from parts)
| Spelling in the text | Path | origin/main output | 3db0d34d output | head output |
|---|---|---|---|---|
| `x %1b%54r0ub4dor%2d3xyzQ y` | tool | `x <ESC><SECRET_REDACTED> y` (n) | `x %1b%54r0ub4dor%2d3xyzQ y` (HAND n, HAND[1:] n, one-step percent decode: **yes**) | same as 3db0d34d (**yes** after one percent decode) |
| same | error | `ValueError: x <ESC><SECRET_REDACTED> y` (n) | `ValueError: x %1b%54r0ub4dor%2d3xyzQ y`, decode yes | same, decode yes |
| same | choke, head | text as written (decode yes) | text as written (decode yes) | text as written (decode yes) |
| same with lower-case-first secret `tr0ub4dor-3xyzQ` (`%1b%74r0ub4dor%2d3xyzQ`) | tool, error | `x <ESC><SECRET_REDACTED> y` (n) | `x <SECRET_REDACTED> y` (n) | `x <SECRET_REDACTED> y` (n) |
| `x \u001bTr0ub4dor-3xyzQ y` (JSON escape text, a backslash and u001b as characters) | tool, error | `x \u001b<SECRET_REDACTED> y` | same | same |
| same | choke, head | HAND readable (Y) | Y | Y |
| `x &#27;&#84;r0ub4dor&#45;3xyzQ y` | tool, error | `x <SECRET_REDACTED> y` | same | same |
| same | choke, head | text as written (html decode yes) | same | same |
| `x <ESC>Tr0ub4dor-3xyzQ y` (raw ESC, for comparison) | tool, error | `x <ESC><SECRET_REDACTED> y` | `x <SECRET_REDACTED> y` | `x <SECRET_REDACTED> y` |
| same | choke, head | HAND[1:] readable (first letter removed) | same | same (`x r0ub4dor-3xyzQ y`) |
| plain | tool, error | masked | masked | masked |
| plain | choke, head | readable (no list) | readable | readable |

The full per-row, per-path lines are in the three raw files (each line: HAND, HAND[1:], decode flags, output text). Only the tool and error paths take a handed-out list; the choke and head rows show a handed-out value readable on every tree because they are given no list.

### Item 10 (F2): handed-out secret `ProdCompany2024!` (made-up), text with a colour code ESC[31m, the secret, the masked marker `<SECRET_REDACTED>` once, the word `Company` elsewhere, ESC[0m at the end
| Path | origin/main | 3db0d34d | head |
|---|---|---|---|
| tool | `err <SECRET_REDACTED> ok <SECRET_REDACTED> word Company elsewhere` (not MARKER+TRUNCATED) | same | **`<SECRET_REDACTED>\n[truncated]` (whole result is MARKER+TRUNCATED: True)** |
| error | `ValueError: err <SECRET_REDACTED> ok <SECRET_REDACTED> word Company elsewhere` | same | `ValueError: <SECRET_REDACTED>\n[truncated]` |
| choke, head | secret readable (no list) | same | same |
The variant without the masked marker in the text (F2b) gives the same on the head (tool: `<SECRET_REDACTED>\n[truncated]`, True). On 3db0d34d and origin/main the F2b tool output is `err <SECRET_REDACTED> word Company elsewhere` (not MARKER+TRUNCATED).

### Item 11 (F3): secret `SECRET_ab12cd` (made-up, contains SECRET in capitals), handed-out on tool and error
| Text | Path | origin/main | 3db0d34d | head |
|---|---|---|---|---|
| `x SECRET_ab12cd y ESC[0m z` | tool | `x <SECRET_REDACTED> y  z` | `x <SECRET_REDACTED> y  z` | `<SECRET_REDACTED>\n[truncated]` |
| same | error | `ValueError: x <SECRET_REDACTED> y  z` | same | `ValueError: <SECRET_REDACTED>\n[truncated]` |
| `x ESC SECRET_ab12cd y` | tool | `x <ESC><SECRET_REDACTED> y` | `x <SECRET_REDACTED> y` | `<SECRET_REDACTED>\n[truncated]` |
| `x SEC<ZW>RET_ab12cd y` | tool | `x <SECRET_REDACTED> y` | `x <SECRET_REDACTED> y` | `x <SECRET_REDACTED> y` |
| `x SECRET_ab12cd y<RLO> z` | tool | `x <SECRET_REDACTED> y<RLO> z` | `x <SECRET_REDACTED> y<RLO> z` | `x <SECRET_REDACTED> y<RLO> z` |
| no hidden item | tool | masked | masked | `x <SECRET_REDACTED> y` |
| any row | choke, head | readable or tail readable (no list); ESC-prefix row `x ECRET_ab12cd y` | same | same |
No secret piece stands in the tool or error output on the head in any F3 row.

## Environment and clean-up
Python 3.13.18; Postgres 16.15 (own cluster, port 56911, socket in my folder); machine shared with other sessions' heavy jobs (full suite and mutants ran through heavy.sh, wait about 0 minutes; cost job waited about 7 minutes for three free slots). Postgres, the private-namespace servers, worktrees and venvs are stopped and removed at the end (see last line of this file). Spend: none. Sub-agents: none.

Final line: Postgres (own cluster, and the two namespace servers) stopped; 4 temporary worktrees and 4 venvs removed; no process of mine left (`ps` check 0).
