"""Plants hostile mutations on copies of EDITS.orig.md; runs verify16.py (builder) and mychk16.py (own). Banned and key-shaped samples are built from parts at run time.
Caught = FAIL lines differ from the unmutated baseline."""
import os, re, subprocess, sys, ast, json
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, H)
import mychk16
SRC = open(os.path.join(H, 'EDITS.orig.md'), encoding='utf-8').read()
V = os.path.join(H, 'a', 'b', 'steps-edits', 'verify16.py')
bl = mychk16.banned_list()
def row(rid, t):
    i = t.index('\n### %s: ' % rid) + 1
    m = re.compile(r'\n### E-\d\d: |\n## Appendix K').search(t, i + 5)
    return i, (m.start() + 1 if m else len(t))
M = []
def m(name, old, new, rid=None, nth=1, allocc=False):
    M.append((name, old, new, rid, nth, allocc))
E48 = 'E-48'
m('01 swap IST alarm1 (23:19->23:29)', '17:49 UTC = 23:19 IST', '17:49 UTC = 23:29 IST')
m('02 swap IST alarm3 (23:39->23:49)', '18:09 UTC = 23:39 IST', '18:09 UTC = 23:49 IST')
m('03 seconds pair 18:14:40 -> 23:44:50', '18:14:40 UTC = 23:44:40 IST', '18:14:40 UTC = 23:44:50 IST')
m('04 E-62 drop exact-address clause', ', and only those whose e-mail address is exactly `take-<id>-a@example.com`, `take-<id>-b@example.com` or `take-<id>-c@example.com` (with the id of the take that failed). If you find more than 3 such contacts, or any other contact, you delete nothing and tell the assistant', '', 'E-62')
m('05 E-04 drop exact-address clause', " You delete a contact only if its e-mail address is exactly `take-<id>-a@example.com`, `take-<id>-b@example.com` or `take-<id>-c@example.com` (with this take's id). If you find more than 3 such contacts, or any other contact, you delete nothing and tell the assistant.", '', 'E-04')
m('06 E-42 address b -> x', '`take-<id>-b@example.com`', '`take-<id>-x@example.com`', 'E-42')
m('07 step A last time 18:19->18:29 (pair kept)', 'Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke)', 'Mon 23 Nov 2026 18:29 UTC = 23:59 IST at the latest (the last time to revoke)', E48)
m('08 step I deadline 18:19->18:29 (pair kept)', 'Revoke the key, ALWAYS, by 18:19 UTC = 23:49 IST', 'Revoke the key, ALWAYS, by 18:29 UTC = 23:59 IST', E48)
m('09 step A UTC only 18:19->18:29 (pair broken)', 'Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke)', 'Mon 23 Nov 2026 18:29 UTC = 23:49 IST at the latest (the last time to revoke)', E48)
def swap_card(t):
    i, j = row(E48, t); seg = t[i:j]
    a = re.search(r'(?m)^   2\. (.*)$', seg); b = re.search(r'(?m)^   7\. (.*)$', seg)
    seg = seg.replace('   2. ' + a.group(1), '   2. @@B', 1).replace('   7. ' + b.group(1), '   7. ' + a.group(1), 1).replace('   2. @@B', '   2. ' + b.group(1), 1)
    return t[:i] + seg + t[j:]
M.append(('10 move shred step after item 1 (swap card 2 and 7)', swap_card, None, None, 1, False))
def addsec(t):
    i, j = row(E48, t); seg = t[i:j]
    s = 'sk-' + 'ant-api03-' + 'abcdefghij' * 3
    return t[:i] + seg.replace('Key step A. The fixed rule.', 'Key step A. The fixed rule. ' + s, 1) + t[j:]
M.append(('11 add key-shaped string sk-ant-... (parts)', addsec, None, None, 1, False))
def addsec2(t):
    i, j = row(E48, t); seg = t[i:j]
    s = 'sk-' + 'proj-' + 'A1b2C3d4' * 3
    return t[:i] + seg.replace('Key step A. The fixed rule.', 'Key step A. The fixed rule. ' + s, 1) + t[j:]
M.append(('12 key-shaped hyphenated sk-proj-... (parts)', addsec2, None, None, 1, False))
def addsec3(t):
    i, j = row(E48, t); seg = t[i:j]
    s = 'AKIA' + 'QWERTYUIOPASDFGH'
    return t[:i] + seg.replace('Key step A. The fixed rule.', 'Key step A. The fixed rule. ' + s, 1) + t[j:]
M.append(('13 AKIA key (parts)', addsec3, None, None, 1, False))
def addsec4(t):
    i, j = row(E48, t); seg = t[i:j]
    s = 'ghp' + '_' + 'Abcdefghij0123456789' + 'ABCD'
    return t[:i] + seg.replace('Key step A. The fixed rule.', 'Key step A. The fixed rule. ' + s, 1) + t[j:]
