"""Round 11 builder: anchored patches of EDITS.md (every old string asserted to occur exactly once).
Reads EDITS.round10b.md, writes EDITS.md. No vendor words, no secrets."""
import re, sys, os
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
src = open(D + 'EDITS.round10b.md', encoding='utf-8').read()
T = src
errs = []

def sub(old, new, n=1):
    global T
    c = T.count(old)
    if c != n:
        errs.append(f'anchor count {c} (want {n}): {old[:70]!r}')
        return
    T = T.replace(old, new)

def row_span(rid):
    i = T.index(f'\n### {rid}: ') + 1
    m = re.compile(r'\n### E-\d\d: |\n## Lines checked and found consistent').search(T, i + 5)
    return i, (m.start() + 1 if m else len(T))

def rsub(rid, old, new, n=1):
    global T
    i, j = row_span(rid)
    seg = T[i:j]
    c = seg.count(old)
    if c != n:
        errs.append(f'{rid}: anchor count {c} (want {n}): {old[:70]!r}')
        return
    T = T[:i] + seg.replace(old, new) + T[j:]

def why_add(rid, text):
    global T
    i, j = row_span(rid)
    seg = T[i:j]
    lines = seg.split('\n')
    idx = [n for n, l in enumerate(lines) if l.startswith('Why:')]
    if len(idx) != 1:
        errs.append(f'{rid}: Why lines {len(idx)}'); return
    lines[idx[0]] = lines[idx[0]].rstrip() + ' ' + text
    T = T[:i] + '\n'.join(lines) + T[j:]

def set_new(rid, body, nth=0):
    """replace the body of the nth NEW block of a row"""
    global T
    i, j = row_span(rid)
    seg = T[i:j]
    lines = seg.split('\n')
    k = 0; n_new = -1; pos = 0
    while k < len(lines):
        l = lines[k]
        if re.match(r'^NEW[^\n]*:$', l) and k + 1 < len(lines) and lines[k + 1] == '~~~~':
            n_new += 1
            if n_new == nth:
                e = k + 2
                while lines[e] != '~~~~': e += 1
                lines[k + 2:e] = body.split('\n')
                T = T[:i] + '\n'.join(lines) + T[j:]
                return
        k += 1
    errs.append(f'{rid}: NEW block {nth} not found')

def set_label(rid, old_label, new_label):
    rsub(rid, old_label + '\n~~~~', new_label + '\n~~~~')

# ============ header and counts ============
sub('(round 10, second pass r10b; draft by a builder, independent reviewers judge it)', '(round 11, batched fix pass after the round 10 reviews; draft by a builder, independent reviewers judge it)')
sub('Round 10b (second pass of round 10; `resolve-r10.md`, section r10b) finishes the findings that the first pass did not fix. The result of round 10b is NOT reviewed yet. Earlier files are kept as `EDITS.round5.md` to `EDITS.round9.md` and `EDITS.round10a.md` (the first pass of round 10).',
    'Round 10b (second pass of round 10; `resolve-r10.md`, section r10b) finished the findings that the first pass did not fix; its result was reviewed (`review-c4-r10-design.md`: 0 Blockers, 4 Majors, 9 Minors; `review-c4-r10-naive.md`: 2 Blockers, 9 Majors, 12 Minors; the independent evidence run is `evidence-r10b-independent/00-SUMMARY.md`). Round 11 (`resolve-r11.md`, money, secret and delete paths: no round cap) applies all of those findings in one batch. The result of round 11 is NOT reviewed yet. Earlier files are kept as `EDITS.round5.md` to `EDITS.round9.md`, `EDITS.round10a.md` (the first pass of round 10) and `EDITS.round10b.md` (the second pass).')
sub('**Hold rows (round 9):** the new text of every Hold row is fenced under a label that starts with `NEW [HOLD Gx: DO NOT APPLY]`. A Hold row is never applied until its gate is open, whatever the row\'s text says. The one other held text is text N of E-36 (a second text inside an Apply now row): its label is `NEW [HOLD Cb: DO NOT APPLY]`, where Cb means confirmation b below. A script that applies the NEW blocks must skip every block whose label contains `[HOLD`.',
    '**Hold rows (round 9, changed in round 11):** the new text of every Hold row is fenced under a label that starts with `NEW [HOLD Gx: DO NOT APPLY]` (E-13 has two blocks, labelled `NEW [HOLD G3: DO NOT APPLY] (1)` and `NEW [HOLD G3: DO NOT APPLY] (2)`; E-39 has one). A Hold row is never applied until its gate is open, whatever the row\'s text says. No Apply now row has a held block: every Apply now row has exactly ONE NEW block (checked by script). The held second wording of E-36 (text N) is no block any more; it is quoted in the Why of E-36, so a script cannot apply it by mistake. A script must apply only the NEW blocks of rows whose status is Apply now. A script that applies every NEW block of the file whatever the status column says would apply 13 held blocks (12 Hold rows, E-13 with two blocks), so it is wrong; every one of those blocks carries the label `[HOLD`, and a script that skips such labels is safe.')
sub('so the ids run E-01 to E-56 without E-10 and E-35 (E-49 to E-53 are new in round 8, E-54 in round 9, E-55 and E-56 in round 10).',
    'so the ids run E-01 to E-58 without E-10 and E-35 (E-49 to E-53 are new in round 8, E-54 in round 9, E-55 and E-56 in round 10, E-57 and E-58 in round 11).')
sub('E-09 does NOT fall away: it is the only place that says how the password file is made, so v4 carries it.',
    'E-09 does NOT fall away: it is the only place that says how the password file is made, so v4 carries it, and v4 puts those steps in a step of their own before step 8 (the file is made before the database server and n8n start; the rest of step 8 comes after n8n runs).')
sub('`resolve-r10.md` and `resolve-r10b-check-output.txt`)', '`resolve-r11.md` and `resolve-r11-check-output.txt`)')
sub('54 rows in total: E-01 to E-56 without E-10 and E-35. By file: OWNER-STEPS 35 rows, AGENT-SCOPE 15 rows,',
    '56 rows in total: E-01 to E-58 without E-10 and E-35. By file: OWNER-STEPS 37 rows, AGENT-SCOPE 15 rows,')
