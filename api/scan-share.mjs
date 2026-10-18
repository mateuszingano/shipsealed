// GET /api/scan-share?r=<keyToken>&t=<tablesToken> — the public "my app scored
// Grade A" page behind a share link. Each token is HMAC-signed by its scanner
// (/api/scan for the service key, /api/scan-tables for the tables) and is only
// issued on a clean result, so this page can't be forged to claim a leaking
// site is safe. Grade A needs BOTH tokens, for the same host. Not indexed.

import { secret, verifyShare, escapeHtml } from './_scan-lib.mjs'

const SCANNER = 'https://shipsealed.com/service-role-scanner/'

export default function handler(req, res) {
  const key = secret()
  const kd = key ? verifyShare(key, String(req.query.r || '')) : null
  if (!kd) {
    res.setHeader('Location', SCANNER)
    return res.status(302).end()
  }
  // The tables token counts only when it's valid AND for the same host.
  const t = req.query.t ? verifyShare(key, String(req.query.t)) : null
  const tablesClean = !!(t && t.kind === 'tbl' && t.h === kd.h)
  const gradeA = tablesClean // both checks clean

  const host = escapeHtml(kd.h)
  const date = new Date(kd.t * 1000).toISOString().slice(0, 10)

  const title = gradeA
    ? `${kd.h} scored an A on the Supabase security check`
    : `${kd.h} passed the Supabase service-key check`
  const desc = gradeA
    ? `No service_role key in the browser, and no tables readable without logging in on ${host} (checked ${date}). Scan your own app in seconds, free.`
    : `No Supabase service_role or sb_secret key found in ${host}'s frontend (checked ${date}). Scan your own app in seconds, free.`
  const img = gradeA
    ? 'https://shipsealed.com/assets/og-scan-grade-a.png'
    : 'https://shipsealed.com/assets/og-scan-pass.png'
  const cta = `${SCANNER}?utm_source=share&utm_medium=referral&utm_campaign=scanner-grade`
  const q = `r=${encodeURIComponent(String(req.query.r))}` + (gradeA ? `&t=${encodeURIComponent(String(req.query.t))}` : '')
  const self = `https://shipsealed.com/api/scan-share?${q}`

  const checksHtml = gradeA
    ? `<ul class="checks">
        <li><b>✓</b> No <code>service_role</code> key shipped to the browser</li>
        <li><b>✓</b> No tables readable without logging in (${t.n} checked with the anon key)</li>
       </ul>`
    : `<ul class="checks">
        <li><b>✓</b> No <code>service_role</code> key shipped to the browser</li>
       </ul>
       <p>This one checked the frontend for a leaked master key. It didn't test the database tables.</p>`

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
<meta property="og:image" content="${img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${title}">
<meta name="twitter:description" content="${desc}">
<meta name="twitter:image" content="${img}">
<script defer src="/_vercel/insights/script.js"></script>
<style>
  :root{--bg:#07090c;--card:#0d1117;--line:#1c242e;--txt:#e8edf2;--dim:#8b97a5;--green:#1fe3b8}
  *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:16px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;display:grid;place-items:center;min-height:100vh;padding:24px}
  .card{max-width:560px;width:100%;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:32px}
  .grade{display:inline-grid;place-items:center;width:64px;height:64px;border-radius:14px;background:rgba(31,227,184,.12);border:1px solid var(--green);color:var(--green);font:800 34px ui-monospace,Menlo,monospace;margin-bottom:14px}
  .ok{font:600 13px ui-monospace,Menlo,monospace;color:var(--green);letter-spacing:.04em}
  h1{font-size:24px;line-height:1.3;margin:6px 0 14px}p{color:var(--dim);margin:0 0 14px}
  .checks{list-style:none;padding:0;margin:0 0 16px}.checks li{margin:0 0 8px}.checks b{color:var(--green);margin-right:8px}
  code{color:var(--txt)}
  a.btn{display:inline-block;background:var(--green);color:#04130c;font-weight:700;text-decoration:none;padding:12px 18px;border-radius:10px;margin-top:6px}
  .small{font-size:13px;margin-top:22px}.small a{color:var(--dim)}
</style>
</head>
<body>
  <main class="card">
    ${gradeA ? '<div class="grade">A</div>' : '<div class="ok">✓ PASSED · ' + date + '</div>'}
    <h1><span style="word-break:break-all">${host}</span> ${gradeA ? 'scored an A on the Supabase security check' : "doesn't ship a Supabase service_role key to the browser"}</h1>
    ${checksHtml}
    <a class="btn" href="${cta}">Scan your own app →</a>
    <p class="small">A one-time check of the public frontend on ${date}, reading only what any visitor can see. <a href="https://shipsealed.com/?utm_source=share&utm_medium=referral&utm_campaign=scanner-grade">ShipSealed</a> · not affiliated with Supabase.</p>
  </main>
</body>
</html>`)
}
