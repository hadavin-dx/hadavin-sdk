# Independent citation and number check of CORE-PR-HANDOFF-v8.md (EVIDENCE RUNNER: runs and records, does not judge)

Run on 2026-11-16 (UTC) about 14:05 to 14:35 (IST = UTC+5:30). Document under check: `handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v8.md` (722 lines). No network, no spend, no database, nothing committed.

## A. Failures and wrong cites (first)

| # | Document line(s) | What the document says | What I found | Verdict |
|---|---|---|---|---|
| 1 | 26, 54, 502 (twice) | `Money` is a type alias at `config.py:45`; its validator `_money` is at `config.py:38-42`. Line 26 says this cite was **fixed** in v8 after the v7 citation check. | `Money = Annotated[Decimal, BeforeValidator(_money)]` is at `config.py:47`; `def _money` is at `config.py:40-44`; line 45 is blank. The v7 cite was rewritten to another wrong pair of numbers. | **WRONG** (off by 2 and 2) |
| 2 | (repo fact, document E0-1 relies on a green suite) | Document does not claim a pass count today, but its plan treats the existing suite as the baseline. | `tests/test_repo_rules.py::test_licences_are_proprietary` FAILS on the current tree: 10 more LICENSE files than expected, first one `handover/promotion-inputs/apexc/LICENSE: not the proprietary licence text`. The failure is outside everything the document cites. | FAIL (repo state, not a document cite) |
| 3 | 353 and E0-12 (line 698) | The import-graph test holds an allowlist of "the three approvals modules" and has a second test that fails if a table module is in a set of 2 or more "under either counting". | Re-run with imports under `TYPE_CHECKING` counted: the approvals set has FOUR modules (`approvals`, `approvals.cards`, `approvals.channel`, `approvals.requests`), plus the two sets the document names. So an allowlist of exactly three approvals modules only matches the run-time counting. Not a wrong number in the document (it says run-time counting); recorded because the wording "either counting" sits next to "three". | NOTE (partly right: the 3-module set is right for run-time counting only) |
| 4 | 353 | The saved import-graph program overlays the 4.2 table. | The program's `PLANNED` dict is not the same as the 4.2 table: `llm.metered` also imports `defaults`; `llm.build` also imports `llm.metered` (table row lists only `backends.factory`, `config`); `limits` also imports `store.protocol`, `models`, `registry` (table lists `llm.spend`, `llm.gate`, `store`, `config`, `store.amounts`); `store.spend_rules` has no entry. The program is the builder's own reading of the same table, so it does not independently check the design. | NOTE |
| 5 | 26 (item 4) | "all six" v7 cite problems are fixed. | Five of six confirmed fixed (purge connection `app.py:152-160`; `test_providers.py:198` has `make("llm"`; `test_p6_detectors.py:351` import and `:355` `make("detector"`; `runmap.py:298`, `:275`, `:417`; E0-12 note). The sixth (Money) is still wrong, see row 1. | partly right |

Not found at all (cited as existing): nothing. Every `file:line` that points at an existing file has the line range inside the file (317 cites, 0 beyond end of file). Every file cited as existing exists (including `handover/core-hardening/ORDERS.md` lines 185-198, where Q28 is at line 192; the document cites it as `ORDERS.md`).

## B. Import-graph re-run

- Command: `python3 -I import_graph_v8.py /home/user/hadavin-sdk/src` using a copy in the scratchpad (the program only reads and prints).
- Output compared with `evidence-handoff-v8/raw-import-graph-v8.txt` with `diff`: **identical** (no difference). Files: `raw-import-graph-rerun.txt`.
- Counts: 102 modules; today 330 run-time edges and **1 cycle** (approvals, approvals.channel, approvals.requests); v8 planned overlay 362 edges, **0 new or changed cycles**; v6 shape gives the cycle `llm.common <-> llm.gate`. Total cycle lines printed: 3 (1 today, 1 in overlay (same one), 1 in v6 shape).
- Same program with TYPE_CHECKING imports counted (one line changed in a scratch copy): 335 edges, **3 cycles** today: {config, deferred, registry, replay_records}, {approvals, approvals.cards, approvals.channel, approvals.requests}, {k1b.replay, k1b.report, k1b.score}. This agrees with the document's statement (v7 found two more sets). File: `raw-import-graph-typechecking-counted.txt`.

## C. Snippets

- The document has 6 fenced blocks and no shell block (`bash -n`: nothing to check). Blocks 1 and 2 (lines 133-181, 185-235) and the 3rd, 4th and 5th are SQL or signature sketches; blocks at 259-279 (reserve_spend signature), 292-299 and 360-383 (class sketches) are not valid Python (`SyntaxError` / `IndentationError`: they are labelled sketches, no language tag); the block at 387-408 (`one_attempt`) parses with `ast.parse`. SQL (two blocks, 133-235): read only; `sqlglot` is installed but I did not run it on PL/pgSQL; no database exists. Output: `raw-snippet-checks.txt`.

## D. Tests run (sampled; no cloud configuration: `env -i`, no network, no spend)

| Run | Files | Result |
|---|---|---|
| A | test_s5_runtime, test_s4_llm_guard, test_k5_round6_contracts, test_lockin_guard, test_no_reference_material, test_g4_parity, test_p5_llm, test_p6_detectors, test_k5_fixes1, test_k3_pilot_env, test_p7_store, test_s1_foundation | 389 passed, 5 skipped, 0 failed (14.1 s) |
| B | test_k5_tools, test_k5_fixes2, test_k3_pilot, test_p5p6_followups, test_k1b_replay, test_p1a_fixes, test_p1b_backends, test_migrate_regex_linear, test_k2_migrations, tests/contracts, test_repo_rules, test_no_hardcoded_values (with `-x`) | stopped at first failure: 518 passed, 39 skipped, **1 failed** (`test_licences_are_proprietary`) |
| C | test_repo_rules, test_no_hardcoded_values, test_no_reference_material | 57 passed, **1 failed** (same test) |
| lint | `ruff check src tests` (venv ruff) | exit 0 |

Skipped tests are Postgres-dependent tests (no Postgres here). Not run: full suite, bandit, ruff format --check, mutation, any Postgres test. Raw: `raw-pytest-sample-A.txt`, `-B.txt`, `-C.txt`. Note: `raw-pytest-sample-B.txt` existed in git HEAD in this folder (an earlier file with the same name); I overwrote it in the working tree (`git status` shows it modified; the HEAD copy is intact in git).

## E. Other checks

