# P2a r6 probes (PG16, scratch, made-up names). Orchestrator ran; no judgement.
## 1. are the role timeouts USERSET (R6-1)
idle_in_transaction_session_timeout|user
lock_timeout|user
statement_timeout|user
NOTICE:  role "p2a_rt" does not exist, skipping
DROP ROLE
CREATE ROLE
ALTER ROLE
-- as p2a_rt: show, then SET to 0, then show
 idle_in_transaction_session_timeout 
-------------------------------------
 1s
(1 row)

SET
 idle_in_transaction_session_timeout 
-------------------------------------
 0
(1 row)

SET
SET
 statement_timeout 
-------------------
 0
(1 row)

 lock_timeout 
--------------
 0
(1 row)

## 2. UPDATE ... WHERE NOT on, row locked by another session, qual false on visible tuple (R6-6)
psql:/tmp/p2a_u.sql:2: NOTICE:  table "ks" does not exist, skipping
SET
UPDATE 0
elapsed seconds: 0.02  (holder holds 4 s; ~0 means no wait)
