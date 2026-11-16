import re
OLD = re.compile(r"(?i)(?=((?:akia|asia)(?:[a-z2-7]|[&.\\](?=[a-z2-7])){16,17}))")
NEW = re.compile(r"(?i)(?=((?:akia|asia)(?:[a-z2-7]|[&.\\](?=[a-z2-7])){16,17})(?![a-z0-9_-]))")
def learn(rx, t):
    out = []
    for m in rx.finditer(t):
        c = m.group(1); g = sum(c.count(x) for x in "&.\\"); core = re.sub(r"[&.\\]", "", c)
        if g <= 1 and len(core) == 20 and sum(ch in "234567" for ch in core[4:]) >= 2:
            out.append(core.upper())
    return out
K2 = "AKIA" + "IOSFODN2" + "7EXAMPLE"
NOT = ["Southeast Asia and Oceania","Asia 2024 Q3 revenue growth","Eurasia 2025 results","Asia-Pacific 2025 results",
 "Asia and Oceania markets overview","Asia leads 5 new markets signed","Malaysia has 5 offices in total",
 "Southeast Asia sales rose 4 percent","Nakia 3 teams","Asia pacific region Q3 2 results","asia-markets-rise-3-5-percent",
 "asia_region_q3_q2_totals","ASIA_SHARD_2_REPLICA_3_PRIMARY","Asia 2 of 3 are on it so be","asia.shard23.example",
 "asia.region23q4totalsx.v2","akia"+"abcdefghijklmnop","asianmarketsq23q4forecast","asiapacificregion23q4",
 "asiaabcdefghijklm23n8xyz","region asiaabcdefghijklm23n_8","asiaabcdefghijklm23n-v2","Asia\nabcdefghijklm23n0 end"]
YES = [K2.lower(), "AKIA&amp;IOSFODN27EXAMPLE".replace("&amp;","&"), "AKIA.IOSFODN27EXAMPLE", "AKIA\\IOSFODN27EXAMPLE",
 "keyz"+K2, "keyz"+K2+" here", "x akia.iosfodn27example.com y", ("ASIAQWER"+K2).lower(),
 "asia."+"abcdefghijklm3no", "asia"+"bcdefghijk01mn23"]
for name, rows in (("NOT", NOT), ("YES", YES)):
    for t in rows:
        print(name, repr(t), "old", learn(OLD, t), "new", learn(NEW, t))
print("viewd", learn(OLD, "Asiaabcdefghijklm23n0 end"), learn(NEW, "Asiaabcdefghijklm23n0 end"))
M8 = lambda t: [re.sub(r"[&.\\]","",m.group(1)).upper() for m in NEW.finditer(t) if len(re.sub(r"[&.\\]","",m.group(1)))==20]
print("M8 asia-1d", M8("asia."+"abcdefghijklm3no"))
M9 = re.compile(r"(?i)(?=((?:akia|asia)(?:[a-z0-9]|[&.\\](?=[a-z0-9])){16,17})(?![a-z0-9_-]))")
print("M9 m9-kill", learn(M9, "asia"+"bcdefghijk01mn23"))
