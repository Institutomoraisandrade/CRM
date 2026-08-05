# Agente de agendamento de pacientes

Agente que roda **na sua máquina**, lê os planos dos seus pacientes
exportados do LiveClin e marca os retornos **sempre dentro do limite de 30
dias** desde a última consulta — nunca depois disso, e nunca depois do fim
da vigência do plano.

Também prepara os avisos de check-in de 15 dias e de fim de plano com 7
dias de antecedência.

---

## Antes de começar: duas limitações honestas

**1. O LiveClin não tem API pública.** Não existe hoje um jeito oficial de
o agente entrar na sua conta do LiveClin e ler os pacientes sozinho. A
origem é sempre a planilha — mas ela pode vir de dois lugares:

- **Google Sheets**, lido direto do seu Drive por OAuth. Você mantém a
  planilha lá e o agente lê sozinho a cada rodada.
- **Arquivo CSV/XLSX** exportado para a sua máquina.

O Sheets é o caminho recomendado: sem exportação manual a cada rodada. Em
nenhum dos dois o agente pede a sua senha.

Se o LiveClin abrir uma API no futuro, só a pasta `agente/fontes/` precisa
mudar — o resto do agente continua igual.

**2. Os pacientes não recebem nada automaticamente.** Os textos de
WhatsApp são montados e gravados em `notificacoes.json`, prontos para
envio, mas o disparo não acontece: falta plugar uma API de WhatsApp. O
sistema fica "engatilhado", como combinado.

O **relatório para você** é diferente: esse sai por e-mail e funciona
hoje (veja "Relatório por e-mail" abaixo).

---

## Instalação

Você precisa de Python 3.11 ou mais novo. Para conferir:

```bash
python3 --version
```

Depois, dentro da pasta do projeto:

```bash
cp config.exemplo.toml config.toml
```

Não há nada para instalar: o agente usa só a biblioteca padrão do Python.

Duas coisas são opcionais:

```bash
pip install openpyxl                     # se preferir exportar .xlsx em vez de .csv
pip install -r requirements-google.txt   # se quiser escrever no Google Calendar
```

## Configuração

Abra o `config.toml` e ajuste:

- `fonte.caminho` — onde está a planilha exportada do LiveClin.
- `agenda.horarios` e `agenda.dias_semana` — quando você atende.
- `agenda.duracao_min` — quanto dura cada consulta.
- `planos` — a duração de cada plano que você vende.

O arquivo tem comentários explicando cada campo.

### Ler direto do Google Sheets

Se a planilha já vive no seu Drive, o agente lê de lá — sem exportar nada
a cada rodada:

```toml
[fonte]
tipo = "google_sheets"
spreadsheet_id = "147iQO95aYNytsVdo3j7EFO0oHbGQv4ZSxkdrt9m7Dxw"
aba = "Pacientes - Daniel"
```

O `spreadsheet_id` é o trecho da URL entre `/d/` e `/edit`:

```
docs.google.com/spreadsheets/d/ESTE_PEDACO_AQUI/edit
```

Usa o mesmo `credentials.json` do Google Calendar, com permissão apenas
de **leitura**. Na primeira execução o navegador abre para você
autorizar; o token fica em `token_sheets.json`, na sua máquina.

A mesma configuração vale para a seção `[webdiet]`.

**O agente nunca pede a senha da sua conta Google.** Se algum dia
precisar dela para alguma coisa, é sinal de que algo está errado.

### A planilha do LiveClin

Exportando para arquivo, o agente reconhece sozinho os cabeçalhos mais
comuns:

| Campo | Cabeçalhos aceitos |
|---|---|
| Nome | Nome, Paciente, Nome do paciente |
| Plano | Plano, Plano selecionado, Tipo de plano |
| Início | Data início, Início do plano, Data de contratação |
| Fim | Vencimento, Fim do plano, Validade, Vigência |
| Última consulta | Última consulta, Último atendimento |
| Status | Status, Situação, Tipo de cliente |
| WhatsApp | WhatsApp, Telefone, Celular |
| Etiquetas | Etiquetas, Tags, Marcadores |

