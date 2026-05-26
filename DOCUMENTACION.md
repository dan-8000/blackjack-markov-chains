# Documentacion — Asistente de Blackjack con Cadenas de Markov

Proyecto final de Logica y Representacion 3.

---

## Diagrama de Clases

A continuacion se describen todas las clases del proyecto con sus atributos, propiedades y metodos.
No se usan flechas de herencia; cada clase es auto-contenida.

---

### Clase `Mano` (archivo: `backend/models.py`)

Representa una mano de blackjack (conjunto de cartas del jugador o crupier).

```
MANO
├── ATRIBUTOS
│   └── cartas : List[str]
│       Lista de cartas que componen la mano.
│       Cada carta es un texto: "A", "2", "3", ..., "10", "J", "Q", "K".
│
├── CONSTRUCTOR
│   └── __init__(cartas: List[str] = None)
│       Inicializa la mano con una lista opcional de cartas.
│
├── PROPIEDADES (calculadas automaticamente)
│   ├── total_duro : int
│   │   Suma de valores de las cartas con todos los Ases valiendo 1.
│   │   Ej: ["A","6"] → 7
│   │
│   ├── total_suave : int
│   │   Suma con un As valiendo 11 si es posible y no pasa de 21.
│   │   Si no hay As o el total suave pasaria de 21, devuelve el total_duro.
│   │   Ej: ["A","6"] → 17
│   │
│   ├── mejor_total : int
│   │   El mejor total posible ≤ 21. Si el total_suave ≤ 21 lo usa;
│   │   si no, usa total_duro.
│   │
│   ├── es_suave : bool
│   │   True si la mano contiene al menos un As contado como 11.
│   │   La mano es "suave" porque no se pasa de 21 aunque pida.
│   │
│   ├── esta_pasado : bool
│   │   True si total_duro > 21 (la mano esta pasada / bust).
│   │
│   ├── es_blackjack : bool
│   │   True si son exactamente 2 cartas y suman 21 (blackjack natural).
│   │
│   ├── es_par : bool
│   │   True si la mano tiene exactamente 2 cartas del mismo valor.
│   │   Ej: ["8","8"] → True, ["10","K"] → True.
│   │
│   └── rango_del_par : int
│       Valor numerico de la carta del par. 0 si no es par.
│       Ej: ["8","8"] → 8
│
├── METODOS
│   ├── agregar_carta(carta: str) -> None
│   │   Anade una carta al final de la mano.
│   │
│   └── copiar() -> Mano
│       Devuelve una copia independiente de la mano.
```

---

### Clase `Zapato` (archivo: `backend/models.py`)

Representa el zapato del crupier (N mazos barajados). Lleva el conteo exacto
de cartas restantes por valor numerico y permite descontar cartas jugadas.
Esta persistencia es la base de las cadenas de Markov: las probabilidades
cambian segun las cartas que ya salieron.

```
ZAPATO
├── ATRIBUTOS
│   ├── cantidad_mazos : int
│   │   Numero de mazos que componen el zapato (1, 2, 4, 6, 8).
│   │
│   └── conteo : Dict[int, int]
│       Cartas restantes por valor numerico.
│       Claves: 1=A, 2=2, ..., 9=9, 10=10/J/Q/K.
│       Valores: cuantas cartas de ese valor quedan.
│       Ej con 1 mazo: {1:4, 2:4, 3:4, 4:4, 5:4, 6:4, 7:4, 8:4, 9:4, 10:16}
│
├── CONSTRUCTOR
│   └── __init__(cantidad_mazos: int = 6)
│       Inicializa el zapato con la cantidad de mazos indicada.
│       Llena el conteo con cantidades_mazos * MAZO_INICIAL.
│
├── PROPIEDADES
│   └── total_cartas : int
│       Suma total de cartas restantes en el zapato.
│
├── METODOS
│   ├── quitar_carta_por_valor(valor: int) -> None
│   │   Desc cuenta una carta del conteo por su valor numerico (1-10).
│   │
│   ├── quitar_carta(texto_carta: str) -> None
│   │   Desc cuenta una carta del conteo usando texto ("A","10","K", etc.).
│   │
│   ├── quitar_cartas(cartas: List[str]) -> None
│   │   Desc cuenta varias cartas del conteo.
│   │
│   ├── probabilidad(valor: int) -> float
│   │   Devuelve la probabilidad de sacar una carta de ese valor
│   │   desde el zapato actual: conteo[valor] / total_cartas.
│   │   Esta funcion ES EL NUCLEO de las cadenas de Markov: alimenta
│   │   todas las probabilidades de transicion.
│   │
│   ├── copiar() -> Zapato
│   │   Devuelve una copia independiente del zapato con el mismo conteo.
│   │
│   └── a_diccionario() -> dict
│       Serializa el zapato a diccionario para enviar al frontend.
│       Campos: cantidad_mazos, restantes, total_restante, por_etiqueta.
```

---

### Clase `Reglas` (archivo: `backend/models.py`)

Configuracion de reglas de la mesa de blackjack. Es un `@dataclass`.

