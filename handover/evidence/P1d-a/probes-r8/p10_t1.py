"""P10: one input/size/entry per process. usage: python p10_t1.py NAME N clean|blocks (seconds, one run)"""
import sys, time
from types import SimpleNamespace
from hadavin_sdk.approvals import channel, slack_channel
def rep(s, n): return (s * n)[:n]
IN = {"H1": lambda n: rep("pwd", n), "H6": lambda n: rep("?password=&a", n), "H10": lambda n: rep("a.a.-", n),
      "[": lambda n: "[" * n, ">": lambda n: ">" * n, "bt1": lambda n: "`" * n, "bt3": lambda n: rep("``` ", n), "bt2": lambda n: rep("`a` `", n),
      "ph.": lambda n: rep("<A_1>.", n), "[.]": lambda n: rep("[.]", n), "&amp;": lambda n: rep("&amp;", n), "dom": lambda n: rep("db01.corp.example.com ", n),
      "nl": lambda n: rep("`a\n", n)}
sl = slack_channel.SlackChannel.__new__(slack_channel.SlackChannel); sl.max_card_chars = 2900
def blocks(x):
    req = SimpleNamespace(summary=x, current_step=0, steps=[1], approval_id="a", status="PENDING")
    return sl._blocks(req, None)
name, n, which = sys.argv[1], int(sys.argv[2]), sys.argv[3]
x = IN[name](n); fn = channel.clean if which == "clean" else blocks
t = time.perf_counter()
try:
    fn(x); print(name, n, which, f"{time.perf_counter()-t:.2f}")
except Exception as e:
    print(name, n, which, type(e).__name__, f"{time.perf_counter()-t:.2f}")
