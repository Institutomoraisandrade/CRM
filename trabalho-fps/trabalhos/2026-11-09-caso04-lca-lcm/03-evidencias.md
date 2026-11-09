# Melhor evidência disponível — Reabilitação conservadora do LCA insuficiente associada a estiramento do LCM em atleta jovem de esporte com pivô (Caso Clínico 04)

> Etapa 03 (fps-3-avaliador-evidencias). Data da avaliação: 09/11/2026. Foco do caso: **tratamento conservador** (decisão do grupo), curso de Educação Física, pós-operatório só como nota breve. Todos os números abaixo vêm de resumos acessados por `get_article_metadata` do PubMed **nesta execução**, salvo onde marcado "texto completo" ou "etapa 01/02". Rótulos de certeza: **direta** (população e intervenção do caso), **indireta** (pós-reconstrução, adultos saudáveis, outra lesão) e **consenso/opinião**. As afirmações de mecanismo estão na etapa 02 e não são repetidas aqui.

## Pergunta PICOS

**P** atleta jovem de esporte com pivô (futebol society), com LCA insuficiente e estiramento do LCM, tratado sem cirurgia · **I** reabilitação/treinamento progressivo por critérios (força, controle neuromuscular e do valgo dinâmico, pliometria, agilidade, retorno graduado) · **C** reabilitação por tempo, cuidado usual ou reconstrução precoce · **O** primários clínicos: falseio, função (KOOS/IKDC), retorno ao esporte, nova lesão; substitutos sinalizados: LSI de quadríceps e de saltos, derrame, dor, valgo dinâmico · **S** diretrizes, RS/MA, ECR; coortes quando não há ECR (@frobell2010 e o ensaio KANON são o único ECR de reabilitação isolada em jovens ativos).

## 1. Estratégia de busca (do 03a-busca.json + buscas complementares)

**Buscas do buscador (03a, aprovadas na r2; resumo).** PubMed, 09/11/2026, filtro pdat 2010–2026, 8 strings (principal sem filtro de desenho, variante de desenho, ensaios, diretrizes com e sem filtro de tipo, dose em conservador, dose em revisões, LCM) mais busca dirigida da diretriz JOSPT; Consensus (`medical_mode`, RS/MA, 50 registros); busca web de diretrizes nacionais e internacionais. Strings completas em `03a-busca.json`. Fluxo: 486 identificados, 108 duplicatas, 378 triados, 80 encaminhados para avaliação.

**Buscas complementares desta etapa (09/11/2026).** Registradas porque a lacuna era evidente: dor/derrame para ajuste de carga, BFR/carga alta, prevenção no futebol e versão da diretriz JOSPT.

| # | Base | String / consulta | Resultados | Uso |
|---|---|---|---|---|
| C1 | PubMed | `(anterior cruciate ligament[tiab]) AND (pain monitoring model[tiab] OR "pain-monitoring"[tiab] OR "pain response"[tiab] OR "knee soreness"[tiab] OR effusion[tiab]) AND (load[tiab] OR rehabilitation[tiab]) AND (systematic review[pt] OR randomized controlled trial[pt] OR guideline[pt])`, pdat ≥ 2010, relevância | 29 no total; 20 PMIDs retornados (a ferramenta devolve só PMIDs); 1 já estava nos 80 (34903114, lido, sem conteúdo extraível). **Os outros 19 não foram triados individualmente** | limitação |
| C2 | PubMed | `"pain monitoring model"[tiab] OR "pain-monitoring model"[tiab]` | 8; 4 lidos (17307888, 33632313, 30090678, 42316329); 4 não lidos (21084657, 17581977, 30268966, 29879638) | 1 incluído (@silbernagel2007, tendão de Aquiles); 33632313 (piloto de tendinopatia patelar, n = 15), 30090678 e 42316329 (outras condições) excluídos |
| C3 | PubMed | `(anterior cruciate ligament[tiab]) AND (quadriceps[tiab]) AND ("high-load"[tiab] OR heavy[tiab] OR "low-load"[tiab] OR "blood flow restriction"[tiab] OR "resistance training"[tiab]) AND (systematic review[pt] OR meta-analysis[pt])`, ≥ 2018 | 12 PMIDs (1 já avaliado, 38887689); os outros 11 não foram triados por título | substituída por C4 |
| C4 | Consensus | "blood flow restriction or high-load resistance training quadriceps strength anterior cruciate ligament injury systematic review", RS/MA, ≥ 2019, 5 registros | 5 RS de BFR pós-ACLR; 1 recuperada e verificada no PubMed (42355875, @xu2026); as demais (Koc 2022, Moiroux-Sahraoui 2025, Hu 2026, Redouane 2025) **não** verificadas por PMID e não usadas | 1 incluída |
| C5 | PubMed | `(FIFA 11+[tiab] OR "11+"[tiab] OR "neuromuscular training"[tiab]) AND (football[tiab] OR soccer[tiab]) AND (injury prevention[tiab]) AND (meta-analysis[pt] OR systematic review[pt])`, ≥ 2015 | 37; 20 PMIDs retornados, sem triagem por título | complementada por C6 |
| C6 | Consensus | "FIFA 11+ warm-up injury prevention football players meta-analysis", RS/MA, ≥ 2015, 8 registros | 8; PMID obtido por `lookup_article_by_citation`/busca para Sadigursky 2017 (29209504) e Zarei 2026 (41981827) | 1 incluída (@sadigursky2017); Zarei 2026 lida e **não usada** (resumo traz apenas o IC 0,12–0,22, sem estimativa pontual, I² = 88,98%) |
| C7 | PubMed | `(knee ligament sprain OR "anterior cruciate ligament" OR "knee stability") AND ("clinical practice guideline"[ti] OR "clinical practice guidelines"[ti]) AND (Orthopaedic Section OR "Academy of Orthopaedic Physical Therapy" OR rehabilitation)`, ≥ 2018 | 14; 3 PMIDs desconhecidos lidos (42893304, 42647856, 42263851): irrelevantes (estudo qualitativo, apreciação de diretrizes com IA, LLM); **nenhuma atualização da diretriz JOSPT 2017** | checagem de versão |
| C8 | Web | `WebSearch` "Logerstedt 2017 knee ligament sprain clinical practice guideline recommendations…"; `WebFetch` de orthopt.org e apta.org | busca devolveu os PDFs do órgão; **`WebFetch` falhou nos dois hosts** (host não resolvido: `www.orthopt.org` e `www.apta.org` precisam ser liberados na rede da sessão) | limitação |
| C9 | PubMed | consultas diretas por PMID de 19204579 e 21694556 (posicionamentos do ACSM) e de títulos pontuais | os PMIDs foram informados de memória e **confirmados pela ferramenta** (metadados batem com o título esperado) | base de prescrição |

