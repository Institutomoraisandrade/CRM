import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Topo } from '@/components/Topo';
import { AcoesProduto } from './AcoesProduto';
import { produto } from '@/lib/catalogo';
import { brl } from '@/components/Carrinho';

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const p = await produto((await params).slug);
  return { title: p?.nome ?? 'Produto', description: p?.descricao ?? undefined, openGraph: { images: p?.imagens?.slice(0, 1) } };
}

export default async function Pagina({ params }: { params: Promise<{ slug: string }> }) {
  const p = await produto((await params).slug);
  if (!p) notFound();
  const preco = p.preco_promocional ?? p.preco;
  const compravel = !p.sob_consulta && preco != null && p.estoque > 0;
  const ld = { '@context': 'https://schema.org', '@type': 'Product', name: p.nome, sku: p.sku, description: p.descricao, image: p.imagens,
    offers: preco != null ? { '@type': 'Offer', price: preco, priceCurrency: 'BRL', availability: p.estoque > 0 ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock' } : undefined };
  return (
    <>
      <Topo />
      <main className="mx-auto grid max-w-6xl gap-10 px-5 py-14 md:grid-cols-2">
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
        <div className="grid aspect-square place-items-center rounded-md bg-superficie">
          {p.imagens?.[0] ? <img src={p.imagens[0]} alt={p.nome} className="h-full w-full rounded-md object-cover" /> : <span className="font-display text-4xl text-linha">{p.sku}</span>}
        </div>
        <div>
          <Link href={`/catalogo?c=${p.categorias?.slug}`} className="over">{p.categorias?.nome?.toUpperCase()}</Link>
          <h1 className="titulo mt-3">{p.nome}</h1>
          <dl className="mt-5 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
            <dt className="text-tinta-suave">SKU</dt><dd>{p.sku}</dd>
            {p.codigo_original && <><dt className="text-tinta-suave">Cód. original</dt><dd>{p.codigo_original}</dd></>}
            {p.marca && <><dt className="text-tinta-suave">Marca</dt><dd>{p.marca}</dd></>}
            {p.aplicacao?.length ? <><dt className="text-tinta-suave">Aplicação</dt><dd>{p.aplicacao.join(', ')}</dd></> : null}
            <dt className="text-tinta-suave">Estoque</dt><dd>{p.estoque > 0 ? `${p.estoque} un.` : 'Sob encomenda'}</dd>
          </dl>
          <p className="mt-6 font-display text-4xl font-extrabold">{compravel ? brl(Number(preco)) : 'Sob consulta'}</p>
          {p.descricao && <p className="mt-4 text-tinta-suave">{p.descricao}</p>}
          <AcoesProduto compravel={compravel} item={{ produtoId: p.id, nome: p.nome, preco: Number(preco ?? 0), slug: p.slug, imagem: p.imagens?.[0] }} />
        </div>
      </main>
    </>
  );
}
