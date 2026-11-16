"""Rung probe for P5a (made-up data only). Prints raw results."""
import io, json, logging, sys, traceback, warnings
warnings.filterwarnings("ignore")

NAME = "Jane" + " " + "Doe"
LOCAL = "jane" + "." + "doe"
DOM = "example" + ".invalid"
# (label, message text a foreign library might put in str(exc), canary substring that must not survive)
ROWS = [
    ("plain_email", f"bad value {LOCAL}@{DOM} in column 3", LOCAL),
    ("name_in_valueerror", f"invoice total 1234.56 does not match line items for {NAME} Holdings", NAME),
    ("qp_email", f"cannot parse {LOCAL}=40{DOM}", LOCAL),
    ("pct_email", f"cannot parse {LOCAL}%40{DOM}", LOCAL),
    ("fullwidth_email", "cannot parse " + "".join(chr(ord(c) + 0xFEE0) if c.isascii() and c.isalpha() else c for c in LOCAL) + "＠" + DOM, LOCAL),
    ("zerowidth_email", "cannot parse " + "​".join(LOCAL) + "@" + DOM, LOCAL),
    ("cyrillic_name", "customer " + "Jane".replace("a", "а") + " Doe unknown", "Doe"),
    ("iban_spaced_lower", "account de89 3704 0044 0532 0130 00 rejected", "05320130"),
    ("iban_plain", "account DE89370400440532013000 rejected", "05320130"),
]

import unicodedata
_CONF = {"\u0430": "a", "\u0435": "e", "\u043e": "o"}
def _fold(t):
    t = unicodedata.normalize("NFKC", t)
    t = "".join(_CONF.get(c, c) for c in t if c not in "\u200b\u200c\u200d\ufeff")
    return t.casefold().replace(" ", "")
def survives(out, canary):
    # folded check: NFKC, drop zero-width, map 3 Cyrillic look-alikes, casefold, drop spaces
    # a leak = the whole canary, or all but its last character, still readable (partial masking is not a pass)
    return _fold(canary)[:-1] in _fold(out)

print("=== A. scrubbers on foreign message text (rung 4: scrubadub 2.0.1) ===")
import scrubadub
s = scrubadub.Scrubber()
a_hit = 0
for label, msg, can in ROWS:
    out = s.clean(msg)
    leak = survives(out, can)
    a_hit += leak
    print(f"{label:20s} LEAK={leak!s:5s} out={out!r}")
print(f"scrubadub: {a_hit} of {len(ROWS)} rows still hold the canary")

print("\n=== B. scrubbers (rung 4: presidio-analyzer 2.2.366, spaCy en_core_web_sm 3.8.0, default recognizers) ===")
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
nlp = NlpEngineProvider(nlp_configuration={"nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]}).create_engine()
eng = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])
b_hit = 0
for label, msg, can in ROWS:
    res = eng.analyze(text=msg, language="en")
    out = msg
    for r in sorted(res, key=lambda r: -r.start):
        out = out[: r.start] + "<X>" + out[r.end :]
    leak = survives(out, can)
    b_hit += leak
    print(f"{label:20s} LEAK={leak!s:5s} found={[r.entity_type for r in res]} out={out!r}")
print(f"presidio: {b_hit} of {len(ROWS)} rows still hold the canary")

print("\n=== C. pydantic 2.14.1 ValidationError: what the safe-looking options still return ===")
import pydantic
from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic_core import PydanticCustomError
import uuid
print("pydantic", pydantic.VERSION)
class M(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ident: uuid.UUID
    amount: int
try:
    M.model_validate({"ident": "J" + "ane-not-a-uuid", "amount": 1, NAME.replace(" ", "_"): 1})
except ValidationError as e:
    for ent in e.errors(include_url=False, include_context=False, include_input=False):
        print("entry", ent)
    print("str(e) contains canary:", NAME.replace(" ", "_") in str(e))
class C(BaseModel):
    x: int
    from pydantic import field_validator
    @field_validator("x")
    @classmethod
    def v(cls, val):
        raise PydanticCustomError("bad_" + NAME.replace(" ", "_"), "nope")
try:
    C(x=1)
except ValidationError as e:
    ent = e.errors(include_url=False, include_context=False, include_input=False)[0]
    print("custom error type field =", repr(ent["type"]), "-> 'type' is NOT always a closed name")

print("\n=== D. logging / structlog / traceback default rendering of an exception ===")
exc = ValueError(f"invoice total 1234.56 for {NAME}")
try:
    raise exc
except ValueError as e:
    tb = "".join(traceback.format_exception(e))
    print("traceback.format_exception holds canary:", NAME in tb)
    buf = io.StringIO()
    h = logging.StreamHandler(buf)
    lg = logging.getLogger("probe"); lg.addHandler(h); lg.propagate = False
    lg.exception("step failed")
    print("logging.exception output holds canary:", NAME in buf.getvalue())
    import structlog
    out = structlog.processors.format_exc_info(None, "error", {"event": "step failed", "exc_info": True})
    print("structlog format_exc_info holds canary:", NAME in json.dumps(out))
    cap = io.StringIO()
    structlog.configure(processors=[structlog.processors.format_exc_info, structlog.processors.JSONRenderer()], logger_factory=structlog.PrintLoggerFactory(file=cap))
    structlog.get_logger().error("step failed", exc_info=True)
    print("structlog JSON log line holds canary:", NAME in cap.getvalue())
