"""c6p part 1: parse REPORT-c6o.md (read only), change the table rows, keep every other line. Imported by build_c6p.py.
Every text patch must match exactly once (assert), so a silent miss is impossible."""
import re
D = "/home/user/hadavin-sdk/handover/core-hardening/c6-skip-audit/"
src = open(D + "REPORT-c6o.md", encoding="utf-8").read()
LINES = src.split("\n")
PAT = re.compile(r"^\| (\d+) \| (NOT APPLIED[^|]*?) \| (handover/[^|]+?) \| (\d+) \| ([^|]*) \| `(.*?)` \| `(.*?)` \| (.*) \| ([^|]*) \|$")
rows, order, row_line = {}, [], {}
for i, l in enumerate(LINES):
    m = PAT.match(l)
    if m:
        k = int(m.group(1))
        rows[k] = dict(i=k, st=m.group(2), f=m.group(3), ln=m.group(4), view=m.group(5), old=m.group(6), new=m.group(7), why=m.group(8), was=m.group(9))
        order.append(k)
        row_line[k] = i
assert sorted(rows) == list(range(1, 95))
FIRST, LAST = min(row_line.values()), max(row_line.values())
assert LAST - FIRST == 93
TOK = re.compile(r"L-[A-Z]+|C-\d+[a-d]?")


def sub(t, old, new, count=1):
    n = t.count(old)
    assert n == count, "patch matched %d times (want %d): %r" % (n, count, old[:100])
    return t.replace(old, new)


def rn(k, old, new, c=1): rows[k]["new"] = sub(rows[k]["new"], old, new, c)
def rw(k, old, new, c=1): rows[k]["why"] = sub(rows[k]["why"], old, new, c)
def rv(k, old, new, c=1): rows[k]["view"] = sub(rows[k]["view"], old, new, c)


def set_dep(k, toks):
    toks = sorted(set(toks), key=lambda x: (x[0] != "C", x))
    cs = [t for t in toks if t.startswith("C-")]
    ls = [t for t in toks if t.startswith("L-")]
    if not toks:
        rows[k]["st"] = "NOT APPLIED; ready"
    else:
        parts = (["after check " + ", ".join(cs)] if cs else []) + (["on the default of " + ", ".join(ls)] if ls else [])
        rows[k]["st"] = "NOT APPLIED; " + "; ".join(parts)


def add_dep(k, *t): set_dep(k, TOK.findall(rows[k]["st"]) + list(t))
def del_dep(k, *t): set_dep(k, [x for x in TOK.findall(rows[k]["st"]) if x not in t])


def words(s): return len(s.split())


