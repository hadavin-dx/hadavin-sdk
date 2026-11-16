<!-- full hand-back report of sub-agent a865e68c, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

# Q8b plan review, round 2 (implementation readiness) — verdict: NOT READY

One blocker, ten majors. I ran nothing (read-only tools): every "main gives / branch gives" below is traced by reading code or taken from the author's saved outputs, and each needs a run before the ticket is revised.

**Tests folder used:** `/home/user/build/EV-P3a2-main-2a8c2aa` existed when I started and vanished mid-review. I read `tests/test_k5_round11.py`, `tools/mutation_runner.py` and `.github/workflows/ci.yml` from it; `tests/stage_mutants.py`, `tests/test_k5_producers.py` and `tests/k1b_support.py` come from `/home/user/build/EV-P89-db0d9eb`.

Ticket: `/home/user/hadavin-sdk/handover/tickets/Q8b-partial-mask-and-card-redaction.md`. Code: `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/`. Prototype: `/home/user/build/q8b-author/protoQ8b/`.

## Blocker

**B1. Behaviour 1f, the setting-word rule makes readable a credential that main masks.**
- Where: ticket line 49; prototype `k1b/redaction.py:104` (`if not words or words[-1] in SETTING_WORDS: return False`); main `k1b/redaction.py:88-91`.
- Main's pattern matches `password_used`, `token_type`, `secret_max` and the like, so their values go through `_pair` and everything nested inherits the mask (line 126).
- Hostile inputs (build the key from parts in tests):
  - `{'pass' + 'word_used': 'tr0ub4dor'}`: main writes `password_used=tr0ub4dor` and the general rule (`guard/redact.py:598-614`) masks it whole. Rev 2 sends the bare value to the redactor with no key, so it stays readable.
  - `{'pass' + 'word_used': 'correct horse battery staple'}`: main shows it partly (F5), rev 2 shows it whole.
  - `{'name': 'API_KEY_TYPE', 'value': 'tr0ub4dor'}`, `{'token_policy': {'default': 'tr0ub4dor'}}`, `{'client_secret_max': 'tr0ub4dor'}`: main gives a placeholder or the fixed mask, rev 2 shows the value.
- Three of the fifteen words do nothing for the stated negatives. `tokens_used` and `max_tokens` are negative because `tokens` is not a credential word (same as main), so `used`, `max` and `min` only open `password_used`, `token_used`, `secret_max`.
- D-011 ruled one key only: "`password_policy_enabled` counts as NOT a credential". The generalisation to any key ending in one of fifteen words is the author's.
- The ticket's "superset" sentence is true only because it excludes exactly these keys.
- Is an exact-key allowlist safer? Yes: an unknown key stays masked. But it is brittle (`passwordPolicyEnabled`, `password_policy_required`). A value-shape gate is safer still and keeps the D-011 ruling.
- Exact text to replace the second bullet of 1f:

  > "`sensitive(key)` has no setting-word exception (every key main accepts is accepted, without exception; the 193,535-key check is re-run with no exclusion). Separately, `_setting_key(key)` is true when `sensitive(key)` and the last word is in `SETTING_WORDS = {enabled, disabled, required, policy, length, count, age, days, ttl, expiry, expires}`. In `_walk`, a value under a `_setting_key` (own key or env-entry name) is left unmasked ONLY when it is a bool, None, an int or float, a timestamp (`parse_ts`), or a string that fully matches `(?i)true|false|yes|no|on|off|none|[0-9]{1,10}[smhdw]?`. Every other string, and every dict or list under it, is treated exactly as under a credential key (as on main). T1: `password_policy_enabled`, `token_expiry`, `secret_count` move to a third list 'credential key, setting value shown'. New N1 rows that must be masked: each literal above. Mutant: the value-shape test replaced by `True`, killed by those rows."