sub('**Apply now 42**, **Hold 12**', '**Apply now 44**, **Hold 12**')
sub('**Conditional 0**; total 54. The Apply now ids (42) are:', '**Conditional 0**; total 56. The Apply now ids (44) are:')
sub('E-52, E-54, E-55, E-56. Round 10 added E-55', 'E-52, E-54, E-55, E-56, E-57, E-58. Round 11 added E-57 (step 21: the secret key for the model is not revoked after the cut but right after the last take) and E-58 (the row of the send table that says when retirement screenshots go to the assistant), relabelled the two held blocks of E-13, made text N of E-36 a quotation in the Why instead of a second NEW block, and rewrote E-09, E-12, E-16, E-17, E-37, E-48 and E-53 (E-53 is a plain MUST NOT). Round 10 added E-55')
sub('Among the Apply now rows, E-36 has two texts (text W is live, text N is labelled DO NOT APPLY) and E-07 and E-08',
    'Among the Apply now rows, E-36 has one NEW block (text W; text N is only quoted in its Why) and E-07 and E-08')
sub('CONTRADICTION 14 (including the rows marked as code-change gated), DEFERRED 1 (E-13); total 54.',
    'CONTRADICTION 16 (including the rows marked as code-change gated), DEFERRED 1 (E-13); total 56.')

# ============ NOT DECIDED / CONFIRM / RULES ============
sub('and the assistant never opens the file (no code change; the assistant cannot check the value;',
    'and the assistant creates the file with its other settings (no password) before the owner adds his line and does not open it afterwards (no code change; the assistant cannot check the value;')
sub('Option B: ONE paid call, outside the take\'s 3 calls',
    'Option B (needs a new AGENT-SCOPE row first, because E-53 is a plain MUST NOT and E-11 says the assistant never starts the model stage with the real key file: the studio lead writes the row that says who starts the stage and how, and reconciles E-11): ONE paid call, outside the take\'s 3 calls')
sub('Default: (a). Record: `ND14: a|b <the exact sentence for b>`.',
    'Default: (a). ANSWERED by the studio lead: (a), no lease sentence in the public post (ORDERS.md, section "LEAD ANSWERS to your 15:49Z QUESTIONS block", item L-Q22c, 2026-11-16); the studio lead still writes the line `ND14: a` into `ANSWERS-c4.md`. Record: `ND14: a|b <the exact sentence for b>`.')
sub('g. The fourth saved credential: E-09 step f says the owner types the table user\'s password into n8n\'s form for a Postgres credential, besides HubSpot, the model and Gmail (plan v5 lines 223 and 505). OWNER-STEPS line 121 (step 22 item 1) and E-37 say "three credentials". Is it four, and does step 22 item 1 say four?',
    'g. The saved credentials in the take\'s n8n: E-09 step f and E-37 now say THREE (the sender mailbox, HubSpot and the take\'s database), the same as OWNER-STEPS line 75 and line 121 (step 22 item 1, "the 3 credentials"). The secret key for the model is never typed into n8n: the model stage reads it from a key file (design review r10 M1). Confirm that no flow node of the take calls the AI model with a credential of its own (plan v5 lines 223 and 505 list a Postgres credential, not a model credential; UNVERIFIED beyond that reading). If a model credential does exist, E-09, E-37, E-48 and step 22 item 1 must change.')
sub('Both are the builder\'s choices from Q25. Confirm or change.',
    'Both are the builder\'s choices from Q25. CONFIRMED by the studio lead (ORDERS.md, "LEAD ANSWERS to your 15:49Z QUESTIONS block", item L-23NOV, 2026-11-16): latest start Mon 23 Nov 2026 18:04 UTC = 23:34 IST, key revoked by 18:19 UTC = 23:49 IST even if a take runs, no take planned on 23 Nov (the take targets Wed 18 Nov). The 18:14 UTC = 23:44 IST that the program accepts stays a reading of line 171, UNVERIFIED by code.')
sub('- **R1 (E-17)**: after the stand-in test, delete the clause "a crash at exactly the moment between sending the mail and recording in the take\'s database that it was sent may send the mail twice"',
    '- **R1 (E-17)**: after the stand-in test, delete the clause "a crash at exactly the moment between sending the mail and recording that it was sent may send the mail twice"')
sub('- **R3 (E-36)**: text W applies by default; text N applies only if confirmation b is answered yes.',
    '- **R3 (E-36)**: text W applies by default (it is the one NEW block of the row); text N is quoted in the Why of E-36 and is applied only if confirmation b is answered yes, by the studio lead replacing text W with the quoted text N by hand in the working copy before the post is written.')
sub('he says so in his written reply to the request for your yes; the assistant then reads', 'he says so in a message that he sends before his reply to the request for your yes; the assistant then reads')

# ============ index ============
sub('| E-56 | AGENT-SCOPE-DO-AND-DONT.md | 20 | Apply now |', '| E-56 | AGENT-SCOPE-DO-AND-DONT.md | 20 | Apply now |')  # presence check
m = re.search(r'\| E-56 \| AGENT-SCOPE-DO-AND-DONT\.md \| 20 \| Apply now \|[^\n]*\n', T)
if not m: errs.append('index E-56 line not found')
else:
    T = T[:m.end()] + '| E-57 | OWNER-STEPS-realrun-v3.md | 116 | Apply now | - | E-48, E-55 | CONTRADICTION |\n| E-58 | OWNER-STEPS-realrun-v3.md | 147 | Apply now | - | E-48, E-55, E-57 | CONTRADICTION |\n' + T[m.end():]
sub('| E-37 | OWNER-STEPS-realrun-v3.md | 27 | Apply now | - | E-12; G1 (one bullet); ND7 | STALE |', '| E-37 | OWNER-STEPS-realrun-v3.md | 27 | Apply now | - | E-09, E-12; G1 (one bullet); ND7 | STALE |')

