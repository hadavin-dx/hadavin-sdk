import re,os,stat,subprocess,pty,select,time
DIR='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
S=open(DIR+'OWNER-SHEET-v23.md',encoding='utf-8').read()
LINE=[sp for sp in re.findall(r'`([^`\n]+)`',S) if sp.startswith('( set -C')][0]
assert LINE.count('<key file>')==1
base='/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/v23ind/ks/'
os.makedirs(base+'keys',exist_ok=True)
fake='fake'+'-'+'key'+'-'+'0123456789'+'abcdef'
def line(kf): return LINE.replace('<key file>',kf)
def fresh(n):
    p=base+'keys/'+n
    if os.path.exists(p): os.remove(p)
    return p
def mk(kf): open(kf,'w').write('OLD\n')
def info(kf):
    if os.path.exists(kf):
        st=os.stat(kf); return 'exists=True mode=%s size=%d'%(oct(stat.S_IMODE(st.st_mode)),st.st_size)
    return 'exists=False'