- The stated costs are otherwise acceptable:
  - `PWD` masked: fine, but also say `OLDPWD` and any key ending in `pwd` (`GLUED_ENDINGS`).
  - `token_expiry`: a timestamp passes under 1d anyway, and a number becomes readable under the gate above.

## Majors

**M1. Behaviour 1e (design M5): the sweep is unbounded for short common values, and nothing that was run touches this path.**
- `guard/redact.py:1207-1216`: a SECRET-kind original of 4 or more characters is replaced at every copy. The common-word exemption at 1217 does not apply to secret kinds.
- Hostile input (base64 of `info`): `[{'kind': 'Secret', 'data': {'LOG_LEVEL': 'aW5mbw=='}}, {'level': 'info', 'message': 'information: retry in 5s'}]`. By reading, this gives `{'level': '<SECRET_n>', 'message': '<SECRET_n>rmation: retry in 5s'}`.
- The same holds for `true`, `prod`, `5432`, `http`, `json`, `root`, `postgres`. Dict keys are swept too (`_key`), so `orders_count` becomes `<SECRET_n>_count`.
- The substitute evidence is not evidence for 1e. `tests/k1b_support.py` holds no Secret, so the "existing k1b tests green" line never runs this branch. D-011 required "replay scores before/after"; that condition is unmet.
- Smallest honest check, with no model and no owner yes needed. Add to the ticket, to be run by the author before build:

  > "Fixture: the `k1b_support` bundle plus one made-up Secret with `LOG_LEVEL=info, DEBUG=true, ENV=prod, PORT=5432, DB_USER=postgres, DB_NAME=orders, DB_PW=<made-up 16 chars>`, and logs that use those words. Report for main and for the branch: (a) the number of characters and of distinct log lines changed outside the Secret; (b) for every tool of `k1b/tools.py` called with the masked spellings, the list of evidence IDs returned (must be equal); (c) the masked `level` and `service` values."

- Is a 4-character sweep of non-credential entries acceptable? Not as written. Proposed rule for the lead to confirm:

  > "Under a NON-credential key of a Secret, a spelling is registered only when it has at least `MIN_REGISTER_CHARS = 8` characters and is neither all digits nor one run of lower-case letters; otherwise fixed mask under its key, as on main. Listed in Limits; G7 pins `orders`, `info`, `true`, `5432` as NOT swept and `orders-svc` (row 46) as swept."

