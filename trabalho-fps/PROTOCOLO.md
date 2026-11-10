# Protocolo comum dos subagentes — Trabalhos FPS

Documento de referência **obrigatório** para todos os subagentes `fps-*`.
Define pastas, contratos de arquivos, formato de referências e regras de integridade.
Cada subagente lê este arquivo antes de começar.

---

## 1. Pasta de cada trabalho

```
trabalho-fps/trabalhos/<AAAA-MM-DD>-<slug-do-tema>/
├── 00-briefing.md              ← orquestrador (tema/enunciado, curso, autores, exigências; "Tipo de trabalho")
├── rubrica.json                ← orquestrador · critérios e pesos do professor (quando houver)
├── fontes-do-professor/        ← enunciado, rubrica e modelos originais (imagens/arquivos)
├── PLANO.md                    ← (opcional) estudo e plano prévio — orientação, nunca fonte de fatos
├── 01-investigacao.md          ← fps-1-investigador (Sonnet)
├── 01-picos.json               ←   pergunta estruturada + estratégias de busca
├── 01-referencias.json         ←   definição, classificação, epidemiologia
├── 03a-busca.json              ← fps-op-buscador (Haiku) · strings, bases, datas, contagens PRISMA
├── 03a-candidatos.json         ←   candidatos triados por título/resumo
├── 02-analise-critica.md       ← fps-2-analista-critico (Sonnet)
├── 02-referencias.json         ←
├── 03-evidencias.md            ← fps-3-avaliador-evidencias (Sonnet)
├── 03-referencias.json         ←
├── 03-quadro-evidencias.json   ←   dados estruturados dos estudos incluídos
├── 04-prescricao.json / .md    ← fps-prescritor-exercicio (Sonnet) · só em caso clínico: fases FITT-VP
├── 04-referencias.json         ←
├── verificacao/                ← fps-op-verificador (Haiku) · metadados PubMed e relatórios de conferência
├── referencias.json            ← fps-4-redator-abnt · mescla de 01 + 02 + 03 (scripts/mesclar_referencias.py)
├── artigo.json  → artigo.docx  ← fps-4-redator-abnt (Sonnet)
├── slides.json  → apresentacao.pptx ← fps-5-designer-slides (Sonnet)
├── roteiro.md                  ← gerado com os slides · fala por integrante com marcas de tempo
├── revisoes/                   ← pareceres dos líderes (Opus) e da banca (Fable) + respostas dos executores
├── painel.md                   ← scripts/parecer.py painel (status de todas as etapas)
├── banca.md                    ← fps-banca (Fable) · parecer final + preparação para a arguição
├── previa-artigo/ previa-apresentacao/  ← PNGs de revisão visual
└── validacao.md                ← scripts/validar_trabalho.py
```

Cada agente **lê** os arquivos das etapas anteriores e **escreve apenas os seus**
(exceção: líderes e banca podem aplicar correções `menor` e, no escalonamento, as demais — sempre registrando no parecer).
Nunca apague nem reescreva o arquivo de outra etapa; se encontrar erro nele,
registre em uma seção `## Pendências para o orquestrador` no seu próprio arquivo.

## 2. Ferramentas de pesquisa (em ordem de preferência)

| Finalidade | Ferramenta |
|---|---|
| Busca biomédica | `mcp__PubMed__search_articles` (aceita sintaxe PubMed: `[MeSH Terms]`, `[tiab]`, `[Publication Type]`) |
| Confirmar metadados (autores, ano, volume, páginas, DOI) | `mcp__PubMed__get_article_metadata` (por PMID) · `mcp__PubMed__lookup_article_by_citation` |
| Texto completo (quando PMC) | `mcp__PubMed__get_full_text_article` |
| Artigos relacionados | `mcp__PubMed__find_related_articles` |
| Busca semântica ampla (400M+ artigos) | `mcp__Consensus__search` (use `medical_mode`, `study_types` quando pertinente) |
| Diretrizes, sites oficiais (MS, OMS, sociedades), DATASUS | `WebSearch` + `WebFetch` |

