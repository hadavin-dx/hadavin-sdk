# F-provider-mark review 2 (hostile, read-only; head 76b22711f)

Verdict: no Blocker, no Major. 3 Minor. Tests: tests/test_refused_before_response.py + tests/test_mark_to_gate.py = 258 passed.

## Checked and sound
- Base_url / platform per kind: bedrock = boto3 client with `ignore_configured_endpoint_urls=True`, no base_url setting
  (bedrock.py:43-54); gemini = module constant `BASE_URL` https://generativelanguage.googleapis.com (gemini.py:20,52), no
  setting, no vertex/OpenAI-compat route; anthropic `api` = constant API_BASE_URL. Neither bedrock nor gemini can be pointed
  at a router/gateway by config, so default True is correct today. Only an operator env proxy (HTTPS_PROXY) can sit in front,
  same for every kind (see Minor 2).
- Gate (core-c model_gate.py:350-368): settles 0 only if `getattr(exc,"refused_before_response",False) is True` AND
  isinstance ProviderError. Truthy non-True, raising property, non-ProviderError: not honoured. A wrapper that re-raises a
  new class/instance loses the attribute -> unmarked -> worst case stays booked (fail-safe). with_retry itself wraps every
  non-ProviderError in a fresh error and marks it from its own state, never copying a mark from the cause. Gate lines
  693-695: ProviderError, marked -> settle 0; else note only (rule c). Matches.
- Never-sent proof (retry.py:never_sent): requires ConnectionRefusedError or gaierror in the chain and NO TimeoutError and NO
  status anywhere; truncated chain -> False. Per case: connect timeout, read timeout, 5xx with body, reset mid-response
  (ConnectionResetError/ConnectionClosedError), HTTP/2 GOAWAY (httpx RemoteProtocolError), SSLEOF mid-read, TLS cert errors:
  none contain Refused/gaierror -> never "never sent" -> unmarked (TLS cert failure is certainly pre-request but stays
  unmarked: conservative, fine). Refused/gaierror are raised by connect()/getaddrinfo before any byte. Exhausted path
  (retry.py unbilled accumulator) is monotone: any 5xx/408/timeout/parse-failed attempt pins it False; 429 counts only with
  throttled_unbilled=True. Mixed [429,429,401] / [429,500,429] unmarked (tested).
- Class attr default plumbing: common.py:391-414 passes self.throttled_unbilled; openai_compat False (79); anthropic class
  False, instance True only when `platform == "api"` exactly (anthropic.py:106,119-120, allowlist); vertex/foundry/typos stay False.

## Minor
1. common.py:414 `throttled_unbilled: bool = True` and retry.py `with_retry(..., throttled_unbilled=True)` default is
   fail-open: a future kind (or a kind added behind a router) silently inherits "429 = unbilled" and the gate settles it at 0
   (money under-counted). Fix: default False on NetworkLLM and on with_retry; set True explicitly on gemini, bedrock and the
   direct-API anthropic (one line each) -- also makes the table in the docstring self-documenting.
2. retry.py docstring / anthropic.py:106 comment: True kinds (gemini, bedrock, anthropic api) are reached through the
   operator's HTTP(S)_PROXY env (urllib ENV_PROXY_OPENER, httpx trust_env, botocore). A corporate gateway answering 429 AFTER
   upstream work through that proxy would be marked unbilled. Via CONNECT tunnels the proxy's 429 is not surfaced as an HTTP
   status (urllib OSError "Tunnel connection failed", httpx ProxyError), so it is unmarked today; only a plain-HTTP
   forward-proxy is exposed and the https-only base URLs preclude that. Fix: state this assumption in the docstring (no code).
3. tests/test_refused_before_response.py:85-90 the 64-combination table runs only with throttled_unbilled=False; the True
   side has just 3 anthropic mixed scripts + one single-attempt case. Fix: parametrize the same RTSX product with
   throttled_unbilled=True, expecting marked iff every attempt in {R,T}.
   Also unverified (stated limit already in the docstring): whether Bedrock ThrottlingException / ModelNotReadyException
   (both 429) and Gemini RESOURCE_EXHAUSTED are unbilled; Bedrock cross-region inference profiles are a router-like layer
   in principle. Treat as accepted risk or set bedrock False if billing evidence is lacking.
