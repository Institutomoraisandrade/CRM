import { Topo } from '@/components/Topo';
import { FormOrcamento } from '@/components/FormOrcamento';
import { produto } from '@/lib/catalogo';
import { supabaseServer } from '@/lib/supabase/server';

export const metadata = { title: 'Pedir orçamento' };

export default async function Pagina({ searchParams }: { searchParams: Promise<{ produto?: string }> }) {
  const { produto: slug } = await searchParams;
  const p = slug ? await produto(slug) : null;
  let inicial;
  if (process.env.NEXT_PUBLIC_SUPABASE_URL) {
    const sb = await supabaseServer();
    const { data: { user } } = await sb.auth.getUser();
    if (user) { const { data } = await sb.from('perfis').select('nome,email,telefone').eq('id', user.id).single(); inicial = data ?? undefined; }
  }
  return (
    <>
      <Topo />
      <main className="mx-auto max-w-3xl px-5 py-16">
        <span className="over">ORÇAMENTO</span>
        <h1 className="titulo mt-3">Receba seu orçamento</h1>
        <p className="mt-4 text-tinta-suave">Conte o que precisa. A equipe responde pelo WhatsApp ou e-mail.</p>
        <div className="mt-10"><FormOrcamento produtoId={p?.id} produtoNome={p?.nome} inicial={inicial} /></div>
      </main>
    </>
  );
}
