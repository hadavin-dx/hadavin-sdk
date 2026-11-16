# P1d plan review round 3 - zoom-out (egm-zoom-out, Sonnet), ticket rev 3 (condensed by the cloud session)
Verdict: idea right and small; size too big. 0 Blockers, 6 Majors, 8 Nits. Reviewer read only the ticket, siblings note and template (source not on this branch, reuse claims unchecked).
Major:
- M1 Interface/constants: P1D_WITHHOLD_ALERT_PER_MIN (cut: log line already a flood signal); P1D_MAX_VIEWS redundant with a fixed pipeline (assert constant length instead; rows X03/X04); reason=clock + deadline duplicates the size cap; pass source/approval_id via logger context, not signature. Keep P1D_MAX_TEXT_CHARS and P1D_MIN_KEY_CHARS.
- M2 Squeezed/case-folded learning is the biggest false-withhold risk: make it ship only if BS-2 shows 0 false learns; say so in Behaviour/Interface; rows/mutants M11-M13 depend on it.
- M3 Operator route: approve-path re-check and display_withheld are an approvals-state feature; ORDER 165 only needs terminal state, log line, visible reason. Recommend card posted without buttons + log + expire/deny; one negative test; approve-path closure as its own ticket line if the lead wants it. (CONFLICTS with ORDER 166 item 3 reading "existing route"; the existing deny/expire is kept either way - decision needed on the approve-path re-check.)
- M4 30 mutants too many; keep ~12-14 for mechanisms (M1, M3-M9, M11, M12, M15, M17, M18, M21, M27); turn M2, M22-M26, M29, M16, M10 into plain tests; decide M14 now.
- M5 Put-back count test copied from lookalike-leak section 5 couples P1d to unmerged P2d-2; justify why the dropped-form deleting-view rule alone is not enough, or defer put-back to P2d-2.
- M6 BS gates: BS-4 fallback branch speculative; BS-5 (markdown-it-py) already CUT in rung table - delete; share one corpus tool for BS-1/BS-3.
Nit: N1 header history to revision log; N2 consider split P1d-core / P1d-cards; N3 vocabulary heavy; N4 merge rung rows; N5 drop F18 (sensitive() is P1d-b); N6 trim boundary rows; N7 H34/F16 duplicate; N8 open questions 3 and 5 already answered.
Missing: no go/no-go number for typical document size vs cap (V9: ~7x slower at 30,000 chars; cap may withhold normal documents, conflicts with R4).
Suggested cut: ~20-25 percent of surface.
