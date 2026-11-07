import sys; sys.path.insert(0, sys.argv[1])
from hadavin_sdk.k1b import redaction as r
for k in ["db_password", "db_pass​word", "DB_PASSWORD", "db_pasѕword", "db-pass**word**", "dbPassword", "db_pаssword"]:
    print(repr(k), r.sensitive(k))
