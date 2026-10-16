# -*- coding: utf-8 -*-
"""
ShipSealed · gerador dos guias de RLS (pSEO, inglês).
Mecânica reaproveitada dos gerador-pseo-*.py da frente 11: shell compartilhado,
JSON-LD validado (json.loads) antes de gravar, sitemap por scan.

Cada página é escrita À MÃO (código real, testado) em PAGES abaixo — nada de molde
raso. O gerador só cuida do shell (head/meta/canonical/OG/JSON-LD/nav/footer/CTA) e
da consistência. Saída: dev-site/rls/<slug>/index.html.
"""
import os, io, json, html, re, subprocess

BASE = "https://shipsealed.com"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "rls")

# --- CTA blocks compartilhados (o funil: nossos grátis + cheat sheet) ---
CTA_TOOLS = """  <div class="cta">
    <span class="soon">◆ FREE · MIT · npm + GitHub Action</span>
    <h2>Catch this before it ships</h2>
    <p><code>airlock-rls</code> is a CI gate that fails your build when a table ships exposed or a policy is permissive: the same class of bug, caught in CI against a database with your migrations applied, before it reaches prod.</p>
    <div class="cmd"><span>npx airlock-rls</span><span class="arw">→</span></div>
    <p style="margin-top:18px">Or start from <a href="https://github.com/mateuszingano/nextjs-supabase-starter"><code>nextjs-supabase-starter</code></a> : auth + a table with RLS + an isolation test, so you start from a pattern that's already sealed.</p>
  </div>
  <div class="cta plain">
    <span class="soon">FREE PDF</span>
    <h2 style="font-size:20px">Grab the Supabase RLS cheat sheet</h2>
    <p>The golden rules, the footguns that leak in prod, correct policy snippets, and the isolation test — on one page.</p>
    <form onsubmit="return joinList(event)">
      <input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px">
      <input type="email" id="email" placeholder="you@yourstartup.dev" required aria-label="Email">
      <button type="submit" class="btn">Email me the cheat sheet →</button>
    </form>
    <div class="msg mono" id="msg" style="margin-top:12px;font-size:13.5px;min-height:18px"></div>
  </div>"""

SIGNUP_JS = """<script>
  var SUPABASE_URL='https://ukaelmxvgggvudlwwexk.supabase.co';
  var SUPABASE_KEY='sb_publishable_ZfgF6NCfzH0T32Gjx5l-bw_DwleKw2S';
  async function joinList(e){e.preventDefault();
    var email=document.getElementById('email').value.trim();var msg=document.getElementById('msg');
    if(!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(email)){msg.style.color='var(--red)';msg.textContent='✖ enter a valid email';return false;}
    msg.style.color='var(--dim)';msg.textContent='joining…';var ok=false;
    try{var r=await fetch('/api/join',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:email,source:'rls-guide'})});ok=r.ok;}catch(x){}
    if(!ok){try{var r2=await fetch(SUPABASE_URL+'/rest/v1/waitlist',{method:'POST',headers:{'apikey':SUPABASE_KEY,'Authorization':'Bearer '+SUPABASE_KEY,'Content-Type':'application/json','Prefer':'return=minimal'},body:JSON.stringify({email:email,source:'rls-guide'})});ok=r2.ok||r2.status===409;}catch(x){}}
    msg.style.color=ok?'var(--green)':'var(--red)';
    msg.innerHTML=ok?'✔ on its way — check your inbox. <a href="/assets/supabase-rls-cheatsheet.pdf" style="text-decoration:underline">grab it now →</a>':'✖ something went wrong — try again.';
    return false;}
</script>"""

NAV = """<nav>
  <div class="wrap">
    <a class="logo" href="/"><span class="dot"></span>ShipSealed</a>
    <div class="nav-links">
      <a href="/#tools">Free tools</a>
      <a href="/rls/">RLS guides</a>
      <a href="/cheatsheet/">Cheat sheet</a>
      <a class="gh" href="https://github.com/mateuszingano">GitHub ↗</a>
    </div>
  </div>
</nav>"""

