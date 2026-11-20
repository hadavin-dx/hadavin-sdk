import sys, importlib
import tests.test_redact_idempotent_property as P
bad = []
for label, text in P.CORPUS:
    pass
n = 0
for text in P._params():
    n += 1
    try: P.test_one_pass_is_a_fixed_point_and_leaves_no_raw_copy(text)
    except AssertionError as e: bad.append((str(text)[:80], str(e)[:200]))
try: P.test_the_corpus_is_what_this_file_says(); print("corpus pinned ok")
except AssertionError as e: print("corpus", e)
try: P.test_no_input_of_the_corpora_is_refused(); print("no refusal ok")
except AssertionError as e: print("refused", e)
print(n, "inputs;", len(bad), "fail", bad[:3])
