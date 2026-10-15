// Shared helpers for the online service_role scanner (/api/scan, /api/scan-share).
// Files starting with "_" are not exposed as routes by Vercel.

import crypto from 'node:crypto'
import dns from 'node:dns/promises'
import net from 'node:net'

export const SUPABASE_URL = 'https://ukaelmxvgggvudlwwexk.supabase.co'
// Publishable key: public by design (same one /api/join and the pages use).
export const SUPABASE_KEY = 'sb_publishable_ZfgF6NCfzH0T32Gjx5l-bw_DwleKw2S'

export function secret() {
  const s = process.env.SCANNER_SECRET
  return s && s.length >= 32 ? s : null
}

export const hmac = (key, text) => crypto.createHmac('sha256', key).update(text).digest('hex')

// ── Share tokens: base64url(JSON).hex(HMAC). Only clean, complete scans get one.
const b64u = (s) => Buffer.from(s).toString('base64url')
export function signShare(key, data) {
  const payload = b64u(JSON.stringify(data))
  return `${payload}.${hmac(key, 'share:' + payload)}`
}
export function verifyShare(key, token) {
  if (typeof token !== 'string' || token.length > 600) return null
  const [payload, sig] = token.split('.')
  if (!payload || !sig || !/^[a-f0-9]{64}$/.test(sig)) return null
  const want = Buffer.from(hmac(key, 'share:' + payload), 'hex')
  const got = Buffer.from(sig, 'hex')
  if (want.length !== got.length || !crypto.timingSafeEqual(want, got)) return null
  try {
    const d = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8'))
    if (typeof d.h !== 'string' || !Number.isInteger(d.t) || !Number.isInteger(d.n)) return null
    return d
  } catch {
    return null
  }
}

// ── SSRF guard by resolved address. The engine already refuses private
// literals and checks every redirect hop by name; this closes the gap it
// documents: a public-looking hostname that resolves to a private address.
function v4ToInt(ip) {
  return ip.split('.').reduce((a, o) => (a << 8) + Number(o), 0) >>> 0
}
const V4_BLOCKED = [
  ['0.0.0.0', 8], ['10.0.0.0', 8], ['100.64.0.0', 10], ['127.0.0.0', 8],
  ['169.254.0.0', 16], ['172.16.0.0', 12], ['192.0.0.0', 24], ['192.0.2.0', 24],
  ['192.168.0.0', 16], ['198.18.0.0', 15], ['198.51.100.0', 24], ['203.0.113.0', 24],
  ['224.0.0.0', 4], ['240.0.0.0', 4],
].map(([base, bits]) => [v4ToInt(base), bits])

export function isBlockedIp(ip) {
  if (net.isIPv4(ip)) {
    const n = v4ToInt(ip)
    return V4_BLOCKED.some(([base, bits]) => (n >>> (32 - bits)) === (base >>> (32 - bits)))
  }
  if (net.isIPv6(ip)) {
    const s = ip.toLowerCase()
    const mapped = s.match(/^::ffff:(\d+\.\d+\.\d+\.\d+)$/)
    if (mapped) return isBlockedIp(mapped[1])
    if (s === '::' || s === '::1') return true
    if (/^f[cd]/.test(s)) return true // fc00::/7 unique local
    if (/^fe[89ab]/.test(s)) return true // fe80::/10 link-local
    if (/^ff/.test(s)) return true // multicast
    if (s.startsWith('64:ff9b:')) return true // NAT64, can reach v4 space
    return false
  }
  return true // not an IP at all: refuse
}

export async function hostIsPublic(hostname) {
  const host = hostname.replace(/^\[|\]$/g, '')
  if (net.isIP(host)) return !isBlockedIp(host)
  try {
    const addrs = await dns.lookup(host, { all: true, verbatim: true })
    return addrs.length > 0 && addrs.every((a) => !isBlockedIp(a.address))
  } catch {
    return false
  }
}

const MAX_BODY = 5 * 1024 * 1024

// fetch for the engine: DNS-checked, deadline-bound, body-capped. Records which
// requests failed so the caller can tell "clean" from "couldn't look".
export function makeSafeFetch({ deadline }) {
  const stats = { attempted: 0, failed: 0 }
  async function safeFetch(url, init = {}) {
    stats.attempted++
    try {
      const u = new URL(url)
      if (!(await hostIsPublic(u.hostname))) throw new Error('blocked host')
      const left = deadline - Date.now()
      if (left <= 0) throw new Error('deadline')
      const signal = AbortSignal.any([init.signal, AbortSignal.timeout(left)].filter(Boolean))
      const res = await fetch(url, { ...init, signal })
      if (res.status >= 300 && res.status < 400) return res // engine follows by hand
      const text = await readCapped(res)
      return new Response(text, { status: res.status, headers: res.headers })
    } catch (e) {
      stats.failed++
      throw e
    }
  }
  return { safeFetch, stats }
}

async function readCapped(res) {
  if (!res.body) return ''
  const reader = res.body.getReader()
  const chunks = []
  let size = 0
  while (size < MAX_BODY) {
    const { done, value } = await reader.read()
    if (done) break
    chunks.push(value)
    size += value.length
  }
  reader.cancel().catch(() => {})
  return Buffer.concat(chunks).subarray(0, MAX_BODY).toString('utf8')
}

export function clientIp(req) {
  const fwd = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim()
  return fwd || String(req.headers['x-real-ip'] || '') || 'unknown'
}

export async function allowScan(rateKey) {
  try {
    const r = await fetch(`${SUPABASE_URL}/rest/v1/rpc/scanner_check_rate_limit`, {
      method: 'POST',
      headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ p_key: rateKey }),
      signal: AbortSignal.timeout(5000),
    })
    if (!r.ok) return null
    return (await r.json()) === true
  } catch {
    return null
  }
}

// Normalise what people paste: "myapp.com", "https://myapp.com/", with spaces.
export function normaliseUrl(input) {
  let s = String(input || '').trim()
  if (!s || s.length > 2048) return null
  if (!/^https?:\/\//i.test(s)) s = 'https://' + s
  try {
    const u = new URL(s)
    if (u.protocol !== 'https:' && u.protocol !== 'http:') return null
    if (u.username || u.password) return null
    if (!u.hostname.includes('.')) return null
    u.hash = ''
    return u
  } catch {
    return null
  }
}

export const escapeHtml = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