FOOTER = """<footer>
  <div class="wrap">
    <div class="links">
      <a href="/#tools">Free tools</a><a href="/rls/">RLS guides</a><a href="/cheatsheet/">Cheat sheet</a>
      <a href="/#paid">Pricing</a><a href="https://github.com/mateuszingano">GitHub ↗</a>
      <a href="/terms/">Terms</a><a href="/privacy/">Privacy</a><a href="/refunds/">Refunds</a>
    </div>
    <div class="legal">ShipSealed — ship Supabase apps that don't leak 🦭 · Code samples are provided as-is; test against your own database.<br>ShipSealed, CNPJ 23.878.157/0001-10, Canela/RS, Brazil. Payments processed by Paddle.com, our Merchant of Record. Not affiliated with Supabase.</div>
  </div>
</footer>"""

FAVICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
           "<rect width='32' height='32' rx='8' fill='%231fe3b8'/><path d='M9 16.5l4.5 4.5L23 10' "
           "stroke='%23041b0f' stroke-width='3.2' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>")


# --- pt-BR: mesmo shell, textos traduzidos. Páginas PT em /pt/rls/<slug>/ ---
CTA_TOOLS_PT = """  <div class="cta">
    <span class="soon">◆ GRÁTIS · MIT · npm + GitHub Action</span>
    <h2>Pegue isso antes de ir pro ar</h2>
    <p><code>airlock-rls</code> é um gate de CI que quebra o build quando uma tabela vai pro ar exposta ou uma policy é permissiva: o mesmo tipo de bug, pego no CI contra um banco com as suas migrations aplicadas, antes de chegar em produção.</p>
    <div class="cmd"><span>npx airlock-rls</span><span class="arw">→</span></div>
    <p style="margin-top:18px">Ou comece pelo <a href="https://github.com/mateuszingano/nextjs-supabase-starter"><code>nextjs-supabase-starter</code></a>: auth + uma tabela com RLS + um teste de isolamento, pra começar de um padrão que já vem selado.</p>
  </div>
  <div class="cta plain">
    <span class="soon">PDF GRÁTIS</span>
    <h2 style="font-size:20px">Baixe o cheat sheet de RLS do Supabase</h2>
    <p>As regras de ouro, as armadilhas que vazam em produção, policies corretas e o teste de isolamento, numa página só (em inglês).</p>
    <form onsubmit="return joinList(event)">
      <input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px">
      <input type="email" id="email" placeholder="voce@suastartup.dev" required aria-label="Email">
      <button type="submit" class="btn">Quero o cheat sheet →</button>
    </form>
    <div class="msg mono" id="msg" style="margin-top:12px;font-size:13.5px;min-height:18px"></div>
  </div>"""

SIGNUP_JS_PT = (SIGNUP_JS
    .replace("✖ enter a valid email", "✖ digite um email válido")
    .replace("joining…", "enviando…")
    .replace("source:'rls-guide'", "source:'rls-guide-pt'")
    .replace("✔ on its way — check your inbox.", "✔ a caminho — confira seu email.")
    .replace("grab it now →", "baixe agora →")
    .replace("✖ something went wrong — try again.", "✖ algo deu errado — tente de novo."))

NAV_PT = """<nav>
  <div class="wrap">
    <a class="logo" href="/"><span class="dot"></span>ShipSealed</a>
    <div class="nav-links">
      <a href="/#tools">Ferramentas grátis</a>
      <a href="/rls/">Guias de RLS</a>
      <a href="/cheatsheet/">Cheat sheet</a>
      <a class="gh" href="https://github.com/mateuszingano">GitHub ↗</a>
    </div>
  </div>
</nav>"""

FOOTER_PT = """<footer>
  <div class="wrap">
    <div class="links">
      <a href="/#tools">Ferramentas grátis</a><a href="/rls/">Guias de RLS</a><a href="/cheatsheet/">Cheat sheet</a>
      <a href="/#paid">Preços</a><a href="https://github.com/mateuszingano">GitHub ↗</a>
      <a href="/terms/">Termos</a><a href="/privacy/">Privacidade</a><a href="/refunds/">Reembolsos</a>
    </div>
    <div class="legal">ShipSealed — apps Supabase que não vazam 🦭 · Exemplos de código fornecidos como estão; teste no seu próprio banco.<br>ShipSealed, CNPJ 23.878.157/0001-10, Canela/RS, Brasil. Pagamentos processados pela Paddle.com, nossa Merchant of Record. Sem vínculo com o Supabase.</div>
  </div>
</footer>"""

