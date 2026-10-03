# Produtos fitness para dieta (Brasil)

Catálogo + ranking de produtos para emagrecimento/definição, indo além do whey:
snacks crocantes (biscoito de arroz Kalassi, chips de grão-de-bico), macarrão konjac,
barras de proteína, pão proteico, pipoca, gelatina zero, laticínios e proteínas básicas, além de conservas (sardinha, atum, palmito, cogumelo, grão-de-bico),
massa de palmito pupunha e molhos zero.

```bash
python buscar.py                          # proteína por 100 kcal
python buscar.py --por saciedade          # menor kcal/g + mais fibra
python buscar.py --papel lanche --por lanche
python buscar.py --categoria "snack crocante" --max-kcal 120
python buscar.py --preparo pronto --markdown   # tabela "abrir e comer" (TABELA-CORRIDA.md)
python buscar.py --baixa-kcal --por saciedade   # até 100 kcal/porção
python buscar.py --max-kcal 250 --min-proteina 10
python buscar.py --viagem aviao                 # livre na bagagem de mão
python buscar.py --por custo                    # R$ por g de proteína (após o monitor ler preços)
python buscar.py --viagem carro                 # sem geladeira
```

`papel`: `proteina`, `lanche`, `base`, `gordura`. Cada item tem `fonte`
(`estimado` ou `varejista/rotulo (conferir)`) e `obs` com dica de uso.

## Site com filtros
`index.html` lista os produtos com busca e filtros (papel, abrir e comer, avião, carro, kcal, proteína) e ordenação.
Para ver localmente: `python -m http.server` e abra http://localhost:8000.
Publicação: o workflow `validar-e-publicar.yml` valida os dados e publica no GitHub Pages quando houver push na `main`
(ative em *Settings > Pages > Source: GitHub Actions*). `python validar.py` checa campos, duplicatas e coerência calórica.

## Montar lanche (no site)
O painel "Montar um lanche" sugere combinações de 2 ou 3 itens "abrir e comer" dentro de um limite de kcal
e proteína mínima, por lugar (qualquer, avião, carro). A lógica está em `combos.js` (testável com Node).

## Monitoramento contínuo
`monitor.py` lê o preço dos produtos que têm `link` e grava em `historico.csv`;
se o preço mudar, cria `alertas.md`. O workflow `.github/workflows/monitor-precos.yml`
roda **a cada 6 horas** (e manualmente em *Actions > Run workflow*) e faz commit do histórico.
Limites: lojas que bloqueiam robôs ou carregam o preço via JavaScript aparecem como `sem_preco`/`erro`
no CSV; nesses casos troque o link por outra loja. Para novos produtos, basta adicionar `link` no JSON.

## Como evoluir
- Preencha `preco_brl`, `link` e `rendimento_porcoes` para calcular R$ por g de proteína.
- Valores são aproximados; sempre confira o rótulo atual. Não substitui nutricionista.

## Fontes
Whey: produtosanalisados.com.br, projetoacerto.com.br. Kalassi: casaplaza.com.br, cafezale.com.br.
Fit Food: fatsecret.com.br, celeiromicah.com.br. Konjac Massa MF: fatsecret.com.br.
Bold / Protein Crisp: drogasil.com.br, integralmedica.com.br. Wickbold: fatsecret.com.br.

## Tabelas prontas
`TABELA-BAIXA-KCAL.md`, `TABELA-PROTEINA-ATE-250KCAL.md`, `TABELA-VIAGEM-AVIAO.md`,
`TABELA-VIAGEM-CARRO.md`, `TABELA-CORRIDA.md`. Regenere com `--markdown`.

## Viagem de avião
"ok" = sólido, embalado, sem refrigeração. "restrito" = líquido, pasta ou gel: em voo
internacional cada embalagem tem limite de 100 ml (regra de bagagem de mão); em voo doméstico
as regras costumam ser mais folgadas, mas confira a companhia aérea. Proteína em pó é permitida.
