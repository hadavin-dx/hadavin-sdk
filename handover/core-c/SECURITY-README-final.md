# Final wording for SECURITY.md and README.md: what the core guarantees and what it does not

Written by core-c (technical writer), 2026-11-20. Status: DRAFT text for the lead or core-b to place. This file changes no other file. README.md and SECURITY.md were read and not edited.

How to read this file
- Part 1 is the owner summary (10 lines).
- Part 2 is the section for SECURITY.md: "What the core guarantees and what it does not".
- Part 3 is the paragraph for README.md: "Python version".
- Part 4 lists the disagreements found between the sources.
- Part 5 is the technical appendix (table of limits, test names, what was not run). Codes and test names are only used there.
- The word UNVERIFIED marks a statement whose only evidence is a reviewer's reading of the code. The reviewer ran nothing, and the fix agent has not yet reproduced it.
- Status words, used in this file with one meaning each:
  - FIXED: the code was changed and a test fails without the change. Where a fix was not re-read by an independent reviewer, the line says so.
  - PINNED: not fixed on purpose. A test fails if the behaviour changes, so the limit cannot change unnoticed.
  - WAITING: the fix belongs to another team (core-b owns the model adapters, the store, the run loop and the approval channel files). The request is written down.
  - OPEN: no fix and no decision yet. Our team or the lead has to act.

---------------------------------------------------------------------------------------------------

## Part 1. Owner summary (10 lines)

