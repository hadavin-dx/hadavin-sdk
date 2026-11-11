<!-- full hand-back report of sub-agent a4db3f05, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW Q8c-1, round 2, design critic, head a77fab72. Read-only; I ran nothing.

## VERDICT: NOT CLEAN. 0 Blockers, 2 Majors, 7 Minors.

All three round-1 Majors are addressed in the code I read. Two things stop a CLEAN verdict. First, the 12 Vault server tests still have no run on record. Second, the operator page presents the new `+` grant as vendor-verified when only the builder read the source that supports it.

Evidence state: `/home/user/hadavin-sdk/handover/evidence/Q8c-1/a77fab7/` holds only `01-head-sha.txt` and `03-gates-output.txt`. The gates file shows ruff, ruff format, bandit, `scan_repo.py`, `policy_page.py --check` and gitleaks all with exit 0. There is no RESULTS.md and no engine, plant, mutant or full-suite output at this head. The older `7af1380` RESULTS.md shows the 11 engine tests SKIPPED, so no real Vault server has run any of them.

## Round-1 Majors, checked against the code

- **M1, server tests unrun: NOT closed as proof, closed as honesty.**
  - `ENGINE_RUN` is `None` (`tools/policy_page.py:45`). The page prints "These tests have not run yet" three times (page lines 15, 79, 129).
  - `tests/test_policy_docs.py:14-23` forbids "refused by a real Vault server" anywhere while no run is on record.
  - CI sets `HADAVIN_REQUIRE_VAULT_ENGINE=1` in both jobs that have the Vault service (`ci.yml:91` and `:156`), and a test checks both.
  - What is still missing is one CI run at the final head with `-rs`, showing the 12 tests passed and not skipped. That is Major 1 below.
- **M2, R17 wider than the code: closed in the code.**
  - The resource is now `{mount}/data/{path_prefix}+` (`secrets_vault.py:237`).
  - `binding_problems` (`test_policy_guard.py:615-644`) derives the resource from the request path (bare name becomes `+`, object attributes become settings). It also derives the capability from the HTTP verb (GET is `read`, POST is `update`).
  - The `*` form is a plant, and so is `sign/*` for R18.
  - The `path_prefix` grammar requires a trailing `/`, so `+` is a whole path part. `_vault_path_problems` enforces that and refuses `+*`. An empty prefix is refused in values mode, and the page's first line says it reads the whole mount.
  - The engine tests include "two levels below the prefix" and a plant of the old `*` form. Both are unrun.
- **M3a, literal `getattr`: closed.** `getattr_ok` is empty for Vault and `{"too_large"}` for Kubernetes, so `getattr(self, "authed")` is reported (`test_policy_guard.py:462-481`, plant P04b exactly). Also banned: `methodcaller`, `attrgetter`, `partial`, `vars`, `__dict__`, `__import__`, imports with an alias, sinks taken as a value, raw HTTP and `_opener` outside `__init__` and `call`, and any import not on a per-module list. Another module importing or subclassing the Vault client is checked by `client_user_problems`. Own-name locals: `_template` keeps `self.` and the object name, so a local called `mount` no longer equals the setting.
- **M3b, `?watch=true`: closed.**
  - `kubernetes_path_problems` requires the literal path to fit the id's pattern in `READ_OPERATIONS` and its query names to be on a per-id list. `query_name_problems` also reads every string constant in the module for `[?&]name=`.
  - The `_items` paging is covered by the module-wide scan, and a test pins the exact set of parameters written (`:1779-1791`).
  - Method is checked at run time by `tools.py:556`. Percent signs and `..` in the path are refused at `tools.py:565`.
  - I traced the P09a plant by reading and it reports two problems at line 247.

## Major findings

**Major 1. Vault server tests: no run on record at this head.**
- Where: `tests/test_policy_engine.py`, all 12 server tests; `docs/declared-permissions.md:79` and `:129`.
- Failure: the 12 tests encode the refusal claims for R17, R18, R19, the 13 listed refused requests, and the "old `*` form" and "admin token" plants. Nobody has seen them pass. Admin-control statuses (200 or 204) were "written from vendor documentation, not seen" (test file header). A wrong status or a fixture signature, such as `transit_key()` returning `(_, key)`, turns CI red after merge. I did not read `tests/contracts/kinds/*`, so I could not check those signatures.
- Fix: before merge, one CI run on the final head with `-rs` output saved by the evidence runner showing 12 passed and 0 skipped. Only then set `ENGINE_RUN` and update `test_m1`.

