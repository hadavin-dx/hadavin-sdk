# Round 9 head, tail and assembly (executed inside build-r9.py, after the rows)

def between(text, a, b=None):
    i = text.index(a)
    j = text.index(b, i) if b else len(text)
    return text[i:j]

def hsub(text, old, new):
    assert text.count(old) == 1, (old[:70], text.count(old))
    return text.replace(old, new)

# ------------------------------------------------------------------ computed facts
hdr = re.compile(r'^### (E-\d+): (\S+), line ([0-9]+)(?: \(and ([0-9]+)\))?, status (.+?), type (.+)$', re.M)
meta = []
for rid, raw in R.items():
    m = hdr.match(raw.split('\n')[0])
    assert m, rid
    meta.append(dict(id=rid, file=m.group(2), line=m.group(3) + (' (and %s)' % m.group(4) if m.group(4) else ''),
                     status=m.group(5).split(' (')[0].strip(), full=m.group(5), type=re.sub(r' \(.*\)', '', m.group(6)).strip(), type_full=m.group(6)))
stc = collections.Counter(x['status'] for x in meta)
fc = collections.Counter(x['file'] for x in meta)
tc = collections.Counter(x['type'] for x in meta)
apply_ids = [x['id'] for x in meta if x['status'] == 'Apply now']
hold_ids = [x['id'] for x in meta if x['status'] == 'Hold']
NROWS = len(meta)
assert stc['Hold'] == 12 and stc['Apply now'] == NROWS - 12

NEEDS = {
 'E-01': 'E-52', 'E-02': '-', 'E-03': '-', 'E-04': 'G1, ND7b', 'E-05': 'G1', 'E-06': 'ND2 (the number)', 'E-07': 'ND2, ND5 (second wording only)',
 'E-08': 'ND5 (second wording only)', 'E-09': 'ND1, ND4 (placeholders)', 'E-11': 'ND6 (flow rehearsal set-up)', 'E-12': 'G1 line before the message is sent; E-37',
 'E-13': 'G3', 'E-14': '-', 'E-15': '-', 'E-16': 'ND3 (default text)', 'E-17': '-', 'E-18': '-', 'E-19': '-', 'E-20': '-', 'E-21': '-', 'E-22': '-',
 'E-23': '-', 'E-24': 'E-25', 'E-25': 'E-24', 'E-26': '-', 'E-27': '-', 'E-28': '-', 'E-29': '-', 'E-30': 'ND1, ND9', 'E-31': 'ND10',
 'E-32': '-', 'E-33': '-', 'E-34': 'confirmation c', 'E-36': 'confirmation b', 'E-37': 'E-12; G1 (one bullet); ND7', 'E-38': 'ND3 (default text)',
 'E-39': 'ND3, G4', 'E-40': 'G1', 'E-41': 'G1', 'E-42': 'G1', 'E-43': '-', 'E-44': 'G1', 'E-45': 'G1', 'E-46': '-', 'E-47': '-',
 'E-48': 'ND7a', 'E-49': 'G5, ND6, ND8, E-50, E-53', 'E-50': 'G5, E-49, E-53', 'E-51': '-', 'E-52': '-', 'E-53': 'G5, ND8, E-49, E-50', 'E-54': '-'}
assert set(NEEDS) == set(R), set(NEEDS) ^ set(R)

# ------------------------------------------------------------------ intro
title = '# C4 steps versus decisions: exact edit list (round 9; draft by a builder, independent reviewers judge it)\n\n'
compared = between(head8, 'Compared: ', '\n\nRound history')
compared = hsub(compared, 'Nothing was run except text checks; the inputs were not edited.',
    'Round 9 also read `ORDERS.md` Q19 to Q34 (the answers of the studio lead of 2026-11-16, quoted as Q19 to Q34 where a row rests on one: Q23 on the contact delete, Q24 on the yes sentence, Q25 and Q26 on the cancel-by time) and the two round-8 reviews. D4 and D11 of the decision file need no row (D4 is about core patches that are not in the take path; D11 is about licence copies in another folder). Nothing was run except text checks; the inputs were not edited.')
