# Q8b b5 Issue 1 repro (run 2026-11-12, raw output)

Script: /home/user/build/B-Q8b-b5-scratch/repro.py. Values built from parts. Head = 999ed05b; main = origin/main 2a8c2aac. Run with PYTHONPATH pointing at the tree src.

## B-Q8b-b5
```
module: /home/user/build/B-Q8b-b5/src/hadavin_sdk/__init__.py
INPUT: x session_cookie=Zq7xV; csrf=Kp9wT; user=Hn4bL y
 redact().text      : x session_cookie=<SECRET_1>; csrf=Kp9wT; user=Hn4bL y
 runmap.redact_text : x session_cookie=<SECRET_1>; csrf=Kp9wT; user=Hn4bL y
 card clean()       : x session_cookie=<SECRET_1>; csrf=Kp9wT; user=Hn4bL y
 tool redact_layered: x session_cookie=<SECRET_1>; csrf=Kp9wT; user=Hn4bL y
```
## B-Q8b-b5-main
```
module: /home/user/build/B-Q8b-b5-main/src/hadavin_sdk/__init__.py
INPUT: x session_cookie=Zq7xV; csrf=Kp9wT; user=Hn4bL y
 redact().text      : x session_cookie=<SECRET_1> y
 runmap.redact_text : x session_cookie=<SECRET_1> y
 card clean()       : x session_cookie=<SECRET_1> y
 tool redact_layered: x session_cookie=<SECRET_1> y
```
