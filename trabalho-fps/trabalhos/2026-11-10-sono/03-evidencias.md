# Melhor evidência disponível — Sono, perda de peso e rotina: o que o sono muda em hábito alimentar, composição corporal e treinamento

Data da avaliação: 10/11/2026 · Tipo: revisão (estudo pessoal) · Etapa 03 (fps-3-avaliador-evidencias).

Convenções: efeitos com IC 95% e origem do dado (resumo do PubMed ou texto completo PMC). Vírgula decimal. A avaliação crítica de revisões (AMSTAR 2) foi feita, na maioria, **só pelo resumo**, e por isso é **provisória** (os domínios críticos de protocolo prévio, lista de excluídos e justificativa de viés exigem o texto completo). Dados individuais completos de cada estudo estão em `03-quadro-evidencias.json` (94 entradas).

## Pergunta PICOS

Em adultos com sobrepeso/obesidade ou em programa de emagrecimento (P), a restrição ou a curta duração do sono (I), em comparação com sono adequado ou com extensão/melhora do sono (C), altera perda de peso, composição corporal (massa gorda × massa livre de gordura) e ingestão energética (O), em ECR e em sínteses de ECR (S)? Estudos de apetite, ingestão e peso fora de dieta aceitam adultos saudáveis (evidência indireta). Coortes dentro de programas de emagrecimento entram como evidência complementar (prognóstico e adesão). Itens 2 a 7 do briefing (hábito alimentar, treino, rotina, prática, mitos) seguem o mesmo critério por subtema.

## 1. Estratégia de busca

### 1.1 Busca do buscador (03a-busca.json, 10/11/2026)

Strings completas, bases e filtros de data estão em `03a-busca.json` e `01-picos.json`; aqui só o resumo (todas em PubMed, exceto a linha final).

| # | Camada | Resultados | Retidos |
|---|---|---|---|
| 1 | Principal: sono × peso/composição/ingestão (ECR, MA, RS, cruzados, internados), 2004–2026 | 279 | 112 |
| 2 | Hormônios do apetite, fome e ingestão | 95 | 10 |
| 3 | Coortes e ECR de perda de peso (sono, dieta, programa comportamental) | 58 | 24 |
| 4 | Treino: desempenho, força, síntese proteica | 29 | 25 |
| 5 | Exercício → sono (revisões, 2012–2026) | 84 | 41 |
| 6 | Higiene, extensão do sono, tempo na cama (revisões, 2010–2026) | 191 | 42 |
| 7 | Experimentos de laboratório sem filtro de desenho | 87 | 7 |
| 8 | Melatonina × peso/composição/desempenho | 61 | 22 |
| 9 | Suplementos × sono (revisões) | 34 | 22 |
| 10 | Rastreadores de sono × polissonografia (revisões, 2016–2026; a variante ampla, 453, não foi triada) | 21 | 11 |
| 11 | Recuperação no fim de semana, dívida de sono | 151 | 9 |
| 12 | Horário das refeições, alimentação noturna, cronotipo, TRE (ECR e observacionais) | 112 | 16 |
| 13 | Cronotipo e jet lag social (revisões) | 22 | 11 |
| 14 | Cafeína, álcool, telas (adultos) | 243 | 69 |
| 15 | Diretrizes, consensos e declarações | 287 | 33 |
| 16 | Diretrizes brasileiras | 26 | 2 |
| 17 | Consensus (medical_mode, RS/MA, 100 resultados) | 100 | 2 |

Registros dirigidos: Life's Essential 8 (PMID 35766027) por busca direta; seis registros dirigidos da etapa 01 (fonte "dirigida"); diretrizes de insônia da ABS (2023), europeia (2023) e da AASM (2021) mantidas pelo parecer r1. A diretriz **OMA 2026 (Obesity Sleep)** ficou **fora**: o conjunto final do buscador a excluiu por fonte não verificável e eu confirmei o impedimento (ver 1.2).

### 1.2 Buscas e verificações complementares (minhas, 10/11/2026)

| Finalidade | String / ação | Base e filtro | Resultado |
|---|---|---|---|
| Atualização de Watson 2015 (AASM/SRS) | `(Watson NF[Author] OR Badr MS[Author]) AND (sleep duration[ti] OR recommended amount of sleep[ti] OR consensus[ti]) AND (adult OR healthy)` | PubMed, 2016/01/01–2026/11/10 [Date - Publication] | 5 registros; todos lidos; nenhum atualiza a diretriz (estudos de gêmeos, hipertensão, câncer) |
| Atualização de Watson 2015 | `(American Academy of Sleep Medicine[ad] OR Sleep Research Society[ad]) AND (recommended amount of sleep[ti] OR sleep duration recommendation[ti] OR update[ti]) AND (consensus[ti] OR statement[ti])` | PubMed, 2016–2026 | 0 registros |
| Atualização de Walsh 2021 | `(Walsh NP[Author] OR Halson SL[Author]) AND sleep[ti] AND (athlete*[ti] OR consensus[ti] OR update[ti])` | PubMed, 2021/01/01–2026/11/10 | 13 registros; li os 4 mais recentes (42986605, 42934391, 42700960, 41722555): nenhum atualiza o consenso; **9 não lidos** |
| Atualização de Hirshkowitz 2015 e St-Onge 2016 | seleção, na lista de cortes por volume do 03a-candidatos.json, de duas publicações posteriores (PMIDs 42248743 e 40223596) | — | NSF 2026 reavalia a recomendação de duração; AHA 2025 é nova declaração sobre saúde do sono multidimensional |
| Camada ausente: suplementos | seleção, na lista de cortes por volume (subtema 9), de três revisões gerais (33441476, 41470897, 42661485) | — | nenhuma revisão de suplementos estava entre os 95 itens |
| Camada ausente: força no treino sustentado | seleção de 36136596 (ECR, mulheres treinadas) na lista de cortes | — | ECR direto do subtema treino |
| Ano do fascículo | `<PMID>[uid] AND <ano>[ppdat]` para 38072635 (2024), 34459060 (2022), 39631226 (2025), 36518092 (2023), 29397329 (2018), 27743803 (2017) | PubMed | os seis confirmados no ano do fascículo |
| Valor da recomendação AASM/SRS 2015 | WebSearch (AASM/SRS "7 ou mais horas") | web | resultado de busca traz "pelo menos 7 horas, adultos de 18 a 60 anos"; `aasm.org` **não pôde ser aberto** (host fora da rede permitida) |
| OMA Obesity Sleep 2026 | WebSearch | web | só trechos de um *bundle* de bolso em `guidelinecentral.com` (publicado em 7/4/2026, segundo a busca); host **não pôde ser aberto**; sem grau de recomendação; **não usada** |

Texto completo PMC lido: Tasali (PMC8822469), Nedeltcheva (PMC2951287), Covassin (PMC9187217), Zuraikat 2026 (PMC13464323), Craven (PMC9584849), Mostafa (PMC13655966, métodos, resultados e tabelas), Life's Essential 8 (PMC10503546; busca por palavra). **Texto sem corpo disponível via PubMed**: Wang 2018 (PMC8591680), Watson 2015 (PMC4442216 e PMC4434546).

