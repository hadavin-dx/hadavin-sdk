# Plan v4 round 1: Blocker/Major findings vs lead resolve rulings (read-only fact table)

Sources: five reports in _local\scratch\wt\handover\handover\reviews\plan-v4-round1\ and egm\hadavin-sdk\core-complete\plan-v4-1-resolve-round1.md (rulings 1-12). Labels: "covered N" = ruling N addresses it; "PARTLY N" = ruling N addresses part, remainder listed; "NOT covered" = no ruling. Severity as labelled on each finding in the report (readiness header says 12 Major but labels 18; per-finding labels used). Nits omitted.

## Structural (no Blocker; 12 Major)
| Id / title | Sev | Status |
|---|---|---|
| S1 no Added/Changed/Unchanged list; v3 frozen, v4 not an amendment | Major | covered 1 |
| S2 package ids differ from v3, no mapping | Major | covered 1 |
| S3 cutting P5b2-P5b5 needs amendment rewriting P5c dependents; HOLD row omits it | Major | NOT covered: asked that s4/s10 cite the v3 cut rule and the P5c Depends-on rewrite |
| S4 rung legend differs from the studio 7-rung ladder | Major | covered 1 |
| S5 s5 paragraph directly after table, malformed table row | Major | NOT covered: asked for a blank line so the table renders |
| S6 Cloud Starter/Pro/Business row vs s2 Business EUR 667 contradiction; billing basis | Major | covered 6 |
| S7 no totals row; EUR/USD mixed without conversion rule | Major | covered 6 (totals); currency rule not named |
| S9 P4 "run T1 first" vs s10.1 default "no"; fallback unstated | Major | covered 7 |
| S10 "about 1 day of agent time" vs v3 "no estimates" | Major | covered 12 |
| S11 decision 3 (do not cut n8n/Make-connected) vs CUT-TO-CONFIG+GLUE; verdict terms undefined | Major | PARTLY 1 (terms defined); remainder: conflict between owner decision 3 and template packs' CUT-TO-CONFIG+GLUE |
| S12 "settled" contains NOT PROVEN items; no Status column (DECIDED/OWNER-OPEN/LEAD-DEFAULT) | Major | NOT covered: asked for a status column and separating settled from unproven |
| S13 T3 and T4 absent from s7 work order; no owner/package for T1, T3, T4 | Major | NOT covered: asked for owner and package for T1, T3, T4 in the work order |

## Comprehension (2 Blocker, 14 Major)
| Id / title | Sev | Status |
|---|---|---|
| C1 AK-G2, AK1, AK1b, AK1a/1c, AK-G15, AK-G1, AK2a, AK4a, AK-G16, AK0, JG-3, P0t, "step" undefined | Blocker | covered 1 (AK ticket ids used); legend/definitions of each not stated |
| C2 sub-ids P1a/b/c, P4b1/b2, P6b1 not in v3; no mapping | Blocker | covered 1 |
| C3 P5b2/P5b5 meaning differs from v3 (R3a, R5); cut needs written yes | Major | covered 11 |
| C4 PR numbers 63-86, "open chain", "P1b fix batch", "PR 66 money chain" undefined | Major | NOT covered: asked for a PR/package/state table |
| C5 verdict words undefined | Major | covered 1 |
| C6 rung scale inline, R447/R448 unexplained, differs from 7-rung ladder | Major | covered 1 |
| C7 evidence column cites no file/section/metric ("scan table 40-60%", "pass 4", "85-90%") | Major | NOT covered: asked for file, section or metric behind each evidence cell |
| C8 door, channel/executor/llm kind, meter, stop_state, audit undefined | Major | NOT covered: asked that these terms be defined in v4 |
| C9 "same key, one effect, forever" unexplained; windows telegraphic | Major | NOT covered: asked for a one-sentence explanation |
| C10 plan names inconsistent; execution, Sustainable Use 1.0, ee folders, Close task undefined; "only tool an agency may legally resell" unsupported | Major | PARTLY 6 (Business split); remainder: term definitions, "legally resell" claim |
| C11 T1 gates P4b1 yet LiteLLM never a core dependency; default "no" removes gate; split T1a/T1b | Major | covered 7 |
| C12 no total/scenario; EUR/USD mixed; caps vs volume; overage; Make; hosting; "one-person team" | Major | covered 6 |
| V1 AK-G2 "v1.1 FIRST/BUILD NEXT" vs v3 trigger and frozen list | Major | covered 1, 9 |
| V2 "about 1 day" vs v3 no estimates | Major | covered 12 |
| V3 Presidio default vs v3 s5 pattern default; P5c 4-PR scope; new dependency | Major | covered 8 |
| V4 P2d meaning/scope differs from v3 | Major | covered 2 |

