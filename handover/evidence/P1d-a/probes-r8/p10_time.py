"""P10: card-path timing (HL2). usage: PYTHONPATH=<tree>/src python p10_time.py [N...]   (median of 3; seconds; exception name if refused)"""
import sys, time, statistics
from types import SimpleNamespace
from hadavin_sdk.approvals import channel, slack_channel
from hadavin_sdk import defaults
sizes = [int(a) for a in sys.argv[1:]] or [65536, 262144]
def rep(s, n): return (s * n)[:n]
IN = {"H1": lambda n: rep("pwd", n), "H6": lambda n: rep("?password=&a", n), "H10": lambda n: rep("a.a.-", n),
      "[": lambda n: "[" * n, ">": lambda n: ">" * n, "bt1": lambda n: "`" * n, "bt3": lambda n: rep("``` ", n), "bt2": lambda n: rep("`a` `", n),
      "ph.": lambda n: rep("<A_1>.", n), "[.]": lambda n: rep("[.]", n), "&amp;": lambda n: rep("&amp;", n), "dom": lambda n: rep("db01.corp.example.com ", n),
      "nl": lambda n: rep("`a\n", n)}
sl = slack_channel.SlackChannel.__new__(slack_channel.SlackChannel); sl.max_card_chars = 2900
def blocks(x):
    req = SimpleNamespace(summary=x, current_step=0, steps=[1], approval_id="a", status="PENDING")
    return sl._blocks(req, None)
print("MAX_REDACT_CHARS", getattr(defaults, "MAX_REDACT_CHARS", None), "REDACT_BUDGET_S", getattr(defaults, "REDACT_BUDGET_S", None))
for name, g in IN.items():
    for n in sizes:
        x = g(n); row = [name, n]
        for label, fn in (("clean", channel.clean), ("blocks", blocks)):
            ts = []
            try:
                for _ in range(3):
                    t = time.perf_counter(); fn(x); ts.append(time.perf_counter() - t)
                row.append(f"{label} {statistics.median(ts):.2f}")
            except Exception as e:
                row.append(f"{label} {type(e).__name__}")
        print(*row, flush=True)
