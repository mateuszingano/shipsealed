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
       has_any_column_privilege(<span class="s">'anon'</span>, c.oid, <span class="s">'select'</span>) <span class="k">as</span> anon_can_read,
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
       has_any_column_privilege(<span class="s">'anon'</span>, c.oid, <span class="s">'select'</span>) <span class="k">as</span> anon_can_read,
       c.relrowsecurity <span class="k">as</span> rls_on
<span class="k">from</span> pg_class c <span class="k">join</span> pg_namespace n <span class="k">on</span> n.oid = c.relnamespace
<span class="k">where</span> n.nspname = <span class="s">'public'</span> <span class="k">and</span> c.relkind = <span class="s">'r'</span>
<span class="k">order by</span> 1;</pre>
  <p>Toda linha com <code>anon_can_read = true</code> e <code>rls_on = false</code> é uma tabela pública: ligue o RLS e crie as policies.</p>
  <div class="cause"><h3>Grants de coluna</h3><p><code>grant select (id, email) on profiles to anon</code> não aparece como privilégio de tabela, mas a API continua servindo essas colunas. <code>has_any_column_privilege</code> pega grant de tabela e de coluna.</p></div>

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

# ---- Upload no Storage: new row violates row-level security policy -------
PT.append({
    "en": "supabase-storage-upload-new-row-violates-row-level-security",
    "slug": "erro-upload-storage-new-row-violates-row-level-security",
    "title": 'Upload no Supabase Storage: "new row violates row-level security policy" (como resolver)',
    "h1_plain": "Upload no Supabase Storage: new row violates row-level security policy",
    "h1": 'Upload no Storage falha: <span class="mono">new row violates row-level security policy</span>',
    "desc": "Por que o upload no Supabase Storage devolve 403 new row violates row-level security policy, a policy em storage.objects que resolve (limitada à pasta do usuário) e por que o upsert precisa de mais duas.",
    "eyebrow": "Supabase Storage · Correção de erro",
    "crumb": "Upload no Storage: new row violates RLS",
    "byline": "Postgres 15 · Supabase Storage",
    "tldr": "Todo arquivo é uma linha em <code>storage.objects</code>, e o RLS está ligado lá. Sem uma policy de INSERT que aceite o caminho, o upload é recusado com 403. Crie uma policy de INSERT pro bucket que amarre a primeira pasta ao <code>auth.uid()</code> e faça o upload em <code>&lt;id do usuário&gt;/arquivo</code>. Substituir um arquivo (<code>upsert: true</code>) também exige policies de SELECT e UPDATE.",
    "body": """  <h2><span class="n">01</span> O que é o erro</h2>
  <p>A API do Storage transforma o erro do Postgres em HTTP 403:</p>
  <p class="filelabel">resposta</p>
  <pre>{ <span class="s">"error"</span>: <span class="s">"Unauthorized"</span>, <span class="s">"message"</span>: <span class="s">"new row violates row-level security policy"</span> }</pre>
  <p>Um upload insere uma linha em <code>storage.objects</code> (bucket, caminho, dono). Essa tabela tem RLS ligado e, por padrão, nenhuma policy deixa alguém inserir, então todo upload feito pelo cliente é recusado até você criar uma. Deixar o bucket público não muda isso: "público" só vale pra download.</p>

  <h2><span class="n">02</span> A policy: cada usuário sobe na própria pasta</h2>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">create policy</span> <span class="s">"users upload to their folder"</span> <span class="k">on</span> storage.objects
  <span class="k">for insert to</span> authenticated
  <span class="k">with check</span> (
    bucket_id = <span class="s">'avatars'</span>
    <span class="k">and</span> (storage.foldername(name))[1] = (<span class="k">select</span> auth.uid())::text
  );</pre>
  <p><code>storage.foldername(name)</code> devolve as pastas do caminho, então em <code>&lt;id do usuário&gt;/avatar.png</code> a primeira é o id do usuário. O upload precisa usar esse caminho:</p>
  <p class="filelabel">upload.ts</p>
  <pre><span class="k">const</span> { data: { <span class="u">user</span> } } = <span class="k">await</span> supabase.auth.getUser();
<span class="k">await</span> supabase.storage.from(<span class="s">'avatars'</span>).upload(<span class="s">`${<span class="u">user</span>.id}/avatar.png`</span>, file);</pre>

  <h2><span class="n">03</span> Por que ainda falha</h2>
  <div class="cause"><span class="tag">CAUSA 1</span><h3>O caminho não começa com o id do usuário</h3><p>Um arquivo na raiz do bucket (<code>avatar.png</code>) não tem pasta, então a checagem dá falso. A pasta de outro usuário também.</p></div>
  <div class="cause"><span class="tag">CAUSA 2</span><h3>Usuário não logado</h3><p>O cliente chama como <code>anon</code>, o <code>auth.uid()</code> vem nulo e uma policy <code>to authenticated</code> não se aplica.</p></div>
  <div class="cause"><span class="tag">CAUSA 3 · upsert</span><h3>Substituir arquivo com <span class="mono">upsert: true</span></h3><p>Sobrescrever um caminho que já existe é um insert que vira update, e o Postgres exige também policies de SELECT e UPDATE. Só com a de INSERT, o upsert é recusado até pra um caminho que ainda não existe.</p></div>
  <p class="filelabel">migration.sql (só se você usa upsert ou lê os arquivos de volta)</p>
  <pre><span class="k">create policy</span> <span class="s">"users read their folder"</span> <span class="k">on</span> storage.objects <span class="k">for select to</span> authenticated
  <span class="k">using</span> (bucket_id = <span class="s">'avatars'</span> <span class="k">and</span> (storage.foldername(name))[1] = (<span class="k">select</span> auth.uid())::text);

<span class="k">create policy</span> <span class="s">"users update their folder"</span> <span class="k">on</span> storage.objects <span class="k">for update to</span> authenticated
  <span class="k">using</span> (bucket_id = <span class="s">'avatars'</span> <span class="k">and</span> (storage.foldername(name))[1] = (<span class="k">select</span> auth.uid())::text);</pre>

  <h2><span class="n">04</span> Prove</h2>
  <div class="prove">
    <div class="row"><span class="bad">✗</span> sem policy de INSERT &nbsp;<span style="color:var(--dim)">→ new row violates row-level security policy</span></div>
    <div class="row"><span class="ok">✓</span> A sobe em <code>A/me.png</code> &nbsp;<span style="color:var(--dim)">→ ok</span></div>
    <div class="row"><span class="ok">✓</span> A sobe em <code>B/x.png</code>, na raiz ou em outro bucket &nbsp;<span style="color:var(--dim)">→ recusado</span></div>
    <div class="row"><span class="ok">✓</span> upsert só com INSERT, depois INSERT + UPDATE &nbsp;<span style="color:var(--dim)">→ recusado; com SELECT também → ok</span></div>
  </div>
  <p>Não "resolva" com <code>with check (true)</code>: isso deixa qualquer um com a sua anon key pública gravar em qualquer lugar do bucket.</p>""",
    "related": [
        ("/pt/rls/erro-upsert-new-row-violates-row-level-security/", "Upsert: new row violates row-level security policy"),
        ("/pt/rls/checklist-seguranca-lovable-supabase/", "Checklist de segurança: Lovable + Supabase"),
        ("/rls/fix-new-row-violates-row-level-security-policy/", 'Fix: "new row violates row-level security policy" (em inglês)'),
        ("/rls/fix-permissive-rls-policy-using-true/", "USING (true) is a security hole (em inglês)"),
    ],
    "faq": [
        ("Deixei o bucket público. Por que o upload ainda falha?",
         "Público só quer dizer que os arquivos podem ser baixados sem token. Upload, atualização e exclusão continuam passando pelas policies de RLS em storage.objects."),
        ("Posso fazer o upload com a chave service_role?",
         "De um servidor, sim: ela ignora o RLS. Nunca do navegador, onde a chave ficaria exposta. Pra upload do usuário, uma policy de INSERT restrita é o caminho certo."),
    ],
})

