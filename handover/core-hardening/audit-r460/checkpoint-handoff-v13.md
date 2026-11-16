# Checkpoint, hand-off v13 builder
Started 2026-11-16T15:18:33Z (first command). Stop and report at 60 minutes (about 16:18Z).
Plan: (1) read v12 + both reviews [done]; (2) run a throwaway Postgres 16 (installed locally) to settle B1, M1, M3 by experiment; (3) copy v12 to v13 and patch; (4) regenerate evidence scripts; (5) read citation check when it lands.
15:24Z: Postgres 16.15 server IS installed here; throwaway cluster experiments done (raw-pg-*-v13.txt, 47/47 real-code checks). B1 CONFIRMED by experiment. Next: patch v13 docs.
