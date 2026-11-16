# walk-C.md (lane C, builder C; audited sha b4cce5b; static reading only, no code run)
Two walks, in the order the plan gives: (1) the llm call path, (2) the k1b diagnosis and replay loop (k1b/ read-only).
Everything that needs a running program to confirm is tagged UNVERIFIED. File:line points at the audited sha.
Plain-words key: "a run" = one agent handling one incoming request; "a person must look" = the run ends in the state NEEDS_PERSON; "the meter" = Limits.charge (limits.py:197).

## WALK 1: the llm call path (llm/protocol, retry, common, backends, fake)

### Trigger
- Production: runtime/agent_loop.py:425 `self.llm.chat(...)`, once per step, up to `agent.max_steps` steps (agent_loop.py:420 `for _step in range(agent.max_steps)`).
- Also callers: evals.py:73 (the gate, `hadavin-sdk gate`), guard/judge.py:72 (the injection judge, called from agent_loop `_screen` and from the gate), extract.py:47 (no caller in src, see C-20), k1b/loop.py:94 (replay, walk 2).
- The object is chosen once at start-up: app.py:162 `llm = llm or make("llm", b.llm, secrets, routes=cfg.routes)`; kind from config `backends.llm.kind`.

### Branches (what `chat` does)
1. `FakeLLM.chat` (fake.py:29): hash of the first document (or of the messages), counts attempts per hash, reads `<sha256>-<attempt>.json` from `recorded_dir`; a missing file raises `UnknownRecording` (a KeyError, NOT a ProviderError, fake.py:47). Cost is computed from the route price (fake.py:50-53).
2. `NetworkLLM.chat` (common.py:208): looks up the route (`self.routes[route]`, a missing route is a KeyError, common.py:218), shapes tools (`tools_for`, common.py:65), shapes turns (`turns`, common.py:86), calls the kind's `_chat`.
3. Per kind:
   - anthropic.py:106 `messages.create`, tool forced with `tool_choice` when `output_schema` is given (anthropic.py:119-120).
   - bedrock.py:128 `converse`; for a model family that cannot be forced to one tool (not anthropic/amazon) the schema goes in the system prompt and the answer is read back from text (bedrock.py:129-131, 170-171).
   - gemini.py:54 one POST, function-calling mode ANY (gemini.py:80-83).
   - openai_compat.py:94 POST `/chat/completions`; up to TWO requests when a forced tool call is missing (openai_compat.py:118-129), each of them with its own retry loop.
4. Every kind wraps the single request in `self._retry` (common.py:233) = `with_retry` (retry.py:83).
5. `reply()` (common.py:152) prices the answer from the route; a cut-off answer (`max_tokens`) keeps its cost but drops its tool calls (common.py:173).

### Error paths
- `with_retry` (retry.py:92-108): a `ProviderError` raised inside the call passes straight through (retry.py:95-96). Any other exception is classified by `transient()` (retry.py:55): certificate or protocol error = not retried (retry.py:56-57); the kind's `retryable(exc)` gets the next say (retry.py:58-59); then an HTTP status (408, 429, 5xx retried, retry.py:39-40); then any `OSError` (retry.py:63). Not transient => `ProviderError("<label>: <class> <status> <code>")` at once (retry.py:98-99). Transient on the last attempt => `ProviderExhausted` (retry.py:100-103). The message holds the class name, status and error code only (retry.py:77-80), never the SDK message.
- A malformed provider answer (KeyError, ValueError in `_parse`) happens INSIDE the retried call, so it becomes a ProviderError (common.py:194-196 says so; gemini.py:106,111 raise ValueError on purpose).
- `reply()` runs OUTSIDE the retry (anthropic.py:123, bedrock.py:157, gemini.py:91, openai_compat.py:132). An exception there (for example a route price that makes `Decimal` arithmetic fail) would not be a ProviderError. UNVERIFIED (needs a runtime to produce one; with `Money` validation it should not occur except NaN, see C-01).
- Caller side, production: agent_loop.py:~429-436 catches `ProviderError` only; `provider_exhausted` or `provider_error` => note + `NEEDS_PERSON` (a person must look). `UnknownRecording`/KeyError from an unknown route would propagate out of the run (route is checked at registry load, UNVERIFIED here; lane B).
- Caller side, gate: evals.py:73 has NO try/except: a ProviderError aborts the whole gate; `cli.main` turns it into exit 3 with the class name (cli.py:70-83).
- Caller side, judge: `injection_check` turns any exception into a flag, never a pass (guard/injection.py:85-101).

