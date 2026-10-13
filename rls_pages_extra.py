# -*- coding: utf-8 -*-
"""Páginas 2-12 do lote 1 de guias de RLS (ShipSealed). Conteúdo à mão, código real.
Importado por gerador-rls.py. Cada dict segue o mesmo shape da flagship."""

EXTRA = []

# ---- 2. Enable RLS on a Supabase table -----------------------------------
EXTRA.append({
    "slug": "enable-row-level-security-supabase-table",
    "title": "How to enable Row-Level Security on a Supabase table",
    "h1_plain": "How to enable Row-Level Security on a Supabase table",
    "h1": "How to enable Row-Level Security on a Supabase table",
    "desc": "Enable RLS on a Supabase table the right way: the one-line command, why RLS-on with no policy denies everything, the first owner policy to add, and how to verify it's on.",
    "eyebrow": "Supabase RLS · How-to",
    "crumb": "Enable Row-Level Security on a table",
    "byline": "Postgres 15 · Supabase",
    "tldr": "Run <code>alter table X enable row level security;</code> — ideally in the same migration that creates the table. But RLS on with <b>no policy denies every row</b>, so add at least one policy in the same step. Verify with <code>pg_class.relrowsecurity</code>.",
    "body": """  <h2><span class="n">01</span> Why it matters</h2>
  <p>Every Supabase table is reachable from the browser through the <code>anon</code> key. Row-Level Security is the <b>only</b> thing between a user and everyone else's rows. RLS <b>off</b> = the table is public. So enabling it is not optional hardening — it's the security boundary.</p>

  <h2><span class="n">02</span> Enable it</h2>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">alter table</span> notes <span class="k">enable row level security</span>;</pre>
  <p>Do this in the <b>same migration that creates the table</b>, so a table can never exist without it. The <code>supabase-saas-kit</code> CLI generates migrations this way by default.</p>

  <h2><span class="n">03</span> The gotcha — on with no policy denies everything</h2>
  <p>Enabling RLS flips the table to <b>deny by default</b>. With no policy, every <code>select</code>/<code>insert</code>/<code>update</code>/<code>delete</code> returns nothing or errors — the table looks "broken." That's expected: you now have to grant access explicitly. Add at least a read policy:</p>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">create policy</span> <span class="s">"owner reads own notes"</span> <span class="k">on</span> notes <span class="k">for select</span>
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()));</pre>
  <p>See <a href="/rls/write-owner-scoped-rls-policy-supabase/">the full owner-scoped policy set</a> for INSERT/UPDATE/DELETE.</p>

  <h2><span class="n">04</span> Verify it's on</h2>
  <p class="filelabel">check.sql</p>
  <pre><span class="k">select</span> relname, relrowsecurity
<span class="k">from</span> pg_class <span class="k">where</span> relname = <span class="s">'notes'</span>;
<span class="c">-- relrowsecurity = t  → RLS is on</span></pre>
  <p>Table owners bypass RLS by default. If you want the owner subject to it too (defense in depth), add <code>alter table notes force row level security;</code>.</p>""",
    "related": [
        ("write-owner-scoped-rls-policy-supabase", "Write an owner-scoped RLS policy (all four operations)"),
        ("supabase-table-public-rls-off", "Why is my Supabase table public? (RLS is off)"),
        ("supabase-security-checklist-before-launch", "Supabase security checklist before launch"),
    ],
    "faq": [
        ("Does enabling RLS break my existing queries?",
         "It will, until you add policies — RLS on with no policy denies everything. Enable it and add the policies your app needs in the same migration, then test the queries the way your app runs them (signed in, through the client)."),
        ("Do I need RLS if I only talk to the database from a server?",
         "If that server uses the service_role key, it bypasses RLS. But the moment any table is reachable by the anon or authenticated key from the browser, RLS is the only thing protecting it. Enable it on every table regardless — it costs nothing and closes the most common leak."),
    ],
})

# ---- 3. Owner-scoped policy (all four ops) -------------------------------
EXTRA.append({
    "slug": "write-owner-scoped-rls-policy-supabase",
    "title": "How to write an owner-scoped RLS policy (SELECT / INSERT / UPDATE / DELETE)",
    "h1_plain": "How to write an owner-scoped RLS policy (SELECT / INSERT / UPDATE / DELETE)",
    "h1": "How to write an owner-scoped RLS policy",
    "desc": "The complete owner-scoped Supabase RLS policy set for SELECT, INSERT, UPDATE and DELETE — with the right USING and WITH CHECK on each, and why UPDATE needs both.",
    "eyebrow": "Supabase RLS · Policy pattern",
    "crumb": "Owner-scoped RLS policy",
    "byline": "Postgres 15 · Supabase",
    "tldr": "Store <code>user_id</code> on the table and compare it to <code>(select auth.uid())</code> in one policy per operation: <code>USING</code> for SELECT/DELETE, <code>WITH CHECK</code> for INSERT, and <b>both</b> for UPDATE. Full set below.",
    "body": """  <h2><span class="n">01</span> The rule</h2>
  <p>Owner-scoped means: a row belongs to one user, and only that user can touch it. Store the owner as <code>user_id</code> and compare it to <code>(select auth.uid())</code> — the id of the signed-in caller — in every policy. Wrapping it in a subselect lets Postgres cache the value per statement, a real speed win at scale.</p>

  <h2><span class="n">02</span> The full policy set</h2>
  <p>One policy per operation. Note where each uses <code>USING</code> vs <code>WITH CHECK</code>:</p>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">alter table</span> notes <span class="k">enable row level security</span>;

<span class="c">-- read: filter to rows you own</span>
<span class="k">create policy</span> <span class="s">"select own"</span> <span class="k">on</span> notes <span class="k">for select</span>
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()));

<span class="c">-- create: the new row must belong to you</span>
<span class="k">create policy</span> <span class="s">"insert own"</span> <span class="k">on</span> notes <span class="k">for insert</span>
  <span class="k">with check</span> (user_id = (<span class="k">select</span> auth.uid()));

<span class="c">-- update: you can only touch your rows (USING) and can't reassign them (WITH CHECK)</span>
<span class="k">create policy</span> <span class="s">"update own"</span> <span class="k">on</span> notes <span class="k">for update</span>
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()))
  <span class="k">with check</span> (user_id = (<span class="k">select</span> auth.uid()));

<span class="c">-- delete: you can only delete your rows</span>
<span class="k">create policy</span> <span class="s">"delete own"</span> <span class="k">on</span> notes <span class="k">for delete</span>
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()));</pre>

  <h2><span class="n">02b</span> Why UPDATE needs both</h2>
  <p><code>USING</code> decides which rows you may update; <code>WITH CHECK</code> validates the row <em>after</em> your change. Without <code>WITH CHECK</code>, a user could update their own row and set <code>user_id</code> to someone else's — handing it away. Both clauses close that.</p>

  <h2><span class="n">03</span> Prove it</h2>
  <div class="prove">
    <div class="row"><span class="ok">✓</span> owner reads / updates / deletes their own rows</div>
    <div class="row"><span class="bad">✗</span> owner sees <b>0 rows</b> for another user</div>
    <div class="row"><span class="bad">✗</span> owner cannot reassign a row to another <code>user_id</code></div>
  </div>
  <p>See <a href="/rls/test-tenant-isolation-supabase/">how to test tenant isolation</a> to turn that into an automated check.</p>""",
    "related": [
        ("test-tenant-isolation-supabase", "Test tenant isolation in Supabase"),
        ("multi-tenant-rls-workspaces-supabase", "Multi-tenant RLS with workspaces"),
        ("fix-new-row-violates-row-level-security-policy", "Fix: new row violates row-level security policy"),
    ],
    "faq": [
        ("Can I use one policy for all operations?",
         "You can write a policy FOR ALL, but you lose the USING/WITH CHECK distinction that matters for writes. A policy per operation is clearer and safer — especially so UPDATE gets both clauses."),
        ("Where does user_id come from on insert?",
         "Set a column default of (select auth.uid()) so the database fills it, or set it explicitly from the signed-in user on the client. Either way the WITH CHECK guarantees it matches the caller."),
    ],
})

