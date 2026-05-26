from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os

from .models import Hand, Shoe, Rules, parse_card, CARD_VALUE
from .markov import compute_full_breakdown

app = FastAPI(title="Asistente Blackjack — Cadenas de Markov")

session_shoe: Optional[Shoe] = None
session_rules: Optional[Rules] = None


class RulesInput(BaseModel):
    num_decks: int = 6
    dealer_stands_soft_17: bool = True
    double_any_two: bool = True
    double_9_10_11_only: bool = False
    double_10_11_only: bool = False
    double_after_split: bool = True
    max_splits: int = 3
    late_surrender: bool = True
    blackjack_pays: float = 1.5
    resplit_aces: bool = True


class CalculateInput(BaseModel):
    player_cards: str
    dealer_upcard: str


class UpdateInput(BaseModel):
    cards_to_remove: str = ""


class RemoveCardsInput(BaseModel):
    cards: str


@app.post("/api/configurar")
def configure(r: RulesInput):
    global session_shoe, session_rules
    session_rules = Rules(
        num_decks=r.num_decks,
        dealer_stands_soft_17=r.dealer_stands_soft_17,
        double_any_two=r.double_any_two,
        double_9_10_11_only=r.double_9_10_11_only,
        double_10_11_only=r.double_10_11_only,
        double_after_split=r.double_after_split,
        max_splits=r.max_splits,
        late_surrender=r.late_surrender,
        blackjack_pays=r.blackjack_pays,
        resplit_aces=r.resplit_aces,
    )
    session_shoe = Shoe(num_decks=r.num_decks)
    return {
        "mensaje": "Sesion configurada",
        "reglas": {
            "num_decks": r.num_decks,
            "dealer_stands_soft_17": r.dealer_stands_soft_17,
            "double_any_two": r.double_any_two,
            "late_surrender": r.late_surrender,
            "max_splits": r.max_splits,
        },
        "zapato": session_shoe.to_dict(),
    }


@app.post("/api/calcular")
def calcular(inp: CalculateInput):
    global session_shoe, session_rules
    if session_shoe is None or session_rules is None:
        raise HTTPException(400, "Configura primero la sesion con /api/configurar")

    try:
        player_cards = [c.strip() for c in inp.player_cards.split(",") if c.strip()]
        dealer_card = inp.dealer_upcard.strip()
        _card_val(dealer_card)
    except Exception:
        raise HTTPException(400, "Formato de cartas invalido. Usa: A,2,3,...,10,J,Q,K")

    hand = Hand(player_cards)
    result = compute_full_breakdown(hand, dealer_card, session_shoe, session_rules)
    return result


@app.post("/api/actualizar")
def actualizar(inp: UpdateInput):
    global session_shoe
    if session_shoe is None:
        raise HTTPException(400, "Configura primero la sesion con /api/configurar")

    cards = [c.strip() for c in inp.cards_to_remove.split(",") if c.strip()]
    session_shoe.remove_cards(cards)

    return {
        "mensaje": f"Se removieron {len(cards)} cartas",
        "zapato": session_shoe.to_dict(),
    }


@app.post("/api/quitar-cartas")
def quitar_cartas(inp: RemoveCardsInput):
    global session_shoe
    if session_shoe is None:
        raise HTTPException(400, "Configura primero la sesion con /api/configurar")

    cards = [c.strip() for c in inp.cards.split(",") if c.strip()]
    session_shoe.remove_cards(cards)

    return {
        "mensaje": f"{len(cards)} cartas removidas del zapato",
        "zapato": session_shoe.to_dict(),
    }


@app.get("/api/estado")
def estado():
    global session_shoe, session_rules
    return {
        "configurado": session_shoe is not None,
        "zapato": session_shoe.to_dict() if session_shoe else None,
    }


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


def _card_val(rank: str) -> int:
    return CARD_VALUE[rank.strip().upper()]
