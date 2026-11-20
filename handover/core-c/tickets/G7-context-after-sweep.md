# G7: the table again after the sweep, to a capped fixed point (ORDERS 012 and 013, escalations E3 and E5)

Status: BUILT as ordered in ORDER 013 (one extra pass); FIX ROUND 2 (ORDER 020 MJ-B) replaced it by a capped fixed-point loop; FIX ROUND 3 (G7 result
review 2, fresh reviewers, 2026-11-20) made it a real fixed point; FIX ROUND 5 (G7 result review 4: caps replaced by a counted work limit, overlaps registered whole, the time statement restated; see ROUND 5 changes) came after FIX ROUND 4 (G7 result review 3) bounded the spelled-form scan, fixed its overlap rule and
the rollback ghost, made the first sweep carry the deadline, and made the time claims, the numbers and the docs say what the tests enforce. READ "Design as
built, ROUND 3" and then "ROUND 4 changes" FIRST. Every section marked ROUND 1 or ROUND 2 below is the record of an earlier design and is not the code.
FIX ROUND 6 (G7 result review 5) is the last: see "ROUND 6 changes" next; where a later section says otherwise, ROUND 6, then ROUND 5, then ROUND 4 win.
Evidence: evidence/G7-1.md (parts in order of work; "G7 fix round 6" is the last and holds the raw tails and the measurements). Reviews: tickets/G7-result-review-2.md to -5.md.

## ROUND 6 changes (G7 result review 5; supersede ROUND 5 where they differ)
- M-A (the honest margin): the suffix walk ran once per matched prefix (P x S). A grown cookie jar (newest cookie first, one signed suffix) needed 3.3 to 3.6 million units
  (83 to 90 percent of the limit) at 64 to 128 suffix characters; 275 lines with a 128-character suffix and copies at the cap are REFUSED on the round 5 scan (test fails before). Now: per first token ONE backward prefix
  trie (a node that ends a registered prefix holds its id) and ONE forward suffix trie of all suffixes (a terminal holds {prefix id: (placeholder, full)}): P + S + the entries looked up
  at terminals (the smaller side is iterated, each entry one unit). Same jar: 254,000 to 304,000 units. `SPELLED_MAX_WORK` stays 4,000,000 and is CHOSEN (13 times the largest honest shape measured), not measured; hostile grid 70 x 40 (2,800 forms) needs 6.3 million, refused after 0.53 s.
  Raw timing 0.09 to 0.23 microseconds per unit (evidence). Registry memory stated: one 200,000-character compound value is about 200,000 trie nodes, 37 MB.
- M-D (`redact()` and `bank_near`): NOT REPRODUCED (128 combinations of keyword spelling x bank-word spelling x order, through `redact`, `redact_many` and `redact_text`: no account left): the dry hits of the fold scan do not depend on the flag and the flag is set before any
  masking and before the direct patterns of the same `find`. Safety net kept: `redact` reads the text once more after a flip (as `redact_many` does), after a deadline check.
- M-E: `settle(..., known=)`: `redact` and `redact_many` read the map size BEFORE the first sweep, so an entry that sweep registered (a union) is growth for round 1 (every string is swept again). No leak was reproduced for it (the string that registers a union covers itself); the invariant is pinned by a sweep-call spy. Union registration counts one work unit per character and checks the deadline.
- M-B (a) raw overlap and M-C / E10 (b) cross-round overlap: both REPRODUCED with exact inputs and outputs (evidence g7r6_overlaps.py) and left as the stated limits, by the lead's order: the fixed-point loop (bound 4, NotSettled if not converged) gets its own ticket and plan review first. The two pins stay. ESCALATIONS.md E10 updated (OPEN).
- Wording: the flip at the last string IS a second pass over every string, each preceded by a check; the overrun is at most one string pass. `curl -u` 4.5 to 5.4 s (5.33 and 5.36 observed). `_spelled_at` holds substrings of the written form; the full value is the same object as in `mapping`.
- Dead code: `_spell`'s `first is None` (now `_place` passes the match), `_unspell`'s defensive returns (a registration is made whole; a test rolls back 60 random registrations and finds both registries empty), the "safety net" comment (the term check stays as defence in depth, pinned by a test that edits the map).
- Tests: ratio tests use a 4x larger honest case and 5 ms slack (a 5x regression fails); `_stepping_clock` patches the module attribute `R.time`; the generator test records its distribution with `record_property` (no print); the "about 5e6 units" claim is replaced by counted figures (6.3 million). Property corpus 1,836 (one jar input added).
- Mutants: evidence g7r6_mutants.py (M-E, M-D, union charge, unspell pruning). The round 5 scratch scripts (m2, m3, m4, measure_new, mutants and outputs) are committed under evidence/g7r5_scratch/ (path-bound to the old scratchpad; the outputs there are the round 5 record).
- SECURITY wording to add (owner): a hostile author can force the REFUSAL of a whole document (`SpelledWorkTooMuch`, `NotSettled`, a deadline refusal): fail closed, nothing shown, the legitimate rest of that document is lost; and the two open overlap limits.
- Counts: tests/test_redact_settle_loop.py 86 + 6 perf, test_redact_context_after_sweep.py 68 + 3 perf, test_redact_idempotent_property.py 1,842 (1,836 + 6), 0 perf.
- Still naming removed constants (not my lane): tickets/G4-P1c-redactor-gaps-v4.md:13 and :520 (SPELLED_MAX_OFFSETS / SPELLED_MAX_FORMS). For core-b: tests/test_runmap_enforce_map.py:368 (`test_m_new_1`) passes whether or not the sweep's deadline works.

