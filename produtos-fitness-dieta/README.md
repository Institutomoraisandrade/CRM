# Produtos fitness para dieta (Brasil)

Catálogo + ranking de produtos para emagrecimento/definição, indo além do whey:
snacks crocantes (biscoito de arroz Kalassi, chips de grão-de-bico), macarrão konjac,
barras de proteína, pão proteico, pipoca, gelatina zero, laticínios e proteínas básicas.

```bash
python buscar.py                          # proteína por 100 kcal
python buscar.py --por saciedade          # menor kcal/g + mais fibra
python buscar.py --papel lanche --por lanche
python buscar.py --categoria "snack crocante" --max-kcal 120
```

`papel`: `proteina`, `lanche`, `base`, `gordura`. Cada item tem `fonte`
(`estimado` ou `varejista/rotulo (conferir)`) e `obs` com dica de uso.

## Como evoluir
- Preencha `preco_brl`, `link` e `rendimento_porcoes` para calcular R$ por g de proteína.
- Valores são aproximados; sempre confira o rótulo atual. Não substitui nutricionista.

## Fontes
Whey: produtosanalisados.com.br, projetoacerto.com.br. Kalassi: casaplaza.com.br, cafezale.com.br.
Fit Food: fatsecret.com.br, celeiromicah.com.br. Konjac Massa MF: fatsecret.com.br.
Bold / Protein Crisp: drogasil.com.br, integralmedica.com.br. Wickbold: fatsecret.com.br.
