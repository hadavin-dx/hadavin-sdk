-- Money guard (step F-store, E11 M4): a runtime login cannot lower a booked spend amount, except by settling a hold.
-- The runtime login holds UPDATE on spend, spend_month and spend_reservations (reserve and settle move them), so the
-- grants alone cannot keep the promise that only `limits release-expired` takes back a booked amount. This BEFORE UPDATE
-- trigger does. What a runtime login MAY do: raise any amount; settle an OPEN hold below its reserved amount (the
-- counters then fall by exactly that difference, in the same transaction). What it may NOT do: lower reserved_usd,
-- lower or clear settled_usd, move closed_at of a closed row, or lower a counter by more than the holds it settled in
-- this transaction fell by, or below the sum of the booked amounts of the holds of that day (month). Only the OWNER of
-- hadavin_release_expired_spend passes: that function is SECURITY DEFINER, so inside its body current_user is its owner
-- and no login can imitate it (a setting such as `SET hadavin.release = on` is a switch the runtime throws itself, so
-- none is used; SET ROLE needs membership in the owner role). A superuser owner is not stopped: this guards the logins.
-- THIS IS A TRIPWIRE, NOT A WALL (E13, tickets/migrations-0009-0010-review-1.md, every item reproduced). It stops a plain
-- lowering UPDATE and a naive plant, and an accident of the store. It does NOT stop a runtime login that writes its own
-- SQL: (H1) a legal settle plus repeated lowering UPDATEs in one transaction (the allowed fall is not consumed, so any
-- plain add_spend charge of the day can be erased); (H2) a forged settled hold (INSERT of a row already settled, or
-- raising reserved_usd of a settled row in the same transaction); (L2) a login that is the owner of the release function
-- (migrate and runtime sharing one login, or a member of the owner role) has no guard at all. A counter also holds
-- charges that are no hold (add_spend); those are tied to no row.
-- OWNER FIRST (option B, tickets/F-money-definer.md): the owner check comes first and a login that is the function
-- owner returns NEW at once; the aggregate (reserved minus settled holds) is computed only for other logins, so the
-- per-row cost is one pg_proc lookup. Consequence: the definer functions (reserve, settle, expire, release) run as the
-- owner, so this trigger no longer protects against a bug INSIDE them. Until option B steps 4-6 ship the guard is a
-- tripwire. The honest sentence "the runtime login can neither lower a booked amount nor change a cap (it can still
-- read a cap, settle a hold it can name, add spend)" applies after step 4 (grants flipped: no UPDATE/INSERT for the
-- runtime on the money tables) and step 6 (caps in a table the runtime cannot write). Before step 4 the runtime could
-- also lower a booked amount through the reproduced bypasses above. The audit chain and the release function's own record are the
-- evidence. Drift: when a counter is already below the booked holds (applied_usd of the release shows it) a
-- legal settle that lowers it is refused (fail closed) until an operator repairs the counter.
-- Emergency switch-off (the OWNER, then switch it back on): ALTER TABLE spend DISABLE TRIGGER spend_money_guard; the
-- same for spend_month (spend_month_money_guard) and spend_reservations (spend_reservations_money_guard), later
-- ENABLE TRIGGER. The audit seq and checkpoint guards of 0009 are switched off the same way (audit_entries_seq_guard,
-- audit_checkpoints_seq_guard).
-- The trigger function is SECURITY INVOKER, finds the owner in the schema of the table (not through the search path),
-- and carries a placeholder pin that `migrate` re-pins to pg_catalog, <this schema>, pg_temp on every run.
CREATE OR REPLACE FUNCTION hadavin_money_guard() RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, pg_temp
AS $fn$
DECLARE
    release_owner NAME;
    allowed_fall NUMERIC;
    booked NUMERIC;