### 1.3 Limitações da busca

BVS e Cochrane Library **não consultadas** (inacessíveis na rede restrita). Não existe diretriz brasileira de duração do sono entre os registros recuperados (a ABS 2023 trata de insônia). O Guia de Atividade Física do MS e o site da ABS foram inacessíveis (403) na etapa 01. 363 registros elegíveis foram cortados por volume pelo buscador; recuperei apenas os de maior impacto (1.2).

## 2. Seleção (fluxo PRISMA)

Números finais de `03a-busca.json` (atualizado em 10/11/2026 10:32).

```
Identificados (PubMed + Consensus + dirigidos) ......................... 1.888
 - duplicatas removidas ................................................   274
Triados por título e resumo ............................................ 1.614
 - excluídos por título/resumo (população, desenho, desfecho, fora do tema) 1.156
 - cortados por volume (teto, hierarquia de desenho) ....................   363
Para avaliação (03a-candidatos.json: 77 "incluir" + 18 "talvez") ........    95
 - lidos no resumo completo do PubMed (ou no texto completo) ...........    91
 - não lidos além do resumo curto do 03a ...............................     4
 - excluídos depois da avaliação (3 lidos + 4 não lidos; 2.1) ..........     7
Incluídos da lista de 95 ...............................................    88
Registros adicionais fora dos 95 (1.2) .................................     6
INCLUÍDOS NA SÍNTESE ...................................................    94
```

Conferência aritmética: 1.888 − 274 = 1.614; 1.614 − 1.156 − 363 = 95; 95 − 7 = 88; 88 + 6 = 94 = entradas de `03-quadro-evidencias.json`.

Composição dos 94: 13 diretrizes e consensos; 43 revisões sistemáticas (com ou sem metanálise, incluindo 2 *umbrella reviews*); 31 ECR e experimentos (inclui 1 análise agrupada de 2 ECR); 1 estudo de validação em laboratório; 6 coortes.

### 2.1 Excluídos depois da avaliação (7 da lista de 95)

| PMID | Registro | Motivo | Lido? |
|---|---|---|---|
| 27417913 | Sleep quality and obesity in young subjects (MA, 2016) | População: crianças, adolescentes e jovens; fora do alvo | só resumo curto do 03a |
| 31097460 | Consenso NCAA, atletas universitários (2019) | Sem desfecho quantitativo; coberto por Walsh 2021 | só resumo curto do 03a |
| 34170250 | AASM, "Sleep is essential to health" (2021) | Posicionamento geral sem recomendação quantitativa | só resumo curto do 03a |
| 36518294 | RS de cochilo em esportistas (2022) | Coberta pela metanálise de Mesas 2023 | só resumo curto do 03a |
| 31739848 | ECR piloto de extensão com tecnologia (n = 16) | Desfecho pressão arterial; amostra mínima | sim |
| 35565955 | Programa combinado em pilotos de companhia aérea | Intervenção multicomponente sem separar o efeito do sono | sim |
| 39317920 | Horário de refeições e sono em sobreviventes de câncer de mama | População fora do alvo; comportamentos inalterados em 18 meses | sim |

Os 18 itens retirados pelo líder (parecer r1 da busca) não foram avaliados.

## 3. Diretrizes vigentes

Hoje é 10/11/2026. A recomendação de duração do sono para adultos é **convergente**: ≥ 7 h (AASM/SRS) e 7 a 9 h (NSF) por noite. Nenhuma diretriz exige peso, composição corporal ou ingestão como alvo do sono; nenhuma é específica para pessoas em emagrecimento.

| Diretriz | Versão/ano | O que recomenda | Força ou certeza | Observações |
|---|---|---|---|---|
| AASM/SRS [@watson2015] | 2015 (JCSM) | Adultos: pelo menos 7 h por noite, regularmente (valor obtido de resultado de busca; página da AASM não aberta) | Consenso RAND modificado; sem GRADE | Sem atualização no PubMed (1.2). Não define limite superior |
| NSF [@hirshkowitz2015] | 2015 (Sleep Health) | Adultos 7 a 9 h; idosos 7 a 8 h; faixas "recomendada", "pode ser apropriada", "não recomendada" | Consenso RAND/UCLA | **Reavaliada em 2026** [@dzierzewski2026]: 133 metanálises; 74% consistentes, 26% inconclusivas, nenhuma contraditória; recertifica as faixas. A reavaliação foi feita pela própria NSF |
| AHA, declaração científica [@stonge2016] | 2016 (Circulation) | Pede que diretrizes de saúde incluam recomendações de sono; sono curto liga-se a obesidade, hipertensão, DM2, doença cardiovascular | Declaração de sociedade; sem graduação no resumo | Parcialmente superada pelos dois itens seguintes |
| AHA, Life's Essential 8 [@lloydjones2022] | 2022 (Circulation) | Sono (duração) é a oitava métrica de saúde cardiovascular, pontuada de 0 a 100; o texto cita ≈ 7 a 8 h para adultos | Comunicado presidencial; reconhece escassez de evidência de que melhorar o sono reduza eventos | Tabela de pontos por faixa de horas não veio no texto extraído |
| AHA, sono multidimensional [@stonge2025] | 2025 (Circ Cardiovasc Qual Outcomes) | Sete dimensões do sono (duração, continuidade, horário, regularidade, funcionamento diurno, arquitetura, ausência de distúrbios); a duração segue sendo a única métrica do LE8 | Declaração científica; versão AHA mais recente do tema | Não substitui a recomendação de duração |
| NSF, regularidade [@sletten2023] | 2023 (Sleep Health) | Regularidade do horário importa para saúde, segurança e desempenho; recuperar o sono no fim de semana "pode ser benéfico" quando o sono da semana é insuficiente | Consenso por votação (63 publicações) | Em tensão com dois experimentos de laboratório (4.6) |
| Consenso de atletas [@walsh2021] | 2021 (BJSM) | Dormir < 7 h é comum em atletas de elite; **não** adotar regra única de 7 a 9 h, mas abordagem individual (necessidade percebida); "caixa de ferramentas" de educação e triagem; lacunas: cochilo e extensão | Consenso de especialistas; sem GRADE | Sem revisão posterior localizada (1.2) |
| AASM, TCC-I [@edinger2021] | 2021 (JCSM) | TCC-I multicomponente: forte; breve, controle de estímulos, restrição do sono, relaxamento: condicionais; **higiene do sono isolada: sugere-se não usar** (condicional) | GRADE próprio | Para insônia crônica, não para sono curto sem insônia |
| Diretriz europeia de insônia [@riemann2023] | 2023 (J Sleep Res) | TCC-I primeira linha (A); exercício e luz como adjuvantes (B); melatonina de liberação rápida **não recomendada** (A); liberação prolongada até 3 meses em ≥ 55 anos (B); actigrafia não rotineira (C) | A/B/C do próprio documento | Atualização da versão de 2017 |
| ABS, insônia [@drager2023] | 2023 (Sleep Science) | Diretriz nacional para diagnóstico e tratamento da insônia em adultos, com perguntas PICO e revisões sistemáticas | Resumo não traz graus | **Única diretriz brasileira**; não trata de duração do sono, peso ou treino |
| AASM e NSF, tecnologia de sono [@khosla2018; @dzierzewski2026cst] | 2018; 2026 | AASM: aparelhos de consumo não servem para diagnóstico ou tratamento por falta de validação; NSF: pede ações de público, profissionais e indústria, reconhece utilidade e limitações | Posicionamentos; sem GRADE | O texto da NSF tem autores ligados a empresas de eletrônicos |