L10N = {
    "en": {"html": "en", "in": "en", "prefix": "/rls/", "home": "Home", "rls": "RLS", "guides": "RLS guides",
           "tested": "✓ code tested against a real database", "related": "Related RLS guides",
           "cta": CTA_TOOLS, "js": SIGNUP_JS, "nav": NAV, "footer": FOOTER},
    "pt": {"html": "pt-BR", "in": "pt-BR", "prefix": "/pt/rls/", "home": "Início", "rls": "RLS", "guides": "Guias de RLS",
           "tested": "✓ código testado num banco de verdade", "related": "Guias relacionados",
           "cta": CTA_TOOLS_PT, "js": SIGNUP_JS_PT, "nav": NAV_PT, "footer": FOOTER_PT},
}


def render(p):
    lang = p.get("lang", "en")
    T = L10N[lang]
    url = BASE + T["prefix"] + p["slug"] + "/"
    hreflang = ""
    switch = ""
    if p.get("alt"):
        en_url = url if lang == "en" else BASE + p["alt"]
        pt_url = url if lang == "pt" else BASE + p["alt"]
        hreflang = ('\n<link rel="alternate" hreflang="en" href="%s">'
                    '\n<link rel="alternate" hreflang="pt-BR" href="%s">'
                    '\n<link rel="alternate" hreflang="x-default" href="%s">') % (en_url, pt_url, en_url)
        switch = (' · <a href="%s" hreflang="pt-BR" lang="pt-BR">Em português</a>' % pt_url if lang == "en"
                  else ' · <a href="%s" hreflang="en" lang="en">Read in English</a>' % en_url)
    # JSON-LD: Article + FAQPage + BreadcrumbList — validado antes de gravar
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "TechArticle", "headline": p["h1_plain"], "description": p["desc"],
             "url": url, "mainEntityOfPage": url, "inLanguage": T["in"],
             "author": {"@type": "Organization", "name": "ShipSealed"},
             "publisher": {"@type": "Organization", "name": "ShipSealed"}},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": T["home"], "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": T["guides"], "item": BASE + "/rls/"},
                {"@type": "ListItem", "position": 3, "name": p["h1_plain"], "item": url}]},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in p["faq"]]},
        ],
    }
    json.loads(json.dumps(ld))  # valida

    related = ""
    if p.get("related"):
        rows = "".join(
            '<a href="%s">%s <span class="arw">→</span></a>' % (s if s.startswith("/") else "/rls/%s/" % s, t)
            for s, t in p["related"])
        related = '<div class="related"><div class="lbl">%s</div>%s</div>' % (T["related"], rows)

    faq_html = "".join(
        "<details><summary>%s</summary><p>%s</p></details>" % (q, a) for q, a in p["faq"])

    doc = """<!doctype html>
<html lang="{html_lang}">
<head>
<script>window.va=window.va||function(){{(window.vaq=window.vaq||[]).push(arguments)}};</script>
<script defer src="/_vercel/insights/script.js"></script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NEVWFBZ3N4"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-NEVWFBZ3N4');</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{url}">{hreflang}
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="{favicon}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{base}/assets/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{base}/assets/og.png">
<link rel="stylesheet" href="/assets/guides.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
{nav}
<main class="wrap">
  <p class="crumb"><a href="/">{home}</a> / <a href="/rls/">{rls}</a> / {crumb}{switch}</p>
  <p class="eyebrow">{eyebrow}</p>
  <h1>{h1}</h1>
  <div class="byline"><span>{byline}</span><span class="ok">{tested}</span></div>
  <div class="tldr"><div class="lbl">TL;DR</div><p>{tldr}</p></div>
{body}
{related}
{cta}
  <h2><span class="n">FAQ</span></h2>
  {faq}
</main>
{footer}
{js}
</body>
</html>
""".format(
        url=url, title=html.escape(p["title"]), desc=html.escape(p["desc"]), favicon=FAVICON,
        html_lang=T["html"], hreflang=hreflang, switch=switch, home=T["home"], rls=T["rls"], tested=T["tested"],
        base=BASE, ld=json.dumps(ld, ensure_ascii=False), nav=T["nav"], crumb=html.escape(p["crumb"]),
        eyebrow=html.escape(p["eyebrow"]), h1=p["h1"], byline=html.escape(p["byline"]),
        tldr=p["tldr"], body=p["body"], related=related, cta=T["cta"], faq=faq_html,
        footer=T["footer"], js=T["js"])
    return doc


