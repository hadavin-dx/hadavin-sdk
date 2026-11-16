"""Check runner: asks a live model for a label on ~12 made-up leads, 3 runs, per model, through the same adapter the
desk uses (lead_desk.live_claude). Prints ONLY counts, cost, valid-label rate, flip rate and latency. Never prints the
key or any reply text.

Usage (run it from your own terminal, not from a script that runs without you):
  python scripts/run_live_check.py --key-file PATH --base-url ADDRESS --ledger PATH \\
      --cap-run 0.50 --cap-total 3 --price-date YYYY-MM-DD --model ID=IN_PRICE,OUT_PRICE [--model ...]
IN_PRICE and OUT_PRICE are US$ per million tokens, read from the provider's price page on --price-date.
Use the model ids and prices from your provider's own price page (the form is ID=IN_PRICE,OUT_PRICE).
Nothing is assumed: without caps, prices and a price date the script refuses to start. It prints the exact
worst-case cost of the whole run and waits for y/N before the first call. --base-url is the provider address
(default: the desk's own default address). The key is sent in a header of every request; any address other than
the provider's own or this computer is refused. The leads' e-mail addresses are made up (example.com)."""

from __future__ import annotations

import argparse
import io
import os
import re
import statistics
import sys
import time
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_CEILING, Decimal, localcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # the repository folder: tools/ and scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # the desk code, ahead of it

from lead_desk.config import LiveSettings
from lead_desk.constants import (
    AI_LABELS,
    EXIT_REFUSED,
    EXIT_STOPPED,
    LIVE_DEFAULT_BASE_URL,
    LIVE_DEFAULT_EFFORT,
    LIVE_DEFAULT_MAX_TOKENS,
    LIVE_DEFAULT_TIMEOUT_SECONDS,
    LIVE_EFFORTS,
    LIVE_LEADS_MAX,
    LIVE_MAX_TOKENS_MAX,
    LIVE_PRICE_DATE_FLOOR,
    LIVE_RUNS_MAX,
    LIVE_TIMEOUT_MIN_SECONDS,
    MODEL_CALL_BUDGET_SECONDS,
)
from lead_desk.envnum import read_number
from lead_desk.live_claude import (
    MONEY_CONTEXT,
    LiveError,
    LiveQualifier,
    SpendLedger,
    question_text,
    request_body,
    worst_case_usd,
)
from lead_desk.regfile import FileRefused, open_regular, read_secret_line
from lead_desk.scrub import secret_boundary
from tools.refusing_args import RefusingParser, bounded_float, bounded_int, refusal

LEADS = 12
RUNS = 3
PCT = 100
P95 = 0.95
PRICE_DATE_FORM = re.compile(r"\d{4}-\d{2}-\d{2}")
PRICE_DATE_FLOOR = date(*LIVE_PRICE_DATE_FLOOR)


def _model_arg(text: str) -> tuple[str, Decimal, Decimal]:
    try:
        model, prices = text.split("=", 1)
        p_in, p_out = prices.split(",", 1)
        return model.strip(), read_number(p_in, Decimal), read_number(p_out, Decimal)
    except ValueError as e:
        raise argparse.ArgumentTypeError("needs ID=IN_PRICE,OUT_PRICE") from e


def _usd_arg(text: str) -> Decimal:
    try:
        return read_number(text, Decimal)
    except ValueError as e:
        raise argparse.ArgumentTypeError("is not a number") from e


def _emails(n: int) -> list[tuple[str, str]]:
    return [(f"L{i:012x}", f"made.up.{i}@example.com") for i in range(1, n + 1)]


NO_TERMINAL_LINE = "stopped, nothing was called: there is no terminal to answer the question on"


def _no_terminal() -> bool:
    """True when standard input is closed, missing or the empty device: the question could never be answered."""
    try:
        fd = sys.stdin.fileno()
        return os.path.samestat(os.fstat(fd), os.stat(os.devnull))
    except io.UnsupportedOperation:  # an object with no descriptor (a test double): input() decides
        return False
    except (AttributeError, ValueError, OSError):  # no stdin object, a closed one, or a closed descriptor (EBADF)
        return True


def _pct(x: float) -> str:
    return f"{x * PCT:.0f}%"


def run_model(s: LiveSettings, leads: list[tuple[str, str]], runs: int, ledger: SpendLedger) -> dict[str, object]:
    q = LiveQualifier(s, ledger)
    labels: dict[str, list[str]] = {lid: [] for lid, _ in leads}
    errors: dict[str, int] = {}
    latencies: list[float] = []
    calls = 0
    for _ in range(runs):
        for lid, email in leads:
            t0 = time.monotonic()
            calls += 1
            try:
                labels[lid].append(q.qualify(lid, email))
            except (LiveError, OSError) as e:
                word = (
                    "model service error" if isinstance(e, LiveError) else "network error"
                )  # fixed words, no class name
                errors[word] = errors.get(word, 0) + 1
            finally:
                latencies.append((time.monotonic() - t0) * 1000)
    valid = sum(len(v) for v in labels.values())
    full = [v for v in labels.values() if len(v) == runs]
    flips = sum(1 for v in full if len(set(v)) > 1)
    spent_run, _ = ledger.totals(s.run_id)
    lat = sorted(latencies)
    return {
        "calls": calls,
        "valid": valid,
        "valid_rate": valid / calls if calls else 0.0,
        "flip_rate": flips / len(full) if full else None,
        "full_leads": len(full),
        "errors": errors,
        "p50_ms": statistics.median(lat) if lat else 0.0,
        "p95_ms": lat[min(len(lat) - 1, int(len(lat) * P95))] if lat else 0.0,
        "spent": spent_run,
        "labels_seen": sorted({x for v in labels.values() for x in v if x in AI_LABELS}),
    }


