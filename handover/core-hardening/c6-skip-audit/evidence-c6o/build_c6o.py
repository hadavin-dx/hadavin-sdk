"""Builds REPORT-c6o.md from REPORT-c6n.md (read only). Every text patch must match exactly once (assert), so a silent miss is impossible.
The old-text of every row is also checked against the audited tree copy (once on its stated line) before the report is written.
Usage: python3 build_c6o.py   Output: REPORT-c6o.md next to REPORT-c6n.md. Reuses the parsing and table code of build_c6n.py."""
import re, sys
D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
TREE = "/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/c6/tree/handover"
H = "/home/user/hadavin-sdk"
src = open(D + "REPORT-c6n.md", encoding="utf-8").read()
LINES = src.split("\n")


def sub(t, old, new, count=1):
    n = t.count(old)
    assert n == count, "patch matched %d times (want %d): %r" % (n, count, old[:90])
    return t.replace(old, new)


def real(p):
    return H + "/" + p if p.startswith("handover/core-hardening/") else TREE + "/" + p[len("handover/"):]


PAT = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| ([^|]*) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")
rows = {}
row_line_idx = {}
first_line = None
for i, l in enumerate(LINES):
    m = PAT.match(l)
    if m:
        k = int(m.group(1))
        rows[k] = dict(i=k, st=m.group(2), f=m.group(3), ln=m.group(4), view=m.group(5), old=m.group(6), new=m.group(7), why=m.group(8), was=m.group(9))
        row_line_idx[k] = i
assert sorted(rows) == list(range(1, 73)), "rows parsed wrong"
first_line, last_line = min(row_line_idx.values()), max(row_line_idx.values())
assert last_line - first_line == 71, "rows not contiguous"

TOK = re.compile(r"L-[A-Z]+|C-\d+[a-d]?")


def rnew(k, old, new, count=1):
    rows[k]["new"] = sub(rows[k]["new"], old, new, count)


def rwhy(k, old, new, count=1):
    rows[k]["why"] = sub(rows[k]["why"], old, new, count)


def rview(k, old, new):
    rows[k]["view"] = sub(rows[k]["view"], old, new)


def set_dep(k, toks, nofilm=False):
    toks = sorted(set(toks), key=lambda x: (x[0] != "C", x))
    st = "NOT APPLIED; " + ("ready" if not toks else "; ".join(
        ([("after check " + ", ".join(t for t in toks if t.startswith("C-")))] if any(t.startswith("C-") for t in toks) else []) +
        ([("on the default of " + ", ".join(t for t in toks if t.startswith("L-")))] if any(t.startswith("L-") for t in toks) else [])))
    if nofilm:
        st = "NOT APPLIED; NOT FILMABLE until " + ", ".join(toks) + " is answered (no default)"
    rows[k]["st"] = st


def add_dep(k, *toks):
    cur = TOK.findall(rows[k]["st"])
    set_dep(k, cur + list(toks), nofilm="NOT FILMABLE" in rows[k]["st"])


def nrow(k, st, f, ln, view, old, new, why, was="new in c6o"):
    assert k not in rows
    rows[k] = dict(i=k, st=st, f=f, ln=str(ln), view=view, old=old, new=new, why=why, was=was)
    set_dep(k, TOK.findall(st))


RS = "handover/demo/VIDEO-RUNSHEET.md"
PG = "handover/demo/n8n-flows/PAGE-STATEMENTS-V4.md"
ONE = "handover/core-hardening/inputs/DECISION-one-store.md"
NSP = "handover/demo/n8n-flows/N8N-START.md"
GEN = "handover/demo/n8n-mainframe/build_mainframe.py"
CARD = "On the default of L-CARDLEN, the closing card length"  # unused label guard

# ======================================================================= B1: rows 13 and 21 (repeat-send sentence)
rows[13]["new"] = ('Line 1, statement, spoken: "A lead sent twice with the same id is processed once."')
rview(13, "Closing card line 1 adds the sentence that the repeat-send statement holds only within 45 seconds.", "Closing card line 1 says the repeat-send statement; the sentence about the lease is added only after the studio lead answers L-LEASE.")
rows[13]["why"] = ("Split of the old row 13 (c6k design review M1). NOT FILMABLE until L-LEASE is answered (c6n naive review B1). The report said two incompatible things about a second send: that it counts as processed once only within 45 s of the first (the old new text), and that a rule on the contact id refuses a second row at any time (risks list item 12). "
                   "What the sources show, read for this version: the contact table has 'lead_key text PRIMARY KEY' (n8n-flows-v4/mf_leads.sql line 5, MF:45), so a second send with the same id can never create a second row, at any gap, while the row exists; the flow writes the row with 'ON CONFLICT (lead_key) DO NOTHING' and a claim time of now plus 45 s (mf-form.json line 97); a repeat is answered from the stored row (mf-form.json lines 270 and 298: repeat true). "
                   "The 45 s lease decides something else: when the recovery flow may take over a row that is NOT finished (mf-recovery.json line 26: claim time already passed, state not done, review, unknown or failed, fewer than 3 attempts). So the lease does not limit the repeat sentence, and the studio lead's reading 'no takeover after expiry' (ORD:151) does not match mf-recovery.json line 26, which takes over after expiry. "
                   "The sentence 'we say this only when the second send comes within 45 seconds' is therefore NOT supported by the flows; it is removed from this row. Which honest lease sentence is spoken is the studio lead's question L-LEASE (two readings in section 3); until he answers, rows 13 and 21 carry only the plain statement and the lease sentence is NOT FILMABLE. "
                   "The unique rule on the contact id is NOT yet seen in the take's own database (MF:45 is the test program's table; DEC and ORD ask the studio lead to see it at the loopback re-smoke): risks list item 12 now stops the take without that; it no longer offers 'index not seen, accepted'. Sources: JF:97, MF:45, ORD:151, ORD:186")
