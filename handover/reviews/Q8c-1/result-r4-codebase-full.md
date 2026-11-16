Q8c-1, head be5313711305f417021a374465acc967b01f68e7, round 4 (delta on r3, head 6bdfadc1), persona: codebase details. Static read only; I ran nothing. Snapshot: /home/user/build/snap/q8c1f3-be531371.

Verdict: 0 Blocker, 1 Major, 4 Minor/Nit. The carried merge gate is unchanged: the 12 Vault server tests have still never run (ENGINE_RUN is None, tools/policy_page.py:45). That is a process gate, not a code defect.

Earlier reports read: result-r3-codebase-full.md, goldfish_review_report-r3.md (resolve), builder-b2-report.md. The r3-design report was not read, so my check of the design findings rests on the resolve report's summary of them.

### [F1] Major - Kubernetes `rules_review` shows "it creates nothing" as checked, while the same page says no vendor source says so
Where: src/hadavin_sdk/sources/kubernetes.py:441 (free `reason`) and :449 (`verified` K-RBAC, K-SRC, K-SSRR); the never entry `create` at :474-480. Page: docs/declared-permissions.md:175 against :184.
What: The page lists `k8s.rules_review` as "asks the cluster what this identity may do; it creates nothing", then "Checked: 2026-11-11, sources K-RBAC, K-SRC, K-SSRR". The never entry `create` says "That these three requests write nothing was not found in a vendor source: the one source listed for the resource (K-SSRR) describes only the first and does not mention the verb". So the page denies the fact once and shows it as checked once. This is the r3 K-SSRR finding (Issue 7), fixed only in the never reason. `free` has no `claims_unverified` field (policy_page.py:162), and NOTE_CLASSES covers `notes` and `note` but not `reason` (test_policy_guard.py:2967-2968). This is the same class as the round-2 R17 `+` Major, a claim shown as verified.
Why it matters: A reader who sees "Checked ... K-SSRR" beside "creates nothing" takes the self-review `create` as vendor-confirmed read-only. The never entry says the opposite. No copy-ready block is affected (free entries do not enter `copy_ready`, policy_page.py:911-913), so the harm is a wrong trust signal on a security page.
Suggested fix: Reword the free reason to what the code does (kubernetes.py:80-81: "treated as harmless by the start-up check; not found in a vendor source"), or add a `claims_unverified` field to `free`, show it in the page, and give it a PENDING_CLAIMS entry. Extend the note-class test to cover free `reason` text.

### [F2] Minor - the never-vs-grant cover check models `{path_prefix}` as a token with no slash, so a two-part never path over R17 is missed
Where: tools/policy_page.py:711 (`_vault_form`), :703-705 (`_vault_sample`), :730-732; GRAMMAR at :178 and ENDS_IN_SLASH at :148.
What: `{path_prefix}` becomes the literal text `path_prefix`, and the `+` after it becomes `[^/]+`. R17 therefore becomes "mount/data/path_prefix<one part>", although the real prefix ends in `/` and may hold several parts (:178). The check uses one sample path per side. I traced a never path `{mount}/data/+/+` with `read`. Its regex is `mount/data/[^/]+/[^/]+`. The R17 sample is `mount/data/path_prefixX`, which does not match. The never sample `mount/data/X/X` does not match R17's regex `mount/data/path_prefix[^/]+`. Nothing is reported, but for a real prefix `team/` the grant covers `data/team/<name>`, which that never line forbids.
Why it matters: The check exists so the page never gives and forbids the same right. A future never line shaped like that passes silently. Today's data is unaffected (test_policy_guard.py:2859 passes for all three kinds), so this is a gap in the guard, not a live wrong page.
Suggested fix: Expand `{path_prefix}` to a sample such as `px/` for the cover check, or compare per path part. Add a clean/caught pair for a two-part never path to the plant test (:2862).