## ROUND 5 changes (G7 result review 4; supersede the ROUND 4 items on caps, overlap and the time statement)
- Caps gone (design M1). The per-token caps on offsets (32) and forms (256) refused honest logs (a Cookie header preceded by other cookies of another length on every line;
  `password=<UUID_1>.<sig_n>` on 300 lines): reproduced, both raised `InputTooLarge("SpelledFormsTooMany")` before the change. The registry is now, per first token, a REVERSED
  prefix trie (what stood before the token) whose nodes hold the forward suffix trie (what stood after it): the cost of a token is the prefix that really matches plus the
  suffix walks of the prefixes that matched, independent of how many forms or prefix lengths are registered. The work of a scan (every step and every token = 1 unit) is counted and
  refused past `defaults.SPELLED_MAX_WORK` (4,000,000; `InputTooLarge("SpelledWorkTooMuch")`), read with the deadline every 1,024 units. The figure comes from measurement (evidence G7-1.md):
  corpora of 1,835 inputs: at most 1 offset and 1 form per first token; 2,000 generated compositions: 1 offset, 6 forms; honest worst built 243,000 units (16x headroom); hostile 5e6 units refused in 0.4 s.
  "0 to 2 in practice" in defaults.py was wrong for cookie lines and is gone.
- Overlap (design M2). A candidate that begins inside one already taken and ends beyond it fails closed: the whole run of overlapping candidates is registered on the spot as one compound
  entry (`xyz` + V + `ab`, `_place_union`, kind of the first form, same entry if the value is known) and replaced by its placeholder, so no part of it stays readable. "THE RULE, exactly" is no longer
  claimed as a safety property. WHAT REMAINS (stated in `_spelled_sweep`, pinned by test): an overlap complete only in a LATER round, when the first form was already swept to its
  placeholder before the second form was registered (`xyz<BEARER_1>`): the part of the later form that the earlier placeholder swallowed (its literal prefix or tail, `xyz`) stays readable.
  Same class, reached without spelled forms: a compound value inside another plain value (`xyz`+V next to V+tail registered as plain values) is cut by the longest-first sweep and leaves `xyz`
  (round 3 "compound inside a compound" limit, unchanged). Escalated: handover/core-c/ESCALATIONS.md.
- Time (design M3). `redact_many` re-reads only strings 0..n after a `bank_near` flip at string n, each after a deadline check. The restated worst case: for one `redact`/`redact_many` call
  budget + the pass in progress + one sweep; for `redact_text` (a series of calls over the views against one absolute deadline) budget + one pass + one sweep + 0.5 s per view. `redact_text` has only the
  CPU clock of the thread; a wall-clock guard at the call is core-b's job (listed below). Settle and module docstrings mention the flip (a flip in the last round is NotSettled: no round read the strings since).
  The segment check is the first free segment, then every 32nd (was `i % 64 == 0`, which read no clock for a text that starts with a placeholder); pinned by a stepping clock.
- Tests: codebase M1 (T4 at the real budget is "refused or redacted, within budget + 2 units + 0.5"; a `scaled` budget of 1.5 x the measured run must redact; the 0.5 s case kept), M2 (`def`, not lambda),
  M3 (the at-cap scan is a ratio to the same sweep without forms, measured 1.1 to 1.35x), nits N1 to N7, N9 (see evidence G7-1.md, "G7 fix round 5": fail-before runs, mutants, raw tails).
  N2: the one-off parity check of the moved builders was run (rows equal) and the parity test deleted. Design nit 4 (forged tokens consuming a cap) is moot: no cap by count. Design nit 6 (an honest 5-pass composition) SKIPPED: none found (the reference loop needs 5 passes on 5 of 2,000 compositions, but the settle loop converges in at most 3 rounds on all of them).

## For core-b (round 5; not done here, other lanes)
- Wall-clock guard at the callers of `redact_text`/`redact_untrusted` (tool-result path, document path): `redact_text` has only the CPU clock; a thread that waits on the GIL, a lock or I/O does not advance it.
- `agent_loop.py` 416-420: the label `document_too_large` is used for any `InputTooLarge`, which is now also `SpelledWorkTooMuch` and a deadline refusal; give each its own label or a neutral one.
- `evals.py` 64-70: "inputs are limited to N characters" is said for `NotSettled`, `SpelledWorkTooMuch` and a deadline refusal too; say what was refused.
- `k1b/replay.py` 158: any `RedactionError` from `redact_bundle` reaches the BaseException handler at 273, so ONE hostile case file aborts the whole replay (true for `InputTooLarge` already); catch it per case.
- Check (nit 5 of design review): no caller passes `_sweep_copies=False` except the tests (grep found only redact.py and tests/test_redact_context_after_sweep.py).