set_dep(13, ["L-CARD", "L-LEASE", "L-CARDLEN"], nofilm=False)
rows[13]["st"] = "NOT APPLIED; NOT FILMABLE until L-LEASE is answered (no default); also on the default of L-CARD, L-CARDLEN"
rows[21]["new"] = ('Caption: "a lead sent twice with the same id is processed once". The screen is the evidence; the rehearsal must show the repeat reply and the clock times of both sends (write them on this run sheet).')
rview(21, "Scene 3 caption adds the sentence about the 45 seconds.", "Scene 3 caption keeps the plain statement; the sentence about the lease is added only after the studio lead answers L-LEASE.")
rows[21]["why"] = ("NOT FILMABLE until L-LEASE is answered (c6n naive review B1; the reading of the flows is in row 13). The caption carries only the plain statement and the rehearsal evidence. The old text 'within 45 seconds of the first send' and the rule 'the repeat send must come less than 30 seconds after the first send' are removed: the unique rule on the contact id refuses a second row at any gap (row 13), so a gap limit is not a condition of the statement; the gap is still written down in the rehearsal (rehearsal list item 13) because the second send must be shown to be a repeat of a row that exists. Sources: JF:97, MF:45, ORD:151, ORD:186")
rows[21]["st"] = "NOT APPLIED; NOT FILMABLE until L-LEASE is answered (no default)"

# ======================================================================= R1 / R33 / R39 split (design M4)
old1 = rows[1]["old"]
pa = '"About a minute after the crash (measured at lease 45 s: 18 kill runs, 60.1 to 61.9 s)". Clock starts at the kill.'
assert pa in old1
pre = "Scene 4 caption (FINAL, lane3 HB194, lease 45 s, film-v4, RELAYED-INDEPENDENT): "
assert old1.startswith(pre)
post = old1[old1.index(pa) + len(pa):]
assert post.startswith(" From n8n up: 52.9 to 54.9 s.")
# row 1 = ALWAYS part: the prefix
rows[1].update(old=pre, new=('Scene 4 filming note (a note for the person filming; it is not a caption): no test result in seconds in any caption, text card or voice (the studio lead cut the number from the video on 2026-11-16). '
                             'On screen only the live stopwatch overlay (the clock of the run being filmed; where the wait is cut short it carries the label "sped up, real wait" and the real time from the overlay) and the label "setting: lease 45 s" (a setting, not a result). Withdrawn old caption, kept as history: '),
               view="Scene 4 shows no test result in seconds; the live stopwatch, the label 'sped up, real wait' and the label 'setting: lease 45 s' stay.")
rows[1]["st"] = "NOT APPLIED; ready"
rwhy(1, rows[1]["why"], "ALWAYS-APPLY part of the old row 1 (split, c6n design review M4): the label of the line changes from 'FINAL caption' to a filming note, and the exceptions (stopwatch, 'sped up, real wait', 'setting: lease 45 s') are named. The wording part is row 74 (question L-APPROX), the kill-case, 52.9 and alert-delay corrections are row 75 (question L-KILL for the kill-case sentence). Sources: DEC:2 (decision 1), RES:92")
nrow(74, "NOT APPLIED; on the default of L-APPROX", RS, 90, "Scene 4 shows no caption with a time after the crash and no rounded wording.", pa,
     'Withdrawn caption (no time after the crash is shown, and no rounded wording such as "about a minute"). The clock of the run is the stopwatch overlay.',
     "L-APPROX WORDING part of the old row 1 (split, c6n design review M4): the caption with 'about a minute' and the range. If the studio lead answers yes to L-APPROX he gives the exact caption and this row is re-issued with it. Sources: DEC:2 (decision 1)")
