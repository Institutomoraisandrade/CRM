"""Erro aqui manda mensagem para quem já está agendado — ou, pior, deixa
de fora quem está esperando. Os testes cobrem as duas direções.
"""

import unittest
from datetime import date

from agente.nao_agendados import (
    Agenda,
    Pendencia,
    corresponder,
    homonimos,
    ler_agenda,
    montar_html,
    nome_do_evento,
    separar,
)

HOJE = date(2026, 8, 9)


def evento(titulo, dia="2026-08-20"):
    return {"summary": titulo, "start": {"dateTime": f"{dia}T09:00:00-03:00"}}


def paciente(nome, dias=30, plano="Mensal"):
    return Pendencia(
        nome=nome, plano=plano, fim_do_plano="2026-09-08", dias_restantes=dias
    )


class TestNomeDoEvento(unittest.TestCase):
    def test_formatos_reais_chegam_no_mesmo_nome(self):
        titulos = [
            "Consulta agendada ( Ramon Casado )",
            "Consulta agendada (Ramon Casado)",
            "Consulta Confirmada - Ramon Casado",
            "🟢 CONSULTA — Ramon Casado — CONFIRMADO",
            "🔷 AGENDAR — Ramon Casado — RETORNO",
            "🔷 — AGENDAR | Ramon Casado | RETORNO",
            "Nutricionista Consulta - Ramon Casado",
            "ON-LINE ( Ramon Casado )",
            "Ramon Casado",
        ]
        for titulo in titulos:
            self.assertEqual(nome_do_evento(titulo), "Ramon Casado", titulo)

    def test_tira_anotacao_de_sessao(self):
        self.assertEqual(nome_do_evento("Andressa on-line 2/3"), "Andressa")
        self.assertEqual(nome_do_evento("Andressa Rossi renov online"), "Andressa Rossi")
        self.assertEqual(nome_do_evento("Isabelle parceira"), "Isabelle")

    def test_pega_o_primeiro_de_um_par(self):
        self.assertEqual(nome_do_evento("Nelson Marques + Luciana"), "Nelson Marques")

    def test_titulo_sem_nome(self):
        self.assertEqual(nome_do_evento("⛪"), "")


class TestLerAgenda(unittest.TestCase):
    def test_lembrete_nao_conta_como_agendado(self):
        agenda = ler_agenda([evento("🔷 AGENDAR — Bruna Lins — RETORNO")], HOJE)
        self.assertEqual(agenda.marcados, {})
        self.assertIn("Bruna Lins", agenda.lembretes)

    def test_standby_nao_conta_como_agendado(self):
        agenda = ler_agenda([evento("Consulta em standby ( Caike Henrique )")], HOJE)
        self.assertEqual(agenda.marcados, {})

    def test_consulta_passada_nao_conta(self):
        agenda = ler_agenda([evento("Thiago Porto", "2026-08-08")], HOJE)
        self.assertEqual(agenda.marcados, {})

    def test_consulta_de_hoje_conta(self):
        agenda = ler_agenda([evento("Thiago Porto", "2026-08-09")], HOJE)
        self.assertEqual(agenda.marcados["Thiago Porto"], "2026-08-09")

    def test_vale_a_consulta_mais_proxima(self):
        agenda = ler_agenda(
            [evento("Ana Souza", "2026-09-30"), evento("Ana Souza", "2026-08-15")], HOJE
        )
        self.assertEqual(agenda.marcados["Ana Souza"], "2026-08-15")

    def test_compromisso_que_nao_e_paciente_fica_de_fora(self):
        naos = ["⛪ A PONTE — Igreja", "Junta comercial", "Reunião Contábil"]
        agenda = ler_agenda([evento(t) for t in naos], HOJE)
        self.assertEqual(agenda.marcados, {})

    def test_evento_de_dia_inteiro(self):
        agenda = ler_agenda(
            [{"summary": "Ana Souza", "start": {"date": "2026-08-20"}}], HOJE
        )
        self.assertEqual(agenda.marcados["Ana Souza"], "2026-08-20")


class TestCorresponder(unittest.TestCase):
    def test_cadastro_mais_longo_que_a_agenda(self):
        # O caso que mais aparece: o CRM traz o nome completo.
        self.assertEqual(
            corresponder("Roberto Santos Miranda", ["Roberto Santos"]), "Roberto Santos"
        )
        self.assertEqual(
            corresponder("Matheus Rodrigues da Silva Lira", ["Matheus Lira"]),
            "Matheus Lira",
        )

    def test_primeiro_nome_sozinho_nao_basta(self):
        self.assertIsNone(corresponder("Gabriel", ["Gabriel Bezerra"]))

    def test_acento_e_caixa_nao_atrapalham(self):
        self.assertEqual(corresponder("Lais Sales", ["Laís Sales"]), "Laís Sales")

    def test_pessoas_diferentes_nao_casam(self):
        self.assertIsNone(corresponder("Lucas Duro", ["Lucas Perrusi"]))

    def test_sem_candidatos(self):
        self.assertIsNone(corresponder("Ana Souza", []))