Se uma ferramenta MCP não estiver disponível, use `WebSearch`/`WebFetch` e registre isso.

## 3. Formato das referências (`*referencias.json`)

Lista JSON. Um objeto por obra. O `id` é a chave usada nas citações do texto.

```json
{
  "id": "page2021",
  "tipo": "artigo",
  "autores": ["Page, Matthew J.", "McKenzie, Joanne E.", "Bossuyt, Patrick M.", "Boutron, Isabelle"],
  "et_al": true,
  "titulo": "The PRISMA 2020 statement",
  "subtitulo": "an updated guideline for reporting systematic reviews",
  "periodico": "BMJ",
  "ano": 2021, "volume": "372", "numero": null, "paginas": "n71",
  "doi": "10.1136/bmj.n71", "pmid": "33782057",
  "desenho": "Diretriz de relato (consenso)",
  "nivel_evidencia": null,
  "verificado": true,
  "verificado_via": "PubMed PMID 33782057"
}
```

- `id`: `sobrenomeAAAA` em minúsculas, sem acento (`page2021`, `brasil2023`, `who2024`); se
  colidir, acrescente uma palavra (`who2024hipertensao`). Antes de criar ids, leia os
  `*referencias.json` das etapas anteriores e **reutilize o mesmo id para a mesma obra**.
- `tipo`: `artigo` · `livro` · `capitulo` · `documento` · `guideline` · `site`.
- `autores`: `"Sobrenome, Prenomes"`. Liste até 4 autores e marque `"et_al": true` se houver mais.
- **Sobrenomes brasileiros/ibéricos no PubMed vêm invertidos**: `da Costa Santos CM` →
  use `"Santos, Cristina Mamédio da Costa"` (ABNT entra pelo último sobrenome;
  exceções: Filho, Júnior, Neto, Sobrinho → `"Souza Filho, Ana"`).
- Instituições: `"autor_entidade": "World Health Organization"`, `"Brasil. Ministério da Saúde"`,
  `"Sociedade Brasileira de Cardiologia"`.
- `paginas`: intervalo `"924-926"` (vira *p. 924-926*); valor único (`"n71"`, `"e0234"`) = número do artigo.
- Livro/documento: `local`, `editora`, `edicao`; capítulo: `in_autores`, `in_papel` (`"org."`/`"ed."`), `in_titulo`.
- Online sem DOI: `url` + `acesso` (`"AAAA-MM-DD"`).
- `desenho`: Diretriz · Revisão sistemática com metanálise · Revisão sistemática · Ensaio clínico randomizado ·
  Coorte · Caso-controle · Transversal · Revisão narrativa · Livro-texto · Documento oficial.
- Formatação ABNT (NBR 6023:2018) é feita **automaticamente** por `scripts/abnt.py` — não escreva a referência formatada à mão.

## 4. Citações no texto (NBR 10520:2023, sistema autor-data)

| Marcação | Resultado |
|---|---|
| `[@page2021]` | (Page et al., 2021) |
| `[@santos2007; @guyatt2008]` | (Santos; Pimenta; Nobre, 2007; Guyatt et al., 2008) |
| `[@page2021, p. 3]` | (Page et al., 2021, p. 3) |
| `@methley2014` | Methley et al. (2014) — citação narrativa |

Use esses marcadores em **todos** os arquivos `.md` e `.json` do pipeline. Até 3 autores
aparecem todos; 4 ou mais viram *et al.* Mesmo autor e ano recebem *a/b* automaticamente.

## 5. Regras de integridade (inegociáveis)

1. **Nada inventado.** Nenhuma referência, autor, ano, DOI, PMID, número ou recomendação
   pode vir da memória. Só cite o que foi **visto em resultado de ferramenta nesta execução**.
