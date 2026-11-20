# Post-merge patch for n8n/README-trigger.md (core-a, d-fix24)

Apply AFTER core-b's `TriggerSettings` (config.py) and core-b's limits (`reserve`/`settle`) are merged. Do NOT apply on
core-a alone: on this branch the `triggers` block is not in the config code. Each block below is an exact OLD text
(line numbers of n8n/README-trigger.md on core-a) and its exact NEW text. Checked against the merged tree
`/home/user/wt/integ` (read-only): `config.py` 395-425 (`TriggerSettings`: `tenant` and `senders` have no default,
`max_body_bytes`, `max_running` default 4, `ack_wait_s` default 5.0, `conflict_events_per_minute` default 10, all
with bounds); `defaults.py:280-282` (`TRIGGER_MAX_RUNNING = 4`, `TRIGGER_ACK_WAIT_S = 5.0`); `limits.py:86,170`
(`reserve`, `settle`); `triggers/worker.py` `check_spend` (warns only when `max_running` > 1 and the runtime's
limits have no `reserve`), `trigger_settings` (a missing `triggers:` block is a ConfigError, exit 2).

## 1. README-t:51-54 (item 6 of the findings: the block IS in the config code after the merge)

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
   code 2 (stated limit 7); the operator has to say how the senders are wired in. The memory store is refused outside the demo stage (exit 2, "the memory store is for the demo stage only"): pilot and prod need the PostgreSQL store.
```

## 2. README-t:803-808 (item 7: only tenant and senders are required)

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
7. The `triggers` block of the configuration has two required fields, `tenant` and `senders`; the rest have defaults
   (`max_running` 4, `ack_wait_s` 5.0 seconds, `max_body_bytes`, `conflict_events_per_minute` 10), each with a lower
   and an upper bound that the configuration load checks. If the block is missing, a required field is missing, or a
   value is out of bounds or of the wrong type (`true` is not a number), the worker refuses to start with a
   configuration error and exit code 2. The memory store is refused unless the stage is demo (`check_store_stage` in `worker.py`, same exit 2): pilot and prod need the PostgreSQL store. Exit codes: 0 clean stop, 2 configuration refused at start, 3 any other start failure; a store that is down at start is NOT an exit: the worker starts degraded, /health answers 503 and it recovers without restart. The worker's own code has no number for `max_running` (it reads the configuration); the 5 seconds for `ack_wait_s` named in this README is the configuration default. Only the address and port have defaults, and they are command-line
   options (address `127.0.0.1`, port 8081: `--host`, `--port`). Check the worker's start line for the port it serves on.
```

## 3. README-t:671 heading (item 10) and the three places that cite it (lines 51, 163, 635)

OLD:

```
## One run at a time: what the sender must do when it is not acknowledged
```

NEW:

```
## Concurrency: max_running: what the sender must do when it is not acknowledged

Also replace every `"One run at a time"` in lines 51, 163 and 635 with `"Concurrency: max_running"`.
```

## 4. README-t:673-680 (items 8 and 10: default 4, the warning)

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
  configuration (default 4, in `defaults.py`). The main model call of a run reserves its worst-case cost before the
  call and settles after it, so runs side by side cannot go over a spending limit through the main call. The worker
  warns at start only when `max_running` is above 1 and the Runtime's limits have no `reserve`; with Hadavin's own
  limits (which have it) there is no warning. The ungated sites (document screen, shadow cards, k1b/evals) are
  still charged after the fact.
- A second event that arrives while all `max_running` runs are going is not queued. The worker holds the request for
  up to `ack_wait_s` (default 5 seconds), in case a run ends in that time, and then answers 503. With
  `max_running` 1 this means a second event while one run is going.
```

## 5. README-t:3 and the other places that cite files under handover/ (item 9; lines 3, 78, 82, 88, 213, 371, 563, 598, 705, 848, 866, 867)

OLD:

```
Every citation of the form  (`handover/core-a/inputs/evidence-n8n-N.md`, ...)  or  `handover/core-a/<file>`  in those lines.
```

NEW:

```
Keep the citation, add after its first use in line 3 (and keep it as the only wording elsewhere): "evidence kept in the
repository's handover/ folder, not shipped". Example for line 3, replace
`(fourth record, \`handover/core-a/inputs/evidence-n8n-4.md\`, head ...` with
`(fourth record, evidence kept in the repository's handover/ folder, not shipped: \`handover/core-a/inputs/evidence-n8n-4.md\`, head ...`
The same note goes once after the first citation of each of the records 1, 2 and 3 in line 3. The line numbers cited
("line 46", "lines 47 and 48", ...) point into those files and cannot be checked from a client's copy.
```

## Review notes (fresh reviewer rev-dfix24, 16:30 UTC): apply when merging
- The sentence 'the 5 seconds for `ack_wait_s` is the configuration default' omits that `Runner` keeps its own `ACK_WAIT_S` default for directly built runners: say 'the configuration default (core-b's defaults.py); a Runner built directly keeps its own ACK_WAIT_S'.
- The header cites `defaults.py:280-282`: line 281 is the ceiling (`TRIGGER_MAX_RUNNING_CEILING` = 64); the conflict defaults are at defaults.py:285-287: cite both.
- 'ungated sites are still charged after the fact' is verified only for `agent_loop.py:392` (`limits.charge`) and `k1b/loop.py:165-201`; the document-screen and shadow-card sites were not verified.
- The 'exit 2' for an out-of-bounds value assumes config load maps to exit 2: not verified.
- Post-merge TEST to add (cannot be written on core-a alone): `worker.CONFLICT_EVENTS_PER_MINUTE == defaults.TRIGGER_CONFLICT_EVENTS_DEFAULT`, so the Runner default cannot drift from core-b's default.