rid = 75
nrow(75, "NOT APPLIED; on the default of L-KILL", RS, 90, "Scene 4 does not mention the two crash tests K3B and K3; the 52.8 figure is corrected.", post,
     (' The 18 kept crash runs of lane3 (60.1 to 61.9 s from the crash to the final state; 52.8 to 54.9 s from n8n coming back up) were measured on the film-v4 stand-in flows, not on the flows of this take, and stay out of the video. '
      'Two further lane3 runs at the same lease, VOID-fl45k3b (it never reached a final state, 338.7 s) and VOID-fl45k6c (the stand-in services were not up), were voided and are not counted; the cause is unknown. '
      'The kill cases K3B and K3 are not mentioned in scene 4. No statement about alert delay is made. Never "within 60 s".'),
     "Correction part of the old row 1: the from-n8n-up start was 52.9 and RESULTS.md line 92 says 52.8; the K3B sentence 'killed after the mail left' is false for K3B (K3B is killed while the mail connection is opening, the mail is not delivered); the 13-minute alert figure was relayed for other flows. The 18 kept runs are named with both voided runs (VOID-fl45k3b, VOID-fl45k6c). The kill-case sentence follows L-KILL (default a: not mentioned). Sources: RES:92, RES:97, MF:153")

# row 33 (PG:161)
old33 = rows[33]["old"]
pa33 = 'Caption wording: "about a minute after the crash (measured at lease 45 s: 18 kill runs, 60.1 to 61.9 s; K1 n=5 median 60.8 s, K2 n=5 median 60.9 s)". The clock starts at the kill.'
assert old33.startswith(pa33) and old33.endswith(" Do not pool medians.")
rows[33]["old"] = pa33
rows[33]["new"] = 'Caption wording: none (the studio lead cut the scene 4 number on 2026-11-16, and the earlier wording "about a minute after the crash (measured at lease 45 s ...)" is withdrawn).'
rwhy(33, rows[33]["why"], "L-APPROX WORDING part of the old row 33 (split, c6n design review M4). The always-apply part is row 76. If the studio lead answers yes to L-APPROX he gives the exact caption. Sources: DEC:2 (decision 1)")
nrow(76, "NOT APPLIED; ready", PG, 161, "Web page: the medians belong to stand-in flows.", " Do not pool medians.",
     " Do not pool medians. The medians belong to the film-v4 stand-in flows, not to the flows in the video.",
     "ALWAYS-APPLY part of the old row 33 (split, c6n design review M4): the medians in the old caption said 'measured at lease 45 s' without saying that the flows were stand-ins. Sources: RES:89, RES:92")

# row 39 (PG:149)
old39 = rows[39]["old"]
pa39 = '"At the film lease of 45 s, a lead interrupted by an n8n crash was finished about a minute after the crash."'
assert old39.startswith("20. " + pa39)
pb39 = old39[len("20. " + pa39):]
new39 = rows[39]["new"]
assert new39.startswith('20. "On the film-v4 stand-in flows')
cut = new39.index('" Final states:') + 1
nA, nB = new39[:cut], new39[cut:]
rows[39]["old"] = pa39
rows[39]["new"] = nA[len("20. "):]
rows[39]["why"] = "L-APPROX WORDING part of the old row 39 (split, c6n design review M4): the sentence with 'about a minute' and 'was finished' (8 of the 18 runs ended unknown with one alert, not finished). The always-apply part (the count, the two voided runs) is row 77. If the studio lead answers yes to L-APPROX he gives the exact wording. Sources: RES:89, RES:92"
nrow(77, "NOT APPLIED; ready", PG, 149, "Web page, statement 20: correct count (10 done, 8 unknown with one alert) and the two voided runs named.", pb39, nB,
     "ALWAYS-APPLY part of the old row 39 (split, c6n design review M4): 'all 18 kill runs correct' is replaced by the final states: 10 runs done (K1 5, K2 5) and 8 runs unknown with one alert (K3B 5, K3 3); the two voided runs VOID-fl45k3b and VOID-fl45k6c are named and the 5 runs that overlapped a voided run are listed. Sources: RES:89, RES:92")
rows[39]["new"] = rows[39]["new"]
# row 39 first piece must keep the '20. ' number: put it back in the old and new of the first piece
rows[39]["old"] = "20. " + pa39
rows[39]["new"] = nA
rows[77]["old"] = pb39

# ======================================================================= card rows: L-CARDTEXT ties (design M4) and L-CARDLEN (M1)
for k in (15, 20, 29, 31):
    add_dep(k, "L-CARDTEXT")
    rwhy(k, rows[k]["why"], rows[k]["why"] + " Row %d is also tied to L-CARDTEXT (c6n design review M4): it removes a card line, and the replacement card lines are the question L-CARDTEXT." % k)
for k in (13, 14):
    pass
add_dep(14, "L-CARDLEN")
rwhy(14, "Sources: MF:153, RS:82, NS:42, NS:45", "Row 14 is also tied to L-CARDLEN: the length of the four spoken lines (about 58 s with the old line 1 and the lease sentence) is the question L-CARDLEN, which offers a shorter text. Sources: MF:153, RS:82, NS:42, NS:45")

