/* ShipSealed — Paddle Billing checkout.
 *
 * DORMANT BY DESIGN. While PADDLE.token is empty this file does nothing: the
 * plan buttons keep their current behavior (they link to the waitlist at /#list).
 * Nothing loads, nothing changes.
 *
 * GO-LIVE (once Paddle verification is approved): fill in the three things below,
 * commit, push. The checkout turns on. No other file needs to change.
 *   1) PADDLE.token       — Paddle > Developer tools > Authentication > Client-side token
 *                           (starts with "live_"; for testing, a "test_" token + environment:'sandbox').
 *                           This is a PUBLIC token — safe to ship in the browser.
 *   2) PADDLE.priceIds    — the production price IDs, by plan and seat index (0 = 1 dev … 4 = 5–8 devs).
 *                           Produce them by running paddle/criar-catalogo.mjs against production,
 *                           then copy the ids out of paddle/paddle-ids.json.
 *   3) PADDLE.environment — flip to 'production' (leave 'sandbox' only while testing).
 */
window.PADDLE = {
  environment: 'sandbox',        // 'production' when live
  token: '',                     // '' = dormant. Fill with the client-side token to arm checkout.
  // Production price IDs, seat index 0..4 (1 dev, 2, 3, 4, 5–8 devs). Order matches the seat buttons.
  priceIds: {
    base: ['', '', '', '', ''],
    pro:  ['', '', '', '', ''],
  },
};

(function () {
  var P = window.PADDLE || {};

  // DORMANT: no token → leave every button exactly as it is (waitlist links).
  if (!P.token || !/\S/.test(P.token)) return;

  var s = document.createElement('script');
  s.src = 'https://cdn.paddle.com/paddle/v2/paddle.js';
  s.async = true;
  s.onload = function () {
    try {
      if (P.environment === 'sandbox' && window.Paddle) Paddle.Environment.set('sandbox');
      Paddle.Initialize({ token: P.token });
      wire();
    } catch (e) { /* if Paddle fails to init, buttons fall back to their href */ }
  };
  document.head.appendChild(s);

  // Which seat tier is selected right now (0..4). Mirrors the seat selector on the pricing page.
  function currentSeat() {
    var active = document.querySelector('.seat-btn.active');
    var i = active ? parseInt(active.getAttribute('data-i'), 10) : 0;
    return isNaN(i) ? 0 : i;
  }

  function wire() {
    var buttons = document.querySelectorAll('[data-paddle-plan]');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener('click', function (e) {
        var plan = this.getAttribute('data-paddle-plan');
        var ids = (P.priceIds && P.priceIds[plan]) || [];
        var priceId = ids[currentSeat()];
        if (!priceId) return;              // no id for this tier → let the link fall through to the waitlist
        e.preventDefault();
        Paddle.Checkout.open({ items: [{ priceId: priceId, quantity: 1 }] });
      });
    }
  }
})();
