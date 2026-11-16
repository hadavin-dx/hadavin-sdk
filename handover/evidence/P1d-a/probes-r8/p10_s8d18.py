"""P10: shape S8d, all 18 samples (6 names x 3 tails), card path and model path; counts samples where the placeholder count of the output is higher than the base's
(`hidden`). usage: PYTHONPATH=<tree>/src python p10_s8d18.py > out   (run on the orig tree and the P10 tree; compare by eye or with the counts line)"""
import re
from hadavin_sdk.approvals import channel
from hadavin_sdk.guard import runmap
NAMES = ["com.example.service.token.refresh", "db.password.rotation.internal.example.com", "credential-sync.corp.example.com",
         "secret-store-prod-eu.example.com", "app.auth.token.TokenRefreshWorker", "token-service.internal.example.com"]
TAILS = [": connection lost", ":5432 ready", ": retry 2 of 5"]
PH = re.compile(r"<[A-Z][A-Z0-9]*_[0-9]+>")
n = 0
for nm in NAMES:
    for t in TAILS:
        x = "x " + nm + t + " y"
        c = channel.clean(x); m = runmap.redact_text(x, runmap.RunMap())
        print(len(PH.findall(c)), len(PH.findall(m)), repr(c), repr(m))
