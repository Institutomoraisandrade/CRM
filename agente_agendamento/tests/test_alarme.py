"""O alarme dos 30 dias e a separação por profissional."""

import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

from agente.modelos import Agendamento, Paciente, SituacaoAgendamento, StatusPaciente
from agente.planos import CATALOGO_PADRAO
from agente.regras import INTERVALO_MAXIMO_DIAS
from agente.relatorio import montar

SP = ZoneInfo("America/Sao_Paulo")
HOJE = date(2026, 8, 5)


def paciente(nome="Ana Souza", profissional="Daniel", plano="mensal",
             inicio=date(2026, 7, 15), ultima=None):
    p = CATALOGO_PADRAO[plano]
    return Paciente(
        nome=nome,
        plano=p,
        plano_inicio=inicio,
        plano_fim=p.data_fim(inicio),
        status=StatusPaciente.ATIVO,
        ultima_consulta=ultima,
        etiquetas=[f"Ativos - {profissional}", "emagrecimento"],
    )


def agendamento(p, limite, situacao=SituacaoAgendamento.AGENDAVEL, dia=None):
    inicio = datetime(2026, 8, dia, 9, 0, tzinfo=SP) if dia else None
    return Agendamento(
        paciente=p, situacao=situacao, limite=limite, inicio=inicio, fim=inicio, motivo=""
    )


class TestAlarme30Dias(unittest.TestCase):
    def test_limite_hoje_entra_no_alarme(self):
        p = paciente(ultima=date(2026, 7, 6))
        rel = montar([p], [agendamento(p, HOJE, dia=6)], [], HOJE)
        self.assertEqual(len(rel.urgentes_30_dias), 1)

    def test_limite_passado_entra_no_alarme(self):
        p = paciente(ultima=date(2026, 6, 25))
        rel = montar(
            [p], [agendamento(p, date(2026, 7, 25), SituacaoAgendamento.ATRASADO, 6)],
            [], HOJE,
        )
        self.assertEqual(len(rel.urgentes_30_dias), 1)

    def test_limite_futuro_nao_entra_no_alarme(self):
        p = paciente(ultima=date(2026, 7, 20))
        rel = montar([p], [agendamento(p, date(2026, 8, 19), dia=18)], [], HOJE)
        self.assertEqual(rel.urgentes_30_dias, [])

    def test_plano_vencido_nao_e_alarme_de_30_dias(self):
        # É outro problema: renovação, não prazo entre consultas.
        p = paciente(plano="mensal", inicio=date(2026, 6, 20))
        rel = montar(
            [p],
            [agendamento(p, date(2026, 7, 20), SituacaoAgendamento.PLANO_VENCIDO)],
            [], HOJE,
        )
        self.assertEqual(rel.urgentes_30_dias, [])

    def test_assunto_grita_quando_ha_urgencia(self):
        p = paciente(ultima=date(2026, 7, 6))
        rel = montar([p], [agendamento(p, HOJE, dia=6)], [], HOJE)
        self.assertIn("🚨", rel.assunto)
        self.assertIn(str(INTERVALO_MAXIMO_DIAS), rel.assunto)

    def test_assunto_calmo_sem_urgencia(self):
        rel = montar([], [], [], HOJE)
        self.assertNotIn("🚨", rel.assunto)

    def test_texto_traz_o_bloco_de_alarme(self):
        p = paciente(ultima=date(2026, 7, 6))
        texto = montar([p], [agendamento(p, HOJE, dia=6)], [], HOJE).texto()
        self.assertIn("🚨", texto)
        self.assertIn("HOJE É O LIMITE", texto)
        self.assertIn("não pode ser esticado", texto)

    def test_html_traz_o_bloco_de_alarme(self):
        p = paciente(ultima=date(2026, 6, 25))
        html = montar(
            [p], [agendamento(p, date(2026, 7, 25), SituacaoAgendamento.ATRASADO, 6)],
            [], HOJE,
        ).html()
        self.assertIn("🚨", html)
        self.assertIn("+11 DIAS", html)

    def test_um_dia_de_atraso_no_singular(self):
        p = paciente(ultima=date(2026, 7, 5))
        html = montar(
            [p], [agendamento(p, date(2026, 8, 4), SituacaoAgendamento.ATRASADO, 6)],
            [], HOJE,
        ).html()
        self.assertIn("+1 DIA<", html)
        self.assertNotIn("+1 DIAS", html)

    def test_sem_urgencia_nao_ha_bloco(self):
        p = paciente(ultima=date(2026, 7, 20))
        html = montar([p], [agendamento(p, date(2026, 8, 19), dia=18)], [], HOJE).html()
        self.assertNotIn("🚨", html)


class TestSeparacaoPorProfissional(unittest.TestCase):
    def test_agrupa_por_etiqueta(self):
        pacientes = [
            paciente("Ana Souza", "Daniel"),
            paciente("Bruno Lima", "Daniel"),
            paciente("Laura Helena", "Juliana"),
        ]
        grupos = montar(pacientes, [], [], HOJE).por_profissional
        self.assertEqual(sorted(grupos), ["Daniel", "Juliana"])
        self.assertEqual(len(grupos["Daniel"]), 2)
        self.assertEqual(len(grupos["Juliana"]), 1)

    def test_html_mostra_a_divisao_com_dois_profissionais(self):
        pacientes = [paciente("Ana", "Daniel"), paciente("Laura", "Juliana")]
        html = montar(pacientes, [], [], HOJE).html()
        self.assertIn("Pacientes por profissional", html)
        self.assertIn("Juliana", html)

    def test_html_omite_a_divisao_com_um_so_profissional(self):
        html = montar([paciente("Ana", "Daniel")], [], [], HOJE).html()
        self.assertNotIn("Pacientes por profissional", html)

    def test_texto_lista_a_divisao(self):
        pacientes = [paciente("Ana", "Daniel"), paciente("Laura", "Juliana")]
        texto = montar(pacientes, [], [], HOJE).texto()
        self.assertIn("Por profissional:", texto)
        self.assertIn("Daniel (1)", texto)

    def test_profissional_aparece_no_alarme(self):
        p = paciente("Laura Helena", "Juliana", ultima=date(2026, 7, 6))
        html = montar([p], [agendamento(p, HOJE, dia=6)], [], HOJE).html()
        self.assertIn("Juliana", html)


if __name__ == "__main__":
    unittest.main()
