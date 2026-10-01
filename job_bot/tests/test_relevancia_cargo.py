"""Pruebas del encaje de cargo, con correos reales de la bandeja."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.relevancia_cargo import Encaje, RelevanciaDelCargo

CASOS = [
    ("GRAN OPORTUNIDAD LABORAL - OFRECIMIENTO COMERCIAL - SECTOR FINANCIERO", Encaje.RETROCESO),
    ("Inicia las evaluaciones para el puesto de Desarrollador Backend Junior/Node.js/APIs/SQL", Encaje.OBJETIVO),
    ("Seguimiento de tu candidatura a la vacante Analista workforce GTR", Encaje.ADYACENTE),
    ("Tu candidatura avanza en el proceso para Analista de Arquitectura de Software Junior", Encaje.OBJETIVO),
    ("Completa el test para el puesto de GTR o Controller call center", Encaje.ADYACENTE),
    ("Analytics Engineer en Hyland", Encaje.OBJETIVO),
    ("Vacante Asesor Comercial Microfinanzas - Oficina Popayan", Encaje.RETROCESO),
    ("Auxiliar de Despachos Separacion de Mercancia", Encaje.RETROCESO),
    # Postulaciones reales del bot que Computrabajo descarto automaticamente.
    ("Programador de Automatizaciòn (PLC Y HMI)", Encaje.RETROCESO),
    ("Operario programador Centro Mecanizado Torno CNC", Encaje.RETROCESO),
    ("Coordinador Comercial / Desarrollador de Negocios / Desarrollador de Productor", Encaje.RETROCESO),
    ("Ejecutivas comerciales / Desarrolladora de negocios / asesoras externas", Encaje.RETROCESO),
    ("Desarrollador/ Consultor de Negocios B2B Sector Seguridad", Encaje.RETROCESO),
    ("Analista de nómina datos maestros", Encaje.RETROCESO),
    ("Gestor de Cultura y Desarrollo de Talentos", Encaje.RETROCESO),
    ("Analista de Talento Humano en Retail", Encaje.RETROCESO),
    # Cargos que si son del perfil y el filtro no debe perder.
    ("Profesional II Ingeniero de Sistemas Bogotá", Encaje.OBJETIVO),
    ("Consultor(a) Líder En Inteligencia Artificial Y Analítica", Encaje.OBJETIVO),
    ("Especialista de Aplicaciones Backend", Encaje.OBJETIVO),
    ("Ingeniero de datos y analítica senior", Encaje.OBJETIVO),
    # Cargos reales que el filtro perdia por nombrar la herramienta y no el rol.
    ("Ingeniero en Python", Encaje.OBJETIVO),
    ("BI Analyst II", Encaje.OBJETIVO),
    ("DBA SQL Junior", Encaje.OBJETIVO),
    ("Analista de informacion logística con experiencia en sql y data", Encaje.OBJETIVO),
    ("Líder de Sistemas y Tecnología – ERP / SQL / Integraciones / IA", Encaje.OBJETIVO),
    ("Ingeniero Responsable De Tic", Encaje.OBJETIVO),
    ("Aprendiz de Análisis de Datos", Encaje.RETROCESO),
    # Descartes automaticos del 27 y 28 de septiembre.
    ("Desarrollador Comercial Consumo Masivo", Encaje.RETROCESO),
    ("Desarrollador PHP", Encaje.STACK_AJENO),
    ("Desarrollador .NET Fullstack  Semisenior", Encaje.STACK_AJENO),
    ("Consultor Desarrollador Progress 4GL / OpenEdge ABL", Encaje.STACK_AJENO),
    ("Analista KPI Senior (BPO)", Encaje.ADYACENTE),
    # Stack mixto: nombra algo que si maneja, asi que se intenta.
    ("Desarrollador Backend Node.js / Golang Senior – Experto en IA", Encaje.OBJETIVO),
    ("Desarrollador Full Stack .NET / React", Encaje.OBJETIVO),
    # "java" no debe casar con "javascript".
    ("Desarrollador JavaScript", Encaje.OBJETIVO),
    # Terminos cortos que no deben casar dentro de otra palabra.
    ("Gerencia de Logística Nacional", Encaje.DESCONOCIDO),
    ("Asesor Bilingüe de Servicio", Encaje.DESCONOCIDO),
]


def main() -> int:
    relevancia = RelevanciaDelCargo()
    fallos = 0
    for texto, esperado in CASOS:
        obtenido = relevancia.valorar(texto)
        ok = obtenido.encaje is esperado
        fallos += 0 if ok else 1
        print(f"  [{'ok ' if ok else 'FALLA'}] {texto[:56]:<58} -> {obtenido.encaje.value}")
    print()
    print(f"  {len(CASOS) - fallos} de {len(CASOS)} correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
