from hadavin_sdk.approvals.channel import clean
bad=0; n=0
tail="0123456789abcdef"*2
for p in ("run","pln","apr","evt"):
    for i in range(16**4):
        ident=f"{p}-{i:04x}{tail[4:]}"; n+=1
        if clean(ident)!=ident: bad+=1; print("bad",ident, clean(ident)) if bad<4 else None
print("clean() ids",n,"bad",bad)