## ROUND 4 changes (supersede the same items of "Design as built, ROUND 3" below; the Spelled forms bullet, the overlap rule and the `curl -u` figures are SUPERSEDED by ROUND 5 and 6)
- Deadline (was item 7): `redact()` and `redact_many()` pass the call's deadline into the FIRST sweep too; `settle` checks it before every round and passes it
  into every sweep of a round. Each sweep checks it in `_build` (every 512th value), every 32nd free segment (when the map holds a value), before each value replaced and every 1,024th unit of
  work of the spelled-form scan (a token of the text, with or without a form, or a step of a trie walk). NOT checked: a pattern pass (`find`) and the loop over the
  strings of one round. THE BOUND the tests enforce (T4): budget + twice the measured unit (one pass and one sweep of the biggest text) + 0.5 s; the claim is
  smaller: the pass in progress when the budget is crossed (pass 1 over every string, or the pass of a round) plus one `str.replace` or finder pass of a sweep. A
  `redact()` or `redact_many()` with no `_deadline` has no total bound (the fold scan restarts a fresh 6 s allowance on every `find`; stated in `_fold_scan`).
  The segment check is made only when the map holds a value to look for (no value, no work to bound): a spent deadline still returns a text that needs nothing, as before,
  and tests/test_redact_fold_budget.py, which counts the clock reads of a call, is unchanged.
- The numbers have ONE source: defaults.py (unit timings, the 25 percent statement, the Windows figure) and the raw tail in evidence G7-1.md ("G7 fix round 4"). This
  ticket does not repeat them. In short: on the Linux test machine `curl -u ` at the cap costs 4.5 to 5.3 s of the 6.0 s budget, so a machine about 25 percent slower (14 percent at the slow end)
  REFUSES that text (InputTooLarge, fail closed; a legitimate 262 KB document of that shape is lost); the Windows laptop figure of 7.2 s (2026-11-02, before the
  deadline) is OVER the budget: that machine would refuse it too.
- Gate clocks (was "the gate converts its monotonic deadline"; false): `runmap.EnforceBudget` keeps TWO clocks and converts neither. A `thread_time` deadline
  (`cpu_deadline`) is passed INTO `_Redactor.sweep` and the held-back sweeps and checked inside them; a monotonic wall deadline is read only by `check()` (every
  64th held-back value, after each sweep), together with the CPU one.
- Spelled forms (was item 8): the scan costs tokens x offsets under that token x trie depth, NOT "independent of the number of forms" (it is independent of the
  forms under OTHER tokens). Two caps in defaults.py bound it per first token: `SPELLED_MAX_OFFSETS` 32 distinct offsets and `SPELLED_MAX_FORMS` 256 forms; a
  registration past either is refused (InputTooLarge), before anything is stored. The deadline is checked per token (before the "no form" skip) and every 1,024
  walk steps.
- Overlap rule, exactly: every full match is a candidate (start, end); at one start the longest; taken leftmost first; a candidate that starts inside one already taken
  is skipped. (Before: the first matching offset won; `xyz<SECRET_1>ab` with forms `<SECRET_1>ab` and `xyz<SECRET_1>` left `xyz` readable. Now `<BEARER_2>ab`.)
- `_rollback` deletes the `_spelled` entry of a rolled-back placeholder (`_unspell`; the journal holds the placeholder). The `mapping.get(placeholder) == full` check stays
  as a safety net. The same-value reissue with another meaning of the form's own token is a test (it failed before).
- `redact_many` (and `settle`) read every string again when `bank_near` flips while a string is read (the fold scan sets it from a FOLDED view): an account in an earlier
  string was left readable (`acct 12345678 paid` then a full-width `BSB 062-000`); the same two strings in the other order masked it.
- `_decide`'s rule for a value of own tokens is `_OWN_OUTPUT` (not `_ESCAPED_LOOKALIKE`, a name that is gone). STATED LIMIT, pinned by a test: a SECRET value made ONLY of own-label tokens
  (`password=<EMAIL_1> host`-shaped: token runs separated by space, tab, `;` or `,`, or a cut-off opening `<SEC`, `<SECRET_`) is left unmasked and gets no map entry.
- redact.py module docstring: there is NO second independent pass on what leaves; the model gate replaces the values the run's map holds (`runmap.enforce_map`) and runs no pattern.
- The three builders of the p1c inputs moved to tests/p1c_builders.py (the property test no longer executes an evidence file; the parity test was deleted in round 5: SUPERSEDED).
The first design (context patterns only, bounded rounds) is GONE from the code.

