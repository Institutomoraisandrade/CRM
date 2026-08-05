import unittest
from datetime import date, timedelta

from agente.modelos import Paciente, StatusPaciente, TipoAlerta
from agente.planos import CATALOGO_PADRAO
from agente.regras import (
    INTERVALO_MAXIMO_DIAS,
    alertas_do_paciente,
    data_checkin,
    data_limite_retorno,
    etiqueta_vigencia,
)

MENSAL = CATALOGO_PADRAO["mensal"]
ANUAL = CATALOGO_PADRAO["anual"]


def paciente(**kwargs) -> Paciente:
    base = dict(
        nome="Fulano de Tal",
        plano=ANUAL,
        plano_inicio=date(2026, 1, 1),
        plano_fim=date(2026, 12, 27),
        status=StatusPaciente.ATIVO,
        whatsapp="5511999999999",
    )
    base.update(kwargs)
    return Paciente(**base)


class TestLimiteRetorno(unittest.TestCase):
    def test_conta_30_dias_da_ultima_consulta(self):
        p = paciente(ultima_consulta=date(2026, 3, 10))
        self.assertEqual(data_limite_retorno(p), date(2026, 4, 9))

    def test_sem_consulta_conta_do_inicio_do_plano(self):
        p = paciente(ultima_consulta=None, plano_inicio=date(2026, 2, 1))
        self.assertEqual(data_limite_retorno(p), date(2026, 3, 3))

    def test_fim_do_plano_encurta_o_limite(self):
        # 30 dias cairiam em 09/04, mas o plano acaba antes.
        p = paciente(ultima_consulta=date(2026, 3, 10), plano_fim=date(2026, 3, 25))
        self.assertEqual(data_limite_retorno(p), date(2026, 3, 25))

    def test_limite_nunca_ultrapassa_30_dias(self):
        for dia in range(1, 400):
            ultima = date(2026, 1, 1) + timedelta(days=dia)
            p = paciente(ultima_consulta=ultima, plano_fim=date(2030, 1, 1))
            self.assertLessEqual((data_limite_retorno(p) - ultima).days, INTERVALO_MAXIMO_DIAS)


class TestCheckin(unittest.TestCase):
    def test_checkin_em_15_dias(self):
        p = paciente(ultima_consulta=date(2026, 3, 10))
        self.assertEqual(data_checkin(p), date(2026, 3, 25))

    def test_sem_consulta_nao_tem_checkin(self):
        self.assertIsNone(data_checkin(paciente(ultima_consulta=None)))


class TestEtiquetas(unittest.TestCase):
    def test_ativo_enquanto_faltam_mais_de_7_dias(self):
        p = paciente(plano_fim=date(2026, 3, 20))
        self.assertEqual(etiqueta_vigencia(p, date(2026, 3, 10)), "ativo")

    def test_faltando_7_dias_mostra_contagem(self):
        p = paciente(plano_fim=date(2026, 3, 20))
        self.assertEqual(etiqueta_vigencia(p, date(2026, 3, 13)), "vence em 7 dias")

    def test_um_dia_no_singular(self):
        p = paciente(plano_fim=date(2026, 3, 20))
        self.assertEqual(etiqueta_vigencia(p, date(2026, 3, 19)), "vence em 1 dia")

    def test_vence_hoje(self):
        p = paciente(plano_fim=date(2026, 3, 20))
        self.assertEqual(etiqueta_vigencia(p, date(2026, 3, 20)), "vence hoje")

    def test_vencido(self):
        p = paciente(plano_fim=date(2026, 3, 20))
        self.assertEqual(etiqueta_vigencia(p, date(2026, 3, 21)), "vencido")

    def test_pausado_mantem_o_proprio_status(self):
        p = paciente(status=StatusPaciente.PAUSADO, plano_fim=date(2026, 3, 20))
        self.assertEqual(etiqueta_vigencia(p, date(2026, 3, 19)), "pausado")


class TestAlertas(unittest.TestCase):
    def _tipos(self, p, hoje):
        return {a.tipo for a in alertas_do_paciente(p, hoje)}

    def test_avisa_7_dias_antes_do_fim_do_plano(self):
        p = paciente(plano=MENSAL, plano_inicio=date(2026, 3, 1), plano_fim=date(2026, 3, 31))
        self.assertIn(TipoAlerta.PLANO_VENCENDO, self._tipos(p, date(2026, 3, 24)))

    def test_nao_avisa_com_8_dias(self):
        p = paciente(plano=MENSAL, plano_inicio=date(2026, 3, 1), plano_fim=date(2026, 3, 31))
        self.assertNotIn(TipoAlerta.PLANO_VENCENDO, self._tipos(p, date(2026, 3, 23)))

    def test_aviso_de_vencimento_vai_para_paciente_e_profissional(self):
        p = paciente(plano=MENSAL, plano_inicio=date(2026, 3, 1), plano_fim=date(2026, 3, 31))
        alerta = next(
            a
            for a in alertas_do_paciente(p, date(2026, 3, 25))
            if a.tipo is TipoAlerta.PLANO_VENCENDO
        )
        self.assertEqual(sorted(alerta.destinatarios), ["paciente", "profissional"])

    def test_checkin_dispara_no_dia_15(self):
        p = paciente(ultima_consulta=date(2026, 3, 10))
        self.assertIn(TipoAlerta.CHECKIN_15_DIAS, self._tipos(p, date(2026, 3, 25)))

    def test_retorno_dispara_no_dia_30(self):
        p = paciente(ultima_consulta=date(2026, 3, 10))
        self.assertIn(TipoAlerta.RETORNO_30_DIAS, self._tipos(p, date(2026, 4, 9)))

    def test_consulta_atrasada_depois_do_limite(self):
        p = paciente(ultima_consulta=date(2026, 3, 10))
        self.assertIn(TipoAlerta.CONSULTA_ATRASADA, self._tipos(p, date(2026, 4, 15)))

    def test_plano_vencido(self):
        p = paciente(plano_fim=date(2026, 3, 1))
        self.assertIn(TipoAlerta.PLANO_VENCIDO, self._tipos(p, date(2026, 3, 5)))

    def test_paciente_inativo_nao_gera_alerta(self):
        p = paciente(status=StatusPaciente.INATIVO, plano_fim=date(2026, 3, 1))
        self.assertEqual(alertas_do_paciente(p, date(2026, 3, 5)), [])


if __name__ == "__main__":
    unittest.main()
