"""Sesion autenticada contra Supabase y llamadas a sus funciones (RPC).

El bot y el agente inician sesion con el mismo usuario del panel: las tablas del
esquema `empleo` no estan expuestas y solo se alcanzan por las funciones
public.empleo_*, que exigen que ese usuario sea operador. Asi no hace falta
guardar en la PC la clave de servicio, que salta todas las reglas de acceso.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

import requests

TIEMPO_ESPERA_HTTP = 30
INTENTOS_POR_LLAMADA = 3
SEGUNDOS_ENTRE_REINTENTOS = 2
# Se renueva el token un poco antes de que caduque, no cuando ya fallo.
MARGEN_RENOVACION_SEGUNDOS = 120


class ErrorSupabase(RuntimeError):
    """Supabase respondio con error; el mensaje trae el detalle de Postgres."""


@dataclass(frozen=True)
class CredencialesSupabase:
    url: str
    clave_publica: str
    email: str
    password: str

    def completas(self) -> bool:
        return all((self.url, self.clave_publica, self.email, self.password))


class ClienteSupabase:
    def __init__(self, credenciales: CredencialesSupabase) -> None:
        if not credenciales.completas():
            raise ErrorSupabase(
                "Faltan SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_EMAIL o "
                "SUPABASE_PASSWORD en el .env."
            )
        self._credenciales = credenciales
        self._base = credenciales.url.rstrip("/")
        self._http = requests.Session()
        self._http.headers.update({"apikey": credenciales.clave_publica})
        self._candado = threading.Lock()
        self._token_acceso = ""
        self._token_renovacion = ""
        self._caduca_en = 0.0

    @classmethod
    def desde_settings(cls, settings: Any) -> ClienteSupabase:
        return cls(CredencialesSupabase(
            url=settings.supabase_url,
            clave_publica=settings.supabase_publishable_key,
            email=settings.supabase_email,
            password=settings.supabase_password,
        ))

    def rpc(self, funcion: str, parametros: dict[str, Any] | None = None) -> Any:
        respuesta = self._post_con_reintentos(funcion, parametros or {})
        if not respuesta.ok:
            raise ErrorSupabase(f"{funcion}: {self._detalle(respuesta)}")
        return respuesta.json() if respuesta.content else None

    def _post_con_reintentos(self, funcion: str, parametros: dict[str, Any]) -> requests.Response:
        """Un corte de red pasajero no debe perder el ciclo: el 09/10 un
        "connection reset" de Supabase tumbo una vuelta entera del bot."""
        for intento in range(1, INTENTOS_POR_LLAMADA + 1):
            try:
                return self._http.post(
                    f"{self._base}/rest/v1/rpc/{funcion}",
                    json=parametros,
                    headers={"Authorization": f"Bearer {self._token_vigente()}"},
                    timeout=TIEMPO_ESPERA_HTTP,
                )
            except (requests.ConnectionError, requests.Timeout):
                if intento == INTENTOS_POR_LLAMADA:
                    raise
                time.sleep(SEGUNDOS_ENTRE_REINTENTOS * intento)
        raise AssertionError("inalcanzable")

    # ------------------------------------------------------------- sesion

    def _token_vigente(self) -> str:
        with self._candado:
            if time.time() >= self._caduca_en - MARGEN_RENOVACION_SEGUNDOS:
                self._autenticar()
            return self._token_acceso

    def _autenticar(self) -> None:
        if self._token_renovacion:
            try:
                self._pedir_token("refresh_token", {"refresh_token": self._token_renovacion})
                return
            except ErrorSupabase:
                pass  # el token de renovacion caduco: se entra de nuevo con la clave
        self._pedir_token("password", {
            "email": self._credenciales.email,
            "password": self._credenciales.password,
        })

    def _pedir_token(self, tipo: str, cuerpo: dict[str, str]) -> None:
        respuesta = self._http.post(
            f"{self._base}/auth/v1/token",
            params={"grant_type": tipo},
            json=cuerpo,
            timeout=TIEMPO_ESPERA_HTTP,
        )
        if not respuesta.ok:
            raise ErrorSupabase(f"No se pudo iniciar sesion en Supabase: {self._detalle(respuesta)}")
        datos = respuesta.json()
        self._token_acceso = datos["access_token"]
        self._token_renovacion = datos["refresh_token"]
        self._caduca_en = time.time() + int(datos.get("expires_in", 3600))

    @staticmethod
    def _detalle(respuesta: requests.Response) -> str:
        try:
            datos = respuesta.json()
        except ValueError:
            return f"HTTP {respuesta.status_code}"
        mensaje = datos.get("message") or datos.get("msg") or datos.get("error_description")
        return f"HTTP {respuesta.status_code}: {mensaje or datos}"
