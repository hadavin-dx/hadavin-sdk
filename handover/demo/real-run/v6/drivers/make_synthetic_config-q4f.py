"""Build a SYNTHETIC real-run config from scripts/real-run.env.example (made-up values only, nothing real).

usage: make_synthetic_config.py REPO_ROOT OUT_DIR [VAR=VALUE ...] [-VAR ...]
 - reads REPO_ROOT/scripts/real-run.env.example, substitutes the <...> placeholders with local made-up paths,
 - uncomments nothing; VAR=VALUE adds or replaces a name, -VAR removes a name,
 - writes OUT_DIR/real-run.env and the key files OUT_DIR/secrets/*.txt (one line each, made-up-key-NNNN built at run time),
 - prints the made-up key strings (one per line, to OUT_DIR/made-up-keys.txt) so a caller can grep outputs for them.
Hosts are loopback or the unroutable reserved names; no value can reach a real service."""
import re
import sys
from pathlib import Path

repo, out = Path(sys.argv[1]), Path(sys.argv[2])
over = sys.argv[3:]
(out / "secrets").mkdir(parents=True, exist_ok=True)
(out / "run").mkdir(parents=True, exist_ok=True)
keys = {}
for n, name in enumerate(("hubspot-key", "sender-app-password", "second-app-password"), 1):
    k = "made-up-" + "key-" + f"{n:04d}"
    keys[name] = k
    (out / "secrets" / f"{name}.txt").write_text(k + "\n", encoding="utf-8")
(out / "made-up-keys.txt").write_text("\n".join(keys.values()) + "\n", encoding="utf-8")
text = (repo / "scripts" / "real-run.env.example").read_text(encoding="utf-8")
text = text.replace("<PRIVATE_FOLDER>\\real-run.env", str(out / "real-run.env"))
text = text.replace("<RUN_FOLDER>\\", str(out / "run") + "/").replace("<SECRETS_FOLDER>\\", str(out / "secrets") + "/")
text = text.replace("<HUBSPOT_ADDRESS>", "http://127.0.0.1:9").replace("<IMAP_HOST>", "localhost")
text = text.replace("<HOST>", "localhost")  # the one placeholder that is a host name (loopback)
lines = text.splitlines()
vals = {}
order = []
for raw in lines:
    s = raw.strip()
    if s and not s.startswith("#") and "=" in s:
        k, v = s.split("=", 1)
        vals[k.strip()] = v.strip()
        order.append(k.strip())
for o in over:
    if o.startswith("-"):
        vals.pop(o[1:], None)
    else:
        k, v = o.split("=", 1)
        if k not in vals:
            order.append(k)
        vals[k] = v
vals.setdefault("DESK_HUBSPOT_ALLOW_ANY_BASE_URL", "yes")
order.append("DESK_HUBSPOT_ALLOW_ANY_BASE_URL") if "DESK_HUBSPOT_ALLOW_ANY_BASE_URL" not in order else None
body = "".join(f"{k}={vals[k]}\n" for k in order if k in vals)
(out / "real-run.env").write_text(body, encoding="utf-8")
leftover = re.findall(r"<[A-Z_]+>", body)
if leftover:
    sys.exit("placeholder left: " + ",".join(leftover))
print(out / "real-run.env")
