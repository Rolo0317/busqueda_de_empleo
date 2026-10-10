"""El bot no postula dos veces a la misma vacante, respeta el tope diario y
solo postula en horario. Casos tomados de las postulaciones repetidas reales."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import tope_del_ciclo
from modelos.job_offer import JobOffer
from postulacion.applicant import JobApplicant
from postulacion.ritmo_de_postulacion import HistorialDePostulaciones, RitmoDePostulacion, clave_de_vacante

AHORA = datetime(2026, 10, 10, 15, 0, tzinfo=timezone(timedelta(hours=-5)))


def oferta(titulo: str, empresa: str, n: int, plataforma: str = "Computrabajo") -> JobOffer:
    return JobOffer(platform=plataforma, title=titulo, company=empresa, city="Bogota",
                    url=f"https://co.computrabajo.com/ofertas-de-trabajo/oferta-{n}")


class TrackerFalso:
    def __init__(self) -> None:
        self.registros: list[tuple[str, str]] = []

    def get_seen_urls(self):
        return set()

    def record(self, offer, status, notes="", analysis=None):
        self.registros.append((status, notes))


class PlataformaFalsa:
    def __init__(self) -> None:
        self.postuladas: list[str] = []

    def apply(self, offer):
        self.postuladas.append(offer.title)
        return "aplicado"


def casos_de_clave() -> list[tuple[bool, str]]:
    return [
        (clave_de_vacante("Ejecutivo(a) Comercial", "Securitas Colombia S.A.")
         == clave_de_vacante("Ejecutivo Comercial", "SECURITAS COLOMBIA SA"),
         "la marca de genero y el sufijo legal no cambian la vacante"),
        (clave_de_vacante("Desarrollador/a II", "Zemsania Colombia SAS")
         == clave_de_vacante("Desarrollador II", "ZEMSANIA COLOMBIA S.A.S."),
         "'/a' y 'S.A.S.' se ignoran"),
        (clave_de_vacante("Analista de Automatización", "Carvajal")
         == clave_de_vacante("Analista de Automatizacion", "carvajal"),
         "tildes y mayusculas no importan"),
        (clave_de_vacante("Desarrollador de software", "No especificada") is None,
         "sin empresa y con cargo generico no se puede saber"),
        (clave_de_vacante("Desarrollador de aplicaciones Java Spring Boot y TypeScript", "Confidencial") is not None,
         "sin empresa, un cargo muy especifico si identifica la vacante"),
        (clave_de_vacante("Desarrollador Backend Java", "Accenture LTDA")
         != clave_de_vacante("Desarrollador Backend IBM i", "Accenture LTDA"),
         "dos cargos distintos de la misma empresa no se confunden"),
    ]


def casos_de_historial() -> list[tuple[bool, str]]:
    historial = HistorialDePostulaciones([
        {"titulo": "Desarrollador Backend IBM i (iSeries)", "empresa": "Accenture LTDA",
         "plataforma": "Magneto", "aplicada": "2026-10-10T13:00:00+00:00"},
        {"titulo": "Analista BI", "empresa": "Fastco SAS", "plataforma": "Computrabajo",
         "aplicada": "2026-10-09T15:00:00+00:00"},
    ])
    repetida = oferta("Desarrollador Backend IBM i (iSeries)", "Accenture Ltda", 1)
    nueva = oferta("Arquitecto de Datos", "Accenture LTDA", 2)
    medianoche = datetime(2026, 10, 10, tzinfo=AHORA.tzinfo)
    resultados = [
        (historial.plataforma_previa(repetida) == "Magneto", "detecta la repetida de otra plataforma"),
        (historial.plataforma_previa(nueva) is None, "una vacante nueva de la misma empresa pasa"),
        (historial.postuladas_desde(medianoche) == 1, "cuenta solo las postulaciones de hoy (hora local)"),
    ]
    historial.registrar(nueva, AHORA)
    resultados += [
        (historial.plataforma_previa(oferta("Arquitecto de Datos", "ACCENTURE", 3)) == "Computrabajo",
         "lo postulado en el ciclo cuenta para el resto del ciclo"),
        (historial.postuladas_desde(medianoche) == 2, "lo postulado hoy suma al cupo"),
    ]
    return resultados


def casos_de_ritmo() -> list[tuple[bool, str]]:
    ritmo = RitmoDePostulacion(tope_diario=40, hora_inicio=7, hora_fin=21)
    dia = AHORA.replace(hour=0)
    hoy_38 = HistorialDePostulaciones([{"titulo": f"c{i}", "empresa": "e", "aplicada": AHORA.isoformat()}
                                       for i in range(38)])
    return [
        (ritmo.dentro_de_horario(dia.replace(hour=7)), "a las 7:00 ya postula"),
        (not ritmo.dentro_de_horario(dia.replace(hour=6, minute=59)), "a las 6:59 todavia no"),
        (not ritmo.dentro_de_horario(dia.replace(hour=21)), "a las 21:00 ya no postula"),
        (ritmo.cupo_de_hoy(hoy_38, AHORA) == 2, "con 38 de 40 hoy, quedan 2"),
        (RitmoDePostulacion(0, 7, 21).cupo_de_hoy(hoy_38, AHORA) is None, "tope 0 es sin tope"),
        (RitmoDePostulacion(40, 0, 24).dentro_de_horario(dia.replace(hour=23, minute=59)),
         "horario 0-24 cubre todo el dia"),
        (tope_del_ciclo(0, None) == 0, "sin tope de corrida ni diario: sin tope"),
        (tope_del_ciclo(20, 5) == 5, "manda el cupo del dia si es menor"),
        (tope_del_ciclo(0, 5) == 5, "sin tope de corrida, manda el cupo del dia"),
        (tope_del_ciclo(20, None) == 20, "sin tope diario, manda el de la corrida"),
    ]


def casos_del_aplicador() -> list[tuple[bool, str]]:
    tracker, plataforma = TrackerFalso(), PlataformaFalsa()
    historial = HistorialDePostulaciones([
        {"titulo": "Analista BI", "empresa": "Fastco SAS", "plataforma": "Magneto"}])
    aplicador = JobApplicant(
        platforms={"Computrabajo": plataforma}, tracker=tracker,
        analyzer=SimpleNamespace(analyze=lambda o: SimpleNamespace(score=90, notes="")),
        wait_seconds=0, min_match_score=45, supervised=False, historial=historial,
    )
    resumen = aplicador.apply_to_offers([
        oferta("Analista BI", "FASTCO S.A.S.", 1),          # ya postulada en Magneto
        oferta("Analista de Datos", "Grupo Uno", 2),        # nueva
        oferta("Analista de Datos", "Grupo Uno SAS", 3),    # la misma, republicada en el ciclo
    ])
    return [
        (plataforma.postuladas == ["Analista de Datos"], "postula una sola vez a cada vacante"),
        (resumen.repetidas == 2, "cuenta las dos repetidas"),
        (("descartado", "Repetida: ya postulada en Magneto") in tracker.registros,
         "la repetida queda descartada con el motivo"),
    ]


def main() -> int:
    resultados = casos_de_clave() + casos_de_historial() + casos_de_ritmo() + casos_del_aplicador()
    fallos = [mensaje for ok, mensaje in resultados if not ok]
    for mensaje in fallos:
        print(f"FALLO: {mensaje}")
    print(f"   {len(resultados) - len(fallos)} de {len(resultados)} correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
