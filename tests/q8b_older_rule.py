"""Rules of the code BEFORE Q8b (main, 2a8c2aac), copied word for word, used as an ORACLE by `tests/test_q8b_batch4.py`: every
value the older rules masked must still be masked, piece by piece. Copied: the two quoted-value rules and the unquoted rule
(`guard/redact.py` on main, lines 577-590 and 591-616), the cookie assignment rule (lines 117 and 511), the flag rule (lines 40-44
and 541) and the `"auth"` JSON rule (line 575), and the record key rule of `k1b/redaction.py` (`SENSITIVE_KEY`, line 88). Not copied:
every other rule of main (hex keys, URLs, headers). Not imported by product code. Made-up text only."""

import re

# The two quoted-value rules (`guard/redact.py` on main, lines 577-590).
QUOTED_DQ = re.compile(
    r"(?i)(?:password|passwd|pwd|pass|secret|token|api[_\-]?key|apikey|credential|session)"
    r"[\w.\-]{0,20}[\"']?\s*[:=]\s*\"([^\"][^\"]{0,255})\""
)
QUOTED_SQ = re.compile(
    r"(?i)(?:password|passwd|pwd|pass|secret|token|api[_\-]?key|apikey|credential|session)"
    r"[\w.\-]{0,20}[\"']?\s*[:=]\s*'([^'][^']{0,255})'"
)
# The generic key=value rule (main, lines 591-616), value part as written there.
UNQUOTED = re.compile(
    r"(?i)(?<![\w.\-])[\w.\-]{0,40}"
    r"(?:password|passwd|pwd|secret|access[_\-]?key|account[_\-]?key|shared[_\-]?access[_\-]?key"
    r"|private[_\-]?key|api[_\-]?key|apikey|auth[_\-]?token|access[_\-]?token|sas[_\-]?token"
    r"|key[_\-]?data|cert(?:ificate)?[_\-]?data"
    r"|session[_\-]?id|jsessionid|phpsessid|sessid|connect\.sid"
    r"|client[_\-]?secret|credential|token|pass(?=[\"']?\s*[:=])|auth(?=[\"']?\s*[:=])"
    r"|session(?=[\"']?\s*[:=]))[\w.\-]{0,20}"
    r"[\"']?\s*[:=]\s*[\"']?"
    r"((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|[^\s\"';,&]|,(?!\s*[\w.\-]+\s*[:=]))+)"
)


# The cookie assignment rule (main, lines 117 and 511): one word, or `;`-joined `name=value` pairs, after `cookie=`.
COOKIE_ASSIGN = re.compile(
    r"(?i)(?<![A-Za-z])(?:set-)?cookies?[\"'\]]*\s*"
    r"(?:=>|=(?!>))\s*+([^\s;,\"'\[{]+(?:;\s*[^\s;=]+=[^\s;]*)*)"
)
# The flag rule (main, lines 40-44 and 541): `--` flags with a hyphen-joined prefix, `-password`, `-passwd`.
_CRED_FLAG = (
    r"(?i)(?<![\w-])(?:--(?:[a-z0-9]+-){0,2}"
    r"(?:password|passwd|pass|pwd|secret|token|api-?key|access-key|secret-key|private-key|"
    r"auth-token|access-token)|-(?:password|passwd))(?![\w-])"
)
_SP = "[ \t\u00a0\u2000-\u200a\u202f\u205f\u3000]"
FLAG_UNQUOTED = re.compile(
    _CRED_FLAG + rf"(?:=|{_SP}+(?![A-Za-z_][\w.-]*=))(?![-\"'])([^\s\"']{{3,}})"
)
AUTH_JSON = re.compile(r"(?i)\"auth\"\s*:\s*\"([^\"]{8,})\"")
# The record key rule of main (`k1b/redaction.py`, line 88): a key is a credential key when a whole word of it matches.
SENSITIVE_KEY = re.compile(
    r"(^|[_.\-\s])(pass(word|wd|phrase)?|secret|token|api[_-]?key|authorization|credentials?|private[_-]?key|bearer)($|[_.\-\s])",
    re.IGNORECASE,
)
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
TEXT_RULES = (QUOTED_DQ, QUOTED_SQ, UNQUOTED, COOKIE_ASSIGN, FLAG_UNQUOTED, AUTH_JSON)


def masked_part(text: str) -> str | None:
    """The part of `text` the three older key rules mask (the longest value they capture), or None when they mask nothing."""
    best = None
    for rx in (QUOTED_DQ, QUOTED_SQ, UNQUOTED):
        m = rx.search(text)
        if m and (best is None or len(m.group(1)) > len(best)):
            best = m.group(1)
    return best


def masked_parts(text: str) -> list[str]:
    """Every value any of the copied TEXT rules captures in `text` (one entry per rule that matches)."""
    return [m.group(1) for rx in TEXT_RULES if (m := rx.search(text))]


def record_key_masked(key: str) -> bool:
    """Did main's record walk mask the value under this key?"""
    return SENSITIVE_KEY.search(_CAMEL.sub("_", key)) is not None
