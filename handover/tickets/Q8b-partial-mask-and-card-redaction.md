# Ticket Q8b (rev 1, draft for plan review): two masking leaks, a half-masked value under a credential key and card text that hides an e-mail address from the redactor
Source: reviews/Q8/redaction-sweep.md findings F5 and F6 (both "NOT reproduced by lead yet" there; both REPRODUCED by the ticket author on 2026-11-11, outputs below). Branch: NEW `core/q8b-partial-mask-and-card-redaction` from origin/main; draft PR against main. Redaction path: result-review rounds uncapped. Nothing is built yet; fresh egm:* reviewers judge this ticket first.

Words used here. The *redactor* is the pattern-based masking code (`guard/redact.py`, reached through `guard.runmap.redact_text`). A *placeholder* is what it writes in place of a value, for example `<EMAIL_1>`. The *whole-value mask* is the fixed text `<SECRET_REDACTED>`. A *credential key* is a key whose name says its value is a password or token (`password`, `api_key`, `clientSecret`, ...). A *card* is the text a person reads in a chat channel before approving an action. *Bracketing a domain* means writing `evil[.]com` so a chat program does not turn it into a link.

HARD LIMIT OF THIS TICKET: it must NOT edit `src/hadavin_sdk/guard/redact.py`, `src/hadavin_sdk/guard/runmap.py` or `src/hadavin_sdk/tools.py` (another builder is changing them for F1-F4 and F7 on the redaction pull request). It only CALLS them. Files it may edit: `k1b/redaction.py`, `approvals/channel.py`, `approvals/gate.py`, `approvals/slack_channel.py`, `guard/producers.py` (one registry row), tests, `CHANGELOG.md`, one new mutant list, one CI step.
MERGE RISK for the lead to decide: sweep finding F4 names `approvals/gate.py:336-338`. This ticket edits `gate.py` lines 229-351. If the F1-F4 builder also edits `gate.py`, the two pull requests conflict; merge one first and rebase the other.

## Reproduction (author, 2026-11-11 UTC; real functions; source tree `/home/user/build/EV-P89-db0d9eb`, whose five files `k1b/redaction.py`, `approvals/channel.py`, `approvals/gate.py`, `guard/runmap.py`, `guard/redact.py` were compared byte for byte with `origin/main` and are the same)
Scripts are in `/home/user/build/q8b-author/` (outside the repository). Command for each: `/home/user/build/venv-p89/bin/python <script>`.

F5, `repro_f5.py` and `repro_f5_passwd.py` (they call `k1b.redaction._walk`, which calls `_pair`, twice with one map, as `redact_bundle` does), output lines copied. Three lines use the key `passwd` because the repository's own secret scan (`tools/scan_repo.py`, rule credential-literal) refuses the longer key word followed by a quoted text of 8 or more characters; the builder's tests build such keys and values from parts for the same reason:
```
{'password': 'correct horse battery staple'}            -> {'password': '<SECRET_1> horse battery staple'}
{'passwd': 'correct\thorse\t\tbattery\tstaple'}         -> {'passwd': '<SECRET_1>\thorse\t\tbattery\tstaple'}
{'passwd': 'ab12;cd34,ef56&gh78'}                       -> {'passwd': '<SECRET_1>;cd34,ef56&gh78'}
{'db_password': 'pa55"word tail-part'}                  -> {'db_password': '<SECRET_1>"word tail-part'}
{'secret': 'line1secret\nline2secret'}                  -> {'secret': '<SECRET_1>\nline2secret'}
{'name': 'DB_PASSWORD', 'value': 'correct horse battery staple'} -> {..., 'value': '<SECRET_1> horse battery staple'}
{'api_key': 'db01.corp.internal/Zx9 tailpart'}          -> {'api_key': '<SECRET_1> tailpart'}
{'secret': 'AKIAIOSFODNN7EXAMPLE and the rest'}         -> {'secret': '<APIKEY_1> and the rest'}
{'password': ['correct horse', 'x']}                    -> {'password': ['<SECRET_1> horse', '<SECRET_2>']}
{'password': 'a b'}                                     -> {'password': 'p<SECRET_1>ssword=<SECRET_1> b'}
controls (correct today): {'passwd': 'hunter2secretXYZ'} -> '<SECRET_1>';  {'message': 'correct horse battery staple'} unchanged;
  {'kind': 'Secret', 'stringData': {'cfg': 'correct horse battery staple'}} -> '<SECRET_REDACTED>';  {'token': 'bob.smith@example.com:Zx9-tail-part'} -> '<SECRET_1>'
```
REPRODUCED. The last leaking line shows a second form: the one-letter "secret" `a` was also replaced inside the key, the result no longer starts with `password=`, and `_pair` returned the whole `key=value` text.

