"""A captura não pode vazar dado de paciente."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))

from capturar_liveclin import formato, interessante  # noqa: E402


class TestOcultacao(unittest.TestCase):
    def test_campos_de_pessoa_somem(self):
        dados = {
            "nome": "Isabela Paiva",
            "email": "isa@exemplo.com",
            "telefone": "5581999250440",
            "cpf": "01350353418",
            "data_nascimento": "27/10/1997",
        }
        saida = formato(dados)
        for campo in dados:
            self.assertEqual(saida[campo], "<oculto>", campo)

    def test_credenciais_somem(self):
        saida = formato({"token": "eyJhbGci.x", "password": "1234", "senha": "abc"})
        self.assertEqual(set(saida.values()), {"<oculto>"})

    def test_nome_de_pessoa_aninhado_some(self):
        saida = formato({"responsavel": {"nome": "Daniel Andrade"}})
        self.assertEqual(saida["responsavel"]["nome"], "<oculto>")

    def test_nenhum_valor_de_pessoa_sobra_no_json(self):
        import json

        bruto = {
            "pacientes": [
                {"nome": "Isabela Paiva", "email": "isa@x.com", "cpf": "013"},
                {"nome": "Kalil Ferraz", "email": "kalil@x.com", "cpf": "014"},
            ]
        }
        texto = json.dumps(formato(bruto), ensure_ascii=False)
        for vazamento in ("Isabela", "Paiva", "isa@x.com", "Kalil", "013"):
            self.assertNotIn(vazamento, texto, vazamento)


class TestCategoricos(unittest.TestCase):
    def test_etiqueta_e_preservada(self):
        saida = formato({"etiquetas": ["Ativos - Daniel", "emagrecimento"]})
        self.assertEqual(saida["etiquetas"][0], "Ativos - Daniel")

    def test_nome_do_plano_e_preservado(self):
        saida = formato({"plano": {"nome": "Semestral", "dias": 180}})
        self.assertEqual(saida["plano"]["nome"], "Semestral")

    def test_status_e_preservado(self):
        self.assertEqual(formato({"status": "ativo"})["status"], "ativo")

    def test_texto_categorico_gigante_nao_passa(self):
        saida = formato({"tipo": "x" * 200})
        self.assertTrue(saida["tipo"].startswith("<str"))


class TestEstrutura(unittest.TestCase):
    def test_tipos_sao_preservados(self):
        saida = formato({"id": 8821, "ativo": True, "peso": 72.4, "nada": None})
        self.assertEqual(saida["id"], "int")
        self.assertEqual(saida["ativo"], True)
        self.assertEqual(saida["peso"], "float")
        self.assertIsNone(saida["nada"])

    def test_lista_mostra_o_tamanho(self):
        saida = formato({"itens": [{"a": 1}, {"a": 2}, {"a": 3}]})
        self.assertIn("3 itens", saida["itens"][1])

    def test_lista_vazia(self):
        self.assertEqual(formato({"itens": []})["itens"], [])

    def test_datas_sao_sinalizadas(self):
        self.assertIn("data?", formato({"inicio": "02/11/2025"})["inicio"])

    def test_profundidade_tem_limite(self):
        fundo = atual = {}
        for _ in range(20):
            atual["n"] = {}
            atual = atual["n"]
        self.assertIn("...", str(formato(fundo)))


class TestFiltroDeUrl(unittest.TestCase):
    def test_aceita_api(self):
        self.assertTrue(interessante("https://v2.liveclin.com/api/patients?tag=1"))
        self.assertTrue(interessante("https://v2.liveclin.com/v1/appointments"))

    def test_recusa_estatico(self):
        for url in ("https://x.com/app.js", "https://x.com/a.css", "https://x.com/l.png"):
            self.assertFalse(interessante(url), url)


if __name__ == "__main__":
    unittest.main()