# ---- 4. Multi-tenant workspaces ------------------------------------------
EXTRA.append({
    "slug": "multi-tenant-rls-workspaces-supabase",
    "title": "Multi-tenant RLS with workspaces in Supabase",
    "h1_plain": "Multi-tenant RLS with workspaces in Supabase",
    "h1": "Multi-tenant RLS with workspaces in Supabase",
    "desc": "Team/workspace multi-tenancy in Supabase with RLS: a membership table, a security-definer function to resolve membership without recursion, and policies that scope every row to the caller's workspaces.",
    "eyebrow": "Supabase RLS · Multi-tenant",
    "crumb": "Multi-tenant RLS with workspaces",
    "byline": "Postgres 15 · Supabase",
    "tldr": "Scope rows to <code>workspace_id</code> and check membership through a <b>security-definer</b> function (<code>user_workspace_ids()</code>) so policies stay simple and don't recurse. Full pattern below.",
    "body": """  <h2><span class="n">01</span> The shape</h2>
  <p>For teams, a row belongs to a <b>workspace</b>, and a user can touch it if they're a member. You need a membership table and a way to ask "which workspaces is this user in?" from inside a policy — without triggering infinite recursion.</p>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">create table</span> workspace_members (
  workspace_id uuid <span class="k">references</span> workspaces,
  user_id      uuid <span class="k">references</span> auth.users,
  <span class="k">primary key</span> (workspace_id, user_id)
);
<span class="k">alter table</span> workspace_members <span class="k">enable row level security</span>;
<span class="k">create policy</span> <span class="s">"read own memberships"</span> <span class="k">on</span> workspace_members <span class="k">for select</span>
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()));</pre>

  <h2><span class="n">02</span> Resolve membership once (security definer)</h2>
  <p>A policy on <code>projects</code> that queries <code>workspace_members</code>, which itself has RLS, can recurse. The fix: a <code>security definer</code> function that reads membership with the definer's rights, so the policy stays a simple <code>IN</code> check. Pin <code>search_path</code> to empty for safety.</p>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">create or replace function</span> public.user_workspace_ids()
  <span class="k">returns setof</span> uuid
  <span class="k">language</span> sql <span class="k">security definer stable</span>
  <span class="k">set</span> search_path = <span class="s">''</span> <span class="k">as</span> $$
    <span class="k">select</span> workspace_id <span class="k">from</span> public.workspace_members
    <span class="k">where</span> user_id = auth.uid()
  $$;</pre>

  <h2><span class="n">03</span> Scope the tenant tables</h2>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">alter table</span> projects <span class="k">enable row level security</span>;

<span class="k">create policy</span> <span class="s">"members read workspace projects"</span> <span class="k">on</span> projects <span class="k">for select</span>
  <span class="k">using</span> (workspace_id <span class="k">in</span> (<span class="k">select</span> public.user_workspace_ids()));

<span class="k">create policy</span> <span class="s">"members write workspace projects"</span> <span class="k">on</span> projects <span class="k">for insert</span>
  <span class="k">with check</span> (workspace_id <span class="k">in</span> (<span class="k">select</span> public.user_workspace_ids()));</pre>
  <p>For role-gated writes (only admins delete), add the member's role to the function's return and check it in the policy.</p>

  <h2><span class="n">04</span> Prove it</h2>
  <div class="prove">
    <div class="row"><span class="ok">✓</span> a member reads their workspace's projects</div>
    <div class="row"><span class="bad">✗</span> a non-member gets <b>0 rows</b> for that workspace</div>
    <div class="row"><span class="bad">✗</span> a member cannot insert a project into a workspace they don't belong to</div>
  </div>""",
    "related": [
        ("write-owner-scoped-rls-policy-supabase", "Owner-scoped RLS policy (single-user)"),
        ("owner-id-vs-workspace-id-rls-pattern", "owner_id vs workspace_id: which pattern to use"),
        ("test-tenant-isolation-supabase", "Test tenant isolation in Supabase"),
    ],
    "faq": [
        ("Why a security-definer function instead of a subquery?",
         "A policy that directly queries an RLS-protected membership table can recurse (the membership table's own policy re-evaluates). A security-definer function reads membership with elevated rights and returns a plain set of ids, so the policy is a simple IN check with no recursion."),
        ("Is security definer safe here?",
         "Yes, when you pin search_path to '' and keep the function's body minimal and read-only. It only returns the caller's own workspace ids — it never exposes another user's memberships."),
    ],
})

