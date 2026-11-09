# Trabalhos FPS — equipe hierárquica de agentes

Pipeline para produzir trabalhos acadêmicos da **FPS (Faculdade Pernambucana de Saúde)**:
do tema bruto ao **artigo científico ABNT (.docx)** e à **apresentação com a identidade da FPS (.pptx)**,
com evidência rastreável e verificada — produzido por modelos mais básicos e **revisado por modelos mais
inteligentes**, camada por camada.

## Como usar

No Claude Code, a partir da raiz do repositório:

```
/trabalho-fps <tema>
```

ou em linguagem natural: *"Faça meu trabalho da FPS sobre <tema>, curso de Medicina, 15 min de apresentação"*.
O orquestrador pergunta só o que faltar, para uma vez para você aprovar a pergunta PICOS e entrega
`artigo.docx`, `apresentacao.pptx` e `banca.md` em `trabalho-fps/trabalhos/<data>-<tema>/`.

## A equipe

```
CAMADA 4 · Fable 5.2   fps-banca ................. audita o produto final E os revisores; prepara a arguição
                          ▲ pareceres
CAMADA 3 · Opus 5.5    fps-lider-pesquisa · fps-lider-ciencia · fps-lider-producao
  (coordenam+revisam)     │ disparam executores, revisam, devolvem correções, só entregam o aprovado
CAMADA 2 · Sonnet 5.5  fps-1-investigador · fps-2-analista-critico · fps-3-avaliador-evidencias
  (produzem)              fps-prescritor-exercicio · fps-4-redator-abnt · fps-5-designer-slides
CAMADA 1 · Haiku 5.5   fps-op-buscador · fps-op-verificador ..... volume e conferência mecânica
CAMADA 0 · scripts     ABNT · portões (parecer.py) · conferência de referências · validador · prévias
```

| Líder (Opus) | Coordena e revisa | Etapas (portões) |
|---|---|---|
| `fps-lider-pesquisa` | investigador (Sonnet), buscador (Haiku), avaliador de evidências (Sonnet) | `01-investigacao`, `03a-busca`, `03-evidencias` |
| `fps-lider-ciencia` | analista crítico (Sonnet); prescritor de exercício (Sonnet, casos clínicos); fidelidade científica do artigo | `02-analise`, `04-prescricao`, `artigo-fidelidade` |
| `fps-lider-producao` | redator ABNT (Sonnet), designer de slides (Sonnet) | `artigo-forma`, `slides` |
| `fps-banca` (Fable) | tudo, inclusive os pareceres dos líderes | `banca` |

O verificador (Haiku) é chamado por todos os líderes antes de cada revisão.

### Tipos de trabalho

- **Revisão** (padrão): artigo ABNT + slides + banca.
- **Caso clínico**: o enunciado e a rubrica do professor entram no briefing; a equipe produz o raciocínio clínico,
  a **prescrição FITT-VP em fases** com critérios de progressão e o **semáforo de ajuste por sintomas**, os slides
  com **apresentador e tempo por slide**, o `roteiro.md` por integrante e a **nota estimada pela rubrica do
  professor**, com banco de arguição. Documento escrito só se exigido.
  Exemplo em andamento: [`trabalhos/2026-11-09-caso04-lca-lcm/`](trabalhos/2026-11-09-caso04-lca-lcm/PLANO.md).

### Fluxo

1. **Investigação** — líder de pesquisa → investigador → verificador → revisão → ✔ você aprova a pergunta PICOS
2. **Ciência ∥ Evidências** (em paralelo) — líder de ciência → analista crítico; líder de pesquisa → buscador → avaliador
3. **Artigo** — líder de produção → redator (forma ABNT) → líder de ciência confere a fidelidade científica
4. **Slides** — líder de produção → designer
5. **Banca** (Fable) — auditoria independente, nota estimada, 10 perguntas prováveis da arguição com respostas-modelo
6. **Fechamento** — validador final, painel de qualidade e consolidação das lições

### Como as camadas trabalham juntas

- **Funil de revisão**: scripts → verificador Haiku → autoverificação Sonnet → líder Opus → banca Fable.
  O que é mecânico fica com código e com o Haiku; os modelos caros gastam esforço em julgamento.
