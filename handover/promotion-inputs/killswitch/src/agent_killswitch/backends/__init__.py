"""Backend implementations for kill switch state storage.

Available backends:
- InMemoryBackend: Zero-dependency, thread-safe, dict-based (default)
- RedisBackend: Distributed, Redis-backed (optional dependency)
- KillSwitchBackend: Protocol for custom backends
"""

from __future__ import annotations

from .base import KillSwitchBackend
from .memory import InMemoryBackend

__all__ = [
    "InMemoryBackend",
    "KillSwitchBackend",
]

# RedisBackend is intentionally not imported here to avoid
# requiring the redis dependency. Import it directly:
#   from agent_killswitch.backends.redis import RedisBackend
