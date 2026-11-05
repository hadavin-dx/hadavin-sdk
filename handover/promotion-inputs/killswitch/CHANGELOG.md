# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-07

### Added

- Core `KillSwitch` class with tiered levels (PAUSE/STOP/KILL) and scoped targets (GLOBAL/CREW/AGENT/TASK)
- `HeartbeatMonitor` for tracking agent health with configurable intervals and miss thresholds
- `CircuitBreaker` pattern with CLOSED/OPEN/HALF_OPEN states
- `BudgetKillTrigger` for automatic kills when cost budgets are exceeded
- `CascadingTerminator` for parent-child agent hierarchy termination
- `InMemoryBackend` (zero dependencies, default)
- `RedisBackend` (optional, for distributed systems)
- Decorators: `@killswitch_protected`, `@with_heartbeat`, `@circuit_breaker`
- LangChain integration (callback handler)
- LangGraph integration (node and conditional edge)
- CrewAI integration (pre-action hook)
- OpenAI Agents SDK integration (guardrail)
- asyncio integration (task group cancellation)
- Fail-closed safety: backend failures default to KILLED state
- Full audit trail for all kill events
- Thread-safe and async-safe implementations
- Type hints on all public APIs
- py.typed marker for PEP 561
