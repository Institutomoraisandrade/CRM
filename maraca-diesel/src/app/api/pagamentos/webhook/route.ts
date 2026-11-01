import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase/server';
import { registraEvento } from '@/lib/marketing';

// Webhook do Mercado Pago: confirma o pagamento consultando a API (não confia no corpo recebido).
export async function POST(req: Request) {
  const corpo = await req.json().catch(() => ({}));
  const id = corpo?.data?.id;
  if (corpo?.type !== 'payment' || !id || !process.env.MP_ACCESS_TOKEN) return NextResponse.json({ ok: true });
  const pg = await fetch(`https://api.mercadopago.com/v1/payments/${id}`, { headers: { Authorization: `Bearer ${process.env.MP_ACCESS_TOKEN}` } }).then((r) => r.json());
  if (pg?.status !== 'approved' || !pg.external_reference) return NextResponse.json({ ok: true });
  const adm = supabaseAdmin();
  const { data: ped } = await adm.from('pedidos').update({ status: 'pago' }).eq('id', pg.external_reference).eq('status', 'aguardando_pagamento').select('id,total,usuario_id').single();
  if (ped) {
    const { data: perfil } = await adm.from('perfis').select('email,telefone,nome,aceita_marketing').eq('id', ped.usuario_id).single();
    if (perfil?.aceita_marketing) await registraEvento({ evento: 'Purchase', eventId: `ped-${ped.id}`, email: perfil.email, telefone: perfil.telefone, nome: perfil.nome, usuarioId: ped.usuario_id, valor: Number(ped.total) });
  }
  return NextResponse.json({ ok: true });
}