# ---------------------------------------------------------------- the card (one definite text under the defaults)
A1 = "A lead sent twice with the same id is processed once. We make this claim only when the second send comes within 45 seconds of the first send; for a longer gap we make no claim."
A2 = "When the system cannot tell whether a contact was fully handled, it sends one alert, a warning mail that asks a person to look. We make no statement about how quickly an alert mail arrives."
A3 = "The made-up name and e-mail address sent to n8n may stay in n8n's own database; we did not measure for how long."
A4 = "Not tested: other mailboxes, other customer-record systems, alerts sent as chat messages, other lease settings. One machine, made-up people, our own runs."
B1 = "A lead sent twice with the same id is processed once, claimed only when the second send comes within 45 seconds of the first."
B2 = "When the system cannot tell if a contact was handled, it sends one alert, a warning mail asking a person to look. We say nothing about how fast it arrives."
B3 = "The made-up name and e-mail address may stay in n8n's database; we did not measure for how long."
B4 = "Not tested: other mailboxes, other systems, chat alerts, other lease settings. One machine, made-up people."
R2 = "The 45 seconds is a setting called the lease. It decides only when the recovery part of the system may take over a contact that is not finished. A second send of the same contact is refused at any time."
WA = [words(x) for x in (A1, A2, A3, A4)]
WB = [words(x) for x in (B1, B2, B3, B4)]
NA, NB = sum(WA), sum(WB)
SA, SB = round(NA / 150 * 60), round(NB / 150 * 60)
up5 = lambda s: ((s + 4) // 5) * 5
BA, BB = up5(SA), up5(SB)
TOTA, TOTB = 150 + BA, 150 + BB
NR2 = words(R2)
R1S = "We make this claim only when the second send comes within 45 seconds of the first send; for a longer gap we make no claim."
NR1S = words(R1S)
CARD = dict(NA=NA, SA=SA, BA=BA, TOTA=TOTA, NB=NB, SB=SB, BB=BB, TOTB=TOTB, NR2=NR2, WA=WA, WB=WB, NR1S=NR1S)

# row 11
rows[11]["new"] = ("- The one video: scenes 1 to 4 and the closing card (scene 12): scene 1 25 s + scene 2 40 s + scene 3 25 s + scene 4 60 s = 150 s, plus the closing card %d s (an ESTIMATE from the word count: the four spoken card lines hold %d words, which is about %d s at 150 words a minute; the card time is EST NOT MEASURED until the stopwatch run of rehearsal list item 10) = about %d s in all. "
                   "The next two lines count scenes 5 to 11, which are not in the one video (the studio lead's decision of 2026-11-16).<br>- Core scenes 1 to 10 and 12:") % (BA, NA, SA, TOTA)
rows[11]["view"] = "Nothing on screen; the run sheet gives 150 s for scenes 1 to 4 and an estimated %d s for the closing card (about %d s in all, not measured)." % (BA, TOTA)
rows[11]["why"] = ("Row 11 of c6o wrote the card as 'about 58 s' (the c6n six-line card of 144 words); the closing card of this report holds %d words (counted by evidence-c6p/verify-c6p.py), about %d s at 150 words a minute, so the budget of 30 s is raised to %d s and the total is about %d s, labelled as an estimate (c6o design review M2, naive review B1). "
                   "The four scenes add to 150 s (25 + 40 + 25 + 60, from the Time column of the run sheet scenes 1 to 4). The card needs a stopwatch run to be measured; until then the number is an estimate. Option (b) of L-CARDLEN (the shorter text of %d words, about %d s, card budget %d s, total about %d s) is in section 3. Sources: RS:41, DEC:2 (decision 1)") % (NA, SA, BA, TOTA, NB, SB, BB, TOTB)
# row 12 unchanged text; row 13: reading 1 sentence (default of L-LEASE)
rows[13]["new"] = 'Line 1, statement, spoken: "%s"' % A1
rows[13]["view"] = "Closing card line 1 says the repeat-send statement and the limit of the claim (a second send within 45 seconds of the first)."
set_dep(13, ["L-CARD", "L-CARDLEN", "L-LEASE"])
rows[13]["why"] = ("Split of the old row 13 (c6k design review M1). Reading 1 of L-LEASE is the studio lead's own answer Q22 (c) in ORDERS.md (ORD:186: 'item 1 wording plus one honest sentence that a gap longer than the lease is not claimed'), so it is the default; ORD:230 (L-Q22c) keeps the lease sentence out of the public POST, not off the video. "
                   "Reading 1 is true but weaker than the flows: the contact table refuses a second row with the same contact id at any gap while the row exists (mf_leads.sql line 5, MF:45; ON CONFLICT DO NOTHING at mf-form.json line 97; repeat answered from the stored row, mf-form.json lines 270 and 298). The 45 s lease decides something else: when the recovery flow may take over a contact that is not finished (mf-recovery.json line 26). "
                   "So reading 1 understates what the flows do; it does not claim anything the flows cannot do. It costs the viewer an unneeded idea (a 45-second window) and, to be filmed, needs the repeat send within 45 s of the first (rehearsal list item 13 asks for under 30 s). Reading 2 and 'none' are in section 3 (L-LEASE) with their sentences. "
                   "The word counts of the whole card are in L-CARDLEN. The unique rule on the contact id is NOT yet seen in the take's own database (risks list item 12 stops the take without it). Sources: JF:97, MF:45, ORD:151, ORD:186, ORD:230")
# row 14: lines 2 to 4 (option a)
rows[14]["new"] = ('Line 2, alerts, spoken: "%s" Line 3, retention, spoken: "%s" Line 4, not tested, spoken: "%s"') % (A2, A3, A4)
rows[14]["view"] = "Closing card lines 2 to 4: what an alert is and no statement about how fast it arrives; what n8n may keep; what was not tested."
rw(14, "Row 14 is also tied to L-CARDLEN: the length of the four spoken lines (about 58 s with the old line 1 and the lease sentence) is the question L-CARDLEN, which offers a shorter text.",
   "Row 14 is also tied to L-CARDLEN: with line 1 of row 13 the four spoken lines hold %d words (about %d s); L-CARDLEN option (b) gives a shorter text of %d words. Line 3 is a shortened form of the retention sentence of c6o (it dropped 'or whether n8n's automatic removal of old runs ever removes them') so that the card fits %d s; the full form is in L-CARDLEN option (b)-long, not needed. Line 2 keeps both the explanation 'a warning mail' and 'no statement about how quickly an alert mail arrives' that L-CARDTEXT promises (c6o naive review B1). Line 3 repeats the content of statement 18, which is UNBACKED (row 44); the card says only 'may stay' and 'we did not measure', which is true whatever statement 18 turns out to be (c6o naive review M7)." % (NA, SA, NB, BA))
# fix the dangling sentence just written (no 'option (b)-long')
rw(14, " the full form is in L-CARDLEN option (b)-long, not needed.", " the c6o form is not lost: it is row 14 of REPORT-c6o.md.")
# row 21: caption
rows[21]["new"] = 'Caption: "a lead sent twice with the same id is processed once (claimed only when the second send comes within 45 seconds of the first)". The screen is the evidence; the rehearsal must show the repeat reply and the clock times of both sends (write them on this run sheet).'
rows[21]["view"] = "Scene 3 caption: the plain statement plus the limit (a second send within 45 seconds of the first)."
set_dep(21, ["L-LEASE"])
rows[21]["why"] = ("Same reading as the card line (row 13): reading 1 of L-LEASE, the studio lead's answer Q22 (c), is the default. If L-LEASE is answered 2 or none, this row is re-issued with the reading 2 sentence or with the plain caption only (texts in section 3). "
                   "The caption is only true when the repeat comes within 45 s of the first send; rehearsal list item 13 writes the gap down and asks for under 30 s. Sources: JF:97, MF:45, ORD:151, ORD:186")
# rows 17, 81: true whatever L-LEASE says
rn(17, "The 45-second lease setting is also said on the closing card and in the scene 3 caption (it is a setting, not a test result).", "The 45-second lease setting may also be shown or said (it is a setting, not a test result); where it is said depends on the answer to the lease question.")
rows[81]["new"] = "The closing card names no lane3 figure (neither 45 s nor 120 s); only the take's own 45 s lease setting may be named."
# row 83 reason: the c6o text said row 23 replaces the sentence with 'pruned'
rw(83, "(row 23 already replaces the sentence with 'pruned')", "(row 23 removes the word 'pruned' from it)")
# row 6: view and items 13, 15, 16, header numbers
rows[6]["view"] = "Nothing on screen; the take is blocked until the workflow list, the owner-sheet check, the repeat-send check, the saved-runs checks and the second leak scan are written; after the take the saved runs are deleted and the leak scan is run again."
rn(6, "The gap is written down, not limited: the unique rule on the contact id refuses a second row at any gap (row 13 explains; the lease only decides when the recovery flow may take over a contact that is not finished). If the gap is long, the studio lead may restructure scenes 2 and 3 so that the repeat send comes straight after the first reply.",
   "If the answer to the lease question is reading 1 (the default; the card and the caption say the claim holds only within 45 seconds of the first send), the gap must be under 30 seconds, because scene 2 is planned at 40 seconds and the first send is made inside it; if the gap is 30 seconds or more, the lease sentence is not filmed: the studio lead either has the scenes restructured so that the repeat send comes straight after the first reply (the studio lead names a builder; this report holds no rows for that), or answers the lease question with reading 2 or none. Under reading 2 or none the gap is only written down.")
rn(6, "the six stores of the scan, hit counts only, never the values", "the stores that the leak scan section of the start notes lists, hit counts only, never the values")
rn(6, "16. AFTER THE TAKE. The same day, the studio lead deletes every saved run from n8n (every execution, not only the ones on the list) and turns saving off again (both n8n settings and the flow-file settings back to none), then writes the time in UTC and IST under this item. Until it is written, n8n still holds the made-up names and e-mail addresses of the take.",
   "16. AFTER THE TAKE. The same day, the studio lead deletes every saved run from n8n (every execution, not only the ones on the list) and turns saving off again (both n8n settings and the flow-file settings back to none). It is NOT verified that deleting a run erases it from n8n's database (the start notes say a deleted run may only be marked deleted until n8n's automatic removal of old runs). So he then runs the leak scan's check of n8n's own database a third time, writes the hit counts and the time in UTC and IST under this item, and, if the made-up names or e-mail addresses are still found, tells the owner and decides in writing how n8n's database is removed. Until the counts are written, n8n may still hold the made-up names and e-mail addresses of the take.")
rw(6, "Item 13 measures from the first SEND, not from the first reply, and asks for under 30 seconds, because the lease starts when the claim row is written (c6m design review M1).",
   "Item 13 measures from the first SEND, not from the first reply, and (under reading 1 of the lease question) asks for under 30 seconds, because the lease starts when the claim row is written (c6m design review M1).")
rw(6, "item 13 no longer limits the gap to 30 s (the limit followed from the 45 s reading that B1 of the c6n naive review shows is not supported; see row 13) and says how the owner sends the same id twice;",
   "item 13 of c6o only wrote the gap down; c6p restores the 30 s limit for reading 1, which is the studio lead's own answer Q22 (c) and therefore the default, and keeps 'only write it down' for reading 2 and none (c6o design review M1, M7); item 13 also says how the owner sends the same id twice;")
rw(6, "new item 15 (second leak scan, c6n design review M8) and item 16 (after the take: delete saved runs, turn saving off, M8).",
   "new item 15 (second leak scan, c6n design review M8) and item 16 (after the take: delete saved runs, turn saving off, M8). c6p: item 16 no longer says that deletion erases the data; it adds a third leak count (c6o design review M6). The rehearsal list has seven steps that can stop the take or a rehearsal with real accounts: items 11, 12, 13, 14, 15 of this list and items 11 and 12 of the risks list; item 16 comes after the take.")
# row 8
rows[8]["view"] = "Nothing on screen; the take is blocked until the studio lead has written the result of the contact-deletion check, and scene 3 is filmed only if the rule that refuses a second row was seen in the take's database and the lease question is answered."
rn(8, "if (b) cannot be shown, STOP: no take on or after Mon 23 Nov 2026 (the target take is Wed 18 Nov 2026);",
   "if (a), (b) or (c) cannot be shown with line numbers, STOP: no take on Mon 23 Nov 2026 (the target take is Wed 18 Nov 2026; the latest start on Mon 23 Nov is 18:04 UTC = 23:34 IST and the owner cancels the key by 18:19 UTC = 23:49 IST);")
rn(8, "(2) the studio lead has decided which sentence about the 45-second setting, if any, is spoken with it. There is no exit:",
   "(2) the lease question is answered (the default is reading 1, the studio lead's answer Q22 (c): the card and caption then say the claim holds only for a second send within 45 seconds of the first, and rehearsal list item 13 shows a gap under 30 seconds); under reading 2 one rehearsal repeat sent more than 45 seconds after the first is also written here and the reply shows the repeat flag true. There is no exit:")
rw(8, "The meaning of (a), (b), (c) is from QUESTIONS.md line 73; what '(b) means stop' is applied here as: no take on or after Mon 23 Nov without it (the lead's own text, Q25, says exactly that).",
   "The meaning of (a), (b), (c) is from QUESTIONS.md line 73 in handover/core-hardening (opened for c6p; that file is not among the inputs of the audit). Q25 (ORD:189) says no take on 23 Nov unless Q27 is shown at the final head; Q27 covers (a), (b) and (c), so all three must be shown (c6o design review M8). The latest start time is L-23NOV (ORD:229).")
# rows 25, 37, 38: stored (RES:97)
rn(25, "lane3 K6 = this sheet's K3 (n8n killed after the mail was delivered)", "lane3 K6 = this sheet's K3 (n8n killed after the mail was stored by the test mailbox; the word of RES:97)")
rn(37, "K3: killed after the mail was delivered (the test mailbox received 1 mail in 3 of 3 runs)", "K3: killed after the mail was stored by the test mailbox (the word of RES:97; the test mailbox received 1 mail in 3 of 3 runs)")
rn(38, "(killed after the mail was delivered: unknown + 1 alert)", "(killed after the mail was stored by the test mailbox: unknown + 1 alert)")
# row 76: design intent
rn(76, "which is the intended safe end state of those two cases (the system cannot tell whether the CRM entry and the mail happened, so it sends one alert and a person decides)",
   "which is the design intent for those two cases as the test program and the studio lead's decisions describe it (relayed; the program is not among the audited files: the system cannot tell whether the CRM entry and the mail happened, so it sends one alert and a person decides)")
# row 39: final state wording
rn(39, "each of the 18 kept crash runs reached a final state 60.1 to 61.9 s after the crash.", "each of the 18 kept crash runs reached its final state 60.1 to 61.9 s after the crash (10 done; 8 ended unknown with one alert to the owner, see the next statement).")
# clock labels for the 144.3 s figure (RES:85 columns: recovery s, then kill to final not recorded)
rn(47, "K1 recovered in 144.3 s at a lease of 120 s", "K1 recovered 144.3 s after n8n came back up (kill to final was not recorded) at a lease of 120 s")
rn(77, "lane3 v4 K1 144.3 s at lease 120 s, n=2", "lane3 v4 K1 144.3 s (counted from n8n coming back up; kill to final not recorded) at lease 120 s, n=2")
rn(78, "lane3 v4 K1 144.3 s at lease 120 s (n=2", "lane3 v4 K1 144.3 s from n8n coming back up (kill to final not recorded) at lease 120 s (n=2")
rn(79, "measured 144.3 s in both of 2 runs", "measured 144.3 s from n8n coming back up (kill to final not recorded) in both of 2 runs")
rn(80, "n=2 for the 144.3 s figure", "n=2 for the 144.3 s figure (counted from n8n coming back up)")
# row 90, 91
rows[90]["new"] = "The target is one Postgres server that holds the claim database and a SEPARATE database `n8n` for n8n's own state"
rw(90, "the files never say 'two stores' or 'three stores': the three places are the n8n database, the claim database and the journal file.",
   "the files never say 'two stores' or 'three stores'. The new text ends right before ' owned by the role', so the sentence that follows still describes the n8n database; the journal file and the other files that are not in Postgres (spend ledger, lock files, the single-use tag marker, n8n.pid) keep their own sentences in the same paragraph (c6o design review M5).")
rows[91]["new"] = "# DECISION (TARGET until the loopback re-smoke, check C-8): one Postgres server for the take (n8n's own database and the claim database; the stage journal and some bookkeeping files stay files)"
# row 23: time wording
rn(23, "with the same take start time.", "with the take start time written for that rehearsal or take.")
# row 92: film-v5
rw(92, "otherwise he stops and tells the studio lead (c6n design review M8).",
   "otherwise he stops and tells the studio lead (c6n design review M8). The generator also writes the four film-v5 files, which are not in the one video; he compares only the four real-v5 files and throws the film-v5 output away, so check C-2 and row 62 stay true (c6o naive review, minor).")
# L-SAVE ties unchanged. update dependent statuses for rows with L-KILL etc unchanged.
