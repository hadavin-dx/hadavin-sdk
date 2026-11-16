import re,subprocess
DIR='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
S=open(DIR+'OWNER-SHEET-v23.md',encoding='utf-8').read()
spans=re.findall(r'`([^`\n]+)`',S)
cmdw=('date','ls','cd','clear','sha256sum','echo','grep','TZ=','pgrep','python3','(')
seen=[];n=0;bad=0
for sp in spans:
    if sp in seen: continue
    if not sp.startswith(cmdw): continue
    seen.append(sp)
    filled=re.sub(r'<[^<>]*>','x',sp)
    r=subprocess.run(['bash','-n','-c',filled],capture_output=True,text=True)
    n+=1; bad+= r.returncode!=0
    print('rc=%d  %s   [filled: %s]'%(r.returncode,sp,filled if filled!=sp else '-'))
# all other spans (non-command) listing
others=sorted(set(sp for sp in spans if not sp.startswith(cmdw)))
print('command spans checked',n,'syntax errors',bad)
print('non-command spans (not checked):',others)
# the fenced block
for blk in re.findall(r'```\n(.*?)```',S,re.S):
    r=subprocess.run(['bash','-n','-c',blk],capture_output=True,text=True); print('fenced block bash -n rc=%d (a message sample, not a command)'%r.returncode)
# start line must have the -I and the sample numbers-message start line
