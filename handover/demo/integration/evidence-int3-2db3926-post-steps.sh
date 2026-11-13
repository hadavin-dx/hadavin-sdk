#!/bin/bash
# resumable post-chunk steps on /tmp/work/h3 (pr-3-tests 2db3926); each step writes /tmp/work/h3post-<n>.txt and h3post-<n>.exit; finished steps are skipped
cd /tmp/work/h3 || exit 1
export PATH=/opt/node22/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers GITLEAKS_BIN=/tmp/work/gl/gitleaks DPLD_REQUIRE_SCAN=1 PYTHONUNBUFFERED=1
V=/tmp/work/int2-venv/bin
step() { n=$1; shift; [ -f /tmp/work/h3post-$n.exit ] && return; { echo "# $*"; date -u +%FT%TZ; } > /tmp/work/h3post-$n.txt; ( "$@" ) >> /tmp/work/h3post-$n.txt 2>&1; echo "exit=$?" > /tmp/work/h3post-$n.exit; }
step 1-ruff-check $V/ruff check .
step 2-ruff-format $V/ruff format --check .
step 3-mypy-linux $V/mypy --platform linux
step 4-mypy-win32 $V/mypy --platform win32
step 5-bandit $V/bandit -ll -q -r src tools scripts
step 6-hygiene-gitleaks $V/python -u -m pytest -q -p no:cacheprovider -rs tests/test_hygiene.py tests/test_gitleaks_exceptions.py
step 7-gitleaks-dir bash -c 'rm -rf /tmp/work/h3arch && mkdir /tmp/work/h3arch && git -C /tmp/work/h3 archive HEAD | tar -x -C /tmp/work/h3arch && cd /tmp/work/h3arch && /tmp/work/gl/gitleaks dir . --no-banner 2>&1 | tail -5'
step 8-gitleaks-git bash -c 'cd /tmp/work/h3 && /tmp/work/gl/gitleaks git . --no-banner 2>&1 | tail -5'
for i in 1 2 3 4 5; do step 9-restart-test-$i $V/python -u -m pytest -q -p no:cacheprovider --durations=3 "tests/test_portal_api.py::test_restart_same_port_portal_open"; done
step 10-nodeoff env PATH=/usr/bin:/bin $V/python -u -m pytest -q -p no:cacheprovider -rs tests/test_mode_safety.py tests/test_portal_browser.py tests/test_portal_lead_pages.py tests/test_portal_mode.py tests/test_portal_wording_and_masking.py tests/test_portal_layout.py tests/test_portal_look.py tests/test_stage_confirm_browser.py
echo done > /tmp/work/h3post.done
