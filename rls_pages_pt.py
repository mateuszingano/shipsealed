# -*- coding: utf-8 -*-
"""Guias de RLS em português (pt-BR). Importado por gerador-rls.py.

Cada página traduz um guia em inglês: "en" é o slug do original. O gerador
grava em /pt/rls/<slug>/ e liga as duas versões com hreflang. O SQL é o mesmo
do original (testado); só o texto muda. Links: /pt/rls/... quando já existe a
tradução, senão o guia em inglês, avisando "(em inglês)".
"""

PT = []

# ---- Mudança de grants de 30/10 -------------------------------------------
PT.append({
    "en": "supabase-october-30-grants-change",
    "slug": "supabase-mudanca-grants-30-outubro",
    "title": "Mudança de grants do Supabase em 30/10: o que quebra e a correção que vaza",
    "h1_plain": "Mudança de grants do Supabase em 30/10: o que quebra e a correção que vaza",
    "h1": "Mudança de grants do Supabase em 30/10: o que quebra e a correção que vaza",
    "desc": "A partir de 30/10/2026, tabelas novas no Supabase precisam de GRANT explícito pra aparecer na Data API. O que quebra (42501), a migration certa e a correção que vaza dados.",
    "eyebrow": "Supabase RLS · Mudança na plataforma",
    "crumb": "Mudança de grants de 30/10",
    "byline": "Supabase · outubro de 2026",
    "tldr": "A partir de 30/10, uma tabela <b>nova</b> em <code>public</code> fica inacessível pra <code>anon</code> / <code>authenticated</code> até você dar <code>GRANT</code>. Tabelas que já existem continuam funcionando. Coloque grant + RLS + policies na <b>mesma migration</b>. Não resolva o 42501 com <code>grant ... on all tables</code>: isso libera também toda tabela que está com RLS desligado.",
    "body": """  <h2><span class="n">01</span> O que muda em 30 de outubro</h2>
  <p>Até agora, toda tabela criada em <code>public</code> recebia automaticamente privilégios completos (<code>select / insert / update / delete</code> e outros) pra <code>anon</code>, <code>authenticated</code> e <code>service_role</code>, via default privileges. Em <b>30 de outubro de 2026</b> o Supabase desliga isso em todos os projetos existentes (projetos novos já vêm assim desde um rollout gradual que começou em 30 de maio). A partir daí:</p>
  <div class="cause"><h3>Tabelas novas</h3><p>Criadas sem <code>GRANT</code>, ficam invisíveis pra Data API (<code>supabase-js</code>, PostgREST, GraphQL), não importa como foram criadas: SQL editor, migration, CLI, MCP ou ferramenta de IA.</p></div>
  <div class="cause"><h3>Tabelas existentes</h3><p>Não mudam. Continuam com os grants que têm hoje, então o app que está no ar segue funcionando.</p></div>
  <div class="cause"><h3>RLS e policies</h3><p>Iguais. O grant decide se um role pode tocar na tabela; o RLS decide quais linhas.</p></div>
  <p>Conexões diretas ao Postgres (psql, ORM, servidor com connection string) não são afetadas. Fonte: <a href="https://github.com/orgs/supabase/discussions/45329">anúncio oficial do Supabase</a> (em inglês).</p>

  <h2><span class="n">02</span> Como é o "quebrou"</h2>
  <p>A primeira tabela nova depois da virada devolve isso pela API, em vez das linhas:</p>
  <p class="filelabel">resposta (exemplo do anúncio do Supabase)</p>
  <pre>{
  <span class="s">"code"</span>: <span class="s">"42501"</span>,
  <span class="s">"message"</span>: <span class="s">"permission denied for table invoices"</span>,
  <span class="s">"hint"</span>: <span class="s">"Grant the required privileges to the current role with: GRANT SELECT ON public.invoices TO anon;"</span>
}</pre>
  <p>O Postgres recusa a query antes mesmo de o RLS rodar. É o novo padrão funcionando como deveria, não um bug nas suas policies.</p>

  <h2><span class="n">03</span> A correção que vaza</h2>
  <p>O jeito mais rápido de sumir com o erro é o grant em massa da seção de rollback do anúncio:</p>
  <p class="filelabel">não cole isso como correção</p>
  <pre><span class="k">grant select</span>, <span class="k">insert</span>, <span class="k">update</span>, <span class="k">delete</span> <span class="k">on all tables in schema</span> public
  <span class="k">to</span> anon, authenticated, service_role;</pre>
  <p>Funciona, e também libera <b>todas</b> as tabelas de <code>public</code>, inclusive as que você nunca quis expor. Qualquer uma delas com <b>RLS desligado</b> passa a poder ser lida e escrita por quem tiver sua anon key, que vai junto no seu frontend. O novo padrão era a chance de parar de expor tabela sem querer; o grant em massa devolve o problema. Peça pra uma ferramenta de IA "corrigir o erro de permissão" e essa linha é uma resposta bem provável.</p>
  <p>Dê grant por tabela, e só o que cada role precisa.</p>

  <h2><span class="n">04</span> O padrão de migration que funciona</h2>
  <p>Trate grant, RLS e policies como uma coisa só, na mesma migration, pra tabela nunca existir pela metade:</p>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">create table</span> public.invoices (
  id         <span class="k">bigint generated always as identity primary key</span>,
  user_id    uuid <span class="k">not null references</span> auth.users(id),
  amount     numeric <span class="k">not null</span>
);

<span class="k">alter table</span> public.invoices <span class="k">enable row level security</span>;

<span class="k">create policy</span> <span class="s">"owner reads"</span> <span class="k">on</span> public.invoices <span class="k">for select to</span> authenticated
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()));

<span class="c">-- só o role e as operações que o app realmente usa</span>
<span class="k">grant select on</span> public.invoices <span class="k">to</span> authenticated;</pre>
  <p>Sem grant pra <code>anon</code> aqui, porque visitante deslogado não lê fatura. Se a tabela usa <code>serial</code> / <code>bigserial</code> em vez de identity e a API insere nela, a sequence precisa do próprio grant: <code>grant usage, select on sequence public.invoices_id_seq to authenticated;</code></p>

  <h2><span class="n">05</span> Veja o que os roles da API alcançam hoje</h2>
  <p>Rode isso no SQL editor. Lista toda tabela e view de <code>public</code>, se <code>anon</code> ou <code>authenticated</code> conseguem ler, e se o RLS está ligado:</p>
  <p class="filelabel">check.sql</p>
  <pre><span class="k">select</span> c.relname,
       has_any_column_privilege(<span class="s">'anon'</span>, c.oid, <span class="s">'select'</span>)          <span class="k">as</span> anon_can_read,
       has_any_column_privilege(<span class="s">'authenticated'</span>, c.oid, <span class="s">'select'</span>) <span class="k">as</span> auth_can_read,
       c.relrowsecurity                                              <span class="k">as</span> rls_on
<span class="k">from</span> pg_class c
<span class="k">join</span> pg_namespace n <span class="k">on</span> n.oid = c.relnamespace
<span class="k">where</span> n.nspname = <span class="s">'public'</span> <span class="k">and</span> c.relkind <span class="k">in</span> (<span class="s">'r'</span>, <span class="s">'p'</span>, <span class="s">'v'</span>, <span class="s">'m'</span>)
<span class="k">order by</span> 1;</pre>
  <p>Tabela com <code>anon_can_read = true</code> e <code>rls_on = false</code> pode ser lida por qualquer um com a sua anon key. Dois detalhes deixam essa consulta mais rigorosa que a versão comum baseada em <code>information_schema.table_privileges</code>:</p>
  <div class="cause"><h3>Grants de coluna</h3><p><code>grant select (id, email) on profiles to anon</code> não aparece como privilégio de tabela, mas a API continua servindo essas colunas. <code>has_any_column_privilege</code> pega grant de tabela e de coluna.</p></div>
  <div class="cause"><h3>Views</h3><p>Views também aparecem na API e, por padrão, leem as tabelas como o dono da view, pulando o RLS. Crie views com <code>security_invoker = on</code> pra elas respeitarem o RLS de quem chama.</p></div>

  <h2><span class="n">06</span> Pra não voltar a acontecer</h2>
  <p>O novo padrão só te protege enquanto toda migration estiver certa. Dois checks grátis ajudam:</p>
  <div class="cause"><h3>No CI</h3><p><a href="https://www.npmjs.com/package/airlock-migrate"><code>npx airlock-migrate</code></a> lê seus arquivos de migration e quebra o build quando um deles cria tabela sem ligar o RLS, ou desliga o RLS. São justamente as tabelas que um grant em massa exporia. Também avisa sobre view sem <code>security_invoker = on</code>. Ele não aponta os grants em si, e só enxerga tabelas que passam pelos seus arquivos de migration.</p></div>
  <div class="cause"><h3>No banco em produção</h3><p><code>SUPABASE_DB_URL=... npx airlock-rls</code> confere o banco rodando atrás de tabelas com RLS desligado e policies que deixam todo mundo passar. <a href="/rls/rls-in-ci-fail-build-exposed-table/">Configure no CI</a> (em inglês).</p></div>""",
    "related": [
        ("/pt/rls/erro-42501-permission-denied-for-table-supabase/", 'Erro 42501: "permission denied for table"'),
        ("/pt/rls/checklist-seguranca-lovable-supabase/", "Checklist de segurança: Lovable + Supabase"),
        ("/rls/supabase-table-public-rls-off/", "Why is my Supabase table public? (em inglês)"),
        ("/supabase-rls-policy-generator/", "Gerador de policies RLS (em inglês)"),
    ],
    "faq": [
        ("Minhas tabelas atuais param de funcionar em 30 de outubro?",
         "Não. O Supabase só muda o padrão das tabelas criadas depois da virada. As tabelas que já existem mantêm os grants atuais. O primeiro a quebrar é a próxima tabela nova criada sem GRANT."),
        ("Essa mudança deixa meu app mais seguro sozinha?",
         "Só pras tabelas novas. Toda tabela existente mantém os grants antigos, então uma que está com RLS desligado hoje continua legível pela API depois de 30/10. Rode o check acima e ligue o RLS em tudo que aparecer com anon_can_read true e rls_on false."),
        ("Dou grant pra anon ou pra authenticated?",
         "Pro role que realmente precisa da tabela. Dado que só usuário logado vê recebe grant pra authenticated e nenhum pra anon. Dado público, como um catálogo de produtos, pode ter grant pra anon com uma policy de RLS que permita a leitura."),
        ("O service_role também é afetado?",
         "Sim. Ele também perde os grants automáticos em tabelas novas, então um backend usando a chave service_role recebe 42501 numa tabela nova até você dar o grant. Depois do grant, ele continua ignorando o RLS."),
    ],
})

