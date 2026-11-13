# Changelog

## Unreleased

### Upgrade steps
- **Breaking: the first stage is now called `demo`; `environment: dev` is refused.** The stages are exactly `demo`, `pilot` and `prod`. A config that says `environment: dev` stops at start with "environment: dev was renamed to demo; write environment: demo (allowed values: demo, pilot, prod)" (shown beside any other problem found in the same file, and also for `Dev`, `DEV` and spellings with spaces, which are refused all the same); any other value (`Demo`, `staging`, `uat`, an empty value) is refused too, and values are never tidied or guessed. To upgrade: (1) change `environment:` in your config to `demo`; (2) if your code imports `backends.table.DEV_ONLY`, import `DEMO_ONLY` instead (same six kind pairs, no old name kept); (3) a project label such as `uat` is not a stage: map it to one stage in your own config. Also: the pilot and prod checks (`deferred.py`, `registry.py`, `app.py`) now ask one function, `hadavin_sdk.stages.is_live(environment)`, which treats anything that is not exactly `demo` as live; the prod-only rules (no local key file, a retention-agreed anchor) ask `hadavin_sdk.stages.is_prod(environment)`, which is true for `prod` and for any value that is not a stage. `STAGES`, `is_live` and `is_prod` live in the new leaf module `hadavin_sdk/stages.py`, not in `config.py`; the list `deferred.LIVE` is removed. The redactor no longer sweeps the words `demo` and `pilot` as a name (it already skipped `prod`), but a secret that reads `demo` is still swept. No stage is stored today; the first change that stores one must map an old `dev` value to `demo` on read, for display only and never for a guard decision, and add a test through that real read site.
- **Code-quality scanner fixes (SonarCloud, an automated code-quality scanner); one public name removed.** `guard.runmap.PARTIAL_ESCAPE` is gone. If your code imports it, call `guard.runmap.partial_escape_start(text, pos)` instead; it returns the start position as a number (or None), not a match object, so replace a `.search(...)` call and its `.start()` with it. The old pattern looked for a cut-off percent code such as `%C3` at the end of a text and slowed down sharply on a long run of them (about 65 s for 40,000 codes in a row, measured 2026-11-06); the new function takes milliseconds. `guard/http.py` now holds the cloud-metadata addresses that no tool may reach as one documented table `METADATA_ENDPOINTS` (the same six addresses as before; the other refused ranges are unchanged).
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
  - New `config.yaml` keys (defaults in `hadavin_sdk/defaults.py`; units as named): `tool_modules`, `tool_timeout_s` (seconds, 10; one deadline for a whole tool call), `tool_module_hashes` (SHA-256 of each tool module's source file; required in pilot and prod), `executor_timeout_s` (seconds, 10; demo executor), `scope_inventory` (`"<page>#<anchor> sha256:<64 hex>"`, format-checked only), `sources` (`kind`, `settings`, `token_secret_name`, `ca_file`; built and probed at start-up), `retention.tool_calls_days` 30, `retention.redaction_maps_days` 30, `retention.hold_labelled` true, `retention.held_maps_max_days` 400 (at most 400 and at least `redaction_maps_days`), `retention.purge_every_s` 86400, and an `evidence` block: `max_tool_errors` 3, `legacy_max_output_bytes` 20000, `fetch_ceiling_bytes` 2097152, `https_ports` [443], `cluster_ports` [80, 8080, 9090, 9093, 3100], `cluster_suffixes` ['.svc.cluster.local', '.svc'], `stored_kinds` (may narrow the default, never widen it; UUID is not stored), `max_tool_calls_per_run` 40, `max_tool_bytes_per_run` 262144, `max_abandoned_tool_threads` 8.
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
    `input.unresolved`) and for the demo executor (`Executor.execute(..., inputs_view=)`). Only identifier kinds are
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

