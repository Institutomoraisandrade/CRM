import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from agente.fontes.base import ErroDeFonte
from agente.fontes.liveclin_csv import FonteLiveClinCSV
from agente.modelos import StatusPaciente


class BaseCSV(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def escrever(self, conteudo: str, nome: str = "pacientes.csv") -> Path:
        caminho = Path(self.dir.name) / nome
        caminho.write_text(conteudo, encoding="utf-8")
        return caminho


class TestLeituraBasica(BaseCSV):
    def test_le_colunas_padrao(self):
        caminho = self.escrever(
            "Nome,Plano,Início do plano,Última consulta,WhatsApp,Status\n"
            "Ana Souza,mensal,01/03/2026,10/03/2026,(11) 99999-8888,Ativo\n"
        )
        pacientes = FonteLiveClinCSV(caminho).carregar()
        self.assertEqual(len(pacientes), 1)
        p = pacientes[0]
        self.assertEqual(p.nome, "Ana Souza")
        self.assertEqual(p.plano.nome, "mensal")
        self.assertEqual(p.plano_inicio, date(2026, 3, 1))
        self.assertEqual(p.plano_fim, date(2026, 3, 31))
        self.assertEqual(p.ultima_consulta, date(2026, 3, 10))
        self.assertEqual(p.whatsapp, "11999998888")
        self.assertEqual(p.status, StatusPaciente.ATIVO)

    def test_aceita_ponto_e_virgula(self):
        caminho = self.escrever(
            "Nome;Plano;Data início;Status\n" "Bruno Lima;trimestral;01/02/2026;Pausado\n"
        )
        pacientes = FonteLiveClinCSV(caminho).carregar()
        self.assertEqual(pacientes[0].status, StatusPaciente.PAUSADO)
        self.assertEqual(pacientes[0].plano_fim, date(2026, 5, 2))

    def test_cabecalho_sem_acento_e_em_caixa_alta(self):
        caminho = self.escrever("NOME,PLANO SELECIONADO,DATA INICIO\nCarla,anual,05/01/2026\n")
        pacientes = FonteLiveClinCSV(caminho).carregar()
        self.assertEqual(pacientes[0].plano.nome, "anual")

    def test_data_iso_e_com_hora(self):
        caminho = self.escrever(
            "Nome,Plano,Data início,Última consulta\n"
            "Diego,semestral,2026-01-05,2026-03-10 14:30\n"
        )
        p = FonteLiveClinCSV(caminho).carregar()[0]
        self.assertEqual(p.plano_inicio, date(2026, 1, 5))
        self.assertEqual(p.ultima_consulta, date(2026, 3, 10))

    def test_apelidos_de_plano(self):
        caminho = self.escrever(
            "Nome,Plano,Data início\n"
            "Um,30 dias,01/03/2026\n"
            "Dois,3 meses,01/03/2026\n"
            "Tres,1 ano,01/03/2026\n"
        )
        pacientes = FonteLiveClinCSV(caminho).carregar()
        self.assertEqual([p.plano.nome for p in pacientes], ["mensal", "trimestral", "anual"])

    def test_fim_explicito_vence_o_calculado(self):
        caminho = self.escrever(
            "Nome,Plano,Data início,Vencimento\nEva,mensal,01/03/2026,15/04/2026\n"
        )
        self.assertEqual(FonteLiveClinCSV(caminho).carregar()[0].plano_fim, date(2026, 4, 15))

    def test_deduz_inicio_a_partir_do_fim(self):
        caminho = self.escrever("Nome,Plano,Vencimento\nFabio,mensal,31/03/2026\n")
        p = FonteLiveClinCSV(caminho).carregar()[0]
        self.assertEqual(p.plano_inicio, date(2026, 3, 1))

    def test_etiquetas(self):
        caminho = self.escrever(
            "Nome,Plano,Data início,Etiquetas\nGil,mensal,01/03/2026,\"emagrecimento, vip\"\n"
        )
        self.assertEqual(
            FonteLiveClinCSV(caminho).carregar()[0].etiquetas, ["emagrecimento", "vip"]
        )

    def test_mapeamento_manual_de_coluna(self):
        caminho = self.escrever("Cliente,Pacote,Começou em\nHelena,mensal,01/03/2026\n")
        fonte = FonteLiveClinCSV(
            caminho,
            colunas={"nome": "Cliente", "plano": "Pacote", "plano_inicio": "Começou em"},
        )
        self.assertEqual(fonte.carregar()[0].nome, "Helena")


class TestLinhasProblematicas(BaseCSV):
    def test_linha_sem_plano_vira_aviso(self):
        caminho = self.escrever(
            "Nome,Plano,Data início\nIvo,,01/03/2026\nJoana,mensal,01/03/2026\n"
        )
        fonte = FonteLiveClinCSV(caminho)
        pacientes = fonte.carregar()
        self.assertEqual([p.nome for p in pacientes], ["Joana"])
        self.assertEqual(len(fonte.avisos), 1)
        self.assertIn("Ivo", fonte.avisos[0])

    def test_plano_desconhecido_vira_aviso(self):
        caminho = self.escrever("Nome,Plano,Data início\nKarl,quinzenal,01/03/2026\n")
        fonte = FonteLiveClinCSV(caminho)
        self.assertEqual(fonte.carregar(), [])
        self.assertIn("quinzenal", fonte.avisos[0])

    def test_consulta_no_futuro_vira_aviso(self):
        amanha = date.today() + timedelta(days=1)
        caminho = self.escrever(
            f"Nome,Plano,Data início,Última consulta\nLia,mensal,01/03/2026,{amanha:%d/%m/%Y}\n"
        )
        fonte = FonteLiveClinCSV(caminho)
        self.assertEqual(fonte.carregar(), [])
        self.assertIn("futuro", fonte.avisos[0])

    def test_fim_anterior_ao_inicio_vira_aviso(self):
        caminho = self.escrever(
            "Nome,Plano,Data início,Vencimento\nMara,mensal,01/03/2026,01/02/2026\n"
        )
        fonte = FonteLiveClinCSV(caminho)
        self.assertEqual(fonte.carregar(), [])
        self.assertIn("anterior", fonte.avisos[0])

    def test_data_invalida_vira_aviso(self):
        caminho = self.escrever("Nome,Plano,Data início\nNilo,mensal,ontem\n")
        fonte = FonteLiveClinCSV(caminho)
        self.assertEqual(fonte.carregar(), [])
        self.assertIn("não reconhecido", fonte.avisos[0])

    def test_linha_em_branco_e_pulada(self):
        caminho = self.escrever("Nome,Plano,Data início\n,,\nOtavio,mensal,01/03/2026\n")
        fonte = FonteLiveClinCSV(caminho)
        self.assertEqual([p.nome for p in fonte.carregar()], ["Otavio"])


class TestErrosFatais(BaseCSV):
    def test_arquivo_inexistente(self):
        with self.assertRaises(ErroDeFonte):
            FonteLiveClinCSV(Path(self.dir.name) / "nao_existe.csv").carregar()

    def test_planilha_vazia(self):
        with self.assertRaises(ErroDeFonte):
            FonteLiveClinCSV(self.escrever("")).carregar()

    def test_sem_coluna_obrigatoria(self):
        caminho = self.escrever("Apelido,Observação\nPaulo,nada\n")
        with self.assertRaises(ErroDeFonte) as ctx:
            FonteLiveClinCSV(caminho).carregar()
        self.assertIn("nome", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
