# Changelog

## Unreleased

### Upgrade steps
- **K5-core, redaction behaviour you may notice.** The producers of text that reaches a model, a vendor screen, a card or a log line (listed in `guard/producers.py`, each tested by `tests/test_k5_round9.py` with a percent-, entity- and assignment-encoded secret) go through one function, `guard.runmap.redact_text`, which also undoes percent, HTML-entity, backslash-u, `\u{41}`, `%u0041`, backslash-x, backslash-U (eight digits) and three-digit octal escapes (not one- and two-digit octal or named escapes: `\1` and Windows paths would decode wrongly) and NFKC to a fixed point before it redacts: a secret written as `%41KIA...`, `&#65;KIA...` or `password%3Dx` is masked in those places, not only in tool results. Not on that list: the text of the ask-your-data demo's own ledger and command line (see its README). A text nested deeper than `defaults.SCRUB_MAX_LAYERS` (8) layers is not shown. A tool result is redacted whole up to 262,144 characters before it is cut; when it IS cut (at that cap, or again after a short handed-out secret was replaced by the longer marker), the last 8,192 characters of the result are dropped so a token that straddles the cut leaves no fragment (`defaults.CUT_MARGIN`; a PEM key is about 1.7 KB for RSA-2048, 3.2 KB for RSA-4096 and 6.4 KB for RSA-8192). Cost: redacting a hostile text at the cap takes one to four seconds on a laptop (one pass per distinct view); a call that has spent `defaults.REDACT_BUDGET_S` (6 s) before a further view is refused (`InputTooLarge`, nothing shown), and the perf step bounds it. A card text is sanitised and has commands withheld first and is redacted once, last (and once more with tags deleted, real placeholders and line breaks kept, when markup split a key from its value; that view is used only when it finds a secret value the text pass did not). A card summary is shown whole or replaced by a short note (never cut); a summary whose inputs are too large to redact says so. In a case bundle, camelCase credential keys (`clientSecret`, `dbPassword`), numbers and nested values under a credential key are masked too. The Kubernetes source defaults (`K8S_*`) stay in `defaults.py`, under their own header, with every other default.
- **K5-core, stated limits of redaction.** A secret value that itself contains a plain space, `;`, `,` or `&` (for example `password="my secret phrase"`) is masked only up to that character, by the redactor's own definition of a value; and a form-encoded `;` or `&` inside a value (`password%3Dab%3Bzq9`) is ambiguous between one secret and a key and value followed by more text (see SECURITY.md). A masked value nested deeper than the layer cap, or more than 256 values that need pairing across decoded views, refuses the text (`InputTooLarge` or `TooDeep`) instead of showing it.
- **K5-core, upgrade steps for an existing database.**
  - **API changes (breaking for custom code; pre-1.0, so the minor version moves).** The `Store` protocol gains six methods (`add_tool_call`, `list_tool_calls`, `purge_tool_calls`, `put_redaction_map`, `get_redaction_map`, `purge_redaction_maps`): a custom store without them is refused at start with their names (`ConfigError`). `Executor.execute` takes an optional `inputs_view`. Source kinds register through `sources.kinds.register`, which refuses overlapping operation prefixes. `make`, `hosts` and `Deps` now live in `hadavin_sdk.backends.factory`; there is no re-export from `hadavin_sdk.backends` on purpose (a repo rule keeps that package file free of imports so importing the config never loads a secret provider), so the old import fails with an ImportError: change it to `from hadavin_sdk.backends.factory import make`.
  - **Ledger test:** a database whose ledger holds `0005_evidence` and whose files are renamed is REFUSED by `migrate` with a message naming the row (`tests/test_k5_fixes2.py`); it never applies anything silently.
  - **Repair every dev and demo database before the first run of the merged code** (a demo database is taken from the merge commit, not from a branch). If the tables already exist: change the `version` of the `0005_evidence` row in `schema_migrations` to `0006_evidence` by hand. If not (or if an early `0005_evidence` lacks `tool_calls.error`): drop `tool_calls`, `redaction_maps` and that ledger row, then run `hadavin-sdk migrate --runtime-role R --purge-role P` again.
- **K5-core, redaction input cap.** `redact_text` refuses text over 262,144 characters AND any view of it the second pass would scan over that size (`InputTooLarge`, before the work; 87,000 U+FDFA used to take 24 s and now 0.03 s). A document refused that way ends `NEEDS_PERSON document_too_large`. `evidence.max_document_bytes` may not exceed 262144. An action input schema with an `identifier` flag below the top level is refused at load. A tool's `generated_suffix` may hold at most two variable-length repeats (`{lo,hi}`). `evals.gate` raises a `ConfigError` naming the golden case whose input cannot be redacted. Name lookups: at most 8 may be stuck process-wide (shared by tools, LLM clients and the executor), and the permit is returned if the lookup thread cannot start. NAT64 (`64:ff9b::/96`, `64:ff9b:1::/48`) is refused by our own rule on every Python version.
- **K5-core, tool-result size and decode.** A tool result is now REFUSED (`InputTooLarge`, the run abstains `redaction_error`) when a secret was handed out to the tool and the decoded view of the result (JSON `\u` escapes, percent-encoding, HTML entities, then NFKC) would pass 262,144 characters; the decode is computed once per result. A tool result that was cut keeps its `[truncated]` marker inside the same cap (the window is 262,132 characters), so a large legitimate output is no longer refused because of the marker. Action contracts with an `identifier` flag below the top level are refused for every action, used or not. Card text over the redactor's cap is refused, and tick, log and validation-error lines are redacted first and then cut to their length.
- **K5-core, the scrub of a tool result.** The limits below are pinned by tests in `tests/test_k5_fixes5.py` to `test_k5_fixes9.py` and `tests/test_k5_layers.py`; the two figures on the end of a cut text (the proportion that loses a group) are estimates from a run, not pinned.
  - **Size.** Scrubbing grows a short secret (6 characters become the 17-character `<SECRET_REDACTED>`), so a result far below the 262,144-character cap could pass it and was refused (`InputTooLarge`; 15,421 copies of a 6-character secret was the smallest case). The grown text is now cut back to the cap with the `[truncated]` marker. `max_bytes` of a tool and `legacy_max_output_bytes` may be at most 262,144. Two refusals remain, both `InputTooLarge` and a `redaction_error` abstention: a decoded view of the result that would pass the cap, and a text that the escaping of result markers and placeholder look-alikes (the neutralise step of `redact_untrusted`) grows past the cap (it needs look-alike characters within a few times of the cap).
  - **Cuts.** A cut can split a handed-out secret (the raw-size cut, the window cut, the cut after a replace inside the scrub), and then no whole spelling is left to mask. After EVERY such cut, and before any swap of the text for its decoded view, the scrub removes: a half-written escape at the end (`\u005`, `&#9`, `%C3`, half of a surrogate pair); the longest stretch before the marker that reads (layers and NFKC undone) as the start of a spelling of any handed-out secret (a compatibility-character spelling can need more than one character to read as a start) (hex in any case); and the front of a base64 token that wraps a secret (standard or URL-safe alphabet, token of 8 characters or more, cut back to the 4-character group that holds the first byte). A reply loses the last few characters to this; ordinary text at the very end can lose a trailing `&T`, a `%C3%A9`, or (about 3 in 100, when the tail looks like base64) its last group. The look-back is at most `evidence.scrub.fragment_scan` (4,096) start positions with one decode each.
  - **Exception messages.** The message of a tool's exception is scrubbed in full BEFORE it is cut to 160 characters (200 for a refusal), so the cut cannot leave the front of a secret.
  - **What the scrub undoes.** A handed-out secret (6 characters or more) is found as it is, URL-quoted, hex (any case), base64 and base32 (base64 also two or three times), and behind JSON string escapes (`\uXXXX` with surrogate pairs joined, `\/`, `\"`, `\\`, `\n`, `\t`; PHP writes every slash as `\/`), percent-encoding (twice), HTML entities, NFKC compatibility characters (full-width, mathematical, circled, superscript) and invisible characters. The layers are undone to a fixed point, at most 8 rounds (`defaults.SCRUB_MAX_LAYERS`; deeper is cut or replaced, see the next entry), so they may nest either way (`&#37;41`, a double-escaped entity). The redactor's second pass (`guard/runmap.py`) joins surrogate pairs and reads `\/` too.
  - **What it does not undo.** Hex of a percent-encoded value, ROT13 or any substitution cipher, reversed text, a character separator (`V-h-5`), one- and two-digit octal escapes, named escapes, a base32 token that wraps a secret, a base64 token shorter than 8 characters (`tools.B64_MIN_TOKEN`, the one bound), and any layer not listed: the text stays as it came and a cut inside such a spelling leaves its first characters next to the marker. This is a limit, not a guarantee: the control is that a tool is not handed a secret it does not need (least privilege). `tests/test_k5_fixes7.py` pins the unhandled layers so a change is seen.
  - **Settings.** The thresholds are validated configuration under `evidence.scrub` (`tail_window` 256, `min_redaction_window` 4096, `min_secret` 6, `fragment_scan` 4096, `fragment_min` 1, `partial_end` 10; ranges in `config.ScrubSettings`), one set of defaults in `hadavin_sdk/defaults.py`.