# ---- Upsert: new row violates row-level security policy -------------------
PT.append({
    "en": "supabase-upsert-new-row-violates-row-level-security",
    "slug": "erro-upsert-new-row-violates-row-level-security",
    "title": 'Upsert no Supabase: "new row violates row-level security policy" mesmo com policy de INSERT',
    "h1_plain": "Upsert no Supabase falha com new row violates row-level security policy",
    "h1": 'Upsert falha: <span class="mono">new row violates row-level security policy</span>',
    "desc": "O insert funciona, mas o upsert() falha com new row violates row-level security policy. Por que o ON CONFLICT DO UPDATE precisa das policies de SELECT e UPDATE, mesmo pra uma linha nova.",
    "eyebrow": "Supabase RLS · Correção de erro",
    "crumb": "Upsert: new row violates RLS",
    "byline": "Postgres 15 · Supabase",
    "tldr": "O <code>upsert()</code> vira <code>insert ... on conflict do update</code>. Pra isso, o Postgres confere as policies de UPDATE e SELECT além da de INSERT, e faz isso mesmo quando a linha é nova. Crie uma policy de UPDATE (com a mesma condição de dono) e uma de SELECT, e dê grant de <code>update</code>.",
    "body": """  <h2><span class="n">01</span> Por que o insert funciona e o upsert não</h2>
  <p>Por padrão, <code>supabase.from('profiles').upsert(row)</code> é enviado como <code>insert ... on conflict (id) do update</code>. Um comando que <i>pode</i> atualizar precisa de todas as policies que talvez use: INSERT pra linha nova, UPDATE pra linha existente e SELECT pra ler a linha com que conflita. Se a de UPDATE ou a de SELECT faltar, o Postgres recusa o comando logo de cara com <code>new row violates row-level security policy</code>, mesmo quando a linha ainda não existe.</p>

  <h2><span class="n">02</span> A correção</h2>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">create policy</span> <span class="s">"owner inserts"</span> <span class="k">on</span> profiles <span class="k">for insert to</span> authenticated
  <span class="k">with check</span> (id = (<span class="k">select</span> auth.uid()));

<span class="k">create policy</span> <span class="s">"owner updates"</span> <span class="k">on</span> profiles <span class="k">for update to</span> authenticated
  <span class="k">using</span> (id = (<span class="k">select</span> auth.uid()));

<span class="k">create policy</span> <span class="s">"owner reads"</span> <span class="k">on</span> profiles <span class="k">for select to</span> authenticated
  <span class="k">using</span> (id = (<span class="k">select</span> auth.uid()));

<span class="k">grant select, insert, update on</span> profiles <span class="k">to</span> authenticated;</pre>
  <p>Mantenha as três com a mesma condição de dono. O usuário continua sem conseguir fazer upsert com o id de outra pessoa: a checagem do INSERT recusa.</p>

  <h2><span class="n">03</span> Se você só insere</h2>
  <p>Se a linha nunca deve ser sobrescrita, não use <code>upsert()</code>. Use <code>insert()</code> e trate o erro de chave duplicada (<code>23505</code>), ou passe <code>{ ignoreDuplicates: true }</code> pra requisição virar <code>on conflict do nothing</code>.</p>

  <h2><span class="n">04</span> Prove</h2>
  <div class="prove">
    <div class="row"><span class="bad">✗</span> só policy de INSERT, upsert de linha nova &nbsp;<span style="color:var(--dim)">→ new row violates row-level security policy</span></div>
    <div class="row"><span class="ok">✓</span> insert comum com a mesma policy &nbsp;<span style="color:var(--dim)">→ ok</span></div>
    <div class="row"><span class="bad">✗</span> INSERT + UPDATE, sem SELECT &nbsp;<span style="color:var(--dim)">→ continua recusado</span></div>
    <div class="row"><span class="ok">✓</span> INSERT + UPDATE + SELECT &nbsp;<span style="color:var(--dim)">→ ok; id de outro usuário → recusado</span></div>
  </div>""",
    "related": [
        ("/pt/rls/erro-upload-storage-new-row-violates-row-level-security/", "Upload no Storage: new row violates RLS"),
        ("/pt/rls/erro-42501-permission-denied-for-table-supabase/", 'Erro 42501: "permission denied for table"'),
        ("/rls/supabase-update-delete-not-working-rls/", "Supabase update or delete does nothing (em inglês)"),
        ("/supabase-rls-policy-generator/", "Gerador de policies RLS (em inglês)"),
    ],
    "faq": [
        ("Por que o Postgres precisa de SELECT num upsert?",
         "Pra detectar o conflito ele precisa olhar a linha existente, e essa leitura passa pelas suas policies de SELECT. Sem nenhuma, o upsert não pode ser checado e é recusado."),
        ("Isso vale também pro upload no Storage com upsert: true?",
         "Vale. Substituir um arquivo é um upsert em storage.objects, então ele precisa de policies de SELECT e UPDATE além da de INSERT."),
    ],
})

