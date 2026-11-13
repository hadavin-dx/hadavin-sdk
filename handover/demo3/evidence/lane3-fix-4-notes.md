# Lane 3 fix 4 (B4): email case rule, documents + pinning test (no code change)
Base: f3c39cf89ec989f032ea48a23cfd824b88da9c68. Python 3.12.3, PYTHONPATH=src. Made-up data (example.com).

## Failures and gaps first
* Finding reproduced (below). BUT the plain-words sentence given in the brief was too narrow and Patch B's obvious fix does not fully work:
  1. The same effect also hits other rare letters (97 letters in all where upper-then-lower does not return the letter; in the Latin range: `ſ` long s, `µ` micro sign, `ŉ`, `ǰ`, plus Greek and Armenian ones). I added "a few rarer letters, such as the long s `ſ`" to the sentence and the test pins `ſam` vs `SAM`.
  2. `casefold()` would fix `ß`/`STRASSE` but NOT `ı`/`ISTANBUL`: `'ı'.casefold() == 'ı'` (verified), so `ISTANBUL` would key to `istanbul`, `ıstanbul` stays different. Casefold alone is not the whole answer.
* **`git apply --check` CONFLICTS (not resolved): lane3-fix-4.patch does not apply after `claims-stack-on-f3c39cf8.patch`** (README.md hunk near line 103: the claims stack edits that region). It applies on bare f3c39cf8 and after lane3-fix-1-r2 + lane3-fix-2 (both on base). With claims + fix-1-r2 + fix-2-for-stack it conflicts the same way. Fix: re-cut the README hunk on top of the claims stack.
* Not run: the full test suite (only the files named below). ruff/mypy/bandit not run (owner rule).
* `schema.sql:39` comment ("trim + lower case") not touched (patch is documents + test only); consider "trim + Python lower()" later.

## 1. Verification on the real code (worktree /home/user/work/b4-base)
Keys from `normalise_email` and `check_payload` (b4-tmp/verify run; `.kind` of both is `ok`, so both are accepted):
```
'stra\xdfe@example.com' 'strasse@example.com' DIFFERENT ok ok
'\u0131stanbul@example.com' 'istanbul@example.com' DIFFERENT ok ok
'\u017fam@example.com' 'sam@example.com' DIFFERENT ok ok
'\xe9mile@example.com' '\xe9mile@example.com' SAME ok ok
'm\xfcller@example.com' 'm\xfcller@example.com' SAME ok ok
'\xf6zil@example.com' '\xf6zil@example.com' SAME ok ok
'fran\xe7ois@example.com' 'fran\xe7ois@example.com' SAME ok ok
'ada@example.com' 'ada@example.com' SAME ok ok
casefold of dotless i: '\u0131'  sharp s: ss
```
Real desk round (tests `test_real_desk_round_makes_two_leads`, real HTTP server on fakes): `straße` then `STRASSE`: 201 `new` + 201 `new`, 2 leads; `ıstanbul` then `ISTANBUL`: same. Reproduced; passes on base (it records the current behaviour).

## 2. The sentence (README.md "Same lead" definition, README "What is not claimed" list, docs/limits.md)
> Lower-casing is Python's `lower()`, not full case folding: an address with `ß` (sharp s) or `ı` (dotless i) written in capitals (`STRASSE`, `ISTANBUL`) is a different lead from the lower-case one (`straße`, `ıstanbul`), and both would be sent a follow-up (a few rarer letters, such as the long s `ſ`, behave the same way); ordinary letters (a-z, accented letters such as é) are not affected.
Claims checked: é, ü, ö, ç and a-z give one key (tests `test_ordinary_and_accented_letters_give_one_key`); `ß`, `ı`, `ſ` differ (above). README line 106 got a short pointer instead of the full sentence.
Diff of the documents (verbatim):
```
--- a/README.md
+++ b/README.md
-* **Lead**: a person who asked to be contacted. **Same lead** means the same email address, trimmed of spaces and lower-cased, nothing more.
+* **Lead**: a person who asked to be contacted. **Same lead** means the same email address, trimmed of spaces and lower-cased, nothing more. Lower-casing is Python's `lower()`, not full case folding: an address with `ß` (sharp s) or `ı` (dotless i) written in capitals (`STRASSE`, `ISTANBUL`) is a different lead from the lower-case one (`straße`, `ıstanbul`), and both would be sent a follow-up
-* The same person with two email addresses is two leads; two people sharing one address are one lead.
+* The same person with two email addresses is two leads; two people sharing one address are one lead. One more case: the same address in capitals is one lead, except for `ß` and `ı` (see the definition of **Same lead** above: `lower()`, not full case folding).
--- a/docs/limits.md
+++ b/docs/limits.md
+* Lower-casing is Python's `lower()`, not full case folding: an address with `ß` (sharp s) or `ı` (dotless i) written in capitals (`STRASSE`, `ISTANBUL`) is a different lead from the lower-case one (`straße`, `ıstanbul`), and both would be sent a follow-up (a few rarer letters, such as the long s `ſ`, behave the same way); ordinary letters (a-z, accented letters such as é) are not affected.
```

