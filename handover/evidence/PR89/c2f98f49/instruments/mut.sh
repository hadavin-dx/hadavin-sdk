#!/bin/bash
. /home/user/build/ev-pr89r22-scripts/env.sh
cd $WT
echo "queued $(date -u +%FT%TZ)" > $RAW/mutants.times
$CLEAN /home/user/build/heavy.sh bash -c 'echo "start $(date -u +%FT%TZ)" >> '$RAW'/mutants.times; uv run --all-extras --group test python tests/mutation_runner_mutants.py > '$RAW'/mutants.log 2>&1; rc=$?; echo "mutants_rc=$rc" >> '$RAW'/mutants.times; echo "end $(date -u +%FT%TZ)" >> '$RAW'/mutants.times; exit $rc'
