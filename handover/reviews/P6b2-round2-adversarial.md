# P6b2 round 2 adversarial review

Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority)
Reviewer type: adversarial (egm:egm-design)
Target: tickets/P6b2.md revision 2

---

R2 ADVERSARIAL review of P6b2 revision 2. Code base read: [path removed] and /tests (current main). Every cite I re-read holds, with one note: `_main` dispatches `tick` at cli.py:134, before `load_config`, which does not change the 137-139 cite.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R2-ADV-1 | Major | 235-238 (N2 `AMBIENT_KINDS` in `config.py`); 315 (test_lockin_guard.py is "NOT changed"); 16 (changelog item 6) | N2 puts a frozenset of 13 (capability, kind) pairs into `config.py`. That includes `("llm","bedrock")` and `("llm","anthropic")`. `literal_problems` (test_lockin_guard.py:592-622) scans `config.py`. It is not in `VENDOR_MODULES` and has only a `(config,"slack")` exception. The "bare vendor name" pattern (:520) matches a constant that is exactly `bedrock` or `anthropic`. So `test_core_logic_names_no_vendor` fails. Revision 2 cut `kind_identity.py` for this same reason (changelog 6), and the test file may not be edited. A4's equality test does not help, because the literals are already flagged. | Decide the form before the build. (a) Derive the set from `TABLE` with an `Entry` field such as `ambient: bool`. This reopens D2 and PENDING LEAD 3. (b) Put the set in a module already in `VENDOR_MODULES`. (c) Allow an edit to `LITERAL_OK` and drop it from the "NOT changed" list. Add a row that runs `test_core_logic_names_no_vendor` with N2 built. |
| R2-ADV-2 | Major | 170 (L1 item 1: `getattr(<any>, non-constant name)` gives `<dynamic>`); 178 | Read literally, every `getattr` with a variable name is reported as `<dynamic>`, which can never be allow-listed. `src` has at least 10 such calls: tools.py:407, config.py:75 and 271, backends/factory.py:54, actions/executor.py:37, models.py:139, table.py:59 and 278, registry.py:139, k1b/tools.py:100. E1 then fails on correct code, so the ticket cannot be built as written. | Report `getattr` only when the base resolves to `os`, `posix` or `nt` (including aliases), or to the result of `import_module`, `__import__` or `sys.modules[...]`. Add an E4 no-false-hit row for `getattr(obj, name)`. Add a mutant for "all getattr flagged". |
| R2-ADV-3 | Major | 3, 7, 235, 248, 469-485 (all pending lead); also the Target-module and Files lists | The ticket was revised at 03:07Z, before order 22 (03:20Z) and order 24 (~03:35Z). Order 22 item 25 answers yes to PL2, PL9, PL10 and PL11, and adds that "P2a's two refs follow the same rule". The ticket still leaves "the lead also decides whether `reset_credential_ref`/`stop_credential_ref` follow" (248) and carries builder defaults. N11 does not refuse those two refs in pilot and prod, and C10 does not test them. Order 24 item 33 says P6b2 owns the fix for the `base_url` text in error messages. `config.py:359-364` on main prints `system.base_url` raw, so a URL with a user name and password is printed. The ticket has no mention of it: not in Files, Interface, Tests or Mutation. | Mark PL2, 9, 10 and 11 as decided. Extend N11 and C10 to `reset_credential_ref` and `stop_credential_ref`. Add a `config.py` change that prints the system name and the reason without the URL, a test with a URL carrying credentials (parts built at run time), and a mutant. Update the PL5-7 status (order 22 item 26). |
| R2-ADV-4 | Major | 229 (step 3), 248, 313, 376 (C8) | The disjointness check forces `migrate` to load a full registry (contracts, tools, hashes). Under N11, now accepted, the migration config is a separate folder that, by the ticket's own cross-config limit (313), cannot see the runtime's secret names. So the check only covers the single-config dev case. The cost is real: `migrate` now fails on any unrelated registry error (a missing tools folder, a bad hash), and the DBA's config needs the full registry. Order 7(3)/8 says to cut surface that does not close a risk. | With N11 as the pilot and prod control, restrict step 3 to the config's own `*_secret_name` fields and `reset_credential_ref`/`stop_credential_ref` (no registry load). Or run the registry check only in dev. Say which in the ticket. If it stays, add a negative row where a broken registry stops `migrate`, so the cost is pinned. |
| R2-ADV-5 | Major | 431-432 (Mb3, Mb4) versus 392 (I7) | Mb3 (one-direction I3) and Mb4 (I4 not tied to `AMBIENT`) name "removing `platform_secret` from slack" and "removing `workload` from bedrock" as killers. Neither plant is listed in I7 or in I3/I4. On real data both mutants stay green, because both directions already hold. A mutant with no plant cannot be killed. | Add both plants to I7 (monkeypatch `DECLARED`): slack without `platform_secret`, bedrock without `workload`. Add them to the row count. |
| R2-ADV-6 | Minor | 193-198 (L4), 218 (L5) | The ambient callee list is closed and fails open. A new `AzureCliCredential`, `ManagedIdentityCredential`, `ChainedTokenCredential` or `InteractiveBrowserCredential` is a developer login or a machine role, and is not found. The same holds for `AsyncAnthropicVertex` or `AsyncAnthropicBedrock`, and for `AsyncAnthropic` or `AsyncOpenAI` in L5 (missing `api_key` is not checked). | Use a suffix rule: any name ending in `Credential` imported from `azure.identity`; any `Async` variant. Add plants. |
| R2-ADV-7 | Minor | 235, 239 | N2 refuses the key variables with no way to opt out. UNVERIFIED from memory: some serverless platforms, such as Lambda, inject `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN` for the attached role. Pilot or prod on such a platform could then never start. The ticket calls over-refusal "fail-safe" and does not mention this. | Add one owner-visible limit line. Name the escape (move the kind to a non-ambient kind, or a future allow flag decided by the lead). Check against AK-G16 (order 23). |
| R2-ADV-8 | Minor | 180-183 (L2), 162-166 | `EXEMPT` hides items 1-5 of L1 for the whole of `secrets_vault.py` and `secrets_env.py`. A new `os.environ["X"]`, a `<dynamic>` or a `<mapping>` there is invisible. For `secrets_vault.py` only `token_env` and `secret_id_env` are legitimate. | Key the exempt files by name too. For the vault, allow only `<dynamic>` inside `_env`, and pin the call count. Or note it as a stated limit. |
| R2-ADV-9 | Minor | 242-247 (N10), 377-383 (C9) | "No `password` key" does not cover `password=` with an empty value or `user:@host`. A DSN that `conninfo_to_dict` cannot parse raises inside `_migrate` and gives exit 3 with a class name, not the exit 2 refusal the step list implies. Step 6 is outside the try/except. | Refuse an empty password in pilot and prod. Wrap the parse and return 2 with `refused: the migration DSN in <ref> cannot be parsed` (name only). Add C9 rows. |
| R2-ADV-10 | Minor | 138-139, 306 | Order 22 item 24 splits P6a into P6a-1 (`app.py` check, early) and P6a-2. The ticket says only "before P6a" for the `app.py` and `config.py` edits. The relative order of P6b2-a and P6a-1 on `app.py` is not settled. | State the order versus P6a-1, or ask in `questions-for-lead.md`. |
| R2-ADV-11 | Minor | 360 (A3) | A3 patches `os.environ` to a mapping whose `__getitem__` raises, then asserts a canary "set as the value" is absent. The canary cannot be in that mapping, so the second half is vacuous. | Put the canary in the mapping's `_data` and let only `__getitem__`/`get` raise. |
| R2-ADV-12 | Nit | 5, 7, 11-50 | The header and changelog use R1-ADV and R1-COR ids that the wording rule says belong in the review notes, not in a ticket a builder reads. | Leave them in, or move them to the resolve file. |