# ============ E-03 ============
rsub('E-03', 'The assistant does everything else (start the database server, the model stage and n8n, import the flows, run the checks).',
     'The assistant does everything else (start the database server, the model stage (our small program that asks the AI model and keeps the money cap) and n8n, import the flows (the automatic step chains that n8n runs), run the checks).')
rsub('E-03', 'You do nothing for the two tests unless the assistant asks you, for example to start Docker Desktop (the program that runs containers).',
     'For the two tests you only answer "ok" or "no" in writing before each test (Phase 1 below says what you are agreeing to) and you do what the assistant asks, for example start Docker Desktop (the program that runs containers).')
why_add('E-03', 'Round 11 (naive minor, design m8): "model stage" and "flows" are explained where line 5 first uses them (E-01 promised an explanation in the list below, which comes later), and the old sentence "You do nothing for the two tests unless the assistant asks you" contradicted E-11, which needs the owner\'s written "ok" before each test.')

# ============ E-04, E-42, E-41 ============
rsub('E-04', 'After the take you delete this take\'s contacts by hand in the HubSpot website. The assistant gives you the list:',
     'After the take you delete this take\'s contacts by hand in the HubSpot website, only the contacts on the assistant\'s list and no other contact. The assistant gives you the list:')
why_add('E-04', 'Round 11 (design m5): the owner deletes only the contacts on the list.')
rsub('E-42', 'You delete this take\'s contacts by hand in the HubSpot website, and the assistant gives you the count',
     'You delete by hand in the HubSpot website only this take\'s contacts that are on the assistant\'s list, no other contact, and the assistant gives you the count')
rsub('E-42', 'if you close the window or press Ctrl-C early', 'if you close the WSL terminal or press Ctrl-C early')
why_add('E-42', 'Round 11 (design m5, naive minor): only the contacts on the list are deleted; "the window" becomes "the WSL terminal" (E-52), because "window" also means the spending window.')
rsub('E-41', 'Ctrl-C or closing the window also ends the take and removes no contact.', 'Ctrl-C or closing the WSL terminal also ends the take and removes no contact.')
why_add('E-41', 'Round 11 (naive minor): "the window" becomes "the WSL terminal" (E-52).')

# ============ E-06, E-07, E-08: "web address" ============
rsub('E-06', 'NEW (exact):\n~~~~\nthe address the assistant gives (it is NOT', 'NEW (exact):\n~~~~\nthe web address the assistant gives (it is NOT')
rsub('E-06', 'the assistant tells you the whole address;', 'the assistant tells you the whole web address;')
why_add('E-06', 'Round 11 (naive M6): "address" is always "web address" or "mail address" in the edited texts (E-52).')
rsub('E-07', 'it is not yet confirmed that your Windows browser can open the address the assistant gives you for the take\'s n8n. n8n runs inside WSL, the Linux part of your laptop (WSL). The plan says an earlier trial (the first smoke) showed it, but nobody on this branch has read that evidence. The assistant checks this with you before you type anything. If your browser cannot open the address, stop, tell the assistant, and type nothing until the assistant says the address works)',
     'it is not yet confirmed that your Windows browser can open the web address the assistant gives you for the take\'s n8n. n8n runs inside the Linux part of your laptop (called WSL). The plan says an earlier trial (the first smoke) showed it, but nobody on this branch has read that evidence. The assistant checks this with you before you type anything. If your browser cannot open the web address, stop, tell the assistant, and type nothing until the assistant says the web address works)')
rsub('E-07', '"the first smoke showed that your Windows browser can open the address the assistant gives you for the take\'s n8n. The assistant checks it again with you before you type anything)"', '"the first smoke showed that your Windows browser can open the web address the assistant gives you for the take\'s n8n. The assistant checks it again with you before you type anything)"')
rsub('E-07', '"the first smoke showed that your Windows browser can open the address the assistant gives you for the take\'s n8n; the assistant checks it again with you before you type anything)"', '"the first smoke showed that your Windows browser can open the web address the assistant gives you for the take\'s n8n; the assistant checks it again with you before you type anything)"')
why_add('E-07', 'Round 11 (naive M6, minor): "address" becomes "web address"; "WSL, the Linux part of your laptop (WSL)" no longer repeats WSL.')
rsub('E-08', '8. Whether the Windows browser can open the address that the assistant gives for n8n. n8n runs inside WSL, the Linux part of the laptop (WSL).',
     '8. Whether the Windows browser can open the web address that the assistant gives for n8n. n8n runs inside the Linux part of the laptop (called WSL).')
why_add('E-08', 'Round 11 (naive M6, minor): "web address"; WSL is no longer repeated.')

