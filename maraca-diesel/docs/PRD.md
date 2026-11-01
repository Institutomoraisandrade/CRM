# PRD — Site Maracá Diesel (peças e serviços para caminhões)

> Versão 1.0 · nov/2026 · Status: MVP implementado em `maraca-diesel/`. Itens marcados **[validar]** dependem de dados reais da empresa.

## 1. Objetivo
Transformar o site em canal de **geração de leads (orçamento)** e **venda direta de peças**, com base própria de clientes para **remarketing**.

| Meta (90 dias após lançamento) | Indicador |
|---|---|
| Leads de orçamento | ≥ 150/mês, taxa de conversão do formulário ≥ 4% |
| Vendas online | ≥ 30 pedidos/mês |
| Base de remarketing | ≥ 60% dos cadastros com consentimento de marketing |
| Tempo de resposta ao lead | < 15 min em horário comercial |

## 2. Públicos
1. **Caminhoneiro autônomo** — celular, pressa, quer preço e prazo no WhatsApp.
2. **Frota / transportadora** — compra recorrente, precisa de CNPJ, nota e histórico.
3. **Oficina** — busca por código original da peça.

## 3. Escopo do MVP (entregue)
### 3.1 Home com hero 3D e motion
- Cena Three.js: caminhão low-poly genérico (sem marca de terceiros) entra na estrada, faróis piscam, parallax de mouse e câmera que abaixa ao rolar.
- Anime.js v4: título sobe palavra por palavra, contador, reveal por rolagem, stagger em cards.
- Botões "Faróis" e "Pausar"; respeita `prefers-reduced-motion` (acessibilidade).

### 3.2 Área de orçamento (`/orcamento` e seção na home)
- Campos: **nome, e-mail, telefone/WhatsApp** (obrigatórios), tipo (peça/serviço), caminhão, placa, mensagem, opt-in de marketing.
- Sem login. Se logado, já vem preenchido.
- Pode vir de um produto (`/orcamento?produto=slug`).
- Ao enviar: grava em `orcamentos`, e-mail para a equipe (Resend), evento `Lead` (Pixel + Conversions API), protocolo + botão "Adiantar pelo WhatsApp" com mensagem pronta.
- Anti-spam: honeypot + validação no servidor (zod).

### 3.3 Catálogo (banco de produtos)
- Tabelas `categorias` e `produtos` (SKU, código original, aplicação por modelo de caminhão, preço, promoção, estoque, imagens, "sob consulta").
- `/catalogo` com busca (nome, código original, SKU) e filtro por categoria; `/catalogo/[slug]` com schema.org Product (SEO / Google Shopping).
- Produto "sob consulta" ou sem estoque → só orçamento. Com preço e estoque → botão Comprar.
- Atualização: Supabase Studio ou importação CSV. **[fase 2]** painel de edição e sincronização com o ERP.

### 3.4 Cadastro e compra
- **Login com Google** (Supabase Auth): nome, e-mail e foto chegam preenchidos automaticamente; telefone é pedido uma única vez em `/conta`.
- **Face ID / Touch ID / digital (Passkeys – WebAuthn)**: após o 1º login com Google, o cliente ativa no aparelho; nas próximas vezes entra só com o rosto/digital, sem senha.
- Carrinho (localStorage) → checkout com CEP (ViaCEP) → pedido criado no servidor **com preço do banco** → Mercado Pago Checkout Pro (Pix, cartão, boleto) → webhook confirma e marca `pago`.
- `/conta`: dados, Face ID, histórico de pedidos.

### 3.5 Remarketing
- Banner LGPD: Pixel Meta e GA4 só carregam com consentimento.
- Eventos: PageView, ViewContent, AddToCart, Lead, CompleteRegistration, InitiateCheckout, Purchase — no navegador **e** no servidor (Meta Conversions API, com e-mail/telefone em SHA-256 e `event_id` para deduplicar).
- UTMs, gclid e fbclid guardados por 90 dias e gravados no lead/pedido (atribuição).
- Tabela `eventos_marketing` = base própria para montar públicos (abandono de carrinho, quem pediu orçamento e não comprou, recompra de filtros a cada X km).
- Criativos de vídeo por produto gerados no Remotion (template `Oferta`) para anúncios de catálogo.

### 3.6 Painel `/admin` (papel `admin`)
- Lista de orçamentos com link direto para WhatsApp e origem (UTM); lista de pedidos.

## 4. Fora do MVP (próximas fases)
1. Painel de produtos com upload de imagens e importação CSV/ERP.
2. Cálculo de frete (Melhor Envio) e emissão de NF-e.
3. Automação de WhatsApp (API oficial) para responder o lead em < 1 min.
4. Fluxos de e-mail: abandono de carrinho, pós-venda, lembrete de revisão.
5. Exportação automática de públicos para Meta/Google (Customer Match).
6. Página de serviços com agendamento.

## 5. Requisitos não funcionais
- LCP < 2,5 s no 4G; cena 3D com `pixelRatio ≤ 2` e fallback se WebGL falhar.
- Acessibilidade WCAG AA: foco visível, `aria-pressed`, movimento reduzido.
- Segurança: RLS em todas as tabelas; service role só no servidor; preço nunca vem do cliente; webhook re-consulta o pagamento na API.
- LGPD: consentimento explícito para marketing, política de privacidade **[validar texto jurídico]**.

## 6. Pendências com a empresa [validar]
Anos de atuação (hoje "24"), lista oficial de serviços, número de WhatsApp, domínio, logo final, catálogo inicial (planilha), conta Mercado Pago, Pixel/GA4, texto jurídico.
