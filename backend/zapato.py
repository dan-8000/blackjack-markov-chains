import numpy as np


class Zapato:
    """
    Representa el zapato de blackjack (N mazos barajados).
    Lleva el conteo exacto de cartas restantes usando un arreglo numpy.

    Atributos:
        conteo: numpy array de 10 posiciones.
                indice 0 = Ases, 1 = doses, ..., 9 = dieces/figuras
    """

    def __init__(self, cantidad_mazos: int):
        # 1 mazo: 4 Ases, 4 de cada numero (2-9), 16 dieces (10+J+Q+K)
        self.conteo = np.array([4] + [4] * 8 + [16], dtype=np.float64) * cantidad_mazos

    def total(self) -> int:
        """Total de cartas restantes en el zapato."""
        return int(np.sum(self.conteo))

    def probabilidades(self) -> np.ndarray:
        """
        Vector de probabilidad para cada valor de carta (A=indice0, ..., 10=indice9).
        probabilidad[i] = conteo[i] / total_cartas
        """
        t = self.total()
        if t == 0:
            return np.zeros(10)
        return self.conteo / t

    def quitar_carta_por_valor(self, valor: int) -> None:
        """Desc cuenta una carta del zapato por su valor numerico (1-10)."""
        indice = valor - 1
        if self.conteo[indice] > 0:
            self.conteo[indice] -= 1

    def quitar_carta(self, texto: str) -> None:
        """Desc cuenta una carta del zapato por su texto ('A','10','K',...)."""
        from .carta import texto_a_valor
        self.quitar_carta_por_valor(texto_a_valor(texto))

    def quitar_varias(self, lista_textos: list) -> None:
        """Desc cuenta varias cartas del zapato."""
        for t in lista_textos:
            self.quitar_carta(t)

    def copiar(self) -> "Zapato":
        """Devuelve una copia independiente del zapato."""
        nuevo = Zapato.__new__(Zapato)
        nuevo.conteo = self.conteo.copy()
        return nuevo
