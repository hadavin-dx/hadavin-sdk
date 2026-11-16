#!/bin/bash
# usage: run.sh WT PY DSNDB(or -) LOG cmd...  ; unsets cloud env vars, prints HEAD first
wt=$1; py=$2; db=$3; log=$4; shift 4
cd $wt || exit 99
for v in $(env | cut -d= -f1 | grep -E '^(AWS_|ANTHROPIC_|AZURE_|GOOGLE_|GCP_|VAULT_|OPENAI_|GEMINI_|CLOUDSDK_|CI$|GH_TOKEN$|GITHUB_TOKEN$|HADAVIN_TEST_PG_DSN$)'); do unset $v; done
[ "$db" != "-" ] && export HADAVIN_TEST_PG_DSN="postgresql://postgres@127.0.0.1:5432/$db"
export UV_PROJECT_ENVIRONMENT=$wt/.venv-$py UV_PYTHON=$py
[ -n "$EXTRA_CI" ] && export CI=true
echo "HEAD=$(git rev-parse HEAD) py=$py dsn=${HADAVIN_TEST_PG_DSN:+set}${HADAVIN_TEST_PG_DSN:-unset} CI=${CI:-unset}"
echo "unset: AWS_ ANTHROPIC_ AZURE_ GOOGLE_ GCP_ VAULT_ OPENAI_ GEMINI_ CLOUDSDK_ CI GH_TOKEN GITHUB_TOKEN HADAVIN_TEST_PG_DSN (then set DSN if given)"
"$@"