# ============ E-09 ============
E09 = '''host, database and user as the assistant names them; password = the password of THAT database user. You make the password file first, in the sub-steps a to e below, and only when the assistant sends you a message that starts "Create the password file". Do not start sub-step a before that message. This part comes BEFORE the assistant starts the database server and n8n, so the assistant asks for it first, although the rest of step 8 waits until n8n is running. (A database user is an account inside the database program Postgres. Its password is not an app password and not a secret key.) The assistant starts the database server itself; you do not start anything. Its message gives you three names that you use below: `<folder>` (a folder on the Linux disk), `<password file name>` and `<database user name>`. Wherever you see a name in angle brackets, you type the name from that message and not the brackets. The assistant never tells you the password.
   a. Ask the assistant to stop looking at your display (the laptop screen) and your clipboard (the place where copied text waits), and wait for its written reply "not looking". This is a promise by the assistant, not a control: nothing in the computer stops it from looking, because it shares your Linux user, your clipboard and your screen, and a file that only you may read (step d) can still be read by the assistant. The same promise is asked again every time you type a password (steps f and g). The assistant looks again only after you write "you may look again".
   b. Open a WSL terminal: the program in which you type commands to the Linux part of your laptop (WSL). Click Start, type the name of your Linux program (for example `Ubuntu`; the assistant tells you the name if you do not know it) and press Enter. This click path is not checked. In the terminal type `umask 077` and press Enter (every file you make in this terminal is then readable by you only). Type `cd <folder>` and press Enter, with the folder from the assistant's message (a folder on the Linux disk, never under `/mnt/c/...`). Type `nano <password file name>` and press Enter (nano is a simple text editor that opens inside the terminal; the file is new and empty).
   c. Type ONE line: the password for the database user `<database user name>`. Make it at least 20 letters and digits, used nowhere else and different from the password of n8n's own database user. Press Ctrl+O and then Enter to save the file, then Ctrl+X to close nano. Never type the password as a word inside a command line, because the shell saves every command line in a history list.
   d. Type `chmod 600 <password file name>` and press Enter (this keeps other Linux users out; it does not keep the assistant out).
   e. Write to the assistant: "password file created", the file's path and "you may look again". Never write the password or the content of the file. The assistant does not open the file; the program that starts the database server is planned to read the password from that file (not yet proven). If the assistant tells you that the program cannot read it, you type the password nowhere else until the assistant tells you how.
   f. Later, after the assistant tells you that n8n is running, it also tells you when to type the SAME password into n8n's form for the saved credential of the take's database. n8n holds three saved credentials for the take: the sender mailbox, HubSpot and the take's database. The secret key for the model is never typed into n8n: the model stage reads it from a key file. Repeat sub-step a first (ask, wait for "not looking"), type the password, then write "you may look again".
   g. A second password belongs to n8n's own database user. It is one line in the file `n8n.env`, which is not the password file. Before you type it, the assistant creates `n8n.env` in the folder it names, with its other settings (none of them is a password). You do NOT repeat sub-steps a to e, because that would make a second file. Instead: repeat sub-step a; in the WSL terminal, in the same folder, type `nano n8n.env` and press Enter; move to the end of the file with the arrow keys; type the one new line that the assistant gives you in the form `<line name>=<password>` (replace `<password>` with a new password of at least 20 letters and digits, used nowhere else and different from the first one); save and close as in sub-step c; type `chmod 600 n8n.env` and press Enter; write "n8n.env done" and "you may look again". The assistant does not open `n8n.env` after you added the line. How n8n and the database server then read that password is planned, not yet proven.'''
set_new('E-09', E09)
why_add('E-09', 'Round 11 (naive B1, design M1, minors 2, 3 and 9): (a) the steps can now be carried out by a person who has never used a terminal: how to open a WSL terminal (click path unchecked), how to change into the folder, what nano is and how to save and close it, `umask 077` before the file exists (as OWNER-STEPS line 58 does) and `chmod 600` after; (b) the three names are filled by the assistant\'s message, and the text says so; (c) WHEN to start is stated: only after the assistant\'s message "Create the password file", before the database server and n8n start, although the rest of step 8 waits for "n8n is running" (E-37 says the same); v4 puts these steps in a step of their own; (d) sub-step g no longer says "repeat a to e" (that made a second file or overwrote `n8n.env`): the assistant creates `n8n.env` with its other settings first (so "never opens n8n.env" now means: not after the owner added his line), and the owner adds one line with nano; (e) credentials: THREE saved credentials (the sender mailbox, HubSpot, the take\'s database), as OWNER-STEPS lines 75 and 121 say; the "fourth saved credential, besides HubSpot, the model and Gmail" of round 10 was wrong because the model stage reads its secret key from a key file, so typing it into n8n would put a paid secret in n8n\'s database outside the model stage\'s spend record (confirmation g).')

# ============ E-11 unchanged ============

# ============ E-12 ============
rsub('E-12', 'The form is: "stand-in test: N1 pass, 0 missed, 0 not run; flow rehearsal: N2 pass, 0 missed, 0 not run". N1 and N2 are the numbers of checks on the list of each test. "Missed" means the check could not see what it was looking for. "Not run" means the check was never carried out.',
     'The form is: "stand-in test: N1 pass, 0 missed, 0 not run; flow rehearsal: N2 pass, 0 missed, 0 not run; crash check: tested or untested". N1 is the number of checks of the stand-in test that ended "pass", and N2 is the same for the flow rehearsal. Each must equal the number of checks on that test\'s list, not counting the crash check. The crash check (see below) has its own slot and is never counted in N1, N2, "missed" or "not run". "Missed" means the check could not see what it was looking for. "Not run" means the check was never carried out.')
rsub('E-12', 'No take is planned for 23 Nov. If the assistant asks for one that day, it asks for no start later than',
     'No take is planned for 23 Nov, and the assistant asks for none unless it has first shown you the studio lead\'s written reading of the final take program on three points: when the program can first spend money, whether it refuses to start after the end of the spending window, and what it does and what exit code it returns when its secret key is revoked during a run. If it then asks for a take that day, it asks for no start later than')
rsub('E-12', 'that check counts as "crash check untested" (it is not counted as missed): the request must say',
     'that check counts as "crash check untested" (it is not counted in N1, N2, "missed" or "not run"): the request must say')
rsub('E-12', '- `<take id>` is the short name you chose for this take. `<N1>` and `<N2>` are the two numbers in the request.',
     '- `<take id>` is the short name you choose for this take, new every take. Use only lowercase letters, digits and hyphens, start with a letter, keep it to at most 20 characters and use no spaces; it becomes part of the take\'s mail addresses (`take-<id>-a@example.com`). This rule is the assistant\'s safe choice and is not read from the program (UNVERIFIED): if the program refuses the id, you choose another one. Choose it before you reply, and use the same id in your reply and in step 17. `<N1>` is the number that the request gives for the checks of the stand-in test that ended "pass", and `<N2>` the same for the flow rehearsal; type exactly those two numbers.')
rsub('E-12', '- The last part, "I know that the assistant shares my Linux user, my clipboard and my screen.", is REQUIRED. Without it the assistant does not start the take.',
     '- The last part, "I know that the assistant shares my Linux user, my clipboard and my screen.", is REQUIRED. Without it the assistant does not start the take. Your Linux user is your sign-in to the Linux part of your laptop (WSL); the programs that the assistant starts there run under it, so they can read every file that you can read.')