BEGIN
    -- owner first: the owner of the release function (inside the SECURITY DEFINER bodies, the definer functions and
    -- release) passes at once, the one pg_proc lookup is the whole per-row cost; the aggregates below run only for
    -- any other login
    SELECT pg_catalog.pg_get_userbyid(p.proowner) INTO release_owner
      FROM pg_catalog.pg_proc p
     WHERE p.proname = 'hadavin_release_expired_spend'
       AND p.pronamespace = (SELECT c.relnamespace FROM pg_catalog.pg_class c WHERE c.oid = TG_RELID);
    IF release_owner IS NULL OR current_user::name IS DISTINCT FROM release_owner THEN
        IF TG_TABLE_NAME = 'spend_reservations' THEN
            IF NOT (NEW.reserved_usd < OLD.reserved_usd
                    OR (OLD.settled_usd IS NOT NULL AND (NEW.settled_usd IS NULL OR NEW.settled_usd < OLD.settled_usd))
                    OR (OLD.status <> 'open' AND NEW.closed_at IS DISTINCT FROM OLD.closed_at
                        AND NOT (OLD.status = 'expired' AND NEW.status = 'settled'))) THEN
                RETURN NEW;
            END IF;
        ELSIF NEW.usd >= OLD.usd THEN
            RETURN NEW;
        ELSE
            -- a counter falls only by the holds settled below their reserved amount in THIS transaction (a late
            -- settle never lowers a row), and never below the booked amounts of the holds
            IF TG_TABLE_NAME = 'spend' THEN
                SELECT COALESCE(sum(CASE WHEN r.status = 'settled' AND r.closed_at >= pg_catalog.transaction_timestamp()
                                          AND r.reserved_usd > r.settled_usd THEN r.reserved_usd - r.settled_usd ELSE 0 END), 0),
                       COALESCE(sum(CASE WHEN r.status = 'open' THEN r.reserved_usd ELSE r.settled_usd END), 0)
                  INTO allowed_fall, booked
                  FROM spend_reservations r WHERE r.agent_id = OLD.agent_id AND r.day = OLD.day;
            ELSE
                SELECT COALESCE(sum(CASE WHEN r.status = 'settled' AND r.closed_at >= pg_catalog.transaction_timestamp()
                                          AND r.reserved_usd > r.settled_usd THEN r.reserved_usd - r.settled_usd ELSE 0 END), 0),
                       COALESCE(sum(CASE WHEN r.status = 'open' THEN r.reserved_usd ELSE r.settled_usd END), 0)
                  INTO allowed_fall, booked
                  FROM spend_reservations r WHERE r.agent_id = OLD.agent_id
                   AND r.day >= OLD.month AND r.day < (OLD.month + INTERVAL '1 month')::date;
            END IF;
            IF OLD.usd - NEW.usd <= allowed_fall AND NEW.usd >= booked THEN
                RETURN NEW;
            END IF;
        END IF;
        RAISE EXCEPTION 'a booked spend amount may only go down through hadavin_release_expired_spend (%)', TG_TABLE_NAME
            USING ERRCODE = 'insufficient_privilege';
    END IF;
    RETURN NEW;
END
$fn$;
REVOKE ALL ON FUNCTION hadavin_money_guard() FROM PUBLIC;
DROP TRIGGER IF EXISTS spend_money_guard ON spend;
CREATE TRIGGER spend_money_guard BEFORE UPDATE ON spend
    FOR EACH ROW EXECUTE FUNCTION hadavin_money_guard();
DROP TRIGGER IF EXISTS spend_month_money_guard ON spend_month;
CREATE TRIGGER spend_month_money_guard BEFORE UPDATE ON spend_month
    FOR EACH ROW EXECUTE FUNCTION hadavin_money_guard();
DROP TRIGGER IF EXISTS spend_reservations_money_guard ON spend_reservations;
CREATE TRIGGER spend_reservations_money_guard BEFORE UPDATE ON spend_reservations
    FOR EACH ROW EXECUTE FUNCTION hadavin_money_guard();
-- the two aggregates of the guard (per agent and day, per agent and month range) filter on these columns
CREATE INDEX IF NOT EXISTS spend_reservations_agent_day ON spend_reservations (agent_id, day);
