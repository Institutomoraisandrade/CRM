'use client';
import Link from 'next/link';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCarrinho, type Item } from '@/components/Carrinho';
import { rastreia } from '@/components/Rastreio';

export function AcoesProduto({ compravel, item }: { compravel: boolean; item: Omit<Item, 'quantidade'> }) {
  const { add } = useCarrinho();
  const r = useRouter();
  useEffect(() => { rastreia('ViewContent', { content_ids: [item.produtoId], content_name: item.nome, content_type: 'product', value: item.preco, currency: 'BRL' }); }, [item]);
  return (
    <div className="mt-8 flex flex-wrap gap-3">
      {compravel && <button className="btn btn-sinal btn-lg" onClick={() => { add(item); r.push('/carrinho'); }}>Comprar</button>}
      <Link href={`/orcamento?produto=${item.slug}`} className={`btn btn-lg ${compravel ? 'border-azul text-azul' : 'btn-sinal'}`}>Pedir orçamento</Link>
    </div>
  );
}