## Design as built, ROUND 3 (supersedes every other design section of this ticket)
`_Redactor.settle(originals, swept)` (guard/redact.py), called by `redact()` and `redact_many()` after pattern pass 1 (`find`) and sweep 1:
1. `todo` = the strings that pass 1 or sweep 1 changed.
2. A ROUND: check the call's deadline; the whole table over every string of `todo`; if that found a NEW value (the map grew) sweep EVERY string
   (the value's other copies go), else sweep only the strings the table changed (a placeholder written beside text can complete a spelled form).
   The next `todo` is the UNION of the strings the table changed and the strings the sweep changed in that round (round 2 had only the sweep's: a
   string the table rewrote and the sweep left alone was never read again, and the loop ended on "the map did not grow", not on "no text changed").
3. The loop ENDS on the first round that changes no text (no map growth is possible then). It is a fixed point of "table, then sweep" over the call's
   strings, not "the map stopped growing".
4. ACCEPTANCE RULE, exactly: the call is settled when some round r, 1 <= r <= `_SETTLE_ROUNDS` (4), changes no text. A chain whose last change is made
   in round 3 is accepted (round 4 confirms). A chain that still changes a text in round 4 is REFUSED: `RedactionError("NotSettled")`, nothing shown,
   because no round has read that text since. (Round 2 coded "a fourth growing round is accepted if its sweep changes nothing"; that is gone.)
5. The cap is a FAIL-CLOSED MARGIN, not a derived bound. Measured depth (tests/test_redact_settle_loop.py prints it; the real run is the raw tail in evidence
   G7-1.md, "G7 fix round 4", the ONE source of these numbers): over the test's 2,000 generated compositions of 4 to 8 lines (half from a pre-seeded run map; seed
   20261121) the rounds run were 1 round 156, 2 rounds 1,715, 3 rounds 129, none more. The maximum, 3, is pinned in the test (`MAX_ROUNDS_SEEN`). The reference
   loop (every string re-read every pass), by the pass that LAST changed something (exact shares): 3rd 249 (12.5%), 4th 73 (3.65%), 5th 5 (0.25%); cumulative (the
   test's counters, "a third pass or more"): 327 (16.4%), "a fourth or more" 78 (3.9%). Both are in the table; the 12 / 3.7 / 0.2 percent of the round 3 text were the exact
   shares of an 8,000-input scratch run that is not in the repo. The real chain of three takes 3 rounds (two that change, one that confirms). No
   natural chain of 4 rounds was found (generated, a 20,000-input random search over 21 bank/secret lines, hand search), so the cap stays at 4 (one round
   of headroom); the tests for exactly 4 rounds (settled) and 5 rounds (refused) use a pass that changes its text for exactly that many rounds (a stub of
   `find` only; the real cap, never patched): an off-by-one in the loop (3 or 5 rounds) fails them. A chain planted on purpose that needs 5 rounds
   forces a refusal: a whole document or tool result is lost (availability), never a leak. That is the stated price of the margin.
6. Callers on `NotSettled`: it is a `RedactionError` and every caller already treats that as "nothing is shown". `runmap.redact_text` now re-raises a
   RedactionError as it is, so the text `NotSettled` reaches the caller's log (before: `RedactionError("RedactionError")`). The DOCUMENT path
   (agent_loop, the trigger document) abstains as "redaction failed", not as "too large"; a tool result is refused with the same reason as any
   redaction failure; a deadline `InputTooLarge` is a different subclass and keeps its own reason. A document planted to need 5 rounds therefore
   makes the run abstain: that is the intended fail-closed behaviour.
7. Deadline (see "ROUND 4 changes" for the final wording): `settle` checks the call's deadline before every round, and passes it into every sweep of a round and
   (through them) into `_build` (`InputTooLarge`, never a skipped pass); since round 4 the first sweep carries it too. The deadline is `time.thread_time()` based (CPU
   time of the creating thread) and valid only in that thread. It is CPU time, not a wall bound (GIL waits and blocked time do not advance it): a caller that needs a
   wall-clock bound adds its own guard. The bound, the unit timings, the 25 percent statement and the Windows figure are in defaults.py (one source). The gate's two clocks
   are described in "ROUND 4 changes". T4 asserts: at the cap with a planted chain of three, redacted under the real budget and REFUSED under a budget of 0.5 s, each within
   budget + twice the measured unit + 0.5 s.
8. Compound tail (dz-2, round 3 M3/M4): when `_place` stores a compound SECRET entry whose written form held placeholders (`<SECRET_1>xy`), that
   form is registered under the FIRST placeholder token it contains, with (placeholder, full value) at the end of a character trie. `sweep` looks the
   placeholder tokens of the text up and walks the trie: cost tokens x offsets under that token x trie depth, capped per token (ROUND 4 changes), not entries x text
   (the old loop searched every form in the whole text on every sweep: 5,000 forms in 250,000 characters 0.17 s per sweep, up to 5 sweeps per call). A rolled-back
   registration deletes its form (round 4); an entry whose placeholder no longer maps to its full value is still ignored when read, so a ghost never writes a wrong
   placeholder that would restore to the wrong value (round 3 M3). Label change, noted (design N3): honest text spelled like a swept compound (`<SECRET_1>xy`) is
   relabelled with the compound's placeholder; the restore round trip is exact, only the label differs.
9. Cost (measured, evidence G7-1.md round 3): a clean text 1 pass 1 sweep; one planted secret 2 passes 1 sweep (unchanged); the chain of three 4 passes
   (one more than round 2: the confirming round over the one string it changed) and 3 sweeps. A string that the table rewrote in the last changing
   round is read once more: that is the price of ending on "no text changed". Texts that need no more passes pay nothing extra.
Fixed by the loop: the chain of three (`password=V`, `BSB: <code>V`, `paid <code>/<account>`) and the compound tail (BEARER up to 7 characters, BASIC /
authorization / `"auth":` about 3, `sig=` up to 11).

## Limits that remain after round 3
- A chain that needs a changing round 4 (5 rounds with the confirming one) is REFUSED, not masked. No natural chain found needs more than 3 rounds.
- NOT REPRODUCED (round 3 M1): a concrete string that round 2 left readable because it ended on map growth. 6,000 + 8,000 + 4,000 generated and
  corpus-mixed compositions gave identical results on the round 2 and round 3 loops, and a fixed-point check of every output (`sweep(find(t)) == t`) was
  clean on both. The union rule is kept as the safety net, and tested with a pass that rewrites a text without growing the map (the stub fails on the round 2 loop).
- Boundary class, fail safe (pinned in tests/test_redact_settle_loop.py): a boundary pattern (SSN, PHONE, EMAIL, IBAN, UUID, IPV4, APIKEY) can match where
  pass 1 saw a word character and the sweep then left a placeholder: `password=hunter` then `ref hunter123-45-6789` gives `ref <SECRET_1><SSN_1>`.
  More is masked, never less.
- Compounds inside compounds: a secret that contains a known compound plus more (`V+xq` known, then a `sig=` value `V+xq+xxqv` under 16 characters after the
  sweep) keeps the part after the known compound readable (the generator avoids it by giving every tail a different first letter). Planted text only.
- The sweep's own rule for short or common values (under 3 characters; all-digit under 6; common words; an identifier where a letter or digit touches it) is unchanged.
- A secret that no pattern matches and no known value contains is not found (the patterns are the control).
- The time bound is stated once, in defaults.py and "ROUND 4 changes": CPU time of one thread; a slow machine refuses the hostile text, it never shows it.
- A hostile text past the WORK limit (`SPELLED_MAX_WORK`, 4,000,000 units; no cap by offsets or forms since round 5) is REFUSED (`InputTooLarge("SpelledWorkTooMuch")`), not masked: availability, never a leak. (Limits that remain after round 3: the caps of 32 offsets and 256 forms are GONE.)
- A SECRET value of own-label tokens only is left unmasked (stated limit, `_OWN_OUTPUT`).
- The test generator and the reference loop cover the shapes listed in the evidence, not every chain. The reference shares `find` and `sweep` with the code.

## Guards that replaced the deleted test (round 3 M7, N2)
Round 2 deleted `test_the_patterns_that_name_a_placeholder_are_still_these_two`. It guarded something real: the fold scan (`_mask_in_place`)
takes a full round for the labels in `_CONTEXT_LABELS` (`{"BANKACCT", "BANKCODE"}`). Now in tests/test_redact_context_after_sweep.py:
(a) every pattern whose regex source reads a placeholder shape is known (`BANKACCT`, and `SECRET` as a negative guard only) and the non-guard ones are in
`_CONTEXT_LABELS`; (b) `_decide` does not read the map (source check and the same decisions with an empty and a full map): the loop assumes a pattern
pass is a function of the text; (c) `_PLACEHOLDER`, `kind_of` and the `<BANKCODE_n>` reader agree with what `_place` writes, for every label.

## For SECURITY wording (round 3; replaces the lists below where they differ)
- After the first pass and sweep the redactor runs the patterns again over the strings that changed, round after round until a round changes no text, at
  most 4 rounds; a call that is still changing in round 4 is refused (RedactionError "NotSettled"), never returned half masked. A text that needs nothing
  more pays nothing more.
- Each round, each sweep of a call (the first included) and the build of the sweep rules are checked against the call's time budget (InputTooLarge past it; CPU time of the
  calling thread, not wall time). A pattern pass in progress is not interrupted: the bound is in defaults.py. A machine about 25 percent slower than the test machine refuses
  a `curl -u `-shaped 262 KB text (fail closed).
