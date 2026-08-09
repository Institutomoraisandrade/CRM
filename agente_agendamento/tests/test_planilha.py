import tempfile
import unittest
from pathlib import Path

from agente.config import Config, ErroDeConfig
from agente.fontes.base import ErroDeFonte
from agente.fontes.planilha import (
    PlanilhaArquivo,
    PlanilhaGoogleSheets,
    montar_linhas,
)
from agente.planos import CATALOGO_PADRAO


class TestMontarLinhas(unittest.TestCase):
    def test_cabecalho_vira_chave(self):
        linhas = montar_linhas([["Nome", "Plano"], ["Ana", "Mensal"]])
        self.assertEqual(linhas, [{"Nome": "Ana", "Plano": "Mensal"}])

    def test_linha_curta_e_completada(self):
        # O Sheets corta células vazias no fim da linha.
        linhas = montar_linhas([["Nome", "Plano", "Etiqueta"], ["Ana", "Mensal"]])
        self.assertEqual(linhas[0]["Etiqueta"], "")

    def test_matriz_vazia(self):
        self.assertEqual(montar_linhas([]), [])

    def test_so_cabecalho(self):
        self.assertEqual(montar_linhas([["Nome"]]), [])

    def test_espaco_no_cabecalho_e_removido(self):
        linhas = montar_linhas([["  Nome  "], ["Ana"]])
        self.assertEqual(linhas[0]["Nome"], "Ana")


class TestPlanilhaArquivo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def test_arquivo_inexistente(self):
        planilha = PlanilhaArquivo(Path(self.dir.name) / "nao_existe.csv")
        with self.assertRaises(ErroDeFonte):
            planilha.linhas()

    def test_descricao_e_o_caminho(self):
        planilha = PlanilhaArquivo("/tmp/x.csv")
        self.assertIn("x.csv", planilha.descricao)

    def test_le_ponto_e_virgula(self):
        caminho = Path(self.dir.name) / "p.csv"
        caminho.write_text("Nome;Plano\nAna;Mensal\n", encoding="utf-8")
        self.assertEqual(PlanilhaArquivo(caminho).linhas()[0]["Plano"], "Mensal")


class TestPlanilhaGoogleSheets(unittest.TestCase):
    def test_exige_identificador(self):
        with self.assertRaises(ErroDeFonte):
            PlanilhaGoogleSheets("")

    def test_descricao_menciona_a_aba(self):
        planilha = PlanilhaGoogleSheets("abc123", aba="Pacientes")
        self.assertIn("abc123", planilha.descricao)
        self.assertIn("Pacientes", planilha.descricao)


def config(**secoes):
    base = dict(
        raiz=Path("/tmp"),
        fonte={},
        agenda={},
        planos=dict(CATALOGO_PADRAO),
    )
    base.update(secoes)
    return Config(**base)


class TestConfigDaPlanilha(unittest.TestCase):
    def test_arquivo_exige_caminho(self):
        with self.assertRaises(ErroDeConfig) as ctx:
            config(fonte={"tipo": "arquivo"}).construir_fonte()
        self.assertIn("fonte.caminho", str(ctx.exception))

    def test_sheets_exige_spreadsheet_id(self):
        with self.assertRaises(ErroDeConfig) as ctx:
            config(fonte={"tipo": "google_sheets"}).construir_fonte()
        self.assertIn("spreadsheet_id", str(ctx.exception))

    def test_tipo_desconhecido(self):
        with self.assertRaises(ErroDeConfig):
            config(fonte={"tipo": "carteiro"}).construir_fonte()

    def test_sheets_monta_a_planilha(self):
        fonte = config(
            fonte={"tipo": "google_sheets", "spreadsheet_id": "abc123", "aba": "Base"}
        ).construir_fonte()
        self.assertIsInstance(fonte.planilha, PlanilhaGoogleSheets)
        self.assertEqual(fonte.planilha.spreadsheet_id, "abc123")

    def test_webdiet_sem_config_fica_none(self):
        self.assertIsNone(config().construir_fonte_webdiet())

    def test_webdiet_por_sheets(self):
        fonte = config(
            webdiet={"tipo": "google_sheets", "spreadsheet_id": "xyz789"}
        ).construir_fonte_webdiet()
        self.assertIsNotNone(fonte)
        self.assertEqual(fonte.planilha.spreadsheet_id, "xyz789")

    def test_liveclin_csv_continua_valendo(self):
        fonte = config(
            fonte={"tipo": "liveclin_csv", "caminho": "p.csv"}
        ).construir_fonte()
        self.assertIsInstance(fonte.planilha, PlanilhaArquivo)


if __name__ == "__main__":
    unittest.main()
