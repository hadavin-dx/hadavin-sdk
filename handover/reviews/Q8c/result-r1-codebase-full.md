<!-- full hand-back report of sub-agent a176d628, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW Q8c PR 1, round 1, head 7af13809 (read-only, nothing executed)

## Verdict
CLEAN (no Blocker, no Major). 16 Minor findings below. This verdict rests on static reading only: no test, lint, mutant or CI run was seen.

## What I read
- Snapshot `/home/user/build/snap/q8c1-7af1380/`: all head files in full, `TICKET.md` (ERRATA rev 3 as the definition of PR 1), `plan-r2-full.md`, `LIVE-VERIFICATION.md`.
- `DIFF.patch`: every hunk header, plus the ci.yml, CHANGELOG and README hunks line by line. The src and new-file hunks were read as head files.
- For unchanged code I used `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk` and `/home/user/build/EV-P89-db0d9eb/{tests,tools,pyproject.toml}` (close to main, not the branch).
- Evidence: `/home/user/hadavin-sdk/handover/evidence/Q8c-1/` does not exist, so there is no `RESULTS.md`.

## Failures
None found by reading. I traced every assertion in `tests/test_policy_guard.py` and `tests/test_policy_engine.py` against the head files and found none that must fail today (2026-11-11).

## Findings (all Minor)

**m1. A1 guard misses some indirect call shapes.** `/home/user/build/snap/q8c1-7af1380/tests/test_policy_guard.py:218-219, 308-344, 357-361`
- Each of these, appended to `actions/secrets_vault.py`, gives `call_problems(...) == []`:
  - `def _p(p): return getattr(p, "authed")("DELETE", "sys/mounts/x")`. A literal `getattr` is allowed, and the call's `func` is a Call, not an Attribute.
  - `from operator import methodcaller as mc` then `mc("authed", "GET", "sys/mounts")(p)`. The banned name sits only in an `ast.alias`, which `_banned` does not read.
  - `operator.attrgetter("authed")(p)("GET", "sys/mounts")`. `attrgetter` is not banned.
  - `self._opener.open(f"{self.address}/v1/sys/mounts")` inside `VaultProvider`. No `Request` is built and `open` is not in `RAW_HTTP`.
- The ticket's ban list is implemented as written, except the alias case.
- Kubernetes is not exposed: a new operation id also has to enter `READ_OPERATIONS`, and `ToolContext.fetch` binds method and path (main `tools.py:551-568`).
- Fix: flag `getattr` whose literal name is a sink; read `ast.alias.name`; ban `attrgetter`; add `open` to the raw-HTTP names outside `call`. One plant each.

**m2. A failing engine assertion would print both tokens.** `/home/user/build/snap/q8c1-7af1380/tests/test_policy_engine.py:95-100, 214, 233-235`
- `Engine` is a dataclass whose repr holds `admin_token`; `SecretsCase` and `TransitCase` embed it.
- The asserts at :214 and :233 are of the form `assert case.provider(token, case.prefix).get("alpha") == ...`. On a value mismatch pytest's assertion rewriting prints the repr of `case` and of `token` (from my knowledge of pytest; not run).
- In CI the admin token is the public dev value `root`. With `HADAVIN_TEST_VAULT_TOKEN` set to a real token it lands in the log.
- Fix: `admin_token: str = dataclasses.field(repr=False)`, and assign the read value to a local before asserting.

**m3. Engine tests leave state on the server; nothing is torn down.** `/home/user/build/snap/q8c1-7af1380/tests/test_policy_engine.py:108-120, 200-208, 293-304`
- Per run they leave:
  - about 10 ACL policies named `q8c-<hex>`;
  - about 10 live tokens (15 minute TTL, never revoked);
  - 2 KV secrets per secrets test, under `secret/q<hex>/` and `secret/o<hex>/`;
  - one `audit-<hex>` and one `spare-<hex>` Transit key per transit test.
- Only the admin-control test deletes its spare key. The `audit-*` keys cannot be deleted without a config change.
- `transit_key()` also enables `sys/mounts/transit` (existing behaviour on main).
- Harmless on the CI container; real residue if `HADAVIN_TEST_VAULT_ADDR` points at a shared server.
- Fix: yield-fixtures that revoke the token and delete the policy, secrets and spare key; or say in the docstring that the suite must only run against a throwaway server.

