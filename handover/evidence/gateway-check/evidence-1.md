# Evidence 1: LiteLLM budgets and Presidio masking (raw output, no judgement)
Date 2026-11-06. Runner: EVIDENCE RUNNER. Scratch: _local/scratch/gw-test (venv, scripts, logs kept there).
Versions: litellm 1.108.1, litellm-proxy-extras 0.4.110, presidio-analyzer/anonymizer 2.2.366, spacy 3.8.18, model en_core_web_lg (the Presidio default; installed fully). Python 3.13.3.

## TEST 1: LiteLLM virtual-key budget
Database: throwaway Postgres 16 in docker container gwtest-pg-7f3a (random localhost port, --rm, stopped afterwards). SQLite was NOT tried: LiteLLM's prisma schema is postgres-only (provider postgresql). pgserver / postgresql-wheel were not on PyPI for this Python. Needed manual 'prisma generate' (the proxy first exited with: Failed to import Prisma client).
Fake provider: fake.py (stdlib ThreadingHTTPServer, 200 ms delay, usage 10 prompt + 10 completion tokens). Price: 0.0005 per token each way = 0.01 USD per call.
### config.yaml
```
model_list:
  - model_name: fake
    litellm_params:
      model: openai/fake-model
      api_base: http://127.0.0.1:18080/v1
      api_key: not-a-real-key
      input_cost_per_token: 0.0005
      output_cost_per_token: 0.0005
general_settings:
  master_key: sk-gwtest-master
  database_url: postgresql://postgres:gwtest@127.0.0.1:63066/litellm
```
Key created via POST /key/generate {"max_budget":0.05}. Proxy started: litellm --config config.yaml --port 14000 (one worker, defaults otherwise).
### Run 1 (t1.py) raw output
```
(a) sequential: statuses [200, 200, 422, 200, 200, 200, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422]
(a) ok = 5 refused = 15
(a) recorded spend after 30s: 0.05 cap 0.05
(b) concurrent: statuses [200, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422, 422]
(b) ok = 1 refused = 19
(b) recorded spend after 30s: 0.01 cap 0.05
(b2) extra calls after settle: [200, 422, 200]
(d0) concurrent ok = 1 spend = 0.01
(d1) concurrent ok = 1 spend = 0.01
(d2) concurrent ok = 1 spend = 0.01
(e) budget_duration=10s key, calls: [200, 422, 200, 422, 422]
(e) spend 0.02
(e) after 60s wait total: 422 spend 0.02 info: {'soft_budget_cooldown': False, 'max_budget': 0.02, 'budget_duration': '10s', 'budget_reset_at': '2026-11-06T05:10:20+00:00', 'model_max_budget': {}, 'budget_fallbacks': {}, 'budget_id': None, 'budget_limits': None, 'litellm_budget_table': None}
```
### Run 2 (t1b.py): error bodies, rapid sequential then 20 concurrent with distinct prompts
```
0 200 {"id":"fake-14","created":1,"model":"fake","object":"chat.completion","choices":[{"finish_reason":"stop","index":0,"message":{"content":"ok","role":"assistant"},"provider_specific_fields":{}}],"usage":{"completion_tokens":10,"prom
1 200 {"id":"fake-15","created":1,"model":"fake","object":"chat.completion","choices":[{"finish_reason":"stop","index":0,"message":{"content":"ok","role":"assistant"},"provider_specific_fields":{}}],"usage":{"completion_tokens":10,"prom
2 422 {"error":{"message":"Budget has been exceeded! Key=key (sk-...Bmhw) Current cost: 0.05000000000000071, Max budget: 0.05","type":"budget_exceeded","param":null,"code":"422"}}
3 200 {"id":"fake-16","created":1,"model":"fake","object":"chat.completion","choices":[{"finish_reason":"stop","index":0,"message":{"content":"ok","role":"assistant"},"provider_specific_fields":{}}],"usage":{"completion_tokens":10,"prom
4 422 {"error":{"message":"Budget has been exceeded! Key=key (sk-...Bmhw) Current cost: 0.05000000000000071, Max budget: 0.05","type":"budget_exceeded","param":null,"code":"422"}}
5 200 {"id":"fake-17","created":1,"model":"fake","object":"chat.completion","choices":[{"finish_reason":"stop","index":0,"message":{"content":"ok","role":"assistant"},"provider_specific_fields":{}}],"usage":{"completion_tokens":10,"prom
6 200 {"id":"fake-18","created":1,"model":"fake","object":"chat.completion","choices":[{"finish_reason":"stop","index":0,"message":{"content":"ok","role":"assistant"},"provider_specific_fields":{}}],"usage":{"completion_tokens":10,"prom
7 422 {"error":{"message":"Budget has been exceeded! Key=key (sk-...Bmhw) Current cost: 0.05000000000000696, Max budget: 0.05","type":"budget_exceeded","param":null,"code":"422"}}
Counter({422: 19, 200: 1})
['{"error":{"message":"Budget has been exceeded! the key (hash masked) Current cost: 16.394000000000002, Max budget: 0.05","type":"budget_exceeded","param"', '{"error":{"message":"Budget has been exceeded! the key (hash masked) Current 
 0.01
```
### Run 3 (t1c.py): one call every 12 s, spend read from DB after each
```
0 200 cost-hdr= 0.01 
   db spend 0.01
1 200 cost-hdr= 0.01 
   db spend 0.02
2 200 cost-hdr= 0.01 
   db spend 0.03
3 200 cost-hdr= 0.01 
   db spend 0.04
4 200 cost-hdr= 0.01 
   db spend 0.05
5 422 cost-hdr= None {"error":{"message":"Budget has been exceeded! Key=key (sk-...vBlA) Current cost: 0.050000
   db spend 0.05
6 422 cost-hdr= None {"error":{"message":"Budget has been exceeded! Key=key (sk-...vBlA) Current cost: 0.050000
   db spend 0.05
```
### Numbers (facts)
- Rapid sequential, 20 calls, key cap 0.05, 0.01 per call: 5 succeeded, 15 refused (HTTP 422 budget_exceeded). Pattern was 200,200,422,200,200,200,422... (refused then allowed again). Recorded spend after 30 s: 0.05. No overshoot above 0.05 recorded.
- 20 concurrent threads: 1 succeeded, 19 refused. Recorded spend 0.01. Repeated 3 more times on fresh keys: 1 succeeded each, spend 0.01 each. (Under-use of the cap, not overshoot.) Refusal messages in the concurrent run reported "Current cost: 16.394" and "24.591" for a key whose database spend was 0.01; the cause was not investigated.
- Run 2 rapid sequential: 200,200,422,200,422,200,200,422; message said "Current cost: 0.05000000000000071" after only 2 recorded successes. So the in-memory counter and the allow/refuse decision were not consistent with 0.01 per call in rapid mode.
- Paced calls (12 s apart): exactly 5 succeeded, spend 0.01..0.05, calls 6 and 7 refused. Response header x-litellm-response-cost = 0.01 on each.
- budget_duration "10s" on a key with max_budget 0.02: calls 200,422,200,422,422 (spend 0.02); after about 60 s the key was still refused (422), spend 0.02, budget_reset_at shown as 2026-11-06T05:10:20+00:00 (the reset is done by a scheduled job; no reset seen within the 60 s we waited; not tested longer).
- Exceeding the cap by one in-flight batch (the classic overshoot) was NOT observed in this setup; the concurrent test instead refused almost everything. Whether overshoot happens with slower spend writes, several workers/pods, or streaming calls was NOT tested.
### Not tested / failed to run (Test 1)
- SQLite (not supported by the schema, not attempted). Multiple proxy workers or pods. Streaming. Real providers. Longer budget_duration reset (e.g. waiting beyond the scheduler interval). Cause of the 16.39 / 24.59 "Current cost" values. Team/user/global budgets. LiteLLM's Presidio guardrail through the proxy (Test 2 used Presidio directly, not through LiteLLM).
- Tidy-up: proxy and fake server processes stopped, docker container stopped (--rm removes it). Scratch folder kept for reproducibility.

