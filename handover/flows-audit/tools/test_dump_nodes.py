"""Run: python3 tools/test_dump_nodes.py (exit 0 = all 4 fixture cases pass). Made-up fixtures only."""
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
print('FAIL: ' + '; '.join(fail) if fail else 'PASS 4/4'); sys.exit(1 if fail else 0)