rows[11]["new"] = ("- The one video: scenes 1 to 4 and the closing card (scene 12): scene 1 25 s + scene 2 40 s + scene 3 25 s + scene 4 60 s = 150 s, plus the closing card: EST NOT MEASURED (the card length is the question L-CARDLEN; the spoken card text is about 58 s long at 150 words a minute, so the total is not 180 s as long as the card keeps its four spoken lines). "
                   "The next two lines count scenes 5 to 11, which are not in the one video (the studio lead's decision of 2026-11-16).<br>- Core scenes 1 to 10 and 12:")
rview(11, "the run sheet gives the length of the one video: 3 minutes.", "the run sheet gives 150 s for scenes 1 to 4 and says that the closing card length is not measured.")
rows[11]["why"] = ("c6n design review M1 and naive review M3: the c6n row wrote 'closing card 30 s = 180 s', a total that its own reason said was probably false. The four scenes add to 150 s (25 + 40 + 25 + 60, checked against the Time column of the run sheet rows 1, 2, 3, 4). The closing card is NOT given a number here because no stopwatch run of the card exists; the four spoken lines hold 144 words (about 58 s at 150 words a minute), which would make a total of about 208 s. "
                   "Two concrete ways to make the total true are the question L-CARDLEN: (a) cut the spoken card text to about 75 words (card about 30 s, total about 180 s), or (b) keep the text and give the card about 60 s (total about 210 s). Rows 11, 13 and 14 are tied to L-CARD and L-CARDLEN. Sources: RS:41, DEC:2 (decision 1)")
rows[11]["st"] = "NOT APPLIED; on the default of L-CARD, L-CARDLEN"

# ======================================================================= M3 carve-out for the 45 s setting (naive M1) and labels
rnew(17, 'the stopwatch overlay (the clock of this run) and the label "setting: lease 45 s"', 'the stopwatch overlay (the clock of this run; where the wait is cut short, with the label "sped up, real wait" and the real time from the overlay) and the label "setting: lease 45 s"')
rnew(2, "NO number in voice or caption", "NO test number in voice or caption (the 45 s lease setting is allowed: it is a setting, not a result)")
rnew(5, "no recovery number on screen", "no recovery number on screen (the 45 s lease setting is allowed: it is a setting, not a result)")
rnew(15, "NO NUMBER on the card.", "NO TEST NUMBER on the card (the 45 s lease setting is allowed: it is a setting, not a result).")
rnew(19, "NO NUMBER on screen (not measured on the flows of this take).", "NO TEST NUMBER on screen (the 45 s lease setting is allowed; nothing is measured on the flows of this take).")
rnew(30, "no recovery number in any caption.", "no recovery number in any caption (the 45 s lease setting is allowed: it is a setting, not a result).")
rnew(34, "no timing number in any caption or in the voice", "no test number in any caption or in the voice (the 45 s lease setting is allowed: it is a setting, not a result)")
for k in (2, 5, 15, 17, 19, 30, 34):
    rwhy(k, rows[k]["why"], rows[k]["why"] + " c6n naive review M1: the line now says that the 45 s lease setting and the stopwatch are allowed, so it does not contradict the closing card and the scene 4 label.")

# row 18 and row 1 put the cut range in notes: add a plain warning that the stopwatch shows the real time (naive M1)
rnew(18, "planning only, never said on screen or in the voice:", "planning only; never said or written in a caption, a card or the voice (the stopwatch overlay shows the real wait itself, which is the run's own clock):")

# ======================================================================= row 6: items 11 to 14 (naive M4, minors) and new items 15 and 16 (design M8)
r6 = rows[6]["new"]
r6 = sub(r6, "Write the list, with the date and time in UTC and IST, into the studio's handoff note (the file handoff\\SESSION-HANDOFF.md in the studio folder, not in this repository).",
         "Write the list, with the date and time in UTC and IST, on this run sheet under this item.")
r6 = sub(r6, "13. REPEAT-SEND TIMING (scene 3). The 45-second lease starts when the first send arrives, because the flow writes the claim row at that moment (mf-form.json line 97), not when the reply is shown. Write down the clock time of the first send in scene 2 and of the repeat send in scene 3 (UTC, to the second), and the reply text of the repeat. The gap between the two sends must be less than 30 seconds, so that 15 seconds of margin remain before the lease ends. Scene 2 is budgeted 40 seconds, so if the first send is the first thing in scene 2 the repeat comes about 40 seconds later, too close to 45: make the first send late in scene 2, or shorten scene 2, and redo the scene until the gap is under 30 seconds. After the repeat",
         "13. REPEAT-SEND CHECK (scene 3). The owner sends the same prepared send note twice (he pastes the note again; he types no new id). Write down the clock time of the first send in scene 2 and of the repeat send in scene 3 (UTC to the second, with IST), the reply text of the repeat (it must say the repeat flag is true), and the gap. The gap is written down, not limited: the unique rule on the contact id refuses a second row at any gap (row 13 explains; the lease only decides when the recovery flow may take over a contact that is not finished). If the gap is long, the studio lead may choose the shorter scenes of question L-SCENES. After the repeat")