**Limitações de cobertura (declaradas).** (1) **BVS/LILACS e Cochrane Library não foram consultadas diretamente**; a Cochrane entrou apenas via PubMed (revisão @monk2016) e a literatura brasileira apenas via PubMed/Consensus; (2) sites de órgãos (APTA/Orthopaedic Section, AAOS, MS/Conitec, NICE, SBOT) não foram abertos: de uma diretriz só se conhece o que o PubMed informa; (3) buscas C1, C3 e C5 retornaram só PMIDs e não foram triadas na íntegra; (4) o filtro de 2010 exclui parte da literatura clássica (mantidos Frobell e outros pivotais).

**Diretriz nacional.** Não há diretriz nacional de reabilitação do LCA (nenhum PCDT/Conitec; SBOT/AMB só 2007, de diagnóstico e enxerto; SBRATE, COFFITO e NICE sem documento específico), conforme `03a-busca.json`. Declarado como lacuna, não como achado de ausência confirmada nos portais.

## 2. Seleção (fluxo PRISMA: identificados → triados → avaliados → incluídos)

| Etapa | n | Origem / motivo |
|---|---|---|
| Registros identificados (03a) | 486 | PubMed 433; Consensus 50; web 3 |
| Duplicatas removidas | 108 | 88 mesmo PMID entre strings; 13 Consensus × PubMed; 7 mesma publicação em periódicos diferentes |
| Triados por título/resumo | 378 | |
| Excluídos na triagem | 144 | população 34; intervenção 48; fora do tema 30; versão superada 4; desfecho 11; desenho 15; período 2 |
| Excluídos por volume (corte do líder) | 154 | nenhuma diretriz cortada |
| **Encaminhados para avaliação** | **80** | 53 "incluir" + 27 "talvez" |
| Avaliados com resumo completo nesta etapa | 45 | 37 incluídos + 8 excluídos após leitura |
| Decididos só pelo registro de triagem (título + resumo curto) | 35 | todos excluídos; ver motivos abaixo |
| Incluídos entre os 80 | **37** | |
| Excluídos entre os 80 | **43** | C1–C7 abaixo |
| Incluídos de fora dos 80 | **10** | 5 já na etapa 01 (@grindem2016, @lundblad2019, @arundale2018, @bullock2025, @webster2019, resumos relidos) + 5 das buscas complementares (@silbernagel2007, @sadigursky2017, @acsm2009, @garber2011, @xu2026) |
| **Total incluído no quadro** | **47** | 9 diretrizes/consensos, 16 revisões, 7 ECR (incl. 2 análises do COMPARE), 12 coortes/caso-controle e 3 fontes de dose/indiretas |

> A meta do agente é 8 a 20 fontes; o total (47) a excede porque o caso cobre sete subtemas essenciais e cada um exigiu fonte própria, e porque quase todo o respaldo de critérios e de dose é indireto e precisou ser rotulado. O **núcleo para slides e arguição** (16 fontes) está no §7. Sugestão ao líder: usar 47 no artigo e 16 nos slides.

**Motivos de exclusão entre os 80 (43).**
- **C1, redundante ou coberto por fonte mais forte/recente já incluída (16):** 38940695 (relatório HTA do ACL SNNAP, já incluído como Lancet), 35975945 (trajetórias da mesma coorte Delaware-Oslo; lido), 29927640 (mesma coorte), 28515057 (análise exploratória do KANON, lida), 39976186 (trajetória de PROMs em 84 ECR, lida; sem relação com o caso), 38646275 e 34929763 e 38130557 (revisões/estudos de periódicos menores sobre ACLR × conservador), 25394687 (preditores de cirurgia; coberto por @arp2024), 24553885 e 26224582 e 21773828 (histórico longo prazo e QV, cobertos por Frobell/Urhausen/Filbay), 22119290 (RS de 2011 de LCA + LCM, lida, superada por @shultz2024 e @vanderlist2024), 22898912 e 30001501 (já usadas na etapa 02), 30170524 (resumo de diretriz; usa-se a diretriz @arundale2018).
- **C2, versão superada ou desatualizada (3):** 22900914 (diretriz holandesa de 2012), 26131301 (MOON 2015, pós-ACLR), Projeto Diretrizes AMB/CFM 2007 (diagnóstico).
- **C3, população pós-ACLR sem dado de conservador e sem ganho sobre Aspetar e van Melick (7):** 42205141, 42549304, 40518903, 35089850, 35998884, 34903114 (lido: resumo sem conteúdo extraível), 26772611.
- **C4, esqueleto imaturo (1):** 41710220.
- **C5, desfecho ou escopo fora da pergunta (10):** 36328403 (RM), 42331698 (preferências de pacientes; lido), 32159239 (biomecânica da marcha), 36952667 (estudo de caso de uso da diretriz AAOS), 37130278 e 37130279 e 36379676 (prevenção de osteoartrite), 37098282 (qualidade de protocolos online), 30537875 (questionários), 30388671 (relato de variáveis de treino).
- **C6, intervenção ou desenho inadequado (4):** 42241597 (revisão narrativa, lida), 38811114 (revisão narrativa), 22061048 (biomecânica da marcha em 21 non-copers, lido), 42317908 (treino aquático, periódico de baixa seleção).
- **C7, documento inacessível (2):** 42875873 (consenso UEFA feminino: resumo indisponível no PubMed) e o documento australiano de 2021 (apenas resultado de busca).

