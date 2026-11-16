"""Apply plan-v10-real-v5-edits.md plus plan-v10-corrections-after-chain.md to the plan AFTER the patch chain.
usage: python3 -I apply-v10-after-chain.py <chained plan, read only> <new output file>
Refuses: wrong input sha256, equal or same-file paths, an output that already exists or is any symlink (also a dangling one), a missing, repeated or malformed RENUMBER line in the corrections file, a RENUMBER that leaves any of edits 8, 13, 27 unchanged, any edit whose old text is not found exactly once.
Writes the output only when no edit failed. Exit 0 = written, exit 1 = refused or failed (nothing written)."""
import hashlib, os, re, sys
H = os.path.dirname(os.path.abspath(__file__)) + '/'
INPUT_SHA = '515cf4704ebba5bdc00e3c2ab9fdce7f65a2a7b8467ceec0bf0942b7e21a7e45'  # gate-rows-v3 result, chain step 3
RX = r'## Edit (\d+): .*?\n~~~~old\n(.*?)\n~~~~\n~~~~new\n(.*?)\n~~~~\n'
RX2 = r'## Edit (\d+) \((?:corrected|added)[^\n]*\n~~~~old\n(.*?)\n~~~~\n~~~~new\n(.*?)\n~~~~\n'
def die(msg):
    print('REFUSED:', msg, file=sys.stderr); sys.exit(1)
def main(argv):
    if len(argv) != 3: die('usage: apply-v10-after-chain.py <chained plan> <new output file>')
    src, dst = argv[1], argv[2]
    if os.path.abspath(src) == os.path.abspath(dst) or os.path.realpath(src) == os.path.realpath(dst): die('input and output are the same path')
    if os.path.lexists(dst): die('output path already exists or is a symlink (this script never overwrites and never follows a link)')
    if not os.path.isdir(os.path.dirname(os.path.abspath(dst))): die('output folder does not exist')
    raw = open(src, 'rb').read(); got = hashlib.sha256(raw).hexdigest()
    if got != INPUT_SHA: die('input sha256 is %s, expected %s (the plan after fixes, repin-v6 and gate-rows-v3)' % (got[:16], INPUT_SHA[:16]))
    cur = raw.decode('utf-8')
    old_t = open(H + 'plan-v10-real-v5-edits.md', encoding='utf-8').read(); cor_t = open(H + 'plan-v10-corrections-after-chain.md', encoding='utf-8').read()
    old = re.findall(RX, old_t, re.S); new = {}
    for i, o, n in re.findall(RX2, cor_t, re.S): new[i] = (o, n)
    ids = [i for i, _, _ in old]
    if len(old) != 29: die('old list parsed %d edits, expected 29' % len(old))
    for i in new:
        if i not in ids and int(i) <= 29: die('correction for unknown edit ' + i)
    lines = re.findall(r'^[ \t]*RENUMBER\b.*$', cor_t, re.M)
    if len(lines) != 1: die('corrections file must hold exactly one RENUMBER line, found %d' % len(lines))
    m = re.fullmatch(r'RENUMBER edits=(\d+(?:,\d+)*) from=(\d+) to=(\d+) shift=(\d+)', lines[0])
    if not m: die('RENUMBER line is malformed: ' + repr(lines[0][:120]))
    rn = (set(m.group(1).split(',')), int(m.group(2)), int(m.group(3)), int(m.group(4)))
    if not {'8', '13', '27'} <= rn[0]: die('RENUMBER must list edits 8, 13 and 27')
    if rn[1] > rn[2]: die('RENUMBER from is greater than to')
    changed = set()
    seq = list(old) + [(i, o, n) for i, (o, n) in new.items() if i not in ids]
    print(len(old), 'old edits; corrected or added:', sorted(new, key=int)); bad = []
    for i, o, n in seq:
        if i in new: o, n = new[i]
        elif rn and i in rn[0]:
            n2 = re.sub(r'UNVERIFIED (\d+)\b', lambda k: 'UNVERIFIED %d' % (int(k.group(1)) + rn[3]) if rn[1] <= int(k.group(1)) <= rn[2] else k.group(0), n)
            if n2 != n: changed.add(i)
            n = n2
        c = cur.count(o)
        if c != 1: bad.append((i, c))
        else: cur = cur.replace(o, n, 1)
    print('failing', bad)
    if bad: die('%d edit(s) did not find their old text exactly once; nothing written' % len(bad))
    if not rn[0] <= changed: die('RENUMBER changed nothing in edit(s) %s (shift 0 or from/to range wrong); nothing written' % sorted(rn[0] - changed, key=int))
    try:
        fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o644)
    except OSError as e: die('cannot create output exclusively: %s' % e)
    try:
        with os.fdopen(fd, 'wb') as f: f.write(cur.encode('utf-8'))
    except BaseException:
        try: os.unlink(dst)
        except OSError: pass
        raise
    print('written', dst, hashlib.sha256(cur.encode('utf-8')).hexdigest()[:16], len(cur.split('\n')) - (1 if cur.endswith('\n') else 0), 'lines')
    return 0
if __name__ == '__main__': sys.exit(main(sys.argv))
