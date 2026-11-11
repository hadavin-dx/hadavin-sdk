<!-- full hand-back report of sub-agent afdf0ff5, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

VERDICT: NOT CLEAN. Blocker 0, Major 1, Minor 9 (plus nits). The review is incomplete on one point: no independent evidence exists for head 5f94f59, so every run-dependent claim is unproven.

Mode: RESULT review by reading only. Snapshot: `/home/user/build/snap/q8a2-5f94f59/`. Main for comparison: `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/`. Nothing was executed.

Evidence: `/home/user/hadavin-sdk/handover/evidence/Q8a-2/5f94f59/RESULTS.md` was absent at the start and at the end of the review. Only `02068eb/RESULTS.md` exists (the previous head); I read it as background, not as proof for this head.

## Findings

### F1. Major. An aliased `from` import of a vendor module passes the name scan (round-1 M3 only partly fixed)
- **Where:** `tests/test_lockin_guard.py:954-956` (`_bound_names`, `ast.ImportFrom` branch): `out += [(a.lineno, a.asname or a.name) for a in n.names]`.
- **Input:** `from hadavin_sdk.approvals import slack as chat` in a neutral module. This is the house idiom at main `approvals/slack_channel.py:17` plus an alias. The same holds for `from hadavin_sdk.llm import gemini as g`.
- **Expected:** one line, `vendor word 'slack' in the name 'slack'`.
- **Actual:** `[]`. The module segments are `["approvals"]`, the bound name is `chat`, and `a.name` is dropped when `asname` is set. The `ast.Import` branch at :951-953 scans both.
- **Written statements this breaks:**
  - guard docstring :22-23: "a name that is only read (it is scanned where it is bound or imported)";
  - test docstring :1428: "A neutral module that imports a vendor module is tied to it even when the name it binds is neutral";
  - `_bound_names` docstring :935-938: "imported names";
  - `CHANGELOG.md:262`: "inside the module path of an import".
- **Smallest fix:** in the `ImportFrom` branch emit both names, as the `Import` branch does: `out += [(a.lineno, x) for a in n.names for x in (a.name, a.asname)]`. Add one plant row to the parametrisation at :1417-1426.
- **Siblings to check:**
  - the plant at :1336 (`from x import a as anthropic_a`) covers only the alias side;
  - `import hadavin_sdk.approvals as ap` followed by `ap.slack.X` is an attribute read and is not seen; state it as a limit or cover it;
  - `MatchClass.kwd_attrs` is not scanned although call-site keywords are.
- The persona file rates "document contradicts code" as Blocker. I rate it Major: it is a guard gap, not a production fault.

