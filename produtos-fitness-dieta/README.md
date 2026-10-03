# Catálogo de produtos fitness para dieta (Brasil)

Catálogo de produtos do meio fitness, úteis para dieta, encontrados por pesquisa na internet e
atualizados periodicamente. Cobre snacks crocantes (biscoito de arroz Kalassi, chips de grão-de-bico),
macarrão konjac e massas alternativas, conservas, barras e cookies proteicos, pães proteicos,
laticínios proteicos, carne seca, molhos e sobremesas zero, whey e proteínas em pó.

## Arquivos
- `produtos.json`: o catálogo. Por porção: kcal, proteína, fibra, preparo, viagem (avião/carro),
  `fonte` (rótulo/varejista ou `estimado`), observação de uso e link de loja quando houver.
- `TABELA-*.md`: tabelas prontas (baixa caloria, proteína até 250 kcal, avião, carro, rotina corrida).
- `buscar.py`: consulta local do catálogo (`python buscar.py --por saciedade`, `--viagem aviao`,
  `--max-kcal 250 --min-proteina 10`, `--markdown`).
- `validar.py`: confere campos, duplicatas e coerência calórica.

## Como atualizar
Pesquisar novos produtos, adicionar ao `produtos.json` com a fonte, rodar `python validar.py` e
regenerar as tabelas com `python buscar.py <filtros> --markdown > TABELA-....md`.

Valores aproximados: confira sempre o rótulo. Não substitui orientação de nutricionista.
