import { NextResponse } from 'next/server';
import { generateAuthenticationOptions } from '@simplewebauthn/server';
import { supabaseAdmin } from '@/lib/supabase/server';
import { rp } from '@/lib/webauthn';

// Login sem senha: o aparelho mostra as contas salvas (discoverable credentials) e pede Face ID.
export async function POST() {
  const opts = await generateAuthenticationOptions({ rpID: rp().rpID, userVerification: 'required' });
  const { data } = await supabaseAdmin().from('webauthn_desafios').insert({ desafio: opts.challenge }).select('id').single();
  return NextResponse.json({ opts, desafioId: data!.id });
}
