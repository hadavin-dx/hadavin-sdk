### Package Q8b, head bcb2bfec, round 2, persona design critic

I read the target, both tickets, the r1 report and the snapshot. I could not run code: I have only Read, Grep and Glob. Everything below is from reading `file:line`, and "fixed" means fixed by reading, not by execution.

## Verdict on the r1 items

| r1 item | Result |
|---|---|
| E1 (blocker) | Fixed by reading. |
| F1 | Fixed. |
| F2 | Fixed. |
| E2 | Only partly fixed, and the fix introduces new defects (B1, B2 below). |
| E3 | Fixed, with decisions to confirm. |
| F3 | Fixed. |
| F4 | Fixed for the listed keys, with a nit on glued forms. |
| F5 | Fixed. |
| M2 | Delivered for `summary()` only (m1). |

No new readable-secret regression against main in the case-bundle path.

## Findings

### [B1] Major - `whole_assignment_values` deletes text from the approval card, so the approver cannot see parts of what will run
Where: `src/hadavin_sdk/approvals/channel.py:64-90`, called at `channel.py:59-61` (so on the Slack path too, `slack_channel.py` `redact_for_people`). Ticket Behaviour 2 and the comment at `channel.py:26-28` promise "nothing is removed or joined" after the redaction.

What: after redaction, the code removes every word on the same line that follows `key=<SECRET_n>`. It stops only at a quote, a `<`, a line end or a word that looks like `key=`. `summary()` builds one line: `... Inputs: {json}. Expected: {expected_outcome}. Plan {hash}.`

Why it matters (concrete input -> wrong output):
- Plan inputs `{"args":"--password=hunter2 --force --target prod"}`. The redactor writes `--password=<SECRET_1> --force --target prod`. `_TAIL_WORD` (`channel.py:71`) consumes ` --force`, ` --target` and ` prod` up to the JSON quote. The card shows `{"args":"--password=<SECRET_1>"}`. The approver approves an action whose flags `--force --target prod` are hidden. This is the approval-card honesty promise (`approvals/channel.py:1`, `requests.py:34`).
- `expected_outcome` is model-written free text. A text such as `rotate token=abc12345 on the primary` deletes everything after it up to the next `key:` word. That includes the `Plan <hash>.` suffix, because `summary()` is one line. An injected input can use this to push content off the card. The ticket's cost note ("prose ... is dropped") does not cover hidden action arguments.
- It is also a regression versus main on a path where main showed everything. The target is the rare case of a multi-word unquoted password.

Suggested fix: do not delete by pattern. Mask the whole value in the redactor's own match, which is the better fix and may need PR77's file. Otherwise restrict the deletion to the redactor's own value span, for example by running the redactor on a view whose spaces inside the value are protected. Failing that, replace the dropped tail with a visible marker (`<SECRET_1> [more text withheld]`) so the approver knows text was hidden. Add a test that `--password=x --force` keeps `--force`, and that the `Plan <hash>.` suffix always survives.

### [B2] Major - the E2 fix is a hand-written third copy of the key list, so E2 is still open for many keys
Where: `channel.py:66-69` (`_ASSIGNED`). The redactor's list is `redact.py` `KEY_ALTERNATIVES`.

What: `_ASSIGNED` knows only `password|passwd|pwd|passphrase|pass|secret|token|api[_-]?key|apikey|credential|auth`, plus a 20-character suffix. It has no prefix class, so these keys are absent: `access_key`, `private_key`, `account_key`, `shared_access_key`, `key_data` / `client-key-data`, `cert_data`, `session_id`, `jsessionid`, `phpsessid`, `sessid`, `connect.sid`, `session`. The redactor masks all of them through its generic key rule, so a placeholder is written. `_ASSIGNED` then never matches. This is the same drift bug class as F4, introduced again one file over.

Why it matters (concrete input -> wrong output):
- `private_key=correct horse battery staple` on a card gives `private_key=<SECRET_1> horse battery staple`.
- `clean("access_key=hunter two three")` leaves `two three` readable. The r2 test (`tests/test_q8b_glued_and_whole_values.py:124-135`) uses only `password`, `token` and `pass`-style rows, so it cannot see this.
- `_ASSIGNED` also requires the placeholder to be `<SECRET_n>`. A value whose first word is classed APIKEY, BEARER or URLCRED leaves the tail readable (`channel.py:47` already lists these kinds for `_assignment_originals`).
- The tail stops at a quote, `<` or a `word:`-shaped word. `password=correct horse bob@example.com staple` becomes `password=<SECRET_1> <EMAIL_1> staple`, so `staple` stays readable.

Suggested fix: build `_ASSIGNED` from `redact.KEY_ALTERNATIVES`, as `_NO_GLUED_KEY` already does. Better, drive it from the map by placeholder kind (`_ASSIGNMENT_KINDS`). Add a drift test like R7 for the card path: every spelling of every `KEY_ALTERNATIVES` entry, with a multi-word value.

### [m1] Minor - the target label route is only wired into `summary()`
Where: `src/hadavin_sdk/approvals/cards.py:85` (unchanged file, read from the base checkout) puts `plan.target.system` into the shadow card. `requests.py` and `app.py` carry `target_labels`.

What: this is the r1 M2 default, "masked with a display label". On the shadow card a host-name target becomes `<HOSTNAME_1>` with no way to show a label. The CHANGELOG says "or to `Approvals`", which suggests all cards.

Suggested fix: pass the labels to `render_shadow`, or say in the CHANGELOG and `build()` docstring that labels apply only to approval summaries.

