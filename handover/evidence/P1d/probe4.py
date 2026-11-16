import sys, time
sys.path.insert(0, sys.argv[1])
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.guard import runmap
if True:
    K = "AKIA" + "IOSFODNN7" + "EXAMPLE"
    S = "wJalr" + "XUtnFEMI/K7MDENG/bPxRfi" + "CYEXAMPLEKEY"
    E = "anna.m" + "@" + "example.org"
    hostile = {
     "md_bold_inside": f"key {K[:4]}**{K[4:]}** here", "md_bold2": f"key {K[:4]}**{K[4:12]}**{K[12:]} here",
     "md_italic": f"key {K[:6]}*{K[6:]}* x", "md_strike": f"key {K[:4]}~~{K[4:]}~~ x", "md_code": f"key {K[:4]}`{K[4:]}` x",
     "md_glued": f"keyz{K[:4]}**{K[4:]}**", "ent_amp": f"key {K[:4]}&amp;{K[4:]} x",
     "ansi_csi": f"key {K[:4]}\x1b[0m{K[4:]} x", "ansi_osc": f"key {K[:4]}\x1b]0;t\x07{K[4:]} x",
     "ctrl_bs": f"key x\x08{K} x", "combining": f"key {K[:4]}́{K[4:]} x",
     "cyrillic_A": "key " + "АKIА" + K[4:] + " x",
     "split_line_patternonly": f"key {K[:10]}\n{K[10:]} x", "lower_patternonly": f"key {K.lower()} x",
     "pw_ansi": f"password={S[:5]}\x1b[1m{S[5:]} end", "pw_ent": f"password={S[:5]}&amp;{S[5:]} end",
     "pw_literal_amp": f"password={S[:5]}&{S[5:]} end",
     "pw_then_md": f"password={S} and again {S[:6]}**{S[6:]}**",
     "pw_then_lower": f"password={S} and again {S.lower()}", "pw_then_split": f"password={S} and {S[:9]}\n{S[9:]}",
     "email_md": f"mail {E[:4]}**{E[4:]}** x", "email_ansi": f"mail {E[:4]}\x1b[0m{E[4:]} x",
     "ent_hex_semi_less": f"key {K[:4]}&#x49{K[5:]} x",
     "ctrl_cr": f"key {K[:4]}\r{K[4:]} x", "ctrl_esc_alone": f"key {K[:4]}\x1b{K[4:]} x",
     "ansi_as_text": f"key {K[:4]}\\x1b[0m{K[4:]} x", "slack_mrkdwn": f"key {K[:4]}_*{K[4:]}*_ x",
     "host_corp": "host db01.corp." + "example.com down", "md_bs_star": f"key {K[:4]}\\*\\*{K[4:]} x",
     "md_escape": f"key {K[:4]}\\*{K[4:]} x", "html_comment": f"key {K[:4]}<!-- -->{K[4:]} x",
    }
    benign = {
     "bold_words": "Approve **restart** of `web-01` in ~~staging~~ demo?",
     "placeholder_in": "Plan for <IPV4_1> and <EMAIL_2>: rotate the key.",
     "code_hash": "commit `0d843b4` and digest `" + "a1b2c3d4" * 8 + "`",
     "md_table": "| a | b |\n|---|---|\n| **x** | `y` |",
     "entities": "Tom &amp; Jerry &lt;ok&gt; &#169; 2026",
     "ansi_color_words": "status \x1b[32mOK\x1b[0m done",
     "ip_twice": "host 10.0.0.1 and 10.0.0.1 again",
     "two_ids": "`fooBarBazQux1234567890abc`/`anotherLongIdentifier99xyz`",
     "glued_code": "run `make`test now",
     "email_plain": f"contact {E} please",
     "pw_plain": f"password={S} end",
     "accented_name": "Approve for Renée Müller-Schön",
     "long_card": ("Approve **step %d**: move `item-%d` to `queue-b`. " * 60),
    }
    for group, rows in (("HOSTILE", hostile), ("BENIGN", benign)):
        print("==", group)
        for n, t in rows.items():
            if "%d" in t: t = t % tuple(range(t.count("%d")))
            t0 = time.perf_counter()
            try: r = "PASS    " + repr(clean(t))[:80]
            except runmap.RedactionError as e: r = "REFUSED " + type(e).__name__
            print(f"{n:24} {time.perf_counter()-t0:5.3f}s {r}")
