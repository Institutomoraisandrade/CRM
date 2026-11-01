'use client';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { novoEventId, rastreia } from './Rastreio';

export type Item = { produtoId: string; nome: string; preco: number; quantidade: number; imagem?: string; slug: string };
type Ctx = { itens: Item[]; add: (i: Omit<Item, 'quantidade'>) => void; muda: (id: string, q: number) => void; limpa: () => void; total: number };
const C = createContext<Ctx | null>(null);

export function CarrinhoProvider({ children }: { children: ReactNode }) {
  const [itens, setItens] = useState<Item[]>([]);
  useEffect(() => { try { setItens(JSON.parse(localStorage.getItem('md_carrinho') ?? '[]')); } catch {} }, []);
  useEffect(() => { localStorage.setItem('md_carrinho', JSON.stringify(itens)); }, [itens]);
  const add: Ctx['add'] = (i) => {
    rastreia('AddToCart', { content_ids: [i.produtoId], content_name: i.nome, value: i.preco, currency: 'BRL' }, novoEventId());
    setItens((l) => l.some((x) => x.produtoId === i.produtoId) ? l.map((x) => x.produtoId === i.produtoId ? { ...x, quantidade: x.quantidade + 1 } : x) : [...l, { ...i, quantidade: 1 }]);
  };
  const muda = (id: string, q: number) => setItens((l) => q <= 0 ? l.filter((x) => x.produtoId !== id) : l.map((x) => x.produtoId === id ? { ...x, quantidade: q } : x));
  return <C.Provider value={{ itens, add, muda, limpa: () => setItens([]), total: itens.reduce((s, i) => s + i.preco * i.quantidade, 0) }}>{children}</C.Provider>;
}
export const useCarrinho = () => useContext(C)!;
export const brl = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
