# Tool-fact register

One shared, dated list of facts about outside tools. Tickets cite a line by its id (for example "T-014"), they do not restate the fact.

## Rules
1. Every fact has an id, the tool, the fact, the source URL, the date it was read, an UNVERIFIED flag and the tickets that cite it.
2. UNVERIFIED = no means the audit read the fact from a page and kept its URL and date. UNVERIFIED = yes means the audit marked it UNVERIFIED, took it from memory, from web-search result text, from a tool run or a package read on the audit machine, or from a ticket line without a page. A row with no URL is always UNVERIFIED = yes. No URL or date has been invented. Where the audit gave a date for a run or a read without a page, it is kept in the date column and the fact text says how it was obtained.
3. Re-check a fact older than 90 days when you touch the ticket that cites it. A fact older than 90 days counts as UNVERIFIED whatever its flag says. The re-check updates the row (new date, URL) or adds a new row; it never edits history silently.
4. Sources: reviews/rung-audit-1-part-A.md to part-E.md, reviews/rung-audit-1.md and the RUNG TABLE build notes in tickets/. Dates are the audit's own (read 2026-11-06, UTC). URLs are written as the audit wrote them (host and path, no scheme).
5. Estimates of agent-hours are not tool facts and are not listed here.

| id | tool | fact | source URL | date read | UNVERIFIED? | cited by |
|---|---|---|---|---|---|---|
| T-001 | kube-linter | Check list has run-as-non-root, no-read-only-root-fs, privilege-escalation-container, privileged-container and host-network/pid/ipc, all on by default. Its capability check forbids only NET_RAW by default, not drop ALL. No seccomp check is listed. | github.com/stackrox/kube-linter (docs/generated/checks.md) | 2026-11-06 | no | AK-G16 |
| T-002 | kube-linter | env-var-secret is on by default; read-secret-from-env-var is off. | github.com/stackrox/kube-linter (docs/generated/checks.md) | 2026-11-06 | no | AK-G16 |
| T-003 | kube-linter | unset-cpu-requirements and unset-memory-requirements are on by default. | github.com/stackrox/kube-linter (docs/generated/checks.md) | 2026-11-06 | no | AK-G16 |
| T-004 | kube-linter | No check for automountServiceAccountToken. Nothing for defaultMode with fsGroup, one service account per workload, volume secret names or projected tokens. No check on the migrate.GRANTS pilot gate. | github.com/stackrox/kube-linter (docs/generated/checks.md) | 2026-11-06 | no | AK-G16 |
| T-005 | kube-linter | non-isolated-pod (off by default) only checks that some network policy selects the pod; no tool listed does CIDR-minus-except arithmetic. job-ttl-seconds-after-finished is the only CronJob check. latest-tag flags only latest or no tag, not a missing digest. | github.com/stackrox/kube-linter (docs/generated/checks.md) | 2026-11-06 | no | AK-G16 |
| T-006 | kube-linter | Whether the capability template can be set to require drop ALL; whether unset-cpu-requirements and unset-memory-requirements flag requests without limits. |  |  | yes | AK-G16 |
| T-007 | kubeconform | Apache-2.0. -strict means disallow additional properties not in schema or duplicated keys; works offline with -schema-location. Cannot refuse a valid schema field that we do not allow (initContainers, hostPath, a second container). | github.com/yannh/kubeconform | 2026-11-06 | no | AK-G16 |
| T-008 | kubeconform | How -strict treats YAML aliases, merge keys and tags. |  |  | yes | AK-G16 |
| T-009 | Helm | Apache-2.0; v4 is current. | github.com/helm/helm | 2026-11-06 | no | AK-G16 |
| T-010 | Helm | Whether values.schema.json would remove the template-injection concern. |  |  | yes | AK-G16 |
| T-011 | Kustomize | Facts not fetched (base plus generated patch as a renderer option). |  |  | yes | AK-G16 |
| T-012 | Kyverno | Apache-2.0. | github.com/kyverno/kyverno | 2026-11-06 | no | AK-G16 |
| T-013 | Kyverno | CLI applies policies to local files without a cluster (kyverno apply <policy> --resource <file>): web-search result text only (main.kyverno.io, kodekloud notes), read 2026-11-06; not a fetched official page. |  |  | yes | AK-G16 |
| T-014 | Kyverno | Library folder fetch showed only other/verify-image-ivpol; a library policy for require-image-digest or no-automounted-token is not confirmed. Whether CIDR-minus-except can be written in its expression language is unknown. |  |  | yes | AK-G16 |
| T-015 | Trivy | Whether it scans container files and which Kubernetes check ids cover seccomp, automount and digest. The README read on 2026-11-06 does not say; search results disagree on the check ids. |  |  | yes | AK-G16 |
| T-016 | PostgreSQL | Role and GRANT behaviour for the audit-writer split (V7): general knowledge, not read. |  |  | yes | AK-G16 |
| T-017 | Gunicorn and Waitress | Licences MIT and ZPL 2.1 are UNVERIFIED (also in the ticket); whether Gunicorn has a body-size cap is unknown. |  |  | yes | AK-G16 |
| T-018 | wsgiref (Python standard library) | Usable as a development server for door_app: general knowledge, not read. |  |  | yes | AK-G2 |
| T-019 | n8n | Webhook node auth is Basic, Header or JWT; Header Auth checks a fixed header value, not a timestamped HMAC; HMAC needs the Raw Body option plus a Crypto or Code node; a community thread (community.n8n.io topic 318758) reports hash mismatches with the Crypto node; Respond: Immediately returns Workflow got started. Source: web-search result text for docs.n8n.io, read 2026-11-06 (docs.n8n.io failed DNS). |  |  | yes | AK-G2 |
| T-020 | n8n | Whether the Webhook node with Respond: Immediately stores the request durably before it answers (the most important unverified fact of the audit: decides how much of the AK-G2 front door a no-code tool could carry). |  |  | yes | AK-G2 |
| T-021 | n8n | Whether n8n can check an HMAC over the exact raw bytes reliably; queue mode (Redis and workers) behaviour when a worker or Redis is down. |  |  | yes | AK-G2 |
| T-022 | n8n | Licence and whether a client may self-host it for this use (must be checked before any client build, R447). |  |  | yes | AK-G2 |
| T-023 | n8n | Whether an n8n flow can list a source's own ids (mailbox ids, delivery log) and post them, for reconciliation; whether it can fetch the sender id list from specific sender APIs. |  |  | yes | AK-G2, AK-G15 |
| T-024 | pgmq | PostgreSQL License. A lightweight message queue like AWS SQS on Postgres; guaranteed exactly once delivery of messages to a consumer within a visibility timeout; archive tables; installed as an extension or as plain SQL. The page mentions no dead-letter queue, no dedupe key and no per-producer backpressure; it shows a read_ct column without defining it; it stores messages as JSON payloads. | github.com/pgmq/pgmq | 2026-11-06 | no | AK-G2, AK-G15 |
| T-025 | pgmq | Absence is not confirmed: dedupe or idempotency key on send, per-tenant cap, dead-letter feature; meaning of read_ct; latest release date (page showed none); whether install needs superuser on managed PostgreSQL. |  |  | yes | AK-G2, AK-G15 |
| T-026 | pg_cron | README: a job runs with the same permissions as the current user; cron.schedule_in_database takes a username; the README lists Amazon RDS, Azure and Google Cloud among supporting services. | github.com/citusdata/pg_cron | 2026-11-06 | no | P4b2 |
| T-027 | pg_cron | Needs a superuser install (stated in the audit summary without a page reference). |  |  | yes | P4b2, AK-G2 |
| T-028 | k6, Locust, Vegeta, Toxiproxy | Named as free load and fault tools in R370 (RULES.md:847); tool docs not fetched. |  |  | yes | AK-G2 |
| T-029 | n8n Wait node (n8n-docs source on GitHub) | The Wait node offloads execution data to the database while it waits and resumes on a webhook or form. | raw.githubusercontent.com/n8n-io/n8n-docs (Wait node page) | 2026-11-06 | no | AK-G15, AK-G1 |
| T-030 | n8n | Notifier nodes (Slack, e-mail, Teams) and the schedule trigger were not read. |  |  | yes | AK-G15 |
| T-031 | Zendesk | Conversations pass control hands a chat from a bot to an agent workspace: third-party guides only (eesel.ai, support.cognigy.com), read 2026-11-06; official reference not read. |  |  | yes | AK-G15 |
| T-032 | Help-desk and ticket tools | Staff can reopen and edit closed tickets: general knowledge, per tool, not read. |  |  | yes | AK-G15 |
| T-033 | Self-hostable internal-tool builders | Usable as the front end for G14: no page read. |  |  | yes | AK-G15 |
| T-034 | SQL view plus dashboard tool | Usable for V11 and V13 reports: no tool page read. |  |  | yes | AK-G15 |
| T-035 | Agent-framework session stores and Postgres checkpointers | Cover AK-G1's conversation store: not fetched. |  |  | yes | AK-G1 |
| T-036 | LLM test frameworks | Multi-turn tests for the AK-G1 harness: not fetched. |  |  | yes | AK-G1 |
| T-037 | Server-side compaction (provider docs) | Compaction replaces the older turns with a summary written on the server so no summarization code is needed; on-demand and threshold modes are in beta; a custom summarization prompt exists; recent turns are kept; context editing is named on the page. | platform.claude.com/docs/en/build-with-claude/compaction | 2026-11-06 | no | AK-G1 |
| T-038 | Server-side compaction | Availability on each client cloud (only the direct API page was read); whether it is still beta when V1 triggers. |  |  | yes | AK-G1 |
| T-039 | langchain-text-splitters | Version 1.1.3, MIT, uploaded 2026-10-02, one required dependency langchain-core. | pypi.org/pypi/langchain-text-splitters/json | 2026-11-06 | no | AK0, AK2a |
| T-040 | chonkie | Version 1.7.0, MIT, base requirements tqdm, numpy, chonkie-core, tenacity, httpx, tokie (brings a network library into ingest, fails AK2a row R17). | pypi.org/pypi/chonkie/json | 2026-11-06 | no | AK0, AK2a |
| T-041 | langchain-text-splitters, chonkie | Whether either splits on legal clauses (R139); size of langchain-core's own dependency tree. |  |  | yes | AK0, AK2a |
| T-042 | ranx | Version 0.3.21, MIT, released 2025-08-07, lists Recall, MRR and Hit Rate. About 15 months before 2026-11-06, so it fails AK0's J4 rule (release within 12 months). | pypi.org/project/ranx | 2026-11-06 | no | AK0 |
| T-043 | Retrieval-metric libraries other than ranx | None checked (AK0 D12). |  |  | yes | AK0 |
| T-044 | import-linter | Version 2.15, BSD-2-Clause, released 2026-09-04, dependencies click, grimp, rich. | pypi.org/pypi/import-linter/json | 2026-11-06 | no | AK1, P6b2 |
| T-045 | import-linter | Forbidden contracts on external packages need include_external_packages = true: web-search snippet (import-linter.readthedocs.io, github.com/seddonym/import-linter), read 2026-11-06; docs host did not resolve. |  |  | yes | AK1 |
| T-046 | pypdf | Version 6.21.4, BSD-3-Clause, no runtime dependency on Python 3.11+. | pypi.org/pypi/pypdf/json | 2026-11-06 | no | AK2a |
| T-047 | pdfplumber | Version 0.11.10, MIT classifier, depends on pdfminer.six, Pillow, pypdfium2. | pypi.org/pypi/pdfplumber/json | 2026-11-06 | no | AK2a |
| T-048 | docling | Version 2.148.0, MIT. | pypi.org/pypi/docling/json | 2026-11-06 | no | AK2a |
| T-049 | docling-serve | Version 1.38.2, MIT, Running Docling as an API service, container images described. | pypi.org/pypi/docling-serve/json | 2026-11-06 | no | AK2a |
| T-050 | docling-serve | Exact endpoints, limits and dependency closure (only the pypi summary was read). |  |  | yes | AK2a |
| T-051 | Docling chunkers and quality flags | HybridChunker and HierarchicalChunker behaviour (headings, merging small chunks, page provenance): search snippet only (docling-project.github.io concepts/chunking); scanned-page flagging via its OCR pipeline and layout labels for headers and footers unconfirmed. |  |  | yes | AK2a |
| T-052 | pypdf advisories | CVE-2025-62707 (fixed 6.1.3) and CVE-2026-54531 (fixed 6.13.0), infinite-loop class: search snippets only (osv.dev, sentinelone.com), read 2026-11-06. |  |  | yes | AK2a |
| T-053 | Container runtime | Flags for no network (--network none) and memory limits: not fetched. |  |  | yes | AK2a |
| T-054 | unstructured | Version 0.27.36, Apache-2.0, 25 runtime dependencies including spacy, numba, requests. | pypi.org/pypi/unstructured/json | 2026-11-06 | no | AK2a |
| T-055 | semchunk | Version 4.1.1, MIT, 2026-06-13, dependency tqdm (plus dill on Windows). | pypi.org/pypi/semchunk/json | 2026-11-06 | no | AK2a |
| T-056 | semchunk | Whether it can return character offsets (needed for a post-check design). |  |  | yes | AK2a |
| T-057 | Cloud knowledge-base services | Fixed, hierarchical and semantic chunking and a custom-function hook: search snippets (aws-samples.github.io amazon-bedrock-samples, community.aws), read 2026-11-06; official guide not read; equivalents on the other two clouds not checked. |  |  | yes | AK2a |
| T-058 | deepeval | Version 4.3.3, Apache-2.0, similar to Pytest but specialized for unit testing LLM apps, per-metric threshold. | pypi.org/pypi/deepeval/json | 2026-11-06 | no | AK4a |
| T-059 | hypothesis | Version 6.170.14, MPL-2.0 (weak copyleft, goes to the owner first under AK0 PL7), dependency sortedcontainers. | pypi.org/pypi/hypothesis/json | 2026-11-06 | no | AK4a, AK1, AK2a |
| T-060 | pytest | Version 9.1.1 behaviour cited by the ticket; caplog not seeing loggers with propagate=False: from memory, not re-read. |  |  | yes | AK4a |
| T-061 | pypdf, docling, unstructured, chonkie, deepeval, hypothesis | Release dates not read (pypi pages truncated before the dates). |  |  | yes | AK2a, AK4a |
| T-062 | Workflow engines, LLM gateways, HTTP fault injectors, file-type sniffing libraries, PDF-writing libraries | Docs not fetched for any of them. |  |  | yes | AK1, AK2a, AK4a |
| T-063 | Anthropic SDK 2.1.0 (read in the installed package) | DEFAULT_MAX_RETRIES = 2; honours retry-after-ms and x-should-retry; retry count exposed only as the outgoing header x-stainless-retry-count, not on the raised error. Read from the wheel, no page URL. |  | 2026-11-06 | yes | P5b1 |
| T-064 | botocore 1.43.122 (read in the installed package) | Standard retries DEFAULT_MAX_ATTEMPTS = 3. Read from the wheel, no page URL. |  | 2026-11-06 | yes | P5b1 |
| T-065 | Semgrep CE 1.184.0 (RAN) | LGPL-2.1-or-later (from PyPI metadata). Run on made-up files: found the ConfigError constructions. Taint rule caught the direct f-string case, missed taint through parts.append(msg) until one pattern-propagators entry was added, does not follow taint across a function call. |  | 2026-11-06 | yes | P5b2, P5b3 |
| T-066 | Semgrep CE | Whether metrics are on by default (flag --metrics off was passed); intra-procedural taint only; any licence change after LGPL-2.1; fail-closed on a parse error; stable match key; SAFE_BODIES-style body pin. semgrep.dev not reachable. |  |  | yes | P5b2, P5b3, P5b5 |
| T-067 | ruff 0.16.9 (RAN) | TID251 banned-api flagged import traceback and logging.basicConfig(); did NOT flag __import__("traceback"); per-file-ignores allowed one file; flagged os.environ (direct and via from os import environ as E) and os.getenv; did NOT flag getattr(os, "environ"); per-file only, not per variable name or count. Run on made-up files. |  | 2026-11-06 | yes | P5b5, P6b2 |
| T-068 | ruff | TID251 on the pinned 0.17.1 (ran 0.16.9); importlib.import_module("traceback"); the P6b2 names not run (os.putenv, os.path.expandvars, getpass.getuser, dotenv, subprocess, ctypes, os.system, os.popen, pydantic_settings.BaseSettings). docs.astral.sh not reachable. |  |  | yes | P5b5, P6b2 |
| T-069 | import-linter 2.15 (RAN) | With source_modules = kit.** and one ignore_imports edge it failed a forbidden import and allowed the pinned one. Run on made-up files. |  | 2026-11-06 | yes | P6b2 |
| T-070 | import-linter | Whether a contract can require that an import EXISTS (equality) and how it handles dynamic imports. |  |  | yes | P6b2 |
| T-071 | LiteLLM | Proxy retries, fallbacks, cooldowns, Presidio guardrail behaviour, whether the caller sees each upstream attempt, whether error objects pass provider text through. docs.litellm.ai not reachable. |  |  | yes | P5b1, P5c |
| T-072 | Microsoft Presidio | Deanonymize, recognizers, MIT licence (from memory). |  |  | yes | P5c |
| T-073 | Protect AI LLM Guard | Anonymize and Deanonymize: not checked. |  |  | yes | P5c |
| T-074 | OpenRouter and OpenAI-shaped APIs | provider.data_collection deny and store false as per-request no-training flags: not checked (also marked UNVERIFIED in the ticket). |  |  | yes | P6b1 |
| T-075 | structlog and loguru | That neither drops foreign message text by design: docs not fetched. |  |  | yes | P5b4 |
| T-076 | Log scrubbers (Sentry before_send style) | Not checked; the claim rests on P5b5's own statement that pattern cleaners miss names. |  |  | yes | P5b3 |
| T-077 | Lead gateway test (reviews/gateway-check-lead-reading-1.md, 2026-11-06) | LiteLLM-style key budget: no overshoot in a simple sequential run; under 20 concurrent calls 19 were refused for an unexplained reason; does not show reserve before, settle after, exact decimal, per-run cap or fail closed on unknown billing. A run by the lead, no URL. |  | 2026-11-06 | yes | P4b1, P4b2 |
| T-078 | Alertmanager | Configuration doc: repeat_interval is how long to wait before repeating the last notification; it does not say it deduplicates; dedupe is left to the receiver through groupKey. | github.com/prometheus/alertmanager (docs/configuration.md) | 2026-11-06 | no | P4c |
| T-079 | PagerDuty Events API | dedup_key behaviour: developer.pagerduty.com failed DNS. |  |  | yes | P4c |
| T-080 | Renovate (pep621 manager) | Readme: supports uv (including uv.lock files and uv workspaces). | github.com/renovatebot/renovate (lib/modules/manager/pep621/readme.md) | 2026-11-06 | no | P8a |
| T-081 | Renovate | Whether it can bump a git-commit dependency in pyproject.toml (the readme does not say; docs.renovatebot.com failed DNS). |  |  | yes | P8a |
| T-082 | py-moneyed | Whether a maintained money library could represent micro-dollars rounded up once per call: not checked. |  |  | yes | P4b1 |
| T-083 | Provider token-counting endpoint or tokenizer library | Whether it returns a documented UPPER bound: no doc fetched. |  |  | yes | P4b1 |
| T-084 | LiteLLM price file | Whether a gateway price file is fit to seed Route prices: docs.litellm.ai failed DNS. |  |  | yes | P4b1 |
| T-085 | tenacity | What it offers for attempt accounting: not checked. |  |  | yes | P4b2 |
| T-086 | Provider error page | Says nothing about billing (ticket line P4b2:47, read 2026-11-05 per the audit); no URL given. |  | 2026-11-05 | yes | P4b2 |
| T-087 | pdoc and mkdocstrings | What they generate for this repo: not fetched. |  |  | yes | P8b |
| T-088 | markdownlint and Vale | Whether a prose linter could replace any T6 check: not fetched. |  |  | yes | P8b |
| T-089 | ledger_check.py and ledger_lint.py | What they do and which arguments they take: not visible in the cloud (P8b:439). |  |  | yes | P8b |
| T-090 | gitleaks | Version 8.30.1, already pinned in CI (ticket line P0a.md:42); no URL. |  |  | yes | P0a |
| T-091 | gitleaks or Semgrep custom rule | Could hold the public word list (class V); any maintained tool matching against a hashed deny list (class P): not searched. |  |  | yes | P0a |
| T-092 | Python mutation tools | Whether maintained ones run hand-written, re-pointed mutants: not checked. |  |  | yes | P1 |
| T-093 | Maintained package or ICU spoof checker | Whether one already ships the look-alike (confusables) table: not checked. |  |  | yes | P1 |
| T-094 | Semgrep and ruff in CI | Whether a rule in either covers the refusal lint: not checked. |  |  | yes | P1 |
| T-095 | PostgreSQL role connection limits | Cover only part of the cap on open stop requests: not checked. |  |  | yes | P2a |
| T-096 | Maintained PII detector | Whether it covers the plain patterns of the redactor: not checked. |  |  | yes | P2d |
| T-097 | Migration tools (alembic, flyway, atlas, sqitch, dbmate, yoyo) | Whether any handles ordering and out-of-order runs: not searched. |  |  | yes | P3a |
| T-098 | PostgreSQL parser library | Whether it could do the SQL lexing and grant scan: not checked. |  |  | yes | P3a |
| T-099 | Schema-diff tools | Whether any covers the previous-release structure test: not checked. |  |  | yes | P3a |
| T-100 | Price-table library | Whether it covers the price lookup (not the refusals): not checked. |  |  | yes | P4a |
| T-101 | pytest database-fixture plugin | Whether it covers the connection setup of the P4d contract harness: not checked. |  |  | yes | P4d |
| T-102 | Retry library | Whether one covers the backoff of the P4d write wrapper: not checked. |  |  | yes | P4d |
| T-103 | ruff TID rules and import-linter for the lock-in guard | ruff selects TID (pyproject.toml:74) and is pinned ruff==0.17.1 (:50) per the ticket; whether import-linter could cover the guard is unchecked. |  |  | yes | P4d, P5b5 |
| T-104 | git, junit XML diff tool | git merge-tree, git diff, git rev-list do the work (ticket line P0c.md:23); whether a maintained tool could diff two junit XML files is unchecked. |  |  | yes | P0c |
| T-105 | gitleaks 8.30.1 custom rules (class V) | Binary from the release asset ran on a toy repo with made-up names: a plain rule finds a name in the tree and in a file added then removed (git mode); a case-sensitive rule and a (?i) twin work; a separator-tolerant regex finds the camel/dash/dot/space spellings. Tool run on this machine. Updates T-091. | github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz | 2026-11-06 | yes | P0a |
| T-106 | gitleaks git mode and stdin | `gitleaks git` did not report a name that was only in a commit message; `git log --all --format=%B | gitleaks stdin` did. `gitleaks dir` also scanned .git/logs. Tool run. | github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz | 2026-11-06 | yes | P0a |
| T-107 | gitleaks empty or missing config | A config with no rules exits 0 with 'no leaks found' on a tree holding a planted name; a missing config file exits 1. So the tool does not fail closed on an empty rule list. Tool run. | github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz | 2026-11-06 | yes | P0a |
| T-108 | gitleaks hashed matching | README of the 8.30.1 archive has no hash or digest matching feature (grep for hash, digest, sha found only an entropy line). Docs host not reachable; absence in the full docs not checked. Updates T-091. | github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz | 2026-11-06 | yes | P0a |
| T-109 | detect-secrets 1.5.0 custom plugin | A 15-line plugin (NFKC, case-fold, letters and digits only, windows of 1 to 4 words, SHA-256 set) loaded with `scan -p` caught 'Acme Corp' and 'ACME-corp.'; the output holds a hash and a line number, not the name. Tool run. Updates T-091. | pypi.org/project/detect-secrets/1.5.0/ | 2026-11-06 | yes | P0a |
| T-110 | detect-secrets history | `scan --help` shows no history or commit option; a name committed then deleted was not found by a scan of the tree. Tool run. | pypi.org/project/detect-secrets/1.5.0/ | 2026-11-06 | yes | P0a |
| T-111 | git 2.43.0, xmllint, sort, comm (shell glue for P0c) | A 12-line loop over git merge-tree --write-tree --name-only, git diff --name-only, git rev-list --left-right --count printed conflicts, clean and 'ref not found UNMEASURED' correctly on a toy repo; an 11-line xmllint/comm script classified NEW_FAILURE, SAME_AS_BASELINE, FIXED_VS_BASELINE, DB_SKIP, skip correctly on two pytest 9.2.0 junit files. xmllint on the studio machine not checked. Updates T-104. | pypi.org/project/pytest/9.2.0/ | 2026-11-06 | yes | P0c |
| T-112 | junitparser 5.0.3 | Installs from PyPI on Python 3.13; parsing used nowhere; whether it has a junit-to-junit diff function not looked for. T-104 stays open. | pypi.org/project/junitparser/5.0.3/ | 2026-11-06 | yes | P0c |
| T-113 | ruff 0.17.4 (TID251, BLE001) for the refusal lint | On a five-shape fixture, TID251 flagged import lines and the dotted use of banned names but not handlers; exemption is per file or per line, not per function; BLE001 flagged only `except Exception`. No rule bans handlers of a named exception. Tool run. Updates T-094; the CI pin is T-103. | pypi.org/project/ruff/0.17.4/ | 2026-11-06 | yes | P1 |
| T-114 | semgrep 1.184.0 custom rule for the refusal lint | A first local rule (try/except name regex plus pattern-not-inside an allowed function) caught 2 of 4 swallow shapes (plain, dotted), missed the aliased tuple and contextlib.suppress. More rules not tried. Tool run. Updates T-094. | pypi.org/project/semgrep/1.184.0/ | 2026-11-06 | yes | P1 |
| T-115 | PostgreSQL 16.15 role CONNECTION LIMIT | A role with CONNECTION LIMIT 2 was refused on a third session ('too many connections for role') and inserted 5,000 rows on one connection. Throwaway server, Ubuntu package. Updates T-095. | postgresql.org/docs/16/sql-createrole.html | 2026-11-06 | yes | P2a |
| T-116 | PostgreSQL 16 settings and ALTER ROLE SET | pg_settings has no row-count or quota setting (only row_security matches); ALTER ROLE SET statement_timeout worked. An extension quota not searched. Tool run on the throwaway server. Updates T-095. | postgresql.org/docs/16/sql-alterrole.html | 2026-11-06 | yes | P2a |
| T-117 | PostgreSQL partial unique index as a row cap | A slot column with CHECK (slot BETWEEN 1 AND 3) and a unique index WHERE cleared_by IS NULL refused a duplicate slot (unique violation) and slot 4 (check violation) on a toy table. Not tried on the real stop design; not adopted. | postgresql.org/docs/16/indexes-partial.html | 2026-11-06 | yes | P2a |
| T-118 | Unicode confusables data pin and unicodedata pin | tools/data/confusables.txt: UTS #39 version 18.0.0, dated 2026-08-06 01:05:35 GMT, 9,862 lines, 763,128 bytes, sha256 6ed3ee96...f5b92 (recomputed on a P1m mutant snapshot copy); generated header: ENTRIES 677, TABLE_DIGEST 1dce77c4..., DATA_UNICODEDATA 15.1.0; pinned interpreter data TEXTNORM_PINNED_UNIDATA 15.1.0 (P1.md BN-12). unicodedata2 18.0.0 lacks casefold, isalpha, isspace, isdecimal (rung audit part F). Read from files, no page. | unicode.org/Public/security/ (file header names unicode.org/terms_of_use.html) | 2026-11-06 | yes | P1 |
| T-119 | Presidio default analyzer vs hostile spellings | Lead's reading: 17 of 30 hostile inputs found (13 missed), 14 of 48 must-mask lines missed, 7 of 14 must-keep lines flagged; misses include full-width, Cyrillic, zero-width, percent, entity spellings. Raw evidence file not in the repository; not rerun. Updates T-096. | reviews/gateway-check-lead-reading-1.md (in this repository) | 2026-11-06 | yes | P2d, P5c |

## Count

Rows: 119. Verified (UNVERIFIED = no): 26. UNVERIFIED (= yes): 93.
