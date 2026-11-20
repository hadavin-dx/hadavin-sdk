# hadavin-sdk

Shared building blocks for Hadavin's fixed-price AI builds, and the demo builds that use them.

| Folder | What it holds |
|---|---|
| `src/hadavin_sdk/` | The reusable core: one interface per capability, with backends chosen per client in config |
| `demos/` | Demo builds on the core (invoice & PO automation, document Q&A) |
| `tests/` | Tests for the core and the repository rules |

Rules:
- The core never imports anything from `demos/` (a test enforces it), so a client delivery can take the core alone.
- Demo data is synthetic only. No client data, secrets, account ids or personal details are ever committed.

## Python version

**Production and pilot must run Python 3.13.x (Unicode 15.1.0). Python 3.12 (Unicode 15.0.0) is for demos only.**

The text fold in `guard/textnorm.py` depends on the interpreter's Unicode data. Its look-alike table is the Unicode 15.1.0 table. On another Python the fold still runs, but every check name starts with a tag and never equals one made on 3.13.

`app.build` calls `textnorm.require_pinned_unidata()` when the stage is pilot or prod. On any other Unicode data (Python 3.12.3 carries 15.0.0) it raises `UnidataMismatch` and nothing runs. The check is not loosened. A demo may still run on 3.12.

Moving the pin to a later Python (for example 3.14) is a data migration, not a version bump. The CHANGELOG entry that starts "Pin", in the section on text folding, lists what changes together.

### Checking your Python, and what other versions do

