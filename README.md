# blackjack-markov-chains

Proyecto final de Lógica y Representación 3 — Asistente de Blackjack con Cadenas de Markov.

---

## Descripción

Asistente interactivo de Blackjack que usa **Cadenas de Markov** como núcleo de toda la lógica de probabilidades. A diferencia de las tablas de estrategia básica estándar (que asumen probabilidades fijas), este sistema recalcula **dinámicamente** las probabilidades de transición en función de la composición exacta del zapato (cartas restantes). Esto permite una recomendación óptima en tiempo real considerando qué cartas ya han salido.

---

## Funcionalidades

1. **Selección de número de mazos** (1, 2, 4, 6, 8)
2. **Persistencia de cartas** — cada carta jugada se descuenta del zapato y no puede repetirse
3. **Ajuste a la partida actual** — se ingresan las cartas del jugador y del crupier, y el sistema recomienda la jugada óptima con desglose completo de valor esperado por acción

---

## Arquitectura

### Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python + FastAPI |
| Frontend | HTML + CSS + JavaScript (servido por FastAPI) |
| Cálculo | Cadena de Markov + value iteration sobre el MDP |
| Reglas | Totalmente configurables desde dropdowns en la UI |

### Estructura del proyecto

```
blackjack-markov-chains/
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── card.py             # Definiciones de cartas (rangos, palos)
│   │   ├── shoe.py             # Zapato (N mazos), tracking de cartas removidas
│   │   ├── hand.py             # Mano: total duro, total suave, bust, soft, par
│   │   └── rules.py            # Reglas configurables (dataclass + defaults)
│   │
│   ├── markov/
│   │   ├── __init__.py
│   │   ├── states.py           # Definición del espacio de estados MDP
│   │   ├── transitions.py      # Probabilidades de transición según composición del zapato
│   │   ├── dealer.py           # Sub-MDP del crupier (juega hasta >=17 o H17)
│   │   └── solver.py           # Cálculo de EV por acción -> recomendación + desglose
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── web.py              # FastAPI endpoints
│   │   ├── static/
│   │   │   └── cards.js        # SVG de cartas
│   │   └── templates/
│   │       └── index.html      # Interfaz principal
│   │
│   └── main.py                 # Entry point: uvicorn
│
├── tests/
│   ├── test_hand.py
│   ├── test_shoe.py
│   ├── test_transitions.py
│   └── test_strategy.py
│
├── requirements.txt
└── README.md
```

---

## Modelo de Markov (núcleo del sistema)

### Definición de estados

Cada estado del MDP se define como una tupla de 6 elementos:

| Componente | Dominio | Descripción |
|---|---|---|
| `player_total` | 4–21 | Total de la mano del jugador |
| `is_soft` | bool | Si contiene un As contado como 11 sin bust |
| `dealer_card` | 1–10 | Carta visible del crupier (As = 1) |
| `can_double` | bool | Si el jugador puede doblar en este estado |
| `can_split` | bool | Si la mano es un par y quedan splits disponibles |
| `can_surrender` | bool | Si aplica rendición tardía |

Además existen **estados terminales**: `WIN`, `LOSE`, `PUSH`, `BUST`, `BLACKJACK`.

### Acciones por estado

| Acción | Condición |
|---|---|
| `HIT` | Siempre (mientras no haya bust) |
| `STAND` | Siempre |
| `DOUBLE` | `can_double == True` |
| `SPLIT` | `can_split == True` |
| `SURRENDER` | `can_surrender == True` (primera acción) |

### Transiciones de Markov

El núcleo del sistema es la **matriz de transición dinámica**:

```
P(estado_siguiente | estado_actual, acción, composición_zapato, reglas)
```

#### Para la acción HIT

Dada la composición actual del zapato (conteo exacto de cartas restantes por rango):

- `P(total_nuevo | total_actual) = count(rango_necesario) / total_cartas_restantes`

Ejemplo con mano 16 duro, crupier muestra 6:

