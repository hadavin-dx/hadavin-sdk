# agent-killswitch

**Your AI agents need an emergency stop button.**

[![PyPI](https://img.shields.io/pypi/v/agent-killswitch)](https://pypi.org/project/agent-killswitch/)
[![Python](https://img.shields.io/pypi/pyversions/agent-killswitch)](https://pypi.org/project/agent-killswitch/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)]()
[![CI](https://img.shields.io/github/actions/workflow/status/veerarakesh56/agent-killswitch/ci.yml?branch=main)](https://github.com/veerarakesh56/agent-killswitch/actions)

Operational safety controls for autonomous AI agents. Kill switch, heartbeat monitor, circuit breaker, and budget controls -- with **zero required dependencies**.

---

## Why?

Autonomous AI agents are powerful, but they can go wrong. They can:
- **Run away** -- looping infinitely, burning tokens and money
- **Go rogue** -- taking actions you never intended
- **Cascade fail** -- one broken agent takes down an entire crew
- **Go silent** -- hanging without responding, consuming resources

**agent-killswitch** gives you an infrastructure-level emergency stop that operates *outside* the agent's reasoning path. The agent cannot talk its way out of being killed.

---

## What happens without vs. with agent-killswitch

| Scenario | Without | With agent-killswitch |
|---|---|---|
| Runaway agent burning $50/hr | Notice hours later in billing | Budget kill triggers at $50 limit |
| Agent making harmful API calls | Hope the LLM stops itself | KILL activates in <500ms |
| Agent crew member dies | Other agents wait forever | Heartbeat detects death, cascading kill cleans up |
| API provider goes down | Agents retry forever | Circuit breaker fails fast after 3 failures |
| Need to stop everything NOW | SSH into servers, kill processes | `ks.activate(KillLevel.KILL, KillScope.GLOBAL)` |

---

## Quick Start

```bash
pip install agent-killswitch
```

Kill an agent in 3 lines:

```python
from agent_killswitch import KillSwitch, KillLevel, KillScope

ks = KillSwitch()
ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="emergency shutdown")
```

Check before every agent action:

```python
status = ks.check(scope_target="my-agent")
if status.is_killed:
    print(f"KILLED: {status.level} - {status.reason}")
    return  # Stop immediately
```

---

## Architecture

```
+--------------------------------------------------+
|              Your Application                     |
|                                                   |
|  +----------+  +----------+  +----------+        |
|  | Agent A  |  | Agent B  |  | Agent C  |        |
|  +----+-----+  +----+-----+  +----+-----+        |
|       |              |              |              |
|  +----v--------------v--------------v---------+   |
|  |          agent-killswitch                  |   |
|  |                                            |   |
|  |  +------------+  +----------+  +--------+  |   |
|  |  | KillSwitch |  | Heartbeat|  | Circuit|  |   |
|  |  | PAUSE/STOP |  | Monitor  |  | Breaker|  |   |
|  |  | /KILL      |  +----------+  +--------+  |   |
|  |  +------------+                             |   |
|  |  +------------+  +----------+               |   |
|  |  | Budget     |  | Cascading|               |   |
|  |  | Kill       |  | Terminate|               |   |
|  |  +------------+  +----------+               |   |
|  |                                            |   |
|  |  +---------+  (InMemory or Redis)          |   |
|  |  | Backend |                               |   |
|  |  +---------+                               |   |
|  +--------------------------------------------+   |
+--------------------------------------------------+
```

---

## Features

### Kill Switch (3 tiers)

| Level | Behavior | Latency Guarantee |
|-------|----------|-------------------|
| **PAUSE** | Stop new tasks, in-flight complete normally | <200ms |
| **STOP** | Checkpoint in-flight tasks, pause all activity | <300ms |
| **KILL** | Terminate everything immediately | <500ms |

```python
from agent_killswitch import KillSwitch, KillLevel, KillScope

ks = KillSwitch()

# Scoped kills
ks.activate(KillLevel.PAUSE, KillScope.AGENT, scope_target="agent-1")
ks.activate(KillLevel.STOP, KillScope.CREW, scope_target="research-crew")
ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="everything must stop")

# Priority: GLOBAL > CREW > AGENT > TASK
status = ks.check(scope_target="agent-1", crew_id="research-crew")
```

### Heartbeat Monitor

```python
from agent_killswitch import HeartbeatMonitor

monitor = HeartbeatMonitor(
    interval_seconds=5.0,
    miss_threshold=3,
    on_dead=lambda agent_id: print(f"DEAD: {agent_id}"),
)

monitor.start("agent-1")
monitor.heartbeat("agent-1")  # Call periodically
dead_agents = monitor.get_dead_agents()
```

### Circuit Breaker

```python
from agent_killswitch import CircuitBreaker, CircuitBreakerOpen

breaker = CircuitBreaker(
    name="openai-api",
    failure_threshold=5,
    recovery_timeout=30.0,
)

try:
    result = breaker.call(call_openai_api, prompt)
except CircuitBreakerOpen:
    result = use_fallback(prompt)
```

### Budget Kill Trigger

```python
from agent_killswitch import BudgetKillTrigger, KillSwitch

ks = KillSwitch()
budget = BudgetKillTrigger(killswitch=ks, kill_on_exceed=True)

budget.set_budget("agent-1", limit=50.0)  # $50 max
budget.track_cost("agent-1", 10.0)  # Track each API call cost
# Auto-kills when budget exceeded
```

### Cascading Termination

```python
from agent_killswitch import KillSwitch, KillLevel
from agent_killswitch.core.cascading import CascadingTerminator

ks = KillSwitch()
cascade = CascadingTerminator(killswitch=ks)

ks.register_agent("supervisor")
ks.register_agent("worker-1", parent_id="supervisor")
ks.register_agent("worker-2", parent_id="supervisor")

# Kill supervisor -> workers cascade
cascade.cascade_kill("supervisor", KillLevel.KILL, reason="parent failed")
```

### Decorators

```python
from agent_killswitch import killswitch_protected, with_heartbeat
from agent_killswitch.decorators import circuit_breaker

ks = KillSwitch()
monitor = HeartbeatMonitor()


@killswitch_protected(killswitch=ks, agent_id="my-agent")
async def my_agent_task(): ...


@with_heartbeat(monitor=monitor, agent_id="my-agent", interval=5.0)
async def long_running_agent(): ...


@circuit_breaker(name="openai", failure_threshold=5, recovery_timeout=30)
async def call_openai(prompt: str) -> str: ...
```

---

## Framework Integrations

### LangChain

```python
from agent_killswitch.integrations.langchain import KillSwitchCallbackHandler

handler = KillSwitchCallbackHandler(killswitch=ks, agent_id="my-agent")
llm = ChatOpenAI(callbacks=[handler])
```

### LangGraph

```python
from agent_killswitch.integrations.langgraph import KillSwitchNode

ks_node = KillSwitchNode(killswitch=ks, agent_id="graph-agent")
graph.add_node("check_kill", ks_node)
graph.add_conditional_edges(
    "check_kill",
    ks_node.should_continue,
    {
        "continue": "agent_work",
        "killed": "terminated",
    },
)
```

### CrewAI

```python
from agent_killswitch.integrations.crewai import KillSwitchHook

hook = KillSwitchHook(killswitch=ks, crew_id="my-crew")
if hook.before_action(agent_id="researcher"):
    # Action is allowed
    ...
```

### OpenAI Agents SDK

```python
from agent_killswitch.integrations.openai_agents import KillSwitchGuardrail

guardrail = KillSwitchGuardrail(killswitch=ks, agent_id="openai-agent")
result = guardrail.check_input("user message")
```

### asyncio

```python
from agent_killswitch.integrations.asyncio_tasks import KillSwitchTaskGroup

group = KillSwitchTaskGroup(killswitch=ks, agent_id="async-agent")
group.add_task(worker_coro())
results = await group.run()  # Cancelled if kill switch activates
```

---

## Backends

| Backend | Dependencies | Use Case |
|---------|-------------|----------|
| `InMemoryBackend` | None (default) | Single process, testing |
| `RedisBackend` | `redis[hiredis]` | Distributed, production |

```python
# Default: in-memory (zero dependencies)
ks = KillSwitch()

# Redis: distributed
import redis
from agent_killswitch.backends.redis import RedisBackend

client = redis.Redis(host="localhost")
ks = KillSwitch(backend=RedisBackend(client, prefix="myapp:ks:"))
```

Custom backends implement the `KillSwitchBackend` protocol.

---

## Safety Design Principles

1. **Fail-closed**: If the backend is unreachable, default to KILLED state
2. **Outside the reasoning path**: Kill switch is checked at infrastructure level, not in the agent's prompt
3. **No TTL**: Kill switches require explicit deactivation to prevent accidental resumption
4. **Audit trail**: Every activation is logged immutably
5. **Thread-safe**: All operations protected by locks
6. **Async-safe**: Full async support for all operations

---

## Performance

| Operation | Latency (p99) | Throughput |
|-----------|--------------|------------|
| `activate()` | <1ms | >100k ops/sec |
| `check()` | <0.1ms | >1M ops/sec |
| `heartbeat()` | <0.1ms | >1M ops/sec |

All with InMemoryBackend. Redis backend adds network RTT (~0.5ms).

---

## Installation

```bash
# Core (zero dependencies)
pip install agent-killswitch

# With Redis support
pip install agent-killswitch[redis]

# With framework integrations
pip install agent-killswitch[langchain]
pip install agent-killswitch[langgraph]
pip install agent-killswitch[crewai]
pip install agent-killswitch[openai]

# Everything
pip install agent-killswitch[all]

# Development
pip install agent-killswitch[dev]
```

---

## License

Apache 2.0 -- see [LICENSE](LICENSE).