F5b, found by the author while reproducing (NOT in the sweep), `probe_f5b.py`: a value that IS masked under its key stays readable where the same value is repeated in another record:
```
[{'kind': 'Secret', 'stringData': {'cfg': 'correct horse battery staple'}}, {'message': 'login with correct horse battery staple failed'}]
 -> [{... 'cfg': '<SECRET_REDACTED>'}, {'message': 'login with correct horse battery staple failed'}]      map: {}
```
REPRODUCED. The whole-value mask never enters the map, so the redactor cannot find the copy.

F6, `repro_f6.py` (`approvals.channel.clean`, next to `runmap.redact_text` alone on the same text):
```
input                                      redact_text alone             clean() on main
'contact bob.smith@example.com'            'contact <EMAIL_1>'           'contact bob.smith@example[.]com'
'restart db01.corp.internal now'           'restart <HOSTNAME_1> now'    'restart db01[.]corp[.]internal now'
'contact\t\tbob.smith@example.com\t\tor\tdb01.corp.internal'  both masked   both kept, bracketed
'see\n~~~\nbob.smith@example.com\n~~~\nend' '<EMAIL_1>' inside the fence  'bob.smith@example[.]com' inside the fence
'from <bob.smith@example.com> today'       'from <<EMAIL_1>> today'      'from ‹bob[.]smith@example[.]com> today'
'Inputs: {"owner":"bob.smith@example.com","host":"db01.corp.internal"}. Expected: restart.'   -> both kept, bracketed
controls (correct today): inside a closed ``` fence and inside `inline code` the address IS masked (no brackets are added there);
  '10.20.30.40' -> '<IPV4_1>';  an ARN -> '<ARN_1>';  'AKIAIOSFODNN7EXAMPLE' -> '<APIKEY_1>';  'password=bob.smith@example.com:Zx9tail' -> 'password=<SECRET_1>'
