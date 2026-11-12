---
name: keep-tool-output-small
description: "owner 2026-11-02: never dump long tool output or error traces into the main chat; redirect to files, send noisy work (CodeRabbit, evidence, reviews) to background agents"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1c82e358-dcf8-4402-88bb-431ce10c72d0
  modified: 2026-11-01T20:19:31.901Z
---

The owner objected (2026-11-02) when a CodeRabbit comment probe printed about 20 Python tracebacks into the main chat (cp1252 decode errors from `gh api` JSON read through subprocess without `encoding='utf-8'`). It burns tokens and context.

**Why:** the owner pays for tokens and wants the main conversation short; noisy work belongs in background agents.

**How to apply:** (1) Any command that may print a lot: redirect stdout and stderr to a file in the scratchpad, then print only counts or the last few lines (`> out.txt 2>&1; tail -n 5 out.txt`). (2) Python reading `gh`/subprocess output: `encoding='utf-8', errors='replace'` and wrap in try/except that prints one line. (3) CodeRabbit, CI log reading, evidence runs, mutation runs, review reading: give them to a background agent and ask for a short table. (4) Never paste raw subagent transcripts; read only the report. See [[long-jobs-run-detached]] and [[token-thrift-reviews]].
