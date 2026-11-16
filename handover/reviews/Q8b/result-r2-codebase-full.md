Package: Q8b (partial masking and card redaction; redaction path)
Head: bcb2bfec179f18bd58de0df2b6669d94a9312472, round 2
Persona: codebase details (technical accuracy, reuse of core code, siblings of each bug class, tests that cannot fail)
Method: I read the snapshot files and DIFF.patch, the ticket and appendix (the appendix page was truncated at line 684, which covers A1 to B), and both round-1 reports. I could not run any code (Read/Grep/Glob only), so every finding below is by reading the lines. Each should be confirmed with the stated input before the fix is written.

## Findings

### [C1] Blocker - the glued-key fix covers only 40 characters of domain before the key; a longer domain still leaves the value readable
Where:
- `src/hadavin_sdk/guard/redact.py:266` (`_NO_GLUED_KEY` used in the first EMAIL pattern; the guard is defined at diff line ~491 and looks at up to 255 characters).
- The key rule at `redact.py:630`: `(?<![\w.\-])[\w.\-]{0,40}(?:KEY...)`.
- The late unguarded EMAIL pattern at `redact.py:721-726`.
- Test: `tests/test_q8b_glued_and_whole_values.py:30-34` (`LEADS`).

What:
- The guard lets the first address pattern step aside when a credential key sits anywhere within 255 domain characters after the `@`.
- Only the key rule can then mask the value. That rule can start only right after the `@` (the previous character must not be `[\w.\-]`), and its prefix is capped at 40 characters.
- If the domain text between the `@` and the key is longer than 40 characters, no pattern masks the value. The late EMAIL pattern then swallows `local@domain.compassword`, leaving `=VALUE`.

Why it matters (concrete input -> wrong output):
- Input: `bob@` + 41 `a` + `.com` + `password=` + a made-up value, no separator (or a separator that is removed, such as a zero-width space).
- Trace: the first EMAIL is skipped by the guard. The key rule cannot match (about 45 characters before `password`). The late EMAIL then gives `<EMAIL_1>=<value readable>`.
- This is the same output as the round-1 blocker.
- On main, the card text was bracketed before redaction (`...[.]compassword=V`). The `]` let the key rule start right at `com`, so the value was masked. This is therefore still a regression versus main for the card path, now only for long domains.
- A realistic domain also triggers it: `svc@some-long-subdomain.corp.internal.example.com` is already 45 characters.
- `LEADS` holds no domain over 40 characters. The `"a" * 300` lead is a long local part, not a long domain. The property test `test_r1_property_every_assignment_value...` therefore cannot find this, and neither can the mutants M24 and M26.

Suggested fix:
- Make the guard and the key rule agree: either raise the key rule's prefix bound for this case, or let the late address pass step aside the same way (do not consume the key when `KEY=` follows).
- A cleaner route is to mask `value` first. The guard could bound its look-ahead to 40 characters so that the first EMAIL is not skipped in cases the key rule cannot handle. Then the first pattern behaves as before when the key is out of the key rule's reach.
- Add LEADS and a property case with domains of 41, 100 and 255 characters before the key.

### [C2] Major - `_ASSIGNED` is a third hand-copied key list; the whole-value rule on a card misses keys the redactor masks
Where: `src/hadavin_sdk/approvals/channel.py:66-69` (`_ASSIGNED`).

What:
- The list is `password|passwd|pwd|passphrase|pass|secret|token|api[_-]?key|apikey|credential|auth`.
- The redactor's own list is public as `redact.KEY_ALTERNATIVES`. It adds `session`, `sessionid`, `jsessionid`, `phpsessid`, `sessid`, `private_key`, `access_key`, `account_key`, `shared_access_key`, `key_data`, `cert_data`, `connect.sid`.
- It also has `client_secret`, which `secret` happens to cover.
- The round-1 report named this class ("the key rule and the value rule drifted apart", F4) and the diff added `KEY_ALTERNATIVES` "so a test can feed every one of them". The new copy was not wired to it.

