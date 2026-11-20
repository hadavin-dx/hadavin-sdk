-- Audit outbox functions (ticket A-audit-rights, review 1 section 2). The runtime login loses DELETE on audit_outbox;
-- a parked event leaves the outbox only through the two SECURITY DEFINER functions below, so the DATABASE enforces
-- "an event is dropped from the outbox only once it is in the chain, or is renamed and kept". THE WALL IS BUILT BY
-- `migrate`, NOT BY THIS FILE ALONE: `migrate --runtime-role` grants the runtime SELECT and INSERT on audit_outbox (no
-- DELETE, no UPDATE) and EXECUTE on these two functions; every other role and PUBLIC lose EXECUTE.
--
-- Rules (the same as 0011): SECURITY DEFINER, VOLATILE, NOT STRICT (a NULL is an explicit error), no EXCEPTION block, no
-- dynamic SQL. Placeholder pin `SET search_path = pg_catalog, pg_temp`: `migrate` re-pins both to
-- pg_catalog, <this schema>, pg_temp on every run (pg_temp stays LAST). Owner: whoever runs `migrate` (the owner of the
-- audit tables and of the hadavin_* functions, checked by `migrate`).
-- HONEST RESIDUAL: the runtime can still INSERT any row into the outbox and rename (quarantine) any parked row, which
-- hides it from the drain but loses nothing; it cannot delete a row whose event is not in audit_entries.

-- hadavin_audit_outbox_done: delete the parked event p_event_id, only when an audit_entries row with that event_id
-- exists. Returns the number of rows deleted (0 or 1).
CREATE OR REPLACE FUNCTION hadavin_audit_outbox_done(p_event_id TEXT)
RETURNS integer
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
DECLARE
    v_n integer;
BEGIN
    IF p_event_id IS NULL OR pg_catalog.char_length(p_event_id) = 0 THEN
        RAISE EXCEPTION 'invalid argument p_event_id' USING ERRCODE = '22023';
    END IF;
    DELETE FROM audit_outbox o
     WHERE o.event_id = p_event_id
       AND EXISTS (SELECT 1 FROM audit_entries e WHERE e.event_id = p_event_id);
    GET DIAGNOSTICS v_n = ROW_COUNT;
    RETURN v_n;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_audit_outbox_done(TEXT) FROM PUBLIC;

-- hadavin_audit_outbox_quarantine: mark a poison row by RENAMING it to p_prefix || p_event_id (nothing is lost; the row
-- stays and every later drain read skips it). The prefix is an argument so the package default stays the one source, but
-- it must not be empty. A row already under the prefix is not renamed again, and a rename onto an existing row is
-- refused (returns 0): a rename can never replace, hence never remove, another parked event. Returns rows renamed.
CREATE OR REPLACE FUNCTION hadavin_audit_outbox_quarantine(p_event_id TEXT, p_prefix TEXT)
RETURNS integer
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
DECLARE
    v_n integer;
BEGIN
    IF p_event_id IS NULL OR pg_catalog.char_length(p_event_id) = 0 THEN
        RAISE EXCEPTION 'invalid argument p_event_id' USING ERRCODE = '22023';
    END IF;
    IF p_prefix IS NULL OR pg_catalog.char_length(p_prefix) = 0 THEN
        RAISE EXCEPTION 'invalid argument p_prefix' USING ERRCODE = '22023';
    END IF;
    UPDATE audit_outbox o
       SET event_id = p_prefix || o.event_id
     WHERE o.event_id = p_event_id
       AND pg_catalog.left(o.event_id, pg_catalog.char_length(p_prefix)) <> p_prefix
       AND NOT EXISTS (SELECT 1 FROM audit_outbox x WHERE x.event_id = p_prefix || p_event_id);
    GET DIAGNOSTICS v_n = ROW_COUNT;
    RETURN v_n;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_audit_outbox_quarantine(TEXT, TEXT) FROM PUBLIC;
