#!/bin/sh
# Thin wrapper: all checks live in hadavin_sdk.safe_reset. Dry run by default; pass --apply to delete.
# Usage: tools/reset.sh --config <file> [--apply]     (the interpreter is $HADAVIN_PYTHON, default python)
set -eu
exec "${HADAVIN_PYTHON:-python}" -m hadavin_sdk.safe_reset "$@"