### Added
- **Mode banner (promoted from a public demo).** The supported call for a screen is `App.mode_banner()`: it knows which parts code handed to `app.build` and which parts changed after the build, and a public demo built with fakes shows the unconfirmed banner. Underneath it is `hadavin_sdk.mode_banner.banner_or_unconfirmed(config, tool_specs=registry.tools, overridden=...)`, which never raises: when a banner cannot be built it logs one line (without the values) and returns the not-confirmed banner. `banner_from_config(config, names, words, *, tool_specs, overridden)` is the version that raises. `overridden` is a required keyword with no default: a list of names (empty `()` means "nothing was handed in") or `None` ("not known", which gives the unconfirmed banner; it is not the same as none). `tool_specs` is required with no default (forgetting it is a `TypeError`): pass the registry's `tools` (agent -> tool name -> spec); an empty mapping `{}` means "no tool specs", `None` means "not known".
  - The stage comes from `config.environment` and must be `demo`, `pilot` or `prod`. Every component of `config.backends.entries()` lands in one of three groups. Components that connect to nothing outside the process are listed in `NOTHING_CONNECTED` (no signer, no anchor, the built-in pattern detector): an explicit allow-list that is not derived from any other table, so a kind added to another table later is never hidden. Stand-ins are the kinds in the existing demo-only table (pretend services). Every other kind is a real service, including a kind the banner does not know: naming too much is the safe mistake.
  - Four more config fields are checked because the demo sentence says nothing is sent to real systems: a `systems` entry whose `base_url` is not this machine, any `egress_hosts` entry (a list, tuple, set, frozenset or dict keys view of host texts; an iterator, a generator, a `bytearray`, a bare string, bytes or a mapping is refused, because a config could hand back the same used-up iterator on the second call and the banner would then read "nothing real"; every list the banner reads is copied once and must be one of those types) that is not this machine, a `sources` entry whose endpoint is not this machine or cannot be worked out, and the hosts named by tool manifests. Each counts as one real service with the keys `external-systems`, `egress-hosts`, `read-sources` and `tool-hosts` (give them nicer names through `names`). A configured `tool_modules` entry that no manifest accounts for (no manifest names a host for that module, or `tool_specs` is `None`) counts as the key `tool-modules`. "This machine" means `localhost`, `127.0.0.1` or `::1` (the shared `guard.http.LOOPBACK`, other `127.x` addresses count as outside), a url is read in a way modelled on the tool client and at least as strict (a backslash, white space, a control or non-ASCII character, `%` or `@` count as leaving; a test pins this direction against the client's own refusals on 40 urls and 20 bare hosts).
  - The words: in the demo stage with nothing real connected the banner says the data is made up and lists the stand-ins in a loud second line; with a real service connected, in any stage, it names every real service and never says the data is made up; a pilot or live system with nothing real connected says so and still lists its stand-ins. A name for a service is plain words (single spaces, at most 40 characters) and may not hold a key word of the made-up claim: the English ones always, plus the sentences and the `reserved_words` of the `BannerWords` in use, so a reworded banner (another language) protects its own claim. A banner whose text or tag is longer than the page script shows (600 characters) is refused. One check before a banner leaves confirms that it names every real service, that a real or quiet banner never holds the made-up sentences, and that a demo banner names no real service.
  - The page script `templates/mode-banner/mode_banner.js` (with an optional `mode_banner.css`) paints the finished banner as plain text and never throws: a banner with an unknown tone, a tag or text that is not plain text (or holds only white space, or is longer than 600 characters counted as code points, as Python counts them), or a contradicting content is shown as "not confirmed". If painting fails part way, the element is unhidden, emptied (so the old words, which may claim made-up data, are gone first), its mode cleared, and the not-confirmed tone and words written, each step on its own; if the word write itself fails the element stays empty. If the emptying write fails, the earlier content may remain.
  - Objects handed to `app.build` (`tools=`, `sources=`, `channel=`, `llm=`, `detector=`, `secrets=`) replace what the config names, and the banner reads the config only, so it cannot judge them. `app.build` therefore records which of them were given (`App.overridden`, names only, now also `hold_run_ids`; an empty `tools={}` or `sources={}` counts as not given; `None` means unknown: an `App` made by hand, or one whose connected parts were replaced or copied after `build`, is compared against a fingerprint of the parts taken at the end of `build` and shows the unconfirmed banner; the parameters of `build` that connect nothing are on `NOT_CONNECTIVITY` with a reason each, and a test requires every `build` parameter to be on exactly one of the two lists) and `App.mode_banner()` passes them on as `overridden=`: the banner then says "These parts were supplied by code and are not checked here: <names>.", drops the made-up claim and the claim "No real service is connected", and has the tone `unconfirmed` (a banner that already lists a real service keeps the tone `real` and gets the sentence added). The unconfirmed text is exactly the not-confirmed words; the page builds the "supplied by code" note itself from the `overridden` names, as text. Blank means one set: `BLANK_RANGES` in Python equals the page's literal (a test compares them with node's `trim` and Python's `strip`). This is the cautious rule for now; relaxing it for objects that the stand-in check of the bind work package accepts waits until that package is merged.
  - Limits: "this machine" means the loopback names, and a loopback address can still be a port forward, a tunnel or a sidecar that leads off the machine, which the banner cannot see; `localhost` is trusted to resolve to the loopback address and that is not checked; the objects handed to `app.build` are invisible to the banner except by name (see above); tool code runs inside the process, is reviewed and is not sandboxed, so the banner counts the hosts a manifest names and cannot see what code does that the manifest does not say; the banner is worked out when it is called, so a page that cached an older banner keeps showing it; a pilot or live banner that says "No real service is connected." only reports what the config lists; the page script is tested in node with a stand-in page, not in a real browser. Tests: `tests/test_mode_banner.py` (CI sets `HADAVIN_REQUIRE_NODE=1` and checks `node --version`, so a runner without node fails instead of skipping); mutants: `python tests/banner_mutants.py` (a blocking CI step).
- **Demo-only folder guard (promoted from a public demo).** `python tools/demo_only_guard.py` fails if product code names the folder that holds everything made only for demos, holds a made-up record id (patterns are listed in `tools/demo_only_guard.toml`), or if that folder sits inside a product folder at any depth. It works from one list, `git ls-files` (files git does not ignore, added or not), over four product folders (`src`, `templates`, `tools`, `demos`), and checks file and folder names too. It matches the folder name in any case, with "-", "_" and a space as one separator, after Unicode NFKC normalisation (a full-width spelling is a hit); a few exact phrases, such as core's `DEMO_ONLY` table, are listed as not the folder, and a listed phrase counts only in its exact case and not beside a letter, digit, slash or dash. A loader file may name the folder once and is still checked for fake ids.
  - What a file's content decides: the file kind comes from the first bytes, not from the ending. The settings may allow only the endings `.png`, `.jpg`, `.jpeg`, `.gif`, `.ico`, `.pdf`, `.woff`, `.woff2`, `.webp`, `.ttf` and `.otf` to skip the text read, and each must start with its own mark (a webp is a RIFF file with `WEBP` at byte 8); `.svg` is text and is read as text, not listed; a file with such an ending and other content is a hit (`ending-does-not-match-content`) and is still searched. The settings file refuses an ending with no known mark. Any other file is read as text when it is valid UTF-8; a valid UTF-8 file that holds a NUL byte is read as text and its bytes are also searched for the name as UTF-16 and UTF-32 text; a file with an ending that is not on the settings list and that is not valid UTF-8 is a hit (`unreadable-file`) and is not searched. Only a file whose ending is on the settings list and that looks binary is searched as bytes (UTF-8, UTF-16 in both byte orders, UTF-32) instead of being read as text. These files are refused: `.pyc`, `.so`, `.zip`, `.whl`, `.gz`, `.tgz`, `.tar`, `.bz2`, `.xz` by ending, and a file whose first bytes are those of: zip, ELF, gzip, bzip2, xz, tar, compiled Python, Mach-O, fat Mach-O or Java class file, PE, RAR, DOS or Windows program (whatever its ending). The first 512 bytes decide (for PE the header offset may reach further); anything appended after a valid mark is not looked at, and an exempt file gets the same first-bytes check. Decision on a file made only of a RAR or MZ mark and NUL bytes (valid UTF-8, so it read as text): those two marks are kinds of their own (RAR; MZ followed only by NUL bytes up to byte 64), and a NUL byte alone is not a hit because UTF-16 and UTF-32 text holds NUL bytes and is searched. A bzip2 file needs a level from 1 to 9 and then a block or end-of-stream mark.
  - Entries that cannot be inspected are hits, never skips: a symlink under a product folder, a submodule (a git link, also when its folder is missing, unless listed as exempt), a pipe or socket, a file over the size cap (8 MiB, set in the settings), and a file or folder the system refuses to read, loops on or cannot enter, including a product folder, a loader file and the demo-only folder itself (only "no such file" counts as gone).
  - A repository that has the folder must carry the marker `tools/demo_only_guard.copy_run`, which must be an empty regular file, and its CI runs the copy run. An exempt file must be a regular file and is still subject to the size cap. `--require` stops a run when the folder is missing.
  - The copy run: `--without-folder -- <pytest arguments>` (or `--without-folder-if-present`) copies exactly the files git tracks, minus the folder and the marker, so a file that is not added to git is not in the copy (the run prints how many). The scan runs first inside the copy run (the marker rule excepted) and its hits stop it; a tracked symlink is copied only when it is a relative one that stays inside the copy and avoids the folder, any other stops the run; each file is opened without following links, so a path swapped for a link after the check is refused. The listing ignores the person's own git ignore file (`core.excludesFile`, the XDG one); `.gitignore` files and `.git/info/exclude` of the repository stay honoured. Pytest arguments need one of these two flags, and the three modes exclude each other (exit code 2). The child process sees only the environment variables named in the settings (no token or key of the caller; DB and Vault variables are left out on purpose) and none of the `GIT_*` variables, and the run checks that the product package is imported from the copy. Links in the copy are checked after the copy is made, on the copy itself with its links in place (a chain of links cannot lead out, a loop stops the run, `..` after a link is refused); each file is read by walking its folders with `O_NOFOLLOW` per component where the system has it, and where it does not a link on the path is refused. The scan reads one `lstat` per file, decides links from the file system (`realpath`, a loop is a hit), and shows the first line of git's own error masked. In that line a value is hidden when its name holds key, token, secret or password (`bypass_key=` and `bypass_token=` are hidden) because such a value is a credential, while a bare word such as `bypass=true` is shown because it is a setting that tells the reader what git was told and hides nothing secret; a bare scheme word with a token and no header name (`Bearer abc`) is left as it is because without a name in front of it the line cannot be told from plain words, and the same words after an `Authorization:` header name are hidden. The four places that list tracked files (this guard, `tools/scan_repo.py`, `tests/test_repo_rules.py`, `tests/test_no_reference_material.py`) are listed in one test that compares them on a made-up repo with a global ignore file. CI runs `python tools/demo_only_guard.py --without-folder-if-present -- -m "not live and not perf"` in the `check` job, with `HADAVIN_REQUIRE_NODE` set (no new permissions).
  - Limits: a name built from pieces at run time cannot be found by any text scan (the copy run is the check for that); the byte search of a binary file looks for the name as written (a binary has no text to normalise with NFKC), and on a case-insensitive file system a differently-cased spelling of a product folder is not matched; the guard needs a git checkout; files the repository ignores are not checked; only the listed product folders are scanned, so packaging files at the repository root (for example `pyproject.toml`) are not. Core has no such folder today. Tests: `tests/test_demo_only_guard.py`, `tests/test_demo_only_guard_ci.py`.
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

### Added (P1m, test tooling: the mutation runner and judge)
- `tools/mutation_runner.py` (a developer tool, not in the wheel) runs one mutant at a time on a temp copy of a package and
  judges the kill by its reason with `hadavin_sdk.testing.mutation` (in the wheel). They come with
  their tests (`tests/test_mutation_runner.py`, one test per guard) and their mutants
  (`tests/mutation_runner_mutants.py`, run with `uv run python tests/mutation_runner_mutants.py`). Changes after review: the tests work on Windows as well (`_pid_alive` asks the system library on Windows; a symlink is skipped only
  on Windows without the privilege, and a junction is used for the folder case); a mutant now names a distinctive fragment of the
  failing assertion message (not the killer's name) and the test it pins; the runner kills the run's whole process group on an
  interrupt (Ctrl-C) and after a normal exit, hands pytest an empty ini file and the copy as rootdir (a planted `pytest.ini` is
  never read), compares the exception class a crash row declares by its parsed leading name (not a substring), treats a baseline
  timeout of 0 as a timeout, and refuses a path with a `:`; the `mutation.py` comment no longer holds process words. Three
  `nosec` comments the scanner does not need are deleted.
  A SIGTERM or SIGHUP sent to the runner now ends it like Ctrl-C (the pytest tree is killed, the temp folders are removed; POSIX);
  after a normal exit the tree is killed on POSIX only (on Windows the pid may be reused); the temp folders are cleaned up when a
  path is refused; the mutants script exits 2 when its filter selects no mutant; `tools` is now also checked by bandit and
  Semgrep in CI.
  Review round 3 (P1m): the judge looks for `expect` in the first error line only (a fragment found only in the test id no longer
  counts; `pinned` ties a kill to its test). The runner waits for the pytest child without reaping it (`os.waitid` with `WNOWAIT`,
  POSIX; macOS has no `waitid` and keeps the old order) and kills the process group before the reap, so the group id cannot belong to
  another process. A SIGTERM or SIGHUP that arrives while the child is being started, while the tree is killed or while the temp
  folders are removed is held until that step is done (then raised), and once a signal has ended the run a second one cannot cut the
  cleanup short; the narrow window of a few instructions between a signal handler and the first line of the cleanup stays (stated in
  the module docstring), and SIGKILL still cannot be caught. A signal that was ignored on entry (SIGHUP under `nohup`, SIGTERM from
  a parent that ignores it) stays ignored. The ini file of a pytest run now lives in its own temp folder, no longer in the working
  folder. `FIRST_LINES` (a module global, not safe for two runs at once) is gone: pass `first_lines={}` to `run_mutants` and read
  it after the call. Tests: the helper tests no longer run a real `os.kill` or `os.symlink` under a faked platform (they failed on
  Windows); the rule "a test that fakes the platform fakes every OS call of that branch" is stated in the helpers docstring; the
  interrupt test kills its leftover process only after its assertions; the signal test starts the runner in its own session, kills
  the leftover pytest group, and resets SIGTERM and SIGHUP to the default first. Eight new mutants (49 in all).
  Review round 4 (P1m): a test path, fixture folder or mutant file that starts with `-` or `@` is refused (`ValueError`; write `./name`)
  where the paths are first checked and again where the pytest command line is built; the `--` marker is no longer relied on (on
  Python 3.12.3 `pytest -- -x` still takes `-x` as an option, and pytest reads `@name` as an argument file also after `--`). A relative
  symlink of the snapshot that points outside the tree is refused. `run_mutants` states that it is not re-entrant and raises
  `RuntimeError` on a nested call in the same thread (POSIX main thread). A leader that someone else already reaped is now known to
  its `Popen` object, so the group of a reaped pid is not signalled. The docstring lists all the module constants. CI runs the tests
  on Python 3.12 and 3.13. Tests: the liveness check of the background-process test polls against a deadline and names the state of
  a process that survives; the signal test ends a runner that never started its child with SIGTERM before it kills the leftovers; the
  refused-run test checks the shared folder after the first refusal. Five new mutants and one replaced (54 in all).
  Fix 1 (P1m, three review-4 Minors): (a) a Windows junction under `src` or a fixture folder is refused (`ValueError`) before the
  snapshot copy, because `shutil.copytree` follows a junction and copies its target as a real folder (`os.path.isjunction`, Python 3.12
  and later; where it is missing nothing is refused). (b) The refusal of a path with `:` now says "a path may not contain ':'" and the
  module docstring states the limit. (c) A pytest child that someone else reaped first (SIGCHLD ignored) used to come back as exit code 0,
  which the judge reads as a pass; it is now `REAPED_ELSEWHERE`: an ERROR row (`REAPED ELSEWHERE`) for a mutant, a `RuntimeError` for the
  baseline. Six new tests, eight new mutants (62 in all). Review 5 (order 40) added: a junction is also refused when it is the `src` or fixture folder itself or a part of the fixture path (`tests` in `tests/fixtures`); a reaped baseline is named as reaped; the Limits docstring now says that without `os.waitid` (macOS) a child reaped by someone else can still read as exit code 0, and that on the reaped-leader path descendants are not killed.
  A real Windows junction was probed by hand by the lead (not by this test, which patches `os.path.isjunction`; record: `handover/reviews/P1m-fix1-junction-probe.txt`). Run by the lead on Windows, Python 3.13.3, `mklink /J`:
  ```
  3.13.3 mklink rc 0
  islink False isjunction True
  is_dir True
  ```
  Also: `tests-py312` is named in the `ci.yml` header comment (no job or check name changed).
  The byte-copy hash of `tools/mutation_runner.py` changes (new value below): re-copy it in every repository that keeps a copy.
- Note on the name: `tools/` is a top-level Python package called `tools`, a generic name. A repository that copies it and already
  has its own `tools` package or folder must merge or rename deliberately; the mutants script puts the repository root on
  `sys.path` so that `tools.mutation_runner` imports, and another `tools` earlier on the path would shadow it.
- Every repository that keeps a byte copy of these files re-copies the four of them in one commit and updates its pins to the
  sha256 values below (also pinned in `tests/fixtures/mutation_manifest.json`):
  - `src/hadavin_sdk/testing/__init__.py`: `3c77d034fe2a1ee70adea0d0bd259a20edda397d8ebd55a0e40b63e5c21c9e1c`
  - `src/hadavin_sdk/testing/mutation.py`: `75c32a4e501f5c3a4edcd6f1fd8a58603ebb2ef6fd43842e558ce0761eaee03e`
  - `tools/__init__.py`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
  - `tools/mutation_runner.py`: `489517fb224f0598e14244ded1b37fe2a68be69e2396e56e450be0d8b1c0a1a7`