## TEST 2: Presidio default analyzer on masking inputs
Source test file: the path named in the brief (tests/test_k1b_redaction_layers.py) does not exist in the working tree of projects/hadavin-sdk; it exists in git history (commit ce70eb5, branch core/ci-scan-job and others). I read it with git show (read-only) into _local/scratch/gw-test/src/layers.py. It tests the repo's own redact_bundle, not Presidio; I re-created its input spellings (full-width, zero-width, JSON escape, percent, HTML entity, base64) as inputs below. The corpus it relates to (tests/warden_port/privacy_corpus.py, same commit, read via git show) is run in full: 48 "must mask" lines and 14 "must keep" lines. 30 hostile inputs were written by me. All data made up; AWS key is the allowed example literal built from parts.
Presidio setup: AnalyzerEngine() with defaults, language en, no custom recognizers, no context words added, 20 supported entity types.
Result key: FOUND = analyzer returned at least one entity; MISSED = none. FOUND does not say the whole value was covered; only that something was flagged.
### Counts
- hostile (30): found 17, missed 13
- corpus must-mask lines (48): found 34, missed 14
- corpus must-keep lines (14): flagged by Presidio anyway 7 of 14 (false positives)
### Table (raw)
analyzer entities supported: 20
| input class | input | Presidio result |
|---|---|---|
| HOSTILE:plain email | `'bob.smith@example.com'` | FOUND EMAIL_ADDRESS,URL |
| HOSTILE:phone intl | `'call +1 415 555 0142'` | FOUND PHONE_NUMBER |
| HOSTILE:card 16 digit spaced | `'card 4111 1111 1111 1111'` | FOUND CREDIT_CARD |
| HOSTILE:card 16 digit bare | `'card 4111111111111111'` | FOUND CREDIT_CARD,US_BANK_NUMBER,US_DRIVER_LICENSE |
| HOSTILE:IBAN | `'iban GB82WEST12345698765432'` | FOUND IBAN_CODE |
| HOSTILE:bank acct with context | `'bank account number 55556666'` | FOUND US_BANK_NUMBER,US_DRIVER_LICENSE |
| HOSTILE:bank acct no context | `'ref 55556666 paid'` | FOUND DATE_TIME,US_BANK_NUMBER,US_DRIVER_LICENSE |
| HOSTILE:bank acct BSB ctx | `'BSB 062-000 account 12345678'` | FOUND US_BANK_NUMBER,US_DRIVER_LICENSE |
| HOSTILE:AWS key plain | `'key AKIAIOSFODNN7EXAMPLE'` | MISSED |
| HOSTILE:sk-ant style key | `'key sk-ant-api03-abcdefghijklmnop'` | MISSED |
| HOSTILE:password assignment | `'password=hunter2'` | MISSED |
| HOSTILE:email fullwidth | `'ｂｏｂ.ｓｍｉｔｈ＠ｅｘａｍｐｌｅ.ｃｏｍ'` | MISSED |
| HOSTILE:AWS key fullwidth | `'ＡＫＩＡIOSFODNN7EXAMPLE'` | MISSED |
| HOSTILE:card fullwidth digits | `'card ４１１１ １１１１ １１１１ １１１１'` | FOUND DATE_TIME |
| HOSTILE:email cyrillic o/a/e | `'bоb.smith@еxаmple.com'` | FOUND EMAIL_ADDRESS,URL |
| HOSTILE:AWS key cyrillic A,I | `'АKІAIOSFODNN7EXAMPLE'` | MISSED |
| HOSTILE:card digits zero-width | `'card 4111\u200b1111\u200b1111\u200b1111'` | MISSED |
| HOSTILE:email zero-width in local | `'bob\u200b.smith@example.com'` | FOUND EMAIL_ADDRESS,URL |
| HOSTILE:AWS key zero-width | `'AK\u200bIAIOSFODNN7EXAMPLE'` | MISSED |
| HOSTILE:phone zero-width | `'call +1 415\u200b555\u200b0142'` | FOUND PHONE_NUMBER |
| HOSTILE:email percent-encoded dot | `'mail bob%2Esmith@example.com'` | FOUND EMAIL_ADDRESS,URL |
| HOSTILE:email percent-encoded at | `'mail bob.smith%40example.com'` | FOUND URL |
| HOSTILE:AWS key percent | `'%41KIAIOSFODNN7EXAMPLE'` | MISSED |
| HOSTILE:email html entity at | `'mail bob.smith&#64;example.com'` | FOUND URL |
| HOSTILE:AWS key html entity | `'&#65;KIAIOSFODNN7EXAMPLE'` | MISSED |
| HOSTILE:email base64 | `'Ym9iLnNtaXRoQGV4YW1wbGUuY29t'` | FOUND PERSON |
| HOSTILE:AWS key base64 | `'QUtJQUlPU0ZPRE5ON0VYQU1QTEU='` | MISSED |
| HOSTILE:card base64 | `'NDExMSAxMTExIDExMTEgMTExMQ=='` | MISSED |
| HOSTILE:email json unicode escape | `'bob.smith@example.com'` | FOUND EMAIL_ADDRESS,URL |
| HOSTILE:AWS key json escape | `'AKIAIOSFODNN7EXAMPLE'` | MISSED |
| CORPUS-EMAIL | `'user priya@corp.example failed'` | MISSED |
| CORPUS-EMAIL | `'to=ops%40corp.example'` | MISSED |
| CORPUS-PHONE | `'call +1 415 555 0142'` | FOUND PHONE_NUMBER |
| CORPUS-PHONE | `'phone=4155550142'` | FOUND PHONE_NUMBER,US_BANK_NUMBER,US_DRIVER_LICENSE |
| CORPUS-NAME | `'full_name=Priya Nair'` | FOUND PERSON |
| CORPUS-NAME | `'"customer_name": "Raj Mehta"'` | FOUND PERSON |
| CORPUS-NAME | `'first name: Asha'` | FOUND PERSON |
| CORPUS-NAME | `'username=asha.rao'` | MISSED |
| CORPUS-NAME | `'assigned to Dr. Meera Iyer'` | FOUND PERSON |
| CORPUS-NAME | `'Mrs Kapoor called'` | FOUND PERSON |
| CORPUS-NAME | `'Dear Ravi Kumar,'` | FOUND PERSON |
| CORPUS-NAME | `'cardholder_name=J Doe'` | FOUND PERSON |
| CORPUS-IPV4 | `'src=10.4.12.9'` | FOUND DATE_TIME,IP_ADDRESS |
| CORPUS-IPV4 | `'node ip-10-0-3-22.ec2.internal'` | FOUND URL |
| CORPUS-IPV6 | `'from 2001:db8::8a2e:370:7334 refused'` | FOUND DATE_TIME,IP_ADDRESS |
| CORPUS-MAC | `'eth0 00:1a:2b:3c:4d:5e up'` | FOUND MAC_ADDRESS |
| CORPUS-MAC | `'port 001a.2b3c.4d5e'` | FOUND MAC_ADDRESS |
| CORPUS-ACCOUNTID | `'account 123456789012'` | FOUND DATE_TIME,US_BANK_NUMBER,US_DRIVER_LICENSE |
| CORPUS-TENANT | `'tenant_id=acme-42'` | FOUND DATE_TIME |
| CORPUS-TENANT | `'org_id: globex7'` | FOUND PERSON |
| CORPUS-TENANT | `'"user_id": "u-99812"'` | MISSED |
| CORPUS-HOSTNAME | `'db at billing-db.prod.corp:5432'` | FOUND URL |
| CORPUS-HOSTNAME | `'smb://files.lan/share'` | FOUND URL |
| CORPUS-HOSTNAME | `'ldap.intranet refused'` | FOUND URL |
| CORPUS-HOSTNAME | `'printer.local offline'` | MISSED |
| CORPUS-HOSTNAME | `'nas.home.arpa'` | FOUND PERSON,URL |
| CORPUS-HOSTNAME | `'db at billing-db.prod.corp.example:5432'` | FOUND LOCATION,URL |
| CORPUS-HOSTNAME | `'smb://files.lan.example/share'` | FOUND URL |
| CORPUS-APIKEY | `'key sk-ant-api03-abcdefghijklmnop'` | MISSED |
| CORPUS-APIKEY | `'AKIAIOSFODNN7EXAMPLE'` | MISSED |
| CORPUS-SECRET | `'password=hunter2x'` | MISSED |
| CORPUS-SECRET | `'client_secret: s3cr3tvalue'` | MISSED |
| CORPUS-CREDITCARD | `'card 4111 1111 1111 1111'` | FOUND CREDIT_CARD |
| CORPUS-CREDITCARD | `'card 4242 4242 4242 4242'` | FOUND CREDIT_CARD |
| CORPUS-CREDITCARD | `'card 5555-5555-5555-4444'` | FOUND CREDIT_CARD |
| CORPUS-SSN | `'ssn 123-45-6789 on file'` | MISSED |
| CORPUS-AADHAAR | `'aadhaar 2345 6789 0123'` | FOUND DATE_TIME |
| CORPUS-PAN | `'pan ABCPD1234E'` | FOUND PERSON |
| CORPUS-ADDRESS | `'ships to 221B Baker Street'` | FOUND LOCATION |
| CORPUS-ADDRESS | `'office at 12 MG Road'` | MISSED |
| CORPUS-ADDRESS | `'lives at 4 Shanti Nagar'` | FOUND LOCATION |
| CORPUS-BANKCODE | `'BSB 062-000'` | MISSED |
| CORPUS-BANKCODE | `'sort code 12-34-56'` | MISSED |
| CORPUS-BANKCODE | `'ABA 123456789'` | FOUND DATE_TIME,US_BANK_NUMBER,US_DRIVER_LICENSE,US_PASSPORT |
| CORPUS-BANKCODE | `'transit 12345 institution 999'` | MISSED |
| CORPUS-BANKACCT | `'BSB 062-000 account 12345678'` | FOUND US_BANK_NUMBER,US_DRIVER_LICENSE |
| CORPUS-BANKACCT | `'sort code 12-34-56 account 87654321'` | FOUND US_BANK_NUMBER,US_DRIVER_LICENSE |
| CORPUS-BANKACCT | `'bank account number 55556666'` | FOUND US_BANK_NUMBER,US_DRIVER_LICENSE |
| CORPUS-KEPT(must stay) | `'2026-10-21T10:02:11Z checkout ERROR 500 upstream timeout'` | FOUND DATE_TIME |
| CORPUS-KEPT(must stay) | `'name=orders-api replicas=3'` | MISSED |
| CORPUS-KEPT(must stay) | `'orders.shop.svc.cluster.local:8080 refused'` | FOUND URL |
| CORPUS-KEPT(must stay) | `'node ip-<IPV4_1>.ap-south-1.compute.internal'` | FOUND URL |
| CORPUS-KEPT(must stay) | `'image registry/shop/checkout:1.4.2-rc1'` | MISSED |
| CORPUS-KEPT(must stay) | `'task 4471 exited with code 137 (OOMKilled)'` | MISSED |
| CORPUS-KEPT(must stay) | `'HTTP 503 from payments in 1200 ms'` | MISSED |
| CORPUS-KEPT(must stay) | `'rule warden-dev-lab-tick-silent'` | MISSED |
| CORPUS-KEPT(must stay) | `'Main St'` | MISSED |
| CORPUS-KEPT(must stay) | `'at jdk.internal.reflect.Method.invoke(Method.java:566)'` | FOUND URL |
| CORPUS-KEPT(must stay) | `'kotlin.internal.PlatformImplementationsKt.getIMPLEMENTATIONS'` | FOUND URL |
| CORPUS-KEPT(must stay) | `'File threading.py, in threading.local()'` | FOUND URL |
| CORPUS-KEPT(must stay) | `'routing table rtb-0abc updated 503 times'` | MISSED |
| CORPUS-KEPT(must stay) | `'Invoice #123456789 total $1,250.00 due 2026-11-30'` | FOUND DATE_TIME,US_BANK_NUMBER,US_DRIVER_LICENSE,US_PASSPORT |
hostile total 30 found 17 missed 13
corpus-masked total 48 found 34 missed 14
kept-evidence lines flagged by Presidio (false positives): 7 of 14

### Not tested / failed to run (Test 2)
- Presidio's anonymizer step was not run (only detection). Custom recognizers or context lists were not added (default analyzer only, as asked). Presidio through the LiteLLM guardrail was not run. Score thresholds were not tuned (all returned results counted). Unicode normalisation was not applied before Presidio (the task asked for the default analyzer). The repo's own redactor was not run against the same inputs for a side-by-side.
- First run of t2.py crashed on console encoding (cp1252); rerun with PYTHONUTF8=1 produced the table above.
