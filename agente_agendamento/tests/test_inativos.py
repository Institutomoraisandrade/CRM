import unittest
from datetime import date

from agente.consultas import cruzar
from agente.fontes.webdiet_csv import Avaliacao
from agente.inativos import RelatorioInativos, agrupar_por_faixa, levantar
from agente.modelos import Paciente, StatusPaciente
from agente.planos import CATALOGO_PADRAO

HOJE = date(2026, 8, 5)


def paciente(nome="Ana Souza", plano="mensal", inicio=date(2026, 6, 1),
             status=StatusPaciente.ATIVO, ultima=None, profissional="Daniel"):
    p = CATALOGO_PADRAO[plano]
    return Paciente(
        nome=nome,
        plano=p,
        plano_inicio=inicio,
        plano_fim=p.data_fim(inicio),
        status=status,
        ultima_consulta=ultima,
        whatsapp="5581999990000",
        etiquetas=[f"Ativos - {profissional}"],
    )


class TestQuemEntra(unittest.TestCase):
    def test_plano_vencido_entra(self):
        p = paciente(inicio=date(2026, 6, 1))  # mensal, venceu 01/07
        self.assertEqual(len(levantar([p], HOJE)), 1)

    def test_plano_vigente_fica_fora(self):
        p = paciente(inicio=date(2026, 7, 20))
        self.assertEqual(levantar([p], HOJE), [])

    def test_status_inativo_entra_mesmo_com_plano_vigente(self):
        p = paciente(inicio=date(2026, 7, 20), status=StatusPaciente.INATIVO)
        self.assertEqual(len(levantar([p], HOJE)), 1)

    def test_pausado_fica_fora(self):
        # Pausa é combinada, não abandono.
        p = paciente(inicio=date(2026, 6, 1), status=StatusPaciente.PAUSADO)
        self.assertEqual(levantar([p], HOJE), [])


class TestTempoParado(unittest.TestCase):
    def test_conta_da_ultima_consulta_quando_existe(self):
        p = paciente(inicio=date(2026, 6, 1), ultima=date(2026, 6, 20))
        item = levantar([p], HOJE)[0]
        self.assertEqual(item.desde, date(2026, 6, 20))
        self.assertEqual(item.origem_da_data, "última consulta")

    def test_cai_no_fim_do_plano_sem_consulta(self):
        p = paciente(inicio=date(2026, 6, 1))
        item = levantar([p], HOJE)[0]
        self.assertEqual(item.desde, date(2026, 7, 1))
        self.assertEqual(item.origem_da_data, "fim do plano")

    def test_usa_o_webdiet_quando_disponivel(self):
        p = paciente("Carla Nunes", "trimestral", date(2026, 1, 1))
        cruzamento = cruzar([p], [Avaliacao("Carla Nunes", date(2026, 3, 15))], HOJE)
        item = levantar([p], HOJE, cruzamento)[0]
        self.assertEqual(item.desde, date(2026, 3, 15))
        self.assertEqual(item.consultas_feitas, 1)
        self.assertEqual(item.consultas_previstas, 3)

    def test_texto_do_tempo(self):
        casos = [
            (date(2026, 8, 4), "1 dia"),
            (date(2026, 7, 25), "11 dias"),
            (date(2026, 6, 20), "1 mês"),
            (date(2026, 2, 5), "6 meses"),
            (date(2025, 7, 5), "1 ano e 1 mês"),
        ]
        for desde, esperado in casos:
            # Status inativo para entrar na lista mesmo com plano vigente.
            p = paciente(
                inicio=desde, ultima=desde, status=StatusPaciente.INATIVO
            )
            item = levantar([p], HOJE)[0]
            self.assertEqual(item.tempo_parado(HOJE), esperado, f"desde {desde}")

    def test_nunca_conta_tempo_negativo(self):
        p = paciente(inicio=date(2026, 8, 1), status=StatusPaciente.INATIVO)
        self.assertGreaterEqual(levantar([p], HOJE)[0].dias_parado(HOJE), 0)


