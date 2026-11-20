# REQUEST 001 from core-a (DOOR) to core-b (SPINE): config and wiring for the signed trigger endpoint

Status: DRAFT 3, 05:41 UTC. REPLACES draft 2. Source: tickets/D-signed-endpoint.md sections 6 and 7b, after its one review round (tickets/D-review-1.md; no second round). Every file:line below was opened for this draft; nothing was run. S = src/hadavin_sdk.

CHANGES from draft 2 (core-b: please note if you already started): (1) R1c also needs a change INSIDE `platform_secrets.check` (S/backends/platform_secrets.py:36-51), not only in app.py (review row CB-N7); (2) the closer existing pattern for the name-limited reader of R1d is `_own_secrets` (S/app.py:304-313) (CB-N8); (3) a duplicate sender id and a secret name shared by two senders raise their OWN ValueError, they are not joined to the stage "refused" list (CB-N9); (4) the body cap is no guarantee: JSON escaping can make a document up to 6 times larger; what the default covers is stated below (CB-M6); (5) the `config_hash` citation is registry.py:132-173 (CB-M5); (6) new section "Field names the built code reads", taken from worker.py and endpoint.py. No field was renamed and no default changed since draft 2.

CHANGES from draft 1 (kept for the record): `senders` is a LIST of TriggerSender, each with its own `id`; new fields host, port, allow_non_loopback, poll_s; max_running default 1 (was 4); max_body_bytes default 2 x MAX_DOCUMENT_BYTES, at most 8 x; the App field is named `trigger_resolve`; the registry check needs principals, which `_cross_check` does not receive today.

Why a request: DOOR creates only new files; all of the below is in existing files that core-b owns.

## The changes asked for (one line each, with the reason)
- R1 `S/config.py` after line 377 and in `_cross_checks` (392-431): add `TriggerSender`, `TriggerSettings`, `Config.triggers`. Reason: `Config` forbids unknown keys (config.py:67-69), so a `triggers:` block cannot load today.
- R1b `S/defaults.py` (after line 33): the default numbers listed below. Reason: one place for defaults (defaults.py:1-8).
- R1c `S/app.py:158-169` AND `S/backends/platform_secrets.py:36-51`: every `secret_names` entry of `Config.triggers` is checked at start, kept apart from backend, tool and executor names. Today `check` has only two name groups besides the backends, `executor_names` and `tool_names` (36-41), and a name passed as a tool name that equals a backend name is refused with the text "used by both a backend and a read tool" (47-51). So adding the trigger names to `extra_secret_names` in app.py (158-168) alone would give a wrong message. Wanted inside `check`: a third group (for example a parameter `trigger_names`), refused with its own sentence when it overlaps the backend, tool or executor names, and included in the loop that reads every name once (58-63). Reason: a missing or shared secret must fail before the first request.
- R1d `S/app.py:46-60` and 286-298: one new App field `trigger_resolve: Callable[[str], str] | None = None`, a reader limited to the trigger secret names, None when `Config.triggers` is None. The closest existing pattern is `_own_secrets` (S/app.py:304-313): a frozenset of allowed names and an inner function that raises for any other name; `platform_secrets.bound` (platform_secrets.py:23-33) is the same idea for backend settings. Reason: App has no way to hand a secret to the worker.
- R2 `S/registry.py:226 and 339`: after principals are loaded (219), refuse a sender whose `agent_id` is not in agents or whose `principal_id` is missing or not kind `service`. Reason: fail at load; today `_cross_check` has no principals argument.
- R3 `README.md`, `SECURITY.md`, `CHANGELOG.md`: the once-only sentence of plan-v4-final B3 with its limits, in this step's PR. (Not read: wording is core-b's.)

