"""Decide si un cargo encaja con el perfil objetivo del candidato.

Es una pregunta distinta de si un correo exige accion: un reclutador humano
puede escribir por una vacante que significa un paso atras. Separar ambas evita
que la bandeja priorice oportunidades que el candidato no va a tomar.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum


class Encaje(str, Enum):
    OBJETIVO = "objetivo"        # el cargo que se busca
    ADYACENTE = "adyacente"      # usa su experiencia, sin ser el objetivo
    RETROCESO = "retroceso"      # por debajo del perfil actual
    STACK_AJENO = "stack_ajeno"  # pide una tecnologia que el perfil no tiene
    RESERVADA = "reservada"      # cupo reservado a una poblacion que no es la del candidato
    DESCONOCIDO = "desconocido"


@dataclass(frozen=True)
class Valoracion:
    encaje: Encaje
    motivo: str

    @property
    def vale_la_pena(self) -> bool:
        return self.encaje in (Encaje.OBJETIVO, Encaje.ADYACENTE)


# Se comprueban antes que el objetivo: comparten palabras con cargos del perfil
# ("desarrollador", "automatizacion", "programador") pero son otro oficio. Por
# ellas el bot se postulo a desarrollo de negocios, PLC industrial y torno CNC,
# y cada una volvio como descarte automatico.
FUERA_DEL_PERFIL = (
    "desarrollador de negocio", "desarrolladora de negocio", "desarrollo de negocio",
    "desarrollador comercial", "desarrolladora comercial", "desarrollo comercial",
    "consultor de negocios", "plc", "hmi", "cnc", "torno", "mecanizado",
    "nomina", "talento humano", "cultura y desarrollo",
)

# Mismo oficio pero un escalon por debajo: con seis anos de experiencia, un
# contrato de aprendiz es un retroceso aunque el cargo sea de datos.
NIVEL_INFERIOR = ("aprendiz", "practicante", "pasante")

# Tecnologias que el perfil no registra. Un titulo que pide una de ellas, sin
# nombrar ninguna propia, termina en descarte automatico: las preguntas del
# filtro ("anos de experiencia en .NET") se contestan con la verdad, que es 0.
STACK_AJENO = (
    "php", ".net", "dotnet", "c#", "java", "golang", "angular", "flutter", "kotlin",
    "swift", "ruby", "laravel", "salesforce", "apex", "sap", "abap", "netsuite",
    "progress", "cobol", "rpg", "iseries", "middleware",
)

# Tecnologias que el perfil si respalda (experience_years y main_skills).
STACK_PROPIO = (
    "python", "sql", "power bi", "react", "node", "javascript", "django", "flask",
    "etl", "excel", "pandas", "docker", "rpa", "datos", "data", "bi", "analitica",
)

# Cargos que son el objetivo declarado del perfil.
CARGOS_OBJETIVO = (
    "analista de datos", "data analyst", "ingeniero de datos", "data engineer",
    "desarrollador", "developer", "full stack", "fullstack", "backend", "frontend",
    "software", "business intelligence", "analista bi", "power bi", "etl",
    "data scientist", "cientifico de datos", "automatizacion", "rpa",
    "arquitectura de software", "analytics", "analitica", "ingeniero de sistemas",
    "ingenieria de datos", "inteligencia artificial",
    # Tecnologias y areas: muchos titulos nombran la herramienta y no el rol
    # ("Ingeniero en Python", "BI Analyst II", "DBA SQL Junior").
    "python", "sql", "dba", "bi", "datos", "data", "sistemas", "programacion",
    "tecnologia", "tic", "ia", "api", "integraciones", "base de datos",
    # Auditoria del 09/10/2026: titulos de su oficio que se descartaban como
    # "no reconocidos" (16 mil descartes en los logs, la causa numero uno).
    "inteligencia de negocios", "business analyst", "analista de negocio",
    "reporting", "qa", "quality assurance", "tester", "pruebas de software",
    "analista ti", "ti", "it", "ai", "aplicaciones",
    "ingeniero desarrollo", "ingeniero de desarrollo",
    "soluciones digitales", "transformacion digital",
)

# Cargos que aprovechan su experiencia en torre de control y BPO.
CARGOS_ADYACENTES = (
    "workforce", "gtr", "controller", "torre de control", "wfm",
    "analista de operaciones", "planeacion operativa", "reporteria",
    "kpi", "indicadores",
    # Auditoria del 09/10/2026: control de operacion, procesos y mejora, donde
    # pesan la torre de control y la automatizacion.
    # Terminos compuestos a proposito: "procesos" o "monitoreo" solos colaban
    # "auxiliar de procesos" u "operador de monitoreo" (camaras de seguridad).
    "real time", "tiempo real", "analista de monitoreo", "ingeniero de monitoreo",
    "analista de planeacion", "gestion de operaciones", "operations analyst",
    "gestion y control", "control de gestion", "inteligencia operacional",
    "gestion del servicio", "mejora continua", "excelencia operacional",
    "analista de procesos", "ingeniero de procesos", "transformacion de procesos",
    "analista de innovacion", "especialista de innovacion", "crm", "itsm", "pricing",
)

# Cargos por debajo del perfil: operativos o comerciales de primera linea.
CARGOS_RETROCESO = (
    "asesor comercial", "ejecutivo comercial", "asesor de ventas", "vendedor",
    "agente call center", "agente de servicio", "asesor call center",
    "atencion al cliente", "servicio al cliente", "teleoperador",
    "auxiliar", "cajero", "mercaderista", "operario", "promotor",
    "ofrecimiento comercial", "asesor telefonico", "recaudo", "cobranza",
)


def sin_tildes(valor: str) -> str:
    plano = unicodedata.normalize("NFKD", valor or "")
    return plano.encode("ascii", "ignore").decode("ascii").lower()


# Vacantes de inclusion: el cupo es para personas con discapacidad. Postular
# sin estarlo quita el puesto a quien si y vuelve como descarte automatico.
MARCAS_INCLUSION_DISCAPACIDAD = (
    "discapacidad", "vacante de inclusion", "vacante incluyente", "persona con discapacidad",
)


# Listas por defecto, con el nombre que las reemplaza en la clave "cargos" del
# perfil. Otro candidato busca otros cargos: las define en su perfil sin tocar
# el codigo, y las que no defina conservan el valor por defecto.
LISTAS_POR_DEFECTO = {
    "fuera_del_perfil": FUERA_DEL_PERFIL,
    "nivel_inferior": NIVEL_INFERIOR,
    "stack_ajeno": STACK_AJENO,
    "stack_propio": STACK_PROPIO,
    "objetivo": CARGOS_OBJETIVO,
    "adyacentes": CARGOS_ADYACENTES,
    "retroceso": CARGOS_RETROCESO,
}


class RelevanciaDelCargo:
    """Valora el encaje de un cargo con el perfil objetivo."""

    def __init__(self, cargos: dict[str, list[str]] | None = None,
                 acepta_vacantes_de_inclusion: bool = False) -> None:
        self.acepta_vacantes_de_inclusion = acepta_vacantes_de_inclusion
        # Las claves con "_" son notas para quien edita el perfil, no listas.
        propias = {k: v for k, v in (cargos or {}).items() if not k.startswith("_")}
        desconocidas = set(propias) - set(LISTAS_POR_DEFECTO)
        if desconocidas:
            raise ValueError(f"Listas de cargos desconocidas en el perfil: {sorted(desconocidas)}")
        self.listas = {
            nombre: tuple(sin_tildes(c) for c in propias.get(nombre, defecto))
            for nombre, defecto in LISTAS_POR_DEFECTO.items()
        }

    def valorar(self, texto: str) -> Valoracion:
        normalizado = sin_tildes(texto)

        if not self.acepta_vacantes_de_inclusion:
            reservada = self._coincidencia(MARCAS_INCLUSION_DISCAPACIDAD, normalizado)
            if reservada:
                return Valoracion(Encaje.RESERVADA, f"Cupo reservado: {reservada}")

        ajeno = self._buscar("fuera_del_perfil", normalizado)
        if ajeno:
            return Valoracion(Encaje.RETROCESO, f"Otro oficio con nombre parecido: {ajeno}")

        inferior = self._buscar("nivel_inferior", normalizado)
        if inferior:
            return Valoracion(Encaje.RETROCESO, f"Nivel por debajo del perfil: {inferior}")

        ajena = self._buscar("stack_ajeno", normalizado)
        if ajena and not self._buscar("stack_propio", normalizado):
            return Valoracion(Encaje.STACK_AJENO, f"Pide {ajena}, que el perfil no tiene")

        # El objetivo manda: un titulo puede mencionar el sector y aun asi
        # tratarse del cargo que se busca.
        objetivo = self._buscar("objetivo", normalizado)
        if objetivo:
            return Valoracion(Encaje.OBJETIVO, f"Cargo objetivo: {objetivo}")

        adyacente = self._buscar("adyacentes", normalizado)
        if adyacente:
            return Valoracion(Encaje.ADYACENTE, f"Aprovecha experiencia previa: {adyacente}")

        retroceso = self._buscar("retroceso", normalizado)
        if retroceso:
            return Valoracion(Encaje.RETROCESO, f"Por debajo del perfil: {retroceso}")

        return Valoracion(Encaje.DESCONOCIDO, "No se reconoce el cargo")

    def _buscar(self, lista: str, texto: str) -> str | None:
        return self._coincidencia(self.listas[lista], texto)

    @staticmethod
    def _coincidencia(cargos: tuple[str, ...], texto: str) -> str | None:
        for cargo in cargos:
            if re.search(_patron(cargo), texto):
                return cargo
        return None


def _patron(termino: str) -> str:
    """El termino debe empezar una palabra; si es corto, tambien terminarla.

    Con subcadenas, "ia" casaba con "gerencia" y "tic" con "logistica". Solo se
    exige el borde inicial en los largos para que "desarrollador" siga casando
    con "desarrolladora" y "negocio" con "negocios".
    """
    inicio = r"(?<![a-z0-9])" + re.escape(termino)
    return inicio + r"(?![a-z0-9])" if len(termino) <= 4 else inicio
