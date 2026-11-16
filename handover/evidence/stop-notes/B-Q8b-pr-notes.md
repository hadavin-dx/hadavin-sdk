# PR notes (draft): Q8b, two masking leaks

Branch `core/q8b-partial-mask-and-card-redaction`, built on origin/main 2a8c2aac. Draft only: the builder opens no pull
request. The other redaction pull request (PR77) lands first; this branch is then rebased by the lead and every proof
below is run again on that base.

Words used here. The *redactor* is the pattern-based masking code. A *placeholder* is what it writes in place of a value
(`<EMAIL_1>`). The *fixed mask* is the text `<SECRET_REDACTED>`. A *credential key* is a key whose name says its value is
a login secret. A *card* is the text a person reads in a chat channel before approving an action.

## What was wrong
1. Incident cases. A value under a credential key was accepted as "masked" as soon as the redactor had changed any part
   of it. A value with a space in it was shown as `<SECRET_1> horse battery staple`: the first word masked, the rest
   readable by the model.
2. Incident cases. A Kubernetes Secret in the only shape a loaded case file allows (its `data` under `spec`) was not
   recognised: its entries were shown as written (base64, readable by decoding), and the made-up database secret stayed
   readable in a log line.
3. Approval cards. The dots of domains were bracketed BEFORE the redactor looked at the text, so the redactor no longer
   saw an e-mail address or a host name: `contact bob.smith@example[.]com` was shown to the approver. Masking could also
   leave a bare domain outside code, and could create a mention (`<IPV4_1>@channel`).

## What changed
- `k1b/redaction.py`: the redactor's result is taken only when it is the key, `=` and nothing but placeholders; anything
  else becomes the fixed mask. One rule (`sensitive`) says which keys name a credential. A setting about a credential
  (`..._policy_enabled`, `token_expiry`) is shown only for a yes/no word, a number or a time. A Secret under `spec` is
  recognised; an entry of at least 8 characters that is not all digits or one lower-case word is also masked where it is
  repeated in the case (first 256 entries of one Secret).
- `approvals/channel.py`, `gate.py`, `slack_channel.py`: one function (`redact_for_people`) builds what a person reads:
  sanitise without bracketing, redact once, then the last step (`defang_domains`) brackets dots of domains outside code
  and rewrites mention words.
- `guard/producers.py`: two data rows name the new function.

## Visible changes for the approver (all in the CHANGELOG)
- A target system or an input shaped like a host name or an e-mail address is a placeholder on the card
  (`<HOSTNAME_1>`); the approver cannot read it there. Numbers are local to one card.
- A line whose only change is a masked identifier or a bracketed domain keeps its heading, quote or list marker.
- Dots in names after `/` are bracketed (`/var/log/app[.]log`).
- `@here`, `@channel`, `@everyone` right after a masked value read `at-here` (also inside inline code).
- Summaries stored before the upgrade keep their old text.

## Visible changes in incident cases
- More keys are masked: `PGPASSWORD`-style glued names, `pwd`, `session`, `auth`, `account_key`, `api_tokens`, env
  entries written `Name`/`Value` or `key`/`value`, numbers and lists under them. Cost: `auth_method`-like keys and env
  entries named `PWD` or `OLDPWD` are masked although they hold no secret.
- A non-secret entry of a Secret that has 8 or more characters and is not one lower-case word (`orders-svc`)
  disappears from the log lines the model reads.

## Built beyond the ticket's wording (each chosen because it masks more; reviewers please check)
- A mention word after a masked value INSIDE inline code (`` `10.20.30.40@channel` ``) was left as `@channel` by the
  ticket's rule, and cleaning that text a second time changed it. The mention rewrite of the last step now runs on the
  whole line (as the existing cleaning does for every mention), not only outside inline code. Dots are still bracketed
  only outside code.
- A Secret whose `data` / `stringData` is not a map (a malformed Secret) is masked whole with the fixed mask; before,
  its text went through the patterns only.
- Stub test S3 as worded in the ticket could not catch its mutant (M3); a second stub (the whole `key=value` answered as
  one placeholder) was added so it does.
- Mutant M12 as worded (only the length test removed) is not caught by the fixture of common words, because those
  words are also "one lower-case word"; the list has M12 (whole rule removed) and M12b (length test only, caught by a new
  6-character case in G7).

## Owner questions
1. A host-shaped target is now a placeholder on the card, so the approver cannot read which host it is. The ticket keeps
   the masking (least privilege) and tells integrators to name targets by a label (`orders-db`). Is that acceptable, or
   should the approver see the real target somewhere? Nothing in the code shows the unmasked target today.
2. The cost named above (keys such as `auth_method`, `PWD`, `OLDPWD` masked; long non-secret Secret entries masked in
   logs): accepted?

## What is NOT promised
- Masking is pattern based. Names in free text, customer or project names, ticket numbers and values in unusual formats
  are not caught.
- "Masked where it is repeated" has limits (the `LIMITS` text, printed in reports): not for values over 255 or under 4
  characters, numbers, values nested deeper under a credential key, values holding both kinds of quote mark, values with
  control or other special characters, values that contain something another pattern masks, and copies in another
  spelling (base64, capitals, wrapped over lines, hex). Each limit has a test marked as an expected failure; the
  follow-up is ticket Q8d (a sweep of registered secrets inside the redactor), due no later than 2026-11-25.
- Compared with main, two copies are now LESS masked, by the ticket's design (no fragment of a value is registered any
  more): the log copy of a value with both kinds of quote mark (main masked its first piece), and the copy of a value
  with an escape sequence written without that sequence (main masked the piece before it). Under its own key the value
  is fully masked in both cases; main showed part of it there.
- An address written with a wide dot inside a code fence or inside inline code is still shown (the redactor does not
  read the wide dot; that is in the other pull request's files).
- A mention word in the BODY of a closed backtick fence is left as written (a fence body is not changed).
- At most 256 entries of one Secret are masked where repeated; the total over many Secrets is not bounded here (Q8d).
- Whether a chat program makes a link of `a/evil.com` or `<IPV4_1>..evil.com` was not verified; both are bracketed.

## Evidence (builder's own; the lead's separate evidence runner and reviewers decide)
See the builder's report: fail-before run on a clean origin/main worktree, appendix measurements re-run, full suite,
mutant lists, lint, bandit, repository scan, gitleaks.
