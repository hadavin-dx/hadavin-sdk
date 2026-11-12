/* Mode banner painter. Framework-free; text nodes only (no HTML is ever parsed).
   The words are written by hadavin_sdk.mode_banner (Python), the one place they live; this file only paints the ready
   banner the system sends: { mode, tone, tag, text, standins, real, stand_ins }.
   A missing or odd banner is never hidden: it paints the "not confirmed" line, because silence would read as "all real".
   Use:  HadavinModeBanner.paint(document.getElementById('mode-banner'), bannerObjectFromTheSystem);
   Copy this file into a page; do not edit the words here (a test pins the fallback to the Python text). */
(function (root) {
  'use strict';
  var TONES = ['demo', 'real', 'quiet', 'unconfirmed'];
  // the fallback when the system gave no usable banner: same words as hadavin_sdk.mode_banner.not_confirmed()
  var NOT_CONFIRMED = {
    mode: '', tone: 'unconfirmed', tag: 'UNCONFIRMED',
    text: 'The mode of this system could not be confirmed. Treat everything here as real until it is.',
    standins: '', real: [], stand_ins: []
  };
  function isText(v) { return typeof v === 'string' && v.length > 0 && v.length <= 600; }
  // returns the banner to paint: the given one when it is complete, else the fallback (never null, never hidden)
  function usable(b) {
    if (b === null || typeof b !== 'object' || Array.isArray(b)) return NOT_CONFIRMED;
    if (TONES.indexOf(b.tone) < 0 || !isText(b.tag) || !isText(b.text)) return NOT_CONFIRMED;
    if (b.standins !== undefined && b.standins !== '' && !isText(b.standins)) return NOT_CONFIRMED;
    return b;
  }
  function node(doc, tag, cls, text) {
    var n = doc.createElement(tag);
    n.className = cls;
    n.textContent = text;
    return n;
  }
  function paint(el, banner, doc) {
    doc = doc || root.document;
    var b = usable(banner);
    el.textContent = '';
    el.appendChild(node(doc, 'span', 'mode-banner__tag', b.tag));
    el.appendChild(node(doc, 'span', 'mode-banner__text', ' ' + b.text));
    if (isText(b.standins)) el.appendChild(node(doc, 'div', 'mode-banner__standins', b.standins));
    el.setAttribute('data-tone', b.tone);
    el.setAttribute('data-mode', typeof b.mode === 'string' ? b.mode : '');
    el.hidden = false;
    return b;
  }
  var api = { paint: paint, usable: usable, NOT_CONFIRMED: NOT_CONFIRMED, TONES: TONES };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.HadavinModeBanner = api;
})(typeof window !== 'undefined' ? window : this);
