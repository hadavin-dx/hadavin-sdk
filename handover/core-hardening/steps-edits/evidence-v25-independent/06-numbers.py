import re,sys,collections
for n in ('A','B'):
    t=open('frozen/OWNER-SHEET-v25-%s.md'%n,encoding='utf-8').read()
    print('=====',n)
    d=collections.Counter(m.group(0) for m in re.finditer(r'(?:US\$|USD|\$)\s?\d[\d,]*(?:\.\d+)?',t))
    print('DOLLAR:',dict(d))
    nums=collections.Counter(re.findall(r'(?:US\$|USD|\$)\s?(\d[\d,]*(?:\.\d+)?)',t))
    allowed={'0.27','0.81','13.21','14.33','15.00','189.00','3.00'}
    print('values not in allowed list:',{k:v for k,v in nums.items() if k not in allowed})
    mins=collections.Counter(m.group(0) for m in re.finditer(r'\b\d+(?:\.\d+)?\s?(?:minutes?|min|seconds?|s)\b',t))
    print('MINUTE/SECOND figures:',dict(mins))
    for m in re.finditer(r'(?:US\$|USD|\$)\s?\d[\d,]*(?:\.\d+)?',t):
        if m.group(0).split()[-1].lstrip('US$D') and re.sub(r'[^\d.]','',m.group(0)) not in allowed:
            s=t.rfind('\n',0,m.start()); e=t.find('\n',m.end())
            print('  CONTEXT',m.group(0),'|',t[max(s,m.start()-80):min(e,m.end()+80)].replace('\n',' '))
