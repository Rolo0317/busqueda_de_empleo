"""El tope de postulaciones por corrida se respeta.

El boton del panel lanza el bot con MAX_OFFERS=20; antes el valor se leia y
nadie lo usaba, asi que cada corrida postulaba a todo lo que encontraba.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.job_offer import JobOffer
from services.applicant import JobApplicant


class PlataformaFalsa:
    def __init__(self) -> None:
        self.postuladas = 0

    def apply(self, offer: JobOffer) -> str:
        self.postuladas += 1
        return "aplicado"


class TrackerFalso:
    def get_seen_urls(self) -> list[str]:
        return []

    def record(self, *args) -> None:
        pass


class AnalizadorFalso:
    def analyze(self, offer: JobOffer):
        return SimpleNamespace(score=90, notes="")


def ofertas(cuantas: int) -> list[JobOffer]:
    return [JobOffer(platform="Magneto", title=f"Desarrollador Python {i}", company="X",
                     url=f"https://www.magneto365.com/co/empleos/oferta-{i}",
                     salary="$ 4.000.000", city="Bogota") for i in range(cuantas)]


def correr(tope: int, disponibles: int) -> int:
    plataforma = PlataformaFalsa()
    aplicador = JobApplicant(
        platforms={"Magneto": plataforma}, tracker=TrackerFalso(),
        analyzer=AnalizadorFalso(), wait_seconds=0, min_match_score=45,
        supervised=False, max_applications=tope,
    )
    aplicador.apply_to_offers(ofertas(disponibles))
    return plataforma.postuladas


def main() -> int:
    casos = [
        (20, 50, 20, "con tope 20 y 50 ofertas, postula 20"),
        (20, 7, 7, "con tope 20 y 7 ofertas, postula las 7"),
        (0, 30, 30, "sin tope (0), postula todas"),
    ]
    fallos = 0
    for tope, disponibles, esperado, nombre in casos:
        obtenido = correr(tope, disponibles)
        ok = obtenido == esperado
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] {nombre:<42} -> {obtenido}")
    print(f"\n  {len(casos) - fallos} de {len(casos)} correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
