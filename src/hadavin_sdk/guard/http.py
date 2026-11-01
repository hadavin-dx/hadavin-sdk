"""The one no-redirect HTTP opener, shared by the executor, the model clients and the read tools.

A redirect would carry a bearer token or API key to a host nobody configured or allowlisted: every redirect is
refused. Kept here, neutral and secret-free, so ``runtime`` and ``tools`` can use it without importing a module
that holds a secret (tests/test_repo_rules.py scans the transitive imports).

Neutral protocol: HTTP/1.1 over the standard library.
"""

from __future__ import annotations

import ssl
import urllib.request

LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)
# A loopback host is reached directly: an HTTP_PROXY would otherwise carry plain-http traffic off the machine.
LOCAL_OPENER = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))


def opener_for(context: ssl.SSLContext, direct: bool = False) -> urllib.request.OpenerDirector:
    """An opener that trusts exactly the CAs in `context` (a per-source or per-tool CA bundle), still without
    redirects."""
    handlers: list = [NoRedirect(), urllib.request.HTTPSHandler(context=context)]
    if direct:  # never via an environment proxy
        handlers.append(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener(*handlers)