- Facts in section 7: no `scripts/` or `tools/` folder: right. Postgres service `postgres:17.10` and `HADAVIN_TEST_PG_DSN` in `.github/workflows/ci.yml`: right (lines 39-40, 86, 93). CI `bandit -q -r src demos -ll` at line 119: right. `pg_schema(migrated=True, runtime=False)` in `tests/contracts/kinds/store_postgres.py:18`: right (the document says `pg_schema(runtime=True)`).
- Counts: 28 `def chat(` sites in `tests/` (document: 28): right; 26 distinct classes (document: "about 25"): partly right (two of the 26 are in `tests/demo_askdata`). `.chat(` call sites in `src/`: 5 real (extract.py:47, evals.py:73, guard/judge.py:72, runtime/agent_loop.py:425, k1b/loop.py:94): right; `guard/producers.py:5` is a docstring mention only. `make("llm"` sites in tests: 11 files-lines match the document's list (test_providers 65,123,148,172,198; bedrock_provider_r16 74,79,90; p5p6_followups 300,302,417; p5_llm 230,301; contracts/kinds/builtin.py:53): right. `Limits(` callers (`app.py:171`, `cli.py:209`, tests at :28, :206, :104, :58, :241, :1133 and :1269): right. Assignments of `.detector =` / `.llm =` after build in tests (p5p6_followups:101, p6_detectors:186/264/364, k5_tools:608): right. `0001` to `0005` migrations exist, no `0006`: right. Default `max_attempts` 3 at `backends/table.py:40`: right. Fixture route 3.00/15.00/1024 at `tests/fixtures/config/config.yaml:6-8`: right. `0.00225` at `test_s4_llm_guard.py:39` and `test_s5_runtime.py:76`: right.
- Identifiers cited as new (planned) and absent from the repo today: 201 distinct names (e.g. `CallBook`, `SpendMeter`, `spend_op`, `to_nano`, `reserve_spend`, `llm/spend.py`, `0006_spend_op.sql`). Expected for a plan; list in `raw-identifiers-not-found-in-repo.txt`. Names in that list the document describes as existing or as v7 errors: `runtime_privileges` (document says it is v7's mistake: confirmed, no such name), `_handle_body` (document says it is planned), `cache_control`/`cachedContent` (document says no hits: confirmed, the grep over `llm/*.py` finds none), `eval_daily_usd` (planned config field).
- Banned strings: `BANNED` tuple of `tests/test_no_reference_material.py` (10 strings) counted over every file in this folder: 0. `__pycache__` created by me in the repo: none (ran with `PYTHONDONTWRITEBYTECODE=1` and `python -I` from the scratchpad).

## F. What I did NOT check

- I compared the first one to three source lines of each of the 317 `file:line` ranges with the claim text next to it (raw: `raw-cite-excerpts.txt`); I did not read every full range, and I did not re-verify long behavioural sentences that have no line cite (sections 4.3 to 4.11 prose, the D-table reasoning, the arithmetic).
- Cites inside the Python-file-name-only form without a line (for example `retry.py` alone) were checked for existence only.
- SQL and all Postgres behaviour: not run (no database). `psycopg` wrapper behaviour: not read.
- Vendor and price facts (tiers, billing of 429, `$2/$10` etc.): not checked (no network); the repo rule file `.claude/rules/model-choice-and-cost-follow-bible.md` exists and the Sonnet/Haiku prices quoted are in it.
- Section 4.5 to 4.11 identifiers beyond the cite list were checked by name only (present or absent in the repo).

## G. Full table (every `file:line` cite in document order; "right" = the first lines of the cited range show the thing the sentence names; excerpt is the first source line)

| Doc line | Cite | Verdict | Source excerpt |
|---|---|---|---|
| 19 | `store/postgres.py:191-197` | right (source at the range matches the named thing) |  ¦ class PostgresStore: ¦ # ponytail: one connection behind one lock p |
| 26 | `app.py:152-160` | right (source at the range matches the named thing) | if purge_name := getattr(b.store, "purge_dsn_secret_name", None): ¦ #  |
| 26 | `config.py:45` | WRONG: `Money =` is at config.py:47 (line 45 is blank) |  |
| 26 | `tests/test_p6_detectors.py:351` | right (import line; make("detector" is :355 as stated) | from hadavin_sdk.guard import bedrock_guardrail |
| 26 | `runmap.py:298` | right (source at the range matches the named thing) | def redact_untrusted(text: str, mapping: dict[str, str]) -> str: |
| 30 | `llm/common.py:59-62` | right (source at the range matches the named thing) | def estimate_tokens(text: str) -> int: ¦ """For a provider that report |
| 30 | `tests/fixtures/config/config.yaml:6-8` | right (source at the range matches the named thing) | input_usd_per_mtok: "3.00" ¦ output_usd_per_mtok: "15.00" ¦ max_tokens |
| 30 | `tests/test_s4_llm_guard.py:39` | right (source at the range matches the named thing) | assert reply.cost_usd == Decimal("0.00225") |
| 30 | `tests/test_s5_runtime.py:76` | right (source at the range matches the named thing) | assert rt.store.get_run(run.run_id).cost_usd == Decimal("0.00225") |
| 40 | `approvals/gate.py:681-698` | right (source at the range matches the named thing) | def withhold_commands(text: str) -> str: ¦ """G4 over one piece of mod |
| 41 | `gate.py:647-678` | right (source at the range matches the named thing) | _WRITE_SHAPES = re.compile( ¦ r"\bpg_(?:cancel/terminate)_backend\s*\( |
| 42 | `runtime/agent_loop.py:440-441` | right (source at the range matches the named thing) | self.limits.charge(agent_id, reply.cost_usd) ¦ self.store.add_cost(run |
| 43 | `store/memory.py:196-204` | right (source at the range matches the named thing) | def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[D |
| 43 | `store/postgres.py:416-431` | right (source at the range matches the named thing) | def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[D |
| 43 | `store/migrations/0001_core.sql:87-92` | right (source at the range matches the named thing) | CREATE TABLE spend ( ¦ agent_id TEXT NOT NULL, ¦ day      DATE NOT NUL |
| 43 | `store/migrations/0003_approvals_tick.sql:15-20` | right (source at the range matches the named thing) | CREATE TABLE spend_month ( ¦ agent_id TEXT NOT NULL, ¦ month    DATE N |
| 43 | `store/protocol.py:107-111` | right (source at the range matches the named thing) | def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[D |
| 44 | `models.py:19-20` | right (source at the range matches the named thing) | def now() -> datetime: ¦ return datetime.now(UTC) |
| 44 | `app.py:73` | right (source at the range matches the named thing) | clock: Callable[[], datetime] = now, |
| 44 | `limits.py:13-30` | right (source at the range matches the named thing) | class Limits: ¦ def __init__(self, store: Store, audit: AuditSink, reg |
| 45 | `llm/retry.py:83-108` | right (source at the range matches the named thing) | def with_retry[T]( ¦ call: Callable[[], T], ¦ *, |
| 45 | `llm/anthropic.py:122` | right (source at the range matches the named thing) | got = self._retry(lambda: self._parse(self._current().messages.create( |
| 45 | `llm/bedrock.py:156` | right (source at the range matches the named thing) | got = self._retry(lambda: self._parse(self._client.converse(**request) |
| 45 | `retry.py:55-63` | right (source at the range matches the named thing) | def transient(exc: BaseException, retryable: Retryable / None = None)  |
| 45 | `llm/common.py:193-196` | right (source at the range matches the named thing) | class NetworkLLM: ¦ """The ``chat`` every network kind shares: the rou |
| 45 | `anthropic.py:122` | right (source at the range matches the named thing) | got = self._retry(lambda: self._parse(self._current().messages.create( |
| 45 | `bedrock.py:156` | right (source at the range matches the named thing) | got = self._retry(lambda: self._parse(self._client.converse(**request) |
| 45 | `gemini.py:86` | right (source at the range matches the named thing) | got = self._retry( |
| 45 | `openai_compat.py:119` | right (source at the range matches the named thing) | got = self._retry( |
| 45 | `llm/common.py:233-241` | right (source at the range matches the named thing) | def _retry(self, call: Callable[[], Answer]) -> Answer: ¦ return with_ |
| 45 | `llm/openai_compat.py:117-129` | right (source at the range matches the named thing) | started, used = time.monotonic(), [0, 0] ¦ for _ in range(2):  # the f |
| 45 | `retry.py:31-36` | right (source at the range matches the named thing) | def status(exc: BaseException) -> int / None: ¦ """The HTTP status an  |
| 45 | `bedrock.py:93-101` | right (source at the range matches the named thing) | def detail(exc: BaseException) -> str: ¦ """The HTTP status and the er |
| 46 | `extract.py:47` | right (source at the range matches the named thing) | reply = llm.chat( |
| 46 | `evals.py:73` | right (source at the range matches the named thing) | reply = llm.chat( |
| 46 | `guard/judge.py:72` | right (source at the range matches the named thing) | reply = self.llm.chat( |
| 46 | `runtime/agent_loop.py:425` | right (source at the range matches the named thing) | reply = self.llm.chat( |
| 46 | `k1b/loop.py:94` | right (source at the range matches the named thing) | box["reply"] = llm.chat(*args, **kwargs)  # type: ignore[arg-type] |
| 46 | `demos/ask-your-data/askdata/pipeline.py:155` | right (source at the range matches the named thing) | reply = self.llm.chat( |
| 46 | `guard/bedrock_guardrail.py:101` | right (source at the range matches the named thing) | resp = self._client.apply_guardrail( |
| 47 | `runtime/agent_loop.py:184-194` | right (source at the range matches the named thing) | def __init__( ¦ self, ¦ registry: Registry, |
| 47 | `tests/k5_support.py:160-211` | right (source at the range matches the named thing) | def build_runtime( ¦ cfg_dir: Path, ¦ llm, |
| 47 | `app.py:162` | right (source at the range matches the named thing) | llm = llm or make("llm", b.llm, secrets, routes=cfg.routes) |
| 47 | `app.py:90-98` | right (source at the range matches the named thing) | if sources and live: ¦ # A source handed in as an object would replace |
| 48 | `cli.py:146-153` | right (source at the range matches the named thing) | if args.cmd == "gate": ¦ b = cfg.backends ¦ run = evals.gate( |
| 48 | `cli.py:221-222` | right (source at the range matches the named thing) | llm = make("llm", cfg.backends.llm, secrets, routes=cfg.routes) ¦ dete |
| 48 | `cli.py:183-190` | right (source at the range matches the named thing) | try: ¦ secrets = make("secrets", b.secrets) ¦ # Same start-up probe as |
| 48 | `cli.py:173-182` | right (source at the range matches the named thing) | if b.store.kind == "memory": ¦ # The memory store lives inside one run |
| 48 | `evals.py:101-110` | right (source at the range matches the named thing) | # An llm_judge is qualified by its own golden set on the same model cl |
| 49 | `llm/fake.py:39-40` | right (source at the range matches the named thing) | doc = documents[0] if documents else json.dumps(messages, sort_keys=Tr |
| 49 | `tests/k5_support.py:124` | right (source at the range matches the named thing) | class ScriptLLM: |
| 49 | `llm/fake.py:21` | right (source at the range matches the named thing) | class FakeLLM: |
| 50 | `audit/chain.py:134-149` | right (source at the range matches the named thing) | @dataclass ¦ class Verification: ¦ rows: int = 0 |
| 50 | `chain.py:363-383` | right (source at the range matches the named thing) | def verify_rows( ¦ rows: list, ¦ checkpoints: list, |
| 50 | `chain.py:171` | right (source at the range matches the named thing) | self.checkpoint_every = checkpoint_every |
| 50 | `anchor_s3.py:70` | right (source at the range matches the named thing) | def all(self) -> dict[int, tuple[str, str]]: |
| 50 | `cli.py:349-363` | right (source at the range matches the named thing) | def audit_verify(audit) -> int: ¦ """Recompute the chain, every checkp |
| 51 | `audit/signer.py:104-108` | right (source at the range matches the named thing) | else: ¦ path = Path(settings.private_key_path) ¦ if not path.is_file() |
| 51 | `actions/secrets_file.py:34-64` | right (source at the range matches the named thing) | # ConfigError on `..`, absolute names or links out of the folder. The  |
| 52 | `agent_loop.py:83` | right (source at the range matches the named thing) | GUARD_STOP_REASONS = frozenset( |
| 53 | `config.py:317` | right (source at the range matches the named thing) | environment: Literal["dev", "pilot", "prod"] |
| 53 | `deferred.py:33` | right (source at the range matches the named thing) | LIVE = ("pilot", "prod") |
| 53 | `backends/table.py:593-602` | right (source at the range matches the named thing) | DEV_ONLY: frozenset[tuple[str, str]] = frozenset( ¦ { ¦ ("llm", "fake" |
| 53 | `config.py:366-370` | right (source at the range matches the named thing) | if self.environment != "dev": ¦ refused = [ ¦ f"{c}: {s.kind}" for c,  |
| 53 | `config.py:451-454` | WRONG: `Money =` is at config.py:47 (line 45 is blank) | except ConfigError: ¦ raise ¦ except (ValueError, TypeError, yaml.YAML |
| 53 | `config.py:400-415` | right (source at the range matches the named thing) | class _UniqueKeyLoader(yaml.SafeLoader): ¦ """A duplicate mapping key  |
| 54 | `config.py:45` | WRONG: `Money =` is at config.py:47 (line 45 is blank) |  |
| 54 | `config.py:57-58` | right (source at the range matches the named thing) | input_usd_per_mtok: Money ¦ output_usd_per_mtok: Money |
| 54 | `registry.py:33-37` | right (source at the range matches the named thing) | class Budget(BaseModel): ¦ model_config = ConfigDict(extra="forbid", f |
| 54 | `registry.py:53` | right (source at the range matches the named thing) | max_run_usd: Money / None = ( |
| 54 | `models.py:294` | right (source at the range matches the named thing) | cost_usd: Decimal = Decimal(0) |
| 54 | `models.py:305` | right (source at the range matches the named thing) | cost_usd: Decimal = Decimal( |
| 54 | `models.py:98` | right (source at the range matches the named thing) | cost_usd: Decimal = Decimal(0) |
| 55 | `models.py:218-222` | right (source at the range matches the named thing) | class DeadLetter(Shape): ¦ run_id: str ¦ reason: str |
| 55 | `extract.py:18-25` | right (source at the range matches the named thing) | @dataclass ¦ class Valid: ¦ data: BaseModel |
| 55 | `guard/runmap.py:218-227` | right (source at the range matches the named thing) | def storable(mapping: dict[str, str], kinds: frozenset[str] / None = N |
| 55 | `runmap.py:560-568` | right (source at the range matches the named thing) | def restore_value(value: Any, mapping: dict[str, str], kinds: frozense |
| 55 | `defaults.py:108-122` | right (source at the range matches the named thing) | STORED_KINDS = ( ¦ "ACCOUNTID", ¦ "ADDRESS", |
| 55 | `runmap.py:275` | right (source at the range matches the named thing) | def escape_placeholders(text: str) -> str: |
| 55 | `evals.py:63` | right (source at the range matches the named thing) | doc = runmap.redact_untrusted(doc.decode("utf-8", "replace"), {}).enco |
| 56 | `guard/injection.py:85-101` | right (source at the range matches the named thing) | def injection_check(detector: Detector, text: str, source: str) -> Ver |
| 56 | `judge.py:100-109` | right (source at the range matches the named thing) | def qualify(judge: JudgeDetector, golden: Path) -> tuple[int, int]: ¦  |
| 56 | `retry.py:97-99` | right (source at the range matches the named thing) | except Exception as exc:  # every failure is classified below, never s |
| 57 | `backends/factory.py:17-54` | right (source at the range matches the named thing) | @dataclass(frozen=True) ¦ class Deps: ¦ """What a factory receives bes |
| 57 | `backends/table.py:570-579` | right (source at the range matches the named thing) | ALLOWED: dict[str, frozenset[str]] = { ¦ "secrets": frozenset(), ¦ "si |
| 57 | `llm/anthropic.py:80-88` | right (source at the range matches the named thing) | def make(settings: Any, deps: Any) -> AnthropicLLM: ¦ name = settings. |
| 57 | `llm/common.py:200-206` | right (source at the range matches the named thing) | def __init__( ¦ self, ¦ routes: dict[str, Any], |
| 59 | `store/protocol.py:151-160` | right (source at the range matches the named thing) | def missing_methods(store: object) -> list[str]: ¦ """The methods of ` |
| 59 | `app.py:147-150` | right (source at the range matches the named thing) | if lacking := missing_methods(store): ¦ raise ConfigError( ¦ f"the sto |
| 59 | `tests/test_k5_round6_contracts.py:14-16` | right (source at the range matches the named thing) | class OldStore: ¦ def create_run(self, run): ... ¦ def get_run(self, r |
| 59 | `tests/contracts/kinds/store_postgres.py:59-71` | right (source at the range matches the named thing) | class _SplitStore: ¦ """The runtime role for everything, the purge rol |
| 60 | `store/migrate.py:46-67` | right (source at the range matches the named thing) | GRANTS: dict[str, Grant] = { ¦ "runs": Grant("table", _RW, portal=True |
| 61 | `cli.py:115-117` | right (source at the range matches the named thing) | rep.add_argument( ¦ "--max-usd", required=True, type=_money, help="tot |
| 62 | `openai_compat.py:122,131` | right (source at the range matches the named thing) | used = [used[0] + (got.tokens[0] or 0), used[1] + (got.tokens[1] or 0) |
| 62 | `llm/common.py:59-62` | right (source at the range matches the named thing) | def estimate_tokens(text: str) -> int: ¦ """For a provider that report |
| 62 | `common.py:164-165` | right (source at the range matches the named thing) | tokens_in = tokens[0] or estimate_tokens(sent) ¦ tokens_out = tokens[1 |
| 62 | `tests/k5_support.py:156` | right (source at the range matches the named thing) | def everything_sent(self) -> str: |
| 62 | `store/postgres.py:146` | right (source at the range matches the named thing) | conn = psycopg.connect(dsn, autocommit=True, connect_timeout=10, **ext |
| 63 | `llm/common.py:208-220` | right (source at the range matches the named thing) | def chat( ¦ self, ¦ messages: list[dict[str, Any]], |
| 63 | `anthropic.py:106` | right (source at the range matches the named thing) | def _chat(self, route, system, turns, specs, forced, output_schema) -> |
| 63 | `bedrock.py:128` | right (source at the range matches the named thing) | def _chat(self, route, system, turns, specs, forced, output_schema) -> |
| 63 | `gemini.py:54` | right (source at the range matches the named thing) | def _chat(self, route, system, turns, specs, forced, output_schema) -> |
| 63 | `openai_compat.py:94` | right (source at the range matches the named thing) | def _chat(self, route, system, turns, specs, forced, output_schema) -> |
| 64 | `store/postgres.py:191-197` | right (source at the range matches the named thing) |  ¦ class PostgresStore: ¦ # ponytail: one connection behind one lock p |
| 66 | `tests/test_p5p6_followups.py:101` | right (source at the range matches the named thing) | rt.detector = AnyOf([RegexDetector(0.5), judge(model)]) |
| 66 | `tests/test_p6_detectors.py:183-194,264,364` | right (source at the range matches the named thing) | def test_the_judge_charge_is_visible_in_limits(cfg_dir): ¦ plain, cfg  |
| 66 | `tests/test_k5_tools.py:608` | right (source at the range matches the named thing) | rt.llm = ScriptLLM([{"tool": "app"}, {"propose": mine, "evidence": evi |
| 93 | `tests/test_s5_runtime.py:107-111` | right (source at the range matches the named thing) | def test_budget_crossed_by_this_call_is_denied_at_the_gate(cfg_dir): ¦ |
| 93 | `tests/test_k5_tools.py:723-731` | right (source at the range matches the named thing) | def test_k5_run_budget_stops_run(tmp_path): ¦ k5_tools.RESULTS["app"]  |
| 93 | `agent_loop.py:245-249` | right (source at the range matches the named thing) | cap = self.registry.agents[run.agent_id].max_run_usd ¦ if cap is not N |
| 95 | `k1b/replay.py:85-91` | right (source at the range matches the named thing) | def _refuse_zero_price(registry: Registry, agent_id: str, llm_kind: st |
| 102 | `anchor_s3.py:1-12` | right (source at the range matches the named thing) | """Checkpoint anchors in an S3 bucket under Object Lock (`pip install  |
| 128 | `retry.py:92-107` | right (source at the range matches the named thing) | for attempt in range(1, max_attempts + 1): ¦ try: ¦ return call() |
| 128 | `backends/table.py:40` | right (source at the range matches the named thing) | max_attempts: int = Field(default=3, ge=1, le=10) |
| 128 | `llm/openai_compat.py:117-129` | right (source at the range matches the named thing) | started, used = time.monotonic(), [0, 0] ¦ for _ in range(2):  # the f |
| 128 | `models.py:23` | right (source at the range matches the named thing) | def new_id(prefix: str) -> str: |
| 132 | `store/migrate.py:71` | right (source at the range matches the named thing) | _FILE = re.compile(r"(\d{4})_[a-z0-9_]+\.sql") |
| 182 | `migrate.py:71-86` | right (source at the range matches the named thing) | _FILE = re.compile(r"(\d{4})_[a-z0-9_]+\.sql") ¦ _CREATE = re.compile( |
| 250 | `store/migrate.py:46-67` | right (source at the range matches the named thing) | GRANTS: dict[str, Grant] = { ¦ "runs": Grant("table", _RW, portal=True |
| 251 | `cli.py:99-103` | right (source at the range matches the named thing) | mig.add_argument( ¦ "--purge-role", ¦ help="grant this database role t |
| 251 | `app.py:152-160` | right (source at the range matches the named thing) | if purge_name := getattr(b.store, "purge_dsn_secret_name", None): ¦ #  |
| 256 | `store/postgres.py:191-197` | right (source at the range matches the named thing) |  ¦ class PostgresStore: ¦ # ponytail: one connection behind one lock p |
| 283 | `tests/test_p7_store.py:184` | right (source at the range matches the named thing) | s.add_spend("a", day, Decimal("0.01")) |
| 283 | `tests/test_s1_foundation.py:161-164` | right (source at the range matches the named thing) | store.add_spend("a", today, Decimal("0.40")) ¦ day, month = store.add_ |
| 284 | `migrate.py:47` | right (source at the range matches the named thing) | "runs": Grant("table", _RW, portal=True, purge_cols=("run_id", "state" |
| 288 | `tests/test_p7_store.py:184` | right (source at the range matches the named thing) | s.add_spend("a", day, Decimal("0.01")) |
| 288 | `tests/test_s1_foundation.py:161-164` | right (source at the range matches the named thing) | store.add_spend("a", today, Decimal("0.40")) ¦ day, month = store.add_ |
| 288 | `tests/contracts/test_store.py:179-189` | right (source at the range matches the named thing) | store.add_spend("a", today, Decimal("0.40")) ¦ assert store.add_spend( |
| 289 | `tests/contracts/kinds/store_postgres.py:59-71` | right (source at the range matches the named thing) | class _SplitStore: ¦ """The runtime role for everything, the purge rol |
| 313 | `llm/openai_compat.py:122,131` | right (source at the range matches the named thing) | used = [used[0] + (got.tokens[0] or 0), used[1] + (got.tokens[1] or 0) |
| 315 | `bedrock.py:115-116` | right (source at the range matches the named thing) | retryable = staticmethod(retryable) ¦ detail = staticmethod(detail) |
| 315 | `anthropic.py:93` | right (source at the range matches the named thing) | retryable = staticmethod(retryable) |
| 315 | `bedrock.py:93-101` | right (source at the range matches the named thing) | def detail(exc: BaseException) -> str: ¦ """The HTTP status and the er |
| 317 | `common.py:164-165` | right (source at the range matches the named thing) | tokens_in = tokens[0] or estimate_tokens(sent) ¦ tokens_out = tokens[1 |
| 317 | `tests/test_k5_tools.py:723-731` | right (source at the range matches the named thing) | def test_k5_run_budget_stops_run(tmp_path): ¦ k5_tools.RESULTS["app"]  |
| 317 | `anthropic.py:107-120` | right (source at the range matches the named thing) | request: dict[str, Any] = { ¦ "model": route.model_id, ¦ "max_tokens": |
| 317 | `bedrock.py:132-154` | right (source at the range matches the named thing) | request: dict[str, Any] = { ¦ "modelId": route.model_id, ¦ "messages": |
| 317 | `gemini.py:54-83` | right (source at the range matches the named thing) | def _chat(self, route, system, turns, specs, forced, output_schema) -> |
| 317 | `gemini.py:97-100` | right (source at the range matches the named thing) | usage = resp.get("usageMetadata") or {} ¦ # Thinking is billed as outp |
| 317 | `openai_compat.py:94-116` | right (source at the range matches the named thing) | def _chat(self, route, system, turns, specs, forced, output_schema) -> |
| 319 | `config.py:55-60` | right (source at the range matches the named thing) | class Route(_Strict): ¦ model_id: str ¦ input_usd_per_mtok: Money |
| 321 | `k1b/replay.py:85-91` | right (source at the range matches the named thing) | def _refuse_zero_price(registry: Registry, agent_id: str, llm_kind: st |
| 321 | `backends/table.py:66-85` | right (source at the range matches the named thing) |  ¦  ¦ _LOOPBACK = {"127.0.0.1", "localhost", "::1"} |
| 325 | `k1b/loop.py:115` | right (source at the range matches the named thing) | def worst_case_usd(route: Route, system: str, messages: list[dict[str, |
| 325 | `common.py:86-100` | right (source at the range matches the named thing) | def turns( ¦ messages: list[dict[str, Any]], documents: list[bytes] /  |
| 325 | `common.py:65-83` | right (source at the range matches the named thing) | def tools_for( ¦ tools: list[dict[str, Any]] / None, output_schema: di |
| 328 | `backends/table.py:34-40` | right (source at the range matches the named thing) |  ¦  ¦ class _LLMSettings(KindSettings): |
| 329 | `limits.py:48-51` | right (source at the range matches the named thing) | def reset(self, by: str) -> None: ¦ """Removing a safety control is au |
| 329 | `app.py:152-160` | right (source at the range matches the named thing) | if purge_name := getattr(b.store, "purge_dsn_secret_name", None): ¦ #  |
| 357 | `llm/common.py:208-220` | right (source at the range matches the named thing) | def chat( ¦ self, ¦ messages: list[dict[str, Any]], |
| 357 | `anthropic.py:106` | right (source at the range matches the named thing) | def _chat(self, route, system, turns, specs, forced, output_schema) -> |
| 357 | `bedrock.py:128` | right (source at the range matches the named thing) | def _chat(self, route, system, turns, specs, forced, output_schema) -> |
| 357 | `gemini.py:54` | right (source at the range matches the named thing) | def _chat(self, route, system, turns, specs, forced, output_schema) -> |
| 357 | `openai_compat.py:94` | right (source at the range matches the named thing) | def _chat(self, route, system, turns, specs, forced, output_schema) -> |
| 386 | `retry.py:97-99` | right (source at the range matches the named thing) | except Exception as exc:  # every failure is classified below, never s |
| 409 | `retry.py:95-96` | right (source at the range matches the named thing) | except ProviderError: ¦ raise |
| 409 | `openai_compat.py:117-129` | right (source at the range matches the named thing) | started, used = time.monotonic(), [0, 0] ¦ for _ in range(2):  # the f |
| 414 | `backends/factory.py:17-26` | right (source at the range matches the named thing) | @dataclass(frozen=True) ¦ class Deps: ¦ """What a factory receives bes |
| 414 | `backends/table.py:570-579` | right (source at the range matches the named thing) | ALLOWED: dict[str, frozenset[str]] = { ¦ "secrets": frozenset(), ¦ "si |
| 414 | `backends/builtin.py:39-40` | right (source at the range matches the named thing) | def fake_llm(settings, deps) -> FakeLLM: ¦ return FakeLLM(settings.rec |
| 414 | `common.py:200-206` | right (source at the range matches the named thing) | def __init__( ¦ self, ¦ routes: dict[str, Any], |
| 421 | `agent_loop.py:184-216` | right (source at the range matches the named thing) | def __init__( ¦ self, ¦ registry: Registry, |
| 421 | `tests/test_k5_fixes1.py:73` | right (source at the range matches the named thing) | Runtime(reg, MemoryStore(), None, None, None, None, ["test-agent"], Ho |
| 421 | `tests/test_k5_tools.py:608` | right (source at the range matches the named thing) | rt.llm = ScriptLLM([{"tool": "app"}, {"propose": mine, "evidence": evi |
| 422 | `app.py:165` | right (source at the range matches the named thing) | members = [make("detector", d, secrets, llm=llm) for d in b.detector] |
| 422 | `app.py:90-98` | right (source at the range matches the named thing) | if sources and live: ¦ # A source handed in as an object would replace |
| 423 | `tests/test_p6_detectors.py:183-194` | right (source at the range matches the named thing) | def test_the_judge_charge_is_visible_in_limits(cfg_dir): ¦ plain, cfg  |
| 423 | `tests/test_p5p6_followups.py:101` | right (source at the range matches the named thing) | rt.detector = AnyOf([RegexDetector(0.5), judge(model)]) |
| 423 | `tests/test_p6_detectors.py:264,364` | right (source at the range matches the named thing) | rt.detector = AnyOf([RegexDetector(0.5), judge(model)]) |
| 423 | `tests/test_k5_tools.py:608` | right (source at the range matches the named thing) | rt.llm = ScriptLLM([{"tool": "app"}, {"propose": mine, "evidence": evi |
| 423 | `tests/test_p5p6_followups.py:101` | right (source at the range matches the named thing) | rt.detector = AnyOf([RegexDetector(0.5), judge(model)]) |
| 424 | `tests/test_k5_tools.py:723-731` | right (source at the range matches the named thing) | def test_k5_run_budget_stops_run(tmp_path): ¦ k5_tools.RESULTS["app"]  |
| 424 | `agent_loop.py:245-249` | right (source at the range matches the named thing) | cap = self.registry.agents[run.agent_id].max_run_usd ¦ if cap is not N |
| 430 | `app.py:152-160` | right (source at the range matches the named thing) | if purge_name := getattr(b.store, "purge_dsn_secret_name", None): ¦ #  |
| 430 | `app.py:171` | right (source at the range matches the named thing) | limits = Limits(store, audit, reg) |
| 430 | `app.py:73` | right (source at the range matches the named thing) | clock: Callable[[], datetime] = now, |
| 431 | `app.py:162` | right (source at the range matches the named thing) | llm = llm or make("llm", b.llm, secrets, routes=cfg.routes) |
| 432 | `app.py:165` | right (source at the range matches the named thing) | members = [make("detector", d, secrets, llm=llm) for d in b.detector] |
| 433 | `app.py:90-98` | right (source at the range matches the named thing) | if sources and live: ¦ # A source handed in as an object would replace |
| 434 | `cli.py:221-222` | right (source at the range matches the named thing) | llm = make("llm", cfg.backends.llm, secrets, routes=cfg.routes) ¦ dete |
| 435 | `cli.py:146-153` | right (source at the range matches the named thing) | if args.cmd == "gate": ¦ b = cfg.backends ¦ run = evals.gate( |
| 437 | `guard/injection.py:85-101` | right (source at the range matches the named thing) | def injection_check(detector: Detector, text: str, source: str) -> Ver |
| 438 | `llm/retry.py:95-96` | right (source at the range matches the named thing) | except ProviderError: ¦ raise |
| 441 | `k1b/loop.py:104` | right (source at the range matches the named thing) | t = threading.Thread(target=work, daemon=True, name="k1b-llm-call") |
| 447 | `guard/judge.py:72` | right (source at the range matches the named thing) | reply = self.llm.chat( |
| 447 | `injection.py:85-101` | right (source at the range matches the named thing) | def injection_check(detector: Detector, text: str, source: str) -> Ver |
| 448 | `k1b/loop.py:94` | right (source at the range matches the named thing) | box["reply"] = llm.chat(*args, **kwargs)  # type: ignore[arg-type] |
| 448 | `k1b/replay.py:175` | right (source at the range matches the named thing) | stop = o.halt |
| 449 | `extract.py:47` | right (source at the range matches the named thing) | reply = llm.chat( |
| 450 | `evals.py:73` | right (source at the range matches the named thing) | reply = llm.chat( |
| 451 | `tests/test_p6_detectors.py:351` | right (import line; make("detector" is :355 as stated) | from hadavin_sdk.guard import bedrock_guardrail |
| 456 | `agent_loop.py:425` | right (source at the range matches the named thing) | reply = self.llm.chat( |
| 456 | `guard/judge.py:72` | right (source at the range matches the named thing) | reply = self.llm.chat( |
| 457 | `evals.py:73` | right (source at the range matches the named thing) | reply = llm.chat( |
| 457 | `evals.py:109` | right (source at the range matches the named thing) | ok, total = judge.qualify(judge.JudgeDetector(llm, d.route, d.threshol |
| 458 | `extract.py:47` | right (source at the range matches the named thing) | reply = llm.chat( |
| 459 | `k1b/loop.py:94` | right (source at the range matches the named thing) | box["reply"] = llm.chat(*args, **kwargs)  # type: ignore[arg-type] |
| 459 | `k1b/loop.py:179` | right (source at the range matches the named thing) | budget.charge(reply.cost_usd) |
| 460 | `bedrock_guardrail.py:101` | right (source at the range matches the named thing) | resp = self._client.apply_guardrail( |
| 461 | `demos/ask-your-data/askdata/pipeline.py:155` | right (source at the range matches the named thing) | reply = self.llm.chat( |
| 465 | `agent_loop.py:440-441` | right (source at the range matches the named thing) | self.limits.charge(agent_id, reply.cost_usd) ¦ self.store.add_cost(run |
| 467 | `guard/producers.py:5` | right (source at the range matches the named thing) | that calls a model (`.chat(` or `.apply_guardrail(`) is not listed, or |
| 469 | `tests/contracts/kinds/llm_wire.py:66,91,119,192` | right (source at the range matches the named thing) | return AnthropicLLM(client, routes, 3, sleep=lambda s: None) |
| 469 | `tests/test_p5_llm.py:248` | right (source at the range matches the named thing) | llm = GeminiLLM(lambda: keys[-1], ROUTES, 5.0, 1) |
| 469 | `tests/warden_port/test_providers.py:65,123,148,172,198` | right (source at the range matches the named thing) | llm = make("llm", settings, routes=ROUTES) |
| 469 | `tests/warden_port/test_bedrock_provider_r16.py:74,79,90` | right (source at the range matches the named thing) | make("llm", BedrockSettings(kind="bedrock", region="contract-region-1" |
| 469 | `tests/test_p5p6_followups.py:300,302,417` | right (source at the range matches the named thing) | make("llm", settings, provider, routes=_route(moving)) |
| 469 | `tests/test_p5_llm.py:230,301` | right (source at the range matches the named thing) | llm = make("llm", settings, routes=ROUTES) |
| 469 | `tests/contracts/kinds/builtin.py:53` | right (source at the range matches the named thing) | llm = make("llm", FakeLLMSettings(kind="fake", recorded_dir=tmp_path), |
| 469 | `tests/test_k1b_replay.py:391` | right (source at the range matches the named thing) | env.run(ScriptedLLM([]), reg=reg, llm_kind="anthropic") |
| 469 | `tests/test_p1a_fixes.py:117` | right (source at the range matches the named thing) | update={"llm": reg.config.backends.llm.model_copy(update={"kind": "bed |
| 469 | `tests/test_p6_detectors.py:351` | right (import line; make("detector" is :355 as stated) | from hadavin_sdk.guard import bedrock_guardrail |
| 469 | `tests/test_p6_detectors.py:183-194` | right (source at the range matches the named thing) | def test_the_judge_charge_is_visible_in_limits(cfg_dir): ¦ plain, cfg  |
| 469 | `tests/test_k5_fixes1.py:73` | right (source at the range matches the named thing) | Runtime(reg, MemoryStore(), None, None, None, None, ["test-agent"], Ho |
| 469 | `tests/test_s5_runtime.py:107-111` | right (source at the range matches the named thing) | def test_budget_crossed_by_this_call_is_denied_at_the_gate(cfg_dir): ¦ |
| 469 | `tests/k5_support.py:160-211` | right (source at the range matches the named thing) | def build_runtime( ¦ cfg_dir: Path, ¦ llm, |
| 484 | `tests/test_k5_tools.py:608` | right (source at the range matches the named thing) | rt.llm = ScriptLLM([{"tool": "app"}, {"propose": mine, "evidence": evi |
| 489 | `registry.py:20` | right (source at the range matches the named thing) | from hadavin_sdk.config import Config, ConfigError, Money, confined, l |
| 502 | `config.py:45` | WRONG: `Money =` is at config.py:47 (line 45 is blank) |  |
| 503 | `cli.py:146-153` | right (source at the range matches the named thing) | if args.cmd == "gate": ¦ b = cfg.backends ¦ run = evals.gate( |
| 503 | `cli.py:183-190` | right (source at the range matches the named thing) | try: ¦ secrets = make("secrets", b.secrets) ¦ # Same start-up probe as |
| 503 | `evals.py:109` | right (source at the range matches the named thing) | ok, total = judge.qualify(judge.JudgeDetector(llm, d.route, d.threshol |
| 504 | `cli.py:221-222` | right (source at the range matches the named thing) | llm = make("llm", cfg.backends.llm, secrets, routes=cfg.routes) ¦ dete |
| 505 | `cli.py:93-95` | right (source at the range matches the named thing) | lim = sub.add_parser("limits", help="kill switch") ¦ lim.add_argument( |
| 505 | `cli.py:173-182` | right (source at the range matches the named thing) | if b.store.kind == "memory": ¦ # The memory store lives inside one run |
| 505 | `cli.py:173-182` | right (source at the range matches the named thing) | if b.store.kind == "memory": ¦ # The memory store lives inside one run |
| 509 | `registry.py:33-37` | right (source at the range matches the named thing) | class Budget(BaseModel): ¦ model_config = ConfigDict(extra="forbid", f |
| 510 | `models.py:294` | right (source at the range matches the named thing) | cost_usd: Decimal = Decimal(0) |
| 519 | `agent_loop.py:325-541` | right (source at the range matches the named thing) | def handle( ¦ self, ¦ agent_id: str, |
| 519 | `agent_loop.py:432-434` | right (source at the range matches the named thing) | except ( ¦ ProviderError ¦ ) as exc:  # a refused key or request must  |
| 521 | `agent_loop.py:318-322` | right (source at the range matches the named thing) | def _to(self, run: Run, new: RunState, reason: str / None = None) -> R |
| 532 | `agent_loop.py:245-249` | right (source at the range matches the named thing) | cap = self.registry.agents[run.agent_id].max_run_usd ¦ if cap is not N |
| 536 | `agent_loop.py:239-250` | right (source at the range matches the named thing) | def _limits_stop(self, run: Run, cited: list[str] / None = None) -> Ru |
| 538 | `agent_loop.py:569-597` | right (source at the range matches the named thing) | def _abstain(self, run: Run, new: RunState, reason: str / None, cited: |
| 542 | `app.py:161` | right (source at the range matches the named thing) | audit = make("audit", b.audit, secrets, store=store, signer=signer, an |
| 542 | `config.py:349-375` | right (source at the range matches the named thing) | @model_validator(mode="after") ¦ def _cross_checks(self) -> Config: ¦  |
| 542 | `config.py:451-454` | WRONG: `Money =` is at config.py:47 (line 45 is blank) | except ConfigError: ¦ raise ¦ except (ValueError, TypeError, yaml.YAML |
| 544 | `app.py:171` | right (source at the range matches the named thing) | limits = Limits(store, audit, reg) |
| 544 | `cli.py:209` | right (source at the range matches the named thing) | return kill_switch(Limits(store, audit, reg), args.action, args.by) |
| 544 | `tests/test_s5_runtime.py:28` | right (source at the range matches the named thing) | limits = Limits(store, audit, reg) |
| 544 | `tests/k5_support.py:206` | right (source at the range matches the named thing) | Limits(store, audit, reg), |
| 544 | `tests/test_k3_pilot.py:104` | right (source at the range matches the named thing) | Limits(store, audit, reg), |
| 544 | `tests/test_k5_postgres.py:58` | right (source at the range matches the named thing) | Limits(pg_store, audit, reg), |
| 544 | `tests/test_k5_round5.py:241` | right (source at the range matches the named thing) | reg, store, audit, ScriptLLM([]), RegexDetector(0.5), Limits(store, au |
| 544 | `tests/test_k5_tools.py:1133` | right (source at the range matches the named thing) | reg, store, audit, ScriptLLM([]), RegexDetector(0.5), Limits(store, au |
| 544 | `limits.py:18` | right (source at the range matches the named thing) | return self.store.add_spend(agent_id, now().date(), usd) |
| 544 | `app.py:73` | right (source at the range matches the named thing) | clock: Callable[[], datetime] = now, |
| 546 | `tests/test_k3_pilot_env.py:61` | right (source at the range matches the named thing) | "llm": {"kind": "openai_compat", "base_url": "https://llm.example/v1"} |
| 548 | `registry.py:338` | right (source at the range matches the named thing) | def _cross_check(config, agents, chains, contracts) -> list[str]: |
| 548 | `k1b/replay.py:85-91` | right (source at the range matches the named thing) | def _refuse_zero_price(registry: Registry, agent_id: str, llm_kind: st |
| 548 | `judge.py:3-4` | right (source at the range matches the named thing) | The only cloud-agnostic model detector: it runs on any configured llm  |
| 554 | `chain.py:161` | right (source at the range matches the named thing) | checkpoint_every: int = 100, |
| 554 | `backends/table.py:193` | right (source at the range matches the named thing) | checkpoint_every: int = Field(default=100, ge=1) |
| 554 | `backends/table.py:192-193` | right (source at the range matches the named thing) | class ChainSettings(KindSettings): ¦ checkpoint_every: int = Field(def |
| 556 | `anchor_gcs.py:69-85` | right (source at the range matches the named thing) | def probed(bucket: Any, settings) -> GcsAnchor: ¦ try: ¦ bucket.reload |
| 556 | `anchor_azure.py:83-96` | right (source at the range matches the named thing) | def probed(container: Any, settings) -> AzureBlobAnchor: ¦ try: ¦ prop |
| 558 | `cli.py:349-363` | right (source at the range matches the named thing) | def audit_verify(audit) -> int: ¦ """Recompute the chain, every checkp |
| 558 | `chain.py:171` | right (source at the range matches the named thing) | self.checkpoint_every = checkpoint_every |
| 558 | `chain.py:203` | right (source at the range matches the named thing) | if self.signer is not None and seq % self.checkpoint_every == 0: |
| 562 | `evals.py:63` | right (source at the range matches the named thing) | doc = runmap.redact_untrusted(doc.decode("utf-8", "replace"), {}).enco |
| 562 | `models.py:221` | right (source at the range matches the named thing) | errors: list[str] |
| 562 | `evals.py:63` | right (source at the range matches the named thing) | doc = runmap.redact_untrusted(doc.decode("utf-8", "replace"), {}).enco |
| 562 | `extract.py:58` | right (source at the range matches the named thing) | errors.append(f"{exc.__class__.__name__}: {safe_head(str(exc), 300)}") |
| 570 | `llm/fake.py:39-40` | right (source at the range matches the named thing) | doc = documents[0] if documents else json.dumps(messages, sort_keys=Tr |
| 574 | `actions/secrets_file.py:49-64` | right (source at the range matches the named thing) | with os.fdopen(fd, "rb") as f: ¦ mode = os.fstat(f.fileno()).st_mode ¦ |
| 576 | `signer.py:104-108` | right (source at the range matches the named thing) | else: ¦ path = Path(settings.private_key_path) ¦ if not path.is_file() |
| 576 | `secrets_file.py:54` | right (source at the range matches the named thing) | if os.name != "nt" and mode & (stat.S_IROTH / stat.S_IWGRP / stat.S_IW |
| 577 | `secrets_file.py:54` | right (source at the range matches the named thing) | if os.name != "nt" and mode & (stat.S_IROTH / stat.S_IWGRP / stat.S_IW |
| 577 | `config.py:395-396` | right (source at the range matches the named thing) | if b.signer.kind == "ed25519_local" and b.signer.private_key_path is n |
| 577 | `signer.py:182` | right (source at the range matches the named thing) | _create(private_real, pem, 0o600) |
| 578 | `audit/signer.py:197` | right (source at the range matches the named thing) | return _private_key(path.read_bytes(), passphrase, str(path)) |
| 578 | `audit/signer.py:209` | right (source at the range matches the named thing) | key = serialization.load_pem_public_key(path.read_bytes()) |
| 579 | `tests/test_lockin_guard.py:68-75` | right (source at the range matches the named thing) | LIBRARY_IMPORTS: dict[str, set[str]] = {  # open-source libraries kept |
| 585 | `tests/test_g4_parity.py:98,221-222` | right (source at the range matches the named thing) | "update its set of rules", |
| 608 | `gate.py:4` | right (source at the range matches the named thing) | (`sanitise_text` and its helpers) and G4 (`withhold_commands`, rewritt |
| 608 | `gate.py:366-377` | right (source at the range matches the named thing) |  ¦ # G4: no command a person could paste to change a system reaches th |
| 608 | `channel.py:19-21` | right (source at the range matches the named thing) | """WARDEN's G3 cleaning (`gate.sanitise_text`): no link, image, HTML,  |
| 609 | `gate.py:546` | right (source at the range matches the named thing) | _TOKEN = re.compile(r"[^\S\n]+([^\s]+)") |
| 609 | `gate.py:695` | right (source at the range matches the named thing) | end = text.find("\n", m.end()) |
| 610 | `gate.py:608-615` | right (source at the range matches the named thing) | def _story(text: str, prog: str, s: int, e: int, toks: list[str]) -> b |
| 612 | `gate.py:674` | right (source at the range matches the named thing) | r"/\brm\s+(?:-[a-zA-Z]*[rRf][a-zA-Z]*/--recursive/--force)(?=\s+\S)" |
| 612 | `gate.py:540` | right (source at the range matches the named thing) | _NAMES = ["aws", *_VERB_FIRST, *_WORD_RUN] |
| 613 | `gate.py:404` | right (source at the range matches the named thing) | _AWS_READ_PREFIXES = ("describe-", "get-", "list-", "head-", "batch-ge |
| 618 | `gate.py:573-589` | right (source at the range matches the named thing) | def _subcommands(toks: list[str]) -> list[str]: ¦ """The subcommand wo |
| 623 | `guard/redact.py:472` | right (source at the range matches the named thing) | "PHONE", |
| 625 | `tests/warden_port/privacy_corpus.py:42` | right (source at the range matches the named thing) | "card 4111 1111 1111 1111", |
| 625 | `tests/warden_port/test_redaction.py:309,356` | right (source at the range matches the named thing) | for pan in ("4111 1111 1111 1111", "4111-1111-1111-1111"): |
| 627 | `k1b/redaction.py:103` | right (source at the range matches the named thing) | def _pair(key: str, value: str, f: Callable[[str], str]) -> str: |
| 633 | `config.py:451-454` | WRONG: `Money =` is at config.py:47 (line 45 is blank) | except ConfigError: ¦ raise ¦ except (ValueError, TypeError, yaml.YAML |
| 633 | `config.py:317` | right (source at the range matches the named thing) | environment: Literal["dev", "pilot", "prod"] |
| 633 | `backends/table.py:593` | right (source at the range matches the named thing) | DEV_ONLY: frozenset[tuple[str, str]] = frozenset( |
| 633 | `tests/test_lockin_guard.py:18,430` | right (source at the range matches the named thing) | from hadavin_sdk.backends.table import DEV_ONLY, NOT_PROD, TABLE |
| 633 | `tests/fixtures/config/config.yaml:2` | right (source at the range matches the named thing) | environment: dev |
| 633 | `tests/test_p4_secrets.py:106` | right (source at the range matches the named thing) | def _config(tmp_path, secrets, environment="dev"): |
| 633 | `tests/warden_port/test_audit_chain.py:568` | right (source at the range matches the named thing) | found = _anchor_refusals("dev", _backends(ANCHOR, KMS, local)) |
| 633 | `tests/test_p1b_backends.py:89-91` | right (source at the range matches the named thing) | @pytest.mark.parametrize("env", ["pilot", "prod"]) ¦ def test_dev_only |
| 633 | `actions/secrets_env.py:1` | right (source at the range matches the named thing) | """`env` secrets: read from environment variables (`dev` only, by the  |
| 633 | `audit/signer.py:64,98` | right (source at the range matches the named thing) | """An Ed25519 key in a PEM file (dev and pilot; refused in prod by the |
| 633 | `table.py:126,214,254,591` | right (source at the range matches the named thing) | # (`require`, `disable`) is an explicit opt-down for dev, refused with |
| 633 | `config.py:346` | right (source at the range matches the named thing) | )  # dev executor only |
| 633 | `defaults.py:100` | right (source at the range matches the named thing) | EXECUTOR_TIMEOUT_S = 10.0  # the dev executor's per-call timeout (Conf |
| 633 | `registry.py:50` | right (source at the range matches the named thing) | # Per-action autonomy. None only in dev (the slice-1 gate path). Not p |
| 633 | `tools.py:361` | right (source at the range matches the named thing) | Without a pin (dev only; pilot and prod require one) it is an ordinary |
| 633 | `agent_loop.py:179,553,572` | right (source at the range matches the named thing) | # Keys the HMAC of the restored inputs on the gate's audit event (None |
| 633 | `actions/contract.py:34` | right (source at the range matches the named thing) | """Hadavin-run execution (Phase 2): refused in pilot and prod, kept in |
| 633 | `store/postgres.py:75,90` | right (source at the range matches the named thing) | captured by an impostor); an explicit weaker `sslmode` is an opt-down  |
| 633 | `guard/redact.py:1162` | right (source at the range matches the named thing) | "dev", |
| 634 | `backends/table.py:155` | right (source at the range matches the named thing) | retain_days: int = Field(default=1, ge=1) |
| 634 | `config.py:377-398` | right (source at the range matches the named thing) | def _anchor_refusals(environment: str, b: Backends) -> list[str]: ¦ "" |
| 634 | `table.py:150-157` | right (source at the range matches the named thing) | class _AnchorSettings(KindSettings): ¦ """Every anchor kind: COMPLIANC |
| 634 | `anchor_gcs.py:69-85` | right (source at the range matches the named thing) | def probed(bucket: Any, settings) -> GcsAnchor: ¦ try: ¦ bucket.reload |
| 634 | `anchor_azure.py:83-96` | right (source at the range matches the named thing) | def probed(container: Any, settings) -> AzureBlobAnchor: ¦ try: ¦ prop |
| 644 | `cli.py:183-190` | right (source at the range matches the named thing) | try: ¦ secrets = make("secrets", b.secrets) ¦ # Same start-up probe as |
| 666 | `tests/test_s5_runtime.py:107-111` | right (source at the range matches the named thing) | def test_budget_crossed_by_this_call_is_denied_at_the_gate(cfg_dir): ¦ |
| 686 | `tests/k5_support.py:160-211` | right (source at the range matches the named thing) | def build_runtime( ¦ cfg_dir: Path, ¦ llm, |
| 693 | `tests/test_k3_pilot_env.py:61` | right (source at the range matches the named thing) | "llm": {"kind": "openai_compat", "base_url": "https://llm.example/v1"} |
| 720 | `test_s5_runtime.py:107-111` | right (source at the range matches the named thing) | def test_budget_crossed_by_this_call_is_denied_at_the_gate(cfg_dir): ¦ |
