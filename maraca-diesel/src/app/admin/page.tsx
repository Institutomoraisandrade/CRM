import { notFound } from 'next/navigation';
import { Topo } from '@/components/Topo';
import { brl } from '@/components/Carrinho';
import { supabaseServer } from '@/lib/supabase/server';

// Painel mínimo: leads de orçamento + pedidos. Produtos são editados no Supabase Studio (ou importados por CSV) nesta fase.
export default async function Admin() {
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  const { data: eu } = await sb.from('perfis').select('papel').eq('id', user?.id ?? '').single();
  if (eu?.papel !== 'admin') notFound();
  const [{ data: orc }, { data: ped }] = await Promise.all([
    sb.from('orcamentos').select('*').order('criado_em', { ascending: false }).limit(100),
    sb.from('pedidos').select('id,status,total,criado_em').order('criado_em', { ascending: false }).limit(50),
  ]);
  const zap = (t: string) => `https://wa.me/55${t.replace(/\D/g, '').replace(/^55/, '')}`;
  return (
    <>
      <Topo />
      <main className="px-5 py-12 md:px-16">
        <h1 className="titulo">Painel</h1>
        <h2 className="mt-10 font-display text-3xl font-bold uppercase">Orçamentos</h2>
        <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm">
          <thead><tr className="border-b border-linha"><th className="py-2">Data</th><th>Nome</th><th>Contato</th><th>Tipo</th><th>Veículo</th><th>Mensagem</th><th>Origem</th><th>Status</th></tr></thead>
          <tbody>{orc?.map((o) => (
            <tr key={o.id} className="border-b border-linha align-top">
              <td className="py-2">{new Date(o.criado_em).toLocaleString('pt-BR')}</td><td className="font-semibold">{o.nome}</td>
              <td><a className="text-azul underline" href={zap(o.telefone)} target="_blank">{o.telefone}</a><br /><a href={`mailto:${o.email}`}>{o.email}</a></td>
              <td>{o.tipo}</td><td>{o.veiculo} {o.placa}</td><td className="max-w-xs">{o.mensagem}</td><td>{o.origem?.utm_source ?? '—'}</td><td>{o.status}</td>
            </tr>))}</tbody>
        </table></div>
        <h2 className="mt-12 font-display text-3xl font-bold uppercase">Pedidos</h2>
        <ul className="mt-4">{ped?.map((p) => <li key={p.id}>#{p.id.slice(0, 8)} · {p.status} · {brl(Number(p.total))}</li>)}</ul>
      </main>
    </>
  );
}