Só o **nome** e o **plano** são obrigatórios, mais uma das duas datas
(início ou fim). Se a sua exportação usar outros nomes de coluna, é só
preencher a seção `[fonte.colunas]` do `config.toml`.

Tem um exemplo pronto em `exemplos/pacientes_liveclin.csv`.

### Formatos de plano reconhecidos

O LiveClin escreve o plano de mais de um jeito. Todos estes funcionam:

| Na planilha | Vira |
|---|---|
| `Trimestral` | trimestral, 90 dias |
| `Dieta (3 Meses) - Presencial` | trimestral, 90 dias |
| `Treino (1 Mes) - Online` | mensal, 30 dias |
| `Parceria` | parceria, 90 dias |

Quando existe uma coluna **Duração (dias)**, é ela que manda — o texto do
plano vira só o rótulo. Se os dois discordarem (plano "Trimestral" com
duração 45), o agente usa a duração e avisa da divergência.

Duração fora do catálogo vira um plano sob medida em vez de a linha ser
descartada.

### Cuidado com a coluna de status

Nem toda coluna chamada "Status" fala do paciente. Em planilhas de
cadastro, "Status LiveClin" costuma dizer se o paciente já existe no
sistema (`EXISTENTE (Inativo)`, `Verificar`) — não se o plano está ativo.

Quando o agente não reconhece o valor, ele trata como ativo **e avisa**,
em vez de assumir em silêncio. Assumir "ativo" calado colocaria na fila
de agendamento alguém que já encerrou.

## Como usar

Os quatro comandos, na ordem em que fazem sentido:

```bash
python3 -m agente verificar    # confere a planilha e mostra os planos
python3 -m agente planejar     # calcula os retornos, sem tocar na agenda
python3 -m agente aplicar --confirmar   # cria as consultas de verdade
python3 -m agente alertas      # lista os avisos do dia
python3 -m agente relatorio --enviar    # manda o resumo do dia no seu e-mail
```

O `planejar` nunca escreve na agenda — use à vontade. O `aplicar` só
escreve quando você passa `--confirmar`; sem a flag ele apenas mostra o
que faria.

Exemplo de saída do `planejar`:

```
PACIENTE                      RETORNO             LIMITE 30D    SITUAÇÃO
Gisele Prado                  —                   20/07/2026    plano_vencido
      plano venceu em 20/07/2026; renove antes de marcar o retorno
Carla Nunes                   06/08/2026 14:00    25/07/2026    atrasado
      42 dias desde 25/06/2026; limite era 25/07/2026
Ana Souza                     14/08/2026 17:00    14/08/2026    agendavel
      30 dias desde 15/07/2026
```

### O que cada situação quer dizer

| Situação | Significado |
|---|---|
| `agendavel` | Retorno marcado dentro dos 30 dias. |
| `atrasado` | Já passou dos 30 dias; o agente encaixou o quanto antes. |
| `ja_agendado` | O paciente já tem consulta futura na agenda; nada foi criado. |
| `sem_vaga` | Não havia horário livre antes do limite. Abra mais horários. |
| `plano_vencido` | O plano acabou. Renove antes de marcar. |

Rodar o agente duas vezes não duplica consulta: ele reconhece quem já
está marcado.

## Como as datas são calculadas

- **Limite de retorno** = a *menor* data entre `última consulta + 30 dias`
  e o fim da vigência do plano. Sem última consulta registrada, a contagem
  parte do início do plano.
- **Escolha do horário**: por padrão o agente procura o horário livre mais
  próximo do limite, para manter o intervalo mensal cheio, dentro dos 7
  dias que antecedem o limite. Trocando `agenda.preferencia` para
  `mais_cedo`, ele antecipa sempre que houver vaga.
- **Check-in** = última consulta + 15 dias.
- **Aviso de fim de plano** = 7 dias antes do vencimento, para você e para
  o paciente.
