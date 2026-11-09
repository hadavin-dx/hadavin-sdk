# Package ticket P1d-b: a credential key name written in a disguised spelling is not recognised (S11, S12 and the literal key checks of `k1b/redaction.py`), and the approval receiver logs the raw request line (S16). DRAFT revision 1 (plan review round 1 not yet run)

**Status (2026-11-09 06:32 UTC / 12:02 IST):** text only, no code. Drafted by `egm:egm-draft` (headless; the skill's `resources/execution_instructions.md` is missing from the plugin cache, so its section gates were not run). Probes P1-P2 below were RUN once on branch `core/cloud-handover` head `391767b` (Python from `uv run --all-extras --group test`); scripts and raw output: `handover/evidence/P1d-b/probe_s11.py`, `probe_s11-2026-11-09.txt`, `probe_s16.py`, `probe_s16-2026-11-09.txt`. Everything about P1d's own code (`guard/_views.py`, `delete_noise`, `P1DB_APPLIED`) is from ticket P1d rev 5 and `round5-resolve.md` D5/G10 and is UNVERIFIED until P1d is built. Marker: CODE-LAST v1.
**Ledger rows closed:** BL-core-p1d-006 (S11, MAJOR) and BL-core-p1d-009 (S16, MINOR; ledger and P1d.md line 176 place S16 here, not in P1d-c). New rows this ticket adds at plan review: 011 (S12a, see below, MAJOR), 012 (literal `kind`/`value`/`data` checks, MAJOR).

## The problem in plain words
The incident-case masker (`k1b/redaction.py`) decides from a key NAME whether its value is a password or other credential; if yes, the value is hidden whole. The test reads the name only as written. So `db_pass` + an invisible zero-width space + `word`, the same name with one Cyrillic letter that looks Latin, or `db-pass**word**` is "not a credential", and a plain password value under it (no pattern knows `hunter2`) is sent to the eval model. Three more checks in the same file compare names literally (`kind == "Secret"`, `k == "value"`, `k in ("data", "stringData")`), so a look-alike letter there shows a Kubernetes secret value or an environment password. Separately, when a credential key IS recognised, a value with spaces is only masked up to the first space. Last, the development HTTP server for approval clicks writes the raw request line (with any query value) to the debug log.

## Words used
- **Key name** = a dictionary key, or the `name` of an environment entry `{"name": ..., "value": ...}`.
- **Plain spelling** = a key made only of ASCII letters and digits in words joined by single `_`, `.`, `-` or space: the grammar `^[A-Za-z0-9]+([_.\- ][A-Za-z0-9]+)*$` (after the existing camelCase split).
- **Views** = the P1d views, reused, never re-written here: `textnorm.fold_views(key, casefold=True, scripts=frozenset())` of the key AND of `delete_noise(key)` (P1d `guard/_views.py`: markdown markers `*`, `~`, backtick, escapes and control characters deleted; `_` kept, round5 G12), and `textnorm.squeeze_views(key)`.
- **Credential word** = the words `SENSITIVE_KEY` already lists (pass/password/passwd/passphrase, secret, token, api key, authorization, credential(s), private key, bearer). No word is added here.
- **Fail closed** = when a check cannot decide, the value is hidden.

## Measured on the base (`391767b`)
| id | input | today | expected after |
|---|---|---|---|
| K01 | key `db_password` | sensitive | sensitive (pb) |
| K02 | `db_pass`+U+200B+`word` (zero-width space) | NOT sensitive | sensitive (fb) |
| K03 | `db_pas`+U+0455+`word` (Cyrillic dze) | NOT | sensitive (fb) |
| K04 | `db-pass**word**` | NOT | sensitive (fb) |
| K05 | `db_p`+U+0430+`ssword` (Cyrillic a) | NOT | sensitive (fb) |
| K06 | `db_pass`+U+00AD+`word` (soft hyphen) | NOT | sensitive (fb) |
| K07 | `db_`+U+FF50+`assword` (full-width p) | NOT | sensitive (fb) |
| K08 | `db_pa`+U+0301+`ssword` (combining accent) | NOT | sensitive (fb) |
| K09 | `db_password`+U+E0041 (tag character) | NOT | sensitive (fb) |
| K10 | `db`+U+00A0+`password` (no-break space) | sensitive | sensitive (pb) |
| K11 | `dbpassword` (plain, no word break) | NOT | NOT (pb; see open question 2) |
| K12 | `passenger`, `author`, `tokens_used` | NOT | NOT (pb, no over-mask on plain spellings) |
| W01 | `_pair("password", "correct horse battery staple")` | `<SECRET_1> horse battery staple` (3 of 4 words shown) | whole value hidden (fb, row 011) |
| W02 | `{"kind": "Secr"+U+0435+"t", "data": {"x": base64("hunter2xyz")}}` | base64 value shown | value hidden (fb, row 012) |
| W03 | `{"name": "DB_PASSWORD", "v"+U+0430+"lue": "hunter2xyz"}` | `hunter2xyz` shown | value hidden (fb, row 012) |
| L01 | `POST /slack/actions?t=<KEY>` to `receiver.serve` | key in DEBUG log | no request line text in the log (fb) |
| L02 | malformed request line `GARBAGE <KEY> HTTP/9` | key in DEBUG log (via `log_error`) | not in the log (fb) |
`<KEY>` = the AWS documentation key built from parts. Rows K02-K09, W01-W03, L01-L02 are M (probe output above); K12 `author`/`tokens_used` R (docstring of `SENSITIVE_KEY`), `passenger` M.

## Class and choke point
**Class:** "a decision about whether a value is secret is made on a literal comparison of a name, while a reader or a later step reads another spelling" (the P1d class, R337, applied to names instead of values). Standards: Unicode UTS #39 (confusables) and UAX #15 (normalisation) as already used by `textnorm`; read date of the standards UNVERIFIED.
**Choke point:** `k1b.redaction.sensitive()` stays the ONE place a name is judged; every other name check in the file is routed through two small helpers in the same file that use the P1d views: `sensitive(key)` and `_is_name(key, word)`. No new masker and no new view code: the value is still masked by `runmap.redact_untrusted` (the P1d choke point) or replaced by the existing `MASKED`.
**Sibling search (done for this draft, R read):** `grep -rn` over `src/hadavin_sdk` for key-name credential tests: only `k1b/redaction.py:88` (`SENSITIVE_KEY`). `guard/redact.py:~480` (the SECRET pattern's key words) runs on the `redact_text` path and is covered by P1d (learning pass on its views), not here. N9 of the sibling report (`demos/.../opscli.py _redact`) uses our own fixed field names: not a sibling. BS-0 repeats the grep on the base it builds from.

## Behaviour, exactly
1. `sensitive(key)`: not a `str` -> False (unchanged). Camel split as today. True if `SENSITIVE_KEY` matches the key as written OR any fold view of the key OR of `delete_noise(key)`. Otherwise, if the key is NOT in the plain spelling and any `squeeze_views` view contains a credential word as a substring -> True (fail closed only for keys that hold something other than plain spelling, so K12 is unchanged). Otherwise, if `textnorm.has_hidden_channel(key)` or `has_mixed_script(key)` -> True. Any `TextnormError` (too long, not text, fold not converging) -> True. Otherwise False.
2. `_is_name(key, word)`: True if the key is a `str` and `textnorm.fold(key, casefold=True) == word.casefold()`, or the key is not in the plain spelling and a squeeze view equals `word` upper-cased. Used for `kind == "Secret"`, `k == "value"`, `"data"`/`"stringData"`, `obj.get("name")` lookup.
3. Allowlist inversion inside credential objects (fail closed): under an object whose `kind` is Secret, every key except the exact plain names `apiVersion`, `kind`, `metadata`, `type` is secret data. Under an environment entry whose `name` is sensitive, every string leaf except the `name` key itself goes through `_pair`.
4. `_pair` (S12, row 011): it still runs the redactor on `key=value` (and on the base64 decoding) so the run map learns the value, but it returns the redactor's output only when that output, with every genuine placeholder removed, holds no letter or digit; otherwise it returns `MASKED`. A value the P1d redactor withholds (`runmap.is_withheld`) also returns `MASKED`.
5. `receiver.serve` (S16): `log_message` writes a fixed line built only from our own words: `"receiver: %s %s %d"` with the method if it is one of `POST`/`GET`/`HEAD`/`OTHER`, the path class (`actions` if the path before `?` equals `PATH`, else `other`) and the status code. Nothing from the request line, headers or body. `log_error` is routed to the same fixed line (BaseHTTPRequestHandler sends its messages through `log_message`; BS-0 reads the Python 3.12 and 3.13 `http.server` source to confirm both `log_request` and `log_error` go through `log_message`).
6. `runmap.P1DB_APPLIED = True` is added by this package (P1d defines the name and the client-profile check, round5 G10).

## RUNG TABLE (scale of 2026-11-06, R447)
| component | need | rung tried | evidence | what only our code gives | verdict |
|---|---|---|---|---|---|
| name views | read a key name as a person reads it | 2: `textnorm.fold_views`, `squeeze_views`, `has_hidden_channel`, `has_mixed_script` (P1b), P1d `delete_noise` | `textnorm.py` on `origin/core/P1b-fixwip` `2034512`, R 2026-11-09 | nothing: reused | CUT-TO-CONFIG+GLUE |
| credential-name decision | which names hide their value | 4: detect-secrets keyword plugin, gitleaks rules | UNVERIFIED (not read); both match key words on the text as written, none folds look-alikes | the fail-closed rule for non-plain names, inside our masker | KEEP-CODE, about 25 lines (estimate) |
| whole-value masking | never show part of a credential value | 2: existing `MASKED`, `redact_untrusted` | M (W01) | the "no letter or digit left" test | KEEP-CODE, about 8 lines |
| request log | log a click without its content | 4: stdlib `http.server` hooks | R (receiver.py:62) | a fixed line from our own words | KEEP-CODE, about 8 lines |
Rung 1 (no-code) closed: a core library function, no flow. 80 percent rule: rung 2 covers the views wholly; the decision and the logging are a guarantee path (redaction before the model, R447).

## Template fields
- **Package id:** P1d-b, "credential names and the receiver log". **Path class:** redaction and security; extended review, no round cap: yes.
- **Depends on (merged first):** P1b (textnorm) and P1d (`guard/_views.py`, `delete_noise`, `is_withheld`, the `P1DB_APPLIED` check). If P1d's D5 move to `guard/_views.py` does not happen, BS-0 imports `delete_noise` from where P1d puts it and records the path; no copy.
- **Source of the code:** our own; nothing copied. Not taken: no new pattern words, no change to `SCHEMA_WORDS` (an exact match there only skips redaction of the key itself; a disguised schema word is redacted, which is already fail closed).
- **Target modules:** `src/hadavin_sdk/k1b/redaction.py`, `src/hadavin_sdk/approvals/receiver.py`, `src/hadavin_sdk/guard/runmap.py` (one line, the marker).
- **Interface:** unchanged signatures: `sensitive(key: object) -> bool`, `_pair(key, value, f) -> str`, `serve(...)`. New private `_is_name(key: object, word: str) -> bool`, `_plain(key: str) -> bool`. `LIMITS` text gains one sentence: a key in plain spelling with no word break (`dbpassword`) is judged by word boundaries only.
- **Neutral default / alternative:** no vendor. Alternative if textnorm is removed: the outline is "names that are not plain spelling are all treated as credentials" (pure fail closed, higher over-mask); trigger = textnorm withdrawn.
- **Files:** change `k1b/redaction.py` (rules 1-4), `approvals/receiver.py` (rule 5), `guard/runmap.py` (marker), `CHANGELOG.md` (non-revertible: more values hidden; log line format changed). Create `tests/test_p1d_b.py` (rows K, W, L), `tests/fixtures/p1d_b_cases.py` (literals built from parts). Change `tests/test_p7_tick.py` only if it asserts the old log text (BS-0 greps).
- **Existing core code reused (checked):** `textnorm` (above), P1d `_views.delete_noise` and `is_withheld`, `runmap.redact_untrusted`, `RunMap`, `MASKED`. Checked, not reused: `guard/redact.py` SECRET key words (another path).
- **Security and least privilege:** no identity, right or secret. The log line holds no client text (test greps the log for the key). Note: `serve` is a server for local use only (its docstring); the docstring's word "development" is renamed to "local use" (R449: no "dev" stage word). Whether the client profile must refuse `serve` is open question 3.
- **Tests:** the rows above, each fb row run on the base and shown failing (evidence command below). Property test (hypothesis): for each credential word and each of zero-width (U+200B, U+200C, U+200D, U+2060, U+FEFF), soft hyphen, a tag character, a combining mark, a Cyrillic/Greek look-alike from the textnorm table, `**`, `~~`, backtick inserted at any position inside the word in a `db_<word>` key -> `sensitive` is True. Over-mask count: run `sensitive` over the made-up corpus of 500 plain key names from the existing k1b fixtures plus 200 non-English names (made up) and report how many flip from False to True, separately from the fb rows (ORDER 166 item 2 style). Hostile: a key of 100,000 characters (TextnormError -> True). End to end: `redact_bundle` on a made-up bundle holding K02-K09 keys, W02, W03 -> no value appears in the output (grep).
- **Mutation plan:** MB1 drop the fold views (K03, K05, K07 kill); MB2 drop `delete_noise` view (K04); MB3 drop the non-plain squeeze rule (K02 if fold keeps U+200B, else K06; BS-0 records which); MB4 drop hidden-channel check (K09); MB5 TextnormError returns False (hostile long key); MB6 `_pair` returns redactor output when changed (W01); MB7 Secret allowlist back to literal `data` (W02); MB8 env `value` literal (W03); MB9 `log_message` passes `args` (L01); MB10 `log_error` not routed (L02); MB11 plain-spelling test always False (K12 over-mask row); MB12 marker missing (P1d's `test_client_profile_refuses_without_marker`).
- **Evidence commands:** `uv run --all-extras --group test pytest tests/test_p1d_b.py -q > handover/evidence/P1d-b/rows.txt 2>&1; echo rc=$?`; fail-before: the same file run on a worktree of the base SHA (counts failures, errors must be 0); full suite once on the final head through the heavy slot; mutants via `tools/mutation_runner.py` if on the base, else a plain loop, output `handover/evidence/P1d-b/mutants.txt`; ruff check, ruff format --check, bandit -ll.
- **Reviewers:** `egm-codebase-details` (correctness) + `egm-design` and `egm-implementation-readiness` (adversarial), fresh, given the diff, this ticket and the evidence only.
- **Done =** a fresh round finds no blocker or major; all gates green (tests 3.12 and 3.13, ruff, format, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit); rows 006, 009, 011, 012 FIXED-VERIFIED; the lead merges.
- **Rollback:** tag `pre-P1d-b`; no migration. Non-revertible semantic changes (CHANGELOG): more values masked; the receiver log line format.
- **Slots and real clock (estimate):** build 2-3 agent-hours after P1d merges; evidence 1 hour (one full suite, one mutant run); review rounds 1 hour each. No conflict with P1d files except `runmap.py` (one line, rebase only).

## Open questions for the lead (each has a default applied)
1. **Placement of S16.** Your brief put S16 in P1d-c; ledger row 009 and P1d.md line 176 put it in P1d-b with marker `P1DB_APPLIED`. Default applied: P1d-b (so the marker covers it). Say if it moves.
2. **`dbpassword` (K11).** A plain name with no word break is not a credential today and stays so (substring matching would hide `passenger`, `bypass_count`, `tokenizer`). Default: unchanged, stated in `LIMITS`, over-mask corpus reports what a substring rule would cost. Say if you want the substring rule.
3. **`serve` in the client profile.** Default: not refused here (it binds 127.0.0.1 by default; the log fix makes it safe to log). Say if the client profile must refuse it (a dev-only kind rule).

## UNVERIFIED
P1d's `delete_noise` and module path; whether `fold_views` deletes U+200B and U+00AD (probe in BS-0; MB3's killer depends on it); the detect-secrets/gitleaks rung row; `http.server` routing of `log_error` on 3.13; whether any test asserts the old receiver log text; the over-mask number.

## Rules cited
R233, R337, R447, R448, R449, R450; preamble rules 3, 5, 6, 7, 13, 14, 20.

## Revision log
Rev 1 (2026-11-09): first draft (egm:egm-draft, headless), from P1d rev 5, round5-resolve, the sibling report S11/S12/S16, ledger rows 006/009, ORDERS 165-168 and probes P1-P2.
