import sys
w,m=sys.argv[1],sys.argv[2]
s=open(w,newline='').read()
E='echo "semgrep $('
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
"continue-on-error step":("        env:\n          RETRY","        continue-on-error: true\n        env:\n          RETRY"),
"continue-on-error job":("    runs-on: ubuntu-24.04","    runs-on: ubuntu-24.04\n    continue-on-error: true"),
"extra pack p/ci":("--config p/javascript src","--config p/javascript --config p/ci src"),
"self-hosted":("runs-on: ubuntu-24.04","runs-on: self-hosted"),
"metrics removed":("--metrics=off --disable-version-check --strict","--disable-version-check --strict"),
"folder tools dropped":("load_tools tools n8n &&","load_tools n8n &&"),
"job id-token write":("    runs-on: ubuntu-24.04","    runs-on: ubuntu-24.04\n    permissions:\n      id-token: write"),
"timeout 360":("timeout-minutes: 20 ","timeout-minutes: 360 "),
}
o,n=M[m]; assert s.count(o)==1,(m,s.count(o)); open(w,'w',newline='').write(s.replace(o,n))
