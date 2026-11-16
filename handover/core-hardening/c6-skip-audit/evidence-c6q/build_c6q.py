"""Builds REPORT-c6q.md from REPORT-c6p.md (read only). Every patch asserts exactly one match.
Usage: python3 -B build_c6q.py   Output: REPORT-c6q.md in the folder above.  Reads the owner-sheet facts from evidence-c6q/static-checks-output.txt."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_c6q_text as T
from build_c6q_text import wc, C1, S1, R2, L2, L3, L4, B_L1_NONE, B_L1_R1, B_L2, B_L3, B_L4, CAP_NONE, CAP_R1, CAP_R2

D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
E = D + "evidence-c6q/"
L = open(D + "REPORT-c6p.md", encoding="utf-8").read().split("\n")


def sub(s, old, new, c=1):
    n = s.count(old)
    assert n == c, "expected %d match(es), found %d: %r" % (c, n, old[:90])
    return s.replace(old, new)


def find(prefix):
    idx = [i for i, l in enumerate(L) if l.startswith(prefix)]
    assert len(idx) == 1, "prefix matched %d lines: %r" % (len(idx), prefix[:70])
    return idx[0]


def patch(prefix, old, new, c=1):
    i = find(prefix)
    L[i] = sub(L[i], old, new, c)


def setline(prefix, new):
    L[find(prefix)] = new


ROWRE = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| ([^|]*) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")
COL = dict(id=0, st=1, f=2, ln=3, view=4, old=5, new=6, why=7, was=8)


def rowi(k):
    return find("| %d | NOT APPLIED" % k)


def getrow(k):
    return list(ROWRE.match(L[rowi(k)]).groups())


def putrow(k, g):
    L[rowi(k)] = "| %s | %s | %s | %s | %s | `%s` | `%s` | %s | %s |" % tuple(g)


def rsub(k, col, old, new, c=1):
    g = getrow(k)
    g[COL[col]] = sub(g[COL[col]], old, new, c)
    putrow(k, g)


def rset(k, col, new):
    g = getrow(k)
    g[COL[col]] = new
    putrow(k, g)


# ---------------------------------------------------------------- facts from the check run (owner sheets)
cs = open(E + "static-checks-output.txt", encoding="utf-8").read()
CT = re.search(r"check time \(UTC\): (\S+)", cs).group(1)


def ist(t):
    h, m, s = int(t[11:13]), int(t[14:16]), int(t[17:19])
    x = (h * 3600 + m * 60 + s + 19800) % 86400
    return "%02d:%02d:%02d" % (x // 3600, x % 3600 // 60, x % 60)


CTU = CT[11:19]
CTI = ist(CT)
sheets = re.findall(r"^(OWNER-SHEET-v(\d+)[^:]*\.md): (\d+) / (\d+) / (\d+) / (\d+)$", cs, re.M)
newest = max(int(x[1]) for x in sheets)
rend = sorted(x[0] for x in sheets if int(x[1]) == newest)
NEWEST_ONLY_SOURCE = all("SOURCE" in x for x in rend)
mt = re.findall(r"^(\d{4}-\d\d-\d\dT(\d\d:\d\d:\d\d)Z) (OWNER-SHEET-v28-[AB]\.md)$", cs, re.M)
V28T = sorted(set(m[1] for m in mt))[-1]
mt29 = re.findall(r"^(\d{4}-\d\d-\d\dT(\d\d:\d\d:\d\d)Z) (OWNER-SHEET-v29-SOURCE\.md)$", cs, re.M)
V29T = mt29[-1][1] if mt29 else None
assert newest == 29 and NEWEST_ONLY_SOURCE and V29T, (newest, rend, V29T)
RANGE = "v19 to v%d-SOURCE" % newest
sheet_zero = all(x[2] == "0" for x in sheets if x[0] != "OWNER-SHEET-v19.md")
assert sheet_zero and [x for x in sheets if x[0] == "OWNER-SHEET-v19.md"][0][2] == "1"
SHEETCHK = ("%s UTC = %s IST" % (CTU, CTI))

# ---------------------------------------------------------------- table of card lengths (numbers computed from the texts)
TAB = T.table()
tab_md = ["| Lease answer | Card length | Spoken words | Seconds at 150 words a minute | Card budget on the run sheet | Video total (scenes 150 s + budget) |", "|---|---|---|---|---|---|"]
for k, ln, w, s, b, tot in TAB:
    nm = {"none": "none (the default)", "1": "1 (45-second limit)", "2": "2 (lease explained)"}[k]
    tab_md.append("| %s | %s%s | %d | %s | %d s | about %d s |" % (nm, ln, " (the default)" if (k == "none" and ln == "(a)") else "", w, s, b, tot))
TABLE = "\n".join(tab_md)
NA = [r for r in TAB if r[0] == "none" and r[1] == "(a)"][0]
NB = [r for r in TAB if r[0] == "none" and r[1] == "(b)"][0]
W_A = (wc(C1), wc(L2), wc(L3), wc(L4))
assert NA[2] == sum(W_A) == 90 and NA[3] == "36.0" and NA[4] == 40 and NA[5] == 190
assert NB[2] == 74 and NB[4] == 30 and NB[5] == 180

# ---------------------------------------------------------------- rows
ROWS = {}
for l in L:
    m = ROWRE.match(l)
    if m:
        ROWS[int(m.group(1))] = m.groups()
N = len(ROWS)
assert N == 94

# row 6 (run sheet: rehearsal list items 11, 13, 15)
rsub(6, "new", " (This check needs n8n and is not run yet.)", "")
i13 = getrow(6)[COL["new"]]
a = i13.index("13. REPEAT-SEND CHECK")
b = i13.index("14. GATE, saved runs")
ITEM13 = ("13. REPEAT-SEND CHECK (scene 3). The owner sends the same prepared send note twice (he pastes the note again; he types no new id). "
          "Write down the clock time of the first send in scene 2 and of the repeat send in scene 3 (UTC to the second, with IST), the reply text of the repeat (it must say the repeat flag is true), and the gap between the two sends. "
          "If the closing card or the scene 3 caption says that the claim holds only within 45 seconds of the first send, the gap must be under 30 seconds, because the 45 seconds start when the first send arrives and scene 2 is planned at 40 seconds. "
          "If the gap is 30 seconds or more, that sentence is not filmed: the studio lead either has scenes 2 and 3 restructured so that the repeat send comes straight after the first reply (he names a builder) or takes the 45-second limit out of the card and the caption. "
          "If neither the card nor the caption says so, the gap is only written down. After the repeat the CRM list must still show 1 row and the test mailbox 1 mail; if not, stop and tell the studio lead (the person who sees it first says stop; the studio lead decides whether to film again).<br>")
g = getrow(6)
g[COL["new"]] = i13[:a] + ITEM13 + i13[b:]
putrow(6, g)
i15 = getrow(6)[COL["new"]]
a = i15.index("15. SECOND LEAK SCAN")
b = i15.index("16. AFTER THE TAKE")
ITEM15 = ("15. SECOND LEAK SCAN. After the first rehearsal with real accounts, the studio lead runs a second leak scan on the stores of this computer (the stores that the leak scan section of the start notes lists; hit counts only, never the values). "
          "It searches for four things: the real value of the mail account's password and the real value of the customer-list key, each read from the file or store that holds the keys and handed to the search without ever being printed or saved; and the made-up names and the made-up e-mail addresses used in that rehearsal. "
          "He writes the number of hits per store and the time in UTC and IST under this item. Any hit in a store other than n8n's own database stops the take; a hit inside n8n's own database is written down and the studio lead decides in writing whether the take goes on. "
          "The first scan runs on fake services and fake keys only; this second scan is the only one that can show whether a real key or a real mail password reached a saved run.<br>")
g = getrow(6)
g[COL["new"]] = i15[:a] + ITEM15 + i15[b:]
putrow(6, g)
rsub(6, "why", "c6n changes: item 13 of c6o only wrote the gap down; c6p restores the 30 s limit for reading 1, which is the studio lead's own answer Q22 (c) and therefore the default, and keeps 'only write it down' for reading 2 and none (c6o design review M1, M7); item 13 also says how the owner sends the same id twice;",
     "c6n changes: item 13 also says how the owner sends the same id twice;")
rsub(6, "why", "Item 13 measures from the first SEND, not from the first reply, and (under reading 1 of the lease question) asks for under 30 seconds,",
     "Item 13 measures from the first SEND, not from the first reply, and asks for under 30 seconds when the card or the caption carries the 45-second limit,")
rsub(6, "why", "item 16 comes after the take.",
     "item 16 comes after the take. c6q changes (c6p design review B1, M1, M3, M5; c6p naive review M6): item 13 asks for under 30 seconds only if the card or caption carries the 45-second limit, because the default puts no lease sentence on public video text (the studio lead's newest word, ORD:230), and no longer uses report words ('reading', 'the lease question'); item 11 loses its stale sentence 'This check needs n8n and is not run yet'; item 15 says what the second scan searches for (the real key values, read from the file that holds the keys and not printed, counts only), so it can show whether real keys reached a saved run.", 1)

# row 8 (risks list items 11, 12)
rset(8, "view", "Nothing on screen; the take is blocked until the studio lead has written the result of the contact-deletion check, and scene 3 is filmed only if the rule that refuses a second row was seen in the database the take runs on.")
rsub(8, "new", "the latest start on Mon 23 Nov is 18:04 UTC = 23:34 IST and the owner cancels the key by 18:19 UTC = 23:49 IST)",
     "the latest start on Mon 23 Nov is 18:04 UTC = 23:34 IST, a plan fact of the studio lead that moves if the seconds the take program needs, which he reads at the re-pin, differ; the owner cancels the key by 18:19 UTC = 23:49 IST)")
g = getrow(8)
n8 = g[COL["new"]]
a = n8.index("<br>12. GATE, the repeat-send statement")
ITEM12 = ("<br>12. GATE, the repeat-send statement: scene 3 and card line 1 are NOT FILMABLE until the unique rule on the contact id (the database rule that refuses a second row for the same contact id) has been seen in the table of the database the take runs on. "
          "The take runs on a fresh database container with the same table layout (the studio lead's answer of 2026-11-16 10:50 UTC = 16:20 IST: after the rehearsal container is removed, the take uses a fresh container), so the rule is looked at twice: in the loopback re-smoke, and again at take preparation after the fresh container is up. "
          "Each time the studio lead lists the table's rules (the psql command \\d mf_leads), writes the output here with the date and the time in UTC and IST, and the output shows a primary key or a unique rule on the contact id. "
          "If the closing card or the scene 3 caption says that a second send is never processed again, one rehearsal repeat sent more than 45 seconds after the first is also written here and its reply shows the repeat flag true; if it says the claim holds only within 45 seconds of the first send, item 13 of the rehearsal list applies. "
          "There is no exit: if the rule is not seen, scene 3 and card line 1 are cut and the take goes on without them. In the test program the table is created with a primary key on the contact id (mf.py line 45) and the same rule is in n8n-flows-v4/mf_leads.sql line 5; that is not proof for the take database.")
g[COL["new"]] = n8[:a] + ITEM12
putrow(8, g)
rsub(8, "why", "c6n changes (c6n design review M5",
     "c6q changes (c6p design review M6, M7 and minors): item 12 no longer waits for an answer about a lease sentence (the default puts none on the card or caption, ORD:230); it says the rule is looked at again in the take's fresh container (ORD:146, the studio lead's answer Q20.2); item 11 says that the latest start 18:04 UTC = 23:34 IST is a plan fact (ORD:229) that moves with the seconds the take program needs (the plan formula: deadline minus need_seconds, G10 of LRN:30 in the older release note v5); the unfinished approval of the lease wording is gate G12 (LRN:33) and LREP:80. DEPARTURE FROM ORD:147: the studio lead's answer Q20.3 asked for the card line 'the HubSpot key used by the take is read-only; the probe key is separate'; this row and every other row write nothing about what the owner's key may do, because the same answer says it is unknown from here (UNVERIFIED until the owner confirms it). c6n changes (c6n design review M5")

# row 13 and 21 and 11 (closing card)
rset(13, "st", "NOT APPLIED; on the default of L-CARD, L-CARDLEN, L-LEASE, L-POST")
rset(13, "view", "Closing card line 1 says the repeat-send statement and nothing about the 45 seconds.")
rset(13, "new", 'Line 1, statement, spoken: "%s"' % C1)
rset(13, "why", "Split of the old row 13 (c6k design review M1). The default puts no lease sentence on the card: the studio lead's newest word says the lease sentence stays out of the public post (ORD:230, later than his answer Q22 (c) at ORD:186), and unless he answers L-POST 'no' the card and caption are part of that post. "
     "The two lease sentences that could replace this line, with their word counts and what each costs the viewer, are in section 3 (L-LEASE); the lengths are in the table of the box. "
     "The contact table refuses a second row with the same contact id at any gap while the row exists (MF:45; mf_leads.sql line 5; ON CONFLICT DO NOTHING at JF:97; repeat answered from the stored row, JF:270 and JF:298), so the plain statement is true for a second send; it says nothing about a contact whose first run crashed, which the recovery flow may take over (JR:26). "
     "The unique rule on the contact id is NOT yet seen in the database the take runs on (risks list item 12 stops the take without it). Sources: JF:97, MF:45, ORD:151, ORD:186, ORD:230, LREP:80")
rset(21, "st", "NOT APPLIED; on the default of L-LEASE, L-POST")
rset(21, "view", "Scene 3 caption: the plain statement; the rehearsal writes down both send times.")
rset(21, "new", 'Caption: "%s". The screen is the evidence; the rehearsal must show the repeat reply and the clock times of both sends (write them on this run sheet).' % CAP_NONE)
rset(21, "why", "Default: no lease sentence on the caption (ORD:230; question L-POST). The two other captions are in section 3 (L-LEASE). Rehearsal list item 13 writes the clock times and the gap down. Sources: JF:97, MF:45, ORD:151, ORD:186, ORD:230")
rset(11, "st", "NOT APPLIED; on the default of L-CARD, L-CARDLEN, L-LEASE, L-POST")
g = getrow(11)
g[COL["new"]] = ("- The one video: scenes 1 to 4 and the closing card (scene 12): scene 1 25 s + scene 2 40 s + scene 3 25 s + scene 4 60 s = 150 s, plus the closing card %d s (an ESTIMATE from the word count: the four spoken card lines hold %d words, which is about %d s at 150 words a minute; "
                 "the card time is EST NOT MEASURED until the stopwatch run of rehearsal list item 10) = about %d s in all. The next two lines count scenes 5 to 11, which are not in the one video (the studio lead's decision of 2026-11-16).<br>- Core scenes 1 to 10 and 12:" % (NA[4], NA[2], round(float(NA[3])), NA[5]))
g[COL["why"]] = ("The closing card of this report holds %d words under the defaults (card line 1 is the plain statement of 11 words; counted by evidence-c6q/verify-c6q.py), about %d s at 150 words a minute, so the budget of 30 s is raised to %d s and the total is about %d s, labelled as an estimate (c6p design review M2). "
                 "The four scenes add to 150 s (25 + 40 + 25 + 60, from the Time column of the run sheet scenes 1 to 4). The card needs a stopwatch run to be measured; until then the number is an estimate. "
                 "If the studio lead answers L-LEASE 1 or 2 (and L-POST 'no') or L-CARDLEN (b), this row is re-issued with the matching line of the table of lengths in the box (for example 115 words, about 46 s, budget 50 s, total about 200 s for the 45-second limit sentence with option (a)). Sources: RS:41, DEC:2 (decision 1) c6o and c6p history: row 11 of c6o wrote the card as 'about 58 s' (the c6n six-line card of 144 words) (c6o design review M2, naive review B1); c6p wrote 115 words and 46 s with the 45-second limit sentence, which c6q no longer uses as the default."
                 % (NA[2], round(float(NA[3])), NA[4], NA[5]))
putrow(11, g)
rsub(14, "why", "with line 1 of row 13 the four spoken lines hold 115 words (about 46 s); L-CARDLEN option (b) gives a shorter text of 87 words.",
     "with line 1 of row 13 the four spoken lines hold %d words (about %d s); the table of lengths in the box gives the other cases (option (b) and the lease sentences)." % (NA[2], round(float(NA[3]))))
rsub(14, "why", "so that the card fits 50 s;", "so that the card stays short;")
rsub(14, "why", "Row 14 is also tied to L-CARDLEN:", "Row 14 is also tied to L-CARDLEN (and the card line 4 words 'other lease settings' name a setting that no spoken line explains under the default; section 3, L-POST, says so):")

# rows 25, 37, 47, 57, 70, 72, 90, 91: no report-only labels inside the new texts
rsub(25, "new", "; the word of RES:97)", "; 'stored' is the word the lane3 results table uses)")
rsub(37, "new", "(the word of RES:97; the test mailbox", "('stored' is the word the lane3 results table uses; the test mailbox")
rsub(47, "new", " (n=2, two runs, both 144.3 s, v4 K1; RES:85)", " (n=2, two runs, both 144.3 s, v4 K1)")
rsub(57, "new", "(the owner's choice as recorded in the plan of the re-smoke, PLAN:125; the studio lead has not yet confirmed it)", "(the owner's choice as recorded in the plan of the re-smoke; the studio lead has not yet confirmed it)")
rsub(70, "new", "(target; true only after check C-8)", "(target; true only after the loopback re-smoke shows that n8n runs on Postgres)")
rsub(72, "new", "they are not true until the loopback re-smoke shows that n8n runs on Postgres, check C-8)", "they are not true until the loopback re-smoke shows that n8n runs on Postgres)")
rsub(91, "new", "(TARGET until the loopback re-smoke, check C-8)", "(TARGET until the loopback re-smoke shows which database n8n uses)")
rset(90, "new", "The target is one Postgres server with two databases: the claim database and, for n8n's own state, a SEPARATE database `n8n`")
rsub(90, "why", "The new text ends right before ' owned by the role', so the sentence that follows still describes the n8n database;",
     "The new text now ends with the database `n8n` itself, so the words ' owned by the role' that follow in the file belong to that database (in c6p the new text ended with 'own state' and ' owned by' attached to the state; c6p design review minor);")

# ---------------------------------------------------------------- section 3: L-LEASE, L-POST, L-CARDLEN, L-SHEET, L-DEL, L-ONEDB, L-SAVE
LEASE_ROW = ("| L-LEASE | studio lead (his answers: ORD:151, Q21.2; ORD:186, Q22 (c) of 12:50 UTC = 18:20 IST; ORD:230, L-Q22c, the newest) | "
             "Which sentence about the 45-second setting goes on the closing card (line 1) and in the scene 3 caption? 1 and 2 count only if L-POST is answered 'no'. "
             "NONE (the default): card line 1 is the plain statement '%s' (11 words) and the caption is '%s'; no sentence about 45 seconds on any public video text. "
             "ANSWER 1 = the studio lead's answer Q22 (c) ('item 1 wording plus one honest sentence that a gap longer than the lease is not claimed'): card sentence '%s' (25 words); caption '%s'. What the viewer gets: a 45-second window that the flows do not need; true, but weaker than what the flows do; it can only be filmed if the repeat send comes within 45 seconds of the first send (rehearsal list item 13 asks for under 30 seconds and scene 2 is planned at 40 seconds, so scenes 2 and 3 may have to be restructured: the studio lead names a builder; no row here does it). "
             "ANSWER 2 = what the flow files show: a second send with the same id is not processed again at any time while its row exists (primary key on the contact id, MF:45, mf_leads.sql line 5, ON CONFLICT DO NOTHING at JF:97, repeat answered from the stored row, JF:270 and JF:298); the 45 seconds only decide when the recovery flow may take over a contact that is not finished (JR:26): card sentence '%s' (40 words; it REPLACES the 25-word sentence of answer 1, so the net is 15 more words and about 6 more seconds of speech, see the table of lengths in the box); caption '%s'. What the viewer gets: a second idea (a second program that takes over stopped contacts) on a card that is already long. "
             "NOT TO BE SPOKEN AS FACT BEFORE C-9 PART 2: the facts of answer 2 rest on files that are not in the checkout and on a table rule not yet seen in the database the take runs on; they stay in the report until part 2 of check C-9 has passed, and a rehearsal repeat sent more than 45 seconds after the first has shown the repeat flag. "
             "WHAT 'NONE' CLAIMS, HONESTLY: 'processed once' for a second send of the same id, which is true while the contact's row exists once the table rule is seen in the take's database; it says nothing about a contact whose first run crashed, which the recovery flow may take over and re-claim (three tries in total, LREP:80), so the words 'processed once' beside a crash scene need the studio lead's approval of the lease wording (gate G12, LRN:33), which is OPEN with him; I do not give it. "
             "WHAT 'NONE' DOES TO YOUR EARLIER ANSWER: if 'public post' includes the card and caption (L-POST yes), 'none' is your newest word and Q22 (c)'s sentence lives only in the one final owner sheet and the release note, which no row here edits (section 9 names who adds it); if 'public post' does not include them (L-POST no), Q22 (c) is in force and the choice is 1 or 2. "
             "RECOMMENDATION: keep none for the video; answer L-POST 'no' and choose 2 only after C-9 part 2 has passed. | none (ORD:230, if L-POST is yes). Rows 11, 13 and 21 apply on it. | No | "
             "1 or 2 (with L-POST 'no'): rows 11, 13 and 21 are re-issued with that sentence and that line of the table of lengths; risks list item 12 stays in force; with 2, rehearsal list item 13 only writes the gap down. | 11, 13, 21 |") % (C1, CAP_NONE, S1, CAP_R1, R2, CAP_R2)
setline("| L-LEASE | studio lead", LEASE_ROW)
POST_ROW = ("| L-POST (new in c6q) | studio lead | Your answer in ORDERS.md (ORD:230, 'L-Q22c') says: 'no, the lease sentence stays out of the public post'. Does 'public post' include the video's closing card and its scene 3 caption? "
            "| Yes, they count as public. So the default puts no lease sentence on the card or the caption, and the 45-second limit lives in the one final owner sheet and the release note only. | No | "
            "If no: the card and caption may carry the sentence chosen in L-LEASE (1 or 2); rows 11, 13 and 21 are re-issued. What a viewer sees under every answer: the on-screen label 'setting: lease 45 s' (rows 1 and 17) and the words 'other lease settings' of card line 4 (row 14) stay; they are not the lease sentence, but the word 'lease' is not explained in the video unless answer 2 is chosen; say so if you want them changed. | 11, 13, 21 |")
i = find("| L-LEASE | studio lead")
L.insert(i, POST_ROW)  # L-POST before L-LEASE in the table: read first
# L-CARDLEN
CARDLEN_ROW = ("| L-CARDLEN | studio lead | Closing card length. OPTION (a), the default and the text of rows 13 and 14: the four spoken lines hold %d words (line 1: %d, line 2: %d, line 3: %d, line 4: %d), about %d s at 150 words a minute; card budget %d s (the run sheet gave 30 s), total about %d s. "
               "OPTION (b), a shorter text: line 1 '%s' line 2 '%s' line 3 '%s' line 4 '%s' (%d words with the plain line 1, about %s s, budget %d s, total about %d s). "
               "The other cases (a lease sentence with (a) or (b)) are in the table of lengths in the box: a lease sentence REPLACES nothing in lines 2 to 4 and is added to line 1, and answer 2 replaces the 25-word sentence of answer 1 (net +15 words). All seconds are estimates from the word count; the stopwatch run (rehearsal list item 10) measures them. "
               "| (a): rows 13 and 14 as written, row 11 with %d s and about %d s in all. | No | (b): rows 13, 14 and 11 are re-issued with the (b) text and the numbers above. | 11, 13, 14, 86 |") % (
    NA[2], W_A[0], W_A[1], W_A[2], W_A[3], round(float(NA[3])), NA[4], NA[5], B_L1_NONE, B_L2, B_L3, B_L4, NB[2], NB[3], NB[4], NB[5], NA[4], NA[5])
setline("| L-CARDLEN | studio lead", CARDLEN_ROW)
# L-SHEET
SHEET_ROW = ("| L-SHEET (was Q10) | OWNER ONLY (the studio lead asks him; if the owner agrees, the studio lead may answer for him) | Confirm the one final owner sheet. The studio lead ordered ONE sheet of at most 6,300 words, with the two routes A and B for the older key and marked blanks for the facts only the owner or the studio lead holds (ORD:226 to ORD:228). "
             "Version v29 is coming: at %s = %s IST only OWNER-SHEET-v29-SOURCE.md exists (written %s UTC), not a rendered v29, and v28 A and B were last changed at %s UTC. | The sheet the studio lead names final once v29 is rendered. Until then C-10c has been run on %s as a stand-in only. "
             "'Apply all defaults' does not cover this question: write it as a separate line. | No | C-10c is run on the confirmed sheet. No row touches an owner sheet. | none (check C-10c) |") % (CTU + " UTC", CTI, V29T, V28T, RANGE)
setline("| L-SHEET (was Q10)", SHEET_ROW)
patch("| L-DEL (ANSWERED; part still open)", "Until then the run sheet says 'UNVERIFIED' and that the studio lead verifies at the re-pin (the order's own words: 'lead verifies at re-pin').",
      "Until then the run sheet says 'UNVERIFIED' and that the studio lead verifies at the re-pin (the order's own words: 'lead verifies at re-pin'). DEPARTURE FROM ORD:147: the same-day answer Q20.3 asked for the card line 'the HubSpot key used by the take is read-only; the probe key is separate'; no row writes it, because that answer also says the scope is unknown from here and the owner has not confirmed it.")
patch("| L-SAVE | studio lead", "Yes (PLAN:125). Checks: C-11 (static, done) and C-4 (import check, not run).", "Yes (the plan of the re-smoke already says all for both settings, PLAN:125). Checks: C-11 (static, done) and C-4 (import check, not run). Why failed runs matter: with saving of failed runs on, a failed run keeps the contact's name and e-mail address in n8n's database, which is why the leak scan and the deletion after the take exist (rows 6 and 49).")
patch("| L-CARD (was Q1, part 1)", "3, 4, 11, 12, 13, 14, 15, 20, 29, 31, 81, 86 |", "3, 4, 11, 12, 13, 14, 15, 20, 29, 31, 81, 86 |")

# ---------------------------------------------------------------- tables 3b / section 3 tied columns are regenerated from the statuses below
TOK = re.compile(r"L-[A-Z]+|C-\d+[a-d]?")
cnt = {}
ready = []
for k in sorted(ROWS):
    g = getrow(k)
    for t in set(TOK.findall(g[COL["st"]])):
        cnt.setdefault(t, []).append(k)
    if g[COL["st"]].endswith("ready"):
        ready.append(k)
withc = [k for k in sorted(ROWS) if any(t.startswith("C-") for t in TOK.findall(getrow(k)[COL["st"]]))]
onlyq = [k for k in sorted(ROWS) if k not in ready and k not in withc]
W1 = len(ready) + len(onlyq)
assert (len(ready), len(onlyq), len(withc), W1) == (49, 42, 3, 91)
lst = lambda a: ", ".join(map(str, a))
# table 3b: rebuild all question/check lines
b0 = find("| L-APPROX | 33, 39, 73")
b1 = find("| (no question, no check)")
newb = []
for t in sorted(cnt):
    rws = cnt[t]
    only = [k for k in rws if set(TOK.findall(getrow(k)["st".__len__() * 0 + 1])) == {t}]
    also = [k for k in rws if k not in only]
    newb.append("| %s | %s | %d | %d (%s) | %d (%s) |" % (t, lst(rws), len(rws), len(only), lst(only) if only else "none", len(also), lst(also) if also else "none"))
L[b0:b1] = newb
# section 3 'rows tied' column: every question line
for t in cnt:
    if not t.startswith("L-"):
        continue
    pre = "| %s" % t
    idxs = [i for i, l in enumerate(L) if l.startswith(pre + " ") and l.count(" | ") >= 6 and "Confirmed" not in l and not re.match(r"\| %s \| [\d, ]+ \| \d+ \|" % re.escape(t), l)]
    assert len(idxs) == 1, (t, idxs)
    i = idxs[0]
    L[i] = re.sub(r" \| ([\d, ]+) \|$", " | %s |" % lst(cnt[t]), L[i])
# TOTAL line unchanged in counts
# ---------------------------------------------------------------- 3c, 3e, 3d
patch("3c. 'APPLY ALL DEFAULTS'", "the closing card gets the four spoken lines of rows 13 and 14 WITH the reading 1 lease sentence (115 words, about 46 s);",
      "the closing card gets the four spoken lines of rows 13 and 14 with the plain statement as line 1 and no lease sentence (%d words, about %d s); the card line 4 and the label 'setting: lease 45 s' name the lease setting without explaining it (L-POST);" % (NA[2], round(float(NA[3]))))
patch("| Repeat-send check (rehearsal list item 13)", "under reading 1 of L-LEASE the gap is under 30 seconds |", "if the card or the caption carries the 45-second limit the gap is under 30 seconds, otherwise it is only written down |")
patch("| Repeat-send check (rehearsal list item 13)", "In a rehearsal: redo scene 3 (or choose L-SCENES).", "In a rehearsal: redo scene 3, or the studio lead takes the 45-second limit out of the card and caption.")
patch("| Repeat-send rule seen (risks list item 12)", "the table rule on the contact id is seen in the take's own database AND the lease question is answered (the default is reading 1)",
      "the table rule on the contact id is seen in the database the take runs on, in the re-smoke and again after the take's fresh container is up")
patch("3d. Who runs the long-standing steps", "before the first rehearsal (DEC:13; decision 12)", "before the first rehearsal (DEC:13; decision 12; the first rehearsal comes after steps 5 to 9 of the box list)")

# ---------------------------------------------------------------- section 1 / 5b / 7 / 8 / 9 / 4 patches
patch("- ONE ID: the first column", "rows 73 to 94 are new in c6o; c6p adds no row.", "rows 73 to 94 are new in c6o; c6p and c6q add no row.")
patch("- ONE ID: the first column", "REPORT-c6n.md and REPORT-c6o.md;", "REPORT-c6n.md, REPORT-c6o.md and REPORT-c6p.md;")
patch("- THE CLOSING CARD ROWS ARE ONE SET:", "rows 3, 4, 11, 12, 13, 14, 15, 20, 29, 31 change the closing card and the lines that talk about it.",
      "rows 3, 4, 11, 12, 13, 14, 15, 20, 29, 31 change the closing card and the lines that talk about it (rows 81 and 86 are tied to the same questions: row 81 is a note about naming the 45 seconds, row 86 the old totals; they apply with the set).")
patch("- THE CLOSING CARD ROWS ARE ONE SET:", "The set depends on five questions (L-CARD, L-CARDCUT, L-CARDTEXT, L-CARDLEN, L-LEASE;", "The set depends on six questions (L-CARD, L-CARDCUT, L-CARDTEXT, L-CARDLEN, L-LEASE, L-POST;")
patch("| 1 | the repeat-send statement | card line 1 (row 13", "| card line 1 (row 13; with the reading 1 lease sentence) |", "| card line 1 (row 13; the plain statement under the default) |")
patch("| 1 | the repeat-send statement", "with the reading 1 lease sentence", "the plain statement under the default")
patch("| OS28 |", "(newest rendered sheet at 16:01 UTC = 21:31 IST; still being written)", "(the newest rendered sheet at the check of %s; v29 is coming)" % SHEETCHK)
patch("| OS19 |", "v28 is newest at 16:01 UTC = 21:31 IST", "v29-SOURCE is newest at %s" % SHEETCHK)
patch("| OS25 |", "(a rendered sheet; v28 is newer, see section 0)", "(a rendered sheet; v28 and v29-SOURCE are newer, see section 0)")
patch("| OS26 |", "(a template with placeholders; v28 is newer, see section 0)", "(a template with placeholders; v28 and v29-SOURCE are newer, see section 0)")
# new short names: after the OS28 row
i = find("| OS28 |")
L.insert(i + 1, "| LREP | handover/core-hardening/REPORT.md | the studio lead's own report blocks (line 80 names the open approval of the lease sentence) |")
L.insert(i + 2, "| LRN | handover/core-hardening/steps-edits/LEAD-RELEASE-NOTE-v12.md | the release note for the studio lead (gate G12 is the approval of the lease wording) |")
# C-9, C-10b, C-10c
patch("| C-9 |", "part 2: the same rule seen in the take's own table (psql \\d mf_leads)", "part 2: the same rule seen in the table of the database the take runs on (psql \\d mf_leads), in the re-smoke and again at take preparation after the fresh container is up (ORD:146)")
patch("| C-9 |", "There is no allowance (the c6n exit 'index not seen, accepted' is removed; the lease question must also be answered, the default is reading 1)", "There is no allowance (the c6n exit 'index not seen, accepted' is removed)")
patch("| C-9 |", "part 2 NOT RUN; missing input: the take's database after the re-smoke (needs-lead)", "part 2 NOT RUN; missing input: the take's database after the re-smoke and the take's fresh container (needs-lead)")
patch("| C-10b |", "the take script sends no request that deletes or archives; (b) is shown |", "the take script sends no request that deletes or archives, and all of (a), (b) and (c) are shown with line numbers |")
patch("| C-10b |", "any other call, or any of (a), (b), (c) not shown: STOP (no take on Mon 23 Nov 2026, Q25; latest start that day 18:04 UTC = 23:34 IST, L-23NOV)", "any other call, or any of (a), (b), (c) not shown: STOP (no take on Mon 23 Nov 2026, Q25; the latest start that day, 18:04 UTC = 23:34 IST, is a plan fact, L-23NOV)")
c10c_old = [l for l in L if l.startswith("| C-10c |")][0]
setline("| C-10c |", "| C-10c | The owner sheet the owner reads: grep -n -i -E 'never deletes|read, create and change only|does not delete' on each sheet | me for the sheets on disk; studio lead for the final sheet | the sheet says the owner deletes leftovers by hand and does not say the HubSpot key is read-only or create-and-change-only unless the owner confirmed it (Q20 item 3) | any other statement of the key's scope | "
        "part 1 DONE on the sheets on disk at %sT%sZ = %s IST (%s, all variants, evidence-c6q/static-checks-output.txt section C-10c: v19 1 hit of 'never deletes', all others 0 for the three phrases); v28 A and B were last changed at %s UTC; v29 exists only as OWNER-SHEET-v29-SOURCE.md (written %s UTC), so the check must be repeated on the final sheet; part 2 NOT RUN; missing input: the rendered v29 and L-SHEET (needs-owner) |" % (CT[:10], CTU, CTI, RANGE, V28T, V29T))
patch("| C-10b |", "STOP (no take on Mon 23 Nov 2026", "STOP (no take on Mon 23 Nov 2026", 1)
patch("| C-4 and C-6 as a gate |", "Row 6, rehearsal list item 14; NOT RUN", "Row 6, rehearsal list item 14; NOT RUN")
# section 4 glossary
patch("| L-CARDLEN | the new question of c6o", "(c6p dropped L-SCENES: the restructure of scenes 2 and 3 is now a consequence of reading 1 of L-LEASE)", "(the question about restructuring scenes 2 and 3 was dropped in c6p; the restructure is now a consequence of answer 1 of L-LEASE when L-POST is 'no')")
patch("| L-CARD, L-CARDCUT, L-CARDTEXT, L-LEASE,", "L-CARD, L-CARDCUT, L-CARDTEXT, L-LEASE,", "L-CARD, L-CARDCUT, L-CARDTEXT, L-LEASE, L-POST,")
patch("| c6b to c6n |", "c6p (this file) supersedes c6o, which superseded c6n;", "c6q (this file) supersedes c6p, which superseded c6o;")
patch("| c6b to c6n |", "| c6b to c6n |", "| c6b to c6p |")

# ---------------------------------------------------------------- section 0
L[0] = "# REPORT-c6q: video audit fix pass, supersedes REPORT-c6p.md (2026-11-16, UTC; IST = UTC + 5:30)"
i0 = find("- THE LAST REPORT (REPORT-c6o.md) FAILED INDEPENDENT REVIEW")
L[i0] = L[i0].replace("- THE LAST REPORT (REPORT-c6o.md) FAILED INDEPENDENT REVIEW:", "- HISTORY, c6o (REPORT-c6o.md FAILED INDEPENDENT REVIEW):", 1)
L[i0] = L[i0].replace("This report (c6p) fixes every item or labels it in section 9; section 8 lists each item with its fix. THIS REPORT HAS NOT BEEN REVIEWED YET by independent reviewers; I did not run the EGM steps (the studio lead runs them). The main faults of c6o that c6p corrects:", "c6p fixed these; the main faults of c6o were:", 1)
L[i0] = L[i0].replace("THIS REPORT HAS NOT BEEN REVIEWED YET by independent reviewers; I did not run the EGM steps (the studio lead runs them). ", "", 1)
NEW0 = [
    "- THE LAST REPORT (REPORT-c6p.md) FAILED INDEPENDENT REVIEW: review-c6p-design.md (1 blocker, 7 majors, minors), review-c6p-naive.md (0 blockers, 6 majors, 10 minors) and evidence-c6p-independent/00-SUMMARY.md (its checks found no failure; it listed gaps the checks did not cover). THIS REPORT (c6q) HAS NOT BEEN REVIEWED YET by independent reviewers; I did not run the EGM steps (the studio lead runs them), and the checks of evidence-c6q/verify-c6q.py are mine: they prove the new text matches what I wrote and that listed slips are gone, not that a statement is true. The main faults of c6p that c6q corrects: (1) the default put a lease sentence on the public video text although your newest word says it stays out of the public post (ORD:230); the default is now no lease sentence, with ONE new yes or no question (L-POST: does 'public post' include the closing card and caption?) and the 45-second limit living in the owner sheet and the release note only; (2) the card arithmetic for the recommended lease sentence was missing; the box now holds a table (lease answer by card length: words, seconds, budget, total), and the lease sentence of answer 2 REPLACES the one of answer 1 (net +15 words, about +6 s, not +16 s); (3) new run-sheet texts used report words ('reading 1', 'the lease question', 'this report holds no rows', check labels, source cites); they are now written as plain sentences and the check scans for these shapes; (4) rehearsal list item 15 said nothing about what the second leak scan searches for; it now says (real key values read from the file that holds the keys, not printed, counts only); (5) the box was about 4,500 words and used words before defining them; it is now shorter and the second word list moved to section 1; (6) L-SHEET was stale; it now says 'confirm the one final sheet' and that v29 is coming; (7) the check C-10b cells disagreed (the pass cell said only (b)); (8) rows 25, 37, 47, 57, 70, 72, 90 and 91 carried source cites or check labels or a wrong 'owned by' attachment.",
    "- NOT DONE, NOT VERIFIED IN c6q (first): nothing is applied; no n8n, flow, harness or stopwatch run exists; the seconds of the card are estimates from word counts; the facts of lease answer 2 are NOT TO BE SPOKEN AS FACT before C-9 part 2; the approval of the lease wording (gate G12, LRN:33; LREP:80) is OPEN with the studio lead; the flows' behaviour was read from files and not run; the take script is not in the audited files; which owner sheet is final is not known (v29 is coming).",
    "- DEPARTURE FROM ORD:147, STATED: the studio lead's answer Q20.3 asked for the card line 'the HubSpot key used by the take is read-only; the probe key is separate'. No row writes it: the same answer says the key's scope is unknown from here and the owner has not confirmed it, and a card line that states an unverified scope is a claim this audit cannot back. If you want the line anyway, say so; a builder adds a row.",
]
L[i0:i0] = NEW0
patch("- SLIPS OF REPORT-c6n.md THAT I CORRECT HERE", "and ORD:151's 'no takeover after expiry' most plausibly meant that a second send does not take over (reading 2's behaviour), so no contradiction with mf-recovery.json line 26 is proven. c6p restates L-LEASE against Q22 (c) and ORD:230 (section 3).",
      "and I guessed that ORD:151's 'no takeover after expiry' meant that a second send does not take over; c6q WITHDRAWS that guess: LREP:80 (the studio lead's own report block of 11:10 UTC = 16:40 IST) says the real-v5 recovery flow re-claims an unfinished contact, three tries in total, and that 'no takeover after expiry' was wrong, which matches JR:26. c6p restated L-LEASE against Q22 (c) and ORD:230; c6q restates it again because ORD:230 is the newest word (section 3).")
patch("- SLIPS OF REPORT-c6n.md THAT I CORRECT HERE", "(c6o text, replaced by c6p; see the next bullet and L-LEASE in section 3)", "(c6o text, replaced by c6p and again by c6q; see L-LEASE in section 3)")
patch("- SLIPS OF REPORT-c6n.md THAT I CORRECT HERE", "so reading 1 is in force; a claim limit that understates", "so reading 1 was in force in c6p (c6q: ORD:230 is newer); a claim limit that understates")
# SPOKEN LENGTH
setline("- SPOKEN LENGTH OF THE CLOSING CARD, STILL NOT TESTED:", "- SPOKEN LENGTH OF THE CLOSING CARD, STILL NOT TESTED: with the rows as they stand (row 13 with the plain statement, row 14) the spoken card holds %d words (counted by evidence-c6q/verify-c6q.py: lines of %d, %d, %d, %d words), about %d s at 150 words a minute; with the 45-second limit sentence it held 115 words (about 46 s) in c6p; the c6n card held 144 words (about 58 s). The run sheet budget is raised to %d s and the video total is about %d s, both estimates (row 11); the table of lengths in the box gives every other case. No stopwatch run exists." % (NA[2], W_A[0], W_A[1], W_A[2], W_A[3], round(float(NA[3])), NA[4], NA[5]))
# what the check script proves
patch("- What the check script proves", "(section 7, rows C-1, C-1b and C-4a; raw output evidence-c6p/verify-c6p-output.txt,", "(section 7, rows C-1, C-1b and C-4a; raw output evidence-c6q/verify-c6q-output.txt,")
patch("- What the check script proves", "It does NOT prove that a statement is true or that a new text is right.", "c6q adds: the word counts, seconds, budgets and totals of the table of lengths are recomputed from the quoted card lines; the new texts hold no report label (check labels such as C-8, source cites such as RES:97 or PLAN:125, 'reading 1', 'reading 2', 'this report', the names of questions); the box and the run-sheet gates agree on (a), (b) and (c). Most other checks only prove that a string is present or absent. It does NOT prove that a statement is true or that a new text is right.")
# newest owner sheet bullet
setline("- THE NEWEST OWNER SHEET, RECHECKED:", "- THE NEWEST OWNER SHEET, RECHECKED AGAIN IN c6q: at %sT%sZ = %s IST (the check time of evidence-c6q/static-checks-output.txt) the owner sheets in the steps-edits folder are v19 to v28 (A and B variants and SOURCE templates) and OWNER-SHEET-v29-SOURCE.md (written %s UTC; a template, not a rendered sheet); v28 A and B were last changed at %s UTC (in c6p the check time was 16:01:45Z and v28 changed after it). The check C-10c is rerun over %s (all variants): 'never deletes' occurs only in v19 (1 hit); 'read, create and change only' and 'does not delete' occur nowhere; v20 and v21 have no mention of read-only; every other sheet has one mention of read-only or read only (a count of any mention, which can be about something other than the HubSpot key). The studio lead has ordered ONE final sheet (ORD:226 to ORD:228) and v29 is coming, so this check must be repeated on the sheet the owner reads. 'Newest' can change at any minute: write the check time whenever you say it. L-SHEET asks you to confirm the one final sheet (section 3)." % (CT[:10], CTU, CTI, V29T, V28T, RANGE))
patch("- CONTACT DELETION IS ANSWERED, NOT NEW:", "a plan line 1051 is stale;", "the studio lead calls a plan line 1051 stale text, which ORD:187 marks UNVERIFIED;")
patch("WHAT IS ANSWERED (your answers in ORDERS.md)", "line 1051 of the plan is stale text;", "the studio lead calls line 1051 of the plan stale text (UNVERIFIED, as ORD:187 itself says);")
patch("- NOT RUN: n8n, any flow", "the checks C-3, C-4, C-5, C-6, C-8, C-10b, C-10c part 2 (the sheet the owner reads, after L-SHEET)", "the checks C-3, C-4, C-5, C-6, C-8, C-10b, C-10c part 2 (the final owner sheet, after L-SHEET)")
patch("- Does the web page carry the number 60.1 to 61.9 s?", "Does the web page carry the number 60.1 to 61.9 s?", "Does the web page carry the number 60.1 to 61.9 s?")
# the 'Words more' first-rehearsal wording is patched in the box block below

# ---------------------------------------------------------------- section 8 and 9
patch("COVERAGE OF THE c6o REVIEWS (review-c6o-design.md", "COVERAGE OF THE c6o REVIEWS (review-c6o-design.md", "COVERAGE OF THE c6o REVIEWS, AS FIXED IN c6p (c6q changes the card default and the lease rows: see the block above) (review-c6o-design.md")
patch("| Naive M3 (L-SCENES unanswerable) | L-SCENES removed; its substance is a consequence of reading 1", "L-SCENES removed; its substance is a consequence of reading 1", "the question about restructuring the scenes was removed; its substance is a consequence of answer 1 of the lease question")
patch("| Design M2 (scenes 2 and 3 restructure) | question L-SCENES with the effect on the 40 s and 25 s budgets", "question L-SCENES with the effect on the 40 s and 25 s budgets", "a question about restructuring the scenes (dropped in c6p) with the effect on the 40 s and 25 s budgets")
i8 = find("COVERAGE OF THE c6o REVIEWS")
COV = [
    "COVERAGE OF THE c6p REVIEWS (review-c6p-design.md, review-c6p-naive.md, evidence-c6p-independent/00-SUMMARY.md); the line-by-line mapping with the exact lead questions is in c6q-CHANGES.md:",
    "",
    "| Review item | Fix | Where / check |",
    "|---|---|---|",
    "| Design B1 (default lease sentence on public video text against ORD:230; 'none reverses Q22 (c)' unsupported) | the default is no lease sentence on the card and caption; ONE new yes or no question L-POST asks whether 'public post' includes the card and caption; the limit then lives in the owner sheet and release note only; the claim of 'none' is restated honestly | box, section 3 (L-POST, L-LEASE), rows 11, 13, 21 |",
    "| Design M1, naive M4 (default incoherent: gap under 30 s, scene 2 at 40 s; label 'setting: lease 45 s'; what the viewer sees per answer) | with no lease sentence on the card the gap is only written down; the table of lengths and L-LEASE say what the viewer gets per answer; the label and the words 'other lease settings' are named in L-POST | box, section 3, row 6 item 13 |",
    "| Design M2, naive M1 (card arithmetic for the recommended sentence; 'add 16 s'; 'add' reads as keeping both) | table of lease answer by card length (words, seconds, budget, total); answer 2 REPLACES answer 1 (net +15 words, about +6 s); 'add' removed | box, L-CARDLEN, verify-c6q.py |",
    "| Design M3 (report-only labels in new run-sheet texts; stale 'needs n8n' sentence) | new texts rewritten as plain sentences (rows 6, 8, 13, 21, 25, 37, 47, 57, 70, 72, 90, 91); the sentence is removed from item 11; the check scans for check labels, source cites, 'reading 1/2', 'this report' and question names | verify-c6q.py |",
    "| Design M4 (newest word L-A/B, L-LEN, L-FACTS ignored; L-SHEET and section 9 stale) | L-SHEET reads 'confirm the one final sheet'; v29 is coming; C-10c rerun at %s (%s) | section 3, section 9, C-10c, evidence-c6q/static-checks-output.txt |" % (CTU + " UTC = " + CTI + " IST", RANGE),
    "| Design M5 (item 15 second leak scan plants only fake values) | item 15 says what is searched: real key values read from the file that holds the keys, not printed, counts only | row 6 |",
    "| Design M6 (C-10b PASS and FAIL cells disagree; the line in the box) | both cells say all of (a), (b) and (c); the box says once that there is no take on Mon 23 Nov unless they are shown | C-10b, box |",
    "| Design M7 (REPORT.md line 80; reading-2 facts) | LREP:80 and gate G12 (LRN:33) named as OPEN with the studio lead; the guess 'plausibly meant a second send' withdrawn; the facts of answer 2 are marked not to be spoken as fact before C-9 part 2 | section 0, L-LEASE, section 9 |",
    "| Design minors (row 90 'owned by'; 'Tue evening'; 18:04 as a plan fact; plan line 1051; ORD:147; fresh container; contact grep copied; duplicate section 9 lines; string-only checks) | row 90 ends at the database n8n; the Tuesday inference is gone; 18:04 is called a plan fact that moves with the seconds the take needs; line 1051 is 'called stale by the studio lead, UNVERIFIED'; the departure from ORD:147 is stated in section 0; the rule is looked at again in the take's fresh container; the contact grep was rerun (evidence-c6q/contact-grep-output.txt); the duplicate lines are merged; verify-c6q.py adds recomputed and cross-place checks | section 0, row 8, rows 90, C-9, section 9 |",
    "| Naive M2 (box too long) | box shortened (see its word count in evidence-c6q/verify-c6q-output.txt); the second word list moved to section 1 | box, section 1 |",
    "| Naive M3 (labels used before definition or never defined) | box defines loopback re-smoke, wave 1, rehearsal list, risks list, stand-in, the two test figures, table rule on the contact id, check C-9 part 2, send, same id and the ten files before using them | box |",
    "| Naive M5 (exact card not in the box) | all four card lines are printed in the box | box |",
    "| Naive M6 (reply line) | the three names are placeholders you choose, the form for several exceptions is given, what happens if C-9 part 2 fails is said, and L-SHEET is said to be outside 'apply all defaults' | box |",
    "| Naive minors | L-SCENES mentions removed; rows 81 and 86 named in section 1; one definition of wave 1; the first rehearsal comes after steps 5 to 9 everywhere; words with more than one meaning listed in section 1; answer 2 no longer says 'refused' or 'recovery part'; raw cites removed from the box; L-SAVE says why failed runs matter | section 1, section 3, box |",
    "| Evidence summary (L-SCENES in 3e; 'ready' and 'n8n' used before definition; C-8, RES:97, PLAN:125 in new texts; owner sheet v28 changed after the check) | 3e reworded; the box defines both words first; the labels are removed from the new texts of rows 25, 37, 47, 57, 70, 72, 91; C-10c rerun | 3e, box, rows, C-10c |",
    "",
]
L[i8:i8] = COV
# section 9
patch("- [needs-owner or needs-lead] L-SHEET:", "- [needs-owner or needs-lead] L-SHEET:", "- [needs-owner or needs-lead] L-SHEET:")
setline("- [needs-owner or needs-lead] L-SHEET:", "- [needs-owner or needs-lead] L-SHEET: confirm the ONE final owner sheet. v29 is coming (only OWNER-SHEET-v29-SOURCE.md exists at %s UTC = %s IST). Next step: when v29 is rendered, name it; C-10c is run on it. The older sheets v10 to v12 still contain the phrases (v10 2 hits, v11 1, v12 1); they are not used if the owner reads v29." % (CTU, CTI))
patch("- [needs-lead] plan-wp6-resmoke-v5.md still names film-v5", "Plan line 1051 is stale (Q23).", "The studio lead calls plan line 1051 stale (Q23); UNVERIFIED (ORD:187): he shows the final version's search at the re-pin.")
setline("- [needs-lead] L-LEASE (default 1;", "- [needs-lead] L-POST (new) and L-LEASE (default none) and L-CARDLEN (default (a)): all have defaults. The exact question: does 'public post' (ORD:230) include the closing card and the scene 3 caption? If it does not and L-LEASE 1 is chosen, scenes 2 and 3 may have to be restructured so that the repeat send comes within 30 seconds of the first send; this report holds no rows for that: a builder the studio lead names writes them.")
i = find("- [needs-lead] L-POST (new) and L-LEASE")
L.insert(i + 1, "- [needs-lead] Gate G12, the approval of the lease wording (LRN:33; LREP:80: the recovery flow re-claims an unfinished contact, three tries in total), is OPEN with the studio lead. Exact question: may the words 'processed once' stand on the card and caption beside a crash scene, given that the recovery flow may take over a crashed contact? I do not approve it.")
L.insert(i + 2, "- [needs-lead] Under the default the 45-second limit sentence (answer 1 of L-LEASE) is not on the video. Next step: the studio lead has the one final owner sheet and the release note carry it; no row of this report edits them (the sheet is being rebuilt).")
i = find("- [needs-lead] Not reviewed: this report was written")
L[i] = "- [needs-lead] Not reviewed: this report was written and checked by me alone; I started no sub-agent and no background process. The EGM review of the changed files, resolve and the drift report for c6q are run by the studio lead."
j = find("- [needs-lead] The EGM review of the changed files, resolve and the drift report for c6p")
del L[j]

# ---------------------------------------------------------------- the box: replace everything between '## Start here' and the line before '- TWO ROLES.' and move the second word list into section 1
b = find("## Start here")
e = find("## 0. Failures")
wi = find("- TWO ROLES.")
words_block = L[wi:e]
words_block = [w for w in words_block]
# first rehearsal wording: one rule
for k, w in enumerate(words_block):
    if w.startswith("- TIMES AND DATES:"):
        words_block[k] = sub(w, "First rehearsal: the studio lead, after the loopback re-smoke has passed and the two lines of rehearsal list item 14 are written (DEC:13 gives only the re-smoke target: tonight or tomorrow morning IST).",
                             "First rehearsal: the studio lead, after steps 5 to 9 of the list in the box are written (the loopback re-smoke has passed, the two lines of rehearsal list item 14 are written, the five entries of risks list item 11 are written, the owner has been asked about the sheet and the key); DEC:13 gives only the re-smoke target: tonight or tomorrow morning IST.")
    if w.startswith("- READY ="):
        words_block[k] = w
words_block.insert(0, "")
words_block.insert(1, "WORDS (more; one meaning each; used the same way in the whole report; the box at the top has the first list):")
words_block.append("- WORDS THAT THE FILES USE IN MORE THAN ONE WAY (this report uses each in one way): ROW = a row of the edit table (section 5), never a row of a database table or of an execution list unless it says so. FINAL = 'final state' is the last state of a contact record (done, or unknown with one alert); 'final version' is the version of the files at the re-pin. KILL = switching n8n off at a chosen moment in a crash test. RUN = one pass of a flow, or one test run. CHECK = a numbered check of section 7. CUT = removed from the video, the file or the card. CLAIM = only the claim table and the claim row (the database row that reserves a contact record); a sentence said in the video is a STATEMENT. LEASE and TAKE and LEAD have the one meaning given above (the files also use 'take' for a run taking a contact record: this report writes 'reserved for the run that took it first').")
sec1 = find("## 1. How to use this report")
# remove old words block from the box region
del L[wi:e]
e = find("## 0. Failures")
BOX = """## Start here: what I need from you (read this box first; everything after it is detail)
NOTHING IN THIS REPORT HAS BEEN APPLIED TO ANY FILE. The edit table (section 5) holds {N} proposed text changes, called rows. Each row has its old text, its new text and what a person watching the video sees. You answer with ONE line in ORDERS.md (below the questions). Every question has a default, and the last list says what 'apply all defaults' does and does not do.