The labels TESTED, MEASURED, UNVERIFIED and NOT RUN are defined once, in [SECURITY.md](SECURITY.md#words-used-here).

- To check, run `python3 --version`, or use the Python you install the kit with. To see its Unicode edition, run `python3 -c "import unicodedata; print(unicodedata.unidata_version)"`. Pilot and prod need `15.1.0`.
- Why: text folding uses the Unicode character data built into Python. The folding tables are built for edition 15.1.0, which Python 3.13 carries. MEASURED: a run on Python 3.12 printed edition 15.0.0.
- Pilot and prod on Python 3.12: NOT RUN (no pilot or prod start on 3.12 was tried). By design, the program refuses to start and prints `UnidataMismatch`. The fix is to install Python 3.13.
- TESTED: one test on Python 3.13, with the version number faked, shows that refusal. The refusal comes before the program connects to the secrets vault. NOT RUN: a check of other outside services.
- UNVERIFIED (read from the project file): the project file allows installing on 3.12 (`requires-python = ">=3.12"`). So the install succeeds, and the failure shows only when the program starts.
- Demo on Python 3.12: by design, the program starts. Each folded name carries a tag with the Unicode edition, so names folded on 3.12 and on 3.13 do not match. Do not compare results from the two versions. UNVERIFIED (read in the code): the tag rule.
- Python 3.11 or older: UNVERIFIED (read from the project file): the install is refused, because the project file asks for 3.12 or later.
- Python 3.14 or later: UNVERIFIED (read from the code): pilot and prod refuse to start on any Python whose Unicode edition is not 15.1.0. Do not run pilot or prod on 3.14 or later until the release notes say the character tables were rebuilt for it.

## Text-fold functions that nothing calls yet

UNVERIFIED (read in the code; a search of `src/` found no caller): the protected-value (DENY) side of the text fold in `guard/textnorm.py` is present and tested, but the redaction path does not call it. The functions are:

- `scan_holds`, `register_value`, `Coverage`, `scan_cache`, `scan_needles` and `scan_views`;
- `identity_key`, `identity_keys`, `could_be_same_person`, `allow_equal` and `names_equal`;
- `has_mixed_script`, `has_hidden_channel` and `value_scripts`.

`guard/injection.py` uses only `scan_views_no_value`. `defaults.py` names some of the others in comments.

## Replay check (report only)

`hadavin-sdk replay AGENT --bundles D --cause-list D --max-usd X --out OUT [--k K]` runs a client's recorded
incidents through an agent. `hadavin-sdk score --outputs OUT --answers F --cause-list D --bundles D` counts the
results into `OUT/score/score-report.md`. Neither gives a verdict, and a replay pass is not evidence of live accuracy.
`replay` refuses a non-empty `OUT`. If a replay dies half-way it leaves `FAILED.txt` in `OUT`: delete the folder to
re-run. `score` refuses an `OUT` holding `FAILED.txt`, and a non-empty `OUT/score/`. A `score_run` audit event does not prove a report file exists (events are written first).

## Limits and trust (read tools)

What this release does and does not promise, in one place. The labels are defined in [SECURITY.md](SECURITY.md#words-used-here). A statement with no label describes how the code is built, as read in the code: UNVERIFIED unless a label says otherwise.

- **The import pin proves one thing: the reviewed text of one file is what runs.** `tool_module_hashes` hashes a tool module (and its parent packages' `__init__.py`, which must hold no code) before it is imported, and the very bytes that were hashed are executed; a module already loaded under other bytes is refused. The loader-name refusal (`import_module`, `__import__`, `importlib`, `runpy`, `exec`, `eval`, `compile()`, `builtins`, ...) is a best-effort tripwire against accidental dynamic loading, not a boundary. A tool body is trusted code: it may import any other module by absolute name (not covered by the pin), call `os`, `subprocess` or `socket`, or build a loader name at run time. The boundary is code review of the module plus K7 network policy. Who may change a pin: `tool_module_hashes` lives in `config.yaml` (hashed into the agent's config hash), so the module and its pin should be one reviewed change that someone other than the author approves (CODEOWNERS on the module and on `config.yaml`); the SDK cannot enforce that.
- **`scope_inventory`** entries are an operator's attestation that a credential is read-only. The `sha256:` token in one is checked for format only and compared with nothing; it is a label, not a signature or a hash check. The Kubernetes probe is the only automatic proof of scope.
- **A tool module declares its own `READ_OPERATIONS`** (method and path regex per operation), so it constrains itself. What keeps a read a read is the credential's scope (probed for Kubernetes) and `evidence.post_read_operations` (a POST read, such as a review or a query, must be named in the config).
- **Egress is in-process only.** The fetch layer resolves a host once, refuses loopback, link-local, unspecified, multicast and reserved answers, the cloud metadata addresses (169.254.169.254, 100.100.100.200, 192.0.0.192, 168.63.129.16, `fd00:ec2::254`, `fd20:ce::254`) and IPv6 forms that carry them (IPv4-mapped, 6to4, Teredo, NAT64), and connects to the checked address, so a DNS answer that changes between the check and the connect cannot reach the socket. **Private ranges are allowed by design** (10/8, 172.16/12, 192.168/16, 100.64/10, fc00::/7, plain http to `.svc` names and ExternalName services): in-cluster services live there, so the only thing that bounds which private host a tool can reach is its manifest `hosts` allowlist and the K7 network policy; review a manifest's hosts as you would a firewall rule. Also refused: 0.0.0.0/8 and 198.18.0.0/15. NAT64 (`64:ff9b::/96` and the local-use `64:ff9b:1::/48`) is refused whole, by our own rule and not the standard library's flags, so an IPv6-only cluster behind DNS64 cannot use it. The request is sent with the checked host (lower case, no trailing dot). At most 8 name lookups can be stuck at once (a lookup cannot be cancelled); more are refused. A name lookup has a 5 s timeout. Loopback NAMES (127.0.0.1, localhost, ::1) skip the address check: that is for tests and local development, tools cannot name one, and the LLM clients and executor share the connection, so a pilot or prod deployment must not point their endpoints at one. **K7 network policy is a hard prerequisite before any pilot;** nothing here replaces it, and a tool body can open its own socket.
- **Redaction is pattern-based and bounded.** It finds the kinds it knows (addresses, ARNs, keys, tokens, e-mail, URL credentials, command-line credential flags) in the original, the canonical (NFKC, invisible characters removed) and the JSON-unescaped text. A secret in a shape it does not know passes: a bare, unlabelled 40- or 32-hex string in prose is not claimed (it looks like a git SHA or a build id); the same string after a label (`api_key=`, `token:`) or with a known prefix is masked. Every scanning bound has a fallback that masks instead of passing text through: a command-line credential more than 1024 characters after its command word masks the rest of the line; a quoted credential over 255 characters is masked whole; a URL password over 1024 characters masks the rest of the token; an e-mail local part over 254 characters is masked whole; JWT segments over 4096 characters and tokens whose mix of cases comes after 128 characters are masked by the run-of-129-base64-characters pattern. Originals of identifier kinds longer than 256 characters are masked but never stored (they cannot be restored). **Cost is bounded polynomial, not linear:** each pattern is O(text x a fixed bound); measured on this build, about 3 s of CPU for 256 KiB of repeated command words and about 2.2 s for 256 KiB of distinct IP addresses. Every call of `redact_text` refuses more than 256 KiB of text, and any view the second pass would scan (NFKC expands some characters: 14,600 U+FDFA make a 262,000-character view) that is over it (`InputTooLarge`, a `RedactionError`), before doing the work, so no caller can skip the cap; the document is capped at 256 KiB, a run's map at 2,000 distinct values (`document_too_complex`), and each tool result is cut to twice its cap before redaction. Not decoded for the generic patterns: base64 or URL-encoded client PII, HTML-entity, octal or hex escapes, a secret split across two results, combining marks (only secrets the box handed to a tool are also scrubbed through percent, HTML-entity, `\u`, base64, base32 and invisible-character layers, to a stated depth of three levels). A fetch that is cut mid-token leaves the prefix of a secret that straddles the cut unrecognised: the cut prefers whitespace within the last 256 bytes and otherwise falls 256 bytes earlier.
- **At rest.** `redaction_maps` holds the ORIGINALS of identifier kinds (e-mail, name, phone, address, IP addresses, ARNs) as plaintext JSON for 30 days (400 under a hold); `tool_calls` holds redacted tool output. Encryption at rest, backups and database access control are the deployment's job. The purge role can read neither the mapping nor the output (column grants).
- **Database roles.** The runtime role appends and reads evidence and has no DELETE; only the purge role (`migrate --purge-role`, `backends.store.purge_dsn_secret_name`, required in pilot and prod on Postgres) deletes it, with SELECT limited to the columns its DELETE needs. `migrate` asserts the roles' EFFECTIVE privileges (inherited, PUBLIC, default privileges, relations outside the grant map, ownership, CREATE on the schema, superuser) and rolls the grants back on any excess. The runtime process holds both DSNs and tool bodies run in-process, so the split defends against bugs and mistakes, not a compromised process; run `purge_evidence` as its own job holding only the purge secret if that matters. The stop switch has its own role: the runtime role can add a stop (INSERT `kill_switch_stops`) and cannot clear one; only the reset role (`migrate --reset-role`, `backends.store.reset_credential_ref`, held on the operator's machine, never by the runtime process) can (see `docs/stop-state-runbook.md`). **Waiver:** the runtime role still holds the approver-recording write rights (UPDATE `approval_requests`, INSERT `approval_decisions`): agent runtime and approvals recorder are one process today; separating them (R365) is K6/K8 work and the owner's to accept.
- **Caps are per process, not per run.** `max_concurrent_tool_calls` and `max_tool_calls_per_minute` (and the abandoned-body ceiling) protect the client's systems from the agent; one run making many slow calls, or eight stuck bodies, can refuse tools to every run in the process until they end, and a body that never returns holds its slot until restart. Per-run fairness is not implemented (waiver). Source reads from the app's own source objects count toward the same request cap.
- **Re-probe.** A source's scope is probed again every `evidence.source_reprobe_s` (3600 s), so RBAC widening goes unseen for up to an hour; a failed re-probe switches off every tool that names the source (`options.source`) or lists its host, and the source's own reads, until a probe passes. The probe reads `resourceRules` for the configured namespaces only: it ignores `nonResourceRules`, cannot see RoleBindings in other namespaces and does not flag `configmaps`.
- Tools never go through an environment proxy (it would resolve the target itself, skipping the address check); the LLM clients and the executor may.
- Grounding is a whole-token match, exact in case. A proposal may name the front of a longer name only where the tool's manifest declares a `generated_suffix`; case is folded only for a `target_system` listed in `evidence.case_insensitive_targets`. An identifier input that is not a string is ungrounded.
- `caught_by=guard` is set when a guard stopped a concrete proposal (ungrounded, uncited, invalid_proposal, run_budget, injection_suspected); failures (tool, redaction, evidence, a guard outage, the provider) are not catches.
- A tooled agent's action contracts must set `additionalProperties: false`; an undeclared input is refused as `invalid_proposal`.
- A hold on a run is not retroactive, and no hold outlives 400 days. The purge step is due 60 s early by design (`TICK_SLACK_S`).
- Every read is an audit event (principal, tool, `inputs_hash`, `output_hash`, `rows`) and a `tool_calls` row a client can review. Tamper evidence of past rows holds only when the runtime login does not own the audit tables and has no UPDATE, DELETE or TRUNCATE on `audit_entries` (`migrate --runtime-role` grants it SELECT and INSERT there, and the append-only triggers refuse the rest even to a role that owned them; migrate does not yet refuse a runtime role that owns the tables); it is not proof of authenticity (a taken-over runtime can still append rows), and two runtime rights are wider than needed today (see SECURITY.md). Nothing of one client is kept in a process-global cache.
- Kubernetes is the only built read-source kind; a second one is an SDK edit (trigger K5-ITO).
- **The import pin proves one thing: the reviewed text of one file is what runs.**
  - `tool_module_hashes` hashes a tool module before it is imported, together with its parent packages' `__init__.py` (which must hold no code).
  - The very bytes that were hashed are executed. A module already loaded under other bytes is refused.
  - The loader-name refusal (`import_module`, `__import__`, `importlib`, `runpy`, `exec`, `eval`, `compile()`, `builtins`, ...) is a best-effort tripwire against accidental dynamic loading. It is not a boundary.
  - A tool body is trusted code. It may import any other module by absolute name (not covered by the pin), call `os`, `subprocess` or `socket`, or build a loader name at run time.
  - The boundary is code review of the module plus a network policy that limits what the process can reach.
  - `tool_module_hashes` lives in `config.yaml`, which is hashed into the agent's config hash. So the module and its pin should be one reviewed change that someone other than the author approves (CODEOWNERS on the module and on `config.yaml`). The SDK cannot enforce that.
- **`scope_inventory`** entries are an operator's attestation that a credential is read-only. The `sha256:` token in one is checked for format only and compared with nothing. It is a label, not a signature or a hash check. The Kubernetes probe is the only automatic proof of scope.
- **A tool module declares its own `READ_OPERATIONS`** (method and path regex per operation), so it constrains itself. What keeps a read a read is the credential's scope (probed for Kubernetes) and `evidence.post_read_operations`. A POST read, such as a review or a query, must be named in the config.
- **Egress is in-process only.**
  - The fetch layer resolves a host once and connects to the checked address. A DNS answer that changes between the check and the connect cannot reach the socket.
  - It refuses loopback, link-local, unspecified, multicast and reserved answers, and 0.0.0.0/8 and 198.18.0.0/15.
  - It refuses the cloud metadata addresses (169.254.169.254, 100.100.100.200, 192.0.0.192, 168.63.129.16, `fd00:ec2::254`, `fd20:ce::254`) and the IPv6 forms that carry them (IPv4-mapped, 6to4, Teredo, NAT64).
  - NAT64 (`64:ff9b::/96` and the local-use `64:ff9b:1::/48`) is refused whole, by our own rule and not the standard library's flags. So an IPv6-only cluster behind DNS64 cannot use it.
  - **Private ranges are allowed by design** (10/8, 172.16/12, 192.168/16, 100.64/10, fc00::/7, plain http to `.svc` names and ExternalName services), because in-cluster services live there. Only the manifest `hosts` allowlist and the network policy bound which private host a tool can reach. Review a manifest's hosts as you would a firewall rule.
  - The request is sent with the checked host (lower case, no trailing dot).
  - At most 8 name lookups can be stuck at once, because a lookup cannot be cancelled. More are refused. A name lookup has a 5 s timeout.
  - Loopback names (127.0.0.1, localhost, ::1) skip the address check. That is for tests and local development. Tools cannot name one. The LLM clients and the executor share the connection, so a pilot or prod deployment must not point their endpoints at one.
  - **A network policy is a hard prerequisite before any pilot.** Nothing here replaces it, and a tool body can open its own socket.
- **Redaction is pattern-based and bounded.**
  - It finds the kinds it knows: addresses, ARNs, keys, tokens, e-mail, URL credentials, command-line credential flags, host names under a private suffix such as `.corp` or `.lan`, and a name after the word `host`.
  - It looks in the original, the canonical text (NFKC, invisible characters removed) and the JSON-unescaped text.
  - A secret in a shape it does not know passes. A bare, unlabelled 40- or 32-hex string in prose is not claimed, because it looks like a git SHA or a build id. After a label (`api_key=`, `token:`) or with a known prefix it is masked.
  - Every scanning bound has a fallback that masks instead of passing text through:
    - a command-line credential more than 1024 characters after its command word masks the rest of the line;
    - a quoted credential over 255 characters is masked whole;
    - a URL password over 1024 characters masks the rest of the token;
    - an e-mail local part over 254 characters is masked whole;
    - JWT segments over 4096 characters, and tokens whose mix of cases comes after 128 characters, are masked by the run-of-129-base64-characters pattern.
  - Originals of identifier kinds longer than 256 characters are masked but never stored. They cannot be restored.
  - **Cost is bounded polynomial, not linear:** each pattern is O(text x a fixed bound).
    - MEASURED on the test machine: 4.5 to 5.4 s of CPU for 256 KiB of repeated `curl -u ` against the 6.0 s budget. A slower machine can refuse that text.
    - MEASURED earlier, not re-run on this code: about 2.2 s for 256 KiB of distinct IP addresses.
  - **Size caps.** Every call of `redact_text` refuses more than 256 KiB of text before doing the work (`InputTooLarge`, a `RedactionError`), so no caller can skip the cap.
    - It also refuses any view the second pass would scan that is over the cap. NFKC expands some characters: 14,600 U+FDFA make a 262,000-character view.
    - The document is capped at 256 KiB. A run's map is capped at 2,000 distinct values or 524,288 characters of values (`document_too_complex`).
    - Each tool result is cut to twice its cap before redaction.
  - **Base64 is decoded and read.** A run of 12 or more base64 characters whose decoded text holds a value the redactor finds is masked whole as `<ENCODED_n>`. The depth is 3 levels (`defaults.B64_MAX_DEPTH`). TESTED (see SECURITY.md, the finding on base64 text).
    - Not covered: a direct `redact()` call, a blob glued to other base64 characters, a blob split across fields, or one wrapped with a log prefix on each line.
    - Hex, base32, base85, compressed data and quoted-printable are not decoded.
  - **Not decoded for the generic patterns:** URL-encoded client PII, HTML-entity, octal or hex escapes, a secret split across two results, and combining marks.
    - Only secrets the box handed to a tool are also scrubbed through percent, HTML-entity, `\u`, base64, base32 and invisible-character layers, to a depth of three levels.
  - A fetch that is cut mid-token leaves the prefix of a secret that straddles the cut unrecognised. The cut prefers whitespace within the last 256 bytes and otherwise falls 256 bytes earlier.
- **At rest.** `redaction_maps` holds the ORIGINALS of identifier kinds (e-mail, name, phone, address, IP addresses, ARNs) as plaintext JSON for 30 days (400 under a hold). `tool_calls` holds redacted tool output. Encryption at rest, backups and database access control are the deployment's job. The purge role can read neither the mapping nor the output (column grants).
- **Database roles.**
  - The runtime role appends and reads evidence and has no DELETE. Only the purge role deletes it (`migrate --purge-role`, `backends.store.purge_dsn_secret_name`, required in pilot and prod on Postgres). Its SELECT is limited to the columns its DELETE needs.
  - `migrate` asserts the roles' EFFECTIVE privileges (inherited, PUBLIC, default privileges, relations outside the grant map, ownership, CREATE on the schema, superuser). It rolls the grants back on any excess.
  - The runtime process holds both DSNs and tool bodies run in-process. So the split defends against bugs and mistakes, not a compromised process. Run `purge_evidence` as its own job holding only the purge secret if that matters.
  - **Waiver:** the runtime role also holds the approver-recording and kill-switch write rights (UPDATE `kill_switch`, UPDATE `approval_requests`, INSERT `approval_decisions`). The agent runtime and the approvals recorder are one process today. Separating them is later work, and the owner must accept the waiver (OPEN).
- **Caps are per process, not per run.** `max_concurrent_tool_calls` and `max_tool_calls_per_minute` (and the abandoned-body ceiling) protect the client's systems from the agent.
  - One run making many slow calls, or eight stuck bodies, can refuse tools to every run in the process until they end.
  - A body that never returns holds its slot until restart.
  - Per-run fairness is not implemented (waiver). Source reads from the app's own source objects count toward the same request cap.
- **Re-probe.** A source's scope is probed again every `evidence.source_reprobe_s` (3600 s), so RBAC widening goes unseen for up to an hour.
  - A failed re-probe switches off every tool that names the source (`options.source`) or lists its host, and the source's own reads, until a probe passes.
  - The probe reads `resourceRules` for the configured namespaces only. It ignores `nonResourceRules`, cannot see RoleBindings in other namespaces and does not flag `configmaps`.
- Tools never go through an environment proxy, because it would resolve the target itself and skip the address check. The LLM clients and the executor may.
- Grounding is a whole-token match, exact in case. A proposal may name the front of a longer name only where the tool's manifest declares a `generated_suffix`. Case is folded only for a `target_system` listed in `evidence.case_insensitive_targets`. An identifier input that is not a string is ungrounded.
- `caught_by=guard` is set when a guard stopped a concrete proposal (ungrounded, uncited, invalid_proposal, run_budget, injection_suspected). Failures (tool, redaction, evidence, a guard outage, the provider) are not catches.
- A tooled agent's action contracts must set `additionalProperties: false`. An undeclared input is refused as `invalid_proposal`.
- A hold on a run is not retroactive, and no hold outlives 400 days. The purge step is due 60 s early by design (`TICK_SLACK_S`).
- Every read is an audit event (principal, tool, `inputs_hash`, `output_hash`, `rows`) and a `tool_calls` row a client can review. Nothing of one client is kept in a process-global cache.
- Kubernetes is the only built read-source kind. A second kind is built only when a client needs one.

## Capped spend and masked model input

- **Capped spend.** Every model call the runtime makes goes through one model gate: before the call the most it could cost (system prompt, messages, documents, tool definitions and output schema at one token per byte, the route's full output, times the client's retry attempts) is booked against the agent's day and month budget, and the call is not made when it does not fit; after the call the booking is replaced by the real cost. This holds for model calls made through the gate on PostgreSQL with the grants applied. Its limits: the `gate` (eval) and `replay` command lines are capped per process in memory (`--max-usd`; `gate` without it uses the agent's daily budget in demo and is refused in pilot and prod) and their calls are not audited one by one; the Bedrock guardrail detector's call is not metered; a stale price table is not refused yet. **A failed call can hold budget without real spend:** when a provider call fails and the provider did not clearly refuse it before doing any work (today that is an HTTP 400, 401, 403, 404, 413 or 422 as the only answer; a call that used up its retries is never treated as refused), the most that call could have cost stays counted against the day and month budget for about an hour (until the tick's expiry step closes it), so a wrong API key or throttling can use up a small daily budget although nothing was spent. The run's own cost moves only when a call is settled.
- **Masked model input.** Every value the run has identified (a value in the run's redaction map) is replaced by its placeholder in everything sent to a model: each message and each document, on every call, including text added before the value was identified. This is not "nothing secret can reach a model": a value the redactor did not identify is sent as written, only the spelling the map holds is replaced, the system prompt and tool definitions are operator text and are not touched, and the `gate` and `replay` command lines and the judge have no run map (they redact their own input before sending).
- **How a refused call ends a run.** Kill switch: `STOPPED` `kill_switch`. Day or month budget: `NEEDS_PERSON` `limits.daily_budget` / `limits.monthly_budget`. Limits store unreachable or an amount the meter cannot book: `NEEDS_PERSON` `limits_unavailable`. Run map could not be enforced: `NEEDS_PERSON` `redaction_error`. No provider is contacted in any of these, and a refusal inside the `llm_judge` detector ends the run the same way instead of being read as an injection flag.
## Spend limits: what is in force today
Status, in one sentence: exact money and the no-lowering wall are in force; no-overspend holds for the live loop's main model call only and is NOT in force for the listed ungated sites until the model gate installs reserve/settle (F-install).
- In force: money is exact decimal (no floats); on PostgreSQL after migration 0011 the runtime login cannot lower a booked amount or change a cap; the caps live in the table `hadavin_caps`, written only under the reset login; `Limits.reserve` and `Limits.settle` exist and are tested.
- The live loop's main model call reserves the worst case before the call and settles after: the reservation bounds the booked worst case per call; a reply costing more than the worst case is booked in full (an overshoot, audited); the kill switch is read before the reserve, not atomic with it. NOT gated: `_screen` llm_judge (charged after the fact), `cards.render_shadow` with a detector (an llm_judge cost there is not charged at all), `guard/bedrock_guardrail` (`apply_guardrail`), `k1b/loop.py`, `evals.py`, `guard/judge.py`. Concurrent use of those can overshoot a cap. A hold of a failed run (provider error, crash) stays booked on the day and month counters until an operator runs `release_expired_spend` (see the runbook); the tick only marks it expired.

## Running the tests

Install with `uv sync --group test` (the parallel runner `pytest-xdist` is only in that group). Run
`pytest -q -n 3 -m "not live and not perf"` for the fast parallel run, as CI does. Run the timing (perf)
tests on their own, without `-n`: `pytest -q -m perf`. Mixing perf tests into a parallel run on a busy
machine can give a false timing alarm. On a 2-core machine use `-n 2`.

## Licence

Proprietary. Copyright (c) 2026 Hadavin. All rights reserved. See [LICENSE](LICENSE). Viewing this repository
does not grant any licence to use it.

## Security

What the core guarantees in pilot and prod, and what it leaves to the client's own tool, is stated in `SECURITY.md`.

See [SECURITY.md](SECURITY.md).
