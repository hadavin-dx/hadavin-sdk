# B-Q8a1-b7 checkpoint (round-7 fix batch). Start 22:33 UTC (machine clock); stop at 00:03 UTC.
Worktree /home/user/build/B-Q8a1-b7, branch core/q8a-1-b7, from origin 4ccb4f9a. Own venv in worktree .venv.

## 22:45 plan note (written before any code; code last)
Read: report r7, both reviewer reports, evidence RESULTS.md + probe.py, src sites. Finding that changes the plan:
the probe marker `zq-probe-mk4417` is lowercase identifier-shaped, so `shown_name` lets it through. The 8 readable
results are therefore VALUE fields (a reference that matched nothing: model_route, scope name, target_system, chain_id,
verify_check, tool file with no agent, operation) plus the pydantic union tag. Fix = never print a reference value that
matched nothing; say the field instead. Ids that DEFINE an entity (agent id, chain id in deferred messages) stay behind
shown_name (documented shape filter); said plainly in the report.
Plan: (1) errors.py ConfigValueError + `_what` allow-list; (2) registry/deferred messages say field not value; (3) new
config_url.py (login, non-ASCII netloc, percent) used by all URL fields incl. sibling fields; (4) tools/app/sources/
platform_secrets sites via shown_name, drop `from exc`; (5) InvalidUrl in tools.fetch -> ToolRefused; (6) unknown values
(chain approver_ids, rights, approver_of, tools_allowed vs manifest, egress.yaml keys); (7) Issue 8 nits; (8) tests + mutants
+ per-function reasons; (9) one full suite, one mutant run, gates.
23:xx b7: tests batch 2 written (323 pass in test_stage_names). Next: tick docstring+nits, mutants re-point, fail-before, full run
22:54 b7: all source+tests done; mutants fixed; next: full suite w/ own PG, gates, fail-before notes, commit, push
22:59 b7: committed a1869655 (local). full suite queued/running via heavy.sh, own PG on 56077 (pid owner postgres, folder B-Q8a1-b7-pg). Next: mutants alone after suite, gitleaks, notes, push.