rsub('E-12', 'You are the one who answers no: answer no if the request leaves out a fact, a file name or the list of checks, or says that anything did not pass. If a part of your reply is missing or wrong, the assistant does not start the take and tells you which part.',
     'You are the one who answers no: answer no if the request leaves out a fact, a file name or the list of checks, or says that anything did not pass. You may send other messages before your reply (a question, a request to show a result file, or the request about filming of step 19); only your reply in the form above can start a take. If a part of your reply is missing or wrong, the assistant does not start the take and tells you which part.')
why_add('E-12', 'Round 11 (naive B2, M2, M3, design minor 1, confirmation h): (a) the crash check has its own slot ("crash check: tested or untested") and is never counted in N1, N2, "missed" or "not run", so the fixed "0 missed, 0 not run" is true also when the crash check is untested, and a slot says which number to type (the number that the request gives); (b) "Linux user" is explained in the closing bullet; (c) the take id has a written rule (a safe choice, UNVERIFIED against the program) and is chosen before the reply; (d) the owner may send other messages before the one-line reply (so E-14 can ask for filming in a message that comes before the reply); (e) Q25\'s condition for any take on 23 Nov (the studio lead\'s reading of the final take program, Q27, shown first) is now in the owner text, in plain words; the studio lead confirmed 18:04 UTC = 23:34 IST and the revoke by 18:19 UTC = 23:49 IST (confirmation h).')

# ============ E-13 labels ============
set_label('E-13', 'NEW 1 [HOLD G3: DO NOT APPLY] (exact; template, the part in angle brackets is filled from the stand-in test result when gate G3 opens):', 'NEW [HOLD G3: DO NOT APPLY] (1) (exact; template, the part in angle brackets is filled from the stand-in test result when gate G3 opens):')
set_label('E-13', 'NEW 2 [HOLD G3: DO NOT APPLY] (exact; template, as NEW 1):', 'NEW [HOLD G3: DO NOT APPLY] (2) (exact; template, as block 1):')
why_add('E-13', 'Round 11 (design M4): the two labels now start with `NEW [HOLD G3: DO NOT APPLY]` like every other Hold label, followed by (1) and (2), so a script that skips on the prefix `NEW [HOLD` skips both.')

# ============ E-14 ============
rsub('E-14', 'say so in your written reply to the request for your yes (step 16); the assistant then first tells you',
     'say so in a message that you send before your reply to the request for your yes (step 16); the assistant then first tells you')
why_add('E-14', 'Round 11 (naive M1): the request to film the detail goes in a message BEFORE the one-line reply, which E-12 now allows.')

# ============ E-15 ============
rsub('E-15', 'or the row preview of the table step of n8n (the step that reads the table of enquiries).',
     'or the preview of rows that n8n shows for its step that reads the table of enquiries.')
why_add('E-15', 'Round 11 (naive minor): "the row preview of the table step of n8n" is replaced by a plain description.')

# ============ E-16 ============
E16 = '''deletes all saved runs of the take (made-up data only, owner decision 2026-11-16), turns off the setting that saves successful runs (a setting of the take's own n8n, not of each workflow), stops n8n, removes the take folder and the container of the database server. Before it removes anything, it copies the take's result file and its counts (names and numbers only, no secret) into a folder of its own on the Linux disk, outside the take folder; the assistant tells you that folder's name before the clean-up. It does this because removing the container is planned to delete n8n's database and the take's table of enquiries too. If the database files sit in a Docker volume (a storage area that Docker keeps apart from the container), removing the container alone may not delete them, and the assistant then also removes the volume that it created for the take; which of the two applies is UNVERIFIED. It removes only the container (and volume) that it started for the take: the assistant tells you the container's name, which is on the list of containers it recorded when the run began, and it touches no other container. The assistant does all of this and there is nothing for you to do. It reports each part as done or not done, and tells you before you start your own steps (items 2 to 6) if a part is not done. The stand-in test is planned to test only whether removing the container also removes the saved runs. A question may come before the clean-up: may the saved runs be deleted only by removing the container? The assistant asks it in the chat before it starts item 1, and only if the method is still undecided. You reply in the chat with exactly `Yes, remove the container only` or `No`. If you do not reply, the answer is No, and the assistant deletes the saved runs first, as described above'''
set_new('E-16', E16)
why_add('E-16', 'Round 11 (naive M4, design m6): the question has a place (the chat), a time (before item 1) and a condition (only if the method is still undecided; ND3 default says it is not asked otherwise), and silence is No with the stated consequence; the question is no longer buried in the middle of a sentence; the folder for the copied results is described (on the Linux disk, outside the take folder, named to the owner before the clean-up); the case of a Docker volume is stated as UNVERIFIED and handled (the assistant also removes the volume it created).')

# ============ E-17 ============
rsub('E-17', '**a lead sent twice with the same id is processed once; a crash at exactly the moment between sending the mail and recording in the take\'s database that it was sent may send the mail twice**',
     '**a lead sent twice with the same id is processed once; a crash at exactly the moment between sending the mail and recording that it was sent may send the mail twice**')
why_add('E-17', 'Round 11 (naive minor): the words "in the take\'s database" are dropped from the public clause, because a reader of the post does not know which database is meant; the clause says the same thing without it. E-36 and R1 quote the new clause.')

# ============ E-22 ============
rsub('E-22', 'the second door (the hook door: the second way into the flows, named after the flow `mf-hook`), and a crash',
     'the second door (the hook door: the second way into the flows), and a crash')
why_add('E-22', 'Round 11 (naive minor): the flow name `mf-hook` is removed from the owner text (it stays in the Why above).')

