"""EVIDENCE RUNNER plant harness. Each plant: edit one file in the plants worktree (old text must occur exactly once),
run tests/test_policy_guard.py, record exit code + failed test ids, restore with git checkout. Also runs tools/policy_page.py --check."""
import os
import re
import subprocess
import sys

WT = "/home/user/build/EV-Q8c1-a77fab7-plants"
V = "src/hadavin_sdk/actions/secrets_vault.py"
T = "src/hadavin_sdk/audit/signer_vault.py"
K = "src/hadavin_sdk/sources/kubernetes.py"
FETCH = '        status, body = self.authed("GET", f"{self.mount}/data/{self.path_prefix}{name}")\n'
EVENTS = '        events, more_e = self._items(f"/api/v1/namespaces/{ns}/events", "k8s.list_events")\n'
SIGN = '        signature = self._call("POST", f"sign/{self.key_name}", body).get("signature")\n'
LOGP = "            f\"?timestamps=true&sinceTime={quote(start, safe='')}&limitBytes={self._cfg.log_bytes}\"\n"
P = [
    ("A01 extra HTTP path (vault GET metadata, direct authed call)", V, FETCH,
     '        self.authed("GET", f"{self.mount}/metadata/{self.path_prefix}{name}")\n' + FETCH),
    ("A02 query string on the secrets read", V, FETCH, FETCH.replace('{name}")', '{name}?version=1")')),
    ("A03 other resource under the declared id (deeper path /x)", V, FETCH, FETCH.replace('{name}")', '{name}/x")')),
    ("A04 import httpx in the vault module", V, "import json\nimport os\n", "import json\nimport os\nimport httpx  # noqa\n"),
    ("A05 methodcaller on authed", V, FETCH,
     '        from operator import methodcaller\n        methodcaller("authed", "DELETE", f"{self.mount}/metadata/x")(self)\n' + FETCH),
    ("A06 attrgetter on authed", V, FETCH,
     '        from operator import attrgetter\n        attrgetter("authed")(self)("DELETE", f"{self.mount}/metadata/x")\n' + FETCH),
    ("A07 getattr literal (P04b) LIST", V, FETCH,
     '        getattr(self, "authed")("LIST", f"{self.mount}/metadata/{self.path_prefix}")\n' + FETCH),
    ("A08 widened grant R17 `+` -> `+*` in POLICY", V, '"resource": "{mount}/data/{path_prefix}+",', '"resource": "{mount}/data/{path_prefix}+*",'),
    ("A09 star capability: name read -> *", V,
     '            "name": "read",\n            "resource": "{mount}/data/{path_prefix}+",',
     '            "name": "*",\n            "resource": "{mount}/data/{path_prefix}+",'),
    ("A10 widened grant R17 to old star form", V, '"resource": "{mount}/data/{path_prefix}+",', '"resource": "{mount}/data/{path_prefix}*",'),
    ("A11 verb of the read changed GET -> DELETE (code)", V, FETCH, FETCH.replace('"GET"', '"DELETE"')),
    ("A12 raw urllib urlopen outside the sender", V, FETCH, '        urllib.request.urlopen("https://example.invalid/x")\n' + FETCH),
    ("A13 opener used outside the sender", V, FETCH,
     '        self._opener.open(urllib.request.Request("https://example.invalid/x"))\n' + FETCH),
    ("A14 getattr(self, 'au'+'thed') computed name", V, FETCH, '        getattr(self, "au" + "thed")("DELETE", "x")\n' + FETCH),
    ("A15 vars(self)['authed'] indirect", V, FETCH, '        vars(self)["authed"]("DELETE", "x")\n' + FETCH),
    ("A16 declared op path deeper (POLICY operations /x)", V,
     '"operations": (("GET", "{self.mount}/data/{self.path_prefix}{name}"),),',
     '"operations": (("GET", "{self.mount}/data/{self.path_prefix}{name}/x"),),'),
    ("A17 transit: extra rotate request", T, SIGN, '        self._call("POST", f"keys/{self.key_name}/rotate")\n' + SIGN),
    ("A18 transit: query string on sign path", T, SIGN, SIGN.replace('f"sign/{self.key_name}"', 'f"sign/{self.key_name}?x=1"')),
    ("A19 transit: sign path with hash-algorithm suffix", T, SIGN, SIGN.replace('f"sign/{self.key_name}"', 'f"sign/{self.key_name}/sha2-256"')),
    ("A20 transit: decrypt instead of sign", T, SIGN, SIGN.replace('f"sign/', 'f"decrypt/')),
    ("A21 transit grant widened to every key (sign/*)", T, '"resource": "{transit_mount}/sign/{key_name}",', '"resource": "{transit_mount}/sign/*",'),
    ("A22 transit grant widened with `+`", T, '"resource": "{transit_mount}/sign/{key_name}",', '"resource": "{transit_mount}/sign/+",'),
    ("A23 k8s: ?watch=true under list_events (P09a)", K, EVENTS,
     '        self._get(f"/api/v1/namespaces/{ns}/events?watch=true", "k8s.list_events")\n' + EVENTS),
    ("A24 k8s: follow=true on pod log query", K, LOGP, LOGP.replace('{self._cfg.log_bytes}"', '{self._cfg.log_bytes}&follow=true"')),
    ("A25 k8s: secrets path under declared id k8s.list_events", K, EVENTS,
     '        self._get(f"/api/v1/namespaces/{ns}/secrets", "k8s.list_events")\n' + EVENTS),
    ("A26 k8s: DELETE method under declared id", K, EVENTS,
     '        self._get(f"/api/v1/namespaces/{ns}/events", "k8s.list_events", method="DELETE")\n' + EVENTS),
    ("A27 k8s: import requests", K, "import json\n", "import json\nimport requests  # noqa\n"),
    ("A28 k8s: unquoted name in path", K, 'ns = quote(scope, safe="")\n        out: list[Record] = []', "ns = scope\n        out: list[Record] = []"),
    ("A29 k8s: grant verb widened list -> *", K,
     '"name": "list",\n            "resource": "core/events in {namespaces}"', '"name": "*",\n            "resource": "core/events in {namespaces}"'),
    ("A30 k8s: resource widened core/events -> core/*", K, '"resource": "core/events in {namespaces}"', '"resource": "core/* in {namespaces}"'),
    ("A31 k8s: getattr(self,'_get') literal extra request", K, EVENTS,
     '        getattr(self, "_get")("/api/v1/namespaces/x/secrets", "k8s.list_events")\n' + EVENTS),
    ("A32 vault never-list entry changed sys/* -> sys/+", V, '            "name": "sys/*",\n', '            "name": "sys/+",\n'),
]


