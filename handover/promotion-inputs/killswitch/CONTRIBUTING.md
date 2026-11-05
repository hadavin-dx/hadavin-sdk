# Contributing to agent-killswitch

Thank you for your interest in contributing to agent-killswitch! This document
provides guidelines and information for contributors.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/veerarakesh56/agent-killswitch.git
cd agent-killswitch

# Install in development mode
pip install -e ".[dev,all]"

# Run tests
make test

# Run linting
make lint

# Run type checking
make typecheck
```

## Running Tests

```bash
# All tests
make test

# Specific test suites
make test-unit          # Unit tests
make test-integration   # Integration tests
make test-e2e          # End-to-end tests
make test-chaos        # Chaos/fault-injection tests
make test-perf         # Performance tests
make test-security     # Security tests

# With coverage
make coverage
```

## Code Quality

We use:
- **ruff** for linting and formatting
- **mypy** for type checking
- **pytest** for testing

Before submitting a PR:

```bash
make lint       # Check for linting errors
make format     # Auto-format code
make typecheck  # Run type checker
make test       # Run all tests
```

## Architecture Principles

1. **Zero required dependencies**: Core functionality must work with Python stdlib only
2. **Fail-closed**: When in doubt, default to the safe state (KILLED)
3. **Thread-safe**: All public APIs must be safe for concurrent access
4. **Outside the reasoning path**: Kill switch operates at infrastructure level
5. **No TTL**: Kill switches require explicit deactivation
6. **Audit everything**: Every state change must be logged

## Adding a New Backend

1. Create a new file in `src/agent_killswitch/backends/`
2. Implement the `KillSwitchBackend` protocol from `backends/base.py`
3. Add tests in `tests/unit/test_backends.py`
4. Document in README.md

## Adding a New Integration

1. Create a new file in `src/agent_killswitch/integrations/`
2. The integration should be a thin adapter (minimal code)
3. Framework dependency should be optional (import in function, not at module level)
4. Add the framework to `[project.optional-dependencies]` in `pyproject.toml`
5. Add tests in `tests/integration/`
6. Add an example in `examples/`

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run all checks (`make lint && make typecheck && make test`)
5. Commit with a descriptive message
6. Push to your fork
7. Open a Pull Request

## Commit Message Format

We use conventional commits:

```
feat: add new backend for DynamoDB
fix: correct race condition in heartbeat monitor
docs: update README with new examples
test: add chaos tests for network partition
refactor: simplify circuit breaker state machine
chore: update CI to test Python 3.13
```

## Reporting Issues

Use the issue templates on GitHub:
- **Bug Report**: For bugs and unexpected behavior
- **Feature Request**: For new features and enhancements

## License

By contributing, you agree that your contributions will be licensed under
the Apache License 2.0.
