# C5 cold reader: contract.md, README.md, SECURITY.md, docs/*.md (not real-services.md, settings.md), load_tools/README.md

Tree: /home/user/build/rr6/tree-C5 (head 61ded9e + 2 patches + survivor tests). Started 12:32Z. Fixed nothing.
Every run used plain `unshare -n` + lo_up-q4g.py (loopback only), no `y` typed, no secrets, no live service.
Docs under /home/user/build/rr6/tree-C5 are the PATCHED versions (contract.md, docs/real-services.md, docs/settings.md are modified by the patches).

## What failed or is wrong (first)
| doc file:line | what it says | tried | result | unclear/wrong (why) |
|---|---|---|---|---|
| docs/tests.md:26 and scripts/crash_desk.py docstring line 3 | crash scene: `PYTHONPATH=src python scripts/crash_desk.py` (Windows: "set PYTHONPATH with ; between entries when two are needed (src;.)") | ran exactly that (run2, run4 logs) | FAILS: `RuntimeError: ... the folder demo_only is missing` (ModuleNotFoundError demo_only). The desk never starts; the next `feed.py` gets connection refused. | WRONG command. A script run by path puts scripts/ (not the repo root) on sys.path, so it needs `PYTHONPATH=src:.`. With `src:.` it works (run5): flag file `data/crash.flag` containing D2 -> "simulate crash", desk ends, restart answers the replay with 201 replayed, 1 email. (The sentence on `;` is only a Windows hint, the crash line itself omits `.`.) Same page, `python -m lead_desk.server` with `PYTHONPATH=src` works (run3) because `-m` adds the current folder. |
| README.md:96-98 (Try it) vs contract.md "Run commands" | `export PYTHONPATH=src` then start_all/feed | ran it (run1) | works only because start_all.sh re-exports `src:.` itself and feed.py needs no demo_only | Unclear to a reader: the README says `PYTHONPATH=src` is enough, contract.md says `src:.` for demo_only; the two pages disagree for `python -m demo_only.fakes_server` (README fallback line points to contract.md, fine). Low. |
| README.md Try it, line "python scripts/feed.py --source webhook --index 1 # ... duplicate" | second lead gets a receipt number | run1 printed `"receipt_id": 3` for the webhook request after a replay of receipt 1; `/counts` says received 2 | a reader expecting 2 sees 3. A replay uses up a receipt number (run11 with no replay shows 1,2,3,... in order). Not stated anywhere I read (grep gap/consecutive: nothing). Unclear. |
| docs/n8n-recipe.md:11 (and :40 area), scripts/n8n_api.py | `scripts/n8n_api.py import|activate|list` | `python scripts/n8n_api.py --help` | prints only "N8N_API_KEY_FILE must be the path of a one-line file with the n8n API key" (rc 0 on this wrapper); no usage text. n8n itself not started, so import/activate/list NOT run. | Unclear: no `--help`; usage is only in the file docstring. Low. |
| docs/n8n-recipe.md:74 (proof workflow) | the `result` expression "was checked only by running its text in node" | not run (needs n8n) | NOT RUN | Doc itself says so; listed so it is not read as a pass. |
| docs/tests.md:61, README.md ("about 20 minutes") | full run 2513 passed/3 skipped in 993 s; 2516 tests at commit 2ce1f98 | `pytest --collect-only -q` in tree-C5 | 3982 tests collected here (patched tree). Clean main 61ded9e (tree-B) collected 3776 with 2 collection errors (I did NOT investigate those errors; I ran collection there from tree-B with PYTHONPATH=src only). | The page names a commit, so it is not false, but a reader on main sees 3776-3982 tests, not 2516, and the "about 20 minutes" in README is older than that count. Stale figure, needs a date/count refresh or an explicit "older commit" sentence near README "Tests and more commands". |
| docs/hubspot-probe.md ("`--token-env NAME` ... anything else is refused without being printed") | refusal of a bad name | `--token-env 'a b' --plan` | `--plan` exits 0 and does NOT check the name (prints only the plan); with `--yes-spend-calls 7` it is refused ("must be the NAME ... not the token"). | Minor wording: the refusal happens only on the spend path, not on `--plan`. |

