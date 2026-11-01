import { NextResponse } from 'next/server';
import { verifyRegistrationResponse } from '@simplewebauthn/server';
import { supabaseAdmin, supabaseServer } from '@/lib/supabase/server';
import { b64, rp } from '@/lib/webauthn';

export async function POST(req: Request) {
  const { data: { user } } = await (await supabaseServer()).auth.getUser();
  if (!user) return NextResponse.json({ erro: 'Faça login' }, { status: 401 });
  const { resposta, desafioId } = await req.json();
  const adm = supabaseAdmin();
  const { data: d } = await adm.from('webauthn_desafios').delete().eq('id', desafioId).eq('usuario_id', user.id).gt('expira_em', new Date().toISOString()).select().single();
  if (!d) return NextResponse.json({ erro: 'Desafio expirado' }, { status: 400 });
  const v = await verifyRegistrationResponse({ response: resposta, expectedChallenge: d.desafio, expectedOrigin: rp().origin, expectedRPID: rp().rpID, requireUserVerification: true }).catch(() => null);
  if (!v?.verified || !v.registrationInfo) return NextResponse.json({ erro: 'Não verificado' }, { status: 400 });
  const c = v.registrationInfo.credential;
  await adm.from('passkeys').insert({ id: c.id, usuario_id: user.id, chave_publica: b64(c.publicKey), contador: c.counter, transportes: c.transports ?? [], apelido: req.headers.get('user-agent')?.slice(0, 80) });
  return NextResponse.json({ ok: true });
}