class TestHomonimos(unittest.TestCase):
    def test_nome_solto_vira_duvida(self):
        self.assertEqual(homonimos("Gabriel", ["Gabriel Bezerra"]), ["Gabriel Bezerra"])

    def test_agenda_com_nome_solto_tambem_e_duvida(self):
        self.assertEqual(homonimos("Beatriz Carvalho", ["Beatriz"]), ["Beatriz"])

    def test_dois_nomes_completos_nao_sao_duvida(self):
        self.assertEqual(homonimos("Ana Souza", ["Ana Lima"]), [])

    def test_primeiro_nome_diferente(self):
        self.assertEqual(homonimos("Ana Souza", ["Bruno Souza"]), [])


class TestSeparar(unittest.TestCase):
    def test_quem_tem_consulta_futura_sai_da_fila(self):
        agenda = Agenda(marcados={"Ana Souza": "2026-08-20"})
        r = separar([paciente("Ana Souza")], agenda)
        self.assertEqual(r.a_agendar, [])
        self.assertEqual(r.ja_agendados, [("Ana Souza", "2026-08-20")])

    def test_so_lembrete_continua_na_fila(self):
        agenda = Agenda(lembretes={"Ana Souza"})
        r = separar([paciente("Ana Souza")], agenda)
        self.assertEqual(len(r.a_agendar), 1)
        self.assertTrue(r.a_agendar[0].tem_lembrete)

    def test_paciente_do_outro_profissional_sai(self):
        r = separar([paciente("Nathalie")], Agenda(), agenda_de_outro={"Nathalie"})
        self.assertEqual(r.a_agendar, [])
        self.assertEqual(r.de_outro_profissional, [("Nathalie", "Nathalie")])

    def test_homonimo_vai_para_conferir_com_motivo(self):
        agenda = Agenda(marcados={"Rebeca": "2026-08-11"})
        r = separar([paciente("Rebeca Imperiano")], agenda)
        self.assertEqual(r.a_agendar, [])
        self.assertEqual(len(r.conferir), 1)
        self.assertIn("Rebeca", r.conferir[0].observacao)

    def test_homonimo_do_outro_profissional_tambem_vai_conferir(self):
        r = separar([paciente("Beatriz Carvalho")], Agenda(), agenda_de_outro={"Beatriz"})
        self.assertEqual(len(r.conferir), 1)

    def test_ordena_por_urgencia(self):
        fila = [paciente("Com Folga", 200), paciente("Vence Ja", 3)]
        r = separar(fila, Agenda())
        self.assertEqual([p.nome for p in r.a_agendar], ["Vence Ja", "Com Folga"])

    def test_ninguem_se_perde(self):
        fila = [
            paciente("Ja Agendado"),
            paciente("Do Outro"),
            paciente("Rebeca Imperiano"),
            paciente("Livre Um"),
        ]
        agenda = Agenda(marcados={"Ja Agendado": "2026-08-20", "Rebeca": "2026-08-11"})
        r = separar(fila, agenda, agenda_de_outro={"Do Outro"})
        total = (
            len(r.a_agendar)
            + len(r.conferir)
            + len(r.ja_agendados)
            + len(r.de_outro_profissional)
        )
        self.assertEqual(total, len(fila))


class TestHtml(unittest.TestCase):
    def test_traz_as_quatro_secoes(self):
        html = montar_html(separar([paciente("Ana Souza")], Agenda()), HOJE)
        for titulo in ("Agendar", "Conferir antes de chamar", "Já têm consulta marcada"):
            self.assertIn(titulo, html)

    def test_mostra_o_aviso(self):
        html = montar_html(separar([], Agenda()), HOJE, aviso="sem etiqueta")
        self.assertIn("sem etiqueta", html)

    def test_escapa_nome(self):
        html = montar_html(separar([paciente("<script>x</script>")], Agenda()), HOJE)
        self.assertNotIn("<script>", html)

    def test_marca_quem_ja_tem_lembrete(self):
        r = separar([paciente("Ana Souza")], Agenda(lembretes={"Ana Souza"}))
        self.assertIn("AGENDAR", montar_html(r, HOJE))

    def test_lista_vazia_nao_quebra(self):
        self.assertIn("Ninguém", montar_html(separar([], Agenda()), HOJE))


if __name__ == "__main__":
    unittest.main()
