import shutil,subprocess,sys,os,re
W='w/'
def run(edit,desc):
    d='h/x/'; shutil.rmtree('h/x',ignore_errors=True); shutil.copytree(W,d,ignore=shutil.ignore_patterns('__pycache__'))
    ok=edit(d)
    r=subprocess.run([sys.executable,'-B',d+'check-v34.py'],capture_output=True,text=True,env=dict(os.environ,V27_DIR=os.path.abspath(d)+'/'))
    f=[l for l in r.stdout.split('\n') if l.startswith('FAIL')]
    print('%s | edit applied=%s | FAIL lines=%d | %s'%(desc,ok,len(f),'CAUGHT' if f else 'MISSED')); 
    for l in f[:3]: print('    ',l[:150])
def sub(fn,old,new,count=1):
    def e(d):
        s=open(d+fn,encoding='utf-8').read()
        if old not in s: return False
        open(d+fn,'w',encoding='utf-8').write(s.replace(old,new,count)); return True
    return e
run(sub('OWNER-CARD-v34-A.md','23:59 IST','23:58 IST'),'H1 card A: IST 23:59 -> 23:58')
run(sub('OWNER-HELPER-v34.md','18:19','18:20'),'H2 helper: 18:19 -> 18:20 (one place)')
run(sub('OWNER-APPENDIX-v34-B.md','18:04 UTC','18:05 UTC'),'H3 appendix B: 18:04 -> 18:05 UTC')
def delptr(d):
    s=open(d+'OWNER-SHEET-v34-A.md',encoding='utf-8').read()
    m=re.search(r'[^\n]*\(?(?:Appendix|Card|appendix|card)[^\n]*\n',s)
    if not m: return False
    open(d+'OWNER-SHEET-v34-A.md','w',encoding='utf-8').write(s.replace(m.group(0),'',1)); print('   deleted line:',m.group(0)[:90].strip()); return True
run(delptr,'H4 sheet A: delete first line naming Card/Appendix')
def delptr2(d):
    s=open(d+'OWNER-FILM-PERSON-v34.md',encoding='utf-8').read()
    m=re.search(r'[^\n]*(?:Sheet|Card|Appendix|Helper)[^\n]*\n',s)
    if not m: return False
    open(d+'OWNER-FILM-PERSON-v34.md','w',encoding='utf-8').write(s.replace(m.group(0),'',1)); print('   deleted line:',m.group(0)[:90].strip()); return True
run(delptr2,'H5 film page: delete first line naming another page')
run(sub('OWNER-SHEET-v34-B.md','CALL_CEILING = 3','CALL_CEILING = 4'),'H6 sheet B: ceiling 3->4 (extra)')
