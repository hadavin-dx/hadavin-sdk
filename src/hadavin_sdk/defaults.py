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
# (redact_untrusted at the cap, Windows laptop, 2026-11-02, BEFORE the deadline existed): "curl -u " repeated 7.2 s, a zero-width-split
# "password=" 4.0 s, full-width 3.7 s, IP addresses 2.6 s, "password=" 1.4 s, 14,563 U+FDFA (a 262,000-character view) 3.0 s. THE 7.2 s OF THAT
# LAPTOP IS OVER THE 6 s BUDGET BELOW: on that machine today the `curl -u ` text is REFUSED (InputTooLarge); nothing is shown. The figures
# that count are the Linux test machine's (2026-11-20, G7 fix round 4; raw run in handover/core-c/evidence/G7-1.md), for a text of the keyword
# repeated up to the cap with a planted chain of three rounds, a compound tail and a backslash so that the views run, through
# redact_untrusted, in CPU seconds of the thread: "password=" 2.5 to 3.2 s, "curl -u " 4.5 to 5.4 s (runs of 4.51, 4.53, 5.27, 5.33 and 5.36 s; budget 6.0 s). One pattern pass plus one
# sweep of that text (the UNIT below): 0.35 to 0.63 s for "password=", 1.96 to 2.41 s for "curl -u ". So a machine about 25 percent slower
# than the test machine (4.8 s x 1.25 = 6.0 s; at the slow end of the runs, 5.36 s, 12 percent is enough) REFUSES a `curl -u `-shaped 262 KB text with InputTooLarge: fail closed, and a legitimate
# document of that shape is lost, never half masked. The test machine's margin is 1.1x to 1.3x on that text; a plain text costs about 7 us a
# character and is nowhere near it. The bound of a call is stated below: size a timeout around that, not around the 7 us.
MAX_REDACT_CHARS = MAX_DOCUMENT_BYTES
# A case bundle is many strings, each within the cap above; the SUM is capped too (redaction cost is linear in it).
MAX_BUNDLE_CHARS = 8 * MAX_REDACT_CHARS
# A text over the redaction cap is cut at the cap, redacted, and this many characters of the result's end are dropped: a
# secret that straddles the cut leaves only a fragment of at most this length (a PEM key is about 1.7 KB for RSA-2048, 3.2 KB for RSA-4096 and 6.4 KB for RSA-8192; 8,192 covers all three with slack), and it is the
# part dropped, never shown.
CUT_MARGIN = 8192
# The most CPU seconds of the calling thread (`time.thread_time()`, not the wall clock) one `redact_text` call may spend
# before it refuses (fail closed, `InputTooLarge`): a hostile text costs 1 to 5 s at the cap (see above) and every extra view repeats
# that. Checked between the stages, once per stored original in `_decoded_masks`, in the loop over the views, in the fold
# scan (once per pattern, per suspect line, per round, per non-ASCII stored value of the alias build, and every 4,096
# characters of the alignment), before EVERY round of `_Redactor.settle` (the pattern passes after the first sweep: one round is a pass
# over the strings the previous round changed plus a sweep; the loop ends on a round that changes no text, at most 4 rounds, then the
# call is refused as NotSettled), inside `_build` (every 512th stored value) and inside EVERY sweep of a call, the FIRST included
# (`redact` and `redact_many` pass the call's deadline since G7 fix round 4): every 32nd free segment (only when the map holds a value), every value replaced, and every 1,024th
# unit of work of the compound-form scan (a placeholder token of the text, with or without a form, a step of the backward prefix walk, a step of the forward suffix walk, or an entry looked up at a suffix terminal) and the registration of a union (one per character). A spent
# budget raises InputTooLarge, a round is never skipped (that would fail open). A direct `sweep()` call with no deadline is not checked, and
# a `redact()` or `redact_many()` with no `_deadline` has no total bound at all (the fold scan restarts a fresh 6 s allowance on each `find`).
# NOT checked: a direct pass of the pattern table (`find` over a string, and the loop over the strings of one round), `_views`
# (`neutralise`, `canonical`, `composed`, `without_spacing_marks` and `undo` on the whole text), `_keep_earlier_masks`, the tail of
# `_folded_line` (the fold of the body and the dry runs), `_withhold`, one `str.replace` or finder pass over one segment and the per-line fold
# loops.
# THE BOUND, one statement (the tests enforce it, tests/test_redact_settle_loop.py T4). For ONE call of `redact` or `redact_many` the time past
# the budget is at most the pass in progress when the budget is crossed (pass 1 over the strings, or the pass of a round) plus the one
# `str.replace` or finder pass of the sweep that was running. A `bank_near` flip (a bank word found only in a folded view) reads again the
# strings read up to it, EACH after a deadline check: a flip at the LAST string IS a second pass over every string (checked before each
# string), so what holds is that the overrun past the budget is at most one string pass, not that the flip is cheap.
# `redact_text` and `redact_untrusted` are a SERIES of such calls (the text, then up to a handful of views) against ONE absolute deadline, so
# their worst case is: budget + the pass of the call in progress + one sweep + 0.5 s PER VIEW for what no check reaches (a regex pass, `_views`,
# `_keep_earlier_masks`, the final `_clean`). The test asserts budget + twice the measured UNIT (one pattern pass and one sweep over the biggest
# text) + 0.5 s on a text with one view, which is looser than the claim for one view and does not cover several views at the cap (not claimed).
# A text for which pass 1 alone costs more than the budget is refused at the first check after it. The clock is `time.thread_time()`: CPU time of
# the calling thread, not wall time, so `redact_text` has ONLY the CPU clock: a thread that waits for the
# GIL or blocks does not advance it, and a `_deadline` is valid only in the thread that created it (thread CPU clocks are per thread). A
# caller that needs a wall-clock bound (a request timeout) must add its own guard at the call: that is the CALLER's job (core-b; listed in
# handover/core-c/tickets/G7-context-after-sweep.md, `For core-b`), not something `redact_text` does. The outbound gate (`runmap.EnforceBudget`) keeps TWO
# clocks and does not convert one into the other: a `thread_time` deadline that it passes INTO `_Redactor.sweep` and the held-back sweeps
# (checked inside them, as above), and a monotonic wall deadline that only its own `check()` reads (every 64th held-back value and after each
# sweep, together with the CPU one). `clean()` makes one call for the text, one
# more for its tag-stripped view only when tags were there, and a check read of its result (at most 3 calls, none when pass 1
# changed nothing); the check reads share ONE budget (`channel.settled`, CPU seconds since `clean` began; a card over it, or a
# read the redactor refuses, shows `SETTLE_NOTE`). Measured 2026-11-20 on the test machine: a 174-character card 1.3 ms ->
# 3.6 ms with the check read, a 71,179-character card 367 ms -> 655 ms.
REDACT_BUDGET_S = 6.0
# The scan of the written forms of compound secrets (`guard.redact._Redactor._spelled_sweep`; a secret found whole after its first copy was cut,
# `<SECRET_1>xy`, or a value with a placeholder inside it, `a=1; sid=<JWT_1>`) looks each placeholder token of a text up in two tries of the forms
# registered under it: backwards over what stood BEFORE the token in the form (the prefixes; the ids of the ones that match are collected) and then
# forwards ONCE over what stood after it (all the suffixes in one trie; at a terminal, the matched prefix ids are looked up). The cost of a token is
# the prefix that really matches the text, plus the suffix that really matches, plus the entries looked up at the terminals met (P + S + entries; round 5
# walked the suffix once per matched prefix, P x S: a cookie jar growing by one cookie per line with the same signed suffix needed 3.3 to 3.6 million
# units at 64 to 128 characters of suffix, 83 to 90 percent of the limit, and was one character away from refusing an honest log). Nothing is capped
# by the NUMBER of forms or of prefix lengths (before round 5 a cap of 32 offsets and 256 forms per token refused honest cookie logs). Instead the
# total work of one scan (every step of a walk, every token and every entry looked up counts one unit; registering a union of overlapping forms counts one per
# character) is counted, read every 1,024 units together with the deadline, and refused past this many units (`InputTooLarge("SpelledWorkTooMuch")`,
# nothing shown). The figure is CHOSEN, not measured: a round number with a margin over the honest shapes MEASURED on the Linux test machine
# (evidence handover/core-c/evidence/G7-1.md "G7 fix round 6" and "round 7", script g7r6_units.py): the largest honest shape that is a valid input
# (the registered text under the 262,144-character cap) is the grown cookie jar of 275 lines with a 128-character signed suffix, 254,629 units, so the
# limit is 15.7 times it (the 330-line jar, 304,221 units, registers 320,924 characters, over the cap: a measure of the walk only, 13.1 times);
# 300 cookie lines of 300 prefix lengths 245,093 units, 300 signed ids 98,227. A shape that grows at BOTH ends (front variants x end variants, every
# combination a distinct registered value) is not among the honest ones: 20 x 20 (400 forms in 16,399 characters) takes 2.28 million units (8.7 per
# character of the text, 57 percent of the limit), 30 x 30 3.56 million (89 percent), about 32 x 32 is refused: each combination is a real match, so its
# cost is the product and no scan can do better. Corpus: the 1,836 inputs of tests/test_redact_idempotent_property.py (the jar, 12 forms at 12 offsets
# under `<JWT_1>`, is one of them) register a spelled form in 4 inputs, at most 105 characters (script g7r7_registry.py). A hostile text (2,800 forms,
# 70 prefixes x 40 suffix lengths in 213,000 characters, then 262,000 characters of copies) needs 6.3 million units and is refused after 0.49 s of CPU;
# the measured cost is 0.09 to 0.21 microseconds per unit (0.13 on the hostile text), so the limit costs 0.4 to 0.9 s at most. WHAT THIS DOES NOT
# BOUND: with no deadline the scan is 4 million units per sweep per string per round, no total bound (stated); the deadline (`REDACT_BUDGET_S`) bounds
# the time on a slower machine whatever this says. A hostile author can therefore FORCE A REFUSAL of the whole document (`SpelledWorkTooMuch` is an
# `InputTooLarge`): fail closed, nothing shown, and a legitimate document in the same text is lost (SECURITY wording). Two OPEN limits (E10, pinned by
# tests): an overlap of forms completed in a LATER round (registered after the earlier form's text was swept) leaves the swallowed literal prefix or
# tail readable, and two compound values that overlap as RAW text leave the tail of one readable in the literal sweep.
SPELLED_MAX_WORK = 4_000_000
# MEMORY of the registry (round 7): the tries hold one dict per character of every registered written form that is not already a node (prefix and
# suffix; about 185 bytes each, measured: 37.2 MB per 200,000 characters, 49 MB per 260,000, tracemalloc, evidence g7r6_units.py `memory()` and
# g7r7_registry.py). Before round 7 nothing limited it: a forged token the map already held (`password=<SECRET_1>` + 260,000 characters) registered
# a form per string, 8 strings (the 8 x 262,144 bundle cap) held 8 x 49 MB of registry, and the call peaked at 2.3 GB under tracemalloc (the rest is the sweep's finders for the 8 large values, 956 MB with no registry at all: a separate cost, not this limit's). Now `_Redactor._spell` (every registration: `find`
# and the union of an overlap) counts the characters held per call and refuses the CALL past this many (`InputTooLarge("SpelledMemoryTooMuch")`,
# nothing shown; the registration is never skipped: that would fail open). CHOSEN: 1,000,000 characters, about 190 MB of registry at most. Honest
# shapes hold far fewer (they share nodes): the 330-line grown jar 1,720, the 275-line jar 1,469, 300 cookie lines 3,017, the corpus 105 at most:
# 330 times the largest (1,000,000 / 3,017). The hostile case above is refused after about 4 strings (186 MB peak). A SINGLE string is not refused for 260,000 characters
# (49 MB of registry); its other costs (the sweep's finder for a 260,000-character value) are not this limit's.
SPELLED_MAX_CHARS = 1_000_000


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
# extra matches the insertion adds stay near 1% or lower per 10,000 characters of text (that figure is only what the one-inserted-letter match ADDS,
# per script, on Bible text; it is NOT the false-hit rate of the whole scan, see FALSE HITS below); a needle holding several groups takes the largest minimum, except a
# needle of Han and kana only (a Japanese word), which takes the Han minimum (measured on its own, CHANGELOG order 137 D3). A script not in the
# table (Armenian, Georgian, ... : not measured) takes the default, 12: the LARGEST minimum measured for any script (Greek, 12; Cyrillic 10), the
# safe side for a script nobody measured. INSERTION_MAX: the longest needle
# the matcher takes (its work grows with the needle length for each hit); a longer needle is matched exactly only.
# FALSE HITS of the whole scan_holds (measured 2026-11-20, Python 3.13.18, Unicode 15.1.0; handover/core-c/evidence/G1-false-hits-and-cost.md,
# "Round 2"): the share of 10,000-character chunks of ordinary Latin text (repository prose and code, standard-library docstrings, generated
# text) in which scan_holds reports a value drawn at random (random pronounceable strings and a 70-name hand list, not real protected values):
# 4 letters 5.3%, 5 letters 1.0%, 6 letters 0.4%, 8 or more 0; a common word of 5-10 letters 3.9-4.5% (its draw is hash-seeded: two runs);
# ASCII ids of 4-5 characters 0.22%; 6 digits 0.007%. An upper bound in ONE sense only: a value that is a whole word of the text counts as a
# hit. It is NOT a bound for other registers (tickets, email, chat) or for real protected values. Share of the hits that cut a word: 4 letters
# 94%, 5 letters 63%, ids of 4-5 characters 99%, 6-letter names 9% (91% are the whole name). Non-Latin: one program's real interface text
# (Russian 4-8 letters 7.6%; Chinese of 2 characters drawn by frequency 5.2%, of 3-4 characters 0); Arabic and Devanagari synthetic only, unknown.
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
# INJECTION_BUDGET_S (guard.injection, G10): the CPU seconds (time.thread_time() of the thread that runs the check) that ONE RegexDetector check,
# one detector call on one text, may spend in the text fold; past them textnorm raises DeadlinePassed and the run is flagged guard_unavailable
# (fail closed). Per check, not per run: a run that checks many texts (k1b: one check per tool result) may spend it once per check. None: no
# deadline. A positive finite number; anything else flags every run. 30.0: about 1.9x the slowest ORDINARY text of 2,000,000 characters measured
# on the build box (16.0 s; a constructed text took 185 s; G10 ticket, D4); on a machine more than about 1.9x slower that text is flagged on every run. CPU only: waiting for the GIL,
# a lock or I/O does not count, and no call site of the injection check has a wall-clock limit.
INJECTION_BUDGET_S = 30.0