- **Pareceres estruturados** (`revisoes/<etapa>.r<N>.parecer.json`): notas por critério e achados com gravidade
  (`critica`/`maior`/`menor`), local, evidência conferida, correção e responsável.
- **Portão determinístico** (`scripts/parecer.py avaliar`): aprova só com 0 críticos, 0 maiores, média ≥ 7,5 e
  nenhuma nota < 6 — vale mais que a opinião do revisor. Na 3ª rodada sem aprovação → **escalonamento**: o líder
  corrige pessoalmente.
- **Diálogo, não obediência**: o executor pode contestar um achado com evidência; o revisor decide na rodada seguinte.
- **Memória de lições** (`memoria/licoes.md`): achados que revelam padrões viram regras por agente, lidas antes de
  cada trabalho. A banca também registra lições para os líderes — a equipe inteira aprende.
- **Painel** (`painel.md`): status, rodadas e notas de todas as etapas.

Para trocar o modelo ou o esforço de um agente, edite `model:` e `effort:` em `.claude/agents/fps-*.md`
(`haiku`, `sonnet`, `opus`, `fable` ou `inherit`). Se o Fable não estiver disponível, o orquestrador roda a
banca no Opus e avisa.

## Primeira configuração: logo da FPS

Copie o logo oficial para `trabalho-fps/marca/logo-fps.png` e rode:

```bash
cd trabalho-fps
python3 scripts/extrair_cores_logo.py marca/logo-fps.png --salvar --gerar-negativo
```

Detalhes em [marca/LEIA-ME.md](marca/LEIA-ME.md). Sem o logo, tudo funciona com marcador de texto e a paleta verde
provisória (estimada das fotos dos slides da disciplina).

## Garantias embutidas

- **Referências reais e verificadas**: cada obra precisa de `"verificado": true`, confirmada no PubMed/site oficial
  durante a execução; o validador reprova referência não verificada e citação sem referência.
- **ABNT automática**: referências (NBR 6023:2018) e citações autor-data (NBR 10520:2023) formatadas pelo código.
- **Formatação NBR 14724/6022/6024/6028**: A4; margens 3/3/2/2 cm; fonte 12 (10 em citações longas, notas,
  legendas e fontes); entrelinha 1,5; recuo 1,25 cm; seções numeradas; resumo/abstract; notas de rodapé reais;
  quadro × tabela (IBGE); paginação; referências em espaço simples.
- **Slides sem redundância**: avisos para mais de 5 tópicos, tópicos longos, conteúdo repetido, dado sem fonte, slide sem notas.
- **Revisão visual**: líderes e executores olham o .docx/.pptx renderizado em PNG antes de aprovar.

## Scripts

| Script | Função |
|---|---|
| `scripts/gerar_docx_abnt.py artigo.json` | Gera o artigo .docx ABNT |
| `scripts/gerar_slides_fps.py slides.json` | Gera a apresentação .pptx FPS (17 layouts, incl. `fases`, `fitt`, `semaforo`) e o `roteiro.md` por integrante |
| `scripts/parecer.py modelo\|avaliar\|resposta\|painel\|licoes` | Pareceres, portões de qualidade, painel e memória de lições |
| `scripts/conferir_referencias.py` | Confere referências contra metadados do PubMed (`--pendentes` prepara as buscas de PMID) |
| `scripts/mesclar_referencias.py saida.json a.json b.json` | Une e deduplica referências (DOI/PMID/título) |
| `scripts/validar_trabalho.py <pasta> [--final]` | Validação → `validacao.md` (`--final` exige todos os portões aprovados e a banca) |
| `scripts/previa.py arquivo.docx\|pptx` | Renderiza em PNG + folha de contato |
| `scripts/extrair_cores_logo.py logo.png` | Paleta da marca a partir do logo |

Contratos de arquivos, formato de referências, regras de integridade e o ciclo de revisão estão em
[PROTOCOLO.md](PROTOCOLO.md). Modelos de entrada em [modelos/](modelos/).

Requisitos: Python 3.10+, `python-docx`, `python-pptx`, `Pillow`; para prévias, LibreOffice e `pdftoppm`.

## Uso responsável

O pipeline acelera pesquisa, organização e formatação, mas **o trabalho é seu**: leia tudo, confira as referências
principais, ajuste ao que o professor pediu e siga a política da FPS sobre uso de IA (declare o uso, se exigido).
