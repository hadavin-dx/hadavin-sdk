<!-- full hand-back report of sub-agent a28e17be, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PLAN REVIEW, round 1, design critic. Ticket: /home/user/hadavin-sdk/handover/tickets/Q8a-2-neutral-callback-and-guard.md

VERDICT: NOT READY. No Blocker, 3 Major, 10 Minor. The receiver design (section 1) is sound and could be built as written; the Majors are in the guard (section 2) and the audit trigger (section 4). Nothing was executed: every statement below comes from reading and grep.

## Major

**M1. Section 2, identifier scan: names bound by a plain import are not scanned, and the "Not scanned" list does not say so.**
- The ticket scans only `ast.alias.asname`. `from hadavin_sdk.approvals import slack` binds the name `slack` through `alias.name`, and every later use is a read.
- Evidence on main: `/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/store/postgres.py:115` has `from hadavin_sdk.store import auth_aws` inside a neutral module. The ticket's "(3) to (6) add 0 hits" is true only because this binder is left out.
- Scenario: someone adds `from hadavin_sdk.approvals import slack` and `if d.channel == slack.NAME:` to `approvals/requests.py`. String scan, identifier scan and rule a (vendor SDKs only) all pass. This is the F6 class, a neutral module tied to one vendor, outside `receiver.py`.
- Other binders missed: `ast.ExceptHandler.name`, `ast.MatchAs.name`, `ast.MatchStar.name`, `ast.MatchMapping.rest`, type parameters (`ast.TypeVar.name`, Python 3.13).
- The ticket's reason for skipping call-site keywords ("scanned where defined") fails for `dict(aws_region=...)`, `SimpleNamespace(slack_token=...)` and any `**kwargs` callee.
- Proposed change:
  - Add to the scanned set: the bound name of every `ast.alias` (`asname`, else the first segment of `name` for `import`, or `name` for `from ... import`), the binders listed above, and `ast.keyword.arg`.
  - Have the EVIDENCE RUNNER measure the new hits on main. I expect `postgres.py:115 auth_aws`; keyword hits are unknown.
  - Give `auth_aws` an exact `IDENTIFIER_OK` entry ("lazy import of the declared VENDOR_HELPER for IAM database sign-in").
  - Change must-fail test 9 from five lines to the measured count, and add plants for each new binder.
  - If any binder is deliberately left out, name it in the guard docstring's stated limit.

**M2. Section 2, "One word list": the 15 words are not the repository's only vendor list, and the stated limit omits list completeness.**
- `/home/user/build/EV-P89-db0d9eb/tests/test_http_metadata.py:114-118` holds a wider list for the same purpose: the same 15 plus google, alibaba, oracle, amazon, microsoft, digitalocean, openstack.
- Evidence of a miss on main: `backends/table.py:185 GcsRetentionLockSettings` is a vendor-named class that neither `VENDOR_WORDS` nor `_TABLE_VENDOR_NAME` (guard:516-518) knows.
- Scenario: `sources/kinds.py:5` names CloudWatch and PagerDuty as the next kinds. `cloudwatch_namespace`, `google_project` or `"/google/callback"` in a neutral module passes both new scans.
- Proposed change:
  - Either add the 7 words plus `gcs`, `gcloud`, `amazon`, `cloudwatch`, `pagerduty` to `VENDOR_WORDS`, with the EVIDENCE RUNNER measuring the extra hits on main and each one getting a disposition.
  - Or keep 15 and add to the guard docstring and CHANGELOG: "the scan knows only these 15 words; a vendor not in the list is not seen", with a tracked follow-up.
  - Either way, add a test that the guard's list is a subset of the `test_http_metadata` list (or the reverse), so the two cannot drift.

**M3. Section 4, audit trigger: flagged honestly as a proposal, but it would land as a backdated fact with no fallback.**
- `decided` stays `date(2026, 10, 31)` while the trigger text is written on 2026-11-11 or later. The entry would then say the owner decided that trigger on 2026-10-31, which is false under CLAUDE.md "Honesty".
- guard:374 defines `"accepted"` as "a reasoned permanent exception". Under that definition `"none"` at guard:392 was a consistent answer. Section 3 of the ticket redefines "accepted" as "a reasoned exception that a named event ends" without editing guard:374, so one word gets two meanings.
- Scenario: the builder writes the sentence, and the owner answers "nothing ends it, the chain is ours". The new rule cannot express that, so the fix lands in a fix batch (cap 2) on a point known today.
- The sentence itself: `AuditSink` is a real seam (`audit/protocol.py:18`). But "a second audit kind" on that client event is a build commitment only the owner can make.
- Proposed change:
  - Get the owner's sentence before build, not before merge.
  - Edit the comment at guard:374 to the new meaning.
  - Record when the trigger was set: change `decided` to the confirmation date, or add a comment line on the entry "trigger set <date>, owner-confirmed (Q8a-2)".
  - Write down the fallback form if the owner wants no client-event trigger, for example "re-decided at review_by; no client event is expected to end it". Note that such a form is itself a placeholder, so the owner must accept that plainly.

