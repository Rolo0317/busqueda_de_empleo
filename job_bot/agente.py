"""Agente local: conecta el boton "Ejecutar" del panel web con esta PC.

El bot no puede correr en Vercel: necesita el Edge del bot con las sesiones de
Magneto y Computrabajo iniciadas, y eso vive aqui. El panel solo deja una
solicitud en Supabase; este agente la toma, abre el navegador si hace falta,
lanza main.py con el tope pedido y va reportando el estado y la cola del log.

    .venv\\Scripts\\python.exe agente.py      (o ..\\scripts\\iniciar_agente.ps1)
"""
from __future__ import annotations

import logging
import os
import re
import socket
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from config import Settings, load_settings
from almacenamiento.supabase_cliente import ClienteSupabase
from navegador.procesos_del_bot import NavegadorDelBot, hay_otro_bot_corriendo

CARPETA_BOT = Path(__file__).resolve().parent

SEGUNDOS_ENTRE_LATIDOS = 15
SEGUNDOS_ENTRE_CONSULTAS = 5
SEGUNDOS_ENTRE_REPORTES = 5
LINEAS_DE_LOG_REPORTADAS = 60

# main.py imprime esto al final de cada ciclo; de aqui sale el resumen del panel.
PATRON_RESUMEN = re.compile(
    r"RESUMEN CICLO \| revisadas=(\d+) \| aplicadas=(\d+) \| errores=(\d+) \| omitidas=(\d+)"
)


@dataclass(frozen=True)
class Corrida:
    id: int
    max_ofertas: int


class EjecutorDelBot:
    """Lanza main.py para una corrida y reporta su avance a Supabase."""

    def __init__(self, cliente: ClienteSupabase) -> None:
        self._cliente = cliente

    def ejecutar(self, corrida: Corrida) -> None:
        lineas: deque[str] = deque(maxlen=LINEAS_DE_LOG_REPORTADAS)
        proceso = subprocess.Popen(
            [sys.executable, "-u", str(CARPETA_BOT / "main.py")],
            cwd=str(CARPETA_BOT),
            env=self._entorno(corrida),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        lector = threading.Thread(target=self._leer, args=(proceso, lineas), daemon=True)
        lector.start()

        while proceso.poll() is None:
            self._reportar(corrida, "running", lineas)
            time.sleep(SEGUNDOS_ENTRE_REPORTES)
        lector.join(timeout=5)

        estado = "finished" if proceso.returncode == 0 else "failed"
        self._reportar(corrida, estado, lineas, codigo=proceso.returncode, resumen=self._resumen(lineas))
        logging.info("Corrida #%s terminada: %s (codigo %s)", corrida.id, estado, proceso.returncode)

    @staticmethod
    def _entorno(corrida: Corrida) -> dict[str, str]:
        # El clic en el panel ya es la aprobacion: no hay terminal donde
        # confirmar cada oferta, por eso el tope es obligatorio.
        return {
            **os.environ,
            "MAX_OFFERS": str(corrida.max_ofertas),
            "RUN_CONTINUOUSLY": "false",
            "SUPERVISED_APPLY": "false",
            "QUESTION_REVIEW_SECONDS": "0",
            "PYTHONIOENCODING": "utf-8",
        }

    @staticmethod
    def _leer(proceso: subprocess.Popen[str], lineas: deque[str]) -> None:
        assert proceso.stdout is not None
        for linea in proceso.stdout:
            linea = linea.rstrip()
            if linea:
                lineas.append(linea)
                print(linea, flush=True)

    def _reportar(self, corrida: Corrida, estado: str, lineas: deque[str],
                  codigo: int | None = None, resumen: dict | None = None) -> None:
        try:
            self._cliente.rpc("empleo_reportar_corrida", {
                "p_id": corrida.id, "p_estado": estado, "p_log": "\n".join(lineas),
                "p_codigo": codigo, "p_resumen": resumen,
            })
        except Exception as error:
            logging.warning("No se pudo reportar el avance: %s", str(error)[:120])

    @staticmethod
    def _resumen(lineas: deque[str]) -> dict | None:
        for linea in reversed(lineas):
            encontrado = PATRON_RESUMEN.search(linea)
            if encontrado:
                revisadas, aplicadas, errores, omitidas = map(int, encontrado.groups())
                return {"revisadas": revisadas, "aplicadas": aplicadas,
                        "errores": errores, "omitidas": omitidas}
        return None


class Agente:
    def __init__(self, settings: Settings) -> None:
        self._cliente = ClienteSupabase.desde_settings(settings)
        self._navegador = NavegadorDelBot(settings)
        self._ejecutor = EjecutorDelBot(self._cliente)
        self._maquina = socket.gethostname()
        self._detener = threading.Event()

    def correr(self) -> None:
        self._cliente.rpc("empleo_reiniciar_agente", {"p_maquina": self._maquina})
        threading.Thread(target=self._latir, daemon=True).start()
        logging.info("Agente escuchando en %s. Ctrl+C para salir.", self._maquina)
        try:
            while not self._detener.is_set():
                corrida = self._tomar()
                if corrida:
                    self._atender(corrida)
                else:
                    self._detener.wait(SEGUNDOS_ENTRE_CONSULTAS)
        except KeyboardInterrupt:
            logging.info("Agente detenido.")
        finally:
            self._detener.set()

    def _latir(self) -> None:
        while not self._detener.is_set():
            try:
                self._cliente.rpc("empleo_latido", {
                    "p_maquina": self._maquina, "p_navegador_listo": self._navegador.listo(),
                })
            except Exception as error:
                logging.warning("Latido fallido: %s", str(error)[:120])
            self._detener.wait(SEGUNDOS_ENTRE_LATIDOS)

    def _tomar(self) -> Corrida | None:
        try:
            datos = self._cliente.rpc("empleo_tomar_corrida", {"p_maquina": self._maquina})
        except Exception as error:
            logging.warning("No se pudo consultar Supabase: %s", str(error)[:120])
            return None
        return Corrida(id=int(datos["id"]), max_ofertas=int(datos["maxOfertas"])) if datos else None

    def _atender(self, corrida: Corrida) -> None:
        logging.info("Corrida #%s solicitada desde el panel (tope %s).", corrida.id, corrida.max_ofertas)
        motivo = self._motivo_para_no_correr()
        if motivo:
            logging.warning("Corrida #%s rechazada: %s", corrida.id, motivo)
            self._cliente.rpc("empleo_reportar_corrida", {
                "p_id": corrida.id, "p_estado": "failed", "p_log": f"[agente] {motivo}",
            })
            return
        self._ejecutor.ejecutar(corrida)

    def _motivo_para_no_correr(self) -> str:
        if hay_otro_bot_corriendo():
            return "Ya hay un bot corriendo en la PC (main.py). Detenlo o espera a que termine."
        if not self._navegador.asegurar():
            return "No se pudo abrir el navegador del bot en el puerto 9222."
        return ""


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | agente | %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    Agente(load_settings()).correr()


if __name__ == "__main__":
    main()