# ---- PGRST202 Could not find the function --------------------------------
PT.append({
    "en": "fix-pgrst202-could-not-find-function-schema-cache",
    "slug": "erro-pgrst202-could-not-find-function-supabase",
    "title": 'Erro PGRST202 "Could not find the function ... in the schema cache" no Supabase (RPC)',
    "h1_plain": "Erro PGRST202: Could not find the function in the schema cache",
    "h1": 'Erro <span class="mono">PGRST202</span>: Could not find the function in the schema cache',
    "desc": "Por que o supabase.rpc() devolve PGRST202 Could not find the function public.fn(...) in the schema cache: nomes de parâmetro diferentes, schema errado, cache desatualizado, e o grant que vem depois.",
    "eyebrow": "Supabase · Correção de erro",
    "crumb": "Erro PGRST202: Could not find the function",
    "byline": "Postgres 15 · Supabase",
    "tldr": "A Data API procura a função pelo nome <b>e pelos nomes dos argumentos que você manda</b>. Se você chama <code>rpc('get_orders', { userId })</code> e o parâmetro da função é <code>p_user_id</code>, ela não é encontrada. Mande os nomes exatos dos parâmetros, mantenha a função num schema exposto e recarregue o cache depois de criá-la.",
    "body": """  <h2><span class="n">01</span> Leia a mensagem</h2>
  <p class="filelabel">resposta</p>
  <pre>{
  <span class="s">"code"</span>: <span class="s">"PGRST202"</span>,
  <span class="s">"message"</span>: <span class="s">"Could not find the function public.get_orders(userId) in the schema cache"</span>
}</pre>
  <p>Os parênteses listam os nomes dos argumentos que <b>o seu cliente mandou</b>, não os da função. Compare com a definição: essa diferença é a causa mais comum. O status HTTP é 404.</p>

  <h2><span class="n">02</span> As causas</h2>
  <div class="cause"><span class="tag">CAUSA 1 · mais comum</span><h3>Os nomes dos argumentos não batem</h3><p>Os argumentos da RPC são casados pelo nome. A função abaixo precisa ser chamada com <code>p_user_id</code>, não <code>userId</code> nem <code>user_id</code>.</p></div>
  <div class="cause"><span class="tag">CAUSA 2</span><h3>A função não está num schema exposto</h3><p>Só os schemas listados nas configurações da Data API são servidos. Uma função em <code>private</code> fica invisível pro <code>rpc()</code>, o que normalmente é o que você quer pra funções auxiliares.</p></div>
  <div class="cause"><span class="tag">CAUSA 3</span><h3>Cache desatualizado</h3><p>A função acabou de ser criada ou mudou de assinatura.</p></div>
  <p class="filelabel">função e chamada</p>
  <pre><span class="k">create function</span> public.get_orders(p_user_id uuid)
<span class="k">returns setof</span> orders <span class="k">language</span> sql <span class="k">stable as</span> $$
  <span class="k">select</span> * <span class="k">from</span> public.orders <span class="k">where</span> user_id = p_user_id
$$;

<span class="c">-- cliente: a chave tem que ser o nome do parâmetro</span>
<span class="c">-- await supabase.rpc('get_orders', { p_user_id: user.id })</span>

<span class="k">notify</span> pgrst, <span class="s">'reload schema'</span>;   <span class="c">-- depois de criar ou alterar</span></pre>

  <h2><span class="n">03</span> O próximo erro: permissão</h2>
  <p>Depois de encontrada, o role de quem chama precisa de <code>execute</code>, senão o erro vira <code>42501 permission denied for function get_orders</code>. Dê permissão só pros roles que devem chamar:</p>
  <pre><span class="k">revoke execute on function</span> public.get_orders(uuid) <span class="k">from</span> public, anon;
<span class="k">grant execute on function</span> public.get_orders(uuid) <span class="k">to</span> authenticated;</pre>
  <p>Funções novas podem ser executadas por todo mundo por padrão (o Postgres dá <code>execute</code> pra <code>public</code>), então revogue primeiro se a função não deve ser pública. Uma função <code>security definer</code> ignora o RLS: <a href="/pt/rls/checklist-seguranca-lovable-supabase/">veja como listar as que anon consegue chamar</a>.</p>

  <h2><span class="n">04</span> Duas funções com o mesmo nome</h2>
  <p>Sobrecargas que só mudam o tipo dão outro erro, <code>PGRST203 Could not choose the best candidate function</code>. Renomeie uma ou dê nomes diferentes aos parâmetros.</p>""",
    "related": [
        ("/pt/rls/erro-pgrst200-could-not-find-relationship-supabase/", "Erro PGRST200: Could not find a relationship"),
        ("/pt/rls/erro-42501-permission-denied-for-table-supabase/", 'Erro 42501: "permission denied for table"'),
        ("/rls/fix-pgrst205-could-not-find-table-schema-cache/", "Fix PGRST205: Could not find the table (em inglês)"),
        ("/pt/rls/checklist-seguranca-lovable-supabase/", "Checklist de segurança: Lovable + Supabase"),
    ],
    "faq": [
        ("Funciona no SQL editor. Por que não pelo rpc()?",
         "O SQL editor chama a função direto, com argumentos por posição ou nome, e como um role privilegiado. O rpc() passa pela Data API, que casa os argumentos pelo nome, só enxerga schemas expostos e roda como anon ou authenticated."),
        ("A ordem dos argumentos importa?",
         "Não. A Data API casa os argumentos pelo nome, então a ordem não importa, mas cada nome precisa existir na lista de parâmetros da função."),
    ],
})

