RR="scripts/run_real_check.py"; BR="demo_only/bad_request.py"; SUP="tests/support.py"
A=["tests/test_r7t_findings.py","tests/test_r7s_findings.py"]
muts=[
("R07",BR,'isinstance(sys.exception(), CLIENT_GONE)','not isinstance(sys.exception(), CLIENT_GONE)',A),
("R10",RR,'return max(0, (created or 0) - accounted)','return max(0, (created or 1) - accounted)',A),
("R19",RR,'run_dir.glob(f"desk-{tag}-*{suffix}")','run_dir.glob(f"desk-{tag}*{suffix}")',A),
("R20",RR,'run_dir.glob(f"desk-{tag}-*{suffix}")','run_dir.glob(f"desk-{tag}-*")',A),
("R27",RR,'return exit_code_of(result["ok"], written, left, unseen)','return exit_code_of(result["ok"], True, left, unseen)',A),
("R39",SUP,'    if os.environ.get(REQUIRE_SCAN_ENV):','    if os.environ.get(REQUIRE_SCAN_ENV) == "1":',A),
]