**Convergência:** o piso de 7 h é comum a AASM/SRS, NSF e ao texto do LE8. **Divergências e porquês:** (a) o consenso de atletas rejeita a faixa única, porque a necessidade varia e há poucos dados em atletas; (b) o NSF e o AASM/SRS são consensos de especialistas, não revisões com GRADE, e a reavaliação de 2026 foi feita pela própria NSF; (c) as diretrizes de insônia (AASM, Europa, ABS) tratam doença, e o que dizem (por exemplo, sobre higiene do sono isolada e melatonina) não se transfere a quem dorme pouco por escolha; (d) a posição do **Ministério da Saúde/SUS** não pôde ser verificada (sem diretriz de duração do sono; o Guia de Atividade Física, 403 na etapa 01).

## 4. Revisões sistemáticas e metanálises

### 4.1 Sono curto, ingestão, peso e composição (pergunta central)

| Revisão | O que mostra | AMSTAR 2 (provisório) |
|---|---|---|
| Alkhatib 2017 [@alkhatib2017] | 11 estudos (n = 172): ingestão **+385 kcal** (IC 95% 252 a 517) após privação parcial; gasto sem mudança; mais gordura e menos proteína (resumo) | baixa |
| Fenton 2021 [@fenton2021] | 15 estudos: **+204 kcal/dia** (112 a 295) com sono ≤ 5,5 h; só 2 estudos de extensão | baixa |
| González-Ortiz 2020 [@gonzalezortiz2020] | 6 estudos: +149,86 kcal/dia (10,09 a 289,63) | baixa (sobrepõe-se às duas anteriores) |
| Soltanieh 2021 [@soltanieh2021] | 50 ECR (7 pediátricos): restrição eleva ingestão, gordura, peso e fome; gasto e QR sem efeito; leptina, grelina e cortisol "não influenciados"; sem estimativas | baixa |
| Capers 2015 [@capers2015] | 18 estudos; efeito da restrição sobre o peso **inconsistente**; poucos ensaios de extensão | baixa |
| **Yu 2019** [@yu2019] | 6 estudos (n = 275): peso DPM 0,44 (−0,13 a 1,02), sem diferença significativa | criticamente baixa a baixa |
| Lin 2020 [@lin2020] | Sono curto: grelina DPM 0,14 (0,03 a 0,25); nos experimentos a **leptina esteve mais alta**, não mais baixa (0,19; 0,03 a 0,35) | baixa |
| **Mostafa 2026** [@mostafa2026] | Ver abaixo | **moderada** (PROSPERO, duplicata, RoB, GRADE) |
| Duan 2026 [@duan2026] | 30 estudos (13 ECR) em programas de emagrecimento: restrição **reduziu a perda de gordura**; duração × perda de peso inconsistente nos observacionais; eficiência e satisfação com o sono podem ajudar | moderada |
| Malasevskaia 2026 [@malasevskaia2026] | Umbrella de 16 MA: sono curto OR 1,40 (1,27 a 1,55; I² 83,7%), sono longo 1,05 (1,02 a 1,08); "sugestivo"; polissonografia OR 2,70 (1,80 a 4,05) × autorrelato 1,14 (0,98 a 1,33) | moderada |
| Bacaro 2020; Itani 2017; Lange 2024; Jiang 2024 [@bacaro2020; @itani2017; @lange2024; @jiang2024] | Associação com obesidade: OR 1,41 (1,18 a 1,69); RR 1,38 (1,25 a 1,53); homens 1,26 e mulheres 1,36 (razão 1,04; 0,79 a 1,36); idosos 1,40 (1,12 a 1,73) | baixa a moderada |
| Yang 2024 [@yang2024] | Umbrella com randomização mendeliana: causalidade do sono curto sustentada para obesidade, hipertensão e DAC | moderada |

**Mostafa 2026, todos os desfechos** (27 estudos; 21 ECR, 5 pré-pós, 1 não randomizado; texto completo e resumo). IMC global: −0,26 kg/m² (−0,70 a 0,18; I² 59%; **não significativo**). TCC-I/higiene (8 estudos, n = 1.384): −0,64 kg/m² (0,28 a 1,01; I² 16%), mas quase todo o peso vem de ensaios em DM2 (3 estudos, n = 1.121). Extensão (5 estudos, n = 138): −0,15 kg/m² (−0,40 a 0,11). **Peso corporal: sem redução significativa** para todas as intervenções (P = 0,23), TCC-I/higiene (P = 0,56) e extensão (P = 0,46). O resultado de −5,55 kg (4,13 a 6,97; 3 estudos, n = 72) é **subgrupo por IMC basal**, igual ao de −0,83 kg (0,32 a 1,35; 6 estudos, n = 337) no sobrepeso. Ingestão: −147,5 kcal/dia (5,74 a 289,41; I² 53%; 5 estudos, n = 223). Gordura % e massa livre de gordura: sem mudança (2 estudos cada). Atividade física e tempo sedentário: sem mudança. Qualidade: 12 de 26 estudos sem preocupações; GRADE dos autores: IMC moderada, peso **baixa**, ingestão moderada. Seguimento: 2 semanas a 2,7 meses (extensão) e 3 a 12 meses (TCC-I/higiene).

### 4.2 Hábito alimentar, cronotipo e horário das refeições

- Teixeira 2022 [@teixeira2022]: em 43 estudos, ≈ 95% associaram vespertinidade a ao menos um hábito alimentar pouco saudável e ≈ 47% a maior peso/IMC (AMSTAR 2 provisório: baixa; observacional).
- Arab 2024 [@arab2024]: jet lag social × adiposidade (43 estudos, n = 231.648): IMC r = 0,12 (0,07 a 0,17; I² 95%), massa gorda r = 0,10 (0,05 a 0,15), cintura r = 0,15 (0,06 a 0,24), sobrepeso/obesidade OR 1,20 (limite superior com erro de digitação no resumo). Baixa; transversal.
- Jin 2026 [@jin2026]: alimentação com restrição de horário (13 estudos, n = 638). Em ensaios controlados, **sem efeito sobre duração do sono ou PSQI**; os ganhos aparecem só em braços únicos.
- Soltanieh 2021 e experimentos (5.1) mostram mais refeições e porções na restrição.

