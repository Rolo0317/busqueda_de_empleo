"""El seguimiento saca el cargo y el enlace util de correos reales, y solo
avisa de lo nuevo, reciente y accionable."""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import seguimiento.seguimiento_correo as modulo
from seguimiento.seguimiento_correo import SeguimientoCorreo, cargo_mencionado, enlace_de_accion
from utilidades.correo_imap import MensajeCorreo, html_a_texto
from utilidades.lector_codigos import ahora

# Asuntos y cuerpos tomados de la bandeja (10/10/2026).
CASOS_CARGO = [
    ("Danilo, tienes novedades en tu postulación a Ingeniero DBA", "", "Ingeniero DBA"),
    ("Danilo, hay una actualización en tu solicitud de empleo Analista BI Route to Market", "",
     "Analista BI Route to Market"),
    ("Danilo, tienes novedades en tu postulación a Analista de Operaciones – Medios de Pago", "",
     "Analista de Operaciones"),
    ("Agradecimiento candidato",
     "Hola william Danilo Queremos expresarte nuestro sincero agradecimiento por tu participación "
     "en el proceso de selección para el puesto de Desarrollador Roku Senior . Valoramos el tiempo",
     "Desarrollador Roku Senior"),
    ("¡Estás cerca! Completa el test para continuar",
     "Tu desempeño en esta etapa puede acercarte al puesto de Ingeniero de Software Danilo, completa "
     "el juego. Has recibido una invitación para la evaluación para el puesto de Ingeniero de Software .",
     "Ingeniero de Software"),
    ("Responder a el test para avanzar en el proceso",
     "Supernumerarios S.A.S Proceso de selección para: Jefe de Sistemas para el Sector Agrícola "
     "Hola Danilo , Para seguir avanzando", "Jefe de Sistemas para el Sector Agrícola"),
    ("Nuevos empleos para ti", "Mira las ofertas de hoy", None),
]

CASOS_ENLACE = [
    ('<a href="https://x.com/unsubscribe?u=1">Baja</a>'
     '<a href="https://cuidarte-tu-salud.pandape.computrabajo.com/Detail/13?a=1&amp;b=2">Iniciar</a>',
     "https://cuidarte-tu-salud.pandape.computrabajo.com/Detail/13?a=1&b=2"),
    ('<img src="https://cdn.pandape.com/logo.png"> Sin boton', None),
    ("Unete: https://teams.microsoft.com/l/meetup-join/abc. Gracias", "https://teams.microsoft.com/l/meetup-join/abc"),
]


def probar_cargo() -> int:
    fallos = 0
    for asunto, cuerpo, esperado in CASOS_CARGO:
        obtenido = cargo_mencionado(asunto, cuerpo)
        if obtenido != esperado:
            fallos += 1
            print(f"FALLO cargo: {asunto[:50]!r} -> {obtenido!r} (esperado {esperado!r})")
    return fallos


def probar_enlace() -> int:
    fallos = 0
    for cuerpo, esperado in CASOS_ENLACE:
        obtenido = enlace_de_accion(cuerpo)
        if obtenido != esperado:
            fallos += 1
            print(f"FALLO enlace: {cuerpo[:50]!r} -> {obtenido!r} (esperado {esperado!r})")
    return fallos


def probar_html_a_texto() -> int:
    texto = html_a_texto("<html><head><style>p{margin:0}</style></head><body><p>Hola&nbsp;Danilo</p></body></html>")
    if "margin" in texto or "Hola\xa0Danilo" not in texto:
        print(f"FALLO html_a_texto: {texto!r}")
        return 1
    return 0


class BuzonFalso:
    def __init__(self, mensajes):
        self.mensajes = mensajes

    def mensajes_desde(self, desde, remitente=None):
        return self.mensajes


def _mensaje(id_, asunto, horas_atras, remitente="no-reply@pandape.com"):
    return MensajeCorreo(id_, remitente, asunto, "", "", ahora() - timedelta(hours=horas_atras))


def probar_revision() -> int:
    """Solo se registran correos seguidos; solo se avisa de lo nuevo y reciente."""
    avisos = []
    modulo.avisar = lambda titulo, texto: avisos.append(texto)
    registrados = []
    buzon = BuzonFalso([
        _mensaje("1", "Completa el test para continuar en la vacante Analista BI", 2),
        _mensaje("2", "Completa el test para continuar", 40),            # viejo: sin aviso
        _mensaje("3", "Nuevos empleos para ti", 1),                       # ruido: no se registra
        _mensaje("4", "Carta de agradecimiento", 1),                      # rechazo: sin aviso
    ])
    seguimiento = SeguimientoCorreo(buzon, lambda evento: registrados.append(evento) or True)
    seguimiento.revisar_si_toca()
    seguimiento.revisar_si_toca()  # dentro del intervalo minimo: no hace nada

    fallos = 0
    if [e["message_id"] for e in registrados] != ["1", "2", "4"]:
        fallos += 1
        print(f"FALLO registro: {[e['message_id'] for e in registrados]}")
    if avisos != ["Analista BI"]:
        fallos += 1
        print(f"FALLO avisos: {avisos}")
    return fallos


if __name__ == "__main__":
    total = len(CASOS_CARGO) + len(CASOS_ENLACE) + 2
    fallos = probar_cargo() + probar_enlace() + probar_html_a_texto() + probar_revision()
    print(f"   {total - fallos} de {total} correctas")
    sys.exit(1 if fallos else 0)
