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
run('1 normal paste + Enter',fake+'\n',fresh('k1'))
run('2 empty input (just Enter)','\n',fresh('k2'))
run('2b empty stdin (EOF / Ctrl-D)','',fresh('k2b'))
run('2c spaces only','   \n',fresh('k2c'))
run('3 no trailing newline',fake,fresh('k3'))
def mk(kf): open(kf,'w').write('OLD\n')
kx=fresh('k4'); 
run('4 existing file (must not overwrite)',fake+'\n',kx,pre=mk)
print('   existing file content after =',repr(open(kx).read()))
run('5 missing folder',fake+'\n',base+'nofolder/k5')
run('6 key with leading/trailing spaces','  '+fake+'  \n',fresh('k6'))
print('   k6 content equals fake? ',open(base+'keys/k6').read()==fake+'\n' if os.path.exists(base+'keys/k6') else 'n/a')
run('7 two lines pasted (2nd line leftover)',fake+'\nrm -rf x\n',fresh('k7'))
print('   k7 content has only first line:',open(base+'keys/k7').read()==fake+'\n')
# sha check of normal file equals expected
print('   k1 content equals fake+newline:',open(base+'keys/k1').read()==fake+'\n')
# permission of file: -rw-------
