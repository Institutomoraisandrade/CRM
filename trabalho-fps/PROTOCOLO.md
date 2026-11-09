# Protocolo comum dos subagentes — Trabalhos FPS

Documento de referência **obrigatório** para todos os subagentes `fps-*`.
Define pastas, contratos de arquivos, formato de referências e regras de integridade.
Cada subagente lê este arquivo antes de começar.

---

## 1. Pasta de cada trabalho

```
trabalho-fps/trabalhos/<AAAA-MM-DD>-<slug-do-tema>/
├── 00-briefing.md              ← orquestrador (tema, curso, autores, exigências do professor)
├── 01-investigacao.md          ← Agente 1 · Investigador
├── 01-picos.json               ← Agente 1 · pergunta estruturada + estratégias de busca
├── 01-referencias.json         ← Agente 1 · definição, classificação, epidemiologia
├── 02-analise-critica.md       ← Agente 2 · Analista crítico (mecanismos e processos)
├── 02-referencias.json         ← Agente 2
├── 03-evidencias.md            ← Agente 3 · Pesquisador de evidências (PICOS + GRADE)
├── 03-referencias.json         ← Agente 3
├── 03-quadro-evidencias.json   ← Agente 3 · dados estruturados dos estudos incluídos
├── referencias.json            ← Agente 4 · mescla de 01 + 02 + 03 (scripts/mesclar_referencias.py)
├── artigo.json  → artigo.docx  ← Agente 4 · Redator ABNT
├── slides.json  → apresentacao.pptx ← Agente 5 · Designer de slides
├── previa-artigo/ previa-apresentacao/  ← PNGs de revisão visual
└── validacao.md                ← scripts/validar_trabalho.py
```

Cada agente **lê** os arquivos das etapas anteriores e **escreve apenas os seus**.
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
