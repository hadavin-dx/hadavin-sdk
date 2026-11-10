"""P9: S8b host:port and S8c colon-after-identifier shapes. usage: PYTHONPATH=<tree>/src python p9_s8.py"""
from hadavin_sdk.guard import runmap
for t in ("x session_timeout: 30d y", "x session: 30d y", "x db.token.example.com:5432 y", "x token-service:8080 y", "x session_store_backend_name_long_enough: redis y", "x password: 30d y", "x secret_manager_region_setting=eu y", "x api.session.local:443/path y"):
    print(repr(t), "->", repr(runmap.redact_text(t, runmap.RunMap())))
