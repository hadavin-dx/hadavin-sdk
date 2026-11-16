# v8 plant runner (builder). One damage per copy of lead-repin-verify.v8.sh; every copy must FAIL the self-test.
# usage: python3 -I mutate8.py SCRIPT OUTDIR SHELL [ID...]
# Phase 1: filter cases only (LEAD_REPIN_NO_META=1, fast). If the copy survives phase 1, phase 2 runs the FULL self-test (machinery cases too).
# Verdicts: KILLED-phase1, KILLED-phase2, SURVIVED (a survivor is NOT proved equivalent by this script).
import sys, os, subprocess, time
script, outdir, shell = sys.argv[1], sys.argv[2], sys.argv[3]
only = sys.argv[4:]
src = open(script, encoding="utf-8").read()
def L(prefix):
    for l in src.split("\n"):
        if l.startswith(prefix): return l + "\n"
    return "@@NOT-FOUND@@"
M = [
("m01", "(Bearer)[[:space:]]+[^[:space:]<\"',;)]{4,}", "(Bearer)[[:space:]]+[^[:space:]<\"',;)]{40,}"),
("m02", "s#(://)[^:/@[:space:]]{4,}@#", "s#(://)[^:/@[:space:]]{40,}@#"),
("m03", "BY[[:space:]]+)(${STR}|[^[:space:];<]", "BX[[:space:]]+)(${STR}|[^[:space:];<]"),
("m04", "(requirepass|masterauth|auth-pass|bindpw|rootpw)", "(masterauth|auth-pass|bindpw|rootpw)"),
("m05", "(ghp|gho|ghs|ghu)_[A-Za-z0-9]{10,}", "(ghp|gho|ghs|ghu)_[A-Za-z0-9]{100,}"),
("m06", "(AKIA|ASIA)[0-9A-Z]{16}/<masked>", "(AKIA|ASIA)[0-9A-Z]{17}/<masked>"),
("m07", "eyJ[A-Za-z0-9_-]{8,}", "eyJ[A-Za-z0-9_-]{80,}"),
("m08", "([A-Za-z0-9-]+\\.)+[A-Za-z]{2,}/<email-masked>", "([A-Za-z0-9-]+\\.)+[A-Za-z]{20,}/<email-masked>"),
("m09", "STRONG='(secret|passw[o0]?r?d|passphrase|credential|token|apikey|", "STRONG='(secret|passw[o0]?r?d|passphrase|credential|apikey|"),
("m10", "PRE=\"[\\\"']?[]]?[[:space:]]*=\"", "PRE=\"[\\\"']?[]]?[[:space:]]*==\""),
("m11", "[[:space:]]*:=[[:space:]]*)(${STR}", "[[:space:]]*:==[[:space:]]*)(${STR}"),
("m12", "if (n < 24) return (tok ~", "if (n < 240) return (tok ~"),
("m13", "umask 077\n", "umask 022\n"),
("m14", " -c core.hooksPath=/dev/null", ""),
("m15", " -c gpg.program=/bin/false", ""),
("m16", "/-----BEGIN [A-Z ]*(PRIVATE|SECRET|ENCRYPTED)[A-Z ]*-----/{", "/-----BEGIN [A-Z ]*(PRIVATE|SECRET)[A-Z ]*-----/{"),
("m17", "/(curl|wget|http)/I s/", "/(curl)/I s/"),
("m18", "[A-Za-z0-9+/=]{16,}#\\1 <masked>#Ig", "[A-Za-z0-9+/=]{160,}#\\1 <masked>#Ig"),
("m19", "  case $WORK in */lead-repin.??????) ;; *) return 0 ;; esac\n", "\n"),
("m20", "SQ=\"'([^'\\\\\\\\]|\\\\\\\\.)*'\"", "SQ=\"'x([^'\\\\\\\\]|\\\\\\\\.)*'\""),
("m21", "xox[abprs]-[A-Za-z0-9-]{8,}", "xox[abprs]-[A-Za-z0-9-]{80,}"),
("m22", "|psql|", "|"),
("m23", "LC_ALL=C; export LC_ALL", "export LC_ALL"),
("m24", "? 1 : 0     # 16 to 23", "? 0 : 0     # 16 to 23"),
# v8 plants: one per new class
("n01", "  if (s ~ /[\\001-\\010\\013-\\037\\177]/) {", "  if (0) {"),
("n02", "  line = ctl_strip(line)  ", "  line = line  "),
("n03", "s/</%s/g\\n", "s/<</%s/g\\n"),
("n04", L("s/(^${PFX0}[[:space:]]*(- +)?[\"']?[A-Za-z0-9_.-]*${STRONG}"), "\n"),
("n05", "printf '%s %s\\n' \"$1\" \"$ms_rc\" >> \"$WORK/mask.fail\" 2>/dev/null", ":"),
("n06", "    elif [ \"$LEAD_REPIN_GIT_STATUS\" != 1 ]; then", "    elif false; then"),
("n07", "do unset \"$env_v\" 2>/dev/null; done", "do :; done"),
("n08", "    gsub(/&[Qq][Uu][Oo][Tt];|&#0*34;|&#[xX]0*22;/, \"\\\"\", t)\n", "\n"),
("n09", "  case ${#MAXSEC} in [1-6]) ;; *) MAXSEC=1200 ;; esac", "\n"),
("n10", "s/(<(${IDB})([[:space:]][^>]*)?>)<!\\[CDATA\\[([^]]|\\][^]]|\\]\\][^>])*\\]\\]>/\\1<masked>/Ig\n", "\n", 2),
("n11", "s/((login|authenticate|authorize|sign_?in|basic_?auth|set_?pass(word)?|add_?user)", "s/((zzzlogin)"),
("n12", "api[_.-]?key)[A-Za-z0-9_.-]*[[:space:]]*[=!]==?", "apikey)[A-Za-z0-9_.-]*[[:space:]]*[=!]==?"),
("n13", "|remmina'\nPWCMDS_A=\"$PWCMDS|http|https|xh\"", "|remmina'\nPWCMDS_A=\"$PWCMDS\""),
("n14", "unset -f sed awk grep tr find git ps head sort wc cat kill sleep date mktemp rm ls cut tee id uname mkdir cp mv chmod basename dirname env printf test 2>/dev/null", ":"),
("n15", "  gsub(/\\002/, \"<\", line)", "  gsub(/\\002/, \"\", line)"),
("n16", "EBD='\\\\\"'", "EBD=''"),
]
os.makedirs(outdir + "/mut", exist_ok=True)
for ent in M:
    name, a, b = ent[0], ent[1], ent[2]
    expect = ent[3] if len(ent) > 3 else 1
    if only and name not in only: continue
    c = src.count(a)
    if c != expect:
        print(f"{name}: PLANT-FAILED (found {c} times, expected {expect})", flush=True); continue
    f = f"{outdir}/mut/{name}.sh"
    open(f, "w", encoding="utf-8").write(src.replace(a, b))
    env = dict(os.environ, TMPDIR=outdir + "/tmp")
    os.makedirs(outdir + "/tmp", exist_ok=True)
    t = time.time()
    e1 = dict(env, LEAD_REPIN_NO_META="1")
    try:
        r = subprocess.run([shell, f, "--self-test"], capture_output=True, text=True, env=e1, timeout=300, errors="replace")
        out = r.stdout + r.stderr; rc = r.returncode
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"; rc = "timeout"
    last = [l for l in out.splitlines() if l.startswith("SELF-TEST") or l.startswith("STOP")][-1:] or [out[-100:].replace("\n", " ")]
    if rc != 0:
        nf = sum(1 for l in out.splitlines() if l.startswith("FAIL"))
        print(f"{name} [{shell}]: KILLED-phase1 exit={rc} fail_lines={nf} {last[0][:100]} ({time.time()-t:.0f}s)", flush=True); continue
    try:
        r = subprocess.run([shell, f, "--self-test"], capture_output=True, text=True, env=env, timeout=900, errors="replace")
        out = r.stdout + r.stderr; rc = r.returncode
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"; rc = "timeout"
    fl = [l for l in out.splitlines() if l.startswith("FAIL")][:2]
    last = [l for l in out.splitlines() if l.startswith("SELF-TEST")][-1:] or [out[-100:].replace("\n", " ")]
    print(f"{name} [{shell}]: {'KILLED-phase2' if rc != 0 else 'SURVIVED'} exit={rc} {last[0][:90]} first_fail={fl[:1]} ({time.time()-t:.0f}s)", flush=True)
