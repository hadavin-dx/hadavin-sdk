/* Mode banner painter. Framework-free; text nodes only (no HTML is ever parsed).
   The words are written by hadavin_sdk.mode_banner (Python), the one place they live; this file only paints the ready
   banner the system sends: { mode, tone, tag, text, standins, real, stand_ins }.
   A missing, odd or self-contradicting banner is never hidden and never half painted: it paints the "not confirmed"
   line, because silence would read as "all real". Nothing in here can throw out of paint().
   Use:  HadavinModeBanner.paint(document.getElementById('mode-banner'), bannerObjectFromTheSystem);
   Copy this file into a page; do not edit the words here (a test pins the fallback to the Python text). */
(function (root) {
  'use strict';
  var TONES = Object.freeze(['demo', 'real', 'quiet', 'unconfirmed']);
  var MODES = Object.freeze(['demo', 'pilot', 'prod']); // the stages; a test pins this list to hadavin_sdk.stages.STAGES
  var MAX_TEXT = 600; // a test pins this number to hadavin_sdk.mode_banner.MAX_TEXT_LENGTH
  // the fallback when the system gave no usable banner: same words as hadavin_sdk.mode_banner.not_confirmed()
  var NOT_CONFIRMED = Object.freeze({
    mode: '', tone: 'unconfirmed', tag: 'UNCONFIRMED',
    text: 'The mode of this system could not be confirmed. Treat everything here as real.',
    standins: '', real: Object.freeze([]), stand_ins: Object.freeze([])
  });
  function isText(v) { return typeof v === 'string' && v.length > 0 && v.length <= MAX_TEXT; }
  function isTextList(v) {
    if (!Array.isArray(v)) return false;
    for (var i = 0; i < v.length; i++) if (typeof v[i] !== 'string' || v[i].length === 0) return false;
    return true;
  }
  // True when `name` is in `text` as whole words: the characters beside it are not letters or digits, so a short name
  // such as "CRM" is not found inside another word. (The names are plain words; the Python side is the real gate.)
  function hasName(text, name) {
    var at = text.indexOf(name);
    while (at >= 0) {
      var before = at === 0 ? '' : text.charAt(at - 1);
      var after = text.charAt(at + name.length);
      if (!/[A-Za-z0-9]/.test(before) && !/[A-Za-z0-9]/.test(after)) return true;
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
      if (TONES.indexOf(tone) < 0 || tone === 'unconfirmed') return NOT_CONFIRMED;
      if (!isText(tag) || !isText(text)) return NOT_CONFIRMED;
      if (standins === undefined || standins === null) standins = '';
      if (standins !== '' && !isText(standins)) return NOT_CONFIRMED;
      if (!isTextList(real) || !isTextList(standIns)) return NOT_CONFIRMED;
      real = real.slice();
      standIns = standIns.slice();
      if (MODES.indexOf(mode) < 0) return NOT_CONFIRMED;
      // the tone must agree with the mode and the real services: a mismatch is never painted as given
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
    el.textContent = '';
    for (var i = 0; i < nodes.length; i++) el.appendChild(nodes[i]);
    el.setAttribute('data-tone', b.tone);
    el.setAttribute('data-mode', b.mode);
    el.hidden = false;
  }
  // Paints the banner into `el` and returns the banner that was painted. The nodes are built BEFORE `el` is touched,
  // so a failure never leaves it empty or half old; if painting fails the "not confirmed" text is put in as plain text.
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
      try {
        el.hidden = false; // first: whatever else fails below, the element is never left hidden
        el.textContent = b.tag + ' ' + b.text;
        el.setAttribute('data-tone', b.tone);
        el.setAttribute('data-mode', '');
      } catch (e2) { /* nothing more can be done: the page itself is broken */ }
    }
    return b;
  }
  var api = Object.freeze({ paint: paint, usable: usable, NOT_CONFIRMED: NOT_CONFIRMED, TONES: TONES, MODES: MODES, MAX_TEXT: MAX_TEXT });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.HadavinModeBanner = api;
})(typeof window !== 'undefined' ? window : this);
