import unittest
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from agente.agenda.base import Agenda, EventoAgenda
from agente.agendador import Agendador, JanelaDeAtendimento
from agente.modelos import Paciente, SituacaoAgendamento, StatusPaciente
from agente.planos import CATALOGO_PADRAO
from agente.regras import INTERVALO_MAXIMO_DIAS
from agente.util import garantir_fuso

SP = ZoneInfo("America/Sao_Paulo")
ANUAL = CATALOGO_PADRAO["anual"]
MENSAL = CATALOGO_PADRAO["mensal"]


class AgendaFalsa(Agenda):
    """Agenda em memória.

    ``ocupacoes`` são blocos anônimos (compromissos que não são consulta);
    ``marcados`` são eventos com título, usados para simular consultas que
    já estão na agenda.
    """

    def __init__(self, ocupacoes=None, marcados=None):
        self.ocupacoes = ocupacoes or []
        self.marcados = marcados or []
        self.criados = []

    def eventos(self, inicio, fim):
        # Devolve os valores originais (às vezes ingênuos) para exercitar a
        # tolerância do agendador.
        todos = [EventoAgenda("Bloqueio", i, f) for i, f in self.ocupacoes]
        todos += [EventoAgenda(t, i, f) for t, i, f in self.marcados]
        return sorted(
            (
                e
                for e in todos
                if garantir_fuso(e.fim, inicio.tzinfo) > inicio
                and garantir_fuso(e.inicio, inicio.tzinfo) < fim
            ),
            key=lambda e: garantir_fuso(e.inicio, inicio.tzinfo),
        )

    def criar_evento(self, titulo, inicio, fim, descricao=""):
        self.criados.append((titulo, inicio, fim))
        self.marcados.append((titulo, inicio, fim))
        return f"id-{len(self.criados)}"


def janela(horarios=("09:00", "10:00"), dias=(1, 2, 3, 4, 5), duracao=50):
    return JanelaDeAtendimento(
        dias_semana=list(dias), horarios=list(horarios), duracao_min=duracao, fuso="America/Sao_Paulo"
    )


def paciente(**kwargs):
    base = dict(
        nome="Fulano de Tal",
        plano=ANUAL,
        plano_inicio=date(2026, 1, 5),
        plano_fim=date(2026, 12, 31),
        status=StatusPaciente.ATIVO,
        ultima_consulta=date(2026, 3, 10),
    )
    base.update(kwargs)
    return Paciente(**base)


AGORA = datetime(2026, 4, 1, 8, 0, tzinfo=SP)


class TestLimiteDe30Dias(unittest.TestCase):
    def test_nunca_agenda_depois_do_limite(self):
        # Última consulta 10/03 → limite 09/04 (quinta-feira).
        agendador = Agendador(AgendaFalsa(), janela(), dias_de_busca=7)
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(resultado.situacao, SituacaoAgendamento.AGENDAVEL)
        self.assertEqual(resultado.limite, date(2026, 4, 9))
        self.assertLessEqual(resultado.inicio.date(), date(2026, 4, 9))

    def test_intervalo_resultante_cabe_em_30_dias(self):
        agendador = Agendador(AgendaFalsa(), janela(), dias_de_busca=7)
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        intervalo = (resultado.inicio.date() - date(2026, 3, 10)).days
        self.assertLessEqual(intervalo, INTERVALO_MAXIMO_DIAS)

    def test_preferencia_proximo_do_limite_escolhe_o_ultimo_dia_util(self):
        agendador = Agendador(AgendaFalsa(), janela(), dias_de_busca=7)
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(resultado.inicio.date(), date(2026, 4, 9))

    def test_preferencia_mais_cedo_antecipa(self):
        agendador = Agendador(
            AgendaFalsa(), janela(), dias_de_busca=7, preferencia="mais_cedo"
        )
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(resultado.inicio.date(), date(2026, 4, 2))
        self.assertLess(resultado.inicio.date(), date(2026, 4, 9))

    def test_limite_cai_em_fim_de_semana_puxa_para_tras(self):
        # 04/04/2026 é sábado; última consulta 05/03 → limite 04/04.
        agendador = Agendador(AgendaFalsa(), janela(), dias_de_busca=7)
        p = paciente(ultima_consulta=date(2026, 3, 5))
        resultado = agendador.planejar([p], agora=AGORA)[0]
        self.assertEqual(resultado.limite, date(2026, 4, 4))
        self.assertEqual(resultado.inicio.date(), date(2026, 4, 3))
        self.assertEqual(resultado.inicio.isoweekday(), 5)

    def test_fim_do_plano_antes_dos_30_dias_manda_no_limite(self):
        p = paciente(plano=MENSAL, plano_fim=date(2026, 4, 6), ultima_consulta=date(2026, 3, 10))
        agendador = Agendador(AgendaFalsa(), janela(), dias_de_busca=7)
        resultado = agendador.planejar([p], agora=AGORA)[0]
        self.assertEqual(resultado.limite, date(2026, 4, 6))
        self.assertLessEqual(resultado.inicio.date(), date(2026, 4, 6))


