import sys, time, psycopg
SOCK, PORT = sys.argv[1], sys.argv[2]
with psycopg.connect(f"host={SOCK} port={PORT} user=postgres dbname=postgres", autocommit=True) as c:
    for strategy in ("WAL_LOG", "FILE_COPY"):
        ts = []
        for i in range(10):
            t = time.perf_counter()
            c.execute(f"CREATE DATABASE cost_{i} TEMPLATE template0 STRATEGY {strategy}")
            c.execute(f"DROP DATABASE cost_{i} WITH (FORCE)")
            ts.append(time.perf_counter() - t)
        print(f"{strategy}: create+drop x10, median {sorted(ts)[5]*1000:.0f} ms, max {max(ts)*1000:.0f} ms (idle 16.15 cluster, no parallel load)")
