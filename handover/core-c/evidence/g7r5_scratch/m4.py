import sys, time, importlib
sys.path.insert(0, ".")
import tests.test_redact_settle_loop as T
R, defaults = T.R, T.defaults
best = T._best_cpu
# hostile 500
r = R._Redactor({"<SECRET_1>": T.SHORT}); r.find(T._hostile_forms(500))
text = ("a"*500 + "<SECRET_1>") * (130_000 // 510); r.sweep("")
w = best(lambda: r.sweep(text)); held, r._spelled = r._spelled, {}; wo = best(lambda: r.sweep(text)); r._spelled = held
print(f"hostile 500 prefix lengths, {len(text)} chars: with forms {w:.4f} s, without {wo:.4f} s, ratio {w/wo:.1f}")
# honest many vs one
many, one = T._cookie_log(300), T._cookie_log(300, same_prefix=True)
a = T._swept_cpu(T._copies_of(many), many); b = T._swept_cpu(T._copies_of(one), one)
print(f"honest 300 prefix lengths {a:.4f} s vs 1 prefix length {b:.4f} s, ratio {a/b:.2f}; probe chars {len(T._copies_of(many))}")
# 5000 forms
values = T._uuid_values(5000)
text = "\n".join(f"password={v}.k_{i % 10}" for i, v in enumerate(values))
r = R._Redactor(None); out = r.find(text)
copies = "\n".join(f"copy {r.reverse[v]}.k_{i % 10}" for i, v in enumerate(values)); probe = out + "\n" + copies
r.sweep(probe)
w = best(lambda: r.sweep(probe)); held, r._spelled = r._spelled, {}; wo = best(lambda: r.sweep(probe)); r._spelled = held
print(f"5000 forms: with {w:.4f} s, without {wo:.4f} s, ratio {w/wo:.2f}")
# deep hostile
forms, probe = T._deep_hostile()
r = R._Redactor({"<SECRET_1>": T.SHORT}); r.find(forms); r.sweep("")
t0 = time.thread_time()
try: r.sweep(probe)
except Exception as e: print("deep hostile at the real limit:", type(e).__name__, e, f"{time.thread_time()-t0:.3f} s")
defaults.SPELLED_MAX_WORK = 10**9
t0 = time.thread_time(); r.sweep(probe); print(f"deep hostile limit raised: {time.thread_time()-t0:.3f} s; probe {len(probe)} chars, forms registered {len(r._spelled_at)}")
