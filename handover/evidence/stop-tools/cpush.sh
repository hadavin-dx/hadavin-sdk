#!/bin/bash
# commit handover (summaries only: no junit/xml, no raw logs), gitleaks gate, push
cd /home/user/hadavin-sdk || exit 1
rm -rf .git/rebase-merge
git add -A handover ':!handover/**/junit/**' ':!handover/**/*.xml' ':!handover/evidence/**/raw/**' 2>/dev/null
git commit -q -m "${1:-Handover update}" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014pRo36xK6rXQgBKwtTHfac"
if /home/user/build/bin/gitleaks git --redact --no-banner --exit-code 1 --config .gitleaks.toml --log-opts="-1" . >/dev/null 2>&1; then
  for i in 1 2 3; do git pull -q --rebase --autostash origin core/cloud-handover && git push -q origin HEAD:core/cloud-handover && echo pushed && break; rm -rf .git/rebase-merge; done
else echo GITLEAKS_FAIL_NOT_PUSHED; fi
