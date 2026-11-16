import sys, glob, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import secdef_guard_v20 as g
from allow_v20 import ALLOWED_BY_FILE as A, ATOMIC_TABLES_BY_FILE as T, EXTRA_BY_FILE as X
for f in sorted(glob.glob("held-sql/*.sql")) + sorted(glob.glob("/home/user/hadavin-sdk/src/hadavin_sdk/store/migrations/*.sql")):
    b = os.path.basename(f)
    print(b, g.check_sql_text(b, open(f).read(), A.get(b, {}), extra_statements=X.get(b, ()), atomic_tables=T.get(b)))
