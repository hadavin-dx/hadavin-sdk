# Market scan 1: do we need these core modules and AK kits at all? (lead orders 119 + 120)

Date: 2026-11-07. Written by the cloud session from five parallel research agents (groups A-E). Research only: no code, no EGM review (EGM skipped: read-only research). Reviewed by nobody yet; the lead reviews before more core beyond the redaction and money chains (PR 63, 70, 66 and what they need) merges.

## Read this first: how strong is this evidence (brutal)
- The research agents had web SEARCH (summaries), not full page reads. GitHub API and most vendor sites (n8n.io, aws.amazon.com, temporal.io, doppler.com and others) were NOT reachable. Release dates and licences are first-hand only where a part file marks (P) PyPI JSON or a LICENSE file; everything else is a search summary (S).
- ALL prices are UNVERIFIED against vendor pages. Re-check before quoting to a client.
- "Cover %" is each agent's judgement against the ticket text, not a measurement. No candidate was installed or run.
- Order 120 bar (whole market, 5+ queries per group, rejected candidates named) is MET on query count and rejected lists for A, C, E; partly met for B and D after a second pass. Still NOT covered: B: Cloudflare services, Port/Retool, Inngest/Hatchet, GitHub topic search for starter kits. D: GCP Workflows, Power Automate approvals, Kestra, Prefect, Rasa, Voiceflow, Crisp. E: Qdrant not searched. C: DROP of P6b1 as code is the agent's weakest verdict.
- Tickets were read by heading and first lines, not in full (they are 10-16 revisions long).

## Verdict counts (42 rows)
ADOPT 9, WRAP 16, KEEP-CODE 12, DROP 5.

| Group | ADOPT | WRAP | KEEP-CODE | DROP |
|---|---|---|---|---|
| A redaction, folding, diagnostics (10) | 2 (P5b2, P5b5) | 3 (P1, P5c, P5b1) | 4 (P1c, P5a, P5b3, P5b4) | 1 (P2d, first-client scope only) |
| B state, store, audit, secrets (11) | 2 (P0a, secrets) | 5 (P3a, P6a, P6b2, signer, audit) | 3 (P2a, P4d, executor identity) | 1 (P0t) |
| C money and llm kind (6) | 1 (gateways) | 2 (P4a, P4c) | 2 (P4b1, P4b2) | 1 (P6b1 as code) |
| D agent runtime kits (5) | 1 (AK-G16) | 2 (AK-G1, AK-G15) | 1 (AK-G2 ledger) | 1 (JG-3, paused) |
| E pipeline, docs, eval, proof (10) | 3 (P8a, P8b, P8c) | 4 (AK1a, AK1c, AK2a, AK4a-1) | 2 (AK1b outbound gate, AK4a-2 joined harness) | 1 (AK0) |

## Headline findings (as the agents reported them; check the group files)
1. Guarantee-class gaps that no product closed in the scan: hard-cap and refuse-instead-of-estimate metering (Cloudflare and Azure docs admit overshoot under concurrency); fail-closed masking with safe put-back (Presidio reverses only via encrypt/decrypt operators); classifying which failed provider calls were billed; content-bound approvals with a separate executor identity; canary harness across a whole run.
2. Cheap partial cover exists: n8n Guardrails node (regex sanitise), Cloudflare AI Gateway DLP, Postgres RLS with FORCE for about 85-90 percent of tenant isolation, AWS Step Functions callbacks for about 65 percent of the needs-a-person queue for a client already on AWS.
3. Licence traps for an agency product: n8n is Sustainable Use (not OSI open source); Windmill AGPL; Unleash AGPL-3.0 from v8.0.0 (LICENSE file); immudb BUSL-1.1 (LICENSE file); Inngest server SSPL; Convoy ELv2; PyMuPDF AGPL; Camunda 8.6+ production licence; MinerU/Marker restricted.
4. Supply-chain and ownership: LiteLLM PyPI 1.82.7/1.82.8 were reported malicious on 2026-03-24 (secondary sources, UNVERIFIED); Helicone in maintenance mode after acquisition (2026-03-03); promptfoo bought by OpenAI; Lakera by Check Point; LLM Guard last release 2025-05-19, archive status unconfirmed; HumanLayer approvals SDK reported deprecated (only a competitor says so).
5. Volume check: group A's agent says its ticket volume (10 tickets) looks large against what a first client needs, but it still gives KEEP-CODE to P1c, P5a, P5b3 and P5b4 and WRAP to P1/P5c/P5b1. Which of those are guarantee-class is the lead's call; the cloud session has no vote on cutting scope.

## What the cloud session recommends (INFORM, not an order)
- Do not merge more core beyond the redaction and money chains until the lead has read the group files; keep P1a/P1b/P4d/P5c/P4b1 on the guarantee list.
- Candidates to ask the lead to cut or demote after review: P2d as separate scope, P6b1 as code (replace by a config check), JG-3 (already paused), AK0, P0t if already shipped. Each is a lead call.
- Re-verify prices and the LiteLLM incident from primary sources before any client-facing claim.

## Which offers sell on n8n + Close + Claude alone, and which need our modules
See the offers section inside Group E below.

---

# GROUP A (full agent file)

# Market scan, MODULE GROUP A (text folding, redaction/put-back, diagnostics, output guard)

Lead ORDER 119/120. Read 2026-11-07. Research only, no code changed, no EGM review (research agent; EGM skipped: read-only research).

Honesty notes up front:
- WebSearch returns summaries, not pages. Where I only have a search summary or a third-party blog, it is marked (S) = search summary, not read at source. Where I read the primary JSON/page it is marked (P).
- GitHub was NOT reachable (gh API: "GitHub access to this repository is not enabled"; api.github.com 403). So "last release" and "maintained?" come from PyPI JSON (P) where possible; repo-archived status and star counts are third-party (S) or UNVERIFIED.
- microsoft.github.io was not reachable from this session (DNS), so I could not read Presidio's own entity list or docs. Presidio claims below are from search summaries.
- Cover percentages are MY JUDGEMENT of how much of the ticket's need the candidate covers, stated with the evidence next to it. They are not measured. No candidate was installed or run.
- Prices are USD unless marked; most come from third-party pages (S). UNVERIFIED against vendor pages unless marked (P).
- Ticket scope was read from the first ~12 lines and key sections of each ticket (they are 16-revision, very large documents). I did not read the code (none of P1/P2d/P5c exists as code yet per the tickets).

## Summary table

| module | need (one line) | best candidates | cover % (judgement) | verdict |
|---|---|---|---|---|
| P1 text folding | Make hidden/obfuscated spellings (fullwidth, zero-width, homoglyph) visible to the redactor | stdlib `unicodedata` NFKC; Unicode UTS #39 confusables data; ftfy; confusable-homoglyphs | 40-50 (pieces exist; the "all views, one pipeline" is ours) | WRAP |
| P1c redactor gaps | Catch base64-encoded secrets, internal host names, bare numbers; permanent corpus test | Presidio recognizers (no base64 decode found); trufflehog-style decoders (UNVERIFIED); stdlib base64 | 20-30 | KEEP-CODE (small) |
| P2d fold scan, hidden-channel refusal, look-alike check | Refuse text with hidden channels / look-alike evasions before the model | prompt-canon (PyPI, S); Lakera / Cloudflare / Bedrock guardrails (cloud, after text leaves) | 20-35 | DROP from first-client scope (KEEP-CODE only if redaction is sold as a guarantee) |
| P5c redactor kind, masked model wrapper, safe put-back | Mask PII/account numbers BEFORE the model, restore only safely after | Presidio + LiteLLM `output_parse_pii`; LLM Guard Anonymize/Deanonymize (stale); Cloudflare AI Gateway DLP (redact, irreversible); Kong AI Sanitizer (Enterprise) | 65-75 for detection+reversible placeholders; 0-30 for the fail-closed/safe-put-back guarantee | WRAP |
| P5a closed error codes, safe diagnostic text | Error records made only of fixed words, never foreign text | OTel `error.type`/`exception.*` conventions; Sentry scrubbing; RFC 9457 style problem types (not searched) | 30-40 (vocabulary yes, "never prints foreign text" no) | KEEP-CODE (small) |
| P5b1 provider error plumbing | Turn provider/library errors into closed codes + retry decision, billing-safe | Anthropic/OpenAI SDK exception classes (status_code); LiteLLM exception mapping | 60-70 | WRAP |
| P5b2 config-error site table + CI test | CI fails if a new ConfigError site is not classified | ast-grep (MIT), Semgrep CE (LGPL-2.1 engine), Opengrep | 85-90 | ADOPT |
| P5b3 rewire writers (R3c/R3b) | Make every writer print render(diagnose()), no raw exception text | Python `logging.Filter` packages (small, unvetted); Sentry before_send | 15-25 (it is edits to OUR call sites) | KEEP-CODE |
| P5b4 output guard for logs/stderr/crash hooks | Nothing raw reaches unattended-tick stderr or crash hooks | redact-secret-adapters / payload-redactor (PyPI, S); OTel redaction processor; Vector `redact`; Datadog SDS | 40-50 (denylist scrubbers) vs ours = allowlist "own lines only" | KEEP-CODE |
| P5b5 pin no old error path, one backstop, operator page | Tests that old error-text paths never return; operator page | ast-grep / Semgrep rules + CI; docs | 85 | ADOPT |

Tally: ADOPT 2 (P5b2, P5b5), WRAP 3 (P1, P5c, P5b1), KEEP-CODE 4 (P1c, P5a, P5b3, P5b4), DROP 1 (P2d, first-client scope). 10 modules.

## Queries run (35 WebSearch queries, plus PyPI JSON fetches)

1 Microsoft Presidio PyPI latest release licence; 2 LLM Guard Protect AI Anonymize Deanonymize Vault; 3 Bedrock Guardrails sensitive info filter pricing; 4 LiteLLM guardrails presidio pii masking output unmask; 5 OTel Collector redaction processor blocked_values; 6 Sentry data scrubbing before_send pricing; 7 Cloudflare AI Gateway guardrails DLP PII pricing; 8 Azure AI Language PII pricing; 9 Google Sensitive Data Protection de-identify pricing reversible; 10 Lakera Guard pricing / Check Point; 11 Langfuse masking function; 12 Datadog Sensitive Data Scanner pricing; 13 n8n community PII redaction before OpenAI; 14 MCP server PII redaction proxy; 15 Presidio unicode normalization homoglyph evasion; 16 OpenAI Privacy Filter; 17 Presidio Data Privacy Stack move; 18 TR39 confusables Python library; 19 Kong AI Sanitizer; 20 Portkey guardrails PII; 21 python-stdnum IBAN Luhn licence; 22 Presidio DeanonymizeEngine reversible; 23 Python logging filter redact secrets tracebacks structlog; 24 Vector VRL redact; 25 Sentry Relay scrubbing limitations; 26 Langfuse licence and pricing; 27 n8n Guardrails node; 28 Guardrails AI detect_pii; 29 AI automation agency kit n8n Close Meta CAPI; 30 Nightfall / Private AI pricing; 31 n8n pricing 2026; 32 Semgrep licence; 33 ast-grep licence; 34 Anthropic Python SDK exceptions; 35 OTel semconv error.type.
PyPI JSON read (P): presidio-analyzer, llm-guard, ftfy, confusable-homoglyphs, guardrails-ai, nemoguardrails, scrubadub, litellm (version only), sentry-sdk (version only), detect-secrets.

## Rejected candidates (dated reason)

- LLM Guard (protectai/llm-guard): last PyPI release 0.3.16, 2025-05-19 (P), MIT (P). A third-party site says the repo is archived and no longer maintained (S, UNVERIFIED on GitHub). Rejected as a dependency; useful only as a design reference for Anonymize+Vault+Deanonymize.
- scrubadub 2.0.1: last release 2023-09-01 (P); licence metadata inconsistent (MIT field vs Apache classifier). Stale.
- detect-secrets 1.5.0: last release 2024-05-06 (P). Secrets only, no PII, no put-back.
- confusable-homoglyphs 3.3.1: MIT, last release 2024-01-30 (P). One blog (S) says it runs on raw input without chaining normalisation. Usable only as a data source.
- ftfy 6.3.1: Apache-2.0, 2024-10-26 (P). Fixes mojibake; it is not a security fold.
- Kong AI Sanitizer: has optional restore, but Enterprise-only (S) and needs Kong gateway plus a PII service. Not a small-client option.
- Datadog Sensitive Data Scanner: logs/APM only, SaaS lock-in, about $0.30/GB scanned on annual (S, third party). Rejected for this module: it scrubs after Datadog receives the data.
- Lakera Guard: acquired by Check Point (date conflicts across sources: Sept or Nov 2025, S); free tier 10K requests/mo then enterprise contract (S). Text goes to a third party before masking is proven. Rejected for the "mask BEFORE the model" guarantee.
- Azure AI Language PII and Google Sensitive Data Protection: send raw text to a cloud first; prices not verified (Azure about $1.00 to $0.25 per 1,000 records by volume, S; Google about $1 to $3/GB, conflicting, S). Fine for a client already on that cloud, not a default.
- Small MCP PII proxies (gs-mcp-proxy-pii-redactor, about 5 stars, MIT; umbryn-mcp "Unvalidated"; Obfuscate MCP): too young to depend on (S). Noted as proof the idea is common, not as adoption targets.
- Sentry server-side scrubbing: key-based denylist on listed event fields; I could NOT confirm it scrubs exception message text (S). Not a guarantee.
- Langfuse server-side masking: Enterprise licence only (S). Client-side `mask` function is free but only covers what is sent to Langfuse.

## Per-module detail

### P1 Text folding (PRs P1m, P1a, P1b)
1. Need: produce NFKC/zero-width/homoglyph-folded views of text so the redactor and guards see what a human sees. Ticket is stdlib-only by lead order (P1c rung table), 16 revisions.
2. Candidates:
   - stdlib `unicodedata` NFKC. PSF-2.0. Python 3.13 (ticket-stated). Cover about 25% (compatibility folding only; NFKC does not collapse cross-script homoglyphs or remove zero-width joiners, S: prompt-canon and Mimecast pages).
   - Unicode UTS #39 confusables.txt skeleton (Unicode licence; data only). Cover about 20% additional (cross-script map). Needs our code to use it; I did not fetch the data file (UNVERIFIED version).
   - confusable-homoglyphs 3.3.1. MIT. 2024-01-30 (P). Detects, does not build the skeleton chain (S). Cover about 10%.
   - ftfy 6.3.1. Apache-2.0. 2024-10-26 (P). About 5% (text repair, not adversarial).
3. Price: all free. Lock-in none. Client can own the licence: yes (all permissive).
4. Cannot guarantee: masking BEFORE the model (a fold gap is a leak; a library does not know our pipeline); that every view is scanned.
5. Verdict: WRAP. Use stdlib plus the UTS #39 table, ours is the thin pipeline and the corpus. Honest remark: 16 frozen revisions for a fold function looks like heavy over-specification against what the market provides; the guarantee is the corpus test, not the code volume.
   Test idea: for each secret/PII fixture, generate variants (fullwidth, zero-width inserts, Cyrillic look-alikes, combining marks); assert the masked output contains no variant and no skeleton of the original.
6. n8n + Close + Claude alone can sell: nothing here, folding is invisible to buyers. Needs our module only if a client demands "PII never reaches the model" as a contractual guarantee.
Monthly cost to small client: 0 licence.