- **Etiqueta**: fica "ativo" até faltarem 7 dias; a partir daí vira "vence
  em N dias".

O limite de 30 dias é um teto rígido: o comando `planejar` confere cada
proposta antes de mostrar e falha se alguma passar da data.

## Relatório por e-mail

O comando `relatorio` monta o resumo do dia e manda para o seu e-mail.

```bash
python3 -m agente relatorio                      # só monta e grava relatorio.html
python3 -m agente relatorio --enviar             # monta e envia
python3 -m agente relatorio --etiqueta Daniel --enviar   # só os seus pacientes
```

Sem a flag `--enviar` nada sai — dá para abrir o `relatorio.html` no
navegador e ver como vai chegar.

O e-mail abre com o bloco **Agendar agora**, em destaque, com os
pacientes na ordem de urgência. Depois vêm a agenda de retornos, o
quadro de consultas por paciente, os alertas do dia e os planos
terminando.

Cada paciente do bloco de prioridade vem com o motivo explícito. Um
paciente pode ter mais de um:

| Motivo | Quando aparece |
|---|---|
| passou N dias do limite | O retorno furou os 30 dias. |
| N consulta(s) a menos | Fez menos avaliações do que o plano previa até hoje. |
| limite vence em N dias | O prazo termina dentro de 7 dias. |
| sem horário livre antes do limite | A agenda está cheia. Abra mais horários. |
| plano vencido | Precisa renovar antes de marcar. |

### O alarme dos 30 dias

O prazo entre consultas é para ser cumprido, não esticado. Sempre que um
paciente **chega ou passa** dos 30 dias desde a última consulta, o
e-mail abre com um bloco vermelho, antes de qualquer outra coisa:

```
🚨 3 PACIENTES NO LIMITE DE 30 DIAS
O prazo entre consultas não pode ser esticado. Agendar hoje.

  [+11 dias]        Carla Nunes (Daniel · semestral)
  [+1 dia]          Isabela Paiva (Daniel · semestral)
  [HOJE É O LIMITE] Laura Helena (Juliana · anual)
```

O assunto do e-mail também muda: vira
`🚨 3 pacientes NO LIMITE DE 30 DIAS — agenda 05/08`, para dar de cara
na caixa de entrada sem precisar abrir.

Plano vencido **não** entra nesse alarme: é outro problema (renovação),
e misturar os dois faz o alarme perder força.

### Filtrar por etiqueta

O relatório considera as etiquetas do LiveClin, no padrão
`Ativos - <Profissional>`:

```toml
[filtro]
etiquetas = ["Ativos - Daniel", "Ativos - Juliana"]
```

Ou na linha de comando, repetindo a flag:

```bash
python3 -m agente relatorio --etiqueta "Ativos - Daniel" --etiqueta "Ativos - Juliana"
```

Quando há mais de um profissional, o e-mail **identifica de quem é cada
paciente** — no alarme, na fila de prioridade e no quadro de consultas —
e traz um resumo com a contagem de cada um.

A comparação ignora acento e maiúscula. Por padrão só entram pacientes
**ativos**; `--incluir-inativos` traz também pausados e inativos.

## Contagem de consultas (WebDiet)

Cada avaliação física registrada no WebDiet conta como uma consulta
realizada. Exporte as avaliações e aponte `webdiet.caminho` para o
arquivo — bastam as colunas de **paciente** e **data**.

Com isso o relatório passa a mostrar, para cada paciente, quantas
consultas foram feitas, quantas o plano prevê no total e quantas já
deveriam ter acontecido até hoje.

### Quem informa o quê

| Dado | Origem |
|---|---|
| Plano, prazo, vigência | LiveClin |
| Etiquetas | LiveClin |
| Número de consultas a que o plano dá direito | LiveClin |
| Consultas realizadas | WebDiet (avaliações antropométricas) |
| Data da última consulta | WebDiet (última avaliação) |