## 3. Diretrizes vigentes (recomendação, força/certeza, ano, convergências e divergências)

**Não há diretriz brasileira (MS/Conitec, SBOT, SBRATE, COFFITO) de reabilitação do LCA ou do LCM.** A conduta no SUS depende de protocolos locais; a evidência abaixo é internacional.

| Documento | Ano | Tipo e qualidade | O que recomenda (relevante ao caso) | Certeza/força |
|---|---|---|---|---|
| @logerstedt2017 (APTA, Orthopaedic Section; JOSPT) | 2017 | CPG com revisão sistemática; AGREE II **não avaliável** (recomendações e graus não acessados: resumo genérico e sites bloqueados) | Conteúdo não extraído. Uma busca web secundária sugere recomendação de combinar treino neuromuscular com fortalecimento e uso do ACL-RSI, **não verificada** e não usada como fato | não aplicável. Nenhuma versão posterior encontrada no PubMed; **confirmação no site do órgão não feita** |
| @diermeier2020 (Panther, tratamento) | 2020 | Consenso Delphi (66 especialistas, 18 países; 80% como consenso; 11/13 declarações) | Alta demanda de pivô e saltos: ACLR anatômica precoce, após reabilitação progressiva para resolver déficits; esporte em plano reto: não operatório com reabilitação estruturada é aceitável; **falseio ou instabilidade funcional persistente: ACLR indicada** | baixa (opinião); sem graus |
| @meredith2020 (Panther, retorno ao esporte) | 2020 | Consenso Delphi | RTS é contínuo (participação, esporte, desempenho); **abandonar decisão só por tempo**; testes funcionais mais prontidão psicológica; considerar cicatrização e lesões concomitantes | baixa (consenso) |
| @filbay2019 (revisão com recomendações; texto completo lido) | 2019 | Revisão narrativa estruturada | Reabilitação como 1ª linha é razoável (único ECR não superou a cirurgia precoce); ACLR se houver instabilidade funcional; reabilitação por critérios em 5 fases; acompanhamento ≥ a cada 2 semanas; regras de derrame e dor para a carga; encaminhar ao médico se falseio repetido | baixa a moderada (síntese de especialistas) |
| @brophy2023 (AAOS, resumo da CPG 2022) | 2023 | Diretriz com RS (8 recomendações, 7 opções) | **Conteúdo não acessado**; a versão de 2015 foi superada | não aplicável |
| @ishibashi2019 (JOA) | 2019 | Diretriz (21 questões clínicas, 23 de fundo) | **Conteúdo não acessado** | não aplicável |
| @kotsifaki2023 (Aspetar) | 2023 | CPG, AGREE II + GRADE, **pós-ACLR** | Exercício é o pilar; pouca evidência de dose-resposta; nenhuma evidência sobre critérios de progressão ou alta; critérios mínimos propostos por consenso (texto completo) | muito baixa para a maioria; concordância dos especialistas ≥ 75,7% |
| @vanmelick2016 (KNGF) | 2016 | CPG com 90 estudos, **pós-ACLR** | Prehab + 3 fases criteriais; bateria de força, saltos, qualidade de movimento e psicologia para progredir; 9 a 12 meses | baixa; 2016, anterior a Aspetar |
| @arundale2018 (CPG prevenção, JOSPT) | 2018 | CPG com RS | Prevenção de lesão de joelho/LCA por exercício; conteúdo não acessado | não aplicável |

**Convergências.** (1) progressão **por critérios**, não por tempo (@meredith2020; @vanmelick2016; @filbay2019; @kotsifaki2023); (2) força de quadríceps e treino neuromuscular como núcleo, com prontidão psicológica no retorno (@filbay2019; @meredith2020); (3) decisão compartilhada e um período de reabilitação antes da decisão cirúrgica (@filbay2019; @diermeier2020, que também pede reabilitação prévia); (4) falseio recorrente é o gatilho para cirurgia (@diermeier2020; @filbay2019).