class TestSituacoes(unittest.TestCase):
    def test_paciente_atrasado_e_marcado_como_atrasado(self):
        p = paciente(ultima_consulta=date(2026, 2, 1))  # limite 03/03, já passou
        agendador = Agendador(AgendaFalsa(), janela())
        resultado = agendador.planejar([p], agora=AGORA)[0]
        self.assertEqual(resultado.situacao, SituacaoAgendamento.ATRASADO)
        self.assertGreaterEqual(resultado.inicio.date(), date(2026, 4, 1))

    def test_plano_vencido_nao_agenda(self):
        p = paciente(plano_fim=date(2026, 3, 20))
        agendador = Agendador(AgendaFalsa(), janela())
        resultado = agendador.planejar([p], agora=AGORA)[0]
        self.assertEqual(resultado.situacao, SituacaoAgendamento.PLANO_VENCIDO)
        self.assertIsNone(resultado.inicio)

    def test_paciente_pausado_e_ignorado(self):
        p = paciente(status=StatusPaciente.PAUSADO)
        agendador = Agendador(AgendaFalsa(), janela())
        resultado = agendador.planejar([p], agora=AGORA)[0]
        self.assertEqual(resultado.situacao, SituacaoAgendamento.IGNORADO)
        self.assertIsNone(resultado.inicio)

    def test_sem_vaga_quando_a_janela_esta_cheia(self):
        # Bloqueia toda a semana anterior ao limite.
        ocupacoes = []
        dia = date(2026, 4, 1)
        while dia <= date(2026, 4, 9):
            for hora in (9, 10):
                inicio = datetime.combine(dia, datetime.min.time(), tzinfo=SP).replace(hour=hora)
                ocupacoes.append((inicio, inicio + timedelta(hours=1)))
            dia += timedelta(days=1)
        agendador = Agendador(AgendaFalsa(ocupacoes), janela(), dias_de_busca=7)
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(resultado.situacao, SituacaoAgendamento.SEM_VAGA)
        self.assertIsNone(resultado.inicio)


class TestConcorrencia(unittest.TestCase):
    def test_dois_pacientes_nao_recebem_o_mesmo_horario(self):
        # Só existe um horário livre por dia útil.
        p1 = paciente(nome="Ana Souza", ultima_consulta=date(2026, 3, 10))
        p2 = paciente(nome="Bruno Lima", ultima_consulta=date(2026, 3, 10))
        agendador = Agendador(AgendaFalsa(), janela(horarios=("09:00",)), dias_de_busca=7)
        r1, r2 = agendador.planejar([p1, p2], agora=AGORA)
        self.assertIsNotNone(r1.inicio)
        self.assertIsNotNone(r2.inicio)
        self.assertNotEqual(r1.inicio, r2.inicio)

    def test_quem_tem_limite_mais_curto_e_atendido_primeiro(self):
        urgente = paciente(nome="Urgente", ultima_consulta=date(2026, 3, 6))  # limite 05/04
        folgado = paciente(nome="Folgado", ultima_consulta=date(2026, 3, 12))  # limite 11/04
        agendador = Agendador(AgendaFalsa(), janela(), dias_de_busca=7)
        resultados = {r.paciente.nome: r for r in agendador.planejar([folgado, urgente], agora=AGORA)}
        self.assertLessEqual(
            resultados["Urgente"].inicio.date(), resultados["Folgado"].inicio.date()
        )


