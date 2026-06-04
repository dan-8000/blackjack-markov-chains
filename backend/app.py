import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import carta
from .zapato import Zapato
from . import markov


# ── App ────────────────────────────────────────────────────

aplicacion = FastAPI(title="Blackjack — Cadenas de Markov")

# ── Estado global (sesion unica) ───────────────────────────

zapato_sesion: Zapato = None


# ── Modelos de entrada ─────────────────────────────────────

class EntradaConfigurar(BaseModel):
    cantidad_mazos: int = 6


class EntradaProbabilidades(BaseModel):
    mis_cartas: str          # ej: "10,6"
    cartas_otros: str = ""   # ej: "5,K,9,3,10"


class EntradaActualizar(BaseModel):
    mis_cartas: str
    cartas_otros: str = ""


# ── Endpoints ──────────────────────────────────────────────

@aplicacion.post("/api/configurar")
def configurar(entrada: EntradaConfigurar):
    """Crea un zapato nuevo con la cantidad de mazos indicada."""
    global zapato_sesion
    zapato_sesion = Zapato(entrada.cantidad_mazos)
    return {
        "mensaje": "Zapato configurado",
        "total_cartas": zapato_sesion.total(),
        "conteo": [int(x) for x in zapato_sesion.conteo],
    }


@aplicacion.post("/api/probabilidades")
def probabilidades(entrada: EntradaProbabilidades):
    """
    Calcula la tabla de probabilidades de la siguiente carta.
    Usa la matriz de transicion de Markov con numpy.
    """
    global zapato_sesion
    if zapato_sesion is None:
        raise HTTPException(400, "Configura primero con /api/configurar")

    mis = carta.convertir_a_lista(entrada.mis_cartas)
    otros = carta.convertir_a_lista(entrada.cartas_otros)

    if not mis:
        raise HTTPException(400, "Ingresa al menos una carta en 'mis_cartas'")

    resultado = markov.calcular_probabilidades(mis, otros, zapato_sesion)

    resultado["zapato"] = {
        "total": zapato_sesion.total(),
        "conteo": [int(x) for x in zapato_sesion.conteo],
    }

    return resultado


@aplicacion.post("/api/actualizar")
def actualizar(entrada: EntradaActualizar):
    """
    Descuenta permanentemente del zapato las cartas que ya salieron.
    Incluye tanto las mias como las de otros jugadores/crupier.
    """
    global zapato_sesion
    if zapato_sesion is None:
        raise HTTPException(400, "Configura primero con /api/configurar")

    mis = carta.convertir_a_lista(entrada.mis_cartas)
    otros = carta.convertir_a_lista(entrada.cartas_otros)
    todas = mis + otros

    zapato_sesion.quitar_varias(todas)

    return {
        "mensaje": f"{len(todas)} cartas removidas del zapato",
        "total_restante": zapato_sesion.total(),
        "conteo": [int(x) for x in zapato_sesion.conteo],
    }


# ── Archivos estaticos y pagina principal ──────────────────

DIR_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
aplicacion.mount("/static", StaticFiles(directory=DIR_FRONTEND), name="static")


@aplicacion.get("/")
def indice():
    return FileResponse(os.path.join(DIR_FRONTEND, "index.html"))
