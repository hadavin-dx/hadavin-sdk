import re
P = 'EDITS.md'
t = open(P, encoding='utf-8').read()

def sub(old, new, n=1):
    global t
    c = t.count(old)
    assert c == n, (c, n, old[:90])
    t = t.replace(old, new)

def block(rid):
    lines = t.split('\n'); infence = False; start = None; end = len(lines)
    for i, l in enumerate(lines):
        if l.strip() == '~~~~': infence = not infence; continue
        if infence: continue
        if start is None and l.startswith('### %s:' % rid): start = i; continue
        if start is not None and (l.startswith('### E-') or l.startswith('## ')): end = i; break
    assert start is not None, rid
    return lines, start, end

def rsub(rid, old, new, n=1):
    global t
    lines, s, e = block(rid)
    seg = '\n'.join(lines[s:e]); c = seg.count(old)
    assert c == n, (rid, c, n, old[:90])
    seg = seg.replace(old, new)
    t = '\n'.join(lines[:s] + seg.split('\n') + lines[e:])

def why_add(rid, text):
    global t
    lines, s, e = block(rid)
    idx = [i for i in range(s, e) if lines[i].startswith('Why:')]
    assert len(idx) == 1, (rid, idx)
    lines[idx[0]] = lines[idx[0]].rstrip() + ' ' + text
    t = '\n'.join(lines)

# ---------- header ----------
sub('(round 10; draft by a builder', '(round 10, second pass r10b; draft by a builder')
sub('The result of round 10 is NOT reviewed yet. Earlier files are kept as `EDITS.round5.md` to `EDITS.round9.md`.',
    'Round 10b (second pass of round 10; `resolve-r10.md`, section r10b) finishes the findings that the first pass did not fix. The result of round 10b is NOT reviewed yet. Earlier files are kept as `EDITS.round5.md` to `EDITS.round9.md` and `EDITS.round10a.md` (the first pass of round 10).')
sub('## Counts (computed by script, `resolve-r10.md` and `resolve-r10-check-output.txt`)', '## Counts (computed by script, `resolve-r10.md` and `resolve-r10b-check-output.txt`)')
sub('role = one named set of permissions.',
    'role = one named set of permissions; first smoke = the earlier trial on this laptop (plan v5 calls it smoke-1; it ran real n8n with a simpler one-file database); stage settings file = the settings file of the model stage that holds the spending cap and the end of the spending window (it is not the key file); search path = the list of schemas (named sections of a database) in which a database user looks for a table whose name has no schema name.')
sub('The word "rehearsal" alone is not used in new texts.', 'The word "flow" is never dropped from "flow rehearsal" in new texts.')
sub("A Hold row is never applied until its gate is open, whatever the row's text says.",
    "A Hold row is never applied until its gate is open, whatever the row's text says. The one other held text is text N of E-36 (a second text inside an Apply now row): its label is `NEW [HOLD Cb: DO NOT APPLY]`, where Cb means confirmation b below. A script that applies the NEW blocks must skip every block whose label contains `[HOLD`.")
sub('(numbered 1 to 13 in the list below the gates)', '(numbered 1 to 14 in the list below the gates)')
sub('(items 1 to 13). Each item says', '(items 1 to 14). Each item says')
sub("and writes one line per answer: `ND<number>: <answer>, <who>, <date and time in UTC and IST>` (for the owner's answers the line quotes his message)",
    "and writes one line per answer. The line has the form shown after \"Record:\" in the item, with the choices filled in, then `; <who>; <date and time in UTC and IST>` (for the owner's answers the line also quotes his message)")
sub('Record: `ND8: A|B <date and time in UTC and IST>`.', 'Record: `ND8: A|B`.')
sub('Record: `ND12: a|b <date and time in UTC and IST>`.', 'Record: `ND12: a|b`.')
sub('`ND7a-late: <answer>, <date and time in UTC and IST>`', '`ND7a-late: <answer>; <who>; <date and time in UTC and IST>`')
sub('under the same US$ cap and window end.', 'under the same US$ cap and the same spending window.')