WORDS YOU NEED FIRST (each label is used only after this list defines it; the second list is at the start of section 1):
- CONTACT = one made-up sales contact. The files and the spoken video call it a 'lead'; this report says 'contact' except inside quoted video words. SEND = one submission of a contact to the flows. SAME ID = every send of the same contact carries the same contact id (the number the flows use to tell contacts apart); the owner sends the same prepared note twice to send the same id twice.
- N8N = the tool that runs our automatic flows. A flow receives a contact, writes it into a customer list (the CRM) and sends a mail. STAND-IN = a fake service (fake mail server, fake customer list) used instead of the real one. LOOPBACK RE-SMOKE = a short test of the whole setup on this computer only, with stand-ins; the studio lead runs it before the first rehearsal.
- TAKE = the one filmed run of the video. REHEARSAL = a practice run before it. RUN SHEET = the file VIDEO-RUNSHEET.md, the scene-by-scene script: scenes 1 to 4 and a closing card (the last card, spoken by voice; the files call it scene 12). RISKS LIST and REHEARSAL LIST = two numbered lists inside the run sheet ('Risks the owner must see' and 'What must be rehearsed on the laptop before the take'); this report adds items to both.
- STUDIO LEAD = the person who decides for the studio and answers this report (the files call him 'the lead'). OWNER = the person who types in the take. Two roles; no file says whether one human fills both.
- LEASE = a setting of 45 seconds kept with every contact: when it has run out and the contact is not finished, the recovery flow (a flow that wakes every 30 seconds) may take the contact over. ALERT = the one warning mail the system sends to a person when it cannot tell what happened to a contact.
- GATE = a step on the run sheet that blocks the take until a named person has written a result on it: a stop sign, not a program. RE-PIN = the moment when the studio lead puts together the final version of the take files and reads them again. PUBLIC POST = your own phrase in ORDERS.md ('the lease sentence stays out of the public post'); question L-POST asks what it covers.
- TABLE RULE ON THE CONTACT ID = the database rule that refuses a second row for the same contact id; CHECK C-9 PART 2 = the studio lead lists that table's rules (the command \\d mf_leads) in the database the take runs on and writes the output on the run sheet; C-4 and the other C- labels are checks listed in section 7.
- K3B AND K3 = two of four crash tests in which n8n is switched off at a chosen moment to see whether the system recovers; scene 4 shows such a crash. '60.1 TO 61.9 S' = seconds from the crash to the final state of the contact, in 18 test runs on stand-in flows (not the flows of the take); the '13-MINUTE ALERT DELAY' = how long an alert took in 2 relayed runs when n8n died while sending it (also not the flows of the take).
- READY = the text of a row can be applied now; it does not mean the gate it adds has passed. Of the {N} rows, {r} are ready, {o} apply on the default of a question you have not answered, and {c} wait for a check that needs n8n running (rows {cl}). WAVE 1 = every row that does not wait for a check: {W1} rows, applied first.
- TIMES are UTC with IST (UTC + 5:30) next to them. CITES such as ORD:150 mean line 150 of ORDERS.md (section 1 lists every short file name).

