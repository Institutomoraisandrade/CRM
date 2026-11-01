import { NextResponse } from 'next/server';
import { generateRegistrationOptions } from '@simplewebauthn/server';
import { supabaseAdmin, supabaseServer } from '@/lib/supabase/server';
import { rp } from '@/lib/webauthn';

// Usuário já logado (Google) cadastra Face ID / digital neste aparelho.
export async function POST() {
  const { data: { user } } = await (await supabaseServer()).auth.getUser();
  if (!user) return NextResponse.json({ erro: 'Faça login' }, { status: 401 });
  const adm = supabaseAdmin();
  const { data: existentes } = await adm.from('passkeys').select('id').eq('usuario_id', user.id);
  const opts = await generateRegistrationOptions({
    rpName: rp().rpName, rpID: rp().rpID, userName: user.email!, userDisplayName: user.user_metadata?.full_name ?? user.email!,
    userID: new TextEncoder().encode(user.id), attestationType: 'none',
    excludeCredentials: (existentes ?? []).map((c) => ({ id: c.id })),
    authenticatorSelection: { residentKey: 'required', userVerification: 'required', authenticatorAttachment: 'platform' },
  });
  const { data } = await adm.from('webauthn_desafios').insert({ desafio: opts.challenge, usuario_id: user.id }).select('id').single();
  return NextResponse.json({ opts, desafioId: data!.id });
}
