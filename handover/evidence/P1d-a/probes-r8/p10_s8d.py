"""P10: S8d shapes (logger / host names that contain a keyword, then `:` and a message or port). usage: PYTHONPATH=<tree>/src python p10_s8d.py"""
from hadavin_sdk.approvals import channel
for x in ["com.example.service.token.refresh: connection lost",
          "db.password.rotation.internal.example.com:5432 ready",
          "credential-sync.corp.example.com:8443 up",
          "secret-store-prod-eu.example.com: timeout after 3 s",
          "app.auth.token.TokenRefreshWorker: retry 2 of 5",
          "password=abc123Xyz9 then db01.corp.example.com:5432"]:
    print(repr(x), "->", repr(channel.clean(x)))
