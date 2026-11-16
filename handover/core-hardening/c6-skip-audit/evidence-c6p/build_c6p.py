"""Builds REPORT-c6p.md from REPORT-c6o.md (read only) with the rows of build_c6p_rows.py. Every patch asserts one match.
Usage: python3 build_c6p.py   Output: REPORT-c6p.md in the folder above."""
import re, sys
sys.path.insert(0, "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/evidence-c6p")
import build_c6p_rows as B
from build_c6p_rows import rows, LINES, FIRST, LAST, set_dep, sub, CARD as C, A1, A2, A3, A4, B1, B2, B3, B4, R2, R1S, TOK
D = B.D
L = list(LINES)


def find(prefix):
    idx = [i for i, l in enumerate(L) if l.startswith(prefix)]
    assert len(idx) == 1, "prefix matched %d lines: %r" % (len(idx), prefix[:70])
    return idx[0]


def setline(prefix, new): L[find(prefix)] = new
def patch(prefix, old, new, c=1): i = find(prefix); L[i] = sub(L[i], old, new, c)


# ------------------------------------------------------------ counts from the rows
N = len(rows)
ready = [k for k in sorted(rows) if rows[k]["st"].endswith("ready")]
withc = [k for k in sorted(rows) if any(t.startswith("C-") for t in TOK.findall(rows[k]["st"]))]
onlyq = [k for k in sorted(rows) if k not in ready and k not in withc]
assert N == 94 and not any("NOT FILMABLE" in rows[k]["st"] for k in rows)
W1 = len(ready) + len(onlyq)
cnt = {}
for k in sorted(rows):
    for t in set(TOK.findall(rows[k]["st"])):
        cnt.setdefault(t, []).append(k)
lst = lambda a: ", ".join(map(str, a))

