"""Aviso emergente de Windows para cuando el bot necesita a la persona.

Es de mejor esfuerzo: si no se puede mostrar, queda el log y el bot sigue.
"""
from __future__ import annotations

import logging
import subprocess

SEGUNDOS_VISIBLE = 15


def avisar(titulo: str, texto: str) -> None:
    logging.warning("AVISO | %s | %s", titulo, texto)
    guion = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "$n = New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon = [System.Drawing.SystemIcons]::Information;"
        f"$n.BalloonTipTitle = '{_escapar(titulo)}';"
        f"$n.BalloonTipText = '{_escapar(texto)}';"
        "$n.Visible = $true;"
        f"$n.ShowBalloonTip({SEGUNDOS_VISIBLE * 1000});"
        f"Start-Sleep -Seconds {SEGUNDOS_VISIBLE};"
        "$n.Dispose()"
    )
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", guion],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as error:
        logging.debug("No se pudo mostrar el aviso de Windows: %s", error)


def _escapar(texto: str) -> str:
    return texto.replace("'", "''")
