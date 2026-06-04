import numpy as np
from . import carta
from .zapato import Zapato


def construir_matriz_transicion(zapato: Zapato) -> np.ndarray:
    """
    Construye la MATRIZ DE TRANSICION DE MARKOV.

    Es una matriz de 19x19 donde:
      - Filas 0-17 representan totales de 4 a 21
      - Fila 18 representa el estado PASADO (bust)
      - Columnas igual que las filas

    T[i][j] = probabilidad de que, estando en el total (i+4),
              la siguiente carta te lleve al total (j+4).
              Si j=18, significa que te pasaste de 21.

    El estado PASADO es absorbente: T[18][18] = 1.0.

    Esta matriz cambia cada vez que el zapato cambia.
    """
    T = np.zeros((19, 19))
    probs = zapato.probabilidades()  # vector de 10: A=0, 2=1, ..., 10=9

    if zapato.total() == 0:
        T[18, 18] = 1.0
        return T

    for i in range(18):           # cada total de 4 a 21
        total_actual = i + 4      # total real de la mano
        for valor in range(1, 11):  # cada valor de carta posible
            prob = probs[valor - 1]
            if prob == 0:
                continue
            nuevo = total_actual + valor
            if nuevo > 21:
                T[i, 18] += prob      # cae en estado PASADO
            else:
                T[i, nuevo - 4] += prob  # cae en el total correspondiente

    # PASADO es absorbente
    T[18, 18] = 1.0

    return T


def calcular_probabilidades(
    mis_cartas: list,
    cartas_otros: list,
    zapato_sesion: Zapato,
) -> dict:
    """
    Calcula la tabla de probabilidades de la SIGUIENTE carta.

    Parametros:
        mis_cartas: lista de cartas del jugador (ej: ['10','6'])
        cartas_otros: cartas visibles de otros jugadores + crupier
        zapato_sesion: zapato actual de la sesion

    Retorna un diccionario con:
        - mano: info de la mano actual (cartas, total, es_suave)
        - tabla: lista de {carta, probabilidad, nuevo_total, pasado}
        - probabilidad_pasarse: porcentaje de pasarse de 21
        - carta_mas_probable: texto de la carta con mas probabilidad
        - matriz: matriz de transicion de Markov (19x19)
    """

    # ── 1. Calcular total de la mano ──
    total_duro = 0
    tiene_as = False
    for c in mis_cartas:
        valor = carta.texto_a_valor(c)
        total_duro += valor
        if valor == 1:
            tiene_as = True

    es_suave = tiene_as and total_duro + 10 <= 21
    total_actual = total_duro + 10 if es_suave else total_duro

    # ── 2. Zapato temporal (descontamos cartas visibles de otros) ──
    temp = zapato_sesion.copiar()
    temp.quitar_varias(cartas_otros)

    # ── 3. Construir la matriz de Markov ──
    matriz = construir_matriz_transicion(temp)

    # ── 4. Calcular tabla de probabilidades ──
    tabla = []
    probs = temp.probabilidades()

    for valor in range(1, 11):
        cantidad = int(temp.conteo[valor - 1])
        if cantidad == 0:
            continue

        porcentaje = float(probs[valor - 1]) * 100

        nuevo_total, nuevo_suave = carta.aplicar_carta(
            total_actual, es_suave, valor
        )
        pasado = nuevo_total > 21

        fila = {
            "carta": carta.TEXTO_VALOR[valor],
            "valor": valor,
            "probabilidad": round(porcentaje, 2),
            "nuevo_total": nuevo_total if not pasado else 0,
            "pasado": pasado,
        }
        tabla.append(fila)

    # ── 5. Ordenar por probabilidad (mayor primero) ──
    tabla.sort(key=lambda f: f["probabilidad"], reverse=True)

    # ── 6. Resultados ──
    carta_top = tabla[0]["carta"] if tabla else "-"
    prob_pasarse = sum(f["probabilidad"] for f in tabla if f["pasado"])

    return {
        "mano": {
            "cartas": mis_cartas,
            "total": total_actual,
            "es_suave": es_suave,
        },
        "tabla": tabla,
        "probabilidad_pasarse": round(prob_pasarse, 2),
        "carta_mas_probable": carta_top,
        "matriz": matriz.tolist(),
    }
