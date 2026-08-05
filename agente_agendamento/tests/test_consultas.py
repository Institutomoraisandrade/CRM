import unittest
from datetime import date, timedelta

from agente.consultas import (
    aplicar_ultima_consulta,
    cruzar,
    previstas_ate,
    previstas_no_plano,
)
from agente.filtros import aplicar, tem_etiqueta
from agente.fontes.webdiet_csv import Avaliacao
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
        etiquetas=["Daniel"],
    )
    base.update(kwargs)
    return Paciente(**base)


class TestPrevistas(unittest.TestCase):
    def test_total_vem_do_plano_do_liveclin(self):
        # Números comerciais: não saem de dividir a duração por 30.
        self.assertEqual(previstas_no_plano(CATALOGO_PADRAO["mensal"]), 1)
        self.assertEqual(previstas_no_plano(CATALOGO_PADRAO["trimestral"]), 3)
        self.assertEqual(previstas_no_plano(CATALOGO_PADRAO["semestral"]), 5)
        self.assertEqual(previstas_no_plano(CATALOGO_PADRAO["anual"]), 10)

    def test_mensal_preve_uma_desde_o_primeiro_dia(self):
        p = paciente(inicio=date(2026, 8, 5))
        self.assertEqual(previstas_ate(p, HOJE), 1)

    def test_trimestral_cresce_a_cada_30_dias(self):
        p = paciente(plano="trimestral", inicio=date(2026, 6, 1))
        self.assertEqual(previstas_ate(p, date(2026, 6, 15)), 1)
        self.assertEqual(previstas_ate(p, date(2026, 7, 1)), 2)
        self.assertEqual(previstas_ate(p, date(2026, 8, 5)), 3)

    def test_anual_espaca_em_36_dias(self):
        # 360 dias divididos em 10 consultas.
        p = paciente(plano="anual", inicio=date(2026, 1, 1))
        self.assertEqual(previstas_ate(p, date(2026, 1, 1)), 1)
        self.assertEqual(previstas_ate(p, date(2026, 2, 6)), 2)
        self.assertEqual(previstas_ate(p, date(2026, 12, 31)), 10)

    def test_semestral_espaca_em_36_dias(self):
        p = paciente(plano="semestral", inicio=date(2026, 1, 1))
        self.assertEqual(previstas_ate(p, date(2026, 2, 6)), 2)
        self.assertEqual(previstas_ate(p, date(2026, 6, 30)), 5)

    def test_nao_passa_do_total_do_plano(self):
        p = paciente(plano="trimestral", inicio=date(2026, 1, 1))
        self.assertEqual(previstas_ate(p, date(2026, 12, 1)), 3)

    def test_anual_nunca_passa_de_dez(self):
        p = paciente(plano="anual", inicio=date(2020, 1, 1))
        self.assertEqual(previstas_ate(p, HOJE), 10)

    def test_antes_do_inicio_nao_preve_nada(self):
        p = paciente(inicio=date(2026, 9, 1))
        self.assertEqual(previstas_ate(p, HOJE), 0)


