import sys
s=open(sys.argv[1],newline='').read()
m=sys.argv[2]
N="\n"
SC="semgrep scan --metrics=off"
M={
"M01 yaml anchor/alias env":("          RETRY_PAUSE_SECONDS: \"20\"","          RETRY_PAUSE_SECONDS: &p \"20\"\n          B: *p"),
"M02 duplicate key run (later wins)":("      - name: Semgrep (fails on findings of severity ERROR)\n","      - name: Semgrep (fails on findings of severity ERROR)\n        run: \"true\"\n"),
"M03 setup with token":('python-version: "3.12"','python-version: "3.12"\n          token: abc'),
"M04 checkout with path":("persist-credentials: false\n","persist-credentials: false\n          path: x\n"),
"M05 checkout with token":("persist-credentials: false\n","persist-credentials: false\n          token: abc\n"),
"M06 step env SEMGREP_RULES":('RETRY_PAUSE_SECONDS: "20"','RETRY_PAUSE_SECONDS: "20"\n          SEMGREP_RULES: p/ci'),
"M07 pause 20->0":('RETRY_PAUSE_SECONDS: "20"','RETRY_PAUSE_SECONDS: "0"'),
"M08 retry count 3->1 loop":("for attempt in 1 2 3; do","for attempt in 1; do"),
"M09 retry on any nonzero":('if [[ "$status" -ne 2 ]]; then break; fi','if [[ "$status" -eq 0 ]]; then break; fi'),
"M10 exit status lost (exit 0)":('exit "$status"','exit 0'),
"M11 scan appended || true":("status=0 || status=$?","status=0 || status=$? || true"),
"M12 bash -x in run (set -x)":("          status=0\n","          set -x\n          status=0\n"),
"M13 scan line continuation":("--severity ERROR --config p/python","--severity ERROR \\\n              --config p/python"),
"M14 echo before scan: semgrep scan in echo":('echo "semgrep $(','echo "semgrep scan x"; echo "semgrep $('),
"M15 scan skipped via if inside run":("          status=0\n","          if [[ -n \"$CI\" ]]; then exit 0; fi\n          status=0\n"),
"M16 -c replaced (config path)":("--config p/javascript src","--config p/javascript src"),
"M17 name change install":("Install Semgrep (pinned version, hashes are checked)","Install"),
"M18 comment hides flag":("--disable-version-check --strict --error","--disable-version-check --strict --error"),
"M19 -x: attempt sleep 20 -> 0 literal":('sleep "${RETRY_PAUSE_SECONDS}"','sleep 0'),
"M20 message claims findings on 2":('elif [[ "$status" -ne 0 ]]; then','elif [[ "$status" -ne 0 && "$status" -ne 3 ]]; then'),
"M21 check step pip check removed":("          python -m pip check\n",""),
"M22 setup step name added":("      - uses: actions/setup-python","      - name: x\n        uses: actions/setup-python"),
"M23 top name changed":("name: semgrep\n","name: other\n"),
"M24 exit code 1 hidden":('if [[ "$status" -eq 1 ]]; then','if [[ "$status" -eq 1 ]]; then status=0'),
"M25 PYTHONPATH/SEMGREP_APP_TOKEN step env":('RETRY_PAUSE_SECONDS: "20"','RETRY_PAUSE_SECONDS: "20"\n          SEMGREP_APP_TOKEN: x'),
"M26 pip install extra index in comment-free":('--no-deps -r requirements-semgrep.txt"','--no-deps -r requirements-semgrep.txt"'),
"M27 permissions pull-requests write job":("timeout-minutes: 20 ","timeout-minutes: 20 "),
"M28 scan words reorder (flags order)":("--strict --error --severity ERROR","--error --strict --severity ERROR"),
"M29 scan step uses id/with":("        env:\n          RETRY","        id: s\n        env:\n          RETRY"),
"M31 skip on pull_request event inside run":("          status=0\n","          if [[ \"${GITHUB_EVENT_NAME:-}\" == \"pull_request\" ]]; then exit 0; fi\n          status=0\n"),
"M32 skip when GITHUB_ACTIONS set":("          status=0\n","          if [[ -n \"${GITHUB_ACTIONS:-}\" ]]; then exit 0; fi\n          status=0\n"),
"M33 dup key run before real (first)":("        run: |\n          # printed once","        run: |\n          # printed once"),
"M34 extra line after loop curl":("          exit \"$status\"","          echo done >> \"${GITHUB_STEP_SUMMARY:-/dev/null}\"\n          exit \"$status\""),
"M30 pull_request_target added":("on:\n  pull_request:","on:\n  pull_request_target:\n    branches: [main]\n  pull_request:"),
}
if m=="LIST": print("\n".join(M)); sys.exit()
o,n=M[m]
if o==n: print("NOOP"); sys.exit(3)
assert s.count(o)==1,(m,s.count(o))
open(sys.argv[1],'w',newline='').write(s.replace(o,n))
