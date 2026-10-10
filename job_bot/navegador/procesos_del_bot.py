"""El Edge del bot y los procesos de main.py, vistos desde fuera del bot.

Lo usan el agente (corridas desde el panel) y el supervisor (bot continuo):
ninguno de los dos se engancha al navegador, solo comprueba que este vivo y
sabe abrirlo, contar los bots que corren y detenerlos.
"""
from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

import requests

from config import Settings

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT_NAVEGADOR = RAIZ / "scripts" / "abrir_navegador_bot.ps1"
SEGUNDOS_ESPERA_NAVEGADOR = 40
# El supervisor corre sin consola: sin esto cada PowerShell abre una ventana.
SIN_VENTANA = subprocess.CREATE_NO_WINDOW


class NavegadorDelBot:
    """El Edge del bot escuchando en el puerto de depuracion."""

    def __init__(self, settings: Settings) -> None:
        direccion = settings.edge_debugger_address or "127.0.0.1:9222"
        self._url_version = f"http://{direccion}/json/version"

    def listo(self) -> bool:
        try:
            return requests.get(self._url_version, timeout=3).ok
        except requests.RequestException:
            return False

    def asegurar(self) -> bool:
        if self.listo():
            return True
        logging.info("El navegador del bot no esta abierto: abriendolo...")
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT_NAVEGADOR)],
            cwd=str(RAIZ), check=False, capture_output=True, creationflags=SIN_VENTANA,
        )
        limite = time.time() + SEGUNDOS_ESPERA_NAVEGADOR
        while time.time() < limite:
            if self.listo():
                return True
            time.sleep(2)
        return False


def pids_del_bot() -> list[int]:
    """Los procesos python que corren main.py (el lanzador del venv y el real)."""
    consulta = (
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object { $_.CommandLine -like '*main.py*' } | "
        "ForEach-Object { $_.ProcessId }"
    )
    salida = subprocess.run(["powershell", "-NoProfile", "-Command", consulta],
                            capture_output=True, text=True, check=False, creationflags=SIN_VENTANA).stdout
    return [int(linea) for linea in salida.split() if linea.isdigit()]


def hay_otro_bot_corriendo() -> bool:
    """Dos bots sobre el mismo Edge se pisan y duplican postulaciones."""
    return bool(pids_del_bot())


def detener_bots() -> None:
    for pid in pids_del_bot():
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                       capture_output=True, check=False, creationflags=SIN_VENTANA)
