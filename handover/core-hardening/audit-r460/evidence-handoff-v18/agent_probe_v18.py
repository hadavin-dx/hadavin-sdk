"""Run AS THE AGENT'S OS USER (a different user from the operator). Builds the agent's own secrets kinds the way the agent process
would (no special access) and tries to resolve the audit-reader secret name. Prints one word (first token): DENIED (ConfigError) or READ (leak).
Usage: python -I -B agent_probe_v18.py <src> <kind: file|file-strict|env> <folder-or-prefix> <name>"""
import sys, os
sys.path.insert(0, sys.argv[1])
from hadavin_sdk.errors import ConfigError
kind, where, name = sys.argv[2], sys.argv[3], sys.argv[4]
if kind in ("file", "file-strict"):
    from hadavin_sdk.actions.secrets_file import MountedFileProvider
    prov = MountedFileProvider(where)
    if kind == "file-strict":  # PROTOTYPE of the S-2b rule (minor m5): the audit-reader secret file must have NO group or other bit (mode & 0o077 == 0)
        import stat
        try: mode = os.stat(os.path.join(where, name)).st_mode
        except OSError: mode = None
        if mode is not None and mode & 0o077:
            print("DENIED strict: mode", oct(mode & 0o777)); sys.exit(0)
else:
    from hadavin_sdk.actions.secrets_env import EnvSecretProvider
    prov = EnvSecretProvider(where)
try:
    v = prov.get(name); print("READ", len(v))
except ConfigError as e:
    print("DENIED", str(e)[:70])
