"""The default numbers of the K5 read path, in one place.

Nothing here is a secret, an account id, a region or a host name. Every value is either validated config
(`Config.evidence`, `Config.retention`, `Config.tool_timeout_s`, the per-agent `max_run_usd`), a validated manifest
field (`max_output_bytes`, `ports`, `options`), or a validated source setting (`KubernetesSettings`); this file only
names the defaults those fields start from, so a number is never written twice. tests/test_no_hardcoded_values.py
keeps host names, account ids, ARNs and key-shaped strings out of `src/`.
"""

from __future__ import annotations

import decimal

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
# The most one model price may be, in USD per million tokens. 10**6 is one dollar per token, far above any list price
# known to the author; it is not read from a provider's price list (UNVERIFIED), so a lead may lower it.
MAX_ROUTE_PRICE_USD_PER_MTOK = 10**6

# --- triggers: the signed trigger endpoint (Config.triggers, TriggerSettings) -------------------------------------------
# A config cannot raise the body cap above this. Twice the document cap: a document of the largest size still fits
# once it is wrapped and escaped in JSON.
TRIGGER_MAX_BODY_BYTES_CEILING = 2 * MAX_DOCUMENT_BYTES
# The largest request body the endpoint reads when the config names none: the ceiling (524288). The document cap
# itself would be too small, because the JSON around a full-size document adds bytes.
TRIGGER_MAX_BODY_BYTES = TRIGGER_MAX_BODY_BYTES_CEILING
# Floors: a typo (`max_body_bytes: 1`, `ack_wait_s: 0.0005`) must not load and then refuse or 503 every request.
TRIGGER_MAX_BODY_BYTES_FLOOR = 1024
TRIGGER_ACK_WAIT_S_FLOOR = 0.1
TRIGGER_MAX_RUNNING = 4  # runs the worker's pool handles at once
TRIGGER_MAX_RUNNING_CEILING = 64
TRIGGER_ACK_WAIT_S = 5.0  # how long a request waits for its run row before it answers 503
TRIGGER_ACK_WAIT_S_CEILING = 30.0
# `trigger.conflict` audit events one sender may write per minute (the rest are counted, logged once).
TRIGGER_CONFLICT_EVENTS_DEFAULT = 10
TRIGGER_CONFLICT_EVENTS_MIN = 1
TRIGGER_CONFLICT_EVENTS_MAX = 1000

# --- spend reservations (limits.py, the `expire_reservations` tick step) -------------------------------------------------
# Seconds after which an open spend reservation is marked expired (its worst case stays booked). The tick step uses
# the larger of this and the stuck-run age, so a reservation never expires while its run could still be working.
RESERVATION_EXPIRE_S = 3600
# The youngest an open hold may be for `hadavin_expire_spend_reservations` to expire it (row `min_expiry_age` of
# `hadavin_limits`). It equals the floor the only legitimate caller (the tick step) already uses, so nothing that works
# today changes; a runtime login that calls the function directly can no longer expire a live hold at age 0 (an expired
# hold can be released by the operator and the real cost of a late settle would be lost, review M1).
MIN_EXPIRY_AGE_S = RESERVATION_EXPIRE_S
# How long an expired hold may stay booked before the tick step `check_expired_holds` fails loudly (a hold that nobody
# released keeps its worst case in the day counter, so after a provider outage or a revoked key the agents run into
# their daily budget without any error). Six hours: past the one hour in which a late settle can still book the real
# cost (MIN_EXPIRY_AGE_S, after which `release-expired` is allowed at all) with room for a normal operator
# response, short enough that the same day's budget is still worth saving. Not a hard limit: only the alert uses it.
EXPIRED_HOLD_ALERT_AFTER_S = 3600 * 6
# How many days the booking day of `hadavin_reserve_spend` may differ from the database's UTC date (row
# `max_day_skew` of `hadavin_limits`). One day covers a clock a few hours off and a call made across midnight; a
# larger window would let a runtime login start a fresh day counter and month counter by naming a far day (review B3).
MAX_RESERVE_DAY_SKEW_DAYS = 1
# Bytes added to the input of every worst-case price of a model call (llm/common.py worst_case_usd): room for what
# an adapter adds around the prompt (JSON framing, role names, the forced-tool wrapper). Not measured against a
# provider (UNVERIFIED); a lead may raise it.
WORST_CASE_OVERHEAD_BYTES = 4096

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
# The most scan keys one text may make (scan_keyset): 2 variants (the text as it is, the text without Mc/Sk) x 4 tag texts x 2 passes = 16 by
# construction; 13 is the most a real text reaches. More than this is refused (TextTooLong), never cut off.
TEXTNORM_SCAN_KEY_CAP = 16
# The most texts a scan_cache() scope keeps at once (the views of the last texts scanned; the scope empties them when it ends).
TEXTNORM_SCAN_CACHE_TEXTS = 2
# The floor of every minimum below: a needle of one character is found in nearly every text of its script, so no minimum under this is accepted.
TEXTNORM_MINIMUM_FLOOR = 2


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
# script not in the table (Armenian, Georgian, ... : not measured) takes the default, 12: the LARGEST minimum measured for any script (Greek, 12; Cyrillic 10), the safe side for a script nobody measured. INSERTION_MAX: the longest needle
# the matcher takes (its work grows with the needle length for each hit); a longer needle is matched exactly only.
TEXTNORM_INSERTION_MIN_CHARS = 12
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
# register_value (guard.textnorm): when True, a protected value that a scan finds only in part (its ASCII part has no needle of its own) or that is
# a script value alone with every script needle outside the one-inserted-letter band is REFUSED with CoverageRefused instead of being registered.
# An ordinary ASCII value (a password, an API key) has an exact view and is registered even when True (lead ruling, order 165 M3). True is the
# default of the client profile: a value we cannot cover loudly is acceptable, one we cannot cover silently is not. A bool.
TEXTNORM_STRICT_COVERAGE = True