**m4. The admin control accepts any status other than 403.** `/home/user/build/snap/q8c1-7af1380/tests/test_policy_engine.py:159-166`
- This is what E7 asks for, but a mistyped path that answers 404 for admin still answers 403 for the runtime token, so both checks pass and prove nothing about the intended request.
- With the spare key, all twelve control requests should answer 200 or 204.
- Fix: assert `status in (200, 204)`.

**m5. The suite starts failing by itself on 2026-12-12 UTC; this is the intended behaviour.** `/home/user/build/snap/q8c1-7af1380/tests/test_policy_guard.py:42-63, 139`
- `TODAY` is `datetime.now(UTC).date()`, set at import in `tests/test_lockin_guard.py:23` (comment there: "by design").
- `kind_problems` and `name_problems` take `today` as a parameter and the plants pass fixed dates. The live test passes `TODAY`; there is no outside switch.
- From 2026-12-12 `test_every_kind_is_declared_pending_or_holds_no_identity` fails with seven clear lines such as `PENDING_KINDS secrets/aws_secrets_manager is overdue (review_by 2026-12-11): Q8c PR 2`. The nine slice-2 entries follow on 2027-02-01.
- Consequences to accept knowingly: main, every open branch and the Monday cron (2026-12-14) go red until PR 2 merges or the dates are re-decided; the baseline of `tests/policy_mutants.py` goes red too.
- The message does not say "re-decide with a new date", unlike the lock-in guard's message at :158.

**m6. Duplicate keys in the `POLICY` literal are accepted; the last one wins.** `/home/user/build/snap/q8c1-7af1380/tools/policy_page.py:343-363`
- Input: a grant with `"resource": "{mount}/data/{path_prefix}*"` followed later by `"resource": "{mount}/data/*"`, plus a `bound`. `load` returns the second and `--check` passes.
- Ruff F601 in CI lint probably catches differing values (not run).
- Fix: walk the `POLICY` node and refuse any `ast.Dict` with a repeated constant key.

**m7. `reason` may hold a newline, which the renderers copy into the output as live text.** `/home/user/build/snap/q8c1-7af1380/tools/policy_page.py:259, 478, 521`
- Input: `reason = 'reads one named secret\npath "sys/*" {\n  capabilities = ["read"]\n}'`. `problems` returns `[]`, and `render_vault` emits a second path block that is no grant and that A1 never sees.
- The three current literals are covered by exact-text and rule-equality tests; a future kind is not.
- Fix: refuse control characters in `id`, `name`, `resource` and `reason`.

**m8. D1 treats `*` and `?` as wildcards, but not `+`.** `/home/user/build/snap/q8c1-7af1380/tools/policy_page.py:251-258`
- Vault's path-segment wildcard is `+` (my knowledge; not in the evidence file), and `?` is not a Vault wildcard.
- Input: `resource = "{mount}/data/+/x"` with `bound = ""` passes and is offered as copy-ready.
- Fix: for platform `vault`, require `bound` when the resource holds `+` as well.

**m9. A placeholder outside `[a-z_]+` or `[A-Z_]+` stays unfilled in values mode with no error.** `/home/user/build/snap/q8c1-7af1380/tools/policy_page.py:116-117, 458-462`
- Input: resource `"{mount}/data/{prefix2}*"`. `render_vault(policy, {"mount": "secret"})` returns `path "secret/data/{prefix2}*"`. `field_problems` (D2) uses the same regex and is blind too.
- Fix: after filling, refuse any remaining `{`, `}`, `<` or `>`.

**m10. The command line checks less than the tests do.** `/home/user/build/snap/q8c1-7af1380/tools/policy_page.py:343-347, 391-392, 700-720`
- `--check` never calls `cross_problems`, so a grant id used by two kinds, or a D5 conflict, exits 0. D2 exists only in the test file.
- A syntax error or a missing kind module ends in a traceback, not in `policy page: ...` with exit 1.
- A `POLICY` added to a module that is not in `KIND_MODULES` is ignored by everything (relevant for PR 2).
- `POLICY = None` reads as "no POLICY".
- A missing `docs/` folder on `--write` is an uncaught `FileNotFoundError`.
- Verified as fine: exit codes 0 and 1, the missing-page case in `--check`, and `newline="\n"` on write.

