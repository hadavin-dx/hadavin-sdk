"""Owner-only fixtures for the reservation table (ticket P4d, B7). The runtime login can neither INSERT a row with
an old `created_at` nor change one (the insert trigger sets the database clock, the update trigger freezes
`created_at`), so a test that needs an AGED reservation does it as the table owner: it switches the one trigger it
must pass off with `ALTER TABLE ... DISABLE TRIGGER`, inside one transaction, does the single change, and switches
the trigger on again before it commits. Only the owner may do this, and a failure inside the block rolls the
`DISABLE` back with everything else, so the trigger is never left off. (This replaces the earlier
`session_replication_role = replica`, which switches off EVERY trigger and foreign key check of the session and
needs a superuser.)"""

import contextlib
from datetime import date
from decimal import Decimal

from tests.contracts.kinds.store_postgres import pg_driver

drv = pg_driver(module_level=True)
_TRIGGERS = (
    "spend_reservations_insert",
    "spend_reservations_update",
)  # an allowlist, never caller text


@contextlib.contextmanager
def trigger_off(dsn, trigger):
    """Yield the owner connection (one transaction) with `trigger` of `spend_reservations` disabled."""
    if trigger not in _TRIGGERS:
        raise ValueError(f"unknown trigger {trigger!r}")
    with drv.connect_admin(dsn, autocommit=False) as conn:
        drv.execute(conn, f"ALTER TABLE spend_reservations DISABLE TRIGGER {trigger}")
        yield conn
        drv.execute(conn, f"ALTER TABLE spend_reservations ENABLE TRIGGER {trigger}")
        conn.commit()


def insert_aged(dsn, reservation_id, agent_id, day: date, amount: Decimal, age_s: int):
    """INSERT an open reservation whose `created_at` is `age_s` seconds old by the database clock, and book it on
    the day and month counters (as `reserve_spend` would), so the counters stay equal to the open reservations.
    Several ids may be given as a list: they share ONE `created_at` (ties for the sweep's ordering)."""
    ids = [reservation_id] if isinstance(reservation_id, str) else list(reservation_id)
    with trigger_off(dsn, "spend_reservations_insert") as conn:
        (stamp,) = drv.execute(
            conn, "SELECT clock_timestamp() - make_interval(secs => %s)", (age_s,)
        )[0]
        for rid in ids:
            drv.execute(
                conn,
                "INSERT INTO spend_reservations (reservation_id, schema_version, agent_id, day, reserved_usd, "
                "created_at) VALUES (%s, 1, %s, %s, %s, %s)",
                (rid, agent_id, day, amount, stamp),
            )
        amount = amount * len(ids)
        drv.execute(
            conn,
            "INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) "
            "ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd",
            (agent_id, day, amount),
        )
        drv.execute(
            conn,
            "INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, %s) "
            "ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd",
            (agent_id, day.replace(day=1), amount),
        )


def age(dsn, reservation_id, age_s):
    """Make an existing reservation `age_s` seconds older (the update trigger refuses the change otherwise)."""
    with trigger_off(dsn, "spend_reservations_update") as conn:
        drv.execute(
            conn,
            "UPDATE spend_reservations SET created_at = created_at - make_interval(secs => %s) "
            "WHERE reservation_id = %s",
            (age_s, reservation_id),
        )


def trigger_states(dsn):
    """{trigger name: tgenabled letter} for the reservation table ('O' is enabled, 'D' disabled)."""
    with drv.connect_admin(dsn, autocommit=True) as conn:
        rows = drv.execute(
            conn,
            "SELECT tgname, tgenabled FROM pg_trigger WHERE tgrelid = 'spend_reservations'::regclass "
            "AND NOT tgisinternal",
        )
    return {name: state for name, state in rows}