### P1c Redactor gaps (base64 view, internal host names, bare number, corpus test)
1. Need: also mask values hidden as base64, whole internal host names, and a bare number as a decided property; permanent corpus test.
2. Candidates: stdlib `base64` (PSF-2.0) for decoding, about 20%; Presidio custom recognizers (MIT, 2.2.366, 2026-10-27, P) can add patterns but I found no base64-decode view (S, UNVERIFIED); trufflehog/gitleaks-class scanners may decode base64 (UNVERIFIED, not searched, GitHub unreachable).
3. Price free. Licence permissive (Presidio MIT). Lock-in none.
4. Cannot guarantee: masking BEFORE the model for decoded forms unless wired into the same loop (ticket's repeat-loop point).
5. Verdict: KEEP-CODE (small; guarantee: a value taught by any later view also masks earlier views). Test idea: encode a known secret in base64 standard and urlsafe, chunked and carved; assert zero residual.
6. Sellable with n8n+Close+Claude: no. Needs our module only for the PII-before-model guarantee offers.

### P2d Fold scan, hidden-channel refusal, look-alike check
1. Need: refuse inputs carrying hidden channels or look-alike spoofs, and scan the folded views.
2. Candidates: prompt-canon (PyPI, S, details UNVERIFIED), cloud guardrails (Bedrock about $0.10 per 1,000 text units for PII, regex free, S; Cloudflare Guardrails billed as Workers AI usage, S), n8n Guardrails node (Check Text uses an LLM; since n8n 1.119, S). Cover about 20-35% by my reading; none documents hidden-channel refusal.
3. Price: Bedrock/Cloudflare per use; n8n see below. Lock-in cloud-specific.
4. Cannot guarantee: masking before the model; fail-closed refusal as a contract.
5. Verdict: DROP from first-client scope. I found no sellable first-client offer that depends on look-alike refusal. Revisit as KEEP-CODE only when redaction is sold as a guarantee. This is an opinion; I have not read the lead's offer list.
6. n8n+Close+Claude sells everything a first client buys without this module.

### P5c Redactor kind, masked model wrapper, safe put-back
1. Need: mask PII and account numbers before any model call, call the model on placeholders, restore values only where safe.
2. Candidates:
   - Presidio (analyzer+anonymizer). MIT. 2.2.366, 2026-10-27 (P). Maintained; project moved to the independent Data Privacy Stack org in mid-2026 (S: announcement dated 2026-06-29), still MIT. Detection cover about 60-70% (many recognizers; docs warn detection is not complete, S). Reversibility only via encrypt/decrypt operator (S), not placeholder maps.
   - LiteLLM Presidio guardrail. MIT. 1.108.2 (P; date not read). Supports MASK/BLOCK pre-call and `output_parse_pii` to restore (S, LiteLLM docs). Cover about 65-75% of the flow. Unverified for streaming, tool-call arguments, and failure behaviour.
   - Cloudflare AI Gateway DLP. DLP scanning free; flag/block/redact (S). Redaction is not described as reversible (S). About 40%.
   - Others: Guardrails AI `detect_pii` (Apache-2.0, 0.11.0, 2026-08-14, P) wraps Presidio, `fix` returns anonymised text; Portkey gateway redact toggle (irreversible per one comparison, S); Kong (Enterprise, restore option); OpenAI Privacy Filter (Apache-2.0 open weights, April 2026, S) is a detector for contextual PII incl. account numbers, 1.5B parameters.
   - Account-number detectors: python-stdnum (LGPL-2.1+ per S, flag LGPL; IBAN and Luhn included), Presidio recognizers (list not read).
3. Price: Presidio, LiteLLM OSS free; self-host cost is a container plus a spaCy model (my estimate: a few USD/month VPS, UNVERIFIED). Private AI about $0.00006/character pay-per-use (S). Bedrock about $0.10/1,000 units (S). Client can own: yes for Presidio/LiteLLM.
4. Cannot guarantee: masking BEFORE the model as fail-closed (a Presidio error or miss passes text; aMazeControlPlane replaces a field with a placeholder on error, S, others differ); safe put-back (restore into the right field only, no restored text re-entering a prompt, no double restore); money exactness.
5. Verdict: WRAP. Presidio (or Privacy Filter) as detector; ours is the thin guarantee layer: fail-closed, per-request map, put-back rules. Anything over 80% of detection is adopted; the missing part is the guarantee gap, with test idea: inject detector exceptions and timeouts, assert no model call is made; plant a placeholder-lookalike in model output, assert it is not restored.
6. n8n+Close+Claude alone: basic masking via n8n Guardrails Sanitize Text (regex, no AI; S) or an HTTP node to a Presidio container, for lead enrichment and reply drafting. Truly needs our module: offers where a client must prove account numbers/PII never reach Claude and values come back safely (finance, healthcare, intake with IDs).

### P5a Closed error codes and safe diagnostic text (R1)
1. Need: error records made only from a closed list (code, step, file:line, numbers); never text from documents, models, people or libraries.
2. Candidates: OpenTelemetry exception semconv (error.type, exception.message, exception.stacktrace; S) gives names, but exception.message is the leak vector; Sentry default scrubber (denylisted keys only, recursion off by default, S); RFC 9457 problem types (not searched).
3. Price free to $26-80/mo for Sentry paid plans (S, third party). Lock-in low (OTel), medium (Sentry).
4. Cannot guarantee: that no foreign text is printed; scrubbing is denylist, ours is allowlist.
5. Verdict: KEEP-CODE (small). Guarantee: diagnostics contain only closed-list tokens. Test: raise exceptions carrying planted secrets from every code path, assert `render()` output matches the grammar.
6. n8n+Close+Claude: n8n error workflows print raw error messages; fine for non-sensitive offers. Our module only where logs may be shared with a client or vendor.

### P5b1 Provider error plumbing (R1P)
1. Need: map provider errors to closed codes plus a retry decision that keeps billing safe (reserved worst case booked when decision fails).
2. Candidates: Anthropic Python SDK exceptions (APIStatusError with status_code, RateLimitError, InternalServerError, connection/timeout classes; S via source mirror) and built-in retries (S, default count unconfirmed); LiteLLM exception mapping (UNVERIFIED).
3. Free. Lock-in to SDK.
4. Cannot guarantee: money exactness (a retried call may be billed twice; no SDK books our reserve).
5. Verdict: WRAP: use SDK classes for status/type, never read messages; ours is the mapping and the billed-class rule. Test: fault-inject 429/529/timeouts, assert exactly one booking per logical call.
6. n8n+Close+Claude: n8n retry-on-fail covers it. Our module only where per-call cost is billed through to a client.

### P5b2 Config-error site table and CI test (R3a)
1. Need: a checked table of every place that builds a ConfigError, with a generator and a CI test failing on unclassified new sites.
2. Candidates: ast-grep (MIT; npm record shows 0.42.1 published 2026-04-04, S, may be stale), Semgrep CE (LGPL-2.1 engine; Semgrep-authored rules under a non-compete rules licence since Dec 2024, S; own rules unaffected as far as I could find, UNVERIFIED), Opengrep fork (LGPL-2.1, S). Cover about 85-90%: a rule "ConfigError( not in allowlist file" is a one-pattern rule; the classification CSV is ours (data).
3. Free. Lock-in none.
4. Cannot guarantee: nothing in the listed guarantee classes; it is repo hygiene.
5. Verdict: ADOPT (rule config + glue). The ticket's own generator plus 39-mutant style runner is not needed if a pattern rule gives the same gate.
6. Not sellable; internal.

### P5b3 Rewire writers (R3c, R3b)
1. Need: make cli, tick, extract, injection guard, approvals receiver and `tools.error_reason` print only render(diagnose()); rewrite 18 config-error messages.
2. Candidates: none replace edits to our own call sites. Logging filters (see P5b4) are a backstop, not the fix.
3. n/a.
4. Cannot guarantee: any foreign text the writer still concatenates.
5. Verdict: KEEP-CODE (own call sites). Test: the P5a xfail-strict hostile rows become plain asserts.
6. Not sellable; internal.

### P5b4 Output guard for logs, stderr, crash hooks (R2)
1. Need: stderr/log lines are either own lines or dropped; crash hooks print nothing raw; unattended `tick` stderr safe.
2. Candidates:
   - redact-secret-adapters (PyPI, S): logging.Filter that handles tracebacks and exc_text, OTel span processor. Version/licence/date UNVERIFIED. About 40%.
   - payload-redactor (PyPI, S): `redact_traceback`, structlog helper, excepthook example. UNVERIFIED. About 40%.
   - OTel Collector redaction processor (Apache-2.0 header on config.go, S): traces pipeline only per Splunk docs (S); blocked_values masks regex matches. About 25% for this need.
   - Vector `redact` (VRL; licence UNVERIFIED, I believe MPL-2.0 but did not confirm): regex on log lines in transit. About 30%.
   - Datadog SDS: rejected above.
3. Price free (OSS) to per-GB SaaS. Client can own: yes for OSS.
4. Cannot guarantee: allowlist default-deny. These are denylist/regex; a novel secret format passes. Also tamper-evident audit: not provided. Note one cautionary report of a Vector remap that silently stopped redacting after an upgrade (S).
5. Verdict: KEEP-CODE (guarantee: only own lines leave the process). Optional adopt of one of the logging filters as the final backstop. Test: run a subprocess that raises with planted secrets in message, locals, chained cause and `__notes__`; capture stderr; assert no planted token.
6. n8n+Close+Claude: n8n execution logs hold raw payloads; enough for small offers. Our module for unattended agents with client data in logs.

### P5b5 Pin no old path, one backstop, operator page, close corpus (R5)
1. Need: tests that no old error-text path returns, exactly one backstop, an operator page.
2. Candidates: ast-grep / Semgrep / ruff rules plus CI; docs page by hand. Cover about 85%.
3. Free.
4. Cannot guarantee: none of the listed classes (hygiene).
5. Verdict: ADOPT for the pinning (rules in CI); the operator page is writing, not a module.
6. Not sellable; internal.

## Price and ownership summary (small client, monthly)

- n8n Cloud Starter about EUR 20/mo annual (2,500 executions), Pro about EUR 50/mo (10,000), Business about EUR 667/mo (S, third-party roundups; Community Edition self-hosted free; Sustainable Use licence assumed, UNVERIFIED). Client can own the n8n account: yes.
- Presidio + LiteLLM self-hosted: 0 licence, my estimate a few USD/month hosting (UNVERIFIED), client can own.
- Bedrock Guardrails PII about $0.10 per 1,000 text units, regex free (S). Cloudflare AI Gateway DLP free (S). Azure/Google/Private AI/Nightfall: see rejected list.
- Sentry paid plans $26-80/mo (S). Langfuse cloud Hobby free, Core $29/mo (S); core MIT with commercial ee/ directory (S).

## Cross-cutting findings
- The market covers DETECTION and basic masking well and cheaply. It covers fail-closed enforcement, safe put-back and allowlist-only diagnostics poorly or not at all (I found no product claiming them).
- The honest weak point of group A is size: group A's tickets are 16-revision designs for what are mostly thin layers over Presidio/stdlib. Against the owner's doubt: for modules P5b2 and P5b5 our module is not needed; for P1/P5c/P5b1 it is needed only as a thin wrapper.
- Whether any first-client offer needs group A at all depends on whether PII/account numbers go to the model. If a first offer is lead qualification (Close + Meta CAPI + Claude), names/emails/phones go to Claude; n8n Guardrails Sanitize Text or Presidio covers the common case and a signed DPA with the model vendor may be the cheaper control. I did not research DPAs.

## SOURCES (all read 2026-11-07)

(P) = primary page/JSON read; (S) = search summary only.
- https://pypi.org/pypi/presidio-analyzer/json (P), https://pypi.org/project/presidio-analyzer/ (P: 2.2.366, 2026-10-27, MIT, home github.com/data-privacy-stack/presidio)
- https://pypi.org/pypi/llm-guard/json (P: 0.3.16, 2025-05-19, MIT)
- https://pypi.org/pypi/ftfy/json (P), https://pypi.org/pypi/confusable-homoglyphs/json (P), https://pypi.org/pypi/guardrails-ai/json (P), https://pypi.org/pypi/nemoguardrails/json (P: 0.24.1, 2026-09-16, Apache-2.0), https://pypi.org/pypi/scrubadub/json (P), https://pypi.org/pypi/litellm/json (P, version only), https://pypi.org/pypi/sentry-sdk/json (P, version only), https://pypi.org/pypi/detect-secrets/json (P)
- LiteLLM Presidio docs: https://docs.litellm.ai/docs/proxy/guardrails/pii_masking_v2 (S)
- Bedrock Guardrails pricing: https://aws.amazon.com/about-aws/whats-new/2024/12/amazon-bedrock-guardrails-reduces-pricing-85-percent/ and third parties (S)
- OTel redaction processor: https://help.splunk.com/en/splunk-observability-cloud/manage-data/manage-sensitive-data/sanitize-data-with-opentelemetry-collector-processors/redaction-processor (S)
- Sentry: https://docs.sentry.io/platforms/python/data-management/sensitive-data (S); pricing aggregators (S)
- Cloudflare: https://developers.cloudflare.com/ai-gateway/features/ , https://developers.cloudflare.com/ai-gateway/reference/pricing (S)
- Azure Language pricing: https://azure.microsoft.com/pricing/details/cognitive-services/text-analytics/ (S, amounts blank)
- Google SDP pricing: https://cloud.google.com/sensitive-data-protection/pricing (S, conflicting)
- Lakera/Check Point: https://dev.to/dokasuka_don_de7635cc481c/lakera-guard-was-acquired-for-300m-here-is-the-free-alternative-we-built-for-developers-4h8 (S)
- Langfuse: https://langfuse.com/docs/observability/features/masking.md , https://langfuse.com/self-hosting/security/data-masking.md (S)
- Datadog SDS pricing: https://signoz.io/blog/datadog-logs-pricing/ (S)
- n8n template: https://n8n.io/workflows/14320 ; Guardrails node: https://n8n.io/workflows/11025 , https://optimizesmart.com/blog/n8n-guardrails-guide/ (S)
- MCP PII proxies: https://github.com/growthspace-engineering/gs-mcp-proxy-pii-redactor , https://github.com/chernomaz/aMazeControlPlane/releases/tag/v0.8 , https://lobehub.com/mcp/rinava-umbryn-mcp (S)
- Unicode evasion: https://www.mimecast.com/blog/5-keystrokes-that-defeat-a-privacy-filter/ , https://pypi.org/project/prompt-canon/ , https://paultendo.github.io/posts/confusable-detection-without-nfkc (S)
- OpenAI Privacy Filter: https://www.helpnetsecurity.com/2026/04/23/openai-privacy-filter-personally-identifiable-information/ (S)
- Presidio move: https://www.everydev.ai/developers/data-privacy-stack (S)
- Kong: https://developer.konghq.com/ai-gateway/policies/ai-sanitizer/ (S)
- Portkey: https://usagepricing.com/blueprint/portkey , https://portkey.ai/docs/virtual_key_old/product/security/pii (S)
- python-stdnum: https://arthurdejong.org/python-stdnum/ (S)
- Presidio deanonymize: https://tessl.io/registry/tessl/pypi-presidio-anonymizer/2.2.0/files/docs/deanonymization.md (S)
- Log redaction libs: https://pypi.org/project/payload-redactor/ , https://pypi.org/project/redact-secret-adapters/ , https://pypi.org/project/misprint (S)
- Vector redact: https://docs.groundcover.com/use-groundcover/configuring-pipelines/logs-traces-sensitive-data-obfuscation (S)
- Guardrails AI detect_pii: https://hub.guardrailsai.com/validator/guardrails/detect_pii (S)
- Agency kits / CAPI: https://www.datahash.com/connections/close/meta-capi-crm/ (S)
- Nightfall / Private AI: https://private-ai.com/en/pricing/ , https://www.nightfall.ai/pricing (S)
- n8n pricing: https://www.jetadmin.io/blog/n8n-pricing/ (S)
- Semgrep/Opengrep: https://semgrep.dev/blog/2024/important-updates-to-semgrep-oss , https://ai.semgrep.dev/docs/faq/comparisons/opengrep (S)
- ast-grep: https://packages.ecosyste.ms/api/v1/registries/npmjs.org/packages/@ast-grep%2Fcli (S)
- Anthropic SDK exceptions: https://sources.debian.org/data/main/a/anthropic-sdk-python/0.79.0-1/src/anthropic/_exceptions.py (S)
- OTel exception semconv: https://opentelemetry.io/docs/specs/otel/semantic-conventions/index.md (S)
- Local tickets read (first ~12 lines and selected sections): handover/tickets/{P1,P1c,P2d,P5a,P5b1,P5b2,P5b3,P5b4,P5b5,P5c}.md

## UNVERIFIED list
Repo archived status and release dates on GitHub for every project; Presidio entity list and Unicode handling; LiteLLM and Sentry upload dates; Vector and redact-secret-adapters licences; UTS #39 data version; trufflehog base64 decoding; n8n licence terms; all non-PyPI prices; whether any hosted guardrail refuses hidden-channel text; whether LiteLLM's restore is safe under streaming and tool calls.

---

# GROUP B (full agent file)

# Market scan, MODULE GROUP B (lead ORDER 119/120), read 2026-11-07

EGM skipped: read-only research. I write findings only; I approve nothing. No code was changed. No secrets appear here.

Honesty notes (read first):
- Tools: WebSearch returns summaries from mostly secondary blogs. WebFetch worked ONLY for github.com, raw.githubusercontent.com, api.github.com and pypi.org. n8n.io, aws.amazon.com, www.doppler.com and docs.n8n.io did not resolve from this session (host blocked). So ALL prices below are secondary or UNVERIFIED. The `gh` CLI was refused for repos not attached. After about 14 api.github.com calls the API returned 403 (rate limit), so several license/release cells are UNVERIFIED.
- Tickets: I read only headings and the first lines of each ticket plus the plan-v3 table rows, not the full 60 lines per ticket. "Need" lines are from those headings. P6b2 and P0t were read least.
- "Cover %" is MY JUDGMENT from the cited feature, not a measured number. It is not tested against our tests.
- Queries run (WebSearch, 11): (1) feature flag kill switch Unleash OpenFeature flagd; (2) Atlas Flyway Alembic sqitch migration tools; (3) immudb tamper-evident audit; (4) pgaudit hash chain Postgres tamper evident; (5) Infisical OpenBao Vault license pricing; (6) human-in-the-loop approval separate executor HumanLayer Temporal LangGraph; (7) AWS Secrets Manager pricing; (8) import-linter forbidden contracts; (9) GitHub rulesets / secret scanning private repo free plan; (10) S3 Object Lock + CloudTrail log integrity; (11) Cerbos/Permit/OpenFGA approval separation of duties; (12) n8n human-in-the-loop Wait node, license, price. Fetches: GitHub README/API for immudb, openbao, infisical, atlas, unleash, flagd, flyway, temporal, rekor, humanlayer, sops, alembic (PyPI), n8n LICENSE.md.
- Not searched (gap, say so): MCP registries for these areas, Azure/GCP/Cloudflare equivalents (Cloudflare Zero Trust/Workers KV kill switch, Azure Confidential Ledger, GCP Secret Manager, Azure Key Vault), AI-ops governance platforms, "AI automation agency" starter kits, Port/Retool/Appsmith/Budibase approval UIs, Hatchet/Inngest/Activepieces. The ORDER 120 "whole market" bar is therefore NOT met for group B. Treat verdicts as provisional.

## Summary table

| Module | Need | Best candidates | Cover % (judgment) | Verdict |
|---|---|---|---|---|
| P2a stop state | Store-backed stop; audited reset; compromised runtime cannot clear it | Unleash (AGPL-3.0), flagd (Apache-2.0), Flagsmith/Flipt (UNVERIFIED) | 40-50 | KEEP-CODE (guarantee: runtime cannot reset stop) |
| P3a migration rule | Renumber in merge order, forward-only, CI fails on duplicate/out-of-order, old code reads new schema | Atlas (Apache-2.0), Flyway (Apache-2.0), Alembic (MIT) | 70-80 (numbering/order); 0 for "old release reads new schema" | WRAP (adopt a tool, keep one test) |
| P4d store contract | One contract test suite over memory and Postgres; DB library only inside store kind | None as product; pytest + Testcontainers pattern | n/a (it is a test suite) | KEEP-CODE (small); consider dropping memory backend |
| P0a backups / push model | Push local heads, branch protection, third-party-file check | GitHub rulesets + secret scanning; plain git mirror | 85-90 (config) | ADOPT (config) |
| P0t stage rename | dev -> demo rename, stages demo/pilot/prod | none (mechanical refactor) | n/a | DROP as market item; do the rename as plain code |
| P6a client-profile check | Pilot/prod refuses test objects; CI catches side-door model calls | import-linter (BSD), Semgrep (UNVERIFIED) | 60-70 (CI half); 0-10 (startup refusal) | WRAP |
| P6b2 secret boundary + kind identity | Only the executor imports secrets; lint; kind identity | import-linter, gitleaks (UNVERIFIED) | 60-70 (lint half) | WRAP |
| secrets kind | env/file default + managed alternative | AWS Secrets Manager, OpenBao (MPL-2.0), Infisical (MIT core), Vault (BUSL, flagged) | 90+ | ADOPT |
| signer | Sign approvals/records | cloud KMS, libsodium/PyNaCl (UNVERIFIED), Sigstore Rekor (Apache-2.0) | 70 (primitive) | WRAP |
| tamper-evident audit | Hash-chained, truncation-detectable log | immudb (BUSL-1.1), S3 Object Lock + CloudTrail digests, hand-built Postgres chain | 60-80 | WRAP (KEEP the verifier) |
| channel / executor, separate identity | Approver and executor are different identities; runtime holds no keys | Temporal (MIT), LangGraph interrupt, n8n Wait/form, Permit.io | 40-60 | KEEP-CODE (guarantee) for executor; ADOPT for channel |

Counts (11 rows): ADOPT 2 (P0a, secrets kind; plus channel half), WRAP 5 (P3a, P6a, P6b2, signer, audit), KEEP-CODE 3 (P2a, P4d, executor), DROP 1 (P0t). The channel half is ADOPT but is counted inside the executor row.

## Per-module detail

### P2a stop state
1. Need: a durable stop switch the running agent cannot clear; reset is audited and done by a separate role (ticket revision 10 discusses role timeouts, locks, a stop-request table).
2. Candidates: Unleash; flagd/OpenFeature; Flagsmith or Flipt (not checked, UNVERIFIED).
3. Evidence:
   - Unleash: GitHub API shows license AGPL-3.0 (read 2026-11-07), 14131 stars, pushed 2026-11-06; latest release v8.3.1 published 2026-10-29. A blog I searched claimed Apache-2.0; the GitHub API, the repo LICENSE file (GNU AGPL v3 heading) and Unleash's own announcement (moved to AGPLv3 from v8.0.0; official Docker images and SDKs stay permissive per that vendor page) agree on AGPL for the server, so the blog is outdated. CONFIRMED from a second source 2026-11-07. AGPL flag: a client or agency embedding or modifying it must publish source of modifications offered over a network. Cover: ~45 (kill-switch flag, no DB-role separation). Price: self-host free; SaaS price UNVERIFIED.
   - flagd: Apache-2.0, latest core/v0.19.2 published 2026-10-28, pushed 2026-11-07. Cover ~40: reads flags from file/HTTP; it has no concept of "runtime cannot write the flag" beyond file permissions. Free; no lock-in (OpenFeature standard).
4. Cannot guarantee: tamper-evident audit of reset; separate-identity reset; that a compromised runtime cannot flip it (flag tools assume the admin API key is held by someone else, but nothing proves the agent process lacks network path/credentials).
5. Verdict: KEEP-CODE. Guarantee: "after stop, no agent process role can clear it, and every reset has an audit row by a different role." Test idea: connect with the runtime DB role, try UPDATE/DELETE/SET LOCAL timeout resets on the stop table; all must fail; reset by stopper role writes an audit row.
6. n8n + Close + Claude alone: a manual "pause" toggle for lead-follow-up bots is fine with an n8n workflow deactivation. Our module is needed only when an agent can spend money or message customers unattended.
Price for small client: free to ~USD 20/month (n8n cloud Starter figures are inconsistent across secondary sources, UNVERIFIED). Client can own the licence: yes (flagd), caution for Unleash AGPL.

### P3a migration rule
1. Need: migration numbers renumbered in merge order, forward-only, CI fails on duplicate or out-of-order number, and a test that the previous release reads the new schema or fails loudly.
2. Candidates: Atlas, Flyway, Alembic.
3. Evidence:
   - Atlas: README (read 2026-11-07) says Apache-2.0 and "50+ built-in analyzers" with `atlas migrate lint`; latest release v1.3.0 published 2026-08-02 per API. The README text I fetched did NOT mention a checksum/linear-history check; I believe Atlas has an `atlas.sum` file but that is memory, UNVERIFIED. Cover ~70. Some Atlas features are paid (UNVERIFIED which).
   - Flyway: GitHub license Apache-2.0, latest flyway-13.12.1 published 2026-11-05. It is a versioned migration runner that validates applied versus local. Cover ~70 (out-of-order detection by default is from memory, UNVERIFIED). Paid tier exists (Redgate); price UNVERIFIED.
   - Alembic: PyPI license MIT, version 1.20.1 (latest upload date not read; last I saw 1.17.1 on 2025-10-29). Has revision graph; a multiple-heads check exists (memory, UNVERIFIED). Python-native, fits our stack.
4. Cannot guarantee: previous-release-reads-new-schema, semantic non-revertible markers, no double-applied migration across concurrent deploys beyond DB locks.
5. Verdict: WRAP. Adopt Alembic or Atlas for numbering, ordering and lint; keep our one downgrade-read test. Test idea: apply migration N+1, run the previous release's test suite subset against it, expect pass or loud named failure.
6. n8n+Close+Claude offers have no schema; this module only matters once we hold client data in our own Postgres.
Price: free. Client can own: yes.

### P4d store contract suite (memory + Postgres)
1. Need: one contract test suite proving both backends behave the same; DB library imported only inside the store kind.
2. Candidates: there is no product; pattern is pytest plus a real Postgres (Testcontainers or CI service). Rejected: SQLAlchemy as the store layer replacement (changes architecture, not checked).
3. Cover: not measurable; this is our test. Licence concerns none.
4. Cannot guarantee: whatever we do not write tests for (money exactness, double-apply).
5. Verdict: KEEP-CODE (small). Surprising option, my opinion: if the memory backend is dev/test only (plan-v3 row 78), dropping it and testing Postgres only would delete the whole "two backends agree" suite. That is a design question for the lead, not a finding I verified.
6. n8n+Close+Claude need no store. Our store is needed for the meter, stop state, and audit.

### P0a backups, push model, third-party check
1. Need: push unpushed heads as branches, main protected, secret/name scan, list third-party files.
2. Candidates: GitHub rulesets/branch protection; GitHub secret scanning/push protection; gitleaks/TruffleHog (UNVERIFIED, not searched).
3. Evidence: GitHub docs say rulesets are available on public repos with Free, and private repos need Pro/Team/Enterprise (docs.github.com via search, 2026-11-07). Secret scanning on private repos is a paid add-on "GitHub Secret Protection"; price not found. A secondary report says GitHub added two Anthropic key patterns to push protection by default on 2026-10-13 (UNVERIFIED).
4. Not applicable to the six guarantee classes except nothing.
5. Verdict: ADOPT (config). Our ticket is text-only anyway.
6. Irrelevant to sellable offers; internal hygiene.
Price: GitHub Team seat price not found (UNVERIFIED).

### P0t stage rename
1. Need: rename stage dev to demo; stages exactly demo, pilot, prod.
2. Candidates: none; a find-and-replace plus a test.
3-4. n/a.
5. Verdict: DROP as a market module ("our module is not needed" is true in the sense nothing exists to buy); do the rename as normal code with a test that the old name is rejected.
6. No offer depends on it.

### P6a client-profile check
1. Need: pilot/prod app refuses to start with test objects injected by code; CI test that no `src/` code reaches the llm kind except through the masking wrapper.
2. Candidates: import-linter; Semgrep rules (UNVERIFIED, not searched); LiteLLM as a single gateway (not checked).
3. Evidence: import-linter is BSD (a third-party index says BSD-2-Clause), latest 2.12 dated 2026-06-23 in its release notes, forbidden-module contracts documented (search 2026-11-07). Cover ~65 for the CI half. It checks imports, NOT dynamic calls such as `getattr`, HTTP libs, or subprocess to the model; that gap needs a Semgrep rule or a runtime network deny. The startup refusal is our config logic: ~0-10 cover.
4. Cannot guarantee: masking BEFORE the model at runtime (static import checks do not prove every payload passed the redactor).
5. Verdict: WRAP. Test idea for the guarantee: spy on the HTTP transport in an integration test with a planted PII value; the model call must never see it.
6. n8n+Close+Claude cannot enforce this; any offer sending client documents with PII to the model needs it. Lead-gen/CRM copy offers need less.

### P6b2 secret boundary + kind identity
1. Need: lint that only the executor reads secrets; secrets import test; kind identity; migration DSN behind secrets kind.
2. Candidates: import-linter (as above), gitleaks (UNVERIFIED).
3. Cover ~60-65 for the lint, same dynamic-access caveat (os.environ reads are not imports).
4. Cannot guarantee: a compromised runtime cannot read env vars it was given. Real boundary = separate process/identity, not lint.
5. Verdict: WRAP (lint via import-linter; custom check for `os.environ` use). Test idea: run the runtime process with an empty environment and fake network; the tool call must fail until routed through the executor.
6. Needed when an agent can touch payment or CRM write credentials.

### secrets kind
1. Need: env/file default plus a managed-secret alternative.
2. Candidates:
   - AWS Secrets Manager: USD 0.40 per secret per month plus USD 0.05 per 10,000 API calls (secondary sources, AWS page not reachable; UNVERIFIED).
   - OpenBao: MPL-2.0 (README read 2026-11-07), latest v2.7.2 published 2026-10-26; Linux Foundation-style open governance; self-host only (a secondary source says no managed SaaS).
   - Infisical: MIT for the main repo, `ee` directories under a proprietary licence (README read 2026-11-07); latest v0.167.6 published 2026-11-03; a secondary source quotes Pro USD 18 per identity per month (UNVERIFIED).
   - HashiCorp Vault: BUSL-1.1 since Aug 2023 per secondary source (flag); GitHub API for it returned 403 so not verified by me.
3. Cover ~90 for fetching secrets; none of them guarantees our boundary.
5. Verdict: ADOPT (the kind is an adapter interface; environment/file default stays). Client can own the licence: yes for OpenBao/Infisical; the client holds the AWS account.
Price for small client: USD 0.40 x number of secrets (e.g. 10 secrets = USD 4/month, secondary).
6. A single n8n credential store (encrypted in n8n) covers n8n+Close+Claude; external secrets in n8n is an enterprise feature (UNVERIFIED).

### signer
1. Need: sign approvals/records so a replay or edit is detectable (plan row P7d: canonical JSON, signer split).
2. Candidates: cloud KMS (AWS/GCP/Azure, not searched), Sigstore Rekor (Apache-2.0, v1.5.5 published 2026-10-21, a transparency log, UNVERIFIED fit), PyNaCl/libsodium (not searched).
3. Cover ~70 for the signature primitive. None provides our canonical-form binding of approval to exact action payload.
5. Verdict: WRAP. Test idea: change one byte or key order in a signed approval; verification must fail; replay an approval for a different action id; must fail.
6. Only matters once approvals exist (refunds, payments).

### tamper-evident audit
1. Need: append-only audit that detects edit, deletion and truncation.
2. Candidates:
   - immudb: README says "licensed under the Business Source License 1.1" (read 2026-11-07), so BUSL, not open source. CONFIRMED from a second source (LICENSE file, 2026-11-07): Licensed Work immudb 1.9.x or later; Change License Apache-2.0 four years after each version is published; Additional Use Grant allows production use except offering it hosted or bundled to outside parties in a way that competes with Codenotary's paid versions. An agency bundling it into a paid client offer is a grey area needing legal review. Latest v1.11.2 published 2026-09-03; v1.11 (2026-05 per press) added structured audit logging and a PostgreSQL wire protocol. Secondary source: tamper-evident, not proof against root deleting the volume. Cover ~70. Price: self-host; managed pricing UNVERIFIED.
   - S3 Object Lock (compliance mode) plus CloudTrail digest validation: sources (AWS doc via search) say validation detects but does not prevent tampering; compliance-mode Object Lock prevents deletion even by root. Cover ~60 as an external anchor, not as per-row audit. Price: S3 storage cents per GB (UNVERIFIED).
   - Hand-built Postgres hash chain: several blogs show previous-hash columns; one notes the truncation gap and recommends anchoring the head externally. pgaudit logs but does not chain (my memory, UNVERIFIED; no extension found).
3. Cannot guarantee in any of them: that the app writes the right event (completeness), and truncation detection unless the head is anchored outside the writer's reach.
4. Verdict: WRAP: use Postgres chain or immudb (check BUSL against the client's use) and S3 Object Lock for anchors; keep our verifier. Test idea: delete the last N rows and re-run verify against the anchored head; must fail.
6. n8n execution logs exist but are editable by the instance admin; for a small-budget offer that is acceptable. Regulated or money-moving offers truly need this.
Price: USD 0 to a few dollars per month on S3 (UNVERIFIED).

### channel / executor with separate identity
1. Need: a human approves on a channel; a different executor identity performs the action; the requesting runtime holds no credentials.
2. Candidates:
   - Temporal: MIT (GitHub API 2026-11-07), latest v1.32.2 published 2026-11-02, signals plus workers give durable approval waits; separate worker credentials are possible but you must design them. Cover ~50. Self-host heavy; Cloud price UNVERIFIED.
   - LangGraph `interrupt`: docs describe pause-until-resume; checkpoint is saved; nothing said about who may resume, so no separate-approver guarantee (search 2026-11-07).
   - n8n Wait/Human-in-the-loop node: hosted form, Slack/Gmail messaging (secondary). n8n licence is Sustainable Use (LICENSE.md read 2026-11-07): internal business use allowed, selling or distributing the software forbidden. Flag for agencies reselling hosted n8n. The identity of the approver is not provably separate (UNVERIFIED).
   - Permit.io: embeddable approval components; OPAL Apache-2.0; paid tiers from USD 5/month per a 2026 guide (secondary). Approver-differs-from-requester not confirmed.
3. Rejected: HumanLayer. Its repo (Apache-2.0) is now described as "best way to get AI coding agents to solve hard problems" and its last tagged release is pro-0.20.0 on 2025-12-23, so it no longer looks like an approval SDK (judgment from the description, UNVERIFIED).
4. Cannot guarantee: approver differs from requester; executor is the only holder of credentials; no double execution of an approved action.
5. Verdict: ADOPT n8n/Slack for the channel; KEEP-CODE for the executor guarantee. Test idea: requester token approving its own request must be refused; executing the same approval twice must apply once; the runtime process without credentials cannot perform the action.
6. With only n8n + Close + Claude you can sell draft-and-approve offers (a human clicks send in n8n). Offers where the agent moves money (refunds) or edits customer records unattended truly need our module.

## Surprising findings
1. Unleash is AGPL-3.0 per the GitHub API, while a 2026 blog says Apache-2.0.
2. immudb is BUSL-1.1 (not open source) per its README.
3. HumanLayer, the obvious approval SDK, now describes itself as a coding-agent tool; no maintained approval-SDK found yet.

## Sources (all read 2026-11-07)
- https://github.com/codenotary/immudb ; https://api.github.com/repos/codenotary/immudb/releases/latest
- https://github.com/openbao/openbao ; https://api.github.com/repos/openbao/openbao/releases/latest
- https://github.com/Infisical/infisical ; https://api.github.com/repos/Infisical/infisical/releases/latest
- https://github.com/ariga/atlas ; https://api.github.com/repos/ariga/atlas/releases/latest
- https://api.github.com/repos/Unleash/unleash (+ /releases/latest)
- https://api.github.com/repos/open-feature/flagd (+ /releases/latest)
- https://api.github.com/repos/flyway/flyway (+ /releases/latest)
- https://api.github.com/repos/temporalio/temporal (+ /releases/latest)
- https://api.github.com/repos/sigstore/rekor (+ /releases/latest)
- https://api.github.com/repos/humanlayer/humanlayer (+ /releases/latest)
- https://api.github.com/repos/getsops/sops/releases/latest (v3.13.3, 2026-07-23; not used in verdicts)
- https://pypi.org/pypi/alembic/json
- https://raw.githubusercontent.com/n8n-io/n8n/master/LICENSE.md
- WebSearch results (secondary): import-linter.readthedocs.io release notes; docs.github.com managing rulesets; appmaster.io tamper-evident audit trails; hexdocs.pm Pkcs11ex.Audit; docs.aws.amazon.com CloudTrail custom validation; infisical.com/blog/hashicorp-vault-pricing; cloudburn.io/blog/aws-secrets-manager-pricing; docs.langchain.com/oss/python/human-in-the-loop; cerbos.dev/cerbos-vs-permit; blog.elest.io immudb AI agents; opensourceforu.com immudb 2026-05; costbench.pages.dev (price pages, low reliability).
- Local: handover/tickets/{P2a,P3a,P4d,P0a,P0t,P6a,P6b2}.md and studio-notes/plan-v3.md (headings and table rows only).
- Blocked hosts (not read): n8n.io, docs.n8n.io, aws.amazon.com, www.doppler.com; api.github.com returned 403 for Vault, Infisical repo, Flagsmith, Flipt, goose, sqitch, Cedar, OPA, import-linter, Atlas repo licence calls.


## ADDENDUM 2 (coordinator follow-up, read 2026-11-07): wider market, licence re-checks

Additional queries run (WebSearch, 7): (13) Unleash licence AGPL vs Apache; (14) immudb BUSL change date and use grant (returned only generic BUSL pages, so I used the LICENSE file instead); (15) MCP server registry human-approval gateway audit log; (16) AI agent governance kill switch approvals audit platforms; (17) Cloudflare KV/Durable Objects, AWS AppConfig, Azure App Configuration kill switch pricing; (18) AWS QLDB end of support, Azure Confidential Ledger, GCP Bucket Lock; (19) AI automation agency starter kit n8n approval audit kill switch. Fetches: Unleash and immudb LICENSE files, PyPI JSON for mcp-control-plane and mcp-gatehouse. Still NOT covered: Cloudflare and Azure App Configuration kill-switch specifics (search returned AWS only), Port/Retool/Appsmith/Budibase, Hatchet/Inngest/Activepieces, GCP Secret Manager/Azure Key Vault prices. aws.amazon.com and others remain unreachable, so all prices stay UNVERIFIED.

Licence re-checks: Unleash server = AGPL-3.0 (confirmed, two sources). immudb = BUSL-1.1 (confirmed, two sources, terms above).

New candidates by area:
- Stop state / killswitch: AWS AppConfig feature flags (pay-as-you-go per retrieval, rate UNVERIFIED; docs say change behaviour without redeploy; rollback via CloudWatch alarms). Cover ~40, same gap as flagd: nothing proves the agent role cannot write the flag; client would own it in their AWS account. CrowdStrike AI Kill Switch: generally available 2026-11-03 per a secondary news source, admin-only trigger, enterprise product, price UNVERIFIED; rejected for small budgets and because it is proprietary. Search sources agree the kill switch should sit outside the agent and the agent must lack permission to modify it, which is exactly our P2a guarantee, so the verdict stays KEEP-CODE. Cloudflare Workers KV/Durable Objects: no evidence found; UNVERIFIED, not assessed.
- Audit: Azure Confidential Ledger (still offered; about USD 3 per day per ledger after March 2025, secondary, UNVERIFIED, roughly USD 90 per month, too high for small clients; a critical CVE listed in Aug 2026 by one source, unchecked). GCP Cloud Storage Bucket Lock = WORM only, no integrity proof, irreversible once locked (secondary). AWS QLDB rejected: discontinued 2025-07-31 (InfoQ and classmethod pages). All of these still need our verifier for truncation.
- Approvals / MCP gateways: mcp-gatehouse (MIT, v0.5.0 uploaded 2026-11-03, first release 2026-07-13; append-only JSONL audit, fails closed without terminal approval). Rejected as the executor: approval is a terminal prompt, JSONL is not tamper-evident, 4 months old. mcp-control-plane (Apache-2.0, only v0.1.0, 2026-06-18, stdio only per search): rejected, immature, one release. Cordon (MIT, TypeScript, Slack approvals, listed in the official MCP registry, 0 stars on 2026-04 per search): rejected, no maintenance history. None provides a separate approver identity or signed approvals (UNVERIFIED, descriptions only). Useful if the client agent talks MCP: WRAP candidate for the channel, not the executor guarantee.
- n8n: community and blog sources say n8n added a "Require Approval" option on tool nodes (gated tool cannot run without human approval) and recommend a separate append-only Postgres audit table, since execution history is not an audit log. This raises the n8n-only coverage for draft-and-approve offers. Approver identity not provably distinct from requester: UNVERIFIED.
- Starter kits: no GitHub starter kit bundling approval + audit + kill switch found (one search, 2026-11-07; GitHub topic search itself not run). Vendor posts only. Rejected: "Guardian" (vendor post, claims unverified).

Updated verdicts: no row changes. The table counts stand: ADOPT 2 (+ channel half), WRAP 5, KEEP-CODE 3, DROP 1. Additional note for the signer and audit rows: WRAP could fall to ADOPT for audit if a client accepts S3 Object Lock plus digest files and does not need row-level truncation detection (judgment).

Corrected surprises: (1) Unleash AGPL-3.0 since v8.0.0 (confirmed twice); (2) immudb BUSL-1.1 with a competing-use restriction (confirmed twice); (3) the market has no maintained approver-identity-separating executor: MCP gateways found are 1-4 months old.

Added sources (read 2026-11-07): https://raw.githubusercontent.com/Unleash/unleash/main/LICENSE ; https://raw.githubusercontent.com/codenotary/immudb/master/LICENSE ; https://www.getunleash.io/blog/unleash-moving-to-agplv3 (via search summary) ; https://pypi.org/pypi/mcp-control-plane/json ; https://pypi.org/pypi/mcp-gatehouse/json ; https://www.infoq.com/news/2024/07/aws-kill-qldb ; docs.aws.amazon.com AppConfig user guide (search summary) ; softprom.com CrowdStrike AI kill switch (secondary) ; community.n8n.io approval threads (anecdotal).

---

# GROUP C (full agent file)

# Market scan, Module group C: metering, billing contract, alert ledger, no-training statement, LLM gateways

Lead ORDER 119/120. Written 2026-11-07. Research only. No code changed. EGM skipped: read-only research; I review nothing.

## Method limits (read first, plain)
- Tools: WebSearch worked. WebFetch worked ONLY for github.com pages and returned little (no release dates). Every other host (developers.cloudflare.com, docs.litellm.ai) failed DNS: those hosts are not in the session's allowed network domains. The `gh api` calls were refused (repos not enabled for this session); I did not add repos.
- So almost every fact below is a WebSearch result snippet read on 2026-11-07. Primary vendor pages were NOT opened (except the github.com README text for LiteLLM, Langfuse, Portkey). Anything marked UNVERIFIED is not confirmed in a primary source. Last-release dates are mostly UNVERIFIED.
- Ticket context read: first sections of tickets P4a, P4b1, P4b2, P4c, P6b1 (plain-words and interface parts), not the full text.

## Queries run (26 searches, 2026-11-07)
1. LiteLLM proxy budgets max_budget per key team spend tracking license release 2026
2. Portkey AI gateway budget limits pricing open source license 2026
3. Helicone AI gateway cost tracking pricing acquired maintenance mode 2026
4. Cloudflare AI Gateway pricing cost tracking spend limits custom costs
5. Langfuse model usage cost tracking pricing tiers license MIT 2026
6. AWS Bedrock application inference profiles cost allocation budgets Azure API Management llm-token-limit policy
7. Azure API Management llm-token-limit policy token quota per key
8. Anthropic Console workspace spend limits Admin API usage cost report
9. OpenMeter vs Lago vs Orb usage-based billing open source license
10. TigerBeetle two-phase transfers pending post void reserve settle license
11. Stripe Billing meters usage-based billing LLM token billing
12. LiteLLM model_prices_and_context_window.json tokencost cache pricing tiers
13. Claude Agent SDK max_budget_usd per run cost limit
14. Pydantic AI UsageLimits request_limit total_tokens_limit cost limit
15. Anthropic commercial terms customer data not used to train, ZDR
16. Kong AI Gateway token rate limiting; Bifrost governance budgets; TensorZero license
17. Vercel AI Gateway / OpenRouter spend limits, budgets, markup
18. LiteLLM supply chain compromise 2026
19. n8n workflow template track OpenAI/Anthropic token cost, budget alert
20. LLM gateway budget reservation concurrent overshoot hard cap pre-authorization
21. OpenMeter pricing cloud / Lago cloud pricing
22. LiteLLM enterprise pricing / cost tracking edge cases
23. OpenAI API data controls not used to train, ZDR, Azure OpenAI, Bedrock
24. Vendor AI DPA checker tool, no-training clause automated review
(Two further fetches: github.com BerriAI/litellm, langfuse/langfuse, Portkey-AI/gateway. Searches 1-24 plus these are the whole set; count is 24 searches, not 26. I miscounted in the heading; 24 is correct.)

## Summary table

| Module | Need (one line) | Best candidates | Cover % (my estimate, evidence below) | Verdict |
|---|---|---|---|---|
| P4a usage + exact cost + refuse-instead-of-estimate | Exact integer micro-USD cost per call; no price or no usage = typed refusal, never a guess | LiteLLM price map (data) + LiteLLM cost calc; Langfuse model/price tiers; Cloudflare AI Gateway cost | 50-60% for "compute a cost"; ~0% for "refuse instead of estimate" (Cloudflare says its cost IS an estimate) | WRAP: take the price DATA (LiteLLM JSON, MIT); KEEP-CODE the refusal and exact rounding |
| P4b1 reserve/settle meter | Reserve worst case before the call, settle after, never exceed cap under concurrency | TigerBeetle two-phase transfers (ledger); LiteLLM/Cloudflare/Azure/Vercel budgets (post-hoc); Hardcap, Tollgate (small projects) | Gateways 30-40% (cap after the fact, overshoot documented); TigerBeetle covers the reserve/post/void primitive but is a separate cluster | KEEP-CODE (guarantee: cap not exceeded under concurrency) |
| P4b2 billing contract | Decide per failure type whether a failed call cost money (release, book, keep reserved) | None found | ~5%. No product I found classifies provider failures as billed/not billed | KEEP-CODE |
| P4c alert ledger + max_run_usd | One alert per period, exactly once; per-run dollar cap that stops a run | n8n (alert delivery), Claude Agent SDK `max_budget_usd`, Langfuse/Cloudflare/LiteLLM alerts, Pydantic AI harness SpendLimits | max_run_usd 70-80% if the run uses the Claude Agent SDK (overshoot up to one call); alerts 70% via n8n; exactly-once ledger 0% | WRAP (deliver alerts with n8n; keep the claim table only if ledger exactness is sold) |
| P6b1 llm kind + no-training statement check | Refuse to start a client backend without a dated operator statement of the provider's no-training terms | Provider contract terms + a signed DPA + a checklist; Bandit / Claude-for-Legal vendor-ai-review (document review) | The code checks a config field, not the truth. A checklist plus DPA covers ~90% of what the code asserts | DROP as code for v1 offers (ADOPT a checklist); revisit only if a client contract demands a startup refusal. This is my judgement, flagged |
| Gateways / budgets (LiteLLM, Portkey, Helicone, cloud) | Spend visibility, budgets, per-tenant keys | LiteLLM (MIT + ee), Cloudflare AI Gateway (free), Vercel AI Gateway (0% markup), Bifrost (Apache-2.0) | Visibility/budget 70-90%; hard-cap exactness no | ADOPT for visibility and coarse caps; they do not replace the meter |

Verdict counts for this group: ADOPT 1 (gateways row), WRAP 2 (P4a, P4c), KEEP-CODE 2 (P4b1, P4b2), DROP 1 (P6b1, as code).

## Per-module detail

### P4a: usage, exact cost, refuse instead of estimate
1. Need: every model call yields integer micro-dollars from a validated price table; a reply without usage, or a model without a price, raises a typed error instead of booking an estimate (ticket P4a: `UsageMissing`, `UnpricedUsage`, upward rounding).
2. Candidates:
   - LiteLLM price map `model_prices_and_context_window.json` (BerriAI/litellm). Evidence (docs search snippet, 2026-11-07): per-token USD fields, cache read/creation rates, `_above_200k_tokens` tier keys, 1-hour cache write key; proxy refreshes the map from GitHub at startup. Covers "price data and tiers" about 80%; gives no refusal behaviour, and floats not integers (per-token USD values such as 1e-6; whether integer-exact conversion is safe is mine to test). Licence: repo MIT, `enterprise/` separate commercial licence (github.com README read 2026-11-07: "Features under the LiteLLM Commercial License"; the exact SPDX text was NOT shown; MIT for the core is from search sources). Last release: UNVERIFIED (search snippets mention PyPI dates Apr 26 and Aug 2026 and a wiki saying v1.82.0 on 2026-03-01; none from a primary page). Maintained: active (62.9k stars, github.com 2026-11-07). Price: free self-host; Enterprise "Talk to sales" (third-party guesses $250/month to $30k/year, UNVERIFIED). Lock-in: low for the JSON, higher for the proxy.
   - Langfuse model definitions with pricing tiers (cost computed at ingestion if usage present and a model definition has prices). About 50% of the cost need; it computes and shows cost, it does not refuse. Licence MIT except `ee` folders (github.com README read 2026-11-07). Owner: ClickHouse acquired Langfuse in Jan 2026 (search snippets, single-source type). Release date UNVERIFIED. Price: self-host free; cloud $8 or $29 per month (sources conflict, UNVERIFIED).
   - Cloudflare AI Gateway cost metric. Docs snippet: cost "is an estimate", only where the response carries token data and model name, custom costs override public prices. Free to start (UNVERIFIED beyond snippet). Proprietary SaaS.
3. Cannot guarantee: money exactness (floats, "estimate" wording), refusal when usage is missing (they show nothing or zero), eval gates.
4. Verdict: WRAP. Adopt the LiteLLM JSON as price DATA source (MIT) behind our validator; KEEP-CODE the refusal and the upward-rounded integer. Test idea: reply with no usage -> assert typed error and zero booked; price file missing a model -> `UnpricedUsage`; property test that cost(micro) >= true decimal cost for random token counts.
5. Rejected: tokencost (npm `tokencost-dev` is an MCP wrapper over the LiteLLM map, cache tiers not confirmed in snippet; the Python `tokencost` library I could not confirm at all), 2026-11-07. Helicone as a price source: acquired by Mintlify 2026-03-03, maintenance mode (several secondary sources), so a bad new dependency.
6. Offers: with only n8n + Close + Claude, a small client can see approximate cost per workflow run (n8n community templates track tokens/cost in Google Sheets; none ships a budget alert, per search 2026-11-07). Exact, refuse-on-missing cost needs our module. Price a small client pays: $0 to roughly $30/month (Langfuse cloud tier, UNVERIFIED). Client can own the licence: yes (MIT parts).

### P4b1: reserve/settle meter
1. Need: before a call, hold the worst case against a cap; after, settle the actual; concurrent runs must never exceed the cap; a crash must not leave money held forever.
2. Candidates:
   - LiteLLM budgets (key, team, tag; `max_budget`, `budget_duration`). Evidence: docs snippet. Spend recorded after the response in Postgres tables. Covers visible caps about 40%. I did not find a reservation step; UNVERIFIED either way.
   - Cloudflare AI Gateway spend limits (open beta 2026-06-05 changelog; 429 when reached; up to 20 rules; "current request's cost is recorded after completion, so a burst of concurrent requests can briefly exceed the limit"). Honest overshoot admission. About 35%.
   - Azure API Management `llm-token-limit`: counts tokens, not dollars; "near-concurrent requests can temporarily exceed". Quota returns 403. About 30%.
   - Vercel AI Gateway budgets: soft caps, "the request that crosses the limit still completes" (secondary sources). About 30%.
   - TigerBeetle two-phase transfers: pending, then post/void/expire, "pending amount is reserved so the second step never breaks balance invariants" (docs snippet). This IS the reserve/settle primitive with timeouts, Apache-2.0, release 0.17.9 on 2026-07-06 per its homepage snippet. Coverage of the primitive about 90%; of the module (LLM worst-case calculation, wrapper, failure mapping) about 30%. Cost: run a separate replicated cluster; heavy for a $500/month client.
   - Hardcap (PyPI) and Tollgate (GitHub JumpMasters/tollgate): reserve, commit or release; Hardcap self-benchmark: post-hoc counting showed ~234% worst-case overshoot at 128 concurrent streams, reserving max_tokens never overshot but locked ~4% of budget (vendor self-report). Both tiny projects; licence, release dates, maintainers UNVERIFIED. Hadrian: self-labelled experimental alpha. Do not depend on these; useful only as proof the pattern is known.
3. Cannot guarantee (gateways): hard cap under concurrency, crash recovery of held money, money exactness. TigerBeetle guarantees exactness and atomic reserve but knows nothing about LLM calls.
4. Verdict: KEEP-CODE. Guarantee: total booked never exceeds cap + at most one stated overshoot, with an abandoned reservation expiring. Test idea: 50 concurrent fake calls against cap B with a worst case of B/10; assert booked <= B; kill the process between reserve and settle; assert the sweep releases it. Note for the lead: if the store were ever swapped for TigerBeetle the code shrinks, but I do not recommend it for small clients.
5. Rejected: Azure token-limit as the meter (tokens not dollars, per-gateway counters); Kong AI rate limiting (token-based, Enterprise tier per a competitor-sourced article, UNVERIFIED).
6. Offers: n8n + Claude can enforce a crude daily cap by checking a sheet before each call (race-prone). A first client with one slow workflow does not need our meter; a multi-tenant or unattended agent with a promised dollar cap does. Price: $0 gateway free tiers; TigerBeetle is self-host only. Client ownership: yes for Apache/MIT parts.

### P4b2: billing contract (which failures cost money)
1. Need: classify each failed attempt as refused / never-sent / unknown and decide release, keep reserved, or book (ticket P4b2: `REFUSED_STATUSES`, `AttemptCounts`).
2. Candidates: none found. I searched gateways, Stripe/Lago/OpenMeter and found no product publishing a provider-by-provider rule for "was this failed call billed". Gateways record cost only when a response carries usage (Cloudflare snippet), so failed or timed-out calls are simply not counted: the opposite error (undercounting). Coverage about 5%.
3. Cannot guarantee: no double-booking across retries, no phantom worst case after a key expires.
4. Verdict: KEEP-CODE. Test idea: a fake provider script (401, 429, connect error, read timeout after send, 500, success) -> assert the booked amount per case equals the table; retry storm with a dead key books zero.
5. Rejected: Stripe Billing meters / Lago / OpenMeter: they bill the CLIENT for usage; they do not decide what the PROVIDER charged us.
6. Offers: not visible to a small client; it protects our margin on resold usage. Only needed if we resell metered usage.

### P4c: alert ledger and max_run_usd
1. Need: (a) one durable alert per period when the wall is hit, exactly once, with retry; (b) a per-run dollar cap that stops the run.
2. Candidates:
   - Claude Agent SDK `max_budget_usd` (Python SDK; changelog 0.1.6 per a mirror; result subtype `error_max_budget_usd`; "cost may exceed the budget by up to one API call"). Sources: git mirror and community docs, not official docs (UNVERIFIED against Anthropic docs). Covers the per-run cap about 75% IF our agent loop is the Claude Agent SDK; our loop is our own (ticket) so it would not apply directly.
   - Pydantic AI `UsageLimits`: request and token limits per run, no dollar limit in core; a harness package `SpendLimits` is claimed (conflicting source). Licence/dates UNVERIFIED.
   - Anthropic Console workspace spend limits with threshold alerts (support-page snippets), plus Spend Limits API said to be Enterprise-only (one third-party guide, UNVERIFIED). Covers org-level wall at the provider about 60%.
   - n8n: deliver the alert to Slack/email and retry. n8n is Sustainable Use Licence (not verified this scan; flag as non-OSI). Covers delivery about 80%.
   - Cloudflare / LiteLLM / Langfuse: budget alerts exist in some form; details UNVERIFIED.
3. Cannot guarantee: alert exactly once per period under concurrent writers; alert survives a crash; the run stops before, not after, the overshooting call.
4. Verdict: WRAP. Send alerts through n8n/Slack; keep only the small claim-once table if we promise "one alert per period". Test idea: 20 concurrent threads hit the wall; assert exactly one claim row and one delivered message; kill delivery mid-send; assert a retry sends it once.
5. Rejected: Helicone alerts (maintenance mode, 2026-03-03).
6. Offers: n8n + Claude sells "email me when spend passes X" fine. A promised "run stops at $Y" plus audit needs the cap logic.

### P6b1: llm kind with no-training statement check
1. Need: a client environment refuses to start an llm backend that lacks a dated, well-formed operator statement of the provider's no-training terms. The ticket itself says the code records a promise and does not stop training, and does not check it is true.
2. Candidates:
   - The provider's own terms: Anthropic Commercial Terms say Anthropic may not train on Customer Content from paid services (search snippet of anthropic.com legal page, 2026-11-07, clause text not shown); OpenAI docs: API data not used to train unless opted in (developers.openai.com snippet). ZDR is by approval only. Retention figures conflict across sources (7 vs 30 days), UNVERIFIED.
   - Document-review aids: Bandit (open-source Python CLI, DPA checklist, AI-training module "coming soon" per its page), Anthropic's `vendor-ai-review` skill in claude-for-legal and an Apache-2.0 derivative. I did not open the repos; licences, maintenance UNVERIFIED. These review a document; they do not gate startup.
   - Azure OpenAI and Bedrock terms: not found in this scan (UNVERIFIED).
3. Cannot guarantee: truth of the promise, account tier behind a key, model behind a host (ticket says so itself).
4. Verdict: DROP as code for v1 offers. What the client actually buys is a signed DPA and a dated checklist; a startup lint adds a nag, not a guarantee. If a client contract requires "system refuses to run without attestation", it is a ~1-day config check, worth keeping then. Marked as judgement, since I only read the ticket's plain-words section.
5. Rejected: DataGrail GPT prompt, CustomGPT DPA pages (marketing / prompts, not gates).
6. Offers: n8n + Close + Claude with a signed Anthropic commercial agreement is sellable now. Our module is needed only if a client demands a technical attestation gate. Price: $0. Client can own the licence: the provider contract is theirs anyway.

### Gateways and budgets (the group's market map)
| Product | Licence | Price (small client) | Status / date | Notes |
|---|---|---|---|---|
| LiteLLM | MIT core + commercial `enterprise/` (github.com read 2026-11-07) | $0 self-host; Enterprise sales-only | Active, 62.9k stars. Supply-chain incident 2026-03-24: PyPI 1.82.7 and 1.82.8 malicious (credential stealer), removed; Docker image pinned (NetSPI, Arthur, Comet snippets) | Pin versions and hashes. ZDI advisory CAN-29838 (reported 2026-03-30) status UNVERIFIED |
| Portkey gateway | MIT (github.com page) vs "Apache-2.0 since Mar 2026" (one secondary source): conflict, UNVERIFIED | OSS $0; hosted $2k-10k+/month is a third-party guess | Acquired by Palo Alto Networks, sold as Prisma AIRS AI Gateway (one search summary, single source) | Hosted budgets in USD (docs snippet); whether budgets are in the OSS build: not addressed in README |
| Helicone | Open source, licence UNVERIFIED | Free self-host | Acquired by Mintlify 2026-03-03; maintenance mode | Reject for new use |
| Cloudflare AI Gateway | Proprietary SaaS | Free to start; Logpush paid (third-party figure, UNVERIFIED) | Spend limits open beta since 2026-06-05 | Estimates; trusts caller metadata |
| Vercel AI Gateway | Proprietary | 0% markup per Vercel FAQ snippet | Budgets per team, project, key, user | Soft caps |
| OpenRouter | Proprietary | 5-5.5% fee (sources conflict) | Active | Per-key credit limits |
| Bifrost (Maxim) | Apache-2.0; SSO, RBAC, team enforcement are paid | $0 core | Active (vendor-written sources) | Hierarchical budgets |
| Kong AI Gateway | Open core | Token features need paid tier (competitor source) | Kong bought OpenMeter Sept 2025 | UNVERIFIED |
| AWS Bedrock application inference profiles | Cloud service | Pay-as-you-go | Cost allocation tags to Cost Explorer; 24-48h delay | Reporting, not enforcement; budgets/alerts UNVERIFIED |
| Azure APIM `llm-token-limit` | Cloud service | APIM tier cost | Tokens, 429 rate / 403 quota; supports Anthropic Messages on v2 tiers | Not dollars |
| Billing/metering: OpenMeter (Apache-2.0; Kong bought it; cloud is sales-led), Lago (AGPLv3 core; cloud quote), Orb (proprietary), Stripe LLM token billing (private preview per Stripe docs snippet; Stripe bought Metronome) | as stated | not public | | They bill the client; not a spend wall for us |

Surfacing the options-first rule: a small client could own LiteLLM (MIT), Bifrost (Apache) or Cloudflare/Vercel accounts themselves, so a gateway for visibility is a configuration task, not a product we should write.

## Honest weak spots in this scan
- No primary-page reads except three github.com README pages; no release dates confirmed.
- Cover percentages are my estimates from feature lists, not measured by running the tools.
- I did not run any candidate. Nothing here shows a gateway fails the concurrency test; the vendors' own admissions (Cloudflare, Azure) are the evidence.
- n8n licence (Sustainable Use) and n8n/Close/Meta CAPI coverage are outside this group and not verified here.
- P6b1 DROP is the weakest verdict: it rests on the ticket's own statement that the check proves nothing technical.

## Sources (all read 2026-11-07 unless noted; "snippet" = search result text, page not opened)
- https://docs.litellm.ai/docs/proxy/users (snippet)
- https://docs.litellm.ai/docs/proxy/virtual_keys.md (snippet)
- https://docs.litellm.ai/docs/proxy/model_cost_map (snippet)
- https://github.com/BerriAI/litellm (opened; license link only, 62.9k stars)
- https://github.com/langfuse/langfuse (opened; MIT except ee folders)
- https://github.com/Portkey-AI/gateway (opened; MIT license shown)
- https://langfuse.com/docs/observability/features/token-and-cost-tracking.md (snippet)
- https://langfuse.com/changelog/2025-12-02-model-pricing-tiers.md (snippet)
- https://portkey.ai/docs/product/ai-gateway/virtual-keys/budget-limits (snippet)
- https://www.truefoundry.com/blog/portkey-pricing-guide (competitor blog, snippet)
- https://chatforest.com/reviews/helicone-llm-observability-gateway/ (snippet)
- https://developers.cloudflare.com/ai-gateway/features/spend-limits (snippet; fetch blocked)
- https://developers.cloudflare.com/changelog/post/2026-06-05-spend-limits/ (snippet)
- https://developers.cloudflare.com/ai-gateway/observability/costs (snippet)
- https://learn.microsoft.com/azure/api-management/llm-token-limit-policy (snippet)
- https://docs.aws.amazon.com/bedrock/latest/userguide/cost-mgmt-application-inference-profiles.html (snippet)
- https://docs.claude.com/en/api/usage-cost-api (snippet)
- https://support.anthropic.com/en/articles/9796807-creating-and-managing-workspaces (snippet)
- https://www.anthropic.com/legal/commercial-terms (snippet)
- https://developers.openai.com/api/docs/guides/your-data (snippet)
- https://docs.tigerbeetle.com/coding/two-phase-transfers/ and https://tigerbeetle.com (snippet)
- https://docs.stripe.com/billing/token-billing (snippet)
- https://openalternative.co/compare/lago/vs/openmeter ; https://www.withorb.com/blog/lago-review (vendor, snippet)
- https://usagepricing.com/blueprint/activity/openmeter-2025-09-03-kong-acquisition (snippet)
- https://getlago.com/pricing.md (snippet)
- https://git.joshthomas.dev/mirrors/claude-code-sdk-python/src/branch/main/examples/max_budget_usd.py (mirror, snippet)
- https://pydantic.dev/docs/ai/api/pydantic-ai/usage/ ; https://pydantic.dev/docs/ai/harness/spend/index.md (snippet)
- https://pypi.org/project/hardcap/ ; https://github.com/JumpMasters/tollgate ; https://hadrian-docs.pages.dev/docs/features/budgets (snippet)
- https://www.getmaxim.ai/articles/best-llm-gateways-for-cost-control-budgets-alerts-2026.md (vendor, snippet)
- https://vercel.com/docs/ai-gateway/faq.md ; https://www.activepieces.com/blog/understanding-openrouter-pricing-2026-and-fees.md (snippet)
- https://www.netspi.com/blog/executive-blog/ai-ml-pentesting/litellm-supply-chain-compromise/ ; https://www.comet.com/site/blog/litellm-supply-chain-attack/ ; https://www.arthur.ai/column/litellm-supply-chain-attack-pypi-compromise-2026 (snippet)
- https://n8n.io/workflows/3513 and related templates (snippet)
- https://conorrusso.github.io/bandit/ ; https://mcpservers.org/agent-skills/anthropic/vendor-ai-review (snippet)
- https://www.activepieces.com/blog/is-litellm-enterprise-pricing-worth-the-monthly-bill (snippet)
- Local: handover/tickets/{P4a,P4b1,P4b2,P4c,P6b1}.md

---

# GROUP D (full agent file)

# Market scan, Part D (Assembly Kit): AK-G1, AK-G2, AK-G15, AK-G16, JG-3

Written 2026-11-07 by a research agent (EGM-GATE v1: research only; no code, no review, no approval). Findings only.

## Read this first: limits of this scan (honest)
- Vendor sites (n8n.io, docs.n8n.io, chatwoot.com, hookdeck.com, inngest.com, temporal.io, zapier.com) did NOT resolve from this session (network allow-list). So every PRICE below comes from third-party aggregator pages returned by WebSearch, which often disagree. Every price is marked UNVERIFIED-VENDOR. Do not quote them to a client without opening the vendor page.
- GitHub and PyPI pages did load via WebFetch. Licences and some release dates come from those (read 2026-11-07). GitHub pages show day and month but often no year; I mark "(year assumed 2026)" where the page was current. Several repo pages did not show a release or last-commit date: I write "not shown".
- `gh api` was refused (no GitHub access for this session), so no API-based date checks.
- "Cover %" is MY judgement of function overlap against the ticket's need, not a measured number. The evidence column says what it is based on.
- Ticket facts come from the ticket text only (AK-G1 r3, AK-G2 r3, AK-G15 r3, AK-G16 r3, JG-3 r1 paused). I did not read code.

## Queries run (23 WebSearch, 11 WebFetch of GitHub/PyPI that worked, 8 WebFetch that failed on DNS)
1. Chatwoot pricing 2026 self-hosted license agent bot human handoff
2. Botpress pricing 2026 plans per month AI messages
3. LangGraph human-in-the-loop interrupt checkpointer PostgresSaver latest release 2026
4. HumanLayer approvals SDK agents human-in-the-loop 2026
5. Hookdeck pricing 2026 webhook deduplication idempotency receive
6. n8n human in the loop send and wait approval Slack wait node pricing cloud 2026
7. n8n pricing 2026 Starter Pro Business euro executions self-hosted Sustainable Use License
8. Temporal Cloud pricing 2026 minimum monthly Essentials plan actions
9. Inngest pricing 2026 hobby free pro waitForEvent human approval
10. Zapier human in the loop approval plan availability 2026 / Zapier Agents pricing
11. Svix Ingest / Convoy license Elastic webhook gateway idempotency 2026
12. Amazon Bedrock AgentCore Memory pricing session conversation retention 2026
13. OpenTofu vs Terraform BUSL 2026, Helm/Kustomize, deploy to customer's own cloud
14. incident.io Slack integration threaded reply alert Datadog PagerDuty pricing 2026
15. Intercom Fin pricing 2026 per resolution / Zendesk AI agents
16. Dify license multi-tenant restriction; Flowise Langflow licence
17. Postgres transactional outbox/inbox exactly-once webhook, pgmq, River, Graphile Worker
18. Camunda 8 self-managed production licence 2026; Windmill approval AGPL
19. n8n Slack node reply in thread thread_ts
20. Datadog Slack integration threaded replies
21. Cloud Run vs Azure Container Apps vs App Runner pricing 2026; Helm licence
(Plus fetches: GitHub pages for langgraph, temporal, n8n, inngest, hatchet, humanlayer, chatwoot, convoy, svix, windmill, river, kube-linter, opentofu; PyPI langgraph.)
NOT searched (gap): Make, Pipedream, Activepieces pricing; Port/Retool/Appsmith/Budibase approvals; Cloudflare Agents/Workflows; AWS Step Functions callback tokens; Azure Logic Apps approvals; Camunda price; Rasa/Voiceflow/Crisp; MCP registries for chat/approval servers; "AI automation agency" starter kits. These are UNVERIFIED and a second pass should cover them.

## Summary table

| Module | Need | Candidates | Cover % (my judgement) | Verdict |
|---|---|---|---|---|
| AK-G1 | Chat agent with read tools, conversation store with retention and delete-by-user, hand-off, multi-turn tests | Chatwoot (MIT) as host/handoff; LangGraph (MIT) + Postgres checkpointer; Botpress Cloud (closed SaaS); community Chatwoot/Intercom MCP servers (read-heavy only); n8n handoff templates | 60-70 on function; ~20 on the guarantees | WRAP (ours only for masking-before-model, delete-by-user incl. run-map copies, final hand-off, subject-scoped tools) |
| AK-G2 | One signed inbound door + ledger: no lost, no double-applied message | n8n webhook + dedupe; Hookdeck (SaaS); River/Postgres inbox pattern; Convoy (ELv2); Svix (MIT, mainly outbound); Cloudflare Queues / SQS FIFO (short dedupe window) | 70 function; 30-40 on the exactly-once-with-effect guarantee | KEEP-CODE (small ledger table), with ADOPT of n8n/Hookdeck as the forwarding front door |
| AK-G15 | Durable queue of needs-a-person items / approvals, separate executor identity, content binding | n8n Send-and-Wait; Zapier Human in the Loop; LangGraph interrupt; Temporal signals; Windmill approvals (AGPL); Camunda user tasks (paid prod licence); AWS Step Functions callback; Port manual approval; Make/Activepieces/Pipedream | 75-85 on function; 30 on binding + executor identity + erase-keep-item | WRAP (thin table + binding + executor split; notifications/UI go to the client's Slack/n8n/Chatwoot) |
| AK-G16 | Deploy assembled agent into the client's own cloud, least-privilege parts | Helm, Kustomize, OpenTofu (MPL-2.0), kube-linter, Cloud Run/Container Apps | 85 for rendering, apply and lint; ~0 for per-part least-privilege secrets | ADOPT for deploy mechanics (do not write per-cloud adapters); the five-part split is app code and stays ours |
| JG-3 | Incident summary as threaded Slack reply with portal link (PAUSED) | Datadog native threaded notifications; n8n Slack node with thread_ts; incident.io | 80-90 for the posting itself | DROP as a module (stays paused); ADOPT n8n/Datadog if a client asks |

Verdict counts (unchanged after the second pass, see "Second pass" below): ADOPT 1, WRAP 2, KEEP-CODE 1, DROP 1.

---

## AK-G1: conversational agent with tools, store, retention, hand-off

1. Need: let a person chat with an agent that can call read-only tools, keep the history masked, delete it on retention or on "forget me", and hand a person off to staff, all without raw personal data reaching the model (ticket decisions D3, D4, D5, D6, D10).

2-3. Candidates:
- **Chatwoot** (open-source helpdesk). Licence MIT per GitHub footer (read 2026-11-07); core stars 39.0k. Release date not shown on page. Maintained: UNVERIFIED (page showed 7,092 commits, no dates). Agent-bot webhook plus human handoff is described by third parties (eesel/featurebase blogs, read 2026-11-07); Captain AI is paid-tier only per same blogs, and whether bot-to-human handoff works on free self-hosted is NOT confirmed by any source. Price (UNVERIFIED-VENDOR): Community self-hosted $0; cloud free tier 2 agents; paid $19-$99 per agent per month. Lock-in: low (MIT, self-host). Cover ~50% (chat window, inbox, handoff UI), 0% masking.
- **LangGraph** (agent runtime). Licence MIT (PyPI licence expression, read 2026-11-07). Latest: langgraph 1.2.20 on 05 Nov (GitHub releases, year assumed 2026); maintained, yes. Postgres checkpointer persists conversation state and `interrupt()` requires a persistent checkpointer (third-party blogs, low quality, read 2026-11-07). Price: $0 library; our hosting. Lock-in: medium (graph API). Cover ~60% of loop + store + hand-off pause. It stores raw state in the checkpointer by default: masking before storage is ours to add.
- **Botpress Cloud** (hosted chatbot builder). Closed SaaS; licence not open (UNVERIFIED for the older open repo). Pricing changed 14 May 2026 for new workspaces (third-party: costbench/techpresso/lindy, read 2026-11-07); legacy Plus $89, Team $495 per month; new Plus about $150 per month billed annually; sources conflict. Lock-in: high. Cover ~65% of function, data sits in the vendor's cloud.
- Also noted: **Intercom Fin** about $0.99 per resolution, 50 outcome minimum (third parties, well agreed); **Zendesk AI agents** about $1.50-$2.00 per automated resolution (UNVERIFIED, conflicting). Closed SaaS, data in vendor cloud.
- **Amazon Bedrock AgentCore Memory**: short-term memory moved to per-GB billing in October 2026 (CodeZine says 12 Oct, developersdigest says 6 Oct; unresolved). Retention and delete-by-user terms not found.

4. Cannot guarantee (from sources and ticket, not from running them): masking BEFORE the model (none of the above masks identifiers before the model call by design; Presidio-class tools do detection only, and were not searched in this group); delete-by-user that also removes derived copies (ticket D5: run-level map copies in `redaction_maps`); hand-off that is final and cannot be turned off by client config (D6 `HANDOFF_STOPS`); tool results scoped to the chatting person (D10; a tool that ignores the subject still leaks, which no platform fixes). Tenant isolation: self-hosted per client only; Botpress/Fin are vendor multi-tenant.

5. Verdict: **WRAP.** Use the client's own chat host (Chatwoot, WhatsApp via n8n, web widget) and our `handle_turn` behind the signed door. Keep code only for: mask-before-model, masked store with delete-by-user including run copies, final hand-off. Ticket already agrees the chat window and transport are not in the package. Test idea: seed a conversation with a known email, run a turn with a recording model stub, assert the stub never saw the raw email; then `forget_user` and assert zero rows contain it in `conversations`, turns, and `redaction_maps`.
Options-first: a client can own the licence directly for Chatwoot (MIT, self-host) and LangGraph (MIT). Botpress/Fin/Zendesk: client buys their own subscription.

6. Small-budget offers: with only n8n + Close + Claude, a FAQ/lead-qualification chatbot that answers from a fixed knowledge base and drops a lead into Close is sellable now, if no personal data goes to the model or the client accepts that in writing. Truly needs our module: any chat that reads customer-specific data (order status, account), handles health/finance personal data, or must prove deletion.
Monthly price a small client pays for the adopted part (UNVERIFIED-VENDOR): $0 (Chatwoot self-host, plus server) to about $150 (Botpress Plus) plus model usage.

## AK-G2: inbound trigger kind + ledger (no lost, no double-applied message)

1. Need: accept a signed inbound message from a forwarder (mail, scheduler, no-code), store a receipt keyed by a stable id, hand ONE StepInput to the step, and never lose or apply twice (ticket D "ONE door").

2-3. Candidates:
- **n8n** webhook trigger (+ our signing step). Licence: Sustainable Use License plus Enterprise licence (GitHub README, read 2026-11-07), NOT open source; flag "fair-code, source available". Latest stable n8n@2.46.6 on 04 Nov 2026 (GitHub releases; changelog dated 2026-11-04). Cloud price (UNVERIFIED-VENDOR, euros, annual billing): Starter 20 per month / 2,500 executions; Pro 50 / 10,000; Business about 667 / 40,000; monthly billing higher. Self-host free for internal use; reselling it as a hosted product is restricted under the licence (terms not re-read; UNVERIFIED). Cover ~50% (receive, forward, retry in the editor). Dedupe is not built in as a guarantee.
- **Hookdeck** (SaaS webhook gateway). Closed SaaS. Deduplication feature added around August 2025 (plushcap summary, read 2026-11-07). Entry price conflicts: free tier (10k events) / $15 / $39 per month (aggregators). Cover ~60% of receive + retry + dedupe + replay. Lock-in medium: its dedupe is at the gateway, not in our transaction.
- **River (Go) / Postgres inbox pattern**. River licence MPL-2.0; features "unique jobs by args, period, queue, state" and transactional enqueue (GitHub README, read 2026-11-07; release date not shown). Inbox pattern records the message id in the same transaction as the effect (oneuptime article 2026-07-22, read 2026-11-07). Cover ~70% but it is a Go library, we are Python (ticket references `hmac_v0.py`): not directly usable.
- **Convoy**: Elastic License 2.0 (GitHub, read 2026-11-07): flag, not OSI open source and restricts offering it as a managed service. Receives and fans out webhooks; no dedupe described on its page. **Svix**: MIT (GitHub), mainly for SENDING webhooks; its receiving product was called "less mature" by a competitor (low-trust source).
- **Inngest**: server under SSPL with delayed Apache-2.0 (DOSP); SDKs Apache-2.0 (GitHub README, read 2026-11-07). Flag SSPL. Free Hobby 50k executions; Pro $50-$99 per month (sources conflict). Event idempotency exists but I did not read its docs.

4. Cannot guarantee: "no lost AND no double-applied" is an end-to-end property: the dedupe record and the business effect must commit together. A gateway (Hookdeck, Svix) can dedupe delivery but cannot make our effect transactional with its record; at-least-once plus idempotent receiver is the standard consensus (dev.to/oneuptime, read 2026-11-07). Signature verification with a separate key per tenant and tenant isolation: gateway-side only, not ours to prove.

5. Verdict: **KEEP-CODE** for the ledger (a table, a unique key, one transaction): guarantee = a delivery with the same key results in exactly one StepInput run, even across crash and replay. Test idea: send the same signed delivery 100 times concurrently and kill the process between receipt and effect at random points; assert effect count is 1 and no receipt is left unprocessed after restart. ADOPT n8n or the client's mail tool as the forwarder (ticket already does this).
Options-first: Hookdeck/n8n are client subscriptions; their licence is the client's own (n8n SUL does not forbid a client self-hosting for own use).

6. Small-budget: with n8n + Close + Claude, "email in, lead out" and form-to-CRM flows are sellable now (n8n webhook, retries). Truly need our ledger: money or irreversible actions fed by inbound messages, anything where a duplicate or lost message costs real money or a double reply.
Monthly price (UNVERIFIED-VENDOR): n8n Starter about 20 EUR; Hookdeck $0-$39.

## AK-G15: durable queue of needs-a-person items / approvals

1. Need: a queue where hand-offs and waiting messages become items; a person claims with a lease, closes with one outcome; action bound to the item's digest; executor is a separate identity; item survives content erasure (ticket words: binding, queue worker identity, re-run function, erased).

2-3. Candidates:
- **n8n Slack "Send and Wait for Response" (approval type)**: approvers click in Slack, workflow resumes, output records who responded (n8n docs via search result, read 2026-11-07; the docs host itself was not reachable). Licence/price as in AK-G2. Cover ~60% (approve/decline, notify, pause), no queue state, no lease, no binding.
- **Zapier Human in the Loop**: help centre says Free/Professional/Team; Zapier blog says Pro and up; July 2026 review says agent approvals are Enterprise/beta (all conflicting, read 2026-11-07). Closed SaaS. Lock-in high. Cover ~50%.
- **LangGraph interrupt/Command** (MIT, v1.2.20 05 Nov): pause graph at a point, resume with human input; needs a persistent checkpointer; node re-runs from the start on resume so earlier side effects must be idempotent (blogs). Cover ~50% (pause/resume, no queue UI).
- **Temporal** (MIT per my training memory, UNVERIFIED this session; v1.32.2 on 02 Nov 2026 per GitHub releases): signals give a durable wait. Cloud pricing in flux: some sources say $100/month Essentials with 1M actions; others say a September 2026 change to no-minimum pay-as-you-go at about $50 per million actions (conflicting). Cover ~60% on durability, 0% on person-facing queue.
- **Windmill**: AGPLv3; commercial licence required to resell, wrap, or re-expose to users (GitHub README, read 2026-11-07). `waitForApproval` returns approved + approver. Cover ~70% but AGPL/commercial-licence trap for an agency product.
- **Camunda 8**: since 8.6 self-managed production use requires a licence (Camunda announcement via search, read 2026-11-07); source under Camunda License 1.0 (not open source). Has user tasks. Price not found.
- Rejected: **HumanLayer approvals SDK**: classic SDK reported deprecated, repo now a coding-agent runner (Apache-2.0; GitHub README read 2026-11-07 shows no mention of approvals SDK; deprecation claim comes from a competitor, Pushary). **Hatchet** MIT, fine as a queue but no approval UX (README only). Not evaluated: Port, Retool, Appsmith, Budibase, Tines, Chatwoot as an item inbox.

4. Cannot guarantee (none of the above offers these, per what I read): the approval is bound to the exact thing the approver saw (digest check); the executor runs under a different database identity than the agent runtime; one final state that never changes (compare-and-set on a version); content erased but the item remains with ids only; a tenant ceiling that refuses loudly. Slack/n8n buttons authenticate a Slack user, not our principal list.

5. Verdict: **WRAP.** Ours: a thin table with version compare-and-set, content binding, separate worker role. Adopt for the front end: the client's Slack/Chatwoot/n8n to notify and to display (ticket row V1 already outlines the mirror). Test idea: two workers claim and close concurrently; assert one wins and the loser changes nothing; tamper the digest in a close call and assert refusal; run `forget_user` and assert the item still exists with `subject_erased` and no text. Scope warning: if the money/irreversible action never exists in an offer, plain n8n Send-and-Wait is enough.
Options-first: n8n/Zapier are the client's own subscriptions; Windmill needs a commercial licence for us to embed it (do not adopt).

6. Small-budget: n8n + Claude can sell "draft reply, human approves in Slack, then send" today. Truly needs our module: approvals that move money or change records and must be provable later, or where the approver's identity and the executor must differ.
Monthly price (UNVERIFIED-VENDOR): n8n 20-50 EUR; Zapier about $20-$30; Windmill/Camunda: unknown or paid.

## AK-G16: deployment into the client's own cloud

1. Need: render files, lint, and run the assembled agent as five least-privilege parts in the client's Kubernetes/serverless, with options-first quote (ticket D0, D1). Per-cloud adapters are v1.1.

2-3. Candidates:
- **Helm** (licence Apache-2.0, CNCF graduated: from my memory, search did not confirm; UNVERIFIED) and **Kustomize** (Apache-2.0, UNVERIFIED). Cover ~70% of "render files the client's team applies". Price $0.
- **OpenTofu**: MPL-2.0 (search: oneuptime/encore articles, read 2026-11-07); latest v1.13.9 on 05 Nov (GitHub releases, year assumed 2026); maintained, yes. Terraform itself: BSL 1.1 since August 2023, flag; fine for a client managing own infra, riskier for a vendor shipping products around it (articles; exact additional-use grant not read). Cover ~80% for cloud resources on any of AWS/Azure/GCP.
- **kube-linter**: Apache-2.0, "now powered by Red Hat", activity visible (889 commits), release date not shown (GitHub, read 2026-11-07). Cover ~60% of lint of rendered manifests (ticket `deploy check` reads files).
- Serverless container targets, prices UNVERIFIED-VENDOR (blog comparison, read 2026-11-07): Cloud Run and Container Apps scale to zero, free allowance about 180k vCPU-seconds, 360k GB-seconds, 2M requests per month; small always-on container about $52-$58 per month on Cloud Run, about $57 on App Runner. Plus a managed Postgres, which the same article did not price.

4. Cannot guarantee: the per-part least privilege (the purge pod cannot read the signing key; the app pod cannot sign): that comes from our build, not from Helm. Also "what is running in the cluster" is out of any file linter (ticket R2-ADV-5). Tamper-evident audit anchor: ours (ticket chain/anchor code).

5. Verdict: **ADOPT** for mechanics: ship Helm/Kustomize files + OpenTofu example, run kube-linter in `deploy check`, no home-made cloud adapter. Our code remains only the part split in the app (secrets per part). Test idea: render the purge part, list its mounted secrets, assert signer and anchor secrets are absent; start it with the signer secret injected and assert it refuses.
Options-first: client owns all licences (Apache/MPL tooling, own cloud bill).

6. Small-budget: with n8n + Close + Claude no deploy module is needed at all (n8n Cloud hosts it). Truly needs this: a regulated client that insists on running in its own cloud.
Monthly price: tooling $0; cloud bill about $50-$60 for one small container plus database (UNVERIFIED-VENDOR).

## JG-3: chat-ops notifier (PAUSED by owner 2026-11-06, order 49)

1. Need: post an incident summary as a threaded reply under the monitoring alert in Slack, with a once-only record and a code-built portal link, all text through `clean()` redaction.

2-3. Candidates:
- **Datadog native Slack threading**: monitor alerts can be threaded via notification rules ("Thread Notifications"); alert cycle grouped under one thread; best-effort (Datadog docs via search, read 2026-11-07; threading text sits under the legacy webhook tab, unclear for the newer Datadog Slack app). Cover ~50% (alert threading, not our incident summary).
- **n8n Slack node with `thread_ts`** (reply in thread; the "Reply in thread" toggle can broadcast to the channel, use `thread_ts` in Additional Fields; community posts, read 2026-11-07). Cover ~80% of the posting. Licence/price as above.
- **incident.io**: Team $15-$19 per user per month, Pro $25, on-call add-on $10-$20 (aggregators, read 2026-11-07), free Basic. Closed SaaS. Threaded handling in Slack not confirmed by my sources (UNVERIFIED).
- Rejected: PagerDuty (Professional $25 per user per month, Business $49 per user, aggregators 2026-11-07): heavier than the need; Opsgenie/Grafana OnCall status not searched, so UNVERIFIED.

4. Cannot guarantee: once-only posting with a stored record and retry after crash (n8n retries can double-post unless built with a check); masking of any personal data in the summary before it hits Slack; links built only by our code.

5. Verdict: **DROP** (keep paused; no sellable offer today). If a client asks: ADOPT n8n + `thread_ts` (config + glue); WRAP only if a client needs once-only proof, using the AK-G2 ledger idea. "Our module is not needed" for any no-code-grade notification.

6. Small-budget: n8n + Slack + Claude can sell "alert summarised in the thread" now. Truly needs our module: nothing found in this scan.
Monthly price: n8n about 20 EUR (UNVERIFIED-VENDOR); Datadog native threading is included in a Datadog plan the client already has.

---

## Cross-module observations
- None of the five modules is fully replaced by an existing product. The job-post claim (n8n + Close + Meta CAPI) is plausible for notification, forwarding, simple approvals and FAQ chat, and I found nothing contradicting it for those. It does not cover: masking before the model, deletion that covers derived copies, exactly-once effects, content-bound approvals with a separate executor.
- Licence flags found: n8n Sustainable Use (not OSI), Convoy ELv2, Inngest server SSPL (delayed Apache), Windmill AGPLv3, Camunda 8.6+ production licence, Terraform BSL 1.1, Dify Apache-2.0 with a multi-tenant written-authorisation clause (read via mirrors; current file not confirmed).
- Biggest data risk in my scan: vendor price pages unreachable, so all prices need a re-check.

## SOURCES (all read 2026-11-07)
Vendor/GitHub pages loaded:
- https://github.com/chatwoot/chatwoot (MIT footer, 39.0k stars)
- https://github.com/langchain-ai/langgraph/releases (langgraph 1.2.20, 05 Nov)
- https://pypi.org/pypi/langgraph/json (MIT expression, version 1.2.20)
- https://github.com/temporalio/temporal/releases (v1.32.2, 02 Nov)
- https://github.com/n8n-io/n8n/releases (n8n@2.46.6, 04 Nov) and https://github.com/n8n-io/n8n (Sustainable Use + Enterprise licence)
- https://github.com/inngest/inngest (SSPL + DOSP Apache-2.0; SDKs Apache-2.0)
- https://github.com/hatchet-dev/hatchet (MIT)
- https://github.com/humanlayer/humanlayer (Apache-2.0, coding-agent runner)
- https://github.com/frain-dev/convoy (Elastic License 2.0)
- https://github.com/svix/svix-webhooks (MIT)
- https://github.com/windmill-labs/windmill (AGPLv3, commercial licence rules)
- https://github.com/riverqueue/river (MPL-2.0, unique jobs, transactional enqueue)
- https://github.com/stackrox/kube-linter (Apache-2.0)
- https://github.com/opentofu/opentofu/releases (v1.13.9, 05 Nov)
Search results (third-party, lower trust):
- Chatwoot: https://www.eesel.ai/blog/chatwoot-pricing ; https://www.featurebase.app/blog/chatwoot-pricing
- Botpress: https://costbench.com/changelog/botpress-plan-removed-2026-05/ ; https://www.featurebase.app/blog/botpress-pricing
- LangGraph HITL: https://rentierdigital.xyz/blog/human-in-the-loop-langgraph
- HumanLayer deprecation claim (competitor): https://pushary.com/vs/humanlayer
- Hookdeck: https://hookdeck.com/blog/the-plans-they-are-a-changin ; https://www.plushcap.com/content/hookdeck/blog/hookdeck-deduplication-microsoft-teams-free-metrics-outpost-s3-hookdeck-august-2025
- n8n approvals: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.slack/approvals (appeared in search; host not fetchable)
- n8n pricing: https://www.cloudzero.com/blog/n8n-pricing/ ; https://toolradar.com/blog/n8n-pricing-2026
- Temporal pricing: https://docs.temporal.io/cloud/pricing.md ; https://pricingsaas.com/companies/temporal/diffs/2026W39
- Inngest pricing: https://costbench.com/software/ai-workflow-orchestration/inngest/
- Zapier HITL: https://help.zapier.com/hc/en-us/articles/38733184458765/ ; https://www.zapier.com/blog/human-in-the-loop-guide
- Svix idempotency: https://docs.svix.com/idempotency.md
- AgentCore: https://aws.amazon.com/bedrock/agentcore/pricing/ ; https://codezine.jp/news/detail/30022
- OpenTofu/Terraform licence: https://encore.dev/articles/opentofu-vs-terraform-2026 ; https://oneuptime.com/blog/post/2026-03-20-mpl-vs-bsl-opentofu-terraform/markdown
- incident.io/PagerDuty: https://incident.io/blog/incident-management-pricing-comparison-2026
- Intercom/Zendesk: https://costbench.com/compare/intercom-fin-vs-zendesk-ai/ ; https://www.getmacha.com/blog/intercom-fin-vs-zendesk-ai-pricing
- Dify licence: https://docs.dify.ai/policies/open-source
- Inbox/outbox pattern: https://oneuptime.com/blog/post/2026-07-22-inbox-pattern-atomic-deduplication/markdown
- Camunda licence: https://docs.camunda.io/docs/self-managed/components/orchestration-cluster/core-settings/configuration/licensing/
- n8n Slack thread_ts: https://community.n8n.io/t/slack-send-a-message-node-reply-in-thread/188869
- Datadog Slack threading: https://docs.datadoghq.com/integrations/slack
- Container pricing: https://sanj.dev/post/cloud-run-vs-app-runner-vs-container-apps/
Ticket files read (first lines/decisions only): handover/tickets/{AK-G1,AK-G2,AK-G15,AK-G16,JG-3}.md
Not fetchable (DNS blocked): n8n.io, docs.n8n.io, chatwoot.com, hookdeck.com, inngest.com, temporal.io, zapier.com.


---

## Second pass (coordinator request, ORDER 120 bar), read 2026-11-07
Same limits as above: vendor pages mostly unreachable, all prices UNVERIFIED-VENDOR (aggregator pages that disagree).

### Queries run in the second pass (10)
1. Make.com pricing 2026 Core Pro Teams operations human approval
2. Pipedream pricing 2026 credits plan; Activepieces license/pricing/approval piece
3. Retool Appsmith Budibase Port licence pricing 2026 self-service approval
4. AWS Step Functions waitForTaskToken, SQS FIFO dedupe, Azure Logic Apps, GCP Workflows, Cloudflare Queues pricing
5. MCP server registry Zendesk Intercom Chatwoot helpdesk approval elicitation 2026
6. AI automation agency starter kit n8n open source support agent human handoff 2026
7. AWS Step Functions pricing per state transition, callback pattern
8. Activepieces licence MIT / enterprise / human input / cloud pricing
9. Azure Logic Apps approval email connector and pricing; GCP Workflows callbacks
10. Port self-service actions manual approval pricing

### Findings by candidate (what it adds to the five modules)
- **Make**: closed SaaS. Core about $9-$12, Pro about $16-$21, Teams about $29-$38 per month (sources conflict; billing unit renamed from operations to credits in 2026 per one source). No human-approval feature found in any source. Cover for AK-G15: unknown (not found), for AK-G2/JG-3 forwarding: same as n8n (~50%). Lock-in high.
- **Pipedream**: closed SaaS; Free 100-300 credits, Basic about $29, Advanced about $49 (conflicting). Several sources say Workday acquired it in late 2025 and flag uncertainty for external users (not confirmed by me). Credit = 30 s at 256 MB. Cover as forwarder ~50%; no approval feature read.
- **Activepieces**: Community Edition MIT per several third-party pages; enterprise features (SSO, audit logs, branding) under a commercial licence. Cloud pricing conflicts ($5 per active flow vs Plus $20 / Team $200 vs $25 / $150). No human-approval piece found by me (gap). Candidate to replace n8n where a client wants a truly MIT tool: good for AK-G2 forwarder and JG-3.
- **Port**: closed SaaS developer portal. Manual approval for self-service actions exists (Port blog via plushcap: "waiting for approval", notifications to approvers). Free plan limits conflict (15 seats; 3 actions in one aggregator). Paid $19-$40 per user (conflicting). Fit: AK-G15 approval UI for developer/ops actions (~60%), not customer-chat items; no separate executor identity or content binding evidence read.
- **Retool**: closed; cloud free then $12 per builder + $7 per internal user; self-hosting sales-led, one source $990 per month per deployment (aggregator, 2026). **Appsmith**: Apache-2.0 Community (one source); Business $15 per user per month. **Budibase**: open-source self-host, cloud free tier reportedly ended March 2026, Pro $19 / Premium $49 / Business $299 (sources conflict; Budibase licence GPLv3 from my memory: UNVERIFIED, flag). Fit: build the queue UI (AK-G15 front end) in about a day; they hold no queue guarantees (CAS, lease, binding). WRAP-side, not a replacement.
- **AWS Step Functions (Standard)**: $0.025 per 1,000 state transitions, 4,000 free per month (AWS Compute Blog + AWS pricing page snippets). A `.waitForTaskToken` callback reportedly counts as one transition and idle wait is not billed (single blog, unconfirmed). Fit: durable approval wait ~65% for a client already on AWS; the token holder can act, so executor separation and content binding are not provided. Lock-in high (AWS-only ASL). Standard-workflow max duration and SQS FIFO 5-minute dedupe window are from my memory: UNVERIFIED this session.
- **Azure Logic Apps**: no approvals connector; use Office 365 Outlook "send approval email" (Microsoft Q&A moderator, 2025); only one approver per action, multi-level by parallel branches. Per-action pricing not verified. Fit ~40% for AK-G15.
- **GCP Workflows callbacks**: search returned nothing; UNVERIFIED, gap remains.
- **Cloudflare Queues**: Queues on the Workers Free plan since 2026-02-04 per a tracker; free 10,000 operations per day, 24-hour message retention not configurable (third-party). Fit for AK-G2 buffering only; 24-hour retention means a message not processed in a day is gone, which is a lost-message risk for our guarantee. Rejected for the ledger: retention.
- **MCP servers/registries**: Intercom official remote MCP is read-oriented (search conversations/contacts/articles; reply/assign/close are REST-only) per toolradar; Zendesk official MCP unconfirmed (sources conflict); Chatwoot only community MCP servers, few stars, not vendor-official; Deskcrew is a community helpdesk MCP with human-approved drafts. Official MCP registry exists (registry.modelcontextprotocol.io; one blog claims 9,400+ servers by April 2026, unverified). None found with MCP-native approval elicitation in helpdesk servers. AK-G1 relevance: MCP servers can supply read tools, but they do not mask output before the model or scope results to the chatting person (D10).
- **Agency starter kits/templates**: n8n human-handoff templates exist (Telegram handoff on Gumroad, $0+; hamstudio GBP 49; growwstacks free JSON; djeknet/n8n-master-workflows GitHub collection, licence not verified). Seller claims (70-80 percent automation) unverified. They cover the "chatbot + human takeover" demo (~50% of AK-G1 function) with no retention, no deletion, no masking.

### Rejected candidates (with dated reason)
- Zapier Agents approval: July 2026 review says Enterprise-only/closed beta; plan eligibility conflicts (2026-11-07). Rejected for a small client.
- Windmill: AGPLv3 plus commercial licence needed to wrap or resell (GitHub README, 2026-11-07). Rejected for an agency product.
- Convoy: Elastic License 2.0 (2026-11-07). Rejected as embedded component.
- Inngest server: SSPL (delayed Apache) (2026-11-07). Rejected to embed; fine as a client's own subscription.
- Camunda 8 self-managed: production licence required since 8.6 (2026-11-07). Rejected on cost and licence.
- HumanLayer approvals SDK: reported deprecated (competitor source only), repo now a coding-agent runner (2026-11-07). Rejected.
- Cloudflare Queues for the inbound ledger: 24-hour retention (2026-11-07).
- Azure Logic Apps for AK-G15: no approvals connector (2025 Q&A, read 2026-11-07).
- Retool self-hosted: sales-led, about $990 per month per deployment (aggregator, 2026-11-07). Rejected for a small client.
- Pipedream: ownership change uncertainty (aggregator, 2026-11-07). Not recommended as a dependency.
- Terraform proper: BSL 1.1 (2026-11-07). Prefer OpenTofu.

### Does the second pass change any verdict or count?
No. Verdict counts stay: ADOPT 1, WRAP 2, KEEP-CODE 1, DROP 1. It strengthens two points: (a) cloud queues and workflow services give durable waits and short-window dedupe but none gives permanent no-lost/no-double-applied with the effect in one transaction, and none gives executor separation or content binding; (b) a client already on AWS can get ~65% of AK-G15 from Step Functions callbacks for cents per month, so our WRAP verdict should be offered as "ours only if the client needs binding and executor identity". Still not covered: GCP Workflows, Power Automate approvals, Kestra/Prefect, Rasa/Voiceflow/Crisp, direct docs of any vendor.

### Additional sources (read 2026-11-07, third-party, lower trust)
- https://www.jetadmin.io/blog/make-pricing/ ; https://www.costbench.com/software/ai-automation/make/
- https://automationatlas.io/answers/pipedream-pricing-explained-2026/ ; https://dailyaifixs.com/blog/pipedream-pricing-2026-credits-are-compute
- https://www.activepieces.com/blog/activepieces-community-edition-vs-enterprise-2026-pricing.md ; https://automationatlas.io/answers/activepieces-pricing-explained-2026/
- https://www.plushcap.com/content/port/blog/port-announcing-manual-approval-for-developer-self-service ; https://port.io/pricing
- https://www.zite.com/blog/appsmith-pricing ; https://www.jetadmin.io/blog/untitled-39/ (Budibase) ; https://dev.to/chasebot/retool-vs-n8n-vs-budibase-pricing-comparison-2026-3ce2
- https://aws.amazon.com/step-functions/pricing ; https://aws.amazon.com/blogs/compute/building-cost-effective-aws-step-functions-workflows/ ; https://cloudburn.io/blog/aws-step-functions-pricing
- https://learn.microsoft.com/en-us/answers/questions/2279697/why-is-there-no-approvals-connector-in-azure-logic ; https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-pricing
- https://developers.cloudflare.com/queues/platform/index.md ; https://agentdeals.dev/vendor/cloudflare-queues
- https://toolradar.com/blog/best-mcp-servers-customer-support ; https://eseospace.com/blog/best-mcp-servers-for-customer-support/ ; https://callsphere.ai/blog/vw2g-mcp-servers-saas-registry-walkthrough.md
- https://aiautomationtemplate.gumroad.com/l/telegram-ai-bot-with-human-in-the-loop-handoff ; https://www.growwstacks.com/workflows/build-your-first-ai-agent ; https://docsearch.algolia.com/mcp/docs/repo/djeknet/n8n-master-workflows

---

# GROUP E (full agent file)

# Market scan, Part E: Assembly Kit (AK0, AK1, AK2a, AK4a) and P8a/P8b/P8c

Date read for every source below: 2026-11-07 (search results and PyPI JSON fetched that day). Researcher: research/evidence agent (EGM-GATE v1: findings only, no review or approval; EGM skipped, read-only research).

**Honesty notes (read first)**
- Almost all prices, dates and licences below come from WebSearch result snippets, mostly third-party aggregators. Only the PyPI JSON reads (version + licence field) are first-hand registry data. Anything I could not tie to a vendor page is marked UNVERIFIED. PyPI upload dates were not visible in the fetched pages (truncated), so "last release" is given as version only unless a dated source exists.
- "Cover %" is my judgement of the module need against the candidate's documented features. It is not a measurement. No tool was installed or run.
- I read the tickets' problem statements and headings only (about 45 lines each, plus greps). I did not read each ticket in full.

## Summary table

| Module | Need (one line) | Best candidates | Cover % (judgement) | Verdict |
|---|---|---|---|---|
| AK0 research note | Written decisions on RAG parts, with dated evidence | This scan; vendor docs | n/a | DROP as a sellable module (internal doc; this scan supplies part of its evidence) |
| AK1a step contract (record, final state, runner) | Every item ends exactly once in a named state | Temporal (MIT, UNVERIFIED), Hatchet, Inngest (SSPL), n8n | 60-70 | WRAP |
| AK1b the ONE outbound gate | No text reaches a model unmasked; spend held; every send audited | Presidio (MIT) + LiteLLM guardrails, Bedrock Guardrails, Cloudflare AI Gateway DLP | 50-60 (masking+budget), ~20 (single choke point, audit of each send, no-training check) | KEEP-CODE |
| AK1c tenant namespace | One customer's text never reaches another | Postgres RLS (FORCE), Pinecone namespaces, Qdrant payload filter | 85-90 | WRAP (thin helper + isolation test; ours only for the guarantee) |
| AK2a reader + chunker | Turn PDFs/DOCX into clean, section-aware passages, safely | docling (MIT), unstructured (Apache-2.0), pypdf (BSD-3) | 80-90 for reading; ~40 for hostile-file limits | WRAP |
| AK4a-1 eval gate buckets | Pilot/prod needs a labelled golden set with pass thresholds | promptfoo (MIT), DeepEval (Apache-2.0), Ragas (Apache-2.0), Langfuse (MIT core) | 70-80 | WRAP (ADOPT the scorer; keep only the rule "refuse to qualify under 50 items / 5 per bucket") |
| AK4a-2 joined-pipeline harness | Check what breaks between parts (PII in logs, double end, cross-tenant, spend over cap) | none found that does this | under 20 | KEEP-CODE |
| P8a repin 4 demos | Move demo pins once, prove nothing drifted | git + uv + each demo's tests; Renovate/Dependabot | 80 for mechanics, ~0 for look-alike check | ADOPT (mechanics); not sellable |
| P8b READMEs + drift report | One README per kind, drift report, ledger check | Our own egm-drift-report skill; claude-code-action; doc-drift skills | 80 | ADOPT; not sellable |
| P8c proof pack | One script runs every v1 kind once, exit 0 | plain pytest/smoke script | 90 | ADOPT; not sellable |

Verdict counts over these 10 rows: ADOPT 3 (P8a, P8b, P8c), WRAP 4 (AK1a, AK1c, AK2a, AK4a-1), KEEP-CODE 2 (AK1b, AK4a-2), DROP 1 (AK0). Counting by the 7 requested modules instead: AK0 DROP, AK1 mixed (WRAP/KEEP/WRAP), AK2a WRAP, AK4a WRAP+KEEP, P8a/b/c ADOPT.

Queries run (more than 5 per group): reader/RAG group: docling release/licence; unstructured release/licence; LlamaParse pricing; Azure Document Intelligence pricing; PyMuPDF AGPL vs pypdf/pdfplumber/pdfminer; Mistral OCR pricing; Reducto/Marker/MinerU licence and pricing; plus PyPI JSON for docling, unstructured, pypdf. Gate/tenant group: Presidio; LiteLLM guardrails/budgets; Cloudflare AI Gateway DLP; Bedrock Guardrails pricing; Portkey/Helicone/Kong; Guardrails AI/NeMo/LLM Guard; Lakera; Postgres RLS + pgvector; Pinecone namespaces (Qdrant part did NOT run); Temporal/Inngest/Hatchet; PyPI JSON for presidio, litellm. Eval group: promptfoo; DeepEval; Ragas; Langfuse; eval CI gates; Braintrust/LangSmith/Phoenix; PyPI JSON for ragas, deepeval, langfuse. P8 group: Renovate/Dependabot for git pins; doc drift tools; n8n+CAPI+Close templates; agency starter kits; Close MCP; n8n human-in-the-loop. Offers: n8n pricing, Close pricing.

Candidates REJECTED (dated reasons, 2026-11-07):
- PyMuPDF: AGPL-3.0 (dual with paid Artifex licence), network use triggers obligations; a client could not own it freely. Source: file2markdown snippet (secondary).
- MinerU: licence reported to have moved from AGPL to a custom Apache-based licence in April 2026, but two sources disagree on date/version and it carries commercial thresholds; custom licence = flag. Not adopted until the LICENSE file is read.
- Marker (Datalab): default model weights reportedly restrict commercial use above a revenue/funding threshold (one source); UNVERIFIED, rejected for a resale kit.
- LLM Guard: one Oct-2026 article says it is archived/unmaintained; UNVERIFIED but enough to not build on it.
- Guardrails AI: one article says it was acquired; UNVERIFIED; not needed since Presidio covers masking.
- Lakera Guard (now Check Point AI Guardrails): quote-based paid pricing, no confirmed PII masking; wrong shape for a small client.
- Arize Phoenix: reported Elastic License 2.0 (source-available, not OSI) by one source, MIT by another; unresolved, so not chosen.
- Inngest: reported SSPL (converts to Apache after 3 years); flag SSPL, avoid for a kit that clients self-host.
- LlamaParse, Azure Document Intelligence, Mistral OCR, Reducto: hosted; they send client documents to a third party. AK0 criterion J2 (no new outside party seeing client text) rejects them as defaults; fine as an opt-in, client-owned contract.
- Pinecone as the tenant answer: namespaces isolate by query convention, not by a database-enforced rule (Pinecone docs per snippet). Fine as store, not as the guarantee.

## Per-module detail

### AK0: research note (decisions on RAG parts)
1. Need: a dated, evidence-backed choice per RAG part (reader, chunker, embedder, store, reranker, masking, tenant).
2. Candidates: this scan; vendor docs. There is no product that does this.
3. Cover: not applicable.
4. Cannot guarantee: n/a (it is a document).
5. Verdict: DROP as a sellable module; keep as an internal note. This part E plus the rest of the market scan can feed its evidence folder, so I would not run a second desk-research pass.
6. First-client offers: not an offer. Nothing to sell.
Price/ownership: free; the client owns nothing.

### AK1a: step contract (record, final state, runner)
1. Need: every item in a pipeline ends exactly once in a closed final state; a step may narrow readers, never widen.
2. Candidates:
   - Temporal: durable execution; MIT per most snippets (UNVERIFIED, no dated release read); cloud from about $100-200/month at low volume (secondary estimates); self-host free but heavy.
   - Hatchet: Postgres-backed; MIT or Apache-2.0 (sources conflict); cloud tiers listed $0/$180/$425 (secondary).
   - n8n (Sustainable Use Licence, not OSI; I did not read its terms): Starter about EUR 20-24/month for 2,500 executions, Pro about EUR 50-60 for 10,000 (secondary, Sep-Oct 2026).
3. Cover: durable engines give retry and resume (about 60-70% of the contract). They do not know our closed final states, readers narrowing, or "no step output carries payload text" (ticket rule).
4. Cannot guarantee by themselves: no double-applied effect unless every step is idempotent; masking before model; tenant isolation. I found no source that addressed idempotency specifically.
5. Verdict: WRAP. Keep our small record/state vocabulary; run on whatever engine the client has. Test idea: kill the worker between "effect applied" and "state written", restart, assert effect count is exactly 1.
6. Offers: n8n alone can sell simple lead flows. Needs our module: anything where a duplicate or lost item costs money.
Price: $0 self-host to roughly $100-200/month managed. Client can own the licence for MIT engines; n8n licence terms need reading.

### AK1b: the ONE outbound gate
1. Need: every path that sends text to a model passes one gate that masks first, holds spend, writes an audit event, and checks the provider's no-training statement.
2. Candidates:
   - Microsoft Presidio: MIT; PyPI presidio-analyzer 2.2.366 (PyPI JSON, 2026-11-07; 2.2.364 uploaded 2026-07-22); maintained. Detects and masks PII; no gateway, no spend, no audit. About 40% (masking only).
   - LiteLLM proxy: PyPI 1.108.2, MIT per licence_expression (an enterprise directory exists, UNVERIFIED). Presidio guardrail masking before the model and spend limits per key/user/model on the open tier (from a competitor blog, UNVERIFIED). Audit logs and team admin are reported as enterprise features (UNVERIFIED). About 50-60%.
   - Cloudflare AI Gateway: DLP scanning free on all plans, only two predefined profiles (financial, national IDs) without Zero Trust; Guardrails billed as Workers AI tokens; Workers Free 100,000 logs total (Cloudflare docs snippet). Dollar spend limits reported (webpronews). Hosted, so client text goes to Cloudflare.
   - Amazon Bedrock Guardrails: about $0.10 per 1,000 text units for PII detection, regex free (secondary); AWS only. Our own `bedrock_guardrail` kind already wraps it (ticket AK1).
3. Cover: see table. Lock-in: LiteLLM low; Cloudflare/AWS high.
4. Cannot guarantee: that no code path bypasses the gate (needs an AST/lint over call sites, which the ticket plans); money exactness (a spend limit is not a held reservation reconciled against billing); tamper-evident audit; masking recall (Presidio is detection, not proof).
5. Verdict: KEEP-CODE. Guarantee: "no outbound text reaches any model without passing the gate." Test idea: plant a canary e-mail in an input, run every pipeline with a recording fake model, assert the canary never appears in any model input, log line or audit event, and that a new call site added without the gate fails lint. Use Presidio/LiteLLM as detectors inside it, not instead of it.
6. Offers: n8n + Claude can sell a lead-reply bot if the client accepts that contact details go to the model provider under the client's own contract. Needs our module: regulated or sensitive data (health, finance, EU consent) where masking before the model must be demonstrable.
Price: Presidio and LiteLLM free self-hosted; Bedrock about $0.10/1,000 units; Cloudflare gateway free tier. Client can own all of these.

### AK1c: tenant namespace
1. Need: text of one tenant never reaches another.
2. Candidates:
   - Postgres row-level security with FORCE ROW LEVEL SECURITY and a transaction-local tenant setting; core Postgres licence (PostgreSQL licence, permissive; I did not read it). Guides: Render, Supabase, pgxn (secondary). About 85-90%.
   - Pinecone namespaces: Starter free; Builder $20/month; Standard $50 minimum; namespaces 100 on Starter (secondary, Oct 2026).
   - Qdrant payload multitenancy: NOT searched. UNVERIFIED.
3. Caveats from sources: table owners bypass RLS unless FORCE is set; pg_dump skips RLS unless the role has BYPASSRLS; vector index recall varies by tenant (pgxn).
4. Cannot guarantee: that the app always sets the tenant (a missing setting must fail closed); that logs, caches and the model prompt do not mix tenants.
5. Verdict: WRAP. Adopt RLS; ours is a thin key helper plus a cross-tenant test. Test idea: two tenants with similar documents, query as tenant A with the tenant setting unset and then wrong, assert zero rows and an error, not an empty success.
6. Offers: one client with one tenant needs nothing. Needs it: any agency-hosted agent serving several clients from one store.
Price: $0 on existing Postgres. Client can own it.

### AK2a: document reader and chunker
1. Need: read text PDFs (and later more), measure read quality, cut section-aware chunks, survive hostile files. Today the core decodes a PDF as UTF-8 text (ticket AK2a).
2. Candidates:
   - docling: MIT (PyPI JSON, version 2.148.0; the search listed up to 2.139.0 and a 2.137.0 page dated Oct 9, 2026); IBM Research origin; model licences are separate (PyPI text). Layout, tables, OCR options. About 85% of reading and structure.
   - unstructured: Apache-2.0 (PyPI JSON 0.27.37); search snippets disagreed on version (0.22.31 / 0.24.0), so use the PyPI value; heavy dependency set (UNVERIFIED).
   - pypdf: BSD-3-Clause (PyPI JSON 7.0.0); text-only, slower and less layout-aware (secondary). About 60% for text PDFs, small footprint, fits a one-library rule.
   - Hosted: LlamaParse (credits; $1.25 per 1,000 credits reported, 1 credit/page Fast tier, plus conflicting older tiers; free 10k credits/month reported), Azure Document Intelligence (Read about $1.50, Layout about $10 per 1,000 pages), Mistral OCR 4 (about $4 per 1,000 pages, $2 batch; July 2026 doubling reported), Reducto (pricing conflicting). All secondary.
3. Cover: docling/unstructured about 80-90% of reading and chunk structure; pypdf less.
4. Cannot guarantee: hostile-file safety (hang, memory, zip-bomb) beyond what a wrapper enforces; no stored text that skips masking; deterministic chunk ids. None of the libraries promises these.
5. Verdict: WRAP. Ours is the isolated child process with time/memory caps, the read-quality score and "poor file goes to needs-a-person." Docling or pypdf sits behind one adapter, with a lock-in test row per the existing `LIBRARY_IMPORTS` rule. KEEP-CODE only for the limits. Test idea: a 514:1 compressed content stream and a deeply nested PDF must end in a refusal inside the time cap with the parent process alive.
6. Offers: n8n + Claude can read simple text PDFs and answer from them for a first client (extract-from-PDF nodes plus Claude reading files). Needs our module: scanned/hostile uploads from the public, or a promise of "poor documents never get indexed silently."
Price: self-host free; hosted $1.5-10 per 1,000 pages. Client can own the MIT/Apache/BSD ones; AGPL ones rejected.

### AK4a: joined-pipeline harness and eval gate buckets
1. Need: (a) a harness that runs a whole pipeline on made-up items and checks what only goes wrong between parts; (b) qualification gate that rejects tiny or unlabelled golden sets, reports false-abstain separately, and refuses pilot/prod otherwise.
2. Candidates:
   - promptfoo: MIT (reported); OpenAI announced its acquisition 2026-03-09 and said it stays open source (secondary); GitHub Action with `fail-on-threshold` percentage; assertion-level thresholds; JUnit XML output (promptfoo docs snippet). Latest version UNVERIFIED (0.121.19 on 2026-07-14 per one aggregator).
   - DeepEval: Apache-2.0 (PyPI JSON 4.3.3); hosted Confident AI tiers reported $0 up to about $2K/month with prices changing May and August 2026 (CostBench, an observed-difference page).
   - Ragas: Apache-2.0 (PyPI JSON 0.4.3); RAG metrics (faithfulness etc., from my memory, UNVERIFIED in this scan).
   - Langfuse: MIT core (PyPI JSON 5.2.0 for the Python SDK; server licence from a snippet); cloud Hobby free 50k units, Core $29, Pro $199, Enterprise $2,499 per month (secondary).
3. Cover: (b) about 70-80%: thresholds and CI failure exist; labelled buckets, the "at least 50 items and 5 per bucket" rule and the false-abstain split are not features I found. (a) under 20%: none of these tools plants a canary and checks logs, audit, stdout and other tenants' output.
4. Cannot guarantee: eval gates themselves are only as good as the labelled set; LLM-as-judge scores are non-deterministic.
5. Verdict: eval buckets WRAP (small rule layer over promptfoo/DeepEval output). Harness KEEP-CODE. Guarantee: "a joined run cannot pass with PII in a log, an item ending twice, cross-tenant text, or spend over cap." Test idea: mutation set already in the ticket (61 mutants); keep that approach.
6. Offers: n8n + Claude can ship a first client with a hand-checked list of 20 sample questions. Needs our module: any pilot/prod claim of measured quality.
Price: promptfoo, DeepEval, Ragas free; Langfuse $0-29/month starter. Client can own all (check promptfoo licence file after the acquisition).

### P8a: repin four demos
1. Need: move four demo repos to one core commit, delete obsolete copies, prove no look-alike check got weaker.
2. Candidates: git + uv lock; Renovate or Dependabot (uv.lock supported per uv docs; whether they bump a `git+...@sha` line is UNVERIFIED).
3. Cover: mechanics about 80%. The look-alike regression proof is ours and only existing demo tests supply it.
4. Cannot guarantee: byte-copy drift. 
5. Verdict: ADOPT for mechanics (plain git and tests); it is a one-time chore, not a product.
6. Offers: none; internal.

### P8b: per-kind READMEs, drift report, ledger check
1. Need: one README per kind, a drift report, a ledger check.
2. Candidates: our egm-drift-report skill (already installed); anthropics claude-code-action running on diffs (write-up, secondary); an open "doc drift detector" skill with AST checks (borghei/claude-skills, 451 stars per a catalog); Falconer (commercial, UNVERIFIED).
3. Cover: about 80%. The ticket-specific text checks (forbidden phrases, 8 fixed headings) are small scripts.
4. Cannot guarantee: semantic truth of a README.
5. Verdict: ADOPT.
6. Offers: none; READMEs help a client handover but do not sell.

### P8c: proof pack
1. Need: one script that runs every v1 kind once, prints a count per kind, exit 0.
2. Candidates: pytest smoke test; the ticket's own counting rule (identity check on the kind object) is stricter than a plain run.
3. Cover: about 90% by plain pytest; the identity rule is a few lines.
4. Verdict: ADOPT (no new dependency; the ticket already says so).
5. Offers: none; internal.

## Which offers can Hadavin sell on n8n + Close + Claude alone (first client, small budget)?

Evidence: n8n Starter about EUR 20-24/month, Pro about EUR 50-60 (secondary, Sep-Oct 2026); Close Solo/Essentials/Growth/Scale roughly $9-139 per user per month depending on source and billing period, calls and SMS billed by usage; Close has an official hosted MCP server and n8n can connect, but Close's help centre reportedly says n8n supports only the read scope for now (UNVERIFIED, conflicting snippets); n8n has Meta CAPI templates (hash and send leads, dedup id) but I found no ready Close-to-CAPI n8n template; Datahash offers a hosted Close-to-Meta sync. Freelancer listings sell n8n RAG/lead bots at roughly $150-$1,200 (secondary).

Can be sold without our modules (low-risk data, human checks the output, no money moves):
1. Lead capture from forms/Meta lead ads into Close with dedupe and Slack/e-mail alert.
2. Meta CAPI lead-stage feedback from Close (hash e-mail/phone, event id for dedup).
3. Speed-to-lead: Claude drafts a first reply, a person sends it (n8n human-in-the-loop).
4. Lead qualification and scoring written to Close fields.
5. Call/meeting summaries and follow-up task drafts into Close.
6. FAQ bot over a few clean text documents with "ask a person" fallback.

Truly need our guarantee modules:
- Anything where a model sees regulated personal data and the client must prove masking happened first: AK1 gate, P5c redactor.
- Any action that moves money (refunds, credits, discounts): P4 money meter, P4b2 billing contract, approvals with a separate executor, P2a stop state. n8n gives a pausing approval step, but forum posts say it is not an audit log and can be bypassed when a flow is misconfigured (community.n8n.io, secondary), and the execution history is not tamper-evident.
- Several clients on one store: AK1c tenant namespace (or RLS config, which is cheap).
- Public file uploads: AK2a hostile-file limits.
- A contract promise of measured quality in pilot/production: AK4a eval gate.
- Retries that must not double-apply an effect: AK1a plus idempotency.

Scan of ticket headings (AK-G1, G2, G15, G16, JG-3, P0 to P8): nearly all concern money, redaction, stop state, audit, deployment or hostile input, i.e. guarantee-class. Very few headings map to a thing an owner of a small client would buy on day one. This supports the owner's doubt for the first offer: a first small client can be served on n8n + Close + Claude, and our modules matter from the first offer that touches money, regulated data, or several tenants. I did not find a competing product that bundles those guarantees (not proven absent; my searches covered gateways, guardrails, workflow engines and eval tools).

## Sources (all read 2026-11-07 unless noted)
Search-result pages only (no direct page fetch unless "PyPI JSON"):
- docling: https://pypi.org/pypi/docling/json (PyPI JSON, first-hand); https://pypi.org/project/docling/2.137.0/ (search hit)
- unstructured: https://pypi.org/pypi/unstructured/json (PyPI JSON); https://pepy.tech/project/unstructured; https://dev.co/ai/frameworks/unstructured
- pypdf: https://pypi.org/pypi/pypdf/json (PyPI JSON); https://www.file2markdown.ai/blog/is-pymupdf-free-for-commercial-use
- LlamaParse: https://developers.llamaindex.ai/llamaparse/general/pricing/ ; https://ecorpit.com/rag-document-parsing-llamaparse-unstructured-docling-2026/ ; https://www.usagepricing.com/blueprint/activity/llamaindex-2026-08-26-llamaparse-turbo-tier
- Azure Document Intelligence: https://superdupr.com/blog/azure-document-intelligence-pricing ; https://www.activepieces.com/blog/azure-document-intelligence-pricing-per-model-in-2026
- Mistral OCR: https://aiproductivity.ai/pricing/mistral-ocr/ ; https://www.usagepricing.com/blueprint/activity/mistral-ai-2026-07-06-api-rate-increase
- Reducto/Marker/MinerU: https://toolnavs.com/article/2457-is-mineru-worth-using-the-50k-star-pdf-to-markdown-tool-has-deployment-and-licen ; https://codesota.com/ocr/reducto-vs-open-source ; https://www.file2markdown.ai/blog/marker-vs-mineru
- Presidio: https://pypi.org/pypi/presidio-analyzer/json (PyPI JSON); https://github.yezi957.workers.dev/microsoft/presidio/blob/main/CHANGELOG.md (mirror)
- LiteLLM: https://pypi.org/pypi/litellm/json (PyPI JSON); https://www.truefoundry.com/blog/litellm-enterprise ; https://neuraltrust.ai/blog/how-to-secure-litellm (competitor blogs)
- Cloudflare AI Gateway: https://developers.cloudflare.com/ai-gateway/reference/pricing ; https://www.webpronews.com/cloudflare-arms-ai-gateway-with-dollar-based-spend-limits-to-tame-runaway-model-costs/
- Bedrock Guardrails: https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-how.html ; https://www.deepinspect.ai/blog/aws-bedrock-guardrails-pricing
- Portkey/Helicone/Kong: https://web-9ja.pages.dev/blog/llm-gateway-pricing-comparison-june-2026/ ; https://ecorpit.com/ai-gateway-litellm-portkey-kong-truefoundry-2026/
- Guardrails/NeMo/LLM Guard: https://docs.nvidia.com/nemo/guardrails/latest/introduction.html ; https://wz-it.com/en/knowledge/ki/ai-guardrails/
- Lakera: https://www.itpro.com/business/acquisition/check-point-buys-lakera-to-secure-the-full-enterprise-ai-lifecycle ; https://costbench.com/software/ai-security/lakera-guard/
- Tenant: https://render.com/articles/multi-tenant-rag-postgresql-pgvector ; https://pgxn.org/dist/pg_trickle/0.36.0/blog/multi-tenant-vector-search-rls.html ; https://www.pinecone.io/pricing.md ; https://www.activepieces.com/blog/pinecone-pricing-plans-and-costs-explained-2026.md
- Workflow engines: https://automationatlas.io/answers/inngest-vs-temporal-2026/ ; https://automationatlas.io/answers/hatchet-pricing-explained-2026/ ; https://www.youngju.dev/blog/culture/2026-05-25-durable-workflow-temporal-inngest-trigger-hatchet-restate-dbos-2026-deep-dive.en
- Eval: https://promptfoo.dev/docs/integrations/ci-cd/ ; https://github.com/typpo/promptfoo-action ; https://appsecsanta.com/promptfoo ; https://pypi.org/pypi/deepeval/json ; https://pypi.org/pypi/ragas/json ; https://pypi.org/pypi/langfuse/json ; https://costbench.com/software/ai-evaluation/deepeval/price-history/ ; https://www.activepieces.com/blog/langfuse-pricing-plans-and-what-you-pay-in-2026 ; https://dev.to/gabrielanhaia/langfuse-vs-langsmith-vs-phoenix-vs-braintrust-the-honest-2026-comparison-253p
- n8n/Close/CAPI: https://www.jetadmin.io/blog/n8n-pricing/ ; https://www.cloudzero.com/blog/n8n-pricing/ ; https://marketbetter.ai/blog/close-crm-pricing-2026/ ; https://developer.close.com/mcp.md ; https://help.close.com/docs/mcp-server ; https://n8n.io/workflows/21595-hash-and-sync-leads-to-meta-capi-with-devdeskapp-google-sheets-and-slack/ ; https://www.datahash.com/connections/close/meta-capi-crm/ ; https://community.n8n.io/t/n8n-users-running-ai-agents-where-do-you-still-keep-a-human-approval-step/303282
- P8: https://docs.astral.sh/uv/guides/integration/dependency-bots ; https://understandingdata.com/posts/doc-drift-detection-ci/ ; https://skillselion.com/skills/borghei/claude-skills/doc-drift-detector
- Local: handover/tickets/{AK0,AK1,AK2a,AK4a,P8a,P8b,P8c}.md (problem statements and greps), studio-notes/GAPS.md, plan-v3.md.

Not done: no GitHub release pages or vendor pricing pages were fetched; Qdrant, Restate, Temporal licence text, n8n Sustainable Use Licence text, LiteLLM enterprise folder licence and MinerU LICENSE were not read.

---