2. **Verificação.** `"verificado": true` apenas depois de confirmar os metadados com
   `get_article_metadata`/`lookup_article_by_citation` (ou página oficial do periódico/DOI/órgão).
   Registre em `verificado_via` (ex.: `"PubMed PMID 33782057"`, `"site do Ministério da Saúde"`).
3. **Números rastreáveis.** Toda estimativa (RR, OR, HR, DM, IC 95%, I², prevalência,
   sensibilidade) vem do resumo ou do texto completo acessado; informe a origem
   (`extraído do resumo` / `texto completo PMC`). Se não conseguiu acessar, diga isso.
4. **Separar níveis de certeza.** Distinga *consenso estabelecido*, *evidência clínica*,
   *evidência mecanística/pré-clínica* e *hipótese*. Nunca extrapole de animal/in vitro para clínica sem avisar.
5. **Atualidade.** Hoje é a data do sistema. Para diretrizes, confirme se existe versão mais recente.
   Prefira estudos dos últimos 10 anos, mantendo os clássicos/pivotais quando forem a melhor evidência.
6. **Lacunas declaradas.** Se a evidência é fraca, ausente ou conflitante, escreva isso — não preencha.
7. **Português do Brasil**, terminologia DeCS, medicamentos pela DCB (nome genérico), unidades do SI.

## 6. Hierarquia da evidência usada no pipeline

1. Diretrizes clínicas atuais (nacionais: MS/PCDT/Conitec, sociedades brasileiras; internacionais: OMS, NICE, AHA/ACC, ESC, ADA, KDIGO, USPSTF…)
2. Revisões sistemáticas com metanálise (Cochrane primeiro) e *umbrella reviews*
3. Ensaios clínicos randomizados (grandes, recentes, pivotais)
4. Estudos observacionais (coorte > caso-controle > transversal)
5. Séries/relatos de caso, opinião de especialistas
— Livros-texto e revisões narrativas de alto impacto: base fisiológica/mecanística (Agente 2).

Avaliação crítica: **AMSTAR 2** (revisões), **RoB 2** (ECR), **ROBINS-I/Newcastle-Ottawa** (observacionais),
**AGREE II** (diretrizes), **QUADAS-2** (acurácia diagnóstica). Certeza por desfecho: **GRADE**
(alta · moderada · baixa · muito baixa).

---

## 7. Hierarquia de modelos (quem executa, quem revisa)

| Camada | Modelo | Agentes | Papel |
|---|---|---|---|
| 4 · Auditoria final | **Fable 5.2** (`fable`) | `fps-banca` | Revisa o produto final **e os próprios revisores**; simula a banca |
| 3 · Liderança e revisão | **Opus 5.5** (`opus`) | `fps-lider-pesquisa`, `fps-lider-ciencia`, `fps-lider-producao` | Coordenam os executores da sua fase, revisam, devolvem correções e só entregam o que passou no portão |
| 2 · Execução de conteúdo | **Sonnet 5.5** (`sonnet`) | `fps-1-investigador`, `fps-2-analista-critico`, `fps-3-avaliador-evidencias`, `fps-prescritor-exercicio`, `fps-4-redator-abnt`, `fps-5-designer-slides` | Produzem o conteúdo |
| 1 · Operacional | **Haiku 5.5** (`haiku`) | `fps-op-buscador`, `fps-op-verificador` | Tarefas mecânicas de volume: rodar buscas, triar, conferir metadados |
| 0 · Determinística | — (scripts) | `scripts/*.py` | ABNT, portões, validação, prévias — nada que um código faça melhor fica com um modelo |

Cada camada é revisada pela de cima. As verificações baratas vêm primeiro (**funil de revisão**):
`scripts` → `fps-op-verificador` (Haiku) → autoverificação do executor (Sonnet) → líder (Opus) → banca (Fable).
Assim os modelos caros gastam esforço em **julgamento**, não em conferência mecânica.

## 8. Ciclo de qualidade: produzir → verificar → revisar → corrigir