```
REPRODUCED. A random probe (`probe_f6_prop.py`, 4,000 texts built from 7 made-up identifiers and markup, seed 8): on main 2,619 texts keep a standalone identifier that the redactor masks when it reads the same text alone.

F6b, found by the author (NOT in the sweep), the mirror image on the link side: brackets are decided BEFORE the redaction, so a redaction that removes a backtick leaves a live domain:
```
clean('password=ab`cd evil.com `evil.com` x')  on main -> 'password=<SECRET_1> evil.com `evil[.]com` x'
```
REPRODUCED: the bare `evil.com` is outside code in what the person receives; the bracketed one is inside code.

What is NOT established: whether the standard runtime ever hands `clean()` a real e-mail address or host. `runtime/agent_loop.py:269-284` says a plan holds placeholders and the real values are restored only for the executor, so on that path `clean()` is the second line of defence, not the first. It is the only line for text that was never masked before: a diagnosis text (`cards.render_shadow`), a notice text (`Channel.notify`), a raw value the model typed, or an integrator's own plan.

## Rung table (CODE-LAST)
| component | need | rung tried | evidence (2026-11-11 unless stated) | what only our code gives | verdict |
|---|---|---|---|---|---|
| acceptance rule in `k1b.redaction._pair` | a value under a credential key is shown to the model only when nothing of it is left readable | rung 1 reuse: `runmap.PLACEHOLDER` (the one definition of a genuine placeholder, `guard/runmap.py:31`) and the existing whole-value mask `MASKED` (`k1b/redaction.py:86`) | read in source; prototype in a private copy: 487 k1b tests pass before and after (`k1b_tests_main.log`, `k1b_tests_proto.log`) | redaction before the model is one of the listed safety guarantees; a library that finds secrets (rung "free library": detect-secrets, Presidio; UNVERIFIED, no network to their pages today) would replace the redactor, not this ten-line decision about its result | KEEP-CODE (about 25 changed lines) |
| whole value enters the map (F5b) | a value known to be a secret from its key is masked wherever it is repeated | rung 1 reuse: the redactor's own quoted-assignment grammar. `runmap.redact_untrusted('passwd="correct horse battery staple"', map)` returns `passwd="<SECRET_1>"` with map `{'<SECRET_1>': 'correct horse battery staple'}`; same for single quotes, a newline, `;` `,` `&` inside the quotes (`probe_f5b.py`, `repro_f5_passwd.py`) | run output | nothing new: thin glue (try the quoted spelling) | KEEP-CODE as glue. Alternative for the reviewers: a public `runmap.remember(mapping, original)` would be cleaner but needs a forbidden file; see "Open decisions" |
| order of steps in `approvals.channel.clean` | every identifier the redactor knows is masked on a card, and no bare domain is left | rung 1 reuse: the existing `gate.sanitise_text`, `gate.withhold_commands`, `runmap.redact_text`; only the place where dots are bracketed moves | two prototypes compared on the existing tests and on the probe (table in Behaviour 2) | approval text a person acts on is a listed safety guarantee (approval binding); a ready-made "defang" package (UNVERIFIED) would bracket dots but cannot fix the ORDER, which is the bug | KEEP-CODE (one flag, one function, about 40 lines) |
| one shared entry for card text | the Slack block path (`slack_channel.py:81`) cannot forget the last step | rung 1 reuse: both callers call one new function in `channel.py` | sibling search below | - | KEEP-CODE (moves a call) |
| mutants and seeded random tests | proof that the new tests bite | rung 1 reuse: `tools/mutation_runner.py` with a list file like `tests/stage_mutants.py`; seeded `random.Random` generators as in `tests/test_k5_round12_fuzz.py` (no `hypothesis` in `pyproject.toml`, none added) | read in source | - | reuse, no new tool |

## Bug class for each
- F5, F5b: "CHANGED IS TAKEN FOR MASKED" (fail open on a partial result). `_pair` line 114 accepts the redactor's answer when the text is merely different from the input. Own promise broken: `_pair` docstring, `k1b/redaction.py:105-106`: "a value under a credential key never reaches the model"; module docstring lines 4-6: "a value found in any alert field, log line, k8s record or runbook chunk is masked in all of them". Standard, cited from memory and NOT re-fetched today (cwe.mitre.org is blocked in this session): CWE-212 (improper removal of sensitive information before storage or transfer) and CWE-636 (not failing securely). The builder verifies both titles or removes the numbers.
- F6: "A REWRITE THAT THE DETECTOR CANNOT READ RUNS BEFORE THE DETECTOR". Bracketing `example.com` to `example[.]com` is an output encoding; it ran inside the hook that `redact_text` applies before its patterns. Own promises broken: `approvals/channel.py:1` "Channel text is template-built, redacted and link-free"; `approvals/requests.py:35` "inputs redacted and link-free"; the same class is already named in `runmap.safe_head` (`guard/runmap.py:533-535`): "Redact FIRST ... a cut first splits a secret and the redactor no longer sees a whole one". Standard, from memory, NOT re-fetched: CWE-696 (incorrect behaviour order), and the usual rule that output encoding is the last step before output.
- F6b: the same class seen from the other side: a decision about the FINAL text (which stretches are code, so where a domain may stay unbracketed) is taken on an EARLIER text.

## Behaviour 1 (F5): `k1b/redaction.py`
1a. `_pair` (lines 103-117). New rule: the redactor's result is accepted only when the VALUE PART consists of placeholders and nothing else; in every other case the function returns `MASKED`.
- Value part: if the result starts with `key + "="`, the text after it; otherwise the whole result (so a result whose key was itself rewritten, the `p<SECRET_1>ssword=` case, can only pass if all of it is placeholders). If the function itself wrapped the value in quotes (1b) and the part starts and ends with that quote, the two quotes are removed.
- "Placeholders only": a new module constant `_ONLY_PLACEHOLDERS = re.compile(rf"(?:{runmap.PLACEHOLDER.pattern})+")`, used with `fullmatch`. One or more placeholders, no space, no punctuation, no other character. Do not write a second placeholder pattern.
- Line 114 `if masked != f"{key}={text}":` and line 115 are replaced by this rule. Line 116 `f(value)` and line 117 `return MASKED` stay.
1b. Spellings tried (so the whole value, not its first word, enters the map; this also closes F5b for credential keys). A value is *plain* when it holds no white space and none of `; & , " '`; these are the characters at which the redactor ends an unquoted value. Put them in one module constant `_VALUE_BREAK`; a test asserts it equals `runmap._VALUE_END` minus white space (the test may read the private name; production code may not) so the two cannot drift apart unseen.
- plain value: try `key=value` (as today);
- other value: try `key="value"` if the value holds no `"`, else `key='value'` if it holds no `'`; a value holding both quote marks is not tried and gets `MASKED`. The unquoted spelling is NOT tried for a value that is not plain: on main that attempt is what plants a fragment (`correct`, `ab12`, `a`) in the map, and the redactor then masks that fragment in every other record of the bundle.
- The base64-decoded spelling (line 109) goes through the same two rules. As today, the first accepted spelling is returned.
1c. Kubernetes Secret values (F5b for `kind: Secret`, `_walk` lines 143-144). These values are secrets whatever their key is called (`cfg`, `db`). `_walk` passes a new flag to `_pair` (`known_secret=True`) for the entries of `data` and `stringData`. With the flag: when the key is not a credential key, each spelling is also tried under the fixed key `secret` (module constant `FALLBACK_KEY`), and EVERY spelling is tried even after one was accepted (the base64 text and its decoded text both enter the map; `data` values are base64 by the Kubernetes Secret format, cited from memory, kubernetes.io is blocked today). The first accepted result is returned. The flag is NOT inherited by values merely nested under a credential key (`{"credentials": {"user": "svc"}}` keeps today's result, `MASKED` with no map entry): a user name under `credentials` planted in the map would be masked in every log line and hide the service the case is about.
1d. Kept on purpose, with a regression test and one sentence in the `_pair` docstring: a string that is exactly a UTC timestamp passes unmasked even under a credential key (`_walk` line 128; `{"token_expiry": "2026-11-11T10:00:00Z"}` is evidence, `parse_ts` is a strict full-match grammar). The docstring sentence "never reaches the model" is corrected to name this one exception.
1e. Docstrings: `_pair` and the module `LIMITS` text say in plain words what happens: placeholders only, else the fixed mask; a value with both quote marks is masked under its key but NOT where it is repeated elsewhere (see "Open decisions").
Author's prototype of 1a-1c in a private copy (`/home/user/build/q8b-author/proto/`, not a build, to be thrown away): every leaking input above returns one placeholder or `MASKED`; `[{'kind': 'Secret', 'stringData': {'cfg': P}}, {'message': 'login with P failed'}]` gives `'login with <SECRET_1> failed'`; the 487 existing k1b tests pass.

## Behaviour 2 (F6, F6b): `approvals/gate.py`, `approvals/channel.py`, `approvals/slack_channel.py`
Order after the change: (1) sanitise WITHOUT bracketing dots, then withhold commands (the hook `redact_text` applies to the text and to every decoded view, as today); (2) redact; (3) LAST, bracket the dots of every domain that is outside code in the final text. Step 3 only adds the characters `[` and `]` (and writes a wide dot as `.`), so it cannot join two pieces into a secret.
- `gate.py`: `sanitise_text(text, defang: bool = True)` (line 312) passes the flag to `_all_prose` (308, called at 327 and 350), `_clean_prose` (267, called at 328 and 344) and `_clean_line` (241, called at 272, 332 and 339). `_clean_line` line 264: with `defang=True` unchanged; with `defang=False` it still writes wide dots as `.` outside inline code (line 177 `_WIDE_DOTS`; this makes `bob@example。com` readable to the redactor) but adds no brackets. Split `_defang_outside_code` (229-238) into the "outside inline code" walk and the two rewrites so both modes share it. The default stays `True`: every existing direct test of `sanitise_text` is untouched.
- `gate.py`: new public `defang_domains(text: str) -> str`: for every line that is not the body of a CLOSED backtick fence of THIS text (`_closed_fences`), apply the same rewrite as today's `_defang_outside_code`; plus one new rule: a domain tail directly after a placeholder is bracketed too (`<IPV4_1>.evil.com` becomes `<IPV4_1>[.]evil[.]com`; the existing `_DOMAIN` look-behind at line 112 refuses a start after `.`). The function is idempotent (a test proves `defang_domains(defang_domains(x)) == defang_domains(x)`).
- `channel.py`: `_neutralise` (47-48) calls `sanitise_text(text, defang=False)`. New function `redact_for_people(text, mapping) -> str` = `defang_domains(runmap.redact_text(text, mapping, neutralise=_neutralise))`. `clean` lines 29 and 36 call it. The docstring of `clean` (19-26) is rewritten: the sentence "Nothing transforms the text after its final redaction" becomes "After the final redaction only brackets are added to domains; nothing is removed or joined".
- `slack_channel.py` line 81 calls `channel.redact_for_people(withheld, seeded)`; line 19 imports it instead of `_neutralise`.
- `guard/producers.py:38`: the registry row for "approval card text" names the function `clean` really calls now, only if the registry test asks for it (see "Existing tests").
Why not "redact first, sanitise, redact again" (the order the brief proposed): the author built both in private copies and ran the 39 existing test files that touch approvals, cards or the sanitiser (1,469 pass on main, `appr_tests_main.log`):
| | redact, sanitise, redact (prototype A) | sanitise without brackets, redact, brackets last (prototype E, this ticket) |
|---|---|---|
| existing tests | 3 real failures: `test_k5_round12_fuzz.py::test_no_fragment_of_an_encoded_secret_value_survives_any_producer` (2 leaks), `::test_a_tag_longer_than_200_characters_splitting_an_encoded_separator_leaves_nothing` (`xyz9abc` shown), `test_k5_round11.py::test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook` | 0 real failures |
| probe, 4,000 texts | 94 texts with a bare domain after a placeholder; link remains such as `[link removed]>/runbook?id=7` and `[link removed]>@<HOSTNAME_1>:5432/app` (the first pass puts a placeholder inside a link, the link pattern stops at `>`) | 0 identifier leaks, 0 bare domains |
| `bob@exa<b></b>mple.com`, `bob.smith@example。com` | second one still shown | both `<EMAIL_1>` |
(Both prototypes also fail `test_the_gitleaks_header_chain_regex...`: it looks for `.gitleaks.toml` beside the copied folder, which the author's copy did not have. Not a result.)
Timing on a 2,800-character made-up card, 5 calls: main 0.037 s, prototype E 0.032 s. No extra redaction pass is added.
Behaviour changes a user can see: (1) e-mail addresses, host names and other identifiers on a card become placeholders outside code too; (2) a text such as `token: bob.smith@example.com` is masked as `<EMAIL_1>` where main wrote `<SECRET_1>` (main only reached the secret rule because the address was already broken by brackets); (3) a domain that ends up outside code after the redaction is bracketed (F6b).

## Sibling search (whole `src/` and `demos/`, 2026-11-11, grep commands in the author's notes; verdict each)
"Changed is taken for masked":
- `k1b/redaction.py:114` THE BUG, fixed here.
- `k1b/redaction.py:128` timestamp passes before the credential check: kept on purpose, 1d.
- `guard/runmap.py:517` `again.mapping != current or _held(again.text) > _held(out)` (a view replaces the result when it holds more placeholders): SAME CLASS, sweep F3 already says this step can replace a masked result with a leaking one. Forbidden file: for the F1-F4 builder; not fixed here.
- `approvals/channel.py:37` (the tag-stripped view replaces the result when its map holds a new secret): same shape. After Behaviour 2 both candidates pass the same three steps. NOT proved safe: the builder adds the seeded test "whatever the first candidate masked is not readable in the returned text" (new tests, N9); if it fails, return the candidate only when it also hides every original of the first map.
- `guard/runmap.py:620` and `actions/authorizer.py:39` `has_placeholder` ("a placeholder is left, so the input is unresolved"): the safe direction (deny). OK.
- `tools.py:956,964`: compare a cut and a fail-closed marker, not masking. OK. (Forbidden file anyway.)
"A rewrite before the detector" (every caller of `redact_text`, `redact_untrusted`, `redact_bounded`, `redact_value`, `safe_head`, `redact_layered`):
- `approvals/channel.py:29,36` THE BUG, fixed here. `approvals/slack_channel.py:74-81` SAME BUG (same hook, plus `withhold_commands` before it), fixed here through the shared function.
- `approvals/requests.py:39,47` and `approvals/cards.py:59` call `clean`: fixed by the fix. `approvals/channel.py:104,111`, `slack_channel.py:197` call `clean`: same.
- `guard/runmap.py:340-350` `neutralise_untrusted` (the hook of every other untrusted text): rewrites `<<` and placeholder look-alikes only; read, no identifier is changed. OK.
- `tools.py:957-1005` (scrub before the escape strip) is sweep F2; `guard/redact.py:825-838` is F3: the other builder.
- `runtime/evidence.py:154,191`, `runtime/agent_loop.py:367,489`, `evals.py:63`, `guard/judge.py:71`, `guard/bedrock_guardrail.py:98`, `extract.py:58`, `guard/injection.py:96`, `k1b/loop.py:187,194`, `k1b/redaction.py:188`: the text reaches the redactor as received (a bytes decode at most). OK.
- `runtime/tick.py:292` replaces line breaks with spaces AFTER the redaction: cannot join two pieces (a space stays between them). OK for this class (line forging there is sweep F9).
- `demos/ask-your-data/askdata/*` call a DIFFERENT function that is also named `clean` (terminal-safe text, no redaction promised). Not this class; not otherwise checked by the author.
Found on the way, in forbidden files, handed to the lead for the F1-F4 builder (reproduced with `runmap.redact_text` alone): `bob.smith@example。com` (U+3002) and `bob.smith@example｡com` (U+FF61) are not masked (`．` U+FF0E is); `bob@é.example.com` is not masked; `password=bob.smith@example.com:Zx9 tail` in free text leaves ` tail`. After this ticket the first two are still shown inside a closed backtick fence on a card (outside code the sanitiser writes the wide dot as `.` first, so they are masked).

## Existing tests
Author's runs (prototype copies, single process, no Postgres: 32 tests skipped): the 12 test files that mention k1b, 487 pass before and after 1a-1c; the 39 approval-related files, 1,469 pass on main and all pass with Behaviour 2 except the copy artefact named above. So NO existing test is expected to change its assertion. FULL-SUITE RESULT: see the line at the end of this section.
Tests the builder must still edit, and why:
- `tests/test_k5_round11.py::test_only_clean_and_the_slack_block_call_the_card_sanitisers` (line 136): add `defang_domains` to the guarded names, so only `channel.py` may call it.
- `tests/test_k5_round11.py::test_every_redact_text_call_that_feeds_a_card_passes_the_neutralise_hook` (line 113): unchanged, must stay green. Add beside it a new guard (N8 below).
- `tests/test_k5_producers.py` and `guard/producers.py:38`: only if the registry test fails because `clean` now reaches `redact_text` through `redact_for_people`; then the row names `redact_for_people` and the test must still prove the chain ends in `redact_text`. Do not loosen the registry test.
- `tests/test_k1b_redaction_layers.py::test_env_name_value_pairs_labels_and_secret_data_are_masked_with_their_key` (line 81): unchanged; the new tests sit next to it.
If any other existing test fails, stop and report; do not edit it without saying why.
FULL-SUITE RESULT (author, one run each of all tests on main and on the combined prototype): PENDING, filled in below before hand-over.

## New tests
Each asserts on the ABSENCE of the made-up original text (never on a placeholder number or kind, which the F1-F4 work may change). Made-up data only; the only key literal is `AKIAIOSFODNN7EXAMPLE` built from two parts.
Must FAIL on origin/main (paste the failing run of each on main, then the pass on the branch):
- N1 `_pair` through `redact_bundle`, one case per input: `correct horse battery staple`; tab runs `correct\thorse\t\tbattery\tstaple`; separators `ab12;cd34,ef56&gh78`; a quote `pa55"word tail-part`; a line break; an e-mail inside the value `bob.smith@example.com Zx9 tail`; an internal host `db01.corp.internal/Zx9 tailpart`; a key followed by words `AKIA... and the rest`; a list `["correct horse", "x"]`; the env form `{"name": "DB_PASSWORD", "value": ...}`; the short value `a b` (must not return text holding `ssword=`); both quote marks `pa55"word 'tail' part` (must be exactly `<SECRET_REDACTED>`). Assert: no word of the value after the first is in the shown bundle, and the shown value is placeholders only or the fixed mask.
- N2 (F5b) the value under `password` repeated in a log message of another record is not readable there; the same for `kind: Secret` `stringData` with key `cfg`, and for `data` with the base64 text under the key and the DECODED text in the log line.
- N3 no fragment is planted: after `{"password": "correct horse battery staple"}` a log line `the correct answer` keeps the word `correct`.
- N4 (F6) `clean`: the sweep input `contact bob.smith@example.com`; an internal host; tab runs between two identifiers; an address inside a `~~~` fence; an address in angle brackets; the JSON line `Inputs: {"owner": ..., "host": ...}`; an address split by a tag `bob@exa<b></b>mple.com`; a zero-width space inside the address; the wide dot `bob.smith@example。com` outside code; percent and entity spellings `bob%2Esmith%40example%2Ecom`, `bob.smith&#64;example.com`. Assert: neither the address nor its bracketed spelling is in the result.
- N5 (F6) the same inputs through `summary()` (`approvals/requests.py`), through `cards.render_shadow` (diagnosis text), through `FakeChannel.send` / `notify`, and through the Slack blocks (`SlackChannel._blocks`, no network: the existing fake transport of the Slack tests).
- N6 (F6b) `password=ab` + backtick + `cd evil.com` + a later inline code: no bare `evil.com` outside code in the result; `10.0.0.5.evil.com` gives no bare `evil.com`.
- N7 combined: one card text holding a secret assignment whose value contains an e-mail address, an internal host, tab runs, a fenced block with an address, and a link; assert every made-up original is absent and no bare domain is outside code.
Regression guards (pass on main too; exempt from the fail-on-main proof):
- `hunter2secretXYZ` under `password` still gives one placeholder; a plain word under `message` is unchanged; a UTC timestamp under `token_expiry` is unchanged (1d); `{"credentials": {"user": "svc"}}` gives the fixed mask and plants nothing in the map (1c).
- an address inside a closed backtick fence and inside inline code is masked and the code stays code; `evil.com` outside code is still bracketed; `evil.com` inside inline code is still not; a placeholder already in the text survives; `clean(clean(x)) == clean(x)` for the N4 inputs; every existing G3/G4 expectation (existing files, untouched).
- N8 guard (class test, AST, like line 113 of `test_k5_round11.py`): in `approvals/`, the only call of `redact_text` with the card hook is inside `redact_for_people`, and `sanitise_text(..., defang=False)` is called only by the hook. So a new card path cannot skip the last step.
- N9 the tag-stripped candidate (`channel.py:37`): seeded random texts with tags, secrets and identifiers; every original in the first candidate's map (seed entries left out) is absent from the returned text.
- `_VALUE_BREAK` equals the redactor's value-ending characters (1b).
Seeded random tests (the repository's way of property testing):
- P1 `_pair`: random values from letters, digits, white space of every kind, `; & , " '`, e-mail addresses, hosts and the example key, under random credential keys and both Secret fields, 3,000 cases, fixed seed. Property: the result fully matches `(placeholder)+` or equals the fixed mask; and no run of 4 or more characters of the value that is bounded by break characters is readable anywhere in the shown bundle, including a second record that repeats the value (except values with both quote marks, asserted separately to be the fixed mask under the key).
- P2 `clean`: the author's probe turned into a test (identifiers, markup, fences, backticks, wide dots, tags, 4,000 cases, fixed seed). Properties: (a) every identifier that `runmap.redact_text` masks when it reads the text alone is not readable as a standalone word in `clean(text)`, as written or bracketed; (b) with each placeholder read as the letter `x`, `gate._DOMAIN` and `gate._NON_ASCII_HOST` find nothing outside code; (c) `clean` is idempotent. Main fails (a) on 2,619 of 4,000 (author's run).
Mutants: a new list `tests/q8b_mutants.py` in the shape of `tests/stage_mutants.py`, run by `tools/mutation_runner.py`, one CI step next to the existing `python tests/stage_mutants.py` step (`.github/workflows/ci.yml:94`). Each mutant names the test that must kill it:
M1 `_ONLY_PLACEHOLDERS.fullmatch` back to "result differs from input" (N1); M2 `fullmatch` to `match` (N1 key-followed-by-words); M3 accept the whole result when it does not start with `key=` without the placeholders-only check (N1 `a b`); M4 plain test always true, so the unquoted spelling is tried for every value (N3); M5 the `known_secret` flag dropped in `_walk` (N2 Secret case); M6 the decoded spelling not tried when the flag is set (N2 base64 case); M7 hook calls `sanitise_text` with brackets on (N4); M8 `redact_for_people` without `defang_domains` (regression guard "outside code is bracketed"); M9 `defang_domains` without the after-placeholder rule (N6); M10 `defang_domains` brackets inside a closed backtick fence (regression guard); M11 `slack_channel.py:81` back to the bare `redact_text` call (N8 and N5).

## CHANGELOG ("Unreleased")
- **Fixed (masking before the model, incident cases):** a value under a key that names a credential (`password`, `token`, `api_key`, an env entry named `DB_PASSWORD`, a Kubernetes Secret entry) was shown partly masked when it held a space, a tab, a line break, `;`, `,`, `&` or a quote mark: `"password": "correct horse battery staple"` reached the model as `<SECRET_1> horse battery staple`. Now the value is shown only as placeholders; anything else becomes `<SECRET_REDACTED>`. The whole value is also masked where it is repeated in another record. Not covered: a value that holds both `"` and `'` is masked under its key but not where it is repeated.
- **Fixed (approval cards and notices):** an e-mail address, a host name or another identifier outside code was shown on a card with brackets in its dots (`bob.smith@example[.]com`) instead of a placeholder. Card text is now masked before dots are bracketed. A domain that ends up outside code after masking is bracketed too.
- **Changed (what an approver sees):** identifiers outside code on a card are placeholders such as `<EMAIL_1>` and `<HOSTNAME_1>`. Some texts change their placeholder kind (an address after `token:` is `<EMAIL_n>`, it was `<SECRET_n>`).
- Honest limit, in the same entry: masking is pattern based; an identifier no pattern knows is still shown (see `LIMITS`).

## Gates
`uv run --all-extras --group test ruff check`, `ruff format --check`, full `pytest` WITH `HADAVIN_TEST_PG_DSN` (own Postgres 16 cluster, non-skipped output pasted), `bandit -ll`, the repo guard tests, `python tests/q8b_mutants.py` (every mutant killed by its named test), the existing redaction performance step of CI unchanged. Gate on pytest's own exit code. Then a separate EVIDENCE RUNNER (raw output, the fail-on-main proof for N1-N7, P1, P2) and egm:* result reviewers on a snapshot of the head; fix every blocker and major; rounds uncapped (redaction path); drift report before "done".

## Open decisions for the plan reviewers (the author does not decide these)
1. F5b through the quoted spelling (1b, 1c) now, or only 1a now and F5b later through a public function in `guard/runmap.py` once the F1-F4 pull request is merged? The author proposes 1b and 1c now: the leak is real on main today and the glue fails safe (if the redactor's quote grammar changes, the result is the fixed mask and N2 fails loudly).
2. The value with both quote marks (masked under its key, not where repeated) cannot be closed without a forbidden file. Proposed next step: follow-up ticket Q8c "register a known secret in the run map" right after the F1-F4 pull request merges; date set by the lead.
3. 1d (a timestamp under a credential key stays readable): keep, as proposed, or mask?

## Not in scope
- Any edit of `guard/redact.py`, `guard/runmap.py`, `tools.py` (F1-F4, F7), and sweep findings F8, F9, F10.
- The wide-dot, non-ASCII and free-text-tail spellings listed at the end of the sibling search (the redactor's patterns).
- `guard/runmap.py:517` (same class as F5, forbidden file).
- The demo's own `clean` in `demos/ask-your-data`.
- New masking patterns, new placeholder kinds, any change to what `sanitise_text` removes, any change to `withhold_commands`.
- Names in free text and other things `LIMITS` already states the redactor does not catch.
