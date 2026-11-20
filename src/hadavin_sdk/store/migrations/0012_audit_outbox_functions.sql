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
-- it must not be empty. A row already under the prefix is not renamed again. When the target name is taken (the same
-- event was parked and quarantined before) the row goes to the first free name p_prefix || p_event_id || '#' || n
-- (n = 1 to 1000), so a repeat converges; but when a row at a candidate name holds an IDENTICAL body, the NEW row is
-- deleted (it is a duplicate: nothing is lost). The function never deletes a row it did not look at as the new row, and
-- never replaces one: a runtime-inserted row named p_prefix || X cannot be used to delete X unless it holds X's own
-- body. Returns rows renamed or removed as duplicates (0 or 1; 0 also when 1000 names are taken).
CREATE OR REPLACE FUNCTION hadavin_audit_outbox_quarantine(p_event_id TEXT, p_prefix TEXT)
RETURNS integer
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $fn$
DECLARE
    v_body TEXT;
    v_cand TEXT;
    v_other TEXT;
    v_i integer;
BEGIN
    IF p_event_id IS NULL OR pg_catalog.char_length(p_event_id) = 0 THEN
        RAISE EXCEPTION 'invalid argument p_event_id' USING ERRCODE = '22023';
    END IF;
    IF p_prefix IS NULL OR pg_catalog.char_length(p_prefix) = 0 THEN
        RAISE EXCEPTION 'invalid argument p_prefix' USING ERRCODE = '22023';
    END IF;
    SELECT o.body INTO v_body FROM audit_outbox o
     WHERE o.event_id = p_event_id
       AND pg_catalog.left(o.event_id, pg_catalog.char_length(p_prefix)) <> p_prefix
       FOR UPDATE;
    IF NOT FOUND THEN
        RETURN 0;
    END IF;
    FOR v_i IN 0..1000 LOOP
        v_cand := p_prefix || p_event_id || CASE WHEN v_i = 0 THEN '' ELSE '#' || v_i::text END;
        SELECT x.body INTO v_other FROM audit_outbox x WHERE x.event_id = v_cand;
        IF NOT FOUND THEN
            UPDATE audit_outbox o SET event_id = v_cand WHERE o.event_id = p_event_id;
            RETURN 1;
        ELSIF v_other = v_body THEN
            DELETE FROM audit_outbox o WHERE o.event_id = p_event_id;  -- the NEW row, an exact duplicate
            RETURN 1;
        END IF;
    END LOOP;
    RETURN 0;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_audit_outbox_quarantine(TEXT, TEXT) FROM PUBLIC;
