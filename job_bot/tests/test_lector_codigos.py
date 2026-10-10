"""El codigo de acceso se extrae del correo sin confundirlo con otros numeros."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utilidades.lector_codigos import codigo_en_texto

CASOS = [
    # Texto real del correo de Magneto (09/10/2026).
    ("Código de ingreso ¡Hola! william Danilo Solano Alvarez Aquí tienes tu código "
     "temporal de acceso. Úsalo cuando se te solicite. 790102 Si no solicitaste el código", "790102"),
    # Un enlace de seguimiento con 6 digitos antes del codigo no debe ganar.
    ('<a href="https://click.magneto365.com/t?id=123456&u=9">Ver</a> Tu codigo es <b>627925</b>', "627925"),
    # Numeros mas largos (telefonos, cedulas) no son el codigo.
    ("Llama al 3203914473. Tu código: 276318", "276318"),
    ("Sin codigo en este correo", None),
]


def main() -> int:
    fallos = 0
    for texto, esperado in CASOS:
        obtenido = codigo_en_texto(texto)
        ok = obtenido == esperado
        fallos += not ok
        print(f"  [{'ok ' if ok else 'FALLA'}] {texto[:60]!r} -> {obtenido}")
    print(f"\n  {len(CASOS) - fallos} de {len(CASOS)} correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
