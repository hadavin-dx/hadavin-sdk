import sys
sys.path.insert(0, sys.argv[1])
import hadavin_sdk, os
print("pkg", os.path.dirname(hadavin_sdk.__file__))
from hadavin_sdk.approvals.channel import clean
K = "AKIA" + "IOSFODNN7" + "EXAMPLE"   # the AWS documentation key, built from parts
S = "wJalr" + "XUtnFEMI/K7MDENG/bPxRfi" + "CYEXAMPLEKEY"  # doc secret key shape, from parts
cases = {
 "plain": f"key {K} here",
 "pw_plain": f"password={S} end",
 "md_bold_inside": f"key {K[:4]}**{K[4:]}** here",
 "md_bold2": f"key {K[:4]}**{K[4:12]}**{K[12:]} here",
 "md_italic_star": f"key {K[:6]}*{K[6:]}* x",
 "md_strike": f"key {K[:4]}~~{K[4:]}~~ x",
 "md_code": f"key {K[:4]}`{K[4:]}` x",
 "md_underscore": f"key {K[:4]}_{K[4:]}_ x",
 "ent_named_amp": f"key {K[:4]}&amp;{K[4:]} x",
 "ent_named_empty": f"key {K[:4]}&shy;{K[4:]} x",
 "ent_dec": f"key {K[:4]}&#73;{K[5:]} x",
 "ent_hex": f"key {K[:4]}&#x49;{K[5:]} x",
 "ent_dec_zw": f"key {K[:4]}&#8203;{K[4:]} x",
 "ansi_csi": f"key {K[:4]}\x1b[0m{K[4:]} x",
 "ansi_osc": f"key {K[:4]}\x1b]0;t\x07{K[4:]} x",
 "ansi_as_text": f"key {K[:4]}\\x1b[0m{K[4:]} x",
 "ctrl_bel": f"key {K[:4]}\x07{K[4:]} x",
 "ctrl_bs": f"key x\x08{K} x",
 "ctrl_del": f"key {K[:4]}\x7f{K[4:]} x",
 "ctrl_c1": f"key {K[:4]}\x85{K[4:]} x",
 "zwsp": f"key {K[:4]}​{K[4:]} x",
 "zwj": f"key {K[:4]}‍{K[4:]} x",
 "wj": f"key {K[:4]}⁠{K[4:]} x",
 "combining": f"key {K[:4]}́{K[4:]} x",
 "fullwidth": "key " + "".join(chr(ord(c)+0xFEE0) for c in K) + " x",
 "split_line": f"key {K[:10]}\n{K[10:]} x",
 "lower": f"key {K.lower()} x",
 "pw_md": f"password={S[:5]}**{S[5:]}** end",
 "pw_ent": f"password={S[:5]}&amp;{S[5:]} end",
 "pw_ansi": f"password={S[:5]}\x1b[1m{S[5:]} end",
 "html_tag": f"key {K[:4]}<b></b>{K[4:]} x",
 "md_bold_glued_word": f"keyz{K[:4]}**{K[4:]}**",
}
for n, t in cases.items():
    try:
        o = clean(t)
    except Exception as e:
        print(f"{n:20} RAISE {type(e).__name__}"); continue
    flat = "".join(ch for ch in o if ch.isalnum()).upper()
    leak = K in flat or S.replace("/","").upper()[:20] in flat.upper()
    print(f"{n:20} {'LEAK' if leak else 'ok  '} {o!r}"[:160])