## 3. Pinning test: tests/test_email_case_rule.py (12 tests)
Asserts the real mapping (ß, ı, ſ pairs differ; é ü ö ç a-z same), the two real desk rounds, and that README.md and docs/limits.md contain `lower()`, `ß`, `ı`, `ſ`, `STRASSE`, `ISTANBUL`. If the code moves to case folding, the mapping tests fail and force the document change.
## 4. Proof
* Documents reverted to base: `2 failed, 10 passed` (the two document tests fail: "README.md must mention 'lower()'"). 
* Patched: `12 passed` (test file alone); `tests/test_email_case_rule.py tests/test_hygiene.py tests/test_portal_wording_and_masking.py`: `46 passed, 7 skipped` (skips are the repo's own optional-tool skips; not checked which). Earlier run of test_hygiene + test_input_edge_cases + test_desk_edge_cases + the new file (before the `ſ` addition): `93 passed, 4 skipped`.
## 5. Patch and apply checks
8af9bb267c390a00b59ac4913f934685dac1a484e29e5666476592cb48375c40  /home/user/hadavin-sdk/handover/demo3/evidence/lane3-fix-4.patch
* `git apply --check` on fresh f3c39cf8: clean. After claims stack: CONFLICT (README.md:103). After fix-1-r2 + fix-2 (base): clean. After claims + fix-1-r2 + fix-2-for-stack: CONFLICT (same hunk).

## 6. Patch B analysis (no code written): switch `normalise_email` to `casefold()`
* **What it fixes:** `ß`->`ss` (STRASSE merges), `ſ`->`s`, ligatures. **What it does not:** `ı` stays `ı` (casefold keeps it), so `ISTANBUL`/`ıstanbul` still differ. A full fix needs a second step (for example mapping `ı` to `i`, which is wrong for Turkish mailboxes where `I` and `ı` are different letters, so that merges two real mailboxes).
* **Stored keys:** `leads.email_key` has a unique index (`schema.sql:43`, `leads_email_key_uq`) and rows are write-once (trigger `leads_no_update`, `schema.sql:44`). Old rows keep their `lower()` key; new mail would be keyed by casefold, so an old lead `straße` and a new `STRASSE` would still be two leads until a migration re-keys. A migration must UPDATE keys, which the trigger refuses (needs a controlled drop/recreate of the trigger), and two stored leads that now collide would break the unique index: they need a person to merge or choose first, with follow-ups already sent. `db.py:51-59` lists the guarded objects, so a migration there is a schema-check change too (`scripts/check_schema.py`).
* **Where else the key is used:** `identity.py:130` (key), `:94` (length check on the key), `:83-91` (`_lower_keeps_ascii_apart`); `desk.py:1132,1224,1241` (lookup, insert); `desk.py:781-802,1602-1610` (key passed to CRM `set_fields` and the AI step); `crm_hubspot.py:378,398,445` has its OWN `strip().lower()` (matching the CRM contact by email; must change together or the CRM match breaks); `load_tools/check_invariants.py:156` reads `email_key` only (and the load generator's oracle, if it uses `lower()`, must follow); the n8n workflows and `demo_only` fakes show no `lower`/`casefold` use (grep above found none in n8n/load_tools/demo_only except `fakes` reading the key as a reply lookup).
* **Non-ASCII rejection rule (`identity.py:83-91`):** it refuses any non-ASCII character whose `lower()` contains an ASCII letter (Kelvin sign U+212A, U+0130). If it is moved to `casefold()`, it would also refuse `ß` (-> `ss`), `ſ` (-> `s`) and the ligatures, so such addresses would go to `review` instead of becoming leads (a visible behaviour change, and real German names would need a person). If it stays on `lower()` while the key uses `casefold()`, `straße@` and `strasse@` merge into one lead, which is the wanted merge but also joins two mailboxes that could in principle be different. The rule and the key must therefore change together, and the owner must decide which merges are acceptable.
* **Length:** `casefold()` can lengthen more (`ß` -> 2, `ﬃ` -> 3); the `<= 254` check at `:94` already uses the key, so it stays correct if it uses the new function.
* **Recommendation:** do NOT change the code now. Ship Patch A (the documents say the truth and the test pins it). The rare case costs one extra follow-up mail, not data loss. If the owner wants it fixed: use `casefold()` plus an explicit decision on `ı`, change `crm_hubspot.py` at the same time, add a migration that finds collisions first (report to a person), and run the identity fuzz (Q2) again. Risk of doing it: a wrong merge sends a follow-up to the wrong mailbox or silently drops one person's lead (worse than one duplicate mail); risk of not doing it: an occasional second mail to a person whose address contains ß/ı/ſ written in capitals. Decision for the lane lead and the owner.
