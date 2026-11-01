import 'server-only';
import { createHash } from 'crypto';
import { supabaseAdmin } from './supabase/server';

const sha = (v?: string | null) => (v ? createHash('sha256').update(v.trim().toLowerCase()).digest('hex') : undefined);
const soDigitos = (t?: string | null) => (t ? '55' + t.replace(/\D/g, '').replace(/^55/, '') : undefined);

type Ev = {
  evento: 'Lead' | 'CompleteRegistration' | 'InitiateCheckout' | 'Purchase' | 'AddToCart' | 'ViewContent';
  eventId: string; email?: string | null; telefone?: string | null; nome?: string | null; usuarioId?: string | null;
  valor?: number; dados?: Record<string, unknown>; ip?: string | null; ua?: string | null; fbc?: string; fbp?: string; url?: string;
};

/** Grava o evento (base própria de remarketing) e envia para a Meta Conversions API (deduplica com o Pixel via event_id). */
export async function registraEvento(e: Ev) {
  const email_hash = sha(e.email), telefone_hash = sha(soDigitos(e.telefone));
  await supabaseAdmin().from('eventos_marketing').insert({
    evento: e.evento, usuario_id: e.usuarioId ?? null, email_hash, telefone_hash, valor: e.valor ?? null, dados: e.dados ?? null, event_id: e.eventId,
  });
  const pixel = process.env.META_PIXEL_ID, token = process.env.META_CAPI_TOKEN;
  if (!pixel || !token) return;
  const [fn, ...ln] = (e.nome ?? '').split(' ');
  await fetch(`https://graph.facebook.com/v21.0/${pixel}/events?access_token=${token}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      data: [{
        event_name: e.evento, event_time: Math.floor(Date.now() / 1000), event_id: e.eventId, action_source: 'website', event_source_url: e.url,
        user_data: { em: email_hash && [email_hash], ph: telefone_hash && [telefone_hash], fn: fn ? [sha(fn)] : undefined, ln: ln.length ? [sha(ln.join(' '))] : undefined,
          external_id: e.usuarioId ? [sha(e.usuarioId)] : undefined, client_ip_address: e.ip ?? undefined, client_user_agent: e.ua ?? undefined, fbc: e.fbc, fbp: e.fbp },
        custom_data: e.valor != null ? { currency: 'BRL', value: e.valor, ...e.dados } : e.dados,
      }],
    }),
  }).catch(() => undefined);
}
