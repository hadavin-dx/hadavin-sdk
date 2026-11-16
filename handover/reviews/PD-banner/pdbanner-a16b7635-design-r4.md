# pdbanner-a16b7635-design-r4: Part 6 (mode banner, demo-only guard), head a16b7635, round 4, persona design

Source: hand-back of agent a164e5cb3c89c9085, saved by the lead (condensed). Static read of snapshot `/home/user/build/snap/pdbanner-a16b7635`; no code run. 0 Blocker, 2 Major, 11 Minor, 8 Nit. Not clean.

## Major
- **M1** tool_specs can still fail open (mode_banner.py:351-365, :398). `getattr(spec,"hosts",None) or ()` reads a spec without `hosts` as no hosts; `tool_specs={}` with `tool_modules` set is read as nothing real; only `None` means cannot say; parameter typed `object`; non-mapping inner value raises AttributeError (B34 pins that accident). Fix: require `hosts` (tuple/list of str) or raise; empty specs with non-empty tool_modules gives TOOL_MODULES; type as Mapping[str, Mapping[str, ToolSpec]] | None; mutant on the getattr default.
- **M2** URL parity with the tool client is a claim, not a pinned property (mode_banner.py:298-311, CHANGELOG:214). Tests do not import tools.py; LEAVING_URLS hand-written; test pins identity with guard.http.LOOPBACK only, not contents. `http://[::1]evil.example/` and `http://[::1]:80x/` not in LEAVING_URLS. Fix: assert LOOPBACK contents; parity test feeding LEAVING_URLS to the fetcher's validator; reject text after `]` other than `:port` or `/?#`; or soften wording to "modelled on".

## Minor
- m1 "A banner is always shown" stronger than code: banner_from_config raises; add `banner_or_unconfirmed` catching Exception, or state the caller's duty.
- m2 limits list incomplete: app.build overrides (tools=, sources=, channel=, llm=, detector=, secrets=), localhost trusted to resolve to loopback, page cache, config reloads, stand-in kind settings not inspected.
- m3 URLs require ASCII but hosts go through NFKC: full-width localhost counts as this machine in egress list, as leaving in a URL; add a row stating the decision.
- m4 BannerWords rewording limited to English and ASCII (_NAME_OK, fixed _NAME_RESERVED); derive reserved set from words or name the lock-in.
- m5 JS last-resort write overstated: if fill cleared the element and appendChild throws, fallback failure leaves it empty; if setAttribute('data-tone') throws after text written, old tone stays. Reword; write tone before text.
- m6 page script does not guard the made-up sentence in quiet/real banners: state the page trusts the tone, or pin a banned-phrase check.
- m7 demo_only_guard.py:273-280 `except OSError: continue` reads an unreadable file as clean; emit `unreadable-file` hit.
- m8 archives/compiled files refused by extension only; renamed zip/.so/.pyc as .png bypasses; check magic bytes or name the limit.
- m9 guard limits incomplete: compile-time spellings, NFKC not searched in binaries, UTF-32, fake_id_patterns not on binary/UTF-16, no size cap.
- m10 hits print unsanitised paths (newline, ANSI, leading `::` workflow commands); escape control characters.
- m11 about 40 of 130 mutants use a loose expect="assert" fragment (B6, B7b, B8, B9, B10*, G1, G2, J2-J9, B23); missing mutants: _field type check, getattr default, names_in(""), egress `not`, `at >= 2`, setAttribute order.

## Nit
n1 duplicate labels J11, J12 (banner_mutants.py:367/691, 374/698); n2 stale first sentence in CHANGELOG guard entry; n3 whole-word test matches all banner.text, check the formatted names segment; n4 fallback `component tool-hosts` does not name the host; n5 load-time import of guard.http/guard.egress not pinned; n6 `--without-folder` passes full environ and copies .env; n7 demo_only_guard.py:300 `d in loaders` no-op for file loaders; n8 CHANGELOG "exactly the way the tool client does" has no test.

## Settled round-3 classes still fixed
A tool_specs required and tool hosts counted; B plain text before clearing; C guard hardening (NFKC, binary search UTF-8/16, NUL, gitlinks, refused suffixes); D URL/source/name parity (shared LOOPBACK and normalise_host, source_endpoint shared, JS and Python name rule equal).

## Not checked
tools.py, guard/egress.normalise_host, guard/http.LOOPBACK, backends/table.py, Config model, ToolSpec, Registry (not in snapshot); any in-repo caller wiring banner_from_config; test bodies beyond round-4 part; no node/pytest/mutants run; CPython urlsplit differences; browser behaviour.