### [F3] Minor - the never `type` is not tied to the platform, so a mis-typed never line is silently skipped by the cover rule
Where: tools/policy_page.py:141 (NEVER_TYPES is global), :440-441, and the branches at :721 and :734.
What: The cover rule reads only `path` entries on Vault and only `resource` entries on Kubernetes. A Vault never entry typed `resource` or `prose` with a path name, or a Kubernetes one typed `path`, passes the data rules and is rendered on the page. No test or rule looks at it.
Why it matters: Typing `{"type": "resource", "name": "{mount}/data/*"}` on the Vault kind would sidestep the cover rule. The line would look like a never rule on the page while being checked by nothing.
Suggested fix: In `_never_problems`, allow per platform: Vault `role` and `path`; Kubernetes `role`, `action` and `resource`. Add a plant.

### [F4] Nit - the note-class test "sources" class cannot fail on the one thing it is for
Where: tests/test_policy_guard.py:2990-2997, :2936-2964.
What: For class "sources" the test only checks that each listed id exists in the sources file. It does not check that the ids appear in a grant's `verified`, nor that the source says the thing. Two notes name V-TOK (:2939, :2952). No POLICY literal lists V-TOK (fixture header, policy_sources_2026-11-11.txt:47), and the page prints ids only through `verified`. So "`no_default_policy` ... `token_no_default_policy`" and "signing stores nothing" show no source id anywhere on the page.
Why it matters: The class label is chosen by a person. Mis-classing a claim as "sources" passes with any real id. The page reader cannot see which source stands behind the sentence.
Suggested fix: Print a "sources:" suffix on classed notes, or say plainly in the test header that the class is only a human label.

### [F5] Nit - two wording gaps on the page
(a) The R17 row (docs/declared-permissions.md:88) lists V-POL and B-POL under "name and form found in a vendor source" without a mark. The fixture header (policy_sources_2026-11-11.txt:29) says the `+` passage in exactly those two files was read by the builder only. The form `{path_prefix}+` is the claimed form. The adjacent "claims not checked" cell mitigates this. The page head (policy_page.py:1049-1059) names the builder-only marks only for V-ACL, V-PARSE and B-ACL.
(b) Three Kubernetes role rows (`cluster-admin`, `admin`, `edit`) show "not yet checked" (docs:181-183). The head explains that string only for the three Vault paths (:1057-1059). The reason (not among the names the evidence runner looked for) is in test_policy_guard.py:87-92 and nowhere on the page.

## Verified at the lines you named

**Builder-only marks**
- `BUILDER_ONLY_SOURCES = (V-ACL, V-PARSE, B-ACL)` at policy_page.py:922 matches the fixture header (policy_sources_2026-11-11.txt:16-17, :62-64).
- `_checked_cell` (:925-931) marks them. The page shows them marked in the R17 row only (docs:88). The test at test_policy_guard.py:1583-1594 finds any unmarked mention by regex, and the mutant at policy_mutants.py:466-473 targets that line.
- The three never paths `undelete`, `subkeys` and `byok-export` have `verified = None` (secrets_vault.py:300, :306; signer_vault.py:204). They show "not yet checked" (docs:102, :103, :144).
- r3 minor 1 (R17 cell) is closed as far as ids go; F5(a) is the leftover.

**PENDING_CLAIMS and PENDING_NAMES**
- PENDING_CLAIMS has R17, R18, R20, R21 and R22 (test_policy_guard.py:119-125). Each of those grants has a non-empty `claims_unverified`: secrets_vault.py:256, signer_vault.py:147-152, kubernetes.py:405, :419, :433. R19 has none. The set equality is pinned at :1547, :1556 and :1525-1528.
- All entries are decided 2026-11-11 with review_by 2026-12-11. That is 30 days, inside the 92-day limit (:40, :148). Today is 2026-11-11, so none is overdue. The suite goes red on 2026-12-12 (:1527), as the CHANGELOG says (:261-262).
- PENDING_NAMES has six entries (:99-106). They equal the six `verified = None` entries and nothing else (:2836).
- The r3 minors are fixed: the R18 hash-suffix claim and the Kubernetes query-parameter claim are now in `claims_unverified` and in the notes (signer_vault.py:117-121, kubernetes.py:386-392). The credential wording now matches app.py:339-340 (read in B-Q8b-base): a named secret, sent as Bearer only when `token_secret_name` is set.
- r3 minor 7 is closed except F1 (K-SSRR in the free entry).

