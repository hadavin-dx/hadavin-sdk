16:42 r11 edits done (run.r11.py, safety-tests.r11.sh with T99); dev run T97 T98 T99 on r11 (dev1) and on r10 code (dev1old)
16:47 found+fixed class bug: check_pytest_config treated -k expression as path (path_indexes choke point); T97i test used relative bash (Child guard refused: test fixed). dev2 rerun on r11 and r10
16:53 early-signal handlers moved before heavy imports (D1/D2), T99g; remaining window = Python start + compile ~30-45 ms measured. Next: proofs (T98 alone on r9, guard removed), freeze, full run
16:56 FINAL full run started from evidence-r11/frozen
17:14 full run 1: 1 failure T95d3 (genuine 0664 file refused by my m6 rule: git archive gives 0664). Fixed: refuse only group bit beyond git's. Full run 2 started
