"""`eval run|report|compare`. Exit codes (also in the README):

  run     0 green, 10 amber ("promising, not demonstrated"), 11 not demonstrated, 12 a hard zero breached,
          13 aborted (meter or kill switch; no verdict), 14 a sealed run was refused, 4 startup (config, lock, files,
          database, no model), 1 usage
  report  0 printed, 4 not a run folder
  compare 0 no regression, 11 regression, 4 the runs are not comparable

Only the scripted model is wired here (`paths.recorded_dir` holds recordings built by the fixture builder). A live
route needs the owner's yes at each step of the budget table and is not connected in this phase.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from askdata import audit as audit_mod
from askdata import evalrun, prompt
from askdata.config import AskdataConfig, ConfigError, config_hash, load_config
from askdata.evalrun import EXIT, Config, Harness, HarnessError, Incomparable, RecordingExecutor
from askdata.evalset import (
    AdversarialItem,
    GoldItem,
    Lock,
    LockError,
    load_jsonl,
    read_lock,
    verify_files,
    write_lock,
)
from askdata.ledger import QueryLedger
from askdata.meter import KillSwitch, Meter, MeterError
from askdata.opscli import out
from askdata.pgsource import PgSource
from askdata.pipeline import Pipeline
from hadavin_sdk.llm.fake import FakeLLM

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
    if cfg.paths.recorded_dir is None:
        raise ConfigError(
            "no model: set paths.recorded_dir (live routes are not connected in this phase)"
        )
    llm = FakeLLM(cfg.paths.recorded_dir, cfg.routes())
    sources = sources or {
        k: PgSource(os.environ[v])
        for k, v in (("a", "ASKDATA_DSN"), ("b", "ASKDATA_DSN_B"), ("clean", "ASKDATA_DSN_CLEAN"))
        if v in os.environ
    }
    missing = {"a", "b"} - set(sources)
    if missing:
        raise ConfigError(
            "set ASKDATA_DSN and ASKDATA_DSN_B (and ASKDATA_DSN_CLEAN for the injection pairs)"
        )
    rec = {k: RecordingExecutor(v, k, run_dir / "statements.jsonl") for k, v in sources.items()}  # type: ignore[arg-type]
    meter, kill = Meter(cfg.paths.meter_file), KillSwitch(cfg.paths.kill_switch_file)
    sink = audit_mod.local_dir_sink(cfg.paths.audit_dir)
    ledger = QueryLedger(cfg.paths.ledger_file)

    def pipeline(key: str) -> Pipeline:
        return Pipeline(
            llm=llm, routes=cfg.routes(), executor=rec[key], audit=audit_mod.AskAudit(sink, principal="claimed:eval"), ledger=ledger,
            meter=meter, kill=kill, prompt=pr, config_hash=chash, settings=cfg.settings(),
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


def cmd_run(
    cfg: AskdataConfig, split: str, k: int, second_look: str | None, harness_factory=build_harness
) -> int:
    eval_dir = cfg.paths.eval_dir
    try:
        lock = read_lock(eval_dir)
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
        out(f"startup: {err}")
        return 4
    adv = [a for a in adv_all if a.needs_llm] if split == "test" else adv_all
    label = (
        "sealed"
        if split == "test" and lock.test_runs == 0
        else ("second look" if split == "test" else "dev")
    )
    meter = Meter(cfg.paths.meter_file)
    try:
        evalrun.sealed_gate(lock, meter.remaining(), split=split, second_look=second_look)
    except (LockError, MeterError) as err:
        out(f"refused: {err}")
        return 14
    run_dir = cfg.paths.runs_dir / evalrun.run_id(label)
    run_dir.mkdir(parents=True, exist_ok=True)
    try:
        harness, meter, meta = harness_factory(cfg, lock, run_dir, Config(k=k, label=label))
    except (ConfigError, KeyError, OSError) as err:
        out(f"startup: {err}")
        return 4
    if (
        split == "test"
    ):  # the counter moves when the sealed set is first touched, after a successful startup
        lock = lock.model_copy(
            update={"test_runs": lock.test_runs + 1, "last_test_status": "aborted"}
        )
        write_lock(eval_dir, lock)
    started = time.monotonic()
    try:
        results = harness.run_gold(gold)
        adv_results = harness.run_adversarial(adv) if not harness.aborted else []
    except HarnessError as err:
        out(f"harness defect (not a model result): {err}")
        return 4
    meta = {**meta, "second_look": label == "second look", "second_look_reason": second_look}
    report = harness.report(
        results, adv_results, split=split, meta=meta, elapsed_s=time.monotonic() - started
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
    if split == "test":
        status = "aborted" if report["aborted"] else "complete"
        write_lock(eval_dir, lock.model_copy(update={"last_test_status": status}))
    out(evalrun.render_md(report))
    out(f"run folder: {run_dir}")
    hz = sum(v for key, v in report["hard_zeros"].items() if key != "model_followed_injection")
    if report["aborted"]:
        return EXIT["aborted"]
    return EXIT["hard_zero"] if hz else EXIT[report["verdict"]]


def cmd_report(run_dir: Path) -> int:
    try:
        rep = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
        out(evalrun.render_md(rep))
    except (OSError, ValueError, KeyError):
        out(f"report: {run_dir} is not a run folder")
        return 4
    return 0


def cmd_compare(a: Path, b: Path) -> int:
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
    sub.add_parser("report").add_argument("run_dir", type=Path)
    c = sub.add_parser("compare")
    c.add_argument("baseline", type=Path)
    c.add_argument("candidate", type=Path)
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 1
    if args.cmd == "report":
        return cmd_report(args.run_dir)
    if args.cmd == "compare":
        return cmd_compare(args.baseline, args.candidate)
    path = args.config or os.environ.get("ASKDATA_CONFIG")
    if not path:
        out("startup: give --config or set ASKDATA_CONFIG")
        return 4
    try:
        cfg = load_config(Path(path))
    except ConfigError as err:
        out(f"startup: {err}")
        return 4
    if args.k < 1:
        out("eval run: --k must be at least 1")
        return 1
    return cmd_run(cfg, args.split, args.k, args.second_look)
