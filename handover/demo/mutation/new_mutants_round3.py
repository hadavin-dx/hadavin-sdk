D = "src/lead_desk/desk.py"
C = "src/lead_desk/constants.py"
S = "src/lead_desk/server.py"
G = "src/lead_desk/gate.py"
# ports of round-2 mutants whose text changed in A4r7: (old round-2 number, file, old, new, label, class)
PORTS = {
 22: (D, "return int(self.config.send_timeout_seconds + SENDING_GRACE_BUSY_WAITS * BUSY_WAIT_SECONDS)", "return int(self.config.send_timeout_seconds + 0 * BUSY_WAIT_SECONDS)", "reaper stuck-sending grace dropped (ported: now the stuck_grace_seconds property)", "reaper"),
 23: (D, "if updated_at + wait_before_drive(int(tries), last_error) <= now:", "if updated_at + wait_before_drive(int(tries), last_error) < now:", "reaper due-time boundary <= -> < (ported)", "boundary"),
 24: (G, "return PENDING_GRACE_SECONDS if auto_attempts == 0 else backoff_after(auto_attempts)", "return PENDING_GRACE_SECONDS if auto_attempts <= 1 else backoff_after(auto_attempts)", "reaper backoff skipped after first retry (ported: now gate.wait_before_drive)", "reaper"),
 35: (D, "return bool(row[1] == 0 or row[2] + wait_before_drive(int(row[1]), row[3]) <= self._now())", "return bool(row[1] == 0 or row[2] + wait_before_drive(int(row[1]), row[3]) < self._now())", "replay due-time boundary <= -> < (ported)", "boundary"),
}
# round-2 mutants with no equivalent line in A4r7: number -> reason
NOT_APPLICABLE = {
 20: "Old pristine text `updated_at <= ?` is now `updated_at < ?` (S1h made the boundary strict). The old mutant's new text (`updated_at < ?`) IS the A4r7 pristine text, so applying it changes nothing. Its reverse (`<=`) is new mutant N2.",
 41: "Old text `... AND attempts=? AND send_started=0` (give-back guarded by send_started=0) no longer exists: `_give_back` now SETS `send_started=0` in the UPDATE and is guarded only by `state='sending' AND lead_id=? AND attempts=?`. Nearest new mutants: N10, N12.",
 47: "`defer_pending` (cap boundary `auto_attempts+1 >= ?`) no longer exists in A4r7; it was replaced by `_give_back` (`auto_attempts=MAX(auto_attempts-1, 0)`). Nearest new mutants: N11.",
 79: "E12 old text `WHERE lead_id=? AND state='pending' AND auto_attempts=?` (defer_pending's guard) no longer exists; `_give_back` guards with `state='sending' AND lead_id=? AND attempts=?`. Nearest new mutant: N10.",
}
NEW = [
 ("N1", D, "\"SELECT count(*) FROM followups WHERE state='sending' AND updated_at < ?\"", "\"SELECT count(*) FROM followups WHERE state='sending' AND updated_at <= ?\"", "reaper count query strict boundary < -> <=", "S1h-boundary"),
 ("N2", D, "WHERE state='sending' AND (? IS NULL OR updated_at < ?)\"", "WHERE state='sending' AND (? IS NULL OR updated_at <= ?)\"", "_requeue_sending strict boundary < -> <=", "S1h-boundary"),
 ("N3", C, "if budget + margin >= grace_floor:", "if budget + margin > grace_floor:", "validate_model_budget budget+margin >= -> >", "S1g-budget"),
 ("N4", C, "if write_deadline + busy_wait >= grace_floor:", "if write_deadline + busy_wait > grace_floor:", "validate_model_budget write_deadline+busy_wait >= -> >", "S1g-budget"),
 ("N5", D, "and declared >= self.stuck_grace_seconds - MODEL_GRACE_MARGIN_SECONDS", "and declared > self.stuck_grace_seconds - MODEL_GRACE_MARGIN_SECONDS", "DeskSettingRefused adapter limit >= -> >", "S1g-budget"),
 ("N6", D, "\" AND state='sending' AND attempts=?\",\n                        (label, lead_id, token),", "\" AND attempts=?\",\n                        (label, lead_id, token),", "label write guard drops state='sending'", "S1h-label-guard"),
 ("N7", D, "\" AND state='sending' AND attempts=?\",\n                        (label, lead_id, token),", "\" AND state='sending' AND attempts>=?\",\n                        (label, lead_id, token),", "label write guard token = -> >=", "S1h-label-guard"),
 ("N8", D, "if not stored[1]:  # the row was put back or claimed again meanwhile: the write above changed nothing", "if False:  # the row was put back or claimed again meanwhile: the write above changed nothing", "re-read after the label write: ownership check skipped", "S1h-label-guard"),
 ("N9", D, "label = stored[0]\n            if label not in AI_LABELS:", "pass\n            if label not in AI_LABELS:", "re-read after the label write: stored (first-wins) label not used", "S1h-label-guard"),
 ("N10", D, "\" WHERE state='sending' AND lead_id=? AND attempts=?\",\n                    (last_error, last_error, NO_DESCRIPTORS_ERROR", "\" WHERE state='sending' AND lead_id=? AND attempts>=?\",\n                    (last_error, last_error, NO_DESCRIPTORS_ERROR", "_give_back token guard = -> >=", "S1i-give-back"),
 ("N11", D, "auto_attempts=MAX(auto_attempts-1, 0), send_started=0,", "auto_attempts=auto_attempts, send_started=0,", "_give_back no longer returns the automatic try", "S1i-give-back"),
 ("N12", D, "auto_attempts=MAX(auto_attempts-1, 0), send_started=0,", "auto_attempts=MAX(auto_attempts-1, 0), send_started=send_started,", "_give_back no longer clears send_started", "S1i-give-back"),
 ("N13", D, "WHEN last_error=? THEN NULL ELSE last_error END", "WHEN last_error=? THEN last_error ELSE last_error END", "_give_back keeps a stale no_descriptors last_error", "S1i-give-back"),
 ("N14", D, "raise SendUnreachable(\"crm capability read\")", "raise SendNoDescriptors(\"crm capability read\")", "crm_done=2 with CRM down: gives the try back instead of using one", "S1i-crm-down"),
 ("N15", D, "if getattr(self._local, \"crm_refresh_failed\", False):", "if False:", "crm_done=2 with CRM down: path never taken", "S1i-crm-down"),
 ("N16", D, "log.warning(\"sending row not refreshed: database stayed locked\")\n            raise", "log.warning(\"sending row not refreshed: database stayed locked\")\n            return False", "_touch swallows a busy database (returns False, not raise)", "S1i-touch"),
 ("N17", D, "self._give_back(lead_id, token, NO_DESCRIPTORS_ERROR if is_fd_exhaustion(exc) else None)", "self._give_back(lead_id, token, None)", "EMFILE give-back no longer marks no_descriptors", "S1i-emfile"),
 ("N18", D, "if not (db.is_busy(exc) or is_fd_exhaustion(exc)):", "if not db.is_busy(exc):", "EMFILE before the send is counted as a used try, not given back", "S1i-emfile"),
 ("N19", S, "            try:\n                server.server_close()\n            finally:\n                try:\n                    desk.close()\n                finally:\n                    lock.close()", "            server.server_close()\n            desk.close()\n            lock.close()", "server.main nested finally chain flattened", "S1i-finally"),
 ("N20", S, "need = FDS_PER_HANDLER_THREAD * max_threads + FD_RESERVE", "need = FDS_PER_HANDLER_THREAD * max_threads", "descriptor arithmetic: reserve left out of need", "S1i-descriptors"),
 ("N21", S, "fits = max((ceiling - FD_RESERVE) // FDS_PER_HANDLER_THREAD, 0)", "fits = max(ceiling // FDS_PER_HANDLER_THREAD, 0)", "descriptor arithmetic: reserve left out of advice (fits)", "S1i-descriptors"),
 ("N22", S, "if soft == res.RLIM_INFINITY or soft >= need:", "if soft == res.RLIM_INFINITY or soft > need:", "ensure_descriptor_budget soft >= need -> >", "S1i-descriptors"),
 ("N23", S, "validate_descriptor_budget(FDS_PER_HANDLER_THREAD, FD_RESERVE, FD_RESERVE_ITEMS, PORTAL_MAX_INFLIGHT)\n    res = resource if res is None else res", "res = resource if res is None else res", "ensure_descriptor_budget no longer re-validates the constants", "S1i-descriptors"),
]