**Divergências e por quê.** O consenso Panther recomenda ACLR precoce em atletas de pivô de alta demanda, argumentando risco de lesão meniscal e condral com a cirurgia tardia (@diermeier2020), enquanto @filbay2019 sustenta reabilitação como primeira linha com base no KANON. A diferença vem do **peso dado à evidência**: o consenso é opinião (nível V); no ECR COMPARE, procedimentos meniscais em 2 anos foram 29% (25/85) com ACLR precoce e 21% (17/82) com reabilitação inicial (RR 0,67; IC 95% 0,40–1,12; p = 0,12), ou seja, **sem aumento** com a estratégia de reabilitação (@graaff2022menisco). Há também diferença de **população**: KANON incluiu lesões agudas em joelho previamente hígido; o ACL SNNAP (lesão não aguda com instabilidade persistente) favoreceu a cirurgia (§4). Os critérios de retorno e de dose vêm de diretrizes **pós-ACLR** (@kotsifaki2023; @vanmelick2016): aplicá-los ao Bruno é extrapolação.

**Posição do MS/SUS.** Sem diretriz específica de reabilitação do LCA/LCM localizada; a posição do SUS não pôde ser documentada (a pista sobre o código SIH/SUS da reconstrução, na pendência 2 da etapa 01, não foi verificada).

## 4. Revisões sistemáticas e metanálises

Confiança AMSTAR 2 e riscos são **estimativas a partir do resumo** (limitação: sem acesso ao texto; domínios críticos como lista de exclusões e fontes de financiamento não puderam ser conferidos).

**Conservador × cirurgia (jovem ativo).**
- @monk2016 (Cochrane, 1 ECR, 121 analisados): KOOS4 em 2 anos, diferença de médias −0,20 (IC 95% −6,78 a 6,38) e em 5 anos −2,0 (−8,27 a 4,27); no braço conservador 39% (23/59) foram operados em 2 anos e 51% (30/59) em 5 anos; RTS no mesmo nível ou maior em 2 anos sem diferença estatística (IC amplo); certeza baixa. AMSTAR 2: confiança alta, mas limitada a um ensaio.
- @saueressig2022 (viva, Bayesiana, 3 ECR, 320 participantes): sem diferença clinicamente importante em função autorrelatada (certeza baixa a muito baixa); OA radiográfico OR 1,45 (credibilidade 95% 0,30–5,17; muito baixa); dano meniscal OR 0,85 (0,45–1,62; baixa). Confiança estimada: alta a moderada.
- @dejonge2024 (LCA isolado; 2 ECR + 3 retrospectivos): estabilidade melhor com ACLR (diferença de médias −2,44; IC 95% −3,21 a −1,66); OA OR 1,84 (0,90–3,75); Lysholm 2,88 (−1,09 a 6,85); ACLR protetora contra lesões subsequentes; qualidade baixa.
- @filbay2025 (15 estudos, 2 ECR): retorno ao esporte OR 1,5 (0,76–2,97), Tegner 0,7 (0,16–1,24) abaixo da mudança mínima detectável; 10 de 15 estudos com alto risco de confusão que favorecia a cirurgia; certeza baixa a muito baixa.
- @arp2024 (escopo, 10 estudos): só menor idade e maior atividade pré-lesão predizem ACLR posterior.
- @dayal2026 (7 estudos, 351 pacientes): continuidade do LCA na RM em 85,6%, porém estabilidade no artrômetro em apenas 54,7%; 21,9% operados depois; reinjúria 7,1%. Confiança baixa.

**Reabilitação conservadora: conteúdo.**
- @ghezzi2026 (escopo, 14 estudos, 570 atletas, 14–57 anos): 53% concluíram sem cirurgia, **30% retornaram ao esporte**, reinjúria 28%; duração média de 12 ± 8 semanas; força em 48% dos protocolos, controle neuromuscular em 10%, exercícios esportivos em 25%; lesões associadas pioraram o retorno; heterogeneidade impede padronizar. Não avalia risco de viés.
- @culvenor2022 (overview, 22 RS, 142 ECR): certeza **moderada** para NMES aumentar força do quadríceps, equivalência entre cadeia aberta e fechada e entre reabilitação domiciliar e presencial, e ineficácia de órtese pós-operatória; **muito baixa** para BFR (tamanho do quadríceps) e para exercícios de controle neuromuscular. Maioria dos ensaios é perioperatória.
- @pamboris2024 (9 ECR, PEDro, GRADE): CCA superior à CCF para força isocinética do quadríceps aos 3 e 4 meses (p = 0,03; 0,008), com menor laxidão em LCA deficiente às 10 semanas (p = 0,01); certeza muito baixa a baixa. Contrasta com @culvenor2022 (equivalência, certeza moderada).
- @xu2026 (BFR pós-ACLR, 17 estudos, 643 participantes): força de quadríceps SMD 0,77 (IC 95% 0,42–1,13; certeza moderada); função SMD 1,47 (0,08–2,87; I² = 91%); dor e equilíbrio sem efeito (muito baixa). **Pós-ACLR: indireta.**
- @nunes2023 (48 ECR): correção do valgo dinâmico se correlaciona com dor/função na dor patelofemoral (r de −0,69 a 0,73), mas em LCA (8 ECR, n = 198) a evidência é limitada e incerta.
- @webster2019 (pós-ACLR): 23% passam as baterias de retorno; passar reduz ruptura de enxerto (RR 0,40; 0,23–0,69), não reduz todas as lesões do LCA (RR 0,80; 0,27–2,3) e se associa a mais lesão do LCA contralateral (RR 3,35; 1,52–7,37).

**LCM associado.**
- @vanderlist2024 (27 estudos, 821 pacientes, LCA + LCM completos agudos): estabilidade em valgo a 30° em **27–68%** com LCA e LCM não operados, 36–77% com reparo de LCM e LCA não operado, 80–100% com ACLR aguda; Lysholm sem diferença. Nível IV.
- @shultz2024 (18 estudos, 1.534 casos): sem diferença entre LCM não operatório e cirúrgico em PRO, ADM e força (todos com ACLR); ACLR tardia permite cicatrização de LCM de baixo grau; valgo ou instabilidade rotatória anteromedial persistente após reabilitação justifica cirurgia concomitante. O bom resultado do LCM não operado ocorre **com o LCA reconstruído**.

