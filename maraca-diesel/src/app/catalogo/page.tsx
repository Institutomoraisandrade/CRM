import Link from 'next/link';
import { Topo } from '@/components/Topo';
import { CardProduto } from '@/components/CardProduto';
import { categorias, listaProdutos } from '@/lib/catalogo';

export const metadata = { title: 'Catálogo de peças' };
export const revalidate = 60;

export default async function Catalogo({ searchParams }: { searchParams: Promise<{ q?: string; c?: string }> }) {
  const { q, c } = await searchParams;
  const [prods, cats] = await Promise.all([listaProdutos({ q, categoria: c }), categorias()]);
  return (
    <>
      <Topo />
      <main className="px-5 py-14 md:px-16">
        <span className="over">CATÁLOGO</span>
        <h1 className="titulo mt-3">Peças para caminhões</h1>
        <form className="mt-8 flex max-w-xl gap-2" role="search">
          <input name="q" defaultValue={q} className="campo" placeholder="Busque por nome, código original ou SKU" aria-label="Buscar peças" />
          {c && <input type="hidden" name="c" value={c} />}
          <button className="btn btn-azul">Buscar</button>
        </form>
        <nav className="mt-6 flex flex-wrap gap-2" aria-label="Categorias">
          <Link href="/catalogo" className={`rounded-full border px-4 py-1.5 text-sm font-semibold ${!c ? 'border-azul bg-azul text-white' : 'border-linha'}`}>Todas</Link>
          {cats.map((k) => <Link key={k.slug} href={`/catalogo?c=${k.slug}`} className={`rounded-full border px-4 py-1.5 text-sm font-semibold ${c === k.slug ? 'border-azul bg-azul text-white' : 'border-linha'}`}>{k.nome}</Link>)}
        </nav>
        {prods.length ? <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{prods.map((p) => <CardProduto key={p.id} p={p} />)}</div>
          : <p className="mt-10 text-tinta-suave">Nenhuma peça encontrada. <Link className="font-semibold text-azul underline" href="/orcamento">Peça um orçamento</Link> que a gente procura para você.</p>}
      </main>
    </>
  );
}