### 4.3 Treinamento

- Craven 2022 [@craven2022] (texto completo): 69 publicações, 227 desfechos, n = 959 (89% homens). Desempenho geral **−7,56%** (−11,9 a −3,13; I² 98,1%). **Força: −2,85%** (−4,47 a −1,23; I² 62,2%; 25 estudos, n = 289, 74% homens), significativa nos subgrupos só na **privação total** (−3,00%; −4,52 a −1,48) e em membros inferiores; tarefas pela manhã pouco afetadas. A queda de ≈ 0,4% por hora acordado refere-se a **privação e restrição tardia** (restrição: −0,36; restrição tardia: −0,55; privação −0,30, não significativa, P = 0,051, e significativa só após retirar um outlier); para a força, a relação com horas acordadas só foi significativa na restrição tardia (−1,07%/hora). Habilidade técnica: −20,9%. Estudos agudos; AMSTAR 2 provisório: baixa.
- Knowles 2018 [@knowles2018] e Easow 2025 [@easow2025]: efeito sobre a força depende do protocolo (restrição em noites consecutivas pode reduzir força em movimentos multiarticulares); qualidade "moderada/fraca"; Easow conclui de modo mais categórico que os dados descritos.
- Mesas 2023 [@mesas2023]: cochilo de 30 a < 60 min melhora desempenho físico (DPM 0,99; 0,67 a 1,31; I² 89,1%), cognição e fadiga; só homens (n = 291).
- Bonnar 2018 [@bonnar2018]: em atletas, extensão do sono teve os melhores efeitos entre as intervenções (10 estudos, n = 218).
- Exercício → sono: Kredlow 2015 [@kredlow2015] (66 estudos; exercício regular melhora qualidade do sono, efeito moderado; busca até 2013); Frimpong 2021 [@frimpong2021] (15 estudos, n = 194; HIIE terminando 0,5 a 4 h antes de dormir reduziu só o REM, −2,34%; sem outras mudanças em bons dormidores); Riedel 2024 [@riedel2024] (insônia: sono objetivo DPM 0,37; 0,17 a 0,57; subjetivo 0,90; 0,61 a 1,19); Faria 2025 [@faria2025] (12 estudos; o exercício mitiga os efeitos da perda de sono sobre glicose e insulina em curto prazo).

### 4.4 Rotina: cafeína, álcool, telas

- Cafeína [@gardiner2023]: tempo total de sono −45 min, eficiência −7%, latência +9 min, vigília +12 min; **café (107 mg/250 mL) ≥ 8,8 h antes de deitar e pré-treino (217,5 mg) ≥ 13,2 h** para evitar perda de sono (intervalos derivados de modelo).
- Álcool [@gardiner2025]: dose baixa (≤ 0,50 g/kg, ≈ 2 doses) já reduz e atrasa o REM; efeitos sobre tempo total e eficiência incertos.
- Telas [@he2025]: cada hora/dia de tela se associou a 3 a 5 min a menos de sono (β −0,05; −0,08 a −0,03), sono curto OR 1,25 (1,08 a 1,40) e atraso de 13,2 min no horário de dormir; coortes com tela autorrelatada.

### 4.5 Intervenções práticas

- Baron 2021 [@baron2021]: intervenções comportamentais de extensão (42 estudos): DPM 0,80 (0,28 a 1,31; I² 99,2%) em dois braços; definir o horário de dormir teve efeito maior que coaching; mais componentes, menos efeito.
- Zhu 2022 [@zhu2022]: extensão em vida livre: +51 min (39 a 63); PA 24 h em pré-hipertensos: PAS −7,8 mmHg (−10,6 a −4,9); glicose e resistência à insulina: sem efeito. Henst 2019 [@henst2019] (7 estudos): efeitos metabólicos favoráveis, estudos pequenos.
- Murawski 2018 [@murawski2018]: intervenções cognitivo-comportamentais em adultos sem distúrbio: qualidade do sono g = −0,54 (−0,90 a −0,19).
- Allman-Farinelli 2020 [@allmanfarinelli2020]: programas eletrônicos que incluem sono para prevenir ganho de peso (6 ensaios): sem conclusão definitiva.

### 4.6 Mitos e controvérsias

- **Melatonina e peso** [@delpino2021]: DPM −0,48 (−0,94 a −0,02; I² 92%; 23 estudos); IMC e cintura sem efeito. **Melatonina e desempenho**: neutra em revisão qualitativa de 10 estudos [@faria2024]; efeitos pequenos a moderados em outra, de 19 ECR e 266 participantes [@guo2026] (potência DPM 0,29; 0,05 a 0,53; resistência 0,58; 0,29 a 0,87). As duas divergem e a segunda tem amostras mínimas.
- **Suplementos** [@chan2021; @mei2025; @lopresti2026]: melhora de qualidade do sono subjetiva com aminoácidos (DM −1,27; −2,35 a −0,20), melatonina (−1,21; −2,17 a −0,24; I² 79%) e vitamina D (−1,63; −3,15 a −0,10; I² 85%); magnésio: certeza baixa a muito baixa, sem suporte para uso de rotina. Nenhum tem desfecho de peso ou treino.
- **Rastreadores de sono**: Lee 2025 [@lee2025] (24 estudos): diferenças significativas versus PSG (tempo total −16,9 min; eficiência −4,7%; vigília após início +13,3 min); Agostinho 2026 [@agostinho2026] (QUADAS-2): **superestimam** tempo total e eficiência e subestimam vigília, com grande variabilidade entre aparelhos; Chinoy 2021 [@chinoy2021]: sensibilidade ≥ 0,93, especificidade 0,18 a 0,54, estágios inconsistentes. O sentido da diferença em Lee 2025 não é explicitado no resumo e **diverge** do de Agostinho. AASM não aceita uso diagnóstico [@khosla2018].
- **Recuperar no fim de semana**: ver 5.4 (consenso favorável da NSF [@sletten2023] versus experimentos de laboratório).

## 5. Ensaios clínicos e outros estudos relevantes

Avaliação de risco de viés pela lógica do RoB 2, aplicada em geral a **resumos**; participantes de intervenções de sono não podem ser cegados, o que pesa nos desfechos autorrelatados e menos nos objetivos (DXA, água duplamente marcada, ressonância).

### 5.1 Sono × dieta hipocalórica: composição do peso perdido (pergunta central)

