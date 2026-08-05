# CLAUDE.md

Orientações para assistentes de IA (Claude Code e afins) que trabalham neste repositório.

## 1. Leia isto primeiro: não existe código aqui

Este repositório **não contém código-fonte**. Hoje ele é um repositório de
**especificação e material de referência** para um produto de CRM. O conteúdo
completo é:

```
CRM/
├── README.md                                    # 2 linhas: "artigos, artes e ideias relacionadas ao meu projeto"
├── CLAUDE.md                                    # este arquivo
└── que meu paciente ele tenha a possibilidade   # quadro de requisitos (PNG 1920x1080)
    de personalizar seu perfil informando os
    seguintes dados.png
```

Não há `package.json`, `requirements.txt`, build, testes, linter, CI ou
qualquer configuração de projeto. Consequências práticas:

- **Não invente comandos de build/test/lint.** Se for pedido "rode os testes"
  ou "faça o build", a resposta correta é que ainda não existe nada para rodar.
- **Não presuma stack.** Nenhuma linguagem, framework ou banco foi escolhido
  neste repositório. Se a escolha for necessária para a tarefa, pergunte ou
  proponha explicitamente como decisão nova — não trate como fato existente.
- **Não deduza arquitetura a partir dos mockups.** As telas do PNG são de um
  app já existente usado como referência visual, não deste repositório.

## 2. Contexto do produto

O dono do repositório é o Instituto Morais Andrade (IMA) — atuação em
nutrição, treino e performance esportiva. O produto especificado é um **CRM
clínico**: gestão de pacientes, planos de acompanhamento, lembretes de
consulta e captação de leads. Os mockups do PNG mostram um app de tema escuro
(verde-esmeralda sobre preto) chamado **Wellto**, usado como base visual e
funcional — a frase final do quadro é "Eu preciso que você coloque esse
sistema dentro do meu aplicativo".

Todo o material do dono é escrito em **português do Brasil**. Ver seção 5.

## 3. A especificação (transcrita do PNG)

O PNG é a única fonte de requisitos do repositório. Ele foi transcrito abaixo
para que não seja necessário reprocessar a imagem a cada sessão. Se a imagem
for atualizada ou substituída, **atualize esta seção junto**.

### 3.1 Perfil do profissional

O profissional personaliza seu perfil informando:

- E-mail
- WhatsApp
- Nome de usuário
- Especialidade

O mockup mostra ainda: nome completo, área de atuação, nº de conselho
(ex.: CRN) e foto. Deve ser possível **adicionar colaboradores** da equipe
(dois ou mais profissionais), com uma tabela de colaboradores contendo nome,
e-mail, permissões, data de adição e ações.

### 3.2 Notificações e ciclo de acompanhamento

Duas regras distintas foram pedidas:

**a) Lembrete de retorno de consulta.** Cada consulta é registrada. A cada
15 dias contados do dia da consulta o sistema lembra o profissional — um
lembrete por volta dos 15 dias e outro 15 dias depois (completando 30 dias
desde a última consulta).

**b) Aviso de vencimento de plano.** O profissional deve ser notificado
quando o plano está perto de vencer. A lógica descrita:

> Plano selecionado → tempo determinado (ex.: 30 / 90 / 180 / 360 dias) →
> **7 dias antes** do prazo do plano, o profissional é notificado **e o
> paciente também**.

A mensagem deve chegar **tanto no WhatsApp quanto dentro do sistema**.
Observação explícita do dono: *"Ainda será colocada a API do WhatsApp, porém
ainda só deixar o sistema engatilhado"* — ou seja, construir o gatilho e o
ponto de integração agora, sem depender de uma API de WhatsApp já conectada.

> ⚠️ **Ambiguidade conhecida.** O texto original mistura "a cada 15 dias" com
> "completar 30 dias da última consulta", e não deixa claro se o ciclo de
> lembretes se repete indefinidamente ou apenas duas vezes por consulta.
> Confirme com o dono antes de implementar; não escolha silenciosamente.

### 3.3 Cadastro de paciente

Campos que devem existir quando o paciente for cadastrado:

- **Nome**
- **Plano selecionado**
- **Data em que ele finaliza o plano**
- **Dias restantes para finalizar o plano, a partir de 7 dias.** Regra da TAG:
  até faltarem 7 dias, mantém a TAG "ativo"; ao chegar em 7 dias, troca para
  uma TAG do tipo "vence em N dias" (N = dias que faltam). Vale para **todos
  os tipos de plano**.