def _price_date_problem(text: str) -> str | None:
    """None when `text` is a real calendar day written YYYY-MM-DD, not before the floor and not in the future."""
    if not PRICE_DATE_FORM.fullmatch(text.strip()):
        return "must be a day written YYYY-MM-DD (for example 2026-01-31)"
    try:
        day = date.fromisoformat(text.strip())
    except ValueError:
        return "is not a real calendar day (written YYYY-MM-DD)"
    if day < PRICE_DATE_FLOOR:
        return f"is too old (not before {PRICE_DATE_FLOOR.isoformat()})"
    if day > datetime.now(UTC).date() + timedelta(days=1):  # wall-clock: a calendar day; one day of slack
        return "is in the future: give the day the prices were read from the provider's page"
    return None


def option_problem(a: argparse.Namespace) -> str | None:
    """The one refusal line for the first typed value that cannot be used, or None. Every text is fixed: it never holds
    what was typed. Runs before anything is read, opened or asked."""
    for option, value in (("--price-date", a.price_date), ("--effort", a.effort)):
        if not value.strip():
            return refusal(option, "must not be empty")
    if any(not model.strip() for model, _, _ in a.model):
        return refusal("--model", "the model id must not be empty")
    if (text := _price_date_problem(a.price_date)) is not None:
        return refusal("--price-date", text)
    if a.effort not in LIVE_EFFORTS:
        return refusal("--effort", "must be one of: " + ", ".join(LIVE_EFFORTS))
    ids = [model.strip().casefold() for model, _, _ in a.model]
    if len(set(ids)) != len(ids):  # two prices for one model would make the cost figures and the run ids ambiguous
        return refusal("--model", "the same model id is given twice: give each model once")
    return None


@secret_boundary()
def file_problem(a: argparse.Namespace) -> str | None:
    """The one refusal line when the key file is not a readable key file or the ledger exists and is not a regular
    file, or None. Run before the cost line, so that a pipe or a folder named here is refused at once and not after
    "Start?" has been answered. Fixed texts; the name of a file is never printed."""
    try:
        read_secret_line(a.key_file, "key", "key")  # the same reader the live step uses: the key itself is dropped
    except FileRefused as e:
        return refusal("--key-file", str(e))
    ledger = Path(a.ledger)
    if ledger.exists() or ledger.is_symlink():
        try:
            open_regular(ledger).close()
        except OSError:
            return refusal("--ledger", "must be a regular file (or a name that does not exist yet)")
    return None


# the desk setting that a refusal of LiveSettings names -> the option of this script that sets it
SETTING_OPTIONS = {
    "DESK_LIVE_MODEL": "--model",
    "DESK_LIVE_KEY_FILE": "--key-file",
    "DESK_LIVE_LEDGER_PATH": "--ledger",
    "DESK_LIVE_PRICE_DATE": "--price-date",
    "DESK_LIVE_PRICE_IN_PER_MTOK": "--model",
    "DESK_LIVE_PRICE_OUT_PER_MTOK": "--model",
    "DESK_LIVE_CAP_RUN_USD": "--cap-run",
    "DESK_LIVE_CAP_TOTAL_USD": "--cap-total",
    "DESK_LIVE_BASE_URL": "--base-url",
    "DESK_LIVE_TIMEOUT_SECONDS": "--timeout",
    "DESK_LIVE_MAX_TOKENS": "--max-tokens",
    "DESK_LIVE_EFFORT": "--effort",
}
SETTING_NAME = re.compile(r"DESK_LIVE_[A-Z_]+")


def _option_wording(text: str) -> str:
    """The refusal line for a LiveSettings refusal: the person typed OPTIONS, not DESK_LIVE_* settings, so the first
    setting name becomes the `refused: <OPTION>:` slot and any other one is replaced by its option. The texts of
    LiveSettings are fixed (they name settings, never values)."""
    names = SETTING_NAME.findall(text)
    option = SETTING_OPTIONS.get(names[0], "the options") if names else "the options"
    body = text[len(names[0]) :].lstrip() if names and text.startswith(names[0]) else text
    return refusal(option, SETTING_NAME.sub(lambda m: SETTING_OPTIONS.get(m[0], "an option"), body))


