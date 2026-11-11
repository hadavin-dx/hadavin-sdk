# Ticket Q8a-2 (rev 1, DRAFT for plan review): a neutral approval callback path, and a lock-in guard that sees vendor words in paths and names

Source: reviews/Q8/deps-audit.md F6, F8, F11 (first clause only); round-1 objections in reviews/Q8a/plan-r1-summary.md; measured dry run evidence/Q8a-2/dryrun-2026-11-11.md (run by a separate EVIDENCE RUNNER).
Branch: NEW `core/q8a-2-neutral-callback-and-guard` from origin/main; draft PR against main; the builder never merges.
Path class: other (lock-in). Stop rule: at most 2 fix batches after result review. If the result review finds that the diff changes signature checking (`Approvals.receive`, any `parse_decision`) or the behaviour of `approvals/gate.py`, that part moves to the security or redaction path (no round cap). This ticket asks for neither.
Depends on: nothing in code. Q8a-1 (branch `core/q8a-1-live-override-refusals`, not merged on 2026-11-11) touches other files; only CHANGELOG.md "Unreleased" can conflict. All file:line references below are for origin/main 2a8c2aa; if Q8a-1 merges first, find the lines again by their text.
Status: written by a ticket author. Nothing is built. Fresh egm:* reviewers judge this ticket before any build.

## Read first: what is not established

1. The numbers and outputs marked "author probe" come from the ticket author's own throwaway prototype (scripts and outputs in `/home/user/build/q8a2-author/`: `scan.py`, `apply.py`, `probe.py`, `scan-main.txt`, `probe-out.txt`; the prototype is a copy of main with the planned edits, never committed). They are not independent evidence. The EVIDENCE RUNNER repeats them on the real branch.
2. Not run by the author: the full test suite, ruff, bandit, the tests in `tests/test_p7_tick.py` (the exported main tree holds `src/` and the guard file only). The prototype ran only `tests/test_lockin_guard.py` (57 passed) and the probes.
3. OWNER-CONFIRM (needs the owner, rule exception "needs the owner"): the new trigger sentence of the `audit` exception (section 4). The author proposes it; only the owner can say what would end that exception.
4. The rung table marks the "ready-made scanner" row UNVERIFIED: no live research on such tools was done for this ticket.
5. Whether the contract suite (`tests/contracts/conftest.py:68-70`) builds the Slack kind as well as the fake one was not read; section 1 words the contract test so it holds for whichever kinds the suite builds.
6. Found while measuring, outside this ticket (lead decides the next step): `guard/runmap.py:215` holds an ARN-shaped regex in a neutral module; today's "ARN" pattern in the guard does not match it, and the new pattern does not either.

## Problem in plain words

The approval receiver is the small web endpoint that takes the click "approve" or "reject" from a chat tool. It is meant to work for any chat tool, but it carries one vendor's name: the URL path `/slack/actions` (receiver.py:18) and the function `handle_slack_action` (receiver.py:22). The repository test that should catch vendor names in shared code (`tests/test_lockin_guard.py`) missed both, because its name pattern only matches a string that starts with the vendor word (guard:520-521) and it never looks at function, class or variable names. Two smaller gaps sit in the same test: the registry of read sources (`sources/kinds.py:39-47`, one kind: Kubernetes) is invisible to the "two kinds or a dated exception" rule, and an exception may state "none" as the event that ends it (guard:392).

## RUNG TABLE (CODE-LAST v1)

Rung numbers follow the scale in handover/TICKET-TEMPLATE.md (2 = our own core modules, 3 = existing free tools, 5 = our own new code).

