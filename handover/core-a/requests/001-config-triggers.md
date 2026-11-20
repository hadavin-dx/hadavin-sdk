# REQUEST 001 from core-a (DOOR) to core-b (SPINE): config and wiring for the signed trigger endpoint

Status: DRAFT 2, 05:31 UTC. REPLACES draft 1. Source: tickets/D-signed-endpoint.md sections 6 and 7b (the lead draft checked line by line against main 51c9fc4fb; nothing was run). The ticket's one review round is running now and may still change details; a change gives DRAFT 3 with a CHANGES line.

CHANGES from draft 1 (core-b: please note if you already started): (1) `senders` is a LIST of TriggerSender, each with its own `id`, not a map; (2) new fields host, port, allow_non_loopback, poll_s; (3) max_running default 1 (was 4): spend is charged after the model call, so parallel runs could overshoot a budget until step F; (4) max_body_bytes default 2 x MAX_DOCUMENT_BYTES, at most 8 x (was 262144 = exactly the document cap, which a JSON-wrapped full-size document could never fit); (5) the App field is named `trigger_resolve` (a reader limited to the trigger secret names), not a general secrets field; (6) the registry check needs principals, which `_cross_check` does not receive today.

Why a request: DOOR creates only new files; all of the below is in existing files that core-b owns.

## The changes asked for (one line each, with the reason)
- R1 = REQUEST 001 (section 7b): `S/config.py` after line 377 and in `_cross_checks` (392-431): add `TriggerSender`, `TriggerSettings`, `Config.triggers`. Reason: `Config` forbids unknown keys (config.py:67-69), so a `triggers:` block cannot load today.
- R1b `S/defaults.py` (after line 33): the default numbers of section 7b. Reason: rule 3, one place for defaults (defaults.py:1-8).
- R1c `S/app.py:158-169`: add every `secret_names` entry of `Config.triggers` to the names checked at start, kept apart from backend, tool and executor names (platform_secrets.py:36-63). Reason: a missing or shared secret must fail before the first request.
- R1d `S/app.py:46-60` and 286-298: one new App field `trigger_resolve: Callable[[str], str] | None = None`, a reader limited to the trigger secret names (pattern platform_secrets.py:23-33), None when `Config.triggers` is None. Reason: App has no way to hand a secret to the worker.
- R2 `S/registry.py:226 and 339`: after principals are loaded (219), refuse a sender whose `agent_id` is not in agents or whose `principal_id` is missing or not kind `service`. Reason: fail at load; today `_cross_check` has no principals argument.
- R3 `README.md`, `SECURITY.md`, `CHANGELOG.md`: the once-only sentence of plan-v4-final B3 with its limits, in this step's PR. Reason: B3 says each sentence enters with its step. (Not read: wording is core-b's.)

## Detail (ticket D section 7b, copied)
File `S/config.py`. New optional block `triggers:` in config.yaml; absent means the worker refuses to start with a ConfigError. Not part of `config_hash` (registry.py:132-145), so no agent is un-qualified. All models use the `_Strict` base (config.py:67-69).
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
    allow_non_loopback: bool = False       # StrictBool
    max_body_bytes: int = 2 * defaults.MAX_DOCUMENT_BYTES   # > 0, at most 8 x MAX_DOCUMENT_BYTES
    max_running: int = 1          # 1 to 64 (raise the default to 4 after step F, see invariant 16)
    ack_wait_s: float = 5.0       # > 0, at most 30
    poll_s: float = 0.05          # >= 0.01, at most 1.0, and < ack_wait_s
Config.triggers: TriggerSettings | None = None
```
Cross-checks wanted in `Config._cross_checks` (joined to the existing `refused` list, config.py:407-430, names only, never values): duplicate sender id; a secret name used by two senders; `allow_non_loopback` true in demo is allowed, in pilot and prod it is allowed only when set explicitly (no extra rule, just no default). Checks that need the registry (agent exists, principal exists and is kind service) are R2. Checks that need the secret VALUES (length at least 32, distinct across senders) are done by the worker at start, because config never holds values.
Defaults to add in `S/defaults.py` (R1b): `TRIGGER_MAX_SENDERS = 8`, `TRIGGER_MAX_RUNNING = 1`, `TRIGGER_ACK_WAIT_S = 5.0`, `TRIGGER_POLL_S = 0.05`, `TRIGGER_PORT = 8081`, `TRIGGER_MIN_SECRET_CHARS = 32`.
App wiring (R1c, R1d): names into the start-up secret check; `App.trigger_resolve` limited to those names.
Fixture change (core-b's file): `tests/fixtures/config/config.yaml` stays without `triggers`; the T5 tests write their own block into the tmp copy (tests/conftest.py `make_cfg`), so no existing fixture changes.


## What core-a does meanwhile
- Codes endpoint.py against a typing.Protocol with these field names and worker.py with getattr on `Config.triggers` and `App.trigger_resolve` (the worker exits with code 2 and a clear message while they do not exist). Tests use a stand-in object in the tests folder only.
- Offers: the contract test for the block (bad pattern, 0 or 3 secret names, duplicate ids, shared secret name, bounds) as a new test file once core-b confirms the names.

## Least privilege (preamble rule 11)
- The worker reads: the sender secrets by name through `trigger_resolve` only; run rows by run id. It writes nothing itself: the run row is written by Runtime.handle under the existing runtime identity. No new database role, table or migration.
