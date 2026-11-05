CREATE SCHEMA
SET
psql:/tmp/r67.sql:2: NOTICE:  table "t" does not exist, skipping
psql:/tmp/r67.sql:2: NOTICE:  table "led" does not exist, skipping
DROP TABLE
CREATE TABLE
BEGIN
CREATE TABLE
psql:/tmp/r67.sql:5: ERROR:  relation "nosuch" does not exist
psql:/tmp/r67.sql:6: ERROR:  current transaction is aborted, commands ignored until end of transaction block
ROLLBACK
 ?column? | count 
----------+-------
 led rows |     0
(1 row)

 ?column? | to_regclass 
----------+-------------
 table t  | 
(1 row)

--- no ON_ERROR_STOP; server 16 at /tmp/pgprobe, probe file /tmp/r67.sql above