- A longer credential found only because a shorter known secret inside it was masked first is stored whole and its other copies are masked whole (no `tail`).
- Boundary class: a call may mask a little MORE than a fresh call on the same text would (digits glued to a swept word), never less.
- Unchanged: values and copies the sweep leaves by rule; escaped look-alikes are never credentials; a tool error text is redacted twice (see below).

## Problem (one root cause)
A pattern's result can change once placeholders stand in the text, and the sweep writes placeholders after every pattern ran.
- E3: `BSB: <code>` then `paid <same code>/<account>`: one pass gave `paid <BANKCODE_1>/12345678`; a second pass masked it.
- E5: `password=V` then `Bearer V+xy` (token under 12 chars): one pass gave `Bearer <SECRET_1>xy`; a second gave `<BEARER_1>`.
  The same for `Basic V+ab` (under 8) and `authorization: V+ab` (under 8).
- `redact_many` had the same gap across strings.

## Patterns that name a placeholder (step 1 of ORDER 012, kept as a record)
BANKACCT "account straight after its code" (literal `<BANKCODE_\d+>`); BANKACCT "account after a keyword" (through
`_bank_context`); SECRET cookie header (negative guard only). Beyond those, every value class that admits `<` `>` with a
minimum length (BEARER, BASIC, authorization, cookie forms, flags) can change after the sweep. Telling them apart is not
cheap AND certain, so the whole table runs again (ORDER 013 item 1).

