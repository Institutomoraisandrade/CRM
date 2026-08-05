import unittest
from datetime import date

from agente.consultas import cruzar, previstas_ate, previstas_no_plano
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
    def test_total_por_plano(self):
        self.assertEqual(previstas_no_plano(30), 1)
        self.assertEqual(previstas_no_plano(90), 3)
        self.assertEqual(previstas_no_plano(180), 6)
        self.assertEqual(previstas_no_plano(360), 12)

    def test_mensal_preve_uma_desde_o_primeiro_dia(self):
        p = paciente(inicio=date(2026, 8, 5))
        self.assertEqual(previstas_ate(p, HOJE), 1)

    def test_trimestral_cresce_a_cada_30_dias(self):
        p = paciente(plano="trimestral", inicio=date(2026, 6, 1))
        self.assertEqual(previstas_ate(p, date(2026, 6, 15)), 1)
        self.assertEqual(previstas_ate(p, date(2026, 7, 1)), 2)
        self.assertEqual(previstas_ate(p, date(2026, 8, 5)), 3)

    def test_nao_passa_do_total_do_plano(self):
        p = paciente(plano="trimestral", inicio=date(2026, 1, 1))
        self.assertEqual(previstas_ate(p, date(2026, 12, 1)), 3)

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