class TestOrdemEFaixas(unittest.TestCase):
    def test_mais_recente_primeiro(self):
        antigo = paciente("Antigo", inicio=date(2025, 1, 1), ultima=date(2025, 2, 1))
        recente = paciente("Recente", inicio=date(2026, 6, 1), ultima=date(2026, 6, 25))
        nomes = [i.nome for i in levantar([antigo, recente], HOJE)]
        self.assertEqual(nomes, ["Recente", "Antigo"])

    def test_faixas_em_ordem(self):
        pacientes = [
            paciente("Recente", inicio=date(2026, 7, 1), ultima=date(2026, 7, 20)),
            paciente("Meio", inicio=date(2026, 4, 1), ultima=date(2026, 4, 10)),
            paciente("Antigo", inicio=date(2024, 1, 1), ultima=date(2024, 2, 1)),
        ]
        grupos = agrupar_por_faixa(levantar(pacientes, HOJE), HOJE)
        self.assertEqual(
            list(grupos), ["até 1 mês", "3 a 6 meses", "mais de 1 ano"]
        )

    def test_concluiu_o_plano(self):
        p = paciente("Kalil", "trimestral", date(2026, 1, 1))
        avaliacoes = [
            Avaliacao("Kalil", d)
            for d in (date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1))
        ]
        item = levantar([p], HOJE, cruzar([p], avaliacoes, HOJE))[0]
        self.assertTrue(item.concluiu_o_plano)

    def test_nao_concluiu(self):
        p = paciente("Bruna", "trimestral", date(2026, 1, 1))
        item = levantar([p], HOJE, cruzar([p], [Avaliacao("Bruna", date(2026, 1, 1))], HOJE))[0]
        self.assertFalse(item.concluiu_o_plano)


class TestRelatorio(unittest.TestCase):
    def _rel(self):
        pacientes = [
            paciente("Ana Souza", inicio=date(2026, 6, 1), ultima=date(2026, 6, 20)),
            paciente("Laura Helena", inicio=date(2025, 1, 1), ultima=date(2025, 3, 1),
                     profissional="Juliana"),
        ]
        return RelatorioInativos(levantar(pacientes, HOJE), HOJE)

    def test_assunto_conta(self):
        self.assertIn("2 pacientes inativos", self._rel().assunto)

    def test_assunto_vazio(self):
        self.assertIn("nenhum", RelatorioInativos([], HOJE).assunto)

    def test_texto_traz_tempo_e_profissional(self):
        texto = self._rel().texto()
        self.assertIn("Ana Souza", texto)
        self.assertIn("parado há", texto)
        self.assertIn("Juliana", texto)

    def test_html_bem_formado(self):
        from html.parser import HTMLParser

        class Checador(HTMLParser):
            VAZIAS = {"br", "img", "meta", "hr", "input"}

            def __init__(self):
                super().__init__()
                self.pilha = []
                self.erros = []

            def handle_starttag(self, tag, attrs):
                if tag not in self.VAZIAS:
                    self.pilha.append(tag)

            def handle_endtag(self, tag):
                if not self.pilha or self.pilha[-1] != tag:
                    self.erros.append(tag)
                else:
                    self.pilha.pop()

        checador = Checador()
        checador.feed(self._rel().html())
        self.assertEqual(checador.erros, [])
        self.assertEqual(checador.pilha, [])

    def test_html_vazio_e_valido(self):
        html = RelatorioInativos([], HOJE).html()
        self.assertIn("Nenhum paciente inativo", html)

    def test_nome_com_html_e_escapado(self):
        p = paciente("<script>x</script>", inicio=date(2026, 6, 1))
        html = RelatorioInativos(levantar([p], HOJE), HOJE).html()
        self.assertNotIn("<script>", html)


if __name__ == "__main__":
    unittest.main()
