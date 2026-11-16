"""Run: python3 tools/test_dump_nodes.py (exit 0 = all 8 fixture cases pass). Made-up fixtures only."""
import subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__))
def table(name):
    return subprocess.run([sys.executable, os.path.join(here, 'dump_nodes.py'), 'table', os.path.join(here, 'fixtures', name)],
                          capture_output=True, text=True, check=True).stdout
def row(out, node):
    return [l for l in out.splitlines() if l.startswith('| ') and f'| {node} |' in l][0]
fail = []
if not row(table('orphan.json'), 'Orphan').rstrip().endswith('NO-INCOMING |'): fail.append('1 orphan must be NO-INCOMING')
if not row(table('subentry.json'), 'SubIn').rstrip().endswith('ENTRY |'): fail.append('2 executeWorkflowTrigger must be ENTRY')
if not row(table('errtarget.json'), 'Err').rstrip().endswith('ENTRY |') or not row(table('errtarget.json'), 'Tell').rstrip().endswith('Y |'): fail.append('3 errorTrigger must be ENTRY and its next node Y')
s = table('secret.json')
if 'hunter2' in s or 'A' * 40 in s or s.count('<masked>') < 2: fail.append('4 secret and 40-char value must be masked')
def run(*a):
    return subprocess.run([sys.executable, os.path.join(here, 'dump_nodes.py'), *a], capture_output=True, text=True)
fx = os.path.join(here, 'fixtures')
sv = table('secret_values.json')
for must in ('postgresql://user', 'abcdefgh1234'):
    if must in sv: fail.append('5 value-only secret leaked: ' + must)
if 'B' * 40 in sv: fail.append('5 whole 40-char token not masked')
if 'https://example.test/v1/' + 'x' * 40 not in sv or 'https://example.test/a/very/long/path' not in sv or 'SELECT lead_key' not in sv: fail.append('5 URL or SQL was masked but must be copied')
c = run('counts', fx).stdout
if 'TOTAL nodes 2' not in c or 'n8n-tests' in c: fail.append('6 counts must count n8n-fx only (2 nodes) and exclude n8n-tests: ' + c.strip())
d = run('diff', os.path.join(fx, 'diff_a.json'), os.path.join(fx, 'diff_b.json')).stdout
if 'ADDED node Extra' not in d or 'CHANGED Work.parameters' not in d: fail.append('7 diff must show ADDED Extra and CHANGED Work.parameters')
if run('diff', os.path.join(fx, 'diff_a.json'), os.path.join(fx, 'diff_a.json')).stdout.count('\n') != 1: fail.append('7 identical diff must print only the settings line')
if run('check', os.path.join(fx, 'dangling.json')).returncode != 1: fail.append('8 dangling edge must exit 1')
if run('check', os.path.join(fx, 'unparsable.json')).returncode != 1: fail.append('8 unparsable must exit 1')
if run('check', os.path.join(fx, 'diff_a.json')).returncode != 0: fail.append('8 clean file must exit 0')
print('FAIL: ' + '; '.join(fail) if fail else 'PASS 8/8'); sys.exit(1 if fail else 0)
