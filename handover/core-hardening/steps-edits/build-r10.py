import re, sys, importlib.util
spec = importlib.util.spec_from_file_location('rows', 'build-r10-rows.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ROWS = m.ROWS
t = open('EDITS.round9.md', encoding='utf-8').read()

def find_blocks(lines):
    infence = False; starts = []; heads = []
    for i, l in enumerate(lines):
        if l.strip() == '~~~~':
            infence = not infence; continue
        if infence: continue
        mm = re.match(r'### (E-\d+):', l)
        if mm: starts.append((i, mm.group(1)))
        if l.startswith('### E-') or l.startswith('## '): heads.append(i)
    return starts, heads

lines = t.split('\n')
starts, heads = find_blocks(lines)
ends = {}
for i, rid in starts:
    ends[rid] = min(h for h in heads if h > i)
# replace whole rows, bottom up
order = sorted([(i, rid) for i, rid in starts if rid in ROWS], reverse=True)
for i, rid in order:
    new = ROWS[rid].rstrip('\n').split('\n') + ['']
    lines[i:ends[rid]] = new
t = '\n'.join(lines)
# insert E-55, E-56 before "## Lines checked"
mark = '## Lines checked and found consistent'
assert t.count(mark) == 1
t = t.replace(mark, ROWS['E-55'].rstrip('\n') + '\n\n' + ROWS['E-56'].rstrip('\n') + '\n\n' + mark)

def sub(old, new, n=1):
    global t
    c = t.count(old)
    assert c == n, (c, n, old[:80])
    t = t.replace(old, new)

# ---------------- header ----------------
sub('# C4 steps versus decisions: exact edit list (round 9;', '# C4 steps versus decisions: exact edit list (round 10;')
sub('round 9 (`resolve-r9.md`, money, secret and delete paths: no round cap) applies all of it. The result of round 9 is NOT reviewed yet. Earlier files are kept as `EDITS.round5.md` to `EDITS.round8.md`.',
    'round 9 (`resolve-r9.md`): `review-c4-r9-design.md` 0 Blockers, 4 Majors, 7 Minors, `review-c4-r9-naive.md` 2 Blockers, 13 Majors, many Minors; round 10 (`resolve-r10.md`, money, secret and delete paths: no round cap) applies all of it, or says why a finding is left. The result of round 10 is NOT reviewed yet. Earlier files are kept as `EDITS.round5.md` to `EDITS.round9.md`.')
sub('Round 9 also read `ORDERS.md` Q19 to Q34 (the answers of the studio lead of 2026-11-16, quoted as Q19 to Q34 where a row rests on one: Q23 on the contact delete, Q24 on the yes sentence, Q25 and Q26 on the cancel-by time)',
    'Round 9 also read `ORDERS.md` Q19 to Q34 (the answers of the studio lead of 2026-11-16, quoted as Q19 to Q34 where a row rests on one: Q23 on the contact delete, Q24 on the yes sentence, Q25 and Q26 on the revoke-by time)')
# Read first
sub('## How to read a row (quoting convention, round 6)',
'''## Read first (round 10)
- **Apply now** = an instruction to the studio lead: put this text into a working copy of the file named in the row. The original `OWNER-STEPS-realrun-v3.md` stays unedited in `inputs/`; the owner reads the working copy with all Apply now rows applied, and the studio lead names that file.
- **Hold** = do not apply until the named gate is open. **E-nn** = the number of one row of this file. **Conditional** = applies only after a named answer (none today).
- **The studio lead** = the Claude session on the laptop that applies the rows, opens the gates and answers the NOT DECIDED questions; **the owner** = the person. **The assistant** (in owner texts) = Claude working with the owner.
- **builder** = a Claude session that writes or edits text or code; **runner** (evidence runner) = a session that runs tests and saves raw output and never judges; **round** = one pass of independent review followed by one batch of fixes; **re-pin** = the studio lead's step that points the demos at the final commit; **final head** = the newest commit of the take code.
- Studio terms that appear only in notes for the studio lead: `egm:*` = the independent review programs; r17 review = one of them (an earlier one); C4b = the queue item that writes OWNER-STEPS v4; `evidence-2` and its INDEX = the folder where the stand-in test results are written; S9-n = a numbered security item of the decision file; `smk_n8n` = a name in the plan; person A, B, C = the three made-up people the take sends; receiver = the mailbox that receives the take's mails; role = one named set of permissions.
- **Contact id and contact number**: the HubSpot number of one contact. Owner texts say "HubSpot contact number".

## How to read a row (quoting convention, round 6)''')
sub('The **last time to cancel** the secret key for the model is 2026-11-23 18:19 UTC = 23:49 IST (Q25: at least 10 minutes before the stop).',
    'The **last time to revoke** the secret key for the model is 2026-11-23 18:19 UTC = 23:49 IST (Q25: at least 10 minutes before the stop; to revoke is to delete it at the company that issued it, so that it stops working).')
# line 34
sub('OWNER-STEPS v3 is archived, never edited or deleted (D10). The OWNER-STEPS rows are an edit list for a working copy of v3 and for OWNER-STEPS v4 (queue item C4b), which replaces v3 and keeps only what is still owner-only.',
    'OWNER-STEPS v3 is archived, never edited or deleted (D10). The OWNER-STEPS rows are an edit list for a working copy of v3 (the studio lead names the file; the original stays unedited) and for OWNER-STEPS v4 (queue item C4b), which replaces v3 and keeps only what is still owner-only.')
sub('that is E-04 (step 7), E-06, E-07, E-08 and E-09 (step 8) and E-37 (the note in front of Phase 0).',
    'that is E-04 (step 7), E-06, E-07, E-08 (step 8) and E-37 (the note in front of Phase 0). E-09 does NOT fall away: it is the only place that says how the password file is made, so v4 carries it.')
sub('(E-37 needs E-12, because it points to the yes message that E-12 extends)', '(E-37 needs E-12, because it points to the request for your yes that E-12 describes)')
sub('so the ids run E-01 to E-54 without E-10 and E-35 (E-49 to E-53 are new in round 8, E-54 in round 9).',
    'so the ids run E-01 to E-56 without E-10 and E-35 (E-49 to E-53 are new in round 8, E-54 in round 9, E-55 and E-56 in round 10).')
# counts
sub('## Counts (computed by script, `resolve-r9.md` and `resolve-r9-check-output.txt`)', '## Counts (computed by script, `resolve-r10.md` and `resolve-r10-check-output.txt`)')
sub('52 rows in total: E-01 to E-54 without E-10 and E-35. By file: OWNER-STEPS 34 rows, AGENT-SCOPE 14 rows,', '54 rows in total: E-01 to E-56 without E-10 and E-35. By file: OWNER-STEPS 35 rows, AGENT-SCOPE 15 rows,')
sub('**Apply now 40**', '**Apply now 42**')
sub('**Conditional 0**; total 52. The Apply now ids (40) are:', '**Conditional 0**; total 54. The Apply now ids (42) are:')
sub('E-51, E-52, E-54. Round 9 added E-54', 'E-51, E-52, E-54, E-55, E-56. Round 10 added E-55 (the heading of step 22) and E-56 (a flag in front of AGENT-SCOPE line 20 while gate G1 is closed), rewrote E-09, E-11, E-12, E-13, E-14, E-16, E-39 and E-48. Round 9 added E-54')
sub('CONTRADICTION 12 (including the rows marked as code-change gated), DEFERRED 1 (E-13); total 52.', 'CONTRADICTION 14 (including the rows marked as code-change gated), DEFERRED 1 (E-13); total 54.')
# G1 text
sub('(E-04, E-05, E-40, E-41, E-42, E-44, E-45; carried into E-12 and E-37)', '(E-04, E-05, E-40, E-41, E-42, E-44, E-45; carried into E-12, E-37 and E-56)')
sub('**When G1 opens, the studio lead applies E-04, E-05, E-40, E-41, E-42, E-44 and E-45 together and deletes the bullet "NOT SETTLED, BEFORE ANY TAKE" of E-37** (rule R9).',
    '**When G1 opens, the studio lead applies E-04, E-05, E-40, E-41, E-42, E-44 and E-45 together and deletes the bullet "NOT SETTLED, BEFORE ANY TAKE" of E-37 and the leading bullet that E-56 put in front of AGENT-SCOPE line 20** (rule R9).')
sub('E-12 (fact 4 of the yes message) and E-37 (one bullet) carry this gate into text that is applied now: the assistant cannot state fact 4 until the line exists, so it cannot send the message.',
    'E-12 (fact 4 of the request for your yes), E-37 (one bullet) and E-56 (one flag) carry this gate into text that is applied now: the assistant cannot state fact 4 until the line exists, so it cannot send the request.')
# ND edits
sub('Default: (a); E-09 says only that the owner types the password into a file (a file is the only way planned; the program that starts the database server reading the password from that file is UNVERIFIED);',
    'Default: (a); E-09 says that the owner types the table user\'s password into a password file (steps a to e) and n8n\'s own database user\'s password as one line of `n8n.env` (step g), and that the assistant opens neither (the programs that read them are UNVERIFIED);')
sub('Owner\'s answer text for (b): `Yes, at clean-up you may delete the saved runs only by removing the container of the database server, instead of turning saving off and deleting the runs first.` Record: `ND3: a|b <owner message>`.',
    'Owner\'s answer text for (b): `Yes, remove the container only` (the question and the exact reply are in E-16; no reply counts as No); the studio lead records it with the owner\'s written message. Record: `ND3: a|b <owner message>`.')
sub('Only one option is allowed: the app user (the user the n8n table steps use: plan v5 section 10 points to it; planned as a restricted user, not yet proven).', 'Only one option is allowed: the table user (the database user the take\'s table steps use: plan v5 section 10 points to it; planned as a restricted user, not yet proven; the plan calls it the app user).')
sub('Default: the app user. Pass or fail: as for ND1 (a).', 'Default: the table user. Pass or fail: as for ND1 (a).')
sub('Answer: `7a: yes` / `7a: no, others use it` / `7a: not sure`.', 'The owner replies `yes`, `no, other things use it` or `not sure`; the studio lead records `7a: yes` / `7a: no, others use it` / `7a: not sure`.')
sub('Answer: `7b: app 1 read-only, app 2 exists` / `7b: no` / `7b: not sure`.', 'The owner replies in plain words; the studio lead records `7b: app 1 read-only, app 2 exists` / `7b: no` / `7b: not sure`.')
sub('so the studio lead deletes that old sentence when applying E-12 and E-52 together).', 'E-12 now includes that old sentence in its old text and replaces it).')
sub('Default: (a) for the words, and the old second example is deleted as said (it is the same text, replaced, not a new claim).', 'Default: (a) for the words; the old second example is replaced by E-12 itself, so the studio lead deletes nothing by hand.')
# confirmations
sub('(a reading or a source, not a decision; letters run a to f without gaps)', '(a reading or a source, not a decision; letters run a to j without gaps)')
sub('f. Whether the plan\'s step S1b and row L4 (the database users) still run, given D3.',
'''f. Whether the plan's step S1b and row L4 (the database users) still run, given D3.
g. The fourth saved credential: E-09 step f says the owner types the table user's password into n8n's form for a Postgres credential, besides HubSpot, the model and Gmail (plan v5 lines 223 and 505). OWNER-STEPS line 121 (step 22 item 1) and E-37 say "three credentials". Is it four, and does step 22 item 1 say four?
h. E-12 and E-48: on 23 Nov the assistant asks for no start later than 18:04 UTC = 23:34 IST (the program itself accepts about 18:14 UTC = 23:44 IST, UNVERIFIED), and if a take is still running at 18:19 UTC = 23:49 IST the owner revokes the model key anyway unless the assistant says otherwise. Both are the builder's choices from Q25. Confirm or change.
i. Q22(c) ("item 1 wording plus one honest sentence that a gap longer than the lease is not claimed") is in ORDERS as an answer about the v19 hand-off item 8. Round 10 did NOT add a lease sentence to the public post of E-17: no input says the post concerns a lease. If the studio lead means the post, the exact sentence is needed.
j. E-56 puts the UNVERIFIED flag as a bullet in front of AGENT-SCOPE line 20 because an edit inside the clause would overlap the held rows E-40 and E-44. Confirm that placement, or name another.''')
# rules
sub('that the reviewers\' report lists no open Blocker or Major, and that the line `CODE-GATE G1 OPEN: ...` exists. If any is missing, the message is not sent.',
    'that the reviewers\' report lists no open Blocker or Major, that the line `CODE-GATE G1 OPEN: ...` exists and that the rows of gate G1 (E-04, E-05, E-41, E-42) are applied. If any is missing, the request is not sent.')
sub('- **R9 (E-04, E-05, E-40, E-41, E-42, E-44, E-45, E-37)**: when gate G1 opens, apply E-04, E-05, E-40, E-41, E-42, E-44 and E-45 together and delete the bullet "NOT SETTLED, BEFORE ANY TAKE" of E-37 (it is true only until then).',
    '- **R9 (E-04, E-05, E-40, E-41, E-42, E-44, E-45, E-37, E-56)**: when gate G1 opens, apply E-04, E-05, E-40, E-41, E-42, E-44 and E-45 together and delete the bullet "NOT SETTLED, BEFORE ANY TAKE" of E-37 and the flag bullet of E-56 (they are true only until then).')
sub('If the owner wants the mail step filmed, he says so in his yes message;', 'If the owner wants the mail step filmed, he says so in his written reply to the request for your yes;')
sub('(E-48 (applies always, with the safe default question; the second ask and the last time to revoke are 18:19 UTC = 23:49 IST)', '(E-48 (applies always, with the safe default question; the second ask and the last time to revoke are 18:19 UTC = 23:49 IST)', 0) if False else None
# index
sub('| E-54 | OWNER-STEPS-realrun-v3.md | 85 | Apply now | - | - | UNCLEAR WORD |',
    '| E-54 | OWNER-STEPS-realrun-v3.md | 85 | Apply now | - | - | UNCLEAR WORD |\n| E-55 | OWNER-STEPS-realrun-v3.md | 119 | Apply now | - | E-48 | CONTRADICTION |\n| E-56 | AGENT-SCOPE-DO-AND-DONT.md | 20 | Apply now | G1 (the studio lead deletes it when G1 opens) | E-40, E-44 | CONTRADICTION |')
sub('| E-13 | OWNER-STEPS-realrun-v3.md | 99 (and 11) | Hold | G3 | G3 | DEFERRED |', '| E-13 | OWNER-STEPS-realrun-v3.md | 99 (and 11) | Hold | G3 | G3, stand-in test result (method) | DEFERRED |')

# ---------------- row patches ----------------
sub('(3) Tell the assistant which of the two apps the secret key in your file belongs to.', '(3) Tell the assistant which of the two apps you took the secret key from (do not show the key or the file).')
sub("Phase 0: set-up. The original deadline was Mon 16 Nov 2026 18:29 UTC = 23:59 IST; Sun evening was ideal. About 60 to 90 minutes if nothing were done yet.\n",
    "Phase 0: set-up. The original deadline was Mon 16 Nov 2026 18:29 UTC = 23:59 IST; it is not the spending window (that ends Mon 23 Nov 2026 18:29 UTC = 23:59 IST). Sun evening was ideal. About 60 to 90 minutes if nothing were done yet.\n")
sub('The yes message (step 16) lists this as its fourth fact.', 'The assistant\'s request for your yes (step 16) lists this as its fourth fact.')
sub('AT THE TAKE you type `y`, then the 6-digit confirmation number that the program shows (it is new for every take), a space and the take id, and then `end`, yourself. The take id',
    'AT THE TAKE you type three things yourself: (1) `y` and Enter; (2) the 6-digit confirmation number that the program shows (it is new for every take), a space and the take id, on one line; (3) later, `end`, when the assistant tells you. The take id')
sub("the assistant tells you when and where to type the three credentials into it.", "the assistant tells you when and where to type the credentials into it (HubSpot, the model, Gmail and the take's database; see step 8, sub-step f).")
sub("the Linux window of your laptop", "the Linux part of your laptop (WSL)")
sub("the Linux window of the laptop", "the Linux part of the laptop (WSL)")
sub("A failed read stops the take safely.", "A failed read stops the take safely (UNVERIFIED).")
sub("Round 9 (naive B9): \"recording in the take's database that it was sent\" (which table?) becomes", "Round 10 (design m5): the circular reason is removed; this row only states the crash clause that the post must carry. Round 9 (naive B9): \"recording in the take's database that it was sent\" (which table?) becomes") if False else None
sub("(a saved passwords)", "(a saved passwords)", 0) if False else None
sub("(2) whether a program step inside n8n can read n8n's encryption key (the long text that locks n8n's saved passwords)", "(2) whether a program step inside n8n can read n8n's encryption key (the long text that locks n8n's saved credentials)")
sub("the long text that locks n8n's saved passwords", "the long text that locks n8n's saved credentials", 0) if False else None
# E-49/50/53 wording
sub("the assistant posts the enquiry straight to the address of the take's own n8n", "the assistant sends the enquiry straight to the address of the take's own n8n")
# yes message bulk
t = t.replace('the yes message', 'the request for your yes').replace('your yes message', 'your reply to the request for your yes').replace('yes message', 'request for your yes')
t = t.replace('app user', 'table user') if 'app user' in t else t
# yes-example in E-12-like 'Linux window'
open('EDITS.md', 'w', encoding='utf-8').write(t)
print('ok', len(t))
