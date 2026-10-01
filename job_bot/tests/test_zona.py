"""Ofertas en otra ciudad, con el perfil sin reubicacion."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.job_offer import JobOffer
from services.zona import ciudad_lejana


def oferta(titulo: str, ciudad: str, descripcion: str = "") -> JobOffer:
    return JobOffer(platform="Magneto", title=titulo, company="X", salary="?",
                    url="https://example.com/o", city=ciudad, description=descripcion)


BOGOTA = "Bogotá, D.C., Colombia"
MEDELLIN = "Medellín, Antioquia"

# (oferta, ciudad del candidato, ciudad lejana esperada)
CASOS = [
    (oferta("Analista de datos SQL y Power BI en Medellín", "Medellín"), BOGOTA, "medellin"),
    (oferta("Desarrollador Full Stack", "Cali, Valle del Cauca"), BOGOTA, "cali"),
    (oferta("Data Engineer", "Medellín", "Modalidad remoto, todo Colombia"), BOGOTA, None),
    (oferta("Analista BI", "Bogotá, D.C."), BOGOTA, None),
    (oferta("Desarrollador Python", "Chía, Cundinamarca"), BOGOTA, None),
    # La lejania depende de donde vive cada candidato, no de una ciudad fija.
    (oferta("Analista BI", "Bogotá, D.C."), MEDELLIN, "bogota"),
    (oferta("Desarrollador Python", "Envigado, Antioquia"), MEDELLIN, None),
    # Sin ciudad en el perfil no hay como juzgar: no se descarta.
    (oferta("Desarrollador Full Stack", "Cali, Valle del Cauca"), "", None),
]


def main() -> int:
    fallos = 0
    for o, ciudad, esperado in CASOS:
        obtenido = ciudad_lejana(o, ciudad)
        ok = obtenido == esperado
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] {o.title[:40]:<42} {o.city[:20]:<22} -> {obtenido}")
    print(f"\n  {len(CASOS) - fallos} de {len(CASOS)} correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