Why it matters (concrete input -> wrong output):
- `clean("session=correct horse battery staple")` -> `session=<SECRET_1> horse battery staple`. The same happens for `access_key=...`, `private_key=...`, `sessionid=...`.
- Reasoning: the redactor masks only up to the first space, and `_ASSIGNED` finds no listed word in `access_key=<SECRET_1>`, so the tail stays. The words are readable on the card.
- The case path (`sensitive`) masks the whole value for the same keys. So the "mask whole on cards, as in a bundle" promise (CHANGELOG, `whole_assignment_values` docstring) holds only for the listed keys.
- `_ASSIGNED` also accepts only `<SECRET_n>`. A value that starts with a recognised shape (`password=<APIKEY_1> more words`) keeps its tail. `_ASSIGNMENT_KINDS` right above (channel.py:47) lists five kinds, so the file has two answers to "which kinds are assignments".
- The tests (`test_r2_*`) use only `password` and `token`, and no mutant narrows `_ASSIGNED`.

Suggested fix:
- Build `_ASSIGNED` from `redact.KEY_ALTERNATIVES` (reuse, no copy).
- Extend the placeholder part to the `_ASSIGNMENT_KINDS`.
- Add a drift test over every spelling of every alternative, as `test_r7` does for `sensitive`. Add a mutant that narrows the key list.
- Alternatively, state in the CHANGELOG and docstring exactly which keys are covered.

### [C3] Major - the CHANGELOG states a test that does not exist
Where: `CHANGELOG.md` line 36 of the diff: "Masked where repeated, with limits (the same text as `k1b.redaction.LIMITS`, which a test compares with the code)."

What:
- No test reads `CHANGELOG.md` (grep of `tests/` for `CHANGELOG` finds only a docstring).
- `test_r5_every_exception_named_in_limits_is_what_the_walk_does` checks three phrases in `LIMITS` against `_walk`. It does not compare the CHANGELOG, and it does not compare the text as a whole.
- The CHANGELOG bullets are a reformatted copy of `LIMITS`. They can drift without any test failing.
- Round-1 item 3 asked for "one test that reads LIMITS and checks each named exception". That was done. The CHANGELOG sentence goes beyond it.

Suggested fix: either add a test that checks each CHANGELOG bullet's sentence is contained in `LIMITS` (or the reverse), or delete the claim.

### [C4] Minor - the label route for a target is not applied to every card
Where:
- `src/hadavin_sdk/approvals/cards.py:85` (`render_shadow`, base file, unchanged): `on {plan.target.system}`.
- `CHANGELOG.md` line 22: "pass `target_labels=...` ... the card then shows your label in place of the target system".

What:
- `target_labels` is applied in `requests.summary` only. The shadow card (`render_shadow`, called from `agent_loop.py:650`) goes through `clean()` and shows `<HOSTNAME_1>` for a host-shaped target. It has no label route.
- This is a sibling card path of the "approver cannot read the target" problem.

Suggested fix: pass the labels into `render_shadow`, or word the CHANGELOG as "the approval request card".

### [C5] Minor - tests that cannot fail in part
- `tests/test_q8b_glued_and_whole_values.py:326`: `R.sensitive("TOKEN" + "İ".lower()[:0])`. The expression `"İ".lower()[:0]` is the empty string, so this checks `sensitive("TOKEN")` and nothing about the dotted capital I. The loop above it does cover İ; this second half is dead weight and misleading.
- The earlier report's F10 (`P1` property (b) cannot fail alone) was not addressed in the files I looked at. I did not re-read `test_q8b_random.py` in full. Check before closing the round.

### [C6] Minor - card cost on the plan hash line
Where: `channel.py:74-90` (`whole_assignment_values`) and the template in `requests.py:41` (`... Expected: {plan.expected_outcome}. Plan <12 hex>.`).

What: `expected_outcome` is free text on the same line as the plan hash. A text such as `reset token=abc then restart` gives `token=<SECRET_1>`. The rest of the line is dropped, including `Plan <hash>.`.

Why it matters: the approver loses the plan fingerprint. This is a stated cost ("prose right after an unquoted credential value on the same line"), but the effect on the template line is not named. A model-written `expected_outcome` can trigger it on purpose.

Suggested fix: name this case in the docstring and CHANGELOG, or stop the tail at a sentence end (`. ` followed by a capital) or at a template boundary.

## Round-1 claims checked against the snapshot
- **F1 `_named` (name plus key):** fixed. `redaction.py:340-349` collects every name-like key in any case and every `value` spelling. Tests `test_r3_*` and mutant M32 pin it.
- **F2 LIMITS contradicts the code:** fixed in the text (`redaction.py:44-63` names the UTC time, true/false/null and setting exceptions). Test `test_r5` backs it. The CHANGELOG sentence is C3 above.
- **F3 case folding (long s, dotted and dotless i):** the fold works.
  - `redaction.py:199`: NFKC, then `.translate(_FOLD)`, then `.casefold()`.
  - I first suspected İ (U+0130) is decomposed by NFKC before the translate. It is not: NFKC recomposes I plus U+0307 back to U+0130, so the translate sees it. I withdraw that worry.
  - `test_r6` covers the equivalents through the older regex. Only the dead assertion at line 326 is weak (C5).
