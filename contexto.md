# Contexto — Recuperação de pacientes (renovação de planos)

> Retomada da sessão "Lista de pacientes ativos" (Cowork), iniciada em 26/09/2026.
> Esse arquivo existe para manter o contexto do trabalho entre sessões diferentes do Claude.

## Objetivo

Criar mensagens personalizadas de renovação para pacientes que já completaram todas as
consultas do plano atual, incentivando upgrade para planos mais longos (trimestral,
semestral ou anual), com foco em:
- Mensais → subir para trimestral ou semestral (mais consistência = mais resultado).
- Trimestrais e o caso do Renan → subir para semestral ou anual.

## Status atual

10 mensagens de renovação já foram redigidas (rascunho pronto, em ordem de vencimento).
**Falta:** confirmar no LiveClin o valor pago por cada paciente (se é online/presencial,
se contratou dieta, treino ou os dois) para inserir o preço certo em cada mensagem.

## Lista de pacientes e mensagens (rascunho)

1. **PAI - Arthur Fonseca** — Mensal, vence 27/09
   > Fala, Arthur! Tudo certo? Seu mês fecha amanhã e quero conversar sobre o próximo
   > passo. Um mês serve pra arrumar a casa, mas o resultado mesmo vem com consistência
   > no tempo. Minha sugestão é seguir num trimestral ou semestral, que sai bem mais em
   > conta por mês e dá tempo de a gente trabalhar de verdade. Aproveitando: se você e
   > seu filho renovarem juntos, dá pra alinhar os dois no mesmo ritmo. Posso te mandar
   > as opções?

2. **Lais Sales** — Trimestral, vence 01/10
   > Oi, Lais! Tudo bem? Fechamos as 3 consultas do seu trimestral e seu plano vai até
   > 01/10. Agora é a fase de consolidar o que você construiu, e é aqui que muita gente
   > para e perde o embalo. Quero te propor seguir num semestral, que tem o melhor custo
   > por mês e garante 5 avaliações pra gente seguir evoluindo. Posso te mandar os
   > valores?

3. **Gabriel Tondello** — Mensal, vence 03/10
   > Fala, Gabriel! Tudo certo? Seu plano fecha dia 03/10 e já quero deixar o próximo
   > ciclo desenhado. Com um mês a gente acerta a rota, mas a mudança de verdade precisa
   > de tempo. Bora seguir num trimestral? Sai mais em conta por mês e são 3 consultas
   > pra ajustar tudo com calma. Te mando as opções?

4. **Luan Albuquerque** — Mensal, vence 04/10
   > Fala, Luan! Beleza? Seu mês fecha dia 04/10. A base tá feita, agora é hora de
   > construir em cima dela. Minha sugestão é um trimestral ou semestral, que além de
   > sair mais barato por mês, garante as reavaliações pra gente não perder o que você
   > conquistou. Posso te mandar os valores?

5. **Filipo Arce Madeira** — Trimestral, vence 13/10
   > Fala, Filipo! Tudo certo? Fechamos as 3 avaliações do trimestral, com os números em
   > mãos, e seu plano vai até 13/10. Tá na hora de pensar no próximo ciclo pra não
   > quebrar a sequência. Minha sugestão é um semestral ou anual: melhor valor por mês e
   > acompanhamento contínuo pra gente seguir evoluindo. Quer que eu te mande as opções?

6. **Georges Jean Paul** — Mensal, vence 14/10
   > Fala, Georges! Tudo bem? Seu mês vai até 14/10 e quero te propor o próximo passo.
   > Um mês é o começo, o resultado de verdade vem com tempo e consistência. Bora num
   > trimestral? Mais em conta por mês e com 3 consultas pra ajustar tudo. Te mando os
   > valores?

7. **FILHO - Arthur Fonseca** — Mensal, vence 16/10
   > Fala, Arthur! Tudo certo? Seu plano vai até 16/10 e já quero deixar o próximo ciclo
   > pronto. Com um mês a gente ajusta a rota, mas o resultado de verdade vem com tempo.
   > Minha sugestão é seguir num trimestral ou semestral, que sai mais em conta por mês.
   > Se fizer junto com seu pai, fica ainda mais fácil manter o ritmo dos dois. Posso te
   > mandar as opções?

8. **Beto Guerra** — Mensal, vence 16/10
   > Fala, Beto! Beleza? Seu mês fecha dia 16/10. Pra transformar o que você começou em
   > resultado de verdade, o ideal é seguir com acompanhamento contínuo. Minha sugestão
   > é um trimestral, que sai mais em conta por mês e tem 3 consultas de ajuste. Te mando
   > os valores?

9. **João Minosso** — Mensal, vence 17/10
   > Fala, João! Tudo certo? Seu plano vai até 17/10 e já quero te propor o próximo
   > ciclo. Um mês organiza, mas o resultado vem com tempo. Bora seguir num trimestral ou
   > semestral? Mais barato por mês e com as reavaliações garantidas. Posso te mandar as
   > opções?

10. **Renan Costa Rego** — vence 07/11, 10 avaliações feitas
    > Fala, Renan! Tudo certo? Foram 10 avaliações ao longo desse ano, disciplina de
    > verdade. Seu plano vai até 07/11 e eu quero manter esse ritmo, porque é agora que
    > o resultado se consolida. Minha proposta é renovar no anual, que tem o melhor
    > custo por mês. Posso te mandar a proposta?

## Próximos passos

- [ ] Conferir no LiveClin, para cada paciente acima: modalidade (online/presencial) e
      serviços contratados (dieta, treino ou ambos).
- [ ] Inserir o valor correto de cada plano (trimestral/semestral/anual) em cada
      mensagem.
- [ ] Definir canal de envio (WhatsApp/BotConversa) e agendar disparo por ordem de
      vencimento.
- [ ] Após envio, registrar respostas e follow-up de quem não renovar em 48h.
