'use client';
import { useState } from 'react';
import { startRegistration, browserSupportsWebAuthn } from '@simplewebauthn/browser';
import { supabaseBrowser } from '@/lib/supabase/client';

type P = { nome: string | null; email: string | null; telefone: string | null; empresa: string | null; cpf_cnpj: string | null; tipo_cliente: string | null; aceita_marketing: boolean };

export function Perfil({ perfil, passkeys }: { perfil: P; passkeys: number }) {
  const [msg, setMsg] = useState(''), [n, setN] = useState(passkeys);
  async function salva(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>;
    const r = await fetch('/api/perfil', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...f, tipo_cliente: f.tipo_cliente || undefined, aceita_marketing: f.aceita_marketing === 'on' }) });
    setMsg(r.ok ? 'Dados salvos.' : 'Confira os dados.');
  }
  async function ativaFaceId() {
    try {
      const { opts, desafioId } = await fetch('/api/passkey/registrar-opcoes', { method: 'POST' }).then((r) => r.json());
      const resposta = await startRegistration({ optionsJSON: opts });
      const r = await fetch('/api/passkey/registrar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ resposta, desafioId }) });
      if (r.ok) { setN(n + 1); setMsg('Face ID ativado neste aparelho.'); } else setMsg('Não foi possível ativar.');
    } catch { setMsg('Ativação cancelada.'); }
  }
  return (
    <div className="grid gap-8">
      {!perfil.telefone && <p className="rounded border-l-4 border-amarelo bg-superficie p-4">Falta só o telefone para concluir seu cadastro.</p>}
      <form onSubmit={salva} className="grid gap-4 md:grid-cols-2">
        <label><span className="rotulo">Nome</span><input className="campo" name="nome" defaultValue={perfil.nome ?? ''} required autoComplete="name" /></label>
        <label><span className="rotulo">E-mail (Google)</span><input className="campo bg-superficie" value={perfil.email ?? ''} readOnly /></label>
        <label><span className="rotulo">Telefone / WhatsApp *</span><input className="campo" name="telefone" type="tel" defaultValue={perfil.telefone ?? ''} required autoComplete="tel" /></label>
        <label><span className="rotulo">CPF / CNPJ</span><input className="campo" name="cpf_cnpj" defaultValue={perfil.cpf_cnpj ?? ''} /></label>
        <label><span className="rotulo">Empresa / frota</span><input className="campo" name="empresa" defaultValue={perfil.empresa ?? ''} autoComplete="organization" /></label>
        <label><span className="rotulo">Você é</span><select className="campo" name="tipo_cliente" defaultValue={perfil.tipo_cliente ?? ''}><option value="">—</option><option value="autonomo">Caminhoneiro autônomo</option><option value="frota">Frota / transportadora</option><option value="oficina">Oficina</option></select></label>
        <label className="flex gap-3 text-sm md:col-span-2"><input type="checkbox" name="aceita_marketing" defaultChecked={perfil.aceita_marketing} className="h-5 w-5 accent-azul" />Quero receber ofertas e lembretes de revisão.</label>
        <button className="btn btn-sinal md:col-span-2">Salvar</button>
      </form>
      {browserSupportsWebAuthn() && (
        <div className="rounded-md bg-superficie p-6">
          <h2 className="font-display text-2xl font-bold uppercase">Face ID / digital</h2>
          <p className="mt-1 text-sm text-tinta-suave">{n ? `${n} aparelho(s) cadastrado(s).` : 'Entre nas próximas vezes sem senha, só com o rosto ou a digital.'}</p>
          <button onClick={ativaFaceId} className="btn btn-azul mt-4">Ativar neste aparelho</button>
        </div>
      )}
      {msg && <p role="status" className="font-semibold">{msg}</p>}
      <button onClick={async () => { await supabaseBrowser().auth.signOut(); location.href = '/'; }} className="justify-self-start text-sm underline">Sair</button>
    </div>
  );
}
