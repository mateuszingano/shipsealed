// GET /api/scan-share?r=<token> — the public page behind a "my app passed" link.
// The token is HMAC-signed by /api/scan and only exists for clean, complete
// scans, so this page can't be forged to claim a site passed. Not indexed.

import { secret, verifyShare, escapeHtml } from './_scan-lib.mjs'

const SCANNER = 'https://shipsealed.com/service-role-scanner/'

export default function handler(req, res) {
  const key = secret()
  const d = key ? verifyShare(key, String(req.query.r || '')) : null
  if (!d) {
    res.setHeader('Location', SCANNER)
    return res.status(302).end()
  }
  const host = escapeHtml(d.h)
  const date = new Date(d.t * 1000).toISOString().slice(0, 10)
  const title = `✓ ${host} passed the Supabase service_role key check`
  const desc = `No Supabase service_role or sb_secret key found in ${host}'s page or its ${d.n - 1} JavaScript bundles (checked ${date}). Check your own app in seconds.`
  const cta = `${SCANNER}?utm_source=share&utm_medium=referral&utm_campaign=scanner-pass`
  const self = `https://shipsealed.com/api/scan-share?r=${encodeURIComponent(String(req.query.r))}`

  res.setHeader('Content-Type', 'text/html; charset=utf-8')
  res.setHeader('Cache-Control', 'public, max-age=3600')
  res.status(200).send(`<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>${title}</title>
<meta name="description" content="${desc}">
<link rel="canonical" href="${SCANNER}">
<meta property="og:type" content="website">
<meta property="og:url" content="${self}">
<meta property="og:title" content="${title}">
<meta property="og:description" content="${desc}">
<meta property="og:image" content="https://shipsealed.com/assets/og-scan-pass.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${title}">
<meta name="twitter:description" content="${desc}">
<meta name="twitter:image" content="https://shipsealed.com/assets/og-scan-pass.png">
<script defer src="/_vercel/insights/script.js"></script>
<style>
  :root{--bg:#07090c;--card:#0d1117;--line:#1c242e;--txt:#e8edf2;--dim:#8b97a5;--green:#1fe3b8}
  *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;display:grid;place-items:center;min-height:100vh;padding:24px}
  .card{max-width:560px;width:100%;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:32px}
  .ok{font:600 13px ui-monospace,Menlo,monospace;color:var(--green);letter-spacing:.04em}
  h1{font-size:26px;line-height:1.25;margin:10px 0 12px}p{color:var(--dim);margin:0 0 14px}
  a.btn{display:inline-block;background:var(--green);color:#04130c;font-weight:700;text-decoration:none;padding:12px 18px;border-radius:10px;margin-top:6px}
  .small{font-size:13px;margin-top:22px}.small a{color:var(--dim)}
</style>
</head>
<body>
  <main class="card">
    <div class="ok">✓ PASSED · ${date}</div>
    <h1><span style="word-break:break-all">${host}</span> doesn't ship a Supabase service_role key to the browser</h1>
    <p>ShipSealed's scanner read the page and its JavaScript bundles and found no <code>service_role</code> JWT and no <code>sb_secret_</code> key. That key bypasses every Row Level Security policy, so this is the leak that matters most.</p>
    <a class="btn" href="${cta}">Check your own app →</a>
    <p class="small">A one-time check of the public frontend on ${date}. It doesn't audit the database. <a href="https://shipsealed.com/?utm_source=share&utm_medium=referral&utm_campaign=scanner-pass">ShipSealed</a> · not affiliated with Supabase.</p>
  </main>
</body>
</html>`)
}
