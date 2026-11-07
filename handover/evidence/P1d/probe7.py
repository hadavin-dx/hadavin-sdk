import sys; sys.path.insert(0, sys.argv[1])
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
K = "AKIA" + "IOSFODNN7" + "EXAMPLE"; S = "wJalr" + "XUtnFEMI/K7MDENG/bPxRfi" + "CYEXAMPLEKEY"
rows = {"H10": f"password={S} and {S[:6]}&amp;{S[6:]} x", "H12a": f"key {K[:4]}\x1b[38;5;196m{K[4:]} x", "H12b": f"key {K[:4]}\x9b0m{K[4:]} x",
 "H12c": f"key {K[:4]}\x1b]8;;http://x\x1b\\{K[4:]} x", "H18b": f"key {K[:4]}̣{K[4:]} x", "H20": f"key {K[:4]}＊{K[4:]} x",
 "F13": "Approve αρχείο for Москва team", "F01b": "Approve **restart** of `web-01` in ~~old~~ demo?",
 "F12": "role arn:aws:iam::" + "1234" + "5678" + "9012:role/x and account " + "1234" + "5678" + "9012",
 "pw_ent": f"password={S[:5]}&amp;{S[5:]} end"}
for n, t in rows.items():
    try: r = "PASS    " + repr(clean(t))[:90]
    except runmap.RedactionError as e: r = "REFUSED " + type(e).__name__
    print(f"{n:6} {r}")
