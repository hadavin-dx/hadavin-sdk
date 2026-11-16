import sys
# (section, cite, in-range, verdict yes/no/partly, actual text)
R=[]
def a(sec,cite,rng,v,txt): R.append((sec,cite,rng,v,txt))
S="src/hadavin_sdk/"
# failures first handled by sorting
a("F1",S+"approvals/gate.py:681-698","yes","yes","def withhold_commands 681 .. return 698; G4 display filter replacing commands with WITHHELD")
a("F2",S+"approvals/gate.py:647-678","yes","yes","_WRITE_SHAPES = re.compile( 647 .. ) 678, no flag arg; (?i: only at 671-673; SQL words upper-case")
a("F3",S+"runtime/agent_loop.py:440-441","yes","yes","self.limits.charge(agent_id, reply.cost_usd) / self.store.add_cost(run.run_id, reply.cost_usd)")
a("F3",S+"runtime/agent_loop.py:314-315","yes","yes","314 self.limits.charge(run.agent_id, verdict.cost_usd); 315 self.store.add_cost(...)")
a("F4",S+"store/memory.py:196-204","yes","yes","add_spend under self._lock, adds usd (any sign), returns (day, month)")
a("F4",S+"store/postgres.py:416-431","yes","yes","one transaction, two upserts with RETURNING usd")
a("F4","migrations/0001_core.sql:87-92","yes","partly","text holds (CREATE TABLE spend ... usd NUMERIC NOT NULL, no check) but the file is src/hadavin_sdk/store/migrations/0001_core.sql; the cite omits store/ (path shorthand)")
a("F4","migrations/0003_approvals_tick.sql:15-20","yes","partly","spend_month, usd NUMERIC NOT NULL, only CHECK on month day; real path src/hadavin_sdk/store/migrations/ (store/ omitted)")
a("F4",S+"store/protocol.py:107-111","yes","yes","107 add_spend; 108-110 spend_totals 'a read with no write'")
a("F5",S+"limits.py:17-30","yes","yes","25 registry.agents[agent_id].budget_usd (KeyError for unknown id); 26 day >= budget.daily; 28 month >=; uses now() from models")
a("F5",S+"models.py:19-20","yes","yes","def now(): return datetime.now(UTC)")
a("F5",S+"app.py:73","yes","yes","clock: Callable[[], datetime] = now")
a("F5",S+"app.py:171","yes","yes","limits = Limits(store, audit, reg)")
a("F5",S+"app.py:176-184","yes","yes","Approvals(store, audit, reg, channel, ..., clock, summary_detector): clock reaches only Approvals")
a("F6",S+"llm/retry.py:83-108","yes","yes","with_retry; ProviderError re-raised 95-96; non-transient -> ProviderError 99; exhausted -> ProviderExhausted 101")
a("F6",S+"llm/anthropic.py:122","yes","yes","got = self._retry(lambda: self._parse(...))")
a("F6",S+"llm/bedrock.py:156","yes","yes","got = self._retry(lambda: self._parse(...))")
a("F6",S+"llm/gemini.py:86","yes","yes","got = self._retry(")
a("F6",S+"llm/openai_compat.py:119","yes","yes","got = self._retry(")
a("F6",S+"llm/common.py:233","yes","yes","def _retry(self, call) -> Answer: return with_retry(")
a("F6",S+"llm/common.py:195","yes","partly","docstring text: 'a malformed answer is a ProviderError, never a stray KeyError'. Supports the claim; the parse code itself was not opened by me")
a("F7",S+"extract.py:47","yes","yes","reply = llm.chat(")
a("F7",S+"evals.py:73","yes","yes","reply = llm.chat(")
a("F7",S+"guard/judge.py:72","yes","yes","reply = self.llm.chat(")
a("F7",S+"runtime/agent_loop.py:425","yes","yes","reply = self.llm.chat(")
a("F7",S+"k1b/loop.py:94","yes","yes","box['reply'] = llm.chat(*args, **kwargs); 104 daemon=True thread")
a("F7","demos/ask-your-data/askdata/pipeline.py:155","yes","yes","reply = self.llm.chat( ; meter.py exists with own cost meter (docstring: 'The cost meter')")
a("F7",S+"guard/bedrock_guardrail.py:101","yes","yes","resp = self._client.apply_guardrail(; grep cost/price/usd in file: 0 hits")
a("F7","grep: five .chat( sites in src/","yes","yes","grep '\\.chat(' src: k1b/loop.py:94, agent_loop.py:425, extract.py:47, evals.py:73, judge.py:72 (+ producers.py:5 docstring mention only)")
a("F8","tests/k5_support.py:160-204","yes","yes","build_runtime 160; Runtime( at 200 (call continues past 204); no app.build")
a("F8",S+"app.py:162","yes","yes","llm = llm or make('llm', b.llm, secrets, routes=cfg.routes)")
a("F8",S+"app.py:165","yes","yes","members = [make('detector', d, secrets, llm=llm) for d in b.detector]")
a("F8",S+"app.py:90-98","yes","yes","refuses sources= and tools= when live; no llm= refusal")
a("F9",S+"cli.py:146-153","yes","yes","gate branch builds only make('llm', ...) at 150; no store/limits")
a("F9",S+"cli.py:150","yes","yes","make('llm', b.llm, make('secrets', b.secrets), routes=cfg.routes)")
a("F9",S+"cli.py:221-222","yes","yes","221 llm = make('llm',...); 222 detector = combine([make('detector', d, secrets, llm=llm)...])")
a("F9",S+"cli.py:183-189","yes","yes","184 secrets, 186 platform_secrets.check, 189 store")
a("F9",S+"evals.py:101-110","yes","yes","llm_judge qualified on same llm via judge.qualify(JudgeDetector(llm,...)) at 109")
a("F10","grep: no non-test caller of extract() in src/","yes","yes","grep 'extract(' src excluding def: no hits")
a("F10",S+"llm/fake.py:39-40","yes","yes","39 doc = documents[0] if documents else ...; 40 digest = hashlib.sha256(doc).hexdigest()")
a("F11",S+"audit/chain.py:134-149","yes","yes","Verification fields rows, signed_through, problems, unreadable; ok and unsigned_tail properties")
a("F11",S+"audit/chain.py:362-385","yes","yes","verify_rows(rows, checkpoints, public_key, anchors, alg, row_algs) 363-370; no checkpoint_every")
a("F11",S+"audit/chain.py:171","yes","yes","self.checkpoint_every = checkpoint_every")
a("F11",S+"audit/anchor_s3.py:70","yes","yes","def all(self) -> dict[int, tuple[str, str]] (no timestamp)")
a("F11",S+"cli.py:349-363","yes","yes","prints rows, signed through, N not signed yet, PROBLEM lines, 'intact'/'NOT intact'; exit 0/1/3")
a("F12",S+"actions/secrets_file.py:34-64","yes","yes","confined 36; os.open O_NOFOLLOW|O_NONBLOCK 38-41; fstat 50; S_ISREG 51; refuse IROTH|IWGRP|IWOTH 54 (group read allowed); skipped when os.name == 'nt'")
a("F12",S+"audit/signer.py:104-108","yes","yes","106 path.is_file(); 108 path.read_bytes(); no mode check")
a("F13",S+"runtime/agent_loop.py:83","yes","yes","GUARD_STOP_REASONS = frozenset( (run_budget membership: v4 check confirmed, not re-read here beyond def line)")
a("F13",S+"runtime/agent_loop.py:79-82","yes","yes","comment: K6 counts every non-null caught_by")
a("F13",S+"runtime/agent_loop.py:569-575","yes","yes","_abstain; 575 caught = 'guard' if reason in GUARD_STOP_REASONS else None")
a("F13",S+"runtime/agent_loop.py:244","yes","yes","return self._to(run, S.NEEDS_PERSON, f'limits.{blocked[0]}')")
a("F13",S+"runtime/agent_loop.py:672","yes","yes","return self._to(run, S.NEEDS_PERSON, 'limits_unavailable'); comment 669 'no card is posted'")
a("F13",S+"runtime/agent_loop.py:703","yes","yes","return self._to(run, S.DENIED, decision.rule_id); 702 'stop means stop: no card'")
a("F14",S+"config.py:317","yes","yes","environment: Literal['dev', 'pilot', 'prod']")
a("F14",S+"deferred.py:33","yes","yes","LIVE = ('pilot', 'prod')")
a("F14",S+"backends/table.py:593-602","yes","yes","DEV_ONLY frozenset incl. ('llm','fake')")
a("F14",S+"config.py:366-370","yes","yes","if self.environment != 'dev': refused = [... in DEV_ONLY] -> pilot/prod refuse fake kind")
a("F14",S+"config.py:453","yes","yes","except (ValueError, TypeError, yaml.YAMLError) as exc (-> ConfigError per v4 check)")
a("F15",S+"config.py:41-47","yes","yes","_money rejects float only; Money = Annotated[Decimal, BeforeValidator(_money)]")
a("F15",S+"config.py:57-58","yes","yes","Route input_usd_per_mtok: Money / output_usd_per_mtok: Money")
a("F15",S+"registry.py:35-36","yes","yes","Budget daily: Money, monthly: Money; no validator")
a("F15",S+"registry.py:53","yes","yes","max_run_usd: Money | None = (")
a("F15",S+"models.py:294","yes","yes","cost_usd: Decimal = Decimal(0)")
a("F16",S+"models.py:218-222","yes","yes","DeadLetter(Shape): run_id, reason, errors: list[str] (required), ts")
a("F16",S+"extract.py:18-25","yes","yes","@dataclass class Valid: data, replies, cost_usd property")
a("F16",S+"guard/runmap.py:218-227","yes","yes","storable(mapping, kinds): keeps kinds in allowed and storable_original")
a("F16",S+"guard/runmap.py:560-568","yes","yes","restore_value handles str, dict, list only")
a("F16",S+"defaults.py:108-122","yes","yes","STORED_KINDS incl. NAME, ADDRESS, PHONE, EMAIL; no IBAN")
a("F16",S+"guard/runmap.py:275-304","yes","yes","escape_placeholders/escape_markers/redact_untrusted; redact_text has no neutralise by default (417)")
a("F16",S+"evals.py:63","yes","yes","runmap.redact_untrusted(doc.decode('utf-8','replace'), {})")
a("F17",S+"guard/injection.py:85-101","yes","yes","except Exception -> Verdict(flagged=True, ..., reason_code='guard_unavailable')")
a("F17",S+"guard/judge.py:100-109","yes","yes","qualify: passed += v.reason_code != 'guard_unavailable' and ...")
a("Sec0",S+"llm/common.py:59-62","yes","yes","estimate_tokens: max(1, len(text)//3)")
a("Sec0","tests/fixtures/config/config.yaml:6-8","yes","yes","input 3.00, output 15.00, max_tokens 1024")
a("Sec0","tests/test_s4_llm_guard.py:39","yes","yes","assert reply.cost_usd == Decimal('0.00225')")
a("Sec0","tests/test_s5_runtime.py:76","yes","yes","cost_usd == Decimal('0.00225')")
a("Sec0","grep -ril cache under llm/ (hits listed: secrets, evidence, k1b replay, table)","yes","yes","no hit under src/hadavin_sdk/llm; hits: actions/secrets_*.py, runtime/evidence.py, k1b/replay.py, backends/table.py")
a("Sec0",S+"audit/anchor_s3.py:1-12 (D18 correction)","yes","yes","docstring says only 'written by a principal the runtime cannot delete with (S11)'; grep PutObject|GetObject|ListBucket in audit/*.py: 0 hits")
a("D14/4.2",S+"llm/protocol.py (SpendRefused to be defined next to ProviderError)","yes","yes","ProviderError 10, ProviderExhausted 14 exist; SpendRefused is new (not present)")
a("D9","tests/test_s5_runtime.py:107-111","yes","yes","charge('0.999'); 'call costs 0.00225 and crosses 1.00'; expects DENIED limits.daily_budget")
a("D9/4.2","tests/test_k5_tools.py:723-731","yes","yes","CostLLM 0.30 (717-720); run_budget NEEDS_PERSON, len(llm.sent)==2, caught_by == 'guard'")
a("D11",S+"k1b/replay.py:85-90","yes","yes","_refuse_zero_price: zero and llm_kind != 'fake' -> ConfigError")
a("D18",S+"audit/anchor_gcs.py:69-85","yes","yes","def probed(bucket, settings) 69 .. return GcsAnchor(bucket) 85")
a("D18",S+"audit/anchor_azure.py:83-96","yes","yes","def probed(container, settings) 83 .. 96")
a("4.1",S+"store/protocol.py:151-160","yes","yes","missing_methods(store): lists Store methods the store lacks; app refuses at start (docstring 152-155)")
a("4.1",S+"store/memory.py:76-80","yes","yes","add_cost raises NotFound(run_id) when run missing")
a("4.1",S+"limits.py:48-51","yes","yes","Limits.reset: audit.write_intent first, then set_kill_switch")
a("4.1",S+"llm/common.py:65-83","yes","yes","tools_for(tools, output_schema) 65 .. return 83")
a("4.1",S+"llm/common.py:86-100","yes","yes","turns(messages, documents) 86 .. return out 100")
a("4.1",S+"k1b/loop.py:115-124","yes","yes","worst_case_usd 115-122; 110-124 also covers timeout path")
a("4.1/4.2",S+"llm/retry.py:31-36","yes","yes","status(exc): status_code or code as int")
a("4.1",S+"llm/protocol.py:9-15","yes","yes","ProviderError 10; ProviderExhausted(ProviderError) 14")
a("4.2",S+"llm/fake.py:29","yes","partly","line 29 is `def chat(`; class FakeLLM is at line 21 with no base class (not a NetworkLLM): claim true, cite points at the method not the class")
a("4.2",S+"llm/common.py:193","yes","yes","class NetworkLLM: (not cited by number in v5; claim 'FakeLLM is not a NetworkLLM' relies on 21 vs 193)")
a("4.2",S+"guard/producers.py:5","yes","yes","docstring mentions `.chat(` -> not a real call (census excludes)")
a("4.2",S+"evals.py:105-109","yes","yes","for d in cfg.backends.detector: if d.kind == 'llm_judge' ... judge.qualify at 109")
a("4.3",S+"runtime/agent_loop.py:425-437","yes","yes","chat call 425; except ProviderError 432-439 (the handler)")
a("4.4",S+"runtime/agent_loop.py:310-316","yes","yes","_screen: injection_check then charge/add_cost for verdict.cost_usd")
a("4.4",S+"runtime/agent_loop.py:241-242","yes","yes","kill_switch -> _to(run, S.STOPPED, 'kill_switch')")
a("4.4",S+"runtime/agent_loop.py:245-249","yes","yes","cap = max_run_usd; >= cap -> _note ... _abstain(run, NEEDS_PERSON, 'run_budget', cited or [])")
a("4.4",S+"runtime/agent_loop.py:560-567","yes","yes","_deliver never raises; returns Delivery(ok=False, reason=...)")
a("4.4",S+"runtime/agent_loop.py:569-597","yes","yes","_abstain; d.ok branch at 581")
a("4.4",S+"runtime/agent_loop.py:87","yes","yes","_REASON_TEXT = {'ungrounded': ...}")
a("4.4",S+"runtime/agent_loop.py:669-672 / 702-703","yes","yes","see F13 rows")
a("4.5",S+"app.py (audit = make(...) just before :162)","yes","yes","line 161: audit = make('audit', b.audit, secrets, store=store, signer=signer, anchor=anchor)")
a("4.5",S+"config.py:362-375","yes","yes","environment table refusals, model_validator end at 374")
a("4.5",S+"registry.py:338","yes","yes","def _cross_check(config, agents, chains, contracts)")
a("4.5",S+"guard/judge.py:3-4","yes","yes","'it runs on any configured llm route and kind'")
a("4.6",S+"audit/chain.py:161","yes","yes","checkpoint_every: int = 100")
a("4.6",S+"audit/chain.py:203","yes","yes","if self.signer is not None and seq % self.checkpoint_every == 0: self.checkpoint()")
a("4.6",S+"audit/chain.py:519-547","yes","yes","settings.checkpoint_every used at 547; settings class not read (v5 says so)")
a("4.6",S+"audit/anchor_gcs.py:69-85 / anchor_azure.py:83-96","yes","yes","see D18 rows")
a("4.7",S+"guard/runmap.py:417 (redact_text), :38 (RedactionError)","yes","yes","def redact_text( 417; class RedactionError 38")
a("4.7",S+"guard/producers.py:36","yes","yes","('extract validation errors', 'extract.py', 'extract', frozenset({'safe_head'}))")
a("4.7",S+"llm/common.py:86-100 (decode utf-8 replace)","yes","partly","turns() lines hold; the decode('utf-8','replace') text is at the cite for evals.py:63; common.py:86-100 not re-opened for decode text beyond the signature")
a("4.8",S+"actions/secrets_file.py:49-64","yes","yes","49 fdopen; 51 S_ISREG; 54 mask; 59-64 read")
a("4.8",S+"actions/secrets_file.py:54","yes","yes","mode & (S_IROTH | S_IWGRP | S_IWOTH): group read allowed")
a("4.8","tests/test_lockin_guard.py:68-75","yes","yes","LIBRARY_IMPORTS: psycopg, cryptography, markdown_it (vendor/library imports only)")
a("4.8",S+"audit/signer.py:182","yes","yes","_create(private_real, pem, 0o600)")
a("4.8",S+"config.py:393-394 ('in prod ed25519_local with a key file is already refused')","yes","no","393-394 is `if anchor is not None and not anchor.retention_ack: refused.append(... without retention_ack)`. The key-file refusal is at 395-396 (`if b.signer.kind == 'ed25519_local' and b.signer.private_key_path is not None`). Claim true, cite 2 lines short")
a("4.9",S+"approvals/gate.py:695","yes","yes","end = text.find('\\n', m.end()) -> cut at next newline")
a("4.9",S+"approvals/gate.py:546","yes","yes","_TOKEN = re.compile(r'[^\\S\\n]+([^\\s]+)') stops at newline")
a("4.9",S+"approvals/gate.py:608-615","yes","yes","_story: first-token test re.fullmatch(r'[A-Z][a-z]+|[^\\w/.~$-]+', first)")
a("4.9",S+"approvals/gate.py:664-666","yes","yes","UPDATE\\s+ + _ID + \\s+SET\\b (no alias/ONLY handling)")
a("4.9",S+"approvals/gate.py:674","yes","yes","rm shape: \\brm\\s+(?:-[a-zA-Z]*[rRf][a-zA-Z]*|--recursive|--force)(?=\\s+\\S)")
a("4.9",S+"approvals/gate.py:540","yes","yes","_NAMES = ['aws', *_VERB_FIRST, *_WORD_RUN]; no 'rm' key (grep)")
a("4.9",S+"approvals/gate.py:404","yes","yes","_AWS_READ_PREFIXES incl 'get-'")
a("4.9",S+"approvals/gate.py:597","yes","yes","words[1].startswith(_AWS_READ_PREFIXES) or s3 ls")
a("4.9",S+"approvals/gate.py:573-589","yes","yes","_subcommands starts 573; v4 check confirmed lower-casing (589 end not re-read)")
a("4.9",S+"approvals/gate.py:4, :366-377; approvals/channel.py:19-21","yes","yes","4 names G3/G4; 367-376 G4 comment; channel docstring 19-21")
a("4.9","tests/test_g4_parity.py:98,221-222","yes","yes","98 'update its set of rules'; 221 'we should delete from the queue only after a fix'; 222 'drop table pressure'")
a("4.9","evidence-handoff-v4.md: 125 pytest passed","yes","yes","line 25: 125 passed in 0.62s (and 0.31s)")
a("4.9","evidence-handoff-v4.md: 37 probes, 0 mismatches","yes","no","raw-v4/probe.json has 36 entries; probe.txt 36 lines; table.md 38 lines = header + separator + 36 rows. 0 mismatches holds (evidence line 7). Count 37 is wrong, 36")
a("4.9","evidence-handoff-v4.md: `git rebase -i HEAD~3` already withheld","yes","yes","line 9 and row G5b-W: withheld/withheld")
a("4.9","evidence-handoff-v4.md: `> /dev/null kubectl delete pod x` already withheld","yes","yes","row G2b-v3 withheld")
a("4.9","evidence-handoff-v4.md: G2a, G2b, G3 (12 lines + alias gap), G4a, G5a leak","yes","yes","rows G3-01..12 shown, G3-UP-1/2 shown, G2a-W shown, G4a-W shown; observed text list line 72 covers G5a and G2b")
a("4.9","evidence-handoff-v4.md: `KUBECTL.EXE delete ns prod` defanged by channel.clean","yes","yes","line 10: clean rewrites the dot to KUBECTL[.]EXE")
a("4.10",S+"guard/redact.py:472 (PHONE)","yes","yes","'PHONE',")
a("4.10",S+"guard/redact.py:247 (IBAN)","yes","yes","'IBAN',")
a("4.10",S+"guard/redact.py:451 (CREDITCARD)","yes","yes","re.compile(r'\\b\\d{4}[ \\-]\\d{4}[ \\-]\\d{4}[ \\-]\\d{4}\\b'): 4-4-4-4 only")
a("4.10",S+"guard/redact.py:236 (EMAIL)","yes","yes","'EMAIL',")
a("4.10",S+"guard/redact.py:513 (HAR cookie pair)","yes","yes","513 comment 'A HAR entry ({\"name\": \"Cookie\", ...' ; pattern 514-516")
a("4.10","CREDPAIR 'not in redact.py today'","yes","yes","grep CREDPAIR src: see check below (0 hits)")
a("4.10",S+"k1b/redaction.py:103","yes","yes","def _pair(key, value, f)")
a("4.10","tests/warden_port/privacy_corpus.py:42","yes","yes","'card 4111 1111 1111 1111'")
a("4.10","tests/warden_port/test_redaction.py:309,356","yes","yes","309 for pan in ('4111 1111 1111 1111', ...); 356 '4111111111111111' not in redact(...)")
a("4.11",S+"config.py:317, :366-367, :19","yes","yes","317 Literal; 366-367 if self.environment != 'dev' / DEV_ONLY; 19 imports DEV_ONLY")
a("4.11",S+"backends/table.py:593","yes","yes","DEV_ONLY: frozenset[tuple[str, str]] = frozenset(")
a("4.11","tests/test_lockin_guard.py:18,430","yes","yes","18 imports DEV_ONLY; 430 coverage_problems(TABLE, DEV_ONLY, ...)")
a("4.11","tests/fixtures/config/config.yaml:2","yes","yes","environment: dev")
a("4.11","tests/test_p4_secrets.py:106","yes","yes","def _config(tmp_path, secrets, environment='dev')")
a("4.11","tests/warden_port/test_audit_chain.py:568","yes","yes","_anchor_refusals('dev', ...)")
a("4.11","tests/test_p1b_backends.py:89-91","yes","yes","parametrize pilot/prod; d.update(environment=env)")
a("4.11",S+"actions/secrets_env.py:1","yes","yes","'(`dev` only, by the environment table)'")
a("4.11",S+"audit/signer.py:64,98","yes","yes","64 '(dev and pilot...'; 98 '(dev and pilot only...'")
a("4.11",S+"backends/table.py:126,214,254,591","yes","yes","126 opt-down for dev; 214 '(dev, pilot)'; 254 'a dev server'; 591 'allowed only in `dev`'")
a("4.11",S+"config.py:346","yes","yes","# dev executor only")
a("4.11",S+"defaults.py:100","yes","yes","'the dev executor's per-call timeout'")
a("4.11",S+"registry.py:50","yes","yes","'None only in dev'")
a("4.11",S+"tools.py:361","yes","yes","'Without a pin (dev only; ...'")
a("4.11",S+"runtime/agent_loop.py:179,553,572","yes","yes","179 'dev only'; 553 'slice-1 gate path (dev)'; 572 'dev slice-1'")
a("4.11",S+"actions/contract.py:34","yes","yes","'kept in dev for the slice-1 tests'")
a("4.11",S+"store/postgres.py:75,90","yes","yes","75 'opt-down for dev'; 90 'opt down with sslmode for dev'")
a("4.11",S+"guard/redact.py:1162","yes","yes","'dev', inside a word list")
a("4.11",S+"backends/table.py:150-157, :155","yes","yes","_AnchorSettings 150; retain_days: int = Field(default=1, ge=1) 155")
a("4.11",S+"config.py:377-398","yes","yes","_anchor_refusals 377 .. return 397")
a("4.11",S+"audit/anchor_s3.py (no probed today)","yes","yes","build() 84-97 has no probe; grep 'def probed' only in gcs/azure")
a("Sec6",S+"hadavin_sdk/fileguard.py and llm/build.py (stated as new)","n/a","yes","neither file exists (ls): stated as new")
a("Sec6","migrations 0006 (new)","n/a","yes","store/migrations holds 0001-0005 only")
a("Sec6",S+"store/migrations dir spend_op (new)","n/a","yes","grep spend_op: not expected present")
order={"no":0,"partly":1,"yes":2}
R.sort(key=lambda r:order[r[3]])
tot=len(R); c={k:sum(1 for r in R if r[3]==k) for k in order}
out=["# Citation check of CORE-PR-HANDOFF-v5.md (2026-11-16, UTC)","",
"EVIDENCE RUNNER output: reads only, nothing run except `grep`, `sed`, `ls` and a tiny `json` count. No git (the checkout has no history). Paths are under /home/user/hadavin-sdk; `src/hadavin_sdk/` prefix shown in full.",
"Target: handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v5.md (320 lines, read in full).","",
"## Counts","",f"- rows (cites and quoted code facts, one row per distinct cite or claim group): {tot}",
f"- match (yes): {c['yes']}",f"- partly: {c['partly']}",f"- not matching (no): {c['no']}",
"- not checked: see end of file (behaviour claims, new-code claims, arithmetic, Postgres)","",
"## v4 failures X1-X9 rechecked","",
"| id | v4 failure | v5 now | status |","|---|---|---|---|",
"| X1 | D18 S3 docstring claimed identity rights | v5 D18 and 4.11 H-1 now say the docstring has none; grep confirms 0 hits | FIXED, holds |",
"| X2 | tests/test_redaction.py wrong path | v5 4.10 cites tests/warden_port/test_redaction.py:309,356; lines hold | FIXED, holds |",
"| X3 | cli.py:179-184 | v5 cites cli.py:183-189; 184 secrets, 186 check, 189 store | FIXED, holds |",
"| X4 | app.py:164 | v5 cites app.py:165 (make('detector', ..., llm=llm)) | FIXED, holds |",
"| X5 | secrets_file.py:46-63 | v5 cites 49-64; holds | FIXED, holds |",
"| X6 | agent_loop.py :669/:702 | v5 cites :244, :672, :703; all hold | FIXED, holds |",
"| X7 | run_budget :245-247 | v5 cites :245-249; holds | FIXED, holds |",
"| X8 | table.py:594 | v5 cites table.py:593; holds | FIXED, holds |",
"| X9 | gcs 69-88, azure 80-95 | v5 cites gcs 69-85, azure 83-96; both hold | FIXED, holds |",
"| note | retain_days 'existing 7' | v5 says default is 1 (table.py:155) and the floor is new | FIXED, holds |",
"| note | CREDPAIR new name | v5 says 'a new label, not in redact.py today' | FIXED, holds |","",
"## Failures first (rows with verdict no or partly)","",
"| # | section | cite | line in range | content matches | actual text |","|---|---|---|---|---|---|"]
n=0
for r in R:
    n+=1
    if r[3]!="yes": out.append(f"| {n} | {r[0]} | `{r[1]}` | {r[2]} | **{r[3]}** | {r[4]} |")
