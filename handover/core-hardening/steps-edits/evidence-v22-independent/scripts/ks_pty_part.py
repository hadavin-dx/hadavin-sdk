import subprocess,os,hashlib,stat,pty,select,time,re
base='/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ks/'
LINE='( set -C; umask 077; read -rs -p \'paste key, Enter: \' K && [ -n "$K" ] && printf \'%s\\n\' "$K" > "'+'{kf}'+'" ); echo "exit $?"'
fake='fake'+'-'+'key'+'-'+'0123456789'+'abcdef'   # built from parts, not a real secret
def run(label,stdin,kf,pre=None):
    if pre: pre(kf)
    r=subprocess.run(['bash','-c',LINE.format(kf=kf)],input=stdin,capture_output=True,text=True,timeout=10)
    ex=os.path.exists(kf)
    info=''
    if ex:
        st=os.stat(kf); info=' file mode=%s size=%d'%(oct(stat.S_IMODE(st.st_mode)),st.st_size)
    leak = fake in r.stdout+r.stderr
    print('%-34s stdout=%r stderr=%r exists=%s%s key_text_printed=%s'%(label,r.stdout.strip(),r.stderr.strip()[:90],ex,info,leak))
def fresh(n): 
    p=base+'keys/'+n; 
    if os.path.exists(p): os.remove(p)
    return p
# PTY run: hidden echo, Enter
def pty_run(label,send,kf,pre=None):
    if pre: pre(kf)
    pid,fd=pty.fork()
    if pid==0:
        os.execvp('bash',['bash','--norc','--noprofile','-c',LINE.format(kf=kf)])
    out=b''; t0=time.time(); sent=False
    while time.time()-t0<4:
        r,_,_=select.select([fd],[],[],0.3)
        if r:
            try: d=os.read(fd,4096)
            except OSError: break
            if not d: break
            out+=d
            if b'paste key' in out and not sent:
                time.sleep(0.2); os.write(fd,send); sent=True
        else:
            if sent and time.time()-t0>3: pass
    try:
        os.kill(pid,9)
    except Exception: pass
    try: os.waitpid(pid,0)
    except Exception: pass
    txt=out.decode('latin1').replace('\r','')
    print('PTY %-30s output=%r key_echoed=%s exists=%s'%(label,txt.strip()[:120],fake in txt,os.path.exists(kf)))
pty_run('normal + Enter',(fake+'\n').encode(),fresh('p1'))
pty_run('Enter only',b'\n',fresh('p2'))
pty_run('Ctrl-D only',b'\x04',fresh('p3'))
pty_run('text then Ctrl-D (no Enter)',(fake).encode()+b'\x04',fresh('p4'))
pty_run('text then Ctrl-D twice',(fake).encode()+b'\x04\x04',fresh('p5'))
pty_run('existing file',(fake+'\n').encode(),fresh('p6'),pre=mk)
pty_run('missing folder',(fake+'\n').encode(),base+'nofolder/p7')