# ------------------------------------------------------------ the new box (lines 3 to 48 of c6o)
b = find("## Start here"); e = find("## 0. Failures")
BOX = """## Start here: what I need from you (read this box first; everything after it is detail)
NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE. The edit table (section 5) holds %(N)d proposed text changes, called rows. Each row has its old text, its new text and what a person watching the video sees. %(r)d rows are 'ready' (the text can be applied now), %(o)d apply on the default of a question you have not answered, and %(c)d wait for a check that needs n8n running (rows %(cl)s). You answer with ONE line in ORDERS.md (below the questions). There is no question without a default any more.

WORDS YOU NEED FIRST (each label below is used only after this list):
- CONTACT = one made-up sales contact. The files and the spoken video call it a 'lead'; this report says 'contact' except inside quoted video words.
- N8N = the tool that runs our automatic flows. A flow receives a contact, writes it into a customer list (the CRM) and sends a mail.
- TAKE = the one filmed run of the video. REHEARSAL = a practice run before it. RUN SHEET = the file VIDEO-RUNSHEET.md, the scene-by-scene script: scenes 1 to 4 and a closing card (the last card, spoken by voice, which the files call scene 12).
- STUDIO LEAD = the person who decides for the studio and answers this report (the files call him 'the lead'). OWNER = the person who types in the take. Two roles; no file says whether one human fills both.
- LEASE = a setting of 45 seconds kept with every contact: when it has run out and the contact is not finished, the recovery flow (a flow that wakes every 30 seconds) may take the contact over. ALERT = the one warning mail the system sends to a person when it cannot tell what happened to a contact.
- GATE = a step on the run sheet that blocks the take until a named person has written a result on it: a stop sign, not a program. RE-PIN = the moment when the studio lead puts together the final version of the take files and reads them again. READY = the text can be applied now; it does not mean the gate it adds has passed.
- K3B and K3 = two of four crash tests in which n8n is switched off at a chosen moment to see whether the system recovers; scene 4 shows such a crash. TIMES are UTC with IST (UTC + 5:30) next to them.

QUESTIONS (label, plain question, the default that 'apply all defaults' uses, who answers). All are answered by the studio lead except L-SHEET (the owner knows the fact).

| Label | Plain question | Default |
|---|---|---|
| L-CARD | Does the closing card stay as the last card of the video? | Yes. |
| L-CARDCUT | Cut the old card lines about '80 kills' and the recovery time? (They count runs of older flows and an estimate that no data of this take backs.) | Yes, cut. |
| L-CARDTEXT | Use the new spoken card lines 2 to 4 (what an alert is and that we make no statement about how fast it arrives; what n8n may keep; what was not tested)? | Yes. |
| L-CARDLEN | Length of the closing card. (a) the four spoken lines of rows 13 and 14: exactly %(NA)d words, about %(SA)d s at 150 words a minute, so the card budget on the run sheet becomes %(BA)d s and the video about %(TOTA)d s; or (b) a shorter text of %(NB)d words, about %(SB)d s, card budget %(BB)d s, video about %(TOTB)d s (text in section 3). All numbers are estimates until the stopwatch run. | (a). |
| L-LEASE | Which honest sentence about the 45-second setting goes on the card (line 1) and in the scene 3 caption? 1 = 'We make this claim only when the second send comes within 45 seconds of the first send; for a longer gap we make no claim.' (your own answer Q22 (c) of ORDERS.md; true, but weaker than what the flows do). 2 = '%(R2)s' (what the flow files show; %(NR2)d words; needs one more check). none = no lease sentence anywhere, the plain statement only (this REVERSES your answer Q22 (c): write it only if you mean to). My recommendation: 2, once the table rule on the contact id has been seen in the take's database (check C-9 part 2), because reading 1 asks for the repeat send within 30 seconds of the first and scene 2 is planned at 40 seconds. Section 3 gives what each costs a viewer. | 1 (your answer Q22 (c) is in force). |
| L-KILL | Say anything in scene 4 about the crash tests K3B and K3? (a) no, (b) yes, labelled as a stand-in test. | (a). |
| L-APPROX | May scene 4 and the web page say 'about a minute' instead of the cut number? | No. |
| L-SAVE | Does the take make n8n save every run, so that the list of past runs filmed in scenes 1 and 2 shows runs? (The test plan records this as the owner's choice of 2026-11-16; you confirm it is still current. The two n8n settings are named in section 3.) | Yes. |
| L-PAGE | May the web page carry the 60.1 to 61.9 s range of the stand-in crash runs and the 13-minute alert delay? | No; both stay in the file, marked not for the page. |
| L-ONEDB | May any text a viewer sees say how many databases n8n and the take use, before the short test of the whole setup (the loopback re-smoke) has shown which database n8n uses? | No. The two rows tied to it (90, 91) edit only the decision file, not viewer text, and apply by default; 'yes' only lets you give a sentence. |
| L-SHEET | Which owner sheet (the checklist the owner reads) does the owner read? OWNER ONLY (the studio lead asks him). | v28 variant A, the newest pair on disk (still being written at 16:01 UTC = 21:31 IST, section 7 C-10c). |
| L-DEL | Does the take delete contacts? ANSWERED by you (Q23, Q19 item 1, Q27): no, never. The open part: at the re-pin you read the take program and write the five entries of risks list item 11. | As answered. |
| L-CUT | Mark the run sheet rows of scenes 5 to 11 (not filmed) as 'not in the one video'? | No edit. |

HOW TO ANSWER. Append this ONE line to handover/core-hardening/ORDERS.md. Replace the time with the real time: type date -u +%%FT%%TZ, which prints UTC with seconds (for example 2026-11-16T16:40:00Z), and add 5 hours 30 minutes by hand for IST (22:10:00); the three names are free labels you choose:

`## ANSWER (studio lead, 2026-11-16T16:40:00Z = 22:10:00 IST): c6p apply all defaults to REPORT-c6p.md; builder: builder-1; reviewers: egm-design, egm-comprehension`

The builder is the agent that applies the %(W1)d wave 1 rows. The reviewers are one who checks facts and risk (egm-design) and one who reads as a person who has never seen the project (egm-comprehension). To change a default add after the names `; except L-KILL: b` (one 'except' per label that differs). REPLY FORM FOR EVERY QUESTION: L-CARD yes or no; L-CARDCUT yes or no; L-CARDTEXT yes or no; L-CARDLEN a or b; L-LEASE 1, 2 or none; L-KILL a or b; L-APPROX yes or no; L-SAVE yes or no; L-PAGE yes or no; L-ONEDB yes or no; L-DEL no reply needed; L-CUT yes or no; L-SHEET cannot be put on this line (write it as a separate line: `## ANSWER (owner via studio lead, time): L-SHEET v28A`).

APPLY ALL DEFAULTS, in three lists.
- IT DOES: (1) the named builder applies wave 1, %(W1)d rows (section 3c lists them), to 10 files (the 9 files of c6n and the flow generator build_mainframe.py), by text, in table order, and writes the applied row numbers to c6p-APPLIED-ROWS.md next to this report. (2) THE CLOSING CARD is exactly: line 1 (%(w1)d words) 'A lead sent twice with the same id is processed once. We make this claim only when the second send comes within 45 seconds of the first send; for a longer gap we make no claim.' line 2 (%(w2)d words) the alert sentences, line 3 (%(w3)d words) the retention sentence, line 4 (%(w4)d words) the not-tested sentence: %(NA)d words, about %(SA)d s, budget %(BA)d s (rows 11, 12, 13, 14; the full lines are in rows 13 and 14). The scene 3 caption carries the same limit (row 21). (3) It edits the four flow files and their generator so that n8n would save every run once they are imported; it changes no running n8n; the studio lead sets the two n8n saving values in the environment that starts n8n (section 3, L-SAVE). (4) It adds seven steps that can stop the take or a rehearsal with real accounts to the run sheet (rehearsal list items 11 to 15, risks list items 11 and 12; item 16 after the take does not stop anything). No reviewer has read these new texts yet.
- IT DOES NOT: apply the %(c)d rows that wait for a check (rows %(cl)s); run any check; import anything into n8n; spend anything; confirm any answer (the column 'Confirmed?' in section 3 stays 'No'); answer L-SHEET; start the take.
- YOU STILL HAVE TO, in this order (no file gives a duration for any step; the studio lead's own target for step 5 is tonight or tomorrow morning IST, DEC:13): (1) write the answer line; (2) the builder applies the rows; (3) two reviewers read the CHANGED FILES (not this report); (4) import the edited flow files into n8n and run the import check C-4 (load the files, send one made-up contact and see runs appear in the list of runs); (5) run the loopback re-smoke on the edited flows (C-3, C-5, C-8 and the table part of C-9 are read during it); (6) have a builder you name write the leak scan C-6 (a test that plants fake secrets and made-up names and searches every place n8n stores data for them; it does not exist yet, the audit writes no code), then run it; rehearsal list item 14 needs the import check line and the leak scan line; (7) at the re-pin read the take script and write the five entries of risks list item 11; (8) ask the owner which sheet he reads (L-SHEET) and what his HubSpot key may do (HubSpot is the CRM of the take; ORDERS.md Q20 item 3); (9) hold the first rehearsal (after steps 5 to 8 are written); (10) film the take. If steps 4 to 6 are done by the evening of Tue 17 Nov 2026 (UTC), Wed 18 Nov is possible (target, not fixed; ORD:150); if one slips, the take slips. The money stop is Mon 23 Nov 2026 18:29 UTC = 23:59 IST; the latest start that day is 18:04 UTC = 23:34 IST; the owner cancels the paid key by 18:19 UTC = 23:49 IST; the post about the video is due Wed 25 Nov 2026 15:00 UTC = 20:30 IST (ORD:150).

TO REVERSE A DEFAULT, the studio lead names a builder who puts back the old text of the affected rows (every old text is in the table).

WORDS (more; one meaning each; used the same way in the whole report):
""" % dict(N=N, r=len(ready), o=len(onlyq), c=len(withc), cl=lst(withc), NA=C["NA"], SA=C["SA"], BA=C["BA"], TOTA=C["TOTA"], NB=C["NB"], SB=C["SB"], BB=C["BB"], TOTB=C["TOTB"], R2=R2, NR2=C["NR2"], W1=W1, w1=C["WA"][0], w2=C["WA"][1], w3=C["WA"][2], w4=C["WA"][3])
# keep the old WORDS block (lines after '- TWO ROLES') verbatim, patched below
wi = find("- TWO ROLES.")
old_words = L[wi:e]
L = L[:b] + BOX.split("\n") + old_words + L[e:]

