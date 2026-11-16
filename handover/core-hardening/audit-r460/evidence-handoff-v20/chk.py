import sys, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import secdef_guard_v20 as g
import allow_v20 as A
for f in sorted(glob.glob("held-sql/*.sql")) + sorted(glob.glob("/home/user/hadavin-sdk/src/hadavin_sdk/store/migrations/*.sql")):
    b = os.path.basename(f)
    print(b, A.check(g, b, open(f).read()))