- Under a credential key nothing changes (the redactor's own 4-character rule).
- Design M5 also asked for "the same placeholder under the key and in the log line". For `data` entries it is not: rows 35 and 37 show `<SECRET_1>` under the key and `<SECRET_3>` / `<SECRET_2>` in the log (`r2_f5_proto.txt:27,35`). The model cannot link them. Text for 1c: "with `known_secret=True` the result returned is that of the LAST accepted spelling (the decoded text), else the first". Have G7 assert the two placeholders are equal.
- The "k1b tools still resolve `service`" test that design M5 asked for is absent.

**M2. 1f, credential keys still not recognised and not listed.**
- `tokens` is in no list. `{'api_tokens': ['correct horse battery staple']}`, `{'refresh_tokens': ...}` and `{'tokens': ...}` are shown whole (same on main, but design M1 asked for plurals and the ticket lists only `tokens_used` and `max_tokens` as negatives).
- Text: "`tokens` is a credential word unless the word before it is one of `max, min, input, output, prompt, completion, total, cached` or the word after it is `used`; T1 gains `api_tokens`, `refresh_tokens`, `tokens` as True and `prompt_tokens`, `total_tokens` as False."
- Key words the redactor's own list has (`redact.py:598-606`) that `sensitive()` lacks: `session`, `sessionid`, `auth`, `account_key`, `sas_token` (covered by `token`), `client-key-data`. The "two grammars drifted" class is narrowed, not closed. Either add them or name them in `LIMITS`.
- Also unlisted and shown: `password2`, `token1` (same on main).

**M3. Limits section, strict xfail tests fail open in three ways, and the follow-up id is taken.**
- A strict xfail stays quietly "expected" when the test dies for any reason (TypeError, import error, fixture). Text: `pytest.mark.xfail(strict=True, raises=AssertionError, reason=...)`.
- Each X test must hold exactly one assertion, the readable-copy one. Preconditions (masked under its own key) go into the non-xfail N1.
- X6 covers two spellings in one test. If the follow-up fixes base64 but not the wrapped copy, the test still fails and nobody is told. Row 38 has five spellings (base64, capitals, wrapped, double space, hex). Text: "X6 is parametrised, one strict xfail per spelling of row 38". The same applies to any X with more than one case.
- "Q8c" is already another ticket: `handover/AUTONOMOUS-DECISIONS.md:74` (D-013, "Q8c after plan review round 2", Vault). The id goes into xfail reasons, `LIMITS` and the public CHANGELOG. Use a free id.
- No date for the follow-up ("the lead sets the date"). `fix-dont-defer-be-honest.md` rule 2 needs the date in the hand-off.
- Add: "after the rebase on PR77 an X test that XPASSes is reported, its mark removed, and the case moved to N2".

**M4. Limits are incomplete, and two sentences still claim more than is true.**
- Still readable where repeated, not listed and with no X test:
  - A value of 1 to 3 characters (`redact.py:1207-1209`: under 3 never, exactly 3 only standalone). Example: `[{'pin_token': 'ab1'}, {'message': 'xab1y'}]`.
  - An env-entry value that is a number (row 12; same class as X5 but another route).
  - A plain value that holds `%XX` or a backslash escape (both in `_PLAIN_CHARS`). The second-pass views may split it, and whether the whole value is registered was not measured. Measure `{PW: 'ab%20cd9xtail'}` and `{PW: 'ab\\u0041cd9xtail'}` with a log copy, then list or fix.
  - A copy without the escape sequence when the value held ESC (row 24 registers a normalised form).
- Overclaims:
  - 1e and the third Upgrade-steps bullet say "every entry ... is replaced wherever it appears". False for composite values, values over 255 characters, both quote marks, under 4 characters and non-strings. Add "within the limits listed under Changed".
  - Rows 39, 40 and 46 back the "copies in a spelling the redactor decodes are masked" claim but are in no test (N1 is rows 1-8, 12-25, 31-33; N2 is 34-35). Design M4 asked for the annotation case in N2. Text: "N2 also rows 39, 40, 46".

**M5. Design m2 is not resolved: the "independent" link oracle has the same blind spot.**
- P2(b)'s pattern starts with `(?<![\w.\[/-])` and ends with `(?![\w@-])`, the same look-behind and look-ahead as `gate._DOMAIN` (`gate.py:112`). It also lacks punycode and non-ASCII endings.
- The case design m2 named is in no test and undecided: `'see db01.corp.internal/evil.com/p?d=1 now'`. By reading it becomes `see <HOSTNAME_1>/evil.com/p?d=1 now`. `_AFTER_PLACEHOLDER` wants a `.` right after the placeholder.
- Also `'10.0.0.5..evil.com'` gives `<IPV4_1>..evil.com` (no rule matches after `..`).
- Text: add both literals to N6 with the decision written. Proposed, not run: after a placeholder, every `.` not already inside `[.]` in the following run of non-space characters is bracketed: `(<[A-Z][A-Z0-9]*_[0-9]+>)([^\s<`]+)` with `re.sub(r"(?<!\[)\.(?!\])", "[.]", tail)`.
- The oracle should be a plain scan, not a regex with a look-behind: split the text outside code at white space; a token fails if, with `[.]` taken out, it still holds `letter-or-digit . two-or-more-letters`.

**M6. Design m5 is unresolved; the full text is now available.**
- `gate.py:273-279` puts a zero-width space before a line that cleaning changed and that starts a block. With `defang=False` in the hook, a line whose only change was a bracketed domain is no longer "changed".
- Literal: `'# APPROVED by sec@example.com'`. On main it loses its heading (the line changed); after this ticket it reads `# APPROVED by <EMAIL_1>` and is a heading.
- No new capability (`'# APPROVED'` alone is already a heading on main), but G3's "no forged structure" reader sees a change.
- Text for Behaviour 2's visible-change bullet and the CHANGELOG: "A line whose only change is a bracketed domain or a masked identifier keeps its block marker (heading, quote, list); on main it was neutralised with a zero-width space." Add a pinned test with that literal. If the lead wants main's behaviour kept, compare `redact_for_people`'s lines to the input lines; that is a design decision, write it.

