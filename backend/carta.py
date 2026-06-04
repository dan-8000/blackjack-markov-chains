# ─── Constantes ────────────────────────────────────────────
# Valor numerico de cada rango de carta en blackjack

VALOR_CARTA = {
    "A": 1, "2": 2, "3": 3, "4": 4, "5": 5,
    "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "J": 10, "Q": 10, "K": 10,
}

# Texto que representa cada valor numerico
TEXTO_VALOR = {
    1: "A", 2: "2", 3: "3", 4: "4", 5: "5",
    6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
}

# ─── Funciones ─────────────────────────────────────────────

def texto_a_valor(texto: str) -> int:
    """
    Convierte el texto de una carta a su valor numerico.
    "A" o "ACE" -> 1
    "J", "Q", "K" -> 10
    "2"..."9" -> el numero
    """
    limpio = texto.strip().upper()
    if limpio in VALOR_CARTA:
        return VALOR_CARTA[limpio]
    raise ValueError(f"No se reconoce la carta: {texto}")


def aplicar_carta(total_actual: int, es_suave: bool, valor_carta: int) -> tuple:
    """
    Aplica una carta a un total de blackjack.
    
    Parametros:
        total_actual: suma actual de la mano (4-21)
        es_suave: True si la mano tiene un As que vale 11
        valor_carta: valor de la nueva carta (1-10, 1 es As)
    
    Retorna: (nuevo_total, nuevo_es_suave)
    
    Ejemplos:
        aplicar_carta(16, False, 5) -> (21, False)   # 16+5=21
        aplicar_carta(16, False, 6) -> (22, False)   # 16+6=22 PASADO
        aplicar_carta(17, True,  5) -> (22, False)   # A(11)+6=17 +5=22
                                                     # 22-10=12 (As pasa a 1)
        aplicar_carta(17, True,  1) -> (18, True)    # A(11)+6=17 +A(1)=18 suave
    """
    if valor_carta == 1:
        # El As puede valer 1 u 11
        if total_actual + 11 <= 21:
            # Vale 11, la mano sigue siendo suave
            return (total_actual + 11, True)
        else:
            # Vale 1 porque 11 se pasaria
            nuevo = total_actual + 1
            if es_suave and nuevo > 21:
                # El As viejo que valia 11 ahora vale 1
                nuevo = nuevo - 10
            # Si la mano era suave y no se paso, el As viejo
            # sigue valiendo 11 -> la mano sigue siendo suave
            sigue_suave = es_suave and nuevo <= 21
            return (nuevo, sigue_suave)
    else:
        # Carta normal (2-10)
        nuevo = total_actual + valor_carta
        if es_suave and nuevo > 21:
            # El As que valia 11 ahora vale 1: restamos 10
            return (nuevo - 10, False)
        else:
            return (nuevo, es_suave)


# ─── Funcion auxiliar para parsear entradas ────────────────

def convertir_a_lista(texto: str) -> list:
    """Convierte '10,A,K' en ['10','A','K']."""
    return [c.strip() for c in texto.split(",") if c.strip()]