Verified (read and checked):
- All 17 template fields are present.
- Fact 1: the environment reads at cli.py:81, 133 and 322; signer.py:127; postgres.py:56; secrets_env.py:17-18; secrets_vault.py:146.
- Fact 14: no `subprocess`, `ctypes`, `os.system` or `os.popen` in `src`. `tools.py:281-291` holds only names in a deny list, not imports.
- Fact 3: the 9 holder-import pairs from 6 files. `make("secrets")` is called only in app.py and cli.py.
- All 13 ambient sites match the file and line numbers in the table.
- `Settings(BaseSettings)` at config.py:311-312; the refusal list at config.py:365-373.
- KindSettings `extra="forbid"` (table.py:24), which supports the rollback note.
- Seven settings models have a `*_secret_name` field.
- `conftest.py:34-35` sets the two AWS key variables.
- `tests/__init__.py` exists, so `from tests.test_env_lint import ...` works.
- The identity table adds up: workload 13, bootstrap 4, platform_secret 7, delegated 2, none 5, 31 rows in all.
- Row counts: 29 plus 6 equals 35. Mutant counts: 31 plus 8 equals 39, and 39 plus 8 equals 47.
- E1 and C1 can fail on the old code. C1 returns 0 on the base because `cli.py:322-346` just reads the variable.

Not checked (UNVERIFIED):
- Whether `psycopg.conninfo_to_dict` returns `passfile` or `service` keys.
- The `azure.identity` module name.
- The attribute paths of `cfg.backends.entries()` and the registry for step 3.
- What `test_no_hardcoded_values.py` flags in `config.py`.
- Which existing pilot or prod tests need `delenv`.
- P2a-1's final validator shape.
- Whether a `psycopg` parse error echoes DSN text.
- Whether Lambda injects the AWS key variables (R2-ADV-7).
- The `demos/` reads.
- The snapshot in the scratchpad, which was not needed.
- Anything under `reviews/` or `evidence/` (not read, for independence).
