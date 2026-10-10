"""Memoria de ofertas ya decididas, para no reevaluarlas en cada ciclo.

Un descarte por titulo (otro oficio) o por ciudad (fuera de zona) no cambia
mientras no cambien los filtros. Se guarda con la huella de esos filtros: si
se editan las reglas o el perfil, la huella cambia y todo se reevalua solo.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from modelos.job_offer import JobOffer
from utilidades.url_utils import canonicalize_url

# Pasado este plazo un descarte se reevalua aunque la huella no haya cambiado.
DIAS_DE_MEMORIA = 14
# Los modulos cuyas reglas deciden un descarte por titulo o por ciudad.
MODULOS_DE_FILTRO = ("relevancia_cargo.py", "zona.py")


def huella_de_filtros(perfil: dict, ciudad_base: str) -> str:
    """Identifica la version de las reglas y del perfil que deciden descartes."""
    carpeta = Path(__file__).parent
    contenido = hashlib.sha256()
    for modulo in MODULOS_DE_FILTRO:
        contenido.update((carpeta / modulo).read_bytes())
    contenido.update(json.dumps({
        "cargos": perfil.get("cargos"),
        "inclusion": bool(perfil.get("safe_booleans", {}).get("has_disability")),
        "ciudad": ciudad_base,
    }, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return contenido.hexdigest()[:16]


class OfertasConocidas:
    """URLs que el bot ya decidio: postuladas, descartadas o en reintento."""

    def __init__(self, urls: set[str] | None = None) -> None:
        self._urls = {canonicalize_url(u) for u in urls or ()}

    def __contains__(self, url: str) -> bool:
        return canonicalize_url(url) in self._urls

    def __len__(self) -> int:
        return len(self._urls)

    def agregar(self, url: str) -> None:
        self._urls.add(canonicalize_url(url))

    def todas_conocidas(self, ofertas: list[JobOffer]) -> bool:
        """Una pagina de resultados sin nada nuevo: las siguientes, menos aun."""
        return bool(ofertas) and all(str(o.url) in self for o in ofertas)
