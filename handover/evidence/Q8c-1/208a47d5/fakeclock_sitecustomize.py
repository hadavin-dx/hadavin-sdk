"""Evidence shim: when FAKE_TODAY=YYYY-MM-DD is set, tools.policy_page.datetime.now() returns that day 12:00 UTC (module attribute replaced by a subclass after import)."""
import os, sys, datetime as _d, importlib.abc, importlib.machinery

_day = os.environ.get("FAKE_TODAY")
if _day:
    y, m, dd = map(int, _day.split("-"))
    FAKE = _d.datetime(y, m, dd, 12, 0, tzinfo=_d.UTC)

    class _FakeDT(_d.datetime):
        @classmethod
        def now(cls, tz=None):
            return FAKE if tz is None else FAKE.astimezone(tz)

    class _Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path, target=None):
            if name != "tools.policy_page":
                return None
            sys.meta_path.remove(self)
            try:
                spec = importlib.util.find_spec(name)
            finally:
                sys.meta_path.insert(0, self)
            if spec is None:
                return None
            orig = spec.loader
            class _L(importlib.abc.Loader):
                def create_module(self, s):
                    return orig.create_module(s)
                def exec_module(self, mod):
                    orig.exec_module(mod)
                    mod.datetime = _FakeDT
                    print(f"[fake-clock] tools.policy_page.datetime patched to {FAKE.isoformat()} ({mod.__file__})", file=sys.stderr)
            spec.loader = _L()
            return spec
    import importlib.util
    if os.environ.get('FAKE_GLOBAL') == '1':
        _d.datetime = _FakeDT
        print(f'[fake-clock] datetime.datetime replaced globally, now() = {FAKE.isoformat()}', file=sys.stderr)
    else:
        sys.meta_path.insert(0, _Finder())