QUESTIONS (label, plain question, the default that 'apply all defaults' uses). The studio lead answers all of them except L-SHEET, which only the owner can settle.

| Label | Plain question | Default |
|---|---|---|
| L-CARD | Does the closing card stay as the last card of the video? | Yes. |
| L-CARDCUT | Cut the old card lines about '80 kills' and the recovery time? (They count runs of older flows and an estimate that no data of this take backs.) | Yes, cut. |
| L-CARDTEXT | Use the new spoken card lines 2 to 4 (what an alert is and that we make no statement about how fast it arrives; what n8n may keep; what was not tested)? | Yes. |
| L-CARDLEN | Length of the closing card. (a) the four spoken lines printed below: {NA} words, about {SA} s, budget {BA} s; or (b) a shorter text of {NB} words, about {SB} s, budget {BB} s (text in section 3). The table below gives every case. All numbers are estimates until the stopwatch run. | (a). |
| L-POST | Your newest answer in ORDERS.md says the lease sentence stays out of the public post. Does 'public post' include the video's closing card and its scene 3 caption? | Yes: they count. So no sentence about the 45-second setting is put on the card or the caption. |
| L-LEASE | Which sentence about the 45-second setting goes on the card (line 1) and in the scene 3 caption? It counts only if L-POST is 'no'. none = the plain statement only; 1 = 'We make this claim only when the second send comes within 45 seconds of the first send; for a longer gap we make no claim.' (25 words, your earlier answer); 2 = '{R2}' (40 words; it REPLACES sentence 1). The facts behind 2 are not to be spoken as fact before check C-9 part 2. Section 3 says what a viewer gets with each. | none. The 45-second limit then lives in the owner sheet and the release note only. |
| L-KILL | Say anything in scene 4 about the crash tests K3B and K3? (a) no, (b) yes, labelled as a stand-in test. | (a). |
| L-APPROX | May scene 4 and the web page say 'about a minute' instead of the cut number? | No. |
| L-SAVE | Does the take make n8n save every run, so that the list of past runs filmed in scenes 1 and 2 shows runs? (The owner approved saving SUCCESSFUL runs on made-up data, for the take only, deleted and turned off afterwards; his words do not mention FAILED runs, so you confirm both; section 3 names the two n8n settings.) | Yes. |
| L-PAGE | May the web page carry the 60.1 to 61.9 s range of the stand-in crash runs and the 13-minute alert delay? | No; both stay in the file, marked not for the page. |
| L-ONEDB | May any text a viewer sees say how many databases n8n and the take use, before the loopback re-smoke has shown which database n8n uses? | No. The two rows tied to it (90, 91) edit only the decision file, not viewer text, and apply by default. |
| L-SHEET | OWNER ONLY (the studio lead asks him): confirm the ONE final owner sheet (the checklist the owner reads). v29 is coming; at {CTU} UTC = {CTI} IST only a template of v29 exists. | The sheet you name final once v29 is rendered. NOT covered by 'apply all defaults'. |
| L-DEL | Does the take delete contacts? ANSWERED by you: no, never. The open part: at the re-pin the studio lead reads the take program and writes the five entries of risks list item 11. | As answered. |
| L-CUT | Mark the run sheet rows of scenes 5 to 11 (not filmed) as 'not in the one video'? | No edit. |