A data da última consulta vem do WebDiet, não do LiveClin — é ela que
define o limite de 30 dias, então o agente lê o WebDiet **antes** de
montar a agenda. Quando as duas fontes discordam, o agente adota a data
do WebDiet e reporta a correção.

### Consultas por plano

O número de consultas é comercial, definido no LiveClin. **Não** sai de
dividir a duração por 30:

| Plano | Vigência | Consultas | Espaçamento médio |
|---|---|---|---|
| Mensal | 30 dias | 1 | 30 dias |
| Trimestral | 90 dias | 3 | 30 dias |
| Semestral | 180 dias | 5 | 36 dias |
| Anual | 360 dias | 10 | 36 dias |

Configure em `[planos]`, na forma
`semestral = { dias = 180, consultas = 5 }`.

As previstas até hoje crescem conforme o plano corre, então "4 de 5,
previstas até hoje 5" quer dizer que falta uma agora.

Só contam as avaliações dentro da vigência do plano atual — avaliações
de um plano anterior não inflam a contagem.

### Atenção: as duas regras não fecham nos planos longos

O limite de agendamento é 30 dias, mas semestral e anual espaçam as
consultas a cada 36. Marcando de 30 em 30 dias, um paciente anual usa as
10 consultas em 300 dias e fica **60 dias com plano vigente e sem
consulta disponível**. No semestral sobram 30 dias.

O agente sinaliza quem esgotou as consultas com plano ainda válido, para
você decidir entre renovar antes ou liberar uma avulsa. Ele não resolve
sozinho porque é decisão comercial, não técnica.

### Nomes escritos diferente nos dois sistemas

O mesmo paciente costuma aparecer escrito de formas diferentes no
LiveClin e no WebDiet. O agente reconhece acento faltando, sobrenome
fora de ordem, nome do meio abreviado e erro de digitação — "Isabel
Oaiva" no WebDiet casa com "Isabela Paiva" do LiveClin.

**Quando dois pacientes ficam igualmente parecidos, o agente não
escolhe.** O nome vai para a seção "Conferir manualmente" do e-mail, com
os candidatos e a porcentagem de cada um. Contar a consulta na pessoa
errada é pior do que não contar, então a dúvida sobe para você em vez de
virar um palpite.

### Configurar o Gmail

No `config.toml`, a seção `[email]` já vem com o destinatário preenchido.
Confira o `remetente` (a conta que envia) e depois gere uma **Senha de
app**:

1. A verificação em duas etapas precisa estar ativa na conta Google.
2. Gere a senha em https://myaccount.google.com/apppasswords — são 16
   letras.
3. Exporte na variável de ambiente:

```bash
export AGENTE_EMAIL_SENHA="assenhade16letras"
```

**A senha não vai no `config.toml`.** O agente lê só da variável de
ambiente, para que ela não acabe versionada por acidente. Para não
digitar toda vez, coloque a linha do `export` no seu `~/.bashrc` (Linux),
`~/.zshrc` (macOS) ou nas variáveis de ambiente do usuário no Windows.

A senha da sua conta Google **não funciona** aqui: o Gmail bloqueia SMTP
com senha comum quando a verificação em duas etapas está ligada. Se o
login for recusado, o agente mostra exatamente esse aviso.

Se preferir outro provedor, mude `servidor` e `porta` (587 para STARTTLS,
465 para SSL direto).

## Etiquetas do BotConversa

No BotConversa a **etiqueta é o gatilho**: `ativo-emagrec` dispara a
sequência de emagrecimento, `finalizado-*` dispara a de reativação. O
agente não escreve nem envia mensagem — ele só mantém a etiqueta
contando a verdade, a partir do plano no LiveClin.

```bash
python3 -m agente etiquetas
```

O comando mostra e grava um CSV com a etiqueta que cada paciente deveria
ter hoje:

```
Ana Souza        mensal       ativo-emagrec, mes-1
Eva Ramos        mensal       ativo-emagrec, mes-1, vence-7dias
Gisele Prado     mensal       finalizado-emagrec
      plano venceu em 20/07/2026, mas o LiveClin ainda marca como ativo
```

