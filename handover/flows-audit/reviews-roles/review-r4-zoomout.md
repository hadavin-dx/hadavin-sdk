# ROLES-PROPOSAL.md zoom-out / necessity review (egm-zoom-out, fresh), saved condensed by flows-audit main session.
Verdict: sound as a client-build hardening design; wrong size and wrong place for a take due Wed 18 Nov.
1 Blocker: serves none of the three ORDER 017 purposes; recommend move out of take-critical path, label 'CLIENT-BUILD / AFTER VIDEO', keep out of the board's before-the-video count.
2 Major: 'never run' contradicted by its form (three runnable-looking SQL parts, untested, one document); do not split into runnable files now; keep out of handover/demo and any path take scripts read; 'DO NOT RUN' header.
3 Major: owner cannot decide from 431 lines and 5 asks (ask 3 mixes three questions; ask 4 depends on unrun tests); cut the owner page to two lines; move sections 4-10 to an appendix.
4 Major: size of change vs need (four logins plus table owner, four credentials, 8 file edits, builder change, re-import: SUB_WORKFLOW_ID changes, credentials bound by id, hard-kill connection exhaustion, silent expiry of mf_alert); for the take state 'one shared login, made-up data, accepted'.
5 Major: add Option A0 'one restricted login' (remove superuser/ownership, revoke PUBLIC, column grants only) as first choice; four logins as client-build default (options-first rule).
6 Major: tests heavy, all unverified, need a throwaway Postgres competing for CPU; cloud has no Postgres; cut to positive control, SELECT * denied, DELETE denied, FW1-FW14.
7 Major: group L (read-only look: superuser? pg_hba trust?) is low risk and valuable; owner may run only group L before the video; changes nothing; needs admin rights.
8 Nit: section 0 defines about 30 terms; replace by six-line owner glossary. 9 Nit: v4 after 3 review rounds; stop reviewing, record 'parked'. 10 Nit: film vs real folder sameness not re-compared; let claims table verify once.