## Minor

**m1. Section 2, new PATTERNS entry: the delimiter set misses query and assignment forms.**
- `"?provider=aws"`, `"kind=slack"`, `"/hook?slack"` and `"@slack"` are not matched.
- My approximate grep of main for `[=?&,@# ]word` inside quotes found only `config.py:98` (prose, already allowed) plus comments and docstrings.
- Proposed: add `=?&#@` to both delimiter classes and let the EVIDENCE RUNNER confirm 0 new hits. Leave space and comma out, since they pull in prose.

**m2. Section 2: "no string matches both" entries is false for compound strings.**
- `"slack:x/aws/y"` gives two problem lines. Harmless.
- Proposed: reword to "no single-word string matches both".

**m3. Section 2, I1 and I6 against I2: the same kind of name gets opposite dispositions.**
- I2 keeps `_AWS_READ_PREFIXES` because "a neutral name would be less true". That ALLOW is justified: `gate.py:595-598` applies the table only to the `aws` program, one of many recognised programs (`gate.py:540`), and `LITERAL_OK` already holds `'aws'` for this module.
- I1 renames `_SLACK` to `_ANGLE_CONTROL` although `gate.py:100` still says "Slack's own control syntax" and the regex is that vendor's grammar (`<!subteam^S1>`, `<url|text>`). After the rename no guard list records that `gate.py:102` is vendor-specific. The new name also blurs with `_HTML` at `gate.py:99`, which is also angle brackets.
- I6 (`_MOVING_ALIAS`) is less of a problem, because its regex keeps a `LITERAL_OK` entry.
- Proposed: either ALLOW `_SLACK` with a reason parallel to I2, or rename to `_CHAT_CONTROL` and say in the ticket that the record moves to the comment.
- All five renames are mechanically safe. Uses in both `/home/user/build/EV-P89-db0d9eb` and `/home/user/hadavin-sdk` (handover excluded) are exactly the lines the ticket lists: `gate.py:102, 254`; `defaults.py:130` and `sources/kubernetes.py:286`; `openai_compat.py:35, 47`; `tick.py:38, 304` and `README.md:40`; `test_p7_tick.py:18, 259, 263, 265, 273`.

**m4. Section 2, split rule bypasses.**
- A digit suffix (`slack2_url`, `aws1`) and glued capitals (`GCPKMS`) do not hit.
- Proposed: also test each part with trailing digits removed, except where the part is itself a listed word (`s3`). Add the plants, or add both forms to the stated limit.

**m5. Section 3: `neutral` read from the docstring line is brittle, but inert today.**
- Dry run 4.1c returns the same list for `neutral=True` and `False` with one kind, so a mutant `neutral=True` constant survives every proposed test.
- The line is written loosely in this repo: `sources/kinds.py:9` says "Neutral protocol: plain Python registry." A copied adapter for a proprietary API would carry the line and count as neutral.
- For `TABLE` the flag is hand-set and the docstring is only evidence; `neutral_problems` (guard:235) also checks the vendor set. The adapter drops both.
- `kind.settings.__module__` is the wrong module if a settings class is defined elsewhere, and `_source_docstring` raises for a module outside `src`.
- `KINDS` is a mutable module dict. `tests/test_k5_round6_contracts.py:38-42` calls `kinds.register`; today it leaves `KINDS` unchanged, but a later test that does not would make the guard order-dependent.
- Proposed:
  - `source_table(kinds=KINDS)` takes the registry as a parameter.
  - `neutral` is the docstring line AND the module not being in `VENDOR_MODULES`.
  - Add a plant test with a fake kind whose settings module lacks the line (expects `neutral` False) and a two-kind plant (expects "passes now").
  - Assert `set(KINDS) == {"kubernetes"}`, or snapshot, at the start of the coverage test.
