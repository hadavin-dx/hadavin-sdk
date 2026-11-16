from ks_lib import *
def pty_run(label,send,kf,pre=None,wait=3.0):
    if pre: pre(kf)
    pid,fd=pty.fork()
    if pid==0:
        os.execvp('bash',['bash','--norc','--noprofile','-c',line(kf)])
    out=b'';t0=time.time();sent=False
    while time.time()-t0<wait+1:
        r,_,_=select.select([fd],[],[],0.3)
        if r:
            try: d=os.read(fd,4096)
            except OSError: break
            if not d: break
            out+=d
            if b'paste key' in out and not sent:
                time.sleep(0.2); os.write(fd,send); sent=True
    try: os.kill(pid,9)
    except Exception: pass
    try: os.waitpid(pid,0)
    except Exception: pass
    txt=out.decode('latin1').replace('\r','')
    print('PTY %-32s output=%r key_echoed=%s %s'%(label,txt.strip()[:100],fake in txt,info(kf)))
pty_run('normal + Enter',(fake+'\n').encode(),fresh('p1'))
pty_run('Enter only',b'\n',fresh('p2'))
pty_run('Ctrl-D only',b'\x04',fresh('p3'))
pty_run('text then one Ctrl-D',fake.encode()+b'\x04',fresh('p4'))
pty_run('text then two Ctrl-D',fake.encode()+b'\x04\x04',fresh('p5'))
pty_run('existing file',(fake+'\n').encode(),fresh('p6'),pre=mk)
pty_run('missing folder',(fake+'\n').encode(),base+'nofolder/p7')
pty_run('multi-line paste (2 lines)',(fake+'\nid\n').encode(),fresh('p8'))
pty_run('Ctrl-C at the prompt',b'\x03',fresh('p9'))
