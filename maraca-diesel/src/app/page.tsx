import Link from 'next/link';
import { Hero } from '@/components/hero/Hero';
import { Revela } from '@/components/Revela';
import { CardProduto } from '@/components/CardProduto';
import { FormOrcamento } from '@/components/FormOrcamento';
import { listaProdutos } from '@/lib/catalogo';

const SERVICOS = [['01', 'Freios'], ['02', 'Suspensão'], ['03', 'Motor'], ['04', 'Elétrica']];

export default async function Home() {
  const destaques = await listaProdutos({ limite: 8 });
  return (
    <main>
      <Hero />
      <Revela />
      <section id="servicos" className="bg-superficie px-5 py-24 md:px-16">
        <span className="over js-rev">SERVIÇOS</span>
        <h2 className="titulo js-rev mt-3 max-w-3xl">Tudo para o caminhão parar pouco</h2>
        <div className="js-cards mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {SERVICOS.map(([n, t]) => (
            <article key={n} className="rounded-md border-t-4 border-azul bg-white p-6 shadow-sm">
              <span className="font-display text-4xl font-extrabold text-amarelo">{n}</span>
              <h3 className="mt-2 font-display text-2xl font-bold uppercase">{t}</h3>
              <p className="mt-2 text-tinta-suave">Descrição do serviço a confirmar com a equipe.</p>
            </article>
          ))}
        </div>
      </section>
      <section className="px-5 py-24 md:px-16">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div><span className="over js-rev">CATÁLOGO</span><h2 className="titulo js-rev mt-3">Peças à pronta-entrega</h2></div>
          <Link href="/catalogo" className="btn btn-azul">Ver catálogo completo</Link>
        </div>
        {destaques.length ? (
          <div className="js-cards mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{destaques.map((p) => <CardProduto key={p.id} p={p} />)}</div>
        ) : <p className="mt-8 text-tinta-suave">Catálogo sendo atualizado. Peça sua peça pelo orçamento abaixo.</p>}
      </section>
      <section id="orcamento" className="bg-marinho px-5 py-24 text-white md:px-16">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[1fr_1.3fr]">
          <div>
            <span className="over js-rev !text-amarelo">ORÇAMENTO</span>
            <h2 className="titulo js-rev mt-3">Precisa de peça ou serviço? Chama a gente.</h2>
            <p className="js-rev mt-5 text-suave">Preencha em 30 segundos. Respondemos pelo WhatsApp com preço e prazo.</p>
          </div>
          <div className="rounded-md bg-white p-6 text-tinta md:p-8"><FormOrcamento /></div>
        </div>
      </section>
      <footer className="bg-tinta px-5 py-10 text-sm text-suave md:px-16">© {new Date().getFullYear()} Maracá Diesel · <Link href="/privacidade" className="underline">Privacidade</Link></footer>
    </main>
  );
}