# ---- 5. Test tenant isolation --------------------------------------------
EXTRA.append({
    "slug": "test-tenant-isolation-supabase",
    "title": "How to test tenant isolation in Supabase (RLS)",
    "h1_plain": "How to test tenant isolation in Supabase (RLS)",
    "h1": "How to test tenant isolation in Supabase",
    "desc": "Prove your Supabase RLS actually isolates tenants: an integration test with two signed-in clients that asserts one tenant gets zero rows for another and can't insert on their behalf.",
    "eyebrow": "Supabase RLS · Testing",
    "crumb": "Test tenant isolation",
    "byline": "supabase-js · any test runner",
    "tldr": "Sign in as two real users, have B create a row, then assert A reads <b>0 rows</b> for it and <b>can't insert</b> a row for B. Run it against a real Postgres in CI — a policy you didn't test is a policy you don't have.",
    "body": """  <h2><span class="n">01</span> The only proof that holds</h2>
  <p>You can't eyeball a policy and know it's correct. The proof is behavioral: sign in as tenant A, and confirm A can reach A's rows and <b>cannot</b> reach or write B's. Do it through the client, as <code>authenticated</code> — the SQL editor bypasses RLS, so testing there proves nothing.</p>

  <h2><span class="n">02</span> The test (two signed-in clients)</h2>
  <p class="filelabel">rls.test.ts</p>
  <pre><span class="k">import</span> { createClient } <span class="k">from</span> <span class="s">'@supabase/supabase-js'</span>

<span class="k">const</span> signIn = <span class="k">async</span> (email) => {
  <span class="k">const</span> c = createClient(URL, ANON_KEY)
  <span class="k">await</span> c.auth.signInWithPassword({ email, password: <span class="s">'test-pw'</span> })
  <span class="k">return</span> c
}

test(<span class="s">'A cannot read B rows'</span>, <span class="k">async</span> () => {
  <span class="k">const</span> a = <span class="k">await</span> signIn(<span class="s">'a@test.dev'</span>)
  <span class="k">const</span> b = <span class="k">await</span> signIn(<span class="s">'b@test.dev'</span>)

  <span class="k">const</span> { data: row } = <span class="k">await</span> b.from(<span class="s">'notes'</span>)
    .insert({ title: <span class="s">'B secret'</span> }).select().single()

  <span class="k">const</span> { data } = <span class="k">await</span> a.from(<span class="s">'notes'</span>).select().eq(<span class="s">'id'</span>, row.id)
  expect(data).toHaveLength(<span class="u">0</span>)          <span class="c">// blocked, not just absent</span>
})

test(<span class="s">'A cannot insert for B'</span>, <span class="k">async</span> () => {
  <span class="k">const</span> a = <span class="k">await</span> signIn(<span class="s">'a@test.dev'</span>)
  <span class="k">const</span> { error } = <span class="k">await</span> a.from(<span class="s">'notes'</span>)
    .insert({ title: <span class="s">'x'</span>, user_id: B_ID })
  expect(error).toBeTruthy()                <span class="c">// new row violates RLS</span>
})</pre>

  <h2><span class="n">03</span> What to assert</h2>
  <div class="prove">
    <div class="row"><span class="ok">✓</span> A reads A's rows</div>
    <div class="row"><span class="ok">✓</span> A gets <b>0 rows</b> for B <span style="color:var(--dim)">(blocked, not just filtered by a WHERE)</span></div>
    <div class="row"><span class="bad">✗</span> A cannot INSERT a row for B <span style="color:var(--dim)">(no WITH CHECK hole)</span></div>
    <div class="row"><span class="bad">✗</span> anon (no session) reads nothing</div>
  </div>

  <h2><span class="n">04</span> Run it in CI</h2>
  <p>Point the test at a real Supabase/Postgres (a CI branch database or a local <code>supabase start</code>) and run it on every migration. A new table that ships without a correct policy should turn the build red. To catch the coarser failure — a table with RLS off entirely — add <a href="/rls/rls-in-ci-fail-build-exposed-table/">an RLS gate in CI</a>.</p>""",
    "related": [
        ("rls-in-ci-fail-build-exposed-table", "RLS in CI: fail the build when a table ships exposed"),
        ("write-owner-scoped-rls-policy-supabase", "Owner-scoped RLS policy"),
        ("fix-new-row-violates-row-level-security-policy", "Fix: new row violates row-level security policy"),
    ],
    "faq": [
        ("Should I use pgTAP instead of a JS test?",
         "pgTAP works and runs in the database, but a JS integration test with two real signed-in clients tests the exact path your app uses — auth, the anon key, and the policies together. That end-to-end realism is worth a lot; use whichever your team will actually keep green."),
        ("Why assert zero rows instead of an error on read?",
         "RLS filters reads silently — a blocked SELECT returns an empty set, not an error. So the correct assertion for reads is length 0. Writes, by contrast, raise the row-level-security violation you can assert on directly."),
    ],
})

# ---- 6. Fix permissive USING(true) ---------------------------------------
EXTRA.append({
    "slug": "fix-permissive-rls-policy-using-true",
    "title": "USING (true) is a security hole — how to fix a permissive RLS policy",
    "h1_plain": "USING (true) is a security hole — how to fix a permissive RLS policy",
    "h1": '<span class="mono">USING (true)</span> is a security hole — how to fix it',
    "desc": "A Supabase RLS policy with USING (true) makes the table public read. Here's how to find every permissive policy in your database and replace it with one scoped to the signed-in user.",
    "eyebrow": "Supabase RLS · Fix",
    "crumb": "Fix a permissive USING (true) policy",
    "byline": "Postgres 15 · Supabase",
    "tldr": "<code>USING (true)</code> means 'everyone, always' — it quietly makes the table public read. Find them with a query on <code>pg_policies</code> and replace each with a policy scoped to <code>(select auth.uid())</code> or workspace membership.",
    "body": """  <h2><span class="n">01</span> Why <span class="mono">USING (true)</span> leaks</h2>
  <p>An RLS policy's <code>USING</code> clause is the filter for which rows a caller may see. <code>USING (true)</code> evaluates true for every row and every caller — so anyone with your <code>anon</code> key can read the whole table. It's the second most common Supabase leak, right after RLS being off, and it usually gets copy-pasted in from a tutorial that just wanted the demo to work.</p>

  <h2><span class="n">02</span> Find every permissive policy</h2>
  <p class="filelabel">audit.sql</p>
  <pre><span class="k">select</span> schemaname, tablename, policyname, cmd, qual
<span class="k">from</span> pg_policies
<span class="k">where</span> schemaname = <span class="s">'public'</span>
  <span class="k">and</span> qual = <span class="s">'true'</span>;      <span class="c">-- USING (true)</span></pre>
  <p>Also check <code>with_check = 'true'</code> for permissive writes. Anything that comes back is a table any user can read (or write).</p>

  <h2><span class="n">03</span> Replace it with a scoped policy</h2>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">drop policy</span> <span class="s">"public read"</span> <span class="k">on</span> notes;

<span class="k">create policy</span> <span class="s">"owner reads own notes"</span> <span class="k">on</span> notes <span class="k">for select</span>
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()));</pre>

  <h2><span class="n">04</span> If you actually want public read</h2>
  <p>Sometimes public read is the point (a blog, a public profile). Do it <b>on purpose</b> and scope the columns — don't expose the whole row. Restrict to a published flag and select only safe columns:</p>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">create policy</span> <span class="s">"anyone reads published posts"</span> <span class="k">on</span> posts <span class="k">for select</span>
  <span class="k">using</span> (is_published = true);</pre>
  <p>That still isn't <code>USING (true)</code> — it's a deliberate rule. Keep private columns out of any table that has a public policy.</p>""",
    "related": [
        ("supabase-table-public-rls-off", "Why is my Supabase table public? (RLS is off)"),
        ("write-owner-scoped-rls-policy-supabase", "Owner-scoped RLS policy"),
        ("rls-in-ci-fail-build-exposed-table", "Catch permissive policies in CI"),
    ],
    "faq": [
        ("How is USING (true) different from RLS being off?",
         "Both make the table publicly readable. RLS off means the engine doesn't check policies at all; USING (true) means RLS is on but the policy allows everyone. The audit is different — one shows up in pg_class.relrowsecurity, the other in pg_policies.qual — but the leak is the same."),
        ("Can I keep USING (true) for an internal table?",
         "No — 'internal' tables are still reachable through the anon key. If a table is exposed to Supabase's API at all, USING (true) makes it public. Scope it to the caller, or don't expose it."),
    ],
})

