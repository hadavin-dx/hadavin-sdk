# Ticket Q8b (rev 2, after plan review round 1): two masking leaks, a half-masked value under a credential key and card text that hides an e-mail address from the redactor
Source: reviews/Q8/redaction-sweep.md F5, F6; plan reviews reviews/Q8b/plan-r1-readiness.md and plan-r1-design.md; decision D-011 (AUTONOMOUS-DECISIONS.md). Branch: NEW `core/q8b-partial-mask-and-card-redaction`; draft PR against main. Redaction path: result-review rounds uncapped. Nothing is built; one fresh round-2 reviewer judges this revision first.

Words used here. The *redactor* is the pattern-based masking code (`guard/redact.py`, reached through `guard.runmap.redact_text`). A *placeholder* is what it writes in place of a value (`<EMAIL_1>`). The *fixed mask* is the text `<SECRET_REDACTED>`. The *map* is the per-case list "placeholder -> original value"; a value in the map is *registered* and the redactor replaces its exact copies in every other text of the case. A *credential key* is a key whose name says its value is a login secret (rule in 1f). A *card* is the text a person reads in a chat channel before approving an action. *Bracketing* a domain means writing `evil[.]com` so a chat program makes no link.

HARD LIMIT: no edit of `src/hadavin_sdk/guard/redact.py`, `guard/runmap.py`, `tools.py` (the other redaction pull request, PR77, owns them). Files this ticket edits: `k1b/redaction.py`, `approvals/gate.py`, `approvals/channel.py`, `approvals/slack_channel.py`, `guard/producers.py` (two data rows), three new test files, two existing test files, one new mutant list, `.github/workflows/ci.yml` (one step), `CHANGELOG.md`.