compared = hsub(compared, 'D1 to D12 with that file\'s own numbers', 'D1 to D12 with that file\'s own numbers')
history = '''Round history: rounds 1 to 4 are in `resolve-r1.md` to `resolve-r4.md`; round 5 (`resolve-r5.md`) was reviewed by two independent reviewers (`review-c4-r5-design.md`: 0 Blockers, 4 Majors, 8 Minors; `review-c4-r5-naive.md`: 3 Blockers, 11 Majors, 8 Minors); round 6 (`resolve-r6.md`): `review-c4-r6-design.md` 0 Blockers, 4 Majors, 9 Minors, `review-c4-r6-naive.md` 8 Majors, many Minors; round 7 (`resolve-r7.md`): `review-c4-r7-design.md` 0 Blockers, 3 Majors, 7 Minors, `review-c4-r7-naive.md` 0 Blockers, 8 Majors, many Minors; round 8 (`resolve-r8.md`): `review-c4-r8-design.md` 0 Blockers, 6 Majors, 5 Minors, `review-c4-r8-naive.md` 3 Blockers, many Majors; round 9 (`resolve-r9.md`, money, secret and delete paths: no round cap) applies all of it. The result of round 9 is NOT reviewed yet. Earlier files are kept as `EDITS.round5.md` to `EDITS.round8.md`.

**Finding ids in the Why lines** name a finding of the review of the round written next to it: "design M1" and "design m1" are the Major and Minor findings of `review-c4-rN-design.md`; "naive A1" (for the studio lead) and "naive B1" (for the owner on take day) are findings of `review-c4-rN-naive.md`; "D-M1" and "D-M5" are findings of round 1 (`review-c4-r1.md`). Q19 to Q34 are answers of the studio lead in `ORDERS.md`.

'''
how_to_read = between(head8, '## How to read a row', '## Words used')
how_to_read = hsub(how_to_read, '(output in `resolve-r8-check-output.txt`)', '(output in `resolve-r9-check-output.txt`)')
how_to_read = how_to_read.rstrip('\n') + '''

**Hold rows (round 9):** the new text of every Hold row is fenced under a label that starts with `NEW [HOLD Gx: DO NOT APPLY]`. A Hold row is never applied until its gate is open, whatever the row's text says.

'''

