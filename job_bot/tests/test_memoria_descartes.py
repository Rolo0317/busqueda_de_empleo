"""La memoria de descartes evita reevaluar ofertas y paginar de mas.

Antes cada ciclo reevaluaba ~270 ofertas fuera del perfil y leia siempre
3 paginas por palabra clave, aunque todas ya se conocieran.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modelos.job_offer import JobOffer
from plataformas.base import BasePlatform
from postulacion.applicant import JobApplicant
from postulacion.memoria_descartes import OfertasConocidas, huella_de_filtros

PERFIL = {"cargos": {"propios": ["analista de datos"]}, "safe_booleans": {"has_disability": False}}


def oferta(titulo: str, n: int) -> JobOffer:
    return JobOffer(platform="Magneto", title=titulo, company="X", city="Bogota",
                    url=f"https://www.magneto365.com/co/empleos/oferta-{n}?utm_source=correo")


class PlataformaDePrueba(BasePlatform):
    nombre = "Prueba"

    def __init__(self) -> None:  # sin navegador: solo se prueba la paginacion
        pass

    def search(self, keyword, conocidas):
        return []

    def apply(self, offer):
        return "aplicado"


class TrackerFalso:
    def get_seen_urls(self):
        return set()

    def record(self, *args):
        pass


def casos() -> list[tuple[bool, str]]:
    conocidas = OfertasConocidas({"https://www.magneto365.com/co/empleos/oferta-1"})
    pagina_vieja = [oferta("Analista de datos", 1)]
    pagina_mixta = [oferta("Analista de datos", 1), oferta("Analista BI", 2)]
    plataforma = PlataformaDePrueba()

    # El aplicador: omite lo conocido y junta los descartes nuevos para guardarlos.
    aplicador = JobApplicant(
        platforms={"Magneto": plataforma}, tracker=TrackerFalso(),
        analyzer=SimpleNamespace(analyze=lambda o: SimpleNamespace(score=10, notes="")),
        wait_seconds=0, min_match_score=45, supervised=False,
    )
    conocidas_urls = {"https://www.magneto365.com/co/empleos/oferta-1"}
    resumen = aplicador.apply_to_offers(
        [oferta("Analista de datos", 1), oferta("Conductor de bus", 3)], OfertasConocidas(conocidas_urls))

    return [
        (huella_de_filtros(PERFIL, "") == huella_de_filtros(dict(PERFIL), ""),
         "la huella es estable con el mismo perfil"),
        (huella_de_filtros(PERFIL, "") != huella_de_filtros({**PERFIL, "cargos": {"propios": ["qa"]}}, ""),
         "cambiar los cargos del perfil cambia la huella"),
        (huella_de_filtros(PERFIL, "") != huella_de_filtros(PERFIL, "Bogota"),
         "cambiar la ciudad base cambia la huella"),
        ("https://www.magneto365.com/co/empleos/oferta-1?utm_source=x" in conocidas,
         "la URL se compara canonizada (sin parametros de rastreo)"),
        (conocidas.todas_conocidas(pagina_vieja), "una pagina con solo ofertas vistas es conocida"),
        (not conocidas.todas_conocidas(pagina_mixta), "una pagina con algo nuevo no es conocida"),
        (not conocidas.todas_conocidas([]), "una pagina vacia no cuenta como conocida"),
        (not plataforma.seguir_paginando(1, pagina_vieja, conocidas), "no pagina tras una pagina conocida"),
        (plataforma.seguir_paginando(1, pagina_mixta, conocidas), "pagina si hay algo nuevo"),
        (not plataforma.seguir_paginando(PlataformaDePrueba.PAGINAS_MAXIMAS, pagina_mixta, conocidas),
         "respeta el tope de paginas"),
        (not plataforma.seguir_paginando(1, [], conocidas), "no pagina tras una pagina vacia"),
        (resumen.duplicates == 1, "la oferta conocida se omite sin evaluarla"),
        ([url for url, _ in resumen.descartes] == ["https://www.magneto365.com/co/empleos/oferta-3"],
         "el cargo de otro oficio queda en los descartes a guardar"),
        (len(conocidas_urls) == 1, "el conjunto original no se modifica"),
    ]


def main() -> int:
    resultados = casos()
    fallos = [mensaje for ok, mensaje in resultados if not ok]
    for mensaje in fallos:
        print(f"FALLO: {mensaje}")
    print(f"   {len(resultados) - len(fallos)} de {len(resultados)} correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
