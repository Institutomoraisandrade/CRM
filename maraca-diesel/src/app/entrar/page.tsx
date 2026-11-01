import { Topo } from '@/components/Topo';
import { Entrar } from './Entrar';
export const metadata = { title: 'Entrar' };
export default async function Pagina({ searchParams }: { searchParams: Promise<{ volta?: string }> }) {
  const { volta } = await searchParams;
  return (<><Topo /><main className="mx-auto max-w-md px-5 py-20"><span className="over">MINHA CONTA</span><h1 className="titulo mt-3">Entrar para comprar</h1><div className="mt-10"><Entrar volta={volta?.startsWith('/') ? volta : '/conta'} /></div></main></>);
}