**Prevenção.**
- @bullock2025 (82 estudos, 154.561 atletas, 55% mulheres): treino neuromuscular (dose mínima de 10 min, 2×/semana) reduz lesões do LCA em 61% (RR 0,39; IC 95% 0,25–0,60; certeza **alta**); lesões de membros inferiores 0,81 (0,61–1,08; baixa). **Mulheres.**
- @sadigursky2017 (6 ECR, 6.344 jogadores; autores brasileiros): FIFA 11+ reduz lesões em geral em 30% (RR 0,70; IC 95% 0,52–0,93), heterogêneo; **não é específico de LCA**.

## 5. Ensaios clínicos e outros estudos relevantes

Risco de viés (RoB 2) estimado do resumo; avaliação feita só pelo resumo é limitação.

**ECR de estratégia (conservador × cirurgia).**
- **KANON** (@frobell2010; @frobell2013): 121 adultos jovens ativos com LCA agudo e joelho previamente hígido, idade média 26 anos. Mudança de KOOS4 em 2 anos de 39,2 (ACLR precoce) × 39,4 (opcional tardia), diferença 0,2 (IC 95% −6,5 a 6,8; P = 0,96); do braço opcional, 23 de 59 foram operados em 2 anos e 30 (51%) em 5 anos, com KOOS4 de 42,9 × 44,9 (diferença 2,0; IC 95% −8,5 a 4,5; P = 0,54) e sem diferença em menisco (P = 0,48) ou OA (P = 0,17). **Cálculo:** 36/59 (61%) evitaram cirurgia em 2 anos e 29/59 (49%) em 5 anos. RoB 2: algumas preocupações (desfecho autorrelatado, sem cegamento).
- **COMPARE** (@reijman2021): 167 adultos de 18 a 65 anos (média 31,3). IKDC em 24 meses melhor com ACLR precoce, diferença 5,3 (IC 95% 0,6–9,9; P = 0,026), de importância clínica incerta; aos 3 meses melhor na reabilitação (−9,3; −14,6 a −4,0); **50% (41/82) foram operados**. Na análise exploratória, 90% (37/41) dos operados citaram instabilidade como motivo, a maior parte (41,5%) entre 3 e 6 meses; eram mais jovens (27,4 × 35,3 anos) e mais ativos (@graaff2022).
- **ACL SNNAP** (@beard2022): 316 pacientes com LCA **não agudo e instabilidade persistente**; KOOS4 aos 18 meses de 73,0 (DP 18,3) com cirurgia × 64,6 (DP 21,6) com reabilitação, diferença ajustada 7,9 (IC 95% 2,5–13,2; p = 0,0053) **a favor da cirurgia**; 41% (65/160) do braço de reabilitação foram operados. É o ensaio mais parecido com o perfil do Bruno, com a ressalva de que "reabilitação" ali é fisioterapia pragmática, não o algoritmo estruturado de Delaware-Oslo.
- **ACL-SPORTS** (@arundale2017; pós-ACLR, 40 homens): treino de perturbação sem benefício adicional à base de força, agilidade e prevenção secundária; simetria do quadríceps em 2 anos de 103 ± 11% × 98 ± 14%. **Indireta.**

**Coortes do algoritmo Delaware-Oslo (única estrutura de reabilitação criterial para o conservador).**
- @thoma2019 (n = 271): após 10 sessões de treino neuromuscular e de força, quase metade dos *non-copers* iniciais passou a *potential copers* (P < 0,001); sucesso em 2 anos de 66% (ACLR) e 74% (não operatório); *potential copers* pós-treino tiveram OR 2,7 (IC 95% 1,3–5,6) e 2,9 (1,2–7,2) de sucesso; *non-copers* persistentes foram mal, sugerindo reabilitação mais intensa.
- @grindem2018 (118 que escolheram não operar): 53,6% (52/97) com sucesso em 2 anos; preditores: maior idade, sexo feminino, melhor hop test e KOS-ADLS; AUC 0,78 (IC 95% 0,68–0,88) após 5 semanas de treino. Excluiu lesão concomitante significativa.
- @pedersen2021 (5 anos; n = 276) e @urhausen2025 (10 anos; 191 no seguimento): resultados semelhantes entre ACLR precoce, tardia e reabilitação isolada (25% no 5º ano); 95–100% ainda no esporte; 10 anos: PASS 78%, quadríceps simétrico 72%, OA sintomática 1% e radiográfica 12%; ACLR tardia com KOOS Esporte/QV e hop pior (p ≤ 0,03). Risco de seleção; **sem lesões concomitantes importantes** (excluem o caso LCA + LCM).

