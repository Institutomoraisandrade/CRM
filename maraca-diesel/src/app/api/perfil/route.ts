import { NextResponse } from 'next/server';
import { z } from 'zod';
import { supabaseServer } from '@/lib/supabase/server';
import { registraEvento } from '@/lib/marketing';
import { contexto } from '@/lib/req';

const Schema = z.object({
  nome: z.string().trim().min(2).max(120), telefone: z.string().trim().regex(/^[\d\s()+-]{10,20}$/),
  cpf_cnpj: z.string().trim().max(18).optional(), empresa: z.string().trim().max(120).optional(),
  tipo_cliente: z.enum(['autonomo', 'frota', 'oficina']).optional(), aceita_marketing: z.boolean(),
});
export async function POST(req: Request) {
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) return NextResponse.json({ erro: 'Faça login' }, { status: 401 });
  const p = Schema.safeParse(await req.json().catch(() => ({})));
  if (!p.success) return NextResponse.json({ erro: 'Confira os dados' }, { status: 400 });
  const ctx = await contexto();
  const { error } = await sb.from('perfis').update({ ...p.data, utm: ctx.origem, atualizado_em: new Date().toISOString() }).eq('id', user.id);
  if (error) return NextResponse.json({ erro: 'Erro ao salvar' }, { status: 500 });
  if (ctx.consente) await registraEvento({ evento: 'CompleteRegistration', eventId: `reg-${user.id}`, email: user.email, telefone: p.data.telefone, nome: p.data.nome, usuarioId: user.id, ip: ctx.ip, ua: ctx.ua, fbc: ctx.fbc, fbp: ctx.fbp });
  return NextResponse.json({ ok: true });
}
