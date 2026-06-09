# blackjack-markov-chains

Proyecto final de Lógica y Representación III — Universidad de Antioquia.

**Autores:** Daniel Salas, Kevin Pantoja, Sebastián Cardona
**Profesor:** Gabriel Darío Uribe Guerra

---

## Descripción

Asistente de Blackjack basado en **Cadenas de Markov**. El sistema calcula en tiempo real la probabilidad de obtener cada posible carta en la siguiente jugada, usando una matriz de transición de 19×19 que se recalcula dinámicamente según las cartas que quedan en el zapato. A diferencia de las tablas de estrategia básica, las probabilidades cambian cada vez que una carta sale.

---

## Estructura

```
blackjack-markov-chains/
├── backend/
│   ├── carta.py          # Constantes y funciones de conversión de cartas
│   ├── zapato.py          # Clase Zapato con numpy (conteo de cartas restantes)
│   ├── markov.py          # Matriz de transición 19×19 + cálculo de probabilidades
│   └── app.py             # FastAPI: 3 endpoints (configurar, probabilidades, actualizar)
├── frontend/
│   ├── index.html         # Layout 2 columnas, sin scroll
│   ├── style.css          # Grid responsive, barras compactas, matriz de Markov
│   └── script.js          # Auto-update con debounce 400ms, sin botón calcular
├── DOCUMENTACION.md       # Documentación detallada con diagrama de clases
├── PRESENTACION.md        # Guion de diapositivas para la presentación
├── requirements.txt
└── README.md
```

---

## Flujo de uso

1. **Iniciar Sesión** — seleccionar número de mazos, se crea el zapato
2. **Escribir cartas** — Mis cartas (ej: `10,6`) + Cartas de otros (`5,K,10`). La tabla de probabilidades se actualiza sola a los 400ms
3. **Pedir carta** — se edita Mis cartas a mano (ej: `10,6,4`), recalcula automáticamente
4. **Actualizar Zapato** — descuenta permanentemente todas las cartas jugadas del zapato

---

## Cómo ejecutar

```bash
git clone https://github.com/dan-8000/blackjack-markov-chains.git
cd blackjack-markov-chains
git checkout develop
python3 -m venv .venv
.venv/bin/pip install fastapi uvicorn numpy
.venv/bin/uvicorn backend.app:aplicacion --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000

---

## Dependencias

- FastAPI
- Uvicorn
- NumPy