Arquivos em `<pasta>/revisoes/`:
- `<etapa>.r<N>.parecer.json` — parecer do revisor na rodada N (`python3 trabalho-fps/scripts/parecer.py modelo <etapa>` gera o esqueleto).
- `<etapa>.r<N>.resposta.json` — resposta do executor ao parecer N: `[{"id": "A1", "status": "corrigido|contestado", "detalhe": "..."}]`.

Etapas: `01-investigacao`, `03a-busca`, `03-evidencias`, `02-analise`, `04-prescricao` (caso clínico),
`artigo-forma`, `artigo-fidelidade` (revisão, ou caso clínico com documento), `slides`, `banca`.

**Gravidade dos achados**
- `critica` — erro factual; referência inexistente, errada ou não verificada; número sem fonte ou divergente da fonte; extrapolação indevida; viola norma obrigatória; compromete a resposta à pergunta.
- `maior` — lacuna relevante; análise superficial; desvio do método declarado; redundância significativa; slide ou seção que não cumpre sua função.
- `menor` — estilo, clareza pontual, formatação. **O revisor corrige direto** e registra em `correcoes_aplicadas` (não gasta uma rodada com isso).

**Portão** (`parecer.py avaliar`, determinístico — vale mais que a opinião do revisor):
APROVADO com 0 críticos, 0 maiores, média dos critérios ≥ 7,5 e nenhuma nota < 6.
Senão REVISAR. Na **3ª rodada** sem aprovação → **ESCALAR**: o revisor corrige pessoalmente o que falta,
marca `"escalonado": true` e reavalia.

**Direito de contestação.** O executor pode contestar um achado com evidência (PMID, trecho, norma).
O revisor decide na rodada seguinte e registra a decisão. Revisão é diálogo técnico, não obediência cega.

**Rastreabilidade.** Todo achado `critica`/`maior` traz `evidencia` (o que o revisor conferiu e onde) e
`correcao` acionável. Achados vagos ("melhorar a discussão") são inválidos.

## 9. Modo correção (para executores)

Quando o seu chamado traz um parecer (`revisoes/<etapa>.r<N>.parecer.json`):
1. Leia o parecer inteiro; trate **só** os achados em que `responsavel` é você.
2. Corrija no lugar, sem reescrever o que já foi aprovado e sem introduzir conteúdo novo não pedido.
3. Se discordar, conteste com evidência em vez de "corrigir" para algo errado.
4. Grave `revisoes/<etapa>.r<N>.resposta.json` e confira com
   `python3 trabalho-fps/scripts/parecer.py resposta <resposta> <parecer>`.
5. Devolva em até 5 linhas: quantos corrigidos, quantos contestados e por quê.

## 10. Memória de lições (aprendizado entre trabalhos)

`trabalho-fps/memoria/licoes.md` reúne regras aprendidas com erros reais, por agente.
- **Executores**: leiam a sua seção antes de começar e tratem cada lição como regra.
- **Revisores**: quando um achado revela um padrão que valeria para qualquer tema, preencham `licao`
  (uma regra curta e geral — não cite o tema). O orquestrador consolida ao final com
  `python3 trabalho-fps/scripts/parecer.py licoes <pasta>` (deduplica e mantém as 12 mais frequentes por agente).

## 11. Procedimento dos líderes (Opus) — coordenar e revisar

Para cada etapa sob sua responsabilidade:
1. **Disparar o executor** (ferramenta `Agent`, `subagent_type` = nome do executor) com: caminho da pasta,
   a missão e "leia PROTOCOLO.md e a sua seção de memoria/licoes.md". Etapas independentes → dispare em paralelo.
2. **Funil barato primeiro**: rode os scripts aplicáveis (`validar_trabalho.py`, `previa.py`) e dispare o
   `fps-op-verificador` para os `*referencias.json` da etapa. Leia o relatório antes de revisar.
