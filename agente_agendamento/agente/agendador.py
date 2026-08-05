"""Motor de agendamento.

Escolhe, para cada paciente ativo, o horário de retorno mais próximo
possível do limite de 30 dias — **sem nunca ultrapassá-lo** e sem
ultrapassar o fim da vigência do plano.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .agenda.base import Agenda, EventoAgenda
from .modelos import Agendamento, Paciente, SituacaoAgendamento, StatusPaciente
from .regras import INTERVALO_MAXIMO_DIAS, data_limite_retorno
from .util import chave, garantir_fuso


class JanelaDeAtendimento:
    """Dias e horários em que o profissional atende."""

    def __init__(
        self,
        dias_semana: list[int],
        horarios: list[str],
        duracao_min: int,
        fuso: str,
    ) -> None:
        if not dias_semana:
            raise ValueError("configure ao menos um dia de atendimento em agenda.dias_semana")
        if not horarios:
            raise ValueError("configure ao menos um horário em agenda.horarios")
        if duracao_min <= 0:
            raise ValueError("agenda.duracao_min precisa ser maior que zero")
        self.dias_semana = sorted(set(dias_semana))
        self.horarios = sorted({self._ler_horario(h) for h in horarios})
        self.duracao = timedelta(minutes=duracao_min)
        self.fuso = ZoneInfo(fuso)

    @staticmethod
    def _ler_horario(bruto: str) -> time:
        try:
            hora, minuto = bruto.strip().split(":")
            return time(int(hora), int(minuto))
        except (ValueError, AttributeError) as erro:
            raise ValueError(f"horário inválido em agenda.horarios: {bruto!r}") from erro

    def slots_do_dia(self, dia: date) -> list[tuple[datetime, datetime]]:
        # ``isoweekday``: segunda = 1 ... domingo = 7.
        if dia.isoweekday() not in self.dias_semana:
            return []
        slots = []
        for horario in self.horarios:
            inicio = datetime.combine(dia, horario, tzinfo=self.fuso)
            slots.append((inicio, inicio + self.duracao))
        return slots


class Agendador:
    def __init__(
        self,
        agenda: Agenda,
        janela: JanelaDeAtendimento,
        dias_de_busca: int = 7,
        antecedencia_horas: int = 24,
        preferencia: str = "proximo_do_limite",
        dias_recuperacao: int = 7,
    ) -> None:
        if preferencia not in ("proximo_do_limite", "mais_cedo"):
            raise ValueError(
                "agenda.preferencia deve ser 'proximo_do_limite' ou 'mais_cedo'"
            )
        self.agenda = agenda
        self.janela = janela
        self.dias_de_busca = max(0, dias_de_busca)
        self.antecedencia = timedelta(hours=max(0, antecedencia_horas))
        self.preferencia = preferencia
        self.dias_recuperacao = max(0, dias_recuperacao)

    def planejar(
        self, pacientes: list[Paciente], agora: datetime | None = None
    ) -> list[Agendamento]:
        agora = agora or datetime.now(self.janela.fuso)
        agora = garantir_fuso(agora, self.janela.fuso)
        hoje = agora.date()

        # Pacientes mais urgentes escolhem primeiro.
        ordenados = sorted(
            pacientes,
            key=lambda p: (data_limite_retorno(p), p.nome)
            if p.status is StatusPaciente.ATIVO
            else (date.max, p.nome),
        )

        eventos = self._eventos_do_horizonte(ordenados, agora, hoje)
        ocupados = [(e.inicio, e.fim) for e in eventos]

        # Slots já entregues nesta rodada não podem ser oferecidos de novo.
        reservados: set[datetime] = set()
        resultados: list[Agendamento] = []
        for paciente in ordenados:
            resultados.append(
                self._planejar_um(paciente, agora, hoje, reservados, eventos, ocupados)
            )
        return resultados

    def _eventos_do_horizonte(
        self, pacientes: list[Paciente], agora: datetime, hoje: date
    ) -> list[EventoAgenda]:
        """Lê a agenda uma única vez, cobrindo todos os limites da rodada."""
        limites = [
            data_limite_retorno(p)
            for p in pacientes
            if p.status is StatusPaciente.ATIVO and p.plano_fim >= hoje
        ]
        fim_horizonte = max(
            [hoje + timedelta(days=self.dias_recuperacao), *limites]
        )
        inicio_consulta = datetime.combine(hoje, time.min, tzinfo=self.janela.fuso)
        fim_consulta = datetime.combine(
            fim_horizonte + timedelta(days=1), time.min, tzinfo=self.janela.fuso
        )
        return [
            EventoAgenda(
                evento.titulo,
                garantir_fuso(evento.inicio, self.janela.fuso),
                garantir_fuso(evento.fim, self.janela.fuso),
            )
            for evento in self.agenda.eventos(inicio_consulta, fim_consulta)
        ]

    def _consulta_marcada(
        self, paciente: Paciente, eventos: list[EventoAgenda], agora: datetime
    ) -> EventoAgenda | None:
        """Encontra uma consulta futura já marcada para este paciente.

        Evita que rodadas repetidas do agente dupliquem o mesmo retorno.
        """
        alvo = chave(paciente.nome)
        for evento in eventos:
            if evento.inicio >= agora and alvo and alvo in chave(evento.titulo):
                return evento
        return None

    def _planejar_um(
        self,
        paciente: Paciente,
        agora: datetime,
        hoje: date,
        reservados: set[datetime],
        eventos: list[EventoAgenda],
        ocupados: list[tuple[datetime, datetime]],
    ) -> Agendamento:
        if paciente.status is not StatusPaciente.ATIVO:
            return Agendamento(
                paciente=paciente,
                situacao=SituacaoAgendamento.IGNORADO,
                motivo=f"paciente {paciente.status.value}",
            )

        if paciente.plano_fim < hoje:
            return Agendamento(
                paciente=paciente,
                situacao=SituacaoAgendamento.PLANO_VENCIDO,
                limite=paciente.plano_fim,
                motivo=(
                    f"plano venceu em {paciente.plano_fim:%d/%m/%Y}; "
                    "renove antes de marcar o retorno"
                ),
            )

        limite = data_limite_retorno(paciente)

        ja_marcada = self._consulta_marcada(paciente, eventos, agora)
        if ja_marcada is not None:
            return Agendamento(
                paciente=paciente,
                situacao=SituacaoAgendamento.JA_AGENDADO,
                limite=limite,
                inicio=ja_marcada.inicio,
                fim=ja_marcada.fim,
                motivo=(
                    f"já existe consulta em {ja_marcada.inicio:%d/%m/%Y %H:%M} na agenda"
                ),
            )

        atrasado = limite < hoje

        if atrasado:
            # O prazo de 30 dias já estourou: marca o quanto antes, sempre
            # dentro da vigência do plano.
            fim_busca = min(hoje + timedelta(days=self.dias_recuperacao), paciente.plano_fim)
            inicio_busca = hoje
            preferencia = "mais_cedo"
        else:
            fim_busca = limite
            inicio_busca = max(hoje, limite - timedelta(days=self.dias_de_busca))
            preferencia = self.preferencia

        candidatos = self._candidatos(inicio_busca, fim_busca, agora, reservados, ocupados)
        if not candidatos:
            atraso = (hoje - limite).days
            detalhe = (
                f"sem horário livre entre {inicio_busca:%d/%m/%Y} e {fim_busca:%d/%m/%Y}"
            )
            return Agendamento(
                paciente=paciente,
                situacao=SituacaoAgendamento.SEM_VAGA,
                limite=limite,
                motivo=(
                    f"{detalhe}; paciente já está {atraso} dia(s) além do limite"
                    if atrasado
                    else f"{detalhe} (limite de {INTERVALO_MAXIMO_DIAS} dias)"
                ),
            )

        escolhido = candidatos[-1] if preferencia == "proximo_do_limite" else candidatos[0]
        reservados.add(escolhido[0])

        situacao = (
            SituacaoAgendamento.ATRASADO if atrasado else SituacaoAgendamento.AGENDAVEL
        )
        base = paciente.ultima_consulta or paciente.plano_inicio
        intervalo = (escolhido[0].date() - base).days
        motivo = f"{intervalo} dias desde {base:%d/%m/%Y}"
        if atrasado:
            motivo += f"; limite era {limite:%d/%m/%Y}"

        return Agendamento(
            paciente=paciente,
            situacao=situacao,
            limite=limite,
            inicio=escolhido[0],
            fim=escolhido[1],
            motivo=motivo,
        )

    def _candidatos(
        self,
        inicio_busca: date,
        fim_busca: date,
        agora: datetime,
        reservados: set[datetime],
        ocupados: list[tuple[datetime, datetime]],
    ) -> list[tuple[datetime, datetime]]:
        if fim_busca < inicio_busca:
            return []

        limite_inferior = agora + self.antecedencia
        livres: list[tuple[datetime, datetime]] = []
        dia = inicio_busca
        while dia <= fim_busca:
            for inicio, fim in self.janela.slots_do_dia(dia):
                if inicio < limite_inferior or inicio in reservados:
                    continue
                if any(fim > oc_i and inicio < oc_f for oc_i, oc_f in ocupados):
                    continue
                livres.append((inicio, fim))
            dia += timedelta(days=1)
        return livres
