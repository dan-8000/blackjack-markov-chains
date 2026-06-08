# Proyecto Final — Asistente de Blackjack con Cadenas de Markov

## 2. Introduccion

El blackjack es un juego de cartas donde las decisiones del jugador determinan el resultado. La estrategia basica tradicional usa tablas fijas con probabilidades constantes, ignorando las cartas que ya salieron del zapato. Este proyecto implementa un asistente basado en **Cadenas de Markov** que recalcula dinamicamente la probabilidad de cada siguiente carta segun la composicion real del zapato en ese instante. La importancia del trabajo radica en demostrar como un modelo de Markov con matriz de transicion dinamica captura la memoria del sistema (cartas ya jugadas) y produce resultados mas precisos que los enfoques estaticos.

## 3. Objetivo

Desarrollar un sistema web que, mediante una matriz de transicion de Markov de 19x19 y la composicion actual del zapato, calcule en tiempo real la probabilidad de obtener cada posible carta en la siguiente jugada de blackjack.

## 4. Desarrollo y Metodologia

**Fase 1 — Investigacion:** Estudio de los fundamentos de Cadenas de Markov, reglas del blackjack y composicion de mazos. Se definio el espacio de estados (totales 4 a 21 + estado PASADO) y la matriz de transicion de 19x19.

**Fase 2 — Implementacion:** Desarrollo del backend en Python con FastAPI y numpy. La clase `Zapato` gestiona las cartas restantes con un arreglo numpy de 10 posiciones. La funcion `construir_matriz_transicion()` genera la matriz de Markov donde `T[i][j]` = probabilidad de pasar del total `i+4` al total `j+4` con una carta. Se construyo una interfaz web con React de 2 columnas con actualizacion automatica cada 400ms y visualizacion compacta del zapato.

**Fase 3 — Analisis:** Validacion de resultados contra probabilidad teorica (ej: con 16 el jugador tiene 61.5% de pasarse con 6 mazos frescos). Verificacion del ajuste dinamico de probabilidades al remover cartas del zapato.

## 5. Resultados y Conclusiones

### Tabla de metricas

| Variable | Valor Esperado | Valor Obtenido |
|---|---|---|
| Precision matriz vs. probabilidad teorica | 100% | 100% |
| Tiempo de respuesta del calculo | < 500ms | < 100ms |
| Estados modelados (totales del jugador) | 19 | 19 |
| Prob. pasarse con total 16 (6 mazos) | 61.5% | 61.6% |

### Conclusion

El proyecto cumple con el objetivo propuesto: la matriz de transicion 19x19 modela correctamente todas las transiciones posibles en blackjack. Se comprobo que al remover cartas del zapato las probabilidades se ajustan adecuadamente (ej: la probabilidad de sacar 10 baja si ya salieron varios 10). La interfaz permite visualizar en tiempo real la cadena de Markov en accion.

## 6. Bibliografia

[1] NumPy Developers. (2024). *NumPy Documentation*. https://numpy.org/doc/

[2] FastAPI. (2024). *FastAPI Documentation*. https://fastapi.tiangolo.com/

[3] React. (2024). *React Documentation*. https://react.dev/
