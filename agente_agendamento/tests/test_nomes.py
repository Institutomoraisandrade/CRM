import unittest

from agente.nomes import casar, normalizar, semelhanca, tokens

BASE = [
    "Isabela Paiva",
    "Ana Carolina Souza",
    "Bruno Lima",
    "Carla Nunes",
    "Diego Alves",
    "Marcos Antonio Silva",
]


class TestNormalizacao(unittest.TestCase):
    def test_tira_acento_e_caixa(self):
        self.assertEqual(normalizar("Marcos ANTÔNIO Silva"), "marcos antonio silva")

    def test_tira_pontuacao_e_espaco_extra(self):
        self.assertEqual(normalizar("  Souza,  Ana-Carolina  "), "souza ana carolina")

    def test_tokens_ignoram_particulas(self):
        self.assertEqual(tokens("Maria de Souza dos Santos"), ["maria", "souza", "santos"])


class TestSemelhanca(unittest.TestCase):
    def test_identico(self):
        self.assertEqual(semelhanca("Bruno Lima", "Bruno Lima"), 1.0)

    def test_so_muda_acento(self):
        self.assertEqual(semelhanca("Marcos Antônio Silva", "Marcos Antonio Silva"), 1.0)

    def test_ordem_do_sobrenome_trocada(self):
        self.assertGreater(semelhanca("Souza Ana Carolina", "Ana Carolina Souza"), 0.9)

    def test_abreviacao_de_nome_do_meio(self):
        self.assertGreater(semelhanca("Ana C Souza", "Ana Carolina Souza"), 0.9)

    def test_nomes_diferentes_ficam_baixo(self):
        self.assertLess(semelhanca("Bruno Lima", "Carla Nunes"), 0.5)

    def test_vazio_nao_quebra(self):
        self.assertEqual(semelhanca("", "Bruno Lima"), 0.0)


class TestCasamento(unittest.TestCase):
    def test_erro_de_digitacao_do_enunciado(self):
        # "Isabel Oaiva" deve virar "Isabela Paiva".
        resultado = casar("Isabel Oaiva", BASE)
        self.assertEqual(resultado.escolhido, "Isabela Paiva")
        self.assertFalse(resultado.exato)
        self.assertGreater(resultado.nota, 0.85)

    def test_casamento_exato_e_marcado_como_exato(self):
        resultado = casar("Bruno Lima", BASE)
        self.assertEqual(resultado.escolhido, "Bruno Lima")
        self.assertTrue(resultado.exato)

    def test_nome_desconhecido_nao_casa(self):
        resultado = casar("Joaquim Nabuco", BASE)
        self.assertIsNone(resultado.escolhido)
        self.assertFalse(resultado.ambiguo)
        self.assertIn("não bateu", resultado.explicar())

    def test_ambiguidade_nao_escolhe_ninguem(self):
        # "Marcia Souza" fica igualmente perto de dois cadastros reais:
        # trocar a última letra do nome ou do sobrenome custa o mesmo.
        base = ["Marcio Souza", "Marcia Sousa"]
        resultado = casar("Marcia Souza", base)
        self.assertIsNone(resultado.escolhido)
        self.assertTrue(resultado.ambiguo)
        self.assertIn("ambíguo", resultado.explicar())

    def test_ambiguidade_lista_os_candidatos(self):
        resultado = casar("Marcia Souza", ["Marcio Souza", "Marcia Sousa"])
        self.assertEqual(len(resultado.candidatos), 2)

    def test_vencedor_folgado_nao_e_ambiguo(self):
        # Aqui a diferença é clara, então o agente decide sozinho.
        resultado = casar("Ana Silvia", ["Ana Silva", "Ana Silvo"])
        self.assertEqual(resultado.escolhido, "Ana Silva")
        self.assertFalse(resultado.ambiguo)

    def test_empate_exato_nao_e_ambiguo(self):
        # Nome idêntico vence mesmo com um parecido ao lado.
        resultado = casar("Bruno Lima", ["Bruno Lima", "Bruno Lino"])
        self.assertEqual(resultado.escolhido, "Bruno Lima")

    def test_lista_vazia(self):
        resultado = casar("Qualquer Um", [])
        self.assertIsNone(resultado.escolhido)
        self.assertEqual(resultado.candidatos, [])

    def test_limiar_configuravel(self):
        frouxo = casar("Joaquim Nabuco", BASE, limiar=0.1, margem=0.0)
        self.assertIsNotNone(frouxo.escolhido)


if __name__ == "__main__":
    unittest.main()
