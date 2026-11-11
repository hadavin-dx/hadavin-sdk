<!-- full hand-back report of sub-agent a40df0e2, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

Q8b RESULT REVIEW round 1, head be53718, mode REVIEW. Read-only; I ran nothing and traced by reading.

VERDICT: REVISE. Every ticket requirement I traced holds in the code. There are 0 Blockers, 2 Majors, 6 Minors and 3 Nits. Both Majors are about behaviour the ticket leaves open or does not cover, not about code that contradicts the ticket. M1 is the only finding on the secret/redaction path. It is evidence-based, and its cause is inferred from samples.

REQUIREMENTS CHECKED AGAINST THE CODE (all hold)

- **Acceptance rule 1a.** `redaction.py:225-237` and `:240-273` match the ticket.
  - The result must start with `<key>=`.
  - If a quote was added, the rest must start and end with it.
  - The remainder must fully match `(?:PLACEHOLDER)+`.
  - Otherwise it falls through to `f(value)` and `MASKED`.
  - At most 4 attempts per value, plus the final `f(value)`.
- **What is written to the redactor, 1b (`:198-222`).**
  - Plain characters are the allowlist U+0021-007E minus `; & , " '`.
  - Under a credential key that fits `_SAFE_KEY`, it tries `key=` and then `secret=`.
  - A value that is not plain is never written under its real key; it is quoted, and if it holds both quotes nothing is tried.
  - Empty or longer than 255 characters tries nothing.
  - A Secret entry under a non-credential key is tried only if it has 8 or more characters and is not all digits or one lower-case word.
  - Inside a Secret the last accepted spelling is returned.
- **`_walk` and `_walk_dict`, 1c and 1c-bis (`:285-339`).**
  - Lists and tuples pass `sens` as `secret_data`.
  - `known_secret` is passed on unchanged.
  - The env-entry value goes through `_walk` with `known_secret`.
  - `spec` of a Secret is looked into.
  - Entries from index 256 on get `known_secret=False`.
- **Timestamp exception 1d (`:326`).** It is checked before `_pair`, and the near misses are masked.
- **Key rule 1f (`:158-195`).**
  - There is no setting-word exception.
  - I compared main's regex: `pass`, `password`, `passwd`, `passphrase`, `secret`, `token`, `api[_-]?key`, `authorization`, `credentials?`, `private[_-]?key` and `bearer` are all still accepted. This is by reading, not the 200,000-key run.
  - The redactor's key words are all added.
  - `_setting_key` and `_setting_value` are fail-closed: a dict or list under a setting key is not a setting value, and the gate is skipped when `secret_data` is already true.
- **Domains and mentions on cards.**
  - `defang_domains` (`gate.py:266-278`) takes its fences from the final text.
  - It brackets outside code, uses `_ANY_NAME_DOT` and rewrites the mention.
  - It only adds brackets or changes single characters, so it cannot rejoin what the redactor masked.
- **Card paths.** I traced `clean` (the `FakeChannel` send and notify, `SlackChannel.notify`, `cards._card`, `requests.summary`) and the Slack `_blocks`. All use `redact_for_people`. `post_card` takes text already cleaned by `_card`. No other caller of `redact_text`, `sanitise_text` or `withhold_commands` feeds a card. The `producers.py` rows are correct.
- **`SENSITIVE_KEY` removal.** No user in the snapshot (`src`, `tests`, `demos`, `docs`). It remains only in the handover documents (`P1d-b.md`, `studio-notes/p1d-siblings.md`, the Q8b plan reviews), which are stale text only. Closed.
- **Single dependency and least privilege.** There are no new imports. `redaction.py` uses only the public `runmap.PLACEHOLDER`, `RunMap` and `redact_untrusted`. The tests reach `R._pair` and `R._setting_key`, which the ticket allows.

FINDINGS

**M1. Major. Card path: assignment values stay readable more often than on main.**

Evidence: `/home/user/hadavin-sdk/handover/evidence/Q8b/be53718/08-hostile.txt:477` against `08b-hostile-on-main.txt:510`. The property run reads "readable-in-assignment-or-both" as 87 on the branch against 38 on main, out of 3000.

