"""`eval run|report|compare`. Exit codes (also in the README):

  freeze  0 lock.json written, 4 startup (a file is missing, or lock.json already exists: never overwritten)
  run     0 green, 10 amber ("promising, not demonstrated"), 11 not demonstrated, 12 a hard zero breached,
          13 aborted (meter or kill switch; no verdict), 14 a sealed run was refused, 4 startup (config, lock, files,
          database, no model), 1 usage
  report  0 printed, 4 not a run folder
  compare 0 no regression, 11 regression, 4 the runs are not comparable

The model is the recorded one (`paths.recorded_dir`, built by the fixture builder) unless `--live` is given: then it is
the config's `llm` entry (the core LLM kind). `--smoke` (with `--live`) also aborts the run when the cost per question
passes US$0.035 or more than 10 % of the model attempts are schema violations. A live run spends real money: it needs
the owner's yes at each step of the budget table, and the meter gates every call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
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
    freeze,
    load_jsonl,
    lock_path,
    read_lock,
    verify_files,
    write_lock,
)
from askdata.ledger import QueryLedger
from askdata.meter import KillSwitch, Meter, MeterError
from askdata.opscli import out
from askdata.pgsource import PgSource
from askdata.pipeline import Pipeline
from askdata.safe_text import clean
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
    if ecfg.live:
        llm = live.make_llm(cfg)
    elif cfg.paths.recorded_dir is None:
        raise ConfigError("no model: set paths.recorded_dir, or use --live with an `llm` entry")
    else:
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


def cmd_freeze(cfg: AskdataConfig) -> int:
    """Write lock.json (file hashes, the gate thresholds, test_runs 0). Run it ONCE, after the prompt and the dev work
    are final and before any sealed run; it never replaces an existing lock (that would reset the sealed counter)."""
    eval_dir = cfg.paths.eval_dir
    names = [n for pair in SPLIT_FILES.values() for n in pair]
    if lock_path(eval_dir).exists():
        out("freeze: lock.json already exists; not overwritten (it holds the sealed-run counter)")
        return 4
    if missing := [n for n in names if not (eval_dir / n).is_file()]:
        out(f"startup: cannot freeze, missing: {', '.join(missing)}")
        return 4
    lock = freeze(eval_dir, names)
    for n, digest in sorted(lock.files.items()):
        out(f"{digest}  {n}")
    t = lock.thresholds
    out(
        f"freeze: lock.json written (green <= {t.green_max_upper}, amber <= {t.amber_max_upper}, test_runs 0)"
    )
    return 0


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
        harness, meter, meta = harness_factory(
            cfg, lock, run_dir, Config(k=k, label=label, live=use_live, smoke=smoke)
        )
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


def cmd_report(run_dir: Path, fmt: str = "md", dest: Path | None = None) -> int:
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
    r.add_argument("--live", action="store_true", help="use the config's llm entry (spends money)")
    r.add_argument("--smoke", action="store_true", help="with --live: abort on the smoke limits")
    sub.add_parser("freeze", help="write lock.json once, after dev work is final")
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
    if args.cmd == "report":
        return cmd_report(args.run_dir, args.format, args.out)
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
    if args.cmd == "freeze":
        return cmd_freeze(cfg)
    if args.k < 1 or (args.smoke and not args.live):
        out("eval run: --k must be at least 1, and --smoke needs --live")
        return 1
    return cmd_run(cfg, args.split, args.k, args.second_look, use_live=args.live, smoke=args.smoke)
