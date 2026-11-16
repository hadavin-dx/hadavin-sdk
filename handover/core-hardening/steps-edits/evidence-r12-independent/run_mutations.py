#!/usr/bin/env python3
"""Plants mutations on scratch copies of EDITS.md (and of inputs) and records whether check_r12 catches each.
Usage: run_mutations.py EDITS_PATH INPUTS_DIR SCRATCH_DIR"""
import sys, os, re, shutil, importlib.util, io, contextlib
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('check_r12', os.path.join(here, 'check_r12.py')); chk = importlib.util.module_from_spec(spec); spec.loader.exec_module(chk)
E, IN, SC = sys.argv[1:4]
base = open(E, encoding='utf-8').read()
os.makedirs(SC, exist_ok=True)
def sub1(old, new, nth=0):
    def f(t):
        idx = [m.start() for m in re.finditer(re.escape(old), t)]
        assert len(idx) > nth, f'mutation anchor not found: {old[:50]}'
        i = idx[nth]; return t[:i] + new + t[i + len(old):]
    return f
def suball(old, new):
    def f(t):
        assert old in t, f'anchor missing {old[:50]}'
        return t.replace(old, new)
    return f
def row_text(t, rid):
    a = t.index(f'### {rid}:'); b = t.index('\n### ', a + 5); return a, b
def in_row(rid, old, new):
    def f(t):
        a, b = row_text(t, rid); seg = t[a:b]
        assert old in seg, f'{rid} anchor missing {old[:50]}'
        return t[:a] + seg.replace(old, new, 1) + t[b:]
    return f
def drop_row(rid):
    def f(t):
        a, b = row_text(t, rid); return t[:a] + t[b + 1:]
    return f
