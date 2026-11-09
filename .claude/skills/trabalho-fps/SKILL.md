---
name: trabalho-fps
description: Orquestra o pipeline de 5 subagentes que produz um trabalho acadêmico completo para a FPS (Faculdade Pernambucana de Saúde) — investigação do tema, análise crítica dos mecanismos, busca da melhor evidência (PICOS, diretrizes, revisões sistemáticas, metanálises, GRADE), artigo científico em .docx no padrão ABNT e apresentação .pptx com logo e cores da FPS. Use quando o usuário pedir um trabalho, seminário, artigo, revisão ou apresentação da faculdade/FPS sobre um tema, ou digitar /trabalho-fps <tema>.
---

# /trabalho-fps — Orquestrador

Você (thread principal) é o **orquestrador**. Os subagentes não conversam entre si nem chamam
outros subagentes: você os dispara na ordem certa, passa a pasta do trabalho, confere cada entrega
e decide se avança. Toda a comunicação entre etapas acontece por **arquivos** (ver
`trabalho-fps/PROTOCOLO.md`).

```
            ┌──────────────────────┐
 briefing ─▶│ 1 fps-1-investigador │  (sonnet · amplitude)
            └──────────┬───────────┘
                       │  ✔ checkpoint: usuário aprova a pergunta PICOS
          ┌────────────┴─────────────┐
          ▼                          ▼          (em paralelo)
┌──────────────────────┐  ┌──────────────────────────────┐
│ 2 fps-2-analista-    │  │ 3 fps-3-pesquisador-         │
│   critico (opus)     │  │   evidencias (opus)          │
└──────────┬───────────┘  └──────────────┬───────────────┘
           └────────────┬────────────────┘
                        ▼
            ┌──────────────────────┐
            │ 4 fps-4-redator-abnt │  (opus · artigo.docx ABNT)
            └──────────┬───────────┘
                       ▼
            ┌──────────────────────┐
            │ 5 fps-5-designer-    │  (sonnet · apresentacao.pptx FPS)
            │   slides             │
            └──────────┬───────────┘
                       ▼
             validar_trabalho.py → entrega
```

## Passo 0 — Briefing
Colete (do pedido do usuário; pergunte **só o que faltar e for essencial**, numa única pergunta):
- **Tema** (obrigatório) e, se houver, a pergunta/recorte que o professor deu.
- Curso e período; disciplina/módulo/tutoria.
- Nomes dos autores (e e-mails para a nota de rodapé); professor(a)/tutor(a).
- Tempo de apresentação (padrão: 15 min).
- Exigências do professor: nº de páginas, fonte (Arial/Times), capa, norma diferente, seções obrigatórias.
- Modo: **com checkpoint** (padrão) ou **automático** (sem parar para aprovar a pergunta PICOS).

Padrões quando o usuário não informar: Arial 12, sem capa, artigo de revisão de 8–14 páginas,
15 min de apresentação, citação NBR 10520:2023, cidade Recife.

Crie a pasta `trabalho-fps/trabalhos/<AAAA-MM-DD>-<slug-do-tema>/` e escreva `00-briefing.md`
com tudo acima (inclua a data de hoje).

**Logo:** se `trabalho-fps/marca/logo-fps.png` não existir, peça ao usuário o arquivo do logo oficial
(PNG, de preferência com fundo transparente) e siga sem bloquear — o pipeline continua com marcador de texto.
Quando o logo chegar: salve em `trabalho-fps/marca/logo-fps.png` e rode
`python3 trabalho-fps/scripts/extrair_cores_logo.py trabalho-fps/marca/logo-fps.png --salvar --gerar-negativo`.

## Passo 1 — Investigação
Dispare `fps-1-investigador` com: caminho da pasta do trabalho + "leia PROTOCOLO.md e 00-briefing.md".
Ao retornar, confira que existem `01-investigacao.md`, `01-picos.json` e `01-referencias.json`.

**Checkpoint (modo padrão):** mostre ao usuário, em poucas linhas, a pergunta estruturada (P, I, C, O, S),
os desfechos primários e os subtemas essenciais, e pergunte se aprova ou quer ajustar o recorte.
Ajustes → edite `01-picos.json`/`00-briefing.md` (ou redispare o agente 1 com a correção).

## Passo 2 — Análise crítica ∥ Evidências
Dispare **na mesma mensagem** (paralelo) `fps-2-analista-critico` e `fps-3-pesquisador-evidencias`,
cada um com o caminho da pasta. Ao retornar, confira os arquivos `02-*` e `03-*` e leia as
*Pendências para o orquestrador*. Se o agente 3 encontrou pouca evidência ou mudou o entendimento da
pergunta, informe o usuário antes de seguir.

## Passo 3 — Artigo ABNT
Dispare `fps-4-redator-abnt` com o caminho da pasta. Confira que `artigo.docx` existe e que o
validador não acusa erros. Abra 1–2 páginas da prévia (`previa-artigo/`) para conferência rápida.

## Passo 4 — Apresentação FPS
Dispare `fps-5-designer-slides` com o caminho da pasta. Confira `apresentacao.pptx` e olhe a
`previa-apresentacao/folha-de-contato.png`.

## Passo 5 — Validação e entrega
1. `python3 trabalho-fps/scripts/validar_trabalho.py <pasta>` → precisa terminar **sem erros**.
   Erro remanescente → devolva ao agente responsável com a mensagem exata (no máximo 2 rodadas).
2. Entregue ao usuário (curto e objetivo):
   - caminhos de `artigo.docx` e `apresentacao.pptx` (envie os arquivos se a ferramenta existir);
   - a pergunta PICOS e a resposta em 2–3 linhas, com a certeza GRADE;
   - nº de referências (todas verificadas), nº de slides × tempo;
   - avisos que exigem ação humana (logo ausente, acesso a texto completo, exigências não atendidas).
3. Lembre o usuário de **ler e revisar** o conteúdo antes de entregar e de seguir a política da FPS/do
   professor sobre uso de IA (declarar, se exigido).
4. Se a pasta estiver num repositório git, ofereça commit dos arquivos do trabalho.

## Regras do orquestrador
- Não escreva o conteúdo das etapas você mesmo; seu papel é coordenar, conferir e decidir.
- Não pule etapas nem o validador. Não avance com arquivo ausente ou referência não verificada.
- Mantenha o usuário informado com uma linha por etapa concluída.
- Reexecução parcial: o usuário pode pedir "refaça só os slides" ou "atualize as evidências" —
  dispare apenas os agentes afetados e os posteriores que dependem deles.
