import re, sys, os, collections
sys.dont_write_bytecode = True
HERE = '/home/user/hadavin-sdk/handover/core-hardening/'
OUT = HERE + 'steps-edits/evidence-r14-independent/'
sys.path.insert(0, OUT)
import chk14
base = open(HERE + 'steps-edits/EDITS.md', encoding='utf-8').read()
banned = chk14.load_banned()
bf, _ = chk14.check(base, banned=banned)
basekeys = collections.Counter((k, m) for k, m in bf)
os.makedirs(OUT + 'mut', exist_ok=True)
rows = chk14.parse(base)
byid = {r['id']: r for r in rows}
def sub(old, new, count=1, within=None):
    def f(t):
        if within:
            a = t.index('### ' + within + ':'); b = t.index('\n### E-', a + 5)
            seg = t[a:b]
            assert old in seg, 'anchor missing ' + old[:50]
            seg2 = seg.replace(old, new, count)
            return t[:a] + seg2 + t[b:]
        assert old in t, 'anchor missing ' + old[:50]
        return t.replace(old, new, count)
    return f
def newblock_sub(rid, old, new, count=1):
    # replace only inside the NEW block(s) of row rid
    def f(t):
        a = t.index('### ' + rid + ':'); b = t.find('\n### E-', a + 5); b = len(t) if b < 0 else b
        seg = t[a:b]
        na = seg.index('NEW'); 
        assert old in seg[na:], 'anchor missing in NEW ' + old[:50]
        seg2 = seg[:na] + seg[na:].replace(old, new, count)
        return t[:a] + seg2 + t[b:]
    return f