**Generated page equals the data**
- I compared docs/declared-permissions.md with `_kind_section`, `head` and `page` section by section. It matches: the column order, R17's verified list with the marks, "No copy-ready text" for all three kinds, the 16-kind list, and ENGINE_STATE inlined three times. The `{{self.mount}}` escape renders as `{self.mount}`.
- I did not run `--check`. Byte-level equality is argued by reading, not by diff.
- No src hunk is anything but an appended POLICY literal (DIFF.patch hunks `@@ -193,3 +193,129`, `-79,3 +79,159`, `-349,3 +349,220`), so "no behaviour change" holds.

**Never-vs-grant mutants**
- Present (policy_mutants.py:416-457): capability filter, narrower, wider, Kubernetes name match, and cross-kinds call. Each names a killer plant. I traced the wider and narrower mutants against the plant cases (test_policy_guard.py:2874-2891). The first failing assertion carries the `expect` text, so they are not weak.
- No mutant for the `_vault_sample` or `_vault_form` substitution (see F2), or for the `n.type == "path"` branch (see F3). The plants cover part of that.
- The never-list literals equal `_WRITE_VERBS` and `_SHELL_RESOURCES` (8 verbs and 6 resources in kubernetes.py:36-48, against the never entries at :471-540), pinned by a test in the file. I did not read that test.

**Tests that cannot fail**
- Beyond F4, none found among those read. `same()` is a full equality. The E2 copy-ready mutant, the claim-needs-entry mutant and the mark mutant each have a plant that fails when the guard is removed.
- The state pins at :1547 and :1565-1567 and R17_CLAIM at :1546 repeat the data on purpose. They stop a silent change, not a behaviour error.

**Siblings of the claim-shown-as-verified gap**
- Kubernetes R20-R22 and Vault R18: closed. Kubernetes `create` self-review: honest text in the never entry but not in the free entry (F1).
- Vault R19 (`read` on keys): no unchecked assertion found.
- The Vault free sign-in entry carries V-API, V-APPROLE, V-K8S, B-API and its reason is plain. The never `root` and `sys/*` rows cite V-POL only. I did not open the sources.

## Checked and found fine
- Three POLICY literals exist, and `load` refuses non-literals (policy_page.py:517-552).
- Every grant has `operations`, and a request is claimed once (:509-513).
- `source_ids` rejects an unpinned row (:626) and the id list is consistent (7 short, 12 long, 19 rows).
- The CI variable is in both Vault jobs (ci.yml diff lines 9 and 23), pinned by test_policy_engine.py:86-100. The policy mutants step is in `check` only.
- The CHANGELOG matches the code on the claims, dates, "no copy-ready for any of the three kinds", and "12 Vault tests still unrun".

## Not checked
- I did not run any test, mutant or plant, nor `policy_page.py --check`.
- I did not read the call-shape tests in test_policy_guard.py (lines 230-1480), the rest of tests/test_policy_engine.py (lines 170-488), or tests/policy_mutants.py outside 395-485.
- I did not re-fetch any vendor source, so I cannot say whether V-TR actually shows the exact-path claim, whether the 7-character ids resolve, or whether the Vault `+` semantics hold.
- I did not look at the ledger rows BL-core-q8c1-lifetime and BL-core-q8c1-openbao on the snapshot; r3 recorded them at handover/ledger.md:2680-2681.
- I did not read the r3 design report.