```
REGLAS
├── ATRIBUTOS (todos con valor por defecto)
│   ├── cantidad_mazos : int = 6
│   │   Numero de mazos en el zapato.
│   │
│   ├── crupier_se_planta_suave_17 : bool = True
│   │   True = S17 (crupier se planta en 17 suave).
│   │   False = H17 (crupier pide en 17 suave).
│   │
│   ├── doblar_cualquier_par : bool = True
│   │   True = se puede doblar con cualquier mano inicial de 2 cartas.
│   │
│   ├── doblar_solo_9_10_11 : bool = False
│   │   True = doblar solo con totales 9, 10 u 11.
│   │
│   ├── doblar_solo_10_11 : bool = False
│   │   True = doblar solo con totales 10 u 11.
│   │
│   ├── doblar_tras_dividir : bool = True
│   │   True = permitir doblar despues de dividir (DAS).
│   │
│   ├── maximas_divisiones : int = 3
│   │   Maximo de divisiones (3 = hasta 4 manos). 0 = no se permite dividir.
│   │
│   ├── rendicion_tardia : bool = True
│   │   True = permitir rendicion tardia (late surrender).
│   │
│   ├── pago_blackjack : float = 1.5
│   │   Factor de pago por blackjack natural (1.5 = 3:2, 1.2 = 6:5).
│   │
│   ├── redividir_ases : bool = True
│   │   True = permitir volver a dividir ases.
│   │
│   └── pedir_en_ases_divididos : bool = False
│       True = permitir pedir carta despues de dividir ases.
│
├── METODOS
│   ├── puede_doblar(total: int) -> bool
│   │   Determina si se permite doblar con el total dado.
│   │   Evalua las reglas en orden: doblar_solo_10_11,
│   │   doblar_solo_9_10_11, doblar_cualquier_par.
│   │
│   └── objetivo_crupier() -> int
│       Devuelve el total objetivo del crupier: 18 si S17, 17 si H17.
```

---

### Clase `SolucionadorMarkov` (archivo: `backend/markov.py`)

**NUCLEO DEL PROYECTO.** Contiene toda la logica de cadenas de Markov para
calcular el valor esperado (EV) de cada accion en blackjack.

```
SOLUCIONADOR_MARKOV
├── ATRIBUTOS (privados)
│   ├── _zapato : Zapato
│   │   Zapato con el conteo actual de cartas restantes.
│   │   Las probabilidades de transicion dependen de el.
│   │
│   └── _reglas : Reglas
│       Reglas de la mesa que condicionan acciones legales y
│       comportamiento del crupier.
│
├── CONSTRUCTOR
│   └── __init__(zapato: Zapato, reglas: Reglas)
│       Recibe un zapato y reglas. El solucionador usa estos objetos
│       para todos los calculos de probabilidad.
│
├── METODO PUBLICO PRINCIPAL
│   └── calcular_desglose(mano_jugador: Mano, carta_visible_crupier: str) -> dict
│       Calcula el valor esperado de cada accion y un desglose completo
│       de probabilidades. Devuelve un diccionario con:
│         - jugador: cartas, total, es_suave, es_blackjack, es_par
│         - crupier: carta_visible, distribucion_final (probabilidad de
│           cada total final del crupier)
│         - acciones: para cada accion, valor_esperado y si es recomendada
│         - zapato: estado actual del zapato
│
├── METODOS PRIVADOS (logica de Markov)
│   │
│   ├── _valor_carta(rango: str) -> int
│   │   Convierte "A","2",...,"K" a valor numerico (1-10).
│   │
│   ├── _valor_a_texto(valor: int) -> str
│   │   Convierte valor numerico (1-10) a texto ("A","2",...,"10").
│   │
│   ├── _crupier_debe_pedir(total: int, es_suave: bool) -> bool
│   │   Politica fija del crupier: pide si total < 17, o si total == 17
│   │   suave con regla H17. Esta es la politica del sub-MDP del crupier.
│   │
│   ├── _aplicar_carta(total: int, es_suave: bool, valor: int) -> (int, bool)
│   │   Aplica una carta de valor `valor` a un total dado.
│   │   Maneja el caso del As (valor=1) como 1 o 11 segun convenga,
│   │   y la conversion de suave a duro si el nuevo total pasa de 21.
│   │   Devuelve (nuevo_total, nuevo_es_suave).
│   │   Esta funcion define las TRANSICIONES DE ESTADO de la cadena.
│   │
│   ├── _distribucion_crupier(carta_visible: int) -> Dict[int, float]
│   │   Calcula la distribucion de probabilidad del total final del
│   │   crupier usando una CADENA DE MARKOV:
│   │     - Para cada posible carta oculta (pesada por zapato):
│   │       inicializa la mano del crupier (2 cartas)
│   │     - El crupier juega su politica fija con _jugar_mano()
│   │     - Acumula probabilidades de cada total final
│   │   La funcion interna _jugar_mano() es recursiva con memoizacion
│   │   (lru_cache) y resuelve el sub-MDP del crupier.
│   │
│   ├── _resultado_plantarse(total_jugador: int, carta_visible: int) -> float
│   │   Valor esperado de plantarse con un total dado.
│   │   Compara el total del jugador contra la distribucion final
│   │   del crupier: gana=+1, pierde=-1, empata=0.
│   │
│   └── _calcular_evs(mano_jugador, carta_visible_str, ...) -> Dict[str, (float, str)]
│       ECUACION DE BELLMAN para el MDP del jugador.
│       Para cada accion legal, calcula el valor esperado:
│
│       PEDIR: EV(total) = Σ P(carta) × max(EV_plantarse(nuevo_total),
│                                            EV_pedir(nuevo_total))
│              Esta es una cadena de Markov con decision optima en
│              cada estado. Se resuelve con recursion memoizada (_ve_pedir).
│
│       PLANTARSE: EV = Σ P(total_crupier) × recompensa
│              Usa _resultado_plantarse().
│
│       DOBLAR: EV = 2 × Σ P(carta) × recompensa_plantarse(nuevo_total)
│              Exactamente una carta, apuesta doble.
│
│       DIVIDIR: EV = Σ P(carta1,carta2) × (EV_mano1 + EV_mano2)
│              La mano se divide en dos manos independientes. Cada una
│              recibe una carta nueva y se juega optimamente.
│
│       RENDIRSE: EV = -0.5 (fijo, rendicion tardia).
│
│       Devuelve {accion: (ev, "RECOMENDADO" | "")}.
```

