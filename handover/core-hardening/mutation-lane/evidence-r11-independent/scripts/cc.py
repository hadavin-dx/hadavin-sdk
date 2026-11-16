import importlib.util, sys
spec = importlib.util.spec_from_file_location("runmod", sys.argv[1]); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
print("has check_child_call:", hasattr(r, "check_child_call"), "has Child:", hasattr(r, "Child"))
cases = {
 "ok (control)": (["/bin/true"], {}),
 "ok env allowed (control)": (["/bin/true"], {"env": {"PATH": "/bin", "HOME": "/", "LC_ALL": "C"}}),
 "shell=True with string": ("/bin/true", {"shell": True}),
 "shell=True with list": (["/bin/true"], {"shell": True}),
 "relative argv0": (["true"], {}),
 "relative ./true": (["./true"], {}),
 "executable=": (["/bin/true"], {"executable": "/bin/false"}),
 "preexec_fn=": (["/bin/true"], {"preexec_fn": lambda: None}),
 "extra env LD_PRELOAD": (["/bin/true"], {"env": {"PATH": "/bin", "LD_PRELOAD": "/x.so"}}),
 "extra env FOO": (["/bin/true"], {"env": {"PATH": "/bin", "FOO": "1"}}),
 "extra env BASH_ENV": (["/bin/true"], {"env": {"BASH_ENV": "/x"}}),
 "NUL in arg": (["/bin/true", "a\0b"], {}),
 "tuple args": (("/bin/true",), {}),
 "pass_fds": (["/bin/true"], {"pass_fds": (3,)}),
}
for name, (a, kw) in cases.items():
    for via in ("check_child_call", "Child"):
        f = getattr(r, "check_child_call", None) if via == "check_child_call" else None
        try:
            if via == "check_child_call":
                if f is None: print(f"ROW|{name}|{via}|NOT RUN (no such function)"); continue
                f(a, kw); print(f"ROW|{name}|{via}|ACCEPTED (no refusal)")
            else:
                C = getattr(r, "Child", None)
                if C is None: print(f"ROW|{name}|{via}|NOT RUN (no Child)"); continue
                p = C(a, **kw); p.wait(); print(f"ROW|{name}|{via}|STARTED (rc={p.returncode})")
        except r.Refused as e: print(f"ROW|{name}|{via}|REFUSED: {str(e)[:90]}")
        except Exception as e: print(f"ROW|{name}|{via}|OTHER {type(e).__name__}: {str(e)[:90]}")
