import base64, json, re, sys, types
from hadavin_sdk.k1b import redaction as R
from hadavin_sdk.guard import runmap
from hadavin_sdk.approvals import channel, slack_channel
from hadavin_sdk.approvals.channel import clean

def b64(s): return base64.b64encode(s.encode()).decode()

def walk(obj, passes=2):
    """redact_bundle's own two-pass method over one object, one map."""
    mapping = runmap.RunMap()
    def mask(s):
        try: return runmap.redact_untrusted(s, mapping)
        except runmap.TooDeep: return R.MASKED
    R._walk(obj, mask)
    return R._walk(obj, mask)

def slack(text):
    req = types.SimpleNamespace(summary=text, current_step=0, steps=[1], status="PENDING", approval_id="a", plan_hash="h")
    me = types.SimpleNamespace(max_card_chars=100000, _who=lambda x: x)
    b = slack_channel.SlackChannel._blocks(me, req, None)
    return b[0]["text"]["text"]

def js(x): return json.dumps(x, ensure_ascii=True, sort_keys=True)
def squash(s): return re.sub(r"\s+", "", s)
def readable(secret, out):
    t = out if isinstance(out, str) else js(out)
    t2 = t.replace("\\n", "\n")
    return secret in t or squash(secret) in squash(t2)
def path_src():
    import hadavin_sdk; return hadavin_sdk.__file__
