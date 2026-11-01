'use client';
import Link from 'next/link';
import { useState } from 'react';
import { Topo } from '@/components/Topo';
import { brl, useCarrinho } from '@/components/Carrinho';
import { novoEventId, rastreia } from '@/components/Rastreio';

export default function Carrinho() {
  const { itens, muda, total, limpa } = useCarrinho();
  const [erro, setErro] = useState(''), [enviando, setEnviando] = useState(false);

  async function finaliza(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); setErro(''); setEnviando(true);
    const f = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>;
    const eventId = novoEventId();
    rastreia('InitiateCheckout', { value: total, currency: 'BRL', num_items: itens.length }, eventId);
    const r = await fetch('/api/pedidos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
      itens: itens.map((i) => ({ produtoId: i.produtoId, quantidade: i.quantidade })), eventId,
      entrega: { cep: f.cep, endereco: f.endereco, numero: f.numero, cidade: f.cidade, uf: f.uf.toUpperCase(), retirar: f.retirar === 'on' } }) });
    const j = await r.json().catch(() => ({}));
    setEnviando(false);
    if (r.status === 401) { location.href = '/entrar?volta=/carrinho'; return; }
    if (!r.ok) { setErro(j.erro ?? 'Erro'); return; }
    limpa();
    location.href = j.pagamentoUrl ?? `/conta?pedido=${j.pedidoId}`;
  }
  async function cep(v: string) {
    if (v.replace(/\D/g, '').length !== 8) return;
    const d = await fetch(`https://viacep.com.br/ws/${v.replace(/\D/g, '')}/json/`).then((x) => x.json()).catch(() => null);
    if (!d || d.erro) return;
    const set = (n: string, val: string) => { const el = document.querySelector<HTMLInputElement>(`[name=${n}]`); if (el) el.value = val; };
    set('endereco', `${d.logradouro}, ${d.bairro}`); set('cidade', d.localidade); set('uf', d.uf);
  }

  return (
    <>
      <Topo />
      <main className="mx-auto max-w-5xl px-5 py-14">
        <h1 className="titulo">Carrinho</h1>
        {!itens.length ? <p className="mt-8">Seu carrinho está vazio. <Link href="/catalogo" className="font-semibold text-azul underline">Ver catálogo</Link></p> : (
          <div className="mt-10 grid gap-10 lg:grid-cols-[1.4fr_1fr]">
            <ul className="divide-y divide-linha">
              {itens.map((i) => (
                <li key={i.produtoId} className="flex items-center gap-4 py-4">
                  <Link href={`/catalogo/${i.slug}`} className="flex-1 font-semibold">{i.nome}</Link>
                  <input type="number" min={0} max={99} value={i.quantidade} onChange={(e) => muda(i.produtoId, Number(e.target.value))} className="campo w-20" aria-label={`Quantidade de ${i.nome}`} />
                  <span className="w-28 text-right font-bold">{brl(i.preco * i.quantidade)}</span>
                </li>
              ))}
              <li className="flex justify-between py-4 font-display text-2xl font-extrabold"><span>Total</span><span>{brl(total)}</span></li>
            </ul>
            <form onSubmit={finaliza} className="grid content-start gap-3 rounded-md bg-superficie p-6">
              <h2 className="font-display text-2xl font-bold uppercase">Entrega</h2>
              <input className="campo" name="cep" placeholder="CEP" required onBlur={(e) => cep(e.target.value)} />
              <input className="campo" name="endereco" placeholder="Endereço" required />
              <div className="grid grid-cols-[1fr_2fr_70px] gap-2"><input className="campo" name="numero" placeholder="Nº" /><input className="campo" name="cidade" placeholder="Cidade" required /><input className="campo uppercase" name="uf" placeholder="UF" maxLength={2} required /></div>
              <label className="flex gap-2 text-sm"><input type="checkbox" name="retirar" /> Vou retirar na loja</label>
              {erro && <p role="alert" className="text-red-700">{erro}</p>}
              <button className="btn btn-sinal btn-lg" disabled={enviando}>{enviando ? 'Processando…' : 'Finalizar compra'}</button>
              <p className="text-xs text-tinta-suave">Pagamento por Pix, cartão ou boleto (Mercado Pago). É preciso entrar com Google ou Face ID.</p>
            </form>
          </div>
        )}
      </main>
    </>
  );
}
