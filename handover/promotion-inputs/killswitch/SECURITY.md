# Security Policy

`agent-killswitch` is an operational safety control. A defect in it can mean an agent that
should have stopped did not, so security reports are taken seriously and are welcome.

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Use GitHub's private vulnerability reporting:

1. Go to the [Security tab](https://github.com/veerarakesh56/agent-killswitch/security)
2. Click **Report a vulnerability**

That channel is private between you and the maintainer, and it works without either of us
publishing an email address.

You should get an acknowledgement within **7 days**. If a report is accepted, the fix and an
advisory are published together, and you will be credited unless you ask not to be.

## What is in scope

The threat model of this package is **an agent that keeps acting after it was told to stop.**
Reports are especially valuable if they show any of the following:

- A kill switch reporting an agent as alive after `activate()` — a **missed stop**.
- A way to bypass a check: a scope that should match but does not, a `TASK`-level kill that
  fails to be caught by an agent-level check, or a cascade that leaves a child running.
- A race between `activate()` and `check()` where an agent observes stale state.
- A backend failure that silently **fails open** rather than closed.
- A way to deactivate a kill switch without authorisation, or to forge an audit event.
- Anything that lets an agent suppress, clear or evade its own kill switch.

## What is out of scope

- Vulnerabilities in the optional frameworks themselves (LangChain, LangGraph, CrewAI,
  OpenAI Agents, Redis). Report those upstream. Bugs in **this package's adapters** for them
  are in scope.
- Denial of service caused by an operator's own configuration — for example setting a
  heartbeat timeout so short that healthy agents are killed.
- The library does not authenticate callers. Any process that can import it and reach the
  backend can activate or deactivate a switch. That is a deliberate design boundary, not a
  vulnerability: authorisation belongs to the system embedding this one. If you can show a
  way to bypass a control that this package *does* claim to enforce, that is in scope.

## Supported versions

Pre-1.0, only the latest released version receives security fixes.

| Version | Supported |
|---|---|
| 0.1.x | ✅ |
