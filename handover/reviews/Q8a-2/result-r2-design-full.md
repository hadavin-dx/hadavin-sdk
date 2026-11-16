<!-- full hand-back report of sub-agent a5696921, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

VERDICT: NOT CLEAN. 0 Blocker, 1 Major, 10 Minor (plus 3 nits). By reading only.

Evidence not yet available: `/home/user/hadavin-sdk/handover/evidence/Q8a-2/5f94f59/` does not exist (checked at the start and at the end; only `02068eb/` and the dry run are there). Nothing below was run by me. Every claim that needs a run is marked UNPROVEN.

Short answers to the six questions:
1. The `do_POST` change is sound. It only narrows what is served. The signature check is untouched and is still the only thing between a network caller and a recorded decision. The ticket deviation is acceptable but is not labelled as one (m8).
2. `valid_callback_path` is tight and is the single checker for both the receiver and the contract test.
3. The guard's allowances are exact and each has a removal test. The string scan's boundary set is where it falls short (M1).
4. Nothing is wider than main today; one hypothetical case (m6).
5. Wording is mostly precise; the owner line and the refusal message are not plain enough (m3, m4).
6. No new dependency.

## Findings

### M1 (Major): the string scan's boundary set was built from examples, and `|` was left out because it finds things
- Where: `/home/user/build/snap/q8a2-5f94f59/tests/test_lockin_guard.py:770-776` (`_SEP`, `PATTERNS`), docstring lines 16-22, `UNSEEN_STRINGS`.
- Lines that pass both scans in any neutral module (traced against the pattern at line 776, which is searched with `re.IGNORECASE`):
  - `KIND = re.compile(r"^(slack|teams)$")` — `|` is no boundary. This is the usual way to write a vendor-specific branch.
  - `Q = "SELECT 1 FROM t WHERE kind = 'slack'"` — a quote is no boundary; the SQL rule covers `.sql` files only.
  - `URL = "https://{host}/{aws_region}/x"` — `{` is no boundary, so `str.format` field names pass, while `"%(aws_region)s"` is caught.
  - `SECTION = "[slack]"`, `TAG = "<slack>"`.
  - `KEY = "channel:slack"` — `:` counts only after the word; `"slack:channel"` is caught.
  - `"kind: slack"`, `"aws s3 ls"` — whitespace (free prose; a fair limit).
- An instance already in the tree, with no recorded exception: `/home/user/build/snap/q8a2-5f94f59/src/hadavin_sdk/approvals/gate.py:89-90` names the link schemes `slack` and `ms-teams` (`...|tel|slack|` then `ms-teams|vscode|...`), and `:671` has `|s3|`. Bare `'aws'`, `'s3'` and `'gcloud'` in the same module each need an exact `LITERAL_OK` entry; these do not.
- The stated reason is at line 770-771: "`|` is left out: on main it adds three hits". That blinds the scan to avoid hits, where the ticket's method is to fix or exactly allow each hit.
- The three hits are two constructs: `_URL`, and `_WRITE_SHAPES` reported twice by the join rule (lines 648 and 670).
- Rules broken:
  - `fix-dont-defer-be-honest.md` rule 1: a gap found in round 1 (m2), measured, then filed as a stated limit although it is fixable now.
  - `class-level-fixes.md`: the boundary is not a derived grammar, and sibling characters were not searched.
  - The ticket's own stop rule (E4/E5): only more than 10 extra hits justifies keeping a limit; this is 3.
- Smallest fix at the choke point (`_SEP`):
  - Define the boundary as "any character that is not an ASCII letter, digit or whitespace" on both sides, with `:` on both sides, not as an enumerated list.
  - Measure on main and give each hit an exact `LITERAL_OK` entry with its reason (the gate ones are legitimate).
  - Move `"slack|teams"` from `UNSEEN_STRINGS` to the caught plants; the property test already iterates `_SEP`.
- If the full-text key of a 2 KB regex is judged too brittle as an allow key, that is a defect of the allow mechanism to state and decide. It is not a reason to drop the separator.
- Basis for the grade: this is Major because a rule is broken, with the concrete inputs above; nothing in the tree is defective today beyond the unrecorded gate words.

