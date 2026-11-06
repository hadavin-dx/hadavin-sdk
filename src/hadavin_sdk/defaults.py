"""The default numbers of the K5 read path, in one place.

Nothing here is a secret, an account id, a region or a host name. Every value is either validated config
(`Config.evidence`, `Config.retention`, `Config.tool_timeout_s`, the per-agent `max_run_usd`), a validated manifest
field (`max_output_bytes`, `ports`, `options`), or a validated source setting (`KubernetesSettings`); this file only
names the defaults those fields start from, so a number is never written twice. tests/test_no_hardcoded_values.py
keeps host names, account ids, ARNs and key-shaped strings out of `src/`.
"""

from __future__ import annotations

# --- tools (manifest and Config.evidence) ---------------------------------------------------------------------------
MAX_TOOL_ERRORS = 3  # tool errors in one run before it ends NEEDS_PERSON tool_error
MAX_OUTPUT_BYTES = (
    16384  # what a tool result may be after redaction; the manifest's `max_output_bytes` default
)
LEGACY_MAX_OUTPUT_BYTES = (
    20_000  # the same cap for plain callables (replay, tests): K1b's own result cap
)
FETCH_CEILING_BYTES = (
    2 * 1024 * 1024
)  # the most one fetch may be asked to read, whatever a source requests
MAX_TOOL_CALLS_PER_RUN = 40  # read-tool calls one run may make
MAX_MAP_ENTRIES = (
    2000  # distinct values in one run's redaction map (the finders are rebuilt when it grows)
)
MAX_CONCURRENT_TOOL_CALLS = (
    4  # read-tool calls running at once in one process (client-side load cap, R372)
)
MAX_TOOL_CALLS_PER_MINUTE = 120  # read-tool calls started per minute in one process
MAX_DOCUMENT_BYTES = (
    262_144  # the largest incident document a run takes (redaction and grounding scan it)
)
# The most one redact_text call takes, counting the text and every view the second pass scans. Measured end to end
# (redact_untrusted at the cap, Windows laptop, 2026-11-02): "curl -u " repeated 7.2 s, a zero-width-split
# "password=" 4.0 s, full-width 3.7 s, IP addresses 2.6 s, "password=" 1.4 s, 14,563 U+FDFA (a 262,000-character
# view) 3.0 s. Size any timeout around ~8 s per call at the cap, not the 7 us per character a plain text costs.
MAX_REDACT_CHARS = MAX_DOCUMENT_BYTES
# A case bundle is many strings, each within the cap above; the SUM is capped too (redaction cost is linear in it).
MAX_BUNDLE_CHARS = 8 * MAX_REDACT_CHARS
# A text over the redaction cap is cut at the cap, redacted, and this many characters of the result's end are dropped: a
# secret that straddles the cut leaves only a fragment of at most this length (a PEM key is about 1.7 KB for RSA-2048, 3.2 KB for RSA-4096 and 6.4 KB for RSA-8192; 8,192 covers all three with slack), and it is the
# part dropped, never shown.
CUT_MARGIN = 8192
# The most wall-clock seconds one `redact_text` call may spend before it refuses (fail closed, `InputTooLarge`): a hostile
# text costs 1 to 4 s at the cap and every extra view repeats that. Checked between the passes, NOT inside one: a single
# pass can run about 7 s on a hostile text, so one call can take up to the budget plus one pass, and `clean()` makes two
# calls (the text and its tag-stripped view).
REDACT_BUDGET_S = 6.0