- **K5-core, layered encodings.** Every tool result, whether or not a secret was handed out, also gets a decode-to-fixed-point view (percent, entity, backslash escapes, NFKC) that is redacted too, so a pattern-shaped secret (`%41KIA...`, `password%3Dx`) is found; a text nested deeper than the cap is not shown. The scrub undoes any ordered stack of percent, HTML entity (decimal and hex), backslash-u, backslash-slash and NFKC full-width layers, and a base64 token front, to a fixed point: each round applies NFKC, JSON escapes, percent-decoding and entity-decoding ONE AT A TIME (a combined step turned the half entity `&#10`, which percent-decoding had just exposed, into a newline, so `percent(entity(secret))` cut inside the token left its front: 7 of 451 cut points). A half-written escape at the end is dropped before every decoder. The depth is capped at `defaults.SCRUB_MAX_LAYERS` (8); a text that still changes after the cap is not shown (the tail is cut back to its start; a whole result becomes `<SECRET_REDACTED>` + `[truncated]`): fail closed. Our own design (not a quoted standard): CWE-174 (double decoding) warns that decoding twice lets values past a check and says to reject non-conforming input; OWASP Input Validation Cheat Sheet says to decode before checking and to cap parser nesting depth (both pages fetched 2026-11-03); neither describes decoding to a fixed point, which is what finding a secret in any spelling needs. `error_reason` and every tool result go through the same `_scrub`. Pinned by `tests/test_k5_layers.py` (seeded fuzz of 20,000 orderings and depths at the default and a small window, the recorded failing cut points, a sensitivity control, a perf-marked 100 KB timing test).
- **K5-core, purge role, store settings and tool gating.**
  - **Required now in pilot and prod on Postgres: `backends.store.purge_dsn_secret_name`** (the process refuses to start without it, so the purge cannot silently fail and keep plaintext originals for ever), and `evidence.restored_hash_key_secret_name` must hold at least 16 bytes. Re-run `hadavin-sdk migrate --runtime-role R --purge-role P`: the purge role now has column-level SELECT only (`runs`: run_id, state, updated_at; `redaction_maps`: run_id, updated_at; `tool_calls`: call_id, run_id, created_at) plus DELETE on the two evidence tables, and `migrate` asserts both roles' EFFECTIVE privileges (membership, PUBLIC, default privileges, relations outside the map, ownership, CREATE, superuser) and rolls back on any excess.
  - New settings, both under `evidence`: `max_map_entries` defaults to 2000 (a run whose text plants more distinct values ends `NEEDS_PERSON document_too_complex`), `post_read_operations` defaults to empty (a tool operation bound to POST must be listed). The redactor's built state is kept per run, so cost no longer multiplies strings by map size.
  - A tool whose source was switched off by a failed re-probe is refused in `ToolBox.invoke` (by `options.source` or by host), not only the app's own source objects. A non-string value for an identifier input is ungrounded. Every redaction bound now has a masking fallback. Source reads count toward the request cap. More metadata addresses are refused and a name lookup has a 5 s timeout. The restored-hash comparison is constant-time.
  - The import-pin text is corrected everywhere: the pin proves the reviewed text of one file is what runs; the loader-name refusal is a best-effort tripwire; a tool body is trusted code. Perf tests moved to a `perf` marker in their own CI step (blocking: the check is a ratio, so a noisy runner moves both runs alike); the `check` job's timeout is 30 minutes.