words = '''## Words used in this file and in the owner texts (round 9)
One word keeps one meaning. The owner texts define their words in the list "Words used (read once)" of the sheet (E-52); E-01 only says who "the assistant" is.
- **the assistant** (owner texts) = Claude working with the owner; the sheet's old words "the lead" mean the same (E-01 and E-52 say so inside the sheet). **the lead** inside a quoted AGENT-SCOPE text = the Claude session that leads the work and talks to the owner (E-26 defines it there). **the studio lead** (this file) = the studio lead session that applies the rows, opens the gates and answers the NOT DECIDED items marked "studio lead". Outside the quoted texts this file writes "the studio lead" and never "the lead". "Lead" has five older meanings that this file keeps apart: the Claude session (the assistant), the studio lead, an enquiry (the public post keeps its own word "lead" for it), a "lead key" (now: **enquiry key**) and a "table of leads" (now: **table of enquiries**); the identifier that the owner chooses for one take is the **take id**, and nothing else is called an id, a tag or a lead id in new texts.
- **enquiry** = one made-up sales message sent through the flows. **contact** = the made-up person an enquiry creates in HubSpot. **enquiry key** = the made-up identifier the program gives an enquiry. **secret key** = a long text that works like a password for a service (HubSpot, the AI model provider); the sheet's old word "token" means the same. **password** = a text a person types (a database user's password, or the app password of a mailbox). Never a bare "key".
- **take** = one real recorded run on the owner's own test accounts (the sheet's "Words used"). **flows** = the automatic step chains that n8n runs. **model stage** = our small program that asks the AI model and enforces the money cap. **saved runs** = the past runs that n8n keeps and lists (n8n itself says "executions"). **preparation** = the last checks the assistant makes before it asks for the owner's yes (Phase 1); it includes the one preparation enquiry (E-49, held; the word is defined in E-49).
- **stand-in test** = the test on this laptop with stand-in programs and made-up data in plan v5 (D8, the loopback re-smoke). **flow rehearsal** = the first run of the changed flows on this laptop that follows it (D12). Both are planned at US$0 (EL-5); nothing about them is proven yet. The word "rehearsal" alone is not used in new texts.
- **counting check** = a small program of ours, not part of n8n, that counts mails, contacts and table rows. It is the one phrase used for this in E-15, E-18, E-31 and E-36. It has no read-only database user of its own (that user is not built; D3 parks it), so it is not claimed to be independent.
- **database server** = the one Postgres program in one **container**; **n8n's own database** and **the take's database** = the two databases on it; **database user** = a Postgres account. **login** = only a mailbox or HubSpot sign-in. (The decision file calls the parked proposal "four logins"; this file says "the proposal of four database users".)
- **spending window** = the last day and time the model stage may spend money, 2026-11-23 18:29 UTC = 23:59 IST (the sheet's old words: "window end"). The **last time to cancel** the secret key for the model is 2026-11-23 18:19 UTC = 23:49 IST (Q25: at least 10 minutes before the stop). **latest start time** = the latest time the take program accepts a start, about 18:14 UTC = 23:44 IST on that day (a reading of OWNER-STEPS line 171, UNVERIFIED by code).
- **Plan codes** (studio notes only; never put one in owner text): **DM** = the plan's row where n8n is killed while the mail is stored (a crash between sending the mail and recording in the take's database that it was sent). **crash case 1** = the plan's case "mail stored, reply held back" (the plan calls it E); **crash case 1, repeat** = the one repeat of it (the plan calls it E2). **NC** = the plan's row that lists the crash windows no test covers. **L4** = the plan's row for the read-only counting user (not built). **P14** = the plan's item "Windows browser reaches n8n inside WSL". **Step 1.2b** = the plan step that writes n8n's database settings; **S1b** and **step 1b** = the plan step that creates the database users, the two databases and the table; **step 2.7** = the plan check that every n8n table sits in n8n's own database; **step 12.5 and 12.5b** = the plan checks of `.n8n/config` and of the saved runs. **EG** = the plan's name for the list of n8n settings that switch off outgoing traffic. **Step 3.3** = the plan step that starts the model stage for the stand-in test against the stand-in model server on port 48767 with a made-up `stage.key`. **Plan UNVERIFIED item 1 and 4** = the plan's own list at its end (section "UNVERIFIED in this plan").

'''