# ND14 and confirmation i
sub('Record: `ND13: a|b`.',
    'Record: `ND13: a|b`.\n14. **Does the lease sentence of Q22(c) belong in the public post of E-17?** Who answers: the studio lead. Q22(c) in ORDERS ("item 1 wording plus one honest sentence that a gap longer than the lease is not claimed") is an answer about the v19 hand-off item 8 and does not mention the post. The word "lease" is explained in no input of this folder, and no input says that the post concerns one. Options: (a) the post gets no lease sentence (the post keeps only the crash clause of E-17); (b) the post gets one more sentence; the studio lead then gives its exact words and one more row is written. Cost: studio lead time only. Default: (a). Record: `ND14: a|b <the exact sentence for b>`.')
sub('i. Q22(c) ("item 1 wording plus one honest sentence that a gap longer than the lease is not claimed") is in ORDERS as an answer about the v19 hand-off item 8. Round 10 did NOT add a lease sentence to the public post of E-17: no input says the post concerns a lease. If the studio lead means the post, the exact sentence is needed.',
    'i. The question whether the lease sentence of Q22(c) belongs in the public post of E-17 is not a reading but a decision, so it is now NOT DECIDED 14. Rounds 10 and 10b added no lease sentence to the post.')

# ---------- rows ----------
# E-04: full stop
rsub('E-04', 'otherwise the made-up names to look for\n~~~~', 'otherwise the made-up names to look for.\n~~~~')
why_add('E-04', 'Round 10b (design m7): the new text now ends with a full stop. The old text is the end of line 69 (nothing follows it in the file), so the sentence is complete and the closing bracket of the old text stays at its start.')
# E-07, E-08
rsub('E-07', 'n8n runs inside WSL, the Linux part of your laptop (WSL). The assistant checks this with you',
     'n8n runs inside WSL, the Linux part of your laptop (WSL). The plan says an earlier trial (the first smoke) showed it, but nobody on this branch has read that evidence. The assistant checks this with you')
rsub('E-08', 'The plan says the first smoke showed it, and nobody has read that evidence yet.',
     'The plan says an earlier trial (the first smoke) showed it, and nobody on this branch has read that evidence yet.')
why_add('E-07', 'Round 10b (naive minor): the owner text now says "nobody on this branch has read that evidence", the same as NOT DECIDED 5 ("branch" is explained in E-02).')
why_add('E-08', 'Round 10b (naive minor): the owner text now says "nobody on this branch has read that evidence yet", the same as E-07 and NOT DECIDED 5.')
# E-12: what happens at 18:19
rsub('E-12', 'that figure is a reading of step 17 and is not checked in the code.',
     'that figure is a reading of step 17 and is not checked in the code. If a take is still running at 18:19 UTC = 23:49 IST, the assistant tells you in writing what happens next (step 22 says what you do with the key).')
why_add('E-12', 'Round 10b (design m4): the request now says that the assistant tells the owner in writing what happens next if a take is still running at the last time to revoke; the earlier latest start (18:04 UTC = 23:34 IST) stays the builder choice of confirmation h.')
# E-14
rsub('E-14', '(rule 5: you post)', '(rule 5 of this sheet: you are the one who publishes)')
why_add('E-14', 'Round 10b (naive minor, who decides the footage): the owner decides, and "post" (which also means sending to n8n) is replaced by "publishes".')
# E-17
rsub('E-17', 'Round 9 (naive B9): "recording in the take\'s database that it was sent" (which table?) becomes "recording in the take\'s database that it was sent", in every text of this file.',
     'Round 9 (naive B9): the clause says "the take\'s database" (the database that holds the table of enquiries) in every text of this file, so the reader is not left to ask which database.')
why_add('E-17', 'Round 10b (design m7, naive minor): (a) the circular sentence of round 9 is replaced; (b) no lease sentence is added: Q22(c) is about the v19 hand-off item 8, so the question is NOT DECIDED 14; (c) when the crash check ends as "crash check untested" (both tries "missed": E-12 and E-22 use these same words), the clause stays in the post (rule R1).')
# E-19 Why quote
rsub('E-19', 'the plan itself never says "rehearsal"', 'the plan itself never says "flow rehearsal"')
# E-22
rsub('E-22', 'Until the test has run and passed, this case is untested.',
     'If both tries "missed", the case counts as "crash check untested", the same words as in the request for your yes (step 16). Until the test has run, the case is untested.')
