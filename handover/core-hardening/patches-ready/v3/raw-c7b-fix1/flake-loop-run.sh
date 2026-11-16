#!/bin/bash
# usage: flake-loop-run.sh <tree-src-dir> <N> ; uses the python of the fix tree venv
S=/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/f1
env -i PATH="$PATH" HOME="$HOME" PYTHONPATH="$1" $S/fix/.venv/bin/python -I -c "import sys; sys.path.insert(0,'$1'); exec(open('$S/raw/flake-loop.py').read())" "$2"