- **K5-core, restored-input hash key, document size and concurrency slots.**
  - **New required key in pilot and prod: `evidence.restored_hash_key_secret_name`** (a secret in your secrets kind). The gate's audit event now carries an HMAC of the restored inputs under that key, not a plain hash of real identifiers; an execution whose plan has no recorded hash is refused (`restored_unbound`), not skipped.
  - `evidence.max_document_bytes` now defaults to 262144 (was 1 MiB). The command-line credential patterns (curl, mysql, redis-cli, sqlcmd, ldap, htpasswd, docker/mongo/az login) were quadratic on repeated words and are bounded to 1024 characters of gap; a long-token sweep masks any run of 129 or more base64-ish characters; the URL-password bound is 1024. EMAIL masks local parts up to 254 characters. A test generates its inputs from every pattern's own keywords and fails on super-linear time.
  - No regular expression is built from a client value any more (`evidence.contains` uses plain scans; the sweep finders are compiled without entering `re`'s cache). The pinned-module import check refuses these loader names as a best-effort tripwire, not a boundary (`import_module`, `__import__`, `importlib`, `runpy`, `exec`, `eval`, `compile()`, `builtins`, `spec_from_file_location`); it stays best effort, a meta-path finder restricted to the pin is the sound fix.
  - The concurrency slot is held until the tool's thread ENDS (a timed-out body keeps its slot), and every request a tool makes counts toward `max_tool_calls_per_minute`. Tools never use an environment proxy; the LLM clients and the executor still may. More addresses are refused (metadata addresses, 6to4, Teredo, NAT64, 198.18.0.0/15). `generated_suffix` is a tiny grammar (literals and bounded character classes). Any credential-bearing header is refused over plain http. The scrub also sees double percent-encoding, base32 and triple base64. A failed re-probe switches the source OFF (reads refused) until a probe passes; a malformed RBAC rule proves nothing.
- **K5-core, migration roles and store settings.**
  - **Run `hadavin-sdk migrate` again with `--runtime-role R --purge-role P` (two different roles) and set `backends.store.purge_dsn_secret_name`.** The runtime role no longer holds DELETE on `tool_calls` or UPDATE/DELETE beyond what it needs: only the purge role deletes evidence (it holds column-level SELECT plus DELETE on the two evidence tables only). Without a purge DSN the purge step runs under the runtime identity, is refused by the database and FAILS loudly (evidence is kept, never silently deleted).
  - New `evidence` keys: `max_document_bytes` 1048576 (a larger document ends `NEEDS_PERSON document_too_large`), `case_insensitive_targets` [] (grounding is exact in case unless the contract's `target_system` is listed), `source_reprobe_s` 3600 (a new tick step `reprobe_sources` probes every source's scope again and fails loudly if RBAC widened), `max_concurrent_tool_calls` 4 and `max_tool_calls_per_minute` 120 (per process: the agent cannot raise the load on a client system). New manifest key `generated_suffix` (a regex; the only way a proposal may name the front of a longer name, such as a pod's hash suffix).
  - Behaviour: grounding is a whole-token match and exact in case (`payments` is not found in `payments-canary`, `admin` not in `Admin`); a validator crash or an evidence-store outage is `evidence_unavailable` with no `caught_by` (it was `invalid_proposal`/`guard`); redaction patterns are bounded (bounded polynomial time, see README) and tool results are cut to twice their cap before redaction; hosts are resolved once, refused if they resolve to loopback, link-local, unspecified, multicast or reserved addresses, and the connection goes to the checked address (DNS rebinding, in process; K7 stays the backstop and is a hard prerequisite before any pilot); the Kubernetes probe accepts `create` only on the three self-review resources and treats an empty or status-less answer as not proven; a bearer token never travels over plain http; a tool secret under 6 characters is refused; the gate's decide event carries `restored_hash` and every tool event carries `output_hash` and `rows`; `forbidden_host` normalises trailing dots, case and non-ASCII and knows more metadata names.
- **K5-core, placeholder look-alikes and decoded views.** `redact_untrusted` escapes markers and placeholder look-alikes in every decoded view; redacted text is cleaned of lone surrogates last and a document that cannot encode is an abstention; tooled agents need `additionalProperties: false` contracts and an undeclared input is `invalid_proposal`; the pin refuses relative imports and parent `__init__.py` with code, and a cached module must carry the same digest; `caught_by=guard` now also covers `uncited` and `invalid_proposal` (not `guard_unavailable`); a failed step is due again at the next tick; a source endpoint obeys the manifest host rules; fetch resolves a hostname once and connects to the checked address; K7 network policy is still required).
- **K5-core, evidence migration, retention keys and tool pins.**
  - The evidence migration is `0006_evidence.sql` (the number follows the reservations migration that ships before it); it was never released under another name, so no database needs renaming except a development one (see the upgrade steps).
  - New key `retention.held_tool_calls_max_days` (400): held runs' tool calls now have their own ceiling, and the two 400-day ceilings run before the hold hook, so a failing hook cannot stop them.
  - `tool_module_hashes` are checked BEFORE any tool module is imported (a mismatch or a missing pin in pilot and prod raises `ConfigError` with nothing imported); the pins are part of the agent's config hash.
  - Every non-boolean action input must say `identifier: false` (or `true` on a string); `evidence.cluster_suffixes` must end in a private label; a Kubernetes `api_url` is scheme and host only; `sources=` objects are refused in pilot and prod.
  - A run parked in NEEDS_PERSON no longer keeps its redaction map past the ordinary retention (it cannot move again).
  - `caught_by` is now set only when a control stopped a proposal (`ungrounded`, `run_budget`, `injection_suspected`, `uncited`, `invalid_proposal`); a tool, redaction or evidence failure sets none.
- **K5-core, config and wiring.**
  - **Run `hadavin-sdk migrate` with the runtime role granted** (`--runtime-role`) **before** starting the new image: the evidence migration (`0006_evidence.sql`) adds `tool_calls` (with an `error` column) and `redaction_maps`; without the grants the runtime cannot write them.
  - New `config.yaml` keys (defaults in `hadavin_sdk/defaults.py`; units as named): `tool_modules`, `tool_timeout_s` (seconds, 10; one deadline for a whole tool call), `tool_module_hashes` (SHA-256 of each tool module's source file; required in pilot and prod), `executor_timeout_s` (seconds, 10; dev executor), `scope_inventory` (`"<page>#<anchor> sha256:<64 hex>"`, format-checked only), `sources` (`kind`, `settings`, `token_secret_name`, `ca_file`; built and probed at start-up), `retention.tool_calls_days` 30, `retention.redaction_maps_days` 30, `retention.hold_labelled` true, `retention.held_maps_max_days` 400 (at most 400 and at least `redaction_maps_days`), `retention.purge_every_s` 86400, and an `evidence` block: `max_tool_errors` 3, `legacy_max_output_bytes` 20000, `fetch_ceiling_bytes` 2097152, `https_ports` [443], `cluster_ports` [80, 8080, 9090, 9093, 3100], `cluster_suffixes` ['.svc.cluster.local', '.svc'], `stored_kinds` (may narrow the default, never widen it; UUID is not stored), `max_tool_calls_per_run` 40, `max_tool_bytes_per_run` 262144, `max_abandoned_tool_threads` 8.
  - Tool manifests (`tools/<agent>.yaml`) gain `ports`, `options`, `ca_file`, `ca_secret_name`; an agent with a manifest must mark every string input of its actions `identifier: true` or `identifier: false`; hosts may not be IP literals, loopback or metadata names; `cluster_http` needs every host in-cluster. A tool with a credential, or one that reads a configured kind of source, needs a `scope_inventory` entry `tool:<name>` or an explicit mapping (`options.source`) to a probed source whose token secret is the tool's only secret and whose host is one of the tool's `hosts`.
  - `app.build(..., hold_run_ids=)` wires the held-run hook (a retention-hold feature supplies it); a hook that raises stops that tick's purge, loudly. A hold is not retroactive. `tools=` (plain callables) is refused in pilot and prod.
  - `evals.gate` now matches by subset (expected inputs must match, extra optional inputs are allowed) and offers a tooled agent's actions with the required `evidence` field, as the runtime does.
  - Behaviour changes to know: a redaction fault is an abstention (no `caught_by`), a store fault while keeping evidence is `evidence_unavailable`; the model now sees its own tool-call arguments in later steps; text sent to the model is no longer rewritten except for placeholder-shaped literals and result markers.
- **K5-core: read-only evidence, redaction before the model, tool wiring.** Needs `hadavin-sdk migrate` (new
  the evidence migration (`0006_evidence.sql`): tables `tool_calls` and `redaction_maps`; the runtime role gets SELECT, INSERT on
  `tool_calls` and SELECT, INSERT, UPDATE on `redaction_maps`; only the purge role deletes them (rounds 8 and 10); the portal role reads neither). Run it
  before starting the new image; a custom `Store` must implement the six new methods.
  - **The document and every tool result are now redacted with the run's one map before the injection check and
    before the model** (`guard/runmap.py`). Placeholders (`<EMAIL_1>`) appear in plans; real values are restored
    only for tool arguments, for the gate's schema check (`authorize(..., inputs_view=)`, new denial
    `input.unresolved`) and for the dev executor (`Executor.execute(..., inputs_view=)`). Only identifier kinds are
    stored; secret and regulated kinds are never stored or restored.
  - **Recorded model answers (`FakeLLM`) and `evals.gate` are keyed by the redacted document.** Re-record any
    fixture whose document holds an email, a phone number or another redactable value (the two repo fixtures were
    re-recorded: `pii.txt`, `injected.txt`). `config_hash` is unchanged for agents without a tool manifest.
  - New `tools/<agent>.yaml` manifests (read tools only; `side_effect: none`), `Config` keys `tool_modules`,
    `tool_timeout_s`, `retention` (`tool_calls_days` 30, `redaction_maps_days` 30, `hold_labelled` true,
    `held_maps_max_days` 400, at most 400) and `scope_inventory`. A manifest is part of `config_hash` (a changed tool
    needs a new gate run); a tooled agent with a manifest must not share a tool secret with a backend or an
    executor.
  - A tooled agent's action tools now require an `evidence` list of call ids (`call_id = "<run_id>:<n>"`); an
    empty or foreign list ends the run `NEEDS_PERSON uncited`, and an input the contract flags `identifier: true`
    (new schema keyword, string properties only) that is not found in the cited results or the incident ends it
    `ungrounded`. `evals.gate` ignores `evidence`. A tool's exception is now a result (`ERROR: ...`) and the third
    one in a run ends it `tool_error`; a run whose cost reaches `max_run_usd` ends `run_budget`.
  - New tick step `purge_evidence` (daily). New `hadavin_sdk.sources` (four read-source interfaces, the neutral
    `KubernetesSource`, the start-up scope probe) and `app.build(sources=)`: a source that fails its probe, or
    cannot be probed and has no `scope_inventory` reference, stops the process starting.
  - The no-redirect HTTP opener moved to `guard/http.py`. **`make`, `hosts` and `Deps` now live in
    `hadavin_sdk.backends.factory`** (`hadavin_sdk.backends` itself imports nothing): change
    `from hadavin_sdk.backends import make` to `from hadavin_sdk.backends.factory import make`.
  - Review round: a tool module's `READ_OPERATIONS` is now a mapping operation id -> `(METHOD, path regex)`, and
    `ToolContext.fetch` refuses a call that fits neither; the manifest gains `ports` (default 443, in-cluster
    set for plain http), `cluster_http` needs every host in-cluster, and a tool with `secret_names` needs a
    `scope_inventory` entry `tool:<name>`. `tool_timeout_s` is one deadline for the whole tool call. Tool results
    that failed are stored with `error = true` (in the evidence migration) and cannot be cited. Literal
    placeholder-shaped text in a document or tool result is escaped (`‹IPV4_2›`) before redaction. The ARN pattern
    stops at `?`, `&` and `#`; the stored map drops any original that holds secret-shaped text. Redaction maps of
    runs that have not ended are kept until the 400-day ceiling (`purge_redaction_maps(..., keep_open=)`).
- **K3 pilot build path (levels, shadow cut-off, fail-closed loading).** Action contracts change shape:
  `executor.system` moves to a contract field `target_system`, and `executor` is now a tagged union
  (`kind: none | manual | http`). Edit every contract: move `system:` out of `executor:` to `target_system:` beside
  it. `chain_id` and `verify_check` may be omitted for `none`.
  - **`config_hash` changes once** (the contract dump changed): every agent needs ONE new gate run
    (`hadavin-sdk gate <agent>`). A level flip (`levels`) never changes the hash.
  - **A tooled agent (`tools_allowed` not empty) now needs a gate run with `--k 3` that passed pass^3**; a k = 1
    green record no longer qualifies it. Non-tooled agents are unchanged.
  - New optional agent fields `levels` (per action: `shadow` or `suggest`; `act` is refused until Phase 4) and
    `max_run_usd`. In `pilot` and `prod` both are required and `levels` must list every `scope_allowed` action;
    `suggest` is refused there until K6 and K8, an `http` contract and a `read_only` contract are refused, and so are
    `confidential` and `restricted` agents. See `deferred.py` for every refusal and the phase it arrives in.
  - In `pilot` and `prod`, `build` makes no `Executor` and reads no client-system secret. `build` takes a new
    `llm=` override.
  - Shadow and abstain cards are posted through the new `Channel.post_card` (and `Channel.max_card_chars`); a
    custom channel kind must implement both. `AuditEvent` gains `caught_by`.
  - New file `replay-records.jsonl` (reader only for now; the writer arrives with K1b-full). A tooled agent at
    `suggest` is refused at load without a green record in it for the current config hash, model and prompt.
    **Shadow qualification through the gate is a start-up gate, not accuracy evidence.**
- **K1b-lite replay check (report only).** New commands `hadavin-sdk replay AGENT --bundles D --cause-list D
  --max-usd X --out OUT [--k K]` and `hadavin-sdk score --outputs OUT --answers F --cause-list D --bundles D`.
  Neither gives a met / not met verdict; a replay pass is not evidence of live accuracy.
  - New optional `k1b:` section in `config.yaml` (`max_steps` 12, `max_tool_calls` 20, `case_timeout_s` 300).
    It does not change `config_hash`, so no agent needs a new gate run.
  - `replay` and `score` write `k1b` audit events (`replay_run`, `hard_check_a`, `hard_check_b`, `score_run`) to the
    configured `local_dir` or `chain` audit. A `chain` over the memory store warns that events are lost at exit.
  - `replay` refuses a non-empty `OUT`, a route with a zero price (unless the llm kind is `fake`) and a bundle with
    any timestamp after the alert time. A run that dies half-way leaves `FAILED.txt`; delete the folder to re-run.
  - **Exit codes of every command changed for crashes.** `main` now returns 2 for a `ConfigError` (message on
    stderr) and 3 for any other uncaught error, instead of a Python traceback with exit 1. Exit 1 keeps its meaning
    (gate red, audit not intact, replay aborted or cost cap reached).
- **K1b-lite masks client data before the model.** Until now `replay` ran only the injection screen: the alert,
  every tool result and the runbooks went to the model raw. Every text value of a case bundle is now masked with
  the studio redactor (`guard.redact.redact_many`, one placeholder namespace per case, so one value is one
  placeholder everywhere) before the model or the injection screen sees it. The placeholder map lives in memory
  only: it is never written to the outputs or the audit sink, and never logged. Evidence IDs, file names, the
  the values of the `service`, `kind` and `fault_type` keys (the Cause List vocabulary), exact timestamps and numbers
  are left alone; dict keys are masked too. Names, queries and labels are masked in the snapshot and in what the model
  sees alike, so citations and queries still resolve. New `k1b.redact` (default `true`); `false` is refused unless `replay` gets
  `--i-know-data-is-already-masked`, and the run records `redaction.mode: off_acknowledged`. `run.json` records the
  scheme and the number of distinct values masked per class (no values); both reports print them. **What the
  redactor does NOT catch:** names in free text, customer or project names, ticket numbers, unusual formats,
  most company or cloud host names (it masks `.local`-style hosts, not `api.client-bank.com` or `*.rds.amazonaws.com`),
  and the values of the `service`, `kind` and `fault_type` keys. It is a strong first filter, not proof that no client data leaves; the
  reports say so under "What the numbers cannot say". Re-run `replay` for earlier runs: they sent data unmasked.
- **K1b-lite: a `not_sure` answer may omit `causes`.** A real Sonnet 5.5 smoke run abstained correctly on a
  no_evidence incident with `{"not_sure": true, "reason": "..."}` and the strict parser called it unreadable (a Miss).
  `causes` may now be omitted (or empty) only when `not_sure` is true; every other strictness is unchanged (both
  forms, no form, wrong types, extra keys, fenced or surrounded text, duplicate keys, NaN). The `submit_diagnosis`
  schema no longer lists `causes` as required and its description, and the system prompt, say so. Case files now
  record `answered_via` (`tool` or `text`), and `run.json`, `replay-report.md` and `score-report.md` list the case
  ids that were unreadable, errored, timed out, capped or converted for uncited evidence (ids only, never answers).
  Re-run `replay` for runs made before this change: their saved unreadable answers are not re-parsed.
- **`tick` now matches the v5 contract.** Exit code **4** (was 3) when the store is unreachable, for both
  `run_tick` and the CLI; 3 stays the wrapper code for any other uncaught error. The heartbeat summary line is no
  longer a step: it is logged after the steps, writes no `tick_state` row and cannot change the exit code (K7 sends
  the external heartbeat is PENDING K7: nothing sends it today). **A scheduler that treated exit 3 as "store down" must now watch 4.** `tick` also returns 4 when the store stops answering during the steps (it re-probes after a step failed); 1 stays for a failed step with a reachable store. Exit 4 is only for connection failures: a store that answers with a missing table or grant exits 2 ("run migrate, check grants") for `tick`, `limits stop` and `limits reset`. `limits stop` and `limits reset` with the store unreachable now exit 4 (was 2) and print "kill switch NOT set" or "NOT reset" with "Nothing was changed".
- **K1b-lite gap fixes.**
  - SDK version is now `0.1.0` (`pyproject.toml` and `hadavin_sdk.__version__`, pyproject and `__init__` kept equal by a test). Replay and
    score reports print it; `0.0.0` still prints "unreleased build".
  - `replay`: every provider call has a wall-clock bound (the time left in `k1b.case_timeout_s`, at least 1 s),
    for every llm kind: the call runs in a worker thread and, on expiry, the case ends as `timeout` with stop
    reason `call_timeout`, the worst-case cost of that call is charged to `--max-usd`, and the whole run stops
    as `aborted` (exit 1), so at most one abandoned call exists per invocation. The abandoned call is not killed;
    it can outlive the run (a slow trickle defeats a socket timeout). Next step, only if a client run ever shows a hung call: run each case in a child process that can be killed. The per-socket timeout is already
    `call_timeout_s` on each llm kind's settings (`backends.llm`). Ctrl-C during a replay now also leaves `FAILED.txt`.
  - `score` audit order changed: `score_report` `started` (intent, before anything is written), the report file,
    then `score_report` `written` and one `score_run` per run (these append like any K1b event: a failed append exits 3 with the report on disk). A report that cannot be written
    leaves `started` then `failed` (with the error class) and no `score_run`; the command exits 3.
- **Audit and lock-in guard gaps.**
  - Anchors and checkpoint rows carry a non-secret `key_label` (new optional `key_label` setting on every
    signer kind; default `pk:` plus a fingerprint of the public key), never the configured `key_id`. An alias and
    an ARN of one key give one label and no account id reaches the anchor bucket. **Anchor bodies written by
    the previous build hold `key_id`; the offline verifier accepts them but never compares or prints it (it can be an ARN).** A custom anchor kind must
    now accept `alg` and `key_label` keywords (one taking `alg`/`key_id` is treated as a legacy 3-argument anchor
    and warns).
  - `verify_anchor_bodies(bodies, public_key, names=None, assume_alg=None)`: `names` binds each object name to
    the seq inside it; `assume_alg` verifies pre-`alg` anchors by signature (a wrong guess fails every
    signature). The immutable objects are not rewritten.
  - **Upgrade step: run `hadavin-sdk migrate`** (0004 adds `alg` and `key_label` to `audit_checkpoints`; old rows
    are NULL, meaning "not recorded": verify then uses the configured signer's scheme). A runtime started before migrating refuses with the "run migrate" hint.
  - Lock-in guard: the literal scan now also covers bytes constants, constant `+` joins and f-strings (it found
    `".meta" + ".json"` written to dodge it; that suffix is now a plain literal and the model-id pattern
    matches `meta.llama` only); every `neutral` kind must show no vendor SDK import (S3 anchor excepted, with
    `endpoint_url`) and a `Neutral protocol:` line in its module docstring.
  - Vault licence check, live 2026-11-01: HashiCorp Vault 1.15 and later is BSL 1.1 (change date four years after
    each release, then MPL-2.0); OpenBao is MPL-2.0 under the Linux Foundation and states API compatibility with
    Vault 1.14 (Transit has extras of its own). The `vault` and `vault_transit` kinds stay `neutral` because they
    speak the Vault-compatible HTTP API that OpenBao also serves, but neither has been run against OpenBao by us
    (they stay `unverified`); the docstrings say so.
- **Lock-in guard.** `tests/test_lockin_guard.py` fails CI when a vendor SDK is imported outside its kind
  module, a capability lacks a neutral prod kind (`Entry.neutral`) and two prod kinds without a dated
  exception, or core logic names a vendor.
  - Anchor objects now carry `alg` and `key_id`, so `chain.verify_anchor_bodies(bodies, public_key)` checks
    them with nothing else. A custom anchor kind's `put` must accept `alg` and `key_id` keywords. Anchors
    written before this change have no body fields and verify only through `verify()`.
- **P5/P6 follow-ups.**
  - **Re-gate every agent once.** `golden_sha256` now covers the input documents the golden cases point at,
    so a changed document un-qualifies.
  - `config_hash` now also holds `eval_threshold` (when not 1.0), `max_completion_tokens` and the Foundry
    `resource`.
  - `eval_threshold: 0` is refused.
  - A `bedrock_guardrail` must name a published `guardrail_version` (digits; `DRAFT` can change).
  - A detector `threshold: 0` is refused (it flagged every clean text).
  - A `bedrock_guardrail` needs `bedrock:GetGuardrail`. Start-up refuses a guardrail with no PROMPT_ATTACK
    input filter switched on.
  - Moving model aliases are refused per kind:
    - OpenAI names with no dated snapshot (`gpt-4o`, `o3`);
    - untagged names on a local OpenAI-compatible server (Ollama: `llama3` means `:latest`);
    - Gemini names with no version (`gemini-pro`);
    - Bedrock names without a provider prefix.
- **Rewrite config.yaml to config v2** (slice 2 P1b). `environment: dev|pilot|prod` is required. Each backend
  is `backends.<capability>: {kind: <name>, ...settings}`. The old top-level keys are refused with a message
  naming the new place: `audit_dir` -> `backends.audit.dir`, `recorded_dir` -> `backends.llm.recorded_dir`,
  `detector_threshold` -> `backends.detector: [{kind: regex, threshold}]`, `region` -> each AWS kind's
  `region`, `slack` -> `backends.channel`. Start-up now refuses dev-only kinds outside `dev`, a secret name used
  by both a backend and an action, and any secret that cannot be read.
- `app.build(config_dir, agents, *, secrets=None, ...)`: `secrets` is now a keyword; `make_llm`,
  `make_detector` and `make_channel` are gone (backends are built from the table in `hadavin_sdk.backends`).
- **Re-gate every agent once** (slice 2 P1a). `config_hash` now hashes with `exclude_defaults` and includes the
  llm backend kind, so every stored green gate run stops matching. Run `hadavin-sdk gate <agent>` for each agent
  before starting the runtime; until then start-up raises `Unqualified`. After this one re-gate, adding an optional
  field with a default no longer un-qualifies agents, and swapping the llm backend does.


### Changed (promoted controls, from a demo's reviews; PR #50)
- **`approvals/gate.py`:** no behaviour change. The unused helpers `_views` and `_rendered` (secret views ported with the gate in slice 2 that no code ever called) are deleted; the live secret check of approval and channel text is `approvals.channel.clean` (neutralise, then one redaction last), whose scans use the fold described below.
- **Behaviour change in `guard/redact.py` (interim, fail closed):** a line with non-ASCII text is scanned FIRST in its FOLDED form (look-alike
  letters, other scripts' digits, invisible characters), before the direct patterns run. On a hit the WHOLE LINE is replaced by the fixed note
  `[line withheld: look-alike text hid a protected value]` plus the placeholders of the hits, and the folded text is NEVER emitted (the fold
  turns full-width and look-alike characters into live ASCII, and `approvals.channel.clean` redacts LAST, after the text was neutralised: an
  emitted folded line could carry a live mention, link, command or fence to a person; fixed in the redactor, so every caller is safe). Running
  the fold first also stops a direct pass from masking only the ASCII tail of a value (`al<look-alike>ce@example.com` kept its head). Masking
  inside the original line is done only when the fold does nothing but ordinary things (see "Review fixes after the first independent review" below); an attack-shaped
  line is still replaced whole, and that replaced line is LOSSY: all of the line except the placeholders is dropped. **`redact.py` still does not fold in general:** a line without non-ASCII text goes through the direct patterns only. What the
  redactor still does not catch: a value split by a character that changes the fold's shape (for example digits spelled as words),
  look-alike letters in a non-folded script, and a secret no pattern knows. A value hidden behind look-alike letters is still withheld with its whole line (the span-mapped mask is done for ordinary text only; see below).
- **`Limits.stop(by, source="cli")` / `Limits.reset(by, source="cli")` and `Limits.is_stopped()`** (small core change; PR #48 also edits
  `limits.py`: rebase it after this PR). A gate flip is audited with `source="gate"`, not as a CLI action. `StopGate` checks at
  construction that its `Limits` has the `source` parameter and raises `TypeError` otherwise: copy `stop_gate.py` together with `limits.py`
  (or pin core at PR #50 or later).
- **Review fixes (PR #50):** `check_text` refuses more than 10000 protected values or 1000 allowed references (`ValueError`), and a protected value or allowed reference longer than 4096 characters (`MAX_VALUE_LEN`; `text_leaks` now returns True, never raises, for input `check_text` refuses); `tools/mutation_runner.py` snapshots the tree once, passes an environment allowlist to its children and can pin a mutant to one test (`only_test`); the residual of the digit check is listed only in `docs/promoted-controls.md`. The mutant run (`tests/promoted_mutants.py`) is a manual gate on Python 3.13 before promotion, not a CI job (see the same file).
- **Review fixes after the first independent review of PR #50 (ledger BL-core-pr50-r2-001 to 006).** Each item has a test in `tests/test_pr50_fix_batch.py` that fails on the reviewed head 2e8a28c.
  - **`guard/redact.py`, fewer legitimate lines withheld.** The fold scan used to replace the WHOLE line whenever the folded text matched something the line did not: an accented address (`josé@exemple.fr`) inside a Russian, Arabic or Japanese sentence lost the sentence. Now, if the fold only (a) turns another script's decimal digits into ASCII digits, (b) strips an accent or mark from a letter, (c) turns a Unicode space into a space, (d) turns an ordinary look-alike letter of another script into an ASCII letter (Cyrillic, Arabic, kana words), or (e) drops marks and invisible characters, ONLY the matched value is replaced by its placeholder, in the line as written (never folded text; up to 4 rounds; `redact().mapping` still holds the folded value). The whole line is still withheld when a masked value itself contains a look-alike letter (a value hidden behind look-alikes), or when the line holds a full-width or compatibility character (the fold would make it live ASCII). Measured on the benign corpus in `tests/test_pr50_fix_batch.py` (22 lines: accented addresses in 12 sentences of Latin, Arabic, Devanagari, Thai, Cyrillic and CJK text, and 10 lines with no value): false withhold 0 of 22 (reviewed head: 12 of 22 withheld, all the 12 address lines). Residual (fail closed, not fixed): a value written WITH a look-alike letter, or glued to a look-alike word with no space, still costs the whole line; a line with a full-width letter next to a fold-only hit is withheld.
  - **`guard/redact.py`, bounded work.** The fold scan ran the whole pattern table twice per non-ASCII line. It now makes one pass of each pattern over the text and one over its folded form, counts matches per line, and runs the exact per-line check only on lines whose folded form holds a match the line does not (130,000 lines of `é` took 8.3 s, now 3.1 s, against 0.9 s for the same ASCII text; one laptop, one run, so a ratio rather than a promise: `test_130k_short_non_ascii_lines_cost_a_small_multiple_of_ascii_lines`). Copies are counted, not compared as a set: a look-alike copy of a value that also stands in clear is now a hit. The scan checks `defaults.REDACT_BUDGET_S` inside its passes and per suspect line and raises `runmap.InputTooLarge` when it is spent (so `redact()` can now raise it for a hostile text; `redact_text` already treated it as a refusal).
  - **`audit/capped.py`.** `sink_append` redacts and clips the object reference or key (128 characters), the error code (96), the kind and the bucket (64) before they reach the append-only audit; the tenant is clipped AFTER escaping (at most 64 characters; it could reach 192). The counters are keyed by bucket and the two latest buckets are kept, so a late event of the previous bucket (midnight, two threads) no longer resets the counter (it allowed more than `cap` rows). A non-string tenant is a name (it raised `TypeError`).
  - **`runtime/rowstore.py`.** New `max_key_chars` (default 256) and `max_row_bytes` (default 65,536, `None` opts out); `copy_row(o, max_bytes=None)`. A row over 64 KiB or a longer key is a `ValueError` before anything is audited. Callers that stored larger rows set `max_row_bytes` explicitly.
  - **`runtime/stop_gate.py`.** `StopGate()` and `StopGate(None)` raise `ValueError` at construction; pass a `Limits` (its audit is the audit), or `unaudited=True` to say that the gate writes no audit row (the check is at start-up, not inside `engage`, so an emergency stop never fails on a configuration error). `restore(False)` raises `StopGateBusy` while this process holds an engage or a sweep runs (only the audited `release` clears one), and every `restore` bumps the generation so a release in flight cannot undo `restore(True)`. A principal that is not a plain label is written as `id:` plus 32 hex digits of an HMAC-SHA256 under the deployment's `label_key` (batch 3; a random per-process key, logged once, when none is given; it was `?`); text with a control character is still `?`.
  - **Smaller fixes.** `guard/http.py`: the loopback skip connects to the NORMALISED host it checked. `testing/mutation.py`: `first_failure_junit` refuses a DOCTYPE or ENTITY declaration (`ValueError`) before parsing; `Mutant.pinned` of `tools/mutation_runner.py` now reaches `judge`, so `OTHER_TEST` can fire. `testing/contracts.py`: `check_rowstore_contract` also checks `update_audited` and `delete_audited` when the store has them. `runtime/config_view.py`: the dead `frozenset` entry of the leaf table is gone and the depth message says "levels below its top value" (65 levels were accepted). `guard/egress_text.py`: `text_leaks` fails closed (True) on ANY exception of the check. The golden table of the digit counts lost its unused "old" column. `docs/promoted-controls.md`: the guarantee sentence now states its own limit (digits hidden as letters pass: the residual list). The fold drops unassigned (Cn) characters according to the Python build's Unicode version (stated in `guard/textnorm.py` and the docs; the generated table is pinned, the Cn set is not, and the mutation gate runs on one Python version).
- **Review fixes after the second independent review of PR #50 (ledger BL-core-pr50-r2-007 to 023).** Tests: `tests/test_pr50_fix_batch2.py`; the ones that fail on fa184e7 are marked FAIL-BEFORE in that file.
  - **`runtime/stop_gate.py`.** `restore(False)` over a stop that `restore(True)` set no longer clears it silently. It now needs a gate with a `Limits` (an unaudited gate raises `StopGateBusy`), a durable switch that reads OFF, and an audit row (`operation="restore"`, written first; if the write fails the flag stays on). Only `restore(True)` bumps the generation, so an operator restore of "off" no longer makes a release in flight raise `StopGateBusy` when no engage ran; the dead sweep condition is gone. A principal label that starts with `id:` is hashed like any odd label (nobody can impersonate a hashed identity), and the hash is now 32 hex digits of an HMAC-SHA256 under a per-process random salt, so a name or e-mail cannot be recovered by hashing a dictionary; the price is that the same principal gets another label after a restart.
  - **`audit/capped.py`.** `_clip` replaces control characters (C0, C1, line and paragraph separators) by spaces, redacts only the first `limit + 1024` characters (it used to redact the whole outsider value: `"é\n"` x 500,000 cost seconds per row), then clips; a value the redactor refuses is written `(details withheld; len=N; sha8=...)` (the first 8 hex digits of the SHA-256 of the raw text, no content) instead of one fixed note for every hostile value. The tenant shown in the audit is redacted BEFORE the clip to 64 (a secret straddling character 64 used to leave a fragment); the counter key is the first 64 characters as before (names equal there share a counter) and is never audited. The drop-the-partial-token step the review asked for is not built: the cut lies 1,024 characters beyond the clip, so nothing past the limit is ever shown and the step could not change any output. Buckets: the two GREATEST are kept (not the last two), a bucket older than both is suppressed and never evicts a newer one (`d1, d2, d3, d1` and `B1, B2, B0, B1` cannot reset a counter), `max_keys` counts the counters of ONE bucket so a key flood on day N cannot send day N+1 tenants to the overflow counter, and a long bucket is clipped in the key. `suppressed()` documents this.
  - **`guard/redact.py`.** In-place masking is covered by cases for combining marks inside and around a value, zero-width spaces inside and at the edges, no-break spaces, a Kelvin sign inside a value (masked whole), two values on one line, three rounds, four rounds that never converge (the line is withheld) and a multi-line value that starts on an ASCII line (the lines it covers are replaced together by the note and the placeholders). One deadline now covers `redact()` and every view `redact_text` tries (it was 6 s per view), and it is checked inside the scan, each round and the alignment. A line costs one pattern sweep per round plus the final no-change sweep (it was about six). Signs that fold to several ASCII characters (an ellipsis, TM, a ligature, a superscript digit) are masked AROUND, in place; inside a masked value they still withhold the line. Withhold rate on the 28 lines of the two corpora (the 22 of the first review plus 6 lines with signs): 1 of 28 at that time, the one-half sign (batch 3 maps the fraction slash and masks around it: 0 of 28). **Cost, measured on one laptop:** about 1 ms per accented-address line, 2,000 lines 2.0 s; a text of about 6,000 such lines reaches the 6 s budget and is REFUSED (`InputTooLarge`, nothing shown); 10,000 and 30,000 lines were refused at 6.0 s. The refusal is bounded and fail-closed, not an availability fix: split larger logs.
  - **`runtime/rowstore.py`.** The size of a row is counted WHILE it is encoded, so an oversized row is refused after at most `max_row_bytes` of encoding work; the count is ASCII-escaped JSON bytes (a non-ASCII character counts 6), not UTF-8 bytes. New `max_total_bytes` (default 64 MiB of the same, `None` opts out): a write that would pass it raises `StoreFull`.
  - **`guard/http.py`.** An explicit loopback name connects to the literal `127.0.0.1` (or `::1`), never to the name, so no resolver answer can send it elsewhere.
  - **Test tooling.** `tools/mutation_runner.py` marks a mutant ERROR (`JUNIT REFUSED`) when its JUnit file is refused instead of aborting the run; `first_failure_junit` also refuses a text over `MAX_JUNIT_CHARS` (8,000,000).
  - **Pins.** Batch 2 pinned `guard/redact.py` and `limits.py`; batch 3 reversed that (see the re-copy list above: copy the core package at one commit). The `text_leaks` docstring is repaired. The Cn (unassigned) set of `fold` still depends on the Python build's Unicode version (documented, not pinned).
- **Review fixes after the third independent review of PR #50 (ledger BL-core-pr50-r2-024, BL-core-pr50-r3-001 to 020).** Tests: `tests/test_pr50_fix_batch3.py`.
  - **`guard/redact.py`.** A bank word anywhere in the FOLDED text now counts as bank context for the fold treatment, so an account number below a keyword spelled with an accent or full-width letters is masked (`BSB 062-000` then `accóunt number 12345678` left the number in clear). The whole-text scan records which patterns matched each line, and a suspect line is masked with only those patterns (plus `BANKACCT` and `BANKCODE`, which depend on context). The time budget is the CPU time of the calling thread (`time.thread_time`), no longer the wall clock, so load from other threads cannot change what is accepted. A one-half sign is masked around (its fraction slash is read as `/`); a full-width slash is still an attack. **Cost, one laptop, one run, CPU budget 6 s:** accented-address lines 2,000: 1.16 s before, 0.90 s after; 10,000: 6.98 s before (budget edge), 5.18 s after; 30,000: refused both times (`InputTooLarge`). 10,000 JSON lines with a name field: 2.09 s before, 2.29 s after (no gain). The gain is about a quarter, not the order of magnitude the review expected: the two whole-text sweeps and `fold()` now dominate. Larger logs must still be split; this is the stated limit, owner: the lead (a cheaper first pass is the next lever).
  - **`audit/capped.py`.** A suppressed event does no redaction at all (the keys are raw, control-stripped, 64 characters; the tenant, kind and bucket are redacted only when a row or a marker is written), so unique 1,088-character tenants cost the same as short ones. The head that is redacted is `limit + 4096` characters; a value longer than that whose head ends inside a word is written `(details withheld; len=N; sha8=...)` (a `https://user:` plus 5,000-character password cannot show its head). `sha8` is a keyed hash (`label_key`); no cache keeps a raw head. The marker passes the clipped bucket. Control, format and separator characters (Cc, Cf, Zl, Zp: bidi overrides, zero-width characters) become spaces. A stale bucket writes ONE `audit_stale_bucket` row per bucket (at most 64), kinds are dropped with their bucket, and `audit_suppressed` / `audit_stale_bucket` are refused as caller kinds (`ValueError`). Buckets still compare as text (documented: ISO days sort right; zero-pad numbers); owner: the callers, none in `src`.
  - **`runtime/stop_gate.py`, `limits.py`.** `release` is a compare-and-set: the gate remembers the (by, ts) of the stop it wrote and `Limits.reset(expect=...)` clears the switch only if it is still that record, read again after the audit intent and just before the write (`SwitchChanged` -> `StopGateBusy`, outcome row `reset_refused`); a stop by an operator or another gate in between is kept. The store has no atomic compare-and-set, so a stop landing between that last read and the write is not seen; owner: the store kind (add a conditional write). Labels use `label_key` (new argument of `StopGate`, `CappedAudit`, `sink_append`; `audit/labelkey.py`): same key, same label in every process; without a key a random per-process key is used and logged once. Plain e-mail principals are stored as written (they are personal data; use a login name). `restore(False)` needs `by` (the principal of its audit rows), reads the durable switch fresh (not through `cache_ttl`), and writes an intent row, then `restore_done` or `restore_refused` (no dangling intent). `Limits.switch()` is new.
  - **`runtime/rowstore.py`.** A row is walked first with a lower-bound size count (a string costs its length, a key its length), so an oversized row is refused after about `max_row_bytes` of work and a 5 MB string is never encoded; dict keys count in the store total; a `None` limit needs `allow_unbounded=True`; `check_rowstore_contract(make, make_small=...)` checks that a full store refuses with `StoreFull` before auditing.
  - **`guard/http.py`.** The name `localhost` is tried as `127.0.0.1` and then `::1`; an explicit address is used alone.
  - **Test tooling.** `Mutant.crash_type` is required with `allow_crash` and the exception class name must appear in the first `E` line, or the row is not good; `crash_markers` reach `judge`; a truncated JUnit file (`ET.ParseError`) marks that mutant ERROR; the JUnit size is checked by `stat` before it is read; `taskkill` is run by its full path under `%SystemRoot%\System32`.
  - **Pin rule.** One rule: files in the manifest are copied byte for byte; `redact.py` and `limits.py` are not (see the re-copy list). Docstring-only edits still change a pinned file's hash; that cannot be avoided without a normalised-hash scheme (owner: the lead).
- **Static-analysis fixes (SonarCloud):** `guard/runmap.py` finds a half-written escape at the end of a text with `partial_escape_start` (linear; the old pattern with a repeated `%XX` group took time that grew with the square of the run: 79 s for 40000 groups) and `PARTIAL_ESCAPE` is gone (a private pattern plus the function replace it; `tools.py` uses the function). `guard/http.py` holds the cloud-metadata deny list as one documented table `METADATA_ENDPOINTS` (provider and reason per address), built from numbers, with the same six addresses and ranges as before; the notes in the table are vendor-neutral (the platform names are in comments), and the networks are built from numbers. Other changes in `guard/http.py` are NOT part of this PR: the 0.0.0.0/8 refusal, the local-use NAT64 prefix, refusing NAT64 by prefix and the stuck-lookup budget came with PR #42 (already on main).
- **Merge order and re-sync of the copies:** PR #49 (a downstream demo repo) and this PR both edit this Unreleased section and share
  `guard/textnorm.py`. Merge #50 first. Every repository that keeps a byte copy (the demos, #49) re-copies, in one commit:
  `guard/textnorm.py` (sha256 `fd9d0ffdbe7d480db29c9e47bb4be4025fbc19638bf83eef9e6d323483659b14`), `guard/egress_text.py` (sha256 `8ac034507995e3bbcae1b155162c26818c8608953e4cccb78aa59d4f5984ae98`; the digit counting changed in review rounds 4 to 6, a stale copy silently keeps the old counting), `runtime/stop_gate.py` (sha256 `864961b4525063024810bb92ad4178ddfe5647cfed184f97f0ca960327fbf770`; copy it with core's `limits.py` from the same core commit), the generated `guard/_confusables.py` (sha256 `41740c11734e2ec1e5a63f9325dffa04226c84f3b81b43c1b5c7e766f8a0ccfd`; `textnorm.py` imports it) and
  `tests/fixtures/textnorm_vectors.json` (sha256 `1a1944708f7d1737588d7b02666620ceb308b0fe4a71ce2a312c4dc29113d349`); the same hashes (all but `limits.py`, which other PRs also edit) are pinned in `tests/fixtures/textnorm_manifest.json`. The consumers are every repository with a `core_copies.json`. After the first independent review the pin covers ALL the files a demo may copy, not five: `runtime/rowstore.py` (sha256 `7ac72628eebc3c32df06e368941b179a5c3a144181f56e6cee9ba71f71a30734`), `runtime/config_view.py` (sha256 `31160290846c0397e59fc3760bc8816683d089cda6bb062cac6d0593c85014d7`), `audit/capped.py` (sha256 `60212bfdc0d2e799991a4991280900a7d8dc6e93c32717b2fd3917ef6cbe5170`), `testing/mutation.py` (sha256 `986b8dc8b27076676793fc953cb3c7e329ea08ae5f945b0f585a6ba242f8b3b4`), `testing/contracts.py` (sha256 `3e8939de7324e66249051b48775cb295badcbd5b42e7c86ac13d7a3af9d480b3`), `tools/mutation_runner.py` (sha256 `c32b92c69e9eec8fa5d362fd9d0d4505812b8c198ae0406834cce8403fa97d24`) (all in `tests/fixtures/textnorm_manifest.json`; `capped.py` imports `guard.runmap` and `models`, `rowstore.py`, `config_view.py` and `testing/*` are stdlib only; `tools/mutation_runner.py` imports `hadavin_sdk.testing.mutation`: copy those two together). `guard/redact.py` and `limits.py` are NOT byte-copy files and are not in the manifest (rule fixed in batch 3): `redact.py` needs `hadavin_sdk.defaults`, `guard.runmap` and `guard.textnorm`, and `limits.py` needs the store, audit and registry kinds, so a demo that uses them copies the CORE PACKAGE at one commit (the PR #50 merge or later), never the two files; the core test suite, not a copy hash, guards them. Every file in `tests/fixtures/textnorm_manifest.json` is stdlib-only or needs only the files named next to it.
  Then update the repository's `core_copies.json` rows (`core_path`, `core_sha256`, `import_rewrite`: `textnorm.py` imports
  `hadavin_sdk.guard._confusables`, `egress_text.py` imports `hadavin_sdk.guard.textnorm`) and adopt the new names: `safe_equal(a, b)` ->
  `allow_equal(a, b) is AllowVerdict.EQUAL` (`VARIANT` and `LOOKALIKE` refuse; `LOOKALIKE` is the audit alarm), `confusable_not_equal` is
  gone, `mixed_script` -> `has_mixed_script`, DENY comparisons -> `same_person`, `squeeze(raw, loose=...)` is keyword-only,
  `check_text(..., policy=)` is required (`LeakPolicy.payments()` / `.general()`, config sections need `profile:`), `runtime/control.py`
  is gone (use `StopGate`; handle `StopGateBusy`). For PR #49 in short: `identity_text` and `reply_check` also drop unassigned code points
  (Cn), and `identity_key(lookalikes="refuse")` also refuses `has_mixed_script(raw)`.

### Added (promoted controls; vendor-neutral)
Call sites in `src`: `guard/redact.py` (the interim fold), `limits.py` (`source`, `is_stopped`). The other
modules below have no call site in this repository yet.
- `guard/textnorm.py` (+ generated `guard/_confusables.py`, `tools/gen_confusables.py`, vendored `tools/data/confusables.txt`): the shared
  text fold of `egress_text` and `guard/redact.py`. The fold makes look-alike text EQUAL, for DENY decisions only (`same_person`,
  blocklists, leak scans). `guard/redact.py` has its own first pass (see Changed) and `approvals/gate.py` keeps a separate invisible-
  character table for URL parsing, so this is NOT "one fold everywhere" yet. For an ALLOW decision use `allow_equal(a, b)` (`EQUAL`
  only for identical strings; `VARIANT`, `LOOKALIKE` and `DIFFERENT` refuse; a plain `Enum` whose truth value raises, so `if
  allow_equal(a, b):` cannot be written by mistake). `names_equal` is a tolerant name comparison for prose, neither ALLOW nor DENY.
  `has_mixed_script` is the fail-closed backstop for look-alikes the table does not list; the micro and ohm signs are exempt. The
  look-alike table is generated from Unicode UTS #39 `confusables.txt` (MA, version 18.0.0, dated 2026-08-06, sha256 pinned in the
  generator) plus 16 listed letters and a rule for Latin small capitals. unicode.org serves only a "latest" URL, so the 763 KB data file
  is vendored (Unicode License v3, notice in the file and in the generated header) and a test regenerates the table offline. The
  small-capital rule reads character names from the running interpreter: the checked-in table was generated with Python 3.13.3 /
  Unicode 15.1.0 (`DATA_UNICODEDATA`), the regeneration test runs only on that Unicode version. Unassigned code points (Cn) are dropped
  (depends on the Python Unicode version). Tests pin the table, the manifest, a shared vector file and a property that every value is ASCII.
- `guard/egress_text.py`: output check for text a person reads. Digit budget: plain digit-like characters, the digits of set-aside amounts
  and references, and 5 per date ADD UP and must stay below 12 in every preset (the shortest card number has 13); a Luhn scan over the digit
  stream is kept as an independent card test (it cannot fire through `check_text` while the budgets hold). Capped set-aside tokens, protected values (also short and non-Latin ones; CJK and Thai match as substrings),
  typed `Violation`s, validated `LeakPolicy`. **No default policy**: `check_text(..., policy=LeakPolicy.payments())` (strict) or
  `LeakPolicy.general()` (ids and phone numbers up to 11 digits; a phone with 12 or more digits needs `allowed_patterns`). Defaults
  table: `docs/promoted-controls.md`. Distinct from `guard/redact.py` (the input mask). Digit-like letters: O o I l L S s B Z z G Q count;
  the lowercase i b g q are WEAK (prose such as "big issue") and count only in a token with 2 or more digits or strong letters, or inside a
  letters-only run with 6 strong letters, so `OlISBZGq` and `1b5i7g3q` (8 digit-like characters each) are refused by `payments()` (limit 8)
  and allowed by `general()` (8 is below 12, the same as plain 12345678). The count is MONOTONIC for appended "separator + token" and for inserting a separator or a filler token between tokens
  made only of strong letters (a seeded fuzz test of 20000+ cases pins both, with a sensitivity control); it is NOT monotonic for every edit
  (a letter glued to a word can change what the word is). It is the larger of a per-run reading and a whole-text reading. Ordinary words are free in a run that holds a digit:
  the strong letters of the first `max_free_words_run` (2) words, and at most `max_free_words` (2; `general()` 4) words in the whole text
  (new `LeakPolicy` fields), so `general()` lets `id is 12345678901`, `Total 12345678901` and `call 5551234567` through, while
  `4 Ib Ib Ib ...` and `Ob Ib Sb Zb Bb Lb 5` are refused (the earlier deferred word rule let a letter-encoded card
  through once one digit was appended). A letter glued to a digit (`12345678901s`) counts. In a text with a real digit, strong letters of
  every token made only of strong letters (even one: `I`) and of every token with 4 or more strong letters (`lllllx`, `OlSZBxxxxx`) are
  counted over the whole text, so `4 x lllll x lllll x lllll`, `4 I x I x I ...` and `4 OlSZBxxxxx OlSZBxxxxx OlSZBxxxxx` are refused.
  False refusals on prose with a digit (`Boss 1234`, `Oslo 1234`, `Bill 1234`, `BLISS GLOSS`) are by design and measured (docs); the free-word
  caps count pieces, not words. **What this does NOT
  stop:** see "Residual of the digit check" in `docs/promoted-controls.md`, the only list of residuals. The Luhn scan over the digit stream cannot fire through `check_text` while the
  budgets hold (it is an independent card test, tested directly). `has_mixed_script` treats a newline or tab as a word break; its script
  list is curated (see its docstring), not the full UTS #39 script-extension data.
- `runtime/config_view.py`: deep-frozen views (accident-proofing, not a sandbox), one immutable `ConfigView`, `ConfigHolder.swap(expect=)`,
  depth and node bounds on `freeze` and `thaw`.
- `runtime/stop_gate.py`: `StopGate`, the in-process effect barrier in front of the audited durable stop (`Limits.stop` / `Limits.reset`,
  one write path); `engage` flips the process flag first and fails closed when the store is down (and records the stop itself if
  `Limits.stop` raises); `release` is audit-first and cannot undo a newer `engage` (`StopGateBusy.durable` says whether the stop was
  written again); `aengage` / `aeffect` for asyncio. The old in-process `KillSwitch` class never shipped on `main`; there is no
  compatibility shim. The durable switch is ONE global row: a per-tenant stop is a tracked item.
- `runtime/rowstore.py`: copy-on-read row store (default limit 100000 rows, validated), validate then audit then write, `KeyPending` vs
  `DuplicateKey`.
- `audit/capped.py`: per-tenant capped audit for refused attempts (bounded tenants, kinds and keys, marker reserved under the lock,
  back-off) and an `AuditSink` adapter (`intent=True` for audit-before-write).
- `testing/mutation.py`, `testing/contracts.py`: mutation-kill judge and a row-store contract check (in the wheel). `tools/mutation_runner.py`
  (NOT in the wheel, nothing imports it): a small runner, paths confined to its tree, a timeout per pytest run. **Not included:** the
  outbox, signer and `Verifier` contracts and reservations belong to PR #49 and stage 2 (a tracked item); only `check_rowstore_contract`
  exists here.

### Added
- **G4 command withholding** (P5/P6 follow-ups). `channel.clean` now withholds every command a person could
  paste to change a system: `[command withheld (G4)]` stands in its place.
  - It covers AWS, gcloud/gsutil/bq, az, azcopy and PowerShell Az, kubectl/oc, helm, terraform/tofu/pulumi,
    ansible, systemctl, docker/podman, git, gh/glab, psql/mysql/mongosh/redis-cli, SQL write statements,
    `rm -rf` and `curl | sh`.
  - It fails closed: a CLI command passes only when it is positively read-only. The WARDEN port was dead code
    and AWS/K8s-only.
- `backends.hosts(entries)`: the hosts the configured kinds connect to, as a suggested egress list.
  The Postgres store is not in the list: its address sits inside the secret DSN, so add the database host by hand.
- **No single-dependency detector.** `llm_judge` runs on any llm kind, a local open-weights model on
  `openai_compat` included, so the cloud-neutral production detectors are `regex` + `llm_judge`.
  `bedrock_guardrail` is AWS-only. The approval-summary screen runs without the judge: no agent can be
  charged there, and the judge already screens the document and tool output.
- `hadavin-sdk tick` (slice 2 P7, v5 contract): one pass of isolated steps (`sweep`, `reconcile`, `stuck`,
  `checkpoint`; the summary line is logged after them and is not a step); a failing step is logged and recorded in `tick_state` and the others
  still run. Exit 0 ok, 1 a step failed, 2 config error, 4 store unreachable. Later steps are appended to
  `runtime.tick.STEPS`.
- `slack` approval channel (`backends.channel: {kind: slack, channel_id, signing_secret_name,
  bot_token_secret_name}`) and `approvals/receiver.py`: verified clicks are recorded only; `tick` runs the plan.
- Migration `0003_approvals_tick.sql`: `approval_requests.sent_at` and `channel_ref` (a failed send is resent
  by `tick`), one decision per approval step, an exact month spend counter, the kill switch row (a missing row
  reads as ON), `tick_state`.

- `postgres` store (`pip install hadavin-sdk[pg]`, slice 2 P2): `backends.store: {kind: postgres,
  dsn_secret_name, iam_auth, region}`; compare-and-set in SQL; RDS IAM login with `iam_auth: true`.
- `hadavin-sdk migrate [--runtime-role R]`: forward-only schema (`store/migrations/0001_core.sql`) applied under
  an advisory lock with the migration role's DSN from `HADAVIN_MIGRATE_DSN`. Rollback = restore the snapshot
  taken before migrating.
- `hadavin-sdk limits stop|reset` now works on a shared (postgres) store.
- llm kinds (slice 2 P5, all `slice2-unverified` until the P9 live run): `anthropic` with `platform: api |
  vertex | foundry` (extra `anthropic`), `bedrock` through Converse (extra `aws`), `openai_compat` (OpenAI,
  Groq, OpenRouter, a local Ollama) and `gemini` over stdlib HTTP. Each has `call_timeout_s` (60) and
  `max_attempts` (3): transient failures retry with exponential backoff and jitter, then `ProviderExhausted`.
  `output_schema` is a forced tool call. Model ids that are moving aliases (`sonnet`, `*-latest`) are refused.
  The llm `platform` and `base_url` are part of `config_hash`.

- Detector lists (slice 2 P6): `backends.detector` takes one or more entries (an `llm_judge` never alone); every
  entry runs and any flag flags the run (max score, the flagging names joined by `+`, the first flag's reason).
  New kinds, both `slice2-unverified`: `llm_judge` (`route`, `threshold` 0.7; a fixed prompt hashed into
  `config_hash`, its cost charged to the agent, qualified at its own rate by a non-empty `golden_dir/judge.jsonl`
  in the evals gate; that file is part of `golden_sha256`) and `bedrock_guardrail`
  (`guardrail_id`, `guardrail_version`, `region`; the PROMPT_ATTACK filter, extra `aws`).

### Changed
- P5/P6 follow-ups:
  - limits are checked again before a tool output is screened, so a reply that spent the budget never pays
    for a judge call;
  - redaction masks GCP `projects/<id>/...` paths and Azure `/subscriptions/<uuid>/...` ids, and ARNs with no
    account (`arn:aws:s3:::bucket`) or in the `aws-cn` and `aws-us-gov`
    partitions;
  - `llm/retry.py` names no vendor: each llm kind says which of its SDK's errors are retryable.
- Postgres TLS (slice 2 P7): `verify-full` by default for any non-local host, with the server's CA bundle
  from `sslrootcert` (a file) or `sslrootcert_secret_name` (a PEM in any secrets backend); an explicit weaker
  `sslmode` is a dev opt-down. With `iam_auth` only `verify-full`/`verify-ca`, and a runtime DSN with a
  password is refused.
- The runtime role gets SELECT, INSERT only on `approval_decisions`, `dead_letters`, `gate_decisions`.
- Gate decisions are written once per run; a run stuck in `RECEIVED` or `PLAN_READY` can go to `NEEDS_PERSON`.
- Approver ids carry the channel kind's name (`slack:<id>`, `fake:<id>`); request signing is the shared
  `approvals/hmac_v0.py`, not borrowed from Slack.
- `ProviderExhausted` from the model ends the run in `NEEDS_PERSON provider_exhausted` instead of escaping.
- A provider that refuses the request (`ProviderError`, e.g. a bad key) ends the run in
  `NEEDS_PERSON provider_error`; `ProviderExhausted` is now a `ProviderError`.
- `Reply.stop_reason` is one of `end_turn`, `tool_use`, `max_tokens`, `refusal` for the network kinds. A reply
  cut off at the output cap or declined ends the run in `NEEDS_PERSON llm_max_tokens` / `llm_refusal` instead
  of `NO_ACTION`; a cut-off reply's tool calls are dropped (their input may be incomplete).
- Store: `get_approval_decision`, `list_approvals`, `list_runs`, `touch`, `spend_totals`; `add_cost` raises
  `NotFound`; `Limits.blocked` no longer writes a zero-spend row.
- The executor calls a heartbeat before every HTTP attempt, so long retries do not look stuck.
- `Verdict.score` is bounded to 0..1; a detector failure is logged with its cause (still fails closed).

### Added (slice 2 P3, every kind `slice2-unverified` until the P9 live run)
- `backends.audit: {kind: chain}`: WARDEN's hash-chained, append-only audit in the store's database, signed
  checkpoints every `checkpoint_every` rows, and an optional `anchor: {kind: s3_object_lock, bucket, region}`
  (GOVERNANCE, 1 day by default). `hadavin-sdk audit verify` exits 0 intact, 1 not intact,
  2 refused (a memory store lives in one process), 3 unreadable.
- `backends.signer`: `none` (default), `ed25519_local`, `aws_kms`. Start-up signs a probe message.
- Environment table: prod refuses `ed25519_local` and a chain without an anchor that has `retention_ack: true`;
  COMPLIANCE mode only in prod with `retention_ack`.
- `store/migrations/0002_audit_chain.sql` (applied by `hadavin-sdk migrate` with the postgres store).

### Added (slice 2 P4, `slice2-unverified` until the P9 live run)
- `backends.secrets: {kind: aws_secrets_manager, region, ttl_s: 300}`: values cached for `ttl_s` (0 = no
  cache), a missing secret is a `ConfigError` at the start-up probe, values are never logged.
- `backends.secrets: {kind: env, prefix: HADAVIN_SECRET_}` (dev only): `fixture-token` reads
  `HADAVIN_SECRET_FIXTURE_TOKEN`.

### Added (slice 2 P4b, `slice2-unverified` until a live run): cloud-neutral secret stores
- `backends.secrets: {kind: vault, address, auth: token|approle|kubernetes, mount, path_prefix, field,
  namespace, ca_cert}`: HashiCorp Vault or OpenBao KV v2 over the standard library (no extra); TLS always
  verified, plain http only to this machine; a 403 signs in again once (approle, kubernetes).
- `backends.secrets: {kind: azure_key_vault, vault_url}` (`pip install hadavin-sdk[azure]`):
  `DefaultAzureCredential` (managed or workload identity).
- `backends.secrets: {kind: gcp_secret_manager, project_id}` (`pip install hadavin-sdk[gcp]`): Application
  Default Credentials (attached service account or workload identity), version `latest`.
- `backends.secrets: {kind: mounted_file, dir}`: one file per secret (Kubernetes Secret, CSI driver, External
  Secrets); paths stay inside the folder; on POSIX a world-readable file is refused (mount 0400/0440).
- Every remote kind shares one TTL cache with one refresh at a time; an empty value is refused at start-up.
  A missing `aws`/`azure`/`gcp` extra now always names the `pip install`.

### Upgrade steps (slice 2 P3b)
- **The anchor moved out of the audit entry.** `backends.audit: {kind: chain, anchor: {...}}` becomes
  `backends.audit: {kind: chain}` plus `backends.anchor: {kind: s3_object_lock, ...}` (default `none`).
- **Prod now refuses `signer: none` and `anchor: none`**, and `ed25519_local` with a key file (set
  `private_key_secret_name` instead). Config errors list every refusal at once.
- `migrate(dsn, password=...)` replaces `iam_auth=`/`region=`; build the helper with
  `hadavin_sdk.store.postgres.password_source(iam_auth, region)` (the CLI does).

### Added (slice 2 P3b, `slice2-unverified` until a live run): cloud-neutral audit
- `backends.anchor`: `s3_object_lock` (AWS S3, or MinIO / Ceph RGW through `endpoint_url`),
  `azure_immutable_blob` (version-level WORM; container checked at start-up), `gcs_retention_lock` (bucket
  retention policy checked; COMPLIANCE needs it locked). A put that finds the same bytes counts as anchored;
  different bytes are never overwritten.
- Signers: `vault_transit` (Vault / OpenBao Transit, ed25519, one pinned key version), `azure_key_vault_key`
  (ECDSA P-256 / ES256: Key Vault has no Ed25519), `gcp_kms` (EC_SIGN_ED25519). `ed25519_local` can read its
  key from any secrets kind (`private_key_secret_name`).
- `audit verify` also checks that each row's event id column matches its body.
- Cloud SDKs only in their kind modules: `audit/signer_aws.py`, `store/auth_aws.py` (RDS IAM).
- `mounted_file` also refuses group- or other-writable files and checks the opened file (no stat-then-read
  gap, `O_NOFOLLOW`); a Kubernetes JWT read error in `vault` is a `ConfigError`; the GCP secret fetch is bounded
  (5 s, no retry).