# ---- PGRST200 Could not find a relationship -------------------------------
PT.append({
    "en": "fix-pgrst200-could-not-find-relationship-schema-cache",
    "slug": "erro-pgrst200-could-not-find-relationship-supabase",
    "title": 'Erro PGRST200 "Could not find a relationship between ... in the schema cache" no Supabase',
    "h1_plain": "Erro PGRST200: Could not find a relationship in the schema cache",
    "h1": 'Erro <span class="mono">PGRST200</span>: Could not find a relationship in the schema cache',
    "desc": "Por que um select com join no Supabase, como select('*, authors(name)'), devolve PGRST200 Could not find a relationship: falta chave estrangeira, cache desatualizado ou duas chaves entre as mesmas tabelas (PGRST201).",
    "eyebrow": "Supabase · Correção de erro",
    "crumb": "Erro PGRST200: Could not find a relationship",
    "byline": "Postgres 15 · Supabase",
    "tldr": "Juntar tabelas dentro do <code>select()</code> (embedding) só funciona por uma <b>chave estrangeira</b>. Sem chave estrangeira entre as duas tabelas, não há relação. Crie a chave estrangeira (a coluna referenciada precisa ser chave primária ou única), recarregue o cache e, se houver duas chaves entre as mesmas tabelas, diga qual você quer.",
    "body": """  <h2><span class="n">01</span> O que o erro diz</h2>
  <p class="filelabel">resposta</p>
  <pre>{
  <span class="s">"code"</span>: <span class="s">"PGRST200"</span>,
  <span class="s">"message"</span>: <span class="s">"Could not find a relationship between 'books' and 'authors' in the schema cache"</span>,
  <span class="s">"details"</span>: <span class="s">"Searched for a foreign key relationship between 'books' and 'authors' in the schema 'public', but no matches were found."</span>
}</pre>
  <p>Uma query como <code>supabase.from('books').select('title, authors(name)')</code> pede pra Data API juntar as tabelas por uma chave estrangeira. Ela não adivinha o join pelo nome da coluna: só ter <code>author_id</code> não basta.</p>

  <h2><span class="n">02</span> Veja quais chaves estrangeiras existem</h2>
  <p class="filelabel">check.sql</p>
  <pre><span class="k">select</span> conrelid::regclass <span class="k">as</span> from_table, confrelid::regclass <span class="k">as</span> to_table, conname
<span class="k">from</span> pg_constraint
<span class="k">where</span> contype = <span class="s">'f'</span> <span class="k">and</span> connamespace = <span class="s">'public'</span>::regnamespace
<span class="k">order by</span> 1;</pre>

  <h2><span class="n">03</span> Crie a chave estrangeira</h2>
  <p class="filelabel">migration.sql</p>
  <pre><span class="k">alter table</span> public.books
  <span class="k">add constraint</span> books_author_id_fkey
  <span class="k">foreign key</span> (author_id) <span class="k">references</span> public.authors(id);

<span class="k">notify</span> pgrst, <span class="s">'reload schema'</span>;</pre>
  <p>A coluna referenciada precisa ser chave primária ou única, senão o Postgres recusa a constraint (<code>there is no unique constraint matching given keys</code>).</p>

  <h2><span class="n">04</span> Duas chaves entre as mesmas tabelas: PGRST201</h2>
  <p>Se <code>books</code> tem <code>author_id</code> e <code>editor_id</code> apontando pra <code>authors</code>, o join fica ambíguo e você recebe <code>PGRST201</code>, cuja dica lista as opções. Diga o nome da chave estrangeira:</p>
  <pre><span class="c">// escolha a relação pelo nome da constraint</span>
supabase.from(<span class="s">'books'</span>).select(<span class="s">'title, author:authors!books_author_id_fkey(name)'</span>)</pre>

  <h2><span class="n">05</span> Achou a relação, mas as linhas vêm vazias</h2>
  <p>Aí é RLS, não a relação: a tabela do join tem as próprias policies, e linhas que quem chama não pode ver voltam como <code>null</code> ou lista vazia. Confira a policy de SELECT da tabela do join.</p>""",
    "related": [
        ("/pt/rls/erro-pgrst202-could-not-find-function-supabase/", "Erro PGRST202: Could not find the function"),
        ("/rls/fix-pgrst205-could-not-find-table-schema-cache/", "Fix PGRST205: Could not find the table (em inglês)"),
        ("/rls/fix-pgrst116-cannot-coerce-result-single-json-object/", "Fix PGRST116: Cannot coerce the result (em inglês)"),
        ("/supabase-rls-policy-generator/", "Gerador de policies RLS (em inglês)"),
    ],
    "faq": [
        ("Dá pra juntar tabelas de schemas diferentes?",
         "A chave estrangeira pode apontar pra outro schema, mas as duas tabelas precisam estar em schemas expostos pela Data API pro join funcionar."),
        ("Criei a chave estrangeira e continua dando PGRST200.",
         "Recarregue o cache do schema (notify pgrst, 'reload schema') e confira os nomes das tabelas no select: o join usa nome de tabela (ou o apelido que você der), não nome de coluna."),
    ],
})