# ============ E-36 ============
set_label('E-36', 'NEW (exact; TEXT W, the default and the only live text until confirmation b is answered yes in writing):', 'NEW (exact; the only text of this row, called text W; the second wording, text N, is quoted in the Why and is no block):')
# remove the second (held) block of E-36
i, j = row_span('E-36')
seg = T[i:j]
n0 = seg.index('NEW [HOLD Cb: DO NOT APPLY]')
n1 = seg.index('Why:')
seg = seg[:n0] + seg[n1:]
T = T[:i] + seg + T[j:]
rsub('E-36', 'a crash at exactly the moment between sending the mail and recording in the take\'s database that it was sent may send the mail twice**." With text N it reads "... and counts the mails and contacts on its own credentials, and the table of enquiries with a small counting program of ours (not part of n8n); **a lead ...**".',
     'a crash at exactly the moment between sending the mail and recording that it was sent may send the mail twice**." With text N it reads "... and counts the mails and contacts on its own credentials, and the table of enquiries with a small counting program of ours (not part of n8n); **a lead ...**".')
rsub('E-36', 'the clause of E-17 follows in the same line and reads exactly: "a crash at exactly the moment between sending the mail and recording in the take\'s database that it was sent may send the mail twice"',
     'the clause of E-17 follows in the same line and reads exactly (round 11 wording): "a crash at exactly the moment between sending the mail and recording that it was sent may send the mail twice"')
why_add('E-36', 'Round 11 (independent evidence r10b, design M4 style): text N is no longer a second NEW block. A script that applied every NEW block to this row failed on its second block ("old text not found", because text W had already replaced it) and would have applied held text. Now the row has ONE NEW block. TEXT N (held, not applied; apply by hand only if confirmation b is answered yes in writing, replacing text W; rule R3): "counts the mails and contacts on its own credentials, and the table of enquiries with a small counting program of ours (not part of n8n)".')

# ============ E-37 ============
E37 = '''## Phase 0: set-up. This phase is mostly done already (see the note below). The deadline that this heading used to carry, Mon 16 Nov 2026 18:29 UTC = 23:59 IST, no longer counts. The spending window is another thing: it ends Mon 23 Nov 2026 18:29 UTC = 23:59 IST. If nothing had been done yet, the phase would take about 60 to 90 minutes.

Most of Phase 0 is already done. Read this note first: where it differs from the steps below, this note applies.
- DONE, from your own statement of 2026-11-16: the throwaway Gmail mailbox (2-step on, settings done, app passwords saved in files; the assistant asks you where the files are, so that the clean-up deletes them); the HubSpot test account (users created, secret key given); your own n8n account (it holds credentials for HubSpot, the model and Gmail in n8n's own credential store; the take uses a fresh n8n, so those are not the take's); a saved secret key for the model. Do not redo a step whose result already exists.
- NOT YET CONFIRMED: whether the secret key for the model was made for this take only, and what the saved HubSpot secret key is allowed to do. Your statement does not cover the two HubSpot private apps or the property `hadavin_label`. Before the take the assistant asks you two things. (1) The question of step 22 item 3 about the secret key for the model: "Is the secret key for the model that you saved one that you made only for this take, and does nothing else use it?" You then know your answer before the take day. (2) Whether the HubSpot secret key that the take uses (the one in your file in `~/take-secrets`, not the key for the model) is the read-only one of step 7, app 1, and whether app 2 exists. If either is not so, you do not say yes to a take until the assistant has told you what to change and you have changed it.
- Do NOT do step 8 until the assistant asks you in a message. Step 8 has two parts. The first part is the password file (sub-steps a to e of item 3): the assistant asks for it first, with a message that starts "Create the password file", before it starts the database server and n8n. The second part is typing the three credentials into n8n (the sender mailbox, HubSpot and the take's database): it comes only after the assistant tells you that n8n is running, and it tells you then where to type them. The secret key for the model is never typed into n8n.
- NOT SETTLED, BEFORE ANY TAKE: whether the take program deletes the take's contacts in HubSpot at its end. An earlier reading of the code found a step that does; a later independent review found none. Nobody has settled which is right, and steps 17 and 18 below still say "archived" (the earlier reading). If the program does delete contacts, a take with the read-only secret key (step 7, app 1) would fail after the enquiries were sent and money was spent. Before the take the assistant gives you a short written summary, with the names of its two saved files (a saved search of the final take program and a saved test output). The summary says one of two things: "the take program makes no delete call to HubSpot", or "a delete call existed and has been removed, shown by a test". Either summary is a good result and you may go on. If the summary says that a delete call still exists, or if no summary comes, you do not say yes to a take. The assistant's request for your yes (step 16) lists this as its fourth fact.
- The assistant tells you before the take which of steps 1 to 9 still need you.
- AT THE TAKE you type three things yourself: (1) `y` and Enter; (2) the 6-digit confirmation number that the program shows (it is new for every take), a space and the take id, on one line; (3) later, `end`, when the assistant tells you. The take id is a short name that you choose for each take, new every time (the rules for it are in the request for your yes, step 16). Take-day settings: mains power, sleep Never, lid Do nothing (rule 6 above).'''
set_new('E-37', E37)
why_add('E-37', 'Round 11 (naive M7, M8, minors; design M1): (a) "the secret key the take uses is the read-only one" is now "the HubSpot secret key that the take uses ... not the key for the model", and the model-key question is asked before the take day, not only at clean-up; (b) the owner is told what a good result of the code search looks like (two accepted summaries, one rejected) and no code-search output or internal word ("route 1 or 2") is shown to him; (c) the step 8 ban is split into its two parts (password file first, credentials after n8n runs), so he can tell when to start; (d) THREE credentials, without the model; (e) the heading no longer says "original deadline" or "if nothing were done yet" and the old deadline is named once with UTC and IST; (f) the take id points to the rules in the request for your yes (E-12). Q23 holds: the text never says as fact that the take program deletes or archives.')