r6 = sub(r6, "This item applies from the moment the four real-v5 flow files are edited to save every run (if they are not edited, delete this item).",
         "This item applies as soon as the four real-v5 flow files, or n8n's two settings, save every run; if they save nothing, the studio lead writes 'not applicable: saving is off' with the time in UTC and IST under this item.")
r6 = sub(r6, "He runs both checks himself, or names a builder to write the leak scan; the builder's name is written here: ______ (while it is empty, the gate cannot pass).",
         "He runs both checks himself, or names a builder to write the leak scan; each of the two lines carries the name of the person who ran that check (a line without a name does not count).")
r6 += ("<br>15. SECOND LEAK SCAN. After the first rehearsal with real accounts, the studio lead runs the same leak scan again on the stores of this computer (the six stores of the scan, hit counts only, never the values) and writes the counts and the time in UTC and IST under this item. Any hit in a store other than n8n's own database stops the take. This scan exists because the first scan runs on fake services only and the rehearsal is the first time a real mail account and a real customer-list account touch the flows."
       "<br>16. AFTER THE TAKE. The same day, the studio lead deletes every saved run from n8n (every execution, not only the ones on the list) and turns saving off again (both n8n settings and the flow-file settings back to none), then writes the time in UTC and IST under this item. Until it is written, n8n still holds the made-up names and e-mail addresses of the take.")
rows[6]["new"] = r6
rview(6, "the take is blocked until the workflow list, the owner-sheet check and the saved-runs checks are written", "the take is blocked until the workflow list, the owner-sheet check, the saved-runs checks and the second leak scan are written; after the take the saved runs are deleted")
rwhy(6, rows[6]["why"], rows[6]["why"] + " c6n changes: item 13 no longer limits the gap to 30 s (the limit followed from the 45 s reading that B1 of the c6n naive review shows is not supported; see row 13) and says how the owner sends the same id twice; the builder instruction and the blank in item 14 and the pointer to a file outside the repository in item 11 are removed from the file text; new item 15 (second leak scan, c6n design review M8) and item 16 (after the take: delete saved runs, turn saving off, M8).")

# ======================================================================= row 8: risks list items 11 and 12 (design M5, naive B1, M5)
r8 = rows[8]["new"]
i11 = r8.index("11. GATE, contact deletion")
i12 = r8.index("12. GATE, the repeat-send statement")
r8 = r8[:i11] + (
    "11. GATE, contact deletion (the studio lead's step). The studio lead decided that the take never deletes contacts (ORDERS.md Q23 of 2026-11-16 12:50 UTC = 18:20 IST). The independent review of 11:00 UTC (16:30 IST) reported only a listing request in the take script scripts/run_real_check_n8n.py, but the script is not in the audited files, so this is UNVERIFIED: the studio lead verifies it at the re-pin (the moment he puts together and reads the final version of the take files). "
    "Two scripts have similar names: scripts/run_real_check_n8n.py is the take script; scripts/run_real_check.py is the old desk test program, whose help text offers a clean-up option that archives contacts; it is not the take. Older plan text that shows the owner a notice 'up to 3 HubSpot contacts archived at the end' is probably stale and must not be shown. "
    "At the re-pin the studio lead reads EVERY line of the take script that sends a request to the customer list (HubSpot), not only the lines found by a search for archive and delete, because a delete can hide behind another word. He writes here, with date and time in UTC and IST: (1) the version id of the files he read; (2) each request line of the take script with its line number (method and path); (3) the answer to Q27 as (a), (b) or (c) with line numbers: (a) the script waits for a go marker before it spends anything, (b) the script refuses to run after the end date (the money stop), (c) what happens and which exit code results when the key is cancelled during a run; "
    "if (b) cannot be shown, STOP: no take on or after Mon 23 Nov 2026 (the target take is Wed 18 Nov 2026, ORDERS.md Q25); (4) 'matches the decision' or, if a request line deletes or archives, 'stop: tell the owner'; (5) that no owner sheet and no notice promises that the program deletes or archives contacts. "
    "The HubSpot key: what the owner's key may do is UNVERIFIED (ORDERS.md Q20 item 3 says it is not known from here); the studio lead asks the owner once at take prep; no text says 'read-only' or 'cannot archive' about the key until the owner has confirmed it. "
    "Made-up contacts are told from real ones by the made-up e-mail domain and the name marker that the take script uses; no file I read names them (the run sheet line 30 names example.test only for what is shown on screen), so the studio lead writes the exact domain and marker here at the re-pin (UNVERIFIED until then); the owner deletes by hand only contacts that carry them, and never any other contact. Until the lines above are written, nothing is touched in the CRM. Not checked: whether an archived contact keeps its e-mail address reserved.<br>") + (
    "12. GATE, the repeat-send statement: scene 3 and card line 1 are NOT FILMABLE until BOTH hold: (1) the unique rule on the contact id (the database rule that refuses a second row for the same contact id) has been seen in the table of the take's own database: in the loopback re-smoke the studio lead lists the table's rules (the psql command \\d mf_leads), writes the output here, and the output shows a primary key or a unique rule on the contact id; (2) the studio lead has answered L-LEASE (which lease sentence, if any, is spoken). "
    "There is no exit: if (1) is not seen, scene 3 and card line 1 are cut and the take goes on without them. In the test program the table is created with a primary key on the contact id (mf.py line 45) and the same rule is in n8n-flows-v4/mf_leads.sql line 5; that is not proof for the take database.")