# ---- JWT expired (PGRST303) ----------------------------------------------
PT.append({
    "en": "fix-supabase-jwt-expired-pgrst303",
    "slug": "erro-jwt-expired-pgrst303-supabase",
    "title": 'Erro "JWT expired" (PGRST303) no Supabase: como manter a sessão renovada',
    "h1_plain": "Erro JWT expired (PGRST303) no Supabase",
    "h1": 'Erro <span class="mono">JWT expired</span> (PGRST303) no Supabase',
    "desc": "Por que as requisições ao Supabase falham com 401 JWT expired (PGRST303), por que isso aparece no código do servidor e depois que o notebook hiberna, e como manter a sessão renovada com @supabase/ssr.",
    "eyebrow": "Supabase Auth · Correção de erro",
    "crumb": "Erro JWT expired (PGRST303)",
    "byline": "Supabase Auth · Next.js",
    "tldr": "O token de acesso da requisição passou da validade, e a Data API responde 401 <code>PGRST303 JWT expired</code>. No navegador, o supabase-js renova sozinho. No servidor, ele só fica válido se algo renovar: no Next.js, é o <code>proxy.ts</code> (<code>middleware.ts</code> antes do Next 16) do <code>@supabase/ssr</code>, chamando <code>supabase.auth.getClaims()</code>.",
    "body": """  <h2><span class="n">01</span> O que é o erro</h2>
  <p class="filelabel">resposta</p>
  <pre>{ <span class="s">"code"</span>: <span class="s">"PGRST303"</span>, <span class="s">"message"</span>: <span class="s">"JWT expired"</span> }</pre>
  <p>Os tokens de acesso do Supabase duram pouco e vêm com um refresh token que gera um novo. O erro quer dizer que uma requisição saiu com um token velho que ninguém renovou. Não é problema de RLS: suas policies nem chegaram a rodar.</p>

  <h2><span class="n">02</span> De onde vem</h2>
  <div class="cause"><span class="tag">CAUSA 1 · mais comum</span><h3>Código de servidor que lê a sessão sem renovar</h3><p>Server Components do Next.js não podem gravar cookies, então não conseguem salvar um token renovado. Se nenhum proxy/middleware renovar antes, as queries do servidor saem com token vencido.</p></div>
  <div class="cause"><span class="tag">CAUSA 2</span><h3>Token passado na mão</h3><p>Um cliente criado com o header fixo <code>Authorization: Bearer ...</code>, ou um token guardado no seu próprio estado, para de funcionar quando vence: nada renova ele.</p></div>
  <div class="cause"><span class="tag">CAUSA 3</span><h3>Aba que hibernou</h3><p>Quando o notebook volta da hibernação, a primeira requisição pode sair antes da renovação. O supabase-js renova sozinho; tentar de novo depois da renovação funciona.</p></div>

  <h2><span class="n">03</span> A correção no Next.js</h2>
  <p>Use o <code>@supabase/ssr</code> e renove no proxy, que roda antes das páginas e pode gravar cookies. Seguindo o guia do Supabase, o proxy cria um cliente de servidor e chama <code>getClaims()</code>, que renova um token vencido:</p>
  <p class="filelabel">proxy.ts (middleware.ts antes do Next 16)</p>
  <pre><span class="c">// dentro do proxy, depois de criar o cliente de servidor com os cookies da requisição</span>
<span class="k">await</span> supabase.auth.getClaims();   <span class="c">// renova o token e grava os cookies novos</span></pre>
  <p>Não confie no <code>getSession()</code> no código do servidor: ele lê o cookie sem conferir. E crie o cliente do Supabase a cada requisição, a partir dos cookies, nunca de um token guardado.</p>

  <h2><span class="n">04</span> Não confunda com</h2>
  <ul>
    <li><b><code>PGRST301</code></b>: o token não pode ser decodificado ou é inválido (projeto errado, header malformado).</li>
    <li><b>Sem sessão nenhuma</b>: as requisições rodam como <code>anon</code> e policies <code>to authenticated</code> não devolvem nada. Veja o <a href="/rls/fix-pgrst116-cannot-coerce-result-single-json-object/">PGRST116</a> (em inglês).</li>
  </ul>""",
    "related": [
        ("/pt/rls/erro-pgrst202-could-not-find-function-supabase/", "Erro PGRST202: Could not find the function"),
        ("/pt/rls/erro-42501-permission-denied-for-table-supabase/", 'Erro 42501: "permission denied for table"'),
        ("/rls/nextjs-app-router-supabase-auth-rls-ssr/", "Next.js App Router + Supabase auth with RLS (em inglês)"),
        ("/rls/v0-supabase-security-checklist/", "v0 + Supabase security checklist (em inglês)"),
    ],
    "faq": [
        ("Devo aumentar a validade do JWT?",
         "Isso esconde o sintoma e deixa um token roubado útil por mais tempo. Corrija a renovação: com o proxy funcionando, a validade deixa de importar pro usuário."),
        ("A chave service_role expira?",
         "Ela não é uma sessão de usuário, então não há o que renovar. E ela ignora o RLS, então fica só no servidor, nunca como solução pra um token de usuário vencido."),
    ],
})