# ------------------------------------------------------------ title and the Words patches
L[0] = "# REPORT-c6p: video audit fix pass, supersedes REPORT-c6o.md (2026-11-16, UTC; IST = UTC + 5:30)"
patch("- TWO ROLES.", "this report never does. In quoted video words", "this report uses it only in the sentence that tells you how to answer. In quoted video words")
patch("- TAKE = the one filmed run of the video (never", "RE-PIN = the moment when the studio lead puts together the final version of the take files and reads them again (the developer rule 'core modules: one source of truth' uses 're-pin' for moving every demo to the newest shared code; the orders use 'at re-pin' and 'at the final head' for this moment).", "RE-PIN: see the first list of the box.")
patch("- RUN SHEET = VIDEO-RUNSHEET.md", "The report never writes 'the sheet' alone.", "The report never writes 'the sheet' alone. ROW = a row of the edit table (section 5); the other rows are named by what they are: the run-sheet row of a scene, a row of the execution list, a claim row.")
patch("- CONTACT RECORD (or CONTACT)", "LEASE = the 45-second setting: how long a contact stays reserved for the run that took it first, before the recovery flow may take it again.",
      "LEASE = the 45-second setting: the time after which the recovery flow may take over a contact that is not finished. It is NOT the time during which a repeat send is recognised: the flows recognise a repeat as long as the contact's row exists (section 3, L-LEASE).")
patch("- TIMING NUMBER = a figure given as a RESULT", "It does say the 45-second setting (the lease) on the closing card and in the scene 3 caption, and it shows",
      "It may say the 45-second setting (the lease; where, depends on the answer to L-LEASE) and it shows")
patch("- READY = the row's new text", "rows 6 and 8 are ready, but the gates they add block the take until the studio lead writes the lines they ask for.", "rows 6 and 8 are ready, but the gates they add block the take until the studio lead writes the entries they ask for.")
patch("- TIMES AND DATES:", "First rehearsal: the studio lead, right after the loopback re-smoke passes (target tonight or tomorrow morning IST; decision 12, DEC:13).",
      "First rehearsal: the studio lead, after the loopback re-smoke has passed and the two lines of rehearsal list item 14 are written (DEC:13 gives only the re-smoke target: tonight or tomorrow morning IST).")

# ------------------------------------------------------------ section 0
s0 = find("- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED.")
L[s0] = ("- NOTHING IN THE EDIT TABLE HAS BEEN APPLIED. Every row says NOT APPLIED. Of the %d rows (rows 1 to 72 keep the numbers of REPORT-c6n.md; rows 73 and up are new in c6o, and rows 1, 33 and 39 were split): %d are 'ready' (no open question and no open check; rows %s); %d apply on the default of a question you have not answered (section 3); %d wait for a check that needs n8n (rows %s); none is NOT FILMABLE any more (c6o had two). The counts per question are made by a script and checked by a second script that fails on any difference (section 3, table 3b; section 7)."
         % (N, len(ready), lst(ready), len(onlyq), len(withc), lst(withc)))
L.insert(s0 + 1, "- THE LAST REPORT (REPORT-c6o.md) FAILED INDEPENDENT REVIEW: review-c6o-design.md (0 blockers, 8 majors, 8 minors), review-c6o-naive.md (2 blockers, 11 majors, minors) and review-c6o-evidence.md (caveats). This report (c6p) fixes every item or labels it in section 9; section 8 lists each item with its fix. THIS REPORT HAS NOT BEEN REVIEWED YET by independent reviewers; I did not run the EGM steps (the studio lead runs them). The main faults of c6o that c6p corrects: (1) 'apply all defaults' left the closing card half-changed and contradicted itself (now one card, with its exact word count); (2) L-LEASE was written against a misreading of your answer Q22 (c) and had no default (now reading 1 is the default because it is your own answer, with a recommendation for reading 2); (3) row 11 wrote a card length from the old six-line card (now %d words, about %d s); (4) section 5a was stale and left out the page rows (now made from the table); (5) 'the newest owner sheet' was wrong (the check is rerun over v19 to v28 at %s); (6) row 90 broke a sentence of the decision file; (7) the box was too long and used labels before defining them (now rewritten)." % (C["NA"], C["SA"], "16:01 UTC = 21:31 IST"))
patch("- THE LAST REPORT (REPORT-c6n.md) FAILED", "- THE LAST REPORT (REPORT-c6n.md) FAILED", "- HISTORY, THE REPORT BEFORE THAT (REPORT-c6n.md) FAILED")
patch("- SLIPS OF REPORT-c6n.md THAT I CORRECT HERE", "(1) THE REPEAT-SEND SENTENCE WAS NOT SUPPORTED: rows 13 and 21 said", "(c6o text, replaced by c6p; see the next bullet and L-LEASE in section 3) (1) THE REPEAT-SEND SENTENCE WAS NOT SUPPORTED: rows 13 and 21 said")
i = find("- SLIPS OF REPORT-c6n.md THAT I CORRECT HERE")
L[i] = sub(L[i], "The studio lead's own reading in ORDERS.md Q21.2 ('no takeover after expiry') does not match that file line. Rows 13 and 21 are now NOT FILMABLE until L-LEASE is answered, and the exit 'index not seen, accepted' is removed from risks list item 12.",
           "The exit 'index not seen, accepted' is removed from risks list item 12. c6o then made rows 13 and 21 NOT FILMABLE with no default, which was a second slip: the studio lead's answer Q22 (c) (ORD:186) already says 'item 1 wording plus one honest sentence that a gap longer than the lease is not claimed', which is reading 1, so reading 1 is in force; a claim limit that understates what the flows do is allowed, and ORD:151's 'no takeover after expiry' most plausibly meant that a second send does not take over (reading 2's behaviour), so no contradiction with mf-recovery.json line 26 is proven. c6p restates L-LEASE against Q22 (c) and ORD:230 (section 3).")