why_add('E-22', 'Round 10b (design m7): the sentence now links to the phrase "crash check untested", worded the same way in E-12, E-17 and here.')
# E-31
rsub('E-31', 'whose search path may not include `app`, and then the read fails. A failed read stops the take safely (UNVERIFIED).',
     'whose search path (the list of schemas, the named sections of a database, in which that user looks for a table whose name has no schema name) may not include `app`, and then the read fails. What the take does when this read fails is not checked, and nothing here says that it stops safely (UNVERIFIED).')
why_add('E-31', 'Round 10b (naive minor): "a failed read stops the take safely" was a safety claim that nothing proves, and "search path" was undefined; both are fixed in the text.')
# E-36
sub('NEW, TEXT W (default; this is the only live text until confirmation b is answered yes in writing):',
    'NEW (exact; TEXT W, the default and the only live text until confirmation b is answered yes in writing):')
sub('NEW, TEXT N [HOLD: DO NOT APPLY unless confirmation b is answered yes in writing] (replaces text W only if confirmation b says the mail count and the contact count run on credentials of their own):',
    'NEW [HOLD Cb: DO NOT APPLY] (exact; TEXT N; apply only if confirmation b is answered yes in writing, because then the mail count and the contact count do run on credentials of their own; it replaces text W):')
rsub('E-36', ' The post sentence reads with text W as before; the old words "table of enquiries" in text N are "table of enquiries" (the post itself says "lead" for an enquiry, so text N says "table of enquiries" only because the public post must not use the older internal name).',
     ' Round 10b (design m7, naive minor): (a) the labels follow the convention: text W is `NEW (exact; TEXT W ...)` and text N is `NEW [HOLD Cb: DO NOT APPLY]`, so a script that applies every NEW block without a `[HOLD` label can apply text W only; (b) the clause of E-17 follows in the same line and reads exactly: "a crash at exactly the moment between sending the mail and recording in the take\'s database that it was sent may send the mail twice"; the old text of E-36 lies before the old text of E-17 and the two do not overlap; (c) the circular last sentence of round 9 is removed.')
# E-43
sub('**ONE Postgres server for everything we own: the single Postgres instance of the take**',
    "**ONE Postgres server for everything we own except the model stage's journal file `stage.journal`: the single Postgres instance of the take**", 2)
why_add('E-43', 'Round 10b (design m7, Q21.3): the words "ONE Postgres server for everything we own" stay; the text says "two databases" and never "Postgres is the one store"; the model stage\'s journal `stage.journal` stays a file (EL-1), so it is named as the one exception.')
# E-48
rsub('E-48', 'unless the assistant tells you otherwise before that time.',
     'unless the assistant tells you otherwise before that time. The assistant then tells you in writing what happens next: which part of the take is finished, which part is not, and what you have to clean up by hand. That the take stops safely when its key is revoked is not proven (UNVERIFIED).')
rsub('E-48', 'Every OLDER secret key for the model, one that was not made for this take: revoke it too',
     'Every OLDER secret key for the model, that is, every key except the one made for this take (the key the take runs on): revoke it too')
why_add('E-48', 'Round 10b: (a) Q19.5 (cancel all older model keys except the run key unless the owner writes a reason and an end date) is covered by the bullet on older keys, which now says "except the one made for this take (the key the take runs on)"; (b) design m4: if a take is still running at the last time to revoke, the assistant tells the owner in writing what happens next.')
# E-49
rsub('E-49', '(<day> is the weekday and the date)', '(<day> is the weekday and the date, written like this: `Wed 18 Nov 2026`)')
rsub('E-49', '- Your consent: the assistant sends the enquiry only after you answer in writing: `Yes, send the one enquiry on <day>`',
     "- Your consent: the assistant sends the enquiry only after you answer in writing, and only with an answer that you wrote AFTER the assistant's message that states (a) to (d); an answer written earlier does not count: `Yes, send the one enquiry on <day>`")
