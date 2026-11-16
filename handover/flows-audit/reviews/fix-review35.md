# Fix log, round 35 (security/money/redaction path, uncapped; static audit, nothing run except the five checks)

Fixed by: the fixer session. Only file edited besides this log: `reviews-of-core-patches/REVIEW.md`. Time: 2026-11-16 17:02 UTC / 22:32 IST. Inputs: `review-design-r34.md` (B1, M2-M9, minors 10-17) and `review-reader-r34.md` (F1-F6, minors). Reviewer words were treated as unverified: each cited line was opened before a decision.

## 1. Failures, uncertainty and what was NOT checked (first)

- NOTHING about Postgres, `ssh-keygen`, hardware keys or the `cryptography` library was run or read from a manual. Findings 7, 10, 11 and 14 rest on reviewer knowledge; REVIEW.md labels them UNVERIFIED and claims no run. Where a claim could not be confirmed (calling `cryptography` for hardware-key signatures) the option was DROPPED instead of asserted.
- Test totals (reader minor): reconciled by arithmetic plus one `git diff --stat`, NOT by a test run. The 692-item difference (10553 minus 9861) is explained by different trees (952 commits, 52 test files changed), but I did not collect the checkout's tests to confirm it is exactly the added tests. Written that way in REVIEW.md.
- The visibility of the remote repository was not checked (no network call); Minor 15 is a question for the studio head with the facts read (`handover/` tracked, no `.gitignore` entry, CLAUDE.md line 23 says "Public repository"). Not claimed public.
- The first dated actions (builder start 2026-11-17 UTC, 05:30 IST the same day) still have NO NAMED OWNER. I did not invent one. NEEDS LEAD: name the builder session; NEEDS STUDIO HEAD: name any human role (verifier person, deployer, rotation lead, CI reviewer, branch rewriter), or say he fills them himself.
- `patch-copies/DEAD-MAN-CHECK.md` STILL needs the heartbeat wording (the heartbeat carries the checked result and a counter, its own scoped secret). I did not edit it (another agent owns patch-copies). REVIEW.md says this in the liveness paragraph. NEEDS the patch-copies owner.
- The `holds` login and the hold table are PROPOSED BY THE AUDIT; there is no hold table in the source today (`hold_run_ids` is a client hook, `tick.py:203`). Labelled as a proposal used only if Decision 3 option (i) is chosen.
- Not run: no mutation or fuzz tests (static edit only). The class sweeps were done by grep and reading, not by a tool that proves completeness.

## 2. Finding by finding

