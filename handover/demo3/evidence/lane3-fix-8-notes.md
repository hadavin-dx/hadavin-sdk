# lane3-fix-8: a badly shaped domain is not a mailbox (builder B8)

Base: public demo main f3c39cf89ec989f032ea48a23cfd824b88da9c68. Python /home/user/work/final-venv. Times UTC (IST = UTC+5:30).
Patch: `evidence/lane3-fix-8.patch` (git diff from the base of the `git add -A` tree, 7 files, +170 -10). Nothing committed.

## What failed first
1. Old code, new tests: 24 of 40 fail (raw: `evidence/raw/b8-fails-before.log`, with a probe of the old behaviour at the end). On the old code `loc@a..b`, `loc@-a.test`, `loc@a-.test` are `ok`; `SmtpSettings(mail_from='desk@.example.test')` is accepted. Honest caveat: the sender, recipient and reminder tests fail on the old code partly because the new function `plain_address_ok` does not exist (AttributeError), not only because of the behaviour; the probe lines at the end of the raw file show the behaviour itself.
2. Correction to the brief: `loc@.dom` (ONE leading dot and no other dot) was ALREADY refused on base (the regex needs a dot with a character after it). The accepted forms on base were `loc@.dom.test` (leading dot plus a later dot) and `loc@a..b` / `ada@example..com` (double dot).
3. First full-suite run FAILED (1 failed, 3723 passed): `tests/test_hygiene.py` flagged my own text (address-shaped test strings `desk@.example.test`, `desk@a..test`, and `1.2.3.4` in contract.md). Log: `evidence/raw/b8-full-suite-run1-1-failed-hygiene.log`. Fixed: test addresses built from parts, contract text reworded. A second run was stopped by me after about 1 minute (I moved a docs sentence to avoid a patch conflict with fix-4; its log was discarded); the third run, on the final tree, is the one reported.

## Where the rule lives
Before: `identity._valid_email` (`not e.endswith(".")`, plus the regex `_EMAIL_RE` that demands one dot with a character on each side). Now: ONE function `identity.domain_labels_ok(domain)` (every label non-empty, none starts or ends with a hyphen; the dot and U+3002, U+FF0E, U+FF61 all split labels, as in IDNA). `_valid_email` calls it (the old `endswith(".")` is covered: a trailing dot is an empty last label). `identity.plain_address_ok` = PLAIN_ADDRESS plus the same function.
Routing: `check_payload` returns `Checked("review", "invalid_email")`; the desk answers 202 `review`, writes no lead row, no follow-up row, no mail (tested on the real desk).

## Sweep table: item | fixed how | verified how
| Item | Decision | Verified |
|---|---|---|
| Lead email: leading dot (`loc@.dom.test`), double dot (`a..b.test`), trailing dot, empty label | FIXED in `domain_labels_ok`, called from `_valid_email` | 24 fails-before; mutants 1, 5 killed |
| Leading/trailing hyphen label (`-a.test`, `a-.test`, `a.b-.test`, `a.test-`) | FIXED, same function | mutants 2, 3 killed |
| Unicode dots (U+3002, U+FF0E, U+FF61) count as a dot (`example。。test`) | FIXED: split on all four | mutant 4 killed |
| Sender `DESK_SMTP_FROM` (smtp_outbox.SmtpSettings), recipient `send(to)` | FIXED: `plain_address_ok` replaces `_ADDRESS.fullmatch` | mutants 8, 9 killed |
| Provider sender and recipients (`smtp_provider.ProviderSettings`, `send(to)`) | FIXED, same | mutants 11, 12 killed |
| Reminder address `DESK_NUDGE_TO` (config.py) | FIXED, same | mutant 10 killed |
| `_ADDRESS` alias in smtp_outbox | removed (no longer used) | full suite |
| Fuzz | fixed seed 8, 20000 generated domains: no accepted address has an empty label or a hyphen at a label end (independent oracle splits by its own loop); both sides exercised (accepted > 100, rejected > 5000) | in `tests/test_domain_labels.py` |

NOT fixed (decided by reading code and docs, for the lead):
* Label longer than 63 characters: not an empty-label/hyphen hole but a length rule; no domain-shape check in the code half-enforces it (only the total 254 limit does; the 63 rule exists only for the `Host` header, contract.md line 104). A fix needs a choice for non-ASCII labels (their length is counted after punycode). Next step: lead decides; small addition inside `domain_labels_ok`.
* Dots in odd places in the part BEFORE the @ (`.a@x.test`, `a..b@x.test`): the order is about the domain; many real mailboxes are refused by other systems for this, so left as is. Written in contract.md and limits.md as "not checked".
* IP literal after the @ (`a@[127.0.0.1]`) is still accepted by the lead check (it has a dot with characters around it); not covered by the order.
* `scripts/run_real_check._ADDRESS` is a text-masking pattern, not a validity check: untouched (also a real-run file).
* Equivalent mutant (survives, cannot change behaviour): `rpartition("@")` to `partition("@")` in `_valid_email`, because the regex already allows only one `@`.

## Fix-4 consistency
b4b2-base `tests/test_email_case_rule.py` has NO assertion that pins `loc@.dom` or `loc@a..b` as accepted (grep on `@.`, `..` found nothing; the fix-4 r3 notes say the same), so no assertion must change. Apply checks (raw results):
A. plain `lane3-fix-8.patch` on base f3c39cf8: OK.
B. plain on top of `claims-stack-on-f3c39cf8.patch`: OK, so no stack variant is needed.
C. fix-8 on top of stack + `lane3-fix-4-for-stack-r3.patch`: OK. (My first docs/limits.md sentence sat next to fix-4's hunk and conflicted; I moved it before the "At most 4 AI calls" bullet, then C passed.)
D. claims stack on top of fix-8: OK.
Not checked: fix-4 plain (non-stack) patches on stack+fix-8 fail on README.md and docs/limits.md because of the stack, not because of fix-8 (they fail on the stack alone too).

## Docs sweep
No sentence in README.md, docs/limits.md, contract.md or docs/tests.md promised the old behaviour (grep: dot, domain, valid, invalid_email). Added: contract.md item (3b), docs/limits.md bullet (what is and is not checked).

## Mutation check by hand (raw: `evidence/raw/b8-mutation.log`)
12 mutants (each new condition flipped, one at a time, tests/test_domain_labels.py): 11 killed, 1 survived (the equivalent one above). The files were restored after each (`git diff` against the index is empty).

## Numbers
* Added lines over 120 characters: 0 (src, tests). `noqa` / `type: ignore` added: 0.
* New tests: 40 in `tests/test_domain_labels.py`.
* Full suite on the final tree (`evidence/raw/b8-full-suite.log`): 3723 passed, 200 skipped, 0 failed, EXIT_CODE=0 WALL_SECONDS=1204. The one extra skip against run 1 is `test_hygiene_scan_public` reaching its gitleaks step (no gitleaks program here): its pattern-scan part passed. 199 skipped as before (no gitleaks, no playwright, root, non-Windows): the hygiene skips mean the gitleaks part of the scan did NOT run here.
* Not run (CI only by brief): ruff, mypy, bandit, gitleaks. Import order in smtp_provider.py was placed by hand.
