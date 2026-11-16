from ks_lib import *
def run(label,stdin,kf,pre=None):
    if pre: pre(kf)
    r=subprocess.run(['bash','-c',line(kf)],input=stdin,capture_output=True,text=True,timeout=10)
    leak = fake in r.stdout+r.stderr
    print('%-36s stdout=%r stderr_has_path=%s %s key_text_printed=%s'%(label,r.stdout.strip(),bool(r.stderr.strip()),info(kf),leak))
print('LINE under test (from sheet):',LINE)
run('1 normal paste + Enter',fake+'\n',fresh('k1'))
print('   k1 content equals key+newline:',open(base+'keys/k1').read()==fake+'\n','size expected',len(fake)+1)
run('2 empty input (just Enter)','\n',fresh('k2'))
run('2b empty stdin (EOF)','',fresh('k2b'))
run('2c spaces only','   \n',fresh('k2c'))
run('3 no trailing newline',fake,fresh('k3'))
kx=fresh('k4'); run('4 existing file (must not overwrite)',fake+'\n',kx,pre=mk); print('   content after =',repr(open(kx).read()))
run('5 missing folder',fake+'\n',base+'nofolder/k5')
run('6 key with spaces around','  '+fake+'  \n',fresh('k6')); print('   k6 content equals key+newline (spaces trimmed):',open(base+'keys/k6').read()==fake+'\n')
run('7 two lines pasted',fake+'\nid\n',fresh('k7')); print('   k7 only first line saved:',open(base+'keys/k7').read()==fake+'\n')
run('8 key with backslash+tab inside',fake+'\\x\n',fresh('k8')); print('   k8 content equals?',open(base+'keys/k8').read()==fake+'\\x\n')
