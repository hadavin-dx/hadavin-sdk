from lib import *
S="<made-up-value>"
seps={"glued":"","zwsp":"​","comma":",","semicolon":";","space":" ","newline":"\n"}
for sn,s in seps.items():
    for k in ("password: ","password=","token: "):
        t=f"https://example.com/x{s}{k}{S}"
        for p,o in (("walk",walk({"m":t})["m"]),("card",clean(t)),("slack",slack(t))):
            print(f"link|{sn}|{k.strip()}|{p}|{'READABLE' if readable(S,o) else '-'}|{o.replace(S,'<A>')!r}")
