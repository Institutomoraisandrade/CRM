import { NextResponse } from 'next/server';
import { z } from 'zod';
import { Resend } from 'resend';
import { supabaseAdmin, supabaseServer } from '@/lib/supabase/server';
import { registraEvento } from '@/lib/marketing';
import { contexto } from '@/lib/req';

const Schema = z.object({
  nome: z.string().trim().min(2).max(120),
  email: z.string().trim().email().max(160),
  telefone: z.string().trim().regex(/^[\d\s()+-]{10,20}$/, 'Telefone inválido'),
  tipo: z.enum(['peca', 'servico', 'ambos']).default('peca'),
  veiculo: z.string().trim().max(120).optional(),
  placa: z.string().trim().max(10).optional(),
  mensagem: z.string().trim().max(2000).optional(),
  produtoId: z.string().uuid().optional(),
  aceitaMarketing: z.boolean().default(false),
  eventId: z.string().max(64),
  site: z.string().max(0).optional(), // honeypot anti-spam
});

export async function POST(req: Request) {
  const corpo = Schema.safeParse(await req.json().catch(() => ({})));
  if (!corpo.success) return NextResponse.json({ erro: corpo.error.issues[0]?.message ?? 'Dados inválidos' }, { status: 400 });
  const d = corpo.data;
  const ctx = await contexto();
  const { data: { user } } = await (await supabaseServer()).auth.getUser();

  const { data, error } = await supabaseAdmin().from('orcamentos').insert({
    nome: d.nome, email: d.email, telefone: d.telefone, tipo: d.tipo, veiculo: d.veiculo, placa: d.placa?.toUpperCase(),
    mensagem: d.mensagem, produto_id: d.produtoId, usuario_id: user?.id, aceita_marketing: d.aceitaMarketing,
    origem: { ...ctx.origem, referer: ctx.referer },
  }).select('id').single();
  if (error) return NextResponse.json({ erro: 'Não foi possível registrar agora. Tente pelo WhatsApp.' }, { status: 500 });

  // Avisa a equipe por e-mail (se configurado)
  if (process.env.RESEND_API_KEY && process.env.EMAIL_EQUIPE) {
    await new Resend(process.env.RESEND_API_KEY).emails.send({
      from: process.env.EMAIL_REMETENTE ?? 'site@maracadiesel.com.br', to: process.env.EMAIL_EQUIPE, replyTo: d.email,
      subject: `Novo orçamento: ${d.nome} (${d.tipo})`,
      text: `Nome: ${d.nome}\nE-mail: ${d.email}\nTelefone: ${d.telefone}\nVeículo: ${d.veiculo ?? '-'}\nPlaca: ${d.placa ?? '-'}\n\n${d.mensagem ?? ''}`,
    }).catch(() => undefined);
  }
  if (ctx.consente) await registraEvento({ evento: 'Lead', eventId: d.eventId, email: d.email, telefone: d.telefone, nome: d.nome, usuarioId: user?.id, ip: ctx.ip, ua: ctx.ua, fbc: ctx.fbc, fbp: ctx.fbp, url: ctx.referer, dados: { tipo: d.tipo } });

  const zap = process.env.NEXT_PUBLIC_WHATSAPP;
  const texto = encodeURIComponent(`Olá! Sou ${d.nome}. Acabei de pedir um orçamento no site (protocolo ${data.id.slice(0, 8)}).${d.veiculo ? ` Veículo: ${d.veiculo}.` : ''}`);
  return NextResponse.json({ ok: true, protocolo: data.id.slice(0, 8), whatsapp: zap ? `https://wa.me/${zap}?text=${texto}` : null });
}