| Estudo | Desenho e n | Resultado (todos os desfechos) | Risco de viés |
|---|---|---|---|
| **Nedeltcheva 2010** [@nedeltcheva2010] (texto completo) | Cruzado, n = 10 (3 mulheres), sobrepeso; dieta de 90% da TMR por 14 dias com 5,5 h × 8,5 h na cama | **Peso perdido semelhante (≈ 3 kg)**; gordura perdida 0,6 × 1,4 kg (P = 0,043; −55%); **massa livre de gordura perdida 2,4 × 1,5 kg (P = 0,002; +60%)**; fome maior; QR e grelina acilada maiores; gasto de repouso menor; leptina sem efeito independente; gasto total (água duplamente marcada) sem diferença detectável por variância alta | algumas preocupações (n = 10, sem cegamento, 2 retiradas); ICs não informados |
| **Wang 2018** [@wang2018] (resumo; texto completo indisponível) | Paralelo, n = 36 (15 dieta; 21 dieta + restrição de ≈ 1 h em 5 noites/semana, 8 semanas) | **Perda semelhante de peso, massa magra e massa gorda**; proporção do peso perdido como gordura maior na dieta isolada (P = 0,016); QR em repouso reduzido só na dieta; leptina reduzida só com restrição | algumas preocupações (sem cegamento; valores absolutos e ICs não obtidos) |
| Duan 2026 (síntese) [@duan2026] | 13 ECR + 17 quase-experimentais | restrição reduziu perda de gordura; duração observacional inconsistente | moderada (revisão) |

### 5.2 Restrição do sono com acesso livre ao alimento: ingestão, gasto, peso e gordura

| Estudo | Desenho e n | Resultado | Risco de viés |
|---|---|---|---|
| **Covassin 2022** [@covassin2022] (texto completo) | Cruzado internado, n = 12 (9 homens), 14 dias de 4 h × 9 h | Ingestão **+308,1 kcal/dia** (59,2 a 556,8); proteína +10,9 g (0,0 a 21,7); gordura +13,5 g (0,3 a 26,8); gasto sem mudança; **peso +0,5 kg** (0,1 a 0,8); gordura corporal total e massa magra sem diferença (DXA; P total = 0,710); gordura abdominal (tomografia) +15,2 cm² (3,6 a 26,8), subcutânea +7,4 (0,1 a 14,6), **visceral +7,8 cm²** (0,3 a 15,3); leptina, grelina total, cortisol sem diferença | algumas preocupações |
| **Markwald 2013** [@markwald2013] | Internado, n = 16, 5 noites de ≈ 5 h | Gasto total +≈ 5%; ingestão acima da necessidade, **sobretudo após o jantar**; peso **+0,82 ± 0,47 kg**; recuperação: ingestão menor e −0,03 ± 0,50 kg | limitado ao resumo |
| **Spaeth 2013** [@spaeth2013] | Medidas repetidas, n = 225 (198 restrição; 27 controle); ingestão em 31 e 6 | Peso **+0,97 ± 1,4 kg × +0,11 ± 1,9 kg** (d = 0,51; P = 0,007), mais em homens e em negros; **+552,9 ± 265,8 kcal entre 22:00 e 03:59**; gordura 33,0% da energia à noite × 28,2% de dia | alto risco para ingestão (6 controles); algumas preocupações para peso |
| **Zuraikat 2026** [@zuraikat2026] (texto completo) | Análise agrupada de 2 cruzados (não pré-especificada), n = 95, 6 semanas de −78,4 min/noite | **Peso +0,45 kg** (0,33 a 0,57); cintura +0,52 cm (0,25 a 0,79); volume corporal +0,56 L (0,19 a 0,93); **sem efeito na % de tecido adiposo ou muscular** (ressonância); leptina +2,03 ng/mL (0,38 a 3,68); grelina tendência de queda (NS); GLP-1 NS; **sedentarismo +17,2 min/dia** (11,7 a 22,7); atividade moderada-vigorosa NS; gasto total (n = 34) NS; ingestão não medida | algumas preocupações |
| Brondel 2010 [@brondel2010] | Cruzado, n = 12 homens, 1 noite | +559 ± 617 kcal no dia seguinte (P < 0,01) | algumas preocupações |
| Radcliffe 2021 [@radcliffe2021] | Cruzado, n = 18 homens, 3 noites de 2 h | Restrição **severa reduziu** a fome (−23%) e o almoço em **332 kcal** (−479 a −185) | algumas preocupações |
| Tajiri 2023 [@tajiri2023] | Cruzado, n = 24, 3 noites de 5 h | Mais fome e lanches; **ingestão total do dia sem diferença** | algumas preocupações |
| Yang 2019 [@yang2019]; Greer 2013 [@greer2013] | 1 noite; ressonância funcional | Mais fome, desejo e porções; menos atividade em córtex frontal/insular e mais na amígdala | desfechos substitutos |
| Spiegel 2004 [@spiegel2004] | Cruzado, n = 12 homens, 2 dias | Leptina −18%, grelina +28%, fome +24% | n pequeno |
| Cros 2019 [@cros2019] | Cruzado, n = 10, sobrealimentação por 6 dias | Restrição do sono **não potencializou** gordura hepática nem glicose | n pequeno |
| Barragán 2023 [@barragan2023]; Zuraikat 2024 [@zuraikat2024] | Cruzados, 6 semanas | Mais refeições na restrição (β = 0,3 ± 0,1); HOMA-IR +0,30 ± 0,12 em mulheres | registro alimentar autorrelatado; laboratorial |

### 5.3 Extensão do sono em quem dorme pouco

| Estudo | Desenho e n | Resultado | Risco de viés |
|---|---|---|---|
| **Tasali 2022** [@tasali2022] (texto completo) | Paralelo, n = 80, IMC 25 a 29,9, sono < 6,5 h; 2 semanas | Sono +1,2 h (1,0 a 1,4); **ingestão −270 kcal/dia** (−393 a −147); gasto total −53,9 (−134,9 a 27,1; NS); balanço −211 kcal/dia (−335 a −87); **peso −0,87 kg** (−1,39 a −0,35); **massa livre de gordura −0,62 kg** (−1,02 a −0,23); **massa gorda −0,25 kg** (−0,39 a −0,10); o grupo controle **ganhou 0,39 kg** (0,02 a 0,76) | baixo risco a algumas preocupações |
| Hartescu 2022 [@hartescu2022] | Paralelo, n = 18 homens, 6 semanas | Sono +79 min; HOMA-IR −0,51 (−0,98 a −0,03); PA menor; peso não relatado | alto risco (piloto) |
| Beals 2026 [@beals2026] | Paralelo, n = 29, ≈ 6 semanas, clamp | Sono +1,1 h; **sem efeito na sensibilidade à insulina** | algumas preocupações |
| Merchant 2025 [@merchant2025] | Paralelo, n = 27, TCC-I 8 semanas | Sono autorrelatado +49,2 min, **acelerometria sem diferença**; menos desejo por doce; ingestão sem diferença (19/27 subnotificaram) | alto risco (ingestão) |
| Alkhatib 2018 [@alkhatib2018] | Piloto, n = 42 | Sono +21 min; açúcar livre −9,6 g (−16,0 a −3,1) | algumas preocupações |
| Erim 2024 [@erim2024] | Paralelo, n = 38 vespertinos com obesidade | Antropometria e qualidade do sono melhores; números não constam do resumo | alto risco |

### 5.4 Recuperação do sono no fim de semana

