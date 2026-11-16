
open(D+'EDITS.md','w').write(T)
print('errors:', len(errs))
for e in errs: print(' ', e)
sys.exit(1 if errs else 0)