**Major 2. The R17 `+` claim is shown as verified, but only the builder read its sources, and the page does not say so.**
- Where: `secrets_vault.py:238-256`; page line 57; the header of `tests/fixtures/policy_sources_2026-11-11.txt:8-10, :16-17`.
- Failure: the fixture header states that V-ACL, V-PARSE and B-ACL, and the `+` reading of V-POL and B-POL, were read only by the second builder. The rule in the ticket's errata (E2) says `verified` means the evidence runner found the form. R17 shows `verified` with sources V-POL through B-ACL and `claims not checked: none`. Its `bound` cell states "nothing deeper is covered" as fact.
- The page head also says names come from "a separate check". For `+`, the one-segment semantics and the `+*` refusal are an unreviewed single reading, with the confirming server test unrun.
- This is the exact claim that closes round-1 Major 2, and the page offers copy-ready text for it.
- Fix: until the evidence runner re-reads V-POL, V-ACL and V-PARSE, or Major 1 is closed, set `claims_unverified=("the + matches exactly one whole path part, nothing deeper",)` on R17. The tool then withholds the copy-ready block (`copy_ready`, line 852) and the page shows "not yet checked". Alternatively, split `verified` from `read by the builder only` in the page cell. Apply the same wording to the never entries whose source was builder-only (`undelete`, `subkeys`, `byok-export`).

## Minor findings

**Minor 3. R17's one-part claim depends on `_NAME`, and its test uses four names.**
- Where: `test_policy_guard.py:1850-1860` against `secrets_vault.py:34`.
- Failure: `_NAME` is `[A-Za-z0-9_.-]{1,255}`. A change that adds `%`, `?`, `#` or `+` to it would let a name reach Vault outside the declared path. `+` stands for one whole path part but also admits `%2F`-style spellings. The test tries only `a/b`, `a/b/c`, `..` and an empty name, so such a change stays green.
- Fix: parametrize the test over `%`, `?`, `#`, `+`, `*`, a space, a newline and `%2F`.

**Minor 4. The hand-written settings map and the Kubernetes namespace check are not followed from setting to request.**
- Where: `Shape.settings` (docstring `test_policy_guard.py:222-224`); `secrets_vault.py:152-159`; `signer_vault.py:80`; `kubernetes.py:228-229`.
- Failure: if `build` passed `settings.field` as the prefix, or the signer took `settings.mount` instead of `transit_mount`, the request would leave the declared path while A1 stays green. Removing `if scope not in self.namespaces` has the same effect for Kubernetes (the namespaced Role fails closed server-side). The page's bounds list does not name this gap.
- Fix: one AST test that `build` assigns the named setting to each mapped attribute, or a sentence on the page.

**Minor 5. The body of `call` is trusted.**
- Where: `secrets_vault.py:71-94`.
- Failure: `call` and `__init__` are the allowed raw-HTTP functions. A change inside `call`, such as appending `?list=true` to the URL or changing the method for a path ending in `/`, is not seen. A Kubernetes query built by concatenation (`"&" + "watch=1"`) also passes the constant scan. Both need deliberate effort.
- Fix: state both on the page as bounds, or pin the `Request(...)` construction line.

**Minor 6. Reserved-value wording is wrong in the safe direction.**
- Where: `policy_page.py:216` and `:983-984`; page head.
- Failure: the page says "a Vault mount that starts with `sys`". The code refuses only when the first path part equals `sys`, `auth`, `identity` or `cubbyhole`, so `sysdata` renders. The page promises more refusals than exist.
- Fix: say "whose first part is".

**Minor 7. Wording for a non-technical reader.**
- Where: page lines 55 and 103.
- Failure: the table shows `update` for Transit signing with no explanation. "No write rights" reads as violated when signing changes nothing stored. Column heads like "claims not checked", "what limits a wildcard" and `{self.mount}` in the call column are developer language.
- Fix: one sentence per kind, "Vault calls signing `update`; it stores nothing", and a plain-words legend.