## What was tried and matched the docs (no finding)
| doc file:line | what it says | tried | result |
|---|---|---|---|
| README Try it (Linux block) | start, 2 feeds + other door, counts, outbox, reset | run1 | 201 new / 201 replayed:true / 200 duplicate; counts received 2 new 1 duplicate 1; outbox count 1; `/` and `/health` 404; `/ui/` 200; reset "reset done" rc 0 |
| README Try it note | `sh scripts/start_all.sh` refuses, exit 2 | run1 | "refused: run this script with bash", rc 2 (sh is dash here) |
| README reset exit codes 2,4,6 and RESET_STOP_WAIT_SECONDS rules | | run9 | 007/1000/abc -> 2; empty and 0 -> accepted; DB path outside ./data -> 2; something on port 8765 -> 4; pid file naming another program -> 6. Codes 3 and 5 not tried. |
| contract.md "Reply rows..." table | 404/405/400 bad_expected/400 bad_envelope/413/HEAD 404/OPTIONS 405/TRACE 501/raw garbage 400/403 forbidden_host/408 after 10 s | run8, run11 | all match, incl. 408 after 10.0 s |
| contract.md HTTP table | 201/200/202 shapes, D item, R item 409 not_actionable with hint, 404 on unknown id, bad_decision 400 | run11 | match |
| contract.md hook points, check_schema.py, named tests | ALL_HOOK_POINTS, MORE_HOOK_POINTS, test names exist | run (inline) | match; `scripts/check_schema.py` RESULT ALL PASS rc 0 |
| contract.md/README constants | 9 s model budget, 15 s margin, 1024 threads/4192 files, 256 connections, 5 tries, backoff 1,2,4,8, 8 portal in flight, 16 lingerers, 10 s deadlines | grep | match code. Start-up exit 3 with `ulimit -n 1000` and exit 4 for `:memory:` confirmed. |
| SECURITY.md / README / docs | loopback-only DESK_FAKES_URL, DESK_SMTP_HOST, real-service bind refusal, bind 0.0.0.0 warning, DESK_NUDGE_TO / APPROVERS_FILE / LEADFLOW_FILE refusals (exit 4) | run10 + bind check | all match |
| docs/hubspot-probe.md | `--plan` prints 7; count mismatch refused; missing token refused; `--dry-run` non-loopback refused | probe runs | match (no spend, no network) |
| docs/tests.md, load_tools/README.md | seven checks after a load run | assembled my own run: catcher + fakes + desk with DESK_OUTBOX=smtp, `load_driver --scenario dupmix:30:0.3`, `check_invariants` (run7) | ALL 7 CHECKS HOLD rc 0. Unclear step: no page gives a start-to-finish recipe (desk must use DESK_OUTBOX=smtp to the catcher, empty model log, CRM dump from /fake/crm); I had to infer it. |
| docs/tests.md promise table, contract.md named tests | the 85 distinct named tests/prefixes | run6: `pytest -k "<all names cited in the docs>"` | 144 passed, 3 skipped (gitleaks missing x1, playwright x2), 3835 deselected, 55 s, rc 0 |
| all docs | dead file names/links | script refs.py | none dead; only placeholders (`test_name`, `cfg.txt`, `notes.properties`, `x_api_key.txt` are explicitly examples; `playwright/driver/package/browsers.json` is inside the Playwright package) |
| docs/n8n-recipe.md | 3 workflow names/files/paths, Retry On Fail 3 x 1000 ms, port 5679, URLs | read n8n/*.json | match |
| docs/tests.md | `requirements-dev.txt` pins | compared with venv312 (`-I` script) | 18 lock pins, 0 mismatch |

## Not run / not checked
- Windows blocks (PowerShell, start_all.ps1, reset.ps1), Playwright/Chromium install, `playwright install chromium`, any `pip install` (forbidden), ruff/mypy/bandit/gitleaks/hygiene (forbidden), n8n import/activate/list and the proof workflow (no n8n), the docs' quoted Windows/macOS statements, Playwright 1.63/1.65 build numbers, reset exit codes 3 and 5, Docker statements.
- Full test suite (not my task). docs/limits.md and docs/portal.md prose was read, not exhaustively verified; only the constants and rows listed above were checked.
- Not read in full: long paragraphs of contract.md lines 240-317 (follow-up handling reference) and docs/limits.md measured-figure bullets (Windows measurements cannot be repeated here).

## Housekeeping
- Created in tree-C5 only: `data/` (by start_all.sh / crash_desk.py, git-ignored); I removed it afterwards. Tree sources untouched (git status shows only the patch changes).
- Slip: I ran `pytest --collect-only` once in tree-B (not my tree) with PYTHONPATH=src: it may have written `__pycache__` there. No source edit.
- Scratch under /home/user/build/rr6/tmp-C5 (scripts qs.sh, crash.sh, http.sh, reset.sh, sec.sh, api.py, load.sh, ld/, sec/, hd/). Logs in /home/user/build/rr6/out/C5/run1..run11*.log.
- Processes: none of mine left. `pgrep` shows 2 processes of another runner (a Config.from_env snippet under unshare); not mine, not touched.
- Commands run: see the tmp-C5 scripts above (each is one `unshare -n python3 .../lo_up-q4g.py bash <script>` call); clock 12:32Z -> about 12:40Z.