def write(p):
    base_dir = os.path.join(HERE, "pt", "rls") if p.get("lang") == "pt" else OUT
    d = os.path.join(base_dir, p["slug"])
    os.makedirs(d, exist_ok=True)
    io.open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render(p))
    return p["slug"]


# =========================================================================
# PAGES — cada uma escrita à mão. Adicionar entradas aqui (código real).
# =========================================================================
PAGES = []

# ---- 1. FLAGSHIP: fix "new row violates row-level security policy" -------
PAGES.append({
    "slug": "fix-new-row-violates-row-level-security-policy",
    "title": 'Fix: "new row violates row-level security policy" (Supabase)',
    "h1_plain": 'Fix: new row violates row-level security policy',
    "h1": 'Fix: <span class="mono">new row violates row-level security policy</span>',
    "desc": "Why Supabase throws new row violates row-level security policy on INSERT, the three real causes, and the correct fix — with a WITH CHECK policy and a test that proves it.",
    "eyebrow": "Supabase RLS · Error fix",
    "crumb": "Fix: new row violates row-level security policy",
    "byline": "Postgres 15 · Supabase",
    "tldr": "Your <code>INSERT</code> is blocked because the new row fails the table's <code>WITH CHECK</code> — usually because there's <b>no INSERT policy</b>, or the row's <code>user_id</code> doesn't equal <code>auth.uid()</code>. Add an INSERT policy with <code>with check (user_id = (select auth.uid()))</code> and make sure the row carries the signed-in user's id.",
    "body": """  <h2><span class="n">01</span> Why you're seeing this</h2>
  <p>Postgres throws <code>new row violates row-level security policy for table "…"</code> when Row-Level Security is <b>on</b> and the row you're writing isn't allowed by any policy's <code>WITH CHECK</code> expression. RLS on with no matching policy means <b>deny</b> — the safe default doing its job, not a bug. It fires on <code>INSERT</code> and on <code>UPDATE</code> (when the updated row would move outside what you're allowed to write).</p>
  <div class="cause"><span class="tag">CAUSE 1 · most common</span><h3>There's no INSERT policy at all</h3><p>You enabled RLS and added a <code>SELECT</code> policy, but never one for <code>INSERT</code>. Reads work, writes are denied — RLS is default-deny per operation.</p></div>
  <div class="cause"><span class="tag">CAUSE 2</span><h3>The row's <span class="mono">user_id</span> doesn't match <span class="mono">auth.uid()</span></h3><p>You have <code>with check (user_id = auth.uid())</code>, but the client inserted the row <b>without</b> setting <code>user_id</code> (so it's <code>null</code>), or set a different id. The check evaluates false → violation.</p></div>
  <div class="cause"><span class="tag">CAUSE 3</span><h3>The request isn't authenticated</h3><p>If the call runs with the <code>anon</code> key and no signed-in session, <code>auth.uid()</code> is <code>null</code>, so <code>user_id = auth.uid()</code> can never be true.</p></div>

  <h2><span class="n">02</span> The fix</h2>
  <p>Give the table an INSERT policy that lets a signed-in user write <b>their own</b> rows, and make sure the row carries their id.</p>
  <p class="filelabel">migration.sql</p>
  <pre><span class="c">-- 1. RLS on (safe to run if it already is)</span>
<span class="k">alter table</span> notes <span class="k">enable row level security</span>;

<span class="c">-- 2. a signed-in user may insert rows that belong to them</span>
<span class="k">create policy</span> <span class="s">"owner inserts own notes"</span> <span class="k">on</span> notes <span class="k">for insert</span>
  <span class="k">with check</span> (user_id = (<span class="k">select</span> auth.uid()));</pre>
  <p>Let the database fill the id so the client can't get it wrong:</p>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">alter table</span> notes
  <span class="k">alter column</span> user_id <span class="k">set default</span> auth.uid();   <span class="c">-- a DEFAULT can't hold a subquery</span></pre>
  <p class="filelabel">insert.ts</p>
  <pre><span class="c">// with the default above, just don't send user_id</span>
<span class="k">await</span> supabase.from(<span class="s">'notes'</span>).insert({ title });

<span class="c">// or set it explicitly from the signed-in user</span>
<span class="k">const</span> { data: { <span class="u">user</span> } } = <span class="k">await</span> supabase.auth.getUser();
<span class="k">await</span> supabase.from(<span class="s">'notes'</span>).insert({ title, user_id: <span class="u">user</span>.id });</pre>
  <p>If cause 3 is yours, the fix is upstream: create the Supabase client with the user's session (their JWT), not the bare anon key — on the server, forward the request cookies so <code>auth.uid()</code> resolves.</p>

  <h2><span class="n">03</span> The gotcha — <span class="mono">USING</span> vs <span class="mono">WITH CHECK</span></h2>
  <ul>
    <li><b><code>USING</code></b> filters rows the user can <b>see or affect</b> — <code>SELECT</code>, <code>UPDATE</code>, <code>DELETE</code>.</li>
    <li><b><code>WITH CHECK</code></b> validates rows the user is <b>writing</b> — <code>INSERT</code> and <code>UPDATE</code>.</li>
  </ul>
  <p>An <code>INSERT</code> policy with only <code>USING</code> and no <code>WITH CHECK</code> doesn't permit the write — that throws this exact violation. For <code>UPDATE</code> you usually need <b>both</b>: <code>USING</code> to pick the row, <code>WITH CHECK</code> so the user can't edit it into someone else's.</p>

  <h2><span class="n">04</span> Prove it — don't hope</h2>
  <p>A policy you didn't test is a policy you don't have. Sign in as tenant A, confirm you can write your own row, and confirm you <b>can't</b> write one for tenant B.</p>
  <div class="prove">
    <div class="row"><span class="ok">✓</span> signed-in A inserts a row for A &nbsp;<span style="color:var(--dim)">→ succeeds</span></div>
    <div class="row"><span class="bad">✗</span> A inserts a row with <b>user_id = B</b> &nbsp;<span style="color:var(--dim)">→ violates RLS (blocked, as it should)</span></div>
    <div class="row"><span class="bad">✗</span> anon (no session) inserts anything &nbsp;<span style="color:var(--dim)">→ violates RLS</span></div>
  </div>
  <p>Run that against a real Postgres in CI on every migration, so a table that ships without a correct write policy turns the build red before production.</p>""",
    "related": [
        ("supabase-october-30-grants-change", "Supabase's Oct 30 grants change: what breaks, and the fix that leaks"),
        ("write-owner-scoped-rls-policy-supabase", "Write an owner-scoped RLS policy (SELECT / INSERT / UPDATE / DELETE)"),
        ("enable-row-level-security-supabase-table", "Enable Row-Level Security on a Supabase table"),
        ("test-tenant-isolation-supabase", "Test tenant isolation in Supabase"),
        ("fix-permissive-rls-policy-using-true", "USING (true) is a security hole — fix a permissive policy"),
    ],
    "faq": [
        ("Does this error mean my table is exposed?",
         "No — the opposite. RLS is on and doing its job (deny by default). The risk is when RLS is off: then there's no error and the table is public. This error means the guardrail is working; you just need a policy that permits the legitimate write."),
        ("Why does the insert work in the SQL editor but fail from my app?",
         "The SQL editor runs as a privileged role that bypasses RLS. Your app runs as authenticated or anon, which RLS applies to. Always test writes the way your app makes them — signed in, through the client."),
        ("Can I just disable RLS to make it go away?",
         "You can, and you'll have made the table public to anyone with your anon key — the #1 Supabase leak. Keep RLS on and add the correct policy instead."),
    ],
})