why_add('E-49', 'Round 10b (design m6, naive minor): the consent is tied to the assistant\'s message that states (a) to (d), and `<day>` has a written example.')
# E-50
rsub('E-50', 'the enquiry was sent after your written "Yes, send the one enquiry on <day>", which traces',
     'the enquiry was sent after your written "Yes, send the one enquiry on <day>" (written after the assistant\'s message that stated (a) to (d)), which traces')
why_add('E-50', 'Round 10b (design m6): fact 5 names the same order as E-49: the yes counts only after the message that states (a) to (d).')
# E-51
rsub('E-51', "the take program does not print these two values (the spending cap and the window end), so you read them in the stage settings file that the assistant shows you in the chat and compare them with the figures in its message. The assistant shows only that settings file, never `n8n.env`)",
     "the decision of 16 Nov 2026 states that the take program does not print these two values (the spending cap and the end of the spending window), and that statement is not checked in the code. So the assistant shows you in the chat only the two lines of the model stage's settings file that hold the spending cap and the end of the spending window, and you compare them with the figures in its message. It shows nothing else from that file, no key file and never `n8n.env`)")
why_add('E-51', 'Round 10b (design m3, naive M9): "window end" becomes "the end of the spending window" (E-52); only the two lines are shown, not the whole file, because nothing proves that the file holds no secret; "does not print" is stated as the decision\'s statement, not as a fact.')
# E-52
rsub('E-52', "- **The spending window**: the last day and time the model stage may spend money: 2026-11-23 18:29 UTC = 23:59 IST (the older text calls it \"the window end\"). It has nothing to do with a screen window.",
     "- **The spending window**: the last day and time the model stage may spend money: 2026-11-23 18:29 UTC = 23:59 IST (the older text calls it \"the window end\"). It has nothing to do with a screen window.\n"
     "- **The request for your yes**: the one message the assistant sends you before the take (step 16). **Your reply**: the one line you type back. The older text uses \"yes message\" for both; the edited texts never do.\n"
     "- **To revoke** a secret key: to delete it at the company that issued it, so that it stops working (the older text may say \"cancel\"). **The last time to revoke** the secret key for the model: 2026-11-23 18:19 UTC = 23:49 IST, ten minutes before the spending window ends.\n"
     "- **WSL**: the Linux part of your laptop. **A WSL terminal**: the program in which you type commands to that Linux part.\n"
     "- **A web address**: what you type into a browser, for example `http://localhost:5678`. **A mail address**: what a mailbox has, for example `name@example.com`. The edited texts never say \"address\" alone.\n"
     "- **App 1** and **app 2**: the two HubSpot private apps that the older text numbers 1 and 2. App 1 is meant to be the read-only app (it may only read contacts); app 2 is the second app.\n"
     "- **The post**: the public text you publish about the take (to send something to n8n is called \"to send\"). **A review round**: one pass of independent review of the code. **A fix round**: a batch of code changes made after reviews. **Screen**: only what the laptop display shows (as in \"the count screen\"); what a program prints is called \"output\".")
why_add('E-52', 'Round 10b (naive M9, minors): new bullets for the request for your yes and your reply, to revoke and the last time to revoke, WSL and a WSL terminal, a web address and a mail address, app 1 and app 2 (the read-only app and the second app), the post, review round and fix round, and screen.')
# E-53
rsub('E-53', 'only after the owner\'s written `Yes, send the one enquiry on <day>`; read the counts',
     'only after the owner\'s written `Yes, send the one enquiry on <day>` (<day> written like `Wed 18 Nov 2026`) that the owner wrote after the assistant\'s message stating the points (a) to (d) of the Phase 1 text of the sheet; read the counts')
rsub('E-53', '\n- Enforced by: nothing in code is known for the posting itself',
     '\n- Section 4b overrides line 27 (no real key, no answer to a prompt of the take program) only for this one enquiry and only for what the MAY line allows. Line 27 stays in force for everything else.\n- Enforced by: nothing in code is known for the posting itself')
why_add('E-53', 'Round 10b (design m5, m6): the MAY line ties the yes to the assistant\'s message and says that section 4b overrides line 27 only for this one enquiry.')
# line 860 rehearsal
sub('the rehearsal costs US$0 (EL-5)', 'the flow rehearsal costs US$0 (EL-5)')
open(P, 'w', encoding='utf-8').write(t)
print('ok')