class TestCruzamento(unittest.TestCase):
    def test_conta_avaliacoes_do_paciente(self):
        p = paciente("Bruno Lima", "trimestral", date(2026, 6, 1))
        avaliacoes = [
            Avaliacao("Bruno Lima", date(2026, 6, 1)),
            Avaliacao("Bruno Lima", date(2026, 7, 20)),
        ]
        resumo = cruzar([p], avaliacoes, HOJE).de(p)
        self.assertEqual(resumo.realizadas, 2)
        self.assertEqual(resumo.previstas_total, 3)
        self.assertEqual(resumo.previstas_ate_hoje, 3)
        self.assertEqual(resumo.deficit, 1)
        self.assertFalse(resumo.em_dia)

    def test_paciente_em_dia(self):
        p = paciente("Ana Souza")
        resumo = cruzar([p], [Avaliacao("Ana Souza", date(2026, 7, 15))], HOJE).de(p)
        self.assertTrue(resumo.em_dia)
        self.assertEqual(resumo.deficit, 0)

    def test_nome_com_erro_de_digitacao_e_associado(self):
        p = paciente("Isabela Paiva", "semestral", date(2026, 4, 1))
        avaliacoes = [Avaliacao("Isabel Oaiva", date(2026, 4, 1))]
        resultado = cruzar([p], avaliacoes, HOJE)
        resumo = resultado.de(p)
        self.assertEqual(resumo.realizadas, 1)
        self.assertFalse(resumo.sem_dados)
        self.assertEqual(len(resultado.avisos), 1)

    def test_nome_ambiguo_nao_conta_para_ninguem(self):
        a = paciente("Marcio Souza")
        b = paciente("Marcia Sousa")
        resultado = cruzar([a, b], [Avaliacao("Marcia Souza", date(2026, 7, 20))], HOJE)
        self.assertEqual(resultado.de(a).realizadas, 0)
        self.assertEqual(resultado.de(b).realizadas, 0)
        self.assertEqual(len(resultado.ambiguidades), 1)

    def test_nome_sem_paciente_correspondente(self):
        p = paciente("Ana Souza")
        resultado = cruzar([p], [Avaliacao("Joaquim Nabuco", date(2026, 7, 20))], HOJE)
        self.assertEqual(len(resultado.sem_paciente), 1)
        self.assertEqual(resultado.de(p).realizadas, 0)

    def test_paciente_sem_registro_no_webdiet(self):
        p = paciente("Ana Souza")
        resumo = cruzar([p], [], HOJE).de(p)
        self.assertTrue(resumo.sem_dados)
        self.assertEqual(resumo.realizadas, 0)

    def test_avaliacao_fora_da_vigencia_nao_conta_no_plano(self):
        p = paciente("Ana Souza", "mensal", date(2026, 7, 15))
        avaliacoes = [
            Avaliacao("Ana Souza", date(2026, 3, 1)),  # plano anterior
            Avaliacao("Ana Souza", date(2026, 7, 15)),
        ]
        resumo = cruzar([p], avaliacoes, HOJE).de(p)
        self.assertEqual(resumo.realizadas, 1)
        self.assertEqual(resumo.total_historico, 2)

    def test_ultima_avaliacao_e_registrada(self):
        p = paciente("Carla Nunes", "semestral", date(2026, 3, 10))
        avaliacoes = [
            Avaliacao("Carla Nunes", date(2026, 3, 10)),
            Avaliacao("Carla Nunes", date(2026, 6, 25)),
        ]
        resumo = cruzar([p], avaliacoes, HOJE).de(p)
        self.assertEqual(resumo.ultima, date(2026, 6, 25))


class TestEsgotamento(unittest.TestCase):
    def _resumo(self, p, datas):
        return cruzar([p], [Avaliacao(p.nome, d) for d in datas], HOJE).de(p)

    def test_mensal_usar_a_unica_consulta_e_normal(self):
        # 1 de 1 num plano que acaba em poucos dias não é anomalia.
        p = paciente("Ana Souza", "mensal", date(2026, 7, 15))
        resumo = self._resumo(p, [date(2026, 7, 15)])
        self.assertTrue(resumo.esgotadas)
        self.assertFalse(resumo.esgotadas_cedo(HOJE))

    def test_anual_que_esgotou_cedo_e_sinalizado(self):
        # 10 consultas usadas com meses de plano sobrando.
        inicio = date(2026, 1, 1)
        datas = [inicio + timedelta(days=25 * i) for i in range(10)]
        p = paciente("Diego Alves", "anual", inicio)
        resumo = self._resumo(p, datas)
        self.assertEqual(resumo.realizadas, 10)
        self.assertTrue(resumo.esgotadas_cedo(HOJE))

    def test_quem_ainda_tem_consulta_nao_e_sinalizado(self):
        p = paciente("Bruno Lima", "trimestral", date(2026, 6, 1))
        resumo = self._resumo(p, [date(2026, 6, 1)])
        self.assertFalse(resumo.esgotadas)
        self.assertFalse(resumo.esgotadas_cedo(HOJE))

    def test_sem_dados_nunca_conta_como_esgotado(self):
        p = paciente("Sem Registro", "anual", date(2026, 1, 1))
        resumo = cruzar([p], [], HOJE).de(p)
        self.assertFalse(resumo.esgotadas)

    def test_adiantadas_conta_o_excedente(self):
        inicio = date(2026, 1, 1)
        datas = [inicio + timedelta(days=25 * i) for i in range(8)]
        p = paciente("Diego Alves", "anual", inicio)
        resumo = self._resumo(p, datas)
        self.assertGreater(resumo.adiantadas, 0)


