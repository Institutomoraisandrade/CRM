import unittest
from datetime import date

from agente.etiquetas import (
    ETIQUETA_VENCENDO,
    desejadas,
    mes_do_acompanhamento,
    nicho_de,
    para_todos,
)
from agente.modelos import Paciente, StatusPaciente
from agente.planos import CATALOGO_PADRAO

HOJE = date(2026, 8, 5)


def paciente(nome="Ana Souza", plano="mensal", inicio=date(2026, 7, 15), **kwargs):
    p = CATALOGO_PADRAO[plano]
    base = dict(
        nome=nome,
        plano=p,
        plano_inicio=inicio,
        plano_fim=p.data_fim(inicio),
        status=StatusPaciente.ATIVO,
        etiquetas=["Daniel", "emagrecimento"],
        whatsapp="5511999990000",
    )
    base.update(kwargs)
    return Paciente(**base)


class TestNicho(unittest.TestCase):
    def test_emagrecimento(self):
        self.assertEqual(nicho_de(paciente(etiquetas=["emagrecimento"])), "emagrec")

    def test_hipertrofia(self):
        self.assertEqual(nicho_de(paciente(etiquetas=["hipertrofia"])), "hiper")

    def test_performance_e_esporte_caem_no_mesmo(self):
        self.assertEqual(nicho_de(paciente(etiquetas=["performance"])), "perf")
        self.assertEqual(nicho_de(paciente(etiquetas=["esporte"])), "perf")

    def test_ignora_caixa_e_acento(self):
        self.assertEqual(nicho_de(paciente(etiquetas=["EMAGRECIMENTO"])), "emagrec")

    def test_ignora_etiquetas_que_nao_sao_nicho(self):
        p = paciente(etiquetas=["Daniel", "vip", "hipertrofia"])
        self.assertEqual(nicho_de(p), "hiper")

    def test_sem_nicho(self):
        self.assertIsNone(nicho_de(paciente(etiquetas=["Daniel", "vip"])))

    def test_mapa_customizado(self):
        p = paciente(etiquetas=["corrida"])
        self.assertEqual(nicho_de(p, {"corrida": "perf"}), "perf")


class TestMes(unittest.TestCase):
    def test_primeiro_mes(self):
        p = paciente(inicio=date(2026, 7, 15))
        self.assertEqual(mes_do_acompanhamento(p, HOJE), 1)

    def test_avanca_a_cada_30_dias(self):
        p = paciente("Bruno", "trimestral", date(2026, 6, 1))
        self.assertEqual(mes_do_acompanhamento(p, date(2026, 6, 15)), 1)
        self.assertEqual(mes_do_acompanhamento(p, date(2026, 7, 1)), 2)
        self.assertEqual(mes_do_acompanhamento(p, date(2026, 8, 5)), 3)

    def test_nao_passa_de_doze(self):
        p = paciente("Longo", "anual", date(2020, 1, 1))
        self.assertLessEqual(mes_do_acompanhamento(p, HOJE), 12)

    def test_antes_do_inicio_conta_como_mes_1(self):
        p = paciente(inicio=date(2026, 12, 1))
        self.assertEqual(mes_do_acompanhamento(p, HOJE), 1)


class TestEtiquetasDesejadas(unittest.TestCase):
    def test_ativo_recebe_sequencia_e_mes(self):
        plano = desejadas(paciente(), HOJE)
        self.assertIn("ativo-emagrec", plano.etiquetas)
        self.assertIn("mes-1", plano.etiquetas)
        self.assertTrue(plano.receberia_mensagem)

    def test_plano_vencendo_ganha_etiqueta_extra(self):
        p = paciente("Eva", "mensal", date(2026, 7, 10))
        plano = desejadas(p, HOJE)
        self.assertIn(ETIQUETA_VENCENDO, plano.etiquetas)

    def test_plano_longe_nao_ganha_etiqueta_de_vencimento(self):
        p = paciente("Diego", "anual", date(2026, 1, 5))
        self.assertNotIn(ETIQUETA_VENCENDO, desejadas(p, HOJE).etiquetas)

    def test_plano_vencido_vira_finalizado(self):
        p = paciente("Gisele", "mensal", date(2026, 6, 20))
        plano = desejadas(p, HOJE)
        self.assertEqual(plano.etiquetas, ["finalizado-emagrec"])
        self.assertTrue(any("venceu" in o for o in plano.observacoes))

    def test_inativo_vira_finalizado(self):
        p = paciente(status=StatusPaciente.INATIVO)
        self.assertIn("finalizado-emagrec", desejadas(p, HOJE).etiquetas)

    def test_pausado_nao_recebe_sequencia(self):
        p = paciente(status=StatusPaciente.PAUSADO)
        plano = desejadas(p, HOJE)
        self.assertEqual(plano.etiquetas, [])
        self.assertFalse(plano.receberia_mensagem)
        self.assertTrue(any("pausado" in o for o in plano.observacoes))

    def test_sem_nicho_nao_recebe_sequencia(self):
        p = paciente(etiquetas=["Daniel"])
        plano = desejadas(p, HOJE)
        self.assertEqual(plano.etiquetas, [])
        self.assertFalse(plano.receberia_mensagem)
        self.assertTrue(any("nicho" in o for o in plano.observacoes))

    def test_pausado_sem_nicho_nao_quebra(self):
        p = paciente(etiquetas=[], status=StatusPaciente.PAUSADO)
        self.assertEqual(desejadas(p, HOJE).etiquetas, [])

    def test_nunca_mistura_ativo_e_finalizado(self):
        for status in StatusPaciente:
            for inicio in (date(2026, 6, 20), date(2026, 7, 15)):
                plano = desejadas(paciente(status=status, inicio=inicio), HOJE)
                ativos = [e for e in plano.etiquetas if e.startswith("ativo-")]
                finalizados = [e for e in plano.etiquetas if e.startswith("finalizado-")]
                self.assertFalse(ativos and finalizados, plano.etiquetas)


class TestLote(unittest.TestCase):
    def test_processa_todos(self):
        pacientes = [paciente("Ana"), paciente("Bruno", etiquetas=["hipertrofia"])]
        planos = para_todos(pacientes, HOJE)
        self.assertEqual(len(planos), 2)
        self.assertIn("ativo-hiper", planos[1].etiquetas)


if __name__ == "__main__":
    unittest.main()