**Retorno ao esporte e nova lesão no conservador.**
- @grindem2012 (coorte pareada, 69 × 69): retorno geral 68,1% × 68,1%; nível I 54,8% × 61,9% (P = 0,66); não operados que eram nível I voltaram menos que os de nível II (54,8% × 88,9%; P = 0,003), com alta não adesão à restrição de atividade.
- @svensson2026 (NACOX, 270): 78% retornaram; nível I 66% e em mediana 12 meses; **futebol 60%**. @slater2022 (88 sem cirurgia): 46% retornaram em 12 meses; prontidão psicológica aos 12 meses OR 1,9 (1,2–3,2) por ponto.
- @hamrinsenorski2025 (31 sem cirurgia × 359 ACLR): maior simetria de força na reabilitação isolada e maior autoeficácia/atividade na ACLR. Cautela: LSI alto sem cirurgia pode vir de seleção.
- @vanyperen2018 (50 atletas de alto nível, 20 anos): sem diferença de OA (80% × 68%; P = 0,508) e IKDC (81,6 × 78,2; P = 0,679); Lachman negativo 48% × 4% (P = 0,002). Viés de seleção grave (os não operados eram os bons respondedores aos 3 meses).
- @grindem2016 (pós-ACLR): reinjúria 38,2% em quem falhou nos critérios × 5,6% em quem passou (HR 0,16; p = 0,075); −51% por mês de espera até 9 meses. **Indireta.**

**LCM em caso combinado.** @dadgostar2024 (11 pacientes com LCA + LCM tratados sem cirurgia × 11 controles saudáveis, 2 anos): nenhuma instabilidade relatada, hop sem diferença (p = 0,326; 0,859); risco grave de viés e amostra mínima. @lundblad2019 (130 lesões do LCM em futebol profissional): concordância clínica × RM de 92% (kappa 0,87; IC 95% 0,77–0,96); LCM grau II com órtese teve afastamento de 41,5 × 31,5 dias (p = 0,010), sem aleatorização, LCM isolado.

**Dor e carga (evidência indireta).** @silbernagel2007 (ECR, n = 38, tendão de Aquiles): continuar corrida e saltos guiado por modelo de monitoramento da dor não piorou o desfecho (VISA-A-S 57 → 85 × 57 → 91 em 12 meses). **Não foi encontrado estudo desse modelo em LCA ou LCM** (buscas C1 e C2); a regra de derrame e de dor vem de consenso (@filbay2019; @kotsifaki2023: sem derrame ou traço para iniciar corrida).

**Dose (FITT-VP).** Não há ECR de dose em LCA deficiente. Bases disponíveis: @ghezzi2026 (descrição dos protocolos), @kotsifaki2023 (dose-resposta desconhecida), @pamboris2024 e @culvenor2022 (cadeia cinética), @xu2026 (BFR), @bullock2025 (treino neuromuscular, mínimo de 10 min, 2×/semana), @acsm2009 e @garber2011 (adultos saudáveis).

## 6. Síntese por desfecho com certeza GRADE (quadro)

Certeza = julgamento **do avaliador** a partir dos resumos e das graduações dos autores quando existem (indicado). "Indireta" rebaixa um nível (evidência pós-ACLR ou sem lesão combinada).

| Desfecho (tipo) | Direção e magnitude | Estudos / participantes | Certeza GRADE | Motivo do rebaixamento/elevação |
|---|---|---|---|---|
| Função autorrelatada (KOOS/IKDC), estratégia reabilitação ± ACLR tardia × ACLR precoce, **LCA agudo** (clínico) | Sem diferença clinicamente importante: KANON 0,2 (−6,5 a 6,8) em 2 anos; COMPARE 5,3 (0,6–9,9) a favor da ACLR, de relevância incerta | 3 ECR; 320 participantes (@saueressig2022; @monk2016) | **Baixa** (autores: baixa a muito baixa) | risco de viés (sem cegamento), imprecisão, indireta (agudos, sem LCM) |
| Função, **LCA não agudo com instabilidade persistente** (clínico) | Cirurgia melhor: KOOS4 +7,9 (2,5–13,2) em 18 meses | 1 ECR; 316 (@beard2022) | **Moderada** (avaliação própria) | rebaixa por cruzamento de grupos (28% do braço cirúrgico sem cirurgia) e ausência de cegamento; mantém por tamanho e precisão |
| Necessidade de cirurgia tardia / falseio (clínico) | 41% a 51% operados (SNNAP 41%, COMPARE 50%, KANON 51% em 5 anos); instabilidade é o motivo em 90% | 3 ECR; ≈ 600 (@frobell2013; @reijman2021; @beard2022; @graaff2022) | **Moderada** para a taxa; **baixa** para preditores (menor idade e maior atividade: @arp2024) | consistência entre ECR; preditores em coortes |
| Retorno ao esporte (clínico) | Conservador ≈ ACLR: OR 1,5 (0,76–2,97); 60% no futebol; 55% nível I sem cirurgia; 30% na revisão de escopo | 15 estudos (2 ECR) + coortes (@filbay2025; @grindem2012; @svensson2026; @ghezzi2026) | **Baixa a muito baixa** | confusão, heterogeneidade, imprecisão |
| Nova lesão (clínico) | ACLR protetora contra lesões subsequentes (qualitativo); reinjúria 28% (escopo) e 7,1% (RS) em conservador; re-rupturas 2 + 1 × 4 + 3 no COMPARE | heterogêneo (@dejonge2024; @ghezzi2026; @dayal2026; @reijman2021) | **Muito baixa** | definições variáveis, seguimentos curtos |
| Estabilidade objetiva (laxidão) (substituto) | Maior no conservador (diferença −2,44; −3,21 a −1,66; Lachman negativo 4% × 48% aos 20 anos), sem pior função | @dejonge2024; @vanyperen2018; @dayal2026 | **Baixa** | desenho misto, viés de seleção; laxidão não prediz função (@filbay2019) |
| Estabilidade em valgo a 30° em LCA + LCM sem cirurgia (clínico/substituto) | 27–68% com ambos sem cirurgia × 80–100% com ACLR aguda | 27 estudos; 821 (@vanderlist2024) | **Muito baixa** | nível IV, lesões completas e agudas, heterogêneo |
| Função e LCM tratado sem cirurgia (clínico) | Sem diferença entre LCM não operado e cirúrgico, **sempre com ACLR** | 16 estudos; 997 (@shultz2024) | **Muito baixa** | observacional, indireta (LCA reconstruído) |
| LCA + LCM sem nenhuma cirurgia: função e instabilidade (clínico) | 0 de 11 com instabilidade em 2 anos, hop normal | 1 caso-controle; 22 (@dadgostar2024) | **Muito baixa** | n mínimo, risco grave de viés, imprecisão |
| Reclassificação coper/non-coper após ~10 sessões (substituto/prognóstico) | Quase metade dos non-copers virou potential coper; potential copers: OR 2,7 a 2,9 de sucesso | 1 coorte; 271 (@thoma2019); modelo de @grindem2018 (AUC 0,78) | **Baixa** | observacional, escolha do tratamento pelo paciente, sem lesão associada |
| Força do quadríceps (substituto) | NMES e CCA = CCF (moderada); CCA melhor aos 3 a 4 meses (muito baixa/baixa); BFR SMD 0,77 (0,42–1,13) | @culvenor2022; @pamboris2024; @xu2026 | **Moderada** para NMES e para BFR **pós-ACLR**; **muito baixa a baixa** para o conservador | **indireta (pós-ACLR)** e inconsistência entre RS |
| Treino neuromuscular/perturbação (substituto/clínico) | Controle neuromuscular: sem efeito claro em força/função (muito baixa); perturbação sem benefício adicional pós-ACLR | @culvenor2022; @arundale2017 | **Muito baixa** | imprecisão, indireta |
| Critérios de progressão/retorno (substituto) | 23% passam as baterias; falhar: reinjúria 38,2% × 5,6% (HR 0,16; p = 0,075); validade equívoca | @webster2019; @grindem2016 | **Baixa (pós-ACLR); muito baixa para conservador** | **indireta**, p não significativo, risco de contralateral |
| Dor/derrame para ajustar carga (substituto) | Sem estudo em LCA/LCM; Aquiles: continuar com monitoramento de dor não prejudicou | @silbernagel2007 (n = 38) + consenso | **Muito baixa** | indireta (outro tendão), n pequeno |
| Prevenção de lesão do LCA com treino neuromuscular (clínico) | −61% (RR 0,39; 0,25–0,60) em **mulheres**; FIFA 11+ lesões em geral RR 0,70 (0,52–0,93) | @bullock2025; @sadigursky2017 | **Alta** (LCA, mulheres); **baixa a moderada** (FIFA 11+, geral) | alta: ensaios consistentes e grandes; FIFA 11+: heterogeneidade; **indireta ao homem já lesionado** |
| Dose FITT-VP no LCA deficiente (substituto) | Sem dose-resposta; protocolos heterogêneos (12 ± 8 semanas) | @ghezzi2026; @kotsifaki2023 | **Muito baixa** | ausência de ensaios, indireta |

