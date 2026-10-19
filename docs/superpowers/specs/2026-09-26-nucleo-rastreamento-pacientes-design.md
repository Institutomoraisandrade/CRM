# Núcleo de rastreamento de pacientes (v1) — Design

## Contexto e objetivo

O Instituto Morais Andrade acompanha pacientes manualmente, cruzando informações
do **LiveClin** (prontuário/agenda) e do **WebDiet** (plano alimentar) para saber
quem está terminando o plano contratado (mensal, trimestral, semestral, anual) e
oferecer renovação. Esse processo hoje é feito à mão, olhando os dois sistemas.

Esta v1 do CRM automatiza a parte de **coleta e cruzamento de dados**: buscar nos
dois sistemas, cruzar por paciente, calcular quem está vencendo, e apresentar essa
lista pronta — o mesmo resultado que hoje é feito manualmente para gerar as
mensagens de renovação.

**Fora do escopo desta v1** (ficam para sub-projetos futuros, cada um com seu
próprio design e spec):
- Criar agendamentos automaticamente na agenda do LiveClin.
- Disparo automático de mensagens via BotConversa.
- Execução automatizada/agendada (cron) sem o usuário pedir.
- Interface visual/dashboard (a lista é apresentada via chat/CLI).

## Acesso aos sistemas de origem

LiveClin e WebDiet só são acessíveis via navegador (login e senha), sem API
pública. A extração usa automação de navegador (Playwright, motor já disponível
no ambiente).

**Disparo:** sob demanda — o usuário pede a atualização, e o processo roda uma
vez, ponta a ponta, buscando os dados atuais nos dois sistemas.

## Arquitetura

```
crm/
  scraping/
    liveclin.py      # login + extração de pacientes/planos/consultas
    webdiet.py        # login + extração de plano alimentar/status/contato
  matching.py          # cruza pacientes entre os dois sistemas
  db.py                # schema e operações do SQLite
  renewal.py           # calcula quem está vencendo e gera lista priorizada
  cli.py               # comando único: "atualizar e mostrar vencimentos"
data/
  crm.db               # banco SQLite (dados reais — NUNCA versionado no git)
```

Cada módulo tem responsabilidade única e não conhece o funcionamento interno dos
outros:
- `liveclin.py` e `webdiet.py` só sabem extrair do seu próprio site.
- `matching.py` só sabe cruzar dois conjuntos de pacientes.
- `db.py` só sabe persistir/ler.
- `renewal.py` só sabe aplicar a regra de negócio de vencimento.
- `cli.py` orquestra o fluxo ponta a ponta.

## Modelo de dados (SQLite)

- **`patients`**: id, nome, telefone_liveclin, telefone_webdiet, data_nascimento,
  email, criado_em.
- **`plans`**: id, patient_id, sistema_origem, tipo_plano, data_inicio,
  data_fim, consultas_contratadas, consultas_usadas, modalidade, servico,
  valor, atualizado_em.
- **`snapshots`**: id, patient_id, executado_em, dados_brutos_json — retrato de
  cada execução, para manter histórico mesmo se o site mudar de layout.

## Fluxo de dados

1. `liveclin.py` faz login (credenciais via variável de ambiente) e extrai, por
   paciente: nome, telefone, data de nascimento, tipo de plano, datas de
   início/fim, consultas contratadas vs. usadas.
2. `webdiet.py` faz login e extrai: nome, telefone, data de nascimento, e-mail,
   status do plano alimentar, modalidade.
3. `matching.py` cruza os dois conjuntos por paciente (ver seção de cruzamento).
4. Os dados cruzados viram uma linha por paciente/plano em `plans`, mais um
   snapshot bruto em `snapshots`.
5. `renewal.py` lê o banco e identifica quem já usou todas as consultas
   contratadas ou está a N dias do fim do plano, gerando lista ordenada por
   vencimento — equivalente ao processo manual já usado.
6. `cli.py` imprime essa lista para o usuário.

## Cruzamento de pacientes (matching.py)

Cascata sequencial, testando um campo por vez até resolver para exatamente um
candidato:

1. **Nome completo**, normalizado (sem acento, minúsculo, espaços colapsados).
   Se exatamente um paciente do outro sistema tiver esse nome, cruza.
2. Se não encontrar, **ou encontrar mais de um** candidato (nomes duplicados,
   ex.: pai e filho com o mesmo nome) → tenta por **telefone** (normalizado,
   somente dígitos, sem DDI/formatação) entre os candidatos remanescentes.
3. Se ainda não resolver → tenta por **data de nascimento**.
4. Se ainda não resolver → tenta por **e-mail** (quando existir nos dois
   sistemas).
5. Se nenhum campo resolver → paciente entra como **"não cruzado"**, separado
   na lista final, para decisão manual.

Cada cruzamento automático registra no banco **qual campo o resolveu**, para
permitir auditoria caso um cruzamento pareça errado.

## Tratamento de erros

- Falha de login ou mudança de layout (seletor não encontrado) em um paciente
  específico não derruba a extração inteira — o erro é registrado e o processo
  segue para os próximos pacientes/sistema.
- Paciente sem cruzamento encontrado não é descartado silenciosamente: aparece
  destacado na lista final como pendência de revisão manual.

## Dados sensíveis e logging

- **Nunca gravado em log, print, terminal ou qualquer arquivo** (nem
  mascarado): login/senha do LiveClin e do WebDiet (lidos só de variável de
  ambiente, em memória, no momento do login); token/cookie de sessão do
  navegador; conteúdo clínico (observações de prontuário, texto livre do plano
  alimentar).
- **Guardado apenas no banco local (`data/crm.db`)**, nunca no git (arquivo
  listado no `.gitignore`), nunca impresso por padrão no terminal: telefone,
  data de nascimento, e-mail — dados pessoais usados só para o cruzamento.
  Aparecem na tela somente se o usuário pedir o detalhe de um paciente
  específico.
- **Aparece normalmente na saída do CLI**, por ser o propósito do sistema:
  nome do paciente, tipo de plano, data de vencimento, consultas
  usadas/contratadas.

## Testes

Seguindo TDD (RED-GREEN-REFACTOR):

- **`matching.py`**: testado com fixtures (sem navegador). Casos: nome único,
  nome duplicado resolvido por telefone, telefone ausente resolvido por
  nascimento, caso "não cruzado".
- **`renewal.py`**: testado com plans falsos no banco: plano vencendo amanhã,
  plano já vencido, plano com consultas todas usadas, plano longe do fim (não
  deve entrar na lista).
- **`db.py`**: testado com um SQLite temporário (não o banco real).
- **`liveclin.py` / `webdiet.py`**: as partes que abrem navegador de verdade são
  validadas manualmente contra os sites reais (simular os sites inteiros não
  compensa); a lógica de parsing dos dados extraídos, isolada em funções
  puras, é testada com HTML/dados de exemplo salvos como fixture.

## Riscos conhecidos

- Mudança de layout no LiveClin/WebDiet pode quebrar seletores — mitigado por
  falha isolada por paciente/sistema, não pelo processo inteiro.
- Dados de contato desatualizados em um dos sistemas podem impedir cruzamento
  automático — mitigado pela cascata de múltiplos campos e pela lista de
  "não cruzados" para revisão manual.

## Próximos sub-projetos (fora desta spec)

1. Criação de agendamentos na agenda do LiveClin.
2. Disparo automático de mensagens de renovação via BotConversa.
3. Execução agendada (sem o usuário precisar pedir).
4. Interface visual/dashboard.