- Adding `neutral: bool` to `SourceKind` is the sturdier design, but it edits src. It is acceptable to defer if the plants are added.

**m6. Section 3, the new `sources` exception.**
- It is a new "accepted" exception to an owner rule with `decided` 2026-11-11 and no owner mark. The trigger is real: K5-ITO is at `sources/kinds.py:7` and `README.md:42`.
- Proposed: add "OWNER-ACK: sources exception" to the PR line, next to the audit one.

**m7. Section 4, reason field.**
- No existing entry breaks. Reasons at guard:384, 391 and 398 are sentences; plants use `"r"`, `"t"` and `""`.
- Only the `audit` trigger `"none"` breaks, as intended.
- Placeholders such as "never", "na", "todo", "?" still pass. The limit is stated; adding those four costs nothing.

**m8. Section 1, the choke point.**
- A Protocol member plus a start check is right.
- Channel implementers: the only classes are `FakeChannel` and `SlackChannel` (grep for `def parse_decision` and `class \w*Chan` across src, tests and demos). No test double defines its own channel class.
- Callers of `serve()`: only `test_p7_tick.py:284`, with a `FakeChannel` (fixture line 45).
- Wrapping: `app.py:170-184` passes the channel through unwrapped.
- Collisions: an `Approvals` holds one channel (`requests.py:68`) and a receiver serves one path, so two kinds cannot collide.
- Security: signature and freshness logic do not move. `Approvals.receive` and `parse_decision` are untouched, and the order in `do_POST` is unchanged.
- "No alias" is safe: the only importer is `test_p7_tick.py`.
- Gap: `serve()` is the only host today, and `handle_action` does not know the path. The S11 production host would not pass through the check.
- Proposed:
  - Add one docstring sentence in `receiver.py`: "any other host must route by `callback_path(approvals)`".
  - State how `name` is read for the error message (`getattr(channel, "name", type(channel).__name__)`), so a channel missing both attributes still gets `ConfigError`.
  - Add `"/a\n"`, `"/a/"`, `"/-a"`, `"/a-"` and bytes `b"/a"` to test 4.

**m9. Tests, contract test.**
- The suite does build the Slack kind (`tests/contracts/kinds/channel_slack.py:14`), so ticket unknown 5 is resolved.
- Proposed: import `CALLBACK_PATH` inside the test body, so running the file against main fails one test instead of breaking collection.

**m10. Scope and order.**
- One pull request is fine.
- The ticket does not fix commit order. If the guard is committed first, the commit is red.
- Proposed order: (1) receiver, channel and their tests; (2) the renames; (3) the guard with its allow lists and the EXCEPTIONS edits. Every commit is then green.
- Also have the EVIDENCE RUNNER run the new guard file against the Q8a-1 branch head, since whichever merges second can turn main red.

## Dispositions judged sound
- **S2/S3, `guard/producers.py`:** a data row naming where text leaves. The entry is an exact pair and stale-checked.
- **S4/I4/I7/I9, `openai_compat`:** `TABLE` already marks it `neutral=True` (`table.py:529-535`), the module has a "Neutral protocol" line (`openai_compat.py:8`), and the module stays scanned.
- **`test_http_metadata.py:161-167`:** applying the new entry there cannot hit, because line 154 already enforces a stricter word-boundary check on the same strings.
- **`TABLE_VENDOR_NAMES`:** the 17 names equal the top-level names of `table.py` that `_TABLE_VENDOR_NAME` matches (checked against the def and class list).

## Not checked
- Nothing was run: no test, no regex, no `ast` behaviour.
- The author's prototype in `/home/user/build/q8a2-author/` was not read.
- `config.py` was read only at the line 98 grep hit; the ticket's quote of `config.py:95` is unverified.
- `defaults.py`, `runtime/tick.py` and `sources/kubernetes.py` beyond line 40 were seen only through grep lines.
- Not read: `tests/test_g4_parity.py`, `reviews/Q8/deps-audit.md`, `handover/TICKET-TEMPLATE.md`, `audit/chain.py:1-22`, the SQL migrations, `guard/runmap.py:215`.
- Main's non-src files (docs, demos, other tests) were checked through the db0d9eb tree and the working tree at `/home/user/hadavin-sdk`, not through an export of 2a8c2aa.
- The Q8a-1 branch was not looked at.
- The rung-table row on ready-made scanners was not researched.
- Whether the M1 widening adds hits beyond `postgres.py:115` is unmeasured.
