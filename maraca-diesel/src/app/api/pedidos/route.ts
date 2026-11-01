import { NextResponse } from 'next/server';
import { z } from 'zod';
import { supabaseAdmin, supabaseServer } from '@/lib/supabase/server';
import { registraEvento } from '@/lib/marketing';
import { contexto } from '@/lib/req';

const Schema = z.object({
  itens: z.array(z.object({ produtoId: z.string().uuid(), quantidade: z.number().int().min(1).max(99) })).min(1).max(50),
  entrega: z.object({ cep: z.string().regex(/^\d{5}-?\d{3}$/), endereco: z.string().min(3).max(200), numero: z.string().max(10), cidade: z.string().max(80), uf: z.string().length(2), retirar: z.boolean().default(false) }),
  eventId: z.string().max(64),
});

export async function POST(req: Request) {
  const { data: { user } } = await (await supabaseServer()).auth.getUser();
  if (!user) return NextResponse.json({ erro: 'Faça login para comprar' }, { status: 401 });
  const p = Schema.safeParse(await req.json().catch(() => ({})));
  if (!p.success) return NextResponse.json({ erro: 'Confira os dados de entrega' }, { status: 400 });
  const adm = supabaseAdmin();
  // Preço SEMPRE vem do banco, nunca do navegador.
  const ids = p.data.itens.map((i) => i.produtoId);
  const { data: prods } = await adm.from('produtos').select('id,nome,preco,preco_promocional,estoque,sob_consulta,ativo').in('id', ids);
  let itens;
  try { itens = p.data.itens.map((i) => {
    const pr = prods?.find((x) => x.id === i.produtoId);
    if (!pr || !pr.ativo || pr.sob_consulta || pr.preco == null) throw new Error(`Produto indisponível para compra online`);
    if (pr.estoque < i.quantidade) throw new Error(`Estoque insuficiente: ${pr.nome}`);
    return { ...i, nome: pr.nome, preco: Number(pr.preco_promocional ?? pr.preco) };
  }); } catch (e) { return NextResponse.json({ erro: (e as Error).message }, { status: 409 }); }
  const total = itens.reduce((s, i) => s + i.preco * i.quantidade, 0);
  const ctx = await contexto();
  const { data: ped, error } = await adm.from('pedidos').insert({ usuario_id: user.id, total, entrega: p.data.entrega, origem: ctx.origem }).select('id').single();
  if (error) return NextResponse.json({ erro: 'Erro ao criar pedido' }, { status: 500 });
  await adm.from('pedido_itens').insert(itens.map((i) => ({ pedido_id: ped.id, produto_id: i.produtoId, quantidade: i.quantidade, preco_unit: i.preco })));
  if (ctx.consente) await registraEvento({ evento: 'InitiateCheckout', eventId: p.data.eventId, email: user.email, usuarioId: user.id, valor: total, ip: ctx.ip, ua: ctx.ua, fbc: ctx.fbc, fbp: ctx.fbp });

  // Pagamento: Mercado Pago Checkout Pro (Pix, cartão, boleto). O webhook marca o pedido como pago e dispara Purchase.
  let pagamentoUrl: string | null = null;
  if (process.env.MP_ACCESS_TOKEN) {
    const r = await fetch('https://api.mercadopago.com/checkout/preferences', {
      method: 'POST', headers: { Authorization: `Bearer ${process.env.MP_ACCESS_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        external_reference: ped.id, payer: { email: user.email },
        items: itens.map((i) => ({ id: i.produtoId, title: i.nome, quantity: i.quantidade, unit_price: i.preco, currency_id: 'BRL' })),
        back_urls: { success: `${process.env.NEXT_PUBLIC_SITE_URL}/conta?pedido=${ped.id}`, failure: `${process.env.NEXT_PUBLIC_SITE_URL}/carrinho` },
        notification_url: `${process.env.NEXT_PUBLIC_SITE_URL}/api/pagamentos/webhook`, auto_return: 'approved',
      }),
    }).then((x) => x.json()).catch(() => null);
    pagamentoUrl = r?.init_point ?? null;
    if (r?.id) await adm.from('pedidos').update({ pagamento_ref: r.id }).eq('id', ped.id);
  }
  return NextResponse.json({ ok: true, pedidoId: ped.id, pagamentoUrl });
}
