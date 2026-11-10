#!/bin/sh
# tree stamp: first 12 hex characters of the sha256 over src/**/*.py (sorted paths, contents), usage: stamp.sh <tree>
cd "$1" && find src -name '*.py' | sort | xargs cat | sha256sum | cut -c1-12