- **Status / vigência**
- **Etiquetas**, configuráveis pelo profissional — cada um escolhe as
  etiquetas que mais se identificam com sua identidade.

### 3.4 Busca e listagem de pacientes

A busca deve permitir procurar por:

- Nome
- Tipo de plano (com possibilidade de cadastrar novos tipos)
- Tipo de cliente: **Ativos**, **Pausados**, **Inativos**
- Paginação com **10, 50, 100 e 150** pacientes por vez na lista

A listagem no mockup ("Clientes Ativos") tem colunas: Nome, Plano, Status do
plano, Etiquetas, Cadastrado, Status, Ações — com busca livre, filtro de
plano, filtro de tipo de cliente, seletor de quantidade, importar/exportar e
botão de adicionar.

### 3.5 Cadastro de leads (painel + formulário)

O sistema de leads deve ser embutido no aplicativo do dono. O painel mostra
abas (Leads / Jornada), cartões de KPI — **Total de Leads, Leads Ativos, Taxa
de Conversão, Leads Quentes** — e gráficos de funil e de progresso no período.

O formulário "Adicionar Lead" tem:

| Campo | Obrigatoriedade | Observações |
|---|---|---|
| Nome | obrigatório | |
| WhatsApp | opcional | prefixo +55; aviso "digite o número exatamente como aparece no WhatsApp" |
| E-mail | opcional | |
| Temperatura | seleção única | Frio / Neutro / Quente (padrão: Neutro) |
| Responsável | atribuição | botão "Atribuir" |
| Canal de aquisição | opcional | ex.: WhatsApp |
| Notas | opcional | texto livre |

## 4. Fluxo de trabalho com git

- **Branch de desenvolvimento:** `claude/claude-md-documentation-lvsyef`.
  Trabalhe e faça push apenas nela, a menos que o dono autorize outra.
  `main` é a branch padrão e não recebe push direto.
- **Push:** `git push -u origin <branch>`. Em falha de rede, tente novamente
  com backoff (2s, 4s, 8s, 16s).
- **Pull requests:** só crie quando explicitamente pedido.
- **Mensagens de commit:** curtas e descritivas. O histórico atual é mínimo
  (`Initial commit`, `Add files via upload`) — não é um padrão a seguir.
- Não há hooks, CI ou verificação automática. Nada roda sozinho no push.

## 5. Convenções

- **Idioma: português do Brasil.** README, requisitos, nomes de arquivo e a
  comunicação do dono são em pt-BR. Responda em português. Documentação e
  strings de interface voltadas ao usuário devem ser em pt-BR; identificadores
  de código podem ser em inglês, mas **preserve os termos de domínio** —
  `paciente`, `plano`, `etiqueta`, `lead`, `temperatura`, `vigência` são
  vocabulário do produto, não sinônimos livres de "customer", "subscription"
  ou "tag".
- **Nomes de arquivo descritivos e longos são intencionais.** O PNG se chama
  pelo próprio enunciado do requisito. Não renomeie nem "organize" arquivos
  do dono sem pedido — inclusive porque o nome carrega informação.
- **Formatos de domínio brasileiros:** telefone com DDI +55, conselho
  profissional (CRN), datas em `dd/mm/aaaa`, moeda em BRL.
- **Identidade visual:** tema escuro, fundo quase preto com verde-esmeralda
  como cor de destaque, cantos arredondados, badges/TAGs coloridas por status.

## 6. Dados pessoais

O PNG contém dados reais do dono (e-mail, telefone, nº de conselho) e de pelo
menos um colaborador. **Não transcreva esses valores** em código, commits,
issues, PRs, documentação ou artefatos publicados. Ao precisar de exemplos,
use dados fictícios (`joao@exemplo.com`, `+55 (11) 90000-0000`).

## 7. Quando o código chegar

Este arquivo descreve um repositório vazio de código. Assim que a
implementação começar, **atualize o CLAUDE.md na mesma mudança**, com:

1. A stack efetivamente escolhida e por quê.
2. A estrutura de diretórios real.
3. Os comandos concretos de instalação, execução, teste e lint.
4. O modelo de dados (paciente, plano, consulta, etiqueta, lead, colaborador).
5. Como o gatilho de notificação é disparado (agendador, cron, fila) e onde
   fica o ponto de integração do WhatsApp ainda não conectado.

Até lá, mantenha a seção 3 sincronizada com o PNG: ele é a especificação, e
esta transcrição é apenas uma conveniência — em caso de divergência, **a
imagem é a fonte da verdade**.
