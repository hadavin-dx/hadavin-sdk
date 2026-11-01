"""`eval run|report|compare`. Exit codes (also in the README):

  reseal  0 lock.json sealed again after a hand edit (needs the key), 14 refused (counter/chain/anchor disagree)
  freeze  0 lock.json written, 4 startup (a file is missing, lock.json already exists: never overwritten, or the
          file system cannot hard-link)
  reconcile  0 lock.json and the sealed-run chain agree (rolled forward if a crash left them apart), 14 they cannot
          be reconciled (the chain is shorter than lock.json or fails its check)
  run     0 green, 10 amber ("promising, not demonstrated"), 11 not demonstrated, 12 a hard zero breached,
          13 aborted (meter, kill switch or a smoke limit; no verdict), 14 a sealed run was refused (budget, k, smoke,
          counter or chain mismatch, stale open reservation, second-look rules), 5 the sealed run could not be recorded
          (chain or lock write failed; run `eval reconcile`), 4 startup (config, lock, files, database, no model) or a
          harness defect found mid-run (a gold query that does not run: not a model result), 1 usage
  report  0 printed, 4 not a run folder
  compare 0 no regression, 11 regression, 4 the runs are not comparable

The model is the recorded one (`paths.recorded_dir`, built by the fixture builder) unless `--live` is given: then it is
the config's `llm` entry (the core LLM kind). `--smoke` (with `--live`) also aborts the run when the cost per question
passes US$0.035 or more than 10 % of the model attempts are schema violations. A live run spends real money: it needs
the owner's yes at each step of the budget table, and the meter gates every call.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import time
from dataclasses import replace
from pathlib import Path

from askdata import audit as audit_mod
from askdata import evalrun, htmlexport, live, prompt
from askdata.config import AskdataConfig, ConfigError, config_hash, load_config
from askdata.evalrun import EXIT, Config, Harness, HarnessError, Incomparable, RecordingExecutor
from askdata.evalset import (
    AdversarialItem,
    GoldItem,
    Lock,
    LockError,
    Thresholds,
    load_jsonl,
    lock_guard,
    read_lock,
    verify_files,
)
from askdata.ledger import QueryLedger
from askdata.meter import KillSwitch, MeterError
from askdata.opscli import out
from askdata.pgsource import PgSource
from askdata.pipeline import Pipeline
from askdata.policy import EXIT_AUDIT
from askdata.safe_text import clean
from askdata.sealed import SealedGate, key_from, verify_run_report
from hadavin_sdk.llm.fake import FakeLLM

# what `evalrun.run_id` produces: UTC time to the microsecond plus the label. Nothing else names a run folder.
RUN_ID = re.compile(r"[0-9]{8}T[0-9]{12}Z-(dev|sealed|second-look)", re.ASCII)

SPLIT_FILES = {
    "dev": ("gold.dev.jsonl", "adversarial.dev.jsonl"),
    "test": ("gold.test.jsonl", "adversarial.jsonl"),
}


def _golden_sha(lock: Lock) -> str:
    return hashlib.sha256(
        "".join(f"{k}:{v}\n" for k, v in sorted(lock.files.items())).encode()
    ).hexdigest()


def build_harness(
    cfg: AskdataConfig,
    lock: Lock,
    run_dir: Path,
    ecfg: Config,
    sources: dict[str, object] | None = None,
):
    """Pipelines over the planted database A (and the clean twin), recorders on A, B and clean."""
    pr = prompt.load(as_of=cfg.as_of)
    chash = config_hash(cfg, pr.prompt_sha256)
    if ecfg.live:
        llm = live.make_llm(cfg)
    elif cfg.paths.recorded_dir is None:
        raise ConfigError("no model: set paths.recorded_dir, or use --live with an `llm` entry")
    else:
        llm = FakeLLM(cfg.paths.recorded_dir, cfg.routes())
    if sources is None:
        limits = (
            cfg.database.limits()
        )  # the client's statement timeout and caps apply to every database
        dsns = {w: live.resolve_dsn(cfg, which=w) for w in ("a", "b", "clean")}
        sources = {k: PgSource(d, limits=limits) for k, d in dsns.items() if d}
    need = {"a": ("ASKDATA_DSN", "dsn_secret_name"), "b": ("ASKDATA_DSN_B", "dsn_secret_name_b")}
    if absent := [w for w in need if w not in sources]:
        raise ConfigError(
            "no DSN for database "
            + " and ".join(
                f"{w.upper()}: set {need[w][0]} or database.{need[w][1]}" for w in absent
            )
            + " (the clean twin, ASKDATA_DSN_CLEAN or database.dsn_secret_name_clean, is optional)"
        )
    rec = {k: RecordingExecutor(v, k, run_dir / "statements.jsonl") for k, v in sources.items()}  # type: ignore[arg-type]
    meter, kill = cfg.meter_obj(), KillSwitch(cfg.paths.kill_switch_file)
    sink = audit_mod.local_dir_sink(cfg.paths.audit_dir)
    ledger = QueryLedger(cfg.paths.ledger_file)

    # A live model always goes through the live meter gate (fresh external_usd), whatever the YAML `live` says.
    # The recorded model never retries inside a call, so it reserves once; a live one reserves for every retry.
    settings = (
        replace(cfg.settings(), live=True)
        if ecfg.live
        else replace(cfg.settings(), llm_max_attempts=1)
    )

    def pipeline(key: str) -> Pipeline:
        return Pipeline(
            llm=llm, routes=cfg.routes(), executor=rec[key], audit=audit_mod.AskAudit(sink, principal="claimed:eval"), ledger=ledger,
            meter=meter, kill=kill, prompt=pr, config_hash=chash, settings=settings,
        )  # fmt: skip

    harness = Harness(
        pipeline=pipeline("a"),
        clean_pipeline=pipeline("clean") if "clean" in rec else None,
        recorders=rec,
        lock=lock,
        config=ecfg,
    )
    return (
        harness,
        meter,
        {
            "model_id": cfg.route.model_id,
            "prompt_sha256": pr.prompt_sha256,
            "config_hash": chash,
            "golden_sha256": _golden_sha(lock),
        },
    )


def _gate(cfg: AskdataConfig) -> SealedGate:
    """The sealed-run gate (sealed.py) with the HMAC key from the secrets kind when the config names one."""
    key = None
    if cfg.sealed_key_secret_name:
        provider = live.make_provider(cfg)
        if provider is None:
            raise LockError("sealed_key_secret_name is set but the config has no `secrets` entry")
        key = key_from(provider, cfg.sealed_key_secret_name)
    # Two anchors with fixed names: one beside the chain, one in the eval folder that you COMMIT to the repository.
    anchors = [cfg.paths.audit_dir / "sealed-anchor.json", cfg.paths.eval_dir / "anchor.json"]
    return SealedGate(
        cfg.paths.eval_dir,
        cfg.paths.audit_dir / "sealed-chain.jsonl",
        cfg.paths.runs_dir,
        key,
        anchors,
    )


def _smoke_key(cfg: AskdataConfig) -> str:
    """What a smoke run vouches for: this prompt, this config and this model. Any change needs a new smoke run."""
    return f"{config_hash(cfg, prompt.load(as_of=cfg.as_of).prompt_sha256)}:{cfg.route.model_id}"


def cmd_freeze(
    cfg: AskdataConfig, new_set_reason: str | None = None, discard_count: int | None = None
) -> int:
    """Write lock.json (file hashes, the gate thresholds, test_runs 0), the chain's genesis entry and the anchors. Run it
    ONCE, after the prompt and the dev work are final and before any sealed run. It refuses while a lock, a chain or
    an anchor exists (that would reset the sealed counter); a genuinely NEW test set needs `--new-set --reason`,
    which leaves a visible `new_set` entry in the chain."""
    eval_dir = cfg.paths.eval_dir
    names = [n for pair in SPLIT_FILES.values() for n in pair]
    if missing := [n for n in names if not (eval_dir / n).is_file()]:
        out(f"startup: cannot freeze, missing: {', '.join(missing)}")
        return 4
    try:  # temp file, then os.link: no-clobber, and a crash never leaves an empty lock.json
        with lock_guard(eval_dir):
            lock = _gate(cfg).create(
                names,
                Thresholds(
                    green_max_upper=cfg.sealed.green_max_upper,
                    amber_max_upper=cfg.sealed.amber_max_upper,
                ),
                new_set_reason,
                discard_count=discard_count,
                lock_fields={
                    "sealed_min_remaining_usd": cfg.sealed.first_run_min_remaining_usd,
                    "second_look_min_remaining_usd": cfg.sealed.second_look_min_remaining_usd,
                    "max_second_looks": cfg.sealed.max_second_looks,
                },
            )
    except LockError as err:
        if "lock.json already exists" in str(err):
            out(
                "freeze: lock.json already exists; not overwritten (it holds the sealed-run counter)"
            )
        else:
            out(f"freeze: {err}")
        return 4
    except OSError as err:  # e.g. a file system without hard links
        out(
            f"startup: cannot create lock.json without overwriting ({type(err).__name__}); nothing was written"
        )
        return 4
    except ConfigError as err:
        out(f"startup: {err}")
        return 4
    for n, digest in sorted(lock.files.items()):
        out(f"{digest}  {n}")
    t = lock.thresholds
    out(
        f"freeze: lock.json written (green <= {t.green_max_upper}, amber <= {t.amber_max_upper}, test_runs 0"
        f"{', sealed with the configured key' if lock.seal else ', NOT keyed: set sealed_key_secret_name for a client run'})"
    )
    out("freeze: commit lock.json and anchor.json (both in the eval folder) to the repository")
    return 0


def cmd_reseal(cfg: AskdataConfig) -> int:
    """Key holder: bless the current lock.json after a hand edit of the harness-defect fields (logged in the chain)."""
    try:
        with lock_guard(cfg.paths.eval_dir):
            fields = _gate(cfg).reseal()
    except LockError as err:
        out(f"refused: {err}")
        return 14
    except (ConfigError, OSError) as err:
        out(f"startup: {err}")
        return 4
    out(
        f"reseal: lock.json sealed again (hand-written fields present: {', '.join(fields) or 'none'})"
    )
    return 0


def cmd_reconcile(cfg: AskdataConfig) -> int:
    """Audited recovery: replay the sealed-run chain over lock.json (what a crash between the two left unmirrored)."""
    try:
        with lock_guard(cfg.paths.eval_dir):
            before, after = _gate(cfg).reconcile()
    except LockError as err:
        out(f"refused: {err}")
        return 14
    except ConfigError as err:
        out(f"startup: {err}")
        return 4
    out(f"reconcile: sealed runs in lock.json {before} -> {after} (the chain is the record)")
    return 0


def _prepare(cfg, split, k, second_look, harness_factory, use_live, smoke):
    """Everything up to and including the sealed counter. Returns an exit code (refused or startup), or the pieces
    `cmd_run` needs. For a sealed run the caller holds the lock.json OS lock around this whole function."""
    eval_dir = cfg.paths.eval_dir
    gate = _gate(cfg)
    try:
        lock = gate.load() if split == "test" else read_lock(eval_dir)
        changed = verify_files(eval_dir, lock)
        if changed:
            out(
                f"startup: frozen file(s) changed or missing since the freeze: {', '.join(changed)}"
            )
            return 4
        gold_name, adv_name = SPLIT_FILES[split]
        if not {gold_name, adv_name} <= set(lock.files):
            out(f"startup: {gold_name} and {adv_name} must both be frozen in lock.json")
            return 4
        gold = [g for g in load_jsonl(eval_dir / gold_name, GoldItem) if g.split == split]
        adv_all = load_jsonl(eval_dir / adv_name, AdversarialItem)
    except (LockError, OSError, ValueError) as err:
        out(f"refused: {err}" if split == "test" else f"startup: {err}")
        return 14 if split == "test" and isinstance(err, LockError) else 4
    adv = [a for a in adv_all if a.needs_llm] if split == "test" else adv_all
    label = (
        "sealed"
        if split == "test" and lock.test_runs == 0
        else ("second look" if split == "test" else "dev")
    )
    meter = cfg.meter_obj()
    try:
        evalrun.sealed_gate(
            lock,
            meter.remaining(),
            split=split,
            second_look=second_look,
            live=use_live,
            smoke_key=_smoke_key(cfg) if use_live else None,
        )
        if use_live and (stale := meter.stale_open()):
            raise LockError(
                f"{len(stale)} model call(s) from an earlier run never settled (see `meter`); check the provider "
                "console for what they cost, then `meter --clear-open`"
            )
    except (LockError, MeterError) as err:
        out(f"refused: {err}")
        return 14
    if split == "test" and second_look == "harness_defect":
        ids = {g.id for g in gold} | {a.id for a in adv_all}
        run = lock.harness_defect_run or ""
        if (
            not RUN_ID.fullmatch(run)
            or run
            not in {e["data"]["run_id"] for e in gate.chain.entries() if e["kind"] == "sealed_run"}
            or not (cfg.paths.runs_dir / run / "report.json").is_file()
            or lock.harness_defect_item not in ids
        ):
            out(
                "refused: harness_defect_run must name a sealed run in the chain and harness_defect_item an id "
                "in the frozen test files"
            )
            return 14
    run_dir = cfg.paths.runs_dir / evalrun.run_id(label)
    run_dir.mkdir(parents=True, exist_ok=True)
    run_handle = None
    try:
        harness, meter, meta = harness_factory(
            cfg,
            lock,
            run_dir,
            Config(k=k, label=label, live=use_live, smoke=smoke, smoke_limits=cfg.smoke),
        )
    except (ConfigError, KeyError, OSError) as err:
        out(f"startup: {err}")
        return 4
    if (
        split == "test"
    ):  # write-ahead: the chain first, then lock.json; a crash between is replayed by the next load
        try:
            lock = gate.begin(lock, run_dir.name)
            run_handle = (
                gate.acquire_run()
            )  # held for the whole run: a second look sees "still running"
        except (OSError, LockError) as err:
            out(
                f"cannot record the sealed run ({type(err).__name__}); nothing was run. "
                "If lock.json and the chain now differ, `eval reconcile` rolls lock.json forward"
            )
            return EXIT_AUDIT
    return lock, harness, meter, meta, gold, adv, label, run_dir, gate, run_handle


def cmd_run(
    cfg: AskdataConfig,
    split: str,
    k: int,
    second_look: str | None,
    harness_factory=build_harness,
    *,
    use_live: bool = False,
    smoke: bool = False,
) -> int:
    eval_dir = cfg.paths.eval_dir
    if (
        split == "test" and k != 1
    ):  # one sealed invocation is one pass; repeats (pass^k) belong to --split dev
        out("refused: the sealed set takes --k 1 only (use --split dev --k 3 for repeated runs)")
        return 14
    guard = lock_guard(eval_dir) if split == "test" else contextlib.nullcontext()
    try:
        with guard:  # sealed: load -> gate -> write-ahead record -> counter, all under one OS lock
            prep = _prepare(cfg, split, k, second_look, harness_factory, use_live, smoke)
    except LockError as err:
        out(f"refused: {err}")
        return 14
    except ConfigError as err:
        out(f"startup: {err}")
        return 4
    if isinstance(prep, int):
        return prep
    lock, harness, meter, meta, gold, adv, label, run_dir, gate, run_handle = prep
    st = {
        "status": "aborted",
        "smoke_ok": True,
    }  # 'aborted' until a report exists; the chain/run folder decide it

    def body() -> int:
        started = time.monotonic()
        try:
            results = harness.run_gold(gold)
            adv_results = harness.run_adversarial(adv) if not harness.aborted else []
        except HarnessError as err:
            out(f"harness defect (not a model result): {err}")
            return 4
        run_meta = {
            **meta,
            "second_look": label == "second look",
            "second_look_reason": second_look,
        }
        report = harness.report(
            results, adv_results, split=split, meta=run_meta, elapsed_s=time.monotonic() - started
        )
        if split == "test" and verify_files(
            eval_dir, lock
        ):  # a changed frozen file mid-run invalidates the run
            report = {
                **report,
                "verdict": "aborted",
                "verdict_text": "invalid: a frozen file changed during the run",
                "aborted": "frozen_file_changed",
            }
        try:
            snap = meter.snapshot()
        except MeterError:
            snap = {}
        evalrun.write_run(run_dir, results + adv_results, report, snap)
        if (
            split == "test"
        ):  # the report's hash goes into the chain now; a later change to report.json is noticed
            st["smoke_ok"] = _record(lambda: gate.record_report(run_dir.name), eval_dir)
        st["status"] = (
            "aborted" if report["aborted"] else "complete"
        )  # the results exist now: nothing may call this 'aborted'
        if smoke and use_live and split == "dev" and not report["aborted"]:
            st["smoke_ok"] = _record(lambda: gate.record_smoke(_smoke_key(cfg)), eval_dir)
        out(evalrun.render_md(report))
        out(f"run folder: {run_dir}")
        hz = sum(v for key, v in report["hard_zeros"].items() if key != "model_followed_injection")
        if report["aborted"]:
            return EXIT["aborted"]
        return EXIT["hard_zero"] if hz else EXIT[report["verdict"]]

    finished = True
    try:
        code = body()
    finally:  # also on KeyboardInterrupt and on any crash after the results were written
        if run_handle is not None:
            gate.release_run(run_handle)  # the run is over: it is no longer "running"
        if split == "test":
            finished = _record(lambda: gate.finish(run_dir.name, st["status"]), eval_dir)
    if not (
        finished and st["smoke_ok"]
    ):  # a green verdict must not hide that the record was not written
        out(
            "the sealed-run record could not be written; the verdict above stands but run `eval reconcile`"
        )
        return EXIT_AUDIT
    return code


def _record(step, eval_dir: Path) -> bool:
    """Run one chain/lock bookkeeping step under the lock. False (and a warning) if it failed: the next `load()`
    derives the same facts from the chain and the run folder, but the caller must not report plain success."""
    try:
        with lock_guard(eval_dir):
            step()
    except (OSError, LockError) as err:
        out(
            f"warning: could not record a sealed-run step ({type(err).__name__}); `eval reconcile` will recover it"
        )
        return False
    return True


def _vouch(cfg: AskdataConfig | None, *run_dirs: Path) -> int | None:
    """With a config: check each run folder's report.json against the hash the sealed-run chain recorded. Returns an
    exit code (4) when a recorded report was deleted or changed, else None (a note is printed for an unrecorded one)."""
    if cfg is None:
        out("note: no config given, so the report is NOT checked against the sealed-run chain")
        return None
    try:
        entries = _gate(cfg).chain.entries()
        for run_dir in run_dirs:
            if not verify_run_report(entries, run_dir) and run_dir.name.endswith(
                ("-sealed", "-second-look")
            ):
                out(f"note: the chain has no record of {run_dir.name}'s report")
    except (LockError, ConfigError) as err:
        out(f"report: {err}")
        return 4
    return None


def cmd_report(
    run_dir: Path, fmt: str = "md", dest: Path | None = None, cfg: AskdataConfig | None = None
) -> int:
    if (bad := _vouch(cfg, run_dir)) is not None:
        return bad
    try:
        rep = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        out(f"report: {run_dir} is not a run folder")
        return 4
    try:
        text = htmlexport.render_eval(rep) if fmt == "html" else evalrun.render_md(rep)
    except (KeyError, TypeError, AttributeError) as err:
        out(f"report: report.json is missing or has a bad field ({type(err).__name__}: {err})")
        return 4
    if dest is not None:
        dest = dest.resolve()
        if Path.cwd().resolve() not in dest.parents:
            out("report: --out must be inside the current folder")
            return 1
        dest.write_text(clean(text) if fmt != "html" else text, encoding="utf-8", newline="\n")
        out(f"wrote {dest.name}")
    elif fmt == "html":
        htmlexport.write_stdout(text)
    else:
        out(text)
    return 0


def cmd_compare(a: Path, b: Path, cfg: AskdataConfig | None = None) -> int:
    if (bad := _vouch(cfg, a, b)) is not None:
        return bad
    try:
        ra, rb = (json.loads((p / "report.json").read_text(encoding="utf-8")) for p in (a, b))
        diff = evalrun.compare_reports(ra, rb)
    except (OSError, ValueError, KeyError, Incomparable) as err:
        out(f"compare: not comparable ({type(err).__name__}: {err})")
        return 4
    out(json.dumps(diff, indent=2, sort_keys=True, default=str))
    return 11 if diff["regression"] else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="askdata eval", description="Evaluation harness")
    ap.add_argument("--config", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--split", choices=["dev", "test"], required=True)
    r.add_argument("--k", type=int, default=1)
    r.add_argument("--second-look", choices=["aborted", "harness_defect"], default=None)
    r.add_argument("--live", action="store_true", help="use the config's llm entry (spends money)")
    r.add_argument("--smoke", action="store_true", help="with --live: abort on the smoke limits")
    fz = sub.add_parser("freeze", help="write lock.json once, after dev work is final")
    fz.add_argument(
        "--new-set",
        action="store_true",
        help="a NEW test set: restart the sealed count (needs --reason)",
    )
    fz.add_argument("--reason", default=None, help="20+ characters; written into the chain")
    fz.add_argument(
        "--discard-count",
        type=int,
        default=None,
        help="with --new-set: the number of counted sealed runs you discard",
    )
    sub.add_parser(
        "reseal",
        help="key holder: re-seal lock.json after a hand edit of the harness-defect fields",
    )
    sub.add_parser(
        "reconcile", help="roll lock.json forward over the sealed-run chain after a crash"
    )
    rp = sub.add_parser("report")
    rp.add_argument("run_dir", type=Path)
    rp.add_argument("--format", choices=["md", "html"], default="md")
    rp.add_argument("--out", type=Path)
    c = sub.add_parser("compare")
    c.add_argument("baseline", type=Path)
    c.add_argument("candidate", type=Path)
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 1
    if args.cmd in ("report", "compare"):
        cfg_path = args.config or os.environ.get("ASKDATA_CONFIG")
        try:
            vouch_cfg = load_config(Path(cfg_path)) if cfg_path else None
        except ConfigError:
            vouch_cfg = None
        if args.cmd == "report":
            return cmd_report(args.run_dir, args.format, args.out, vouch_cfg)
        return cmd_compare(args.baseline, args.candidate, vouch_cfg)
    if args.cmd == "freeze" and args.new_set != bool((args.reason or "").strip()):
        out('eval freeze: --new-set and --reason "..." go together')
        return 1
    if args.cmd == "run" and (args.k < 1 or (args.smoke and not args.live)):
        out("eval run: --k must be at least 1, and --smoke needs --live")
        return 1
    path = args.config or os.environ.get("ASKDATA_CONFIG")
    if not path:
        out("startup: give --config or set ASKDATA_CONFIG")
        return 4
    try:
        cfg = load_config(Path(path))
    except ConfigError as err:
        out(f"startup: {err}")
        return 4
    if args.cmd == "freeze":
        return cmd_freeze(cfg, args.reason if args.new_set else None, args.discard_count)
    if args.cmd == "reseal":
        return cmd_reseal(cfg)
    if args.cmd == "reconcile":
        return cmd_reconcile(cfg)
    return cmd_run(cfg, args.split, args.k, args.second_look, use_live=args.live, smoke=args.smoke)
