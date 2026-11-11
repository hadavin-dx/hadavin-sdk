"""EVIDENCE shim (no behaviour): gives the missing names so the head tests can be collected on the old code. Each stub raises NotImplementedError when called."""
import hadavin_sdk.testing.mutation as m
import tools.mutation_runner as r

def _stub(name):
    def f(*a, **k):
        raise NotImplementedError(name)
    f.__name__ = name
    return f

for n in ("fixture_errors", "read_junit", "skipped_tests"):
    if not hasattr(m, n):
        setattr(m, n, _stub(n))
if not hasattr(r, "PASS_ENV_ALLOWED"):
    r.PASS_ENV_ALLOWED = frozenset()

class CanaryFailed(Exception):
    pass

if not hasattr(r, "CanaryFailed"):
    r.CanaryFailed = CanaryFailed
for n in ("_checked_env_names", "_fragment_spans", "_junit_text", "_masked", "_one_run_per_database", "_plugin_module", "_secret_values", "_why_not_opened", "_lock_dir"):
    if not hasattr(r, n):
        setattr(r, n, _stub(n))
