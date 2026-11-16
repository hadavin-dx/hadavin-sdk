P="/home/user/hadavin-sdk/handover/core-hardening/audit-r460/CORE-PR-HANDOFF-v11.md"
t=open(P,encoding="utf-8").read()
def sub(old,new,count=1):
    global t
    n=t.count(old); assert n==count,(n,old[:80]); t=t.replace(old,new)
sub("`SpendRefused(ProviderError)` is defined in `llm/protocol.py` beside `ProviderError` (so `guard/injection.py` can name it without importing `llm.spend`); it has `code`.","`SpendRefused(Exception)` is defined in `errors.py` beside `ConfigError` (the one module with no imports, so `guard/injection.py` and `limits.py` can name it with no new cycle, section 8.1) and is **not** a `ProviderError`; it has `code`.")
sub("`SpendRefused` is a subclass of `ProviderError` (defined in `llm/protocol.py`), and `with_retry` re-raises a `ProviderError` at once (`retry.py:95-96`), so a refusal is never wrapped or retried and `retry.py` does not change.","`SpendRefused` is defined in `errors.py` and is not a `ProviderError`; `with_retry` gets one changed line, `except (ProviderError, SpendRefused): raise` (`retry.py:95-96`, new import `errors`), so a refusal is never wrapped or retried. Why not a `ProviderError` subclass (v10's choice): the one edge `guard.injection -> llm.protocol` it needed merged the guard module group into the import cycle of the `llm` group (independent check `raw-merge-probe.txt`, 8.1). Consequence: the `except ProviderError` sites (`k1b/loop.py:176`, `agent_loop.py:432-433`) no longer catch it, which is what we want; the S-2a builder reads `k1b/loop.py` 85-215 and gives the replay a defined end for a `SpendRefused` (test in E0-S2-4).")
sub("The existing `except ProviderError` (`:432-433`) comes after a new `except SpendRefused: raise`.","The existing `except ProviderError` (`:432-433`) does not see a `SpendRefused` (it is not a `ProviderError`), so no ordering rule is needed.") if "The existing `except ProviderError` (`:432-433`) comes after a new `except SpendRefused: raise`." in t else None
# table
sub("| llm.spend | models, llm.protocol | |","| llm.spend | models, errors | |")
sub("| llm.callgate | llm.spend, llm.protocol, models | |","| llm.callgate | llm.spend, errors, models | |")
sub("| llm.common | llm.spend, llm.protocol | llm.callgate |","| llm.common | llm.spend, llm.protocol, errors | llm.callgate |")
sub("| limits | llm.spend, llm.protocol, models, registry, store.protocol, audit.protocol | |","| limits | llm.spend, errors, models, registry, store.protocol, audit.protocol | |")
sub("| runtime.agent_loop | limits, llm.spend, llm.protocol | |","| runtime.agent_loop | limits, llm.spend, llm.protocol, errors | |")
sub("| guard.injection | llm.protocol | |","| guard.injection | errors | |")
sub("| guard.bedrock_guardrail | llm.spend, llm.protocol | llm.callgate |","| guard.bedrock_guardrail | llm.spend, errors | llm.callgate |")
sub("| k1b.loop | llm.spend | |","| k1b.loop | llm.spend, errors | |\n| llm.retry | errors | |")
sub("| store.memory | store.protocol | |","| store.memory | store.protocol, errors | |\n| store.migrate | errors | |") if False else None
open(P,"w",encoding="utf-8").write(t); print("ok")