def cut_margin(length: int) -> int:
    """The characters dropped from the end of a text cut at the redaction cap: `CUT_MARGIN`, but never more than a quarter
    of a short text (and never under 4,096). A cut happens at 262,144 characters in production, where this is the full
    margin; only a test that cuts a small text meets the smaller values."""
    return min(CUT_MARGIN, max(length // 4, 4096))


# The scrub of handed-out secrets in a tool result (`tools.prepare_output`); validated in `config.ScrubSettings`.
SCRUB_TAIL_WINDOW = 256  # bytes looked back over for a place to cut that is not inside a token
SCRUB_MIN_REDACTION_WINDOW = (
    4096  # redaction always sees at least this much, whatever the tool's cap
)
SCRUB_MIN_SECRET = (
    6  # a shorter secret would shred ordinary text if scrubbed: a tool is refused one
)
SCRUB_FRAGMENT_SCAN = (
    4096  # how far back from a cut the strip looks for the front of a partial secret
)
SCRUB_FRAGMENT_MIN = 1  # characters of a secret's front that are removed next to a cut
SCRUB_MAX_LAYERS = (
    8  # nested encodings (percent, entity, backslash) undone before the scrub fails closed
)
SCRUB_PARTIAL_END = 10  # the longest half-written escape a cut can leave; added to the look-back
SOURCE_REPROBE_S = 3600  # how often the scope of a configured source is probed again while running
MAX_TOOL_BYTES_PER_RUN = 262_144  # bytes of tool results one run may send to the model
MAX_ABANDONED_TOOL_THREADS = (
    8  # tool bodies still running after their deadline before calls are refused
)
CLUSTER_SUFFIXES = (
    ".svc.cluster.local",
    ".svc",
)  # host suffixes that count as in-cluster (plain http)
# The last label a cluster suffix may end in: a private namespace, never a public TLD such as .com.
PRIVATE_SUFFIX_LABELS = frozenset(
    {
        "svc",
        "local",
        "internal",
        "lan",
        "corp",
        "home",
        "intranet",
        "localdomain",
        "cluster",
        "test",
        "invalid",
    }
)
EXECUTOR_TIMEOUT_S = 10.0  # the demo executor's per-call timeout (Config.executor_timeout_s)
HTTPS_PORTS = (443,)  # ports a tool may reach over https unless its manifest lists `ports`
CLUSTER_PORTS = (80, 8080, 9090, 9093, 3100)  # the same for plain http to in-cluster hosts

PURGE_EVERY_S = 86400  # how often the `purge_evidence` tick step does its work (Config.retention)

# --- redaction (Config.evidence.stored_kinds may narrow this, never widen it) -------------------------------------------
# Identifier kinds a fix or a read may need back (M14). Secret and regulated kinds are never stored.
STORED_KINDS = (
    "ACCOUNTID",
    "ADDRESS",
    "ARN",
    "AZURERESOURCE",
    "EMAIL",
    "GCPRESOURCE",
    "HOSTNAME",
    "IPV4",
    "IPV6",
    "MAC",
    "NAME",
    "PHONE",
    "TENANT",
)  # not UUID: a UUID is often a session or API token, so it is placeholdered but never stored

# --- kubernetes kind: the Kubernetes source (KubernetesSettings). Decision: kind defaults stay here with every other default
# (a repo rule keeps one set); when a second kind arrives each kind gets its own `<kind>_defaults.py` and the rule test
# becomes syntax-tree based (K5-ITO outline in sources/kinds.py) -------------------
K8S_PAGE_SIZE = 20  # list page size: a deployment object can be tens of KB
K8S_MAX_PAGES = 25  # pages followed per list; past that the answer says it is incomplete
K8S_JSON_CAP_BYTES = 1024 * 1024  # fetch cap for a JSON list reply
K8S_LOG_SLACK_BYTES = 8192  # fetch-cap room over `log_bytes` for the line framing
K8S_LOG_BYTES = 65536  # asked of the API as limitBytes

# --- text folding (guard/textnorm.py) ---
# The weighted size rule of the fold: a text whose weight W (the sum over its characters of the longest string the fold makes from
# one character; an ASCII text has W = its length) is above this is refused with TextTooLong. Same number as the redaction cap.
TEXTNORM_MAX_CHARS = MAX_REDACT_CHARS
# The Unicode data version the fold's keys were made with; require_pinned_unidata compares the interpreter with it.
TEXTNORM_PINNED_UNIDATA = "15.1.0"
# The Python minor version that carries that Unicode data; require_pinned_unidata names it in its message (the only other place that said it was a
# second copy inside guard.textnorm). guard.textnorm refuses a value that is not a non-empty str when it is imported.
TEXTNORM_PINNED_PYTHON = "3.13"
# Passes (the confirming pass included) of a scan-key reading before FoldNotConverged (read by guard/textnorm.py at the call). A whole number
# of at least 1 (guard.textnorm refuses another value when it is imported and every time a scan key is made).
TEXTNORM_MAX_PASSES = 3


# The shortest view of a protected value that a scan may use (guard.textnorm.scan_needles), one number per KIND of view; a shorter view (an
# empty one above all) is found in nearly every text. Each must be an int of at least 2, the floor (guard.textnorm refuses another value when it
# is imported and every time a scan takes its needles): a single character is found in nearly every text of its script.
# SPELLING: a view that keeps separators and punctuation (fold_views, without the script views); it is a needle but never the only one.
TEXTNORM_MIN_SPELLING_CHARS = 2
# SQUEEZE: a view of ASCII letters and digits only (squeeze_views): an inserted separator cannot hide it, so it must be long enough not to
# be found in ordinary text (a 3-letter name is found in many English words).
TEXTNORM_MIN_SQUEEZE_CHARS = 4
# SCRIPT: a view of the non-ASCII letters of the value's own scripts (fold_views with the scripts of the value). Letters of an alphabet or a
# syllabary repeat in every text, so the minimum is the squeeze one.
TEXTNORM_MIN_SCRIPT_CHARS = 4
# IDEOGRAPH: the script minimum for a value that is only Han ideographs (no ASCII letter or digit): one ideograph is a word, two are a name.
TEXTNORM_MIN_IDEOGRAPH_CHARS = 2
# DIGITS: the squeeze minimum for a view of ASCII digits only (a PIN, an account number): a short digit string is found in almost every table of
# numbers (a 4-digit needle is found in 99 of 100 random 50,000-digit tables), so it must be longer than a view that holds a letter.
TEXTNORM_MIN_DIGIT_CHARS = 6

# ONE INSERTED LETTER (guard.textnorm.scan_holds): a script needle (see SCRIPT above) is also looked for in the text with ONE extra letter of the value's own
# scripts inserted anywhere inside it, so "密码测试" is found in "密的码测试". INSERTION_MIN: the fewest characters such a needle may have, per script group (the first
# word of the Unicode name, Han and kana grouped; see guard.textnorm); a shorter needle is matched exactly only, because "a?b" matches too many ordinary words.
# The numbers come from a measurement on running text (CHANGELOG, "ONE INSERTED LETTER"): for each script, the shortest needle for which the
# extra matches the insertion adds stay near 1% or lower per 10,000 characters of text; a needle holding several groups takes the largest minimum, except a needle of Han and kana only (a Japanese word), which takes the Han
# minimum (measured on its own, CHANGELOG order 137 D3). A
# script not in the table (not measured) takes the default, the most cautious of the measured Latin-free scripts. INSERTION_MAX: the longest needle
# the matcher takes (its work grows with the needle length for each hit); a longer needle is matched exactly only.
TEXTNORM_INSERTION_MIN_CHARS = 8
TEXTNORM_INSERTION_MIN_CHARS_BY_SCRIPT = (
    ("HAN", 4),
    ("KANA", 7),
    ("HANGUL", 5),
    ("THAI", 8),
    ("ARABIC", 7),
    ("HEBREW", 7),
    ("DEVANAGARI", 7),
    ("CYRILLIC", 10),
    ("GREEK", 12),
)
TEXTNORM_INSERTION_MAX_CHARS = 64
# register_value (guard.textnorm): when True, a protected value that a scan covers only exactly (a Latin or digit value, a script value outside the
# one-inserted-letter band) or only in part (its ASCII part has no needle of its own) is REFUSED with CoverageRefused instead of being registered.
# True is the default of the client profile: a value we cannot cover loudly is acceptable, one we cannot cover silently is not. A bool.
TEXTNORM_STRICT_COVERAGE = True