# ---- Erro 42501 permission denied for table -------------------------------
PT.append({
    "en": "fix-permission-denied-for-table-supabase-42501",
    "slug": "erro-42501-permission-denied-for-table-supabase",
    "title": 'Erro 42501 "permission denied for table" no Supabase: como resolver',
    "h1_plain": "Erro 42501: permission denied for table",
    "h1": 'Erro <span class="mono">42501</span>: permission denied for table',
    "desc": "Por que o Supabase devolve 42501 permission denied for table (ou for schema), a diferença pra um erro de RLS e o GRANT por tabela que resolve sem expor as outras tabelas.",
    "eyebrow": "Supabase RLS · Correção de erro",
    "crumb": "Erro 42501: permission denied for table",
    "byline": "Postgres 15 · Supabase",
    "tldr": "O role (<code>anon</code>, <code>authenticated</code> ou <code>service_role</code>) <b>não tem privilégio</b> na tabela, então o Postgres barra a query antes mesmo de o RLS rodar. Dê grant só daquela tabela, só pro role que precisa, na mesma migration que cria a tabela. Nunca resolva com <code>grant ... on all tables</code>.",
    "body": """  <h2><span class="n">01</span> Grants e RLS: duas trancas diferentes</h2>
  <p>Toda query que chega pela Data API passa por duas verificações. Os <b>grants</b> decidem se um role pode tocar na tabela. O <b>RLS</b> decide depois quais linhas. <code>42501 permission denied for table invoices</code> significa que a primeira tranca falhou, então suas policies nem foram consultadas. Problema de RLS tem outra cara: zero linhas, ou <code>new row violates row-level security policy</code>.</p>

  <h2><span class="n">02</span> De onde vem</h2>
  <div class="cause"><span class="tag">CAUSA 1 · tabelas novas</span><h3>Tabela criada depois da mudança de grants do Supabase</h3><p>Tabelas novas não ganham mais grants automáticos pros roles da API. A primeira query numa tabela nova devolve 42501 até você dar o grant. <a href="/pt/rls/supabase-mudanca-grants-30-outubro/">O que mudou em 30/10 e por que importa</a>.</p></div>
  <div class="cause"><span class="tag">CAUSA 2</span><h3>Tabela em outro schema</h3><p>O role também precisa de <code>usage</code> no schema; sem isso, a mensagem é <code>permission denied for schema app</code>.</p></div>
  <div class="cause"><span class="tag">CAUSA 3</span><h3>O grant foi revogado ou nunca foi dado pra esse role</h3><p>Por exemplo, grant pra <code>authenticated</code>, mas quem chama é um visitante deslogado (<code>anon</code>). A Data API responde 401 pra <code>anon</code> e 403 pra <code>authenticated</code>.</p></div>

  <h2><span class="n">03</span> A correção: grant por tabela, com RLS na mesma migration</h2>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">alter table</span> public.invoices <span class="k">enable row level security</span>;

<span class="k">create policy</span> <span class="s">"owner reads"</span> <span class="k">on</span> public.invoices <span class="k">for select to</span> authenticated
  <span class="k">using</span> (user_id = (<span class="k">select</span> auth.uid()));

<span class="c">-- só o role e as operações que o app realmente usa</span>
<span class="k">grant select on</span> public.invoices <span class="k">to</span> authenticated;</pre>
  <p>Pra tabela em outro schema, adicione também <code>grant usage on schema app to authenticated;</code></p>

  <h2><span class="n">04</span> A correção que vaza</h2>
  <pre><span class="c">-- não cole isso pra sumir com o erro</span>
<span class="k">grant select on all tables in schema</span> public <span class="k">to</span> anon, authenticated;</pre>
  <p>Some com o 42501 e libera também todas as outras tabelas de <code>public</code>. Qualquer uma com RLS desligado vira leitura livre pra quem tiver sua anon key pública. Confira o que cada role alcança antes e depois de qualquer grant:</p>
  <p class="filelabel">check.sql</p>
  <pre><span class="k">select</span> c.relname,
       has_table_privilege(<span class="s">'anon'</span>, c.oid, <span class="s">'select'</span>) <span class="k">as</span> anon_can_read,
       c.relrowsecurity <span class="k">as</span> rls_on
<span class="k">from</span> pg_class c <span class="k">join</span> pg_namespace n <span class="k">on</span> n.oid = c.relnamespace
<span class="k">where</span> n.nspname = <span class="s">'public'</span> <span class="k">and</span> c.relkind = <span class="s">'r'</span>
<span class="k">order by</span> 1;</pre>
  <p>Linha com <code>anon_can_read = true</code> e <code>rls_on = false</code> é tabela pública. O <a href="/pt/rls/supabase-mudanca-grants-30-outubro/">guia da mudança de grants</a> tem uma versão mais rigorosa, que também pega grants de coluna e views.</p>
  <p>Se for escrever as policies do zero, o <a href="/supabase-rls-policy-generator/">gerador de policies RLS</a> monta a migration com RLS, policies e só os grants necessários (em inglês).</p>""",
    "related": [
        ("/pt/rls/supabase-mudanca-grants-30-outubro/", "Mudança de grants do Supabase em 30/10"),
        ("/pt/rls/checklist-seguranca-lovable-supabase/", "Checklist de segurança: Lovable + Supabase"),
        ("/rls/fix-pgrst205-could-not-find-table-schema-cache/", "Fix PGRST205: Could not find the table (em inglês)"),
        ("/rls/enable-row-level-security-supabase-table/", "Enable Row-Level Security on a table (em inglês)"),
    ],
    "faq": [
        ("O 42501 é um erro de RLS?",
         "Não. É erro de privilégio, que acontece antes do RLS. O mesmo SQLSTATE aparece quando um insert ou update falha no WITH CHECK de uma policy, mas aí a mensagem é new row violates row-level security policy, e não permission denied for table."),
        ("Preciso dar grant pro service_role também?",
         "Se o seu backend usa a chave service_role numa tabela nova, sim. O service_role ignora o RLS, mas continua precisando do privilégio na tabela."),
    ],
})