## ROUND 1 design, SUPERSEDED (kept as the record; the code is the round 3 design above)
(`guard/redact.py` only; no regex changed; no public signature changed)
`_Redactor.settle(originals, swept)`, called by `redact()` (when it sweeps) and `redact_many()`:
1. pattern pass 1 (`find`), 2. sweep 1, 3. pattern pass 2: the WHOLE table once more over each swept string, 4. sweep 2,
only if pass 2 added a value to the map (every string of the call is swept, so the new value's other copies go too).
Round 1 ran a pattern pass at most 2 times and a sweep at most 2 times per call, no loop (that is NOT the code: see ROUND 3). (`_CONTEXT_PATTERNS`, `_CONTEXT_ROUNDS`, `ContextNotSettled` were removed).
Skip, cheap and certain: a string that pass 1 and sweep 1 left unchanged is not scanned again (the same patterns over the
same text with the same state give the same result). A text with nothing to mask costs what it did.
Caps and budget: untouched (they live in runmap); both extra steps are the existing linear ones.

## Invariants (ROUND 3; the round 1 list, "at most 2 passes", is gone)
- A call is settled on the first round (1 to 4) that changes no text, else refused (RedactionError "NotSettled"); asserted by counting rounds.
- A clean text: 1 pattern pass, 1 sweep, byte-identical result. One planted secret: 2 passes, 1 sweep. The chain of three: 4 passes, 3 sweeps.
- For the E3 and E5 shapes one call equals two calls of the old path; a second `redact_text` changes neither text nor map (property test).
- `_sweep_copies=False` (find only) unchanged.

## Property test (ORDER 013 item 2): tests/test_redact_idempotent_property.py
Through `runmap.redact_text` with one run map, per input: (a) a second pass changes neither text nor map; (b) no original of
the map stands raw in the output, by the redactor's own copy rule (`redact._sweep`: secret kinds of 4+ chars nowhere
outside a placeholder; other kinds nowhere as their own token; values the rule never sweeps are not checked).
Inputs: 1,835, none dropped (counts pinned by a test):
| Corpus | Source | Inputs |
|---|---|---|
| privacy | tests/warden_port/privacy_corpus.py MASKED + KEPT | 48 + 14 |
| bank | tests/warden_port/test_redaction_bank.py POSITIVE, NEGATIVE, PINNED | 61 + 16 + 18 |
| review2 | tests/warden_port/test_redaction_review2.py LEAKS, FALSE_POSITIVES | 19 + 5 |
| cookies | tests/warden_port/test_redaction_review9.py COOKIES | 16 |
| own-shapes | tests/warden_port/test_redaction.py OWN_SHAPES | 8 |
| spellings | tests/test_k5_round8.py SPELLINGS (the layered spellings rounds 8 and 9 drive) | 3 |
| round12-fuzz | tests/test_k5_round12_fuzz.py `_case`, its seed | 1,200 |
| round-trip | tests/redact_corpus_support.py `random_text` (its seed) + LOOKALIKES | 300 + 6 |
| p1c | tests/p1c_builders.py gap1_values, gap2_cases, gap3_cases (moved from handover/core-c/evidence/p1c_probe.py) | 16 + 44 + 43 |
| g7 | tests/test_redact_context_after_sweep.py SHAPES, MUST_KEEP, E5 | 6 + 8 + 3 |
| constructed | built for this file to find what one extra pass misses | 1 |
Not used (not redactor inputs): tests/demo_askdata/fuzzgen.py (SQL), tests/test_peel_run_id.py HOSTILE (run ids),
tests/fixtures/textnorm_corpus.json (name pairs for the fold).
Result (round 3, measured): 1,835 pass, 0 refused, 0 fail. With settle switched off 9 fail (5 g7 shapes, 3 g7 E5, `constructed:0`); with ONE extra pass only `constructed:0` fails. HONEST NOTE: no input of the OLDER corpora fails with or without the extra pass; they did not hold this class.

