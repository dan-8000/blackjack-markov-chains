# Documentacion — Blackjack con Cadenas de Markov

Proyecto final de Logica y Representacion III — Universidad de Antioquia.

**Autores:** Daniel Salas, Kevin Pantoja, Sebastian Cardona

---

## Arquitectura Simplificada

```
blackjack-markov-chains/
├── backend/
│   ├── __init__.py
│   ├── carta.py        Constantes y 2 funciones (sin clases)
│   ├── zapato.py       1 clase Zapato con numpy
│   ├── markov.py       2 funciones: matriz_transicion + calcular_probabilidades
│   └── app.py          3 endpoints FastAPI
├── frontend/
│   ├── index.html      Layout 2 columnas (izq: inputs, der: resultados)
│   ├── style.css       Grid layout, barras zapato compactas, responsive
│   └── script.js       Auto-update con debounce 400ms, sin boton calcular
├── DOCUMENTACION.md
├── requirements.txt
└── README.md
```

---

## Diagrama de Clases / Modulos

---

### Modulo `carta.py`

Sin clases. Solo constantes y funciones auxiliares para convertir cartas.

```
MODULO carta
├── CONSTANTES
│   ├── VALOR_CARTA : dict[str, int]
│   │   Mapea texto de carta a valor numerico.
│   │   {"A":1, "2":2, ..., "9":9, "10":10, "J":10, "Q":10, "K":10}
│   │
│   └── TEXTO_VALOR : dict[int, str]
│       Mapea valor numerico a texto.
│       {1:"A", 2:"2", ..., 9:"9", 10:"10"}
│
├── FUNCIONES
│   ├── texto_a_valor(texto: str) -> int
│   │   Convierte "A"→1, "2"→2, ..., "K"→10.
│   │
│   ├── aplicar_carta(total: int, es_suave: bool, valor: int) -> (int, bool)
│   │   Aplica una carta a un total de blackjack.
│   │   Maneja el As (valor=1) que puede ser 1 u 11.
│   │   Si la mano es suave y se pasa de 21, el As(11) pasa a As(1).
│   │   Retorna (nuevo_total, nuevo_es_suave).
│   │
│   └── convertir_a_lista(texto: str) -> list[str]
│       Convierte "10,A,K" en ["10","A","K"].
```

---

### Clase `Zapato` (archivo: `zapato.py`)

Representa el zapato con N mazos. Usa un arreglo numpy de 10 posiciones.

```
CLASE Zapato
├── ATRIBUTOS
│   └── conteo : numpy.ndarray (shape=10, dtype=float64)
│       indice 0 = Ases restantes
│       indice 1 = Doses restantes
│       ...
│       indice 8 = Nueves restantes
│       indice 9 = Dieces/Figuras restantes (10+J+Q+K)
│
├── CONSTRUCTOR
│   └── __init__(cantidad_mazos: int)
│       Inicializa el arreglo con 4 de cada valor y 16 dieces por mazo.
│       Ej con 6 mazos: [24,24,24,24,24,24,24,24,24,96]
│
├── METODOS
│   ├── total() -> int
│   │   Suma de todas las cartas restantes.
│   │
│   ├── probabilidades() -> numpy.ndarray
│   │   Vector de 10 probabilidades: conteo / total.
│   │   Si total==0, devuelve vector de ceros.
│   │
│   ├── quitar_carta_por_valor(valor: int) -> None
│   │   Descuenta 1 del indice (valor-1).
│   │
│   ├── quitar_carta(texto: str) -> None
│   │   Convierte el texto a valor y descuenta.
│   │
│   ├── quitar_varias(lista: list[str]) -> None
│   │   Descuenta varias cartas.
│   │
│   └── copiar() -> Zapato
│       Devuelve un Zapato nuevo con el mismo conteo.
```

---

### Modulo `markov.py`

Contiene la logica de la CADENA DE MARKOV con numpy.

