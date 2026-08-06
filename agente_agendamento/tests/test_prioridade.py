import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

from agente.consultas import cruzar
from agente.fontes.webdiet_csv import Avaliacao
from agente.modelos import Agendamento, Paciente, SituacaoAgendamento, StatusPaciente
from agente.planos import CATALOGO_PADRAO
from agente.prioridade import montar_fila

SP = ZoneInfo("America/Sao_Paulo")
HOJE = date(2026, 8, 5)


def paciente(nome="Ana Souza", plano="mensal", inicio=date(2026, 7, 15),
             ultima=date(2026, 7, 15)):
    p = CATALOGO_PADRAO[plano]
    return Paciente(
        nome=nome,
        plano=p,
        plano_inicio=inicio,
        plano_fim=p.data_fim(inicio),
        status=StatusPaciente.ATIVO,
        ultima_consulta=ultima,
        etiquetas=["Daniel"],
    )


def agendamento(p, situacao, limite, dia=None):
    inicio = datetime(2026, 8, dia, 9, 0, tzinfo=SP) if dia else None
    return Agendamento(
        paciente=p,
        situacao=situacao,
        limite=limite,
        inicio=inicio,
        fim=inicio,
        motivo="",
    )


class TestFila(unittest.TestCase):
    def test_atrasado_vem_antes_de_tudo(self):
        atrasado = paciente("Atrasado")
        proximo = paciente("Proximo")
        fila = montar_fila(
            [
                agendamento(proximo, SituacaoAgendamento.AGENDAVEL, date(2026, 8, 9), 7),
                agendamento(atrasado, SituacaoAgendamento.ATRASADO, date(2026, 7, 25), 6),
            ],
            None,
            HOJE,
        )
        self.assertEqual(fila[0].paciente.nome, "Atrasado")

    def test_motivo_do_atraso_conta_os_dias(self):
        p = paciente()
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.ATRASADO, date(2026, 7, 25), 6)],
            None,
            HOJE,
        )
        self.assertIn("passou 11 dias", fila[0].motivo_principal)

    def test_sem_ultima_consulta_nao_afirma_atraso(self):
        # Sem a data, o limite sai do início do plano — dizer "passou N
        # dias" seria inventar um atraso que ninguém pode confirmar.
        p = paciente("Sem Registro", ultima=None)
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.ATRASADO, date(2026, 7, 25), 6)],
            None,
            HOJE,
        )
        self.assertNotIn("passou", fila[0].motivo_principal)
        self.assertIn("sem consulta registrada", fila[0].motivo_principal)
        self.assertIn("WebDiet", fila[0].motivo_principal)

    def test_sem_ultima_consulta_perde_prioridade_para_atraso_real(self):
        real = paciente("Atraso Real", ultima=date(2026, 6, 20))
        incerto = paciente("Sem Registro", ultima=None)
        fila = montar_fila(
            [
                agendamento(incerto, SituacaoAgendamento.ATRASADO, date(2026, 7, 1), 6),
                agendamento(real, SituacaoAgendamento.ATRASADO, date(2026, 7, 20), 7),
            ],
            None,
            HOJE,
        )
        self.assertEqual(fila[0].paciente.nome, "Atraso Real")

    def test_deficit_de_consulta_entra_na_fila(self):
        p = paciente("Bruno Lima", "trimestral", date(2026, 6, 1))
        cruzamento = cruzar([p], [Avaliacao("Bruno Lima", date(2026, 6, 1))], HOJE)
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.AGENDAVEL, date(2026, 8, 30), 20)],
            cruzamento,
            HOJE,
        )
        self.assertEqual(len(fila), 1)
        self.assertIn("consulta(s) a menos", fila[0].motivos[0])

    def test_paciente_em_dia_e_longe_do_limite_fica_fora(self):
        p = paciente("Diego Alves", "anual", date(2026, 1, 5))
        cruzamento = cruzar(
            [p], [Avaliacao("Diego Alves", d) for d in _mensais(date(2026, 1, 5), 8)], HOJE
        )
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.AGENDAVEL, date(2026, 8, 31), 31)],
            cruzamento,
            HOJE,
        )
        self.assertEqual(fila, [])

    def test_limite_proximo_entra_na_fila(self):
        p = paciente("Eva Ramos")
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.AGENDAVEL, date(2026, 8, 9), 7)],
            None,
            HOJE,
        )
        self.assertIn("limite vence em 4 dias", fila[0].motivos)

    def test_limite_hoje(self):
        p = paciente()
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.AGENDAVEL, HOJE, 5)], None, HOJE
        )
        self.assertIn("limite vence hoje", fila[0].motivos)

    def test_plano_vencido_entra_com_motivo_de_renovacao(self):
        p = paciente("Gisele Prado")
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.PLANO_VENCIDO, date(2026, 7, 20))],
            None,
            HOJE,
        )
        self.assertIn("renovar", fila[0].motivo_principal)

    def test_sem_vaga_entra_na_fila(self):
        p = paciente()
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.SEM_VAGA, date(2026, 8, 9))], None, HOJE
        )
        self.assertIn("sem horário livre", fila[0].motivos[0])

    def test_ja_agendado_fica_fora(self):
        p = paciente()
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.JA_AGENDADO, date(2026, 8, 9), 7)],
            None,
            HOJE,
        )
        self.assertEqual(fila, [])

    def test_ignorado_fica_fora(self):
        p = paciente()
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.IGNORADO, None)], None, HOJE
        )
        self.assertEqual(fila, [])

    def test_varios_motivos_no_mesmo_paciente(self):
        p = paciente("Carla Nunes", "semestral", date(2026, 3, 10))
        cruzamento = cruzar([p], [Avaliacao("Carla Nunes", date(2026, 3, 10))], HOJE)
        fila = montar_fila(
            [agendamento(p, SituacaoAgendamento.ATRASADO, date(2026, 7, 25), 6)],
            cruzamento,
            HOJE,
        )
        self.assertGreaterEqual(len(fila[0].motivos), 2)


def _mensais(inicio, quantidade):
    from datetime import timedelta

    return [inicio + timedelta(days=30 * i) for i in range(quantidade)]


if __name__ == "__main__":
    unittest.main()
