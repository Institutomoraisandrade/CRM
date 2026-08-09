import smtplib
import unittest
from unittest import mock

from agente.entrega.email import EnviadorEmail, ErroDeEnvio


def enviador(**kwargs):
    base = dict(
        remetente="agente@exemplo.com",
        destinatarios=["suporte@exemplo.com"],
        servidor="smtp.exemplo.com",
        porta=587,
    )
    base.update(kwargs)
    return EnviadorEmail(**base)


class TestValidacao(unittest.TestCase):
    def test_exige_remetente(self):
        with self.assertRaises(ErroDeEnvio):
            enviador(remetente="")

    def test_exige_destinatario(self):
        with self.assertRaises(ErroDeEnvio):
            enviador(destinatarios=[])

    def test_usuario_padrao_e_o_remetente(self):
        self.assertEqual(enviador().usuario, "agente@exemplo.com")


class TestSenha(unittest.TestCase):
    def test_senha_ausente_explica_senha_de_app(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ErroDeEnvio) as ctx:
                enviador().enviar("assunto", "texto", "<p>html</p>")
        self.assertIn("AGENTE_EMAIL_SENHA", str(ctx.exception))
        self.assertIn("Senha de app", str(ctx.exception))

    def test_variavel_customizada(self):
        with mock.patch.dict("os.environ", {"MINHA_SENHA": "segredo"}, clear=True):
            e = enviador(variavel_senha="MINHA_SENHA")
            self.assertEqual(e._senha(), "segredo")

    def test_senha_so_com_espacos_e_recusada(self):
        with mock.patch.dict("os.environ", {"AGENTE_EMAIL_SENHA": "   "}, clear=True):
            with self.assertRaises(ErroDeEnvio):
                enviador()._senha()


class TestMontagem(unittest.TestCase):
    def test_mensagem_tem_texto_e_html(self):
        msg = enviador().montar("Agenda 05/08", "versão texto", "<p>versão html</p>")
        tipos = {parte.get_content_type() for parte in msg.walk()}
        self.assertIn("text/plain", tipos)
        self.assertIn("text/html", tipos)

    def test_cabecalhos(self):
        msg = enviador(destinatarios=["a@x.com", "b@x.com"]).montar("Assunto", "t", "<p>h</p>")
        self.assertEqual(msg["Subject"], "Assunto")
        self.assertIn("agente@exemplo.com", msg["From"])
        self.assertIn("Agente de agendamento", msg["From"])
        self.assertEqual(msg["To"], "a@x.com, b@x.com")
        self.assertIsNotNone(msg["Date"])


class TestEnvio(unittest.TestCase):
    def setUp(self):
        self.ambiente = mock.patch.dict(
            "os.environ", {"AGENTE_EMAIL_SENHA": "senhadeapp"}, clear=True
        )
        self.ambiente.start()
        self.addCleanup(self.ambiente.stop)

    def test_porta_587_usa_starttls(self):
        with mock.patch("smtplib.SMTP") as fake:
            smtp = fake.return_value.__enter__.return_value
            destinos = enviador(porta=587).enviar("a", "t", "<p>h</p>")
        smtp.starttls.assert_called_once()
        smtp.login.assert_called_once_with("agente@exemplo.com", "senhadeapp")
        smtp.send_message.assert_called_once()
        self.assertEqual(destinos, ["suporte@exemplo.com"])

    def test_porta_465_usa_ssl_direto(self):
        with mock.patch("smtplib.SMTP_SSL") as fake:
            smtp = fake.return_value.__enter__.return_value
            enviador(porta=465).enviar("a", "t", "<p>h</p>")
        smtp.login.assert_called_once()
        smtp.send_message.assert_called_once()
        self.assertFalse(hasattr(smtp.starttls, "assert_called") and smtp.starttls.called)

    def test_login_recusado_explica_senha_de_app(self):
        with mock.patch("smtplib.SMTP") as fake:
            smtp = fake.return_value.__enter__.return_value
            smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad")
            with self.assertRaises(ErroDeEnvio) as ctx:
                enviador().enviar("a", "t", "<p>h</p>")
        self.assertIn("Senha de app", str(ctx.exception))

    def test_servidor_fora_do_ar_vira_erro_amigavel(self):
        with mock.patch("smtplib.SMTP", side_effect=OSError("conexão recusada")):
            with self.assertRaises(ErroDeEnvio) as ctx:
                enviador().enviar("a", "t", "<p>h</p>")
        self.assertIn("smtp.exemplo.com:587", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
