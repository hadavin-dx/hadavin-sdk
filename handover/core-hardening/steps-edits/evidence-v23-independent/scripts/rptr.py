import re
DIR='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
for n in ['OWNER-SHEET-v23.md','LEAD-RELEASE-NOTE-v7.md','v23-OPEN-FOR-LEAD.md','v23-CHANGES.md','checkpoint-v23.md']:
    t=open(DIR+n,encoding='utf-8').read()
    for m in re.finditer(r'\bR(\d+)\b|card (?:Part|step|list)s? [\d, a-z()and]+|\bPart \d[^ ]*|\bsections? \d+( to \d+)?|\bcard\b[^.;|]{0,30}\([a-h]\)|list \([a-h]\)|\bstep \d+|\bsteps \d[^ ]*( to \d)?',t):
        print(n[:12],'|',m.group(0),'|',t[max(0,m.start()-80):m.end()+60].replace('\n',' '))