# ---- Checklist Lovable + Supabase -----------------------------------------
PT.append({
    "en": "lovable-supabase-security-checklist",
    "slug": "checklist-seguranca-lovable-supabase",
    "title": "Checklist de segurança Lovable + Supabase: seu app está vazando dados?",
    "h1_plain": "Checklist de segurança: Lovable + Supabase",
    "h1": "Checklist de segurança: Lovable + Supabase",
    "desc": "Fez seu app com a Lovable no Supabase? Seis verificações com SQL testado: chave service_role exposta, tabelas públicas, policies sempre verdadeiras, funções liberadas e o teste como estranho.",
    "eyebrow": "Segurança no Supabase · Lovable",
    "crumb": "Checklist de segurança: Lovable + Supabase",
    "byline": "Postgres 15 · Supabase · Lovable",
    "tldr": "A Lovable escreve o app; quem decide quem lê os dados são as suas policies no Supabase. Antes de divulgar o link: procure a chave <code>service_role</code> no app no ar, liste as tabelas que a anon key consegue ler, ache policies sempre verdadeiras e funções que qualquer um executa, e teste deslogado. Cada passo abaixo é uma query ou um clique.",
    "body": """  <h2><span class="n">01</span> Por que apps da Lovable precisam disso</h2>
  <p>Um app da Lovable fala com o Supabase direto do navegador, usando a sua anon key. Isso é normal, e significa que o Row Level Security é a única coisa protegendo seus dados. Quando as policies geradas estão faltando ou abertas demais, qualquer pessoa consegue ler ou escrever nas suas tabelas.</p>
  <p>É isso que o <a href="https://www.cve.org/CVERecord?id=CVE-2025-48757">CVE-2025-48757</a> descreve: policies de RLS insuficientes em sites gerados pela Lovable (até 15/04/2025) deixavam atacantes sem login ler ou escrever tabelas do banco. A Lovable contesta o CVE, dizendo que cada cliente é responsável pelos dados do próprio app. De um jeito ou de outro, a correção é a mesma e fica no seu banco: os passos abaixo.</p>
  <p>Apps da Lovable são feitos com Vite, então toda variável que começa com <code>VITE_</code> vai parar no JavaScript que cada visitante baixa.</p>

  <h2><span class="n">02</span> A chave mestra está no seu frontend?</h2>
  <p>A chave <code>service_role</code> (ou a nova <code>sb_secret_</code>) ignora todas as policies de RLS. Se ela vai pro navegador, qualquer pessoa que abrir o site pode copiá-la e ler ou alterar o banco inteiro. Isso acontece quando ela cai numa variável <code>VITE_</code> ou é colada no código do cliente.</p>
  <p><a href="/service-role-scanner/">Escaneie seu app no ar</a> (grátis, é só colar a URL; página em inglês). Achou? Troque a chave no painel do Supabase (Settings → API), mova pra uma variável só do servidor, publique de novo e escaneie outra vez.</p>
  <p class="filelabel">.env</p>
  <pre><span class="c"># pode ir pro navegador: a URL e a chave anon / publishable</span>
VITE_SUPABASE_URL=https://xyz.supabase.co
VITE_SUPABASE_ANON_KEY=...  <span class="c"># ou uma chave sb_publishable_</span>
<span class="c"># nunca com o prefixo VITE_: iria pra todo visitante</span>
SUPABASE_SERVICE_ROLE_KEY=...</pre>

  <h2><span class="n">03</span> Quais tabelas qualquer um consegue ler?</h2>
  <p>Sua anon key é pública por natureza; o RLS é a única coisa entre ela e seus dados. Rode no SQL editor do Supabase:</p>
  <p class="filelabel">check.sql</p>
  <pre><span class="k">select</span> c.relname,
       has_table_privilege(<span class="s">'anon'</span>, c.oid, <span class="s">'select'</span>) <span class="k">as</span> anon_can_read,
       c.relrowsecurity <span class="k">as</span> rls_on
<span class="k">from</span> pg_class c <span class="k">join</span> pg_namespace n <span class="k">on</span> n.oid = c.relnamespace
<span class="k">where</span> n.nspname = <span class="s">'public'</span> <span class="k">and</span> c.relkind = <span class="s">'r'</span>
<span class="k">order by</span> 1;</pre>
  <p>Toda linha com <code>anon_can_read = true</code> e <code>rls_on = false</code> é uma tabela pública: ligue o RLS e crie as policies.</p>

  <h2><span class="n">04</span> O RLS está ligado, mas está fazendo alguma coisa?</h2>
  <p>"RLS ligado" não é o mesmo que "dado protegido". Uma policy sempre verdadeira deixa todo mundo entrar, e código gerado muitas vezes tem uma. Liste:</p>
  <p class="filelabel">check.sql</p>
  <pre><span class="k">select</span> tablename, policyname, cmd, roles, qual, with_check
<span class="k">from</span> pg_policies
<span class="k">where</span> schemaname = <span class="s">'public'</span>
  <span class="k">and</span> (qual = <span class="s">'true'</span> <span class="k">or</span> with_check = <span class="s">'true'</span>)
<span class="k">order by</span> 1, 2;</pre>
  <p>Só mantenha a linha se a tabela for pública de propósito (um catálogo, uma página de status). Senão, troque por uma policy restrita ao usuário. O <a href="/supabase-rls-policy-generator/">gerador de policies RLS</a> escreve uma por operação, testada (em inglês).</p>

  <h2><span class="n">05</span> Funções que qualquer um pode chamar</h2>
  <p>Uma função <code>security definer</code> roda como o dono dela e pula o RLS. No schema <code>public</code>, ela também vira um endpoint da API (<code>/rest/v1/rpc/…</code>). Liste as que um visitante deslogado consegue executar:</p>
  <p class="filelabel">check.sql</p>
  <pre><span class="k">select</span> p.proname
<span class="k">from</span> pg_proc p <span class="k">join</span> pg_namespace n <span class="k">on</span> n.oid = p.pronamespace
<span class="k">where</span> n.nspname = <span class="s">'public'</span>
  <span class="k">and</span> p.prosecdef
  <span class="k">and</span> has_function_privilege(<span class="s">'anon'</span>, p.oid, <span class="s">'execute'</span>)
<span class="k">order by</span> 1;</pre>
  <p>Pra cada uma: era pra ser pública? Se não, <code>revoke execute on function public.nome(...) from public, anon;</code> ou mova pra um schema que a API não expõe.</p>

  <h2><span class="n">06</span> Prove como um estranho</h2>
  <p>O painel e o SQL editor ignoram o RLS, então sempre parecem certos. Teste como um atacante faria: abra o app numa janela anônima, deslogado, copie a anon key na aba de rede e peça uma tabela privada:</p>
  <p class="filelabel">terminal</p>
  <pre>curl <span class="s">"$SUPABASE_URL/rest/v1/orders?select=*"</span> -H <span class="s">"apikey: $ANON_KEY"</span>
<span class="c"># linhas de outros usuários → a policy está quebrada; [] → tudo certo</span></pre>
  <p>Depois, mantenha corrigido: <code>npx airlock-rls</code> no CI quebra o build quando uma tabela vai pro ar sem RLS ou com policy sempre verdadeira, não importa quem (ou o quê) escreveu a migration.</p>""",
    "related": [
        ("/pt/rls/supabase-mudanca-grants-30-outubro/", "Mudança de grants do Supabase em 30/10"),
        ("/pt/rls/erro-42501-permission-denied-for-table-supabase/", 'Erro 42501: "permission denied for table"'),
        ("/rls/bolt-new-supabase-security-checklist/", "Bolt.new + Supabase security checklist (em inglês)"),
        ("/rls/v0-supabase-security-checklist/", "v0 + Supabase security checklist (em inglês)"),
    ],
    "faq": [
        ("O scan de segurança da Lovable passou. Estou seguro?",
         "Um scan aprovado é um bom começo, não uma prova. Uma policy pode existir e ainda deixar todo mundo entrar (USING (true)). Rode a query de policies sempre verdadeiras e o teste com curl deslogado acima: eles mostram o que um atacante realmente conseguiria."),
        ("Devo esconder a anon key?",
         "Não dá: ela vai no app por natureza. Ela é segura quando o RLS está ligado e toda policy restringe as linhas ao usuário certo. A chave que precisa ficar secreta é a service_role / sb_secret_."),
        ("Posso pedir pra Lovable corrigir as policies?",
         "Pode, e depois confira com as queries acima. Correções geradas pra erros de permissão às vezes abrem mais do que deveriam, como uma policy sempre verdadeira ou um grant amplo."),
    ],
})
