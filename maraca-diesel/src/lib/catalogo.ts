import 'server-only';
import { supabaseServer } from './supabase/server';

export type Produto = { id: string; sku: string; slug: string; nome: string; descricao: string | null; marca: string | null; aplicacao: string[] | null;
  codigo_original: string | null; preco: number | null; preco_promocional: number | null; estoque: number; imagens: string[]; sob_consulta: boolean; categorias: { nome: string; slug: string } | null };

const configurado = () => !!process.env.NEXT_PUBLIC_SUPABASE_URL;

export async function listaProdutos(f: { q?: string; categoria?: string; limite?: number } = {}): Promise<Produto[]> {
  if (!configurado()) return [];
  const sb = await supabaseServer();
  let q = sb.from('produtos').select('*, categorias!inner(nome,slug)').eq('ativo', true).order('nome').limit(f.limite ?? 60);
  if (f.categoria) q = q.eq('categorias.slug', f.categoria);
  if (f.q) q = q.or(`nome.ilike.%${f.q.replace(/[%,()]/g, '')}%,codigo_original.ilike.%${f.q.replace(/[%,()]/g, '')}%,sku.ilike.%${f.q.replace(/[%,()]/g, '')}%`);
  const { data } = await q;
  return (data ?? []) as Produto[];
}
export async function produto(slug: string) {
  if (!configurado()) return null;
  const { data } = await (await supabaseServer()).from('produtos').select('*, categorias(nome,slug)').eq('slug', slug).eq('ativo', true).single();
  return data as Produto | null;
}
export async function categorias() {
  if (!configurado()) return [];
  const { data } = await (await supabaseServer()).from('categorias').select('nome,slug').order('ordem');
  return data ?? [];
}
