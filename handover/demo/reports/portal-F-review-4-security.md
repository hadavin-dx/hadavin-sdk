# WP-F round 4 security review (head 77e27d1), saved by the cloud session
Reviewer: egm-design (fresh, read-only, snapshot only; ran nothing; could not see desk source, Config or WP-A).
Verdict: no Blocker, no Major in WP-F, 4+ Nits. All five round-3 items fixed in code. New tests: 4 scheme tests are real proof; budget and sweep tests fail on old code with AttributeError (constants missing), logic would also fail behaviourally.
Checked without real finding: desk_url scheme bypass (case, whitespace, userinfo, redirects, other handlers); burst budget (lock, off-by-one, refused burst sends nothing); stale .crash-*.tmp sweep (non-recursive, no symlink/dir/traversal, no race with live mkstemp); skipped gate tests claim nothing false.
Nits:
1. :177,:313,:220-231 _fetch_json uses cfg.fakes_url with no scheme check; wired checks hostname only; the all-protocol opener would open file:/ftp:/data: if operator Config said so. Fix: http-only rule in _adapter_points_at (or opener without File/FTP/Data handlers).
2. :254-255 no port check on desk_url (operator-set only).
3. Budget is per PortalDemo instance, not per process (wording); budget counts slots not POSTs; page/UI must handle 429 burst_budget_used (WP-A/G).
4. Sweep test lacks symlink and directory cases.
5. importorskip(...) skips on any ImportError and can turn ~120 tests into one green SKIP. Fix: exc_type=ModuleNotFoundError and re-raise unless e.name starts with demo_only, or skip only when demo_only/ dir is absent.
6. Skipped WP-A gate tests look like coverage; use xfail(strict) or a MERGE-BLOCKER marker. Round-3 Major (Origin/Content-Type) stays an open WP-A/WP-G gate.
Evidence: full run c77e27d1 8 failed = baseline names; HYGIENE_WORDLIST not run (lead).
