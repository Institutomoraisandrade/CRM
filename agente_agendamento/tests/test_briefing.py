"""O briefing conduz um agente que fala com paciente de verdade.

Os testes aqui protegem o que não pode dar errado: ninguém com cadastro
duvidoso vai para a fila de contato, e nenhuma data de agendamento passa
do teto.
"""

import json
import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

from agente.briefing import montar_contatos, montar_html, montar_json
from agente.modelos import Agendamento, Paciente, SituacaoAgendamento, StatusPaciente
from agente.planos import CATALOGO_PADRAO

SP = ZoneInfo("America/Sao_Paulo")
HOJE = date(2026, 8, 6)


def paciente(nome="Ana Souza", plano="mensal", inicio=date(2026, 7, 1), ultima=None):
    p = CATALOGO_PADRAO[plano]
    return Paciente(
        nome=nome,
        plano=p,
        plano_inicio=inicio,
        plano_fim=p.data_fim(inicio),
        status=StatusPaciente.ATIVO,
        ultima_consulta=ultima,
        whatsapp="5581999990000",
    )


def agendamento(p, situacao=SituacaoAgendamento.ATRASADO, limite=None, dia=10):
    inicio = datetime(2026, 8, dia, 9, 0, tzinfo=SP)
    return Agendamento(
        paciente=p,
        situacao=situacao,
        limite=limite or date(2026, 7, 31),
        inicio=inicio,
        fim=inicio,
        motivo="",
    )


class TestQuarentena(unittest.TestCase):
    def test_sem_ultima_consulta_nao_vai_para_contato(self):
        p = paciente(ultima=None)
        contatar, conferir = montar_contatos([agendamento(p)], HOJE)
        self.assertEqual(contatar, [])
        self.assertEqual(len(conferir), 1)
        self.assertEqual(conferir[0].acao, "confirmar_cadastro")

    def test_atraso_implausivel_nao_vai_para_contato(self):
        # Plano ativo com dieta parada há 5 anos: cadastro suspeito.
        p = paciente("Victor Hugo", "anual", date(2026, 1, 26), date(2021, 2, 4))
        contatar, conferir = montar_contatos(
            [agendamento(p, limite=date(2021, 3, 6))], HOJE
        )
        self.assertEqual(contatar, [])
        self.assertTrue(conferir[0].conferir_antes)
        self.assertIn("desatualizado", conferir[0].observacao)

    def test_atraso_plausivel_vai_para_contato(self):
        p = paciente(ultima=date(2026, 6, 1))
        contatar, conferir = montar_contatos([agendamento(p)], HOJE)
        self.assertEqual(len(contatar), 1)
        self.assertEqual(conferir, [])
        self.assertEqual(contatar[0].acao, "marcar_consulta")

    def test_quarentena_traz_o_motivo(self):
        p = paciente(ultima=None)
        _, conferir = montar_contatos([agendamento(p)], HOJE)
        self.assertTrue(conferir[0].observacao)


class TestTetoDeAgendamento(unittest.TestCase):
    def test_agendar_ate_nunca_passa_do_fim_do_plano(self):
        p = paciente("Ana", "mensal", date(2026, 7, 1), date(2026, 7, 1))
        contatar, conferir = montar_contatos([agendamento(p)], HOJE)
        for item in contatar + conferir:
            self.assertLessEqual(
                datetime.strptime(item.agendar_ate, "%d/%m/%Y").date(), p.plano_fim
            )

    def test_agendar_ate_respeita_o_limite_quando_futuro(self):
        p = paciente("Bruno", "anual", date(2026, 1, 1), date(2026, 8, 1))
        limite = date(2026, 8, 31)
        contatar, _ = montar_contatos(
            [agendamento(p, SituacaoAgendamento.AGENDAVEL, limite)], HOJE
        )
        self.assertEqual(contatar[0].agendar_ate, "31/08/2026")

    def test_situacoes_sem_acao_ficam_de_fora(self):
        p = paciente(ultima=date(2026, 7, 1))
        for situacao in (
            SituacaoAgendamento.IGNORADO,
            SituacaoAgendamento.JA_AGENDADO,
            SituacaoAgendamento.PLANO_VENCIDO,
        ):
            contatar, conferir = montar_contatos([agendamento(p, situacao)], HOJE)
            self.assertEqual(contatar + conferir, [], situacao)


class TestOrdem(unittest.TestCase):
    def test_mais_atrasado_vem_primeiro(self):
        muito = paciente("Muito Atrasado", ultima=date(2026, 5, 1))
        pouco = paciente("Pouco Atrasado", ultima=date(2026, 7, 1))
        contatar, _ = montar_contatos(
            [
                agendamento(pouco, limite=date(2026, 7, 31)),
                agendamento(muito, limite=date(2026, 5, 31)),
            ],
            HOJE,
        )
        self.assertEqual(contatar[0].nome, "Muito Atrasado")
        self.assertEqual(contatar[0].prioridade, 1)

    def test_prioridade_e_sequencial(self):
        pacientes = [
            paciente(f"P{i}", ultima=date(2026, 6, i + 1)) for i in range(1, 5)
        ]
        contatar, _ = montar_contatos([agendamento(p) for p in pacientes], HOJE)
        self.assertEqual([c.prioridade for c in contatar], [1, 2, 3, 4])


class TestSaidas(unittest.TestCase):
    def test_json_tem_regras_e_proibicoes(self):
        p = paciente(ultima=date(2026, 6, 1))
        dados = montar_json(*montar_contatos([agendamento(p)], HOJE), HOJE)
        self.assertTrue(dados["regras"])
        self.assertTrue(dados["proibido"])
        self.assertEqual(dados["limite_dias_entre_consultas"], 30)
        self.assertIn("agendar_ate", dados["campos"])

    def test_json_e_serializavel(self):
        p = paciente(ultima=date(2026, 6, 1))
        dados = montar_json(*montar_contatos([agendamento(p)], HOJE), HOJE)
        self.assertIn("Ana Souza", json.dumps(dados, ensure_ascii=False))

    def test_html_avisa_para_nao_contatar_a_quarentena(self):
        p = paciente(ultima=None)
        html = montar_html(*montar_contatos([agendamento(p)], HOJE), HOJE)
        self.assertIn("NÃO envie mensagem", html)
        self.assertIn("CONFERIR ANTES DE CONTATAR", html)

    def test_html_escapa_nome(self):
        p = paciente("<script>x</script>", ultima=date(2026, 6, 1))
        html = montar_html(*montar_contatos([agendamento(p)], HOJE), HOJE)
        self.assertNotIn("<script>", html)

    def test_html_sem_ninguem_para_contatar(self):
        html = montar_html([], [], HOJE)
        self.assertIn("Ninguém para contatar hoje", html)

    def test_campos_rotulados_um_por_linha(self):
        # Formato pensado para sobreviver à extração de texto do PDF.
        p = paciente(ultima=date(2026, 6, 1))
        html = montar_html(*montar_contatos([agendamento(p)], HOJE), HOJE)
        for rotulo in ("PACIENTE:", "WHATSAPP:", "AGENDAR_ATE:", "ACAO:"):
            self.assertIn(rotulo, html)


if __name__ == "__main__":
    unittest.main()