```
MODULO markov
├── FUNCION construir_matriz_transicion(zapato: Zapato) -> numpy.ndarray
│   │
│   │   Construye la MATRIZ DE TRANSICION DE MARKOV.
│   │
│   │   Dimension: 19 x 19
│   │     Filas 0-17  = totales actuales 4, 5, ..., 21
│   │     Fila 18      = estado PASADO (bust)
│   │     Columnas      = mismas que las filas
│   │
│   │   T[i][j] = probabilidad de que, estando en el total (i+4),
│   │             la siguiente carta te lleve al total (j+4).
│   │             Si j=18, significa que te pasaste de 21.
│   │
│   │   El estado PASADO es absorbente: T[18][18] = 1.0
│   │
│   │   Ejemplo con 6 mazos sin cartas removidas:
│   │     Desde total 16 (fila 12):
│   │       T[12][13]=0.077 (sacar 1→total 17)
│   │       T[12][14]=0.077 (sacar 2→total 18)
│   │       T[12][15]=0.077 (sacar 3→total 19)
│   │       T[12][16]=0.077 (sacar 4→total 20)
│   │       T[12][17]=0.077 (sacar 5→total 21)
│   │       T[12][18]=0.615 (sacar 6+→PASADO)
│   │
│   │   La matriz se recalcula cada vez que el zapato cambia.
│   │
│   │
│   └── FUNCION calcular_probabilidades(
│           mis_cartas: list[str],
│           cartas_otros: list[str],
│           zapato_sesion: Zapato
│       ) -> dict
│
│       Calcula la probabilidad de cada posible siguiente carta.
│
│       Pasos:
│         1. Calcula el total actual de la mano del jugador
│            (duro si no tiene As, suave si tiene As=11).
│         2. Crea un zapato temporal descontando cartas_otros
│            (las cartas visibles de otros jugadores y el crupier).
│         3. Construye la matriz de Markov con ese zapato temporal.
│         4. Para cada valor de carta (1 al 10) con cartas
│            restantes > 0, calcula:
│              - Probabilidad de sacarla (conteo/total)
│              - Nuevo total aplicando la carta
│              - Si el nuevo total pasa de 21 (PASADO)
│         5. Ordena por probabilidad descendente.
│
│       Retorna:
│         {
│           "mano": { cartas, total, es_suave },
│           "tabla": [ {carta, valor, probabilidad, nuevo_total, pasado}, ... ],
│           "probabilidad_pasarse": 61.57,
│           "carta_mas_probable": "10",
│           "matriz": [[...], ...]   # 19x19
│         }
```

---

## Flujo de la Cadena de Markov

```
1. Zapato inicial: conteo = [4N, 4N, 4N, ..., 16N]  (N = cantidad de mazos)

2. El usuario ingresa:
   - mis_cartas: ["10", "6"]
   - cartas_otros: ["5", "K", "9", "3", "10"]

3. Se crea un zapato TEMPORAL sin las cartas_otros.
   Esto refleja que esas cartas YA NO ESTAN en el zapato
   al momento de calcular que carta viene.

4. Se construye la MATRIZ DE TRANSICION T (19x19):
   Para cada total actual (4 a 21):
     Para cada valor de carta (1 a 10):
       prob = conteo[valor-1] / total_cartas
       nuevo = total_actual + valor
       Si nuevo > 21: T[total][PASADO] += prob
       Si no:         T[total][nuevo-4]  += prob

5. Se muestra la tabla de probabilidades:
   ┌───────┬──────────────┬──────────────┬──────────┐
   │ Carta │ Probabilidad │ Total nuevo  │ ¿Pasado? │
   ├───────┼──────────────┼──────────────┼──────────┤
   │  10   │    30.62%    │      -       │   SI     │
   │   A   │     7.82%    │      17      │   NO     │
   │   ... │     ...      │     ...      │   ...    │
   └───────┴──────────────┴──────────────┴──────────┘

6. El usuario ve la probabilidad de pasarse (61.57%)
   y la carta mas probable (10, con 30.62%).

7. Al terminar la mano, el usuario pulsa "Actualizar Zapato".
   Se descuentan PERMANENTEMENTE mis_cartas + cartas_otros
   del zapato de sesion. Las barras del zapato se actualizan.

8. Siguiente mano: el zapato tiene menos cartas →
   las probabilidades CAMBIAN (la cadena de Markov es dinamica).
```