out+=["","## Full table","","| # | section | cite | exists / line in range | matches | actual text |","|---|---|---|---|---|---|"]
n=0
for r in R:
    n+=1
    out.append(f"| {n} | {r[0]} | `{r[1]}` | {r[2]} | {r[3]} | {r[4].replace('|','\\|')} |")
out+=["","## Not checked","",
"- Behaviour claims about new code (everything marked 'specified, unverified' in v5: reserve_spend, SpendMeter, MeteredLLM, gate, wall card, fileguard, extract masking order).",
"- Postgres behaviour (row lock, grants); nothing was run; no tests, ruff or bandit.",
"- Scratch-regex results in v5 4.9 (match/withheld table): not re-run; only the evidence-v4 probe rows were compared.",
"- The 'Where each finding went' claims in v5-CHANGES.md and finding ids (security B-1 etc.): the review files were not opened.",
"- `ledger.md`, `ci.yml`, `.claude/rules/*` references: not opened (v5 cites none by line).",
"- `agent_loop.py:83` membership of `run_budget` in GUARD_STOP_REASONS, and `gate.py:573-589` end line: only the start line was re-read; v4 check confirmed content.",
"- Whether `common.py:195` parse path really raises ProviderError for a malformed 200: only the docstring was read.",
"- The 4.2 claim that `with_retry` would wrap a SpendRefused (F17): follows from retry.py:97-99 (read) but not run.",
"- Arithmetic (0.00225, 3 chars per token): the constants were read, nothing recomputed."]
open(sys.argv[1],"w").write("\n".join(out)+"\n")
print(tot,c)
