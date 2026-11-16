import json,subprocess,sys
s=json.load(open('/tmp/claude-0/er13/sample.json'))
a,b=int(sys.argv[1]),int(sys.argv[2])
sys.exit(subprocess.call([sys.executable,'tests/banner_mutants.py',*s[a:b]]))