K = '18:19 UTC = 23:49 IST'; S = '18:29 UTC = 23:59 IST'
M = []
def add(name, desc, fn, mem=False): M.append((name, desc, fn, mem))
add('M01', 'key end 18:29/23:59 in E-48 3a', newblock_sub('E-48', 'by Mon 23 Nov 2026 ' + K + ' at the latest (the last time', 'by Mon 23 Nov 2026 ' + S + ' at the latest (the last time'))
add('M02', 'key end 18:29 in E-48 3h', newblock_sub('E-48', '3h. Revoke the key, ALWAYS, by ' + K, '3h. Revoke the key, ALWAYS, by ' + S))
add('M03', 'key end 18:29 in E-12 (first occurrence in NEW)', newblock_sub('E-12', K, S))
add('M04', 'key end 18:29 in E-55', newblock_sub('E-55', K, S))
add('M05', 'key end 18:29 in E-58', newblock_sub('E-58', K, S))
add('M06', 'key end 18:29 in E-37', newblock_sub('E-37', K, S))
add('M07', 'key end changed to 18:29 everywhere in the file', lambda t: t.replace(K, S))
add('M08', 'weekday wrong: Mon 23 Nov -> Tue 23 Nov (one place, E-48 3a)', newblock_sub('E-48', 'by Mon 23 Nov 2026 ' + K, 'by Tue 23 Nov 2026 ' + K))
add('M09', 'weekday wrong: Wed 18 Nov -> Thu 18 Nov (E-48 3c)', newblock_sub('E-48', 'normally on Wed 18 Nov 2026', 'normally on Thu 18 Nov 2026'))
add('M10', 'weekday wrong: Mon 16 Nov -> Tue 16 Nov', sub('Mon 16 Nov', 'Tue 16 Nov'))
add('M11', 'weekday wrong: Mon 23 Nov -> Sun 23 Nov (all)', lambda t: t.replace('Mon 23 Nov', 'Sun 23 Nov'))
add('M12', 'IST dropped: money stop in E-48 3a', newblock_sub('E-48', 'at ' + S + '; that is when', 'at 18:29 UTC; that is when'))
add('M13', 'IST dropped: latest start we plan in E-12', newblock_sub('E-12', 'latest start we plan (18:04 UTC = 23:34 IST)', 'latest start we plan (18:04 UTC)'))
add('M14', 'IST dropped: key end in E-37', newblock_sub('E-37', K, '18:19 UTC'))
add('M15', 'wrong IST: 23:49 -> 23:19 in E-55', newblock_sub('E-55', K, '18:19 UTC = 23:19 IST'))
add('M16', 'wrong IST: 17:49 UTC = 23:19 IST alarm -> 23:49', newblock_sub('E-48', '17:49 UTC = 23:19 IST', '17:49 UTC = 23:49 IST'))
add('M17', 'not looking removed from E-09 step a (wait clause)', newblock_sub('E-09', 'and wait for its written reply `not looking`; (2)', '; (2)'))
add('M18', 'not looking removed from E-09 step a (type nothing secret sentence)', newblock_sub('E-09', ' The wait is part of the rule every time: type nothing secret before you have the reply `not looking`. Do not go on before you have that reply.', ''))
add('M19', 'not looking removed from E-09 step f', newblock_sub('E-09', 'apply the typing rule (write `please stop looking`, wait for `not looking`, and at the end write `you may look again`)', 'apply the typing rule (write `please stop looking`, and at the end write `you may look again`)'))
add('M20', 'not looking removed from E-09 step g', newblock_sub('E-09', 'apply the typing rule (write `please stop looking` and wait for `not looking`); in the WSL terminal', 'apply the typing rule (write `please stop looking`); in the WSL terminal'))
add('M21', 'not looking removed from E-09 step h', newblock_sub('E-09', 'with its own `please stop looking` and its own wait for `not looking`', 'with its own `please stop looking`'))
add('M22', 'not looking removed from E-48 3g', newblock_sub('E-48', 'write `please stop looking`, wait for `not looking`, type or paste', 'write `please stop looking`, type or paste'))
add('M23', 'not looking removed from E-52 typing rule', newblock_sub('E-52', 'write `please stop looking` and wait for the assistant\'s reply `not looking`; type it by hand', 'write `please stop looking`; type it by hand'))
add('M24', 'shred rule line (2) deleted (no .., no space ...)', newblock_sub('E-48', ' (2) It contains no `..`, no space, no quote sign and none of the signs `*`, `?` and `[`.', ''))
add('M25', 'whole shred rule 3f check (3) realpath deleted', newblock_sub('E-48', ' (3) `realpath \'<path>\'` prints exactly the same path, which shows that no part of the path is a link (a link is a shortcut to another place).', ''))
add('M26', 'route B condition deleted from 3c', newblock_sub('E-48', 'because in route B the words `no more takes` count only after `cut accepted` (step 21); if you write them earlier the assistant says that route B is chosen and does nothing', 'because route B'))
add('M27', 'Route B label removed from E-48', newblock_sub('E-48', 'Route B: after your last take', 'after your last take'))
add('M28', 'Q-number inserted in E-09 owner text', newblock_sub('E-09', 'The assistant never tells you the password.', 'The assistant never tells you the password (Q25).'))
add('M29', 'L-id inserted in E-16 owner text', newblock_sub('E-16', 'only after you have written `no more takes`', 'only after you have written `no more takes` (L-23NOV)'))
add('M30', 'ORD: inserted in E-55 owner text', newblock_sub('E-55', '`no more takes`', '`no more takes` (ORD: take-2)'))
add('M31', "'unless the assistant tells you otherwise' re-added to 3j", newblock_sub('E-48', 'No message of the assistant changes this.', 'Revoke the key at that time unless the assistant tells you otherwise.'))
add('M32', '18:14:40 inserted without the label (E-37)', newblock_sub('E-37', K, K + ' (the take ends at 18:14:40 UTC = 23:44:40 IST)'))
add('M33', 'header Apply now 44 -> 45', sub('**Apply now 44**', '**Apply now 45**'))
add('M34', 'Hold count 12 -> 13 in header', sub('**Hold 12**', '**Hold 13**'))
add('M35', 'row E-20 header deleted (55 rows, rest merges)', lambda t: re.sub(r'(?m)^### E-20: .*\n', '', t, count=1))
add('M36', 'duplicate id: E-21 header renamed E-20', lambda t: re.sub(r'(?m)^### E-21:', '### E-20:', t, count=1))
add('M37', 'OLD text of E-09 altered by one word', newblock_sub('E-09', 'x', 'x') if False else (lambda t: t.replace('password = the one you set in WSL when you start', 'password = the one you set in WSL when you begin', 1)))
add('M38', 'stated line of E-11 wrong (87 -> 88)', sub('### E-11: OWNER-STEPS-realrun-v3.md, line 87,', '### E-11: OWNER-STEPS-realrun-v3.md, line 88,'))
add('M39', 'HOLD label removed from E-13 NEW (1)', lambda t: re.sub(r'(?m)^NEW \[HOLD G3: DO NOT APPLY\] \(1\)', 'NEW (1)', t, count=1))
add('M40', 'latest start we plan paired with 18:14 in E-12', newblock_sub('E-12', 'latest start we plan (18:04 UTC = 23:34 IST)', 'latest start we plan (18:14 UTC = 23:44 IST)'))
add('M41', 'money stop moved to 18:19 in E-12 (all 3)', newblock_sub('E-12', S, K, 99))
add('M42', 'shred before revoke: "When the key is revoked, shred" -> "Before the key is revoked, shred"', newblock_sub('E-48', 'When the key is revoked, shred every file', 'Before the key is revoked, shred every file'))
add('M43', 'keep-copies sentence deleted', newblock_sub('E-48', ' Until the key is revoked, keep its copies.', ''))
add('M44', 'E-13 second pass: index table file name changed for E-14', lambda t: re.sub(r'(?m)^(\| E-14 \| )OWNER-STEPS-realrun-v3\.md', r'\1AGENT-SCOPE-DO-AND-DONT.md', t, count=1))
add('M45', 'phrase `key kept` re-added in E-58', newblock_sub('E-58', '`key not revoked`', '`key kept`'))
add('M46', 'banned string appended (in memory only)', lambda t: t + '\n' + banned[0] + '\n', True)
add('M47', 'secret-shaped string appended (in memory only; built from parts)', lambda t: t + '\nsk' + '-' + 'A1b2C3d4' * 4 + '\n', True)
add('M48', 'owner NEW text: bare time 18:19 for the key end (no UTC/IST)', newblock_sub('E-55', K, '18:19'))
res = []
for name, desc, fn, mem in M:
    try:
        t2 = fn(base)
    except Exception as e:
        res.append((name, desc, 'ANCHOR-ERROR', str(e))); continue
    if t2 == base: res.append((name, desc, 'NO-CHANGE', '')); continue
    try:
        f2, _ = chk14.check(t2, banned=banned)
    except Exception as e:
        res.append((name, desc, 'CAUGHT(crash)', repr(e)[:100])); continue
    c2 = collections.Counter((k, m) for k, m in f2)
    new = c2 - basekeys
    if not mem: open(OUT + 'mut/%s.md' % name, 'w', encoding='utf-8').write(t2)
    kinds = sorted(set(k for k, m in new.elements()))
    res.append((name, desc, 'CAUGHT' if new else 'MISSED', ','.join(kinds) + (' | ' + [m for k, m in new.elements()][0][:90] if new else '')))
for r in res: print(*r, sep=' | ')
cnt = collections.Counter(r[2] for r in res); print('TOTAL', len(res), dict(cnt))
print('baseline fails (present on unmutated file):', [(k, m[:60]) for k, m in bf])