| Finding | Result | What was done (REVIEW.md) |
|---|---|---|
| Design B1 (evidence not bound to the tests) | FIXED | Decision 27: third hash (T) with five parts (test files and command; required negative-test list in (B); environment; mutation check; the counting run started by a job the verifier person controls, assistant runs are trial only). Hold sentence, criterion (8) enforcement, criterion (9) EVIDENCE BINDING updated. |
| Design M2 (light profile skips checks) | FIXED | Light profile relaxes freshness only; still verifies (A), the signature on (B) and its minimum counter; process-kind list is part of (B). Negative test added. |
| Design M3 / reader F3 (verifier naming) | FIXED at the choke point | Glossary (line 12) defines "admission", "admission verifier", "chain checker", "checkpoint checker", hash (A) vs (B) vs (T). Login `verifier` renamed `chain-checker`; new `admission-reader` row. "verifier program" uses in the receiver row and the liveness paragraph reworded. Class sweep: every remaining "verifier" use means the admission verifier. |
| Design M4 (operator split) | FIXED, partly contested | Option (a) allowed only while reset is not gated; once gated, (b) is mandatory. Contested in part: (b) alone is not enough because both logins write the same row, so a database guard on `session_user` or a signed reset token plus a negative test was added. |
| Design M5 / reader F2 (identity without table row) | FIXED at the choke point | Login table: 13 names (12 logins while agent and tick share one), new rows `admission-reader`, `holds`, conditional `freezer` and `rotator-<secret class>`; `purge`, `drain`, `agent and tick` rows extended. Class rule: every identity has a row, rights, per-action reason, positive test, negative test and a criterion (9) entry; (9) is refused when one is missing. X-6.6a notes that purge, holds and freezer write only to `audit_outbox`. |
| Design M6 (holds vs 400-day ceilings) | FIXED | X-5.7 (iv) states ceilings ignore holds and holds are not retroactive (`tick.py:187-192`); visible choice folded into Decision 3 (no new number); hold-and-purge race test added; `purge` row gets hold-table SELECT and outbox INSERT, event first. |
| Design M7 (key set, tools) | FIXED | Next key revoke-only until promoted by a (B) signed with the current key; one tool path (`ssh-keygen -Y verify`, touch flag required); `cryptography` option dropped; four negative tests added. |
| Design M8 (client countersignature) | FIXED | Mandatory sixth part for pilot and production; no e-mail hash; client key pinned in (B) only after fingerprint confirmation by a separate channel, recorded in the note. Decision 26, ACCEPTANCE NOTE, Decision 27 all say the same. |
| Design M9 (one-person studio) | FIXED, partly contested | ONE-PERSON LIMIT added to the hold sentence: two-person checks are advisory when the roles are one person; an assistant session is never verifier person, deployer, rotation lead or CI reviewer. Contested: the first dated actions need no named verifier person (they are builder work); only the lead/head naming of their owner is open (section 1). |
| Design minor 10 | FIXED | Explicit environment allowlist; `python -I` from an entrypoint outside the install tree; names PYTHONHOME, PYTHONINSPECT, PYTHONPYCACHEPREFIX, PYTHONWARNINGS, LD_PRELOAD; negative test. |
| Design minor 11 | FIXED | Read-only install tree stops file changes, not in-memory patching by hostile hook code (`agent_loop.py:886`, `:901`, `:909`). |
| Design minor 12 | FIXED (patch-copies part NEEDS OTHER OWNER) | Heartbeat carries the checked result and a counter, own scoped secret, tick cover weak until Decision 8. |
| Design minor 13 | FIXED | Decision 21 rotator = secrets manager's scoped rotation; row, negative test, criterion (9) entry. |
| Design minor 14 | FIXED | Decision 12 mechanism is a trigger per X-6.5, not column grants; test added. |
| Design minor 15 | FIXED as a question | Decision 26 (1) is a question for the studio head with facts; no claim of public. |
| Design minor 16 | FIXED | Spool OS user to login map in (B), set by the deployer; quarantine test for an unmapped uid. |
| Design minor 17 | FIXED | Signing load up to about 14 signatures per client and release (estimate, not measured); carry-over list proposed by the audit, not decided. |
| Reader F1 | FIXED | X-5.3 now says it is sized once on Decision 29 and is not inside the "large" of (i). |
| Reader F4 | FIXED | Size scale defined once ("Size labels" bullet); labels corrected for Decisions 12, 13, 14 (two places) and 29 (two places), X-5.7. Decision 7 stays "large" (code part 3 to 5 days, deployer part has no figure) under the new scale; Decisions 3, 10, 11 already agree. |
| Reader F5 | FIXED | Least-privilege items 6 and 7 and the no-lost-messages rule for criterion (4) added; the table of which criteria a note can close is unchanged. |
| Reader F6 | FIXED, owner open | One date format, UTC with IST; every dated item marked "owner: not named yet". |
| Reader minors | FIXED | "build digest" = hash (A); X-2 part 1 and part 2 defined in the X-2 row; criterion (9) table cell reads "NO ON ITS OWN"; note parts listed once (re-lists in Decisions 26 and 23b replaced by pointers); header names round 35; History claim "dates and sizes aligned" marked wrong and corrected, Round 35 bullet added; superseded section carries a note about duplicate headings (`tools/check_refs.py` does not depend on headings); test totals reconciled (see section 1). Stale-target side finding: not a defect, REVIEW.md already says A-01 is deferred and C-01 extras cut. |
| Decision 23b (lead as rewriter) | FIXED | "himself, or another human he names; an assistant session, the lead included, is not proposed" (three places; proposed by the audit). |
| X-6.6e rating | CONTESTED | Stays Minor under the file's rating rule (a proposal, now consistent with the `freezer` row); the studio head may take the Major reading; no count changes. |

## 3. Counts (restated, unchanged)

28 rows (Major 4, Minor 13, Nit 11; PROPOSE FIX 25, DECLINE 3). 33 answers = 29 + 2 + 1 + 1. NO numbered decision was added; the new choices (holds vs ceilings, the client countersignature, is `handover/` published) sit inside Decisions 3 and 26. New proposals are labelled "proposed by the audit".

## 4. Raw output of the five checks (run in `handover/flows-audit`, 2026-11-16 17:02 UTC)

```
$ python3 -I reviews-of-core-patches/count_review.py reviews-of-core-patches/REVIEW.md
rows 28 ['C-1', ... 'X-6']
severity {'Nit': 11, 'Minor': 13, 'Major': 4}
decision {'DECLINE': 3, 'PROPOSE FIX': 25}
rc=0
$ python3 -I tools/check_refs.py
PASS 5171 references           rc=0
$ python3 -I tools/check_names.py
PASS 655 rows                  rc=0
$ python3 -I tools/check_secrets.py
PASS 0 hits in 2683 files      rc=0
$ ruff format --check .
831 files already formatted    rc=0
```

## 5. Needs lead or others

1. Lead: name the builder session for the two dated actions (start 2026-11-17 UTC, 05:30 IST the same day; reports by the end of 2026-11-19 UTC).
2. Studio head: fill or confirm the human roles (verifier person, deployer, rotation lead, CI reviewer, branch rewriter), or accept that the two-person checks are advisory; answer the question about `handover/` publication.
3. Owner of `patch-copies/`: put the heartbeat wording into `DEAD-MAN-CHECK.md`.
4. Next round: an independent reviewer should check the new login table rows against the class rule, and an evidence runner should run the Postgres statements the file marks UNVERIFIED.
