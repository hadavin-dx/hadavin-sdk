import logging, io
from pydantic import ValidationError
from hadavin_sdk.config import Route
base = {"input_usd_per_mtok": "1", "output_usd_per_mtok": "1", "max_tokens": 10}
def try_route(label, text):
    try:
        r = Route(model_id=text, **base); print(f"ROUTE {label}: ACCEPTED {text[:60]!r} len={len(text)}")
    except ValidationError as e:
        msg = str(e).replace(text, "<value>") if len(text) > 8 else str(e)
        print(f"ROUTE {label}: REFUSED len={len(text)} :: {str(e).splitlines()[-1][:160]}"); print("   echoes value in message:", text in str(e))
part = "A1"*16
cases = [
 ("bare bedrock-shaped id", "anthropic.claude-sonnet-5-5-v1:0"),
 ("bare bedrock-shaped id w/ region prefix", "us.anthropic.claude-haiku-5-5-v1:0"),
 ("with space", "claude sonnet-5-5"),
 ("129 chars", "a"*129), ("128 chars", "a"*128),
 ("32 alnum run", part), ("32 alnum run in middle", "x-"+part+"-y"),
 ("31 alnum run", "A"*31), ("empty", ""), ("newline", "claude-x\n"),
]
for l,t in cases: try_route(l,t)
# tick
from hadavin_sdk.runtime import tick
marker = "zq-probe-" + "Kx7" + "-marker"
print("TICK _message RuntimeError:", repr(tick._message(RuntimeError(marker))))
print("TICK _message ValueError:", repr(tick._message(ValueError(marker))))
print("TICK _message ConfigError:", repr(tick._message(tick.ConfigError(marker))))
logging.basicConfig(stream=(buf:=io.StringIO()), level=logging.DEBUG, format="%(levelname)s %(name)s %(message)s")
def boom(i): raise RuntimeError(marker)
try:
    tick._each([1], boom, "probe step"); print("TICK _each returned normally")
except BaseException as e:
    print("TICK _each raised", type(e).__name__, repr(str(e)))
print("LOG OUTPUT:\n"+buf.getvalue()); print("marker in log:", marker in buf.getvalue())
# DSN with sslmode
from hadavin_sdk.store.postgres import tls_mode
from hadavin_sdk.errors import ConfigError
odd = "zq-probe-" + "ssl" + "-Wm4"
for label, dsn, kw in [
  ("odd sslmode, iam_auth", f"host=db.example.invalid dbname=d user=u sslmode={odd}", {"iam_auth":True}),
  ("odd sslmode, no iam", f"host=db.example.invalid dbname=d user=u sslmode={odd}", {}),
  ("sslmode=require, iam", "host=db.example.invalid dbname=d user=u sslmode=require", {"iam_auth":True}),
  ("sslmode=disable, iam", "host=db.example.invalid dbname=d user=u sslmode=disable", {"iam_auth":True}),
  ("sslmode=verify-full, iam", "host=db.example.invalid dbname=d user=u sslmode=verify-full", {"iam_auth":True}),
  ("URI sslmode odd, iam", f"postgresql://u@db.example.invalid/d?sslmode={odd}", {"iam_auth":True}),
]:
    try: print("DSN", label, "->", repr(tls_mode(dsn, **kw)))
    except ConfigError as e: print("DSN", label, "-> ConfigError:", str(e)[:300], "| odd echoed:", odd in str(e))