i = find("- SPOKEN LENGTH OF THE CLOSING CARD")
L[i] = ("- SPOKEN LENGTH OF THE CLOSING CARD, STILL NOT TESTED: with the rows as they stand (row 13 with the reading 1 sentence, row 14) the spoken card holds %d words (counted by evidence-c6p/verify-c6p.py: lines of %s words), about %d s at 150 words a minute; the c6n card held 144 words (about 58 s) and the c6o rows 103 words before a lease sentence. The run sheet budget is raised to %d s and the video total is about %d s, both estimates (row 11). The shorter text of L-CARDLEN option (b) holds %d words. No stopwatch run exists."
        % (C["NA"], ", ".join(map(str, C["WA"])), C["SA"], C["BA"], C["TOTA"], C["NB"]))
i = find("- THE NEWEST OWNER SHEET IS NOT v25")
L[i] = ("- THE NEWEST OWNER SHEET, RECHECKED: at 2026-11-16T16:01:45Z (UTC) = 21:31:45 IST the newest owner sheets in the steps-edits folder are OWNER-SHEET-v28-A.md, -v28-B.md and -v28-SOURCE.md (modification time 16:01:41Z, so still being written); c6o said v26-SOURCE and its check C-10c covered only v19 to v26-SOURCE. C-10c is rerun over v19 to v28 (all variants; evidence-c6p/static-checks-output.txt): the phrases 'never deletes', 'read, create and change only', 'does not delete' occur only in v19 (1 hit of 'never deletes'); v20 and v21 have no mention of read-only; every other sheet from v22 to v28 has one mention of read-only or read only (a count of any mention, which can be about something other than the HubSpot key). The rendered sheets are the A and B variants; the SOURCE files are templates. 'Newest' can change at any minute: write the check time whenever you say it. L-SHEET asks which one the owner reads (section 3).")
i = find("- 'UNKNOWN WITH ONE ALERT'")
L[i] = ("- 'UNKNOWN WITH ONE ALERT' (end state of K3B and K3) IS THE DESIGN INTENT, NOT A FAILURE, AS RELAYED: the test program and the studio lead's decisions describe it that way (the system cannot tell whether the CRM entry and the mail happened, so it sends one alert and a person decides); the test program mf.py is not among the audited files, so this is not verified against it. K3B being false in 'killed after the mail left' does not make K3 false: K3 (killed after the mail was stored by the test mailbox, the word of RES:97) is described correctly by mf.py. Only the K3B sentence is wrong.")

# ------------------------------------------------------------ section 1
i = find("- ONE ID:")
L[i] = sub(L[i], "the row numbers 1 to 72 are the same as in REPORT-c6l.md, REPORT-c6m.md and REPORT-c6n.md; rows 73 and up are new in c6o; the table lists the rows file by file, the lowest line first within a file's group REVERSED (highest line first) so that the lines of the file do not move while the rows are applied.",
           "the row numbers 1 to 72 are the same as in REPORT-c6l.md, REPORT-c6m.md, REPORT-c6n.md and REPORT-c6o.md; rows 73 to 94 are new in c6o; c6p adds no row. The table lists the rows file by file; inside a file's group the highest line comes first, so that the lines of the file do not move while the rows are applied.")
i = find("- THE CLOSING CARD ROWS ARE ONE SET")
L[i] = ("- THE CLOSING CARD ROWS ARE ONE SET: rows 3, 4, 11, 12, 13, 14, 15, 20, 29, 31 change the closing card and the lines that talk about it. They apply together or not at all, so the card is never left half-changed; under 'apply all defaults' they all apply. The set depends on five questions (L-CARD, L-CARDCUT, L-CARDTEXT, L-CARDLEN, L-LEASE; section 3 says which row depends on which). If you answer one of them differently, the studio lead names the rows to re-issue; the others stay.")
patch("| OS25 |", "(the newest sheet on disk)", "(a rendered sheet; v28 is newer, see section 0)")
patch("| OS26 |", "(a template with placeholders; the newest file in the folder)", "(a template with placeholders; v28 is newer, see section 0)")
patch("| OS19 |", "(assumed newest by REPORT-c6k.md)", "(assumed newest by REPORT-c6k.md; v28 is newest at 16:01 UTC = 21:31 IST)")
i = find("| OS19 |"); L.insert(i + 1, "| OS28 | handover/core-hardening/steps-edits/OWNER-SHEET-v28-A.md | owner sheet v28, variant A (newest rendered sheet at 16:01 UTC = 21:31 IST; still being written) |")

# ------------------------------------------------------------ section 3
i = find("| L-LEASE | studio lead")
L[i] = ("| L-LEASE | studio lead (his answers Q21.2 at ORD:151 and Q22 (c) at ORD:186; ORD:230 L-Q22c: the lease sentence stays out of the public post only) | Which honest sentence about the 45-second setting is spoken on the closing card (line 1) and shown in the scene 3 caption? "
        "READING 1, the studio lead's own answer Q22 (c) ('item 1 wording plus one honest sentence that a gap longer than the lease is not claimed'): card sentence '%s' (%d words); caption 'a lead sent twice with the same id is processed once (claimed only when the second send comes within 45 seconds of the first)'. Cost to the viewer: it adds the idea of a 45-second window that the flows do not need; it is true but weaker than the flows; to be filmed the repeat send must come within 45 seconds of the first send (rehearsal list item 13 asks for under 30 seconds, and scene 2 is planned at 40 seconds, so the scenes may have to be restructured: the studio lead names a builder, this report holds no rows for it). "
        "READING 2 (what the flow files show: a second send with the same id is refused at any time while its row exists, primary key on the contact id, MF:45, mf_leads.sql line 5, ON CONFLICT DO NOTHING at mf-form.json line 97, repeat answered from the stored row at mf-form.json lines 270 and 298; the lease only decides when the recovery flow may take over a contact that is not finished, mf-recovery.json line 26): card sentence '%s' (%d words, about %d more seconds of speech); caption 'a lead sent twice with the same id is processed once (the 45 seconds is only the recovery setting called the lease)'. Cost to the viewer: 15 more words and a second idea (recovery) on a card that is already long; it makes a stronger claim, so it needs the table rule seen in the take's database (check C-9 part 2) and one rehearsal repeat sent more than 45 seconds after the first (risks list item 12). "
        "NONE = no lease sentence anywhere; the plain statement 'A lead sent twice with the same id is processed once.' only; it REVERSES the studio lead's answer Q22 (c), so it needs his explicit yes. "
        "RECOMMENDATION: reading 2, after C-9 part 2 passes, because it matches the flows and does not force the 30-second gap; until then the default 1 is used because it is his own answer. The question ORD:151 'no takeover after expiry' versus mf-recovery.json line 26 needs no answer: the sentences above do not depend on it. | 1 (reading 1, Q22 (c) in force). Rows 13 and 21 apply on it. | No | 2 or none: rows 13 and 21 are re-issued with the sentence of that reading (the card sentence and caption above; for none, the plain statement only); risks list item 12 stays in force; for 2, rehearsal list item 13 only writes the gap down. | 13, 21 |"
        % (R1S, C["NR1S"], R2, C["NR2"], round(C["NR2"] / 150 * 60)))
