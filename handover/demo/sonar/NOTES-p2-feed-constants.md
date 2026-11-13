# NOTES p2-feed-constants (contingent delta; NOT pushed)
Patch: sonar/sonar-p2-feed-constants-delta.patch, base pr-3-tests 3598120. Use only if pythonsecurity:S8703 (scripts/feed.py:50) is still open after the head is analysed.
Live Sonar API at 07:45Z still shows the PRE-push flow (updateDate 2026-11-12 19:48Z): source feed.py:67 parse_args -> args.url (L73) -> sink L49/L50; the head 3598120 has not been analysed yet.
Change: scripts/feed.py `desk_url(bind, port)`: host = the ELEMENT of LOOPBACK_HOSTS ("127.0.0.1","[::1]","localhost") equal to the configured bind (wildcards mapped by target_host as before); port int, 1..65535; URL = desk_origin(chosen, int) + constant "/leads"; main() turns ValueError into ap.error (exit 2, message). build_envelope picks `source` as the element of SOURCES equal to the argument; source_ref uses int(index). Tests: tests/test_sonar_p2_feed_constants.py (new), one assertion in test_sonar_p2_feed_optional.py (desk.example -> localhost, because non-loopback is now refused).
## Behaviour differences (old measured on 3598120, evidence-2): old refused NOTHING
- 127.0.0.2, LAN IP, hostnames (desk.example), "0", ::ffff:127.0.0.1, "x@evil" shapes: old built the URL as is; NEW refused (exit 2). A desk bound to a LAN address/Docker name (docs/settings.md) can no longer be fed by feed.py: DECISION for the lead.
- LocalHost -> localhost (lowercase). Port 0 and >65535/negative: old built the URL; new refused.
- Unchanged: default, localhost, ::1, long IPv6 form, 0.0.0.0/::/[::] mapped to 127.0.0.1 / [::1], ports 1..65535.
## Sonar judgement (not measured)
Host now comes only from constants by equality (the measured law of PROBE-V3-MAPPING), port is an int, scheme/path constants: the URL carries no tainted string. Residual: --source/--index reach only the JSON body (data=), now also chosen from SOURCES / int; env config is a possible source, but only an int and a selected constant reach the sink. Odds to clear: ~75% (up from ~65%).
## Rung table: CUT-TO-CONFIG not possible (a guard in our own 10 lines; no library covers it) | verdict KEEP-CODE, contingent.