key_gates = '''## Gates (a row marked Hold is NOT applied until its gate is open)
**Key (read first).** **ND** = a NOT DECIDED item (numbered 1 to 13 in the list below the gates). **Apply now** = the studio lead applies the row today to a working copy of the file named in the row (OWNER-STEPS v3, AGENT-SCOPE, DECISION-one-store). **Hold** = not applied until its gate is open. **Conditional** = applies only after a named answer (none today). **NEEDS-STUDIO-LEAD** = only the studio lead can supply the missing input; it is in none of the six inputs. **G1 to G5** = the five gates below. The "needs" column of the index names what a row waits for or depends on.
- **G1, the take program makes no delete call to HubSpot (E-04, E-05, E-40, E-41, E-42, E-44, E-45; carried into E-12 and E-37)**: D2 says the take never deletes contacts. Whether the code at the final head contains a delete call is NOT SETTLED (Q23): an earlier reading found one (`run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, `review-codebase-1.md` F-01); the r17 review (egm reviewer, 11:00Z) found no delete or archive path (only a GET, `rows_with_prefix`); line 1051 is UNVERIFIED stale text; the HubSpot key is not widened; the studio lead shows the final head's grep at re-pin. The gate is opened by the STUDIO LEAD (never by the builder and never by the owner) by writing the line `CODE-GATE G1 OPEN: <final head commit id>, <evidence file name>, route 1|2` into the newest checkpoint note, and only when all three hold: (1) one of two routes is shown by saved raw output: route 1, a delete call exists at the final head and a commit removes it, shown by a test that fails on the old code and passes on the new; route 2, no delete call exists, shown by the saved raw search of the final head (the Q23 grep: command and output) and a saved raw test output in which a fake HubSpot records every call the end-of-take step makes and none is a delete; (2) the same evidence shows the notice and the list the rows describe, or the studio lead lists the rows whose wording differs; (3) independent `egm:*` reviewers have read the diff (if any) and the output and their saved report lists no open Blocker or Major (delete and money path: no round cap). If OWNER-STEPS v3 or v4 is issued before the line exists, these rows stay unapplied and no paid take starts. E-12 (fact 4 of the yes message) and E-37 (one bullet) carry this gate into text that is applied now: the assistant cannot state fact 4 until the line exists, so it cannot send the message. **When G1 opens, the studio lead applies E-04, E-05, E-40, E-41, E-42, E-44 and E-45 together and deletes the bullet "NOT SETTLED, BEFORE ANY TAKE" of E-37** (rule R9). Whether the code prints the list of leftover contacts by enquiry key and contact id is UNVERIFIED.
- **G2, later wording only, Windows reaching n8n in WSL (E-07, E-08)**: E-07 and E-08 are Apply now with neutral words. G2 only decides a second wording: opened by the studio lead after reading the first-smoke evidence for plan item P14; the studio lead writes `ND5: proven <file>` or `ND5: not proven <file>`; if proven, the second wording in the Why of E-07 and E-08 replaces the neutral one.
- **G3, second edit pass (E-13)**: opened by the studio lead when the stand-in test result file (in `evidence-2`, its INDEX) exists and independent reviewers have read it; the studio lead writes the report name.
- **G4, saved-runs method (E-39)**: opened when NOT DECIDED 3 is answered (the answer decides the text).
- **G5, the preparation enquiry (E-49, E-50, E-53)**: the one made-up enquiry through the real accounts is not allowed by any scope row today (AGENT-SCOPE line 27 forbids a real key and answering a prompt), the route is not decided (NOT DECIDED 8) and nothing proves that a paid model call is impossible there (NOT DECIDED 6). Opened by the STUDIO LEAD only, by writing `GATE G5 OPEN: ND8 <A|B>, ND6 <A <evidence file>|B <owner message>>` into `ANSWERS-c4.md`, and only when both hold: (1) NOT DECIDED 8 is answered; (2) NOT DECIDED 6 is answered, and for A a saved raw test output shows the model stage started with the stand-in model and a made-up key file, read by independent `egm:*` reviewers whose saved report lists no open Blocker or Major (money path: no round cap). When G5 opens, the studio lead applies E-49, E-50 and E-53 together (rule R8); E-53 is not a condition of the gate. E-49 and E-53 are written for route B of NOT DECIDED 8; if the answer is A, the studio lead first rewrites item (a) of E-49 and does not apply E-53. The owner's consent for the enquiry is the written line `Yes, send the one enquiry on <day>` (E-49, E-53). While G5 is closed no preparation enquiry is sent (safe default; D8's "one made-up lead" is then not done and the take rests on the tests). E-11 and E-12 contain nothing of G5, so they apply now.

'''

