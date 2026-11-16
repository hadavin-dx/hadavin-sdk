\pset pager off
\echo == setup: one object of each relation kind plus types in schema app2
CREATE SCHEMA app2;
CREATE TABLE app2.tab (i int);
CREATE TABLE app2.part (i int) PARTITION BY RANGE (i);
CREATE TABLE app2.part_1 PARTITION OF app2.part FOR VALUES FROM (0) TO (10);
CREATE VIEW app2.v AS SELECT 1 AS x;
CREATE MATERIALIZED VIEW app2.mv AS SELECT 1 AS x;
CREATE SEQUENCE app2.seq;
CREATE FOREIGN DATA WRAPPER dummy_fdw; CREATE SERVER dummy_srv FOREIGN DATA WRAPPER dummy_fdw;
CREATE FOREIGN TABLE app2.ft (i int) SERVER dummy_srv;
CREATE TYPE app2.comp AS (a int, b text);
CREATE TYPE app2.en AS ENUM ('x','y');
CREATE TYPE app2.rng AS RANGE (subtype = int4);
CREATE DOMAIN app2.dom AS int;
\echo == (b1) pg_type rows in app2 with the relation they belong to, typacl and the default for everyone
SELECT t.typname, t.typtype, t.typrelid <> 0 AS has_rel, c.relkind, (t.typelem <> 0 AND t.typcategory = 'A') AS is_array,
       t.typacl, pg_catalog.acldefault('T', t.typowner) AS default_acl
  FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace LEFT JOIN pg_class c ON c.oid = t.typrelid
 WHERE n.nspname = 'app2' ORDER BY has_rel DESC, c.relkind, t.typname;
\echo == (b2) relations in app2 with reltype = 0 (no row type)
SELECT relname, relkind, reltype FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='app2' ORDER BY relkind, relname;
\echo == (b3) the row-type key the errata uses: typtype = 'c' AND typrelid <> 0 AND relkind <> 'c'
SELECT t.typname, c.relkind FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace JOIN pg_class c ON c.oid = t.typrelid
 WHERE n.nspname = 'app2' AND t.typtype = 'c' AND c.relkind <> 'c' ORDER BY 1;
\echo == (b4) a GRANT on a row type materialises typacl with the everyone entry next to it
CREATE ROLE rt2;
GRANT USAGE ON TYPE app2.tab TO rt2;
SELECT typname, typacl FROM pg_type WHERE typname = 'tab' AND typnamespace = 'app2'::regnamespace;
\echo == (b5) a GRANT on a standalone composite type and on a sequence row type
GRANT USAGE ON TYPE app2.comp TO rt2;
SELECT typname, typacl FROM pg_type WHERE typname IN ('comp') AND typnamespace = 'app2'::regnamespace;
GRANT USAGE ON TYPE app2.seq TO rt2;
\echo == (b6) every pg_type with typacl NULL defaults to USAGE for everyone (any typtype)
SELECT DISTINCT typtype, pg_catalog.acldefault('T', typowner) FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE n.nspname='app2' ORDER BY 1;