## Zoom-out (2 Blocker, 8 Major)
| Id / title | Sev | Status |
|---|---|---|
| Z1 P2d "off by default" contradicts owner orders 11, 19E | Blocker | covered 2 |
| Z2 AK-G2 WRAP pg-boss/Graphile (Node in Python core) | Blocker | covered 3 |
| Z3 T1 unresolved though gateway-check already ran; gates P4b1 | Major | covered 7 |
| Z4 missing rows P5b3, P5b4, P6b2, secrets, signer, audit, executor, P0a, P8, P4e, P7*, template packs | Major | NOT covered: asked for rows for these modules or one line "all other v3 rows unchanged" |
| Z5 v4 not an amendment; silently changes redactor default, build order, cut list; AK-G2 vs P8a | Major | PARTLY 1, 8, 11; remainder: statement of AK-G2 vs P8a (re-pin of demos) ordering and list of what v4 supersedes |
| Z6 n8n licence evidence narrow (client-service clause, operating client's n8n) | Major | covered 5 |
| Z7 s5 n8n rows lumped; one-person inference; Cloud credential sharing unread; execution count vs 3,000 messages | Major | covered 6 |
| Z8 "only automation tool an agency may legally resell" unsupported | Major | NOT covered: asked to reword to "only one found with MIT core in a limited scan; ee folders and embed terms not read" |
| Z9 hosting USD 5-10 does not buy Postgres or Python runtime | Major | covered 6 |
| Z10 LiteLLM 1.107.0 source note; decision 3 vs CUT-TO-CONFIG+GLUE and n8n Wait node replacing waiting screen | Major | NOT covered: asked for source note on LiteLLM 1.107.0 and rename/keep-pack resolution of the decision-3 conflict |

## Readiness (4 Blocker, 18 Major as labelled)
| Id / title | Sev | Status |
|---|---|---|
| V4-01 P2d "off by default" vs orders 11, 19E | Blocker | covered 2 |
| V4-20 no inbound webhook contract (signature, delivery key, response codes) | Blocker | covered 4 |
| V4-21 no OUT action API contract (schema, auth, idempotency, executor, credential holder) | Blocker | covered 4 |
| V4-22 "effect in one transaction" vs client CRM/payment; "forever" vs retention/erasure | Blocker | PARTLY 4 (ticket wording for one transaction); remainder: retention-vs-erase rule |
| V4-02 Presidio default vs v3 s5 and order 35 | Major | covered 8 |
| V4-03 "Presidio does not fold look-alikes" is UNVERIFIED | Major | NOT covered: asked to mark UNVERIFIED or cite order 35 hostile-set run |
| V4-04 pg-boss/Graphile Node vs Python core | Major | covered 3 |
| V4-05 "about 1 day" estimate; Tier A gates | Major | covered 12 |
| V4-06 v3 frozen; ids undefined; no amendment | Major | covered 1 |
| V4-07 AK-G15 approval via n8n Wait; approver identity; flow token must not approve | Major | NOT covered: asked how the human click reaches the API with the human's identity and a negative test that the flow's token cannot approve |
| V4-08 AK1b in door pipeline but v1.1; which gate covers the OUT action API | Major | NOT covered: asked for one gate per path (llm, tool/recipient, OUT) and its owning package |
| V4-09 n8n licence claim not in lead-fetch; no clause quoted | Major | covered 5 |
| V4-10 paid self-hosted "Business EUR 667", "one-person team", Cloud Starter/Pro contents unbacked | Major | covered 6 |
| V4-11 Make "one action ~ one credit" unbacked | Major | covered 6 (Make stays UNREAD) |
| V4-12 Activepieces "may legally resell" is a legal conclusion | Major | NOT covered: asked for "MIT outside ee folders (LICENSE read)" wording and cloud plan separated from self-host licence |
| V4-13 hosting USD 5-10 unbacked; ignores Postgres | Major | covered 6 |
| V4-16 missing rows for v3/kit ids (P0*, P5b3, P5b4, P6b2, P4c, P8*, secrets, signer, audit, AK2b/c/d, AK3, AK4b, G-tickets) | Major | NOT covered: asked for a row per v3 and kit id |
| V4-17 rung table has 5 rows vs 20+ modules; scale differs from 7-rung ladder | Major | PARTLY 1 (rung legend); remainder: rung row per non-KEEP-CODE module |
| V4-18 AK1a/1c WRAP Postgres RLS FORCE is Postgres-only; no alternative | Major | NOT covered: asked for memory/SQLite equivalent or exclusion from client profiles, plus cross-backend tenant test |
| V4-23 T2 needs injectable clock, named crash points, no-expiry schema assertion | Major | PARTLY 10 (ledger layer tested directly); remainder: fake clock, named crash points, no-expiry assertion |
| V4-24 T5 Make not self-hostable; Activepieces Docker; offline recorded contract test | Major | NOT covered: asked for an offline recorded contract test plus manual per-tool end-to-end runs |
| V4-25 T1 pinned version unnamed; "admitted"/cap undefined; order 35 test not cited | Major | covered 7 |

## Design (2 Blocker, 18 Major)
| Id / title | Sev | Status |
|---|---|---|
| F1 P2d "off by default" vs orders 11, 19E | Blocker | covered 2 |
| F2 Presidio default vs orders 64, 35 | Blocker | covered 8 |
| F3 door contract only named; OUT arrow ambiguous | Major | covered 4 |
| F4 replay after 31 days vs signature tolerance; "forever" vs retention/erasure; clock source | Major | covered 10 (timestamp tolerance separated); retention/erasure and clock source not addressed |
| F5 T5/template packs cannot reach local door; CI no internet; speculative packs vs decision 4, order 57 DEMAND | Major | NOT covered: asked for per-tool test method and building only packs for chosen tools |
| F6 "no loss" before the door; reconciliation | Major | covered 4 (hop before door out of guarantee, stated plainly); daily reconciliation not addressed |
| F7 n8n Wait resume URL bearer link; approver credential inside n8n | Major | NOT covered: asked for approval authenticated by a human identity outside the flow, n8n only notifies |
| F8 AK-G2 WRAP pg-boss/Graphile | Major | covered 3 |
| F9 missing rows: AK1 step contract, audit, signer, secrets, P6b2, P0a, P8, invoicing, AK2*/AK3/AK4b | Major | NOT covered: asked for rows for these modules |
| F10 rung table lacks guarantee + failing property per KEEP-CODE row; licence/version/SPDX/date; "rung 0 / CLIENT-EXCLUDED" | Major | PARTLY 1 (rung legend); remainder: per-row guarantee, reproduced failing property, licence/version/SPDX/date |
| F11 AK-G15/G1/G16 DEFERRED (order 57.2) but scheduled | Major | covered 9 |
| F12 T1 ignores order 35 result and Options paragraph; pinned version unnamed | Major | covered 7 |
| F13 n8n licence unquoted | Major | covered 5 |
| F14 Community gap; paid self-hosted EUR 8,004 vs Port 10 seats; Cloud Starter/Pro unread | Major | covered 6 |
| F15 Make price/credit unbacked | Major | covered 6 |
| F16 cost table not a usable quote model (mixed currency, no totals, hosting, Presidio container, execution cap vs workload, tokens) | Major | covered 6 |
| F17 T1 gate stalls P4b1; weaker than v3 s8 test | Major | covered 7 |
| F18 unbacked claims (failed-call billing, Activepieces resell, cloud filters, LiteLLM 1.107.0, PR figures, Langfuse tier, Hatchet/pg-boss inferences) | Major | NOT covered: asked that these seven claims be sourced or marked as inference/UNVERIFIED |
| F19 "about 1 day" unsupported | Major | covered 12 |
| F20 RLS Postgres-only; SQLite cannot hold same ledger; "85-90%" judgement | Major | NOT covered: asked that ledger and AK1c require Postgres, SQLite for dev only, with a negative test |

## Counts (Blocker + Major findings, per-finding labels)
| Reviewer | Total | Covered | PARTLY | NOT covered |
|---|---|---|---|---|
| Structural | 12 | 7 | 1 | 4 |
| Comprehension | 16 | 11 | 1 | 4 |
| Zoom-out | 10 | 6 | 1 | 3 |
| Readiness | 22 | 12 | 3 | 7 |
| Design | 20 | 14 | 1 | 5 |
| **All** | **80** | **50** | **7** | **23** |

Blockers: 10 listed (comprehension 2, zoom-out 2, readiness 4, design 2): 8 covered, 1 PARTLY (V4-22), 0 NOT covered... recount: C1, C2, Z1, Z2, V4-01, V4-20, V4-21, F1, F2 are covered (9); V4-22 PARTLY (1). Blockers NOT covered: 0.
Overlap note: several findings name the same issue across reviewers (e.g. missing rows Z4/V4-16/F9; rung table V4-17/F10; unbacked resell claim Z8/V4-12/F18; Postgres-only RLS V4-18/F20; approval identity V4-07/F7); counts are per reviewer finding, not deduplicated.
