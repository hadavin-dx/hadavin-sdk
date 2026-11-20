# Request 004 (core-a to core-b): one shared "qualified agents" helper

Found in code review round 3 (minor). The same loop exists three times:
- `src/hadavin_sdk/cli.py` (tick: builds the App with every qualified agent, skips an unqualified one with a stderr line),
- `src/hadavin_sdk/triggers/worker.py` `qualified_agents(registry)` (the trigger worker: skips with a WARNING on `hadavin_sdk.triggers`),
- `src/hadavin_sdk/runtime/agent_loop.py` `Runtime.__init__` (strict: raises `Unqualified` for the first one).

core-a changed only its own copy (now public, one function inside `triggers`). Core-a does not edit cli.py or agent_loop.py.

Ask: one function in `runtime/agent_loop.py`, for example
`qualified_agents(registry, on_unqualified: Callable[[str], None] | None = None) -> list[str]`
(every agent id for which `assert_qualified` passes; calls `on_unqualified(agent_id)` for each other one).
cli.py and `triggers/worker.py` then pass their own message writer. When it lands, core-a deletes the copy in worker.py
(one import; the tests call `worker.qualified_agents` and are moved by name).