THE CLOSING CARD UNDER THE DEFAULTS (exactly what rows 13 and 14 put on the run sheet): line 1 ({w1} words) '{C1}' line 2 ({w2} words) '{L2}' line 3 ({w3} words) '{L3}' line 4 ({w4} words) '{L4}' Total {NA} words, about {SA} s, budget {BA} s.

CARD LENGTH BY LEASE ANSWER (a lease sentence is added to line 1; answer 2 REPLACES the 25-word sentence of answer 1: net +15 words, about +6 s; seconds = words / 150 x 60; budget = seconds rounded up to a multiple of 5; video total = 150 s of scenes 1 to 4 + budget):

{TABLE}

HOW TO ANSWER. Append this ONE line to handover/core-hardening/ORDERS.md. Replace the time with the real time: type date -u +%FT%TZ, which prints UTC with seconds (for example 2026-11-16T16:40:00Z), and add 5 hours 30 minutes by hand for IST (22:10:00). The three names after 'builder' and 'reviewers' are labels you choose for the people or agents; nothing reads them:

`## ANSWER (studio lead, 2026-11-16T16:40:00Z = 22:10:00 IST): c6q apply all defaults to REPORT-c6q.md; builder: builder-A; reviewers: reviewer-B, reviewer-C`

The builder is the agent that applies the {W1} wave 1 rows. Reviewer-B checks facts and risk; reviewer-C reads as a person who has never seen the project. To change a default, add after the names one 'except' per label, for example `; except L-KILL: b; except L-SAVE: no`. REPLY FORM FOR EVERY QUESTION: L-CARD yes or no; L-CARDCUT yes or no; L-CARDTEXT yes or no; L-CARDLEN a or b; L-POST yes or no; L-LEASE none, 1 or 2; L-KILL a or b; L-APPROX yes or no; L-SAVE yes or no; L-PAGE yes or no; L-ONEDB yes or no; L-DEL no reply needed; L-CUT yes or no. L-SHEET cannot be put on this line; write it as a separate line: `## ANSWER (owner via studio lead, time): L-SHEET v29A` (v29A is an example).