3. **Revisar com profundidade** (critérios da etapa: `python3 trabalho-fps/scripts/parecer.py modelo <etapa>`):
   leia os arquivos inteiros e **confira por amostragem contra as fontes** (`mcp__PubMed__get_article_metadata`
   para o resumo, página oficial para diretrizes). Priorize números, recomendações, afirmações causais fortes e
   tudo o que vai para os slides.
4. **Gravar o parecer** `revisoes/<etapa>.r<N>.parecer.json`, corrigindo você mesmo os achados `menor`.
5. **Portão**: `python3 trabalho-fps/scripts/parecer.py avaliar <parecer>` →
   - `APROVADO` (0): etapa concluída.
   - `REVISAR` (1): dispare o executor em **modo correção** com o caminho do parecer; ao voltar, rode
     `parecer.py resposta`, decida as contestações e revise a rodada N+1 só sobre os achados e possíveis regressões.
   - `ESCALAR` (3): corrija pessoalmente o que falta, marque `"escalonado": true`, registre e reavalie.
6. Em achados que revelem padrão geral, preencha `licao` (alimenta a memória do pipeline).
7. **Responder ao orquestrador** em até 12 linhas: decisão do portão por etapa, nº de rodadas, o que mudou,
   pendências que dependem do usuário.

Regras: nas rodadas 1–2 não reescreva o trabalho do executor (exceto `menor`) — devolva instruções precisas;
quem erra corrige, e a lição fica registrada. Achado bom: *"03-evidencias.md §4: RR 0,74 (0,65–0,85) diverge do
resumo do PMID 12345678 (RR 0,79; 0,70–0,89) → corrigir no texto e no quadro"*. Achado ruim: *"revisar números"*.

**Fallback (modo plano):** se você não tiver a ferramenta `Agent` (limite de profundidade ou versão do
Claude Code), não execute o trabalho do executor: responda ao orquestrador `MODO PLANO NECESSÁRIO` com a lista
de disparos; ele dispara os executores e chama você de novo apenas para revisar.

## 12. Tipos de trabalho

| Tipo | Linha no `00-briefing.md` | Etapas com portão | Produto principal |
|---|---|---|---|
| Revisão (padrão) | `Tipo de trabalho: revisao` | 01, 03a, 03, 02, artigo-forma, artigo-fidelidade, slides, banca | artigo ABNT + slides |
| Caso clínico | `Tipo de trabalho: caso_clinico` | 01, 03a, 03, 02, **04-prescricao**, slides, banca (+ artigo-* se houver `artigo.json`) | slides + roteiro + prescrição + arguição |

No caso clínico:
- a **rubrica do professor** (`rubrica.json`) orienta a estrutura dos slides e a nota estimada pela banca;
- o raciocínio clínico (biomecânica, testes, compensações) é a missão do Agente 2;
- a prescrição (FITT-VP por fase, critérios de progressão, ajuste por sintomas) é do `fps-prescritor-exercicio`;
- o enunciado do professor é **dado do caso** (não precisa de referência), mas toda interpretação, conduta e
  número fora do enunciado segue as regras de integridade da §5;
- se o enunciado for ambíguo ou internamente inconsistente, isso é registrado e discutido (é material de
  raciocínio clínico), nunca "corrigido" em silêncio.

## 13. Formato do documento escrito

| Formato | Linha no briefing | Estrutura | `config.formato` |
|---|---|---|---|
| Artigo (padrão) | — | NBR 6022: resumo, abstract, palavras-chave, Método, etc. | `artigo` |
| Capítulo de livro | `Formato do documento: capitulo` | Revisão narrativa didática: objetivos, seções temáticas, caixas de pontos-chave/na prática, síntese final; **ABNT só na formatação** | `capitulo` |

No capítulo, os revisores avaliam os mesmos critérios de `artigo-forma` e `artigo-fidelidade`, lendo "estrutura_abnt"
como "formatação ABNT + estrutura de capítulo" (não cobrar resumo, abstract nem Método).