# ============ E-48 ============
rsub('E-48', 'Take a screenshot. Before you save it, crop it', 'Make a screenshot (a picture of your screen). Before you save it, crop it')
rsub('E-48', 'Before the assistant starts item 1, it asks you this question and waits for your reply: "Is the secret key', 'Before the assistant starts item 1, it asks you this question and waits for your reply (it also asked you before the take; it asks again because your answer may have changed): "Is the secret key')
rsub('E-48', 'Do it right after the take, and in every case by 2026-11-23 18:19 UTC = 23:49 IST, the last time to revoke.',
     'Do it right after the last take that you accept, and in every case by 2026-11-23 18:19 UTC = 23:49 IST, the last time to revoke. Once the key is revoked no further take can run, so if a failed take (step 20) is still wanted, revoke only after it.')
rsub('E-48', 'Take a screenshot of the list of secret keys showing it gone, cropped in the same way.', 'Make a screenshot of the list of secret keys showing it gone, cropped in the same way.')
rsub('E-48', '- If a take is still running at 18:19 UTC = 23:49 IST: tell the assistant at once.',
     '- If a take is still running at 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 (a take runs that day only under the condition stated in the request for your yes, step 16): tell the assistant at once.')
rsub('E-48', '- Every OLDER secret key for the model, that is, every key except the one made for this take (the key the take runs on): revoke it too, unless you tell the assistant a reason and an end date.',
     '- Every OTHER secret key for the model, that is, every key except the key that the take runs on (the key you saved for the take): revoke it too, unless you tell the assistant a reason and an end date. If you replied `no, other things use it`, the key that the take runs on is shared and stays; then tell the assistant which keys exist and which of them other things use.')
rsub('E-48', '(the file with the app password of the receiver mailbox and the file with the HubSpot read secret key)',
     '(the file with the app password of the mailbox that receives the take\'s mails, called the receiver mailbox, and the file with the HubSpot read secret key)')
why_add('E-48', 'Round 11 (naive M5, M9, minors; design M3, minor 7): (a) "Take a screenshot" becomes "Make a screenshot" so that "take" keeps one meaning; (b) the key is revoked right after the LAST take that the owner accepts, and the text says that revoking ends all retakes (step 20), so a retake is done before the revoke; (c) the rule for a take still running at 18:19 UTC = 23:49 IST is tied to Mon 23 Nov (the take is planned for Wed 18 Nov); (d) the older-keys bullet names "the key that the take runs on" and says what happens when it is shared; (e) "receiver mailbox" is explained in the text and in E-52; (f) the model-key question is asked before the take (E-37) and again here. E-55, E-57 and E-58 align the heading of step 22, step 21 and the send table with this timing.')

# ============ E-49, E-53 ============
rsub('E-49', 'the assistant sends the enquiry straight to the address of the take\'s own n8n on this laptop.', 'the assistant sends the enquiry straight to the web address of the take\'s own n8n on this laptop.')
rsub('E-49', '(b) that no paid model call is possible, either because the model stage was started with the stand-in model and a secret key file that holds a made-up value, or because you gave a separate written yes with a number for one paid call;',
     '(b) that no paid model call is possible, because the model stage was started with the stand-in model and a secret key file that holds a made-up value (no row allows a paid call in the preparation);')
why_add('E-49', 'Round 11 (design M2): the alternative "or a separate written yes for one paid call" is removed, because E-53 is now a plain MUST NOT and E-11 says the assistant never starts the model stage with the real key file; a paid call in the preparation needs a new row first (NOT DECIDED 6, option B). "address" becomes "web address".')
rsub('E-53', 'post ONE made-up enquiry to the take\'s own n8n address on this laptop,', 'post ONE made-up enquiry to the web address of the take\'s own n8n on this laptop,')
rsub('E-53', 'hold or use a real secret key of its own; start the model stage with a real key file unless the owner\'s written yes with a number for one paid call is quoted in the lead\'s message; answer a prompt',
     'hold or use a real secret key of its own; start the model stage with a real key file or with the web address of the real AI model; answer a prompt')
why_add('E-53', 'Round 11 (design M2): the MUST NOT is plain. The earlier "unless the owner\'s written yes with a number for one paid call is quoted" read as a permission and contradicted E-11 (the assistant never starts the model stage with the real key file). If NOT DECIDED 6 is answered B, the studio lead first writes a new row that says who starts the stage and how, and reconciles E-11.')

# ============ E-51 ============
rsub('E-51', 'not a ceiling the program enforces against a second file; the decision of 16 Nov 2026 states that the take program does not print these two values (the spending cap and the end of the spending window), and that statement is not checked in the code. So the assistant shows you in the chat only the two lines of the model stage\'s settings file that hold the spending cap and the end of the spending window, and you compare them with the figures in its message. It shows nothing else from that file, no key file and never `n8n.env`)',
     'not a ceiling the program enforces against a second file. The decision of 16 Nov 2026 states that the take program does not print these two values (the spending cap and the end of the spending window); that statement is not checked in the code. So the assistant first tells you the path of the model stage\'s settings file. If that file sits inside `~/take-secrets` or any other folder that holds secrets, the assistant shows nothing and you open the file yourself. If it does not, the assistant shows you in the chat only the two lines that hold the spending cap and the end of the spending window, and you compare them with the figures in its message. It shows nothing else from that file, no key file and never `n8n.env`)')
why_add('E-51', 'Round 11 (naive minor, design m4): the long bracket sentence is split into short sentences, and the assistant first names the path and shows the two lines only if the file is not in a secret folder (nothing read says where the file sits).')

# ============ E-52 ============
rsub('E-52', '- **The post**: the public text you publish about the take (to send something to n8n is called "to send"). **A review round**',
     '- **The post**: the public text you publish about the take. In the edited texts "to send" always means that a program sends something (a mail or an enquiry); a person "publishes" the post. **A review round**')
rsub('E-52', '- **WSL**: the Linux part of your laptop. **A WSL terminal**: the program in which you type commands to that Linux part.',
     '- **WSL**: the Linux part of your laptop. **A WSL terminal**: the program in which you type commands to that Linux part. **Your Linux user**: your sign-in to that Linux part; the programs that the assistant starts there run under it.')