## Merge order and couplings (D-011)
PR77 lands FIRST. Q8b may be built in parallel on today's main, then is rebased on the merge base that holds PR77, and on that base the builder RE-RUNS: the reproduction scripts, every fail-on-base proof (N1-N8, S1-S5, P1, P2), the measured table below, and the mutants. A must-fail test that passes on the new base because PR77 already fixed it is reported and moved to the regression list, not deleted. Couplings to PR77's files, each pinned by a test that asserts the ABSENCE of made-up originals, never a placeholder number or kind:
- `guard/redact.py:577-590`: the quoted-assignment rules list the key word `secret` and take a quoted value of 1 to 256 characters. 1b depends on both. If PR77 changes them the result falls back to the fixed mask (safe) and N2 fails loudly.
- `guard/redact.py` copy sweep (a registered SECRET of 4 or more characters is replaced at every copy): 1c and the M5 change depend on it.
- `runmap.PLACEHOLDER` (`guard/runmap.py:31`): the one definition of a genuine placeholder, used by 1a.
- `runmap.canonical` / `strip_ansi` (sweep F3, F4): can change WHICH spellings N4 and the ESC case mask; the tests assert only absence.
- `approvals/gate.py`: this ticket edits lines 229-351; sweep F4 names 336-338. If PR77 touches `gate.py`, rebase by hand there.
- No production or test code of this ticket reads a private name of `runmap` (rev 1's `_VALUE_END` test is dropped; see 1b).

## Reproduction on main (author, 2026-11-11; real functions; tree `/home/user/build/EV-P89-db0d9eb`; the seven files this ticket reads or edits were compared byte for byte with origin/main 2a8c2aa and are the same; scripts and logs in `/home/user/build/q8b-author/`; keys built from parts because the repository's secret scan refuses the long key word followed by a quoted text)
- F5 REPRODUCED: `{'password': 'correct horse battery staple'}` -> `{'password': '<SECRET_1> horse battery staple'}`; `{'password': 'a b'}` -> `{'password': 'p<SECRET_1>ssword=<SECRET_1> b'}`.
- F5b (author's finding) REPRODUCED: a Secret entry masked with the fixed mask stays readable in a log line of another record (row 34 below).
- F6 REPRODUCED: `clean('contact bob.smith@example.com')` -> `'contact bob.smith@example[.]com'`; `runmap.redact_text` alone gives `'contact <EMAIL_1>'`. Random probe, 4,000 texts, seed 8: main keeps a standalone identifier in 2,619.
- F6b (author's finding) REPRODUCED: a redaction that removes a backtick leaves a bare domain outside code (row 58).
- NOT established: whether the standard runtime ever hands `clean()` a real address. `runtime/agent_loop.py:269-284` says plans hold placeholders; `clean()` is the only line for a diagnosis text, a notice text, a raw value the model typed, or an integrator's own plan.

## Rung table (CODE-LAST)
| component | need | rung tried | evidence (2026-11-11) | what only our code gives | verdict |
|---|---|---|---|---|---|
| acceptance rule in `_pair` (1a) | a value under a credential key reaches the model only as placeholders | rung 1 reuse: `runmap.PLACEHOLDER`, existing `MASKED` | measured table rows 1-33 | redaction before the model is a listed safety guarantee; a secret-finding library (detect-secrets, Presidio: UNVERIFIED, no network) would replace the redactor, not this decision about its result | KEEP-CODE |
| registering the whole value (1b, 1c) | a pattern-free secret is masked where it is repeated | rung 1 reuse: the redactor's own quoted rule under the key word `secret`; no second sweep engine | rows 34-36 | thin glue | KEEP-CODE (glue); the general case goes to the redactor after PR77 (follow-up in "Limits") |
| credential-key rule (1f) | one rule for "this key names a credential" | rung 1 reuse: extend `sensitive()` in place; the redactor's key list cannot be imported as a rule (it is inside patterns) | rows 1-11 | - | KEEP-CODE (one function, word lists as module constants) |
| order of steps on a card (2) | every identifier the redactor knows is masked, no bare domain | rung 1 reuse: existing `sanitise_text`, `withhold_commands`, `redact_text`; only the bracketing moves last | rows 46-61; prototype comparison in rev 1 (the order "redact, sanitise, redact" failed two existing leak tests) | a ready-made defang package (UNVERIFIED) cannot fix the ORDER | KEEP-CODE |
| mutants, seeded random tests | proof the tests bite | rung 1 reuse: `tools/mutation_runner.py`, seeded `random.Random` (no `hypothesis` in the project) | read in source | - | reuse |

## Bug classes
- F5/F5b/1f: "CHANGED IS TAKEN FOR MASKED" (`k1b/redaction.py:114`), plus its neighbour "THE KEY RULE AND THE VALUE RULE DRIFTED APART" (`sensitive()` at 88-100 and the redactor's key list name different keys). Own promise broken: `_pair` docstring 105-106 "a value under a credential key never reaches the model". CWE-212, CWE-636: from memory, cwe.mitre.org blocked today; the builder verifies the titles or removes the numbers.
- F6/F6b: "A REWRITE THE DETECTOR CANNOT READ RUNS BEFORE THE DETECTOR", and its mirror "a decision about the final text is taken on an earlier text". Own promises: `approvals/channel.py:1`, `approvals/requests.py:35`; the same class is named in `runmap.safe_head` (`guard/runmap.py:533-535`). CWE-696: from memory, same caveat.

## Behaviour 1: `k1b/redaction.py`
1a. `_pair` accepts the redactor's result only when (i) it starts with `<key written>=`, (ii) if this function wrapped the value in a quote, the rest starts and ends with that quote, and (iii) what remains fully matches `_ONLY_PLACEHOLDERS = re.compile(rf"(?:{runmap.PLACEHOLDER.pattern})+")`. Anything else: next attempt; no attempt left: `f(value)` then `return MASKED` (lines 116-117 kept). A result that does not start with the key written is never accepted (the `p<SECRET_1>ssword=` case). At most 4 calls of `f` per value (2 spellings x 2 attempts), plus the final `f(value)` (design m7).
1b. What is written to the redactor (D-011, readiness B1, design M3, M6). `FALLBACK_KEY = "secret"`, `MAX_SPELLING_CHARS = 255`, `_PLAIN_CHARS` = the visible ASCII characters U+0021 to U+007E minus `; & , " '` (an ALLOWLIST; any other character, including every `str.isspace()` character, ESC and all non-ASCII, makes the value not plain). `_SAFE_KEY = [A-Za-z0-9_.-]{1,60}`. For one spelling `text`:
- empty, or longer than `MAX_SPELLING_CHARS`: nothing is tried (fixed mask).
- plain: under a credential key that fully matches `_SAFE_KEY`, try `key=text`, then `secret=text`; under a non-credential key of a Secret, only `secret=text`.
- not plain: NEVER written under its real key and never unquoted. Try `secret="text"` if the text holds no `"`, else `secret='text'` if it holds no `'`; a text with both quote marks: nothing is tried.
- Spellings are the value as written and, when it decodes (line 109), its base64-decoded text. Outside a Secret the first accepted spelling is returned (as today). The rev-1 test on the private `runmap._VALUE_END` is replaced by the behavioural tests S5 and N3.
1c. `_walk` gets a fifth parameter: `def _walk(obj, f, key=None, secret_data=False, known_secret=False)`. It is passed on unchanged at the string branch (`_pair(key, obj, f, known_secret)`), at lines 146, 149 and 151 (dict values, lists, tuples) and is set to `True` at line 144 for every entry of `data` / `stringData` of a `kind: Secret`. With `known_secret=True` EVERY spelling is tried (the base64 text and the decoded text are both registered) and the first accepted result is returned. `_pair` with a non-credential key and `known_secret=False` (a string merely nested under a credential key, `{"credentials": {"user": "svc"}}`) tries nothing: `f(value)`, fixed mask, as today.
1d. Kept (D-011 ruling 7): a string that is exactly a UTC timestamp (`parse_ts`, full match) passes unmasked even under a credential key. Near misses are masked (rows 41-45). The `_pair` docstring names this one exception.
1e. BEHAVIOUR CHANGE, stated (design M5): every entry of a Secret's `data` / `stringData`, whatever its key is called, is registered as a secret, in both spellings; the redactor then replaces every copy of 4 or more characters anywhere in the case, also inside a longer word. Measured (row 37): `{'data': {'DB_NAME': <base64 of "orders">}}` plus the log line `orders-api timeout` gives `<SECRET_2>-api timeout`. On main that entry got the fixed mask and the log line stayed whole. Why accepted: a Secret entry is secret by its location (least privilege); cost: a non-secret word stored in a Secret (a database name, a user name) disappears from the evidence the model reads. Pinned by test G7 and a CHANGELOG line. Replay scores before and after: NOT measured, see "Could not establish".
1f. Credential-key rule (design M1, M2), one function `sensitive(key)`, replacing `SENSITIVE_KEY` (88-91) and its body (97-100). Split the key into lower-case words: camelCase boundary first (existing `_CAMEL`), then at `_ . -` and white space. The key is a credential key when BOTH hold:
- some word is in `CREDENTIAL_WORDS` (pass, password, passwords, passwd, pwd, passphrase, secret, secrets, token, apikey, apikeys, authorization, credential, credentials, bearer), OR ends with one of `GLUED_ENDINGS` (password, passwd, pwd, passphrase, secret, token, apikey, secretkey, accesskey, privatekey), OR is `key`/`keys` right after a word in `KEY_QUALIFIERS` (api, private, access, secret, signing, encryption);
- the LAST word is not in `SETTING_WORDS` (enabled, disabled, policy, required, length, min, max, count, age, days, ttl, used, expiry, expires, type). This is the rule that separates `password_policy_enabled`: a key that ends in a word describing a setting ABOUT a credential is not a credential.
Every key main accepts and that does not end in a setting word is still accepted (superset; measured on the prototype: 193,535 random keys built from the rule's words and separators, 0 exceptions; table test T1 lists both sides). Negatives that stay readable: `author`, `tokens_used`, `max_tokens`, `password_policy_enabled`, `token_expiry`, `cache_key`, `compass`. Known cost, stated in the docstring: an env entry named `PWD` (a working directory) is masked. The four word lists are module constants in this one file.
Env-entry shapes (M2): a dict that has a key whose lower-case form is `name` or `key` AND a key whose lower-case form is `value` (`name/value`, `Name/Value`, `key/value`), and whose name is a credential key: its value, WHATEVER its type, goes through `_walk(value, f, str(name), True, known_secret)`. So a number gets the fixed mask and a list is walked item by item (rows 12-15). Lines 136-137 and 141-142 are replaced by this.
1g. Docstrings and `LIMITS` say exactly the "Limits" list below; `SCHEME` is unchanged.

## Limits of "masked where it is repeated" (D-011 option A; written the same in `LIMITS`, the `_pair` docstring and the CHANGELOG)
A value under a credential key, or an entry of a Secret, is ALWAYS masked under its own key. It is ALSO masked where the same text is repeated elsewhere in the case only when: it is a string directly under that key (or an item of a list there); it has at most 255 characters; it does not hold both `"` and `'`; no part of it is matched by another pattern (an e-mail address, a host, a key); and the copy is spelled the same or in a spelling the redactor already decodes (JSON escape and percent copies measured masked, rows 39-40). NOT masked where repeated, one STRICT xfail test each (`pytest.mark.xfail(strict=True, reason="Q8c: sweep of registered secrets before the patterns")`): X1 composite value (row 26); X2 over 255 characters (row 27); X3 both quote marks (row 28); X4 a string nested under a credential key (row 29); X5 a number (row 30); X6 a respelled copy: the base64 text of a `stringData` value, and a copy wrapped over two lines (row 38). Follow-up Q8c "sweep of registered secrets before the patterns, and a public way to register one" is a change in the redactor, AFTER PR77 merges; the lead holds the ledger row and sets the date. No second sweep engine is built in k1b.

## Behaviour 2: `approvals/gate.py`, `approvals/channel.py`, `approvals/slack_channel.py`, `guard/producers.py`
- `gate.py`: `sanitise_text(text, *, defang=True)` (line 312; keyword-only) passes `defang` to `_all_prose` (308; calls at 327, 350), `_clean_prose` (267; calls at 328, 344) and `_clean_line` (241; calls at 272, 332, 339). Split `_defang_outside_code` (229-238) into `_outside_code(line, fn)` (the inline-code walk) and two rewrites: `_fold_dots` (line 177 `_WIDE_DOTS` to `.`) and `_bracket_dots`. `_clean_line` line 264: `defang=True` as today (fold, then bracket); `defang=False` folds only. "Fold" in this ticket means only: the three wide dots of `_WIDE_DOTS` are written as `.` outside inline code (design m1).
- `gate.py`, new public `defang_domains(text: str) -> str`: split at `\n`; for each line that is not the body of a closed backtick fence of THIS text (`_closed_fences`), apply `_outside_code(line, lambda p: _bracket_dots(_fold_dots(p)))`. `_bracket_dots` = today's two substitutions (`_DOMAIN`, `_NON_ASCII_HOST`) and then `_AFTER_PLACEHOLDER = re.compile(r"(<[A-Z][A-Z0-9]*_[0-9]+>)((?:\.[\w-]+)+)")`, replaced by group 1 + group 2 with every `.` written `[.]`. The placeholder shape is spelled out as at line 142 (`gate.py` imports nothing new). Measured: `<UUID_1>.json` is bracketed, as `report.json` already is on main (rows 59-60); no change of rule. Idempotent (test G5).
- `channel.py`: `_neutralise` (47-48) = `withhold_commands(sanitise_text(text, defang=False))`. New `redact_for_people(text: str, mapping: dict[str, str]) -> str` = `defang_domains(runmap.redact_text(text, mapping, neutralise=_neutralise))`. New `clean`, in steps:
  1. `text = text.replace("\x00", "")`. 2. `mapping = _seeded(text)`. 3. `out = redact_for_people(text, mapping)`. 4. `joined = _TAGS.sub("", text)`; if `joined == text` return `out`. 5. `joined_map = runmap.RunMap({**_seeded(joined), **mapping})` (the tag-stripped pass STARTS from everything the first pass found; this is the N9 rule, design m4). 6. `alt = redact_for_people(joined, joined_map)`. 7. return `alt` if `_assignment_originals(joined_map) - _assignment_originals(mapping)` else `out`.
  The docstring sentence "Nothing transforms the text after its final redaction" becomes "After the final redaction only brackets are added to domains and wide dots are written as dots; nothing is removed or joined".
- `slack_channel.py`: line 19 becomes `from hadavin_sdk.approvals.channel import clean, redact_for_people` (same import style as today); line 81 `shown = redact_for_people(withheld, seeded)`.
- `guard/producers.py`: row at line 38 names `frozenset({"redact_for_people"})`; `CHOKE_FAMILY` (44-51) gains `"redact_for_people": "approvals/channel.py"`. Two data rows; the registry then holds the same number of producer rows as before and one more choke-family entry.
- VISIBLE CHANGE for the approver, stated (design M7, D-011: masking stays, least privilege; the owner question is logged by the lead): a target system or an input shaped like a host name or an e-mail address is shown as a placeholder on the card; the person approves a target they cannot read there. Numbers are local to one card (`<HOSTNAME_1>` on two cards can be two hosts). An IPv4-shaped target is already a placeholder on main (row 64). Pinned by G8. Summaries stored before the upgrade keep their old text.

## Measured table (author, 2026-11-11; "main" = origin/main source; "prototype" = a throwaway private copy with Behaviours 1 and 2, `/home/user/build/q8b-author/protoQ8b/`; scripts `r2_f5.py`, `r2_f6.py`, `r2_xf.py`, `r2_m7.py`; P = `correct horse battery staple`; PW = the long key word; ONE = a 16-character made-up one-word value)
| # | input (review id) | main | prototype |
|---|---|---|---|
| 1 | `{PG+PW upper: P}` (design M1) | unchanged, readable | `<SECRET_1>` |
| 2 | `{name: PG+PW upper, value: ONE}` (M1) | unchanged | value `<SECRET_1>` |
| 3 | `{pwd: ONE}` (M1) | unchanged | `<SECRET_1>` |
| 4-8 | `DBPassword`, `secretkey`, `secrets`, `root`+PW, `accessKey`, each with P (M1) | all unchanged | all `<SECRET_1>` |
| 9 | `{author: 'Priya Nair'}` (1f negative) | unchanged | unchanged |
| 10 | `{tokens_used: 1234}` (1f negative) | unchanged | unchanged |
| 11 | `{PW_policy_enabled: 'true'}` (1f negative) | fixed mask | `'true'` readable |
| 12 | `{name: DB_PW, value: 12345678}` (M2) | number readable | fixed mask |
| 13 | `{name: DB_PW, value: [P, 42]}` (M2) | both readable | `['<SECRET_1>', fixed mask]` |
| 14 | `{Name: DB_PW, Value: P}` (M2) | readable | `<SECRET_1>` |
| 15 | `{key: 'api_key', value: P}` (M2) | readable | `<SECRET_1>` |
| 16 | `{authorization: P}` (readiness B1) | fixed mask | `<SECRET_1>` |
| 17 | `{private_key: P}` (B1) | `<SECRET_1> horse battery staple` | `<SECRET_1>` |
| 18 | `{privateKey: P}` (B1) | `<SECRET_1> horse battery staple` | `<SECRET_1>` |
| 19 | `{bearer: P}` (B1) | fixed mask | `<SECRET_1>` |
| 20 | `{passphrase: P}` (B1) | fixed mask | `<SECRET_1>` |
| 21 | `{PW_for_the_primary_database_replica: P}` and the same with ONE (B1 long suffix) | fixed mask (both) | `<SECRET_1>` (both) |
| 22 | `{PW: 300-character multi-word text}` (B1) | first word of each group masked, the rest readable | fixed mask |
| 23 | `{PW: 255-character multi-word text}` / 256 characters | readable but the first word | `<SECRET_1>` / fixed mask |
| 24 | `{PW: 'hunter' ESC '[0m2secretXYZ'}` (design M6) | `<SECRET_1> 2secretXYZ` | `<SECRET_1>` |
| 25 | row 24 plus log `the hunter came` (M6 planted fragment) | log: `the <SECRET_1> came` | log unchanged |
| 26 | `[{token: 'bob.smith@example.com Zx9 tail'}, log 'login with bob.smith@example.com Zx9 tail failed']` (design B1) | key `<EMAIL_1> Zx9 tail`; log `<EMAIL_1> Zx9 tail` | key `<SECRET_1>`; log `<EMAIL_1> Zx9 tail` (X1, still readable) |
| 27 | row 22 plus the same text in a log line (M4) | readable in both | key fixed mask; log readable (X2) |
| 28 | `{PW: 'pa55"word \'tail\' part'}` plus the same in a log line (M4) | readable but `pa55` in both | key fixed mask; log readable (X3) |
| 29 | `[{credentials: {note: P}}, log 'saw P']` (M4) | key fixed mask; log readable | same (X4) |
| 30 | `[{pin_token: 12345678}, log 'pin 12345678 used']` (M4) | key fixed mask; log readable | same (X5) |
| 31 | `{PW: P}` (F5) | `<SECRET_1> horse battery staple` | `<SECRET_1>` |
| 32 | `{PW: 'a b'}` (F5) | `p<SECRET_1>ssword=<SECRET_1> b` | `<SECRET_1>` |
| 33 | `{db_PW: 'pa55"word \'tail\' part'}` (F5) | `<SECRET_1>"word 'tail' part` | fixed mask |
| 34 | `[Secret stringData {cfg: P}, log 'login with P failed']` (F5b) | key fixed mask; log readable | `<SECRET_1>`; log `login with <SECRET_1> failed` |
| 35 | `[Secret data {p: base64(P)}, log 'login with P failed']` (F5b) | key fixed mask; log readable | masked in both |
| 36 | `[{PW: P}, log 'login with P failed; correct answer']` (F5b, N3) | log `<SECRET_1> horse battery staple failed; <SECRET_1> answer` | log `login with <SECRET_1> failed; correct answer` |
| 37 | `[Secret data {DB_NAME: base64('orders')}, log 'orders-api timeout']` (design M5) | key fixed mask; log unchanged | key `<SECRET_1>`; log `<SECRET_2>-api timeout` |
| 38 | Secret `stringData {cfg: P}` and elsewhere: base64(P); P in capitals; P wrapped over two lines; P with a double space; hex (M4 respelled) | all readable | all readable (X6) |
| 39 | Secret `stringData {cfg: 'line1 horse\nline2 staple'}` and its JSON-escaped copy in a `last-applied-configuration` annotation (M4) | copy readable | copy masked |
| 40 | Secret `stringData {cfg: P}` and `GET /login?p=correct%20horse%20battery%20staple` | readable | `p=<SECRET_1>` |
| 41 | `{token: '2026-11-11T10:00:00Z'}` (1d) | unchanged | unchanged |
| 42-45 | near misses under `token`: `+00:00` offset; a space for `T`; trailing `x`; month 13 | masked; `<SECRET_1> 10:00:00Z` (time readable); masked; masked | all four `<SECRET_1>` |
| 46 | `[Secret stringData {username: 'orders-svc'}, log 'user orders-svc NAME denied']` (design M3) | `<NAME_1>` in both | `<SECRET_1>` in both; the word `NAME` untouched in both |
| 47 | `clean('contact bob.smith@example.com')` (F6) | `contact bob.smith@example[.]com` | `contact <EMAIL_1>` |
| 48 | `clean('restart db01.corp.internal now')` | `restart db01[.]corp[.]internal now` | `restart <HOSTNAME_1> now` |
| 49 | `clean('bob%2Esmith%40example%2Ecom')` (readiness M2) | returned as written; after `runmap.undo` it reads `bob.smith@example.com` | `<EMAIL_1>` |
| 50 | `clean('bob.smith&#64;example.com')` (M2) | `bob[.]smith&amp;#64;example[.]com` | `<EMAIL_1>` |
| 51 | `clean('bob@exa<b></b>mple.com')` | `bob@example[.]com` | `<EMAIL_1>` |
| 52 | wide dot `bob.smith@example。com` | `bob.smith@example[.]com` | `<EMAIL_1>` |
| 53 | zero-width space inside the address | `bob.smith@example[.]com` | `<EMAIL_1>` |
| 54 | address inside a `~~~` fence | `bob.smith@example[.]com` | `<EMAIL_1>` |
| 55 | `from <bob.smith@example.com> today` | `from ‹bob[.]smith@example[.]com> today` | `from ‹<EMAIL_1>> today` |
| 56 | address inside a closed backtick fence (guard) | `<EMAIL_1>` | `<EMAIL_1>` |
| 57 | `clean('10.0.0.5.evil.com')` (readiness M2) | `10[.]0[.]0[.]5[.]evil[.]com` (the address readable) | `<IPV4_1>[.]evil[.]com` |
| 58 | `clean(PW + '=ab`cd evil.com `evil.com` x')` (F6b) | `...=<SECRET_1> evil.com `evil[.]com` x` (bare domain) | `...=<SECRET_1> evil[.]com `evil.com` x` |
| 59 | `see <a UUID>.json` (design m3) | `see <UUID_1>[.]json` | same |
| 60 | `see report.json`; `` `evil.com` and evil.com `` (guards) | `report[.]json`; inline code kept, outside bracketed | same |
| 61 | probe, 4,000 random card texts, seed 8 | 2,619 with a readable identifier, 0 bare domains | 0 and 0 (6.6 s) |
| 62 | N9, 3,000 random tagged texts, seed 9: texts where an original of the first pass's map is readable in the returned text | 1 (the text `password=` itself was registered as a secret and is readable in the returned candidate) | 0 |
| 63 | `summary()` with `target.system='db01.corp.internal'` (design M7) | `... on db01[.]corp[.]internal. Inputs: ...` | `... on <HOSTNAME_1>. Inputs: ...` |
| 64 | `summary()` with `target.system='10.20.30.40'` | `... on <IPV4_1>.` | same |
| 65 | `summary()` with inputs `{host: 'db01.corp.internal', owner: 'bob.smith@example.com'}` | both readable, bracketed | `{"host":"<HOSTNAME_1>","owner":"<EMAIL_1>"}` |
Existing tests, one full run each (single process, no Postgres; logs `full_main.log`, `full_proto_r2.log`): main `10193 passed, 455 skipped`, exit 0. Prototype of this revision (with the two `producers.py` rows): `2 failed, 10192 passed, 455 skipped in 508.89s`; the 2 are `tests/test_ci_gitleaks_scope.py::test_the_gitleaks_config_has_only_narrow_path_allowlists` and `tests/test_repo_rules.py::test_licences_are_proprietary`, both `git ls-files` exit 128 because the private copy is not a git checkout (not a result). No existing test about keys, cards or k1b replay and score fails.

## Sibling search (unchanged from rev 1, short form; whole `src/` and `demos/`)
Same class, fixed here: `k1b/redaction.py:114`; `approvals/channel.py:29,36`; `approvals/slack_channel.py:74-81`; `approvals/channel.py:37` (now rule 5 above, measured row 62). Same class, forbidden file, for PR77's builder: `guard/runmap.py:517` (a view wins when it holds more placeholders, sweep F3); `tools.py:957-1005` (F2); `guard/redact.py:825-838` (F3). Checked, not this class: `guard/runmap.py:340-350`, `runtime/evidence.py:154,191`, `runtime/agent_loop.py:367,489`, `evals.py:63`, `guard/judge.py:71`, `guard/bedrock_guardrail.py:98`, `extract.py:58`, `guard/injection.py:96`, `k1b/loop.py:187,194`, `runtime/tick.py:292`, `actions/authorizer.py:39`. `demos/ask-your-data` has a different function also named `clean` (no redaction promised; not otherwise checked). Redactor gaps found on the way, for PR77's builder: `bob.smith@example。com` and the U+FF61 form are not masked by `redact_text` alone (shown inside a closed backtick fence on a card also after this ticket); `bob@é.example.com` is not masked; free text `password=<address>:Zx9 tail` leaves ` tail`.

## Existing tests that change
- `tests/test_k5_producers.py::test_each_producer_calls_its_redaction_function[approval card text]` fails until the two `producers.py` rows are in (measured in rev 1). The test file is not loosened. Its `REDACTORS` set (line 147) gains `"redact_for_people"` for consistency; the prototype's full run passed without that edit.
- `tests/test_k5_round11.py::test_only_clean_and_the_slack_block_call_the_card_sanitisers` (136): keep the first loop; add a SECOND loop over the same files: a call whose name is `defang_domains` is allowed only in `approvals/gate.py` and `approvals/channel.py`; a call of `redact_for_people` only in `approvals/channel.py` and `approvals/slack_channel.py`. `test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook` (113) stays unchanged and green.
- Any existing test that asserts a key is or is not a credential key, or the fixed mask for `password_policy`-like keys: none found by the author's runs; if one fails, stop and report, do not edit it silently.

## New tests (three files; made-up data; `PW_KEY = "pass" + "word"` and every value under it built from parts, no allowlist line added to `tools/scan_allowlist.txt`; each assertion carries the MESSAGE the mutant table quotes)
`tests/test_q8b_credential_keys.py`
- S1-S5, direct tests of `_pair` with a STUB in place of the redactor (readiness M1; these, not the end-to-end tests, kill mutants M1-M3): S1 stub returns `k=<SECRET_1> rest of value` -> fixed mask (message "a partly masked value was accepted"); S2 stub returns `k=<SECRET_1>x` and, for a quoted attempt, `k="<SECRET_1>" tail` -> fixed mask ("text after the placeholder was accepted"); S3 stub returns `<SECRET_1>` with no key in front -> fixed mask ("a result without its key was accepted"); S4 stub returns `k=<secret_1>` -> fixed mask ("a look-alike placeholder was accepted"); S5 a recording stub: for a value with a space no call text starts with the real key and `=`, every call text is `secret="..."` or `secret='...'`; for a 256-character value there is exactly one call, the final `f(value)` ("a value that is not plain was written under its real key" / "an over-long spelling was tried").
- T1 table test of `sensitive()`: every key of rows 1-8 and 16-21, the keys main accepts today (`password`, `api_key`, `api-key`, `apikey`, `clientSecret`, `accessToken`, `dbPassword`, `credentials`, `token`, `pass`, `SECRET_KEY_BASE`, `password_hash`) -> True; `author`, `tokens_used`, `max_tokens`, `password_policy_enabled`, `token_expiry`, `secret_count`, `cache_key`, `object_key`, `key`, `message`, `compass`, `bypass` -> False ("the key rule changed").
- N1 (through `redact_bundle`), rows 1-8, 12-25, 31-33. Assertion: the words `horse`, `battery`, `staple` (and for other values every run of 4 or more characters between break characters) are absent from the shown bundle, AND the shown value fully matches placeholders or equals the fixed mask ("part of the value is readable"). N2 rows 34-35, N3 row 36 (`correct answer` still readable: "a fragment was registered"), row 25. X1-X6 strict xfail, rows 26-30, 38.
- Regression guards: G1 one-word value -> one placeholder; G2 `message` unchanged; G3 timestamp row 41 unchanged and rows 42-45 masked (the space case must not show `10:00:00Z`: FAILS on main); G4 `{credentials: {user: 'svc'}}` fixed mask and an empty map; G7 row 37 pinned as written (1e); G6 rows 9-11.
`tests/test_q8b_card_text.py`
- N4 rows 47-55 through `clean`. Assertion (readiness M2, so each fails on main): `flat = runmap.undo(result).replace("[.]", ".")`; neither `bob.smith@example.com`, `bob@example.com`, `smith`, nor `db01.corp.internal` is in `flat` ("an identifier is readable on the card"). N5 the same inputs through `summary()`, `cards.render_shadow` (diagnosis), `FakeChannel.send` / `notify`, and the Slack blocks with the existing fake transport. N6 row 57: `10.0.0.5` is not in `flat` AND no bare `evil.com` (fails on main on the first part); row 58: the text outside inline code holds no `evil.com` without brackets ("a bare domain is outside code"). N7 one combined card: a secret assignment whose value holds an address, an internal host, tab runs, a fenced block with an address, a link.
- N8 AST guard (in this file; listed as a NEW-CODE guard, it cannot fail on main because the functions do not exist there): inside `approvals/`, `redact_text` with `neutralise=_neutralise` is called only inside `redact_for_people`; `sanitise_text` with `defang=False` only inside `_neutralise`.
- Guards: G5 `defang_domains` idempotent and `clean(clean(x)) == clean(x)` for rows 47-60; rows 56, 59, 60; a bare `evil.com` in the body of a closed backtick fence stays without brackets ("a fence body was changed", kills M15); G8 rows 63-65 pinned (M7); a placeholder already in the text survives.
`tests/test_q8b_random.py` (seeded `random.Random`, no clock in an assertion)
- P1, seed 20261111, 3,000 cases. Alphabet for made-up values: words drawn from the letters `qxzjkwvy` (4 to 9 letters, so a fragment check cannot hit an ordinary word of the fixture), digits, every character for which `str.isspace()` is true below U+3000, the five break characters, ESC, and with probability 0.2 a made-up address or host. Keys: random picks from T1's True list; one case in four inside a Secret under a non-credential key. `ENDS` = the `str.isspace()` characters plus `; & , " '`. Properties: (a) the shown value fully matches placeholders or is the fixed mask; (b) no run of 4 or more characters of the value between `ENDS` is in the shown value; (c) when the value has at most 255 characters, not both quote marks and no address or host, no such run is readable in a second record that repeats the value.
- P2, seed 8, 4,000 cases: the author's probe as a test. (a) every identifier `runmap.redact_text` masks when it reads the text alone is not readable as a standalone word in `clean(text)` after `[.]` is written back as `.`; (b) link oracle that does NOT reuse `gate._DOMAIN` (design m2): with each placeholder read as `x`, the test's own pattern `(?<![\w.\[/-])[\w-]+(?:\.[\w-]+)*\.[a-z]{2,24}(?![\w@-])` finds nothing outside code; (c) idempotent.
- N9, seed 9, 3,000 tagged texts (generator of `r2_f6.py`): every original in the first pass's map (seed entries and entries under 4 characters left out) is not readable as a standalone word in `clean(text)`. Measured: main 1 failing text, prototype 0. It belongs to the must-fail list.
- Run time measured on the prototype: P2 6.6 s; P1 and N9 not timed separately (N9 ran inside a 280 s limit with the other card measurements). The builder reports the three times and keeps each under 60 s on CI by lowering only the case count, never the alphabet.
Must FAIL on the merge base (paste the failing line of each, then the pass): S1-S5 (S5 on main: the value is written under its real key), T1, N1, N2, N3, N4, N5, N6, N7, G3 space case, N9, P1, P2. Guards (pass on main): G1, G2, G4, G5 (clean part), G8 row 64, rows 56, 59, 60. New-code guards: N8, G5 (`defang_domains`), G7.

## Mutants: `tests/q8b_mutants.py` (shape of `tests/stage_mutants.py`; `Mutant(name, file, old, new, expect, test_file=..., only_test=..., pinned=test_file[:-3] + "::" + only_test)`; `expect` = the assertion message fragment)
| name | file | old -> new | test_file | only_test | expect |
|---|---|---|---|---|---|
| M1 changed counts as masked | `k1b/redaction.py` | `_ONLY_PLACEHOLDERS.fullmatch(part)` -> `part != text` | `test_q8b_credential_keys.py` | `test_s1_a_partly_masked_result_is_refused` | `a partly masked value was accepted` |
| M2 prefix match | same | `.fullmatch(part)` -> `.match(part)` | same | `test_s2_text_after_the_placeholder_is_refused` | `text after the placeholder was accepted` |
| M3 result without key accepted | same | the `continue` after `if not masked.startswith(k + "=")` -> `part = masked` path | same | `test_s3_a_result_without_its_key_is_refused` | `a result without its key was accepted` |
| M4 not-plain written under the real key | same | the non-plain branch returns `[(key, quote)]` | same | `test_s5_what_is_written_to_the_redactor` | `written under its real key` |
| M5 plain is a denylist | same | `_PLAIN_CHARS` test -> "no space and no break character" | same | `test_n3_no_fragment_is_registered_for_an_esc_value` (row 25; under the key the result is the fixed mask either way) | `a fragment was registered` |
| M6 length cap removed | same | `len(text) > MAX_SPELLING_CHARS` -> `False` | same | `test_s5_what_is_written_to_the_redactor` | `an over-long spelling was tried` |
| M7 Secret flag dropped | same | `True, True)` at the Secret line -> `True, False)` | same | `test_n2_a_secret_entry_is_masked_where_repeated` | `readable in the log line` |
| M8 decoded spelling not registered | same | `and not known_secret` removed from the early return | same | `test_n2_decoded_copy_of_a_base64_entry` | `readable in the log line` |
| M9 setting-word rule removed | same | `or words[-1] in SETTING_WORDS` removed | same | `test_t1_the_key_rule` | `the key rule changed` |
| M10 glued endings removed | same | `or w.endswith(GLUED_ENDINGS)` removed | same | `test_t1_the_key_rule` | `the key rule changed` |
| M11 env value only when a string | same | the env branch guarded by `isinstance(v, str)` again | same | `test_n1_a_number_in_a_named_entry` | `part of the value is readable` |
| M12 hook brackets again | `approvals/channel.py` | `defang=False` -> `defang=True` | `test_q8b_card_text.py` | `test_n4_an_address_outside_code` | `an identifier is readable on the card` |
| M13 last step removed | same | `defang_domains(` wrapper removed (inner call kept) | same | `test_guard_a_domain_outside_code_is_bracketed` | `a bare domain is outside code` |
| M14 after-placeholder rule removed | `approvals/gate.py` | the `_AFTER_PLACEHOLDER.sub` line -> `return part` | same | `test_n6_a_domain_after_a_placeholder` | `a bare domain is outside code` |
| M15 brackets inside a closed fence | same | `if i in code` -> `if False` | same | `test_guard_code_stays_code` | `a fence body was changed` |
| M16 joined pass starts empty | `approvals/channel.py` | step 5 -> `joined_map = _seeded(joined)` | `test_q8b_random.py` | `test_n9_the_tag_stripped_candidate_hides_what_the_first_pass_found` | `readable in the returned text` |
| M17 Slack path keeps the name but skips the last step | `approvals/slack_channel.py` | `redact_for_people(withheld, seeded)` -> `runmap.redact_text(withheld, seeded, neutralise=channel_neutralise)` with the import line changed in the same mutant so nothing is undefined | `test_q8b_card_text.py` | `test_n8_only_one_function_feeds_a_card` | `a card path skips redact_for_people` |
`run_mutants(ROOT, M, [the three test files], extra_dirs=("tests", "tools", "demos", "docs"))`. Exit 1 if any mutant is not killed by its pinned test.
CI: in `.github/workflows/ci.yml`, job `check`, directly after the step at line 93-94, add `- name: Q8b masking mutants (each reverted guard must be killed by its named test) (blocks)` with `run: python tests/q8b_mutants.py`.

## CHANGELOG ("## Unreleased"; the file's existing headings are "### Upgrade steps", "### Added", "### Changed")
Under "### Upgrade steps":
- **Approval cards mask identifiers outside code.** An e-mail address, a host name or another identifier outside code was shown with brackets in its dots (`bob.smith@example[.]com`); it is now a placeholder (`<EMAIL_1>`). A target system or an input that is shaped like a host name is shown as `<HOSTNAME_n>`: the approver cannot read it on the card. Placeholder numbers are local to one card. Summaries stored before the upgrade keep their old text. What to do: name targets by a label that is not a host name (`orders-db`), or open the request in the console to see the target.
- **Incident cases: more keys count as credential keys, one fewer.** Keys such as `PGPASSWORD`, `pwd`, `secretkey`, `secrets`, `accessKey`, `DBPassword` and env entries written `Name`/`Value` or `key`/`value` are now masked, also when the value is a number or a list. A key whose last word describes a setting (`password_policy_enabled`, `token_expiry`) is no longer treated as a credential. An env entry named `PWD` is masked.
- **Incident cases: every entry of a Kubernetes Secret is registered as a secret.** Its text (as written and base64-decoded) is replaced wherever it appears in the case, also inside a longer word: a database name stored in a Secret disappears from log lines the model reads.
Under "### Changed":
- **Fixed: a value under a credential key was shown partly masked** when it held a space, a tab, a line break, an escape character, `;`, `,`, `&` or a quote mark (`<SECRET_1> horse battery staple`). It is now shown only as placeholders, or as `<SECRET_REDACTED>`.
- **Masked where repeated, with limits.** The same value is also masked in other records of the case when it has at most 255 characters, does not hold both quote marks, and no part of it is an address, host or key that another pattern masks. NOT masked where repeated: composite values, longer values, values with both quote marks, strings nested under a credential key, numbers, and copies in another spelling (base64 of a plain value, line-wrapped). Follow-up Q8c.
- **Fixed: a domain that ends up outside code after masking is bracketed.** Honest limit, same entry: masking is pattern based; what no pattern knows is still shown.

## Gates
`uv run --all-extras --group test ruff check`, `ruff format --check`, full `pytest` WITH `HADAVIN_TEST_PG_DSN` on the Postgres version CI pins (17.10; non-skipped output pasted), `bandit -ll`, the repo guard tests, `python tests/q8b_mutants.py`, `python tests/stage_mutants.py`, the CI redaction-performance step unchanged. Gate on pytest's own exit code. Then a separate EVIDENCE RUNNER (raw output; the fail-on-base proofs; the measured table re-run on the merge base) and egm:* result reviewers on a snapshot; rounds uncapped; ledger rows; drift report before "done".

## Could not establish (author)
- Replay scores before and after (D-011 ruling 5): NOT run. Exactly why: the repository holds no recorded incident set with recorded model replies; the k1b tests build made-up bundles (`tests/k1b_support.py:71`, no Secret in them) and answer with a scripted model whose replies do not depend on the masked text, so its score cannot move; a real before/after needs a live model run on a client's or a made-up incident set, which needs the owner's yes with numbers. Next step for the lead: when such a set exists, run `k1b` replay with redaction on at the merge base and at the branch head, same model and seed, and compare the score report. What was run instead: the existing k1b tests (replay and score included) on the prototype, in the full-run line.
- Standards numbers (CWE-212, CWE-636, CWE-696) and the Kubernetes "data is base64" sentence: from memory, both sites blocked in this session.
- The full text of the two reviews: the files on disk are summaries (5 and 17 lines). Where a review says "three cases given", "sharper assertions given" or "steps 1-7 provided" without the text, S1-S5, the N4/N6 assertions and the seven steps above are the author's own wording of them.
- Whether PR77 changes any measured row: the table is from today's main only.
- Not run by the author: the Postgres-backed tests, ruff, bandit, any mutant. P1 as specified (only its inputs by hand, rows 1-46); N5 through the Slack blocks.

## Not in scope
Any edit of the three forbidden files; sweep findings F1-F4, F7-F10; `guard/runmap.py:517`; a general sweep of registered secrets (Q8c); new masking patterns or placeholder kinds; what `sanitise_text` removes; `withhold_commands`; the demo's own `clean`; names in free text and whatever `LIMITS` already says the redactor does not catch.

## Resolution of plan review round 1
| id | finding | where resolved |
|---|---|---|
| readiness B1 | quoted spelling fails for authorization, private_key, bearer, passphrase; 256 cap | 1b; rows 16-23; S5; M4, M6 |
| readiness M1 | mutants M1-M3 not killed by end-to-end tests | S1-S5; mutant table M1-M3 |
| readiness M2 | N4, N6, N2 could pass on main | N4/N6/N1 assertions (`flat`, words absent); rows 49, 50, 57 |
| readiness M3 | `_walk` parameter | 1c |
| readiness M4 | `defang_domains` pattern, import, keyword-only | Behaviour 2, first two bullets |
| readiness M5 | N9 list and rule | clean step 5; row 62; N9 in the must-fail list; M16 |
| readiness M6 | mutant list does not fit the runner; test files | mutant table (expect, pinned, test_file; M17 changes the import in the same mutant); three files named |
| readiness M7 | P1/P2 under-specified | `test_q8b_random.py` section |
| readiness M8 | round11 edit does not restrict `defang_domains` | "Existing tests that change", second loop |
| readiness M9 | open decisions into the ticket body | rulings of D-011 written into 1b, 1d, Limits, Behaviour 2; no open decision left in the ticket |
| design B1 | F5b cannot be closed for composite values | "Limits" (option A); X1-X6 strict xfail; row 26 |
| design M1 | key rule too narrow, two grammars drifted | 1f; T1; rows 1-11; M9, M10 |
| design M2 | env form and non-string values skip `_pair` | 1f env shapes; rows 12-15; M11 |
| design M3 | fallback key on the wrong set and order | 1b; rows 16-21, 46 |
| design M4 | "left open" understated | "Limits"; rows 26-30, 38; X1-X6 |
| design M5 | every Secret entry swept as a substring | 1e; row 37; G7; CHANGELOG. Replay scores NOT resolved: not measurable here, reason and next step in "Could not establish" |
| design M6 | "plain" was a denylist | 1b allowlist; rows 24-25; M5; private-name test dropped |
| design M7 | approver sees a placeholder for a host-shaped target | Behaviour 2 last bullet; rows 63-65; G8; CHANGELOG upgrade step; owner question with the lead |
| minors | m1 wording, m2 oracle, m3 UUID file, m4 N9 rule, m6 stored summaries, m7 call bound, m8 flag through lists, m9 rows count; readiness minors (N8 list, PW_KEY, CI step, headings, import style, REDACTORS, Postgres version, steps 1-7) | Behaviour 2; P2(b); rows 59-60; step 5; M7 bullet; 1a; 1c; producers bullet; N8; tests header; Mutants; CHANGELOG; slack bullet; Existing tests; Gates; clean steps. Design m5 ("heading guard") NOT resolved: the summary on disk does not say what it asks |