APPLY ALL DEFAULTS, in three lists.
- IT DOES: (1) the named builder applies wave 1 (every row except the {c} that wait for a check), {W1} rows (section 3 lists them), to 10 files (the run sheet, the page statements, the start notes, the test program mf.py, the four real-v5 flow files, the one-store decision file and the flow generator build_mainframe.py; section 1 gives their paths), by text, in table order, and writes the applied row numbers to c6q-APPLIED-ROWS.md next to this report. (2) It puts on the run sheet the closing card printed above and the plain caption in scene 3 (rows 11, 12, 13, 14, 21). (3) It edits the four flow files and their generator so that n8n would save every run once they are imported; it changes no running n8n; the studio lead sets the two n8n saving values in the environment that starts n8n (section 3, L-SAVE). (4) It adds seven steps that can stop the take or a rehearsal with real accounts to the run sheet (rehearsal list items 11 to 15, risks list items 11 and 12; item 16 after the take does not stop anything). No reviewer has read these new texts yet.
- IT DOES NOT: apply the {c} rows that wait for a check (rows {cl}); run any check; import anything into n8n; spend anything; confirm any answer (the column 'Confirmed?' in section 3 stays 'No'); answer L-SHEET; start the take; write a card line about what the owner's HubSpot key may do (your earlier request for such a line is not followed: nobody has confirmed the key's scope; section 0); approve the lease wording (gate G12 stays open with you); put the 45-second limit sentence into the owner sheet or the release note (no row edits them).
- YOU STILL HAVE TO, in this order (no file gives a duration for any step; your own target for step 5 is tonight or tomorrow morning IST, DEC:13): (1) write the answer line; (2) the builder applies the rows; (3) two reviewers read the CHANGED FILES (not this report); (4) import the edited flow files into n8n and run the import check C-4 (load the files, send one made-up contact and see runs appear in the list of runs); (5) run the loopback re-smoke on the edited flows (the checks C-3, C-5, C-8 and the table part of C-9 are read during it); (6) have a builder you name write the leak scan C-6 (a test that plants fake secrets and made-up names and searches every place n8n stores data for them; it does not exist yet, the audit writes no code), then run it; (7) at the re-pin read the take script and write the five entries of risks list item 11; (8) ask the owner which sheet he reads (L-SHEET) and what his HubSpot key may do (HubSpot is the CRM of the take; ORDERS.md Q20 item 3); (9) have the one final owner sheet and the release note carry the 45-second limit sentence if L-POST stays 'yes'; rehearsal list item 14 needs the import check line and the leak scan line; (10) hold the first rehearsal (after steps 5 to 9 are written); (11) film the take. If C-9 part 2 fails, scene 3 and card line 1 are cut (row 8, item 12) whatever else is answered. No file gives a duration for steps 4 to 6, so I cannot say whether Wed 18 Nov 2026, your target (ORD:150, not fixed), can be reached; it can only be reached if steps 1 to 10 are written before the take starts that day. No take is planned on Mon 23 Nov (ORD:229); if one is ever needed: the money stop is Mon 23 Nov 2026 18:29 UTC = 23:59 IST, the latest start is 18:04 UTC = 23:34 IST (a plan fact that moves with the seconds the take program needs), the owner cancels the paid key by 18:19 UTC = 23:49 IST, and there is no take on that day unless (a), (b) and (c) of the take-script check (risks list item 11) are all shown with line numbers. The post about the video is due Wed 25 Nov 2026 15:00 UTC = 20:30 IST (ORD:150).

