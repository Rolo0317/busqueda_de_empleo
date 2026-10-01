"""Pruebas del clasificador, con correos reales de la bandeja."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.clasificador_correos import Categoria, ClasificadorCorreos, Correo

CASOS = [
    (Correo("no-reply@pandape.com",
            "Inicia las evaluaciones para el puesto de Desarrollador Backend Junior",
            "Completa esta etapa para seguir avanzando en el proceso de seleccion."),
     Categoria.ACCION_REQUERIDA),
    (Correo("no-reply@pandape.com",
            "Estas cerca! Completa el test para continuar",
            "Ana, completa el juego para seguir avanzando en el proceso."),
     Categoria.ACCION_REQUERIDA),
    (Correo("angie.gomez@atento.com",
            "GRAN OPORTUNIDAD LABORAL - OFRECIMIENTO COMERCIAL",
            "Somos ATENTO COLOMBIA, hemos recibido tu postulacion."),
     Categoria.CONTACTO_HUMANO),
    (Correo("postulaciones@computrabajo.com",
            "Ana, tu candidatura avanza en el proceso de seleccion para Lider de Programacion",
            "Hay un cambio en tu candidatura. Nuevo estado en Lider de Programacion."),
     Categoria.AVANCE),
    (Correo("postulaciones@computrabajo.com",
            "Seguimiento de tu candidatura a la vacante Analista workforce GTR",
            "Te postulaste con exito. Tu HV ya esta en manos de la empresa."),
     Categoria.CONFIRMACION),
    (Correo("empleos_co@computrabajo.com",
            "Tu perfil encaja perfectamente en Saitemp S.A",
            "Estas empresas tienen nuevos empleos para ti!"),
     Categoria.RUIDO),
    (Correo("jobalerts-noreply@linkedin.com",
            "Analytics Engineer en Hyland",
            "Overview Analytics Engineer Colombia Remote"),
     Categoria.RUIDO),
    (Correo("sin-respuesta@computrabajo.com",
            "Ana, visualiza como te destacas entre los demas solicitantes",
            "Revisa quien compite contigo en este proceso de reclutamiento."),
     Categoria.RUIDO),
    # Bandeja del 23 al 25 de septiembre.
    (Correo("postulaciones@computrabajo.com",
            "Ana, tienes novedades en tu postulación a Ingeniero Desarrollador Python",
            "Novedades en tu postulación Hay un cambio en tu candidatura Nuevo estado en "
            "Ingeniero Desarrollador Python"),
     Categoria.RECHAZO),
    (Correo("keralty@emailmagneto365.com", "Carta de agradecimiento", ""),
     Categoria.RECHAZO),
    (Correo("notificaciones@emailmagneto365.com", "Agradecimiento candidato",
            "Agradecemos sinceramente el envío de su hoja de vida y el interés en formar parte"),
     Categoria.RECHAZO),
    (Correo("notificaciones@emailmagneto365.com", "Invitación a Pruebas Psicotécnicas",
            "Avanzaste a la siguiente etapa del proceso de selección para Especialista de "
            "Aplicaciones Backend"),
     Categoria.ACCION_REQUERIDA),
    (Correo("mzroa@staffing.com.co",
            "Entrevista Analista Senior Automatizador de Procesos Cavipetrol",
            "Contacto contigo en relación con la vacante a la que te inscribiste por Magneto"),
     Categoria.ACCION_REQUERIDA),
]


def main() -> int:
    clasificador = ClasificadorCorreos()
    fallos = 0

    for correo, esperada in CASOS:
        obtenida = clasificador.clasificar(correo)
        marca = "ok " if obtenida.categoria is esperada else "FALLA"
        if obtenida.categoria is not esperada:
            fallos += 1
        print(f"  [{marca}] {correo.asunto[:52]:<54} -> {obtenida.categoria.value}")

    print()
    print(f"  {len(CASOS) - fallos} de {len(CASOS)} correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
