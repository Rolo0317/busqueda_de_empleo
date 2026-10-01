"""Lanza el bot de postulacion como proceso aparte.

Se usa subproceso y no una llamada directa aunque el bot sea Python: abre un
navegador y puede correr varios minutos, asi que no tiene nada que hacer dentro
del hilo de una peticion HTTP.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings


@dataclass
class EstadoEjecucion:
    corriendo: bool
    iniciado: datetime | None = None
    terminado: datetime | None = None
    codigo_salida: int | None = None
    max_ofertas: int | None = None
    log: str | None = None

    def como_dict(self) -> dict[str, object]:
        return {
            "corriendo": self.corriendo,
            "iniciado": self.iniciado.isoformat() if self.iniciado else None,
            "terminado": self.terminado.isoformat() if self.terminado else None,
            "codigoSalida": self.codigo_salida,
            "maxOfertas": self.max_ofertas,
            "log": self.log,
        }


class EjecucionEnCurso(Exception):
    """El bot ya esta corriendo: lanzarlo dos veces duplicaria postulaciones."""


class BotNoDisponible(Exception):
    """Falta el interprete o el script del bot."""


class RequiereSupervision(Exception):
    """El modo supervisado exige una terminal para aprobar cada postulacion."""


@dataclass
class GestorDelBot:
    """Sostiene la unica ejecucion viva. Un operador, un proceso."""

    _proceso: subprocess.Popen[bytes] | None = field(default=None, repr=False)
    _estado: EstadoEjecucion = field(default_factory=lambda: EstadoEjecucion(corriendo=False))

    def estado(self) -> EstadoEjecucion:
        if self._proceso is not None and self._proceso.poll() is not None:
            self._estado.corriendo = False
            self._estado.terminado = datetime.now(timezone.utc)
            self._estado.codigo_salida = self._proceso.returncode
            self._proceso = None
        return self._estado

    def ejecutar(self, max_ofertas: int) -> EstadoEjecucion:
        if self.estado().corriendo:
            raise EjecucionEnCurso

        if settings.BOT_SUPERVISED:
            raise RequiereSupervision

        interprete = Path(settings.BOT_PYTHON)
        guion = Path(settings.BOT_DIR) / "main.py"
        if not interprete.exists() or not guion.exists():
            raise BotNoDisponible(f"No se encontro {interprete} o {guion}")

        log = Path(settings.BOT_DIR) / "bot_run.log"
        entorno = {
            # Tope duro de ofertas y una sola pasada: sin bucle infinito.
            "MAX_OFFERS": str(max_ofertas),
            "RUN_CONTINUOUSLY": "false",
        }

        salida = log.open("ab")
        self._proceso = subprocess.Popen(
            [str(interprete), str(guion)],
            cwd=str(settings.BOT_DIR),
            env={**_entorno_base(), **entorno},
            stdout=salida,
            stderr=subprocess.STDOUT,
        )
        self._estado = EstadoEjecucion(
            corriendo=True,
            iniciado=datetime.now(timezone.utc),
            max_ofertas=max_ofertas,
            log=str(log),
        )
        return self._estado


def _entorno_base() -> dict[str, str]:
    import os

    return dict(os.environ)


gestor = GestorDelBot()