---

## Endpoints de la API

```
POST /api/configurar
    Entrada: { "cantidad_mazos": 6 }
    Crea un zapato nuevo.
    Salida: { mensaje, total_cartas, conteo: [24,24,...,96] }

POST /api/probabilidades
    Entrada: { "mis_cartas": "10,6", "cartas_otros": "5,K,9,3,10" }
    Calcula la tabla de probabilidades y la matriz de Markov.
    Salida: { mano, tabla, probabilidad_pasarse, carta_mas_probable, matriz, zapato }

POST /api/actualizar
    Entrada: { "mis_cartas": "10,6", "cartas_otros": "5,K,9,3,10" }
    Descuenta PERMANENTEMENTE todas las cartas del zapato.
    Salida: { mensaje, total_restante, conteo: [...] }
```

---

## Dependencias

```
fastapi
uvicorn
numpy
```

---

## Como Ejecutar

```bash
cd blackjack-markov-chains
python3 -m venv .venv
.venv/bin/pip install fastapi uvicorn numpy
.venv/bin/uvicorn backend.app:aplicacion --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000 en el navegador.

---

## Interfaz de Usuario

### Layout (2 columnas, sin scroll)

```
┌────────────────────┬──────────────────────────────────┐
│  IZQUIERDA (300px) │  DERECHA (resto)                  │
│                    │                                   │
│  Mazos: [6▼]       │  ZAPATO compacto (barras horiz)   │
│  [Iniciar Sesion]  │  A ██ 24  2 ██ 24 ... 10 ████ 96 │
│                    │                                   │
│  Mis cartas        │  TU MANO: 10,6 → Total 16         │
│  [10,6       ]     │                                   │
│                    │  TABLA DE PROBABILIDADES           │
│  Cartas otros      │  Carta │ Prob │ Total │ ¿Pasa?    │
│  [5,K,10     ]     │   10   │ 30%  │   -   │   SÍ      │
│                    │   A    │  8%  │  17   │   NO      │
│  [Actualizar]      │   2    │  8%  │  18   │   NO      │
│                    │  ...                               │
│  Instrucciones     │                                   │
│                    │  Pasarte: 61% │ A salvo: 39%       │
│                    │  Más probable: 10                  │
└────────────────────┴──────────────────────────────────┘
```

### Flujo de uso

1. **Iniciar Sesion** → se crea el zapato, aparecen las barras
2. Escribir `10,6` en **Mis cartas** → la derecha se actualiza sola a los 400ms
3. Al pedir carta, el usuario **edita Mis cartas** a mano: `10,6,4` → recalcula solo
4. **Actualizar Zapato** → descuenta Mis cartas + Cartas otros del zapato permanentemente
5. Las barras compactas muestran cuantas cartas quedan de cada rango

### Auto-update

- Los inputs `oninput` disparan un debounce de 400ms
- Sin boton "Calcular": todo se recalcula al escribir
- Sin recarga de pagina: todo via `fetch` + actualizacion DOM

### Matriz de Markov desplegable

- Boton "Ver matriz de Markov ▼" debajo de los resultados
- Muestra la matriz 19x19 completa como mapa de calor
- Filas = total actual, Columnas = total destino
- Celdas coloreadas por intensidad (azul mas intenso = mayor probabilidad)
- Tooltip al pasar el raton con la transicion exacta
- Leyenda: valores en porcentaje con un decimal