i = find("| L-CARDLEN | studio lead")
L[i] = ("| L-CARDLEN | studio lead | Closing card length. OPTION (a), the default and the text of rows 13 and 14: %d words (line 1: %d, line 2: %d, line 3: %d, line 4: %d), about %d s at 150 words a minute; card budget %d s (the run sheet gave 30 s), total about %d s. OPTION (b), a shorter text of %d words, about %d s, budget %d s, total about %d s, used with reading 1 of L-LEASE: line 1 '%s' line 2 '%s' line 3 '%s' line 4 '%s' (with reading 2 add its sentence of %d words: about %d s more; with none, line 1 is 'A lead sent twice with the same id is processed once.'). All seconds are estimates from the word count; the stopwatch run (rehearsal list item 10) measures them. | (a): rows 13 and 14 as written, row 11 with %d s and about %d s in all. | No | (b): rows 13, 14 and 11 are re-issued with the (b) text and the numbers above. | 11, 13, 14, 86 |"
        % (C["NA"], *C["WA"], C["SA"], C["BA"], C["TOTA"], C["NB"], C["SB"], C["BB"], C["TOTB"], B1, B2, B3, B4, C["NR2"], round(C["NR2"] / 150 * 60), C["BA"], C["TOTA"]))
del L[find("| L-SCENES | studio lead")]
patch("| L-KILL (was Q2)", "If (b): row 1 is re-issued with:", "If (b): row 74 is re-issued (row 1 keeps its always-apply part) with:")
patch("| L-ONEDB | studio lead", "| No: no viewer-facing text says anything about the number of databases or stores until C-8 passes. The target wording of decision 10 goes into DECISION-one-store.md marked as a target (rows 72, 71, 70). No row of wave 1 depends on this question; rows 58 and 59 wait for C-8 only. |",
      "| No: no viewer-facing text says anything about the number of databases or stores until C-8 passes. The target wording of decision 10 goes into DECISION-one-store.md marked as a target (rows 72, 71, 70, 90, 91). Rows 90 and 91 are tied to this question and apply by default; they edit only the decision file, not text a viewer sees; 'yes' only lets the studio lead give a viewer sentence (a new row). Rows 58 and 59 wait for C-8 only. |")
patch("| L-SHEET (was Q10) |", "Sheets on disk: v19 to v25 variants A and B, and OWNER-SHEET-v26-SOURCE.md (a template, still being edited at 15:05 UTC = 20:35 IST). | v25 variant A. Not decided in any file I read.",
      "Sheets on disk at 16:01 UTC = 21:31 IST: v19 to v28, variants A and B from v24 on, and SOURCE templates; v28 is the newest and was still being written. | v28 variant A (the newest rendered sheet at the check time; c6o said v25 A, which was out of date). Not decided in any file I read.")
patch("| L-DEL (ANSWERED; part still open) |", "the take program run_real_check_n8n.py has no delete call and uses a HubSpot identity that cannot archive (Q19 item 1);",
      "the take program run_real_check_n8n.py has no delete call (Q19 item 1; the same answer says it uses a HubSpot identity that cannot archive, which is the studio lead's statement, UNVERIFIED, and is not the same thing as the owner's own HubSpot key, whose scope only the owner knows: Q20 item 3);")
patch("| L-DEL (ANSWERED; part still open) |", "answers (a), (b) or (c) of Q27 with line numbers.", "answers (a), (b) and (c) of Q27 with line numbers (the five entries of risks list item 11).")
# 3b
i = find("3b. Count of rows per question")
j = find("3c. 'APPLY ALL DEFAULTS'")
rowsq = ["L-APPROX", "L-CARD", "L-CARDCUT", "L-CARDLEN", "L-CARDTEXT", "L-KILL", "L-LEASE", "L-ONEDB", "L-PAGE", "L-SAVE", "C-4", "C-8"]
tb = ["3b. Count of rows per question, made by the build script from the table and checked by evidence-c6p/verify-c6p.py (which recounts from the markdown table of section 5):", "",
      "| Question or check | Rows tied to it | How many | Of those: wait ONLY for this | Of those: also wait for something else |", "|---|---|---|---|---|"]
for q in rowsq:
    r = cnt[q]
    only = [k for k in r if set(TOK.findall(rows[k]["st"])) == {q}]
    oth = [k for k in r if k not in only]
    tb.append("| %s | %s | %d | %d (%s) | %d (%s) |" % (q, lst(r), len(r), len(only), lst(only) or "none", len(oth), lst(oth) or "none"))