## Former strict expected failures (round 1; both are ordinary passing tests since round 2)
1. `constructed:0`, the chain of three: `password=V`, `BSB: <code>V`, `paid <code>/<account>`: masked in one call by the loop (3 rounds).
2. The compound tail (`password=V`, `Bearer V+tail`, `note V+tail+more`): masked by the spelled-form sweep (`note <BEARER_1>vw end`).

## ROUND 1 cost of the extra pass (measured, CPU seconds, best of 3; the round 3 numbers are in evidence G7-1.md)
| Text | before G7 (one pass) | narrow design (context patterns) | as built (whole table again) |
|---|---|---|---|
| 100,000 chars, 40 bank codes, ~2,900 accounts | 0.206 | 0.263 | 0.484 |
| 60,000 -> 240,000 chars of the same | - | 0.158 -> 0.640 | 0.283 -> 1.128 (4.0x for 4x: linear) |
| 320,013 chars of code placeholders, no account | 0.699 | 0.716 | 1.434 |
A text with matches costs about 2.0x to 2.4x the old pass; a text with no match costs 1.0x (skip). All 25 perf-marked
redactor tests pass on try 1 of 3 (22 existing + 3 new; serial, 70 s; slowest: the per-pattern super-linear sweep 33 s).

## Tests (ROUND 4 counts, SUPERSEDED: ROUND 6 counts are 86 + 6 perf, 68 + 3 perf, 1,842; the collect-only lines are in evidence G7-1.md)
- tests/test_redact_settle_loop.py (round 4: 54 non-perf + 4 perf; round 5: 69 + 6): the cap at its real value (hop chains of 1 to 4 rounds settled, 5 refused, no monkeypatch of the cap;
  NotSettled text asserted through `redact_text`), the real chain of three (3 rounds), the fixed-point and union tests, the rolled-back and reissued spelled forms (and
  the deleted ghost), the 5,000-form scan at the size cap with a text that walks the trie (ratio test), the hostile-map tests (refused past the offset cap; at the cap a time
  bound; the walk's own deadline with the caps raised; a deadline for a token with no form; the forms cap), the overlap rule, deadline tests (value loop and segment check
  with a stepping clock, `_build`, settle passes the deadline to every sweep, a direct `settle` with a spent deadline and a stub `find`), the `bank_near` flip, the generator
  of 4 to 8 lines with a pre-seeded map against the reference loop plus the depth distribution, T4 with budget 6.0 and 0.5.
- tests/test_redact_context_after_sweep.py (round 4: 59 + 3 perf; round 5: 68 + 3): E3 shapes, redact_many, E5, must-keep, call counts, timing, the three guards of "Guards that replaced the
  deleted test" (the pattern-source guard is named for what it sees, and states that value classes that merely admit `<` are invisible to it), and the own-token limit.
- tests/test_redact_idempotent_property.py: round 4: 1,835 params + 7 tests; round 5: 1,835 + 6 (the parity test is gone); round 6: 1,836 + 6.
- tests/test_redact_own_output.py (23).
- Fail-before (round 3, new files on the round 2 redact.py and runmap.py swapped in for a few seconds): 14 of the new tests failed; the ones that fail
  for the reason of a finding: the hop chains (the loop ended on map growth), the union test, the reissue ghost, the 5,000-form ratio, the `_build` deadline,
  the settle deadline, the NotSettled text. The three guards (M7) and the generator pass on the old code too: they guard what the design relies on.