## 7. Resposta à pergunta e lacunas

**Resposta (5 linhas).** (1) Em jovens ativos com **LCA agudo**, reabilitação estruturada com cirurgia tardia opcional dá função equivalente à cirurgia precoce (certeza baixa), mas **41% a 51% acabam operados**, sobretudo os mais jovens e ativos, por instabilidade; em lesão **não aguda com instabilidade persistente**, que é o perfil do Bruno, a cirurgia foi superior em ensaio pragmático (certeza moderada). (2) A conduta conservadora defensável é um **bloco inicial de reabilitação por critérios (≈ 5 semanas, ≈ 10 sessões de treino neuromuscular e de força), reclassificação coper/non-coper e decisão compartilhada**, com encaminhamento ao ortopedista se houver falseio recorrente, derrame que não resolve, déficit de extensão ou valgo residual (certeza baixa, consenso). (3) Os critérios de progressão e de retorno, e a dose do exercício, vêm quase todos de populações **pós-ACLR ou de adultos saudáveis** e têm certeza muito baixa para o conservador; a expectativa de retorno ao esporte de pivô sem cirurgia é de cerca de 55% (nível I, @grindem2012) a 60% (futebol, tratamentos mistos, @svensson2026). (4) Para o **LCM**, o que há mostra que o ligamento de baixo grau cicatriza em geral **quando o LCA é reconstruído**; com os dois sem cirurgia a estabilidade em valgo a 30° foi de 27% a 68% (certeza muito baixa), portanto o estiramento associado **não** autoriza tratar o caso como isolado. (5) A prevenção neuromuscular tem alta certeza para LCA, mas em mulheres; a extensão ao homem lesionado é indireta.

**Núcleo para slides e arguição (16 fontes).** @frobell2010; @frobell2013; @reijman2021; @beard2022; @monk2016; @thoma2019; @pedersen2021; @diermeier2020; @filbay2019; @meredith2020; @kotsifaki2023; @ghezzi2026; @vanderlist2024; @shultz2024; @webster2019; @bullock2025.