class TestRestricoesDeAgenda(unittest.TestCase):
    def test_respeita_antecedencia_minima(self):
        agora = datetime(2026, 4, 9, 8, 0, tzinfo=SP)  # limite é hoje às 09:00
        agendador = Agendador(AgendaFalsa(), janela(), dias_de_busca=7, antecedencia_horas=24)
        resultado = agendador.planejar([paciente()], agora=agora)[0]
        # Não cabe mais nada dentro do limite respeitando 24h de antecedência.
        self.assertEqual(resultado.situacao, SituacaoAgendamento.SEM_VAGA)

    def test_nao_agenda_em_dia_nao_atendido(self):
        agendador = Agendador(AgendaFalsa(), janela(dias=(1,)), dias_de_busca=30)
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(resultado.inicio.isoweekday(), 1)

    def test_desvia_de_horario_ocupado(self):
        ocupado_inicio = datetime(2026, 4, 9, 9, 0, tzinfo=SP)
        agendador = Agendador(
            AgendaFalsa([(ocupado_inicio, ocupado_inicio + timedelta(hours=1))]),
            janela(),
            dias_de_busca=7,
        )
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertNotEqual(resultado.inicio, ocupado_inicio)
        self.assertEqual(resultado.inicio, datetime(2026, 4, 9, 10, 0, tzinfo=SP))

    def test_ocupacao_sem_fuso_e_tratada_no_fuso_local(self):
        ingenuo = datetime(2026, 4, 9, 9, 0)
        agendador = Agendador(
            AgendaFalsa([(ingenuo, ingenuo + timedelta(hours=1))]), janela(), dias_de_busca=7
        )
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(resultado.inicio, datetime(2026, 4, 9, 10, 0, tzinfo=SP))


class TestIdempotencia(unittest.TestCase):
    def test_nao_remarca_quem_ja_tem_consulta(self):
        agenda = AgendaFalsa(
            marcados=[
                (
                    "Consulta — Fulano de Tal",
                    datetime(2026, 4, 8, 9, 0, tzinfo=SP),
                    datetime(2026, 4, 8, 9, 50, tzinfo=SP),
                )
            ]
        )
        agendador = Agendador(agenda, janela(), dias_de_busca=7)
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(resultado.situacao, SituacaoAgendamento.JA_AGENDADO)
        self.assertEqual(resultado.inicio, datetime(2026, 4, 8, 9, 0, tzinfo=SP))

    def test_rodar_duas_vezes_nao_duplica(self):
        agenda = AgendaFalsa()
        agendador = Agendador(agenda, janela(), dias_de_busca=7)

        primeira = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(primeira.situacao, SituacaoAgendamento.AGENDAVEL)
        agenda.criar_evento(
            f"Consulta — {primeira.paciente.nome}", primeira.inicio, primeira.fim
        )

        segunda = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(segunda.situacao, SituacaoAgendamento.JA_AGENDADO)
        self.assertEqual(segunda.inicio, primeira.inicio)
        self.assertEqual(len(agenda.criados), 1)

    def test_consulta_passada_nao_conta_como_marcada(self):
        agenda = AgendaFalsa(
            marcados=[
                (
                    "Consulta — Fulano de Tal",
                    datetime(2026, 3, 10, 9, 0, tzinfo=SP),
                    datetime(2026, 3, 10, 9, 50, tzinfo=SP),
                )
            ]
        )
        agendador = Agendador(agenda, janela(), dias_de_busca=7)
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(resultado.situacao, SituacaoAgendamento.AGENDAVEL)

    def test_consulta_de_outro_paciente_nao_conta(self):
        agenda = AgendaFalsa(
            marcados=[
                (
                    "Consulta — Outra Pessoa",
                    datetime(2026, 4, 8, 9, 0, tzinfo=SP),
                    datetime(2026, 4, 8, 9, 50, tzinfo=SP),
                )
            ]
        )
        agendador = Agendador(agenda, janela(), dias_de_busca=7)
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(resultado.situacao, SituacaoAgendamento.AGENDAVEL)

    def test_titulo_com_acento_diferente_ainda_casa(self):
        agenda = AgendaFalsa(
            marcados=[
                (
                    "CONSULTA - FULANO DE TAL",
                    datetime(2026, 4, 8, 9, 0, tzinfo=SP),
                    datetime(2026, 4, 8, 9, 50, tzinfo=SP),
                )
            ]
        )
        agendador = Agendador(agenda, janela(), dias_de_busca=7)
        resultado = agendador.planejar([paciente()], agora=AGORA)[0]
        self.assertEqual(resultado.situacao, SituacaoAgendamento.JA_AGENDADO)


class TestJanelaInvalida(unittest.TestCase):
    def test_sem_horarios(self):
        with self.assertRaises(ValueError):
            janela(horarios=())

    def test_horario_malformado(self):
        with self.assertRaises(ValueError):
            janela(horarios=("9h",))

    def test_preferencia_invalida(self):
        with self.assertRaises(ValueError):
            Agendador(AgendaFalsa(), janela(), preferencia="qualquer")


if __name__ == "__main__":
    unittest.main()