### [m2] Minor - E3 decision to confirm
`defang_domains` leaves `<IPV4_1>@channel` unchanged inside a closed backtick fence (`gate.py` `defang_domains`, the `if i in code` skip; the decision is pinned in `test_q8b_card_text.py:218-225`). That matches the fence-verbatim rule of the sanitiser, and Slack sends no notification for code. I accept it as a stated decision. Note that the fence set is computed from the final text. Any later change that lets the redactor create a fence would make this a bypass, so the test should also assert that no fence appears that the input did not hold.

### [n1] Nit - glued forms of the redactor's key words are not covered by the drift test
`tests/test_q8b_glued_and_whole_values.py` R7 expands each key spelling as `key`, `db_key`, `key_x`. The redactor also masks glued prefixes (`dbpass=`, `mycredential=`, `usersession=`, `userauth=`). `sensitive()` accepts glued endings only for the list in `GLUED_ENDINGS`, and `credential`, `pass`, `auth` and `session` are whole words only. So `{"dbcredentials": "<multi word>"}` is not a credential key in the walk path. This is the same as main, so not a regression, but F4's drift promise is weaker than it reads. Add the glued spellings to R7, or state the limit in the `sensitive` docstring.

### [n2] Nit - the redactor-performance test cannot fail
`test_r1_the_guard_in_front_of_the_address_pattern_is_bounded` (`tests/test_q8b_glued_and_whole_values.py:112-118`) asserts under 30 seconds. A 100-fold slowdown of the address pattern would still pass. The new guard (`redact.py` `_NO_GLUED_KEY`: up to 255 lazy steps times about 27 alternatives per `@`, in a regex used by every caller) deserves a ratio test like the existing perf step. Use the ratio method of `ci.yml` "Performance of the redaction patterns", or tighten the bound.

### [n3] Nit - E1 glue tests use only `=`
`test_r1_*` build `lead + sep + key + "=" + value`. The guard and the key rule also accept `:` and a quoted key (`"password":"V"`). By reading `redact.py` `_NO_GLUED_KEY` they work, but no test fails if the colon branch is dropped. Add one row each for `:` and `"key":"v"`.

## Checked and found fine

- E1: early EMAIL pattern (`redact.py` `_NO_GLUED_KEY`) steps aside on a glued key. The unguarded `_EMAIL_DOMAIN` patterns run after the key rule (late EMAIL at the end of `PATTERNS`, `{255,}` pattern after the generic key rule). The value is masked first and the address is still masked. `<EMAIL_1>=<SECRET_1>` is the pinned output.
- E1 sweep: `KEY_ALTERNATIVES` is the old inline list in the same order, so the generic key rule is unchanged. Sequential `find()` (`redact.py:950-954`) confirms the ordering argument.
- E1: hosts glued to a key are not swallowed. `HOSTNAME` requires `\b` after the suffix, so `.corppassword`, `.internalpassword` and `.localpassword` do not match.
- Authorization rule: dropping `\b` and making the ARN guard case-insensitive only add masking. The cost is stated in the CHANGELOG.
- `PATTERNS.append` for the late EMAIL sits before `_BANK_CODES`, `_UUID_SHAPE` and `_CARD_SHAPE` are computed, so no pattern is shifted.
- F1: `_named` (`k1b/redaction.py:340-349`) collects every name-like key in any case and every `value` spelling. Named when any name is sensitive.
- F2: `LIMITS` (`redaction.py:44-63`) names the three as-written cases. These match `_walk` (`redaction.py:393-411`): timestamp before `_pair`, bool and None fall through, setting-key gate.
- E3, `kind: secret`: `_is_secret` casefolds (`redaction.py:352-355`).
- E3, non-map `data`: `_walk` with `secret_content` registers lists and texts, and masks numbers.
- F3: `_key_words` runs NFKC, `_FOLD` and casefold (`redaction.py:196-200`). The r6 test checks every spelling the old `re.IGNORECASE` accepted.
- F4: `accountkey`, `keydata`, `certdata` and `certificatedata` were added to `GLUED_ENDINGS`, and `sharedaccess` to `WORD_PAIRS`. R7 feeds every `KEY_ALTERNATIVES` spelling through `sensitive`.
- F5: one shared `_Budget` is taken per text across nested dicts and lists, and by credential values inside a Secret (`redaction.py:318`, `371`, `405`). A Secret under `spec` and one nested inside another Secret each get their own budget.
- No-exception rule of 1f: `sensitive` is a superset of main's rule. COUNT words are extended for `tokens` keys, which is stated.
- `_pair` acceptance (`redaction.py:272-284`) matches 1a and 1b: key prefix, quote check, fullmatch placeholders.
- `redact_for_people` is the only card caller of `redact_text`. `slack_channel.py` uses it, `producers.py` rows are updated, and `CHOKE_FAMILY` gains the new name.
- CHANGELOG claims about E1, the Secret `data` shape, `SENSITIVE_KEY` removal and the label route match the code, except B1's "cost" which understates the harm.

## Not checked

- I ran nothing: no tests, no mutants (`tests/q8b_mutants.py` rows for the r1 items not read in detail), no timing, no perf step.
- Whether `redact.py` changes conflict with PR77's rebase. Only the errata paragraph was read.
- Postgres tests, the unchanged parts of `gate.py`, and the other patterns of `redact.py` that run before the key rule (JWT, UUID, URLCRED, WEBHOOK, GCP and Azure resources) for a swallowed glued key. The r1 test leads cover URL, ARN, IPv4 and host only.
- The percent-encoded and entity-encoded multi-word rows of `test_r2_*`: the pinned outputs are taken from the test file, not reproduced.