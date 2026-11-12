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
MAX_SWALLOWED_CHARS = (
    20_000  # characters a text may have swallowed by sequences and still get the character reading
)
REDACT_BUDGET_S = 6.0
# The most passes (one pass = all patterns of `redact` over one reading) one `redact_text` call may make; one more is refused
# (`InputTooLarge`, nothing shown), counted in `runmap._Work.count_pass`. Measured on 2026-11-12 (`handover/evidence/PRH/b9/hillclimb.py`,
# 50 seconds of mutating texts that mix ESC ( B, colour codes, percent, entity and backslash-u spellings, non-ASCII, a placeholder
# look-alike and values): two runs reached the bound (24) with 821 of 1,920 and 874 of 2,100 mutated texts (43 and 42 percent; the previous head ea6dbdaf: 858 of 2,010, 43 percent), so a dense hostile text IS refused (nothing shown, never shown unmasked) and the real worst need is above 24; the cap is a cost bound, not a measured maximum. What the tests assert on every run (`tests/test_prh_steps.py`): the
# 600 seeded texts of `test_pass_bound_holds_for_a_seeded_search` never reach the bound (their worst is 16), and every row of
# `tests/fixtures/prh_regressions.json` makes 8 passes or fewer on every path of the row.
MAX_REDACT_PASSES = 24


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
SPACED_VALUE_MIN_CHARS = 12  # the shortest KNOWN secret (a value the run holds, or one handed to a tool) that is also looked for with a space between its characters (`A K I A ...`); shorter ones would match ordinary text
SPACED_RUN_MIN_TOKENS = 10  # a run of at least this many single-character tokens, one space apart, is read with its spaces taken out
SPACED_RUN_MAX_RUNS = 32  # the most candidate runs (10 or more spaced single characters, 6 or more different ones) one text may hold; more and the text is withheld, never skipped (cost bound: each run is read by the patterns)
SPACED_RUN_MIN_DISTINCT = 6  # and those tokens must hold at least this many different characters (`x x x x ...` is not a secret)
SPACED_READ_MAX_CHARS = 200_000  # the most characters the pattern reads of ALL spaced runs of one text may scan (a run of 100,000 characters is one read of 100,000 plus the context; more and the text is withheld, never skipped); counted before the reads run, so it bounds work, not seconds
SPACED_CONTEXT_CHARS = 64  # the text before a spaced run that is read together with it (`password=` + a spaced value)
SPACED_DROP_MAX = 4  # a run is read as it stands and without its first one, two and three tokens (a one-letter word in front: `a A K I A ...`)
READ_SPACED_OUT_UNKNOWN = True  # the check that finds an UNKNOWN secret written with spaces between its characters (`redact.spaced_unknown`); shipped ON because it changed 0 of 1,933,591 lines of the Python 3.13 library and only the example key in 86,698 lines of the repository (`handover/evidence/PRH/b9/spaced_rate.py`); set False to turn it off (`q-prh-spaced-secrets`)
SCRUB_PIECE_MIN = 6  # width of the stretch the piece check looks for (exact; see `tools._has_piece` for what it does not promise)
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
