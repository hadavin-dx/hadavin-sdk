## Stand-in kinds are loopback-only, every kind is classified, and the rules run at the first config

promoted from the public demo repo duplicate-proof-lead-desk-n8n at 43110e7

Part 3 of the demo promotion. It depends on part 2 (`wip/cloud-pd-bind`, head e75f9f25), which brought `netguard.py` (the one loopback check), `bindguard.py` and the shared loopback list. This branch merges that head (merge commit 473b1742) and builds on it. The `netguard` credit belongs to part 2: this PR adds no `netguard` code, only a docstring.

### What changes, in plain words
- Every kind in the backend table (`src/hadavin_sdk/backends/table.py`) now says what it is: a **stand-in** (a local imitation of a service) or a **real** kind (it does the job itself or talks to a real service). A kind with no role stops the import of the table, naming the kind. Seven kinds are stand-ins: `llm/fake`, `store/memory`, `channel/fake`, `secrets/fake`, `audit/local_dir`, `signer/none`, `anchor/none`.
- The stage rule, stated once: a stand-in must be listed in `DEMO_ONLY`, which every live stage (pilot and prod) refuses. The only exceptions are the missing signer and the missing anchor (the named set `PILOT_STAND_INS`): they run inside the process and are refused only in prod. A stand-in listed only in `NOT_PROD` is reported as a mistake. (An earlier draft of this text said a pilot refuses every stand-in; that was wrong for these two, and is corrected here and in the CHANGELOG.)
- A stand-in must declare its hosts. `hosts=lambda s: []` is the deliberate "none" and is accepted only while the kind has no setting that points at a machine (by the words in the field name, or by a field typed as a URL or an IP address).
- The rules run the first time a config is built, not only in this repository's tests: the `Backends` model calls `assert_registry_sound()` and the loopback rule, so the loader, `Config(...)`, `Backends(...)` and `Backends.model_validate(...)` all hit them, and a kind a downstream user adds is refused at once. Import keeps only the classification check: running every rule at import crashed 5 of the 37 stage mutants before their test ran (`tests/test_kind_registry.py::test_a_broken_listing_does_not_stop_the_import_but_fails_at_first_use` pins the design).
- Every host a stand-in reaches must be `localhost` or a loopback address (`netguard.is_loopback_host`). A stand-in that lists no host although it has a host setting, whose hosts function raises, or that declares no hosts function, is refused. The refusal names the capability and the kind and never prints a host or another setting value. Limit, stated in the code: the rule judges the name only; the port is ignored and a forwarder on 127.0.0.1 can still carry traffic to another computer.
- One loopback meaning in `src`: `store/postgres._is_local` now asks `netguard.is_loopback_host` (it keeps its own socket and comma-list handling), so it also reads `LOCALHOST` and a mapped IPv6 loopback address as this computer. The new test `tests/test_loopback_sites.py::test_no_module_of_src_keeps_its_own_loopback_list` scans `src` and fails when a module writes its own loopback list. Allowed, each with a written reason: the default bind `127.0.0.1` in `approvals/receiver.py`, the deny-list names in `tools.py`, and `.is_loopback` in `guard/http.py` (a check on every address a name resolved to, a different question).
- A system address that is refused for not being https is no longer printed in the refusal (it can carry a user name and password).
- Stage names are the core's own `demo`, `pilot`, `prod`; nothing new was added. No second registry: the existing `TABLE`, `Entry`, `DEMO_ONLY` and `NOT_PROD` were extended.

Honest limits: no kind in the table names a host today, so no existing config changes and the host rule is proven with planted kinds, not with a shipped one. The read-source kinds (`KINDS` in `sources`) are a different registry and were not classified.

### Rung table
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| kind classification and registry guard | a new kind must say stand-in or real | rung 2 (exists in the public demo `lead_desk.constants`, `*_CHOICES` and `*_STAND_IN`) and rung 4 (promote) | demo tests/test_bind_refusals.py lines 100-106, read at 43110e7 | the check that the real core table is complete, run at the first config | KEEP-CODE (promoted, generalised) |
| loopback-only stand-ins | a stand-in must not reach another computer | rung 2 (demo `Config.__post_init__`) | demo tests/test_mode_safety.py, read at 43110e7 | refusal on every build path of a config, with no secret in the message | KEEP-CODE |

### Demo names removed in the generalisation
`lead_desk`, `HubSpot`, `n8n`, `DESK_*` setting names (`DESK_FAKES_HOST`, `DESK_BIND`, `DESK_CRM`, `DESK_OUTBOX`, `DESK_QUALIFIER`), `fakes server`, `leadflow`, `crm`/`outbox`/`qualifier` kind names, `CRM_STAND_IN`, `OUTBOX_STAND_INS`, `QUALIFIER_STAND_IN`. The demo's per-kind constants became one `role` field on each table entry.

### Loopback sites after this PR (searched `src` for `127.0.0.1`, `"localhost"`, `"::1"`, `ipaddress`, `.is_loopback`)
Moved to `netguard` by part 2: `config.py` (`url_allowed`), `backends/table.py`, `guard/http.py`, `llm/openai_compat.py`, `llm/common.py`, `actions/secrets_vault.py`. Moved here: `store/postgres.py`. Left, with the reason written in the scan test: `approvals/receiver.py` (default bind), `tools.py` (deny list), `guard/http.py` `.is_loopback` (address check after name resolution). Two meanings stay on purpose and are written in the `netguard` docstring: `is_loopback_literal` (three exact spellings, for the paths that send a request) and `is_loopback_host` (is this host this computer; used by the stand-in rule and the bind refusal).

### Tests that fail on the old code
Old code = 9c831f70 (round 1 head) with the three new test files copied in, run on a clean `git archive` tree. Raw output: `/home/user/build/B-PD-standins-b2-oldcode.log`.
- `tests/test_stand_in_hosts.py`: 8 failed, 10 passed (the direct `Backends(...)` build, the empty host list, the stand-in with no hosts function, the hosts function that raises, the unlisted kind, the two refusal-echo tests and the "reaches no machine" test).
- `tests/test_kind_registry.py`: collection fails (`ImportError: cannot import name 'PILOT_STAND_INS'`). A behaviour probe on the same old tree: a stand-in with an `api_base` setting and no hosts is not reported (`[]`), a stand-in listed only in NOT_PROD is not reported (`[]`), a planted kind that breaks rule 3 gets no refusal from `assert_registry_sound`.
- `tests/test_loopback_sites.py`: 3 failed (the shared-list test and the scan, because the part-2 sites are not merged in that tree, and the database address check on `LOCALHOST`).

### Mutants
`tests/standin_mutants.py` (same runner as `tests/stage_mutants.py`, a blocking CI step): 30 mutants, one per code item. Results are in the section below.

### Measured results
Head 08b8361c (code head 103e95df plus changelog and one mutant-text fix). Raw logs: `/home/user/build/pd-standins-tmp/b2final-*.log`.
- ruff check, ruff format --check, bandit -ll, tools/scan_repo.py: all rc=0.
- stage_mutants: 37 of 37 good. bind_mutants: 18 of 18 good.
- standin_mutants: 29 of 30 good at 103e95df; the one bad (S28) was a snippet that ruff format had split over lines. Fixed in 08b8361c (format and lint clean). NOT re-run on the final head: gate owed.
- Full pytest: NOT run (queued, no slot): gate owed.
- gitleaks over the branch's own commits (origin/main..HEAD): no leaks. A full-history scan reports 1776 findings in older history, not in this branch.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac
