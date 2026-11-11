<!-- full hand-back report of sub-agent ace02d78, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

# Q8b plan review, round 1 (design critic) — verdict: NOT READY

I ran nothing (read-only). Every finding below is traced by reading the code at main 2a8c2aa; none is executed. The evidence runner should confirm each hostile input before the ticket is revised.

Short version: the F5 acceptance rule (1a) and the F6 order are sound for what reaches them. The ticket is not ready because the F5b closing cannot deliver what the CHANGELOG and test P1 promise, and because credential values still bypass `_pair` entirely through `_walk` and `sensitive()`.

Paths: ticket `/home/user/hadavin-sdk/handover/tickets/Q8b-partial-mask-and-card-redaction.md`; code under `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/`; author prototype `/home/user/build/q8b-author/protoQ8b/`.

## Blocker

**B1. F5b cannot be closed for a value that holds anything another pattern masks first (ticket 1b, 1c, N2, P1, CHANGELOG line 154).**
- Evidence: `guard/redact.py:919-923` runs every pattern in `find()` before `sweep()`. `redact.py:1029-1049` sweeps literal originals only in the segments between placeholders. The map stores the restored whole value (`redact.py:946-956`).
- Hostile input: `[{'token': 'bob.smith@example.com Zx9 tail'}, {'message': 'login with bob.smith@example.com Zx9 tail failed'}]`.
- Trace: under the key the quoted spelling gives one placeholder. In the message, EMAIL fires first and leaves `login with <EMAIL_1> Zx9 tail failed`; the whole original is no longer present literally, so ` Zx9 tail` stays readable.
- The same holds for the ticket's own N1 inputs `db01.corp.internal/Zx9 tailpart` and `AKIA... and the rest` when repeated in a second record.
- P1's generator includes e-mails, hosts and the example key, and its property covers "a second record that repeats the value". So P1 as written should fail on the branch, and the builder can only pass it by narrowing the generator.
- This cannot be fixed with the quoted spelling. It needs the sweep to handle registered secrets before the patterns (forbidden `redact.py`), or a second sweeper in k1b.
- Change to the ticket, choose one:
  - **(A, recommended)** Narrow the claim everywhere (1b, 1c, CHANGELOG, `LIMITS`) to "masked where repeated only if no part of the value is itself matched by another pattern". Split P1's second-record property into pattern-free values (must pass) and composite values (`xfail(strict=True)` naming Q8c). Q8c becomes "`runmap.remember` plus sweep of registered secrets before patterns", with a date.
  - **(B)** A k1b-local pre-pass in `redact_bundle.mask()` that splits each string around literal copies of values collected by `_pair` and joins with their placeholder or `MASKED`. It closes B1, the both-quotes case and the over-255 case in an allowed file, but it is a second sweep engine and needs its own review.

## Major

**M1. The choke point is one level too high: `sensitive()` decides whether `_pair` is reached at all, and it misses common credential keys (bug class, sibling search).**
- Evidence: `k1b/redaction.py:88-100`. The pattern needs a separator or string start before the keyword, has no `pwd`, and no plurals. Line 132 then calls `f(obj)` with no key.
- Hostile inputs, each shown whole (no pattern matches plain words):
  - `{'PGPASSWORD': 'correct horse battery staple'}`
  - `{'name': 'PGPASSWORD', 'value': 'hunter2secretXYZ'}`
  - `{'DBPassword': 'hunter2secretXYZ'}` (the camel split needs lower-then-upper)
  - `{'pwd': 'hunter2secretXYZ'}`, `{'secretkey': ...}`, `{'secrets': ...}`, `{'rootpassword': ...}`, `{'accessKey': ...}`
- The redactor's own key grammar (`redact.py:598-606`) is wider and unanchored. The two grammars have drifted.
- Ticket 1d/1e would rewrite the docstring to "never reaches the model, one exception (timestamp)", which would be false.
- Change: add Behaviour 1f. Widen `SENSITIVE_KEY` (unanchored left for `password|passwd|pwd|secret`, add `pwd`, plurals, `access[_-]?key`; keep `token` and `auth` anchored for `author` and `tokens_used`). Add a table test of at least the keys above plus the negatives `author`, `tokens_used`, `password_policy_enabled` (decide it).

**M2. Env-form and non-string values skip `_pair` and the mask.**
- Evidence: `k1b/redaction.py:141` requires `isinstance(v, str)`; otherwise line 146 passes the parent's `sens`, not `named`.
- Hostile inputs:
  - `{'name': 'DB_PASSWORD', 'value': 12345678}` returns the number.
  - `{'name': 'DB_PASSWORD', 'value': ['correct horse', 'x']}` returns both strings unmasked.
  - `{'Name': 'db_password', 'Value': 'correct horse battery staple'}` and `{'key': 'DB_PASSWORD', 'value': ...}` are not recognised (line 136 reads exact `"name"`; AWS parameter and tag shapes use these).
- Change: at line 141 route any `value` of a named entry through `_walk(v, f, str(name), True)`. Decide and test the `Name`/`Value` and `key`/`value` shapes, or list them in `LIMITS`.
- Bytes are not a route: bundles are strict JSON (`k1b/bundle.py:112`). The ticket should say so.

**M3. The fallback key is applied to the wrong set and in the wrong order (1b, 1c; prototype `redaction.py:123`).**
- (a) Credential keys that the redactor's quoted grammar does not know stay `MASKED` with no map entry, so F5b is open for them:
  - `{'authorization': 'correct horse battery staple'}`, also `bearer`, `passphrase`.
  - Any key with more than 20 characters after the keyword, or holding `/` or `(`.
- (b) `{'private_key': 'correct horse battery staple'}` and `privateKey`: only the generic pattern (`redact.py:598-614`) matches. It masks `correct` and plants that fragment, which N3 forbids.
- (c) Under a Secret, the own non-credential key is tried first and can plant a fragment: `{'kind': 'Secret', 'stringData': {'username': 'svc payments'}}` plants `svc` as NAME (`redact.py:438`); `user_id` plants a TENANT.
- Change: for a non-credential key under `known_secret`, try only `FALLBACK_KEY`. For a credential key, try the own key then `FALLBACK_KEY`. Add N2 cases for `authorization`, `passphrase`, `privateKey`, a long-suffix key, and N3 cases for `private_key` and Secret `username`.
- The claim "closes F5b for credential keys" is otherwise false.

**M4. "What is left open" is understated (1e, CHANGELOG line 154, Open decision 2; fix-dont-defer honesty).** Besides both quote marks and B1, these stay readable where repeated:
- Values over 255 characters (`redact.py:581`; the 256 fallback at 663-672 is for command-line flags only). Example: a service-account JSON or `.dockerconfigjson` under `stringData`. The generic pattern also plants the first word.
- Strings nested under a credential key with a non-credential own key, by the 1c decision: `{'secret': {'value': 'correct horse battery staple'}}`.
- Numbers under a credential key (line 133-134).
- Respelled copies: a multi-line `stringData` value repeated in the `kubectl.kubernetes.io/last-applied-configuration` annotation string is spelled with `\n` and `\"` and is not matched by the literal sweep; the same for copies with collapsed white space.
- Change: list every case in `LIMITS`, the `_pair` docstring and the CHANGELOG. Add one `xfail(strict=True)` test per case naming Q8c. Add the annotation case to N2, since the single-line case is closed by 1c.
- Nested values need a ruling. Mine: inherit registration. The house precedent is `redact.py:1210-1215` ("must never stay in clear ... handled by escalating"), and the value is already treated as secret under its key.

**M5. 1c is an unstated, evidence-destroying behaviour change, and contradicts its own argument.**
- Every Secret entry is registered as kind SECRET, which is swept as a substring from 4 characters (`redact.py:1209-1216`, 1046).
- Scenario: `{'kind': 'Secret', 'data': {'DB_NAME': 'b3JkZXJz'}}` plus a log line `'orders-api timeout'` gives `<SECRET_n>-api timeout`. `DB_USER`, `DB_HOST` and a port `5432` behave the same. On main these were `MASKED` under the key and nothing was planted.
- 1c rejects exactly this for `credentials.user`.
- Masking is the right default on this path, but the ticket must state it:
  - a CHANGELOG "Changed" line;
  - a pinned test (same placeholder under the key and in the log line; k1b tools still resolve `service`);
  - a before/after run of the recorded k1b replay scores, not only the 487 unit tests.

**M6. "Plain" is a denylist and P1's alphabet is too narrow (1b, P1; class-level-fixes asks for an allowlist).**
- Hostile input: `{'password': 'hunter\x1b[0m2secretXYZ'}`. It has no white space and no break character, so the unquoted spelling is tried. `strip_ansi` (`redact.py:825-838`) inserts a space, the result is `<SECRET_1> 2secretXYZ`, the value is `MASKED`, `hunter` is planted and the whole value is never registered.
- Change: plain means `re.fullmatch` on visible ASCII minus `; & , " '`; everything else goes quoted. Or always try the quoted spelling first.
- Widen the P1 generator: ESC sequences, `\x08`, `\x7f`, `%XX`, backslash escapes, `&#59;`, `< > = : | / @`, non-ASCII and full-width letters, zero-width characters, a look-alike `<SECRET_1>`, length over 256, composite values.
- Keep property (i) "placeholders only or fixed mask under the key" unconditional. Mark second-record failures that depend on sweep F3/F4 as strict xfail with the finding number.
- Replace the `_VALUE_BREAK == runmap._VALUE_END` test with a behavioural one (for each character, does `redact_untrusted('passwd=ab' + c + 'cd9x')` leave a tail). `_VALUE_END` (`runmap.py:421`) is a private name in a file another branch is rewriting, and the real grammar is `redact.py:614`.

**M7. Approver-facing consequence not analysed (Behaviour 2, "Behaviour changes a user can see").**
- `requests.py:39-43` and `cards.py:85` pass `plan.target.system`, `agent_id` and the inputs through `clean`.
- Scenario: a system named `billing-db.prod.corp` showed as `billing-db[.]prod[.]corp` on main and now reads `on <HOSTNAME_1>`. The person approves a target they cannot see.
- `clean` numbers from a local map (`channel.py:28`, `_seeded`), so the card's `<HOSTNAME_1>` need not be the run's `<HOSTNAME_1>`.
- This already happens for IPs and ARNs; the ticket widens it to hosts and e-mails.
- Change: state it in the ticket and CHANGELOG. Add a test pinning what `summary()` shows for a host-shaped `target.system`. Get the owner's decision on whether registry-sourced template fields are masked.

## Minor

- **m1 (gate.py step 3).** Folding wide dots after the redaction is itself a rewrite after the detector. A text that leaves inline code because a redaction ate a backtick can gain an ASCII e-mail address the redactor never read: ``'password=ab`cd bob.smith@example。com `x` y'``. It is no new disclosure (it was readable with the wide dot). The new docstring must say "brackets are added and wide dots folded". The stated wide-dot limit applies inside inline code too, not only inside a closed fence.
- **m2 (N6, P2(b)).** The oracle reuses `gate._DOMAIN`, whose look-behind refuses a start after `/` (`gate.py:112`). `'see db01.corp.internal/evil.com/p?d=1 now'` becomes `<HOSTNAME_1>/evil.com/p?d=1` and passes P2(b). Main has the same gap, and I did not verify whether a chat client links it. Add the case to N6 and decide. Use an oracle that does not share the implementation's regex.
- **m3.** The after-placeholder rule is not specified. The prototype uses `(<PH>)((?:\.[\w-]+)+)`, which also brackets `<UUID_1>.json`. Put the regex and that effect in the ticket.
- **m4 (N9, `channel.py:33-38`).** Do not leave "if it fails, then ...". Specify now: seed the joined pass with the first pass's map so its sweep masks every first-pass original.
- **m5.** The "changed line starts no block" guard (`gate.py:273-279`) no longer sees bracket-only or redaction-only changes. `'# APPROVED by sec@example.com'` stays a heading. This is no new capability (a heading without a domain already stays), but it is a visible change to list.
- **m6.** Requests created before the upgrade keep `bob.smith@example[.]com` in the stored `req.summary`; the redactor cannot read it in `_blocks`. State it in the CHANGELOG.
- **m7.** More `f()` calls per secret value count against `2 * MAX_BUNDLE_CHARS` (`redaction.py:182-186`). State the bound (at most 5 calls) and test a realistic large Secret.
- **m8.** The prototype drops the `known` flag through lists (`redaction.py:177-179`). Specify the behaviour.
- **m9.** The hard limit says "one registry row" but Behaviour 2 edits two places in `producers.py`. Docs that describe card text are not in the editable list; I did not check whether any exist.

## Rulings on the six questions

1. **F5 fix.** Rule 1a is sound and fails closed for everything that reaches `_pair`: a rewritten key, a decoded view or a pipe-joined pair of placeholders all fall to the fixed mask. Lists and nested dicts route correctly. The leaks are upstream (M1, M2). The whole-value mask is the right trade, at a cost: two different secrets both read `<SECRET_REDACTED>`, so "same or different credential" is lost; 1b reduces that.
2. **F5b.** The quoted spelling is sound only for pattern-free values of at most 255 characters without both quote marks, under a key the grammar knows or the fallback key. It is not right without the sweep (B1). Ship it narrowed, with strict xfails and a dated Q8c.
3. **F6 order.** Correct. Bracketing after the redaction cannot corrupt a placeholder (placeholders hold no dot, and `_DOMAIN` and `_NON_ASCII_HOST` labels cannot span `<` or `>`). It is idempotent. Judging code regions on the final text is what closes F6b, including when a multi-line quoted secret swallows a fence closer. Rejecting "redact, sanitise, redact" is right. The Slack sibling is covered by the shared function; `clean(withhold_commands(req.summary))` would be simpler and would need no new public name.
4. **producers.py rows and mutants.** Not scope creep. The rows are the registry doing its job if `redact_for_people` exists. The mutant list and CI step follow the existing `stage_mutants.py` step (`ci.yml:94`). Add mutants for M1-M3 and for "own key tried before the fallback key".
5. **Merge order.** The F1-F4/F7 pull request lands first: it carries the Blocker, owns the redactor, and Q8b's F5b glue and P1 depend on its sweep and view behaviour. Q8b can be built in parallel, then rebased. Its repro and fail-on-main proof must be re-run on the merge base, and the `gate.py` 332-340 flag threading redone. Ask the lead whether that builder also touches `approvals/channel.py`: the sweep's shared fix says "channel.clean call the same step".
6. **Open decisions.**
   - (1) Do 1b and 1c now, narrowed per B1, M3 and M4. The leak is live and the glue fails safe.
   - (2) Deferring both-quotes to Q8c is acceptable only with the full list from M4, strict xfails and a date, or take option B.
   - (3) Keep the timestamp exception. `_TS_RE` (`bundle.py:26-28`) is a full-match ASCII grammar, a value of that shape carries no secret, and expiry times are evidence. Add near-miss tests that must be masked (trailing space or newline, lower-case `z`, `+00:00`).

## Not checked

- No code, test, prototype or log was executed, and the author's logs and counts were not verified.
- I did not read `tests/test_k5_round12_fuzz.py`, `tests/warden_port/`, `tools.py`, `demos/` or `docs/`.
- Chat-client link behaviour and CWE titles are unverified.
- `parse_ts` was read only to its regex and docstring, not its range checks.
- The other branch's actual diff was not seen.