# ---- 7. Table public / RLS off -------------------------------------------
EXTRA.append({
    "slug": "supabase-table-public-rls-off",
    "title": "Why is my Supabase table public? (RLS is off)",
    "h1_plain": "Why is my Supabase table public? (RLS is off)",
    "h1": "Why is my Supabase table public? (RLS is off)",
    "desc": "If your Supabase table has Row-Level Security off, anyone with your anon key can read every row. Here's how to confirm the leak, see it with a single curl, and close it.",
    "eyebrow": "Supabase RLS · Leak",
    "crumb": "Why is my table public? (RLS off)",
    "byline": "Postgres 15 · Supabase",
    "tldr": "Your <code>anon</code> key is public (it ships in the browser). With RLS <b>off</b>, that key can read the whole table over the REST API. Confirm with one <code>curl</code>, then <code>enable row level security</code> and add a policy.",
    "body": """  <h2><span class="n">01</span> The anon key is public — that's by design</h2>
  <p>Supabase's <code>anon</code> key is meant to ship in your frontend. It's not a secret. The thing that stops it from reading everyone's data is RLS. So a table with RLS <b>off</b> is readable by anyone who opens your site's network tab and copies that key. This is the single most common Supabase data leak.</p>

  <h2><span class="n">02</span> See the leak in one command</h2>
  <p class="filelabel">terminal</p>
  <pre><span class="c"># with RLS off, the public anon key returns every row</span>
curl <span class="s">"$SUPABASE_URL/rest/v1/notes?select=*"</span> \\
  -H <span class="s">"apikey: $ANON_KEY"</span>
<span class="bad">-- → returns ALL rows, from every user</span></pre>
  <p>If that returns data you expected to be private, the table is public.</p>

  <h2><span class="n">03</span> Confirm which tables are exposed</h2>
  <p class="filelabel">audit.sql</p>
  <pre><span class="k">select</span> tablename
<span class="k">from</span> pg_tables t
<span class="k">join</span> pg_class c <span class="k">on</span> c.relname = t.tablename
<span class="k">where</span> t.schemaname = <span class="s">'public'</span>
  <span class="k">and</span> c.relrowsecurity = false;   <span class="c">-- RLS is off</span></pre>

  <h2><span class="n">04</span> Close it</h2>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">alter table</span> notes <span class="k">enable row level security</span>;

<span class="k">create policy</span> <span class="s">"owner reads own notes"</span> <span class="k">on</span> notes <span class="k">for select</span>
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()));</pre>
  <p>Then re-run the <code>curl</code> as an anonymous caller — it should now return an empty set. To make sure a new table can never ship like this again, add <a href="/rls/rls-in-ci-fail-build-exposed-table/">an RLS gate in CI</a>.</p>""",
    "related": [
        ("enable-row-level-security-supabase-table", "Enable Row-Level Security on a table"),
        ("rls-in-ci-fail-build-exposed-table", "RLS in CI: fail the build when a table ships exposed"),
        ("fix-permissive-rls-policy-using-true", "USING (true) is a security hole — fix it"),
    ],
    "faq": [
        ("Isn't the anon key protected by my app's login?",
         "No. The anon key works without any login — that's what 'anonymous' means. Your app's login controls your UI, not the REST API. Anyone can call the API directly with the anon key; RLS is what makes that safe."),
        ("Should I hide the anon key instead of enabling RLS?",
         "You can't — it ships to every browser that loads your app. Hiding it is impossible and unnecessary. Enable RLS and the public anon key becomes harmless."),
    ],
})

# ---- 8. Next.js App Router SSR -------------------------------------------
EXTRA.append({
    "slug": "nextjs-app-router-supabase-auth-rls-ssr",
    "title": "Next.js App Router + Supabase auth with RLS (SSR)",
    "h1_plain": "Next.js App Router + Supabase auth with RLS (SSR)",
    "h1": "Next.js App Router + Supabase auth with RLS (SSR)",
    "desc": "Make RLS work in a Next.js App Router server component: create a Supabase server client from the request cookies with @supabase/ssr so auth.uid() resolves — and stop your queries returning an empty array on the server.",
    "eyebrow": "Supabase RLS · Next.js",
    "crumb": "Next.js App Router + Supabase RLS (SSR)",
    "byline": "Next.js 14+ · @supabase/ssr",
    "tldr": "On the server, build the Supabase client from the request <b>cookies</b> with <code>@supabase/ssr</code>, not the bare anon client. Otherwise <code>auth.uid()</code> is null and RLS returns nothing — the classic 'my query is empty on the server' bug.",
    "body": """  <h2><span class="n">01</span> Why server queries come back empty</h2>
  <p>In a Server Component, if you create a plain anon Supabase client, it has no session — so <code>auth.uid()</code> is <code>null</code>, and every owner-scoped policy filters your rows to nothing. The query "works" and returns <code>[]</code>. The fix is to hand the client the user's session, which lives in the request cookies.</p>

  <h2><span class="n">02</span> The server client (from cookies)</h2>
  <p class="filelabel">utils/supabase/server.ts</p>
  <pre><span class="k">import</span> { createServerClient } <span class="k">from</span> <span class="s">'@supabase/ssr'</span>
<span class="k">import</span> { cookies } <span class="k">from</span> <span class="s">'next/headers'</span>

<span class="k">export async function</span> createClient() {
  <span class="k">const</span> store = <span class="k">await</span> cookies()
  <span class="k">return</span> createServerClient(URL, ANON_KEY, {
    cookies: {
      getAll: () => store.getAll(),
      setAll: (list) =>
        list.forEach(({ name, value, options }) => store.set(name, value, options)),
    },
  })
}</pre>

  <h2><span class="n">03</span> Use it in a Server Component</h2>
  <p class="filelabel">app/notes/page.tsx</p>
  <pre><span class="k">const</span> supabase = <span class="k">await</span> createClient()
<span class="k">const</span> { data: notes } = <span class="k">await</span> supabase.from(<span class="s">'notes'</span>).select()
<span class="c">// auth.uid() resolves from the cookie → RLS returns THIS user's notes</span></pre>
  <p>The same client works in Route Handlers and Server Actions. Refresh the session in <code>middleware.ts</code> so the cookie stays valid across requests (the <code>@supabase/ssr</code> docs and the <a href="https://github.com/mateuszingano/nextjs-supabase-starter">nextjs-supabase-starter</a> both wire this up).</p>

  <h2><span class="n">04</span> The service_role trap</h2>
  <p>Don't "fix" the empty result by switching to the <code>service_role</code> key — it bypasses RLS entirely and, if it ever reaches the browser via <code>NEXT_PUBLIC_*</code>, exposes every row. Keep it server-only and rare (webhooks, cron). For user-facing reads, always go through the cookie-based session so RLS still applies.</p>""",
    "related": [
        ("fix-new-row-violates-row-level-security-policy", "Fix: new row violates row-level security policy"),
        ("write-owner-scoped-rls-policy-supabase", "Owner-scoped RLS policy"),
        ("rls-vs-app-layer-authorization", "RLS vs app-layer authorization"),
    ],
    "faq": [
        ("Why not just use the service_role key on the server?",
         "Because it bypasses RLS. Every query then trusts your code to filter correctly, and one missing WHERE is a cross-tenant leak. Use the cookie-based authenticated client so the database enforces isolation for you; reserve service_role for trusted background jobs."),
        ("Does this work in Pages Router / Route Handlers?",
         "Yes. @supabase/ssr has helpers for Pages Router (getServerSideProps) and for Route Handlers; the principle is identical — build the client from the request's cookies so the session, and therefore auth.uid(), is present."),
    ],
})

