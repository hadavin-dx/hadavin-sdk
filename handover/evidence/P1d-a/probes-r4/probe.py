import sys, re
sys.path.insert(0, sys.argv[1])
import hadavin_sdk, importlib
redact = importlib.import_module("hadavin_sdk.guard.redact"); from hadavin_sdk.guard import runmap
from hadavin_sdk.approvals import channel
print("pkg", hadavin_sdk.__file__)
old = r"((?:&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|[^\s\"';,&]|,(?!\s*[\w.\-]+\s*[:=]))+)"
idx = [i for i,(k,p) in enumerate(redact.PATTERNS) if p.pattern.endswith(old)]
assert len(idx)==1, idx
i = idx[0]; kind, p = redact.PATTERNS[i]
key = p.pattern[:-len(old)]
assert key.startswith(r"(?i)(?<![\w.\-])[\w.\-]{0,40}")
alt = key[len(r"(?i)(?<![\w.\-])[\w.\-]{0,40}"):]
ENT=r"&(?:amp;)?#[0-9]{1,7};|&(?:amp;)?#[xX][0-9a-fA-F]{1,6};|"
fix = sys.argv[2]=="fix"
pk = r"(?i)(?<![\w.\-?&])" + (r"(?<!&amp;)" if fix else "") + r"[\w.\-]{0,40}"
pv = r"((?:"+ENT+(r"&amp;|" if fix else r"&amp;(?=[^\s\"';,])|")+r"[^\s\"';,]|,(?!\s*[\w.\-]+\s*[:=]))+)"
qk = (r"(?i)(?:(?<=[?&])|(?<=&amp;))" if fix else r"(?i)(?<=[?&])") + r"[\w.\-]{0,40}"
qv = r"((?:"+ENT+r"&amp;(?![^\s&#\"'=]*=)|[^\s\"';,&]|,(?!\s*[\w.\-]+\s*[:=])|&(?![^\s&#\"'=]*=))+)"
redact.PATTERNS[i:i+1] = [(kind, re.compile(pk+alt+pv)), (kind, re.compile(qk+alt+qv))]
SV_A="Tq7mZ"; SV_B="4xKp2Vb9Lr3NcW8dYh6uJs"
X=["?password=ab&cd34\"x=1 y","?password=ab&amp;cd34\"x=1 y","password=ab&amp; x","?user=bob&password=ab12cd&next=/home x","password=ab12&cd34ef56gh78ij", f"password={SV_A}&amp;{SV_B}", f"password={SV_A}&{SV_B} end","password=ab12&cd34ef56; next",
"?password=ab&cd34ef56&user=bob x","?password=ab&cd34ef56","?password=ab&amp;cd34ef56&amp;user=bob x","?password=ab&cd34#x=1 y",
"?password=ab&cd34 x=1","?password=ab&cd34; x","password=ab12&cd34ef56gh78ij and later ab12&cd34ef56gh78ij",
"?password=ab12cd&user=bob x","?password=ab12cd&amp;user=bob x","password=hunter22&user=bob","password=&user=bob","?password=ab12cd&debug x",
"?user=bob&password=ab12cd&next=/home x","?user=bob&password=ab&cd34ef56 x","?a=1&amp;password=ab12cd&amp;next=/home x",
"password=ab&cd34;ef56","password=ab&copy;cd x", "?password=SuperSecretPw99&next=/home", f"password={SV_A}&#59;{SV_B}"]
for x in X:
    print(repr(x), "\tmodel", repr(runmap.redact_text(x, runmap.RunMap())), "\tcard", repr(channel.clean(x)))