| component | need | rung tried | evidence (source, date) | what only our code gives | verdict |
|---|---|---|---|---|---|
| callback path per channel kind | the receiver serves the path of the configured channel kind and holds no vendor word | 2, reuse: `Channel` Protocol already carries per-kind attributes `name`, `max_card_chars` (channel.py:69-71), read directly at app.py:187 | read 2026-11-11 | nothing new: one more attribute of the same shape, one start-up check | KEEP-CODE (about 15 changed lines in src) |
| reverse proxy or no-code tool rewrites the path instead | same | 1 and "client's own tool" | a proxy can map any public URL to our path, but our module would still name the vendor, so finding F6 stays | - | rejected for this need (it stays the client's choice for the public URL) |
| wider string pattern | a vendor word inside a path or key (`/slack/actions`, `aws_region`) fails CI | 2, reuse: one more entry in the existing `PATTERNS` dict (guard:519-536), same scan, same allow list | dry run 2026-11-11: 8 hits, 4 not covered | - | KEEP-CODE (1 entry) |
| identifier scan | a vendor word in a function, class, variable, parameter, attribute or module name fails CI | 2, reuse: same file, standard-library `ast`, same shape as `literal_problems` (guard:592-622) | dry run: 25 hits, 8 not covered; author probe: a wider node set adds 0 hits | allow list with a reason per entry and a stale-entry check, in the same file as the other two rules | KEEP-CODE (about 50 lines in the test file) |
| ready-made scanner (for example a Semgrep rule set) for both scans | same | 3 | UNVERIFIED (not researched; would add a development dependency and a second place for allow lists) | - | not chosen; reviewers may challenge |
| source registry coverage | the read-source registry is held to the same "neutral kind and two kinds, or dated exception" rule | 2, reuse: `coverage_problems` (guard:406-426) with a 10-line adapter in the test | dry run part 4 | - | KEEP-CODE (test only, `SourceKind` unchanged) |
| trigger rule | an exception cannot say "none" for what ends it | 2, reuse: one condition at guard:422 | dry run part 4.2 | - | KEEP-CODE (1 line + 1 constant) |

Ladder line: every component is "our own core module, extended" (rung 2). No no-code tool, MCP server, retrieval or model feature applies to a repository test or a URL path match.

## 1. Receiver

### Decision: `callback_path` is a member of the `Channel` Protocol, read once when `serve()` starts and checked; there is no silent fallback

- `approvals/channel.py`: add above the Protocol `DEFAULT_CALLBACK_PATH = "/channel/actions"` and `CALLBACK_PATH = re.compile(r"/[a-z0-9]+(?:[/-][a-z0-9]+)*")` (`re` is already imported, channel.py:5). Add `callback_path: str` to `Channel` after `max_card_chars` (channel.py:71) with the comment "the URL path this kind's callbacks are posted to; the receiver answers this path only". `FakeChannel` gets `callback_path = DEFAULT_CALLBACK_PATH` beside `name = "fake"` (channel.py:90).
- `approvals/slack_channel.py`: `SlackChannel` gets `callback_path = "/slack/actions"` beside `name = "slack"` (slack_channel.py:34). This module is a vendor module for the guard (guard:499), so the literal is allowed there.
- Why a Protocol member and not `getattr(channel, "callback_path", "/channel/actions")`: (a) precedent: `name` and `max_card_chars` are plain per-kind attributes read directly (app.py:187, 195); (b) a default would hide a mistake: a new kind whose author forgets the attribute would listen on the neutral path while its vendor posts elsewhere, and every click would get 404 with no error at start; (c) the repository refuses rather than shims (config.py:95: "no clients yet, so no migration shim"). `/channel/actions` is still the neutral default in the sense the brief asks for: it is the named constant that the fake kind uses and that any future kind without a vendor-fixed path should use.
- A Protocol is not checked when the program runs, so the receiver checks it: new function in `approvals/receiver.py`
  `def callback_path(approvals: Approvals) -> str` reads `getattr(approvals.channel, "callback_path", None)` (`Approvals.channel` exists: requests.py:68) and raises `ConfigError(f"channel {name}: callback_path must be a path such as /channel/actions")` unless the value is a `str`, matches `CALLBACK_PATH.fullmatch`, and is at most 64 characters. The `getattr` here is only so that a missing attribute gives this message instead of an AttributeError; it never supplies a path. Grammar source: a lower-case subset of the path segment characters of RFC 3986 section 3.3 (no query, no dot segments, no empty segment).
- `serve()` (receiver.py:40-65) calls `callback_path(approvals)` once before it defines the handler; `do_POST` compares `self.path != path` exactly, as line 47 does today. Nothing else in `do_POST` changes.
- Rename `handle_slack_action` to `handle_action` (receiver.py:22, 54). NO alias and no re-export. Precedent confirmed: config.py:95 reads `# Slice 1 keys, refused with the place they moved to (design 12.3; no clients yet, so no migration shim).` The constant `PATH` (receiver.py:18) is deleted, not renamed. Repository-wide users on main (`git grep` 2026-11-11): only `tests/test_p7_tick.py`.
- No vendor word anywhere in `approvals/receiver.py`: code, constants, comments and docstrings. Lines to reword: 1 (function name), 3 ("Slack's 3 seconds" becomes "the reply deadline of an interactive channel (the tightest one known is 3 seconds)"), 4 ("a Slack retry" becomes "a repeated delivery"), 5 ("for development" becomes "for the demo stage and local runs"; stage names rule), 17 (comment), 25-26 (docstring), 41 (docstring: "POST to the configured channel's `callback_path`"). Author probe: main's file holds 9 vendor words by the word-boundary pattern below, the prototype 0.

### What stays true in the documents (no edit)

- docs/slack-app-manifest.yaml:5 (`POST /slack/actions`) and :30 (`request_url: https://receiver.example.com/slack/actions`): true, because a deployment configured with the Slack kind serves exactly that path.
- docs/slack-app.md:14 (`POST /slack/actions`): true for the same reason.
- tests/test_p7_tick.py:537 (the manifest's `request_url` ends with `/slack/actions`): unchanged, a regression guard.

### Path by kind

| configured channel kind | where the path is set | POST to `/slack/actions` | POST to `/channel/actions` | POST to anything else |
|---|---|---|---|---|
| `slack` | `SlackChannel.callback_path` (vendor module) | handled (401 bad signature, 413, 400, 200 as today) | 404 | 404 |
| `fake` (demo only) | `FakeChannel.callback_path = DEFAULT_CALLBACK_PATH` | 404 | handled | 404 |
| a future kind (Teams, e-mail link) | its own kind module; a vendor-fixed path there, else `DEFAULT_CALLBACK_PATH` | 404 | handled only if that is its path | 404; its own path is handled |
| any kind with a missing or malformed `callback_path` | - | `serve()` raises `ConfigError` at start; no server is created | same | same |

"Anything else" includes a trailing slash, a query string, another letter case and a longer path (author probe: `/slack/actions/`, `/slack/actions?x=1`, `/SLACK/ACTIONS`, `/channel/actions/x` all 404 for both kinds). Behaviour change to state in the CHANGELOG: a demo that runs `serve()` with the fake kind now listens on `/channel/actions` (on main it listened on `/slack/actions`).

### tests/test_p7_tick.py: every changed line

| line | today | change | reason |
|---|---|---|---|
| 18 | `from hadavin_sdk.approvals.receiver import MAX_BODY, handle_slack_action, serve` | `handle_action` | rename |
| 259, 263, 265, 273 | `handle_slack_action(...)` | `handle_action(...)` | rename; assertions unchanged |
| 290 | `url + "/slack/actions"` | `url + "/channel/actions"` | the `app` fixture builds a `FakeChannel` (test_p7_tick.py:45), whose path is now the neutral one; the expected 401 at line 294 is unchanged |
| 1, 295-298, 537 | - | no change | docstring; `/other` gives 404; manifest check |

## 2. Guard (`tests/test_lockin_guard.py`)

### One word list

`VENDOR_WORDS = ("slack", "teams", "aws", "azure", "gcp", "github", "gitlab", "bedrock", "anthropic", "vertex", "gemini", "openai", "kms", "s3", "foundry")` and `_W = "|".join(VENDOR_WORDS)`, placed above `PATTERNS`. These are the 15 words of today's "bare vendor name" (guard:520-521), in the same order.

### The new PATTERNS entry (exact)

```python
PATTERNS = {
    "bare vendor name": rf"^({_W})(:|$)",                                   # same regex text as today, built from _W
    "vendor word in a path or key": rf"[/_.-]({_W})([/_.:-]|$)|^({_W})[/_.-]",   # NEW, second entry
    ...the other eight entries unchanged...
}
```

- The two entries together match exactly what the dry-run candidate `(^|[/_.-])(W)([/_.:-]|$)` matches, and no string matches both, so one planted string gives one problem line.
- The label "bare vendor name" keeps its name because two places test for it: guard:633 (`sql_problems`) and tests/test_http_metadata.py:165. Neither is edited; both therefore apply the new entry too. Author probe: 0 hits in the 5 migration files and 0 hits in the strings of `guard/http.py`.
- Chosen over a plain word-boundary pattern. Author probe (`scan-main.txt`): the word-boundary form gives 18 rows instead of 8; the 10 extra are refusal-message prose (config.py:97, 98; backends/table.py:135; store/postgres.py:120) and regular expressions that recognise commands or secrets (approvals/gate.py:89, 648, 670; guard/runmap.py:215 three rows). None is a path, key or name.
- Stated limit (goes into the guard's module docstring): inside a STRING the pattern does not see a vendor word in free prose or glued in camel case (`"/slackActions"`, `"post to Slack"`); comments and docstrings are not scanned (except receiver.py, below); YAML, Markdown, tests and demos are not scanned. Names in code are covered by the identifier scan with a camel-case split.

### The identifier scan (new)

```python
_CAMEL = re.compile(r"[A-Z]+(?![a-z])\d*|[A-Z]?[a-z]+\d*|\d+")

def name_parts(name: str) -> set[str]: ...
def identifier_problems(src: Path, vendor_modules: set[str], identifier_ok: dict[tuple[str, str], str],
                        table_names: frozenset[str]) -> list[str]: ...
def test_core_names_no_vendor_in_identifiers():
    assert identifier_problems(SRC, VENDOR_MODULES, IDENTIFIER_OK, TABLE_VENDOR_NAMES) == []
```

- Split (`name_parts`, the same as the dry-run script): split the name on `_`; split each snake part with `_CAMEL` (digits stay with the letters before them, so `S3` gives `s3`); also join each pair of neighbouring camel parts (so `GitHub` gives `github`, `OpenAI` gives `openai`); lower-case everything. A hit is a part that EQUALS a word of `VENDOR_WORDS` (`awsome`, `laws`, `teamster` do not hit).
- Modules: every `.py` under `src` whose module is not in `VENDOR_MODULES` (guard:493-501), as in `literal_problems`.
- Names scanned in each module: (1) each segment of the module's own dotted name after the package name (reported at line 1); (2) `ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.ClassDef` names at any nesting; (3) `ast.arg` (every parameter, lambdas included); (4) `ast.Name` with `Store` context (module, class-body and local assignments, annotated fields such as pydantic fields, loop, `with`, comprehension and walrus targets); (5) `ast.Attribute` with `Store` context (`self.x = ...`); (6) `ast.alias.asname` (`import x as y`). The dry run covered only (2) and module-level assignments; author probe: (1) adds one hit (`llm.openai_compat`), (3) to (6) add 0 hits on main, so the wider set costs nothing today.
- Not scanned: names that are only read, keyword names at call sites (they are another function's parameters, scanned where defined), dictionary keys (strings: the string scan). 
- `backends.table` (the kind table, where vendor kinds are declared): a top-level class or function is skipped only when its name is in the exact set
  `TABLE_VENDOR_NAMES = frozenset({"AnthropicSettings", "BedrockSettings", "GeminiSettings", "AwsSecretsManagerSettings", "S3ObjectLockSettings", "AzureImmutableBlobSettings", "AwsKmsSettings", "AzureKeyVaultKeySettings", "GcpKmsSettings", "AzureKeyVaultSettings", "GcpSecretManagerSettings", "SlackSettings", "_aws_host", "_aws", "_vertex_host", "_anthropic_hosts", "_s3_anchor_hosts"})`
  (the 17 covered hits of the dry run; names inside a skipped node are skipped with it). New test `test_the_table_skip_is_the_pinned_set`: the top-level class and function names of `backends/table.py` that `_TABLE_VENDOR_NAME` (guard:516-518) matches equal `TABLE_VENDOR_NAMES`. So the prefix-based skip the string scan already uses cannot grow silently: a new vendor-named thing in the table file must be added to the set by hand. Author probe: 17 matches, equal to the set.
- Problem text: `f"{mod}:{line}: vendor word {word!r} in the name {name!r}"`. An unused `IDENTIFIER_OK` entry gives `f"IDENTIFIER_OK {mod} {name!r} is gone: delete the entry"` (same idea as guard:617-621).

### Disposition of the 4 uncovered string hits

| # | hit | disposition |
|---|---|---|
| S1 | approvals/receiver.py:18 `'/slack/actions'` | FIX: the constant is deleted; the literal moves to `SlackChannel.callback_path` in the vendor module (section 1) |
| S2, S3 | guard/producers.py:29 and :60 `'guard/bedrock_guardrail.py'` | ALLOW, one exact entry: `(f"{PKG}.guard.producers", "guard/bedrock_guardrail.py"): "the redaction registry must list every module that sends text to a model or a vendor screen, by file path; data read by tests/test_k5_producers.py, not a call into the vendor module"` |
| S4 | llm/openai_compat.py:75 `'openai_compat'` | ALLOW, one exact entry: `(f"{PKG}.llm.openai_compat", "openai_compat"): "the kind's own name in error messages; the name of an open wire format that several servers speak (Neutral protocol line, llm/openai_compat.py:8; neutral=True, backends/table.py:529-535)"` |

Does the producers table belong in a neutral module? Yes, it stays in `guard/producers.py` and is not edited. It is the single list that the redaction tests walk ("data only", producers.py:1-9); the vendor row is a file path that names where text leaves, not logic that depends on the vendor. Moving that row into the vendor module would split the one registry and would be a change on the redaction path for no lock-in gain. The allow entry is the exact pair (module, string), is stale-checked, and does not allow the same string in any other module.

How the guard treats `openai_compat`: by exact entries only, never by a general rule. The module stays a scanned neutral module (it is the neutral default of the `llm` capability, so a vendor host or model id in it must still fail). A neutral module that branches on the string `"openai_compat"`, or a new name containing `openai` anywhere else, still fails.

### Disposition of the 8 uncovered identifier hits (plus 1 module name found by the wider scan)

| # | hit | disposition |
|---|---|---|
| I1 | approvals/gate.py:102 `_SLACK` (used at :254) | FIX: rename to `_ANGLE_CONTROL`. The regex removes angle-bracket control syntax from text for every channel kind, so the name says what the syntax is, not whose. Two lines change in gate.py, no behaviour change; the comment at :100 keeps its wording |
| I2 | approvals/gate.py:404 `_AWS_READ_PREFIXES` (used at :597) | ALLOW: `(f"{PKG}.approvals.gate", "_AWS_READ_PREFIXES"): "G4 command shape: the read-verb prefixes of the aws program only; same exception as LITERAL_OK (approvals.gate, 'aws') (tests/test_g4_parity.py)"`. The table applies only when the program is `aws` (gate.py:595), so a neutral name would be less true |
| I3 | approvals/receiver.py:22 `handle_slack_action` | FIX: rename to `handle_action`, no alias (section 1) |
| I4 | backends/table.py:71 `OpenAICompatSettings` | ALLOW: `(f"{PKG}.backends.table", "OpenAICompatSettings"): "settings class of the neutral openai_compat kind: an open wire format, not one vendor's service"`. `_TABLE_VENDOR_NAME` is NOT widened (that would also stop the string scan inside the class) |
| I5 | defaults.py:130 `K8S_LOG_SLACK_BYTES` (used at sources/kubernetes.py:286) | FIX: rename to `K8S_LOG_MARGIN_BYTES`. English "slack" meaning spare room; renamed so one word keeps one meaning in this repository. Two lines |
| I6 | llm/openai_compat.py:35 `_OPENAI_ALIAS` (used at :47) | FIX: rename to `_MOVING_ALIAS`. Its regex text keeps its existing LITERAL_OK entry (guard:510-513). Two lines |
| I7 | llm/openai_compat.py:74 `OpenAICompatLLM` (also tests/contracts/kinds/llm_wire.py:89, 91) | ALLOW: `(f"{PKG}.llm.openai_compat", "OpenAICompatLLM"): "class of the neutral openai_compat kind (open wire format)"` |
| I8 | runtime/tick.py:38 `TICK_SLACK_S` (used at :304; README.md:40) | FIX: rename to `TICK_MARGIN_S` in all three places. Same reason as I5 |
| I9 (new) | module name `llm.openai_compat` | ALLOW: `(f"{PKG}.llm.openai_compat", "openai_compat"): "module of the neutral openai_compat kind (open wire format); renaming the kind would break every config that says kind: openai_compat"` |

Totals: 5 renames, 2 new `LITERAL_OK` entries, 4 `IDENTIFIER_OK` entries, 1 pinned set of 17 names. No entry covers a whole module or a whole word. Author probe on the prototype: `literal_problems` and `identifier_problems` both return `[]`; removing any one of the 6 allow entries returns exactly the hit it covers (`probe-out.txt`, block 2).

### receiver.py holds no vendor word at all

New test `test_the_receiver_file_names_no_vendor_anywhere`: read `src/hadavin_sdk/approvals/receiver.py` as text (comments and docstrings included) and assert that `re.compile(rf"(?<![A-Za-z0-9])({_W})(?![A-Za-z0-9])", re.IGNORECASE)` finds nothing. Same pattern shape as the precedent at tests/test_http_metadata.py:114-118. Only this file is held to the whole-text rule; other neutral modules name vendors in docstrings by design (the guard skips docstrings, guard:604), for example approvals/hmac_v0.py:4.

## 3. Source registry coverage (F8)

No change to `SourceKind` or `sources/kinds.py`. In the guard, above `coverage_problems`:

```python
@dataclass(frozen=True)
class _SourceEntry:
    neutral: bool

def source_table() -> dict[str, dict[str, _SourceEntry]]:
    from hadavin_sdk.sources.kinds import KINDS
    return {"sources": {name: _SourceEntry("Neutral protocol:" in _source_docstring(kind.settings.__module__))
                        for name, kind in KINDS.items()}}

def coverage_table() -> dict:
    assert "sources" not in TABLE, "the kind table gained a 'sources' capability: drop the adapter"
    return {**TABLE, **source_table()}
```

`neutral` is not hand-set: it is read from the same `Neutral protocol:` docstring line that `neutral_problems` requires (guard:240), reusing `_source_docstring` (guard:215-222). For the one kind today it is true (sources/kubernetes.py:7). `test_every_capability_has_a_neutral_prod_kind_and_two_prod_kinds` (guard:429-430) passes `coverage_table()` instead of `TABLE`.

New `EXCEPTIONS` entry, full text:

```python
    "sources": ExceptionEntry(
        "accepted",
        "Kubernetes (open source, runs on every cloud and on-prem) is the only read-source kind built; the "
        "Source Protocol and the sources.kinds registry are the seam",
        "K5-ITO: first client that needs a second source kind",
        date(2026, 11, 11),
        date(2027, 4, 30),
    ),
```

Status "accepted" (a reasoned exception that a named event ends), matching sources/kinds.py:5-7, which already names trigger K5-ITO.

Tests: (a) the existing test at guard:429 fails when the entry is removed; (b) new `test_the_source_registry_needs_its_exception_entry` states that directly: with `EXCEPTIONS` minus `"sources"`, `coverage_problems(coverage_table(), ...)` equals `["sources: needs a neutral prod kind and >= 2 prod kinds, or an EXCEPTIONS entry"]`; and with the real `EXCEPTIONS` but plain `TABLE` it equals `["sources: exception names no capability: delete the entry"]` (so the entry cannot stay if the adapter is dropped). Author probe: both lists exactly as written. When a second source kind with a neutral one exists, the existing rule answers "sources: passes now, delete its EXCEPTIONS entry" (guard:417-418).

## 4. Trigger rule (F11, first clause)

At guard:422 replace `if not ex.reason or not ex.trigger:` with

```python
NO_ANSWER = frozenset({"", "none", "n/a", "-", "tbd"})
...
        if ex.reason.strip().lower() in NO_ANSWER or ex.trigger.strip().lower() in NO_ANSWER:
```

The message stays `f"{name}: exception needs a reason and a trigger"` (the plant at guard:486-488 keeps passing). The brief asked for the trigger; the same set is applied to the reason because it is the same mistake in the neighbouring field. Author probe: `none`, `None `, `n/a`, `N/A`, `-`, `tbd`, `TBD`, the empty string and a single space are refused; `t` and the real `store` trigger pass. Stated limit: the rule refuses placeholders; it cannot judge whether a sentence is a real event.

The `audit` entry (guard:389-395) then needs a real trigger. Read: audit/chain.py:1-22 (the chain is our own append-only hash chain in the store's database; signer and anchor come from the kind table) and the entry's reason ("chain is our own code on the store; the signer and anchor are the pluggable parts"); the table has `chain` and the demo-only `local_dir` (backends/table.py:502-511). Proposed trigger, **OWNER-CONFIRM**:

> "a client whose compliance rules require the audit record itself to be written to an external ledger or log service they already run (a second audit kind behind the AuditSink Protocol)"

`decided` and `review_by` of that entry stay as they are (2026-10-31, 2027-04-30): the exception is not re-decided, only its missing trigger is filled in. The builder writes this sentence; the PR description carries the line "OWNER-CONFIRM: audit exception trigger"; the lead gets the owner's yes or his own sentence before merge.

## Files

Change: `src/hadavin_sdk/approvals/receiver.py`, `approvals/channel.py`, `approvals/slack_channel.py` (1 line), `approvals/gate.py` (2 lines, rename only), `defaults.py` (1), `sources/kubernetes.py` (1), `runtime/tick.py` (2), `llm/openai_compat.py` (2), `README.md` (line 40), `tests/test_lockin_guard.py`, `tests/test_p7_tick.py` (6 lines, table above), `tests/contracts/test_capabilities.py` (1 new test), `CHANGELOG.md`.
Create: `tests/test_q8a2_callback.py`.
Not edited: `guard/producers.py`, `sources/kinds.py`, `backends/table.py`, `approvals/requests.py`, `approvals/slack.py`, docs/slack-app.md, docs/slack-app-manifest.yaml, tests/test_http_metadata.py.

## Tests

How "fails on main" is proved for this ticket: the new or changed TEST files are run against the `src/` of origin/main (a `git worktree` or `git archive` export of main with only the test files copied in; never by reverting files on the branch). Each must-fail test imports only names that exist on main and fails on its own assertion, so an ImportError does not count as a pass of the proof. That is why the receiver tests live in a new file and not in `tests/test_p7_tick.py` (whose import line 18 cannot load on main after the rename).

### Must FAIL on main (paste each failing run)

`tests/test_q8a2_callback.py` (no Postgres, no conftest fixture: `Approvals(None, None, None, channel, lambda *a: None)` is enough because a bad signature returns before the store is touched, requests.py:76-78; servers on port 0, shut down in `finally`):
1. fake kind: POST `/channel/actions` with a bad signature gives 401 (main: 404).
2. fake kind: POST `/slack/actions` gives 404 (main: 401).
3. a future kind (a `FakeChannel` subclass with `callback_path = "/future-kind/actions"`): its path gives 401, `/channel/actions` gives 404 (main: 404 and 404, so the first half fails).
4. `serve()` raises `ConfigError` with `match=re.escape("callback_path must be a path such as /channel/actions")` for a channel object with no `callback_path`, and for each of: `None`, `""`, `"slack/actions"`, `"/a b"`, `"/a?x"`, `"/a/../b"`, `"/"`, `"/a//b"`, `"/A"`, a 65-character path, the integer 5 (main: does not raise).
5. `getattr(FakeChannel, "callback_path", None) == "/channel/actions"` and `getattr(SlackChannel, "callback_path", None) == "/slack/actions"` (main: None).
6. `hasattr(receiver, "handle_action")`, and neither `handle_slack_action` nor `PATH` exists on the module (the no-alias proof).
7. `handle_action` returns `(413, b"")` for an oversize body and `(401, b"")` for a bad signature (looked up with `getattr(receiver, "handle_action", None)` and an assertion that it is not None, so main fails on the assertion).

`tests/test_lockin_guard.py`, run against main's `src/`:
8. `test_core_logic_names_no_vendor` fails with exactly `hadavin_sdk.approvals.receiver:18: vendor word in a path or key in '/slack/actions'` (author probe).
9. `test_core_names_no_vendor_in_identifiers` fails with exactly five lines: `_SLACK` (gate:102), `handle_slack_action` (receiver:22), `K8S_LOG_SLACK_BYTES` (defaults:130), `_OPENAI_ALIAS` (openai_compat:35), `TICK_SLACK_S` (tick:38) (author probe).
10. `test_the_receiver_file_names_no_vendor_anywhere` fails (9 words on main).
11. Proof that each allow entry is needed and exact, as one parametrised test that runs on the branch: for each of the 2 new `LITERAL_OK` and 4 `IDENTIFIER_OK` entries, the scan with that one entry removed returns exactly the hit(s) it covers. (This is a property of the new guard, not a fail-on-main test; listed here so it is not forgotten.)

Trigger rule and source coverage (guard functions are new or changed, so the proof is "the same call with main's guard file returns the other answer"; paste both runs):
12. `_cov({"x": {"aws": _E()}}, {"x": ExceptionEntry("accepted", "r", t, ...)})` contains "needs a reason and a trigger" for `t` in `none`, `None `, `n/a`, `N/A`, `-`, `tbd`, a single space (main: `[]` for all, dry run 4.2 and 4.3); the same for a reason of `none`.
13. `test_the_source_registry_needs_its_exception_entry` (section 3).

### Regression guards (expected to PASS on main where they can run there; exempt from the fail-on-main proof)

- Slack kind: POST `/slack/actions` with a bad signature gives 401; `/channel/actions` and `/other` give 404 (`SlackChannel("C1", token, secret)` built from parts; a bad signature makes no network call).
- For both kinds: trailing slash, query string, upper case and a longer path give 404.
- tests/test_p7_tick.py:256-279 and :282-300 with the six edited lines; :537 unchanged.
- `tests/contracts/test_capabilities.py`, new `test_channel_names_its_callback_path(channel_factory)`: for each channel kind the contract suite builds, `getattr(channel, "callback_path", None)` is a string that `CALLBACK_PATH` fully matches. (Fails on main; placed here because it is the per-kind contract a future kind must meet.)
- Every existing test in the guard file passes unchanged (author probe: 57 passed on the prototype with the two test edits of sections 3 and 4).
- Plants for the new pattern through `_lit` (guard:655-657): `'/slack/actions'`, `'aws_region'`, `'x.azure.example'`, `'s3-bucket'` each give one "vendor word in a path or key" line; `'aws'` gives one "bare vendor name" line and no second line; `'laws_of_teamsters'` gives none. Plants for the identifier scan (one each): a function name, a camel-case class (`GitHubClient`), a parameter, `self.slack_url = 1`, an annotated class field, a loop variable, `import json as openai`, a lambda parameter, a module file `approvals/slack_helpers.py`, a package folder `aws/x.py`; negative: `awsome = laws = teamster = 1`; a listed name is allowed; a stale `IDENTIFIER_OK` entry is reported. Plants for the documented limit: `'/slackActions'` and `'post to Slack now'` give no line (pins the limit so a later change is deliberate).
- `test_the_table_skip_is_the_pinned_set` (section 2).
- Gate behaviour after the `_SLACK` rename: the existing gate tests (tests/test_g4_parity.py and the G3 tests) pass unchanged; the diff of approvals/gate.py is exactly two changed lines.

### The planted-vendor-string meta test (runs on a temp copy)

`test_a_vendor_path_or_name_planted_in_the_real_receiver_is_caught(tmp_path)`: `shutil.copytree(SRC / PKG, tmp_path / PKG)`; assert both scans return `[]` on the untouched copy; append `PATH = "/slack/actions"` and `def handle_slack_action(): ...` to the copy of `approvals/receiver.py`; assert the string scan returns one "vendor word in a path or key" line and the identifier scan one "in the name 'handle_slack_action'" line, both for `hadavin_sdk.approvals.receiver`; assert the whole-text pattern of the receiver test also finds the word. The real tree is never written.

### Mutants

The repository has no mutant list for this guard: `tests/stage_mutants.py`, `tests/migration_numbers_mutants.py` and `tests/mutation_runner_mutants.py` do not name the guard or the receiver (`git grep` 2026-11-11). The guard proves each of its rules with plant tests, and this ticket adds plants for every new rule. No new mutant list is proposed (lock-in path, not a money, redaction or security guard). If the reviewers require one, the two candidates are: in receiver.py replace `if self.path != path:` with `if False:` (killed by test 2), and make `callback_path()` return `DEFAULT_CALLBACK_PATH` without checking (killed by test 4).

## CHANGELOG ("Unreleased")

Upgrade steps:
- **Breaking for custom code that imports the receiver: `approvals.receiver.handle_slack_action` is now `handle_action`; the constant `approvals.receiver.PATH` is gone. There is no alias.** Change the import. Arguments and return value are the same.
- **The Slack callback URL does not change.** A deployment configured with `backends.channel: {kind: slack, ...}` still answers `POST /slack/actions`; the Slack app manifest and docs/slack-app.md need no edit.
- The receiver now answers only the path of the configured channel kind (`Channel.callback_path`). The demo-only `fake` kind answers `POST /channel/actions` (before: `/slack/actions`). A custom channel class must set `callback_path` (for example `"/channel/actions"`); `serve()` refuses to start with "callback_path must be a path such as /channel/actions" when it is missing or malformed.
- Renamed constants (only relevant to code that imports them): `runtime.tick.TICK_SLACK_S` is `TICK_MARGIN_S`; `defaults.K8S_LOG_SLACK_BYTES` is `K8S_LOG_MARGIN_BYTES`. Values unchanged.

Changed:
- **Lock-in guard.** `tests/test_lockin_guard.py` now also fails CI for a vendor word inside a path or key string (`/slack/actions`, `aws_region`) and inside a module, function, class, variable, parameter or attribute name in shared code. What it does not see: a vendor word in free prose or glued in camel case inside a string, comments and docstrings (except `approvals/receiver.py`, which is checked as whole text), and files that are not Python under `src`. The read-source registry is now held to the "neutral kind and two kinds, or a dated exception" rule (exception recorded: only Kubernetes is built; ends when a first client needs a second source kind). An exception can no longer state "none", "n/a", "-" or "tbd" as its reason or as the event that ends it.

## Gates and evidence

Builder, on the final head only (one full run; affected tests while iterating): `uv run --all-extras --group test ruff check`, `uv run --all-extras --group test ruff format --check`, `uv run --all-extras --group test pytest > log 2>&1; rc=$?` (gate on `rc`, with no cloud variables in the environment; `HADAVIN_TEST_PG_DSN` set so Postgres tests do not skip), `bandit -ll`, `python tests/stage_mutants.py` (unchanged list, must stay green). Then CI, CodeQL, SonarCloud, CodeRabbit.
Then, by the lead: a separate EVIDENCE RUNNER (repeats the fail-on-main runs against main's `src/`, the six "entry removed" probes, the path matrix over HTTP, and the hostile path list of test 4; saves raw output to handover/evidence/Q8a-2/), then fresh egm:* result reviewers on a snapshot of the head, then resolve; at most 2 fix batches; drift report before "done".
Done = every must-fail test shown failing on main and passing on the head, the regression guards green, both scans `[]` on the head, the owner's answer on the audit trigger recorded, all gates green.
Rollback: tag `pre-Q8a-2`; no migration; the rename is the only non-compatible change and is stated in the CHANGELOG.

## Out of scope (each stays where it is tracked)

- Where `post_json` lives (`approvals/slack_channel.py:23` imports it from `llm.common`; second half of F6).
- Vault token rule and the `app.build` override refusals (ticket Q8a-1).
- F2, F3, F4, F7, F9, F10, and the other clauses of F11 (single markdown parser; no neutral flag on the `env` secrets kind).
- A `callback_path` setting in the channel kind's config: not needed to remove the lock-in; the natural moment is the production hosting decision (S11, receiver.py:5).
- The existing prefix-based skip of the STRING scan inside vendor-named classes of `backends/table.py` (guard:552-562) is unchanged; this ticket only pins which names it may match.