rows[8]["new"] = r8
rwhy(8, rows[8]["why"], rows[8]["why"] + " c6n changes (c6n design review M5, naive review B1 and M5): item 11 now asks the studio lead to read every request line of the take script and to answer Q27 (a), (b), (c) with line numbers, states the HubSpot key scope as UNVERIFIED, and says how made-up contacts are told from real ones; item 12 no longer has the exit 'index not seen, accepted'. The meaning of (a), (b), (c) is from QUESTIONS.md line 73; what '(b) means stop' is applied here as: no take on or after Mon 23 Nov without it (the lead's own text, Q25, says exactly that). Sources: ORD:187, ORD:189, ORD:191, ORD:147")

# ======================================================================= row 47 and n=1 rows (design M6)
rnew(47, "(n=1, one run, v4 K1)", "(n=2, two runs, both 144.3 s, v4 K1; RES:85)")
rwhy(47, "Sources:", "c6n design review M6: RESULTS.md line 85 shows 2 runs for v4 K1 (n=2), not 1. Sources: RES:85,")
rows[47]["why"] = rows[47]["why"].replace("RES:85, RES:85,", "RES:85,")
nrow(78, "NOT APPLIED; ready", RS, 33, "Nothing on screen (planning note).", "lane3 v4 K1 144.3 s at lease 120 s, n=1 (RELAYED-INDEPENDENT)",
     "lane3 v4 K1 144.3 s at lease 120 s, n=2 (two runs, both 144.3 s; RESULTS.md line 85)",
     "n=1 was wrong: RESULTS.md line 85 shows 2 runs (c6n design review M6). The same count in the three other places is rows 79, 80 and 81. Sources: RES:85")
nrow(79, "NOT APPLIED; ready", RS, 23, "Nothing on screen (planning note).", "Source: lane3 v4 K1 144.3 s at lease 120 s (n=1, RELAYED-INDEPENDENT)",
     "Source: lane3 v4 K1 144.3 s at lease 120 s (n=2, two runs, both 144.3 s; RESULTS.md line 85)",
     "n=1 was wrong (c6n design review M6, RES:85). Sources: RES:85")
nrow(80, "NOT APPLIED; ready", PG, 120, "Web page, statement 17: the 120 s figure has two runs.", "measured 144.3 s once (n=1, v4 K1)",
     "measured 144.3 s in both of 2 runs (n=2, v4 K1; RESULTS.md line 85)",
     "n=1 was wrong (c6n design review M6, RES:85). Statement 17 lives on PAGE-STATEMENTS-V4.md line 120 (it is the page statement number 17). Sources: RES:85")
nrow(81, "NOT APPLIED; ready", PG, 145, "Web page: the 144.3 s figure has two runs.", "n=1 for the 144.3 s figure", "n=2 for the 144.3 s figure",
     "n=1 was wrong (c6n design review M6, RES:85). Sources: RES:85")

# ======================================================================= M7 residual lines
nrow(82, "NOT APPLIED; on the default of L-CARD, L-CARDCUT", RS, 57, "Nothing on screen (an open decision on the run sheet).",
     "The closing card names the take's 45 s and the 120 s lane3 figure separately.",
     "The closing card names only the take's 45 s setting; no lane3 figure (neither 45 s nor 120 s) is on the card.",
     "Rows 14 and 15 remove the 120 s lane3 figure from the card; this open decision (item 8) still said the card names it (c6n design review M7). Sources: RS:41, DEC:2 (decision 1)")
nrow(83, "NOT APPLIED; ready", RS, 52, "Nothing on screen (a rule on the run sheet): earlier runs are hidden from the list, not 'pruned'.",
     "prune old ones first. It must not be presented as privacy proof: the request body stays in n8n data until pruned.",
     "the studio lead hides the earlier executions from the list first. It must not be presented as privacy proof: the request body stays in n8n data until n8n's automatic removal of old runs removes it, if it ever does.",
     "'Prune' means two different things in the files (hiding a run on the screen, and n8n's automatic removal); the glossary uses HIDING and AUTOMATIC REMOVAL (c6n design review M7). Sources: NS:42, NS:45")
nrow(84, "NOT APPLIED; ready", RS, 30, "Nothing on screen (a note on the run sheet).",
     "Executions older than the take are pruned first; if a leftover execution shows, do not open it.",
     "The studio lead hides every execution made before the take from the list first (row of this scene about the take start time); if a leftover execution shows, do not open it.",
     "RS:30 still said 'pruned' (c6n design review M7). This is the wording part only; the saved-run rows 23 and 24 on the same line are separate pieces. Sources: NS:42")
