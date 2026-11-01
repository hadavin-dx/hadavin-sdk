-- Ask-your-data demo: the read-only login. Applied by an ADMIN (never by the app), once per database.
--
--   psql -d <db> -f roles.sql -v confirm_dedicated=yes -v ro_password=<password> \
--        -v ro_connection_limit=N -v ro_statement_timeout=Ns -v ro_lock_timeout=Ns -v ro_idle_timeout=Ns
--   (the numbers are required; the documented values are in askdata/settings.py, class Runtime)
--
-- WARNING: REVOKE ... FROM PUBLIC changes access for EVERY login role in this database. Run it on a dedicated
-- database or a read replica, never on a shared production database. It first runs preflight_roles.sql and stops
-- (exit 3) when other logins would lose access, unless you also pass -v accept_loss=yes.
-- Optional: -v ro_role=<name> (default askdata_ro). Without ro_password the login has no password: set one with
-- \password. (A password given with -v can end up in server logs when log_statement=all; prefer \password.)
\set ON_ERROR_STOP on
\if :{?confirm_dedicated}
\else
  \set confirm_dedicated no
\endif
\if :{?accept_loss}
\else
  \set accept_loss no
\endif
\if :{?ro_role}
\else
  \set ro_role askdata_ro
\endif

SELECT (:'confirm_dedicated' = 'yes') AS dedicated \gset
\if :dedicated
\else
  SELECT 'refusing: pass -v confirm_dedicated=yes (dedicated database or replica only)'::int;
\endif

\ir preflight_roles.sql

-- The numbers come from the caller (the CLI passes them from askdata/settings.py Runtime); this script has none.
\if :{?ro_connection_limit}
\else
  SELECT 'refusing: pass -v ro_connection_limit=N -v ro_statement_timeout=Ns -v ro_lock_timeout=Ns -v ro_idle_timeout=Ns'::int;
\endif
\if :{?ro_statement_timeout}
\else
  SELECT 'refusing: pass -v ro_statement_timeout=Ns'::int;
\endif
\if :{?ro_lock_timeout}
\else
  SELECT 'refusing: pass -v ro_lock_timeout=Ns'::int;
\endif
\if :{?ro_idle_timeout}
\else
  SELECT 'refusing: pass -v ro_idle_timeout=Ns'::int;
\endif
-- A value from the command line is checked before it is used: a whole number, in range; a timeout is a positive
-- number of seconds (a '0s' timeout would DISABLE the limit, so it is refused).
SELECT (:'ro_connection_limit' ~ '^[0-9]{1,3}$') AS ok_cl_shape \gset
\if :ok_cl_shape
\else
  SELECT 'refusing: ro_connection_limit must be a whole number from 1 to 999'::int;
\endif
SELECT (:'ro_connection_limit')::int AS cl \gset
SELECT (:cl BETWEEN 1 AND 999) AS ok_cl_range \gset
\if :ok_cl_range
\else
  SELECT 'refusing: ro_connection_limit must be from 1 to 999'::int;
\endif
SELECT (:'ro_statement_timeout' ~ '^[1-9][0-9]{0,4}s$'
        AND :'ro_lock_timeout' ~ '^[1-9][0-9]{0,4}s$'
        AND :'ro_idle_timeout' ~ '^[1-9][0-9]{0,4}s$') AS ok_timeouts \gset
\if :ok_timeouts
\else
  SELECT 'refusing: each timeout must be a positive whole number of seconds like 15s (0s would disable it)'::int;
\endif
SELECT (:'accept_loss' = 'yes') AS accepted \gset
\if :has_loss
  \if :accepted
  \else
    SELECT 'refusing: other logins would lose access (listed above); review, then pass -v accept_loss=yes'::int;
  \endif
\endif

SELECT current_database() AS dbname \gset

BEGIN;  -- all or nothing: a failure leaves no half-made login behind

CREATE ROLE :"ro_role" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS CONNECTION LIMIT :cl;
\if :{?ro_password}
  ALTER ROLE :"ro_role" PASSWORD :'ro_password';
\endif

REVOKE ALL ON DATABASE :"dbname" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"dbname" TO :"ro_role";
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA shop FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA shop FROM PUBLIC;
REVOKE ALL ON SCHEMA analytics FROM PUBLIC;
GRANT USAGE ON SCHEMA analytics TO :"ro_role";
GRANT SELECT ON analytics.customers_v, analytics.products_v, analytics.orders_v, analytics.order_items_v
    TO :"ro_role";
-- Functions created later by this admin are not PUBLIC-executable. (Existing pg_catalog functions such as
-- pg_sleep stay executable by PUBLIC: the watchdog and the validator bound them, not this script.)
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- Defaults only: a session can change them. The revoked privileges above are what hold.
ALTER ROLE :"ro_role" IN DATABASE :"dbname" SET default_transaction_read_only = on;
ALTER ROLE :"ro_role" IN DATABASE :"dbname" SET statement_timeout = :'ro_statement_timeout';
ALTER ROLE :"ro_role" IN DATABASE :"dbname" SET lock_timeout = :'ro_lock_timeout';
ALTER ROLE :"ro_role" IN DATABASE :"dbname" SET idle_in_transaction_session_timeout = :'ro_idle_timeout';
ALTER ROLE :"ro_role" IN DATABASE :"dbname" SET search_path = analytics;
COMMIT;
\echo roles.sql: done
