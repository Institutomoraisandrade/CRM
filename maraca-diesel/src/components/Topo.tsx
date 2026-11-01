'use client';
import Link from 'next/link';
import { useCarrinho } from './Carrinho';

export function Topo({ escuro = false }: { escuro?: boolean }) {
  const { itens } = useCarrinho();
  const n = itens.reduce((s, i) => s + i.quantidade, 0);
  return (
    <header className={`${escuro ? 'absolute text-white' : 'sticky bg-marinho text-white'} inset-x-0 top-0 z-20 flex h-20 items-center gap-6 px-5 md:px-16`}>
      <Link href="/" className="flex flex-col leading-none" aria-label="Maracá Diesel, início">
        <b className="font-display text-[22px] md:text-[28px] font-extrabold tracking-wide">MARACÁ DIESEL</b>
        <span className="mt-1 text-[10px] font-bold tracking-[.22em] text-suave">PEÇAS E SERVIÇOS</span>
      </Link>
      <nav aria-label="Principal" className="ml-auto hidden gap-7 font-semibold md:flex">
        <Link className="nav-link" href="/catalogo">Peças</Link>
        <Link className="nav-link" href="/#servicos">Serviços</Link>
        <Link className="nav-link" href="/orcamento">Orçamento</Link>
        <Link className="nav-link" href="/conta">Minha conta</Link>
      </nav>
      <Link href="/carrinho" className="relative ml-auto md:ml-0" aria-label={`Carrinho, ${n} itens`}>
        <svg viewBox="0 0 24 24" className="h-7 w-7 fill-none stroke-current stroke-2"><path d="M3 4h2l2.4 11h10.2L20 7H6.2M9 20a1 1 0 1 0 0-.01M17 20a1 1 0 1 0 0-.01" /></svg>
        {n > 0 && <span className="absolute -right-2 -top-2 grid h-5 min-w-5 place-items-center rounded-full bg-amarelo px-1 text-xs font-bold text-tinta">{n}</span>}
      </Link>
      <Link href="/orcamento" className="btn btn-sinal hidden sm:inline-flex">Pedir orçamento</Link>
    </header>
  );
}