def main(argv: list[str] | None = None) -> int:
    ap = RefusingParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--key-file", required=True, help="file holding the key; read by this script only")
    ap.add_argument("--base-url", default=LIVE_DEFAULT_BASE_URL)
    ap.add_argument("--ledger", required=True, help="spend ledger file (kept; counts across runs)")
    ap.add_argument("--cap-run", type=_usd_arg, required=True, help="US$ cap for one model run")
    ap.add_argument("--cap-total", type=_usd_arg, required=True, help="US$ cap over the whole ledger")
    ap.add_argument("--price-date", required=True)
    ap.add_argument("--model", action="append", required=True, type=_model_arg, help="ID=IN_PRICE,OUT_PRICE")
    ap.add_argument("--max-tokens", type=bounded_int(1, LIVE_MAX_TOKENS_MAX), default=LIVE_DEFAULT_MAX_TOKENS)
    ap.add_argument("--effort", default=LIVE_DEFAULT_EFFORT)
    ap.add_argument(
        "--timeout",
        type=bounded_float(LIVE_TIMEOUT_MIN_SECONDS, MODEL_CALL_BUDGET_SECONDS),
        default=LIVE_DEFAULT_TIMEOUT_SECONDS,
    )
    ap.add_argument("--leads", type=bounded_int(1, LIVE_LEADS_MAX), default=LEADS)  # checked before any list is built
    ap.add_argument("--runs", type=bounded_int(1, LIVE_RUNS_MAX), default=RUNS)
    a = ap.parse_args(argv)
    if (problem := option_problem(a)) is not None:  # the one place that judges the typed values (all fixed texts)
        print(problem)
        return EXIT_REFUSED
    batch = uuid.uuid4().hex[:8]
    leads = _emails(a.leads)
    settings: list[LiveSettings] = []
    try:
        for model, p_in, p_out in a.model:
            settings.append(
                LiveSettings(
                    model=model,
                    key_file=Path(a.key_file),
                    price_in_per_mtok=p_in,
                    price_out_per_mtok=p_out,
                    price_date=a.price_date,
                    cap_run_usd=a.cap_run,
                    cap_total_usd=a.cap_total,
                    ledger_path=Path(a.ledger),
                    run_id=f"check-{batch}-{model}",
                    base_url=a.base_url,
                    timeout_seconds=a.timeout,
                    max_tokens=a.max_tokens,
                    effort=a.effort,
                )
            )
    except ValueError as e:  # the desk's own setting text, said with the option the person typed instead
        print(_option_wording(str(e)))
        return EXIT_REFUSED
    if (problem := file_problem(a)) is not None:  # the key file and the ledger are checked BEFORE the cost line
        print(problem)
        return EXIT_REFUSED
    if _no_terminal():  # after every typed value is judged (a bad option is a refusal, not "no terminal"), and before
        print(NO_TERMINAL_LINE)  # any cost line: one line, nothing else
        return EXIT_STOPPED
    # worst case: every call of every model, the longest question this script can send
    questions = [question_text(lid, em) for lid, em in leads]
    with localcontext(MONEY_CONTEXT):  # the money context: exact sums, rounded UP so the figure is never too low
        worst = sum(  # the exact request bytes (model name, system text, question): the number the reserve counts
            worst_case_usd(s, max(len(request_body(s, q)) for q in questions)) * a.leads * a.runs for s in settings
        )
        worst_shown = worst.quantize(Decimal("0.0001"), rounding=ROUND_CEILING)
    print(f"models: {len(settings)}, calls per model: {a.leads * a.runs}, prices dated {a.price_date}")
    print(f"expected MAXIMUM cost of this whole run: US${worst_shown} (caps: run {a.cap_run}, total {a.cap_total})")
    try:
        answer = input("Start? [y/N] ").strip().lower()
    except (EOFError, OSError):  # no terminal to answer on (closed input, a scheduled job): never read as a yes
        print(NO_TERMINAL_LINE)  # an empty pipe: only reading shows it
        return EXIT_STOPPED
    if answer != "y":
        print("stopped, nothing was called")
        return EXIT_STOPPED
    ledger = SpendLedger(Path(a.ledger))
    for s in settings:
        try:
            r = run_model(s, leads, a.runs, ledger)
        except (LiveError, OSError):  # the spend ledger could not be read: nothing more is spent
            print("stopped: the spend ledger could not be read or written; nothing more was called")
            return EXIT_REFUSED
        flip = "n/a" if r["flip_rate"] is None else _pct(float(r["flip_rate"]))  # type: ignore[arg-type]
        print(
            f"model {s.model}: calls {r['calls']}, valid labels {r['valid']} ({_pct(float(r['valid_rate']))}),"  # type: ignore[arg-type]
            f" flip rate {flip} over {r['full_leads']} leads with all runs valid,"
            f" latency p50 {float(r['p50_ms']):.0f} ms p95 {float(r['p95_ms']):.0f} ms,"  # type: ignore[arg-type]
            f" cost US${r['spent']:.5f} (US${Decimal(str(r['spent'])) * PCT / int(str(r['calls'])):.5f} per 100 calls),"
            f" errors by class: {r['errors'] or 'none'}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
