/* Mode banner painter. Framework-free; text nodes only (no HTML is ever parsed).
   The words are written by hadavin_sdk.mode_banner (Python), the one place they live; this file only paints the ready
   banner the system sends: { mode, tone, tag, text, standins, real, stand_ins }.
   A missing, odd or self-contradicting banner is never hidden and never half painted: it paints the "not confirmed"
   line, because silence would read as "all real". Nothing in here can throw out of paint().
   The page trusts the `tone` it is given as far as it can check it (against the mode, the real list and the names); the
   made-up sentences themselves are checked in Python before a banner is sent (hadavin_sdk.mode_banner), not here.
   Use:  HadavinModeBanner.paint(document.getElementById('mode-banner'), bannerObjectFromTheSystem);
   Copy this file into a page; do not edit the words here (a test pins the fallback to the Python text). */
(function (root) {
  'use strict';
  var TONES = Object.freeze(['demo', 'real', 'quiet', 'unconfirmed']);
  var MODES = Object.freeze(['demo', 'pilot', 'prod']); // the stages; a test pins this list to hadavin_sdk.stages.STAGES
  var MAX_TEXT = 600; // characters (code points, as Python counts them); a test pins this number to hadavin_sdk.mode_banner.MAX_TEXT_LENGTH
  // the fallback when the system gave no usable banner: same words as hadavin_sdk.mode_banner.not_confirmed()
  var NOT_CONFIRMED = Object.freeze({
    mode: '', tone: 'unconfirmed', tag: 'UNCONFIRMED',
    text: 'The mode of this system could not be confirmed. Treat everything here as real.',
    standins: '', real: Object.freeze([]), stand_ins: Object.freeze([])
  });
  // text the page may show: a string with something visible in it (not only white space) of at most MAX_TEXT characters,
  // counted in code points like Python does (Array.from), not in UTF-16 units
  function isText(v) { return typeof v === 'string' && v.trim().length > 0 && Array.from(v).length <= MAX_TEXT; }
  function isTextList(v) {
    if (!Array.isArray(v)) return false;
    for (var i = 0; i < v.length; i++) if (typeof v[i] !== 'string' || v[i].length === 0) return false;
    return true;
  }
  // True when `name` is in `text` as a whole name (the same rule as hadavin_sdk.mode_banner.names_in, which a test runs
  // against this function on one table): a neighbouring letter, digit, "_" or "-" makes it part of a longer word, and so
  // does a "." with a letter or digit beyond it ("CRM.v2", "x.CRM"); a sentence-ending "." does not.
  function isWordPart(c) { return c !== '' && /[A-Za-z0-9_-]/.test(c); }
  function isAlnum(c) { return c !== '' && /[A-Za-z0-9]/.test(c); }
  function hasName(text, name) {
    if (name === '') return false;
    var at = text.indexOf(name);
    while (at >= 0) {
      var end = at + name.length;
      var before = at === 0 ? '' : text.charAt(at - 1);
      var after = text.charAt(end);
      var joinedBefore = isWordPart(before) || (before === '.' && isAlnum(at >= 2 ? text.charAt(at - 2) : ''));
      var joinedAfter = isWordPart(after) || (after === '.' && isAlnum(text.charAt(end + 1)));
      if (!joinedBefore && !joinedAfter) return true;
      at = text.indexOf(name, at + 1);
    }
    return false;
  }
  // The banner to paint: a plain copy of the given one when it is complete and consistent, else the fallback (never
  // null, never hidden, never throws). Every field is read once; a getter or Proxy that throws gives the fallback.
  function usable(b) {
    try {
      if (b === null || typeof b !== 'object' || Array.isArray(b)) return NOT_CONFIRMED;
      var mode = b.mode, tone = b.tone, tag = b.tag, text = b.text, standins = b.standins;
      var real = b.real, standIns = b.stand_ins;
      if (TONES.indexOf(tone) < 0) return NOT_CONFIRMED;
      if (!isText(tag) || !isText(text)) return NOT_CONFIRMED;
      if (standins === undefined || standins === null) standins = '';
      if (standins !== '' && !isText(standins)) return NOT_CONFIRMED;
      if (!isTextList(real) || !isTextList(standIns)) return NOT_CONFIRMED;
      real = real.slice();
      standIns = standIns.slice();
      if (MODES.indexOf(mode) < 0) return NOT_CONFIRMED;
      // the tone must agree with the mode and the real services: a mismatch is never painted as given
      // an "unconfirmed" banner is painted as given only when it is the system's own not-confirmed words, then the note of
      // which parts were supplied by code (hadavin_sdk.mode_banner, `overridden`); any other text under that tone is not
      if (tone === 'unconfirmed' && (tag !== NOT_CONFIRMED.tag || text.indexOf(NOT_CONFIRMED.text) !== 0 ||
          real.length !== 0 || standins !== '')) return NOT_CONFIRMED;
      if (tone === 'demo' && (mode !== 'demo' || real.length !== 0)) return NOT_CONFIRMED;
      if (tone === 'quiet' && (mode === 'demo' || real.length !== 0)) return NOT_CONFIRMED;
      if (tone === 'real') {
        if (real.length === 0) return NOT_CONFIRMED;
        for (var i = 0; i < real.length; i++) if (!hasName(text, real[i])) return NOT_CONFIRMED;
      }
      return { mode: mode, tone: tone, tag: tag, text: text, standins: standins, real: real, stand_ins: standIns };
    } catch (e) {
      return NOT_CONFIRMED;
    }
  }
  function node(doc, tag, cls, text) {
    var n = doc.createElement(tag);
    n.className = cls;
    n.textContent = text;
    return n;
  }
  function build(doc, b) {
    var nodes = [
      node(doc, 'span', 'mode-banner__tag', b.tag),
      node(doc, 'span', 'mode-banner__text', ' ' + b.text)
    ];
    if (b.standins !== '') nodes.push(node(doc, 'div', 'mode-banner__standins', b.standins));
    return nodes;
  }
  function fill(el, b, nodes) {
    // The tone goes in first, then the words as plain text, then the element is cleared and filled. Any failure is
    // caught by paint, which clears the element and writes the "not confirmed" words (see below).
    el.setAttribute('data-tone', b.tone);
    el.textContent = b.tag + ' ' + b.text;
    el.textContent = '';
    for (var i = 0; i < nodes.length; i++) el.appendChild(nodes[i]);
    el.setAttribute('data-mode', b.mode);
    el.hidden = false;
  }
  // Paints the banner into `el` and returns the banner that was painted. The nodes are built BEFORE `el` is touched.
  // If painting fails, the element is repaired in this order, each step on its own so that one failing write cannot
  // skip the rest: unhidden, emptied (so the words of an earlier or half written banner, which may claim made-up data,
  // are gone first), data-mode cleared, the "not confirmed" tone written, then its words as plain text. If the word write
  // fails the element is left empty (nothing is shown, never the old claim); if the clearing write fails, the earlier
  // content may remain (nothing more can be done from inside a broken page).
  function paint(el, banner, doc) {
    var b = NOT_CONFIRMED;
    var nodes = null;
    try {
      doc = doc || root.document;
      b = usable(banner);
      nodes = build(doc, b);
    } catch (e) {
      b = NOT_CONFIRMED;
      nodes = null;
    }
    if (el === null || el === undefined) return b;
    try {
      if (nodes === null) throw new Error('no nodes');
      fill(el, b, nodes);
    } catch (e) {
      b = NOT_CONFIRMED;
      var repair = [
        function () { el.hidden = false; },
        function () { el.textContent = ''; },
        function () { el.setAttribute('data-mode', ''); },
        function () { el.setAttribute('data-tone', b.tone); },
        function () { el.textContent = b.tag + ' ' + b.text; }
      ];
      for (var r = 0; r < repair.length; r++) {
        try { repair[r](); } catch (e2) { /* the next step still runs */ }
      }
    }
    return b;
  }
  var api = Object.freeze({ paint: paint, usable: usable, NOT_CONFIRMED: NOT_CONFIRMED, TONES: TONES, MODES: MODES, MAX_TEXT: MAX_TEXT });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.HadavinModeBanner = api;
})(typeof window !== 'undefined' ? window : this);