**Insumos para a prescrição (04), com o rótulo de certeza de cada um.**
- **Bloco inicial e reavaliação:** 5 semanas de treino neuromuscular e de força antes de decidir a cirurgia, ou ≈ 10 sessões para reclassificar (@pedersen2021; @thoma2019; coorte, certeza baixa). Visitas supervisionadas ao menos a cada 2 semanas e exercícios em frequência de diária a 2–3 vezes por semana (@filbay2019; consenso).
- **Força:** treino de alta carga é o recomendado (@filbay2019); dose de referência para adultos saudáveis: 8–12 RM no iniciante, progressão de 2–10% quando se fazem 1–2 repetições acima da meta, 2–3 dias por semana no iniciante e 3–4 no intermediário (@acsm2009; **indireta**). Cadeia aberta e fechada combinadas, monitorando dor anterior (@kotsifaki2023; pós-ACLR); equivalência entre elas com certeza moderada (@culvenor2022). BFR de baixa carga tem certeza moderada para força, mas **só pós-ACLR** (@xu2026).
- **Pliometria e agilidade:** 8 semanas de pliometria, com benefício em função na fase avançada (@kotsifaki2023; pós-ACLR); só depois dos critérios mínimos de corrida propostos por consenso: sem derrame ou derrame traço, flexão ≥ 95%, extensão total, LSI de quadríceps > 80% e saltitos unipodais sem dor (@kotsifaki2023).
- **Dor e derrame (semáforo):** usar derrame (teste do golpe modificado, confiabilidade na etapa 01, @sturgill2009) e desconforto no joelho como regras de carga (@filbay2019); modelo de monitoramento da dor com apoio apenas **indireto** (@silbernagel2007). Carga de campo pela PSE da sessão × minutos (@filbay2019).
- **Retorno ao esporte:** por critérios e não por tempo (@meredith2020); critérios pós-ACLR: força e saltos > 90%, KOS-ADLS e escala global > 90 (@grindem2016) e ACL-RSI (@slater2022; @filbay2019); **extrapolação para o conservador, certeza muito baixa**. Não há prazo mínimo validado sem cirurgia.
- **Prevenção e nova lesão:** manter treino neuromuscular com dose mínima de 10 min, 2×/semana (@bullock2025) e FIFA 11+ como aquecimento de equipe (@sadigursky2017).
- **Pós-operatório tardio (nota breve):** retorno a esportes de pivô só após ≥ 9 meses de ACLR (@filbay2019; @grindem2016; @vanmelick2016 prevê 9 a 12 meses), com maturação do enxerto que pode passar de 12 meses (@filbay2019) e restrições definidas pelo cirurgião; não muda a prescrição conservadora.

**Lacunas persistentes.** (1) Nenhum ECR de reabilitação progressiva **por critérios × por tempo** no LCA deficiente; (2) nenhum estudo de dose-resposta no LCA deficiente; (3) o ACL SNNAP não é o algoritmo Delaware-Oslo e os estudos Delaware-Oslo **excluíram lesões associadas**: não há estudo do conservador com LCA + LCM em atleta; (4) critérios de retorno e BFR validados só pós-ACLR; (5) o modelo de monitoramento da dor só tem apoio em tendinopatia; (6) predominam amostras de mulheres na prevenção e de homens na reabilitação (@culvenor2022); (7) nenhuma diretriz nacional; (8) recomendações da diretriz JOSPT 2017, da AAOS e da JOA **não extraídas**; (9) o grau do LCM, o tempo de lesão, a cirurgia prévia e a RM do Bruno não constam do enunciado (etapa 02).

**Limitações gerais da avaliação.** Resumos apenas, salvo @filbay2019 e @kotsifaki2023 (texto completo). AMSTAR 2, RoB 2 e ROBINS-I estimados a partir do resumo. Conflitos de interesse e financiamento não avaliados. Cochrane Library e BVS/LILACS não consultadas diretamente.

## Pendências para o líder

1. **Meta de fontes excedida (47 em vez de 8 a 20)**, justificada no §2; núcleo de 16 fontes no §7. Decidir se o artigo adota as 47.
2. **Diretrizes sem recomendações extraídas:** JOSPT 2017 (@logerstedt2017), AAOS (@brophy2023), JOA (@ishibashi2019) e UEFA feminino 2026 (PMID 42875873, sem resumo). `orthopt.org` e `apta.org` não resolveram no `WebFetch`; liberar esses hosts permitiria extrair os graus (A–F) e confirmar que a versão de 2017 é a mais recente (o PubMed não mostra revisão posterior).
3. **Ano do fascículo a conferir pelo verificador:** @ishibashi2019 (J Orthop Sci 25(1); publicação eletrônica em dez/2019), @slater2022 (Sports Health 15(2)), @graaff2022menisco (BJSM 57(2); eletrônica em set/2022). Mantive o ano do PubMed. @xu2026 sem paginação no PubMed (número do artigo provável 4706). @acsm2009 sem autores individuais no PubMed (autor_entidade ACSM).
4. **PMIDs informados de memória e confirmados pela ferramenta:** 19204579 e 21694556 (ACSM); metadados batem com os títulos.
5. **Buscas complementares C1, C3 e C5 devolveram só PMIDs**; 19 + 11 + 20 registros não foram triados por título. Possível revisão pelo buscador (Haiku) se o líder quiser fechar essa lacuna.
6. **Zarei 2026 (PMID 41981827; não incluída)** lida e não usada: o resumo não traz estimativa pontual.
7. **Monk 2016 (Cochrane)** pode ter atualização não verificada.
8. **Dados do caso que mudam a conduta** (etapa 02, pendência 7): grau do LCM, tempo desde a lesão, cirurgia prévia, RM, KT-1000, número de falseios. Com falseio recorrente, o encaminhamento ao ortopedista não é opcional (@diermeier2020; @beard2022).
9. **Reutilização:** ids de 01 e 02 mantidos; não reconferidos nesta execução e citados só por contexto: @sturgill2009 (01), além de @augustsson2013 e @petushek2019 (01), mencionados nas lacunas via etapa 02.
