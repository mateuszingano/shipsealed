// POST /api/scan — online version of `npx airlock-rls --site`.
// Fetches a public site and its JS bundles and reports whether a Supabase
// service_role / sb_secret key ships to the browser, plus a downloadable .env,
// a public .git folder and public source maps (each confirmed by content).
// Uses the published airlock-rls engine; never returns a key or a .env value.
// Each problem carries a copy-paste fix prompt for an AI coding tool.
//
// Abuse limits: 10 scans per hour per client (HMAC of the IP, checked in
// Postgres via scanner_check_rate_limit), 1000 per hour overall, every
// address DNS-checked against private ranges, 25 bundles, 40s budget.
//
// A share link is only issued for a clean AND complete scan: anyone can scan
// any public site, so a leak must never become a public URL.

import { scanSiteForServiceRole } from './_service-role.mjs'
import { fixPromptFor } from './_fix-prompts.mjs'
import {
  secret, hmac, signShare, makeSafeFetch, clientIp, allowScan, normaliseUrl,
} from './_scan-lib.mjs'

const MAX_SCRIPTS = 25
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

  const allowed = await allowScan(hmac(key, 'ip:' + clientIp(req)))
  if (allowed === null) return res.status(503).json({ error: 'rate_limit_unavailable' })
  if (!allowed) return res.status(429).json({ error: 'rate_limited' })

  const { safeFetch, stats } = makeSafeFetch({ deadline: Date.now() + BUDGET_MS })
  let result
  try {
    result = await scanSiteForServiceRole({ siteUrl: url.href, fetchImpl: safeFetch, maxScripts: MAX_SCRIPTS })
  } catch (e) {
    const msg = String((e && e.message) || '')
    const code = /only public http\(s\) hosts|blocked host/i.test(msg) ? 'blocked_host' : 'unreachable'
    return res.status(422).json({ error: code })
  }

  const FILE_KINDS = new Set(['env_file_exposed', 'git_exposed', 'source_map_exposed'])
  // The engine's key detail ends with a redacted fragment ("Found: eyJhb…").
  // This page can scan anyone's site, so drop it from anything we return.
  const scrub = (f) => ({ ...f, detail: String(f.detail || '').replace(/\s*Found: .*$/, '') })
  const leaks = result.findings.filter((f) => f.kind === 'service_role_exposed')
  const files = result.findings.filter((f) => FILE_KINDS.has(f.kind))
  const filesBad = files.some((f) => f.severity === 'fail')
  const truncated = result.findings.some((f) => f.kind === 'scan_truncated')
  const complete = !truncated && stats.failed === 0
  const host = url.hostname.replace(/^www\./, '')

  const out = {
    host,
    scanned: result.scanned,
    leaked: leaks.length > 0,
    complete,
    skipped: stats.failed,
    truncated,
    // Where the key sits, never the key: the engine's detail ends with a
    // redacted fragment, dropped here because this page can scan anyone.
    leaks: leaks.map((f) => ({ where: f.object, prompt: fixPromptFor(scrub(f)) })),
    // .env / .git (fail) and source maps (warn). The detail names the file and,
    // for .env, how many variables it holds; never a value.
    files: files.map((f) => ({ kind: f.kind, severity: f.severity, where: f.object, detail: f.detail, prompt: fixPromptFor(f) })),
    filesBad,
  }
  // Share only a site with no key, no exposed .env/.git, and a complete scan.
  if (!out.leaked && !filesBad && complete) {
    out.share = signShare(key, { h: host, t: Math.floor(Date.now() / 1000), n: result.scanned })
  }
  return res.status(200).json(out)
}
