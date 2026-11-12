# Thin wrapper: all checks live in hadavin_sdk.safe_reset. Dry run by default; pass --apply to delete.
# Usage: tools\reset.ps1 --config <file> [--apply]     (the interpreter is $env:HADAVIN_PYTHON, default python)
$ErrorActionPreference = 'Stop'
$py = if ($env:HADAVIN_PYTHON) { $env:HADAVIN_PYTHON } else { 'python' }
& $py -m hadavin_sdk.safe_reset @args
exit $LASTEXITCODE
