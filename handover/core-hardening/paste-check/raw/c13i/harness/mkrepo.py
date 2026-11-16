import re,subprocess,os,sys
hb,=sys.argv[1:]
pf=hb+'/egm/duplicate-proof-lead-desk/wp6/plan-wp6-resmoke-v5.md'
wt=hb+'/_local/scratch/wt/nlite-fix5'
os.makedirs(wt+'/scripts',exist_ok=True)
rows=[]
for l in open(pf):
    if l.startswith('| S7 |'): rows.append(('S7','n8n_start.sh','N8N_*|DB_*|EXECUTIONS_*|WEBHOOK_URL|GENERIC_TIMEZONE|TZ) ;;')); continue
    m=re.match(r'^\| (\w+) \| (\S+) \| `(.*)` \|',l)
    if m and '<FINAL-LINES>' in l: rows.append((m.group(1),m.group(2),m.group(3).split('` (in')[0].replace('\\','')))
def g(*a): subprocess.run(['git','-C',wt]+list(a),check=True,capture_output=True)
g('init','-q','-b','main'); g('config','user.email','x@example.invalid'); g('config','user.name','t')
files={}
for i,f,s in rows: files.setdefault(f,[]).append(s)
def write(extra):
    for f,ss in files.items():
        open(wt+'/scripts/'+f,'w').write('# header\n'+'\n'.join(ss)+'\n'+extra)
write('old\n'); g('add','-A'); g('commit','-q','-m','old')
write('refused: new wording\n'); open(wt+'/scripts/n8n_kill.py','a').write('    return 3\n'); g('add','-A'); g('commit','-q','-m','new'); g('branch','take/nlite-int-r5')
open(os.path.dirname(os.path.dirname(pf))+'/../../../_x','w') if False else None
sm=hb+'/_local/scratch/wp6-smoke'; os.makedirs(sm,exist_ok=True)
with open(sm+'/strings.txt','w') as o:
    for i,f,s in rows: o.write(f'{i}\t{f}\t{s}\n')
print(len(rows),'rows'); print(subprocess.run(['git','-C',wt,'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip(),file=open(hb+'/../../pin.txt','w'))