---

## Constantes del Modulo (archivo: `backend/models.py`)

```
VALOR_CARTA : Dict[str, int]
    Mapea texto de carta a valor numerico.
    {"A":1, "2":2, ..., "9":9, "10":10, "J":10, "Q":10, "K":10}

MAZO_INICIAL : Dict[int, int]
    Composicion de 1 mazo: {1:4, 2:4, ..., 9:4, 10:16}
    (10 incluye 10, J, Q, K: 4 palos x 4 rangos = 16)

convertir_carta(texto: str) -> int
    Funcion auxiliar: convierte "A","2",...,"K","ACE","JACK",... a valor.
```

---

## Funciones Auxiliares (archivo: `backend/markov.py`)

```
convertir_cartas(texto_mano: str) -> List[str]
    Parsea un string de cartas separadas por coma. Ej: "10,A,K" → ["10","A","K"]
```

---

## Endpoints de la API (archivo: `backend/app.py`)

La aplicacion FastAPI (`aplicacion`) expone los siguientes endpoints:

```
POST /api/configurar
    Recibe: EntradaReglas (JSON con reglas de la mesa)
    Crea: Zapato y Reglas en variables globales de sesion
    Devuelve: mensaje, reglas, estado del zapato

POST /api/calcular
    Recibe: EntradaCalculo {cartas_jugador: "10,A", carta_visible_crupier: "6"}
    Ejecuta: SolucionadorMarkov.calcular_desglose()
    Devuelve: desglose completo con EVs y distribucion del crupier

POST /api/actualizar
    Recibe: EntradaActualizacion {cartas_a_remover: "5,Q,8"}
    Ejecuta: Zapato.quitar_cartas() para descontar cartas jugadas
    Devuelve: mensaje, estado del zapato

POST /api/quitar-cartas
    Alternativa a /api/actualizar con formato simplificado {cartas: "5"}

GET /api/estado
    Devuelve: si la sesion esta configurada y estado del zapato

GET /
    Sirve el archivo frontend/index.html

/static/*
    Sirve archivos estaticos del frontend (CSS, JS)
```

---

## Flujo de la Cadena de Markov

```
ESTADO INICIAL
  jugador: (total_actual, es_suave, carta_visible_crupier, puede_doblar, puede_dividir, puede_rendirse)
  zapato: composicion actual de cartas restantes

PARA CADA ACCION:
  │
  ├── PEDIR (cadena de Markov recursiva)
  │   Para cada carta posible en el zapato:
  │     nuevo_estado = estado + carta
  │     Si pasado → recompensa -1
  │     Si no pasado → max(EV_plantarse, EV_pedir)
  │   EV_pedir = Σ prob(carta) × recompensa
  │
  ├── PLANTARSE (sub-MDP del crupier)
  │   distribucion_crupier = cadena_markov_crupier(carta_visible)
  │   EV = Σ prob(total_crupier) × (gana?+1 : pierde?-1 : 0)
  │
  ├── DOBLAR (1 carta, apuesta doble)
  │   EV = 2 × Σ prob(carta) × recompensa_plantarse(nuevo_total)
  │
  ├── DIVIDIR (dos cadenas independientes)
  │   mano1 = par[0] + nueva_carta → jugar optimamente
  │   mano2 = par[1] + nueva_carta → jugar optimamente
  │   EV = Σ prob(carta1,carta2) × (EV_mano1 + EV_mano2)
  │
  └── RENDIRSE
      EV = -0.5

ACCION RECOMENDADA = argmax(EV)
```

---

## Dependencias

```
fastapi>=0.100.0
uvicorn>=0.23.0
```

---

## Como Ejecutar

```bash
cd blackjack-markov-chains
python3 -m venv .venv
.venv/bin/pip install fastapi uvicorn
.venv/bin/uvicorn backend.app:aplicacion --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000 en el navegador.
