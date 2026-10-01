"""Registro de plataformas.

Agregar una bolsa de empleo es agregar una linea a PLATAFORMAS. main.py no se
toca: ese era el acoplamiento que obligaba a editar el arranque por cada
plataforma nueva.
"""
from __future__ import annotations

import logging
from typing import Mapping

from browser.navegador import Navegador
from config import Settings
from platforms.base import BasePlatform
from platforms.computrabajo import ComputrabajoPlatform
from platforms.magneto import MagnetoPlatform

PLATAFORMAS: Mapping[str, type[BasePlatform]] = {
    "magneto": MagnetoPlatform,
    "computrabajo": ComputrabajoPlatform,
}


class PlataformaDesconocida(Exception):
    pass


def crear(nombres: list[str], navegador: Navegador, settings: Settings,
          tracker=None) -> dict[str, BasePlatform]:
    """Construye las plataformas pedidas, indexadas por su nombre publico."""
    desconocidas = [n for n in nombres if n.lower() not in PLATAFORMAS]
    if desconocidas:
        raise PlataformaDesconocida(
            f"No existen: {', '.join(desconocidas)}. Disponibles: {', '.join(PLATAFORMAS)}"
        )

    instancias: dict[str, BasePlatform] = {}
    for nombre in nombres:
        clase = PLATAFORMAS[nombre.lower()]
        instancias[clase.nombre] = clase(navegador=navegador, settings=settings, tracker=tracker)
        logging.info("Plataforma habilitada: %s", clase.nombre)
    return instancias
