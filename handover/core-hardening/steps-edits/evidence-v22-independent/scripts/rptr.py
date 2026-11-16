import re
DIR='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
for n in ['OWNER-SHEET-v22.md','LEAD-RELEASE-NOTE-v6.md','v22-OPEN-FOR-LEAD.md','v22-CHANGES.md','checkpoint-v22.md']:
    t=open(DIR+n,encoding='utf-8').read()
    for m in re.finditer(r'\bR(\d+)\b|card (?:Part|step)s? [\d, a-z()and]+|\bsections? \d+( to \d+)?',t):
        print(n[:12],'|',m.group(0),'|',t[max(0,m.start()-70):m.end()+50].replace('\n',' '))