### m1 (Minor): two-part vendor names with a separator were fixed for names only
- Where: `tests/test_lockin_guard.py:19-22` and `UNSEEN_STRINGS`.
- `open_ai_key = 1` is caught; `X = {"open_ai_key": 1}`, `"/pager-duty/hook"`, `"git-hub"` and `"cloud_watch_ns"` pass.
- Seven of the 26 words are affected: pagerduty, cloudwatch, openai, github, gitlab, digitalocean, openstack.
- Rule: `class-level-fixes.md` (the sibling was left open).
- This is an honest stated and pinned limit, but cheap to close. Fix: in the string pattern, allow one optional separator at the known split of those seven words (`pager[-_./]?duty` and so on), measure on main, dispose of the hits.

### m2 (Minor): names that are only read pass, and the docstring's reassurance is false
- Where: `tests/test_lockin_guard.py:26-27`, "a name that is only read (it is scanned where it is bound or imported)".
- `if cfg.slack_signing_secret:` or `x = settings.aws_region` in a neutral module passes. The field is bound in a vendor module or in a skipped kind-table class such as `SlackSettings`, which is not scanned at all.
- This is the most common way shared code ties itself to a vendor, and it matters more than the camel-case limits.
- It is in the ticket's plan ("Not scanned: names that are only read"), hence Minor.
- Fix: measure `ast.Attribute` and `ast.Name` in Load context on main. If the count is within the ticket's stop rule, scan them; otherwise reword to "a name that is only read is not seen, also when the place that binds it is a vendor module".
- The CHANGELOG's "What it does not see" list omits this limit and the look-alike-letter limit.

### m3 (Minor): the owner-acknowledgement line is not clear to a non-technical reader
- Where: `/home/user/build/snap/q8a2-5f94f59/PR-NOTES-builder.md:5`.
- It uses "OWNER-ACK", "K5-ITO", "registry of read sources", "kind" and "neutral kind" unexplained, and never says what the owner must do or what a "no" means.
- The code already records `"accepted"`, decided 2026-11-11 (`tests/test_lockin_guard.py:428-435`), before the owner has answered.
- Rule: `wording-clear-for-everyone.md` rules 1, 3 and 4.
- Proposed text: "Owner, please say yes or no. Today the core can read from one kind of system only: Kubernetes. Our rule asks for two, or a written exception with an end date. This change writes that exception: it stays until the first client needs a second system to read from, and it is looked at again by 30 April 2027. If you say no, a second read source must be built before this merges."

### m4 (Minor): the refusal message does not say what is checked
- Where: `/home/user/build/snap/q8a2-5f94f59/src/hadavin_sdk/approvals/receiver.py:35`.
- `callback_path = "/Teams/Actions"` or `"/teams_hook"` gets "must be a path such as /channel/actions"; both look like such a path to their author.
- Rule: `wording-clear-for-everyone.md` rule 3.
- Fix: append the rule to the message: "(a `/`, then lower-case letters and digits in parts joined by `/` or `-`, at most 64 characters)". The tests match the current text as a substring, so appending is compatible.

### m5 (Minor): the round-1 flake class is back in a new test
- Where: `/home/user/build/snap/q8a2-5f94f59/tests/test_q8a2_callback.py`, `test_a_double_slash_in_front_of_the_path_is_not_served`: `_post(port, slashes + path, UNSIGNED) == 404`.
- The server answers 404 and closes without reading the body; `http.client` sends headers and body in two writes, so a reset can race the response.
- Round 1 (codebase item 3) removed exactly this from the helper's default.
- UNPROVEN: needs repeated runs. On Linux loopback it probably passes.
- Fix: drop the with-body 404 probes, or drain `min(length, MAX_BODY)` before answering 404 (that is a behaviour change and needs the lead).

### m6 (Minor): `_skipped_table_nodes` now also skips a vendor-prefixed `async def`
- Where: `tests/test_lockin_guard.py:811-813`.
- The string scan of main would scan the strings inside such a function. None exists today, and the pinned-set test forces a hand edit, so nothing is less today.
- The CHANGELOG sentence "No existing check sees less than before" is absolute. The stricter harmonisation is the opposite one: do not skip `AsyncFunctionDef` in either scan.
- Fix: revert that widening, or write "sees less today".

