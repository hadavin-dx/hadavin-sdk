"""EVIDENCE RUNNER: build(demo, timeout_s=x) on whatever code the current worktree holds; records the refusal text or what was built.
Values: TIMEOUT_REFUSED and the accepted list of the head's tests/test_q8a_live_overrides.py, typed in again here."""
import sys, tempfile
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import hadavin_sdk
from hadavin_sdk import app as app_mod
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.config import load_config
from hadavin_sdk.registry import load_registry
from tests.conftest import make_cfg, qualify
base = Path(tempfile.mkdtemp(prefix="q8a1c-tb-", dir=sys.argv[1]))
print("code under test:", hadavin_sdk.__file__)
vals = [0, 0.0, -1, -0.5, True, False, float("nan"), float("inf"), "5", [5], Decimal("2.5"), Fraction(5, 2), 10**400, 3601, 3600.1,
        3, 0.001, 2.5, 3600, 3600.0, 1e-9, 5e-324]
for i, v in enumerate(vals):
    d = base / f"t{i}"; d.mkdir()
    cfg = make_cfg(d); qualify(load_registry(load_config(cfg)))
    label = repr(v) if len(repr(v)) < 30 else "10**400"
    try:
        a = app_mod.build(cfg, ["test-agent"], secrets=FakeSecretProvider({"fixture-token": "tok" + "-ev"}), timeout_s=v)
        print(f"timeout_s={label} -> no exception; executor.timeout_s={str(getattr(a.executor, 'timeout_s', 'n/a'))[:40]!r}")
    except BaseException as e:
        print(f"timeout_s={label} -> {type(e).__name__}: {str(e)[:300]}")