# ---- 9. RLS in CI --------------------------------------------------------
EXTRA.append({
    "slug": "rls-in-ci-fail-build-exposed-table",
    "title": "RLS in CI: fail the build when a table ships exposed",
    "h1_plain": "RLS in CI: fail the build when a table ships exposed",
    "h1": "RLS in CI: fail the build when a table ships exposed",
    "desc": "Turn RLS from a thing you remember into a thing your pipeline enforces: a CI gate that fails the build when a Supabase table ships with RLS off or a permissive policy.",
    "eyebrow": "Supabase RLS · CI",
    "crumb": "RLS in CI: fail the build",
    "byline": "GitHub Actions · Postgres",
    "tldr": "Add a CI step that scans for tables with RLS off or <code>USING (true)</code> and exits non-zero. The fastest way is <code>npx airlock-rls</code> as a GitHub Action; a raw SQL check is below if you'd rather roll your own.",
    "body": """  <h2><span class="n">01</span> Why a gate, not a checklist</h2>
  <p>Every RLS leak in production started as a table someone forgot to protect. A human checklist misses it eventually; a build that goes red does not. The goal: a new table with RLS off, or a policy with <code>USING (true)</code>, <b>fails the pull request</b> before it can merge.</p>

  <h2><span class="n">02</span> The gate (airlock-rls)</h2>
  <p><code>airlock-rls</code> is a free CI gate that does exactly this — it checks your project for exposed tables and permissive policies and exits non-zero when it finds one.</p>
  <p class="filelabel">.github/workflows/rls.yml</p>
  <pre>jobs:
  rls:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - <span class="k">name</span>: Gate RLS
        <span class="k">run</span>: npx airlock-rls
        <span class="c"># exits 1 if any table ships with RLS off or a permissive policy</span>
        <span class="k">env</span>:
          SUPABASE_DB_URL: ${{ secrets.SUPABASE_DB_URL }}</pre>

  <h2><span class="n">03</span> Or the raw SQL check</h2>
  <p>Prefer to own it? Run this against your migration database and fail if it returns any rows:</p>
  <p class="filelabel">ci-check.sql</p>
  <pre><span class="c">-- any public table with RLS off = fail</span>
<span class="k">select</span> t.tablename
<span class="k">from</span> pg_tables t
<span class="k">join</span> pg_class c <span class="k">on</span> c.relname = t.tablename
<span class="k">where</span> t.schemaname = <span class="s">'public'</span> <span class="k">and</span> c.relrowsecurity = false
<span class="k">union all</span>
<span class="c">-- any permissive policy = fail</span>
<span class="k">select</span> tablename <span class="k">from</span> pg_policies
<span class="k">where</span> schemaname = <span class="s">'public'</span> <span class="k">and</span> (qual = <span class="s">'true'</span> <span class="k">or</span> with_check = <span class="s">'true'</span>);</pre>
  <p>Wrap it so a non-empty result exits <code>1</code>. This catches the coarse failures (RLS off, permissive) — pair it with an <a href="/rls/test-tenant-isolation-supabase/">isolation test</a> for the behavioral proof that policies actually isolate tenants.</p>""",
    "related": [
        ("test-tenant-isolation-supabase", "Test tenant isolation in Supabase"),
        ("supabase-table-public-rls-off", "Why is my Supabase table public? (RLS off)"),
        ("supabase-security-checklist-before-launch", "Supabase security checklist before launch"),
    ],
    "faq": [
        ("Does the gate need production credentials?",
         "No — point it at your migration/CI database (a branch database or a local supabase start), the same schema that will ship. It checks structure (RLS flags and policies), not production data."),
        ("Is the SQL check enough on its own?",
         "It catches the coarse failures — RLS off and permissive policies. It can't tell whether a scoped policy is actually correct; only a behavioral isolation test does that. Run both: the gate for structure, the test for behavior."),
    ],
})

