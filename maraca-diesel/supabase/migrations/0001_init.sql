-- Maracá Diesel — schema inicial (Supabase/Postgres)
create extension if not exists "pgcrypto";

-- Perfis (1:1 com auth.users). Google preenche nome/e-mail/foto; telefone é pedido no 1º acesso.
create table public.perfis (
  id uuid primary key references auth.users(id) on delete cascade,
  nome text, email text, telefone text, avatar_url text, cpf_cnpj text,
  empresa text, tipo_cliente text check (tipo_cliente in ('autonomo','frota','oficina')),
  aceita_marketing boolean not null default false,
  papel text not null default 'cliente' check (papel in ('cliente','admin')),
  utm jsonb, criado_em timestamptz not null default now(), atualizado_em timestamptz not null default now()
);

create or replace function public.novo_usuario() returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.perfis (id, nome, email, avatar_url)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'), new.email, new.raw_user_meta_data->>'avatar_url')
  on conflict (id) do nothing;
  return new;
end $$;
create trigger on_auth_user_created after insert on auth.users for each row execute function public.novo_usuario();

create or replace function public.eh_admin() returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.perfis where id = auth.uid() and papel = 'admin');
$$;

-- Passkeys (Face ID / Touch ID / Windows Hello) via WebAuthn
create table public.passkeys (
  id text primary key,                       -- credentialID (base64url)
  usuario_id uuid not null references auth.users(id) on delete cascade,
  chave_publica text not null,               -- base64url
  contador bigint not null default 0,
  transportes text[], apelido text,
  criado_em timestamptz not null default now(), usado_em timestamptz
);
create table public.webauthn_desafios (
  id uuid primary key default gen_random_uuid(),
  desafio text not null, usuario_id uuid, expira_em timestamptz not null default now() + interval '5 minutes'
);

-- Catálogo
create table public.categorias (
  id uuid primary key default gen_random_uuid(), nome text not null, slug text unique not null, ordem int default 0
);
create table public.produtos (
  id uuid primary key default gen_random_uuid(),
  sku text unique not null, slug text unique not null, nome text not null, descricao text,
  categoria_id uuid references public.categorias(id),
  marca text, aplicacao text[],               -- ex.: {'Scania R440','Volvo FH 460'}
  codigo_original text, preco numeric(12,2), preco_promocional numeric(12,2),
  estoque int not null default 0, imagens text[] default '{}',
  ativo boolean not null default true, sob_consulta boolean not null default false,
  criado_em timestamptz not null default now(), atualizado_em timestamptz not null default now()
);
create index on public.produtos using gin (to_tsvector('portuguese', nome || ' ' || coalesce(descricao,'') || ' ' || coalesce(codigo_original,'')));

-- Orçamentos (leads — não exige login)
create table public.orcamentos (
  id uuid primary key default gen_random_uuid(),
  nome text not null, email text not null, telefone text not null,
  tipo text not null default 'peca' check (tipo in ('peca','servico','ambos')),
  veiculo text, placa text, mensagem text, produto_id uuid references public.produtos(id),
  usuario_id uuid references auth.users(id), aceita_marketing boolean not null default false,
  status text not null default 'novo' check (status in ('novo','em_atendimento','enviado','ganho','perdido')),
  origem jsonb,                               -- utm_*, gclid, fbclid, referrer, página
  criado_em timestamptz not null default now()
);

-- Pedidos
create table public.pedidos (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid not null references auth.users(id),
  status text not null default 'aguardando_pagamento'
    check (status in ('aguardando_pagamento','pago','separando','enviado','entregue','cancelado')),
  total numeric(12,2) not null, frete numeric(12,2) default 0,
  entrega jsonb, pagamento_ref text, origem jsonb,
  criado_em timestamptz not null default now()
);
create table public.pedido_itens (
  id uuid primary key default gen_random_uuid(),
  pedido_id uuid not null references public.pedidos(id) on delete cascade,
  produto_id uuid not null references public.produtos(id),
  quantidade int not null check (quantidade > 0), preco_unit numeric(12,2) not null
);

-- Eventos para remarketing / audiências (espelho do que vai para Meta CAPI e GA4)
create table public.eventos_marketing (
  id bigint generated always as identity primary key,
  evento text not null,                        -- PageView, ViewContent, AddToCart, Lead, InitiateCheckout, Purchase, CompleteRegistration
  usuario_id uuid, email_hash text, telefone_hash text, valor numeric(12,2), dados jsonb,
  event_id text, criado_em timestamptz not null default now()
);

-- RLS
alter table public.perfis enable row level security;
alter table public.passkeys enable row level security;
alter table public.webauthn_desafios enable row level security;
alter table public.categorias enable row level security;
alter table public.produtos enable row level security;
alter table public.orcamentos enable row level security;
alter table public.pedidos enable row level security;
alter table public.pedido_itens enable row level security;
alter table public.eventos_marketing enable row level security;

create policy "perfil: dono lê" on public.perfis for select using (id = auth.uid() or public.eh_admin());
create policy "perfil: dono edita" on public.perfis for update using (id = auth.uid())
  with check (id = auth.uid() and papel = (select papel from public.perfis where id = auth.uid()));
create policy "passkeys: dono lê" on public.passkeys for select using (usuario_id = auth.uid());
create policy "catálogo público" on public.categorias for select using (true);
create policy "produtos públicos" on public.produtos for select using (ativo or public.eh_admin());
create policy "admin gerencia produtos" on public.produtos for all using (public.eh_admin()) with check (public.eh_admin());
create policy "admin gerencia categorias" on public.categorias for all using (public.eh_admin()) with check (public.eh_admin());
create policy "admin vê orçamentos" on public.orcamentos for select using (public.eh_admin() or usuario_id = auth.uid());
create policy "admin atualiza orçamentos" on public.orcamentos for update using (public.eh_admin());
create policy "pedidos: dono/admin" on public.pedidos for select using (usuario_id = auth.uid() or public.eh_admin());
create policy "itens: dono/admin" on public.pedido_itens for select using (
  exists (select 1 from public.pedidos p where p.id = pedido_id and (p.usuario_id = auth.uid() or public.eh_admin())));
create policy "eventos: admin" on public.eventos_marketing for select using (public.eh_admin());
-- Inserções de orçamentos, pedidos, passkeys e eventos são feitas pelo servidor (service role), com validação.

-- Seed de exemplo (substituir pelo catálogo real)
insert into public.categorias (nome, slug, ordem) values
 ('Freios','freios',1),('Suspensão','suspensao',2),('Motor','motor',3),('Elétrica','eletrica',4),('Filtros','filtros',5);
insert into public.produtos (sku, slug, nome, descricao, categoria_id, marca, aplicacao, preco, estoque, sob_consulta) values
 ('FR-001','lona-de-freio-exemplo','Lona de freio (exemplo)','Produto ilustrativo: substituir pelo cadastro real.',(select id from public.categorias where slug='freios'),'—','{"Linha pesada"}',null,0,true),
 ('FI-001','filtro-de-oleo-exemplo','Filtro de óleo (exemplo)','Produto ilustrativo: substituir pelo cadastro real.',(select id from public.categorias where slug='filtros'),'—','{"Linha pesada"}',89.90,10,false);
