"""Run AS THE AGENT'S OS USER (a different user from the operator). Builds the agent's own secrets kinds the way the agent process
would (no special access) and tries to resolve the audit-reader secret name. Prints one word: DENIED (ConfigError) or READ (leak).
Usage: python -I -B agent_probe_v17.py <src> <kind: file|env> <folder-or-prefix> <name>"""
import sys, os
sys.path.insert(0, sys.argv[1])
from hadavin_sdk.errors import ConfigError
kind, where, name = sys.argv[2], sys.argv[3], sys.argv[4]
if kind == "file":
    from hadavin_sdk.actions.secrets_file import MountedFileProvider
    prov = MountedFileProvider(where)
else:
    from hadavin_sdk.actions.secrets_env import EnvSecretProvider
    prov = EnvSecretProvider(where)
try:
    v = prov.get(name); print("READ", len(v))
except ConfigError as e:
    print("DENIED", str(e)[:70])