# páginas 2-12 do lote 1 (conteúdo à mão) vivem em rls_pages_extra.py pra manter este enxuto
try:
    from rls_pages_extra import EXTRA
    PAGES += EXTRA
except ImportError:
    pass

# Traduções pt-BR (rls_pages_pt.py). Cada uma aponta pro slug em inglês ("en");
# as duas versões ganham hreflang uma pra outra. Ficam fora do hub /rls/.
PAGES_PT = []
try:
    from rls_pages_pt import PT
    _by_slug = {p["slug"]: p for p in PAGES}
    for _p in PT:
        _p["lang"] = "pt"
        _en = _by_slug[_p["en"]]
        _p["alt"] = "/rls/%s/" % _en["slug"]
        _en["alt"] = "/pt/rls/%s/" % _p["slug"]
        PAGES_PT.append(_p)
except ImportError:
    pass


def build_index():
    """Hub /rls/ — lista todos os guias. Pillar em destaque."""
    pillar_slug = "supabase-security-checklist-before-launch"
    cards = ""
    for p in PAGES:
        if p["slug"] == pillar_slug:
            continue
        cards += ('<a class="idx" href="/rls/%s/"><span class="k">%s</span>'
                  '<span class="d">%s</span></a>') % (
            p["slug"], html.escape(p["h1_plain"]), html.escape(p["eyebrow"]))
    pillar = next((p for p in PAGES if p["slug"] == pillar_slug), None)
    pillar_html = ""
    if pillar:
        pillar_html = ('<a class="idx pillar" href="/rls/%s/"><span class="soon">◆ START HERE · PILLAR</span>'
                       '<span class="k">%s</span><span class="d">%s</span></a>') % (
            pillar["slug"], html.escape(pillar["h1_plain"]), html.escape(pillar["desc"]))
    # JSON-LD do hub: CollectionPage + BreadcrumbList + ItemList (todas as guias, pillar 1o) — validado
    ordered = ([pillar] if pillar else []) + [p for p in PAGES if p["slug"] != pillar_slug]
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "name": "Supabase RLS guides",
             "headline": "Supabase RLS guides",
             "description": "Practical, tested guides to Supabase Row-Level Security: enable it, scope policies, go multi-tenant, fix the common errors, and prove tenant isolation in CI.",
             "url": BASE + "/rls/", "inLanguage": "en",
             "publisher": {"@type": "Organization", "name": "ShipSealed"}},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "RLS guides", "item": BASE + "/rls/"}]},
            {"@type": "ItemList", "name": "Supabase RLS guides", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": p["h1_plain"],
                 "url": BASE + "/rls/" + p["slug"] + "/"}
                for i, p in enumerate(ordered)]},
        ],
    }
    json.loads(json.dumps(ld))  # valida
    ld_json = json.dumps(ld)
    doc = """<!doctype html>
<html lang="en">
<head>
<script>window.va=window.va||function(){{(window.vaq=window.vaq||[]).push(arguments)}};</script>
<script defer src="/_vercel/insights/script.js"></script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-NEVWFBZ3N4"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-NEVWFBZ3N4');</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{base}/rls/">
<title>Supabase RLS guides — ShipSealed</title>
<meta name="description" content="Practical, tested guides to Supabase Row-Level Security: enable it, scope policies, go multi-tenant, fix the common errors, and prove tenant isolation in CI.">
<link rel="icon" href="{favicon}">
<meta property="og:type" content="website">
<meta property="og:url" content="{base}/rls/">
<meta property="og:title" content="Supabase RLS guides — ShipSealed">
<meta property="og:description" content="Tested guides to Supabase Row-Level Security — enable it, scope policies, go multi-tenant, fix common errors, prove isolation.">
<meta property="og:image" content="{base}/assets/og.png">
<link rel="stylesheet" href="/assets/guides.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
{nav}
<main class="wrap">
  <p class="eyebrow">ShipSealed · guides</p>
  <h1>Supabase RLS guides</h1>
  <p style="color:var(--muted);font-size:17px;max-width:640px;margin:0 0 6px">Row-Level Security done right — enable it, scope policies, go multi-tenant, fix the errors that leak, and prove tenant isolation with tests. Every snippet is real and tested against a database.</p>
  {pillar}
  {cards}
  <div class="cta plain" style="margin-top:30px">
    <span class="soon">FREE · MIT</span>
    <h2 style="font-size:20px">Make RLS the default</h2>
    <p>Start from <a href="https://github.com/mateuszingano/nextjs-supabase-starter"><code>nextjs-supabase-starter</code></a>, gate it in CI with <code>npx airlock-rls</code>, or grab the <a href="/cheatsheet/">one-page cheat sheet</a>.</p>
  </div>
</main>
{footer}
</body>
</html>
""".format(base=BASE, favicon=FAVICON, nav=NAV, footer=FOOTER, pillar=pillar_html, cards=cards, ld=ld_json)
    io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(doc)


