"""Inicio de sesion automatico en Magneto con codigo al correo.

Flujo (verificado el 09/10/2026): correo -> "Continuar" -> elegir "Enviar al
correo electronico" -> 6 casillas numericas -> redirige a la busqueda de
empleos. La pagina tiene Cloudflare Turnstile: en el Edge real del usuario pasa
sin reto; si aparece uno, o Magneto no logra enviar el codigo, se avisa a la
persona y se espera. Nunca se intenta saltar el captcha.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from services.aviso import avisar
from services.lector_codigos import FuenteDeCodigos, ahora

URL_LOGIN = "https://login.magneto365.com/candidates"
DOMINIO_LOGIN = "login.magneto365.com"
REMITENTES_CODIGO = ("emailmagneto365.com", "potential-365.com")
OPCION_CORREO = "Enviar al correo electrónico"
FALLO_ENVIO = "No pudimos enviar el código"
CASILLAS_CODIGO = "input[inputmode=numeric]"
DIGITOS_CODIGO = 6
MS_ESPERA_PASO = 20_000
SEGUNDOS_LEYENDO_CORREO = 120
# En la prueba del 09/10 Magneto tardo mas de 30 s en redirigir tras el codigo.
SEGUNDOS_TRAS_CODIGO = 90
BOTONES_CONFIRMAR = ("Continuar", "Verificar", "Confirmar", "Ingresar")


@dataclass(frozen=True)
class ResultadoLogin:
    exito: bool
    motivo: str


class LoginMagneto:
    def __init__(self, pagina: Page, correo: str, codigos: FuenteDeCodigos,
                 minutos_espera_manual: int) -> None:
        self._pagina = pagina
        self._correo = correo
        self._codigos = codigos
        self._segundos_espera_manual = minutos_espera_manual * 60

    def iniciar(self) -> ResultadoLogin:
        try:
            if not self._escribir_correo():
                # Con la sesion viva, Magneto redirige fuera del login: el "sin
                # sesion" fue una lectura temprana del encabezado (09/10).
                return ResultadoLogin(True, "Ya había sesión: el login redirigió solo")
            pedido = ahora()
            if not self._pedir_codigo_al_correo():
                return self._esperar_a_la_persona("Magneto no pudo enviar el código o pidió un reto.")
            codigo = self._codigos.esperar_codigo(REMITENTES_CODIGO, pedido, SEGUNDOS_LEYENDO_CORREO)
            if not codigo:
                return self._esperar_a_la_persona("Escribe en el Edge del bot el código que te llegó al correo.")
            self._escribir_codigo(codigo)
            if self._salio_del_login(SEGUNDOS_TRAS_CODIGO):
                return ResultadoLogin(True, "Sesión iniciada con el código del correo")
            return self._esperar_a_la_persona("El código no fue aceptado.")
        except PlaywrightTimeout as error:
            return self._esperar_a_la_persona(f"La página de login no respondió como se esperaba ({str(error)[:60]}).")

    # ------------------------------------------------------------------ pasos

    def _escribir_correo(self) -> bool:
        """Escribe el correo; False si el login redirigio porque ya hay sesion."""
        self._pagina.goto(URL_LOGIN, wait_until="domcontentloaded")
        try:
            self._pagina.wait_for_selector("#email", timeout=MS_ESPERA_PASO)
        except PlaywrightTimeout:
            if DOMINIO_LOGIN not in self._pagina.url:
                return False
            raise
        self._pagina.fill("#email", self._correo)
        self._pagina.get_by_role("button", name="Continuar").click()
        return True

    def _pedir_codigo_al_correo(self) -> bool:
        self._pagina.get_by_text(OPCION_CORREO).first.wait_for(timeout=MS_ESPERA_PASO)
        self._pagina.get_by_text(OPCION_CORREO).first.click()
        try:
            self._pagina.wait_for_selector(CASILLAS_CODIGO, timeout=MS_ESPERA_PASO)
        except PlaywrightTimeout:
            return False
        return FALLO_ENVIO not in self._pagina.inner_text("body")

    def _escribir_codigo(self, codigo: str) -> None:
        casillas = self._pagina.query_selector_all(CASILLAS_CODIGO)
        if len(casillas) >= DIGITOS_CODIGO:
            for casilla, digito in zip(casillas, codigo):
                casilla.type(digito)
        else:
            casillas[0].type(codigo)
        # Hoy el formulario se envia solo al completar las casillas; si algun dia
        # agrega un boton de confirmar, se pulsa.
        for nombre in BOTONES_CONFIRMAR:
            boton = self._pagina.get_by_role("button", name=nombre)
            if boton.count():
                boton.first.click()
                break

    def _salio_del_login(self, segundos: int) -> bool:
        limite = time.time() + segundos
        while time.time() < limite:
            if DOMINIO_LOGIN not in self._pagina.url:
                return True
            time.sleep(1)
        return False

    def _esperar_a_la_persona(self, motivo: str) -> ResultadoLogin:
        minutos = self._segundos_espera_manual // 60
        avisar("Bot de empleo: inicia sesión en Magneto",
               f"{motivo} Tienes {minutos} min; el bot sigue solo cuando entres.")
        logging.warning("Login de Magneto requiere a la persona: %s", motivo)
        try:
            self._pagina.bring_to_front()
        except Exception:
            pass
        if self._salio_del_login(self._segundos_espera_manual):
            return ResultadoLogin(True, "Sesión iniciada con ayuda de la persona")
        return ResultadoLogin(False, motivo)
