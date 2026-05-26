from dataclasses import dataclass, field
from typing import List, Dict, Tuple

VALOR_CARTA = {
    "A": 1, "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 10, "Q": 10, "K": 10,
}

MAZO_INICIAL = {
    1: 4,
    2: 4,
    3: 4,
    4: 4,
    5: 4,
    6: 4,
    7: 4,
    8: 4,
    9: 4,
    10: 16,
}


def convertir_carta(texto: str) -> int:
    texto = texto.strip().upper()
    if texto in ("A", "ACE", "AS"):
        return 1
    if texto in ("J", "JACK", "JOTA"):
        return 10
    if texto in ("Q", "QUEEN", "REINA"):
        return 10
    if texto in ("K", "KING", "REY"):
        return 10
    try:
        valor = int(texto)
        if 1 <= valor <= 10:
            return valor
        raise ValueError(f"Valor de carta invalido: {texto}")
    except ValueError:
        raise ValueError(f"Carta invalida: {texto}")


class Mano:
    """
    Representa una mano de blackjack con sus cartas y propiedades derivadas.

    Atributos
    ---------
    cartas : List[str]
        Lista de cartas que componen la mano. Cada carta se representa
        como string (ej: "A", "10", "K").
    """

    def __init__(self, cartas: List[str] = None):
        self.cartas: List[str] = cartas or []

    def agregar_carta(self, carta: str) -> None:
        self.cartas.append(carta)

    def _valores(self) -> List[int]:
        return [VALOR_CARTA[c.upper()] for c in self.cartas]

    def _tiene_as(self) -> bool:
        return any(c.upper() == "A" for c in self.cartas)

    @property
    def total_duro(self) -> int:
        return sum(self._valores())

    @property
    def total_suave(self) -> int:
        total = self.total_duro
        if self._tiene_as() and total + 10 <= 21:
            return total + 10
        return total

    @property
    def mejor_total(self) -> int:
        suave = self.total_suave
        if suave <= 21:
            return suave
        return self.total_duro

    @property
    def es_suave(self) -> bool:
        return self._tiene_as() and self.total_duro + 10 <= 21

    @property
    def esta_pasado(self) -> bool:
        return self.total_duro > 21

    @property
    def es_blackjack(self) -> bool:
        return len(self.cartas) == 2 and self.total_suave == 21

    @property
    def es_par(self) -> bool:
        if len(self.cartas) != 2:
            return False
        return VALOR_CARTA[self.cartas[0].upper()] == VALOR_CARTA[self.cartas[1].upper()]

    @property
    def rango_del_par(self) -> int:
        if not self.es_par:
            return 0
        return VALOR_CARTA[self.cartas[0].upper()]

    def copiar(self) -> "Mano":
        return Mano(list(self.cartas))


class Zapato:
    """
    Representa el zapato de blackjack (N mazos). Lleva el conteo de
    cartas restantes por valor numérico y descuenta cartas jugadas.

    Atributos
    ---------
    cantidad_mazos : int
        Número de mazos que componen el zapato.
    conteo : Dict[int, int]
        Cartas restantes por valor clave: {1: ases, 2: doses, ..., 10: dieces/figuras}.
    """

    def __init__(self, cantidad_mazos: int = 6):
        self.cantidad_mazos = cantidad_mazos
        self.conteo: Dict[int, int] = {}
        self._reiniciar()

    def _reiniciar(self) -> None:
        self.conteo = {k: v * self.cantidad_mazos for k, v in MAZO_INICIAL.items()}

    @property
    def total_cartas(self) -> int:
        return sum(self.conteo.values())

    def quitar_carta_por_valor(self, valor: int) -> None:
        clave = valor if valor <= 10 else 10
        if self.conteo.get(clave, 0) > 0:
            self.conteo[clave] -= 1

    def quitar_carta(self, texto_carta: str) -> None:
        valor = VALOR_CARTA[texto_carta.strip().upper()]
        self.quitar_carta_por_valor(valor)

    def quitar_cartas(self, cartas: List[str]) -> None:
        for carta in cartas:
            self.quitar_carta(carta)

    def probabilidad(self, valor: int) -> float:
        total = self.total_cartas
        if total == 0:
            return 0.0
        return self.conteo.get(valor, 0) / total

    def copiar(self) -> "Zapato":
        zapato = Zapato(self.cantidad_mazos)
        zapato.conteo = dict(self.conteo)
        return zapato

    def a_diccionario(self) -> dict:
        return {
            "cantidad_mazos": self.cantidad_mazos,
            "restantes": dict(self.conteo),
            "total_restante": self.total_cartas,
            "por_etiqueta": {
                "A": self.conteo[1],
                "2": self.conteo[2],
                "3": self.conteo[3],
                "4": self.conteo[4],
                "5": self.conteo[5],
                "6": self.conteo[6],
                "7": self.conteo[7],
                "8": self.conteo[8],
                "9": self.conteo[9],
                "10": self.conteo[10],
            },
        }


@dataclass
class Reglas:
    """
    Configuración de reglas de la mesa de blackjack.

    Atributos
    ---------
    cantidad_mazos : int
        Número de mazos en el zapato.
    crupier_se_planta_suave_17 : bool
        True = S17 (el crupier se planta en 17 suave). False = H17 (pide).
    doblar_cualquier_par : bool
        Si se permite doblar con cualquier mano inicial de 2 cartas.
    doblar_solo_9_10_11 : bool
        Si doblar solo se permite con totales 9, 10 u 11.
    doblar_solo_10_11 : bool
        Si doblar solo se permite con totales 10 u 11.
    doblar_tras_dividir : bool
        Si se permite doblar después de dividir (DAS).
    maximas_divisiones : int
        Máximo de divisiones permitidas (3 = hasta 4 manos).
    rendicion_tardia : bool
        Si se permite rendición tardía.
    pago_blackjack : float
        Factor de pago por blackjack natural (1.5 = 3:2, 1.2 = 6:5).
    redividir_ases : bool
        Si se permite volver a dividir ases.
    pedir_en_ases_divididos : bool
        Si se permite pedir después de dividir ases.
    """

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
    pedir_en_ases_divididos: bool = False

    def puede_doblar(self, total: int) -> bool:
        if self.doblar_solo_10_11:
            return total in (10, 11)
        if self.doblar_solo_9_10_11:
            return total in (9, 10, 11)
        if self.doblar_cualquier_par:
            return True
        return False

    def objetivo_crupier(self) -> int:
        return 18 if self.crupier_se_planta_suave_17 else 17