RE_NOINDEX = re.compile(r'<meta\s+name="robots"[^>]*content="[^"]*noindex', re.I)


def _versionados():
    """Arquivos que o git rastreia = o que realmente vai pro ar no push.

    Página existente no disco mas não commitada ainda NÃO está publicada, e
    sitemap apontando pra 404 é pior do que página faltando no sitemap. Quando
    o arquivo for commitado, ele entra no sitemap sozinho na próxima geração.
    """
    out = subprocess.run(["git", "-C", HERE, "ls-files", "*.html"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("ABORTADO: 'git ls-files' falhou — sem saber o que está publicado, "
                         "não dá pra montar o sitemap com honestidade.\n" + out.stderr)
    return set(p.strip().replace("/", os.sep) for p in out.stdout.splitlines() if p.strip())


def paginas_indexaveis():
    """Caminhos de URL de toda página que PODE e DEVE ser indexada.

    Entra se: é uma `index.html` (o site serve por pasta), está versionada, e
    não declara `noindex`. Assim o funil (checkout/subscribe/welcome) e os stubs
    de redirect (pricing) ficam de fora sozinhos, sem lista pra manter.
    """
    versionados = _versionados()
    fora = {".git", "__pycache__", "_internal", "assets", "api", "node_modules"}
    caminhos = []
    for dirpath, dirnames, files in os.walk(HERE):
        dirnames[:] = [d for d in dirnames if d not in fora]
        if "index.html" not in files:
            continue
        full = os.path.join(dirpath, "index.html")
        rel = os.path.relpath(full, HERE)
        if rel not in versionados:
            continue
        if RE_NOINDEX.search(io.open(full, encoding="utf-8", errors="replace").read()):
            continue
        url = rel.replace(os.sep, "/")[:-len("index.html")]
        caminhos.append("/" + url)
    # "/" primeiro (é a de maior prioridade), o resto em ordem estável
    return sorted(caminhos, key=lambda p: (p != "/", p))


def build_sitemap():
    slugs = sorted(d for d in os.listdir(OUT)
                   if os.path.isdir(os.path.join(OUT, d))
                   and os.path.exists(os.path.join(OUT, d, "index.html"))) if os.path.isdir(OUT) else []
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
          '  <url><loc>%s/rls/</loc><changefreq>weekly</changefreq></url>' % BASE]
    for s in slugs:
        sm.append('  <url><loc>%s/rls/%s/</loc><changefreq>monthly</changefreq></url>' % (BASE, s))
    sm.append('</urlset>')
    io.open(os.path.join(HERE, "rls-sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm) + "\n")

    # sitemap.xml principal: TODAS as páginas indexáveis, descobertas por scan.
    # (Era uma lista escrita à mão e ela tinha saído da realidade: listava a
    # /pricing/, que é um stub noindex, e não listava /demo/, /service-role-scanner/
    # nem /compare/…, que estão no ar e querem ranquear. Lista à mão não acompanha
    # o site — mesma lição do sitemap das calculadoras, 29/07/26.)
    main = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path in paginas_indexaveis():
        pr = ' <priority>1.0</priority>' if path == "/" else ''
        freq = 'monthly' if path.startswith("/rls/") and path != "/rls/" else 'weekly'
        main.append('  <url><loc>%s%s</loc><changefreq>%s</changefreq>%s</url>' % (BASE, path, freq, pr))
    main.append('</urlset>')
    io.open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(main) + "\n")
    return len(slugs)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    done = [write(p) for p in PAGES]
    done_pt = [write(p) for p in PAGES_PT]
    build_index()
    n = build_sitemap()
    print("Páginas geradas:", len(done))
    for s in done:
        print("  ·", "/rls/" + s + "/")
    print("Sitemap (rls-sitemap.xml):", n, "URLs de guia")
