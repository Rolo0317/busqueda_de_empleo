"""Supervisor del bot continuo: lo mantiene vivo sin que nadie lo vigile.

Arranca con Windows (tarea programada, ver scripts\\instalar_supervisor.ps1) y
cada 30 s revisa el bot:
  - si no corre, abre el Edge del bot si hace falta y lanza main.py, con
    esperas crecientes si se cae una y otra vez;
  - si corre pero el log lleva 20 min quieto, lo da por colgado y lo relanza;
  - si el panel pidio pausa, lo detiene y no lo vuelve a lanzar.
En cada vuelta late a Supabase para que el panel sepa si hay actividad.

    .venv\\Scripts\\python.exe supervisor.py
"""
from __future__ import annotations

import logging
import msvcrt
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import load_settings
from almacenamiento.supabase_cliente import ClienteSupabase
from navegador.procesos_del_bot import NavegadorDelBot, detener_bots, pids_del_bot
from utilidades.aviso import avisar

CARPETA_BOT = Path(__file__).resolve().parent
LOG_DEL_BOT = CARPETA_BOT / "logs" / "bot.log"
LOG_DEL_SUPERVISOR = CARPETA_BOT / "logs" / "supervisor.log"
CANDADO = CARPETA_BOT / "logs" / "supervisor.lock"
# El supervisor corre con pythonw (sin ventana); el bot con python.exe, que es
# el nombre de proceso que buscan el agente y pids_del_bot().
PYTHON_DEL_BOT = Path(sys.executable).with_name("python.exe")

SEGUNDOS_ENTRE_REVISIONES = 30
# Mas que la espera del login manual (10 min) y que un ciclo normal sin log.
MINUTOS_PARA_DAR_POR_COLGADO = 20
# Si el bot vivio esto sin caerse, las esperas entre reinicios vuelven a empezar.
MINUTOS_DE_VIDA_ESTABLE = 10
ESPERAS_ENTRE_REINICIOS = (30, 60, 120, 300, 600)
BYTES_FINALES_DEL_LOG = 64_000


class Accion(Enum):
    NADA = "nada"
    ARRANCAR = "arrancar"
    DETENER = "detener"
    REINICIAR = "reiniciar"


def siguiente_accion(pausado: bool, pausa_nueva: bool, bot_vivo: bool,
                     minutos_sin_actividad: float | None, puede_arrancar: bool) -> Accion:
    """La decision de cada vuelta, separada de los efectos para poder probarla.

    Al pausar solo se detiene el bot una vez: despues, una corrida lanzada a
    proposito desde el panel no debe morir en la siguiente revision.
    """
    if pausado:
        return Accion.DETENER if bot_vivo and pausa_nueva else Accion.NADA
    if not bot_vivo:
        return Accion.ARRANCAR if puede_arrancar else Accion.NADA
    if minutos_sin_actividad is not None and minutos_sin_actividad >= MINUTOS_PARA_DAR_POR_COLGADO:
        return Accion.REINICIAR
    return Accion.NADA


class EsperaEntreReinicios:
    """Si el bot se cae en seguida, cada reinicio espera mas que el anterior."""

    def __init__(self, esperas: tuple[int, ...] = ESPERAS_ENTRE_REINICIOS) -> None:
        self._esperas = esperas
        self._fallos_seguidos = 0
        self._ultimo_arranque: float | None = None

    def puede_arrancar(self, ahora: float) -> bool:
        if self._ultimo_arranque is None:
            return True
        indice = min(self._fallos_seguidos, len(self._esperas)) - 1
        return indice < 0 or ahora - self._ultimo_arranque >= self._esperas[indice]

    def registrar_arranque(self, ahora: float) -> None:
        vivio_estable = (self._ultimo_arranque is not None
                         and ahora - self._ultimo_arranque >= MINUTOS_DE_VIDA_ESTABLE * 60)
        self._fallos_seguidos = 0 if vivio_estable or self._ultimo_arranque is None else self._fallos_seguidos + 1
        self._ultimo_arranque = ahora


class LogDelBot:
    """Lo que el log del bot dice sobre su actividad."""

    def __init__(self, ruta: Path = LOG_DEL_BOT) -> None:
        self._ruta = ruta

    def ultima_actividad(self) -> datetime | None:
        try:
            return datetime.fromtimestamp(self._ruta.stat().st_mtime, tz=timezone.utc)
        except OSError:
            return None

    def ultimo_ciclo(self) -> str | None:
        try:
            with self._ruta.open("rb") as archivo:
                archivo.seek(max(0, self._ruta.stat().st_size - BYTES_FINALES_DEL_LOG))
                cola = archivo.read().decode("utf-8", "replace")
        except OSError:
            return None
        ciclos = [linea for linea in cola.splitlines() if "RESUMEN CICLO" in linea]
        return ciclos[-1][:300] if ciclos else None


