# interactive bash on a pty: type the sheet's line, then paste TWO lines (key + a harmless marker command); shows whether the 2nd line reaches the shell
from ks_lib import *
kf=fresh('i1')
pid,fd=pty.fork()
if pid==0: os.execvp('bash',['bash','--norc','--noprofile','-i'])
def rd(t=1.0):
    out=b'';t0=time.time()
    while time.time()-t0<t:
        r,_,_=select.select([fd],[],[],0.2)
        if r:
            try: d=os.read(fd,4096)
            except OSError: break
            if not d: break
            out+=d
    return out.decode('latin1').replace('\r','')
rd(1.0)
os.write(fd,(line(kf)+'\n').encode()); o1=rd(1.0)
os.write(fd,(fake+'\necho LEFTOVER_LINE_RAN\n').encode()); o2=rd(1.5)
print('after typing the line:',repr(o1[-60:]))
print('after pasting key + second line:',repr(o2[-200:]).replace(fake,'<KEY>'))
print('key echoed:',fake in o1+o2,'| second line reached the shell and ran:', 'LEFTOVER_LINE_RAN' in o2.replace('echo LEFTOVER_LINE_RAN','')); print(info(kf))
try: os.write(fd,b'exit\n')
except Exception: pass
time.sleep(0.3)
try: os.kill(pid,9)
except Exception: pass
try: os.waitpid(pid,0)
except Exception: pass
