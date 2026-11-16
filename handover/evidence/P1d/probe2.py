import sys; sys.path.insert(0, sys.argv[1])
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
K = "AKIA" + "IOSFODNN7" + "EXAMPLE"; E = "anna.m" + "@" + "example.org"; H = "db01.corp." + "example.com"
rows = {
 "email_plain": f"contact {E} please", "email_in_code": f"contact `{E}`", "host_corp": f"host {H} down",
 "url_cred": "see https://" + "u:" + "p4ss" + "w0rdXYZ@" + "example.com/x", "ipv4": "from 10.1.2.3 now",
 "ent_shy": f"key {K[:4]}&shy;{K[4:]} x", "ent_zwsp_named": f"key {K[:4]}&ZeroWidthSpace;{K[4:]} x",
 "ent_nobreak": f"key {K[:4]}&NoBreak;{K[4:]} x", "ent_invtimes": f"key {K[:4]}&InvisibleTimes;{K[4:]} x",
 "ent_hex_nosemi_zw": f"key {K[:4]}&#x200B{K[4:]} x", "ent_dec_nosemi": f"key {K[:4]}&#73{K[5:]} x",
 "ent_double": f"key {K[:4]}&amp;#8203;{K[4:]} x",
 "ins_dash": f"key {K[:4]}-{K[4:]} x", "ins_dot": f"key {K[:4]}.{K[4:]} x",
 "ansi_sgr_long": f"key {K[:4]}\x1b[38;5;196m{K[4:]} x", "ansi_c1_csi": f"key {K[:4]}\x9b0m{K[4:]} x",
 "ansi_osc8_link": f"key {K[:4]}\x1b]8;;http://x\x1b\\{K[4:]} x",
 "ctrl_cr": f"key {K[:4]}\r{K[4:]} x", "ctrl_vt": f"key {K[:4]}\x0b{K[4:]} x", "ctrl_ff": f"key {K[:4]}\x0c{K[4:]} x",
 "ctrl_nul": f"key {K[:4]}\x00{K[4:]} x", "ctrl_esc_alone": f"key {K[:4]}\x1b{K[4:]} x",
 "bidi_rlo": f"key {K[:4]}‮{K[4:]} x", "softhyphen_raw": f"key {K[:4]}­{K[4:]} x",
 "md_link": f"key [{K[:4]}]({K[4:]}) x", "md_html_b": f"key {K[:4]}<b>{K[4:]}</b> x",
 "slack_mrkdwn": f"key {K[:4]}_*{K[4:]}*_ x", "md_bs_star": f"key {K[:4]}\\*\\*{K[4:]} x",
 "fullwidth_star": f"key {K[:4]}＊{K[4:]} x",
 "combining_below": f"key {K[:4]}̣{K[4:]} x",
}
for n, t in rows.items():
    try: o = clean(t)
    except Exception as e: print(f"{n:20} RAISE {type(e).__name__}"); continue
    print(f"{n:20} {repr(o)[:110]}")