Samples at lines 478-501 of the branch file point to one cause: the e-mail or host pattern now runs before the key word is read, and swallows a key glued to it.
- Input: `bob.smith@example.compassword="zqalpha43 delta54 india79"`, in the longer text of line 496 (a `password` + `<!channel>` prefix).
- Branch output: `<EMAIL_1>="zqalpha43 delta54 india79"`, so the whole value is readable.
- On main the sanitise step brackets the e-mail first (`example[.]compassword=`), so the redactor reads the key and masks the value.

Line 508 shows the same family as a non-idempotence. Input `=tokenevil.com<i></i>=password = zqgolf25 golf16saw zqgolf25 golf16` comes out of the first `clean()` with `zqgolf25 golf16` readable. The second `clean()` masks it. Not-idempotent is 3 of 3000 on the branch against 11 on main, which is better, but this sample is a leak on the first pass.

How realistic: the glued shapes are unusual. The delta is still a measured regression on the security path, and neither the CHANGELOG nor the LIMITS text says it.

Not verified: that all 49 extra cases are this one cause. I did not check the unglued rows individually.

Smallest fix inside the allowed files: state it as a limit in the CHANGELOG and the `LIMITS` text, and add a strict xfail test pointing at PR77/Q8d. A real fix belongs in the redactor, which is PR77's file. A candidate is making the e-mail pattern stop before a key word. Alternatively, `clean()` could run the redactor on the text with the dots bracketed as well as on the unbracketed text and take the more-masked result. That second option is more than a one-line change.

**M2. Major (design, not code). The approver cannot read the target on the card.**

`requests.py:41` puts `plan.target.system` through `clean`. `summary()` for target `db01.corp.internal` now yields `... on <HOSTNAME_1>. Inputs: {...}`. A host name is the commonest target form, so the card loses the main thing the approver is consenting to.

The ticket and the CHANGELOG state this and leave "the owner question with the lead". The workaround, naming targets by a label, puts the burden on integrators.

Before merge the lead must either decide this explicitly or exempt the template-built fixed fields (`agent_id`, `action_id`, `target.system`) from identifier masking while still masking `Inputs`. I did not check whether `agent_loop` restores values for the card command, as the ticket itself notes.

**m1. Minor. The 256-entry cap is bypassable.** `redaction.py:296-299` applies the cap to top-level entries only, but `known_secret` is passed down into nested dicts and lists (`:307`, `:336`).
- Scenario: `{"kind":"Secret","data":{"a":["v00000001", ... 100,000 strings]}}` registers every string. Cost grows quadratically; the ticket measured 26 s for 1,000 entries without the cap.
- Wording: the CHANGELOG sentence "At most 256 entries of one Secret are treated this way" is false for such a bundle.
- Fix: `known_secret = i < MAX_REGISTERED_ENTRIES and isinstance(vx, str)`. Add a test with a list inside `data`. G10 tests only 2,000 flat entries.

**m2. Minor. The wider key rule over-masks, and the stated cost list is incomplete.** CHANGELOG and docstring name only `auth_method`, `session_duration`, `PWD` and `OLDPWD`.
- `tokens` is masked unless the word before it is in the count list or the word after is `used` (`:179`), so `tokens_per_second`, `tokens_remaining`, `reasoning_tokens` and `cache_tokens` become `<SECRET_REDACTED>`. For example `{"reasoning_tokens": 812}` is masked.
- The word `session` alone also masks the real Kubernetes Service field `sessionAffinity: ClientIP`.
- This is not a leak. It is lost diagnostic information, and the claim "0 of main's accepted keys refused" says nothing about it. Add these examples to the cost sentence, or widen the exclusions (`per`, `remaining`, `limit`, `reasoning`).

**m3. Minor. `_named` (`:276-282`) looks at only the first of `name` and `key`.** The input `{"name":"web","key":"api_key","value":"..."}` (made up) is not recognised, so the value is shown. Fix: test every candidate field, and use the credential one.

