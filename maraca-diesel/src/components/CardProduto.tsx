import Link from 'next/link';
import type { Produto } from '@/lib/catalogo';
import { brl } from './Carrinho';

export function CardProduto({ p }: { p: Produto }) {
  const preco = p.preco_promocional ?? p.preco;
  return (
    <Link href={`/catalogo/${p.slug}`} className="group flex flex-col overflow-hidden rounded-md border border-linha bg-white transition hover:-translate-y-1 hover:shadow-xl">
      <div className="grid aspect-[4/3] place-items-center bg-superficie">
        {p.imagens?.[0] ? <img src={p.imagens[0]} alt={p.nome} className="h-full w-full object-cover" loading="lazy" /> : <span className="font-display text-2xl font-bold text-linha">{p.sku}</span>}
      </div>
      <div className="flex flex-1 flex-col gap-1 p-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-tinta-suave">{p.categorias?.nome}{p.codigo_original ? ` · Cód. ${p.codigo_original}` : ''}</span>
        <h3 className="font-display text-xl font-bold leading-tight group-hover:text-azul">{p.nome}</h3>
        <span className="mt-auto pt-2 text-lg font-bold">{p.sob_consulta || preco == null ? 'Sob consulta' : brl(Number(preco))}</span>
      </div>
    </Link>
  );
}