# The injection check (guard.injection) reads a text over TEXTNORM_MAX_CHARS in overlapping pieces instead of refusing it whole. CHUNK: the
# characters of one piece (a piece whose weight is still over the cap is halved until it fits). OVERLAP: the characters two neighbouring pieces
# share at least (a new piece also starts far enough back to hold enough letters, see OVERLAP_MAX), so a steering phrase cut by a boundary is whole
# in one piece. MAX: the longest text read in pieces (a case bundle's cap); a text
# longer than that is still flagged as guard_unavailable. The time is in tests/test_textnorm_round2.py (printed with -s) and the CHANGELOG.
TEXTNORM_INJECTION_CHUNK_CHARS = 32_768
TEXTNORM_INJECTION_OVERLAP_CHARS = 1_024
# OVERLAP_MAX: the farthest back a new piece may start to find enough letters (see guard.injection._start_of_next); a boundary with too few letters
# within it is refused (fail closed). PHRASE: the characters the longest steering-phrase pattern reads (about 120).
TEXTNORM_INJECTION_OVERLAP_MAX_CHARS = 8_192
TEXTNORM_INJECTION_PHRASE_CHARS = 120
TEXTNORM_INJECTION_MAX_CHARS = MAX_BUNDLE_CHARS

# Milliseconds a store call may wait for a row lock (store/postgres.py `build`, the runtime connection only; the migrate
# connection sets none). A call that waits longer fails loudly instead of holding the process-wide store lock for ever;
# the runtime maps it to limits_unavailable. It does not limit how long a statement itself runs.
STORE_LOCK_TIMEOUT_MS = 10000

# --- audit outbox drain (audit/chain.py reconcile) ----------------------------------------------------------------------
# Rows of audit_outbox read and drained per reconcile (one tick): a big backlog is drained over several ticks, so a
# tick stays short and holds a bounded number of bodies in memory.
AUDIT_DRAIN_BATCH = 500
# Inline flush of events parked in memory: a transient failure is retried up to this many times in one flush, with
# a sleep of BACKOFF_S doubling each time and never above BACKOFF_MAX_S; then the event stays parked (never dropped).
AUDIT_FLUSH_ATTEMPTS = 3
AUDIT_FLUSH_BACKOFF_S = 0.05
AUDIT_FLUSH_BACKOFF_MAX_S = 0.5
# An outbox row refused for a PERMANENT reason (not 42501) on a reconcile pass is renamed to the quarantine prefix
# when its own event.ts is at least this many seconds old (about 3 tick periods; `hadavin-sdk tick` runs ONE pass per
# process, so the age is read from the row, not counted in memory): still readable, never deleted, skipped by reads.
AUDIT_QUARANTINE_AFTER_S = 300
# Upper bound of `backends.audit.drain_batch` (a 1 MB body x 5000 rows would be GBs in one page list).
# backends/table.py imports nothing of ours and keeps this value as a literal; a test pins them equal.
AUDIT_DRAIN_BATCH_MAX = 2000
# SQLSTATE prefixes the audit chain counts as a PERMANENT refusal (waiting never helps): class 22 data, class 23
# integrity, 42501 missing grant, 54000 limit exceeded. Every other database error is transient and is retried.
AUDIT_PERMANENT_SQLSTATES = ("22", "23", "42501", "54000")
# Prefix of the event_id an outbox row gets when the chain refuses it for ever (a poison row): the runtime role may
# INSERT and DELETE but not UPDATE, so "marking" is insert-under-the-new-id then delete-the-old.
AUDIT_QUARANTINE_PREFIX = "poison:"

# Decimal digits used for money sums and price checks, set locally so a host's own Decimal context cannot round money.
MONEY_DECIMAL_PRECISION = 60
# Exponent range of the money context (the traps and rounding are pinned in `money_context`, too).
MONEY_DECIMAL_EXPONENT_LIMIT = 999_999


def money_context() -> decimal.Context:
    """The ONE Decimal context every money sum, product and price check runs in (`with
    decimal.localcontext(defaults.money_context())`). Built from nothing, not from `decimal.DefaultContext`: a host's
    precision, rounding mode, traps or exponent range cannot change a cost. Exact up to
    `MONEY_DECIMAL_PRECISION` digits; an overflow of that raises (InvalidOperation) and the caller fails closed."""
    return decimal.Context(
        prec=MONEY_DECIMAL_PRECISION,
        rounding=decimal.ROUND_HALF_EVEN,
        Emin=-MONEY_DECIMAL_EXPONENT_LIMIT,
        Emax=MONEY_DECIMAL_EXPONENT_LIMIT,
        capitals=1,
        clamp=0,
        flags=[],
        traps=[decimal.InvalidOperation, decimal.DivisionByZero, decimal.Overflow],
    )