## Detail
File `S/config.py`. New optional block `triggers:` in config.yaml; absent means the worker refuses to start with a ConfigError (exit code 2). It is not part of `config_hash`: only the fields listed in the hashed dict count (S/registry.py:132-173; two of them are Config-level, `tool_module_hashes` at 155 and `eval_threshold` at 168), and `Config.triggers` must not be added there, so no agent loses its qualification. All models use the `_Strict` base (config.py:67-69).
```
class TriggerSender(_Strict):
    id: str                       # ^[a-z0-9-]{1,40}$
    secret_names: list[str]       # 1 or 2 names (2 only during a swap), distinct, non-empty
    agent_id: str
    principal_id: str
class TriggerSettings(_Strict):
    tenant: str                   # ^[a-z0-9-]{1,40}$, required, no default
    senders: list[TriggerSender]  # 1 to defaults.TRIGGER_MAX_SENDERS (8); ids unique; secret_names disjoint across senders
    host: str = "127.0.0.1"       # literal lives in defaults.py or here: core-b's choice under the no-hardcoding guard
    port: int = 8081              # 1 to 65535
    allow_non_loopback: bool = False       # StrictBool: the worker tests `is True`
    max_body_bytes: int = 2 * defaults.MAX_DOCUMENT_BYTES   # > 0, at most 8 x MAX_DOCUMENT_BYTES
    max_running: int = 1          # 1 to 64 (raise the default to 4 after step F)
    ack_wait_s: float = 5.0       # > 0, at most 30
    poll_s: float = 0.05          # >= 0.01, at most 1.0, and < ack_wait_s
Config.triggers: TriggerSettings | None = None
```
Cross-checks wanted in `Config._cross_checks`: a duplicate sender id, and a secret name used by two senders. Each raises its OWN ValueError (names only, never values), the way the checks at config.py:393-400 do. They must NOT be joined to the `refused` list (config.py:407-430): that list is the stage table and its message starts "environment <stage>: refused:" (430), so a duplicate id there would read as a stage refusal. `allow_non_loopback` needs no extra rule: no default of true; the worker refuses a non-loopback host in every stage (demo, pilot, prod) unless the field is exactly true. Checks that need the registry (agent exists, principal exists and is kind service) are R2. Checks that need the secret VALUES (at least 32 characters, distinct across senders) are done by the worker at start, because config never holds values.

The body cap is no guarantee. The request body is the document written as a JSON string, and escaping makes it longer: a quote, a backslash or a line break takes 2 bytes; a sender that escapes non-ASCII text as `\uXXXX` turns a 2-byte character into 6 bytes (3 times); a control character takes 6 bytes (6 times). The wrapper (two field names and a key of at most 128 characters) adds about 150 bytes. What the default of 2 x MAX_DOCUMENT_BYTES (262144, defaults.py:31-33) covers: a full-size document sent as plain UTF-8 with few escapes, and any document whose escaped form adds less than about 262000 bytes. Not covered: a document near the document cap with many escaped characters; it gets 413 although it is under the document cap. An operator who needs every document to fit sets 6 x plus the wrapper, which the upper bound of 8 x allows. Please carry one sentence of this into the field's description.

Defaults to add in `S/defaults.py` (R1b): `TRIGGER_MAX_SENDERS = 8`, `TRIGGER_MAX_RUNNING = 1`, `TRIGGER_ACK_WAIT_S = 5.0`, `TRIGGER_POLL_S = 0.05`, `TRIGGER_PORT = 8081`, `TRIGGER_MIN_SECRET_CHARS = 32`. The same numbers are literals in S/triggers/endpoint.py:36-37 and S/triggers/worker.py:57-63 today; core-a replaces them by the defaults in a follow-up once these exist.
Fixture change (core-b's file): `tests/fixtures/config/config.yaml` stays without `triggers`; the trigger tests write their own block into a tmp copy, so no existing fixture changes.

## Field names the built code reads (S/triggers/worker.py and endpoint.py, read 05:41 UTC)
- `config.triggers` (worker.py:196); None gives the ConfigError "triggers block not configured".
- `settings.senders` (worker.py:204): a list whose items have `id` (208); a mapping id -> sender is also taken (205-206).
- per sender: `id`, `agent_id` (worker.py:218), `principal_id` (222), `secret_names` (239; more than one name gives a warning at start, 240-243).
- `settings.tenant` and `settings.max_body_bytes` (endpoint.py:216-218): read without a fallback, so both must exist.
- `settings.max_running`, `ack_wait_s`, `poll_s` (worker.py:285-287) and `host`, `port`, `allow_non_loopback` (341-343): read with `getattr` and the worker's own fallbacks, so a missing field does not fail.
- `app.config`, `app.trigger_resolve` (worker.py:271-272; a missing or None reader is a ConfigError), `app.runtime`, `app.runtime.agents`, `app.registry.principals` (278), `app.store` (283-284); a principal's `kind` must equal "service" (227).
- start: `load_config(config_dir)` and `build(config_dir, agents)` with every qualified agent (worker.py:339, 344).

## What core-a does meanwhile
- endpoint.py is coded against a typing.Protocol with these field names and worker.py reads them by attribute name; `main` exits with code 2 and a clear message while `Config.triggers` or `App.trigger_resolve` do not exist. Tests use stand-in objects inside the tests folder only.
- Offers: the contract test for the block (bad pattern, 0 or 3 secret names, duplicate ids, shared secret name, bounds) as a new test file once core-b confirms the names.

## Least privilege (preamble rule 11)
- The worker reads: the sender secrets by name through `trigger_resolve` only; run rows by run id. It writes nothing itself: the run row is written by Runtime.handle under the existing runtime identity. No new database role, table or migration.