FAKE_SK = 's' + 'k-' + 'A1b2C3d4' * 4
muts = [
 ('M01 change a UTC revoke time 18:19->18:18 (one place, E-48)', in_row('E-48', '18:19 UTC = 23:49 IST', '18:18 UTC = 23:49 IST')),
 ('M02 change an IST revoke time 23:49->23:50 (E-48)', in_row('E-48', '18:19 UTC = 23:49 IST', '18:19 UTC = 23:50 IST')),
 ('M03 revoke deadline set to 18:29 pair in E-48 ("in every case by")', in_row('E-48', 'by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest', 'by Mon 23 Nov 2026 18:29 UTC = 23:59 IST at the latest')),
 ('M04 swap revoke/latest-start pairs in E-12 sentence', in_row('E-12', 'no start later than 18:04 UTC = 23:34 IST, so that the take is over before 18:19 UTC = 23:49 IST', 'no start later than 18:19 UTC = 23:49 IST, so that the take is over before 18:04 UTC = 23:34 IST')),
 ('M05 revoke order swap in E-48: "by 18:19 ... rest by 18:29" -> reversed', in_row('E-48', 'Revoke the secret key for the model right after you write `no more takes` (item 3 below), and in every case by Mon 23 Nov 2026 18:19 UTC = 23:49 IST', 'Revoke the secret key for the model right after you write `no more takes` (item 3 below), and in every case by Mon 23 Nov 2026 18:29 UTC = 23:59 IST') if False else sub1('Do the rest of the retirement by 18:29 UTC = 23:59 IST', 'Do the rest of the retirement by 18:19 UTC = 23:49 IST')),
 ('M06 latest start 18:04 -> 18:05 pair broken (IST kept 23:34)', sub1('18:04 UTC = 23:34 IST', '18:05 UTC = 23:34 IST')),
 ('M07 latest start IST wrong 23:34->23:44', sub1('18:04 UTC = 23:34 IST', '18:04 UTC = 23:44 IST', 1)),
 ('M08 window end IST wrong 23:59->23:29', sub1('18:29 UTC = 23:59 IST', '18:29 UTC = 23:29 IST', 2)),
 ('M09 remove IST from a UTC time in NEW text (E-12)', in_row('E-12', '18:04 UTC = 23:34 IST', '18:04 UTC')),
 ('M10 bare time without UTC/IST in NEW text (E-12)', in_row('E-12', '18:04 UTC = 23:34 IST', '18:04')),
 ('M11 drop one hold marker (E-04 NEW label)', in_row('E-04', 'NEW [HOLD G1: DO NOT APPLY] (exact):', 'NEW (exact):')),
 ('M12 drop hold marker in G5 row E-50', in_row('E-50', 'NEW [HOLD G5: DO NOT APPLY] (exact):', 'NEW (exact):')),
 ('M13 hold label text DO NOT APPLY -> DO APPLY (E-41)', in_row('E-41', 'DO NOT APPLY', 'DO APPLY')),
 ('M14 hold gate label differs from header (E-42 label G1->G2)', in_row('E-42', 'NEW [HOLD G1: DO NOT APPLY]', 'NEW [HOLD G2: DO NOT APPLY]')),
 ('M15 remove second hold block of E-13 (count 12)', lambda t: (lambda a, b: t[:a] + re.sub(r'NEW \[HOLD G3: DO NOT APPLY\] \(2\).*?\n~~~~\n.*?\n~~~~\n', '', t[a:b], count=1, flags=re.S) + t[b:])(*row_text(t, 'E-13'))),
 ('M16 apply-now row flipped to Hold in header (E-14)', in_row('E-14', 'status Apply now', 'status Hold (gate G1)')),
 ('M17 hold row flipped to Apply now in header (E-45)', in_row('E-45', 'status Hold (gate G1)', 'status Apply now')),
 ('M18 counts text Apply now 44->45', sub1('**Apply now 44**', '**Apply now 45**')),
 ('M19 counts text Hold 12->13', sub1('**Hold 12**', '**Hold 13**')),
 ('M20 total rows text 56->57', sub1('56 rows in total', '57 rows in total')),
 ('M21 break an OLD text (one character, E-20)', lambda t: (lambda a, b: t[:a] + re.sub(r'(OLD \(exact\):\n~~~~\n)(.)', lambda m: m.group(1) + ('Z' if m.group(2) != 'Z' else 'Y'), t[a:b], count=1) + t[b:])(*row_text(t, 'E-20'))),
 ('M22 stated line number changed (E-21 line 164->165)', in_row('E-21', ', line 164,', ', line 165,')),
 ('M23 duplicate row id (E-30 header renamed E-29)', sub1('### E-30:', '### E-29:')),
 ('M24 delete a whole row (E-33)', drop_row('E-33')),
 ('M25 weekday wrong: Wed 18 Nov -> Thu 18 Nov (first)', sub1('Wed 18 Nov', 'Thu 18 Nov')),
 ('M26 weekday wrong: Mon 23 Nov 2026 -> Tue 23 Nov 2026 (in E-48)', in_row('E-48', 'Mon 23 Nov 2026', 'Tue 23 Nov 2026')),
 ('M27 date wrong: Mon 23 Nov 2026 -> Mon 24 Nov 2026 (in E-55)', sub1('Mon 23 Nov 2026', 'Mon 24 Nov 2026', 3)),
 ('M28 year wrong: Mon 16 Nov 2026 -> Mon 16 Nov 2027 (E-37 NEW)', sub1('Mon 16 Nov 2026', 'Mon 16 Nov 2027')),
 ('M29 delete reply definition: "last take that you accept" bullet (E-52)', lambda t: (lambda a, b: t[:a] + re.sub(r'- \*\*The last take that you accept\*\*[^\n]*\n', '', t[a:b], count=1) + t[b:])(*row_text(t, 'E-52'))),
 ('M30 delete `cut accepted` definition sentence (E-52)', in_row('E-52', 'there you reply `cut accepted` or list the bad seconds', 'there you reply with the result')),
 ('M31 delete "How you reply" bullet name (E-52)', in_row('E-52', '- **How you reply**', '- **Replies**')),
 ('M32 delete "same key / different key / not sure" definition (E-48)', in_row('E-48', 'Reply `same key`, `different key` or `not sure`', 'Reply with the key situation')),
 ('M33 delete `key kept` (E-58)', in_row('E-55', '`key kept`', 'a short note') if False else sub1('send the words `key kept` and the reason', 'send a short note and the reason')),
 ('M34 delete `end` definition (E-37)', in_row('E-37', '`end`, when the assistant tells you', 'the closing word, when the assistant tells you')),
 ('M35 delete the exact reply `Yes, remove the container only` (E-16)', in_row('E-16', 'Reply with exactly `Yes, remove the container only` or `No`', 'Reply with your decision')),
 ('M36 delete `Yes, send the one enquiry on` (E-49)', in_row('E-49', 'Yes, send the one enquiry on', 'Send the enquiry on')),
 ('M37 internal code E-12 in owner NEW (E-14)', lambda t: (lambda a, b: t[:a] + re.sub(r'(NEW \(exact\):\n~~~~\n)', r'\1(see E-12) ', t[a:b], count=1) + t[b:])(*row_text(t, 'E-14'))),
 ('M38 internal code gate G3 in owner NEW (E-15)', lambda t: (lambda a, b: t[:a] + re.sub(r'(NEW \(exact\):\n~~~~\n)', r'\1(gate G3) ', t[a:b], count=1) + t[b:])(*row_text(t, 'E-15'))),
 ('M39 internal code R12 in owner NEW (E-17)', lambda t: (lambda a, b: t[:a] + re.sub(r'(NEW \(exact\):\n~~~~\n)', r'\1(rule R12) ', t[a:b], count=1) + t[b:])(*row_text(t, 'E-17'))),
 ('M40 e-mail address in NEW (E-19)', lambda t: (lambda a, b: t[:a] + re.sub(r'(NEW \(exact\):\n~~~~\n)', r'\1write to ann.lee@gmail.com ', t[a:b], count=1) + t[b:])(*row_text(t, 'E-19'))),
 ('M41 secret-shaped string in NEW (E-22)', lambda t: (lambda a, b: t[:a] + re.sub(r'(NEW \(exact\):\n~~~~\n)', r'\1' + FAKE_SK + ' ', t[a:b], count=1) + t[b:])(*row_text(t, 'E-22'))),
 ('M42 delete a fence line (odd fence count)', lambda t: t.replace('\n~~~~\n', '\n', 1)),
 ('M43 OLD of E-02 replaced by a string that occurs many times in input', lambda t: (lambda a, b: t[:a] + re.sub(r'(OLD \(exact\):\n~~~~\n).*?(\n~~~~)', r'\1the\2', t[a:b], count=1, flags=re.S) + t[b:])(*row_text(t, 'E-02'))),
 ('M44 NEW block removed (E-25 row has OLD only)', lambda t: (lambda a, b: t[:a] + re.sub(r'NEW \(exact\):\n~~~~\n.*?\n~~~~\n', '', t[a:b], count=1, flags=re.S) + t[b:])(*row_text(t, 'E-25'))),
 ('M45 banned-list entry planted (read at run time)', None),
]
def banned_entry():
    import ast
    bt = open(os.path.join(here, '../../../../tests/test_no_reference_material.py'), encoding='utf-8').read()
    return ast.literal_eval('(' + re.search(r'BANNED = \((.*?)\n\)', bt, re.S).group(1) + ')')[0]