how_used = '''## How the rows are used
**What "Apply now" means.** OWNER-STEPS v3 is archived, never edited or deleted (D10). The OWNER-STEPS rows are an edit list for a working copy of v3 and for OWNER-STEPS v4 (queue item C4b), which replaces v3 and keeps only what is still owner-only. An **Apply now** row is applied TODAY to the working copy of v3, so that v3 is safe to read even if v4 is late; the same text is then carried into v4. A row about a step that v4 strips (Phase 0 steps 1 to 7 and 9, perhaps step 8) falls away there: that is E-04 (step 7), E-06, E-07, E-08 and E-09 (step 8) and E-37 (the note in front of Phase 0). Everything else (Phase 1, steps 16 to 23, the status lists) stays in v4. The old advice "if v3 is read before v4 exists, apply only E-37 and E-52" is withdrawn: apply every Apply now row to v3 (E-37 needs E-12, because it points to the yes message that E-12 extends). When v4 is issued is NOT DECIDED 12 (no input gives a date); until it is issued, v3 plus the Apply now rows is what the owner reads. The AGENT-SCOPE rows patch that file in place; the DECISION-one-store rows (E-39, E-43, E-46, E-47) are applied by the studio lead (the file is in `inputs/`; E-39 changes the written record of an owner approval and is held). Ids are not renumbered: E-10 was deleted in round 3 (D7) and E-35 in round 5 (its content is part of E-34), so the ids run E-01 to E-54 without E-10 and E-35 (E-49 to E-53 are new in round 8, E-54 in round 9).

'''

counts = '''## Counts (computed by script, `resolve-r9.md` and `resolve-r9-check-output.txt`)
%d rows in total: E-01 to E-54 without E-10 and E-35. By file: OWNER-STEPS %d rows, AGENT-SCOPE %d rows, DECISION-one-store %d rows (the studio lead applies those). By status: **Apply now %d**, **Hold %d** (G1: E-04 E-05 E-40 E-41 E-42 E-44 E-45, G3: E-13, G4: E-39, G5: E-49 E-50 E-53; the Hold rows are %s), **Conditional 0**; total %d. The Apply now ids (%d) are: %s. Round 9 added E-54 (the Phase 1 heading), rewrote E-09 as sub-steps, split E-11 into a structural control, and put a `[HOLD Gx: DO NOT APPLY]` label on every held NEW text. Among the Apply now rows, E-36 has two texts (text W is live, text N is labelled DO NOT APPLY) and E-07 and E-08 apply their neutral wording (gate G2 only decides a second wording). By type: STALE %d, UNCLEAR WORD %d, MISSING STEP %d, CONTRADICTION %d (including the rows marked as code-change gated), DEFERRED %d (E-13); total %d.

''' % (NROWS, fc['OWNER-STEPS-realrun-v3.md'], fc['AGENT-SCOPE-DO-AND-DONT.md'], fc['DECISION-one-store.md'], stc['Apply now'], stc['Hold'],
       ', '.join(hold_ids), NROWS, stc['Apply now'], ', '.join(apply_ids), tc['STALE'], tc['UNCLEAR WORD'], tc['MISSING STEP'], tc['CONTRADICTION'], tc['DEFERRED'], NROWS)