- Depner 2019 [@depner2019] (n = 36): recuperação *ad libitum* (+1,1 h) reduziu a ingestão após o jantar, mas na restrição recorrente seguinte a ingestão, o peso e a perda de sensibilidade à insulina (−9% a −27%) voltaram.
- Depner 2021 [@depner2021] (mesma série): balanço energético sem diferença entre os grupos (todos +797,7 ± 96,7 kcal/dia).
- Killick 2015 [@killick2015] (n = 19 homens com restrição crônica): 3 noites de 10 h melhoraram a sensibilidade à insulina versus 6 h.
- Covassin 2022 [@covassin2022]: 3 dias de recuperação normalizaram ingestão e peso, mas a gordura visceral continuou a subir.

### 5.5 Treino: síntese proteica, força e recuperação

- Lamon 2021 [@lamon2021]: 1 noite de privação total: **síntese proteica miofibrilar −18%** (0,072 ± 0,015 para 0,059 ± 0,014 %/h; P = 0,040); cortisol +21%, testosterona −24% (n = 13).
- Saner 2020 [@saner2020]: 5 noites de 4 h: síntese miofibrilar 1,24 ± 0,21 versus 1,53 ± 0,09 %/dia (controle) e 1,61 ± 0,14 com **HIIE** (n = 24 homens).
- Knowles 2022 [@knowles2022]: 9 noites de 5 h, mulheres treinadas (n = 10): carga de volume cai < 1%; **velocidade da barra até 15% menor nos exercícios de membros inferiores**; cortisol salivar +42%; esforço percebido +11%.
- Estudos de massa muscular: **nenhum ECR** de hipertrofia ou composição com restrição crônica do sono foi encontrado nos 95 itens.

### 5.6 Horário de exercício, refeições e TRE

- Saidi 2020 [@saidi2020] (n = 16): corrida moderada à noite não perturbou o sono; melhor vigília quando terminou 4 h antes de deitar; ingestão seguinte sem diferença.
- Shen 2025 [@shen2025] (n = 58 homens sedentários): exercício matinal reduziu gordura corporal mais cedo e adiantou a fase do sono; noturno melhorou mais a função vascular; registro tardio possível.
- Steger 2023 [@steger2023]: TRE precoce em aderentes (n = 90 randomizados): peso −3,7 ± 1,2 kg, mas relataram dormir menos e demorar mais para adormecer. Clavero 2025 [@clavero2025] (n = 197, 3 horários de TRE): **sem diferença** em sono, humor ou qualidade de vida (tempo total de sono 0,2 h; −0,2 a 0,6).

### 5.7 Coortes em programas de emagrecimento (complementares)

| Estudo | n e desenho | Resultado | Viés (ROBINS-I) |
|---|---|---|---|
| Kline 2026 [@kline2026] | 296; 12 meses | Sono curto (< 6 h) perdeu **4,5 ± 1,3%** menos; sono ruim 2,2 ± 1,2% menos; ambos ≥ 5,0% menos; menos 2,0 sessões; menor ganho de atividade | moderado |
| Creasy 2022 [@creasy2022] | 156; 18 meses | Menor eficiência, mais despertares e latência maior → perda atenuada (ajustado); mais duração e tempo na cama → menor chance de atingir ≥ 300 min/semana de atividade | moderado |
| Rodríguez-Martín 2025 [@rodriguezmartin2025] | 3.628; 25 semanas | **Sono longo (> 8 h)** perdeu 7,42% × 7,90% (P = 0,015); OR 0,79 para perda ≥ 5%; abandono OR 1,21 (1,03 a 1,43); **sono curto sem associação** | moderado a sério |
| Papandreou 2020 [@papandreou2020] | 1.986; 12 meses | Maior variabilidade do sono: peso +0,5 kg (0,1 a 0,9); sono < 6 h: cintura −0,8 cm (−1,5 a −0,01) (sinal não esclarecido no resumo; o título indica menor redução) | moderado |
| Bogh 2023 [@bogh2023] | 195; manutenção por 1 ano | Após −13,1 kg, sono curto: reganho de 5,3 kg e menor queda de gordura; má qualidade: 3,5 kg (resumo não deixa claro se é valor absoluto ou diferença) | moderado |
| Thomson 2012 [@thomson2012] | 245 mulheres; 24 meses | Melhor qualidade e > 7 h aumentam o sucesso (RR 0,67; 0,52 a 0,86 conforme o resumo) | moderado |

## 6. Síntese por desfecho com certeza GRADE

Ponto de partida: ECR = alta; observacional = baixa. Rebaixamento por risco de viés, inconsistência, evidência indireta, imprecisão e viés de publicação. Quando o desfecho é autorrelatado, sem cegamento, ou o IC é amplo, aplico o rebaixamento (lição do pipeline).