M.append(('14 github-style token (parts)', addsec4, None, None, 1, False))
def addmail(t):
    i, j = row(E48, t); seg = t[i:j]
    s = 'jane.doe' + '@' + 'gmail' + '.com'
    return t[:i] + seg.replace('Key step A. The fixed rule.', 'Key step A. The fixed rule. ' + s, 1) + t[j:]
M.append(('15 personal e-mail address', addmail, None, None, 1, False))
def addbanned(t):
    i, j = row(E48, t); seg = t[i:j]
    return t[:i] + seg.replace('Key step A. The fixed rule.', 'Key step A. The fixed rule. ' + bl[0], 1) + t[j:]
M.append(('16 banned string (first of list, run time)', addbanned, None, None, 1, False))
m('17 break xref key step I -> L', 'go straight to key step I', 'go straight to key step L', E48)
m('18 break xref appendix K-D -> K-E', 'Detail with the full costs of both routes: appendix K-D', 'Detail with the full costs of both routes: appendix K-E', E48)
m('19 break E-ref E-55 -> E-99', 'E-55', 'E-99', 'E-57')
m('20 wrong weekday Mon 23 -> Tue 23', 'Mon 23 Nov 2026', 'Tue 23 Nov 2026', E48)
m('21 wrong weekday Wed 18 -> Thu 18', 'Wed 18 Nov 2026', 'Thu 18 Nov 2026', E48)
m('22 year Mon 23 Nov 2026 -> 2027', 'Mon 23 Nov 2026', 'Mon 23 Nov 2027', E48)
m('23 absolute path in owner text', '`n8n.env`, and any file', '`n8n.env` (/home/' + 'alice/n8n.env), and any file', E48)
m('24 internal code Q25 in owner text', 'Key step A. The fixed rule.', 'Key step A. The fixed rule (Q25).', E48)
m('25 ORD: code in owner text', 'Key step A. The fixed rule.', 'Key step A. The fixed rule ORD:14.', E48)
m('26 DEC: code in owner text', 'Key step A. The fixed rule.', 'Key step A. The fixed rule DEC:5.', E48)
m('27 shred check realpath -> pwd', "`realpath '<path>'`", "`pwd`", E48)
m('28 take-10 example changed', '/x/take-10/key', '/x/take-20/key', E48)
m('29 shred -u -- -> shred -u', "run `shred -u -- '<path>'`", "run `shred -u '<path>'`", E48)
m('30 link count 1 -> 2', 'the number `1` in its second column', 'the number `2` in its second column', E48)
m('31 alarm 1 consistent shift 17:49->17:59', '17:49 UTC = 23:19 IST', '17:59 UTC = 23:29 IST', E48)
m('32 alarm 1 name changed', 'named `revoke the secret key for the model`', 'named `revoke the key`', E48)
m('33 margin 3:40 -> 4:40 words', '3 minutes 40 seconds', '4 minutes 40 seconds', None, 1, True)
m('34 drop key gone word from step B list', '`key gone, no more decisions`, `shred done 1`', '`shred done 1`', E48)
m('35 D.5 time 18:19->18:09 (pair kept)', 'ONLY when you type it AFTER 18:19 UTC = 23:49 IST', 'ONLY when you type it AFTER 18:09 UTC = 23:39 IST', E48)
m('36 drop item-1 guard sentence', ' (it never starts while a copy of the key exists and the key is not revoked)', '', E48)
m('37 spending window end -> 18:19 (pair kept)', 'The spending window ends 10 minutes later, at 18:29 UTC = 23:59 IST', 'The spending window ends 10 minutes later, at 18:19 UTC = 23:49 IST', E48)
m('38 E-01 status Apply now -> Hold', '### E-01: OWNER-STEPS-realrun-v3.md, line 3, status Apply now', '### E-01: OWNER-STEPS-realrun-v3.md, line 3, status Hold (gate G1)')
m('39 index line number of E-02 changed', '| E-02 | OWNER-STEPS-realrun-v3.md | 3 |', '| E-02 | OWNER-STEPS-realrun-v3.md | 4 |')
m('40 key step F reply options drop not sure', 'Reply `same key`, `different key` or `not sure`', 'Reply `same key` or `different key`', E48)
m('41 F: only yes together with different key -> only yes', 'Only `yes` together with `different key`', 'Only `yes`', E48)
m('42 D.2 case 3 label dropped', '(3) Route B, before `cut accepted`', '(3) Route B', E48)
m('43 typed word please stop looking dropped from B', '`please stop looking`, `you may look again`, ', '`you may look again`, ', E48)
m('44 key J 7 days -> 1 day', 'more than 7 days ago', 'more than 1 day ago', E48)
m('45 H 20 minutes -> 2 minutes (first)', 'only if at least 20 minutes remain', 'only if at least 2 minutes remain', E48)
m('46 undefined gate G7', 'status Hold (gate G3), type DEFERRED', 'status Hold (gate G7), type DEFERRED')
m('47 loose heading pair 23:59 IST -> 23:49 IST (Phase 0 heading)', 'by Mon 16 Nov 18:29 UTC (23:59 IST)', 'by Mon 16 Nov 18:29 UTC (23:49 IST)', None, 1)
m('48 drop do-not-shred-while-take-runs (G)', ' Do not shred part (a) while a take is running (the model stage reads that copy); wait until the take has stopped.', '', E48)
m('49 drop never shred a recording', 'Never shred a recording, a video file, a screenshot or anything under `/mnt/c` that is not on your own list, and never a file that only the assistant named. ', '', E48)
m('50 duplicate row id E-30 -> E-31', '### E-30: AGENT-SCOPE', '### E-31: AGENT-SCOPE')
m('51 remove Why line of E-62', '\nWhy: Security F2 of round 15', '\nNote: Security F2 of round 15', 'E-62')
m('52 seconds in K 23:45:20 -> 23:45:30', '18:15:20 UTC = 23:45:20 IST', '18:15:20 UTC = 23:45:30 IST', None, 1, True)
m('53 UNVERIFIED removed from key step K', 'is not proven (UNVERIFIED)', 'is proven', E48)
m('54 drop only-your-own-typed-messages (key step B ref)', ' Only your own typed messages count (key step B).', '', E48)
m('55 E-48 OLD text altered (not in input)', 'You: delete BOTH HubSpot private apps', 'You: delete ONE HubSpot private apps', E48)
m('56 card item 4 line deleted', '   4. Do your item 5: the retire check.\n', '', E48)
m('57 delete ALL then-wrong: drop shred G.2 EVERY', '`shred done 1` means that EVERY file of (a) and (b) is shredded', '`shred done 1` means that a file of (a) and (b) is shredded', E48)
m('58 E-42 drop more-than-3 stop rule', '; if you find more than 3, or any other contact, you delete nothing and tell the assistant.', '.', 'E-42')
m('59 time 18:29 UTC=23:59 IST -> 18:29 UTC=23:58 IST once', 'Mon 23 Nov 2026 18:29 UTC = 23:59 IST (the end of the spending window', 'Mon 23 Nov 2026 18:29 UTC = 23:58 IST (the end of the spending window', E48)
m('60 revoke key tied to window: item1 revoke "at 18:19" -> "at 18:29"', 'on Mon 23 Nov 2026 it is at 18:19 UTC = 23:49 IST at the latest', 'on Mon 23 Nov 2026 it is at 18:29 UTC = 23:59 IST at the latest', E48)

