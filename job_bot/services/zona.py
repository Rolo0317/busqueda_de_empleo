"""Si una oferta queda fuera de la ciudad del candidato.

Con reubicacion en false, postular a un cargo presencial o hibrido en otra
ciudad solo produce un descarte, o obliga a contestar "no me interesa" en el
cuestionario. Paso con varias ofertas de Medellin.
"""
from __future__ import annotations

import re
import unicodedata

from models.job_offer import JobOffer

# Cada ciudad con los municipios y departamentos desde los que se puede ir y
# volver en el dia. Una oferta en el area de la ciudad del candidato no es lejana.
AREAS = {
    # Sin "Madrid" ni "Caldas": tambien nombran un pais y un departamento lejanos.
    "bogota": ("bogota", "chia", "cota", "funza", "mosquera", "soacha",
               "cajica", "zipaquira", "facatativa", "la calera", "tocancipa"),
    "medellin": ("medellin", "envigado", "itagui", "bello", "sabaneta", "rionegro",
                 "la estrella", "copacabana", "antioquia"),
    "cali": ("cali", "palmira", "jamundi", "yumbo", "valle del cauca"),
    "barranquilla": ("barranquilla", "soledad", "malambo", "puerto colombia", "atlantico"),
    "bucaramanga": ("bucaramanga", "floridablanca", "giron", "piedecuesta"),
    "cartagena": ("cartagena",),
    "pereira": ("pereira", "dosquebradas"),
    "manizales": ("manizales",),
    "cucuta": ("cucuta",),
    "ibague": ("ibague",),
    "villavicencio": ("villavicencio",),
    "santa marta": ("santa marta",),
    "pasto": ("pasto",),
    "neiva": ("neiva",),
    "armenia": ("armenia",),
    "monteria": ("monteria",),
    "tunja": ("tunja",),
    "popayan": ("popayan",),
    "valledupar": ("valledupar",),
    "sincelejo": ("sincelejo",),
}

MARCAS_REMOTO = ("remoto", "remote", "teletrabajo", "home office", "trabajo en casa", "100% virtual")


def _plano(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(base.lower().split())


def _nombra(termino: str, texto: str) -> bool:
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(termino) + r"(?![a-z0-9])", texto))


def _area_de(texto: str) -> str | None:
    """El area metropolitana que nombra el texto, o None si no nombra ninguna."""
    return next((area for area, lugares in AREAS.items()
                 if any(_nombra(lugar, texto) for lugar in lugares)), None)


def ciudad_lejana(offer: JobOffer, ciudad_candidato: str) -> str | None:
    """La ciudad lejana en la que es la oferta, o None si es alcanzable o remota.

    Sin saber donde vive el candidato no se puede juzgar: no se descarta nada.
    """
    area_propia = _area_de(_plano(ciudad_candidato))
    if area_propia is None:
        return None

    area_oferta = _area_de(_plano(f"{offer.title} {offer.city}"))
    if area_oferta is None or area_oferta == area_propia:
        return None

    todo = _plano(f"{offer.title} {offer.city} {offer.description}")
    if any(m in todo for m in MARCAS_REMOTO):
        return None
    return area_oferta
