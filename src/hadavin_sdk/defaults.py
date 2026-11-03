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
EXECUTOR_TIMEOUT_S = 10.0  # the dev executor's per-call timeout (Config.executor_timeout_s)
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

# The Kubernetes source's own defaults (page size, caps) live in `sources/kubernetes.py`, with the kind.