**m4. Minor. LIMITS understates what the reader will see for the X8 case.** The branch run (`08-hostile.txt:22-24`) shows `saw hunter<SECRET_2>` for a second record, so `hunter` stays readable. "Not masked where repeated" suggests the copy is shown whole. The headline bug of this ticket is a half-masked value. Add "may be shown partly masked" for control characters.

**m5. Minor. Pre-upgrade stored summaries keep their e-mail.** Slack `_blocks` re-renders `req.summary` on every `chat.update`, and the redactor cannot read `bob.smith@example[.]com`. The ticket states this in point (e). It still means in-flight approvals show the address after the upgrade. At minimum add it to the CHANGELOG as an exposure and not only as a "visible change".

**m6. Minor. LIMITS is one dense paragraph for a non-technical reader** ("pattern", "Secret", "spelled the same way", "and the like"). The text is fixed by the ticket (1g), so ask for a rewrite with the content unchanged: short bullets, and a gloss that "Kubernetes Secret" means a stored credential record.

NITS
- `redaction.py:14` and `SCHEME` still say "every number" is kept, but numbers under a credential key are masked. This was already true on main.
- `_ANY_NAME_DOT` also brackets prose with no space after a full stop (`done.Next` becomes `done[.]Next`). Cosmetic.
- The oracle in `test_q8b_random.py:201-208` and `test_q8b_card_text.py:423-430` reuses `gate._closed_fences` and `gate._INLINE_CODE`. A wrong fence rule would pass its own test.

LIMITS X1-X9: honest apart from m4. X6 correctly names base64 of a plain `stringData` value. The "3 characters" row is milder than stated: in the A2 rows a 3-character value is masked as a standalone word, which is safe.

IDEMPOTENCE: `_last_step_line` and `defang_domains` look idempotent by reading. `[.]` is not re-bracketed because `_ANY_NAME_DOT` needs a letter, digit or `>` before the dot, and `_DOMAIN` needs `[\w-]+\.`. The mention rewrite leaves no `@`. I found no code-level counterexample. The branch hostile run shows 3 non-idempotent texts in 3000, all of the M1 family.

BEYOND THE TICKET (all acceptable)
- The mention rewrite runs on the whole line, inline code included. This matches `_clean_line`, and a mention is not code in either reader.
- A malformed Secret (`data` not a map) gets the fixed mask on every string and number (`:300-303`). Fail-closed, tested by the evidence runner [037-039]; those rows still leak a copy of the value elsewhere in the case ('horse'), which is the documented "nothing registered" behaviour.
- Removing `SENSITIVE_KEY` is fine; see above.

WHAT I DID NOT CHECK
- I executed no code, so I could not confirm any measured number (200,000 keys, A4 rows, P1, P2, N9) or the 87-versus-38 cause beyond reading the samples.
- I did not read appendix B and C (lines 685-933), the new test files in full, `tests/q8b_mutants.py` (the mutants' `old` strings), `ci.yml`, the Postgres tests, or the redactor internals in `guard/redact.py` (PR77's file).
- `evidence/Q8b/be53718/RESULTS.md` does not exist yet. I used `08-hostile.txt` and `08b-hostile-on-main.txt`; `02-full-pytest.log` had no match for pass/fail summary text, so I do not know the full-suite result.
- I did not check wide-dot, homoglyph or IPv6 spellings of hosts, or `agent_loop`'s restore of the real target for the executor.

Files: /home/user/build/snap/q8b-be53718/src/hadavin_sdk/k1b/redaction.py, /home/user/build/snap/q8b-be53718/src/hadavin_sdk/approvals/gate.py, /home/user/build/snap/q8b-be53718/src/hadavin_sdk/approvals/channel.py, /home/user/build/snap/q8b-be53718/src/hadavin_sdk/approvals/slack_channel.py, /home/user/build/snap/q8b-be53718/src/hadavin_sdk/approvals/requests.py, /home/user/hadavin-sdk/handover/evidence/Q8b/be53718/08-hostile.txt, /home/user/hadavin-sdk/handover/evidence/Q8b/be53718/08b-hostile-on-main.txt
