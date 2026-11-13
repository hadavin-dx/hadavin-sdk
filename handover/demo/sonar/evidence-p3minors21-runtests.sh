#!/bin/bash
# usage: runtests.sh <tree-dir> <logname> [extra pytest args]  -- all under unshare -rn + loopback up + connect blocker
export PATH=/tmp/work/gl:$PATH DPLD_REQUIRE_SCAN=1 GITLEAKS_BIN=/tmp/work/gl/gitleaks
T="tests/test_path_confinement.py tests/test_hygiene.py tests/test_gitleaks_exceptions.py tests/test_codeant_hygiene.py tests/test_load_tools.py tests/test_scrub_n8n_export.py tests/test_n8n_api_url.py tests/test_real_check_dry.py tests/test_env_numbers.py tests/test_no_placeholders.py tests/test_sonar_p2_gaps.py tests/test_sonar_p2_feed_optional.py tests/test_sonar_p2_regex_optional.py"
D=$1; L=$2; shift 2
if [ $# -gt 0 ]; then ARGS=("$@"); else ARGS=($T); fi
cd $D; git add -A >/dev/null 2>&1
rm -f /tmp/work/sn-v21/net-$L.log
RV_LOG=/tmp/work/sn-v21/net-$L.log PYTHONPATH=/tmp/work/rv39-1/sc unshare -rn python3 /tmp/demo-push/handover/demo/real-run/lo_up-q4g.py /tmp/work/venv-p3/bin/python -m pytest -q -p no:cacheprovider "${ARGS[@]}" 2>&1 | tail -15
echo "net: $(awk '{print $3,$NF}' /tmp/work/sn-v21/net-$L.log 2>/dev/null | sort | uniq -c | tr '\n' ';')"