assert set(cnt) == set(rowsq), set(cnt) ^ set(rowsq)
tb.append("| (no question, no check) | %s | %d | ready | none |" % (lst(ready), len(ready)))
tb.append("| TOTAL | all rows | %d | ready %d, on defaults only %d, with a check %d, NOT FILMABLE until an answer %d | |" % (N, len(ready), len(onlyq), len(withc), 0))
tb.append("")
L[i:j] = tb
i = find("3c. 'APPLY ALL DEFAULTS'")
L[i] = ("3c. 'APPLY ALL DEFAULTS': what it does is in the box at the top. Rows it applies: the %d ready rows (%s) and the %d rows that wait only for a question (%s), %d rows in all, in the files VIDEO-RUNSHEET.md, PAGE-STATEMENTS-V4.md, N8N-START.md, mf.py, mf-form.json, mf-hook.json, mf-recovery.json, mf-sub-crm-mail.json, DECISION-one-store.md and build_mainframe.py. Rows 6 and 8 are in the ready rows: their text can be applied now, but the gates they add stay closed until the studio lead writes the entries they ask for (Words: READY). Rows it does not apply: %s (wait for a check). What changes in content: the closing card gets the four spoken lines of rows 13 and 14 WITH the reading 1 lease sentence (%d words, about %d s); scene 4 has no kill-case words and no rounded timing wording; the take saves every run (flow-file rows, the generator, saving notes); statements 19 and 20 are marked not for the web page; DECISION-one-store.md gets the target wording marked as a target."
        % (len(ready), lst(ready), len(onlyq), lst(onlyq), W1, lst(withc), C["NA"], C["SA"]))
patch("3d. Who runs the long-standing steps", "Loopback re-smoke: the studio lead, before the first rehearsal (DEC:13; decision 12); checks C-4, C-8 and the table part of C-9 are read during it.",
      "Loopback re-smoke: the studio lead, on the edited and imported flows, before the first rehearsal (DEC:13; decision 12); checks C-3, C-5, C-8 and the table part of C-9 are read during it; the import check C-4 comes before it (box, step 4).")
patch("3d. Who runs the long-standing steps", "the studio lead runs it on the loopback stand-ins before the first rehearsal and again after any change", "the studio lead runs it on the loopback stand-ins before the first rehearsal with real accounts and again after any change")
# 3e
patch("| Repeat-send check (rehearsal list item 13) |", "(a second take needs the owner's spend limit to cover it: the studio lead computes the retake count, Q21.4)", "(a second take costs a second run: the studio lead computes how many takes the cumulative cost limit covers, 'retake count: lead computes', Q21.4; the owner already said to use the credits, Q24)")
patch("| Repeat-send check (rehearsal list item 13) |", "| both clock times and the repeat reply are written; the repeat reply says the repeat flag is true; CRM 1 row; test mailbox 1 mail |",
      "| both clock times and the repeat reply are written; the repeat reply says the repeat flag is true (the flag in the reply that tells the repeat from a first send); CRM 1 row; test mailbox 1 mail; under reading 1 of L-LEASE the gap is under 30 seconds |")
patch("| Repeat-send rule seen (risks list item 12) |", "the table rule on the contact id is seen in the take's own database AND L-LEASE is answered", "the table rule on the contact id is seen in the take's own database AND the lease question is answered (the default is reading 1)")
patch("| Contact deletion (risks list item 11) |", "the four lines are written and the search shows no archive or delete call", "the five entries are written, every request line of the take script is listed and the search for the words archive and delete shows no call")
# ------------------------------------------------------------ section 4 glossary
patch("| L-CARDLEN, L-SCENES |", "| L-CARDLEN, L-SCENES | the two new questions of c6o (section 3): the length of the closing card, and the restructure of scenes 2 and 3 | c6n design review M1, M2 |",
      "| L-CARDLEN | the new question of c6o (section 3): the length of the closing card (c6p dropped L-SCENES: the restructure of scenes 2 and 3 is now a consequence of reading 1 of L-LEASE) | c6n design review M1 |")
patch("| NOT FILMABLE |", "status of a row whose text may not be filmed or applied until the studio lead has answered a question that has no default (rows 13 and 21, question L-LEASE)", "status used by c6o for rows 13 and 21; c6p has no such row any more (L-LEASE has a default)")
patch("| risks list, rehearsal list |", "(line 59 is its item 10; row 8 adds items 11 and 12)", "(line 59 is its item 10; row 8 adds items 11 and 12)")
patch("| risks list, rehearsal list |", "row 6 adds items 11 to 14)", "row 6 adds items 11 to 16)")
patch("| ORDERS.md answers Q19 to Q34 |", "Q27 the studio lead reads the take script at the final version.", "Q27 the studio lead reads the take script at the final version and answers (a) go marker before spending, (b) refusal after the end date, (c) key cancelled during a run and the exit code (QUESTIONS.md line 73).")
patch("| gate |", "a step on the run sheet that blocks the take until a named person has written a result with the time in UTC and IST; a stop sign written on the sheet, not a program", "a step on the run sheet that blocks the take until a named person has written a result with the time in UTC and IST; a stop sign written on the sheet, not a program (defined in the box)")
patch("| money stop, the post, re-pin, claim, take |", "defined in the first paragraph of the box at the top of this report", "defined in the box and in Words at the top of this report")
patch("| c6b to c6n |", "c6n (this file) supersedes c6m", "c6p (this file) supersedes c6o, which superseded c6n")

# ------------------------------------------------------------ section 5: 5a from the table, rows
i = find("5a. WHAT CHANGES"); j = find("5b. THE CLOSING CARD")
vis = [k for k in sorted(rows) if not rows[k]["view"].startswith("Nothing") and ("VIDEO-RUNSHEET" in rows[k]["f"] or "PAGE-STATEMENTS" in rows[k]["f"])]
flowrows = [k for k in sorted(rows) if rows[k]["f"].endswith(".json") or rows[k]["f"].endswith("build_mainframe.py")]
t5 = ["5a. WHAT CHANGES FOR A PERSON WATCHING THE VIDEO OR READING THE PAGE (made from the table: the %d rows of the run sheet and the page statements whose 'What the viewer sees' is not 'Nothing'; the full table follows; the flow-file rows %s change what the execution list shows in scenes 1 and 2, see row 24):" % (len(vis), lst(flowrows)), "",
      "| Row | Where | What a viewer sees after the row |", "|---|---|---|"]