class Supervisor:
    def __init__(self) -> None:
        settings = load_settings()
        self._cliente = ClienteSupabase.desde_settings(settings)
        self._navegador = NavegadorDelBot(settings)
        self._log = LogDelBot()
        self._espera = EsperaEntreReinicios()
        self._maquina = socket.gethostname()
        self._pausado = False
        self._arranques = 0

    def correr(self) -> None:
        logging.info("Supervisor del bot activo en %s.", self._maquina)
        while True:
            self._vuelta()
            time.sleep(SEGUNDOS_ENTRE_REVISIONES)

    def _vuelta(self) -> None:
        bot_vivo = bool(pids_del_bot())
        pausado = self._latir(bot_vivo)
        pausa_nueva = pausado and not self._pausado
        self._pausado = pausado
        actividad = self._log.ultima_actividad()
        minutos_quieto = (datetime.now(timezone.utc) - actividad).total_seconds() / 60 if actividad else None

        accion = siguiente_accion(pausado, pausa_nueva, bot_vivo, minutos_quieto,
                                  self._espera.puede_arrancar(time.time()))
        if accion is Accion.DETENER:
            logging.info("Pausa pedida desde el panel: deteniendo el bot.")
            detener_bots()
        elif accion is Accion.REINICIAR:
            logging.warning("El log lleva %.0f min quieto: el bot parece colgado. Reiniciando.", minutos_quieto)
            avisar("Bot de empleo", "El bot estaba colgado; el supervisor lo reinicio.")
            detener_bots()
            self._arrancar()
        elif accion is Accion.ARRANCAR:
            self._arrancar()

    def _arrancar(self) -> None:
        if not self._navegador.asegurar():
            logging.warning("No se pudo abrir el Edge del bot; se reintenta en la proxima vuelta.")
            return
        self._espera.registrar_arranque(time.time())
        self._arranques += 1
        subprocess.Popen(
            [str(PYTHON_DEL_BOT), "-u", str(CARPETA_BOT / "main.py")],
            cwd=str(CARPETA_BOT), env=self._entorno(),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        logging.info("Bot lanzado (arranque #%d de este supervisor).", self._arranques)

    @staticmethod
    def _entorno() -> dict[str, str]:
        # Sin terminal no hay quien apruebe oferta por oferta.
        return {**os.environ, "RUN_CONTINUOUSLY": "true", "SUPERVISED_APPLY": "false",
                "PYTHONIOENCODING": "utf-8"}

    def _latir(self, bot_vivo: bool) -> bool:
        """Reporta al panel y devuelve si pidio pausa. Sin red, sigue como estaba."""
        actividad = self._log.ultima_actividad()
        try:
            return bool(self._cliente.rpc("empleo_latido_bot", {
                "p_maquina": self._maquina,
                "p_estado": {
                    "actividad_at": actividad.isoformat() if actividad else None,
                    "proceso_vivo": bot_vivo,
                    "reinicios": max(0, self._arranques - 1),
                    "ultimo_ciclo": self._log.ultimo_ciclo(),
                },
            }))
        except Exception as error:
            logging.warning("Latido fallido: %s", str(error)[:120])
            return self._pausado


def tomar_candado():
    """Un solo supervisor por PC: dos lanzarian dos bots sobre el mismo Edge."""
    CANDADO.parent.mkdir(exist_ok=True)
    archivo = CANDADO.open("a+")
    try:
        msvcrt.locking(archivo.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        archivo.close()
        return None
    return archivo


def main() -> None:
    LOG_DEL_SUPERVISOR.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s | supervisor | %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[RotatingFileHandler(LOG_DEL_SUPERVISOR, maxBytes=1_000_000, backupCount=2, encoding="utf-8"),
                  # Con pythonw no hay consola: sys.stderr es None.
                  *([logging.StreamHandler()] if sys.stderr else [])],
    )
    candado = tomar_candado()
    if candado is None:
        logging.info("Ya hay un supervisor corriendo en esta PC; este se cierra.")
        return
    try:
        Supervisor().correr()
    except KeyboardInterrupt:
        logging.info("Supervisor detenido. El bot sigue corriendo si estaba activo.")


if __name__ == "__main__":
    main()
