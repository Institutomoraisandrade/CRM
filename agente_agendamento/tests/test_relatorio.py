import unittest
from datetime import date, datetime
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

from agente.modelos import Agendamento, Paciente, SituacaoAgendamento, StatusPaciente
from agente.notificacoes import alertas_pendentes
from agente.planos import CATALOGO_PADRAO
from agente.relatorio import montar

SP = ZoneInfo("America/Sao_Paulo")
HOJE = date(2026, 8, 5)


class ChecadorHTML(HTMLParser):
    """Confere se as tags abrem e fecham na ordem certa."""

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
            self.erros.append(f"</{tag}> inesperado")
        else:
            self.pilha.pop()


def paciente(nome="Ana Souza", **kwargs):
    base = dict(
        nome=nome,
        plano=CATALOGO_PADRAO["mensal"],
        plano_inicio=date(2026, 7, 15),
        plano_fim=date(2026, 8, 14),
        status=StatusPaciente.ATIVO,
        ultima_consulta=date(2026, 7, 15),
        whatsapp="5511999990000",
    )
    base.update(kwargs)
    return Paciente(**base)


def agendamento(p, situacao=SituacaoAgendamento.AGENDAVEL, dia=14, motivo="30 dias"):
    if situacao in (SituacaoAgendamento.AGENDAVEL, SituacaoAgendamento.ATRASADO):
        inicio = datetime(2026, 8, dia, 17, 0, tzinfo=SP)
        fim = datetime(2026, 8, dia, 17, 50, tzinfo=SP)
    else:
        inicio = fim = None
    return Agendamento(
        paciente=p,
        situacao=situacao,
        limite=date(2026, 8, 14),
        inicio=inicio,
        fim=fim,
        motivo=motivo,
    )


class TestConteudo(unittest.TestCase):
    def test_conta_os_numeros_do_topo(self):
        ativos = [paciente("Ana Souza"), paciente("Bruno Lima")]
        pausado = paciente("Fabio Costa", status=StatusPaciente.PAUSADO)
        ags = [agendamento(ativos[0]), agendamento(ativos[1])]
        rel = montar([*ativos, pausado], ags, [], HOJE)
        self.assertEqual(len(rel.ativos), 2)
        self.assertEqual(len(rel.marcados), 2)
        self.assertEqual(len(rel.pendencias), 0)

    def test_pendencias_separam_sem_vaga_e_vencido(self):
        p1 = paciente("Sem Vaga")
        p2 = paciente("Vencido", plano_fim=date(2026, 7, 20))
        ags = [
            agendamento(p1, SituacaoAgendamento.SEM_VAGA),
            agendamento(p2, SituacaoAgendamento.PLANO_VENCIDO),
        ]
        rel = montar([p1, p2], ags, [], HOJE)
        self.assertEqual(len(rel.pendencias), 2)
        self.assertEqual(len(rel.marcados), 0)

    def test_ja_agendado_nao_conta_como_marcado(self):
        p = paciente()
        rel = montar([p], [agendamento(p, SituacaoAgendamento.JA_AGENDADO)], [], HOJE)
        self.assertEqual(len(rel.marcados), 0)
        self.assertEqual(len(rel.pendencias), 0)

    def test_alertas_urgentes_vem_primeiro(self):
        atrasado = paciente("Carla Nunes", ultima_consulta=date(2026, 6, 25),
                            plano_fim=date(2026, 9, 6))
        vencendo = paciente("Eva Ramos", plano_fim=date(2026, 8, 9))
        alertas = alertas_pendentes([vencendo, atrasado], HOJE)
        rel = montar([vencendo, atrasado], [], alertas, HOJE)
        self.assertEqual(rel.alertas[0].paciente.nome, "Carla Nunes")

    def test_assunto_conta_quem_precisa_ser_agendado(self):
        p = paciente()
        rel = montar([p], [agendamento(p, SituacaoAgendamento.ATRASADO, dia=6)], [], HOJE)
        self.assertIn("05/08", rel.assunto)
        self.assertIn("1 paciente(s) para agendar", rel.assunto)

    def test_assunto_quando_nao_ha_nada(self):
        rel = montar([], [], [], HOJE)
        self.assertIn("nada pendente", rel.assunto)


class TestTexto(unittest.TestCase):
    def test_texto_lista_retornos_programados(self):
        p = paciente()
        texto = montar([p], [agendamento(p)], [], HOJE).texto()
        self.assertIn("Ana Souza", texto)
        self.assertIn("14/08/2026 17:00", texto)
        self.assertIn("AGENDA — RETORNOS", texto)

    def test_texto_avisa_que_nada_foi_ao_paciente(self):
        rel = montar([], [], [], HOJE)
        self.assertIn("Nada foi enviado aos pacientes", rel.texto())

    def test_secoes_vazias_somem(self):
        texto = montar([], [], [], HOJE).texto()
        self.assertNotIn("ALERTAS", texto)
        self.assertNotIn("RETORNOS", texto)


class TestHTML(unittest.TestCase):
    def _html(self):
        atrasado = paciente("Carla Nunes", ultima_consulta=date(2026, 6, 25),
                            plano_fim=date(2026, 9, 6))
        vencendo = paciente("Eva Ramos", plano_fim=date(2026, 8, 9))
        pacientes = [paciente(), atrasado, vencendo]
        ags = [
            agendamento(pacientes[0]),
            agendamento(atrasado, SituacaoAgendamento.ATRASADO, dia=6),
            agendamento(vencendo, SituacaoAgendamento.SEM_VAGA),
        ]
        return montar(pacientes, ags, alertas_pendentes(pacientes, HOJE), HOJE).html()

    def test_html_bem_formado(self):
        checador = ChecadorHTML()
        checador.feed(self._html())
        self.assertEqual(checador.erros, [])
        self.assertEqual(checador.pilha, [])

    def test_html_traz_as_secoes(self):
        html = self._html()
        self.assertIn("Agendar agora", html)
        self.assertIn("Agenda de retornos", html)
        self.assertIn("Alertas de hoje", html)

    def test_html_sem_pendencia_mostra_tudo_em_dia(self):
        html = montar([paciente()], [], [], HOJE).html()
        self.assertIn("Ninguém precisa ser agendado hoje", html)

    def test_html_vazio_ainda_e_valido(self):
        checador = ChecadorHTML()
        checador.feed(montar([], [], [], HOJE).html())
        self.assertEqual(checador.pilha, [])

    def test_nome_com_html_e_escapado(self):
        p = paciente(nome="Ana <script>alert(1)</script>")
        html = montar([p], [agendamento(p)], [], HOJE).html()
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_planos_terminando_aparecem(self):
        vencendo = paciente("Eva Ramos", plano_fim=date(2026, 8, 9))
        html = montar([vencendo], [], [], HOJE).html()
        self.assertIn("Planos terminando", html)
        self.assertIn("vence em 4 dias", html)

    def test_plano_longe_nao_aparece_na_secao_de_vigencia(self):
        longe = paciente("Diego Alves", plano_fim=date(2026, 12, 31))
        html = montar([longe], [], [], HOJE).html()
        self.assertNotIn("Planos terminando", html)


if __name__ == "__main__":
    unittest.main()