for k in vis:
    f = rows[k]["f"]
    where = ("run sheet, line %s" if "RUNSHEET" in f else "page statements, line %s") % rows[k]["ln"]
    t5.append("| %d | %s | %s |" % (k, where, rows[k]["view"]))
t5.append("")
L[i:j] = t5
# rewrite the table
def rowline(k):
    r = rows[k]
    return "| %d | %s | %s | %s | %s | `%s` | `%s` | %s | %s |" % (k, r["st"], r["f"], r["ln"], r["view"], r["old"], r["new"], r["why"], r["was"])
a = find("| 1 | NOT APPLIED"); z = a
while L[z + 1].startswith("| ") and re.match(r"^\| \d+ \| NOT APPLIED", L[z + 1]): z += 1
assert z - a == 93, (a, z)
for off, k in enumerate(B.order):
    L[a + off] = rowline(k)
# section 5b mention
patch("5b. THE CLOSING CARD, BEFORE AND AFTER", "(the old file numbers six lines, the new card four; rows 4, 12 to 15 and 20)", "(the old file numbers six lines, the new card four; rows 4, 12 to 15 and 20)")
patch("| 1 | the repeat-send statement | card line 1 (row 13) |", "card line 1 (row 13)", "card line 1 (row 13; with the reading 1 lease sentence)")
patch("| 4 | alerts: two or one | card line 2: what an alert is, no statement about its speed (row 14) |", "(row 14)", "(row 14; line 2 keeps the explanation 'a warning mail')")

# ------------------------------------------------------------ section 6 and 7
patch("WHAT IS ANSWERED (your answers in ORDERS.md):", "the take script has NO delete call and uses a read-only HubSpot identity with archive_contacts 'no' and lists leftovers;",
      "the take script has NO delete call and, in the studio lead's words, uses a HubSpot identity with archive_contacts 'no' (the take script's identity; UNVERIFIED, and not the same as the owner's own HubSpot key, whose scope only the owner knows: Q20 item 3) and lists leftovers;")
patch("THE GATE (row 8, item 11 of the RISKS LIST", "before the take the studio lead reads the take script at the final version, runs two searches (one for the word archive, one for the word delete; I give two commands because the table cell must not hold a pipe character), writes the output on the run sheet, and writes a four-line record (version id; search output; 'matches the decision' or 'stop: tell the owner'; no notice that promises delete or archive is shown). Until then the take is blocked.",
      "before the take the studio lead reads the take script at the final version, lists EVERY line that sends a request to the customer list (method and path), answers Q27 (a), (b) and (c) with line numbers, runs two searches (one for the word archive, one for the word delete: an extra check, never enough alone) and writes the five entries of row 8 item 11 (version id; request lines; answers to (a), (b), (c); 'matches the decision' or 'stop: tell the owner'; no notice or owner sheet promises delete or archive). Until then the take is blocked.")
patch("| C-10b |", "any other call, or (b) not shown: STOP (no take on or after Mon 23 Nov 2026)", "any other call, or any of (a), (b), (c) not shown: STOP (no take on Mon 23 Nov 2026, Q25; latest start that day 18:04 UTC = 23:34 IST, L-23NOV)")
patch("| C-10c |", "part 1 DONE on the sheets on disk (v19 to v25 and v26-SOURCE, evidence-c6o/static-checks-output.txt section C-10c: v19 1 hit, others 0 for these phrases); v26-SOURCE was still being edited at 15:05 UTC = 20:35 IST;",
      "part 1 DONE on the sheets on disk at 2026-11-16T16:01:45Z = 21:31:45 IST (v19 to v28, all variants, evidence-c6p/static-checks-output.txt section C-10c: v19 1 hit of 'never deletes', all others 0 for the three phrases); the v28 files were still being written at 16:01:41Z, so the check must be repeated on the sheet the owner reads;")
