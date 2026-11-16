import sys, glob, os
sys.path.insert(0,'.')
import secdef_guard_v18 as g
from allow_v18 import ALLOWED_BY_FILE as A
for f in sorted(glob.glob("held-sql/*.sql"))+sorted(glob.glob("/home/user/hadavin-sdk/src/hadavin_sdk/store/migrations/*.sql")):
    print(os.path.basename(f), g.check_sql_text(os.path.basename(f), open(f).read(), A.get(os.path.basename(f), {})))
