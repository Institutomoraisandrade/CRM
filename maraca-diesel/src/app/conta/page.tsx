import { redirect } from 'next/navigation';
import { Topo } from '@/components/Topo';
import { brl } from '@/components/Carrinho';
import { supabaseServer } from '@/lib/supabase/server';
import { Perfil } from './Perfil';

export const metadata = { title: 'Minha conta' };
export default async function Conta() {
  const sb = await supabaseServer();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) redirect('/entrar');
  const [{ data: perfil }, { count }, { data: pedidos }] = await Promise.all([
    sb.from('perfis').select('*').eq('id', user.id).single(),
    sb.from('passkeys').select('id', { count: 'exact', head: true }).eq('usuario_id', user.id),
    sb.from('pedidos').select('id,status,total,criado_em').order('criado_em', { ascending: false }).limit(20),
  ]);
  return (
    <>
      <Topo />
      <main className="mx-auto grid max-w-5xl gap-14 px-5 py-14">
        <div><span className="over">MINHA CONTA</span><h1 className="titulo mt-3">Olá, {perfil?.nome?.split(' ')[0] ?? 'cliente'}</h1></div>
        <Perfil perfil={perfil!} passkeys={count ?? 0} />
        <section>
          <h2 className="font-display text-3xl font-bold uppercase">Meus pedidos</h2>
          {pedidos?.length ? <ul className="mt-4 divide-y divide-linha">{pedidos.map((p) => (
            <li key={p.id} className="flex justify-between py-3"><span>#{p.id.slice(0, 8)} · {new Date(p.criado_em).toLocaleDateString('pt-BR')}</span><span className="font-semibold">{p.status.replace('_', ' ')}</span><span>{brl(Number(p.total))}</span></li>
          ))}</ul> : <p className="mt-3 text-tinta-suave">Nenhum pedido ainda.</p>}
        </section>
      </main>
    </>
  );
}