### F2. Minor (already on main, security path). `Content-Length` is converted before the path check with no digit cap
- **Where:** `src/hadavin_sdk/approvals/receiver.py:64-65`; identical at main `receiver.py:45-46`.
- **Input:** any path, with header `Content-Length: ` followed by 4301 nines. The header line is under http.client's 65536 limit.
- **Expected:** 404 for a wrong path, 400 or 413 for the right one.
- **Actual:** `int(raw)` raises `ValueError` (Python's 4300-digit limit). It is uncaught in `do_POST`, so there is no HTTP response and socketserver writes a traceback to stderr, outside `_LOG`. An unauthenticated caller can do this on any path.
- **Reuse:** the core already has this guard for the timestamp header, at main `approvals/hmac_v0.py:46-47` (`len(ts) <= 12`, with a comment naming this exact failure).
- **Smallest fix:** `length = int(raw) if raw.isascii() and raw.isdigit() and len(raw) <= 12 else -1`, and move the two lines below the path check.
- **Sibling:** `hmac_v0.py:73` `int(step)` is already inside a `try` that catches `ValueError`, after verification; no change needed.

### F3. Minor. Round-1 item 3 is back in a new test
- **Where:** `tests/test_q8a2_callback.py:194`: `assert _post(port, slashes + path, UNSIGNED) == 404`.
- It sends a 9-byte body to a path the server answers 404 without reading. The server closes with unread data, which is the reset race round 1 flagged.
- The helper docstring at :52-53 says "A probe that expects 404 sends no body".
- **Fix:** delete line 194 (line 193 already covers it), or correct the docstring and accept the race in writing.

### F4. Minor. The module's own name: first segment dropped unconditionally, and one key for equal segments
- **Where:** `tests/test_lockin_guard.py:985`: `mod.split(".")[1:]`.
- **Input 1:** `src/slack_tools/x.py` or `src/aws_helpers.py` (a second top-level package or module under `src`). The segment `slack_tools` is never reported. `_path_segments` at :928-931 drops the first segment only when it equals `PKG`.
- **Input 2:** `hadavin_sdk/aws/aws.py`. `own` is a set, so both segments share the one key `module:aws`; an allowance for the file's name also allows the package's.
- **Fix:** `own` from `_path_segments(mod)`, keyed by position. Sibling: the plant at :1359.

### F5. Minor. Comment in the refusal path is not true for the fallback
- **Where:** `src/hadavin_sdk/approvals/receiver.py:31-34`: "never an empty, multi-line or non-text name in the message".
- **Input:** a channel object of a class made with `type("x\ny", (), {})` and no usable `name`. The fallback `type(channel).__name__` is not checked, so the message holds a line break.
- Also: `name` has no length bound, and a `str` subclass passes `isinstance`.
- This text comes from the channel author, not from the network. The path value itself is never printed.
- **Fix:** choose the name, then apply one check to whichever was chosen (or use `repr`). Sibling: `tests/test_q8a2_callback.py:150-152`.

### F6. Minor. PR notes, line 8, inexact
- **Quote:** "so `POST //slack/actions` reached the signature check (it was still refused there with 401)".
- True only for a bad or missing signature. On main a correctly signed request to `//slack/actions` was handled (200). That is the real behaviour change and should be said.
- "No other status changed" is unproven for this head.

### F7. Minor. `CHANGELOG.md:262`: "No existing check sees less than before" is a universal claim with one counter-case
- `_skipped_table_nodes` (`tests/test_lockin_guard.py:811-813`) now also skips a top-level `async def` in the kind table whose name matches the prefix pattern; main scanned it.
- No such function exists today. Main's `backends/table.py` has 12 classes and 5 functions matching, equal to the 17 pinned names, checked by reading.
- PR notes line 30 states it correctly; the CHANGELOG should say the same, or the widening should be dropped.

### F8. Minor. Ticket text and code differ with no errata line
- TICKET.md section 1: "`do_POST` compares `self.path != path` exactly ... Nothing else in `do_POST` changes".
- Head compares `self.requestline.split()[1:2]` (`receiver.py:68-69`). This changes which requests reach the signature check: fewer.
- Errata E4 says the module-name key is "the single segment"; head uses `module:<segment>`.
- Both changes follow round-1 findings and are stricter, but the ticket is frozen. The lead should record them; the stop rule mentions changes around signature checking.

### F9. Minor. `[pinned]` markers and section labels
- Guard docstring :27: "files that are not Python (YAML, Markdown, SQL outside the migrations rule) [pinned]". The test at :1244-1250 plants YAML and Markdown only, no `.sql`.
- `tests/test_q8a2_callback.py:253` (`test_the_generated_paths_cover_every_length_and_both_joiners`) sits under "must fail on the code before the change" and the file docstring :4-5 says "each test fails there on its own assertion". It uses no product code and passes on main.

### F10. Minor. "Exactly as it was sent" is slightly too strong
- Appears at `receiver.py:66` and `CHANGELOG.md:8`.
- The target is the second whitespace-separated word of the line decoded as iso-8859-1. `str.split()` also splits on TAB, VT, FF, 0x1C-0x1F, 0x85 and 0xA0, so `POST\xa0/slack/actions\xa0HTTP/1.1` is served. The old evidence shows a trailing space served too.
- Same on main; old and new do not differ here.

### Nits
- `valid_callback_path` accepts `str` subclasses (`channel.py:80`). A subclass with its own `__eq__` could match every target at `receiver.py:69`. Trusted code; `type(value) is str` closes it.
- `vendor_words_in`: `s32_bucket` is not seen, because `rstrip` of digits gives `s`.
- `git_HubClient` is not seen (no join across a snake part and the first camel part of the next).
- The fold at :836 turns a constant empty `{""}` in an f-string into `{}`.
- `test_removing_one_name_from_the_pinned_table_set_reports_that_name` (:1585-1588) asserts `any(...)`, not the exact list.
- A name allowance covers any kind of binding of that name (def, variable, keyword, path segment). The count is pinned by the removal test, the kind is not. This is stated in the comment at :675-679.
- Formatter splits recur: `receiver.py:32-34`, `test_q8a2_callback.py:163-165` and :188-190, `test_capabilities.py:158-160`.
- The `TABLE` skip at guard :814 (`"TABLE" in ast.unparse(top)[:12]`) is a substring test, unchanged from main and not pinned.

## (1) Receiver trace

By reading the standard library's `parse_request`:

| Request line | What happens | `do_POST` runs? |
|---|---|---|
| Empty | returns False, no response | no |
| 1 word | 400 | no |
| 2 words with POST | 400 "Bad HTTP/0.9 request type"; `command` stays None | no |
| 4 or more words | 400 (or 505 or 400 on the version word) | no |
| 3 words | `command = words[0]`, `path = words[1]`, rewritten to one `/` if it starts with `//` | yes, for exact `POST` |

- `requestline` is the raw line minus trailing CR LF. The handler's `split()` is the same call on the same string, so `requestline.split()[1]` is `words[1]`.
- Other methods (including `post` in lower case) get 501 on any path.

Where old and new differ:
- Only targets that start with `//`.
- `//<path>`, `///<path>` and so on: old matched (401, or 200 when signed); new gives 404. That is right: it is a different target, and the valid grammar never starts with `//`.
- No input matches new but not old.
- Absolute form (`http://host/path`): 404 in both.

Order of checks:
1. Method (stdlib).
2. `Content-Length` conversion (F2).
3. Path, 404.
4. Bad length, 400.
5. Length over `MAX_BODY`, 413.
6. Body read. It comes after both the path check and the cap, at most 65536 bytes, blocking with no socket timeout (as on main).
7. `handle_action`: length again, then `parse_decision`. In `hmac_v0.verify` freshness comes first, then `compare_digest`; both give the same 401.

What an unauthenticated caller learns or costs:
- the path, by 404 against 400, 401 or 413;
- the body cap, by 413;
- the Python version, from the stdlib `Server` header;
- one thread per held connection on the right path.
- `log_message` (:82-83) passes the raw request line to the logger at DEBUG without the stdlib's control-character escaping (as on main).

## (2) `valid_callback_path`

- **Grammar:** `/[a-z0-9]+(?:[/-][a-z0-9]+)*`, ASCII only, `fullmatch`, so `"/a\n"` is refused.
- **Length:** checked before the regex; 64 accepted, 65 refused.
- **Types:** bytes, int and None are refused by `isinstance`.
- **Callers:** `receiver.callback_path` and the contract test (`tests/contracts/test_capabilities.py:154-163`). Both use the one function; the docstring claim is true.
- **Reuse:** I found no existing URL-path validator in main's `src` to reuse.

## (3) Guard as code

**Name scan visits:**
- def, async def and class names;
- `except ... as`;
- `MatchAs`, `MatchStar`, `MatchMapping.rest`;
- the three type-parameter kinds;
- every `ast.arg` (lambda, `*`, `**`, positional-only, keyword-only);
- `ast.keyword` (calls and class keywords);
- `Name` in Store context: assignments, annotated and augmented assignments, `for`, `with`, comprehension targets, walrus, `type` alias name;
- `Attribute` in Store context;
- `Import`: alias and all path segments;
- `ImportFrom`: module segments and alias-or-name.

**Name scan skips:**
- anything in Load or Del context: annotations, decorators, bases, attribute reads, `del`;
- `global` and `nonlocal` name lists (the binding is seen at its Store);
- `MatchClass.kwd_attrs`;
- the original name of an aliased `from` import (F1);
- names that exist only as strings (`__all__`, `setattr`, functional `namedtuple`). These fall to the string scan, which does not split camel case.

**String scan:**
- Visits `Constant` (str and bytes), `BinOp` with `+` (folded), and `JoinedStr`.
- Skips the first-statement constant of a module, class or function; `%` and `.format` joins; and the table skip.

**Word-boundary rule:**
- The two entries together equal the docstring's rule: (start or separator) word (separator, `:` or end).
- `$` without MULTILINE also matches before a final newline, a harmless over-match.
- The character class `[/_.=?&#@,;()+-]` is well formed.

**Allowances:**
- `(module, text)` covers every occurrence of that literal in the module under any label. Count and labels are pinned by `_LITERAL_OK_LABELS`, for example two lines for `'aws'` in the gate.
- Completeness is tested at :1559-1561.
- No removal test is vacuous: 10 and 6 non-empty parameter sets, tied to the live dicts.

**Deterministic generator:**
- `test_the_generated_paths_cover_every_length_and_both_joiners` uses the same seed and the same 500 draws as the accept test, so it speaks for that test.
- Whether seed 8802 really yields all 63 lengths is run-dependent and unproven.
- The refusal test (seed 8803) has no such coverage check; each foreign character is tried at one drawn position only.

## (4) Tests

- **Counts by reading:** guard file 90 test functions and 158 cases; callback file 17 functions and 38 cases. Both match the PR notes.
- **Removed or weakened on main:** none. `test_the_anchor_is_a_capability_with_a_prod_kind_besides_s3` only moved. The `test_p7_tick.py` edits are the six ticket lines.
- **Suppression comments:** none added; the two `# noqa: S311` are gone. The remaining `noqa` lines are main's.
- **Credentials:** built from parts (`test_q8a2_callback.py:21-22`).
- **Plants:** the 29 name plants, 7 snake-case plants and 5 import-path plants each assert what the name says, traced by hand. The fifth import-path case tests an imported name, not a module path.

## (6) Statements checked and found true by reading

- 26 words (15 plus 11).
- 10 string allowances (4 old, 6 new) and 6 name allowances.
- 17 pinned names, equal to main's prefix matches.
- `gcs_retention_lock` stands at main `table.py:188` (scanned) and :484 (inside TABLE, skipped).
- `auth_aws` at main `store/postgres.py:115`.
- Signature and freshness code is not in the diff; `gate.py` has two renamed lines.
- New CHANGELOG bullets come first in both sections.
- The audit exception and the trigger rule are untouched (E1).
- The OWNER-ACK line is present.

## Round-1 checklist

| Item | Status | Where verified |
|---|---|---|
| M1 no evidence | NOT fixed for this head | no `5f94f59` folder |
| M2 `gcs` prefix | fixed | guard :710-712, :671-673, :690-694, plant :1253 |
| M3 import path | PARTLY | F1 |
| m1 snake pairs | fixed | :893, :1401-1414 |
| m2 separators | fixed and stated | :772, :1226 |
| m3 "each limit pinned" | partly | F9 |
| m4 one checker | fixed | `channel.py:76-83` |
| m5 read once | fixed | callback test :155 |
| m6 CHANGELOG `serve()` only | fixed | `CHANGELOG.md:8` |
| m7 build module | fixed | :463 |
| m8 owner line | present | PR notes line 5 |
| m9 comment | fixed | :713-716 |
| F1 `noqa` | fixed | grep |
| F2 errata lists | present in PR notes | lists themselves not verifiable |
| 3 unread body | PARTLY | F3 |
| 4 near-miss list | fixed | callback test :317-326 |
| 5 completeness of removal test | fixed | :1559 |
| 6 key collision | fixed | `module:` key, :1439 (residue in F4) |
| 7 two lines for f-string | stated and pinned, not changed | :1232 |
| 8 snake two-part words | fixed | same as m1 |
| 9 `name` in error | fixed | `receiver.py:30-34` (residue in F5) |
| 10 lazy registry import | fixed | :444-449 |
| 11 assertion message | fixed | :501-503 |
| Nit: annotation comment split | fixed there, same split recurs elsewhere | `channel.py:89-90`; see Nits |
| Nit: "last segment" comment | fixed | :675-679 |
| Nit: "the one word list" | fixed | :738-740 |
| Nit: `AsyncFunctionDef` | changed | :811-813 (see F7) |

## Not checked

- Anything that needs a run on 5f94f59: pytest, ruff, bandit, fail-on-main, the six removal probes, the HTTP matrix, raw-socket request lines (tab, 0xA0, oversize `Content-Length`), and the merge with Q8a-1.
- `tests/test_http_metadata.py` is not in the snapshot, so the regex in `test_the_word_list_covers_the_list_of_the_http_metadata_test` (:1055-1063) is unverified.
- The measured hit lists in the PR notes (25 names, 28 lines, +0 and +3 counts).
- Leftover users of the renamed names outside the snapshot's changed files.
- `approvals/requests.py` beyond `receive`, `approvals/slack.py`, `sources/kinds.py`, and the docs.
- The on-disk checkout was not read.
