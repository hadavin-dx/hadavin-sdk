"""Compare the five commands of gate4.sh with the run lines of ci.yml. Reads files only."""
import re, sys
ci = open('/home/user/hadavin-sdk/.github/workflows/ci.yml').read()
sh = open('gate4.sh').read()
want = ['ruff check src tests demos', 'ruff format --check src tests demos',
        'pytest -q -m "not live and not perf" -rs', 'pytest -q -m perf -rs', 'bandit -q -r src demos -ll']
bad = 0
for w in want:
    in_ci = any(l.strip().endswith(w) and 'run:' in l for l in ci.splitlines())
    in_sh = any(l.startswith(('uv run --all-extras --group test ', 'uv run --all-extras --group scan ')) and (w + ' >') in l for l in sh.splitlines())
    print(('OK  ' if in_ci and in_sh else 'FAIL'), w, '| in ci.yml:', in_ci, '| in gate4.sh:', in_sh)
    bad += not (in_ci and in_sh)
print('commands in gate4.sh with a redirect:', len([l for l in sh.splitlines() if re.search(r' > "\$p-', l)]))
sys.exit(1 if bad else 0)
