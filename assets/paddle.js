/* ShipSealed — Paddle Billing checkout.
 *
 * LIVE. The token below is a production client-side token and this store takes
 * real money: clicking any [data-paddle-plan] element opens the Paddle overlay.
 *
 * The href on those elements is a FALLBACK, not the real destination. Every buy
 * link points at /checkout/?plan=<plan>, a rescue page that explains the overlay
 * was blocked and offers a direct link by email. With JavaScript alive the click
 * is preventDefault()ed and the href is never followed — so judge this by
 * CLICKING, not by reading the markup. (Reading it wrong has cost us a session.)
 *
 * Base and Pro are seat arrays indexed 0 = 1 dev … 4 = 5–8 devs, chosen from
 * whichever .seat-btn carries .active at click time. Add-ons are a flat string.
 * The seat selector and any price label near a buy button must stay in sync, or
 * the page advertises one price and charges another.
 *
 * The public token is safe in the browser. Price IDs come from
 * paddle/criar-catalogo.mjs; the ids live in paddle/paddle-ids.json.
 */
window.PADDLE = {
  environment: 'production',
  token: 'live_d70c26e0d9ecf79a9b177a12ce9',
  // Production price IDs, seat index 0..4 (1 dev, 2, 3, 4, 5–8 devs). Order matches the seat buttons.
  priceIds: {
    base: [
      'pri_01kxgz2rphzs70p4ptv6gxreg2', // 1 dev  — $119.99
      'pri_01kxgz2rwn40gyq3nknzh5a0m2', // 2 devs — $199.99
      'pri_01kxgz2s2p095w5hwyarrrjvz9', // 3 devs — $279.99
      'pri_01kxgz2s8fev99fxbb0kgjxeqk', // 4 devs — $349.99
      'pri_01kxgz2seb7wwe1z6qxpqnm442', // 5–8 devs — $399.99
    ],
    pro: [
      'pri_01kxgz2t18dvwtgsj062mpsahs', // 1 dev  — $179.99
      'pri_01kxgz2t7enx3p4mah32feqwf4', // 2 devs — $249.99
      'pri_01kxgz2td61cq616rsn6bxrsc6', // 3 devs — $329.99
      'pri_01kxgz2tkgwafp434qzzq9ja3a', // 4 devs — $399.99
      'pri_01kxgz2ts97sfdh5jfgrsbkwj5', // 5–8 devs — $479.99
    ],
    // à-la-carte add-ons — flat price (a string, not a seat array)
    'kit-auth-rls': 'pri_01kxgz2vydz85g6h8syxj4by36', // $39.99
    'test-kit':     'pri_01kxgz2wg8v0qa7x0xg5njjseb', // $29.99
    'ui-kit':       'pri_01kxgz2vbw8rge6kvcafb2k6yy', // $4.99
    // Airlock Monitor subscription — buy here (pay-first). After payment the
    // Monitor webhook provisions the account from the buyer's email and mails a
    // login link, so the success page just says "check your email".
    'monitor':      'pri_01kxgz2x3bnkhgt6xtcdmctj7p', // $19.99/mo
    // 'combo' NAO tem price proprio: e um carrinho com as 3 pecas + COMBO10.
    // Montado por itensDoPlano(); nunca resolva por priceIds['combo'].
    'combo':        null,
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

  // O carrinho de cada plano, em UM lugar so — a landing e a /checkout/ usam a
  // mesma funcao, entao nao ha como uma cobrar diferente da outra.
  window.PADDLE.itensDoPlano = function (plan, seat) {
    if (plan === 'combo') {
      return [
        { priceId: P.priceIds['kit-auth-rls'], quantity: 1 },
        { priceId: P.priceIds['test-kit'],     quantity: 1 },
        { priceId: P.priceIds['ui-kit'],       quantity: 1 },
      ];
    }
    var entry = P.priceIds && P.priceIds[plan];
    var priceId = Array.isArray(entry) ? entry[seat || 0] : entry;
    return priceId ? [{ priceId: priceId, quantity: 1 }] : null;
  };
  window.PADDLE.cupomDoPlano = function (plan) {
    return plan === 'combo' ? 'COMBO10' : null;
  };

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
        var itens = P.itensDoPlano(plan, currentSeat());
        if (!itens) return;                // sem carrinho → segue o href
        e.preventDefault();
        // The Monitor is a subscription (provisioned by email post-payment), so it
        // lands on the "check your email" page; one-time products go to delivery.
        var successUrl = plan === 'monitor'
          ? 'https://shipsealed.com/welcome/'
          : 'https://boilerplate-delivery.vercel.app/';
        var opcoes = { settings: { successUrl: successUrl }, items: itens };
        var cupom = P.cupomDoPlano(plan);
        if (cupom) opcoes.discountCode = cupom;
        Paddle.Checkout.open(opcoes);
      });
    }
  }
})();