### m7 (Minor): the word list has no chat vendors besides slack and teams
- `callback_path = "/discord/actions"` in `FakeChannel`, or `def handle_discord_action` in `receiver.py`, passes both scans and the receiver whole-text test.
- The same holds for telegram, webex, whatsapp, twilio, zoom, opsgenie, datadog, okta, servicenow and jira.
- The limit is stated and pinned, and the list was set by errata E5, hence Minor.
- For a ticket whose purpose is the channel receiver, add at least the chat and paging vendors and measure.

### m8 (Minor): the ticket deviation is not named as one
- Where: `PR-NOTES-builder.md:8`.
- The ticket says "`do_POST` compares `self.path != path` exactly... Nothing else in `do_POST` changes."
- The notes describe the change accurately but do not say it departs from the frozen ticket and needs the lead's recorded yes.
- I judge the deviation acceptable. It makes the ticket's own table true ("anything else: 404") and matches the grammar's "no empty segment".

### m9 (Minor): CHANGELOG wording
- "request target" is used without saying what it is (the path as written in the first line of the request).
- "each one has a test that removing it reports exactly what it covers" holds for the 10 string and 6 name allowances. The 17 pinned table names are tested with `any(...)`, not exactly, and whole vendor modules are exempt without such a test.
- Fix: say "each (module, string) and (module, name) allowance".

### m10 (Minor): three boundary limits are neither listed by example nor pinned
- `":"` before the word, quotes and brackets are covered only by the general sentence, with no plant.
- Folds into M1 if that is fixed.

### Nits
- n1: `tests/test_lockin_guard.py:28` lists `open_ai` among parts that "happen to spell a word", while `open_ai_key` is an intended catch with its own plant.
- n2: "SQL outside the migrations rule" is marked [pinned], but only YAML and Markdown are planted.
- n3: `receiver.py:31`: a printable channel name of any length goes into the error text; cap it. `callback_path()` returns a `str` subclass unchanged; `str(path)` would close that (trusted code, so low).

## Question 1: the `do_POST` comparison (by reading the standard library's parser)
- `parse_request` computes `words = requestline.split()` and takes `path = words[1]`. So `self.requestline.split()[1:2]` is exactly the path before the `//` rewrite, in every CPython version.
- The new accept set is a subset of main's: if `words[1] == path`, the path cannot start with `//` (grammar), so main's condition held too. No target that is not the configured path can newly reach the signature check.
- Request lines that never reach `do_POST`:
  - an empty line (the parser returns False);
  - a two-word HTTP/0.9 line (400: only GET is allowed);
  - four or more words (400).
- Request lines that get 404, as on main:
  - absolute form;
  - a query string;
  - non-ASCII (the path is ASCII only).
- Tabs and other whitespace: `str.split()` also splits on `\x0b`, `\x0c`, `\x1c`-`\x1f`, `\x85` and `\xa0` after the latin-1 decode. So `POST\xa0/slack/actions\xa0HTTP/1.1` is served. This is unchanged from main and the signature is still required. A front proxy that filters by path may parse that line differently; this is not new here, state it when hosting is decided.
- The only newly refused form is a leading `//`, `///` and so on. A reverse proxy that joins paths with a doubled slash now gets 404 on every click. It fails closed, and the CHANGELOG states it.
- 404s are logged at debug level only, so an operator sees nothing by default.
- Compared with `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/approvals/receiver.py`: `handle_action` is identical to `handle_slack_action` apart from the name and docstring. The order of the length, 400, 413 and `approvals.receive(..., record_only=True)` steps is unchanged.

## Question 2: `valid_callback_path`
- Accepts: a `str` of at most 64 characters that fully matches `/[a-z0-9]+(?:[/-][a-z0-9]+)*`.
- Refuses: `%`, `.`, `..`, `_`, upper case, an empty segment, a trailing joiner, control characters, non-ASCII (explicit ASCII ranges, no IGNORECASE), `bytes` and non-strings.
- One checker: `receiver.py:29` and `tests/contracts/test_capabilities.py` both call it.
- No shadowing is possible: one path per server, read once (tested).
- A vendor-fixed path with a dot, underscore or capital could not be expressed. That is acceptable, since we choose the URL.

## Question 4: wider than main?
No. `_TABLE_VENDOR_NAME` and `VENDOR_MODULES` are unchanged, the first pattern is a superset, and every allowance is an exact pair for a hit that main did not report. The one exception is m6.