caught = 0; out = []
# input mutations
for name, f in muts:
    t = base
    try:
        if f is None:
            b = banned_entry(); t = base + '\n' + b + '\n'
        else:
            t = f(base)
        assert t != base, 'mutation did not change text'
    except Exception as e:
        out.append((name, 'SETUP-ERROR', str(e))); continue
    p = os.path.join(SC, 'EDITS.mut.md'); open(p, 'w', encoding='utf-8').write(t)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): fails = chk.run(p, IN, True)
    ok = bool(fails); caught += ok
    out.append((name, 'CAUGHT' if ok else 'MISSED', (fails[0][:140] if fails else '')))
def in_mut(name, fn, mutator):
    d = os.path.join(SC, 'in'); shutil.rmtree(d, ignore_errors=True); shutil.copytree(IN, d)
    p = os.path.join(d, fn); t = open(p, encoding='utf-8').read(); t2 = mutator(t); assert t2 != t
    open(p, 'w', encoding='utf-8').write(t2)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): fails = chk.run(E, d, True)
    return (name, 'CAUGHT' if fails else 'MISSED', fails[0][:140] if fails else '')
_, rows_, _ = chk.parse(base)
def oldtext(rid): return [b['text'] for r in rows_ if r['id'] == rid for b in r['blocks'] if b['kind'] == 'OLD'][0]
o6 = oldtext('E-06'); o28 = oldtext('E-28')
for res in (in_mut('I01 input OWNER-STEPS: change first word of the OLD text of E-06', 'OWNER-STEPS-realrun-v3.md', lambda t: t.replace(o6, 'Z' + o6[1:], 1)),
            in_mut('I02 input AGENT-SCOPE: change middle char of the OLD text of E-28', 'AGENT-SCOPE-DO-AND-DONT.md', lambda t: t.replace(o28, o28[:len(o28)//2] + '#' + o28[len(o28)//2+1:], 1)),
            in_mut('I03 input OWNER-STEPS: blank line inserted at top (all line numbers shift)', 'OWNER-STEPS-realrun-v3.md', lambda t: '\n' + t),
            in_mut('I04 input AGENT-SCOPE: OLD text of E-28 appended a second time (count 2)', 'AGENT-SCOPE-DO-AND-DONT.md', lambda t: t + '\n' + o28),
            in_mut('I05 input DECISION-one-store: file emptied', 'DECISION-one-store.md', lambda t: '')):
    out.append(res)
for r in out: print(*r, sep=' | ')
tot = len(out)
print(f'TOTAL {tot} caught {sum(1 for r in out if r[1]=="CAUGHT")} missed {sum(1 for r in out if r[1]=="MISSED")} setup-errors {sum(1 for r in out if r[1]=="SETUP-ERROR")}')