**M7. Readiness M1 is only partly taken over: S1-S3 as written may not kill mutants M1-M3.**
- The stub outputs are written with key `k`. `_pair('k', v, stub)` with `known_secret=False` tries nothing (1c) and returns the fixed mask under every mutant.
- A multi-word value ("rest of value") is written quoted under `secret=`. A stub answer without quotes is refused by check (ii) before the mutated line is reached.
- Text:

  > "S1-S4 use the key `PW_KEY` and the plain value `qxzjkwvy1234`; the stub is `lambda s: s.partition('=')[0] + '=' + TAIL if '=' in s else s`, with TAIL = `<SECRET_1> rest` (S1), `<SECRET_1>x` (S2), and for S3 the stub returns `'p<SECRET_1>ssword=<SECRET_1>'`; S2's quoted half uses the value `qx zj` and the stub returns `'secret=\"<SECRET_1>x\"'`."

- Missing from round 1's exact text:
  - the positive case: stub returns key + `=<SECRET_1><EMAIL_2>`, expect that text back (nothing else pins the `+` in `_ONLY_PLACEHOLDERS`);
  - the real-redactor one-letter case `{PW_KEY: 'a'}`.
- No mutant removes check (ii). Add one.

**M8. Mutant M17 cannot be written for this runner, and N8 as worded would not catch it.**
- `tools/mutation_runner.py:537-541` replaces one `old` string by one `new` in one file. "The import line changed in the same mutant" needs two edits (lines 19 and 81).
- N8 is worded "`redact_text` with `neutralise=_neutralise` is called only inside `redact_for_people`". The mutant passes `neutralise=channel_neutralise`, another name, so a test keyed on that keyword value passes.
- Text:
  - N8: "any call named `redact_text` in a file under `approvals/` must sit inside the function `redact_for_people`, whatever its arguments; message `a card path skips redact_for_people`".
  - M17 `new`: `runmap.redact_text(withheld, seeded, neutralise=clean.__globals__["_neutralise"])` (one replacement, nothing undefined).
- State once: the `file` column is `src/hadavin_sdk/...`, `test_file` is `tests/...`, as in `tests/stage_mutants.py:22-27`.
- The `old`/`new` cells of M3, M4, M5, M11, M13 and M16 are prose about code the ticket never fixes. Say either "the production text of `sensitive`, `_attempts`, `_accepted`, `_pair`, `_named`, `_walk`, `defang_domains` is the prototype's, pasted here" or "the builder writes the exact strings; a `SNIPPET NOT FOUND` row is a failure".

**M9. The random tests depend on files outside the repository and on one lucky text (readiness M7 partly resolved).**
- P2 is "the author's probe as a test" and N9 is "the generator of `r2_f6.py`". Both live in `/home/user/build/q8b-author/`; a sibling build folder disappeared during this review.
- Paste into the ticket: N9's `IDS`, `SEC`, `BITS` and the 0.45 / 2-10 draw (`r2_f6.py:39-45`), and P2's generator with its identifier list.
- N9's fail-on-main proof and mutant M16 rest on 1 text in 3,000. "Lower only the case count" or a PR77 change can lose it. Add it as a fixed case and pin M16 to that test. The text (`r2_f6_main.txt:20`), with the key built from parts: `'<i></i>hunter2secretXYZ3D\npassword=password=<i></i> hunter2secretXYZ</b>'`.
- State plainly that the "original" readable there is the text `password=`, not a secret.
- P1 gaps:
  - No value length range. Give "1 to 300 characters, at least 5% over 255".
  - The alphabet lacks what design M6 listed: `\x08`, `\x7f`, `%XX`, backslash escapes, `< > = : | / @`, full-width letters and U+FF02 / U+FF07, zero-width characters, a literal `<SECRET_1>`.
  - The precondition of (c), "no address or host", misses digit runs that another pattern masks. Use "`runmap.redact_text(value, {})` returns the value unchanged".
