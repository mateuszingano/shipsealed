// POST /api/scan-tables — "is my app's data readable without logging in?"
//
// Given a public app URL, it reads the SAME things the app already ships to
// every browser — its Supabase project URL, its anon / publishable key, and the
// table names it queries in its own JavaScript — then asks that project whether
// an anonymous visitor can read those tables. It uses ONLY the public anon key,
// reads NO row of real data (row counts come from the Content-Range header), and
// reports only table name + count. It finds nothing a logged-out visitor
// couldn't already find by opening the app and reading its bundle.
//
// Abuse limits: 10 scans/hour per client (separate bucket from the key scanner),
// every address DNS-checked against private ranges, 25 bundles, 40s budget.

import { extractScriptUrls, isFetchableUrl } from './_service-role.mjs'
import { extractSupabaseConfig, extractTableNames, probeOpenTables } from './_anon-read.mjs'
import {
  secret, hmac, makeSafeFetch, clientIp, allowScan, normaliseUrl,
} from './_scan-lib.mjs'

const MAX_SCRIPTS = 25
const MAX_TABLES = 40
const MAX_TEXT = 8 * 1024 * 1024 // cap combined bundle text fed to the regexes
const BUDGET_MS = 40_000

export const config = { maxDuration: 60 }

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store')
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return res.status(405).json({ error: 'method_not_allowed' })
  }
  const key = secret()
  if (!key) return res.status(503).json({ error: 'not_configured' })

  let body = req.body
  if (typeof body === 'string') { try { body = JSON.parse(body) } catch { body = {} } }
  const url = normaliseUrl(body && body.url)
  if (!url) return res.status(400).json({ error: 'invalid_url' })

  // Own rate-limit bucket so table scans and key scans don't starve each other.
  const allowed = await allowScan(hmac(key, 'tbl:ip:' + clientIp(req)))
  if (allowed === null) return res.status(503).json({ error: 'rate_limit_unavailable' })
  if (!allowed) return res.status(429).json({ error: 'rate_limited' })

  const { safeFetch } = makeSafeFetch({ deadline: Date.now() + BUDGET_MS })
  const headers = { 'User-Agent': 'airlock-rls (table read scan)' }

  // 1) Fetch the page + its JS bundles (SSRF-guarded), concatenate their text.
  let texts
  try {
    if (!isFetchableUrl(url.href)) throw new Error('blocked host')
    const pageRes = await safeFetch(url.href, { headers })
    const html = await pageRes.text()
    const scripts = extractScriptUrls(html, url.href).filter(isFetchableUrl).slice(0, MAX_SCRIPTS)
    texts = [html]
    let size = html.length
    for (const s of scripts) {
      if (size >= MAX_TEXT) break
      try {
        const r = await safeFetch(s, { headers })
        const t = await r.text()
        texts.push(t)
        size += t.length
      } catch { /* a bundle we can't fetch just isn't read */ }
    }
  } catch (e) {
    const msg = String((e && e.message) || '')
    const code = /blocked host|only public/i.test(msg) ? 'blocked_host' : 'unreachable'
    return res.status(422).json({ error: code })
  }

  const host = url.hostname.replace(/^www\./, '')

  // 2) The app's own Supabase config. No project/key in the bundle → not a
  //    Supabase app we can check this way (or it talks to its DB server-side).
  const cfg = extractSupabaseConfig(texts)
  if (!cfg) return res.status(200).json({ host, usesSupabase: false })

  // 3) The tables the app itself references, probed count-only as anon.
  const tables = extractTableNames(texts, MAX_TABLES * 2)
  let open = [], checked = 0
  try {
    const r = await probeOpenTables({
      projectUrl: cfg.projectUrl, anonKey: cfg.anonKey, tables, fetchImpl: safeFetch, maxTables: MAX_TABLES,
    })
    open = r.open
    checked = r.checked
  } catch {
    return res.status(200).json({ host, usesSupabase: true, checked: 0, open: [], error: 'probe_failed' })
  }

  return res.status(200).json({
    host,
    usesSupabase: true,
    checked,
    exposed: open.length > 0,
    // table name + how many rows anon can read. Never a cell value.
    open: open.map((o) => ({ table: o.table, rows: o.rows })),
  })
}
