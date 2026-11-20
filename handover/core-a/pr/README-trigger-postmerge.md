# Post-merge patch for n8n/README-trigger.md (core-a; state of 2026-11-20 after the lead's order 015, steps D+E)

Apply AFTER core-b's `TriggerSettings` (config.py) and core-b's limits (`reserve`/`settle`) are merged. Do NOT apply on core-a alone: on this branch the `triggers` block is not in the config code, so the new text would be false there. Each block below is an exact OLD text and its exact NEW text. The OLD blocks of items 1 to 4 were checked against the current n8n/README-trigger.md of this branch (all four match as written). The coordinator strips every `[path:line]` proof in square brackets from the NEW text before pasting; `integ:` means the merged tree /home/user/wt/integ (read-only).

What this patch rests on, read in the merged tree: `TriggerSettings` has `tenant` and `senders` without a default. It has `max_body_bytes`, `max_running` (default 4, at most 64), `ack_wait_s` (default 5.0) and `conflict_events_per_minute` (default 10, 1 to 1000), all with bounds [integ:src/hadavin_sdk/config.py:395-425; integ:src/hadavin_sdk/defaults.py:278-290]. The worker reads `max_running`, `ack_wait_s` and `conflict_events_per_minute` from that object and holds no second default [src/hadavin_sdk/triggers/worker.py:103-104; src/hadavin_sdk/triggers/worker.py:714-723]. `load_config` turns a value out of bounds into a configuration error, and the worker turns that into exit 2 [integ:src/hadavin_sdk/config.py:709-717; src/hadavin_sdk/triggers/worker.py:1171-1172]. The worker warns about `max_running` above 1 only when the limits have no `reserve` [src/hadavin_sdk/triggers/worker.py:685-696].

## 1. README-t:51-54 (the `triggers` block IS in the config code after the merge)

OLD:

```
   and "One run at a time"). Also the stated fact that the `triggers` configuration block of the endpoint is NOT in the
   configuration code on this branch yet: the worker has no fallback numbers, and without that block (or with a field
   missing or misspelled in it) it refuses to start with a configuration error, exit code 2 (stated limit 7); the
   operator has to say how the senders are wired in. The memory store is refused outside the demo stage (exit 2, "the memory store is for the demo stage only"): pilot and prod need the PostgreSQL store.
```

NEW:

```
   and "Concurrency: max_running"). The `triggers` configuration block of the endpoint is in the configuration code
   (`TriggerSettings`): `tenant` and `senders` are required; `max_body_bytes`, `max_running` (default 4), `ack_wait_s`
   (default 5.0) and `conflict_events_per_minute` (default 10) have defaults and bounds. Without the block, or with
   a required field missing or a value out of bounds, the worker refuses to start with a configuration error, exit
   code 2 (stated limit 7). The operator has to say how the senders are wired in.
   The memory store is refused outside the demo stage (exit 2, "the memory store is for the demo stage only").
   Pilot and prod need the PostgreSQL store.
```

## 2. README-t:803-808 (only `tenant` and `senders` are required)

OLD:

```
7. The worker has no fallback numbers for the `triggers` block of the configuration. If the block is missing, or a
   field it reads (`max_running`, `ack_wait_s`, the senders, the trigger secret) is missing or misspelled, the worker
   refuses to start with a configuration error and exit code 2; it never runs on silent defaults. The memory store is refused unless the stage is demo (`check_store_stage` in `worker.py`, same exit 2): pilot and prod need the PostgreSQL store. Exit codes: 0 clean stop, 2 configuration refused at start, 3 any other start failure; a store that is down at start is NOT an exit: the worker starts degraded, /health answers 503 and it recovers without restart. `max_running`
   has no default in the worker at all (a missing `triggers.max_running` is a configuration error); the 5 seconds
   for `ack_wait_s` named in this README is the default of the worker's `Runner` class, not a fallback for a missing setting. Only the address and port have defaults, and they are command-line
   options (address `127.0.0.1`, port 8081: `--host`, `--port`). Check the worker's start line for the port it serves on.
```

NEW:

