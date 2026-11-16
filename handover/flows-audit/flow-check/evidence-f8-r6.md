# Evidence F8 round 6 (raw output; reviewer-line fix)
Date (UTC): 2026-11-16. Hashes cut to 16 hex plus '...': take_check.sh f99407c3a20cee4d..., test_take_check.sh ff9ff309331bcec2..., old take_check.sh (copy of the script before this round) bb3050fe0aae33ae...
Patched real-v5 copy built the way run_all.sh builds it (F-002, F-008 applied, generator for real).

## 1. Reproduction on the OLD script (exit 5 = would-be pass with test override, i.e. NOT refused; 4 = refused)
5   Pat O L L M, 2026-11-16
5   Pat C L A U D E, 2026-11-16
5   Pat L. L. M., 2026-11-16
5   Pat Cla.ude, 2026-11-16
5   Pat Cl-aude, 2026-11-16
4   Pat Claude bot, 2026-11-16 (name msg)
5   Pat Claudebot, 2026-11-16
5   Pat Chatgpt, 2026-11-16
5   Pat Openai, 2026-11-16
5   Pat Gptbot, 2026-11-16
5   Pat Smith, 2026-11-16, written by Claude
4   Pat Sessions, 2026-11-16 (session msg)
4   Pat O_L_L_M, 2026-11-16 (name msg)
5   Pat Smith, 2026-11-16, note ChatGPT
5   Al Lee, 2026-11-16
5   Bo Ng, 2026-11-16
5   Mary-Jane O'Neil, 2026-11-16
5   J.R.R. Tolkien, 2026-11-16
5   Aiden Botha, 2026-11-16
5   Pat Smith, 2026-11-16
4   Ai Nguyen, 2026-11-16 (name msg)

## 2. Same names on the NEW script
4   Pat O L L M, 2026-11-16 (name msg)
4   Pat C L A U D E, 2026-11-16 (name msg)
4   Pat L. L. M., 2026-11-16 (name msg)
4   Pat Cla.ude, 2026-11-16 (name msg)
4   Pat Cl-aude, 2026-11-16 (name msg)
4   Pat Claude bot, 2026-11-16 (name msg)
4   Pat Claudebot, 2026-11-16 (name msg)
4   Pat Chatgpt, 2026-11-16 (name msg)
4   Pat Openai, 2026-11-16 (name msg)
4   Pat Gptbot, 2026-11-16 (name msg)
4   Pat Smith, 2026-11-16, written by Claude (name msg)
4   Pat Sessions, 2026-11-16 (session msg)
4   Pat O_L_L_M, 2026-11-16 (name msg)
4   Pat Smith, 2026-11-16, note ChatGPT (name msg)
5   Al Lee, 2026-11-16
5   Bo Ng, 2026-11-16
5   Mary-Jane O'Neil, 2026-11-16
5   J.R.R. Tolkien, 2026-11-16
5   Aiden Botha, 2026-11-16
5   Pat Smith, 2026-11-16
4   Ai Nguyen, 2026-11-16 (name msg)

## 3. New test file against a copy of the OLD take_check.sh
test_take_check: 120 of 148 cases as expected, 28 not as expected exit=1 
FAIL f8-r6: reviewer line 'Pat O L L M, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat C L A U D E, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat L. L. M., 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Cla.ude, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Cl-aude, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat C.laude, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Clau.de, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Cla Ude, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Claudebot, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Chatgpt, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Openai, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Gptbot, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Bots, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Agents, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Grok, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Llama, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Mistral, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Deepseek, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Copilot, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Anthropic, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Robot, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Ol L M, 2026-11-16' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Smith, 2026-11-16, written by Claude' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Smith, 2026-11-16, note ChatGPT' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Smith, 2026-11-16, read with C.l.a.u.d.e' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Smith, 2026-11-16, an LLM read it' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Smith, 2026-11-16, via O p e n A I' is exit 4 with the reviewer-line message (got exit 5)
FAIL f8-r6: reviewer line 'Pat Smith, 2026-11-17' is accepted (would-be pass with the override: exit 5) (got exit 4)

## 4. New test file against the NEW script
test_take_check: 148 of 148 cases as expected, 0 not as expected
rc=0; FAIL lines: 0

## 5. Syntax and run_all
bash -n take_check.sh / test_take_check.sh / run_all.sh: rc 0 / 0 / 0
run_all.sh (RUN_ALL_RAW scratch + RUN_ALL_NESTED=1): run_all rc=0
real-v5 placeholder ids: 12 file(s) warn in the committed flows (pass --strict to make that a failure)
COMMITTED PIN (take-warns.pin) reviewer line, as written: 'flows-audit session, 2026-11-16, content read by that session only, lead to confirm'. NOT confirmed by the lead: a bare take_check.sh exits 4 until the lead replaces that line (this run used 
OPEN LEAD DECISIONS (real-v5, the take): 2 webhook(s) without auth, 2 $env node(s); n8n's env-access setting is NOT visible to any static check

## 6. Checks from handover/flows-audit
python3 -I tools/check_secrets.py rc=0 (PASS 0 hits in 1818 files)
python3 tools/check_refs.py rc=0 (PASS 5162 references)
ruff check . rc=0 (All checks passed!)
ruff format --check . rc=0 (534 files already formatted)
flow-check/raw and flow-check/selftest-output: run_all used a scratch raw folder, git status shows no change there; no checkout needed