# ------------------------------------------------------------------ not decided
nd = between(head8, '## NOT DECIDED', '## FOR THE STUDIO LEAD TO CONFIRM')
nd = hsub(nd, '(items 1 to 11)', '(items 1 to 13)')
nd = hsub(nd, '(a) you type the password yourself into `n8n.env` in WSL, in an editor and NOT on a command line', '(a) the owner types the password himself into `n8n.env` in WSL, in an editor and NOT on a command line')
nd = hsub(nd, 'E-09 says only that you type the password into a file (a file is the only way planned);', 'E-09 says only that the owner types the password into a file (a file is the only way planned; the program that starts the database server reading the password from that file is UNVERIFIED); E-09 writes its steps with the placeholders `<password file name>`, `<folder>` and `<database user name>`, which this item and item 4 fill;')
nd = hsub(nd, '**Which database user\'s password you type for the n8n table steps**', '**Which database user\'s password the owner types for the n8n table steps**')
nd = hsub(nd, 'the studio lead names the database user (never the password); you type its password.', 'the studio lead names the database user (never the password); the owner types its password.')
nd = hsub(nd, 'Facts: for the tests on this laptop a paid call is excluded by the ABSENCE of the real key:', 'Facts: for the tests on this laptop a paid call is excluded by the ABSENCE of the real key, and since round 9 E-11 makes that a structural control for both tests (the model stage starts only with the stand-in model address on this laptop, 127.0.0.1, and a key file in the test\'s own folder; the assistant names both and waits for the owner\'s written reply):')
nd = hsub(nd, 'same cap, window end 2026-11-23 23:59 IST.`', 'same cap, spending window ends 2026-11-23 18:29 UTC = 23:59 IST.`')
nd = hsub(nd, '(the assistant asks you at clean-up whether to revoke; you revoke only after a clear yes)', '(the assistant asks the owner at clean-up whether to revoke; the owner revokes only after a clear yes, and the second ask comes before 18:19 UTC = 23:49 IST)')
nd = hsub(nd, 'you type `y`, the confirmation number and the take id yourself', 'the owner types `y`, the confirmation number and the take id himself')
nd = hsub(nd, '(B) the assistant posts the enquiry straight to the take\'s own n8n web address on this laptop;', '(B) the assistant posts the enquiry straight to the take\'s own n8n web address on this laptop, only after the owner\'s written `Yes, send the one enquiry on <day>` (E-49, E-53);')
nd = nd.rstrip('\n') + '''
12. **When OWNER-STEPS v4 is issued, and what "Apply now" does until then** (all OWNER-STEPS rows). Who answers: the studio lead. No input gives a date or a condition for v4 (queue item C4b; "tonight" in earlier drafts was a guess). Options: (a) issue v4 only after the Apply now rows are applied and the gates G1 and G5 are decided (v3 plus the rows is what the owner reads meanwhile); (b) issue v4 first and apply the rows to it only (v3 stays as it is and is unsafe to read: it still says "archived" and shows the old yes example). Cost: studio lead time only. Default: (a). Record: `ND12: a|b <date and time in UTC and IST>`.
13. **Words in OWNER-STEPS v3 that no row touches** (naive B16 of round 8). Examples: "plan-4 N-lite" (lines 1 and 133), the older word "the stage" (line 12), "smoke" (line 7) and the old second yes example of step 16 (line 92: "You answer in one line, for example: ..."; E-12 gives one example, so the studio lead deletes that old sentence when applying E-12 and E-52 together). Who answers: the studio lead. Options: (a) leave the words and rely on E-01 and E-52, which name the older words and their meaning; (b) one more row each (more rows, more review). Default: (a) for the words, and the old second example is deleted as said (it is the same text, replaced, not a new claim). Record: `ND13: a|b`.

'''

confirm = between(head8, '## FOR THE STUDIO LEAD TO CONFIRM', 'Removed in round 3')
confirm = hsub(confirm, 'that the end-of-take step no longer deletes (gate G1)', 'that the last step of the take program makes no delete call to HubSpot (gate G1; Q23)')
removed = between(head8, 'Removed in round 3', '## Rules for the studio lead')

rules = between(head8, '## Rules for the studio lead', '## Decision D5')
rules = hsub(rules, '## Rules for the studio lead (round 8)', '## Rules for the studio lead (round 9)')
rules = hsub(rules, '(E passed or E2 passed, not both missed)', '(crash case 1 passed or crash case 1, repeat passed, not both missed)')
rules = hsub(rules, 'the studio lead checks that the files named in the four facts exist (five once gate G5 is open), that the reviewers\' report lists no open Blocker or Major, and that the line `CODE-GATE G1 OPEN: ...` exists. If any is missing, the message is not sent.', 'the studio lead checks that the files named in the four facts exist (five once gate G5 is open), that the list of checks is attached, that the latest start time and the spending window are stated in UTC and IST, that the reviewers\' report lists no open Blocker or Major, and that the line `CODE-GATE G1 OPEN: ...` exists. If any is missing, the message is not sent.')
rules = hsub(rules, 'the assistant asks once more before the window ends (Mon 23 Nov 2026 18:29 UTC = 23:59 IST) and the studio lead writes', 'the assistant asks once more before 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 (the last time to revoke, Q25; the spending window itself ends 18:29 UTC = 23:59 IST) and the studio lead writes')
rules = rules.rstrip('\n') + '''
- **R9 (E-04, E-05, E-40, E-41, E-42, E-44, E-45, E-37)**: when gate G1 opens, apply E-04, E-05, E-40, E-41, E-42, E-44 and E-45 together and delete the bullet "NOT SETTLED, BEFORE ANY TAKE" of E-37 (it is true only until then). Before that, no one writes that the take program deletes contacts or that it no longer does (Q23).

'''