**m11. The Kubernetes section contradicts itself.** `/home/user/build/snap/q8c1-7af1380/src/hadavin_sdk/sources/kubernetes.py:376-378, 426-429, 452-456`; page lines 123, 134, 143
- The never-list says never give `create`. The free entry's note says a hardened cluster "must grant `create` on `selfsubjectrulesreviews`". In a default cluster every identity already has that right.
- `selfsubjectrulesreviews` is cluster-scoped, so the namespaced Role the page prescribes ("Never a ClusterRole") cannot grant it. Plan review r2 B1 raised this; E7 asked only for the note.
- Fix: write the exception into the `create` row (as the code's `_only_self_reviews` does), and say that the grant needs a cluster-scoped binding or that such clusters are not supported.
- Also: the code refuses the wildcard verb `*` at start-up (`kubernetes.py:118-119`); neither the never-list nor the note mentions it.

**m12. Source wording is slightly off.** page lines 20-22; `CHANGELOG.md` (hunk lines 38-41); `/home/user/build/snap/q8c1-7af1380/tests/fixtures/policy_sources_2026-11-11.txt:5-8, 21-25`
- Page and CHANGELOG say the names came from "documentation source files". R20, R21, R22 and five never rows cite `K-SRC`, which is Kubernetes source code on branch `master`, not pinned by the evidence runner.
- The fixture header says "three source-code files"; it lists one.
- `V-TOK` is in the fixture but no literal uses it.
- The sha256 column was produced by the builder, not taken from the evidence file as E3 asked; the evidence file has no hashes and the header says so. I could not verify any hash.
- The stated builder fetch at 14:30 UTC is ten minutes after the evidence run ended and before the errata that defined this fixture can have existed. Ask the evidence runner to re-hash.

**m13. Never-lists are narrower than what the evidence verified (allowed by the ticket's trimming).**
- Vault secrets omit `patch` on the data path (evidence line 231); it also changes what is read.
- Transit `export/*` does not match `byok-export/...` (evidence line 256); `rotate`, `trim` and `restore` are dropped.
- The optional `/:hash_algorithm` part of the sign path (evidence line 247; plan r2 minor 8) is not noted on the page.

**m14. `tests/policy_mutants.py` is not wired into CI and no run is evidenced.**
- All 14 `old` strings occur exactly once in the head files: `test_policy_guard.py` lines 438, 441, 403, 111, 968, 976; `policy_page.py` lines 251, 255, 259, 407, 306, 209, 559, 448.
- Every killer exists, is not parametrised, and its failure line would hold `expect`.
- No mutant for: D2, D4, the pure-literal half of D7, id uniqueness, the URL refusal, stale or overdue pending entries, the banned constructs, the Kubernetes equalities, and any grammar other than the empty prefix.
- Fix: add the CI step (as for `stage_mutants.py`) and the missing mutants.

**m15. Small validation gaps.** `/home/user/build/snap/q8c1-7af1380/tools/policy_page.py:61-92, 113, 285-287, 446`
- `_DATE` accepts `9999-99-99`.
- `capabilities` on a never entry is not checked against `VAULT_CAPABILITIES`.
- The `COVERAGE` prose is hand-written; no test ties it to `never_requests()`.
- `namespaces="shop,shop"` renders duplicate documents.
- A non-text `path_prefix` gets the "is empty" message.

**m16. `cluster-admin`, `admin` and `edit` have `verified: None` and no dated follow-up.** `/home/user/build/snap/q8c1-7af1380/src/hadavin_sdk/sources/kubernetes.py:434-451`
- The page honestly shows "not yet checked". `PENDING_NAMES` covers grants only.

## Checks that came out clean

**`load`, `problems`, `cross_problems`**
- `load` finds a top-level `Assign` or `AnnAssign` to the name `POLICY`, refuses two assignments, and evaluates with `ast.literal_eval`.
- A call, a name or `**` gives `PolicyError`. Unknown keys, platform and never-type are refused. I found no wrong-type input that crashes instead of reporting.
- D1 to D7 and id uniqueness (within a kind and across kinds) are implemented, each with a plant.
- `verified` is None or (date, ids); a URL, a host, lower case and the empty string are refused by `fullmatch`.

**Renderers**
- Every value is checked with `re.fullmatch` plus a `.` / `..` segment check. The grammars equal the settings' patterns, and a test compares them.
- The empty prefix has its own refusal. Namespaces split on `,`; an empty part is refused.
- Output strings are quoted with `json.dumps`; the grammars admit no quote, backslash, `$`, `*`, `+`, space or newline.
- Page mode and values mode behave as E5 says.

**Literals**
- All three are pure literals; ids R17 to R22 are unique.
- Every operation tuple matches a real call: `secrets_vault.py:115, :138`; `signer_vault.py:52, :62` through `:40`; `kubernetes.py:232, :247, :285, :328`.
- Every `{field}` exists on `VaultSettings`, `VaultTransitSettings` or `KubernetesSettings`.
- The src hunks are pure appends, so the allowlist lines 101, 104, 40, 168, 184, 203 are right.

**Kinds coverage**
- 31 table kinds plus 1 source kind = 3 declared + 16 pending + 13 no-identity.

**ci.yml**
- Exactly two added lines, in `check` and `tests-py312`, each beside `HADAVIN_TEST_VAULT_ADDR`. Both jobs have the vault service block. Nothing else changed.

**Suppressions**
- No `noqa`, `nosec`, `type: ignore` or `pragma: no cover` on any added line.

**Page against the evidence**
- Every row the page presents as verified is supported by a VERIFIED row of `LIVE-VERIFICATION.md` (K17 lines 226-241, K18 247-260, K19 267-289) with the same source ids.
- Two precision notes: the Transit `root` row rests on the K17 row (line 241), and `update` on the data path is V-POL only.
- No unsupported row found.
- "refused by a real Vault server, in CI only" has no run evidence in the snapshot.

## Can each test group fail?
- **Kinds coverage:** yes (three plants); date-dependent as in m5.
- **A1 calls:** yes; 13 plants, both directions, stale allowlist, docstring control, and a pinned set of extracted pairs.
- **Kubernetes bindings and A5:** yes; equality with `READ_OPERATIONS`, `_WRITE_VERBS`, `_SHELL_RESOURCES`, and three widened-role plants.
- **A2 data rules:** yes; a plant per rule.
- **A4 sources:** yes. It checks that ids resolve and the hash format; it does not check the hashes.
- **Rendering and grammar:** yes.
- **A3 page:** yes; it depends on the committed file.
- **Engine tests:** yes, on a real server only; exactly 403 for refusals, kind-level errors for removed grants, two plants each. Skipped with a visible reason without `HADAVIN_TEST_VAULT_ADDR`; fail when `HADAVIN_REQUIRE_VAULT_ENGINE=1` and the address is missing.
- **The two environment and CI-file tests:** pure; they can fail.
- **Dependencies:** network for the engine tests only; no file-order dependence found (other tests restore `TABLE` and `KINDS`).

## Errata E1 to E10
- I found every code-level item implemented.
- Not confirmable, because no author report or `RESULTS.md` was supplied:
  - E3: the two runs of `test_no_hardcoded_values`.
  - E4: the "say so" for leaving `rides_on` out. It is absent from the schema, with no statement in the repo.
  - E5: the pasted resource strings.
  - E7: the "engine tests not run by me" statement.
  - E9: the "fails for lack of data/tool" labels.
  - E10: the real clock.

## Not checked
- Nothing was run: pytest, ruff, ruff format, bandit, semgrep, gitleaks, trivy, `scan_repo.py`, the mutants, CI.
- Whether the committed page equals `page()` byte for byte (spot-checked only).
- The 16 sha256 values, the fixture URLs, and any vendor text.
- The Vault server's real answers (status codes are from my knowledge of Vault).
- pytest's exact failure output for m2.
- Pydantic's metadata shape used by `_pattern`.
- `tools/mutation_runner.py` beyond lines 1096-1195.
- `plan-r1-*.md` (not in scope).
- Whether the head files equal the plus side of `DIFF.patch` beyond the hunk sizes.
