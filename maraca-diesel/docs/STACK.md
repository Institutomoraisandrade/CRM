# Stack

| Camada | Tecnologia | Por quê |
|---|---|---|
| Front + back | **Next.js 15** (App Router, Server Components, Route Handlers) · TypeScript | SEO do catálogo, API no mesmo projeto, deploy simples |
| Estilo | **Tailwind CSS v4** com tokens da marca (`globals.css`) | Marinho `#0a2350`, azul `#1746a2`, amarelo `#ffc20e`, Barlow / Barlow Condensed |
| 3D | **Three.js** (`src/components/hero/cena.ts`) | Porta do protótipo Hero 3D |
| Motion web | **Anime.js v4** (timeline, stagger, onScroll, createAnimatable) | Mesmo motor do protótipo |
| Vídeo | **Remotion 4** + `@remotion/three` (`remotion/`) | Vídeos 9:16 para Reels/TikTok e criativos de catálogo por produto, a partir do mesmo modelo 3D |
| Banco + Auth | **Supabase** (Postgres + RLS + Auth Google) | `supabase/migrations/0001_init.sql` |
| Face ID | **Passkeys / WebAuthn** com `@simplewebauthn` | Sessão Supabase criada no servidor após verificar a passkey |
| E-mail | **Resend** | Aviso de novo orçamento para a equipe |
| Pagamento | **Mercado Pago** Checkout Pro + webhook | Pix, cartão, boleto |
| Remarketing | Meta Pixel + **Conversions API**, GA4 | Deduplicação por `event_id`; consentimento LGPD |
| Hospedagem | Vercel (site) + Supabase (banco) | |

## Rodar localmente
```bash
cd maraca-diesel
cp .env.example .env.local   # preencher
npm install && npm run dev   # http://localhost:3000
```
Sem as variáveis do Supabase o site abre em modo demonstração (hero, orçamento visual, catálogo vazio).

## Configurar
1. **Supabase**: criar projeto → rodar `supabase/migrations/0001_init.sql` → Auth › Providers › Google (Client ID/Secret do Google Cloud) → URL de redirect `https://SEU-DOMINIO/auth/callback`.
2. Tornar admin: `update perfis set papel='admin' where email='...';`
3. **Face ID**: `WEBAUTHN_RP_ID` = domínio (sem https). Passkeys exigem HTTPS (ou localhost).
4. **Mercado Pago**: `MP_ACCESS_TOKEN`; webhook aponta para `/api/pagamentos/webhook`.
5. **Meta**: Pixel ID + token da Conversions API. **GA4**: ID de medição.

## Vídeos (Remotion)
```bash
cd maraca-diesel/remotion && npm install
npm run studio           # editor visual
npm run render:reveal    # vídeo de marca 9:16
npm run render:oferta    # criativo de produto (edite oferta.json)
```

## Mapa de pastas
```
src/app/            páginas e API (orcamento, pedidos, passkey, perfil, pagamentos/webhook, auth/callback)
src/components/     Hero 3D, Topo, Carrinho, FormOrcamento, Rastreio (Pixel/GA4/LGPD), Revela
src/lib/            supabase, catálogo, marketing (CAPI), webauthn
supabase/           migrations
remotion/           composições de vídeo
docs/               PRD, Stack, referências de motion
```