# ---- 10. owner_id vs workspace_id ----------------------------------------
EXTRA.append({
    "slug": "owner-id-vs-workspace-id-rls-pattern",
    "title": "owner_id vs workspace_id: which RLS pattern to use",
    "h1_plain": "owner_id vs workspace_id: which RLS pattern to use",
    "h1": "<span class=\"mono\">owner_id</span> vs <span class=\"mono\">workspace_id</span>: which RLS pattern to use",
    "desc": "Choosing between an owner-scoped and a workspace-scoped RLS model in Supabase: what each looks like, when to pick it, and how to migrate from single-owner to teams later without a rewrite.",
    "eyebrow": "Supabase RLS · Decision",
    "crumb": "owner_id vs workspace_id",
    "byline": "Postgres 15 · Supabase",
    "tldr": "Single-user data? Scope rows to <code>owner_id = auth.uid()</code>. Anything a team shares? Scope to <code>workspace_id</code> + a membership check. If teams are even plausible, start with workspace — retrofitting it later is the painful path.",
    "body": """  <h2><span class="n">01</span> The two models</h2>
  <p><b>Owner-scoped</b> — every row belongs to one user. Simplest possible RLS: <code>user_id = (select auth.uid())</code>. Perfect for personal apps, single-player tools, per-user settings.</p>
  <p><b>Workspace-scoped</b> — rows belong to a team/workspace, and membership decides access. More moving parts (a members table, a membership function), but it's the only model that supports sharing, invites, and roles.</p>

  <h2><span class="n">02</span> How to choose</h2>
  <ul>
    <li><b>Will two people ever need to see the same row?</b> If yes → workspace. If never → owner.</li>
    <li><b>Invites, seats, roles, org billing on the roadmap?</b> → workspace, from day one.</li>
    <li><b>A genuinely personal tool</b> (a journal, a solo dashboard)? → owner. Don't add workspace machinery you'll never use.</li>
  </ul>
  <p>The trap is picking owner because it's easy, then bolting on teams a year later — every table, policy, and query has to change under load. If teams are <em>plausible</em>, the small upfront cost of workspace is cheap insurance.</p>

  <h2><span class="n">03</span> Side by side</h2>
  <p class="filelabel">owner-scoped</p>
  <pre><span class="k">create policy</span> <span class="s">"select own"</span> <span class="k">on</span> notes <span class="k">for select</span>
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()));</pre>
  <p class="filelabel">workspace-scoped</p>
  <pre><span class="k">create policy</span> <span class="s">"members read"</span> <span class="k">on</span> notes <span class="k">for select</span>
  <span class="k">using</span> (workspace_id <span class="k">in</span> (<span class="k">select</span> public.user_workspace_ids()));</pre>

  <h2><span class="n">04</span> Migrating owner → workspace later</h2>
  <p>If you must retrofit: create a workspace per existing user, backfill <code>workspace_id</code> from <code>user_id</code>, add the membership rows (each user is the sole member of their own workspace), then swap the policies. It's doable, but it's a data migration plus a policy rewrite across every table — which is exactly why starting with workspace is worth considering.</p>""",
    "related": [
        ("multi-tenant-rls-workspaces-supabase", "Multi-tenant RLS with workspaces (full pattern)"),
        ("write-owner-scoped-rls-policy-supabase", "Owner-scoped RLS policy"),
        ("supabase-security-checklist-before-launch", "Supabase security checklist before launch"),
    ],
    "faq": [
        ("Can I mix both in one app?",
         "Yes, and many apps do — per-user settings stay owner-scoped while shared resources are workspace-scoped. Just be deliberate about which model each table uses, and keep the membership function as the single source of truth for the workspace side."),
        ("Is workspace-scoped slower?",
         "Slightly, because each policy resolves membership. Keep it fast by resolving membership once in a stable security-definer function and indexing workspace_id. At normal scale the difference is negligible next to the flexibility you gain."),
    ],
})

# ---- 11. RLS vs app-layer authorization ----------------------------------
EXTRA.append({
    "slug": "rls-vs-app-layer-authorization",
    "title": "RLS vs app-layer authorization: which and why",
    "h1_plain": "RLS vs app-layer authorization: which and why",
    "h1": "RLS vs app-layer authorization: which and why",
    "desc": "Should you enforce access in Row-Level Security or in your application code? Why RLS is the security boundary that can't be bypassed, where app-layer checks still belong, and how to use both.",
    "eyebrow": "Supabase RLS · Decision",
    "crumb": "RLS vs app-layer authorization",
    "byline": "Architecture",
    "tldr": "Make <b>RLS the security floor</b> — it's enforced by the database and can't be bypassed by a missing <code>WHERE</code>. Use app-layer checks on top for UX and business rules, never as the only thing between a user and someone else's data.",
    "body": """  <h2><span class="n">01</span> The difference that matters</h2>
  <p>App-layer authorization lives in your code: an <code>if (row.userId !== me)</code> or a <code>.eq('user_id', me)</code> on every query. It works — until the one query that forgot the filter. That single miss is a cross-tenant breach, and it's invisible in code review because the code looks fine.</p>
  <p>RLS lives in the database. Once a policy is on the table, <b>every</b> query — from any client, any endpoint, any forgotten code path — is filtered. There's no query that can accidentally skip it. That's why RLS is a <em>boundary</em> and app-layer checks are <em>convenience</em>.</p>

  <h2><span class="n">02</span> Use RLS as the floor</h2>
  <ul>
    <li><b>Tenant isolation</b> — who can see whose rows. This is security; it belongs in RLS, always.</li>
    <li><b>Ownership and membership</b> — owner-scoped or workspace-scoped access. RLS.</li>
    <li><b>The service_role exception</b> — trusted server jobs bypass RLS on purpose; keep that key server-only.</li>
  </ul>

  <h2><span class="n">03</span> Where app-layer still belongs</h2>
  <ul>
    <li><b>UX</b> — hiding a button the user isn't allowed to use, before they click it.</li>
    <li><b>Business rules</b> — "you can't archive a project with open invoices." Richer than a row filter; fine in code.</li>
    <li><b>Rate limits, workflow state, validation</b> — logic that isn't about row ownership.</li>
  </ul>
  <p>The rule of thumb: if getting it wrong <b>leaks data</b>, it must be in RLS. If getting it wrong is a worse experience or a broken rule, app-layer is fine.</p>

  <h2><span class="n">04</span> Belt and suspenders</h2>
  <p>The strongest setup runs both: RLS guarantees isolation no matter what, and app-layer checks give fast, friendly feedback. If your app-layer filter and your RLS ever disagree, RLS wins — and that's the point. Prove the floor holds with an <a href="/rls/test-tenant-isolation-supabase/">isolation test</a>.</p>""",
    "related": [
        ("test-tenant-isolation-supabase", "Test tenant isolation in Supabase"),
        ("nextjs-app-router-supabase-auth-rls-ssr", "Next.js App Router + Supabase RLS (SSR)"),
        ("supabase-security-checklist-before-launch", "Supabase security checklist before launch"),
    ],
    "faq": [
        ("Is RLS enough on its own?",
         "For tenant isolation, yes — that's exactly what it's built for. You'll still want app-layer logic for UX and business rules, but you don't need app-layer checks to make data access safe once RLS is correct and tested."),
        ("Does RLS replace my API's auth?",
         "No — you still authenticate users (Supabase Auth) and may gate whole endpoints in code. RLS handles row-level access: given an authenticated user, which rows they may touch. The two layers complement each other."),
    ],
})

