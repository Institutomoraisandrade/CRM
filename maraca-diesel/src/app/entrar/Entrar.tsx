'use client';
import { useEffect, useState } from 'react';
import { startAuthentication, browserSupportsWebAuthn } from '@simplewebauthn/browser';
import { supabaseBrowser } from '@/lib/supabase/client';

export function Entrar({ volta }: { volta: string }) {
  const [erro, setErro] = useState(''), [temPasskey, setTemPasskey] = useState(false);
  useEffect(() => { setTemPasskey(browserSupportsWebAuthn()); }, []);

  const google = () => supabaseBrowser().auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: `${location.origin}/auth/callback?volta=${encodeURIComponent(volta)}`, queryParams: { prompt: 'select_account' } },
  });

  async function faceId() {
    setErro('');
    try {
      const { opts, desafioId } = await fetch('/api/passkey/entrar-opcoes', { method: 'POST' }).then((r) => r.json());
      const resposta = await startAuthentication({ optionsJSON: opts });
      const r = await fetch('/api/passkey/entrar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ resposta, desafioId }) });
      if (!r.ok) throw new Error((await r.json()).erro);
      location.href = volta;
    } catch (e) { setErro((e as Error).message?.includes('cadastrada') ? 'Este aparelho ainda não tem Face ID cadastrado. Entre com o Google primeiro.' : 'Não foi possível entrar com Face ID.'); }
  }

  return (
    <div className="grid gap-3">
      <button onClick={google} className="btn btn-lg border-linha bg-white text-tinta hover:bg-superficie">
        <svg viewBox="0 0 48 48" className="h-6 w-6" aria-hidden><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-7.9l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"/></svg>
        Continuar com Google
      </button>
      {temPasskey && <button onClick={faceId} className="btn btn-azul btn-lg">Entrar com Face ID / digital</button>}
      {erro && <p role="alert" className="text-sm text-red-700">{erro}</p>}
      <p className="text-xs text-tinta-suave">Ao entrar com o Google, seu nome e e-mail já vêm preenchidos. Depois é só confirmar o telefone e ativar o Face ID para as próximas compras.</p>
    </div>
  );
}