nrow(85, "NOT APPLIED; ready", RS, 30, "Nothing on screen (a note on the run sheet).",
     "the request body stays in n8n data until pruned.",
     "the request body stays in n8n data until n8n's automatic removal of old runs removes it, if it ever does.",
     "RS:30 col 7 still said 'until pruned' (c6n design review M7). Sources: NS:42, NS:45")
nrow(86, "NOT APPLIED; ready", RS, 47, "Nothing on screen (a note on the run sheet).", "behind the sped-up scenes (4, 5, 9, 11)",
     "behind the sped-up scene (scene 4; scenes 5, 9 and 11 are not in the one video)",
     "RS:47 still counted scenes 5, 9 and 11 (c6n design review M7); the rest of the line is row 10. Sources: DEC:2 (decision 1)")
nrow(87, "NOT APPLIED; on the default of L-CARD, L-CARDLEN", RS, 6, "Nothing on screen (a note on the run sheet).", "EST total re-done: 355 s core, 380 s with scene 11.",
     "EST total re-done on 2026-11-16 for the one video: see the one-video line of this run sheet (line 44); the older totals 355 s and 380 s counted scenes that are not in the one video.",
     "RS:6 kept the old totals (c6n design review M7). The new total depends on the closing card length (L-CARDLEN). Sources: RS:44")
nrow(88, "NOT APPLIED; on the default of L-PAGE", PG, 144, "Web page: the 13-minute alert delay is marked not for the page.",
     "- Alert delay: up to about 13 minutes if n8n dies during the alert send (statement 19); n and raw file not given to me.",
     "- Alert delay: up to about 13 minutes if n8n dies during the alert send (statement 19; relayed for lane3 v4 flows, not the flows of the video, and not for the web page unless the studio lead says yes); n and raw file not given to me.",
     "PG:144 repeated the figure without the hold of row 43 (c6n design review M7). Sources: RES:78, RES:79")
nrow(89, "NOT APPLIED; ready", PG, 121, "Web page: the 45 s line says what was measured and what was not.", "45 s: NOT RUN.",
     "45 s: lane3 ran 18 kept crash runs on film-v4 stand-in flows (statement 20; the voided runs VOID-fl45k3b and VOID-fl45k6c are not counted); on the real-v5 flows of the video: NOT RUN.",
     "'45 s: NOT RUN' contradicted statement 20 (c6n design review M7). Sources: RES:89, RES:92")
nrow(90, "NOT APPLIED; ready", PG, 132, "Web page: the NOT RUN list says where 45 s was run.", "17 (lease 45 s)",
     "17 (lease 45 s on the real-v5 flows of the video; the film-v4 stand-in runs are in statement 20)",
     "PG:132 listed statement 17 at 45 s as NOT RUN with no word on statement 20 (c6n design review M7). Sources: RES:89")
nrow(91, "NOT APPLIED; on the default of L-ONEDB", ONE, 26, "Nothing (the one-store decision wording).",
     "The one store is Postgres, including n8n's own state, which for the re-smoke lives in a SEPARATE database `n8n`",
     "The target is one Postgres server that holds two databases: n8n's own database (`n8n`, separate from the claim database) and the claim database; the stage journal file is a third place that stays a file",
     "ONE:26 said 'the one store is Postgres' (c6n design review M7); the files never say 'two stores' or 'three stores': the three places are the n8n database, the claim database and the journal file. Sources: ORD:152")
nrow(92, "NOT APPLIED; on the default of L-ONEDB", ONE, 1, "Nothing (the one-store decision title).",
     "# DECISION: one database for the take",
     "# DECISION (TARGET until the loopback re-smoke, check C-8): one Postgres server for the take (n8n's own database and the claim database; the stage journal stays a file)",
     "ONE:1 titled the decision 'one database', which is the 'one store' wording the studio lead rejected (ORD:152). Sources: ORD:152")

# ======================================================================= M8: generator vs JSON rows 62-69
nrow(93, "NOT APPLIED; on the default of L-SAVE", GEN, 44, "Scenes 1 and 2: the generated flow files save every run.",
     '"saveDataSuccessExecution": "none", "saveDataErrorExecution": "none"',
     '"saveDataSuccessExecution": "all", "saveDataErrorExecution": "all"',
     "The four flow files are GENERATED by build_mainframe.py (its docstring line 6; the setting is the dictionary ST at line 44): a hand edit of the JSON (rows 62 to 69) is lost the next time the generator runs. GENERATOR RULE for rows 62 to 69: the builder applies this row AND rows 62 to 69; afterwards he runs the generator into a temporary folder with the arguments of the V5 README and compares the four generated files with the four edited ones: they must be identical, otherwise he stops and tells the studio lead (c6n design review M8). Sources: JF:424")
for k in range(62, 70):
    rwhy(k, rows[k]["why"], rows[k]["why"] + " GENERATOR RULE (c6n design review M8): these files are generated; apply row 93 as well and compare the generator output with these edits (row 93 explains).")

