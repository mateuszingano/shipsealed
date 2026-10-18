// node --test. Covers RLSGen.parseCreateTable (the "paste your CREATE TABLE" parser).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createRequire } from 'module'
const require = createRequire(import.meta.url)
const RLSGen = require('./rls-gen.js')

test('parses an owner table and detects user_id', () => {
  const r = RLSGen.parseCreateTable(`create table public.notes (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id),
    body text, amount numeric(10,2)
  );`)
  assert.equal(r.table, 'notes')
  assert.equal(r.schema, 'public')
  assert.equal(r.ownerCol, 'user_id')
  assert.equal(r.detectedOwner, true)
  assert.equal(r.detectedTeam, false)
  assert.equal(r.suggestedPattern, 'owner')
  assert.equal(r.columns.length, 4) // id, user_id, body, amount — not the constraints
})

test('parses a team table, keeps schema, reads the team col type', () => {
  const r = RLSGen.parseCreateTable(`CREATE TABLE IF NOT EXISTS app.invoices (
    id bigint generated always as identity primary key,
    workspace_id bigint not null,
    total numeric not null,
    constraint fk foreign key (workspace_id) references workspaces(id)
  )`)
  assert.equal(r.table, 'invoices')
  assert.equal(r.schema, 'app')
  assert.equal(r.teamCol, 'workspace_id')
  assert.equal(r.detectedTeam, true)
  assert.equal(r.teamColType, 'bigint')
  assert.equal(r.suggestedPattern, 'team')
  assert.equal(r.columns.length, 3) // the constraint line is skipped
})

test('no owner/team column → public_read_only', () => {
  const r = RLSGen.parseCreateTable(`create table products ( id int primary key, name text, price numeric )`)
  assert.equal(r.suggestedPattern, 'public_read_only')
  assert.equal(r.detectedOwner, false)
  assert.equal(r.detectedTeam, false)
})

test('owner synonyms are recognised in priority order', () => {
  assert.equal(RLSGen.parseCreateTable('create table t (id int, owner uuid)').ownerCol, 'owner')
  assert.equal(RLSGen.parseCreateTable('create table t (id int, created_by uuid)').ownerCol, 'created_by')
  // user_id wins over owner_id when both are present
  assert.equal(RLSGen.parseCreateTable('create table t (owner_id uuid, user_id uuid)').ownerCol, 'user_id')
})

test('comments and nested parens do not break the split', () => {
  const r = RLSGen.parseCreateTable(`create table t (
    id uuid primary key, -- the id
    amount numeric(10, 2),
    user_id uuid /* owner */
  )`)
  assert.equal(r.columns.length, 3)
  assert.equal(r.ownerCol, 'user_id')
})

test('garbage input returns a helpful error, not a throw', () => {
  assert.ok(RLSGen.parseCreateTable('select * from notes').error)
  assert.ok(RLSGen.parseCreateTable('').error)
  assert.ok(RLSGen.parseCreateTable('create table t ()').error) // no columns
})

test('a parsed table feeds generate() and yields a valid migration', () => {
  const p = RLSGen.parseCreateTable('create table public.posts (id uuid primary key, user_id uuid, title text)')
  const g = RLSGen.generate({ pattern: p.suggestedPattern, table: p.table, schema: p.schema, ownerCol: p.ownerCol })
  assert.equal(g.errors.length, 0)
  assert.match(g.sql, /enable row level security/)
  assert.match(g.sql, /user_id = \(select auth\.uid\(\)\)/)
})