TO REVERSE A DEFAULT, the studio lead names a builder who puts back the old text of the affected rows (every old text is in the table).
"""
rep = dict(N=N, r=len(ready), o=len(onlyq), c=len(withc), cl=lst(withc), W1=W1, NA=NA[2], SA=round(float(NA[3])), BA=NA[4], NB=NB[2], SB=round(float(NB[3])), BB=NB[4], R2=R2, C1=C1, L2=L2, L3=L3, L4=L4,
           w1=W_A[0], w2=W_A[1], w3=W_A[2], w4=W_A[3], TABLE=TABLE, CTU=CTU, CTI=CTI)
for k, v in rep.items():
    BOX = BOX.replace("{%s}" % k, str(v))
assert "{" not in BOX.replace("{N}", ""), re.findall(r"\{\w+\}", BOX)
L[b:e] = BOX.split("\n")
sec1 = find("## 1. How to use this report")
L[sec1 + 1:sec1 + 1] = words_block[1:] + [""] if False else []
# insert the second word list right after the heading of section 1
L[sec1 + 1:sec1 + 1] = words_block[1:]
open(D + "REPORT-c6q.md", "w", encoding="utf-8").write("\n".join(L))
print("built REPORT-c6q.md: %d lines" % len(L), "rows", N, "box words", len(BOX.split()))