# ---- 12. PILLAR: security checklist --------------------------------------
EXTRA.append({
    "slug": "supabase-security-checklist-before-launch",
    "title": "Supabase security checklist before launch",
    "h1_plain": "Supabase security checklist before launch",
    "h1": "Supabase security checklist before launch",
    "desc": "The pre-launch Supabase security checklist: RLS on every table, policies scoped to the user, WITH CHECK on writes, no permissive policies, service_role server-only, and an isolation test in CI — each with the guide to do it.",
    "eyebrow": "Supabase RLS · Pillar guide",
    "crumb": "Supabase security checklist before launch",
    "byline": "Postgres 15 · Supabase",
    "tldr": "Before you launch: RLS on <b>every</b> table, every policy scoped to <code>auth.uid()</code> or membership, <code>WITH CHECK</code> on every write, no <code>USING (true)</code>, <code>service_role</code> server-only, and an isolation test that fails the build. The full list, each linked to how to do it, is below.",
    "body": """  <h2><span class="n">01</span> The checklist</h2>
  <p>Run every item before you ship. Each links to the guide that shows the exact fix. If any one fails, you have a leak waiting to happen — not a maybe.</p>
  <div class="cause"><h3>1 · RLS on every table</h3><p>No exceptions, even "internal" tables. On with no policy denies everything — that's the safe starting point. → <a href="/rls/enable-row-level-security-supabase-table/">Enable RLS on a table</a></p></div>
  <div class="cause"><h3>2 · Every policy scoped to the caller</h3><p>Compare <code>user_id</code> to <code>(select auth.uid())</code>, or <code>workspace_id</code> to membership. → <a href="/rls/write-owner-scoped-rls-policy-supabase/">Owner-scoped policy</a> · <a href="/rls/multi-tenant-rls-workspaces-supabase/">Workspace policy</a></p></div>
  <div class="cause"><h3>3 · WITH CHECK on every INSERT and UPDATE</h3><p>No WITH CHECK = users write rows they can't read, or reassign rows to others. → <a href="/rls/fix-new-row-violates-row-level-security-policy/">USING vs WITH CHECK</a></p></div>
  <div class="cause"><h3>4 · No <code>USING (true)</code> anywhere</h3><p>The permissive policy that quietly makes a table public. Audit and scope them. → <a href="/rls/fix-permissive-rls-policy-using-true/">Fix a permissive policy</a></p></div>
  <div class="cause"><h3>5 · <code>service_role</code> key server-only</h3><p>It bypasses RLS. Never in the browser, never in <code>NEXT_PUBLIC_*</code>. → <a href="/rls/nextjs-app-router-supabase-auth-rls-ssr/">Next.js SSR the right way</a></p></div>
  <div class="cause"><h3>6 · An isolation test that fails the build</h3><p>Prove tenant A can't read or write tenant B — in CI, on every migration. → <a href="/rls/test-tenant-isolation-supabase/">Test tenant isolation</a> · <a href="/rls/rls-in-ci-fail-build-exposed-table/">RLS gate in CI</a></p></div>

  <h2><span class="n">02</span> The 30-second version</h2>
  <div class="prove">
    <div class="row"><span class="ok">✓</span> RLS enabled on every table</div>
    <div class="row"><span class="ok">✓</span> every policy scoped to auth.uid() / membership</div>
    <div class="row"><span class="ok">✓</span> WITH CHECK on every INSERT / UPDATE</div>
    <div class="row"><span class="ok">✓</span> no USING (true) anywhere</div>
    <div class="row"><span class="ok">✓</span> service_role key server-only</div>
    <div class="row"><span class="ok">✓</span> an isolation test that fails the build</div>
  </div>

  <h2><span class="n">03</span> Make it the default, not the checklist</h2>
  <p>A checklist you run by hand gets skipped under a deadline. The durable fix is to make the safe path the default: scaffold new projects with RLS already on and an isolation test in place (<a href="https://github.com/mateuszingano/nextjs-supabase-starter"><code>nextjs-supabase-starter</code></a>, <code>supabase-saas-kit</code>), and gate every migration in CI (<code>airlock-rls</code>). Then the checklist becomes something your pipeline enforces, not something you have to remember.</p>""",
    "related": [
        ("enable-row-level-security-supabase-table", "Enable Row-Level Security on a table"),
        ("test-tenant-isolation-supabase", "Test tenant isolation in Supabase"),
        ("rls-in-ci-fail-build-exposed-table", "RLS in CI: fail the build when a table ships exposed"),
    ],
    "faq": [
        ("What's the single most important item?",
         "RLS on every table. It's the one that, if you miss it, makes the table public to anyone with your anon key — the most common Supabase leak by far. Everything else refines access; this one is the boundary."),
        ("How do I keep this from regressing after launch?",
         "Gate it in CI so a new table without RLS, or a permissive policy, fails the build — and keep an isolation test green on every migration. Enforcement beats memory; that's what turns this checklist from a one-time ritual into a guarantee."),
    ],
})