| Desfecho | Evidência (n) | Efeito principal | Certeza | Motivos |
|---|---|---|---|---|
| **Proporção de gordura × massa livre de gordura perdida em dieta, com restrição do sono** | 2 ECR (n = 46) [@nedeltcheva2010; @wang2018] | Nedeltcheva (n = 10): menos gordura perdida (0,6 × 1,4 kg) e mais massa livre de gordura perdida (2,4 × 1,5 kg) com 5,5 h. Wang (n = 36): perdas de peso, massa magra e massa gorda semelhantes; só a proporção do peso perdido como gordura foi menor com restrição do sono | **Baixa** | −1 risco de viés (sem cegamento, n pequeno, curto prazo); −1 imprecisão (n = 46, ICs não informados). Direção concorde, magnitude incerta |
| **Peso total perdido em dieta** | os mesmos 2 ECR | Semelhante entre braços | **Baixa** | Mesmos motivos; ausência de diferença com n pequeno |
| **Ingestão energética com restrição do sono (acesso livre)** | 3 MA (11, 15 e 6 estudos) e ECR [@alkhatib2017; @fenton2021; @covassin2022] | +150 a +385 kcal/dia (MA); +308 (59 a 557) em 14 dias | **Moderada** (direção do aumento); baixa (magnitude em vida real) | −1 evidência indireta (laboratório, jovens saudáveis, 1 a 14 dias, às vezes refeição única). Inconsistência não rebaixada: as 3 MA concordam; o ECR oposto (Radcliffe, restrição severa de refeição única) é explicável pela dose |
| **Peso corporal com restrição (sem dieta)** | 1 MA + 4 estudos [@yu2019; @spaeth2013; @markwald2013; @covassin2022; @zuraikat2026] | +0,45 a +0,97 kg em 5 dias a 6 semanas; MA com 6 estudos sem diferença | **Baixa** | −1 inconsistência (MA nula versus estudos positivos; estudo de 3 semanas sem diferença citado por Zuraikat); −1 indireta (curto prazo, saudáveis). Efeito pequeno (≈ 0,5 kg) |
| **Gordura corporal com restrição** | Covassin; Zuraikat 2026 | Total: sem diferença nos dois; abdominal +15,2 cm² e visceral +7,8 cm² (0,3 a 15,3) em n = 12 | **Baixa** (sem aumento detectável de gordura total); **muito baixa** (visceral) | Visceral: 1 estudo, n = 12, IC quase nulo, análise exploratória; ressonância sem efeito diferencial em n = 95 |
| **Ingestão com extensão do sono em quem dorme pouco** | 1 ECR (n = 80) e MA (5 estudos, n = 223) [@tasali2022; @mostafa2026] | −270 kcal/dia (−393 a −147); MA −147,5 (5,7 a 289,4; I² 53%) | **Baixa** | −1 imprecisão (MA com limite inferior de IC perto de zero e I² 53%) e −1 evidência indireta (2 semanas, sem dieta, adultos jovens com sobrepeso sem insônia): dois rebaixamentos a partir de ECR. Diverge da GRADE dos autores da MA (moderada), que não rebaixaram por indireção; o ECR principal (Tasali) tem IC que exclui efeito trivial e ingestão medida por água duplamente marcada, mas é um único ensaio de 2 semanas |
| **Peso e composição com extensão** | Tasali; MA [@tasali2022; @mostafa2026] | −0,87 kg (−1,39 a −0,35) em 2 semanas, sobretudo massa livre de gordura (−0,62 kg); MA: peso NS (extensão P = 0,46; global P = 0,23); IMC extensão −0,15 (−0,40 a 0,11) | **Baixa** | −1 inconsistência (ECR positivo × MA nula); −1 imprecisão/curta duração; ganho no grupo controle contribui. GRADE dos autores para peso: baixa |
| **TCC-I/higiene do sono → IMC e peso** | 8 estudos, n = 1.384; subgrupo obesidade 3 estudos, n = 72 [@mostafa2026] | IMC −0,64 (0,28 a 1,01); peso NS; −5,55 kg só no subgrupo de obesidade | **Baixa** (IMC); **muito baixa** (subgrupo de obesidade) | IMC dominado por ensaios em DM2; subgrupo exploratório de 3 estudos pequenos; sono ruim/insônia no basal |
| **Sono curto/ruim e perda de peso em programas** | 6 coortes + RS [@kline2026; @creasy2022; @rodriguezmartin2025; @papandreou2020; @bogh2023; @thomson2012; @duan2026] | Perda menor com sono curto/ineficiente em 5 de 6; sem associação com sono curto em n = 3.628 | **Muito baixa** | Observacional; −1 inconsistência (Rodríguez-Martín; Duan: metade dos estudos positivos); autorrelato e confundimento |
| **Horário das refeições/ingestão noturna com sono curto** | 3 experimentos [@spaeth2013; @markwald2013; @depner2019] e Barragán | Mais calorias à noite (+553 kcal entre 22:00 e 03:59, n = 31) | **Baixa** | Laboratório; subconjunto; registro autorrelatado em Barragán |
| **Cronotipo vespertino e jet lag social × adiposidade/dieta** | 2 RS observacionais [@teixeira2022; @arab2024] | r = 0,12 (IMC); ≈ 95% dos estudos com hábito pior | **Baixa** (associação); **muito baixa** (efeito de corrigir o horário) | Transversais, I² 95%, causalidade desconhecida |
| **Desempenho de força com perda aguda de sono** | MA de 25 estudos (n = 289) [@craven2022] | −2,85% (−4,47 a −1,23); privação −3,00%; manhã pouco afetada | **Baixa** | −1 indireta (agudo, 74% homens, tarefas variadas); −1 inconsistência (I² 62,2%); sem mulheres/idosos |
| **Síntese proteica muscular** | 2 estudos (n = 13 e 24) [@lamon2021; @saner2020] | −18% (privação 1 noite); 1,24 × 1,53 %/dia (4 h × 5 noites); HIIE preserva | **Muito baixa** | Desfecho substituto; n pequeno; privação total no primeiro; sem desfecho de massa muscular |
| **Exercício → sono** | MA [@kredlow2015; @frimpong2021] | Exercício regular melhora a qualidade (efeito moderado); HIIE noturna reduz só o REM (−2,34%) | **Baixa** | População de bons dormidores; busca antiga (2013); estimativas numéricas ausentes no resumo da primeira |
| **Cafeína e sono** | MA de 24 estudos [@gardiner2023] | −45 min de sono; ≥ 8,8 h antes de deitar (café) | **Moderada** | Estudos laboratoriais objetivos e coerentes; −1 indireta (doses variadas; intervalos de modelo) |
| **Álcool e sono** | MA de 27 estudos [@gardiner2025] | REM reduzido a partir de ≈ 2 doses | **Moderada** (REM); **muito baixa** (tempo total, eficiência) | Incerteza grande nos outros desfechos |
| **Telas e sono** | MA de 21 coortes [@he2025] | 3 a 5 min a menos por hora de tela | **Baixa** | Observacional; tela autorrelatada; subgrupo por idade sem modificação, contrariando o texto do resumo |
| **Recuperação no fim de semana** | 3 ensaios pequenos [@depner2019; @depner2021; @killick2015] + consenso | Não preveniu a piora metabólica (Depner 2019); sem diferença de balanço (2021); melhora de sensibilidade em 3 noites (Killick) | **Baixa** | n de 8 a 36; laboratório; resultados discordantes; consenso NSF favorável |
| **Melatonina para peso/desempenho** | 2 MA + 1 RS [@delpino2021; @faria2024; @guo2026] | Peso DPM −0,48 (−0,94 a −0,02; I² 92%); desempenho neutro ou pequeno | **Muito baixa** | Heterogeneidade extrema; IC encostado em zero; amostras mínimas; achados divergentes |
| **Suplementos para qualidade do sono** | 3 revisões [@chan2021; @mei2025; @lopresti2026] | Aminoácidos/vitamina D/melatonina melhoram índice subjetivo; magnésio inconsistente | **Muito baixa** | Autorrelato, I² 79 a 85%, populações mistas; nenhum desfecho de peso |
| **Acurácia de rastreadores de sono** | 3 estudos [@lee2025; @agostinho2026; @chinoy2021] | Diferem da PSG em tempo total, eficiência e vigília; estágios imprecisos | **Moderada** (não substituem PSG); **baixa** (magnitude e sentido do viés) | Direção do erro difere entre MA |

## 7. Resposta à pergunta e lacunas

**Resposta.** Em experimentos de laboratório com adultos majoritariamente saudáveis, **dormir pouco aumenta a ingestão** (≈ 150 a 385 kcal/dia; certeza moderada quanto à direção do efeito, evidência indireta para quem tem sobrepeso). **Durante a dieta, dormir pouco mudou a composição do que se perde**: em um ECR cruzado (n = 10), a perda total foi semelhante, mas com menos gordura e mais massa livre de gordura perdida; em outro ECR (n = 36), peso, massa magra e massa gorda perdidos foram semelhantes, com menor proporção de gordura no peso perdido (certeza **baixa**). Estender o sono de quem dorme pouco reduziu a ingestão em 270 kcal/dia em um ECR de 2 semanas (certeza **baixa**: imprecisão da metanálise e evidência indireta) e o peso em 0,87 kg, em sua maior parte massa livre de gordura (certeza baixa); a metanálise geral de intervenções de sono **não** mostrou redução significativa de peso (P = 0,23). Em programas de emagrecimento, sono ruim ou curto associou-se a menor perda e adesão em 5 de 6 coortes (certeza muito baixa), com um grande estudo sem associação para o sono curto. O trabalho não permite afirmar que corrigir o sono emagrece, nem quanto, nem por quanto tempo.

