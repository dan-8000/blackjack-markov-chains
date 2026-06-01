from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from .models import VALOR_CARTA, Mano, Zapato, Reglas
from .markov import SolucionadorMarkov, convertir_cartas

aplicacion = FastAPI(title="Asistente Blackjack — Cadenas de Markov")

zapato_sesion: Optional[Zapato] = None
reglas_sesion: Optional[Reglas] = None


class EntradaReglas(BaseModel):
    cantidad_mazos: int = 6
    crupier_se_planta_suave_17: bool = True
    doblar_cualquier_par: bool = True
    doblar_solo_9_10_11: bool = False
    doblar_solo_10_11: bool = False
    doblar_tras_dividir: bool = True
    maximas_divisiones: int = 3
    rendicion_tardia: bool = True
    pago_blackjack: float = 1.5
    redividir_ases: bool = True


class EntradaCalculo(BaseModel):
    cartas_jugador: str
    carta_visible_crupier: str
    cartas_otros: str = ""


class EntradaActualizacion(BaseModel):
    cartas_a_remover: str = ""


class EntradaQuitarCartas(BaseModel):
    cartas: str


@aplicacion.post("/api/configurar")
def configurar(entrada: EntradaReglas):
    global zapato_sesion, reglas_sesion
    reglas_sesion = Reglas(
        cantidad_mazos=entrada.cantidad_mazos,
        crupier_se_planta_suave_17=entrada.crupier_se_planta_suave_17,
        doblar_cualquier_par=entrada.doblar_cualquier_par,
        doblar_solo_9_10_11=entrada.doblar_solo_9_10_11,
        doblar_solo_10_11=entrada.doblar_solo_10_11,
        doblar_tras_dividir=entrada.doblar_tras_dividir,
        maximas_divisiones=entrada.maximas_divisiones,
        rendicion_tardia=entrada.rendicion_tardia,
        pago_blackjack=entrada.pago_blackjack,
        redividir_ases=entrada.redividir_ases,
    )
    zapato_sesion = Zapato(cantidad_mazos=entrada.cantidad_mazos)
    return {
        "mensaje": "Sesion configurada",
        "reglas": {
            "cantidad_mazos": entrada.cantidad_mazos,
            "crupier_se_planta_suave_17": entrada.crupier_se_planta_suave_17,
            "doblar_cualquier_par": entrada.doblar_cualquier_par,
            "rendicion_tardia": entrada.rendicion_tardia,
            "maximas_divisiones": entrada.maximas_divisiones,
        },
        "zapato": zapato_sesion.a_diccionario(),
    }


@aplicacion.post("/api/calcular")
def calcular(entrada: EntradaCalculo):
    global zapato_sesion, reglas_sesion
    if zapato_sesion is None or reglas_sesion is None:
        raise HTTPException(400, "Configura primero la sesion con /api/configurar")

    try:
        cartas_jugador = convertir_cartas(entrada.cartas_jugador)
        cartas_otros = convertir_cartas(entrada.cartas_otros)
        carta_crupier = entrada.carta_visible_crupier.strip()
        _valor_carta(carta_crupier)
    except Exception:
        raise HTTPException(
            400, "Formato de cartas invalido. Usa: A,2,3,...,10,J,Q,K"
        )

    zapato_temporal = zapato_sesion.copiar()
    zapato_temporal.quitar_cartas(cartas_otros)
    zapato_temporal.quitar_carta(carta_crupier)

    mano = Mano(cartas_jugador)
    solucionador = SolucionadorMarkov(zapato_temporal, reglas_sesion)
    resultado = solucionador.calcular_desglose(mano, carta_crupier)

    resultado["zapato"] = zapato_sesion.a_diccionario()
    resultado["cartas_otros"] = cartas_otros
    return resultado


@aplicacion.post("/api/actualizar")
def actualizar(entrada: EntradaActualizacion):
    global zapato_sesion
    if zapato_sesion is None:
        raise HTTPException(400, "Configura primero la sesion con /api/configurar")

    cartas = convertir_cartas(entrada.cartas_a_remover)
    zapato_sesion.quitar_cartas(cartas)

    return {
        "mensaje": f"Se removieron {len(cartas)} cartas",
        "zapato": zapato_sesion.a_diccionario(),
    }


@aplicacion.post("/api/quitar-cartas")
def quitar_cartas(entrada: EntradaQuitarCartas):
    global zapato_sesion
    if zapato_sesion is None:
        raise HTTPException(400, "Configura primero la sesion con /api/configurar")

    cartas = convertir_cartas(entrada.cartas)
    zapato_sesion.quitar_cartas(cartas)

    return {
        "mensaje": f"{len(cartas)} cartas removidas del zapato",
        "zapato": zapato_sesion.a_diccionario(),
    }


@aplicacion.get("/api/estado")
def estado():
    global zapato_sesion
    return {
        "configurado": zapato_sesion is not None,
        "zapato": zapato_sesion.a_diccionario() if zapato_sesion else None,
    }


DIR_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
aplicacion.mount("/static", StaticFiles(directory=DIR_FRONTEND), name="static")


@aplicacion.get("/")
def indice():
    return FileResponse(os.path.join(DIR_FRONTEND, "index.html"))


def _valor_carta(rango: str) -> int:
    return VALOR_CARTA[rango.strip().upper()]