# ---- 13. Supabase Oct 30 2026 grants change ------------------------------
# Fonte: anúncio oficial github.com/orgs/supabase/discussions/45329 (lido 13/10/26).
# Ângulo nosso: o conserto rápido do 42501 (grant em massa) reexpõe tabela sem RLS.
EXTRA.append({
    "slug": "supabase-october-30-grants-change",
    "title": "Supabase's Oct 30 grants change: what breaks, and the fix that leaks",
    "h1_plain": "Supabase's Oct 30 grants change: what breaks, and the fix that leaks",
    "h1": "Supabase's Oct 30 grants change: what breaks, and the fix that leaks",
    "desc": "From Oct 30, 2026, new Supabase tables need an explicit GRANT to reach the Data API. What breaks (42501), the migration that works, and the fix that leaks.",
    "eyebrow": "Supabase RLS · Platform change",
    "crumb": "Oct 30 grants change",
    "byline": "Supabase · October 2026",
    "tldr": "From Oct 30, a <b>new</b> table in <code>public</code> isn't reachable by <code>anon</code> / <code>authenticated</code> until you <code>GRANT</code> it. Existing tables keep working. Put grant + RLS + policies in the <b>same migration</b>. Don't fix a 42501 with <code>grant ... on all tables</code>: that also grants every table that has RLS off.",
    "body": """  <h2><span class="n">01</span> What changes on October 30</h2>
  <p>Until now, every table created in <code>public</code> got full privileges (<code>select / insert / update / delete</code> and more) granted to <code>anon</code>, <code>authenticated</code> and <code>service_role</code> automatically, through default privileges. On <b>October 30, 2026</b> Supabase turns that off for all existing projects (new projects have had it off since a gradual rollout that started May 30). From then on:</p>
  <div class="cause"><h3>New tables</h3><p>Created without a <code>GRANT</code>, they're invisible to the Data API (<code>supabase-js</code>, PostgREST, GraphQL), however you created them: SQL editor, migration, CLI, MCP or an AI tool.</p></div>
  <div class="cause"><h3>Existing tables</h3><p>Not affected. They keep the grants they have today, so your running app keeps working.</p></div>
  <div class="cause"><h3>RLS and policies</h3><p>Unchanged. Grants decide whether a role can touch the table at all; RLS decides which rows.</p></div>
  <p>Direct Postgres connections (psql, an ORM, a server with a connection string) aren't affected. Source: Supabase's <a href="https://github.com/orgs/supabase/discussions/45329">official announcement</a>.</p>

  <h2><span class="n">02</span> What "broken" looks like</h2>
  <p>The first new table after the cutover returns this from the API instead of rows:</p>
  <p class="filelabel">response (example from Supabase's announcement)</p>
  <pre>{
  <span class="s">"code"</span>: <span class="s">"42501"</span>,
  <span class="s">"message"</span>: <span class="s">"permission denied for table invoices"</span>,
  <span class="s">"hint"</span>: <span class="s">"Grant the required privileges to the current role with: GRANT SELECT ON public.invoices TO anon;"</span>
}</pre>
  <p>Postgres rejects the query before RLS even runs. That's the new default working as intended, not a bug in your policies.</p>

  <h2><span class="n">03</span> The fix that leaks</h2>
  <p>The fastest way to make that error go away is the bulk grant from the rollback section of the announcement:</p>
  <p class="filelabel">don't paste this as a fix</p>
  <pre><span class="k">grant select</span>, <span class="k">insert</span>, <span class="k">update</span>, <span class="k">delete</span> <span class="k">on all tables in schema</span> public
  <span class="k">to</span> anon, authenticated, service_role;</pre>
  <p>It works, and it also grants <b>every</b> table in <code>public</code>, including the ones you never meant to expose. Any of those with <b>RLS off</b> becomes readable and writable by anyone holding your anon key, which ships in your frontend. The new default was your chance to stop exposing tables by accident; the bulk grant gives that back. Ask an AI coding tool to "fix the permission error" and this line is a likely answer.</p>
  <p>Grant per table instead, and only what each role needs.</p>

  <h2><span class="n">04</span> The migration pattern that works</h2>
  <p>Treat grant, RLS and policies as one unit, in the same migration, so a table never exists half-configured:</p>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">create table</span> public.invoices (
  id         <span class="k">bigint generated always as identity primary key</span>,
  user_id    uuid <span class="k">not null references</span> auth.users(id),
  amount     numeric <span class="k">not null</span>
);

<span class="k">alter table</span> public.invoices <span class="k">enable row level security</span>;

<span class="k">create policy</span> <span class="s">"owner reads"</span> <span class="k">on</span> public.invoices <span class="k">for select to</span> authenticated
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()));

<span class="c">-- only the role and the operations the app actually uses</span>
<span class="k">grant select on</span> public.invoices <span class="k">to</span> authenticated;</pre>
  <p>No grant to <code>anon</code> here, because signed-out visitors don't read invoices. If a table uses <code>serial</code> / <code>bigserial</code> instead of an identity column and the API inserts into it, the sequence needs its own grant: <code>grant usage, select on sequence public.invoices_id_seq to authenticated;</code></p>

  <h2><span class="n">05</span> Check what the API roles can reach today</h2>
  <p>Run this in the SQL editor. It lists every table and view in <code>public</code>, whether <code>anon</code> or <code>authenticated</code> can read it, and whether RLS is on:</p>
  <p class="filelabel">check.sql</p>
  <pre><span class="k">select</span> c.relname,
       has_any_column_privilege(<span class="s">'anon'</span>, c.oid, <span class="s">'select'</span>)          <span class="k">as</span> anon_can_read,
       has_any_column_privilege(<span class="s">'authenticated'</span>, c.oid, <span class="s">'select'</span>) <span class="k">as</span> auth_can_read,
       c.relrowsecurity                                              <span class="k">as</span> rls_on
<span class="k">from</span> pg_class c
<span class="k">join</span> pg_namespace n <span class="k">on</span> n.oid = c.relnamespace
<span class="k">where</span> n.nspname = <span class="s">'public'</span> <span class="k">and</span> c.relkind <span class="k">in</span> (<span class="s">'r'</span>, <span class="s">'p'</span>, <span class="s">'v'</span>, <span class="s">'m'</span>)
<span class="k">order by</span> 1;</pre>
  <p>A table with <code>anon_can_read = true</code> and <code>rls_on = false</code> can be read by anyone with your anon key. Two details make this stricter than the usual query built on <code>information_schema.table_privileges</code>:</p>
  <div class="cause"><h3>Column grants</h3><p><code>grant select (id, email) on profiles to anon</code> doesn't show up as a table privilege, but the API still serves those columns. <code>has_any_column_privilege</code> catches table and column grants alike.</p></div>
  <div class="cause"><h3>Views</h3><p>Views are reachable through the API too, and by default a view reads its tables as the view's owner, which skips RLS. Create views with <code>security_invoker = on</code> so they respect the caller's RLS.</p></div>

  <h2><span class="n">06</span> Keep it from coming back</h2>
  <p>The new default only protects you while every migration stays honest. Two free checks help there:</p>
  <div class="cause"><h3>In CI</h3><p><a href="https://www.npmjs.com/package/airlock-migrate"><code>npx airlock-migrate</code></a> reads your migration files and fails the build when one creates a table without enabling RLS, or turns RLS off. Those are the tables a bulk grant would expose. It also warns on a view without <code>security_invoker = on</code>. It doesn't flag grants themselves, and it only sees tables that go through your migration files.</p></div>
  <div class="cause"><h3>On the live database</h3><p><code>SUPABASE_DB_URL=... npx airlock-rls</code> checks the running database for tables with RLS off and policies that let everyone through. <a href="/rls/rls-in-ci-fail-build-exposed-table/">Set it up in CI</a>.</p></div>""",
    "related": [
        ("supabase-table-public-rls-off", "Why is my Supabase table public? (RLS is off)"),
        ("enable-row-level-security-supabase-table", "Enable Row-Level Security on a table"),
        ("supabase-security-checklist-before-launch", "Supabase security checklist before launch"),
    ],
    "faq": [
        ("Do my existing tables stop working on October 30?",
         "No. Supabase only changes the default for tables created after the cutover. Existing tables keep their current grants. The first thing that breaks is the next new table you create without a GRANT."),
        ("Does this change make my app more secure by itself?",
         "Only for new tables. Every existing table keeps its old grants, so one that has RLS off today stays readable through the API after October 30. Run the check above and enable RLS on anything that shows anon_can_read true with rls_on false."),
        ("Should I grant to anon or to authenticated?",
         "Grant to the role that actually needs the table. Data only signed-in users see gets a grant to authenticated and no grant to anon. Public data, like a product catalog, can be granted to anon with an RLS policy that allows reading it."),
        ("Is service_role affected?",
         "Yes. It also loses the automatic grants on new tables, so a backend using the service_role key gets 42501 on a new table until you grant it. Once granted, it still bypasses RLS."),
    ],
})