d5 = between(head8, '## Decision D5', '## The edit index')
d5 = hsub(d5, '(round 8)', '(round 9)')
d5 = hsub(d5, 'E-48 (applies always, with the safe default question).', 'E-48 (applies always, with the safe default question; the second ask and the last time to revoke are 18:19 UTC = 23:49 IST).')

index = '## The edit index (no texts here; the texts are in the row blocks below)\n| id | file | line | status | gate | needs | type |\n|---|---|---|---|---|---|---|\n'
for x in meta:
    g = re.search(r'gate (G\d)', x['full'])
    gate = g.group(1) if g else '-'
    if x['id'] in ('E-07', 'E-08'):
        gate = 'G2 (second wording only)'
    index += '| %s | %s | %s | %s | %s | %s | %s |\n' % (x['id'], x['file'], x['line'], x['status'], gate, NEEDS[x['id']], x['type_full'])
index += '\n'

head = title + compared + '\n\n' + history + how_to_read + words + key_gates + how_used + counts + nd + confirm + removed + rules + d5 + index

# ------------------------------------------------------------------ tail
tail = tail8
tail = tail.rstrip('\n') + '''

- Round 9 added: nothing was run except text and count checks by script (`resolve-r9-check-output.txt`). I did not read the code, the smoke evidence, any click path, `review-codebase-1.md` (NOT DECIDED 10), `WP6-RUNBOOK.md`, or the plan beyond the lines named at the top. Whether the take program contains a contact delete call at the final head is not settled (Q23) and nothing in this file claims either; the evidence is the studio lead's grep at re-pin. The mechanism that keeps a paid model call impossible in the flow rehearsal and in the preparation enquiry (ND6) is a control written in E-11, but that the model stage accepts a made-up key value and a stand-in address in the flow rehearsal is UNVERIFIED; the route of the preparation enquiry (ND8) is not decided; that the start program reads a database password from a file (E-09, ND1) is unproven; the click paths of E-04, E-48 and E-49 (HubSpot website, the model provider's key list) are unchecked; the latest start time of about 18:14 UTC = 23:44 IST comes from a reading of OWNER-STEPS line 171, not from the code; the new owner texts (E-04, E-09, E-11, E-12, E-14, E-15, E-16, E-18, E-37, E-48, E-49, E-52, E-54) are not yet read by a stranger; no one has checked that v4 can be written from these rows in one pass. The egm:egm-resolve skill was not used (see `resolve-r9.md`).
'''

# ------------------------------------------------------------------ assemble
body = pre_rows + '\n'.join(R[k].rstrip('\n') + '\n' for k in R)
full = head + body + '\n' + tail
# global word fixes outside OLD fences
for a, b in (('lead key', 'enquiry key'), ('table of leads', 'table of enquiries'),
             ('noting it in the table', "recording in the take's database that it was sent")):
    full = smart(full, a, b)
full = full.replace('\x01', ' ')
open(D + 'EDITS.md', 'w', encoding='utf-8').write(full)
print('written', len(full), 'rows', NROWS, 'apply', stc['Apply now'], 'hold', stc['Hold'])
