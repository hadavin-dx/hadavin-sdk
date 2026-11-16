# MUTATION driver (builder): one damage per copy of the FROZEN v6 script. Each copy must FAIL its self-test.
# usage: python3 -I mutate.py SCRIPT OUTDIR SHELL ID...   (prints one line per damage)
import subprocess, sys, os, re, signal, tempfile, shutil
script, outdir, shell = sys.argv[1], sys.argv[2], sys.argv[3]
ids = sys.argv[4:]
src = open(script, encoding="utf-8").read()
def L(prefix):
    for l in src.split("\n"):
        if l.startswith(prefix): return l + "\n"
    return "@@NOT-FOUND@@"
D = {
 "v01-no-pre-stage": ("awk -v MODE=pre -v MAXL=20000 -v CF=\"$LENCUT\" -f \"$MASKAWK\" | sed -E -f \"$MASKSED\"", "sed -E -f \"$MASKSED\""),
 "v02-pwcmds-list-unused": ("(${PWCMDS})", "(zzzqx)", "all"),
 "v03-nonascii-noop": ("    if (body ~ /[\\200-\\377]/) body = nonascii_names(body)\n", "\n"),
 "v04-ml-start-off": ("function ml_start(b,   m, nm, rest, sec, t, tk) {\n", "function ml_start(b,   m, nm, rest, sec, t, tk) {\n  return\n"),
 "v05-length-guard-off": ("-v MAXL=20000 -v CF=", "-v MAXL=900000000 -v CF="),
 "v06-url-userinfo-off": ("s#(//[^:/@[:space:]]*:)[^[:space:]]*@#\\1<masked>@#g\n", "\n"),
 "v07-canary-count-off-by-one": ("CANARY_PLANNED=1372", "CANARY_PLANNED=1371"),
 "v08-selftest-count-off-by-one": ("SELFTEST_PLANNED=1398", "SELFTEST_PLANNED=1397"),
 "v09-signal-kids-not-killed": ("kill_tree \"$MAINPID\" kids; ", ""),
 "v10-bearer-rule-off": (L("s#(Bearer)[[:space:]]+"), "\n"),
 "v11-jwt-rule-off": ("s/eyJ[A-Za-z0-9_-]{8,}\\.[A-Za-z0-9_.-]+/<masked>/g\n", "\n"),
 "v12-recount-always-ok": ("st_recount() {\n", "st_recount() {\n  return 0\n"),
 "v13-watchdog-off": (L("  ( wd_i=0;") + "  WDPID=$!\n", "  WDPID=\n"),
 "v14-premain-not-background": ("  bg_wait make_list \"$WORK/named.$2.txt\"", "  make_list \"$WORK/named.$2.txt\""),
 "v15-dotted-camel-rule-reverted": ("return dotted_secret(tok)   # every piece a plain name: kept", "return 1"),
 "v16-ml-continue-off": ("  else if (ML_D > 0) { ml_scan(body); hid = 1 }\n", "\n"),
 "v17-escaped-quote-string-rule-off": (L("s/(${BQ}(${IDQ})${BQ}[[:space:]]*:[[:space:]]*${BQ})"), "\n"),
 "v18-unicode-escape-key-rule-off": (L('s/(["\'][^"\']*'), "\n"),
 "v19-shape-rule-separators-off": ("|[;&|(]|\\\\\\$\\\\()[[:space:]]*([A-Za-z_]", ")[[:space:]]*([A-Za-z_]"),
 "v20-glued-names-off": ("|requirepass|masterauth|jsessionid|phpsessid|(db|root|admin|user|mysql|pg|redis|master|ssh|smtp|mail|ldap|sql|wifi|wpa|sys|login)(pass|pw|pwd))'\n  W=", ")'\n  W="),
 "v21-git-safety-settings-off": ("-c log.showSignature=false -c gpg.program=/bin/false -c core.hooksPath=/dev/null ", ""),
 "v22-relative-tmpdir-allowed": (L("case ${TMPDIR:-/tmp} in /*)"), "\n"),
 "v23-xml-text-rule-off": (L("s/(<(${IDB})([[:space:]][^>]*)?>)[^<]+<"), "\n"),
 "v24-userinfo-no-scheme-rule-off": (L("s#(^|[[:space:]\"'=(])([A-Za-z0-9._-]+:)"), "\n"),
 "v25-identified-by-rule-off": (L("s/(IDENTIFIED[[:space:]]+"), "\n"),
 "v26-colon-equals-rule-off": (L("s/((${ID})[[:space:]]*:=[[:space:]]*)"), "\n"),
 "v27-requirepass-line-rule-off": (L("s/(^${PFX0}[[:space:]]*(requirepass|masterauth"), "\n"),
 "v28-second-literal-rule-off": (L("s/(<masked>[[:space:]]*(\\|\\||"), "\n"),
 "v29-escaped-slash-userinfo-off": (L("s#(("), "\n"),
}
META = {"v21-git-safety-settings-off", "v22-relative-tmpdir-allowed", "v08-selftest-count-off-by-one", "v09-signal-kids-not-killed", "v13-watchdog-off", "v14-premain-not-background", "v12-recount-always-ok"}
for i in ids:
    old, new = D[i][0], D[i][1]
    if src.count(old) < 1:
        print(f"{i} {shell}: PLANT-FAILED (text to damage not found)"); continue
    m = src.replace(old, new) if len(D[i]) > 2 else src.replace(old, new, 1)
    p = os.path.join(outdir, f"mut-{i}-{shell}.sh")
    open(p, "w", encoding="utf-8").write(m)
    env = dict(os.environ)
    if i not in META: env["LEAD_REPIN_NO_META"] = "1"
    # v7 driver: private TMPDIR per damage, own session, raw output saved, whole process group killed on timeout
    # (v6 driver used subprocess.run(timeout=...), which waits for pipes held by grandchildren and hung on v13).
    tmpd = tempfile.mkdtemp(prefix=f"mut7-{i}-", dir=outdir); env["TMPDIR"] = tmpd
    rawp = os.path.join(outdir, f"raw-{i}-{shell}.txt")
    with open(rawp, "wb") as rf:
        pr = subprocess.Popen([shell, p, "--self-test"], stdout=rf, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        try:
            rc = pr.wait(timeout=400); to = False
        except subprocess.TimeoutExpired:
            to = True; rc = None
        try: os.killpg(pr.pid, signal.SIGKILL)
        except OSError: pass
        pr.wait()
    out = open(rawp, encoding="utf-8", errors="replace").read().splitlines()
    first = next((l for l in out if l.startswith("FAIL")), "")
    last = out[-1] if out else ""
    left = len(os.listdir(tmpd)); shutil.rmtree(tmpd, ignore_errors=True)
    print(f"{i} {shell}: {'TIMEOUT(group killed)' if to else 'rc=%s' % rc} folders_left_in_private_tmp={left} {last[:70]} | first: {first[:110]}", flush=True)
    os.remove(p)
