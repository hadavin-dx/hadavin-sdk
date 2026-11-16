"""Same logic as tests/test_s4_llm_guard.py::test_ids_and_plan_hashes_survive_redaction, N times, plus a per-id count.
usage: python flake-loop.py N   (PYTHONPATH picks the source tree: old or fixed)"""
import sys
import hadavin_sdk.approvals.gate as g
from hadavin_sdk.approvals.channel import clean
from hadavin_sdk.models import new_id, sha256_hex
N = int(sys.argv[1]); bad_iter = 0; bad_ids = 0
for _ in range(N):
    ids = [new_id(p) for p in ("run", "pln", "apr", "evt")]
    d = sha256_hex({"a": "b"})
    c = clean(" ".join(ids) + f" plan {d} short {d[:12]}")
    miss = [v for v in [*ids, d, d[:12]] if v not in c]
    bad_ids += sum(1 for v in miss if v in ids)
    bad_iter += bool(miss)
print("source", g.__file__)
print(f"iterations {N}: iterations with a missing id/hash {bad_iter}; ids missing {bad_ids} of {4 * N}")