- **F4 GLUED_ENDINGS drift:** fixed. `accountkey`, `keydata`, `certdata`, `certificatedata` are added, and `test_r7` feeds every alternative of `KEY_ALTERNATIVES` through `sensitive`. This is the right pattern; C2 shows the new `_ASSIGNED` list did not follow it.
- **F5 256 cap and its wording:** fixed. `_Budget` counts nested texts and credential-key entries past the cap (`_pair:318`). Tests `test_r4_the_budget_*` pin both cases.
- **F6 docstring and CHANGELOG exception wording:** fixed (`_pair` docstring now names both exceptions; the module docstring says numbers are masked under a credential key).
- **F8 `SeededData(random.Random)` subclass:** not re-checked (random test file not read in full).
- **F12 mutant gaps:** the new rows M40-M45 cover the 8-character digit rule, the one-word rule, the token count words, the `>` dot alternative and the wide-dot fold. M35 is syntactically valid. The `old` strings I checked (M24, M26, M27, M31, M36, M44) match the built text of `redact.py`, `channel.py`, `gate.py` and `redaction.py`.
- **E1 blocker (glued key):** only partly fixed (C1).
- **E2 (card path half-masks a value with spaces):** fixed for the listed keys only (C2).
- **E3 items:**
  - lower-case `kind: secret`: fixed (`_is_secret`, `casefold`).
  - Secret `data` of any shape: fixed.
  - `<IPV4_1>@channel` in a closed fence: I did not find a decision recorded; `defang_domains` skips fence-body lines, so the mention stays inside a fence. The code comment at `gate.py:254` says the mention rewrite runs on lines that are not fence bodies. Consistent with the earlier "state it" option, but I did not see it stated in the CHANGELOG.
  - M5 row (`orders-api timeout`): handled as a decision in `test_r4_a_common_value_of_a_secret_stays_readable...` and in LIMITS.
- **Item 10 (target label):** added (`app.build`, `Approvals`, `summary`). Incomplete for the shadow card (C4).

## Checked and found fine
- `_pair` / `_accepted` acceptance rule (key prefix, quote check, full-match placeholders), the attempt count and the `known_secret` last-spelling rule.
- `sensitive()` is a superset of main's `SENSITIVE_KEY` by reading (words, camelCase cut first, trailing digits, NFKC fold); `_setting_key` gate is not applied under a credential parent or in a Secret.
- `_walk_dict` handles `spec` under a Secret and the `data` / `stringData` branch; `kind` case folding.
- `ARN_CHAR` parenthesis structure is balanced; the new guard has no nested quantifier (no ReDoS by reading: the lazy 255-character run with a 20-character suffix is bounded).
- `defang_domains` skips fence-body lines, adds only brackets and `at-` rewrites, and is idempotent by reading. `_ANY_NAME_DOT` and the mention step are as in the ticket.
- `redact_for_people` is the only caller of `runmap.redact_text` in `approvals/` (checked by grep over base plus snapshot); the Slack path uses it; `producers.py` rows and `CHOKE_FAMILY` match.
- Mutant file plumbing (fields, pinned ids, CI step) is as in the ticket.
- Authorization rule without `\b`: the CHANGELOG states the cost (`reauthorization=...` masked).

## Not checked
- Nothing was run: no pytest, ruff, mutants, perf step, Postgres tests.
- `tests/test_q8b_random.py` was not read in full (P1/P2/N9 oracle independence, F8 and F10 of round 1), nor `test_q8b_card_text.py` and `test_q8b_credential_keys.py` beyond greps for xfail, skip and weak asserts.
- Performance of the widened `ARN_CHAR` lookahead (about 28 alternatives, up to 40 offsets) against the CI perf step.
- A glued key behind other first-running patterns (JWT segments `[A-Za-z0-9_\-]{1,4096}` would also swallow a glued `password`): this exists on main and is not a regression, so I did not raise it.
- Whether PR77 touches the same lines of `redact.py` (the errata already lists the conflict).