### Retries and timeouts
- Attempts: `max_attempts` per request, 1 to 10, default 3 (backends/table.py:40). Backoff: full jitter, base 0.5 s doubling, cap 8 s (retry.py:22-23, 106); a server `Retry-After` is honoured only up to 8 s (retry.py:72) although the comment says "never sooner than the server asked" (retry.py:104-105): C-14.
- Timeout: `call_timeout_s` default 60 (table.py:37-38) is a PER SOCKET OPERATION timeout (the field comment says so), handed to the SDK/urllib (anthropic.py:37, bedrock.py:47, common.py:264). There is NO wall-clock limit on one `chat` in production: a server that trickles bytes keeps the call alive for as long as it sends. Only k1b adds a wall-clock bound (k1b/loop.py:84-112). C-16.
- Worst case time of one `chat` call: `max_attempts x (socket timeouts add up per phase)` + sleeps up to 8 s x (attempts-1); openai_compat doubles it (two requests). The stuck-run rule (runtime/tick.py:99-109) assumes `max_steps x call_timeout_s x max_attempts + 60`, which ignores the second openai_compat request, the backoff sleeps, the judge call per step (agent_loop `_screen`) and the tool time. C-19.
- No circuit breaker, no rate limit on the llm calls themselves (only on tools: tools.py:1013, 1100). UNVERIFIED whether a provider rate limit is hit in a burst; retry handles 429.

### Kill, restart, duplicate, out-of-order, empty, huge input
- Kill during a call: the request is lost with the process. The provider may have billed it. Nothing is written before the call (no reserve), so the meter never learns about it: C-02. Restart: tick marks the run stuck after `stuck_after_s` and it goes to NEEDS_PERSON or "interrupted" (tick.py:112-118, lane B).
- Duplicate: no idempotency key is sent to any provider (grep for idempotency in llm/: none). A retried request after a timeout can be billed twice; only the second answer is used. The meter charges only the answer that came back (agent_loop.py:437).
- Out-of-order messages: `turns()` passes roles through unchanged (common.py:95-99); the vendor rejects bad alternation with HTTP 400 => ProviderError at once.
- Empty: `messages=[]` gives an empty request that the vendor refuses (400). Documents that are blank after decoding are dropped (common.py:91-93). If the message list has NO user turn the documents are silently never sent (the `docs` list is only consumed on a user turn, common.py:97-98). UNVERIFIED that any caller can produce this (agent_loop and evals always start with a user message).
- Huge input: no size check before sending in llm/ (redaction cap `MAX_DOCUMENT_BYTES` 262,144 is applied by callers, agent_loop; lane B). Huge output: `max_tokens` from the route bounds it for the model; the HTTP body read for gemini/openai_compat is NOT bounded (`resp.read()`, common.py:265): C-15.
- Non-UTF8 documents are decoded with replacement (common.py:92).

### What is written where
- Nothing is written by llm/ itself (no file, no store, no log line). Only `FakeLLM` reads files (`recorded_dir`, fake.py:45-48).
- The caller writes: `limits.charge` -> store spend table (agent_loop.py:437), `store.add_cost` (agent_loop.py:438), audit note only on failure or stop (agent_loop.py:431, 443). On a SUCCESSFUL call there is no audit or log line for tokens, latency, route, cache hit or prompt version (grep `input_tokens|latency_ms` outside llm/ and models.py: no hit): C-17.

### What a person sees
- Production: a card/state NEEDS_PERSON with reason code `provider_exhausted`, `provider_error`, `llm_max_tokens` or `llm_refusal` (agent_loop.py:429-447).
- Gate/CLI: `failed: <ClassName>` on stderr, exit 3 (cli.py:70-83); with `HADAVIN_DEBUG=1` the full traceback (cli.py:81-82; a traceback can contain request text, UNVERIFIED).

### What is logged
- llm/: no logger at all (grep `getLogger` in llm/: no hit). Errors surface only through the exception text (class, status, code).
- k1b: one warning line for an abandoned call (k1b/loop.py:100-102).

### Which identity acts
- The process identity of the runtime. Key-based kinds read the key by secret NAME through the secrets kind on every call (anthropic.py:132, gemini.py:33, openai_compat.py:53-56); vertex and bedrock use the workload identity (ADC, IAM role) and hold no key (anthropic.py:41, bedrock.py:1-3). Names only: `api_key_secret_name` (setting), no value read.
- Egress hosts: anthropic.py:23 `API_BASE_URL` constant; gemini.py:20 constant; vertex host derived (anthropic.py:26-33); foundry host from a validated resource name (anthropic.py:51); bedrock region host (SDK); openai_compat `base_url` from config (https, or keyless loopback; table.py:75-85). Redirects are off for stdlib calls: common.py:248-250 uses the shared opener and guard/http.py:160 `NoRedirect` refuses redirects (read, not run).
- `ignore_configured_endpoint_urls=True` (bedrock.py:53) and explicit base URLs (anthropic.py:27-28) stop environment variables from redirecting the key. No test names `ignore_configured_endpoint_urls` (grep tests: no hit); the test for the Anthropic base URL is not found by grep for `ANTHROPIC_VERTEX_BASE_URL`; test_p5_llm.py:291 covers the foundry variable only.

