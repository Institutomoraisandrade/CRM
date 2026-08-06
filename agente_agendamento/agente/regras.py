"""Regras clínicas de acompanhamento.

Regra central: o retorno de um paciente nunca pode ser marcado mais de
``INTERVALO_MAXIMO_DIAS`` depois da última consulta, e nunca depois do fim
da vigência do plano. As duas datas são tetos rígidos — o motor de
agendamento só escolhe horários abaixo do menor dos dois.
"""

from __future__ import annotations

from datetime import date, timedelta

from .modelos import Alerta, Paciente, StatusPaciente, TipoAlerta

# Teto rígido do intervalo entre consultas.
INTERVALO_MAXIMO_DIAS = 30

# Check-in intermediário entre uma consulta e a seguinte.
CHECKIN_DIAS = 15

# Antecedência do aviso de fim de plano.
AVISO_VENCIMENTO_DIAS = 7


def data_limite_retorno(paciente: Paciente) -> date:
    """Última data em que o retorno ainda respeita a regra dos 30 dias.

    Considera o teto de 30 dias sobre a última consulta e o fim da vigência
    do plano, devolvendo o menor dos dois. Sem última consulta registrada, a
    contagem parte do início do plano.
    """
    base = paciente.ultima_consulta or paciente.plano_inicio
    limite_intervalo = base + timedelta(days=INTERVALO_MAXIMO_DIAS)
    return min(limite_intervalo, paciente.plano_fim)


def data_checkin(paciente: Paciente) -> date | None:
    """Data do check-in de 15 dias, quando há consulta registrada."""
    if paciente.ultima_consulta is None:
        return None
    return paciente.ultima_consulta + timedelta(days=CHECKIN_DIAS)


def etiqueta_vigencia(paciente: Paciente, hoje: date) -> str:
    """Etiqueta automática de vigência do plano.

    Mantém "ativo" até faltarem 7 dias; a partir daí passa a indicar quantos
    dias restam, como pedido no levantamento de requisitos.
    """
    if paciente.status is not StatusPaciente.ATIVO:
        return paciente.status.value
    restantes = paciente.dias_para_vencer_em(hoje)
    if restantes < 0:
        return "vencido"
    if restantes == 0:
        return "vence hoje"
    if restantes <= AVISO_VENCIMENTO_DIAS:
        return f"vence em {restantes} dia{'s' if restantes > 1 else ''}"
    return "ativo"


def _texto_dias(dias: int) -> str:
    return f"{dias} dia" if dias == 1 else f"{dias} dias"


def alertas_do_paciente(paciente: Paciente, hoje: date) -> list[Alerta]:
    """Alertas que devem disparar hoje para este paciente."""
    if paciente.status is not StatusPaciente.ATIVO:
        return []

    alertas: list[Alerta] = []
    restantes = paciente.dias_para_vencer_em(hoje)

    if restantes < 0:
        alertas.append(
            Alerta(
                tipo=TipoAlerta.PLANO_VENCIDO,
                paciente=paciente,
                data_referencia=paciente.plano_fim,
                mensagem=(
                    f"O plano {paciente.plano.nome} de {paciente.nome} venceu em "
                    f"{paciente.plano_fim:%d/%m/%Y}. Renovar antes de agendar novo retorno."
                ),
                destinatarios=["profissional"],
            )
        )
    elif restantes <= AVISO_VENCIMENTO_DIAS:
        quando = "hoje" if restantes == 0 else f"em {_texto_dias(restantes)}"
        alertas.append(
            Alerta(
                tipo=TipoAlerta.PLANO_VENCENDO,
                paciente=paciente,
                data_referencia=paciente.plano_fim,
                mensagem=(
                    f"O plano {paciente.plano.nome} de {paciente.nome} termina {quando} "
                    f"({paciente.plano_fim:%d/%m/%Y}). Falar sobre renovação."
                ),
                destinatarios=["profissional", "paciente"],
            )
        )

    checkin = data_checkin(paciente)
    if checkin == hoje:
        alertas.append(
            Alerta(
                tipo=TipoAlerta.CHECKIN_15_DIAS,
                paciente=paciente,
                data_referencia=checkin,
                mensagem=(
                    f"{paciente.nome} está há {CHECKIN_DIAS} dias da última consulta "
                    f"({paciente.ultima_consulta:%d/%m/%Y}). Momento do check-in intermediário."
                ),
                destinatarios=["profissional", "paciente"],
            )
        )

    limite = data_limite_retorno(paciente)

    if paciente.ultima_consulta is None:
        # Sem a data da última consulta o limite é contado do início do
        # plano. Serve para agendar, mas não para afirmar atraso: um
        # paciente antigo apareceria com meses de atraso não confirmável.
        return alertas

    if limite == hoje:
        alertas.append(
            Alerta(
                tipo=TipoAlerta.RETORNO_30_DIAS,
                paciente=paciente,
                data_referencia=limite,
                mensagem=(
                    f"Hoje é o último dia para o retorno de {paciente.nome} dentro do "
                    f"limite de {INTERVALO_MAXIMO_DIAS} dias."
                ),
                destinatarios=["profissional", "paciente"],
            )
        )
    elif limite < hoje and restantes >= 0:
        atraso = (hoje - limite).days
        alertas.append(
            Alerta(
                tipo=TipoAlerta.CONSULTA_ATRASADA,
                paciente=paciente,
                data_referencia=limite,
                mensagem=(
                    f"{paciente.nome} passou {_texto_dias(atraso)} do limite de "
                    f"{INTERVALO_MAXIMO_DIAS} dias entre consultas. Agendar com prioridade."
                ),
                destinatarios=["profissional"],
            )
        )

    return alertas