- P2(b): "outside code" is undefined. Round 1 gave the sentence (`gate._closed_fences(result)` bodies and `_INLINE_CODE` spans of a line without a double backtick).
- P1 and N9 run times were not measured. Round 1 asked for them.

**M10. Two edits were never in the prototype's full run, and two guards break the ticket's own coupling rule.**
- 1g rewrites `LIMITS` and the `_pair` docstring. The prototype kept main's `LIMITS` (`protoQ8b/.../redaction.py:41-46`) and has no docstrings. `tests/test_k1b_redaction.py:136` asserts `LIMITS in report` and `k1b/report.py:70,84` prints it, so the "no existing test fails" line does not cover 1g.
- Give the exact new `LIMITS` string in the ticket (it is user-facing report text). Main's has a broken sentence, "does not mask the values of the values the patterns do not know".
- Line 9 says tests assert absence, "never a placeholder number or kind". G7 ("row 37 pinned as written": `<SECRET_2>-api timeout`) and G8 (rows 63-65: `<HOSTNAME_1>`, `<IPV4_1>`) pin both.
- Text: G7 asserts `orders` absent and `re.search(r"<SECRET_[0-9]+>-api timeout", line)`. G8 asserts the host and the address absent and `re.search(r" on <[A-Z0-9]+_[0-9]+>\.", text)`.

## Minors