def sh(*a):
    return subprocess.run(a, cwd=WT, capture_output=True, text=True)


env = dict(os.environ)
env["PYTHONPATH"] = WT + "/src"
for k in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_CA_BUNDLE", "ANTHROPIC_BASE_URL", "GH_TOKEN",
          "GITHUB_TOKEN", "CLOUDSDK_AUTH_ACCESS_TOKEN", "VAULT_TOKEN", "VAULT_SECRET_ID"]:
    env.pop(k, None)
PY = "/home/user/build/venv-evq8c1/bin/python"


def run_tests():
    r = subprocess.run([PY, "-m", "pytest", "tests/test_policy_guard.py", "-q", "-p", "no:cacheprovider", "-rf", "--no-header"],
                       cwd=WT, capture_output=True, text=True, env=env)
    fails = re.findall(r"^FAILED (\S+)", r.stdout, re.M)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    return r.returncode, fails, (lines[-1] if lines else "")


def page_check():
    r = subprocess.run([PY, "tools/policy_page.py", "--check"], cwd=WT, capture_output=True, text=True, env=env)
    return r.returncode, (r.stderr.strip().splitlines() or [""])[0][:200]


only = sys.argv[1:]
print("import path check:", subprocess.run([PY, "-c", "import hadavin_sdk;print(hadavin_sdk.__file__)"], cwd=WT,
                                           capture_output=True, text=True, env=env).stdout.strip())
rc, fails, last = run_tests()
print("baseline (no plant):", rc, last, page_check(), flush=True)
for pid, f, old, new in P:
    if only and pid.split()[0] not in only:
        continue
    path = os.path.join(WT, f)
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        print(f"{pid} | PLANT NOT APPLIED: old text occurs {n} times", flush=True)
        continue
    open(path, "w", encoding="utf-8", newline="\n").write(text.replace(old, new))
    try:
        rc, fails, last = run_tests()
        prc, pmsg = page_check()
    finally:
        sh("git", "checkout", "--", f)
    st = sh("git", "status", "--porcelain").stdout.strip()
    print(f"{pid} | pytest exit {rc} | {'CAUGHT' if rc != 0 else 'NOT CAUGHT'} | {last} | failing tests: {len(fails)} | "
          f"first: {[x.split('::')[-1][:70] for x in fails[:3]]} | page --check exit {prc} {pmsg!r} | tree clean after restore: {st == ''}", flush=True)
