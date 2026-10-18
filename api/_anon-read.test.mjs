// node --test. Pure-logic tests for the table-read scanner (no network).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { extractSupabaseConfig, extractTableNames, probeOpenTables } from './_anon-read.mjs'

const U = 'https://abcdefghijklmnopqrst.supabase.co'
const PUB = 'sb_publishable_ZfgF6NCfzH0T32Gjx5l_demoKeyXXXX'

test('extractSupabaseConfig: finds the project URL and publishable key', () => {
  const cfg = extractSupabaseConfig(`const c="${U}/rest/v1";const k="${PUB}";`)
  assert.deepEqual(cfg, { projectUrl: U, anonKey: PUB })
})

test('extractSupabaseConfig: picks the most-referenced project ref', () => {
  const other = 'https://zzzzzzzzzzzzzzzzzzzz.supabase.co'
  const cfg = extractSupabaseConfig(`${other} ${U} ${U} ${U} k="${PUB}"`)
  assert.equal(cfg.projectUrl, U)
})

test('extractSupabaseConfig: falls back to an anon JWT, never a service_role one', () => {
  const mk = (role) => 'eyJ' + Buffer.from('{"alg":"HS256"}').toString('base64url') + '.' +
    Buffer.from(JSON.stringify({ role })).toString('base64url') + '.c2lnbmF0dXJlX2xvbmdfZW5vdWdo'
  const anon = mk('anon'), svc = mk('service_role')
  assert.equal(extractSupabaseConfig(`${U} ${anon}`).anonKey, anon)
  // a service_role key alone must NOT be adopted as the probe key
  assert.equal(extractSupabaseConfig(`${U} ${svc}`), null)
})

test('extractSupabaseConfig: null when no Supabase project is present', () => {
  assert.equal(extractSupabaseConfig('just a normal site, no backend keys'), null)
})

test('extractTableNames: reads .from() and /rest/v1/ names, skips rpc', () => {
  const blob = `a.from('profiles').select();b.from("orders");fetch("/rest/v1/invoices?x");c.from(\`notes\`);d.from('rpc')`
  assert.deepEqual(extractTableNames(blob).sort(), ['invoices', 'notes', 'orders', 'profiles'])
})

// A fake PostgREST: count>0 for an exposed table, count 0 (RLS) or 401 otherwise.
function fakeRest(map) {
  return async (url) => {
    const t = new URL(url).pathname.split('/rest/v1/')[1]
    const entry = map[decodeURIComponent(t)]
    if (!entry) return new Response('', { status: 404 })
    if (entry.status && entry.status >= 400) return new Response('', { status: entry.status })
    return new Response('', { status: entry.rows > 0 ? 206 : 200, headers: { 'content-range': `*/${entry.rows}` } })
  }
}

test('probeOpenTables: reports only tables anon actually sees rows in', async () => {
  const fetchImpl = fakeRest({
    leaky: { rows: 42 },        // open: anon reads 42 rows
    empty_public: { rows: 0 },  // RLS blocks (or empty) → safe
    protected: { status: 401 }, // not reachable by anon → safe
  })
  const res = await probeOpenTables({
    projectUrl: U, anonKey: PUB, fetchImpl,
    tables: ['leaky', 'empty_public', 'protected', 'does_not_exist'],
  })
  assert.deepEqual(res.open, [{ table: 'leaky', rows: 42 }])
  assert.equal(res.checked, 4)
})

test('probeOpenTables: never reads a response body (count comes from the header)', async () => {
  let bodyReads = 0
  const fetchImpl = async (url) => {
    const t = new URL(url).pathname.split('/rest/v1/')[1]
    const res = new Response('SHOULD NOT BE READ', { status: 206, headers: { 'content-range': '*/5' } })
    const json = res.json.bind(res), text = res.text.bind(res)
    res.json = async () => { bodyReads++; return json() }
    res.text = async () => { bodyReads++; return text() }
    return res
  }
  await probeOpenTables({ projectUrl: U, anonKey: PUB, fetchImpl, tables: ['a', 'b'] })
  assert.equal(bodyReads, 0)
})

test('probeOpenTables: caps how many tables it probes', async () => {
  let calls = 0
  const fetchImpl = async () => { calls++; return new Response('', { status: 200, headers: { 'content-range': '*/0' } }) }
  const many = Array.from({ length: 100 }, (_, i) => `t${i}`)
  const res = await probeOpenTables({ projectUrl: U, anonKey: PUB, fetchImpl, tables: many, maxTables: 40 })
  assert.equal(calls, 40)
  assert.equal(res.checked, 40)
})
