// Shared helper for the "is my app's data readable?" scan (/api/scan-tables).
// Files starting with "_" are not exposed as routes by Vercel.
//
// What it does: given a public app URL, it reads the SAME values the app already
// ships to every browser — its Supabase project URL, its anon / publishable key,
// and the table names it queries in its own JavaScript — then asks that project
// whether an anonymous visitor can read those tables. This finds nothing a
// logged-out attacker couldn't find by opening the app and reading its bundle.
//
// Hard safety rules (this page can be pointed at any public URL):
//   • anon / publishable key ONLY — never a service key, no privilege at all.
//   • It NEVER reads a single row of real data. Each table is probed with a
//     count-only request (limit=0, Prefer: count=exact); the row COUNT comes
//     from the Content-Range header and the body is never read.
//   • A table counts as EXPOSED only when anon actually sees rows (count > 0).
//     A table that returns 0 rows is safe — RLS is doing its job, or it's empty.
//   • It reports table NAME + row COUNT only. Never a cell value.

const PROJECT_RE = /https:\/\/([a-z0-9]{20})\.supabase\.co/gi
const PUBLISHABLE_RE = /\bsb_publishable_[A-Za-z0-9_-]{20,}\b/g
const JWT_RE = /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g
// Table names the app references: supabase-js `.from('x')` and raw `/rest/v1/x`.
const FROM_RE = /\.from\(\s*["'`]([a-zA-Z_][a-zA-Z0-9_]{0,62})["'`]\s*\)/g
const REST_RE = /\/rest\/v1\/([a-zA-Z_][a-zA-Z0-9_]{0,62})(?:[?/"'`\\\s]|$)/g

/** Decode a JWT payload without verifying (we only read the role claim). */
function jwtRole(token) {
  try {
    const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString('utf8'))
    return typeof payload.role === 'string' ? payload.role : null
  } catch {
    return null
  }
}

/**
 * Pull the app's own Supabase project URL + a public (anon/publishable) key out
 * of its HTML/JS text. Returns { projectUrl, anonKey } or null if not found.
 * A `service_role` JWT is never returned — that's the service-key scanner's job,
 * and we must not probe with one.
 */
export function extractSupabaseConfig(texts) {
  const blob = Array.isArray(texts) ? texts.join('\n') : String(texts || '')
  const refs = [...blob.matchAll(PROJECT_RE)].map((m) => m[1].toLowerCase())
  if (refs.length === 0) return null
  const ref = refs.sort(
    (a, b) => refs.filter((r) => r === b).length - refs.filter((r) => r === a).length,
  )[0]

  const pub = blob.match(PUBLISHABLE_RE)
  let anonKey = pub ? pub[0] : null
  if (!anonKey) {
    for (const jwt of blob.match(JWT_RE) || []) {
      if (jwtRole(jwt) === 'anon') { anonKey = jwt; break }
    }
  }
  if (!anonKey) return null
  return { projectUrl: `https://${ref}.supabase.co`, anonKey }
}

/** Candidate table names the app queries, from its own bundle. De-duplicated. */
export function extractTableNames(texts, max = 60) {
  const blob = Array.isArray(texts) ? texts.join('\n') : String(texts || '')
  const names = new Set()
  for (const re of [FROM_RE, REST_RE]) {
    for (const m of blob.matchAll(re)) {
      const n = m[1]
      // Skip PostgREST's own endpoints and obvious non-tables.
      if (n === 'rpc' || n === 'graphql') continue
      names.add(n)
      if (names.size >= max) break
    }
    if (names.size >= max) break
  }
  return [...names]
}

/** The exact row count from a PostgREST Content-Range header (the part after the slash). */
function countFromRange(res) {
  const total = (res.headers.get('content-range') || '').split('/')[1]
  if (total === undefined || total === '*') return null
  const n = Number(total)
  return Number.isFinite(n) ? n : null
}

/**
 * Count-probe each candidate table as an anonymous visitor. A table is EXPOSED
 * only when the read succeeds AND anon sees rows (count > 0) — the same rule the
 * airlock engine proves, but read from the header so no row is ever pulled.
 *
 * @returns {Promise<{open: Array<{table:string, rows:number}>, checked:number}>}
 */
export async function probeOpenTables({ projectUrl, anonKey, tables, fetchImpl = fetch, maxTables = 40 }) {
  const base = projectUrl.replace(/\/$/, '')
  const list = (tables || []).slice(0, maxTables)
  const open = []
  for (const t of list) {
    let res
    try {
      res = await fetchImpl(`${base}/rest/v1/${encodeURIComponent(t)}?limit=0`, {
        method: 'GET',
        headers: {
          apikey: anonKey,
          Authorization: `Bearer ${anonKey}`,
          Prefer: 'count=exact',
        },
      })
    } catch {
      continue // couldn't reach this one; unknown, not reported as open
    }
    if (res.status >= 200 && res.status < 300) {
      const rows = countFromRange(res)
      if (rows && rows > 0) open.push({ table: t, rows })
    }
  }
  return { open, checked: list.length }
}