- **Behaviour 2, wording.** `channel.py:25` is a comment, not the docstring. The docstring line 21 "then ONE redaction, last" also needs rewording (readiness minor, still open).
- **Design m1 (partial).** The wide-dot limit applies inside inline code too, not only in a closed fence (ticket line 131). Say so in the CHANGELOG limit.
- **`_AFTER_PLACEHOLDER`.** It is a third hand-written placeholder shape in `gate.py` (also 96-99 and 142). Add a test that its first group equals `runmap.PLACEHOLDER.pattern` with the groups removed.
- **Prototype mismatch.** The prototype's `sanitise_text(text, defang=True)` is not keyword-only (`protoQ8b/.../gate.py:333`); the ticket is right, but the prototype numbers were measured without it.
- **round11 second loop.** "Over the same files" is ambiguous: the first loop skips the three allowed files (`test_k5_round11.py:141`). Write "over every file under `ROOT`, each name with its own allowed set".
- **G4.** "An empty map" cannot be read (`redact_bundle` drops the map). Use round 1's text: the returned Counter is empty and `svc` stays readable in a second record.
- **G5.** `clean(clean(x)) == clean(x)` is listed as passing on main and P2(c) as holding; no run is shown for either.
- **N5 through the Slack blocks.** Say the input is a raw `req.summary` (not built by `summary()`), otherwise the test cannot fail on main.
- **Design m7.** The call bound is stated, but there is no large-Secret test against `2 * MAX_BUNDLE_CHARS` (`redaction.py:182-186`). Up to four counted calls per value where main had two.
- **Design M2.** "Bytes are not a route (`k1b/bundle.py:112`)" is not stated.
- **CHANGELOG.** "Open the request in the console to see the target": nothing shows the console displays the unmasked target. Verify or delete.
- **Citations.** `agent_loop.py:269-284` and `requests.py:35` are still as round 1 corrected them (280-290 and 34).
- **Look-alike value.** `{PW_KEY: '<SECRET_1>'}` is safe only because `redact_untrusted` escapes look-alikes (`runmap.py:341-347`, PR77's file). Add it as an N1 row and to the coupling list.
- **Mutant-table test names.** `test_guard_code_stays_code`, `test_n1_a_number_in_a_named_entry` and others are not tied to the S/N/G ids. Add the id to each.
- **Evidence files.** No saved output for `r2_xf.py` (row 38) or `r2_m7.py` (rows 63-65) among the `.txt` / `.log` files in the author folder.

## Resolution table, row by row

| id | status | note |
|---|---|---|
| readiness B1 | resolved | 1b; rows 16-23 match `r2_f5_proto.txt` |
| readiness M1 | partial | M7 above |
| readiness M2 | resolved | each N4 / N6 row fails on main per `r2_f6_main.txt`; N2's assertion text is missing but inferable |
| readiness M3 | resolved | env form now passes the flag on, a stated deviation |
| readiness M4 | resolved | pattern differs from the proposal, with a reason |
| readiness M5 | resolved in rule | fragile in proof (M9) |
| readiness M6 | partial | M8 |
| readiness M7 | partial | M9 |
| readiness M8 | resolved | wording nit |
| readiness M9 | resolved | — |
| design B1 | resolved (option A) | xfail defects in M3 |
| design M1 | partial, and it introduces B1 | M2 |
| design M2 | resolved | — |
| design M3 | resolved | row 46 untested (M4) |
| design M4 | partial | M4 |
| design M5 | partial | M1 |
| design M6 | partial | allowlist done; P1 alphabet not widened |
| design M7 | resolved | owner question open with the lead |
| design m1 | partial | — |
| design m2 | mention only | M5 |
| design m3, m4, m6, m8 | resolved | — |
| design m5 | not resolved | M6 |
| design m7 | partial | — |
| design m9 | resolved | no docs describe bracketed card text; grep of `docs/` in EV-P89 found none |

## Behaviour 2 `clean()`, the seven steps

- I found no step that re-exposes text or corrupts a placeholder.
- The patterns run before the sweep, so a seeded map cannot hide a value from a pattern.
- `joined_map` is a superset of `mapping`, so step 7's difference is exactly "new in the joined pass" and placeholder numbers no longer collide.
- `_DOMAIN`, `_NON_ASCII_HOST` and `_AFTER_PLACEHOLDER` cannot span `<` or `>`.
- `_AFTER_PLACEHOLDER` is idempotent (after one pass the placeholder is followed by `[`).
- Open points: M5 (tail after `/` or `..`) and M6 (block guard).

## Forbidden files and re-runs

- No step needs an edit of `guard/redact.py`, `guard/runmap.py` or `tools.py`.
- After PR77 merges, re-run in addition to the ticket's list:
  - X1-X6 (expect XPASS reports);
  - the 193,535-key check;
  - P1, P2 and N9 with their seeds, plus the fixed N9 case;
  - every mutant `old` string in `gate.py`;
  - the M1 fixture measurement;
  - the two escaped-value rows of M4;
  - the full suite with the real `LIMITS` text.

**Verdict: NOT READY** (B1 is a new readable-credential regression; M1 lacks the evidence D-011 required).

## Not checked

- Nothing was executed; all outputs are by reading or from the author's files.
- `guard/redact.py` outside 570-615, 940-970, 1020-1050 and 1195-1220.
- `runmap.py` outside 31, 141, 276-347 and 464-543.
- `approvals/requests.py`, `approvals/cards.py`, `k1b/bundle.py` beyond greps.
- `full_*.log`, `r2_f5_main.txt`, `r2_f5.py`, the 193,535-key script and the P2 probe script.
- Chat-client link behaviour, CWE titles.
- PR77's diff.
- `handover/` start-of-session files and `.claude/rules/README.md`.
- Whether the secret scanners flag the new test literals.
