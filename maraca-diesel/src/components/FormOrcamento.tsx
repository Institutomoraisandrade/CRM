'use client';
import { useState } from 'react';
import { novoEventId, rastreia } from './Rastreio';

type Props = { produtoId?: string; produtoNome?: string; inicial?: { nome?: string; email?: string; telefone?: string } };

const mascaraTel = (v: string) => v.replace(/\D/g, '').slice(0, 11).replace(/^(\d{2})(\d)/, '($1) $2').replace(/(\d{5})(\d{1,4})$/, '$1-$2');

export function FormOrcamento({ produtoId, produtoNome, inicial }: Props) {
  const [estado, setEstado] = useState<'livre' | 'enviando' | 'ok' | 'erro'>('livre');
  const [msg, setMsg] = useState('');
  const [zap, setZap] = useState<string | null>(null);
  const [tel, setTel] = useState(inicial?.telefone ?? '');

  async function envia(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const eventId = novoEventId();
    setEstado('enviando');
    const r = await fetch('/api/orcamento', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...Object.fromEntries(f), telefone: tel, aceitaMarketing: f.get('aceitaMarketing') === 'on', produtoId, eventId }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { setEstado('erro'); setMsg(j.erro ?? 'Erro ao enviar'); return; }
    rastreia('Lead', { content_name: produtoNome ?? 'orcamento' }, eventId);
    setZap(j.whatsapp); setMsg(`Protocolo ${j.protocolo}. Nossa equipe vai falar com você em breve.`); setEstado('ok');
  }

  if (estado === 'ok') return (
    <div className="rounded-md border-l-4 border-amarelo bg-superficie p-6" role="status">
      <h3 className="font-display text-3xl font-extrabold uppercase">Pedido recebido!</h3>
      <p className="mt-2 text-tinta-suave">{msg}</p>
      {zap && <a href={zap} target="_blank" rel="noopener" className="btn btn-azul mt-5">Adiantar pelo WhatsApp</a>}
    </div>
  );

  return (
    <form onSubmit={envia} className="grid gap-4 md:grid-cols-2" noValidate={false}>
      {produtoNome && <p className="md:col-span-2 rounded bg-superficie px-4 py-3 text-sm">Orçamento para: <b>{produtoNome}</b></p>}
      <label className="md:col-span-2"><span className="rotulo">Nome completo *</span><input className="campo" name="nome" required minLength={2} autoComplete="name" defaultValue={inicial?.nome} /></label>
      <label><span className="rotulo">E-mail *</span><input className="campo" name="email" type="email" required autoComplete="email" defaultValue={inicial?.email} /></label>
      <label><span className="rotulo">Telefone / WhatsApp *</span><input className="campo" name="telefone" type="tel" inputMode="tel" required autoComplete="tel" value={tel} onChange={(e) => setTel(mascaraTel(e.target.value))} placeholder="(00) 00000-0000" /></label>
      <label><span className="rotulo">Preciso de</span>
        <select className="campo" name="tipo" defaultValue="peca"><option value="peca">Peça</option><option value="servico">Serviço</option><option value="ambos">Peça e serviço</option></select></label>
      <label><span className="rotulo">Caminhão (marca / modelo / ano)</span><input className="campo" name="veiculo" placeholder="Ex.: Scania R440 2015" /></label>
      <label><span className="rotulo">Placa</span><input className="campo uppercase" name="placa" maxLength={8} /></label>
      <label className="md:col-span-2"><span className="rotulo">O que você precisa?</span><textarea className="campo min-h-28" name="mensagem" placeholder="Descreva a peça (código, se tiver) ou o problema do caminhão." /></label>
      <input name="site" tabIndex={-1} autoComplete="off" className="hidden" aria-hidden />
      <label className="flex items-start gap-3 text-sm text-tinta-suave md:col-span-2">
        <input type="checkbox" name="aceitaMarketing" className="mt-1 h-5 w-5 accent-azul" />
        Quero receber ofertas de peças e revisões por WhatsApp e e-mail. (Você pode sair quando quiser.)
      </label>
      {estado === 'erro' && <p className="text-red-700 md:col-span-2" role="alert">{msg}</p>}
      <button className="btn btn-sinal btn-lg md:col-span-2" disabled={estado === 'enviando'}>{estado === 'enviando' ? 'Enviando…' : 'Receber orçamento'}</button>
      <p className="text-xs text-tinta-suave md:col-span-2">Seus dados são usados para responder este pedido, conforme a <a className="underline" href="/privacidade">LGPD</a>.</p>
    </form>
  );
}
