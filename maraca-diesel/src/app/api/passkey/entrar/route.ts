import { NextResponse } from 'next/server';
import { verifyAuthenticationResponse } from '@simplewebauthn/server';
import { supabaseAdmin, supabaseServer } from '@/lib/supabase/server';
import { deB64, rp } from '@/lib/webauthn';

export async function POST(req: Request) {
  const { resposta, desafioId } = await req.json();
  const adm = supabaseAdmin();
  const { data: d } = await adm.from('webauthn_desafios').delete().eq('id', desafioId).gt('expira_em', new Date().toISOString()).select().single();
  if (!d) return NextResponse.json({ erro: 'Desafio expirado' }, { status: 400 });
  const { data: cred } = await adm.from('passkeys').select('*').eq('id', resposta?.id).single();
  if (!cred) return NextResponse.json({ erro: 'Passkey não cadastrada' }, { status: 404 });
  const v = await verifyAuthenticationResponse({
    response: resposta, expectedChallenge: d.desafio, expectedOrigin: rp().origin, expectedRPID: rp().rpID, requireUserVerification: true,
    credential: { id: cred.id, publicKey: deB64(cred.chave_publica), counter: Number(cred.contador), transports: cred.transportes ?? undefined },
  }).catch(() => null);
  if (!v?.verified) return NextResponse.json({ erro: 'Não verificado' }, { status: 401 });
  await adm.from('passkeys').update({ contador: v.authenticationInfo.newCounter, usado_em: new Date().toISOString() }).eq('id', cred.id);

  // Cria a sessão Supabase: gera um magic link no servidor e o consome na hora (o token nunca sai do servidor).
  const { data: u } = await adm.auth.admin.getUserById(cred.usuario_id);
  const { data: link, error } = await adm.auth.admin.generateLink({ type: 'magiclink', email: u.user!.email! });
  if (error) return NextResponse.json({ erro: 'Falha na sessão' }, { status: 500 });
  const sb = await supabaseServer();
  const { error: e2 } = await sb.auth.verifyOtp({ token_hash: link.properties.hashed_token, type: 'magiclink' });
  if (e2) return NextResponse.json({ erro: 'Falha na sessão' }, { status: 500 });
  return NextResponse.json({ ok: true });
}