### Approval points
- None in this path. The llm answer is only a proposal; approval binding lives in approvals/actions (lane A). The only llm-related guard is the injection screen (agent_loop `_screen`).

### Loop stop conditions
- Per request: `max_attempts`. Per `chat` call in openai_compat: 2 requests. Per run: `agent.max_steps` (agent_loop) and `_limits_stop` (budget and kill switch, checked BEFORE each call, agent_loop.py:421, again before a tool, agent_loop.py:460, and once before the loop, 359). The meter is charged AFTER the call (agent_loop.py:437), so one call can overshoot the budget, and N concurrent runs can each pass the check before any is charged: C-02. `ProviderError` ends the run at once (no further steps).

### Walk 1 findings (also in findings-C.md)
C-01 (route prices unchecked), C-02 (no reserve before call, failed calls unmetered), C-14 (Retry-After cap vs comment), C-15 (unbounded read), C-16 (no wall clock in production), C-17 (no per-call log, no cache), C-19 (stuck rule formula), C-25 (fake edge).

## WALK 2: the k1b diagnosis and replay loop (k1b/ read only)
Files read: k1b/loop.py (all), replay.py (all), audit_sink.py, atomic.py, diagnosis.py (head), bundle.py/causelist.py/score.py/tools.py/redaction.py (grep level only: path confinement and size caps). NOT-AUDITED in this walk: score.py logic, bundle.py parsing, redaction.py regexes, report.py (lane B owns k1b findings; I read only for the walk).

### Trigger
- CLI `hadavin-sdk replay AGENT --bundles D --cause-list D --max-usd X --out OUT [--k K]` (cli.py:108-123, 212-245). Operator-run, one process, no schedule. `score` is a second command that reads the outputs (cli.py:124-130, 248-275).

### Branches
1. Refusals before anything is written: bad k, non-positive or non-finite `--max-usd` (replay.py:112-115), unknown agent (116), zero price on a non-fake route (85-90, 118), redaction off without the acknowledgement flag (119-123), output folder not empty (125-126), bad cause list or bundles (127-129). All are `ConfigError` = exit 2.
2. For each run index 1..k, for each bundle: mask the bundle once per case (replay.py:156-159), then `loop.run_case` (162-174). After a halt (`capped` or `aborted`) the remaining cases are written as capped/error records without calling the model (176-179).
3. `run_case` loop (k1b/loop.py:150-215): per step check case deadline (151-153), check USD cap (154-156), call `_chat_bounded` (158-165). Reply branches: max_tokens/refusal => status error (180-182); no tool call => parse text as diagnosis (183-188); `submit_diagnosis` => parse (190-195); unknown tool => "unknown tool" result and a hard_check_a mark (200-202); known tool => run on the frozen snapshot, then injection check of the result (204-209).
4. After the case: hard check b (citations must appear in what tools returned; else converted to not_sure, replay.py:195-209), write case JSON.

### Error paths
- `CallTimeout` (wall-clock bound hit): charge worst case, stop the whole run `aborted` (loop.py:166-172). `ProviderExhausted`: case error, run continues (173-175). Other `ProviderError`: case error, run aborted (176-178). Any OTHER exception from `llm.chat` (UnknownRecording, KeyError route, programming error) is re-raised through `_chat_bounded` (loop.py:110-111) and escapes `run_case`, although its docstring says "Never raises for a model or provider problem" (loop.py:139). `replay()` then writes FAILED.txt and re-raises (replay.py:269-277); the cli prints `failed: <class>` exit 3.
- Detector errors are flags, not crashes (guard/injection.py:85-101); a flagged tool result is replaced by NO_DATA (loop.py:207-209).
- Audit failure: `K1bAudit.emit` raises `AuditUnavailable`; replay does not catch it, so the command fails (audit_sink.py:3, replay.py:109-110).

### Retries and timeouts
- Per-call retries come from the llm kind (max_attempts). Case deadline `k1b.case_timeout_s` default 300 (config.py:171), per-call wait = remaining case time with a 1 s floor (loop.py:81, 106). Steps: `min(k1b.max_steps, agent.max_steps)` (replay.py:132); tool calls per case `k1b.max_tool_calls` default 20 (config.py:170).
- When the wait expires, the call thread is ABANDONED, not cancelled (loop.py:107-109). Its retry loop can still send up to `max_attempts` requests. The charged worst case is ONE attempt: `worst_case_usd` says "one attempt, a full reply" (loop.py:115-122) while the comment above says "a retry layer can re-send" (loop.py:167-168). The real overshoot is up to `max_attempts` x that estimate. And if `route_prices` is None (the default, loop.py:130) nothing is charged at all (loop.py:169). C-03.

