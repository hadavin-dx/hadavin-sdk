# AK-G16: how `deploy render` and `deploy check` decide (render and refusal-gate flow)

* **Author:** Claude (lead's session, `egm:egm-brainstorm`, AUTO mode, SHORT)
* **Date:** 2026-11-06

**Read this first (honest notes).**
- **This is NOT a Goldfish review.** The skill asks for six reviewer lenses run as fresh sub-agents (`egm-synthesizer`). This session has no sub-agent tool, so none was run. The skill says that a review in the same context does not count as a Goldfish review. The "Analysis" below is the author's own stress test. The real independent check is the build-start review (`egm:egm-review`), which still has to run.
- **AUTO mode.** Every interactive gate of the skill was skipped (the readiness gate, the iteration loop and the handoff gate), as order 46 PL1 and the brief require. Wherever the skill would ask the author to choose, this brief takes the option the FROZEN ticket already took. Each such choice is named in "Key decisions".
- **Scope.** Only the render and refusal-gate flow of AK-G16 (sub-PR -b1 and the -b2 rights lint). The parts build (D1), the smoke test (D3) and the web doors (D4) are out of scope here, except where the render reads their outputs.
- **Sources.** `<repo>/handover/tickets/AK-G16.md` (FROZEN at revision 3, plus build notes BN-1 to BN-32; build notes win), `<repo>/handover/reviews/AK-G16-round3-resolve.md`, and `LEAD-ORDERS.md` orders 43, 45 and 46. Core code was read on `ce70eb5`, the last commit that touches `src/`. No other review file was read.

## Overview

A client who runs our program in their own cloud needs deployment files: plain Kubernetes files plus one container-image recipe. AK-G16-b1 adds two commands:
- `hadavin-sdk deploy render --out <dir>` writes those files from the client's config.
- `hadavin-sdk deploy check <dir>` reads files the client's team may have edited and refuses any file that breaks a rule.

Neither command calls a cloud, a cluster or a secret store. Both are text in, text out.

The flow has to answer four questions:
1. Which configs may be rendered at all? The **refusal gate**: pilot and prod are refused until the separate audit-writer role (V7) exists.
2. Which backend settings the neutral kit cannot express safely, and so refuses: an anchor (the locked proof copy), a key file on disk, a secrets kind other than mounted files.
3. What is rendered for each part: `app`, `tick`, `purge`, `maintenance`, `audit` and the one-off `migrate` Job.
4. How the lint rules check the result, and in what order all these checks run.

Who uses it: the client's platform team (runbook R5), the lead, and CI tests, which run plan-only.

## Analysis (author's stress test; not Goldfish)

**What is wrong or risky, first.**
1. **The ticket contradicts itself on `dev`.** I6 (ticket line 348) and the Security notes (line 227) say `deploy render` refuses a `dev` config. BN-6 builds its cost statement on that ("no real config renders until V7"). Order 46 and BN-32 say "dev renders stay allowed". BN-32 explicitly overrides BN-1, BN-6 and BN-31; it does not name I6. The design follows BN-32, the later and lead-signed text, and lists the conflict for the lead (design, C1).
2. **If `dev` renders, nothing refuses dev-only kinds in a render.** Outside `dev`, the config itself refuses the fake model, fake channel, fake and env secrets, the memory store and `local_dir` audit (`config.py:365-370`, `backends/table.py:593-602`). Inside `dev` it allows them. The render refuses non-mounted secrets kinds (R2), so `fake` and `env` secrets cannot render. A dev config with the memory store, the fake model or `local_dir` audit would render Kubernetes files that look deployable. No ticket row covers this (design, C2).
3. **The prod half of row R16 cannot reach the gate as BN-6 words it.** BN-6 item 4 says "the fixture config set to pilot and then to prod is refused, and the message names V7". The fixture is a pilot config with `anchor: none`, because R15 demands that. Change it to `prod` and loading the config already fails: prod refuses `signer: none` and `anchor: none` (`backends/table.py:604`, applied at `config.py:391-392`). Loading raises `ConfigError` (`config.py:436-454`), so the command exits 2 (`cli.py:74-76`) before any render code runs. The message then names the anchor, not V7. Any prod config that does load has an anchor, and R15 refuses that. So in v1 prod can never render, whatever the gate says. The gate's V7 message can appear for prod only if the gate and R15 report together, on a prod variant that has an anchor (design, C3).
4. **`deploy check` and the gate.** BN-6 says render AND check refuse pilot and prod. Order 46 and BN-32 say only "`deploy render` REFUSES", although BN-32 adds "as BN-6 describes". The ticket's check exits 1 on a problem (Interface 3). It does not say which exit code a gate refusal gets (design, C4).
5. **"Every problem listed".** Interface 3 says render exits 2 "with every problem listed". The lint cannot run on a config that the pre-render refusals stopped, so "every problem" can only mean every problem of the stage that stopped the run (design, C5).

**Counter-arguments weighed.**
- *"Put the gate first and stop at once: simpler."* Rejected. The config already reports every environment refusal at once "so one fix round is enough" (`config.py:365`). A client who fixes the anchor and only then learns about V7 wastes a round. And for prod, a gate that runs first and stops would hide R15.
- *"Let `deploy check` skip the gate: it only reads files."* Rejected. BN-6 names check, and BN-32 points back to BN-6. A check that passes a pilot config would hand a client team a green light that render withholds.
- *"Lint only the files, not the in-memory render."* Rejected. The ticket proves each render mutant by "the clean-render lint test" (mutation plan -b1 render side). So render must lint its own output before it writes anything.

**What survives.** One ordered flow shared by both commands:
1. Load the config.
2. Collect every pre-render refusal, the gate included.
3. Build the plan.
4. Render to memory.
5. Lint, with rule ids on every problem.
6. Write only if there were zero problems.

`deploy check` reuses steps 1-3 and 5, and reads the files from disk instead of rendering them.

## Goals vs. Non-Goals

* **In-Scope Goals:**
  - the order of checks in `deploy render` and `deploy check`;
  - the pilot/prod gate on `defaults.AUDIT_WRITER_SEPARATE` (BN-6 as decided by BN-32);
  - the no-anchor refusal (R15 as narrowed by BN-10);
  - the other target refusals: the secrets kind (R2), key files (BN-26), distinct Secret object names (BN-3), the migrate role mapping (R3), and `wsgi_app` from -d on (BN-9);
  - what each part gets in the render;
  - how the lint rules fire: the strict loader (L17) first, then the allow-list (L18), then the rest, each problem prefixed with its rule id (BN-5);
  - the -b2 rights lint (L10, L13) on `rights_for(plan)`.
* **Out-of-Scope Non-Goals:**
  - the parts build (D1), `secret_names_for` internals beyond its signature (BN-20);
  - the smoke test, the WSGI adapter, and the image build or push;
  - any cloud adapter (V1-V3), any `deploy apply`;
  - V7 itself (it flips the constant in its own PR);
  - changing the frozen ticket.

## Alternatives Weighed

- **Gate enforced only by a person (PL20 (b)).** Rejected by the lead: order 46 item 108 and BN-32 choose (a), "enforced by code and a test, not left to a human".
- **Gate in both code and a person's check (PL20 (c)).** Not chosen: the lead chose (a). The lead still shows O12 at the pilot gate (order 45 item 16), which is a person's step outside this flow.
- **Anchor allowed when "a cloud adapter is configured" (order 45 item 17 wording).** Narrowed by BN-10. v1 has no adapter field and `target` is `Literal["kubernetes"]`, so the render refuses whenever `backends.anchor` is not `none`.
- **Stopping at the first refusal.** Rejected by the author: it costs extra fix rounds and hides R15 behind the gate for prod (Analysis, counter-argument 1).
- **The lint rules L1 and L6's Secret-object half.** Cut by BN-5: L18 refuses those kinds outright, so neither rule could ever be the only one that fails.
- **A schedule-dependent `startingDeadlineSeconds`.** Replaced by BN-12: the value 50 goes on every CronJob.

## Key Decisions & Staging for Next Steps

1. **Ticket choice taken:** PL20 (a). `deploy render` and `deploy check` refuse `environment: pilot` and `prod` while `defaults.AUDIT_WRITER_SEPARATE` is `False`, with the message "pilot and prod need the separate audit-writer role (V7); not built yet" (BN-6, BN-32).
2. **Ticket choice taken:** `dev` is not gated (BN-32). Conflict with I6 listed as C1. Dev-only kinds in a render listed as C2. No new refusal is invented here.
3. **Ticket choice taken:** R15 via BN-10, "refuse whenever `backends.anchor` is not `none`".
4. **Author choice (flow detail the ticket leaves open):** every pre-render refusal, the gate included, goes into one list that is reported at once, in the `config.py:365` style. Lint runs only when that list is empty.
5. **Author choice:** a gate refusal or other pre-render refusal in `deploy check` exits 2, like any `ConfigError` (`cli.py:74-76`). Lint problems exit 1 (Interface 3). Listed as C4 for the lead.
6. **Author choice:** render lints its in-memory output and writes nothing unless the lint is clean (Interface 3 "writes nothing if any problem").
7. **Staged for `egm:egm-draft`:** the design describes the flow step by step with file:line cites, lists every contradiction (C-list) for the lead, and marks UNVERIFIED anything not read.
