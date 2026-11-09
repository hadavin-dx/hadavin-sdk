"""PR75 round-2 mutant runner. usage: mutate75.py [--dry] [name-substring ...]. Plants one mutant at a time in the
WT-75 worktree, runs its killer selection, restores the file in `finally`. Prints one line per mutant."""
import os, pathlib, subprocess, sys

R = pathlib.Path("/home/user/build/WT-75")
PY = "/home/user/build/venv-pr75-313/bin/python"
PG = "src/hadavin_sdk/store/postgres.py"
MO = "src/hadavin_sdk/models.py"
ME = "src/hadavin_sdk/store/memory.py"
PR = "src/hadavin_sdk/store/protocol.py"
CM = "src/hadavin_sdk/llm/common.py"
MIG = "src/hadavin_sdk/store/migrations/0006_spend_reservations.sql"
P = "tests/contracts/test_store_reserve_proofs_pg.py"
C = "tests/contracts/test_cost_rounding.py"
RES = "tests/contracts/test_store_reserve.py"
RPG = "tests/contracts/test_store_reserve_pg.py"
LONE = "tests/contracts/test_memory_lone_caller.py"
Q = "x.quantize(_COST_UNIT, rounding=ROUND_UP)"
STEPS = "for which, table, query, key, cap in steps:"
SORTED = "for which, table, query, key, cap in sorted(steps, key=lambda s: s[0] == 'run'):"
GUARD = "WHERE {w} AND {c} >= %(delta)s RETURNING {c}"
SWEEP_AGE = '"WHERE status = \'open\' AND clock_timestamp() - created_at > make_interval(secs => %s) "'
M = [
 ("b15 lock order inverted (run last), vii-a+vii-b+vii-c", PG, STEPS, SORTED, [P, "-k", "vii_a or vii_b or vii_c"]),
 ("b15-vii-b only", PG, STEPS, SORTED, [P, "-k", "vii_b"]),
 ("b15-vii-a only", PG, STEPS, SORTED, [P, "-k", "vii_a"]),
 ("b15-settle/release order inverted (vii-c)", PG, "for table, col, where, key in targets:", "for table, col, where, key in reversed(targets):", [P, "-k", "vii_c"]),
 ("b11c release/settle guard dropped (counter may go negative)", PG, GUARD, "WHERE {w} RETURNING {c}", [RES, "-k", "r1_to_r4"]),
 ("b11d missing/damaged counter on close not an error", PG, "if got is None:\n                    _LOG.error(", "if False:\n                    _LOG.error(", [RES, "-k", "r1_to_r4 or damaged or missing"]),
 ("b28b ceiling applied to a settle's excess", PG, GUARD, "WHERE {w} AND {c} >= %(delta)s AND {c} - %(delta)s <= 1000000000000000 RETURNING {c}", [RES, "-k", "e3"]),
 ("b28c per-call excess bound restored (max(reserved,1))", PG, "            targets = []\n", "            if delta < 0 and -delta > max(claim['reserved_usd'], Decimal(1)):\n                raise ValueError('excess too large')\n            targets = []\n", [RES, "-k", "e1 or e2"]),
 ("b17 kill-switch read takes FOR SHARE", PG, 'found = self._select(KillSwitch, "kill_switch", "id = 1", ())', 'found = self._select(KillSwitch, "kill_switch", "id = 1", (), " FOR SHARE")', [P, "-k", "select_only_on_the_kill_switch"]),
 ("b18c deadline check removed from _exec", PG, "if deadline is not None and time.monotonic() >= deadline:", "if False:", [P, "-k", "t4_a or T4"]),
 ("b13 kill switch not checked (postgres)", PG, "if self.get_kill_switch().on:  # the one kill switch read (fails closed)", "if False:", [RES, "-k", "kill_switch"]),
 ("b13m kill switch not checked (memory)", ME, "if self._kill_on().on:", "if False:", [RES, "-k", "kill_switch"]),
 ("b16 sweep age uses the Python clock", PG, "clock_timestamp() - created_at > make_interval(secs => %s) ", "%s::timestamptz - created_at > make_interval(secs => %s) ", [P, "-k", "database_clock"]),
 ("b16b sweep without ORDER BY", PG, '"ORDER BY created_at, reservation_id LIMIT %s FOR UPDATE SKIP LOCKED) "', '"LIMIT %s FOR UPDATE SKIP LOCKED) "', [P, "-k", "sweep_takes_the_oldest"]),
 ("b16c sweep result not sorted (RETURNING order)", PG, "out.sort(key=lambda r: (r.created_at, r.reservation_id))  # RETURNING has no order", "out.reverse()", [RES, P, "-k", "sweep"]),
 ("b22 day bound from the Python clock", PG, "today = self._exec(\"SELECT (now() AT TIME ZONE 'UTC')::date AS d\").fetchone()[\"d\"]", "today = now().date()", [P, "-k", "database_clock"]),
 ("M5 purge unbatched", PG, "PURGE_BATCH_ROWS = defaults.STORE_PURGE_BATCH_ROWS", "PURGE_BATCH_ROWS = 10**9", ["tests/contracts/test_store_writes_pg.py", "-k", "M5"]),
 # this round's fixes: each mutant restores the OLD behaviour (fail-before proof)
 ("r2-c meta text not scanned (old: memory accepts NUL/surrogate)", PR, "    # NUL and a lone surrogate: the same refusal as the Postgres write wrapper, on both stores\n    check_text(meta)\n", "", [RES, "-k", "meta_text"]),
 ("r2-a reserve reads self._kill.on directly (old: no single helper)", ME, "if self._kill_on().on:", "if self._kill.on:", [LONE, "-k", "one_helper"]),
 ("r2-e memory counters move before the row is built (old)", ME, "            # built BEFORE any counter moves: a failure here leaves nothing half-booked\n", "            self._spend[(agent_id, day)] = new_day\n", [LONE, "-k", "building_the_row"]),
 ("r2-d price_cost catches InvalidOperation only (old)", CM, "except DecimalException as exc:", "except InvalidOperation as exc:", [C, "-k", "price_cost or fake_model_prices"]),
 ("r2-d2 fake model prices inline, not through price_cost (old)", "src/hadavin_sdk/llm/fake.py", 'cost = price_cost(r, data.get("input_tokens", 0), data.get("output_tokens", 0))', 'cost = __import__("hadavin_sdk.models", fromlist=["x"]).round_cost_up(__import__("decimal").Decimal(data.get("input_tokens", 0)) * r.input_usd_per_mtok / __import__("decimal").Decimal(1_000_000))', [C, "-k", "fake_model_prices"]),
 ("r2-e trigger lets open->settled carry expired_at (old)", MIG, "        IF NEW.expired_at IS NOT NULL THEN\n            RAISE EXCEPTION 'spend_reservations: change refused';\n        END IF;\n    ELSIF OLD.status = 'expired' AND", "        NULL;\n    ELSIF OLD.status = 'expired' AND", [RPG, "-k", "keeps_expired_at_null"]),
 ("r2-e sweep claims rows without status guard / skip locked removed", PG, "FOR UPDATE SKIP LOCKED) ", ") ", [P, "-k", "sweep_skips"]),
 # money rounding, i-series
 ("i10a no rounding", MO, f"return {Q}", "return x", [C]),
 ("i10b ROUND_DOWN", MO, Q, "x.quantize(_COST_UNIT, rounding='ROUND_DOWN')", [C]),
 ("i10c ROUND_HALF_UP", MO, Q, "x.quantize(_COST_UNIT, rounding='ROUND_HALF_UP')", [C]),
 ("i10d ROUND_HALF_EVEN", MO, Q, "x.quantize(_COST_UNIT, rounding='ROUND_HALF_EVEN')", [C]),
 ("i10e ROUND_HALF_DOWN", MO, Q, "x.quantize(_COST_UNIT, rounding='ROUND_HALF_DOWN')", [C]),
 ("i10f ROUND_UP then always add one unit", MO, f"return {Q}", f"return {Q} + Decimal('1E-8')", [C]),
 ("i10g quantize at 7 decimals", MO, Q, "x.quantize(Decimal('1E-7'), rounding=ROUND_UP)", [C]),
 ("i10g2 quantize at 9 decimals", MO, Q, "x.quantize(Decimal('1E-9'), rounding=ROUND_UP)", [C]),
 ("i10h tiny nonzero cost rounds to zero", MO, f"return {Q}", f"return {Q} if x >= Decimal('1E-7') else Decimal(0)", [C]),
 ("i10i ROUND_05UP", MO, Q, "x.quantize(_COST_UNIT, rounding='ROUND_05UP')", [C]),
 ("i10j value passes the context before quantize", MO, Q, "(+x).quantize(_COST_UNIT, rounding=ROUND_UP)", [C]),
]
args = sys.argv[1:]
dry = "--dry" in args
only = [a for a in args if a != "--dry"]
env = dict(os.environ, HADAVIN_TEST_PG_DSN="postgresql://postgres@127.0.0.1:56175/postgres", HADAVIN_REQUIRE_PG="1")
for name, f, old, new, sel in M:
    if only and not any(o in name for o in only):
        continue
    path = R / f
    text = path.read_text()
    n = text.count(old)
    if n != 1:
        print(f"== {name}: PATTERN FOUND {n} TIMES, not run", flush=True)
        continue
    if dry:
        print(f"== {name}: pattern ok", flush=True)
        continue
    path.write_text(text.replace(old, new, 1))
    try:
        r = subprocess.run([PY, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-x", "-rf", *sel], cwd=R, env=env, capture_output=True, text=True, timeout=900)
        out = r.stdout.strip().splitlines()
        fails = [l for l in out if l.startswith("FAILED")][:2]
        tail = [l for l in out if " passed" in l or " failed" in l or " error" in l][-1:]
        print(f"== {name}: {'KILLED' if r.returncode != 0 else 'SURVIVED'} (rc={r.returncode})", *fails, *tail, sep="\n   ", flush=True)
        if "b15-vii-b only" in name or name.startswith("r2-c"):
            (pathlib.Path("/home/user/build/B-P75-out") / ("raw-" + name.split()[0] + ".txt")).write_text(r.stdout[-6000:])
    finally:
        path.write_text(text)
