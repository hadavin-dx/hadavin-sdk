import sys
w,m=sys.argv[1],sys.argv[2]
s=open(w,newline='').read()
N="\n"
E='echo "semgrep $('
job="    runs-on: ubuntu-24.04"; senv="        env:\n          RETRY"; tail="--config p/javascript src"; setup='python-version: "3.12"'
inst="      - name: Install Semgrep (pinned version, hashes are checked)"; last='exit "$status"\n'
M={
"persist-credentials true":("persist-credentials: false","persist-credentials: true"),
"PR title in run":(E,'echo "${{ github.event.pull_request.title }} $('),
"head_ref in run":(E,'echo "${{ github.head_ref }} $('),
"ref_name in run":(E,'echo "${{ github.ref_name }} $('),
"base_ref in run":(E,'echo "${{ github.base_ref }} $('),
"strict removed":("--disable-version-check --strict --error","--disable-version-check --error"),
"severity WARNING":("--severity ERROR --config","--severity WARNING --config"),
"retry also on exit 1":('if [[ "$status" -ne 2 ]]; then break; fi','if [[ "$status" -ne 2 && "$status" -ne 1 ]]; then break; fi'),
"GITHUB_TOKEN env":('RETRY_PAUSE_SECONDS: "20"','RETRY_PAUSE_SECONDS: "20"\n          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}'),
"no-deps removed":("--only-binary=:all: --no-deps -r","--only-binary=:all: -r"),
"continue-on-error step":(senv,"        continue-on-error: true\n"+senv),
"continue-on-error job":(job,job+"\n    continue-on-error: true"),
"extra pack p/ci":(tail,"--config p/javascript --config p/ci src"),
"self-hosted":("runs-on: ubuntu-24.04","runs-on: self-hosted"),
"metrics removed":("--metrics=off --disable-version-check --strict","--disable-version-check --strict"),
"folder tools dropped":("load_tools tools n8n &&","load_tools n8n &&"),
"job id-token write":(job,job+"\n    permissions:\n      id-token: write"),
"timeout 360":("timeout-minutes: 20 ","timeout-minutes: 360 "),
# reader's 21 (REVIEW-semgrep-v9-fresh.md)
"R1 step if skips scan":(senv,"        if: github.event_name != 'pull_request'\n"+senv),
"R2 job if false":(job,job+"\n    if: false"),
"R3 extra action step":(inst,"      - uses: actions/cache@"+"0"*40+"\n\n"+inst),
"R4 --config=":(tail,"--config p/javascript --config=./other.yml src"),
"R5 --exclude=src":(tail,"--config p/javascript --exclude=src src"),
"R6 defaults shell sh":("permissions:\n  contents: read","defaults:\n  run:\n    shell: sh\n\npermissions:\n  contents: read"),
"R7 step shell sh":(senv,"        shell: sh\n"+senv),
"R8 matrix":(job,job+"\n    strategy:\n      matrix:\n        x: [1]"),
"R9 cache pip":(setup,setup+"\n          cache: pip"),
"R10 python 3.9":(setup,'python-version: "3.9"'),
"R11 working-directory":(senv,"        working-directory: tools\n"+senv),
"R12 job env":(job,job+"\n    env:\n      SEMGREP_RULES: p/ci"),
"R13 push dev":("  push:\n    branches: [main]","  push:\n    branches: [dev]"),
"R14 pr nothing":("  pull_request:\n    branches: [main]","  pull_request:\n    branches: [nothing]"),
"R15 install || true":('-r requirements-semgrep.txt"','-r requirements-semgrep.txt || true"'),
"R16 step timeout 1":(senv,"        timeout-minutes: 1\n"+senv),
"R17 container":(job,job+"\n    container: example/img:latest"),
"R18 workflow_dispatch":("on:\n  pull_request:","on:\n  workflow_dispatch:\n  pull_request:"),
"R19 -c file":(tail,"--config p/javascript -c ./other.yml src"),
"R20 second job needs":(last,last+"\n  second:\n    needs: semgrep\n    runs-on: ubuntu-24.04\n    steps:\n      - run: echo hi\n"),
"R21 --exclude-rule":(tail,"--config p/javascript --exclude-rule x src"),
}
if m=="LIST": print("\n".join(M)); sys.exit()
o,n=M[m]; assert s.count(o)==1,(m,s.count(o)); open(w,'w',newline='').write(s.replace(o,n))