| Carta necesaria | Total resultante | Probabilidad |
|---|---|---|
| As (1) | 17 | `ases_restantes / total` |
| 2 | 18 | `doses_restantes / total` |
| 3 | 19 | `treses_restantes / total` |
| 4 | 20 | `cuatros_restantes / total` |
| 5 | 21 | `cincos_restantes / total` |
| 6..K | BUST | `suma_resto / total` |

#### Para la acción STAND

Se invoca el **sub-MDP del crupier**:

1. Estado inicial: `(dealer_total, dealer_is_soft)` desde la carta visible + carta oculta
2. El crupier sigue su política fija: pegar hasta >=17 (o >=18 si soft 17 = stand, según reglas)
3. Resultado: distribución de probabilidad del total final del crupier (incluyendo bust)
4. De esa distribución se derivan los resultados `WIN`, `LOSE`, `PUSH`

#### Para la acción DOUBLE

Similar a HIT pero con exactamente **una** carta extra y apuesta doble.

#### Para la acción SPLIT

La mano se divide en dos manos independientes. Cada sub-mano se evalúa por separado con la misma cadena de Markov. El EV del split es la suma ponderada del EV de ambas sub-manos.

### Función de recompensa

| Resultado | Recompensa |
|---|---|
| Win | +1 |
| Lose | -1 |
| Push | 0 |
| Blackjack | +1.5 (3:2) o +1.2 (6:5) |
| Surrender | -0.5 |

### Evaluación de valor esperado

```
EV(acción) = Σ P(resultado | acción, zapato, reglas) × recompensa(resultado, reglas)
```

El solver entrega para cada acción legal:
- **Valor esperado** numérico
- **Indicador de acción recomendada** (la de mayor EV)
- **Desglose de probabilidades** de cada resultado terminal

---

## Reglas configurables

Todas las reglas se modelan como un `dataclass` y se seleccionan desde dropdowns en la UI:

| Parámetro | Opciones |
|---|---|
| N° de mazos | 1, 2, 4, 6, 8 |
| Crupier soft 17 | Stand (S17), Hit (H17) |
| Doblar | Any 2 cards, 9/10/11 only, 10/11 only |
| Doblar tras split (DAS) | Sí, No |
| Resplit límite | 1, 2, 3, 4 manos máx |
| Resplit ases | Sí, No |
| Rendición (Surrender) | Sin rendición, Tardía |
| Pago blackjack | 3:2, 6:5 |
| Hit tras split de ases | Sí, No, Solo 1 carta |

---

## Flujo de uso

### 1. Configuración inicial
Seleccionar reglas desde dropdowns + número de mazos -> Iniciar sesión.

### 2. Pantalla principal
- Visualización del zapato restante (resumen por rangos: cuántos Ases, doses, etc. quedan)
- Selector de cartas del jugador (click para añadir) + carta visible del crupier
- Botón "Calcular jugada"

### 3. Resultado
- Tabla con EV de cada acción:

  | Acción | Valor Esperado |
  |---|---|
  | HIT | +0.12 |
  | STAND | -0.08 |
  | DOUBLE | +0.18 (RECOMENDADO) |

- Gráfico de barras comparando EVs
- Desglose de probabilidades de cada desenlace posible

### 4. Resolver mano
El usuario indica qué carta salió (al hacer HIT/DOUBLE) y qué total obtuvo el crupier -> el zapato se actualiza -> siguiente mano.

---

## Dependencias

```
fastapi
uvicorn
jinja2
```

Sin bases de datos, sin frameworks complejos. Toda la lógica de Markov es Python puro.

---

## Consideraciones técnicas

- **Persistencia del zapato**: `Shoe` mantiene un array de conteos por rango `[ases, doses, ..., dieces/figuras]` que se descuenta al jugar cartas. Se mantiene en sesión.
- **Probabilidades dinámicas**: No son estáticas — cada mano recalcula desde la composición actual del zapato.
- **Rendimiento**: El espacio de estados es acotado (~200 estados x 5 acciones). Con memoización, cada consulta toma < 1ms.
- **Split**: El EV se calcula como la suma ponderada de los EVs de cada sub-mano resultante del split.