As regras:

- O nicho vem da etiqueta do LiveClin (emagrecimento, hipertrofia,
  performance/esporte). Configure em `[botconversa.nichos]`.
- `mes-N` avança a cada 30 dias de plano, até `mes-12`.
- `vence-7dias` entra quando faltam 7 dias ou menos.
- Plano vencido ou paciente inativo viram `finalizado-<nicho>`.
- **Paciente pausado fica sem etiqueta de sequência**, para não receber
  disparo. Sem etiqueta de nicho, idem — o agente avisa em vez de
  chutar uma sequência.

Um paciente nunca recebe `ativo-*` e `finalizado-*` ao mesmo tempo.

### Por que só etiqueta, e não envio

Suas sequências do BotConversa já disparam segunda, quarta e quinta. Se
o agente também mandasse mensagem, o paciente receberia em dobro. Um
cérebro decide o conteúdo (BotConversa), o outro mantém o cadastro
correto (o agente).

### Integração direta com a API

Ainda não existe: falta confirmar os endpoints contra o Swagger oficial
(`backend.botconversa.com.br/swagger/`). Por enquanto o caminho é
importar o CSV no BotConversa.

Quando existir, a chave da API virá de variável de ambiente
(`BOTCONVERSA_API_KEY`), nunca do `config.toml` — mesma regra da senha
do e-mail.

## Google Calendar (opcional)

Por padrão as consultas vão para um arquivo local (`agenda_local.json`),
o que funciona sem nenhuma credencial. Para escrever na sua agenda do
Google:

1. `pip install -r requirements-google.txt`
2. No [console do Google Cloud](https://console.cloud.google.com/apis/credentials),
   crie uma credencial OAuth do tipo "Aplicativo para computador" e baixe
   o `credentials.json` para esta pasta.
3. No `config.toml`, mude `agenda.tipo` para `"google_calendar"` e
   descomente a seção `[agenda.google]`.

Na primeira execução o navegador abre para você autorizar. O agente não
pede nem guarda a sua senha do Google — o token fica no `token.json`,
nesta pasta, na sua máquina.

## Rodar todo dia automaticamente

**Linux/macOS** — `crontab -e`, e acrescente (todo dia às 8h):

```
0 8 * * * cd /caminho/para/agente_agendamento && AGENTE_EMAIL_SENHA="assenhade16letras" python3 -m agente relatorio --enviar
```

**Windows** — Agendador de Tarefas, ação "Iniciar um programa":
programa `python`, argumentos `-m agente relatorio --enviar`, iniciar em
`C:\caminho\para\agente_agendamento`. A senha precisa estar nas variáveis
de ambiente do usuário.

Vale deixar o `relatorio` no automático e rodar o `aplicar` na mão, para
você conferir os horários antes de eles entrarem na agenda. Assim você
recebe o resumo todo dia e decide o que marcar.

Se algo falhar (planilha faltando, senha errada), o agente termina com
erro e o cron registra a falha em vez de fingir sucesso.

## Testes

```bash
python3 -m unittest discover -s tests -t .
```

## Estrutura

```
agente/
  regras.py       limite de 30 dias, check-in, alertas, etiquetas
  agendador.py    escolhe os horários dentro do limite
  planos.py       catálogo (30/90/180/360 dias)
  fontes/         leitura da planilha do LiveClin
  agenda/         arquivo local e Google Calendar
  notificacoes.py fila de mensagens (WhatsApp engatilhado)
  consultas.py    cruzamento LiveClin x WebDiet (feitas x previstas)
  nomes.py        casamento de nomes com erro de digitação
  prioridade.py   fila de quem precisa ser agendado, e por quê
  filtros.py      seleção por etiqueta e status
  relatorio.py    resumo do dia em HTML e texto
  entrega/        envio por e-mail (SMTP)
  cli.py          comandos de linha
```
