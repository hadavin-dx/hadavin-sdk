"""Stub for the fail-before measurement only: names exist so the test files import; every function fails."""
from hadavin_sdk.errors import ConfigError
MAX_COMPONENT_BYTES = 255
MAX_PATH_CHARS = 4096
class PathRefused(ConfigError):
    def __init__(self, rule, message):
        super().__init__(message); self.rule = rule
def _no(*a, **k): raise NotImplementedError("stub")
component = inside = join = operator_dir = operator_file = _no
