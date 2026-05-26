# blackjack-markov-chains

Proyecto final de Lógica y Representación 3 — Asistente de Blackjack con Cadenas de Markov.

---

## Descripción

Asistente de Blackjack donde toda la lógica de probabilidades se basa en **Cadenas de Markov**. Las cartas se ingresan manualmente y el número de mazos afecta únicamente las probabilidades de transición del modelo de Markov (composición del zapato). El sistema recalcula dinámicamente las probabilidades en función de las cartas que ya salieron y recomienda la jugada óptima con desglose de valor esperado por acción.

---

## Estructura simplificada

```
blackjack-markov-chains/
├── backend/                  # Toda la lógica en Python
│   ├── __init__.py
│   ├── models.py             # Carta, Mano, Zapato, Reglas
│   ├── markov.py             # Cadena de Markov: estados, transiciones, solver
│   └── app.py                # Endpoints FastAPI
├── frontend/                 # Toda la parte visual
│   ├── index.html            # Interfaz web
│   ├── style.css             # Estilos
│   └── script.js             # Lógica del frontend
├── tests/
│   └── test_core.py          # Tests unitarios
├── requirements.txt
└── README.md
```

---

## Flujo de uso

1. **Configurar reglas** — seleccionar número de mazos y reglas desde dropdowns
2. **Ingresar cartas manualmente** — escribir las cartas del jugador y la visible del crupier (ej: `10,A` para 10 y As)
3. **Calcular jugada** — el sistema corre la cadena de Markov con la composición actual del zapato y devuelve:
   - Valor esperado de cada acción (HIT, STAND, DOUBLE, SPLIT, SURRENDER)
   - Acción recomendada (mayor EV)
   - Desglose de probabilidades de cada desenlace
4. **Registrar resultado** — se ingresan las cartas que salieron, el zapato se actualiza y se pasa a la siguiente mano

---

## Modelo de Markov

### Estados

`(player_total, is_soft, dealer_card, can_double, can_split, can_surrender)`

### Acciones

HIT, STAND, DOUBLE, SPLIT, SURRENDER (condicionadas a las flags del estado).

### Transiciones

La probabilidad de cada transición se calcula a partir de la composición **actual** del zapato (cartas no jugadas). Para HIT:

```
P(total_nuevo | total_actual, zapato) = count(rango_necesario) / total_cartas_restantes
```

Para STAND se ejecuta el sub-MDP del crupier, que juega su política fija. El EV de cada acción es la suma ponderada de recompensas terminales.

---

## Reglas configurables (dropdowns)

| Parámetro | Opciones |
|---|---|
| N° de mazos | 1, 2, 4, 6, 8 |
| Crupier soft 17 | Stand (S17), Hit (H17) |
| Doblar | Any 2 cards, 9/10/11 only, 10/11 only |
| Doblar tras split (DAS) | Sí, No |
| Resplit | 1, 2, 3, 4 manos máx |
| Rendición | Sin rendición, Tardía |
| Pago blackjack | 3:2, 6:5 |

---

## Dependencias

```
fastapi
uvicorn
```

---

## Nota de diseño

- El número de mazos **solo** afecta la composición inicial del zapato (`models.py`) y por tanto las probabilidades de transición del modelo de Markov (`markov.py`). No se modelan reglas adicionales ligadas al número de mazos.
- Las cartas se ingresan de forma manual (texto), sin selector gráfico complejo.
- Backend y frontend están separados en carpetas independientes para mantener el proyecto simple y trabajable.