rsub('E-52', '- **App 1** and **app 2**: the two HubSpot private apps',
     '- **The receiver mailbox**: the throwaway mailbox that receives the take\'s mails (the older text says "RECEIVER"). **The sender mailbox**: the throwaway mailbox that sends them (the older text says "SENDER"). **An app password**: the 16-letter password that Google creates for one program to use a mailbox; it has nothing to do with a HubSpot private app.\n- **App 1** and **app 2**: the two HubSpot private apps')
why_add('E-52', 'Round 11 (naive M5, minors): "receiver mailbox", "sender mailbox" and "app password" are defined (the word "app" had three meanings: a HubSpot private app, an app password, a program); "Your Linux user" is defined; the circular sentence on "to send" is replaced.')

# ============ E-54, E-55 ============
rsub('E-54', 'The days are not fixed: the take is aimed at Wed 18 Nov 2026.', 'The days are not fixed: the take is aimed at Wed 18 Nov 2026, and the assistant gives you the start time in UTC and IST in the request for your yes (step 16).')
why_add('E-54', 'Round 11 (naive, times): "Wed 18 Nov 2026" had no time of day; the request for your yes states it.')
rsub('E-55', '### Step 22. Retirement. The secret key for the model is revoked by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke); the rest of the retirement is done by 18:29 UTC = 23:59 IST (the end of the spending window). The take is planned for Wed 18 Nov 2026, so retirement normally follows the take on the same day.',
     '### Step 22. Retirement. The secret key for the model is revoked right after the last take that you accept, and by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke); the rest of the retirement is done by 18:29 UTC = 23:59 IST (the end of the spending window). The take is planned for Wed 18 Nov 2026, so the key is normally revoked on that day, and the revoke does not wait for the cut (step 21).')
why_add('E-55', 'Round 11 (design M3, naive M9): the heading now says that the key is revoked right after the last accepted take (as E-48 says), not after the cut; E-57 and E-58 change step 21 and the send table to the same timing.')

# ============ E-57, E-58 (new rows) ============
NEWROWS = '''### E-57: OWNER-STEPS-realrun-v3.md, line 116 (and 117), status Apply now, type CONTRADICTION
OLD (exact):
~~~~
### Step 21. Mon 23 Nov before 18:29 UTC: you watch the cut
NEEDS-OWNER (owner decision 3 in plan-4 sense: watch on Mon 23, before the window ends; Claude default). Watch from the first second to the last; reply "accepted" or list the bad seconds. Retirement follows; after it there is no third take.
~~~~
NEW (exact):
~~~~
### Step 21. Mon 23 Nov 2026, before 18:29 UTC = 23:59 IST: you watch the cut
NEEDS-OWNER (watching on Mon 23 Nov, before the spending window ends, is the assistant's default). Watch the cut from the first second to the last; reply "accepted" or list the bad seconds. This watch does not delay the revoke of the secret key for the model: step 22 item 3 says when you revoke it (right after the last take that you accept, and by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest). Revoking that key ends every further take, so revoke it only when no retake (step 20) is wanted. The rest of the retirement (step 22) follows the cut; after it there is no further take.
~~~~
Why: Design M3 of round 10: step 21 said "Retirement follows" the cut on Mon 23 Nov, while E-48 and E-55 revoke the secret key for the model right after the take (the take is planned for Wed 18 Nov) and by 18:19 UTC = 23:49 IST at the latest (Q25), and step 20 allows a retake while the key still works. The new text separates the two: the revoke does not wait for the cut and is done only when no retake is wanted; the other retirement items follow the cut. The heading carries UTC and IST (18:29 + 5:30 = 23:59; Mon 23 Nov 2026 is a Monday). "plan-4 sense", "Claude default" and "third take" (no input says how many takes there are) are removed from the owner text. The old text is the two lines 116 and 117 and occurs once; E-55 changes line 119 and does not overlap.

### E-58: OWNER-STEPS-realrun-v3.md, line 147, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
| Mon 23 | retirement screenshots, retire-check output (counts and words only) |
~~~~
NEW (exact):
~~~~
| Right after the last take that you accept (by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest) | the screenshot of the list of secret keys for the model showing the key gone (step 22 item 3) |
| Mon 23 Nov 2026, by 18:29 UTC = 23:59 IST | the other retirement screenshots and the retire-check output (counts and words only) |
~~~~
Why: Design M3 of round 10 (v3 line 147): the send table put all retirement on Mon 23; the key revoke is now earlier (E-48, E-55, E-57). The old row is the last row of the table "What to send the lead" and occurs once. The two new rows keep the table form of the file (the bars are part of the text).

'''
m = re.search(r'\n## Lines checked and found consistent', T)
if not m: errs.append('lines-checked heading not found')
else:
    T = T[:m.start() + 1] + NEWROWS + T[m.start() + 1:]

# ============ what I did not check ============
T = T.rstrip('\n') + '''

- Round 11 added: nothing was run except text and count checks by script (`resolve-r11-check-output.txt`; `verify11.py` has negative controls). I did not read the code, the smoke evidence, any click path (the Start menu path to a WSL terminal in E-09 and the HubSpot and model-provider pages are unchecked), `review-codebase-1.md` or `WP6-RUNBOOK.md`. The take id rule of E-12 (lowercase letters, digits, hyphens, at most 20 characters) is the builder's safe choice and is not read from the take program. Whether a Docker volume is used for the database (E-16), whether the stage settings file sits in a secret folder (E-51), whether `n8n.env` can be created by the assistant and read by the start script as E-09 step g describes (NOT DECIDED 1), and whether a take stops safely when its key is revoked (E-48) are UNVERIFIED. The new owner texts of round 11 (E-09, E-12, E-16, E-37, E-48, E-57, E-58) are not yet read by a stranger. The egm:egm-resolve skill was not used (see `resolve-r11.md`).
'''
open(D + 'EDITS.md', 'w', encoding='utf-8').write(T)
print('errors', len(errs))
for e in errs: print('ERR', e)
sys.exit(1 if errs else 0)
