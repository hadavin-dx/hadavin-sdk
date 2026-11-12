"""The key rules of the code BEFORE Q8b (main, 2a8c2aac), copied word for word, used as an ORACLE by `tests/test_q8b_batch4.py`:
every key the older rules masked must still be masked. Not imported by product code. Made-up text only."""

import re

# The two quoted-value rules (`guard/redact.py` on main, lines 575-590).
QUOTED_DQ = re.compile(
    r"(?i)(?:password|passwd|pwd|pass|secret|token|api[_\-]?key|apikey|credential|session)"
    r"[\w.\-]{0,20}[\"']?\s*[:=]\s*\"([^\"][^\"]{0,255})\""
)
QUOTED_SQ = re.compile(
    r"(?i)(?:password|passwd|pwd|pass|secret|token|api[_\-]?key|apikey|credential|session)"
    r"[\w.\-]{0,20}[\"']?\s*[:=]\s*'([^'][^']{0,255})'"
)
# The generic key=value rule (main, lines 591-613), value part as written there.
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


def masked_part(text: str) -> str | None:
    """The part of `text` the older rules mask (the longest value they capture), or None when they mask nothing."""
    best = None
    for rx in (QUOTED_DQ, QUOTED_SQ, UNQUOTED):
        m = rx.search(text)
        if m and (best is None or len(m.group(1)) > len(best)):
            best = m.group(1)
    return best