**Por item do briefing (impacto do sono):**
- **Hábito alimentar (item 2):** aumento de ingestão e de lanches noturnos com restrição (moderada/baixa); hormônios do apetite têm papel pouco consistente (grelina maior, leptina mais alta ou nula) e a restrição severa pode reduzir o apetite; cronotipo vespertino associa-se a pior dieta, sem causalidade demonstrada.
- **Peso e composição (item 3):** ver resposta acima; ganho de ≈ 0,5 a 1 kg em 5 dias a 6 semanas com restrição; gordura visceral sob suspeita em um estudo (muito baixa).
- **Treinamento (item 4):** a perda aguda de sono reduz desempenho (força −2,85%; maior com privação e à tarde); a síntese proteica cai em estudos pequenos; **não há ECR de massa muscular** com restrição crônica; exercício regular melhora o sono e o exercício noturno intenso, em bons dormidores, pouco o altera (REM −2,34%).
- **Rotina (item 5):** cafeína (≥ 8,8 h antes de deitar), álcool (REM) e telas (3 a 5 min por hora) têm efeito mensurável sobre o sono; a ligação com o peso é indireta.
- **Prática (item 6):** é possível estender o sono em ≈ 40 a 80 min com intervenções comportamentais (heterogeneidade extrema); a higiene do sono isolada não é recomendada para insônia crônica, e a TCC-I tem recomendação forte na insônia; o efeito em peso fora de insônia é pequeno e incerto.
- **Mitos (item 7):** recuperar no fim de semana não preveniu a piora metabólica em laboratório; melatonina e suplementos não têm evidência de efeito em peso ou treino; rastreadores não substituem a polissonografia.

**Lacunas.** (1) ECR de perda de peso com sono manipulado: só 2, com n = 46, e sem ICs acessíveis; nenhum com sono estendido em dieta. (2) Sem ensaios de composição corporal com restrição crônica em treino resistido. (3) Seguimento máximo de 6 semanas (restrição) e 2 meses (extensão); sem dados de sustentabilidade. (4) Populações: jovens, saudáveis, maioria homens nos estudos de treino e de laboratório; poucos brasileiros; nenhuma diretriz do MS sobre duração. (5) Ingestão frequentemente inferida (não medida), autorrelatada ou de refeição única. (6) Hormônios do apetite (grelina, leptina) são desfechos substitutos e inconsistentes. (7) BVS e Cochrane não consultadas; OMA 2026 não verificável. (8) A maioria das avaliações de revisões é provisória, só por resumo.

## Pendências para o líder

1. **Meta de 8 a 20 fontes excedida (94 incluídas).** O escopo (7 subtemas) e o conjunto de 95 itens do parecer r1 produzem 94 fontes incluídas; sugiro um **núcleo de ≈ 25** para o artigo: Nedeltcheva, Wang, Tasali, Covassin, Zuraikat 2026, Spaeth, Markwald, Alkhatib 2017, Fenton, Mostafa, Duan, Kline, Creasy, Rodríguez-Martín, Craven, Knowles 2018, Lamon, Saner, Depner 2019, Gardiner 2023, Delpino, Agostinho, Edinger, Riemann, Hirshkowitz + Dzierzewski 2026, Watson e Walsh.
2. **Erro a evitar na etapa 02 (e no artigo):** o −5,55 kg de Mostafa é **subgrupo por IMC basal** (3 estudos, n = 72); o peso global **não** foi significativo (P = 0,23) e a GRADE dos autores para peso é **baixa**. Conferir se `02-analise-critica.md` cita o número sem essa ressalva.
3. **Radcliffe 2021** (restrição severa de 2 h reduziu a ingestão em 332 kcal) e **Lin 2020** (leptina mais alta, não mais baixa, nos experimentos) contrariam a narrativa "pouco sono → leptina baixa e fome alta". Conferir o §1.1 da análise.
4. **Wang 2018:** texto completo vazio no PubMed; valores absolutos e ICs não extraídos. Idem a página da AASM e do OMA (hosts fora da rede): para o valor ≥ 7 h de Watson 2015 usei resultado de busca; a página da AASM precisa ser liberada para verificação direta.
5. **Life's Essential 8:** a tabela de pontuação do sono não veio no texto extraído; não citar o corte "7 a < 9 h = 100 pontos" sem conferi-lo.
6. **Atualizações de diretrizes:** NSF 2015 foi reavaliada em 2026 (mesma entidade, mantém as faixas); AHA 2016 foi seguida pelo LE8 (2022) e pela declaração de 2025. Walsh 2021 e Watson 2015: sem atualização localizada (Walsh: 9 de 13 registros não lidos).
7. **Registros fora dos 95** (6): Knowles 2022, St-Onge 2025, Dzierzewski 2026, Chan 2021, Mei 2025, Lopresti 2026; quatro vieram da lista de cortes por volume. Se o líder preferir, retire-os dos números (88 em vez de 94).
8. **Itens possivelmente incoerentes nos resumos** (sinalizados no quadro): unidade mista em Yu 2019; erro de digitação no OR de Arab 2024; sinal da cintura em Papandreou 2020; valor absoluto × diferença em Bogh 2023; direção do RR em Thomson 2012; sentido da diferença em Lee 2025; Frontiers (He 2025) afirma maior vulnerabilidade de adolescentes sem efeito de modificação por idade.
9. **Ano do fascículo:** Hartescu (id `hartescu2022`, eletrônico em 2021), Arab 2024, Gardiner 2025, Steger 2023, Murawski 2018 e Itani 2017 confirmados por `[ppdat]`; verificador pode reconferir.
10. **Não lidos:** 27417913, 31097460, 34170250 e 36518294 (excluídos pelo resumo curto do 03a) e 9 dos 13 registros da busca por Walsh/Halson.
11. **Suplementos, melatonina e rastreadores** têm evidência de revisão geral, não por desfecho de peso ou treino; o artigo deve tratá-los como mitos, não como tratamentos.
12. **Rodada 2 (correção do parecer r1):** a certeza da ingestão com extensão do sono caiu de moderada para **baixa** (dois rebaixamentos escritos: imprecisão e evidência indireta). Redator e designer devem trocar 'moderada' por 'baixa' para esse desfecho. A frase 'mais massa magra perdida' vale só para Nedeltcheva 2010 (n = 10); em Wang 2018 só a proporção de gordura no peso perdido foi menor. O aumento de ingestão de +150 a +385 kcal/dia vem de adultos majoritariamente saudáveis em laboratório (indireto para quem tem sobrepeso).
