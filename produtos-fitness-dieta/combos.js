// Sugere combinações de 2 ou 3 produtos dentro de um orçamento de kcal, maximizando proteína.
function sugerirCombos(produtos, { kcalMax, protMin = 0, tamanho = 2, local = '', topo = 5, soPronto = true }) {
  const ok = produtos.filter(p => {
    if (soPronto && p.preparo !== 'pronto') return false;
    // ingredientes de cozinha não são lanche
    if (['molho zero', 'volume/saciedade', 'massa alternativa'].includes(p.categoria)) return false;
    if (p.categoria === 'conserva' && p.papel === 'base') return false;
    if (local === 'aviao') return p.viagem_aviao === 'ok';
    if (local === 'carro') return p.viagem_carro === 'sem geladeira';
    if (local === 'pronto') return p.preparo === 'pronto';
    return true;
  });
  const res = [];
  const rec = (ini, atual) => {
    if (atual.length === tamanho) {
      const kcal = atual.reduce((a, p) => a + p.kcal, 0);
      const prot = atual.reduce((a, p) => a + p.proteina_g, 0);
      const cats = new Set(atual.map(p => p.categoria));
      const nProt = atual.filter(p => p.papel === 'proteina').length;
      if (cats.size === atual.length && nProt <= 1 && kcal <= kcalMax && prot >= protMin) {
        res.push({ itens: atual.slice(), kcal, prot, p100: prot / Math.max(kcal, 1) * 100 });
      }
      return;
    }
    for (let i = ini; i < ok.length; i++) rec(i + 1, atual.concat(ok[i]));
  };
  rec(0, []);
  res.sort((a, b) => b.prot - a.prot || a.kcal - b.kcal);
  const vistos = new Set(), saida = [];
  for (const r of res) {
    const chave = r.itens.map(p => p.categoria).sort().join('|');
    if (vistos.has(chave)) continue; // uma sugestão por tipo de combinação
    vistos.add(chave);
    saida.push(r);
    if (saida.length >= topo) break;
  }
  return saida;
}
if (typeof module !== 'undefined') module.exports = { sugerirCombos };