class TestUltimaConsultaDoWebDiet(unittest.TestCase):
    def test_preenche_quando_o_liveclin_nao_tem(self):
        p = paciente("Carla Nunes", "semestral", date(2026, 3, 10))
        self.assertIsNone(p.ultima_consulta)
        cruzamento = cruzar(
            [p],
            [
                Avaliacao("Carla Nunes", date(2026, 3, 10)),
                Avaliacao("Carla Nunes", date(2026, 6, 25)),
            ],
            HOJE,
        )
        ajustes = aplicar_ultima_consulta(cruzamento)
        self.assertEqual(p.ultima_consulta, date(2026, 6, 25))
        self.assertEqual(len(ajustes), 1)

    def test_corrige_data_divergente(self):
        p = paciente("Ana Souza", ultima_consulta=date(2026, 7, 1))
        cruzamento = cruzar([p], [Avaliacao("Ana Souza", date(2026, 7, 20))], HOJE)
        ajustes = aplicar_ultima_consulta(cruzamento)
        self.assertEqual(p.ultima_consulta, date(2026, 7, 20))
        self.assertIn("corrigida", ajustes[0])

    def test_datas_iguais_nao_geram_ajuste(self):
        p = paciente("Ana Souza", ultima_consulta=date(2026, 7, 20))
        cruzamento = cruzar([p], [Avaliacao("Ana Souza", date(2026, 7, 20))], HOJE)
        self.assertEqual(aplicar_ultima_consulta(cruzamento), [])

    def test_sem_avaliacao_mantem_o_que_havia(self):
        p = paciente("Ana Souza", ultima_consulta=date(2026, 7, 1))
        cruzamento = cruzar([p], [], HOJE)
        aplicar_ultima_consulta(cruzamento)
        self.assertEqual(p.ultima_consulta, date(2026, 7, 1))

    def test_nome_ambiguo_nao_altera_data(self):
        a = paciente("Marcio Souza")
        b = paciente("Marcia Sousa")
        cruzamento = cruzar([a, b], [Avaliacao("Marcia Souza", date(2026, 7, 20))], HOJE)
        aplicar_ultima_consulta(cruzamento)
        self.assertIsNone(a.ultima_consulta)
        self.assertIsNone(b.ultima_consulta)


class TestFiltros(unittest.TestCase):
    def test_etiqueta_ignora_caixa_e_acento(self):
        p = paciente(etiquetas=["DANIEL"])
        self.assertTrue(tem_etiqueta(p, "daniel"))

    def test_etiqueta_ausente(self):
        p = paciente(etiquetas=["Roberta"])
        self.assertFalse(tem_etiqueta(p, "Daniel"))

    def test_etiqueta_vazia_aceita_todos(self):
        self.assertTrue(tem_etiqueta(paciente(etiquetas=[]), ""))

    def test_filtra_por_etiqueta_e_status(self):
        ativo = paciente("Ativo Daniel", etiquetas=["Daniel"])
        outro = paciente("Outro Prof", etiquetas=["Roberta"])
        pausado = paciente("Pausado", etiquetas=["Daniel"], status=StatusPaciente.PAUSADO)
        selecionados = aplicar([ativo, outro, pausado], etiqueta="Daniel")
        self.assertEqual([p.nome for p in selecionados], ["Ativo Daniel"])

    def test_incluir_inativos(self):
        ativo = paciente("Ativo", etiquetas=["Daniel"])
        pausado = paciente("Pausado", etiquetas=["Daniel"], status=StatusPaciente.PAUSADO)
        selecionados = aplicar(
            [ativo, pausado], etiqueta="Daniel", somente_ativos=False
        )
        self.assertEqual(len(selecionados), 2)


if __name__ == "__main__":
    unittest.main()