# ======================================================================= M6 naive: row 57 wording for an unconfirmed default
r57 = rows[57]["new"]
r57 = sub(r57, "(owner decision of 2026-11-16)", "(the owner's choice as recorded in the plan of the re-smoke, PLAN:125; the studio lead has not confirmed it, question L-SAVE)")
rows[57]["new"] = r57
rwhy(57, rows[57]["why"], rows[57]["why"] + " c6n naive review M7: the c6n new text called an unconfirmed default 'owner decision', which breaks the report's own rule that a default is never called a decision.")

# ======================================================================= C-1: old text once on its line, in the tree
bad = 0
for k, r in rows.items():
    fl = open(real(r["f"]), encoding="utf-8", errors="replace").read().split("\n")
    n = r["old"].count("<br>") + 1
    old = r["old"].replace("<br>", "\n")
    seg = "\n".join(fl[int(r["ln"]) - 1:int(r["ln"]) - 1 + n])
    if seg.count(old) != 1:
        bad += 1
        print("C-1 MISMATCH row", k, r["f"], r["ln"], repr(r["old"][:70]))
assert bad == 0, "old text mismatch"

# ======================================================================= order: bottom-up per file, stable
files_order = []
for k in sorted(rows):
    pass
file_first = {}
for k in range(1, 73):
    file_first.setdefault(rows[k]["f"], k)
for k in sorted(rows):
    if k > 72:
        file_first.setdefault(rows[k]["f"], 10 ** 6 + k)
order = sorted(rows, key=lambda k: (file_first[rows[k]["f"]], -int(rows[k]["ln"]), k if k <= 72 else 0 if False else k))
# keep original relative order of existing rows on equal line; new rows after them
order = sorted(rows, key=lambda k: (file_first[rows[k]["f"]], -int(rows[k]["ln"]), 0 if k <= 72 else 1, k))


def row_line(r):
    return "| %s | %s | %s | %s | %s | `%s` | `%s` | %s | %s |" % (r["i"], r["st"], r["f"], r["ln"], r["view"], r["old"], r["new"], r["why"], r["was"])


for k, r in rows.items():
    if k <= 72:
        r.setdefault("was", r["was"])
newlines = LINES[:first_line] + [row_line(rows[k]) for k in order] + LINES[last_line + 1:]
text = "\n".join(newlines)
NROWS = len(rows)

# ======================================================================= counts
cnt = {}
for k, r in rows.items():
    for t in set(TOK.findall(r["st"])):
        cnt.setdefault(t, []).append(k)
nofilm = [k for k, r in rows.items() if "NOT FILMABLE" in r["st"]]
ready = [k for k, r in rows.items() if r["st"].endswith("ready")]
onlyq = [k for k, r in rows.items() if k not in nofilm and TOK.findall(r["st"]) and all(t.startswith("L-") for t in TOK.findall(r["st"]))]
withc = [k for k, r in rows.items() if any(t.startswith("C-") for t in TOK.findall(r["st"]))]
assert len(ready) + len(onlyq) + len(withc) + len(nofilm) == NROWS, (len(ready), len(onlyq), len(withc), len(nofilm), NROWS)
fl = lambda xs: ", ".join(str(x) for x in sorted(xs))
ns = dict(sub=sub, rows=rows, cnt=cnt, fl=fl, D=D, ready=ready, onlyq=onlyq, withc=withc, nofilm=nofilm, NROWS=NROWS, order=order)

tb = ["| Question or check | Rows tied to it | How many | Of those: wait ONLY for this | Of those: also wait for something else |", "|---|---|---|---|---|"]
for t in sorted(cnt, key=lambda x: (x[0] != "L", x)):
    ks = sorted(cnt[t])
    only = [k for k in ks if set(TOK.findall(rows[k]["st"])) == {t}]
    other = [k for k in ks if k not in only]
    tb.append("| %s | %s | %d | %d (%s) | %d (%s) |" % (t, fl(ks), len(ks), len(only), fl(only) if only else "none", len(other), fl(other) if other else "none"))
tb.append("| (no question, no check) | %s | %d | ready | none |" % (fl(ready), len(ready)))
tb.append("| TOTAL | all rows | %d | ready %d, on defaults only %d, with a check %d, NOT FILMABLE until an answer %d | |" % (NROWS, len(ready), len(onlyq), len(withc), len(nofilm)))
s3b = text.index("| Question or check | Rows tied to it |")
e3b = text.index("\n\n3c.")
text = text[:s3b] + "\n".join(tb) + text[e3b:]

ns["text_holder"] = [text]
exec(open(D + "evidence-c6o/sections_c6o.py", encoding="utf-8").read(), ns)
text = ns["patch_sections"](text)

open(D + "REPORT-c6o.md", "w", encoding="utf-8").write(text)
print("written REPORT-c6o.md, lines", text.count("\n") + 1, "rows", NROWS, "ready", len(ready), "defaults-only", len(onlyq), "with-check", len(withc), "not-filmable", len(nofilm))
