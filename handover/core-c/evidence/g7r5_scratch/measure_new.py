import sys, importlib, collections, random
sys.path.insert(0, ".")
import tests.test_redact_idempotent_property as P
import tests.test_redact_settle_loop as T
R = T.R
def stats(texts, many=False):
    mo = mf = n = 0; ho = collections.Counter(); hf = collections.Counter()
    for text in texts:
        r = R._Redactor(None); out = r.find(text); r.settle([text], [r.sweep(out)])
        per = collections.defaultdict(list)
        for ph, orig in r._spelled_at.items():
            f = R._PLACEHOLDER.search(orig); per[f.group(1)].append(f.start())
        for tok, offs in per.items():
            n += 1; mo = max(mo, len(set(offs))); mf = max(mf, len(offs)); ho[len(set(offs))] += 1; hf[len(offs)] += 1
    return n, mo, mf, dict(sorted(ho.items())), dict(sorted(hf.items()))
print("corpora (1835 inputs): tokens with forms, max offsets, max forms, hist offsets, hist forms:", stats([t for _, t in P.CORPUS]))
rng = random.Random(20261121)
lines = ["\n".join(T._lines(rng)[0]) for _ in range(2000)]
print("2000 generated compositions:", stats(lines))
print("honest A(300) cookie log:", stats([T._cookie_log(300)]))
print("honest B(300) signed log:", stats([T._signed_log(300)[0]]))
