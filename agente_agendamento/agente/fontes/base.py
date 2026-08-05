"""Contrato das fontes de pacientes.

O LiveClin não publica API. A fonte concreta hoje é a planilha exportada
da plataforma; qualquer integração futura (API oficial ou automação de
navegador) só precisa implementar ``FontePacientes.carregar``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..modelos import Paciente


class ErroDeFonte(Exception):
    """Falha ao ler ou interpretar a fonte de pacientes."""


class FontePacientes(ABC):
    @abstractmethod
    def carregar(self) -> list[Paciente]:
        """Devolve os pacientes conhecidos pela fonte."""

    @property
    def avisos(self) -> list[str]:
        """Problemas não fatais encontrados durante a leitura."""
        return []
