# Fresh clone evidence (ORDER 019)
Written 2026-11-16 09:30 UTC. Evidence runner, no judging.
Clone: branch cloud/flows-audit, dir /tmp/fresh19/c, head sha 0c0715e25f1e70ee45b3cf91b51df8f77180a942
Cloud env vars (AWS_/AZURE_/GOOGLE_/GCP_) unset.

## Run 1: uv run --all-extras --group test pytest -x -q -p no:cacheprovider <T1> <T2> (rc=1, stopped after first failure so T2 did not run here)
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Using CPython 3.13.18 interpreter at: /usr/local/bin/python3
Creating virtual environment at: .venv
   Building hadavin-sdk @ file:///tmp/fresh19/c
Downloading moto (6.9MiB)
      Built hadavin-sdk @ file:///tmp/fresh19/c
 Downloaded moto
Installed 76 packages in 65ms
F
=================================== FAILURES ===================================
____________________ test_no_vendor_brand_string_is_tracked ____________________

    def test_no_vendor_brand_string_is_tracked():
        """Scan every text file (any suffix, e.g. .tsx/.svg); binary files are skipped; undecodable text FAILS."""
        bad = []
        for rel in _tracked():
            if rel in SELF:
                continue
            try:
                raw = (ROOT / rel).read_bytes()
            except OSError as exc:
                bad.append(f"{rel}: unreadable ({exc.__class__.__name__})")
                continue
            if b"\0" in raw:  # binary: covered by the hash test
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                bad.append(f"{rel}: not UTF-8 text, cannot be scanned for vendor strings")
                continue
            bad += [f"{rel}: {s!r}" for s in BANNED if s in text]
>       assert not bad, "vendor brand strings or unscannable files in the repo: " + "; ".join(bad)
E       AssertionError: vendor brand strings or unscannable files in the repo: handover/flows-audit/heavy-test-lane/SUMMARY.md: '[vendor-brand-string]'; handover/flows-audit/heavy-test-lane/evidence-baseline.md: '[vendor-brand-string]'; handover/flows-audit/heavy-test-lane/evidence-patched.md: '[vendor-brand-string]'
E       assert not ["handover/flows-audit/heavy-test-lane/SUMMARY.md: '[vendor-brand-string]'", "handover/flows-audit/heavy-test-lane/evidence-baseline.md: '[vendor-brand-string]'", "handover/flows-audit/heavy-test-lane/evidence-patched.md: '[vendor-brand-string]'"]

tests/test_no_reference_material.py:87: AssertionError
=========================== short test summary info ============================
FAILED tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed in 0.53s
rc1=1
```

## Run 2: T1 with -vv (rc=1)
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
============================= test session starts ==============================
platform linux -- Python 3.13.18, pytest-9.2.0, pluggy-1.7.0 -- /tmp/fresh19/c/.venv/bin/python
rootdir: /tmp/fresh19/c
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 1 item

tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked FAILED [100%]

=================================== FAILURES ===================================
____________________ test_no_vendor_brand_string_is_tracked ____________________

    def test_no_vendor_brand_string_is_tracked():
        """Scan every text file (any suffix, e.g. .tsx/.svg); binary files are skipped; undecodable text FAILS."""
        bad = []
        for rel in _tracked():
            if rel in SELF:
                continue
            try:
                raw = (ROOT / rel).read_bytes()
            except OSError as exc:
                bad.append(f"{rel}: unreadable ({exc.__class__.__name__})")
                continue
            if b"\0" in raw:  # binary: covered by the hash test
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                bad.append(f"{rel}: not UTF-8 text, cannot be scanned for vendor strings")
                continue
            bad += [f"{rel}: {s!r}" for s in BANNED if s in text]
>       assert not bad, "vendor brand strings or unscannable files in the repo: " + "; ".join(bad)
E       AssertionError: vendor brand strings or unscannable files in the repo: handover/flows-audit/heavy-test-lane/SUMMARY.md: '[vendor-brand-string]'; handover/flows-audit/heavy-test-lane/evidence-baseline.md: '[vendor-brand-string]'; handover/flows-audit/heavy-test-lane/evidence-patched.md: '[vendor-brand-string]'
E       assert not ["handover/flows-audit/heavy-test-lane/SUMMARY.md: '[vendor-brand-string]'", "handover/flows-audit/heavy-test-lane/evidence-baseline.md: '[vendor-brand-string]'", "handover/flows-audit/heavy-test-lane/evidence-patched.md: '[vendor-brand-string]'"]

tests/test_no_reference_material.py:87: AssertionError
=========================== short test summary info ============================
FAILED tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked - AssertionError: vendor brand strings or unscannable files in the repo: handover/flows-audit/heavy-test-lane/SUMMARY.md: '[vendor-brand-string]'; handover/flows-audit/heavy-test-lane/evidence-baseline.md: '[vendor-brand-string]'; handover/flows-audit/heavy-test-lane/evidence-patched.md: '[vendor-brand-string]'
assert not ["handover/flows-audit/heavy-test-lane/SUMMARY.md: '[vendor-brand-string]'", "handover/flows-audit/heavy-test-lane/evidence-baseline.md: '[vendor-brand-string]'", "handover/flows-audit/heavy-test-lane/evidence-patched.md: '[vendor-brand-string]'"]
============================== 1 failed in 0.46s ===============================
rc=1
```

## Run 3: T2 with -vv (rc=0)
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
============================= test session starts ==============================
platform linux -- Python 3.13.18, pytest-9.2.0, pluggy-1.7.0 -- /tmp/fresh19/c/.venv/bin/python
rootdir: /tmp/fresh19/c
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 1 item

tests/test_repo_rules.py::test_licences_are_proprietary PASSED           [100%]

============================== 1 passed in 0.07s ===============================
rc=0
```

## Offending file list (T1, raw)
handover/flows-audit/heavy-test-lane/SUMMARY.md: '[vendor-brand-string]'; evidence-baseline.md: '[vendor-brand-string]'; evidence-patched.md: '[vendor-brand-string]' (no line numbers: test reports file and string only)
T2: none; passed in this clone.
