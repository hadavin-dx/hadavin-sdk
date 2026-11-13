#!/bin/bash
SP=/tmp/claude-0/-home-user-hadavin-sdk/3c7954a2-a1b2-5867-97dd-d4d94c9e06fd/scratchpad
w=$1; WT=/home/user/build/ER-pdbanner12-$w; PY=/home/user/build/wt/q8c1-b17fix/.venv/bin/python
cd $WT; export PYTHONPATH=$WT/src; mkdir -p $SP/raw/fb-$w
$PY -c 'import hadavin_sdk;print("sdk:",hadavin_sdk.__file__)' > $SP/raw/fb-$w/_sdk.txt
for f in test_mode_banner test_demo_only_guard test_demo_only_guard_ci test_banner_mutant_table test_changelog_numbers test_repo_rules test_scan_repo test_workflow_files_parse test_stage_names; do
 env -u GH_TOKEN -u GITHUB_TOKEN -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL timeout 400 $PY -m pytest tests/$f.py -q -p no:cacheprovider --no-header --tb=line -rf > $SP/raw/fb-$w/$f.txt 2>&1
 echo "$f: $(tail -1 $SP/raw/fb-$w/$f.txt)"
done