1. Protected now, in the built code, under the conditions in Part 2: a value the run already knows is sensitive is swapped for a placeholder before text goes to a model; a model call is refused if no money was reserved first; text that hides a value with look-alike or invisible characters is found.
2. Important: the model gate (the single wrapper around every model call) is built and tested as a module. The evidence does not show it installed at the places that call a model; core-b does that. Until then none of the gate sentences describe the running system.
3. Not protected: a secret in a shape the pattern list does not know; a value written in base64 under 40 characters; bare numbers with no label; a host name with no "host" word in front of it.
4. Not protected: the system prompt and the tool definitions sent to a model are never checked. The separate guardrail call to the vendor does not pass through the gate.
5. Money: a failed model call keeps its worst-case amount booked for about an hour, so a few failures can stop an agent for the day. A reply with no cost shown may be booked as free. Both are fixes for core-b.
6. Open weaknesses from the second independent review (reading only, not yet reproduced): a forged tool-result marker can leave a known secret unmasked in one case; a second case leaves most of a secret readable.
7. Approval cards (the messages that ask a person to approve an action): masked and written so links cannot be clicked. The "requested by" line is not yet masked (core-b's file).
8. Nothing was run on Python 3.12, nor on PostgreSQL 17. The integration of the text work (cards, folding, redactor) sits on a working branch that is not pushed or merged.
9. Decisions needed from the lead: four choices in the table in Part 2.8 (marked DECISION).
10. Wording rule kept: nothing in this file claims more than the evidence shows; "NOT RUN" means exactly that.

---------------------------------------------------------------------------------------------------

## Part 2. For SECURITY.md: "What the core guarantees and what it does not"

### 2.0 Words used here
- Model: the AI service that reads text and answers (for example a hosted language model).
- Run: one job of one agent from start to finish.
- Placeholder: a stand-in such as `<SECRET_1>` that replaces a sensitive value. The model sees the stand-in. The real value stays in the run's own table.
- Run map: that table, one per run, that remembers which real value each placeholder stands for.
- Redactor: the code that looks at text and finds sensitive values by patterns (shapes such as `password=...`, e-mail addresses, keys). It writes the run map. It runs where text is produced (tool results, documents, cards).
- Gate: one wrapper around every model call. It does not look for new sensitive values. It only swaps values already in the run map, reserves money, makes the call, settles the money, and writes an audit row.
- Reservation: an amount set aside before the call at its worst case, so the cap cannot be passed by a call already under way. Settling gives back what the call did not cost.
- Audit row: one line in the permanent record of what happened (who, which kind of action, result, a short code). Audit rows hold no message text.
- Made-up values in the examples below are not real credentials.

### 2.1 Masked model input

What holds (conditions in the same sentence):
- Values the run has identified as sensitive (they are in the run map) are replaced by their placeholders in every message and every document the gate sends to a model. The condition: the gate was bound with the run's map. Detection of new values is the redactor's job, not the gate's.
- If the gate cannot do the replacement (text too large, content that is not text, time budget used up, text still changing after 4 rounds), it makes no model call and reserves no money. It stops with a refusal that carries a short code and no text.
- If nothing known is present, what is sent is the same text, unchanged.
- The gate never writes to the run map and never changes the caller's own lists.
- Since the order of 2026-11-20 the caller must say "no map" explicitly. A forgotten map is an error, not a silent skip.
- The built evidence: 140 tests in the first build, later suites; 66 of 66 deliberate code breaks ("mutants") were caught in the last run on the gate files. Measured by the builder, not by an independent runner. Not run: the full test suite, Python 3.12, a live model.

Limits, in plain words (the number is used in the appendix):
- L1 A secret that is in no map is not touched by the gate. Example: a raw `hunter2zz` that no pattern ever matched goes out as written. PINNED.
- L2 Not replaced even when known: values under 3 characters; digit-only values under 6 digits; common words (`prod`, `admin`, `test`); and, for names and identifiers (not for secrets), a copy with a letter or digit touching it. Example: when `abc123` is known, `xabc1234` stays. A secret of 4 or more characters is replaced everywhere, even inside a longer word. PINNED.
- L3 Only the exact spelling stored in the map is replaced. A copy written with percent codes, HTML entities, backslash codes, full-width or look-alike letters, a hidden zero-width character, a NUL character or a colour code inside it goes out as written. Example: known `abc123` and the text `abc&#49;23`. The text folding in 2.6 is the control at the place where text is produced. PINNED.
- L4 Capital and small letters count as different. Known host `db01.acme.example`, text `DB01.ACME.EXAMPLE`: not replaced. PINNED.
- L5 Two known values that overlap leave the tail of one readable. Example: known `abcd` and `cdef`, text `abcdef` becomes `<SECRET_1>ef`. PINNED.
- L6 A key and a value that are clean on their own but form a pattern once joined into one line are not touched. Example: `"user_id": "abc123"`. PINNED.
- L7 A known value that itself contains something shaped like a placeholder (`ab<X_1>cd`), or that is written inside angle brackets, is not replaced. A value standing right against a fresh placeholder can keep its tail readable (`<SECRET_1>abc`). PINNED.
- L8 Only the message text and the documents are replaced. The system prompt, tool definitions, the "role" label, extra message fields, the output format description and the route are sent as they are. Example: an operator who puts a customer name in the system prompt sends it unmasked. PINNED.
- L9 With "no map" (used by the evaluation and replay command lines) nothing is replaced. The audit row says `no_map`. UNVERIFIED that the audit row can never say "map in use" when the map was empty or a test replacement function was supplied (second review, reading). OPEN.
- L10 The separate vendor guardrail call (Bedrock) does not pass through the gate. Decided in the plan, not a defect. PINNED by decision (no test named in the evidence).
- L11 UNVERIFIED. A forged tool-result marker can leave a known secret unmasked. The gate leaves a marker of the form `<<TOOL RESULT call_id=... tool=...>>` alone, so a user message that writes such a marker with a known secret inside the id slot would send the secret as written. Found by the second independent review of the gate; its own test pins the opposite and never checks the secret is gone. OPEN: the fix agent is to reproduce and fix it.
- L12 UNVERIFIED. A held-back edge value can leak most of a secret. Example from the review: known secrets `S3cr3t` and `>abcdef`; the text `S3cr3t>abcdef` becomes `<SECRET_1>abcdef`. OPEN.
- L13 UNVERIFIED. The time and size limits of the replacement step are not hard limits. A hostile input can make the gate slow (the time check happens after each round, and each message has its own clock). OPEN.
- L14 A planted word that equals a marker word or a tool name (example: a tool result containing `password=RESULT`) makes every later tool-using call of that run refuse with `framing_refused`. This is a way to stop a run on purpose. DECISION for the lead: accept, or protect the marker line instead and keep the refusal only for secrets. OPEN.
- L15 Two threads writing one run map at the same time can give one placeholder number to two values. Not pinned (a race). OPEN, stated: one writer per map.
- L16 The gate is built and tested as a module. The evidence does not show it called from the run loop, the judge, the replay, the evaluations or the extraction code. core-b has a per-place list. Until then masking depends on each place doing its own. WAITING.

### 2.2 Capped spend

What holds:
- The gate makes no model call without a reservation. Order: replace known values, reserve, call, settle, audit row.
- A reservation succeeds only when the day total and the month total stay within the cap, and a stop switch is off. The 50-connection test (50 database connections asking at once, cap 3.00, worst case 1.00) grants exactly 3 and refuses 47. Condition: this was run on core-b's store code, PostgreSQL 16.15, Python 3.13, two runs of 49 passing tests. Not run on PostgreSQL 17 or Python 3.12.
- When a reply comes back with a usable cost, the gate settles the real cost.
- When no reservation could be made, no call goes out.

Limits:
- L17 A failed call keeps its worst-case amount booked until the store's clean-up closes it (about an hour). The model adapters do not yet say "refused before any answer", so the gate cannot release the amount. Example: cap 3.00, worst case 1.00 per call, three failed calls that cost nothing stop the agent for the day (reviewer's example, reading only, UNVERIFIED). WAITING on core-b (request 2).
- L18 A reply whose cost is missing, negative or not a number is returned to the caller, and its reservation is not settled. WAITING for the owner of the adapters to set a cost. Separately, today a reply with no cost set reads as 0 (the code default), so it would be settled as free (found by reading models.py: UNVERIFIED). WAITING on core-b.
- L19 A call that succeeds after retries settles only the last attempt; an earlier attempt that timed out might have been billed (reviewer's reading, UNVERIFIED). WAITING on core-b.
- L20 Settling above the reservation books the overshoot past the cap. Measured: reserve 1.00, settle 2.50 books 4.50 against a cap of 3.00, and all later calls are then refused. PINNED (test in the store tests). So the cap can be passed once by one call whose real cost exceeds its worst case.
- L21 The worst-case amount is calculated by core-b's code. No function in the tree fits the gate's call today, and the gate refuses an amount that is not a finite number of 0 or more. The first real helper needs a contract test. WAITING on core-b.
- L22 The cap rests on code, not on database permissions. By reading core-b's permission map, the runtime login can rewrite a reserved amount, and the purge login can delete an open reservation (the counters stay booked, the safe side). Not run, UNVERIFIED. WAITING on core-b / DECISION for the lead.

### 2.3 Stop

What holds:
- When the store's stop switch is on, a reservation is refused with the code `kill_switch`, so no model call goes out. This follows from the reservation rule above. The evidence runs no end-to-end stop test of a live run.
- The permission test files (49 passing on core-b's code, PostgreSQL 16) check which database logins may read or write the reservation table.

Limits:
- L23 UNVERIFIED. The run loop catches only the provider's errors, so a stop refusal could leave a run in the state "working" instead of "stopped" until core-b wires it (reviewer's reading). WAITING on core-b.
- L24 UNVERIFIED. The runtime login can insert a stop under any name; the reset login can change any stop row (reads as "on", the safe side). core-b's ticket accepts the second. WAITING / DECISION.

### 2.4 Audit

What holds:
- Each gate call writes one audit row with the run id, the kind (model call), the principal, the result and a short code from a fixed list. The row never holds text, a cause or a chain of errors. A test reads the module's syntax tree to prove it holds no logging or error text.
- The reservation id is in the row when a reservation exists.
- If writing the row or settling fails after the reply came back, the reply is still returned.

Limits:
- L25 The row does not say whether anything was replaced, and has no route or model name. NOT DONE (needs a lead decision on which fields). OPEN.
- L26 UNVERIFIED. If the process is interrupted (Ctrl-C) while the gate reserves or calculates the worst case, no row is written and a booked reservation may stay (second review, reading). OPEN.
- L27 Two database logins (runtime and reset) can append any audit row, not only their own kind. Named by core-b as a known cost. UNVERIFIED (reading). WAITING.
- L28 Every successful call now writes a new row. Tests that count rows change at installation. WAITING on core-b.

### 2.5 The redactor (what goes into the run map)

What holds:
- The redactor finds the kinds it knows (addresses, keys, tokens, e-mail, URL credentials, command-line credential flags, supplier payment details such as a bank account beside its bank code). Since the change of 2026-11-20 one call to the redactor is enough for a bank account beside its bank code, and for the part after a known secret inside a longer credential (up to the limits below). Condition: the text is written in the shape of the kind.
- Where a line cannot be masked in place it is withheld whole with a fixed note.

Limits:
- L29 A secret in a shape no pattern knows is not found anywhere. Example: an unlabelled 40-character code in prose. PINNED (README already says so).
- L30 A bare number with no label (`ref 55556666 paid`) is not masked, by decision. PINNED.
- L31 A host name that is not private and has no host word in front (`db01.acme.example`) is not masked. A private name followed by a public tail is only partly masked today (`db01.corp.example` becomes `<HOSTNAME_1>.example`). The planned fix (G4) is not built: no build evidence exists. OPEN (DECISION: keep as stated limit or build).
- L32 Base64 text: a base64 value under 40 characters passes unchanged (41 of 41 test rows leaked on the earlier code; long unbroken blobs are masked). The decoding step (G4) is not built. Measured on the main code before the text work, not re-measured on the current branch. OPEN.
- L33 A value with a letter, underscore or digit written right behind it may be shown whole for some kinds. E-mail is fixed (`anna.m@example.org9` is masked, on the working branch). Still not fixed: the last part of a host name, an IPv4 address (`10.20.30.40_x`), a phone number, a bank number (IBAN), a UUID. Measured by the integration agent. OPEN (the next ticket).
- L34 The redactor does at most two pattern rounds and two replace rounds on one text. A chain that needs a third round leaves a value readable. Example: a bank code glued to a secret, then the account number after that code elsewhere. The text has to be planted on purpose, and the attacker has to know the bank code. PINNED as an expected failure. A fix that fails safe (stop instead of continue) is proposed and OPEN (needs the lead).
- L35 When a longer credential is found only because a shorter known secret inside it was masked first, a short tail of up to 7 characters of it stays readable in other copies (`<SECRET_1>tail`). The earlier test pinned 5. PINNED, fix proposed (dz-2). OPEN.
- L36 Time and cost: every text containing one secret takes about 2.0 to 2.4 times as long (100,000 characters: 0.206 s before, 0.484 s after, measured). The time budget is checked between rounds, not inside one. OPEN (dz-3).
- L37 A text may pass through the redactor up to 7 times (itself and its decoded views). The "two rounds" rule is per call, not per text.
- L38 A secret first seen in a tool's error message is not entered in the run's map, so its other copies in later tool results are not replaced. The placeholder reaches the model escaped (`‹SECRET_1›`) and is not numbered in the run's map. The fix is in core-b's file (request 4). WAITING.
- L39 A credential spelled exactly like an escaped placeholder (`‹SECRET_1›`) is not masked. After the fix of 2026-11-20 only that exact shape of the label SECRET counts, with ASCII digits. FIXED (reviewer found `‹hunter2zz_1›` stayed readable; reproduced by a run, fixed, 30 new tests). The fix was not re-read by an independent reviewer.
- L40 The redactor must not be applied to its own output with the hook that escapes placeholders. Reading found one caller doing so (the tool error path); it is now handled. UNVERIFIED that no other caller does it (a caller table made by reading).
- L41 Existing limits kept as they are: a secret that itself contains a plain space, `;`, `,` or `&` is masked only up to that character; a form-encoded `;` or `&` is ambiguous. (Existing text of SECURITY.md, not re-checked in this round.) PINNED.

### 2.6 Text folding (look-alike and hidden characters)

What holds:
- Text is compared in a folded form (full-width letters, Cyrillic look-alikes, invisible characters, combining marks and similar are reduced to a common spelling) before patterns and known values are looked for. A line that hides a value this way is masked in place if possible, and withheld whole if not. Condition: the interpreter's Unicode data is 15.1.0 (Python 3.13). Part 3.
- The build evidence: 1 test red in the first batch (decided, see Part 4), 8,616 passed; later integrated batch 11,542 passed with one known red test about a file registration (another team's). Nothing run on Python 3.12.

Limits:
- L42 Escape codes written in text (backslash codes, entities) are not decoded by the fold. A look-alike letter added in a Unicode version later than 15.1 is dropped. The fold's "hidden channel" check counts only the tag block and variation selectors. Confirmed by the reviewer's reading (UNVERIFIED, no run). PINNED as documented limits.
- L43 Over-matching. A known name can be found inside a longer word (`Mary` in `summary`, `ab12` in `(tab) 12 apples`), so innocent text may be masked or withheld. Not measured on ordinary text. UNVERIFIED. OPEN.
- L44 The fold's own time use has no deadline. The injection check reads up to 2,097,152 characters with no clock. Not measured. UNVERIFIED. OPEN.
- L45 A very long text of only Chinese or Japanese letters (measured: 300,000 characters) is flagged as a guard failure (`guard_unavailable`) instead of being read. Russian prose over the same size passes. Behaviour unchanged, measured. PINNED (stated).
- L46 DECISION taken in code, confirmation by the lead awaited: dashes and curly quotes are treated as ordinary punctuation, so a value beside them is masked in place; three slash look-alikes (U+2215, U+2571, U+29F8) cause the line to be withheld. 30 characters differ from the earlier design. PINNED (5 tests).
- L47 The evidence check ("is this value in the evidence") finds more than before when an invisible character sits between a letter and its accent. Accepted as the stricter side for Latin. Wider cases (Korean jamo, Indic vowel signs, kana) were not decided or tested. OPEN.

### 2.7 Approval cards

What holds:
- On every path that produces text for an approval card or a channel message, the redactor runs first and web addresses are made unclickable last (a dot written as `[.]`). 27 path tests, plus seeded property tests (800 and 2,000 generated texts: 0 failures after the fix round). Condition: the text is a free-text field of the card.
- A card is re-read until stable, at most 3 times. If it never settles, the card becomes a fixed note instead of text. Stored old cards are masked again on display (reviewer's reading, UNVERIFIED).
- Glued e-mail addresses, an e-mail with a digit or underscore behind it, are masked in one pass. Condition: on the integration branch (see L53).

Limits:
- L48 The "requested by" line and other card strings (ids) are neither masked nor made unclickable and are read as Slack formatting. Example: a requested-by value `slack:U1|<!channel>` gives a live `<!channel>` notice. Reviewer's reading, UNVERIFIED. WAITING on core-b (request 5).
- L49 The check that "no clickable link remains" uses the same patterns as the code that makes links unclickable, so both share any blind spot (`see/evil.com`, `[evil.com]`). No independent link checker was run. UNVERIFIED. OPEN.
- L50 A card costs more time: the 174-character card 1.26 ms to 3.60 ms; a 71,179-character card 367 ms to 655 ms (median, measured, a loaded machine). Stated.
- L51 Old stored summaries may show unmasked in the admin console (the reviewer did not check it). UNVERIFIED. OPEN.
- L52 Sending a card above the size limit can now raise an error out of the card code (not only the summary path); the fix falls back to the fixed note. Reading only. UNVERIFIED.
- L53 The text work for cards, folding and the redactor was combined on a working branch that was never pushed, and picking it onto the main working branch was not done. A change to a file of core-b's team (the channel code) was accepted by the lead's order but sits on the same branch. WAITING / DECISION.

### 2.8 What the lead has to decide (DECISION lines)
1. L14: accept the stop-by-planted-word, or protect the marker line.
2. L25: which fields the audit row should carry.
3. L31 and L32: build the host-name and base64 changes (G4) or keep them as stated limits.
4. L46 and L47: confirm the dash, quote and slash choices, and the wider accent matching.
Also open: L34 and L35 (fail-safe fix), L22 and L24 (database permissions).

---------------------------------------------------------------------------------------------------

## Part 3. For README.md: "Python version"

Production and pilot must run Python 3.13 (its Unicode data is version 15.1.0). Python 3.12 (Unicode 15.0.0, measured on the build machine) is for demos and tests only.

Why: the text folding (the look-alike and hidden-character check) depends on the Unicode data of the interpreter, and its look-alike table is the 15.1.0 table.

What happens on another version: when the stage is pilot or prod, the start-up check refuses to start. It raises an error named `UnidataMismatch`, and nothing runs. The check is not loosened. On a demo stage the program starts, but every check name carries a tag with the Unicode version, so a name made on 3.12 never equals one made on 3.13. After the review of 2026-11-20 the check runs before any secret store or backend is built (a test covers the order).

What is not shown by evidence: nothing was run on Python 3.12 for the text work. The project file still allows 3.12 and the continuous-integration job for 3.12 is expected to stay green, but that is UNVERIFIED until it is run. Moving the pin to a later Python (for example 3.14) is a data change, not a version bump.

(The existing README section says this twice, in two paragraphs. One of the two can be deleted.)

---------------------------------------------------------------------------------------------------

## Part 4. Disagreements found

Newer source wins; each line says what was replaced.
1. Limit 3 of the first draft ("values under 3, digit strings under 6, common words, identifiers touching a letter") versus revision 2 and the gate ticket (round 1): the exemptions do not apply to a secret of 4 or more characters. Used: revision 2 (L2).
2. Gate ticket Amendment 1 item 6 (settle 0 on a plain provider error, worst case on exhaustion) versus the round 1 "one settle rule" (settle 0 only when the adapter marks it; otherwise do not settle). Used: round 1 (L17, and 2.2).
3. Amendment 1 item 4 (`bind` without a map means no replacement) versus the order of 2026-11-20 (map required, `NO_MAP` named). Used: the order (2.1).
4. The first review said "bind the judge with no map"; the ticket's install list says the judge gets the run's map. Used: the ticket (the later). The first draft limit 8 still says "the judge with its own map". Not settled; stated here.
5. G7 ticket says the tool-error double redaction is "harmless"; the review (dz-6) and revision 3 withdraw it. Used: the review (L38).
6. G7 ticket and revision 2 say "two pattern rounds per call" and a tail of 5 characters. Revision 3 and the review: per call of the redactor, up to 7 calls per text, tail up to 7. Used: revision 3 (L35, L37).
7. G7 ticket and revision 2 say a value made only of escaped look-alikes is never a credential (any kind). Evidence of the G7 fix round: only the exact SECRET shape with ASCII digits. Used: the evidence (L39).
8. Gate evidence says the marker problem was fixed (reproduced, mutants, tests). The second review says the fix opened a leak (L11). Used: the second review, UNVERIFIED.
9. Revision 2 says glued-digit e-mail is "not fixed" (question 15). The integration evidence says fixed (on the unpushed branch). Used: the integration evidence (L33, 2.7).
10. G2 evidence "Verdict in short" (two property tests failing, mutants blocked) versus its "Fix round" (both fixed, 7,879 passed). Used: the fix round.
11. G3 evidence lists one red test (the spacing-mark test) as awaiting the lead; the G text ticket Amendment 1 says the test was changed and decided (option a). The integration batch shows no such failure. Used: the integration evidence, so closed. The G3 worktree evidently lacked the change.
12. G1 review blockers B1 and B2 "being fixed" versus the G1 evidence "fix round 1" (reproduced, fixed, tests). Used: the evidence. No independent re-review of the fixes.
13. G text ticket (G1 review M3): the fold is wired into no redaction path. Later: the fold scan was ported (G3) into the redactor. Used: the later. Also stale numbers in the F ticket "AS BUILT" (269 lines, 12 mutants): now 347 lines and 66 mutants. The review counted these as stale citations.
14. Draft requirement line says "Python 3.12 carries 15.0.0 (measured in this box)". The G1 review adds that the start-up check ran after the secret store was built; fixed afterwards (Part 3).

---------------------------------------------------------------------------------------------------

## Part 5. Technical appendix

### 5.1 Table: limit, where pinned, status, owner
Test names are as given in the sources. T = tests/test_model_gate.py. E = tests/test_runmap_enforce_map.py. "none named" = the sources name no test.

| limit | where pinned (test or evidence) | status | owner |
|---|---|---|---|
| L1 unknown secret passes | T::test_t5_a_raw_secret_that_is_not_in_the_map_passes_unchanged_detection_is_the_producers_job | PINNED | core-c |
| L2 short values, digits, common words, touching | E::test_stated_limit_short_values_short_digit_strings_and_common_words_are_not_swept; E::test_stated_limit_an_identifier_touching_a_letter_or_digit_is_not_swept | PINNED | core-c |
| L3 encoded or look-alike copy | T::test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate; E::test_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced; E::test_stated_limit_a_copy_split_by_nul_characters_is_not_found; T::test_d7_stated_limit_a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced | PINNED | core-c |
| L4 letter case | T::test_d7_stated_limit_another_letter_case_of_a_known_value_is_not_replaced | PINNED | core-c |
| L5 partial overlap | E::test_stated_limit_partial_overlap_leaves_a_tail; T::test_b1_stated_limit_a_partial_overlap_leaves_a_tail_in_what_is_sent | PINNED | core-c |
| L6 composed key and value | T::test_stated_limit_a_clean_key_and_value_that_match_a_pattern_once_composed_are_not_touched | PINNED | core-c |
| L7 placeholder-shaped values, edge tail | E::test_stated_limit_a_value_holding_a_placeholder_shaped_token_is_never_replaced; E::test_stated_limit_a_known_value_written_inside_angle_brackets_reads_as_a_placeholder; E::test_e2_a_value_straddling_the_edge_of_a_placeholder_written_in_the_same_pass | PINNED | core-c |
| L8 system, tools, role, schema not enforced | T::test_t20_system_and_tools_are_not_touched; T::test_d7_role_extra_message_keys_and_output_schema_are_forwarded_untouched | PINNED | core-c |
| L9 no map; audit says map enforced when it was not | T::test_no_map_means_no_enforce_step_at_all; no test for the audit-row claim | PINNED / OPEN, UNVERIFIED (dz2-M5) | core-c |
| L10 Bedrock guardrail outside gate | none named (plan decision A3) | PINNED by decision | lead |
| L11 forged framing token | `test_o17_6_..._inside_a_framing_token_leaves_the_token_alone` pins the leak (line 1923) | OPEN, UNVERIFIED (dz2-B1) | core-c |
| L12 held-back edge value leaks | none (dz2-M2) | OPEN, UNVERIFIED | core-c |
| L13 bounds not hard | none (dz2-M3); evidence only for 100 messages and 2,000 entries | OPEN, UNVERIFIED | core-c |
| L14 planted word stops a run | `test_o17_6_reproduction_...` | OPEN, DECISION | lead |
| L15 two writers, one map | not pinned (race) | OPEN (stated) | core-c |
| L16 gate not installed at call sites | tests/test_k5_producers.py::test_every_module_that_calls_a_model_is_registered is red on purpose; requests/1-producers.patch | WAITING | core-b |
| L17 failed call stays booked | requests/2-refused-before-response.md; no test of the mark | WAITING, UNVERIFIED | core-b |
| L18 missing cost; default 0 | model gate tests for None, float, NaN, negative (round 2); models.py:299 read only | gate part FIXED; default WAITING, UNVERIFIED | core-b |
| L19 retries settle last attempt | none (llm/retry.py:92-107 read) | WAITING, UNVERIFIED | core-b |
| L20 overshoot passes cap | tests/contracts/test_t1_reserve_cap.py (settle above reserve case) | PINNED | core-b / core-c tests |
| L21 worst-case formula | contract test at install not written | WAITING | core-b |
| L22 grants let runtime rewrite amount | evidence/B-grants-rework.md findings 1-2 (read, not run) | WAITING, UNVERIFIED | core-b |
| L23 stop not mapped in run loop | none (cb-M7 reading) | WAITING, UNVERIFIED | core-b |
| L24 runtime can sign a stop; reset can update stops | ESCALATIONS E7 items 3-4 (read) | WAITING / DECISION, UNVERIFIED | core-b |
| L25 audit row lacks replaced flag, route | none | OPEN | lead |
| L26 interrupt skips row | none (dz2-M7) | OPEN, UNVERIFIED | core-c |
| L27 two roles can append any audit row | E7 item 5 (read) | WAITING, UNVERIFIED | core-b |
| L28 more audit rows after install | none | WAITING | core-b |
| L29 unknown shape passes | README "Limits and trust" | PINNED | core-c |
| L30 bare number | probe rows pinned by G4c plan; no G4 build evidence | PINNED by decision (test not shown as built) | core-c |
| L31 host name | evidence/P1c-probe.md (28 of 44 rows leaked on main) | OPEN | lead |
| L32 base64 under 40 | evidence/P1c-probe.md (52 of 142 leaked on main) | OPEN | lead |
| L33 glued kinds (host, IPv4, phone, IBAN, UUID) | INT-g2-g3.md follow-up (c); e-mail: tests/test_text_parts_together.py, test_p1d_a_paths.py | e-mail FIXED (branch); others OPEN | core-c |
| L34 third round chain | tests/test_redact_idempotent_property.py (strict expected failure `constructed:0`) | PINNED, fix proposed | core-c / lead |
| L35 tail up to 7 | `test_limit_the_tail_of_a_compound_value_found_late_is_not_swept_from_its_other_copies` (pins 5) | PINNED (value wrong, to correct), fix OPEN | core-c |
| L36 cost x2.0-2.4 | evidence/G7-1.md perf tests (3 tries) | OPEN (dz-3) | core-c |
| L37 up to 7 calls | none | stated | core-c |
| L38 error text not in map | requests/4-error-reason-run-map.md | WAITING | core-b |
| L39 escaped look-alike credential | tests/test_redact_own_output.py (23), tests/test_redact_own_output_hardening.py (30+) | FIXED, no independent re-review | core-c |
| L40 own-output callers | caller table in G7 ticket (read) | UNVERIFIED | core-c |
| L41 space, `;`, `,`, `&` in value | existing SECURITY.md text | PINNED | core-c |
| L42 escape, new code points, hidden channel | tests/test_textnorm_*.py (documented limits; reviewer confirmed by reading) | PINNED, UNVERIFIED | core-c |
| L43 name inside longer word | none | OPEN, UNVERIFIED | core-c |
| L44 no deadline in fold | none | OPEN, UNVERIFIED | core-c |
| L45 CJK over cap fails closed | measured in evidence/G1-fold.md (M6); no new test | PINNED (stated) | core-c |
| L46 dash, quote, slash choice | tests/test_redact_g3_port.py (5) | PINNED, DECISION | lead |
| L47 wider accent matching | tests/test_evidence_decomposed.py (Latin only) | OPEN | lead |
| L48 card strings not masked | requests/5-card-ids-redact-defang.md | WAITING, UNVERIFIED | core-b |
| L49 link oracle shares blind spots | none | OPEN, UNVERIFIED | core-c |
| L50 card cost | measured, INT-g2-g3.md (b) | stated | core-c |
| L51 admin console old cards | none | OPEN, UNVERIFIED | core-b |
| L52 oversize card error | none | OPEN, UNVERIFIED | core-c |
| L53 branch not pushed or merged | INT-g2-g3.md "never pushed", "picking not done" | WAITING / DECISION | lead |

Totals: 53 limits (L1 to L53). Sources of the UNVERIFIED marks: the first and second gate reviews, the G7, G1 and G2 reviews (all by reading, nothing executed), the grants findings (read, not run), and caller tables made by reading.

### 5.2 What was NOT RUN (copied from the evidence files; nothing here is claimed to pass)
- Python 3.12: no test of the text fold, the gate or the redactor.
- PostgreSQL 17 (CI uses 17.10): only 16.15. The two concurrency tests ran twice each, no repeat loop.
- The full repository suite: only the files that mention the redactor, run map, text fold, cards or gate.
- The text fold's 240 mutants: 238 not run (G1). The redactor's 63 mutants: not run on the fold (G3). Whether they are still caught: UNVERIFIED. The gate's 66 and the cards' 51 (48 caught, 3 survived: A11 later caught, A43 later caught, A15 inherited survivor) were run.
- Type check; the real limits and spend-refusal code (not built at that time); a live model call.
- The install of the gate at any call site; the run loop's mapping of stop and budget errors.
- The tools `tools/p1d_corpus.py` and the generated fixtures (cards), line by line.
- The G4 build (host names, base64): no evidence file exists; the probe measured the earlier main code only.
- Mutant script for cards after step 5 in one run; the stop switch end to end.

### 5.3 Open requests to core-b (files exist in handover/core-c/requests)
1. requests/1-producers.patch (register the gate as a model caller).
2. requests/2-refused-before-response.md (the mark that lets the gate release a failed call). Contract sentence to add: "mark only if NO attempt was answered".
3. requests/3-bind-mapping-required.md.
4. requests/4-error-reason-run-map.md.
5. requests/5-card-ids-redact-defang.md.
Also: change the reply cost default from 0; supply the worst-case helper; map stop and budget errors in the run loop.
