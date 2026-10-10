"""El supervisor relanza el bot caido o colgado, respeta la pausa y no entra
en un bucle de reinicios si el bot se cae en seguida."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from supervisor import (ESPERAS_ENTRE_REINICIOS, MINUTOS_DE_VIDA_ESTABLE, MINUTOS_PARA_DAR_POR_COLGADO,
                        Accion, EsperaEntreReinicios, LogDelBot, siguiente_accion)

COLGADO = MINUTOS_PARA_DAR_POR_COLGADO


def casos_de_accion() -> list[tuple[bool, str]]:
    def accion(pausado=False, pausa_nueva=False, vivo=True, quieto=1.0, puede=True):
        return siguiente_accion(pausado, pausa_nueva, vivo, quieto, puede)

    return [
        (accion(vivo=False) is Accion.ARRANCAR, "bot caido: se lanza"),
        (accion(vivo=False, puede=False) is Accion.NADA, "bot caido en plena espera: no se lanza aun"),
        (accion(quieto=COLGADO + 1) is Accion.REINICIAR, "log quieto 20+ min: se reinicia"),
        (accion(quieto=COLGADO - 1) is Accion.NADA, "log reciente: se deja trabajar"),
        (accion(quieto=None) is Accion.NADA, "sin log todavia: no se da por colgado"),
        (accion(pausado=True, pausa_nueva=True) is Accion.DETENER, "pausa nueva: se detiene el bot"),
        (accion(pausado=True) is Accion.NADA, "pausa vieja: una corrida del panel no se mata"),
        (accion(pausado=True, vivo=False) is Accion.NADA, "en pausa no se relanza"),
        (accion(pausado=True, quieto=COLGADO + 5) is Accion.NADA, "en pausa no se vigila el log"),
    ]


def casos_de_espera() -> list[tuple[bool, str]]:
    espera = EsperaEntreReinicios()
    resultados = [(espera.puede_arrancar(0), "el primer arranque no espera")]
    espera.registrar_arranque(0)
    espera.registrar_arranque(5)  # se cayo a los 5 s
    primera = ESPERAS_ENTRE_REINICIOS[0]
    resultados += [
        (not espera.puede_arrancar(5 + primera - 1), "tras una caida rapida, espera la primera pausa"),
        (espera.puede_arrancar(5 + primera), "cumplida la pausa, puede arrancar"),
    ]
    espera.registrar_arranque(5 + primera)  # otra caida rapida
    segunda = ESPERAS_ENTRE_REINICIOS[1]
    resultados.append((not espera.puede_arrancar(5 + primera + segunda - 1),
                       "la segunda caida seguida espera mas"))
    estable = 5 + primera + MINUTOS_DE_VIDA_ESTABLE * 60
    espera.registrar_arranque(estable)  # vivio estable antes de caer
    resultados.append((espera.puede_arrancar(estable + 1),
                       "tras una vida estable, la cuenta de caidas vuelve a cero"))
    return resultados


def casos_de_log() -> list[tuple[bool, str]]:
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "bot.log"
        sin_log = LogDelBot(ruta)
        resultados = [(sin_log.ultima_actividad() is None and sin_log.ultimo_ciclo() is None,
                       "sin archivo de log no hay actividad ni ciclo")]
        ruta.write_text(
            "10:00 | INFO | RESUMEN CICLO | revisadas=10 | aplicadas=1\n"
            "10:05 | INFO | Buscando...\n"
            "10:09 | INFO | RESUMEN CICLO | revisadas=20 | aplicadas=2\n"
            "10:09 | INFO | Esperando 300s\n", encoding="utf-8")
        log = LogDelBot(ruta)
        resultados += [
            (log.ultima_actividad() is not None, "con log hay ultima actividad"),
            ("revisadas=20" in (log.ultimo_ciclo() or ""), "el ultimo ciclo es el RESUMEN mas reciente"),
        ]
        return resultados


def main() -> int:
    resultados = casos_de_accion() + casos_de_espera() + casos_de_log()
    fallos = [mensaje for ok, mensaje in resultados if not ok]
    for mensaje in fallos:
        print(f"FALLO: {mensaje}")
    print(f"   {len(resultados) - len(fallos)} de {len(resultados)} correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
