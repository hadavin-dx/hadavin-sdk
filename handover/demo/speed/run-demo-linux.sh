#!/bin/bash
# demo repo, Linux, no docker. Usage (from an EMPTY work folder):  bash run-demo-linux.sh serial|par  RUN_NUMBER  [WORKERS=3]
# Needs: python3.12, git, curl, github + pypi reachable. Playwright is NOT installed (same as the real hosted CI: ~119 browser tests skip; that is the baseline).
# Writes everything under ./out/<mode><run>/ ; the tree is cloned ONCE into ./dpld (b29bb1f + ci-xdist-demo-b29bb1f.patch + fake-hubspot-read-body-before-answer.patch if present).
set -u
MODE=${1:?serial|par}; RUN=${2:?run number}; NW=${3:-3}
HERE=$(cd "$(dirname "$0")" && pwd); W=$PWD; O=$W/out/$MODE$RUN; mkdir -p "$O"
export PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1
if [ ! -d "$W/dpld" ]; then
  git clone -q https://github.com/hadavin-dx/duplicate-proof-lead-desk-n8n "$W/dpld" || exit 2
  cd "$W/dpld" && git checkout -q b29bb1f && git apply "$HERE/ci-xdist-demo-b29bb1f.patch" || exit 2
  [ -f "$HERE/fake-hubspot-read-body-before-answer.patch" ] && { git apply "$HERE/fake-hubspot-read-body-before-answer.patch" || exit 2; }
  python3.12 -m venv "$W/venv" && . "$W/venv/bin/activate" && pip install --require-hashes -r requirements-dev.txt > "$W/out/pip.txt" 2>&1 || exit 2
  GV=8.30.1; GS=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
  (cd /tmp && curl -sSfL -o gl.tgz "https://github.com/gitleaks/gitleaks/releases/download/v$GV/gitleaks_${GV}_linux_x64.tar.gz" && echo "$GS  gl.tgz" | sha256sum --check - && mkdir -p "$W/gl" && tar -xzf gl.tgz -C "$W/gl" gitleaks) || exit 2
fi
cd "$W/dpld" && . "$W/venv/bin/activate"
bash "$HERE/quiet-check.sh" "$O/quiet-before.txt" || exit 3
export PYTHONPATH=src:. DPLD_REQUIRE_DEMO=1 DPLD_REQUIRE_SCAN=1 GITLEAKS_BIN=$W/gl/gitleaks
ARGS=""; if [ "$MODE" = par ]; then export PYTHONHASHSEED=0; ARGS="-n $NW --dist loadgroup"; fi
git rev-parse HEAD > "$O/head.txt"; git diff | sha256sum > "$O/patch-hash.txt"; python --version > "$O/versions.txt"; nproc >> "$O/versions.txt"
S=$(date +%s)
/usr/bin/time -v -o "$O/time.txt" timeout 2700 python -m pytest -q -p no:cacheprovider -rA $ARGS --junitxml="$O/junit.xml" > "$O/pytest.txt" 2>&1
echo "exit=$? secs=$(( $(date +%s)-S ))" | tee "$O/result.txt"; tail -1 "$O/pytest.txt" >> "$O/result.txt"