def apply(t, mu):
    name, old, new, rid, nth, allocc = mu
    if callable(old):
        return old(t)
    if rid:
        i, j = row(rid, t); seg = t[i:j]
        if old not in seg: return None
        seg = seg.replace(old, new, 1); return t[:i] + seg + t[j:]
    if old not in t: return None
    return t.replace(old, new) if allocc else t.replace(old, new, 1)

def run_v(path):
    env = dict(os.environ, EDITS_PATH=path, NO_NEG='1')
    p = subprocess.run([sys.executable, '-I', V], env=env, capture_output=True, text=True, cwd=os.path.dirname(V))
    return sorted(l[:160] for l in p.stdout.split('\n') if l.startswith('FAIL'))
base_v = run_v(os.path.join(H, 'EDITS.orig.md'))
base_m = sorted(mychk16.check(SRC))
res = []
tmp = os.path.join(H, 'mut-tmp.md')
for mu in M:
    t = apply(SRC, mu)
    if t is None: res.append((mu[0], 'ANCHOR MISSING', '', '')); continue
    if t == SRC: res.append((mu[0], 'NO CHANGE', '', '')); continue
    open(tmp, 'w', encoding='utf-8').write(t)
    v = run_v(tmp); new_v = [x for x in v if x not in base_v]
    mm = sorted(mychk16.check(t)); new_m = [x for x in mm if x not in base_m]
    res.append((mu[0], bool(new_v), bool(new_m), (new_v[0][:90] if new_v else ''), (new_m[0][:90] if new_m else '')))
os.remove(tmp)
json.dump(res, open(os.path.join(H, 'mut-results.json'), 'w'), indent=1)
bv = sum(1 for r in res if r[1] is True); bm = sum(1 for r in res if r[2] is True)
print('planted', len(res), 'verify16 caught', bv, 'mychk16 caught', bm)
for r in res: print(r)
