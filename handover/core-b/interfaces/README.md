# INTERFACES published by core-b (SPINE) for core-a and core-c (2026-11-20 05:29 UTC)
State: PUBLISHED, version 1. NOT reviewed yet (the EGM round comes with ticket F-store). NOT run: nothing here was executed by core-b; the signatures are copied from code that exists on unmerged branches (named below), where the lead's baseline passed.
- i-store-methods.md + store_spend_protocol.py: interface (i), the six store methods for spend reservations.
- ii-reserve-settle-api.md + reserve_settle_api.py: interface (ii), what the model gate wrapper calls before and after a model call.
The .py files are signature files for reading and for typing against (Protocols and dataclasses, no logic). They are NOT importable package code; the real code lands in src/hadavin_sdk in step F.
Rule: code against these names. If you need a change, write handover/<your-name>/requests/<n>-interface.md with the reason; core-b answers in its DECISIONS.md and bumps the version here.
Receipts and work items (plan-v3 named them under interface (i)): NO store method is offered. The lead's draft ticket D (finding 1 and 2) needs no table; step H is cut unless a review proves a gap.
