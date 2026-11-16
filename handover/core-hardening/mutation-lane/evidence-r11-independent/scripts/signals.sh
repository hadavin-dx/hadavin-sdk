#!/bin/bash
. $W/neg/lib.sh; mk_toy; cd $W/neg/toy
echo "### S signals during --restore, uid $(id -u); 5 repeats each of 2 signals x 7 delays"
n=0
for rep in 1 2 3 4 5; do for sig in INT TERM; do for d in 0 0.01 0.02 0.05 0.08 0.12 0.2; do
  n=$((n+1)); fresh_root; plant_kill
  rcl=$($PY - $RUN $sig $d "$W/neg/root" "$W/neg/s.out" <<'PY'
import os, signal, subprocess, sys, time
run, sig, d, root, out = sys.argv[1:6]
t0 = time.monotonic()
with open(out, "w") as fh:
    p = subprocess.Popen([sys.executable, "-B", "-I", run, "--root", root, "--restore"], stdout=fh, stderr=subprocess.STDOUT)
    time.sleep(float(d))
    try: p.send_signal(getattr(signal, "SIG" + sig))
    except ProcessLookupError: pass
    try: rc = p.wait(30)
    except subprocess.TimeoutExpired: p.kill(); rc = "HANG"
print("exit=%s elapsed=%.3f" % (rc, time.monotonic() - t0))
PY
)
  tbl=$(grep -c 'Traceback\|^  File \|Error' $W/neg/s.out)
  mk=$(ls $STATE/*.planted.json 2>/dev/null | wc -l)
  echo "ROW|S$n|uid=$(id -u)|rep=$rep|sig=$sig|delay=$d|$rcl|traceback_lines=$tbl|marker=$([ $mk -gt 0 ] && echo kept || echo gone)|file_after=$(last)|msg=$(tail -1 $W/neg/s.out|cut -c1-110|tr '\n' ' ')"
  $PY $RUN --root $W/neg/root --restore --sha $SHA --repo $W/neg/toy >/dev/null 2>&1; echo "    followup_exit=$? final_file=$(last)"
done; done; done
echo DONE