```
7. The `triggers` block of the configuration has two required fields, `tenant` and `senders`. The rest have
   defaults: `max_running` 4, `ack_wait_s` 5.0 seconds, `max_body_bytes` and `conflict_events_per_minute` 10. Each has
   a lower and an upper bound that the configuration load checks. If the block is missing, a required field is
   missing, or a value is out of bounds or of the wrong type (`true` is not a number), the worker refuses to start
   with a configuration error and exit code 2.
   The memory store is refused unless the stage is demo (`check_store_stage` in `worker.py`, same exit 2). Pilot and
   prod need the PostgreSQL store.
   Exit codes: 0 clean stop, 2 configuration refused at start, 3 any other start failure. A store that is down at
   start is NOT an exit: the worker starts degraded, /health answers 503 and it recovers without restart.
   The worker's own code has no number for `max_running` or `conflict_events_per_minute`. It reads the
   configuration, and a settings object that lacks either is a start error.
   The 5 seconds for `ack_wait_s` named in this README is the configuration default (`defaults.py`). A `Runner`
   built directly keeps its own `ACK_WAIT_S`.
   Only the address and port have defaults, and they are command-line options (address `127.0.0.1`, port 8081:
   `--host`, `--port`). Check the worker's start line for the port it serves on.
```

## 3. README-t:671 heading, and the three places that cite it (lines 51, 163, 635)

OLD:

```
## One run at a time: what the sender must do when it is not acknowledged
```

NEW:

```
## Concurrency: max_running: what the sender must do when it is not acknowledged

Also replace every `"One run at a time"` in lines 51, 163 and 635 with `"Concurrency: max_running"`.
```

## 4. README-t:673-680 (default 4; the spend warning)

OLD:

```
In plain words: the worker handles as many runs at a time as `triggers.max_running` says.

- The setting is `max_running`; the worker has no number of its own, it reads `triggers.max_running` from the
  configuration (default in `defaults.py`). Set it to 1 until Hadavin can reserve spend before a model
  call; until then two runs side by side could together go over a spending limit (the worker warns at start).
- A second event that arrives while a run is going is not queued. The worker holds the request for up to
  `ack_wait_s` (default 5 seconds), in case the first run ends in that time, and then answers 503.
- Limit: at most 128 requests may wait at once (MAX_WAITING, worker.py:110, 329-331); a request over that gets an immediate 503.
```

NEW:

```
In plain words: the worker handles as many runs at a time as `triggers.max_running` says (default 4, at most 64).

- The setting is `max_running`; the worker has no number of its own, it reads `triggers.max_running` from the
  configuration (default 4, in `defaults.py`; the ceiling is 64) [integ:src/hadavin_sdk/defaults.py:280-281; integ:src/hadavin_sdk/defaults.py:285-287]. The main model call of a run reserves its worst-case cost before the
  call and settles after it, so runs side by side cannot go over a spending limit through the main call. The worker
  warns at start only when `max_running` is above 1 and the Runtime's limits have no `reserve`; with Hadavin's own
  limits (which have it) there is no warning. Two other sites are charged differently: the document screen
  (`_screen`) is charged after the fact, and a shadow card with a detector is not charged at all; the list is
  "Money status" in CHANGELOG.md. [integ:src/hadavin_sdk/runtime/agent_loop.py:388-392; integ:CHANGELOG.md:8]
- A second event that arrives while all `max_running` runs are going is not queued. The worker holds the request for
  up to `ack_wait_s` (default 5 seconds), in case a run ends in that time, and then answers 503. With
  `max_running` 1 this means a second event while one run is going.
- Limit: at most 128 requests may wait at once (MAX_WAITING, worker.py:110, 329-331); a request over that gets an immediate 503.
```

## 5. README-t:3 and the other places that cite files under handover/ (lines 3, 78, 82, 88, 213, 371, 563, 598, 705, 848, 866, 867)

Unchanged from the first version of this patch. In line 3 and after the first citation of each of the records 1 to 4, add the words "evidence kept in the repository's handover/ folder, not shipped". The line numbers cited into those files cannot be checked from a client's copy.

## 6. Review notes, now folded into the blocks above

- The `Runner` default `ACK_WAIT_S` for a Runner built directly: folded into item 2.
- Cite the ceiling (`defaults.py:281`) and the conflict defaults (`defaults.py:285-287`) as well as `TRIGGER_MAX_RUNNING`: folded into item 4 as proofs.
- "Ungated sites": only `_screen` is read in code (`limits.charge`, `agent_loop.py:392`); the shadow card and `k1b/evals` statements are core-b's CHANGELOG text and are not checked here. Item 4 now says so by citing that text.
- "Exit 2 for an out-of-bounds value": read, not run: `load_config` raises a configuration error and `main` returns exit 2.
- Post-merge TEST still to add on the merged tree (cannot be written on core-a alone): `worker.CONFLICT_EVENTS_PER_MINUTE == defaults.TRIGGER_CONFLICT_EVENTS_DEFAULT`, so the Runner default cannot drift from core-b's default.
