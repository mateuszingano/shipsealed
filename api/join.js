// POST /api/join — waitlist signup + cheat-sheet delivery (Vercel serverless).
// Inserts the email into Supabase, then emails the RLS cheat sheet via Resend.
// The signup succeeds even if the email send fails (best-effort delivery).
//
// The only SECRET is RESEND_API_KEY — set it in Vercel → Project → Settings →
// Environment Variables. The Supabase publishable key below is public by design
// (INSERT-only RLS policy, no SELECT), so it's safe in this public repo.

const SUPABASE_URL = 'https://ukaelmxvgggvudlwwexk.supabase.co'
const SUPABASE_KEY = 'sb_publishable_ZfgF6NCfzH0T32Gjx5l-bw_DwleKw2S'
const CHEATSHEET_URL = 'https://shipsealed.com/assets/supabase-rls-cheatsheet.pdf'
const FROM = 'ShipSealed <hello@shipsealed.com>'

const isEmail = (s) => typeof s === 'string' && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(s)

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return res.status(405).json({ error: 'method_not_allowed' })
  }

  // Vercel parses JSON bodies; fall back to manual parse just in case.
  let body = req.body
  if (typeof body === 'string') { try { body = JSON.parse(body) } catch { body = {} } }
  body = body || {}

  // Honeypot: a filled `website` field means a bot. Fake success, do nothing.
  if (typeof body.website === 'string' && body.website.length > 0) {
    return res.status(200).json({ ok: true })
  }

  const email = String(body.email || '').trim().toLowerCase()
  const source = String(body.source || 'hub').slice(0, 40)
  if (!isEmail(email)) return res.status(400).json({ error: 'invalid_email' })

  // 1) Save to the waitlist (idempotent). 201 = a brand-new signup; 409 = already on
  //    the list (unique email). We only email brand-new signups — never re-send.
  let isNew = false
  try {
    const r = await fetch(`${SUPABASE_URL}/rest/v1/waitlist`, {
      method: 'POST',
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
        'Content-Type': 'application/json',
        Prefer: 'return=minimal',
      },
      body: JSON.stringify({ email, source }),
    })
    if (!r.ok && r.status !== 409) {
      return res.status(502).json({ error: 'waitlist_failed' })
    }
    isNew = r.status === 201 // a fresh insert, not a duplicate
  } catch {
    return res.status(502).json({ error: 'waitlist_unreachable' })
  }

  // 2) Email the cheat sheet — only to brand-new signups. Best-effort: a delivery
  //    hiccup must not fail the signup.
  const key = process.env.RESEND_API_KEY
  if (isNew && key) {
    try {
      await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from: FROM,
          to: email,
          subject: 'Your Supabase RLS cheat sheet 🦭',
          html: emailHtml(),
          text: emailText(),
        }),
      })
    } catch (err) {
      console.error('resend send failed:', err && err.message)
    }
  } else if (isNew && !key) {
    console.warn('RESEND_API_KEY not set — skipped cheat-sheet email')
  }

  return res.status(200).json({ ok: true })
}

function emailHtml() {
  return `<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;max-width:520px;margin:0 auto;color:#0b1016;line-height:1.55">
    <p style="font-size:16px"><strong>Your Supabase RLS cheat sheet 🦭</strong></p>
    <p>Thanks for joining ShipSealed. As promised, here's the one-page cheat sheet — the golden rules, the footguns that leak in prod, correct policy snippets, and the test that proves tenant isolation.</p>
    <p style="margin:22px 0"><a href="${CHEATSHEET_URL}" style="background:#1EC97E;color:#04130c;font-weight:700;text-decoration:none;padding:12px 20px;border-radius:8px;display:inline-block">Download the cheat sheet (PDF) &rarr;</a></p>
    <p>The free tools are live today too:</p>
    <ul>
      <li><code>npx supabase-saas-kit new my-app</code> &mdash; scaffold a secure Next.js + Supabase app</li>
      <li><code>npx airlock-rls</code> &mdash; the CI gate that fails your build if a table ships exposed</li>
    </ul>
    <p>We'll email you the moment the paid boilerplate's checkout opens &mdash; your founding price is locked in.</p>
    <p style="color:#667;font-size:13px;margin-top:26px">ShipSealed &mdash; ship Supabase apps that don't leak &middot; <a href="https://shipsealed.com" style="color:#0a7d4f">shipsealed.com</a></p>
  </div>`
}

function emailText() {
  return [
    'Your Supabase RLS cheat sheet',
    '',
    `Download (PDF): ${CHEATSHEET_URL}`,
    '',
    'The free tools are live today:',
    '- npx supabase-saas-kit new my-app',
    '- npx airlock-rls (the CI gate for RLS)',
    '',
    "We'll email you the moment the paid boilerplate's checkout opens — your founding price is locked in.",
    '',
    'ShipSealed — shipsealed.com',
  ].join('\n')
}
