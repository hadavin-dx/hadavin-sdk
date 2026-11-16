# MUTATION driver (builder): one damage per copy of the FROZEN v6 script. Each copy must FAIL its self-test.
# usage: python3 -I mutate.py SCRIPT OUTDIR SHELL ID...   (prints one line per damage)
import subprocess, sys, os, re
script, outdir, shell = sys.argv[1], sys.argv[2], sys.argv[3]
ids = sys.argv[4:]
src = open(script, encoding="utf-8").read()
D = {
 "v01-no-pre-stage": ("awk -v MODE=pre -v MAXL=20000 -v CF=\"$LENCUT\" -f \"$MASKAWK\" | sed -E -f \"$MASKSED\"", "sed -E -f \"$MASKSED\""),
 "v02-pwcmds-list-unused": ("(${PWCMDS})", "(zzzqx)", "all"),
 "v03-nonascii-noop": ("    if (body ~ /[\\200-\\377]/) body = nonascii_names(body)\n", "\n"),
 "v04-ml-start-off": ("function ml_start(b,   m, nm, rest, sec, t, tk) {\n", "function ml_start(b,   m, nm, rest, sec, t, tk) {\n  return\n"),
 "v05-length-guard-off": ("-v MAXL=20000 -v CF=", "-v MAXL=900000000 -v CF="),
 "v06-url-userinfo-off": ("s#(//[^:/@[:space:]]*:)[^[:space:]]*@#\\1<masked>@#g\n", "\n"),
 "v07-canary-count-off-by-one": ("CANARY_PLANNED=1167", "CANARY_PLANNED=1166"),
 "v08-selftest-count-off-by-one": ("SELFTEST_PLANNED=1191", "SELFTEST_PLANNED=1190"),
 "v09-signal-kids-not-killed": ("kill_tree \"$MAINPID\" kids; ", ""),
 "v10-bearer-rule-off": ("s#(Bearer)[[:space:]]+[A-Za-z0-9._~+/=-]{6,}#\\1 <masked>#Ig\n", "\n"),
 "v11-jwt-rule-off": ("s/eyJ[A-Za-z0-9_-]{8,}\\.[A-Za-z0-9_.-]+/<masked>/g\n", "\n"),
 "v12-recount-always-ok": ("st_recount() {\n", "st_recount() {\n  return 0\n"),
 "v13-watchdog-off": ("  ( sleep \"$MAXSEC\"; : > \"$WORK/timeout.flag\"; kill -TERM \"$MAINPID\" 2>/dev/null ) &\n  WDPID=$!\n", "  WDPID=\n"),
 "v14-premain-not-background": ("  bg_wait make_list \"$WORK/named.$2.txt\"", "  make_list \"$WORK/named.$2.txt\""),
 "v15-dotted-camel-rule-reverted": ("return dotted_secret(tok)   # every piece a plain name: kept", "return 1"),
 "v16-ml-continue-off": ("  else if (ML_D > 0) { ml_scan(body); hid = 1 }\n", "\n"),
}
META = {"v08-selftest-count-off-by-one", "v09-signal-kids-not-killed", "v13-watchdog-off", "v14-premain-not-background", "v12-recount-always-ok"}
for i in ids:
    old, new = D[i][0], D[i][1]
    if src.count(old) < 1:
        print(f"{i} {shell}: PLANT-FAILED (text to damage not found)"); continue
    m = src.replace(old, new) if len(D[i]) > 2 else src.replace(old, new, 1)
    p = os.path.join(outdir, f"mut-{i}-{shell}.sh")
    open(p, "w", encoding="utf-8").write(m)
    env = dict(os.environ)
    if i not in META: env["LEAD_REPIN_NO_META"] = "1"
    try:
        r = subprocess.run([shell, p, "--self-test"], capture_output=True, timeout=400, env=env)
        out = r.stdout.decode("utf-8", "replace").splitlines()
        first = next((l for l in out if l.startswith("FAIL")), "")
        last = out[-1] if out else ""
        print(f"{i} {shell}: rc={r.returncode} {last[:60]} | first: {first[:110]}")
    except subprocess.TimeoutExpired:
        print(f"{i} {shell}: TIMEOUT")
    os.remove(p)