## Second finding: `redact_untrusted` over its own output (caller table)
| Call site | Input | Can the input be output of redact_untrusted? |
|---|---|---|
| runtime/agent_loop.py:412 (document) | the trigger document, raw bytes | Not from this run. Only if the document itself quotes an earlier masked text (a ticket that pastes a previous report): outside content, escaped by design |
| tools.py:982 `redact_layered` <- tools.py:967 `prepare_output` <- tools.py:1198 (toolbox) and agent_loop.py:311 (plain tool) | the tool's raw return value | Normal result: no, unless the tool echoes its arguments: `restore_value` leaves secret-kind placeholders in the arguments, so an echo carries genuine `<SECRET_n>` back in (measured: `password=<SECRET_1>` echoed -> `password=<SECRET_2>`, map gains `<SECRET_2>` = the escaped token) |
| the same two sites, ERROR path: tools.py:1193 and agent_loop.py:309 `error_reason(exc)` then `prepare_output` | the exception message | YES, always. `error_reason` (tools.py:1005) runs `redact_bounded(message, {}, neutralise_untrusted)` with a throwaway map, then `prepare_output` runs `redact_untrusted` with the run map on that output. Measured: `login failed password=V host A` -> after error_reason `password=<SECRET_1> host <IPV4_1>` -> after prepare_output `password=<SECRET_2> host ‹IPV4_1›`, run map gains `<SECRET_2>` = `‹SECRET_1›` |
| k1b/redaction.py:188 `redact_bundle` <- k1b/replay.py:158 | every string of a case bundle read from disk | No: pass 1 and pass 2 both walk the ORIGINAL bundle (pass 1's output is dropped), and the masked bundle is cached per case, not re-masked. A bundle file that quotes masked text is outside content, as the document |
| evals.py:63 | golden case input file, fresh map | No (same outside-content note) |
| guard/judge.py:71, guard/bedrock_guardrail.py, runtime/evidence.py, approvals/channel.py, approvals/slack_channel.py | already redacted text | They use `redact_text` without the untrusted hook (judge, guardrail, evidence) or with the channel's own hook that keeps placeholders (channel): not this finding |
| demos/ | none of the three names occurs | No caller |

Verdict: ONE caller can and does: the tool-error path (both loops); an echoing tool does the same. FIXED in the
follow-up (coordinator order after ORDER 012 item 2), in `guard/redact.py` `_Redactor._mask` only:
- Rule: a value that is nothing but ESCAPED look-alikes (`_OWN_OUTPUT`, matched in `_decide`: U+2039, letters/digits, `_`, ASCII digits,
  U+203A, exactly what `runmap.escape_placeholders` writes) and genuine placeholders, with nothing else but spaces, `;`
  and `,`, is left alone, as a value of genuine placeholders alone already was. No map entry is made.
- Result (through `tools.error_reason` then `tools.prepare_output`): `password=‹SECRET_1› host ‹IPV4_1›`, run map
  unchanged; `is_masked(out, map, neutralise_untrusted)` True; `redact_untrusted` of that output returns it unchanged.
- The escape of the throwaway `<IPV4_1>` in the second pass is REQUIRED and untouched (it is not the run map's).
- Security, each tested (tests/test_redact_own_output.py, 23 tests): a look-alike PLUS anything else (a secret after,
  before or between, one letter, one digit, non-ASCII letters, punctuation only, a dot between two look-alikes) is masked
  whole as before; a secret beside a look-alike as its own value is masked; only the exact escaped shape qualifies
  (no number, no kind, not closed, a secret inside the brackets: all masked); an escaped token gets no map entry, so
  `restore_text` / `restore` return it as typed and `has_placeholder` is False; a typed genuine placeholder in untrusted
  text is still escaped.
- Gives up: a real credential spelled exactly `‹WORD_1›` is not masked (as a credential spelled `<nil>` is not).
- Fail-before: 8 of the first 20 tests failed on the code before the rule (evidence).
- tests/test_runmap_is_masked.py: the strict xfail marker of `test_round_trip_of_redact_untrusted_with_the_same_hook_and_escaped_lookalikes`
  removed (one exact-string edit, nothing else); it passes.
- CHANGED OUTCOME, NOT EDITED (held file): `tests/test_runmap_is_masked.py::test_recorded_the_untrusted_hook_on_already_redacted_text_escapes_its_real_placeholders`
  now FAILS: it records the old behaviour. Old: `is_masked(out, mapping, neutralise_untrusted) is False` and
  `again == "password=<SECRET_2> at ‹IPV4_1›"`; new: `True` and `"password=‹SECRET_1› at ‹IPV4_1›"`. Its owner must
  rewrite or remove it.
- Still open, tools.py (not mine): `error_reason` redacting before `prepare_output` is a double pattern pass; harmless now.

## Stays out
No pattern regex, no pattern order, no change to `tools.py`, the sweep rule or the caps. `runmap.py`: only `redact_text` re-raises a RedactionError as it is (round 3 N8); `enforce_map`, `snapshot` and `EnforceBudget` are another lane.

## NOT CHECKED (ROUND 3)
- The whole test suite: only the files named in evidence G7-1.md (redact, runmap, stage names, hard-coded values).
- A natural chain of 4 rounds: none found (generated, random search, by hand); the 4 and 5 round tests use a stub pass.
- Timing on Windows or under load. The wall-clock behaviour of the budget (it is CPU time of one thread).
- The gate's own clocks beyond what its code says (another agent's lane, `runmap.EnforceBudget`): round 4 only re-read them and corrected the wording.
- tools.py `error_reason` redacting before `prepare_output` (a double pass, harmless; not mine).

## For SECURITY wording (ROUND 3, END)
See "For SECURITY wording (round 3...)" near the top: it is the list. Older lists ("two passes at most, not a fixed point", "a THIRD pattern pass leaves
the account readable", "`tail` stays readable") were round 1 and are false for the code.
- Also unchanged since the follow-up: a value made only of escaped placeholder look-alikes (`‹KIND_n›`) is never treated as a credential; a tool error
  text is redacted twice (throwaway map, then run map): its placeholders reach the model escaped, not numbered in the run's map.
- Copies the sweep leaves by rule: values under 3 characters; all-digit values under 6; common words (`prod`, `admin`, ...); a non-secret identifier where a
  letter or digit touches it.
