"""Generacion de claves temporales. Vive aparte para que crear y resetear
una cuenta usen exactamente la misma regla."""
import secrets
import string

# Sin caracteres ambiguos: la clave se lee de pantalla y se teclea una vez.
ALFABETO = (
    string.ascii_lowercase.replace("l", "")
    + string.ascii_uppercase.replace("I", "").replace("O", "")
    + "23456789"
)
LARGO = 16


def clave_temporal() -> str:
    return "".join(secrets.choice(ALFABETO) for _ in range(LARGO))