**Minor 8. Short-lived credentials and Q8a-1.**
- Where: `kubernetes.py:368-372`; `secrets_vault.py:213-219`.
- Failure: all three kinds declare `lifetime: long` with an exception (rule D6 satisfied). The Kubernetes text says Q8a-1 "covers credentials that this package reads but does not issue", but the kind holds no credential, and Q8a-1's branch is named `live-override-refusals`. I could not confirm Q8a-1 removes any of these tokens.
- Fix: name the real removing ticket, or open a ledger row. The never-list for Kubernetes still has 3 unverified role names, but they are dated in `PENDING_NAMES` and shown "not yet checked", so I raise no finding on them.

**Minor 9. Single-dependency and process items.**
- Engine evidence rests on one source-available server image (`hashicorp/vault:2.2.0` pinned by digest). OpenBao is named in the page as not run, and I found no ledger row with a trigger in `handover/ledger*.md`. I did not read the real ledger, so this may exist elsewhere.
- `ENGINE_RUN` is a hand-set constant that nothing ties to an actual run.
- No new runtime dependency: `tools/policy_page.py` is standard library only, and PyYAML (`pyproject.toml:18`) is already pinned and used only in tests.

## Checks that came out as intended

- Policy paths and capabilities against the code:
  - R17 is GET `{mount}/data/{path_prefix}{name}` with `read`.
  - R18 is POST `sign/{key_name}` with `update`, exact path, so the hash-algorithm suffix is excluded.
  - R19 is GET `keys/{key_name}` with `read`.
  - The sign-in POST `auth/{auth_mount}/login` is a free entry; the signer's note says it is declared in the other module.
  - These match the code's three request sites and are not wider.
- Kubernetes: R20 `list` on `apps/deployments`, R21 `list` on `core/events`, R22 `get` on `core/pods/log`, one Role and RoleBinding per namespace, never a ClusterRole. `_derived` ties each grant to its path pattern, and the never-list equals `_WRITE_VERBS` plus `_SHELL_RESOURCES` plus `secrets`. `create` now carries the self-review exception, and `watch` is deliberately absent. The free `rules_review` note says a hardened cluster needs its own cluster-wide grant.
- Never-list gaps from round 1 are closed (`delete`, `undelete`, `subkeys`, `patch`, `restore`, `rotate`, `trim`, `byok-export`).
- Reserved values (`sys`, `auth`, `identity`, `cubbyhole`; `kube-`; built-in and `system*` role names; `default` service account; duplicate namespaces) are refused and have tests. Control characters are refused in every text field, and `+*` and `*` in the middle of a path are refused.
- One identity per function is not claimed. The page says one process uses one identity, and that verifying needs the signing grant (an honest disclosure of the open F2 finding).
- The credential block says "A token that holds only this policy" and warns about the `default` policy and identity groups.
- `+`, `?` and `*` cannot enter via values: grammars are full-match, and text is written with `json.dumps`.

## What I did not check

- I ran nothing: not the 12 server tests, the guard tests, the plants, the mutants (CI now includes a policy-mutants step) or the full suite. I traced the plant outcomes by reading code only.
- I did not read the rest of `policy_mutants.py`, `tests/test_no_hardcoded_values.py`, `tests/contracts/kinds/*`, `tests/test_lockin_guard.py` or `ci.yml` beyond the lines cited.
- I could not confirm Vault's `+` semantics, `no_default_policy`, or the admin status codes against any vendor text; the fixture hashes were not re-fetched by me.
- I did not read other tool modules that share the Kubernetes ServiceAccount token. A process running tools with their own `READ_OPERATIONS` would need more than this Role.
- OpenBao and AppRole or Kubernetes sign-in are untested, as the page already states.
- The builder's notes, as instructed.

Files: `/home/user/build/snap/q8c1-a77fab7/{src/hadavin_sdk/actions/secrets_vault.py, src/hadavin_sdk/audit/signer_vault.py, src/hadavin_sdk/sources/kubernetes.py, tools/policy_page.py, tests/test_policy_guard.py, tests/test_policy_engine.py, tests/test_policy_docs.py, tests/fixtures/policy_sources_2026-11-11.txt, docs/declared-permissions.md}`.
