from functools import lru_cache
from collections import defaultdict
from typing import Dict, List, Tuple

from .models import VALOR_CARTA, Mano, Zapato, Reglas


class SolucionadorMarkov:
    """
    Motor de cálculo de valor esperado para blackjack basado en cadenas de Markov.

    Toda la lógica de probabilidades se deriva de la composición actual del zapato.
    Las transiciones entre estados del MDP se calculan dinámicamente con las
    cartas restantes en el zapato.

    Atributos
    ---------
    zapato : Zapato
        Zapato con el conteo actual de cartas restantes.
    reglas : Reglas
        Reglas de la mesa.
    """

    def __init__(self, zapato: Zapato, reglas: Reglas):
        self._zapato = zapato
        self._reglas = reglas

    def calcular_desglose(
        self, mano_jugador: Mano, carta_visible_crupier: str
    ) -> dict:
        """
        Calcula el valor esperado de cada acción y el desglose completo
        de probabilidades para la mano actual.

        Retorna un diccionario con la mano del jugador, distribución del
        crupier, EVs por acción, y estado del zapato.
        """
        evs = self._calcular_evs(mano_jugador, carta_visible_crupier)

        valor_visible = self._valor_carta(carta_visible_crupier)
        dist_crupier = self._distribucion_crupier(valor_visible)

        distribucion_formateada = {}
        for total, prob in dist_crupier.items():
            etiqueta = "PASADO" if total > 21 else str(total)
            distribucion_formateada[etiqueta] = (
                distribucion_formateada.get(etiqueta, 0) + prob * 100
            )
        distribucion_formateada = {
            k: round(v, 2) for k, v in distribucion_formateada.items()
        }

        return {
            "jugador": {
                "cartas": mano_jugador.cartas,
                "total": mano_jugador.mejor_total,
                "es_suave": mano_jugador.es_suave,
                "es_blackjack": mano_jugador.es_blackjack,
                "es_par": mano_jugador.es_par,
            },
            "crupier": {
                "carta_visible": carta_visible_crupier.upper(),
                "distribucion_final": distribucion_formateada,
            },
            "acciones": {
                accion: {
                    "valor_esperado": round(ev, 4),
                    "recomendada": etiqueta == "RECOMENDADO",
                }
                for accion, (ev, etiqueta) in evs.items()
            },
            "zapato": self._zapato.a_diccionario(),
        }

    def _valor_carta(self, rango: str) -> int:
        return VALOR_CARTA[rango.strip().upper()]

    def _valor_a_texto(self, valor: int) -> str:
        if valor == 1:
            return "A"
        elif 2 <= valor <= 9:
            return str(valor)
        else:
            return "10"

    def _crupier_debe_pedir(self, total: int, es_suave: bool) -> bool:
        if total > 21:
            return False
        if total < 17:
            return True
        if total == 17 and es_suave and not self._reglas.crupier_se_planta_suave_17:
            return True
        return False

    def _aplicar_carta(
        self, total: int, es_suave: bool, valor: int
    ) -> Tuple[int, bool]:
        if valor == 1:
            if total + 11 <= 21:
                return (total + 11, True)
            else:
                nuevo_total = total + 1
                if es_suave and nuevo_total > 21:
                    nuevo_total -= 10
                return (nuevo_total, False)

        nuevo_total = total + valor
        if es_suave:
            if nuevo_total > 21:
                return (nuevo_total - 10, False)
            else:
                return (nuevo_total, True)
        else:
            return (nuevo_total, False)

    def _distribucion_crupier(self, carta_visible: int) -> Dict[int, float]:
        @lru_cache(maxsize=100)
        def _jugar_mano(total: int, es_suave: bool) -> Dict[int, float]:
            if not self._crupier_debe_pedir(total, es_suave):
                return {total: 1.0}

            resultado = defaultdict(float)
            total_cartas_zapato = self._zapato.total_cartas
            if total_cartas_zapato == 0:
                return {total: 1.0}

            for valor, cantidad in self._zapato.conteo.items():
                if cantidad == 0:
                    continue
                prob = cantidad / total_cartas_zapato
                nuevo_total, nuevo_suave = self._aplicar_carta(
                    total, es_suave, valor
                )
                sub_dist = _jugar_mano(nuevo_total, nuevo_suave)
                for total_final, prob_final in sub_dist.items():
                    resultado[total_final] += prob * prob_final

            return dict(resultado)

        resultado = defaultdict(float)
        total_cartas_zapato = self._zapato.total_cartas
        if total_cartas_zapato == 0:
            return {carta_visible: 1.0}

        for valor_oculta, cantidad_oculta in self._zapato.conteo.items():
            if cantidad_oculta == 0:
                continue
            prob = cantidad_oculta / total_cartas_zapato

            total_duro = carta_visible + valor_oculta
            tiene_as = carta_visible == 1 or valor_oculta == 1
            if tiene_as and total_duro + 10 <= 21:
                total_inicial = total_duro + 10
                es_suave_inicial = True
            else:
                total_inicial = total_duro
                es_suave_inicial = False

            sub = _jugar_mano(total_inicial, es_suave_inicial)
            for total_final, prob_final in sub.items():
                resultado[total_final] += prob * prob_final

        return dict(resultado)

    def _resultado_plantarse(
        self, total_jugador: int, carta_visible: int
    ) -> float:
        if total_jugador > 21:
            return -1.0
        distribucion = self._distribucion_crupier(carta_visible)
        ve = 0.0
        for total_crupier, prob in distribucion.items():
            if total_crupier > 21:
                ve += prob * 1.0
            elif total_jugador > total_crupier:
                ve += prob * 1.0
            elif total_jugador < total_crupier:
                ve += prob * -1.0
        return ve

    def _calcular_evs(
        self,
        mano_jugador: Mano,
        carta_visible_str: str,
        divisiones_restantes: int = None,
        permitir_doblar: bool = True,
        permitir_rendirse: bool = True,
    ) -> Dict[str, Tuple[float, str]]:
        """
        Calcula el valor esperado (EV) de cada acción legal usando la
        ecuación de Bellman sobre la cadena de Markov.
        """
        if divisiones_restantes is None:
            divisiones_restantes = self._reglas.maximas_divisiones

        carta_visible = self._valor_carta(carta_visible_str)
        total_jugador = mano_jugador.mejor_total
        es_suave = mano_jugador.es_suave

        resultados: Dict[str, float] = {}

        if mano_jugador.es_blackjack:
            return {"BLACKJACK": (self._reglas.pago_blackjack, "RECOMENDADO")}

        if total_jugador > 21:
            return {"PASADO": (-1.0, "")}

        if permitir_rendirse and self._reglas.rendicion_tardia:
            resultados["RENDIRSE"] = -0.5

        ve_plantarse = self._resultado_plantarse(total_jugador, carta_visible)
        resultados["PLANTARSE"] = ve_plantarse

        @lru_cache(maxsize=2000)
        def _ve_pedir(total: int, suave: bool, puede_doblar: bool) -> float:
            ve = 0.0
            total_cartas_zapato = self._zapato.total_cartas
            if total_cartas_zapato == 0:
                return 0.0

            for valor, cantidad in self._zapato.conteo.items():
                if cantidad == 0:
                    continue
                prob = cantidad / total_cartas_zapato
                nuevo_total, nuevo_suave = self._aplicar_carta(
                    total, suave, valor
                )

                if nuevo_total > 21:
                    ve += prob * (-1.0)
                else:
                    ve_stand = self._resultado_plantarse(
                        nuevo_total, carta_visible
                    )
                    if puede_doblar:
                        ve_hit = _ve_pedir(nuevo_total, nuevo_suave, False)
                        ve += prob * max(ve_stand, ve_hit)
                    else:
                        ve += prob * max(
                            ve_stand, _ve_pedir(nuevo_total, nuevo_suave, False)
                        )

            return ve

        ve_pedir = _ve_pedir(total_jugador, es_suave, False)
        resultados["PEDIR"] = ve_pedir

        if (
            permitir_doblar
            and len(mano_jugador.cartas) == 2
            and self._reglas.puede_doblar(total_jugador)
        ):
            ve_doblar = 0.0
            total_cartas_zapato = self._zapato.total_cartas
            for valor, cantidad in self._zapato.conteo.items():
                if cantidad == 0:
                    continue
                prob = cantidad / total_cartas_zapato
                nuevo_total, _ = self._aplicar_carta(
                    total_jugador, es_suave, valor
                )
                if nuevo_total > 21:
                    ve_doblar += prob * (-2.0)
                else:
                    ve_stand = self._resultado_plantarse(
                        nuevo_total, carta_visible
                    )
                    ve_doblar += prob * 2.0 * ve_stand
            resultados["DOBLAR"] = ve_doblar

        if mano_jugador.es_par and divisiones_restantes > 0:
            ve_dividir = 0.0
            valor_par = mano_jugador.rango_del_par
            total_cartas_zapato = self._zapato.total_cartas

            if total_cartas_zapato > 0:
                for valor1, cnt1 in self._zapato.conteo.items():
                    if cnt1 == 0:
                        continue
                    p1 = cnt1 / total_cartas_zapato
                    mano1 = Mano(
                        [self._valor_a_texto(valor_par), self._valor_a_texto(valor1)]
                    )
                    ve1 = max(
                        _ve_pedir(
                            mano1.mejor_total,
                            mano1.es_suave,
                            self._reglas.doblar_tras_dividir,
                        ),
                        self._resultado_plantarse(
                            mano1.mejor_total, carta_visible
                        ),
                    )

                    for valor2, cnt2 in self._zapato.conteo.items():
                        if cnt2 == 0:
                            continue
                        p2 = cnt2 / total_cartas_zapato
                        mano2 = Mano(
                            [
                                self._valor_a_texto(valor_par),
                                self._valor_a_texto(valor2),
                            ]
                        )
                        ve2 = max(
                            _ve_pedir(
                                mano2.mejor_total,
                                mano2.es_suave,
                                self._reglas.doblar_tras_dividir,
                            ),
                            self._resultado_plantarse(
                                mano2.mejor_total, carta_visible
                            ),
                        )
                        ve_dividir += p1 * p2 * (ve1 + ve2)

            resultados["DIVIDIR"] = ve_dividir

        mejor_accion = max(resultados, key=lambda k: resultados[k])
        return {
            k: (v, "RECOMENDADO" if k == mejor_accion else "")
            for k, v in resultados.items()
        }


def convertir_cartas(texto_mano: str) -> List[str]:
    if not texto_mano.strip():
        return []
    return [c.strip() for c in texto_mano.split(",")]