## Question 6: single-dependency audit
- No new external dependency: only the standard library and pytest, both already used.
- `receiver.py` holds no vendor word (by reading).
- The neutral default path is used only by the demo-only `fake` kind. The `channel` capability still has one production kind, under its existing exception (review by 2027-01-31); this change does not touch it.
- `SlackChannel.callback_path` is a literal in the vendor module, not config. The ticket puts a config setting out of scope with a named moment (the hosting decision), which I accept.
- The guard's word list is hand-kept; the subset test against `tests/test_http_metadata.py` stops drift one way.

## Round-1 checklist (verified in the code or diff, not from the builder's notes)

| Item | State | Verified where |
|---|---|---|
| Design M1, no evidence for the head | not fixed | no evidence folder for 5f94f59 |
| Design M2, `gcs` in the prefix pattern | fixed | pattern equals main; exact name and string entries; plant `test_plant_a_vendor_literal_inside_the_gcs_settings_class_is_caught` |
| Design M3, import module path | fixed | `_path_segments`, `_bound_names`, 5 plants and a negative; relative imports covered by reading |
| m1, two-part names | partly | names fixed; strings left (my m1) |
| m2, string limit stated loosely | partly | `, ; ( ) +` added, sentence now exact; `|` left out (my M1) |
| m3, "each limit is pinned" | fixed | wording is now "[pinned] where a test exists"; unlisted word and non-Python plants added |
| m4, one checker for grammar and length | fixed | `valid_callback_path` |
| m5, "read once" untested | fixed | `test_the_path_is_read_once_when_the_server_starts` |
| m6, CHANGELOG scope | fixed | now says `serve()` and that `handle_action` does not look at the path |
| m7, build function's module | fixed | `source_table` plus the `vendor_build` plant |
| m8, owner line | partly | present, unclear (my m3) |
| m9, "both scans skip" comment | fixed | comment reworded |
| Codebase F1, two `noqa` | fixed | none added in the diff; own small number generator instead |
| Codebase F2, errata items visible | partly | hit lists are in the PR notes; raw files not in the snapshot |
| Codebase 3, 404 probes with a body | partly | helper fixed; reintroduced in one test (my m5) |
| Codebase 4, near-miss list | fixed | percent-encoding, inner `//`, absolute form added |
| Codebase 5, completeness check | fixed | `test_every_allowance_is_checked_by_a_removal_test` |
| Codebase 6, module-name key | fixed | `module:` key and test |
| Codebase 7, two lines for a join | stated and pinned, not removed | needs two allow entries |
| Codebase 8, snake two-part names | fixed | for names |
| Codebase 9, unchecked `name` in the error | fixed | `isprintable` fallback and test |
| Codebase 10, registry import at module level | fixed | `_source_kinds()` imports lazily |
| Codebase 11, assertion message | fixed | message added |
| Nits | fixed | the async one by widening (my m6) |

Errata, by reading:
- E1: the audit entry still says "none" and there is no NO_ANSWER rule.
- E2, E5, E6, E7, E8 and E9 are present.
- E3 is met with `valid_callback_path` instead of `CALLBACK_PATH`, consistent with round-1 m4.
- E10: I counted 90 `def test_` in the guard file. In the callback file I counted 17 test functions and 38 cases. Both match the notes.

## UNPROVEN (needs a run)
- All tests pass on the head and fail on main.
- Both scans return `[]` on the head.
- The "+0" and "+3" hit counts and "the same 17 as before".
- 158 collected cases in the guard file.
- `from tests.test_http_metadata import VENDOR_WORDS` is importable under the repository's pytest setup.
- `_post(port, VENDOR)` with an empty body gives 401 for the Slack kind.
- ruff, bandit, the merged tree with Q8a-1.
- The flake in m5.

## Not checked
- Any head source outside the eight files in the snapshot. I could not grep the head for other `|`, quote or attribute-read cases; the gate.py instances are the only ones I saw.
- `tests/contracts/conftest.py`: whether the contract suite builds the Slack kind.
- `Approvals.receive` and `parse_decision` bodies. They are not in the diff, and I relied on the diff for "unchanged".
- The builder's raw files in `/home/user/build/q8a2-build/`.
- The round-1 evidence folder.
- docs, the Slack manifest, CI configuration.
- CPython behaviour is from my knowledge of `http/server.py`, not from reading the installed file.