### Kill, restart, duplicate, out-of-order, empty, huge input
- Ctrl-C (SIGINT): `except BaseException` in `replay()` writes FAILED.txt (replay.py:273-277). SIGTERM or SIGKILL or power loss: Python's default SIGTERM ends the process without running the handler, so no FAILED.txt, no `replay_run` audit event, no `outputs.sha256`. Paid calls may already have happened. The only audit events are `hard_check_*` per case and the final `replay_run` (replay.py:185-206, 260); there is NO audit event before the first paid call although `K1bAudit.emit` says "Write one event BEFORE its side effect" (audit_sink.py:24-25). C-18.
- Restart: the output folder must be empty (replay.py:125-126), so a killed run cannot be resumed; the operator deletes the folder and pays again for everything. No per-case resume.
- Duplicate: two replays into the same folder: the second sees a non-empty folder and refuses, unless both start at once (check-then-mkdir, replay.py:125-133 is not atomic): UNVERIFIED.
- `atomic_write` uses a fixed temp name `<file>.tmp` (atomic.py:12); a crash leaves `*.tmp` in `run*/`, and `outputs_files` hashes every file under `run*` (replay.py:78-82) so a leftover would change the outputs digest. UNVERIFIED whether score refuses it (score.py:195-205 compares file sets: likely refuses).
- Empty: zero bundles are refused ("bundles folder holds no incidents", bundle.py:344-346). Zero cause-list entries: not read.
- Huge: bundle JSON read whole (`read_bytes`, bundle.py:112, 137), case ids restricted by `CASE_RE`, symlinks refused (bundle.py:189-200), redaction total capped at `2 x MAX_BUNDLE_CHARS` (redaction.py:185). Tool results capped at 20,000 bytes (k1b/tools.py:23). Messages grow by at most `max_steps` pairs.

### What is written where
- OUT/runN/<case>.json, OUT/runN/run.json, OUT/outputs.sha256, OUT/replay-report.md (replay.py:1-5, 222, 256, 261-262), all through `atomic_write` (atomic.py), UTF-8 with backslash replacement.
- Audit: through `K1bAudit` into the configured sink (`local_dir` or `chain`; k1b/audit_sink.py:56-72). With a chain over the MEMORY store the events vanish at exit and only a warning is printed (audit_sink.py:15-17, 71-72).
- `replay-records.jsonl` is NOT written by replay: no writer exists in src (replay_records.py:3 says "K1b-full adds the writer"; grep `ReplayRecord(` in src: no hit). C-08.

### What a person sees
- Console: `replay <result>: outputs in <dir> (see replay-report.md)`, exit 0 complete, 1 aborted/capped, 2 refused, 3 failure (cli.py:20-23, 244). `replay-report.md` carries DISCLAIMER "nothing here is a warranty and a replay pass is not evidence of live accuracy" (replay.py:6).
- The per-case record shows status, stop reason, diagnosis or raw head (2,000 characters, loop.py:37, 187).

### What is logged
- Logger name from the module (loop.py:100) only for an abandoned call; the cause class name only. Audit rows hold hashes and codes (models.py:189 AuditEvent docstring).

### Which identity acts
- The OS user running the CLI, read with `getpass.getuser()` (audit_sink.py:62-66), recorded as audit `principal`; `source="cli"`. Not checked against principals.yaml. The model credentials are those of the process (same as walk 1).

### Approval points
- None: replay is report-only and "does not run the production approval and limits path" (loop.py:5-6). It does not check the production kill switch or the production budget meter either: a replay is not stopped by `limits stop` (grep `Limits` in k1b/: no hit). UNVERIFIED whether that is wanted; it spends real money, so the kill switch not applying is worth a decision (listed under C-04 as the same class).

### Loop stop conditions
- Case: `max_steps`, `max_tool_calls`, `case_timeout_s`, USD cap, submit_diagnosis, a reply with no tool call (loop.py:150-215). Whole run: k runs x cases, `halt` on cap or abort (replay.py:175). The USD check happens BEFORE each call and one reply may overshoot (loop.py:41 docstring says so); judge cost is charged after each tool result (loop.py:206).

### Walk 2 findings
C-03, C-04 (gate and replay share the no-kill-switch/no-reserve class), C-08, C-18. NOT-AUDITED: k1b/score.py, bundle.py, redaction.py, report.py, tools.py, causelist.py internals (read only for path and size caps).