patch("| C-9 |", "(the c6n exit 'index not seen, accepted' is removed)", "(the c6n exit 'index not seen, accepted' is removed; the lease question must also be answered, the default is reading 1)")
# ------------------------------------------------------------ section 8: coverage of the c6o reviews
i = find("COVERAGE OF THE c6n REVIEWS")
cov = ["COVERAGE OF THE c6o REVIEWS (review-c6o-design.md, review-c6o-naive.md, review-c6o-evidence.md):", "",
       "| Review item | Fix | Where / check |", "|---|---|---|",
       "| Naive B1 (apply-all-defaults leaves the card half-changed; five contradictions) | one definite card under the defaults: rows 11, 13, 14 hold the (a) text with the reading 1 sentence, exact word count and seconds in the box; all card rows apply together | box, rows 11, 13, 14, L-CARDLEN, section 1 |",
       "| Naive B2, design M1 (L-LEASE) | restated against Q22 (c) (ORD:186) and ORD:230; default 1 (his own answer); sentence texts for 1 and 2; 'none' says it reverses Q22 (c); costs to the viewer; a recommendation; definition of lease corrected | box, section 3 L-LEASE, Words, rows 13, 21, 8 (item 12) |",
       "| Design M2 (row 11 false figure; 75 vs 71 words; option (a) row; 37-word sentence) | row 11 states %d words, about %d s, budget %d s, about %d s in all; option (a) is now the text of rows 13 and 14; the reading 2 sentence is counted (%d words) | rows 11, 13, 14, L-CARDLEN |" % (C["NA"], C["SA"], C["BA"], C["TOTA"], C["NR2"]),
       "| Design M3 (section 5a stale, page rows missing) | 5a is made from the table (%d rows) | section 5a |" % len(vis),
       "| Design M4 (newest owner sheet) | C-10c rerun over v19 to v28 at 16:01:45Z; 'newest' restated with the time; L-SHEET default v28 A | section 0, section 3, C-10c, evidence-c6p/static-checks-output.txt |",
       "| Design M5 (row 90) | new text ends before ' owned by'; 'third place' removed; row 91 says some bookkeeping files stay files | rows 90, 91 |",
       "| Design M6 (row 6 item 16) | says it is not verified that deletion erases; third leak count added | row 6 |",
       "| Design M7 ('row N' in new text; 'accepted'; scene 3 timing; 30 s in the reason) | item 13 no longer says 'row 13 explains'; row 8's view no longer says 'accepted'; row 6's view says the repeat-send check; reasons updated; the check script scans new texts for 'row N' | rows 6, 8, verify-c6p.py |",
       "| Design M8 (row 76 design intent; 'stored'; L-23NOV; Q25/Q27 cover (a)(b)(c); QUESTIONS.md line 73) | row 76 and section 0 say design intent, relayed; rows 25, 37, 38 say 'stored'; 18:04 UTC = 23:34 IST used in row 8, box, C-10b; (a), (b), (c) all required | rows 76, 25, 37, 38, 8, box, C-10b |",
       "| Design m1 to m8 | m1 L-SAVE confirm wording kept (section 3); m2 'seven steps can stop' (box); m3 3e reworded (retake count, Q21.4, Q24); m4 the 144.3 s figure says 'from n8n coming back up' (rows 47, 77 to 80); m5 none needed; m6 section 1 sentence rewritten; m7 option (a) total includes the lease sentence; m8 controls now cover card length, 'row N', stale numbers (neg-output.txt) | section 3, rows 47, 77 to 80, verify-c6p.py |",
       "| Naive M1 (rows 17, 81 and Words say the 45 s is on the card) | rows 17, 81 and Words say 'may', true for every answer | rows 17, 81, Words |",
       "| Naive M2 (stale numbers in L-CARDLEN) | recomputed (%d words, %d s; option (b) %d words) | L-CARDLEN |" % (C["NA"], C["SA"], C["NB"]),
       "| Naive M3 (L-SCENES unanswerable) | L-SCENES removed; its substance is a consequence of reading 1 (item 13 and L-LEASE say what the studio lead does) | section 3, row 6 |",
       "| Naive M4 (contact-deletion gate described three ways) | one description: five entries, every request line, searches additional | box, L-DEL, section 6, 3e, row 8 |",
       "| Naive M5 (HubSpot key / identity) | the take script's identity (studio lead's words, UNVERIFIED) is kept apart from the owner's key (unknown) | section 3 L-DEL, section 6 |",
       "| Naive M6 (L-ONEDB and rows 90, 91) | box and section 3 say rows 90 and 91 apply by default and edit only the decision file | box, section 3 |",
       "| Naive M7 (row 14 vs row 44) | row 14's reason says the card line says only 'may stay' and 'not measured', true whatever statement 18 turns out to be | row 14 |",
       "| Naive M8 (step order) | one numbered order in the box; first rehearsal after the re-smoke and the two lines of item 14; Words and 3d agree | box, Words, 3d |",
       "| Naive M9 (L-KILL form and row) | reply form a or b; the question reads 'a/b'; row 74 named | box, section 3 |",
       "| Naive M10 (box too large; labels before definitions; setting names) | box rewritten: words first, a table of questions, one answer line; no setting names in the box | box |",
       "| Naive M11 ('switches ON' vs 'changes no running n8n') | one sentence: it edits the files; the studio lead sets the n8n values | box |",
       "| Naive minors | line 6 'never writes the lead' corrected; 'two crash tests' now 'two of four'; OS25 entry fixed and OS28 added; row 83 reason fixed; row 23 start time; leak-scan store list; row 92 film-v5; K3B/K3 name table kept (section 2) | Words, section 1, rows 23, 83, 92 |",
       "| Evidence caveats (the audited files are not in the repo checkout; the runner's own checker bugs; builder's controls run from a copy) | stated in section 0 (the audited tree is a read-only copy of branch origin/cloud/flows-audit in the build session's scratchpad); verify-c6p.py reads that copy; nothing new is claimed about files that were not read | section 0, section 7 |",
       "", "COVERAGE OF THE c6n REVIEWS (kept from REPORT-c6o.md):", ""]
L[i:i + 1] = cov
# ------------------------------------------------------------ section 9
patch("- [needs-lead] L-DEL part open:", "answers (a), (b) or (c) of Q27 with line numbers (his own plan at ORDERS.md Q27)", "answers (a), (b) and (c) of Q27 with line numbers (his own plan at ORDERS.md Q27)")
patch("- [needs-lead] Spoken length of the closing card", "decides whether the card text is shortened or the card time raised.", "decides whether L-CARDLEN option (a) or (b) fits.")
patch("- [needs-lead] L-LEASE (two readings, section 3), L-CARDLEN (two options), L-SCENES (restructure of scenes 2 and 3): each needs the studio lead's answer; rows 13 and 21 are NOT FILMABLE until L-LEASE is answered.",
      "- [needs-lead] L-LEASE (default 1; recommendation 2 after C-9 part 2) and L-CARDLEN (default (a)): both have defaults; the studio lead may change them. If reading 1 stays, the scenes 2 and 3 may have to be restructured so that the repeat send comes within 30 seconds of the first; this report holds no rows for that (a builder he names writes them).", 1) if False else None
i = find("- [needs-lead] L-LEASE (two readings")
L[i] = "- [needs-lead] L-LEASE (default 1; recommendation 2 after C-9 part 2) and L-CARDLEN (default (a)): both have defaults and the studio lead may change them. If reading 1 stays, scenes 2 and 3 may have to be restructured so that the repeat send comes within 30 seconds of the first send; this report holds no rows for that: a builder he names writes them."
i = find("- [needs-lead] Not reviewed:")
L.insert(i + 1, "- [needs-lead] The EGM review of the changed files, resolve and the drift report for c6p: run by the studio lead.")
# ------------------------------------------------------------ global renames
out = "\n".join(L)
out = out.replace("evidence-c6o/", "evidence-c6p/").replace("verify-c6o", "verify-c6p")
open(D + "REPORT-c6p.md", "w", encoding="utf-8").write(out + ("\n" if not out.endswith("\n") else ""))
print("built REPORT-c6p.md: rows", N, "ready", len(ready), "defaults", len(onlyq), "check", len(withc), "wave1", W1, "visible rows in 5a", len(vis), "card words", C["NA"], C["WA"])
