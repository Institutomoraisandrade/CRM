# Trabalhos FPS — agente orquestrador + 5 subagentes

Pipeline para produzir trabalhos acadêmicos da **FPS (Faculdade Pernambucana de Saúde)**:
do tema bruto ao **artigo científico ABNT (.docx)** e à **apresentação com a identidade da FPS (.pptx)**,
com evidência rastreável e verificada.

## Como usar

No Claude Code, a partir da raiz do repositório:

```
/trabalho-fps <tema>
```

ou em linguagem natural: *"Faça meu trabalho da FPS sobre <tema>, curso de Medicina, 15 min de apresentação"*.
O orquestrador pergunta só o que faltar (autores, curso, exigências do professor), roda as etapas,
para uma vez para você aprovar a pergunta PICOS e entrega os arquivos em
`trabalho-fps/trabalhos/<data>-<tema>/`.

## Os 5 subagentes

| # | Subagente | Nível · modelo | O que faz | Entrega |
|---|---|---|---|---|
| 1 | `fps-1-investigador` | exploratório · sonnet | Delimita o tema, epidemiologia Brasil/mundo, subtemas, controvérsias; formula a pergunta **PICOS** (ou PECOS/PIRD/PICo) com descritores DeCS/MeSH e strings de busca testadas | `01-investigacao.md`, `01-picos.json`, `01-referencias.json` |
| 2 | `fps-2-analista-critico` | alto · opus | Explica **como o processo ocorre**, passo a passo (molecular → celular → orgânico → clínico), detalhes específicos, consenso × evidência × hipótese, mecanismo × desfecho clínico | `02-analise-critica.md`, `02-referencias.json` |
| 3 | `fps-3-pesquisador-evidencias` | máximo · opus | Busca em camadas: **diretrizes → revisões sistemáticas/metanálises → ECR**; extrai efeitos com IC 95%; avalia com **AMSTAR 2, RoB 2, AGREE II**; certeza **GRADE** por desfecho | `03-evidencias.md`, `03-referencias.json`, `03-quadro-evidencias.json` |
| 4 | `fps-4-redator-abnt` | alto · opus | Escreve o artigo de revisão (NBR 6022) integrando 1–3, gera o .docx ABNT, confere a prévia e roda o validador | `artigo.json` → `artigo.docx` |
| 5 | `fps-5-designer-slides` | médio · sonnet | Condensa o artigo em slides FPS: uma ideia por slide, título-mensagem, fonte em todo dado, roteiro nas notas | `slides.json` → `apresentacao.pptx` |

As etapas 2 e 3 rodam **em paralelo**. Os agentes se comunicam por arquivos com contratos fixos
([PROTOCOLO.md](PROTOCOLO.md)). Para mudar o modelo de um agente, edite o campo `model:` em
`.claude/agents/fps-*.md` (`sonnet`, `opus`, `haiku` ou `inherit`).

## Primeira configuração: logo da FPS

Copie o logo oficial para `trabalho-fps/marca/logo-fps.png` e rode:

```bash
cd trabalho-fps
python3 scripts/extrair_cores_logo.py marca/logo-fps.png --salvar --gerar-negativo
```

Detalhes em [marca/LEIA-ME.md](marca/LEIA-ME.md). Sem o logo, tudo funciona com marcador de texto e
paleta provisória.

## Garantias embutidas

- **Referências reais e verificadas**: cada obra precisa de `"verificado": true` (confirmada no PubMed/DOI/site
  oficial durante a execução); o validador reprova referência não verificada e citação sem referência.
- **ABNT automática**: referências (NBR 6023:2018) e citações autor-data (NBR 10520:2023) são formatadas
  pelo código, não à mão — o texto usa marcadores `[@id]`.
- **Formatação NBR 14724/6022/6024/6028**: A4; margens 3/3/2/2 cm; fonte 12 (10 em citações longas, notas,
  legendas e fontes); entrelinha 1,5; recuo 1,25 cm; títulos numerados e diferenciados por nível;
  resumo e abstract com palavras-chave; notas de rodapé reais; quadro (fechado) × tabela (aberta, IBGE);
  paginação no canto superior direito; referências em espaço simples, alinhadas à esquerda.
- **Slides sem redundância**: o gerador avisa sobre mais de 5 tópicos, tópicos longos, conteúdo repetido
  entre slides, slide de dados sem fonte e slide sem notas.
- **Revisão visual**: os agentes renderizam o .docx/.pptx em PNG e olham o resultado antes de entregar.

## Scripts (também podem ser usados à mão)

| Script | Função |
|---|---|
| `scripts/gerar_docx_abnt.py artigo.json` | Gera o artigo .docx ABNT |
| `scripts/gerar_slides_fps.py slides.json` | Gera a apresentação .pptx FPS (14 layouts) |
| `scripts/mesclar_referencias.py saida.json a.json b.json` | Une e deduplica referências (DOI/PMID/título) |
| `scripts/validar_trabalho.py <pasta>` | Validação final → `validacao.md` |
| `scripts/previa.py arquivo.docx\|pptx` | Renderiza em PNG + folha de contato |
| `scripts/extrair_cores_logo.py logo.png` | Paleta da marca a partir do logo |

Modelos de entrada: [modelos/artigo.exemplo.json](modelos/artigo.exemplo.json),
[modelos/slides.exemplo.json](modelos/slides.exemplo.json),
[modelos/referencias.exemplo.json](modelos/referencias.exemplo.json).

Layouts de slide: `capa`, `secao`, `topicos` (com `destaque` ou `imagem` opcionais), `dois_colunas`, `fluxo`,
`numeros`, `tabela`, `picos`, `evidencias`, `mensagem`, `conclusao`, `imagem`, `referencias`, `encerramento`.

Opções do artigo (`config` em `artigo.json`): `fonte` (`Arial`/`Times New Roman`), `capa` (`true`/`false`),
`estilo_citacao` (`2023` → *(Silva, 2020)* | `2002` → *(SILVA, 2020)*), `autores_referencia`
(`et_al`/`todos`), `destaque` (`negrito`/`italico`), `abstract`, `cidade`.

Requisitos: Python 3.10+, `python-docx`, `python-pptx`, `Pillow`; para prévias, LibreOffice e `pdftoppm`.

## Uso responsável

O pipeline acelera pesquisa, organização e formatação, mas **o trabalho é seu**: leia tudo, confira as
referências principais, ajuste ao que o professor pediu e siga a política da FPS sobre uso de IA
(declare o uso, se exigido).
