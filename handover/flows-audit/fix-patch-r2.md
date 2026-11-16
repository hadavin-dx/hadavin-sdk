# Fix log: F-002 patch, review round r2 (2026-11-16; static, nothing ran in n8n)
Unfixed / open first:
1. Major 1 NOT changed: always=False on Claim stays. Repeat-key reply depends on the Postgres node emitting an item for a no-row INSERT (UNVERIFIED; builder comment line 114 says it does). Written in the patch comment and as a T19 line; settled only by running T19. Owner of next step: laptop run of T19.
2. Nit 5 ({1,64} inside {{ }}) and Nit 6 (F-008 sub-workflow saving) not touched (not asked): UNVERIFIED.
3. Array/number lead_key pass the shape check after String(): documented in the note, not rejected.
Done: Major 2 (.first()), Nit 3 (A-Z, a-z in comment and reply text), Nit 4 (hostile inputs in REGENERATED-NOTE).
Reviewer claims checked: Major 1 and 2 match the patch and builder; Major 1 reasoning is right about the dependency but the alternative cannot be judged from files.
Commands: sh handover/flows-audit/tools/check_patches.sh -> PASS 4 patches; git apply --check F-002 -> ok; git apply F-002 then --check F-008 -> ok; python3 ast.parse of result -> syntax ok (temp copy only). Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-patch2/
